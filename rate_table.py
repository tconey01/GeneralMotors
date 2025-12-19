"""
Rate Table Sinusoidal Test
Collects position data during sinusoidal oscillation for IMU validation.
"""

import serial
import time
import csv
import threading
from datetime import datetime

# === CONFIG ===
COM_PORT = 'COM10'
BAUD_RATE = 9600
LOG_FILE = 'rate_table_sinusoid_test.csv'

AMPLITUDE = 20      # degrees
FREQUENCY = 0.3     # Hz
DURATION = 180      # seconds
NUM_CYCLES = 54     # cycles to run

TARGET_SAMPLE_RATE = 5  # Hz
MIN_SAMPLE_INTERVAL = 1.0 / TARGET_SAMPLE_RATE

# Globals
ser = None
logging_active = False
test_start_time = None


def connect_rate_table():
    """Open serial connection to rate table."""
    global ser
    try:
        ser = serial.Serial(COM_PORT, baudrate=BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        print(f"Connected to {COM_PORT}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


def send_command(cmd, timeout=2.0, silent=False):
    """Send command and wait for response."""
    try:
        ser.reset_input_buffer()
        ser.write((cmd + '\r').encode())
        
        response = b''
        start = time.time()
        while time.time() - start < timeout:
            if ser.in_waiting:
                response += ser.read(ser.in_waiting)
                if b'>' in response:
                    break
            time.sleep(0.01)
        
        text = response.decode('ascii', errors='ignore')
        text = text.replace('>', '').replace('\r', '').replace('\n', '').strip()
        
        if '?' in text:
            return False, text
        if not silent:
            print(f"  {cmd}: {text if text else 'OK'}")
        return True, text
    except Exception as e:
        return False, str(e)


def query_position():
    """Get current position (fast query)."""
    try:
        ser.reset_input_buffer()
        ser.write(b'PPO\r')
        
        response = b''
        start = time.time()
        while time.time() - start < 0.5:
            if ser.in_waiting:
                response += ser.read(ser.in_waiting)
                if b'>' in response:
                    break
            time.sleep(0.001)
        
        val = response.decode('ascii', errors='ignore')
        val = val.replace('>', '').replace('\r', '').replace('\n', '').strip()
        if val.startswith('PPO'):
            val = val[3:].strip()
        return float(val) if val and '?' not in val else None
    except:
        return None


def wait_for_motion_complete(timeout=60):
    """Poll until table stops moving."""
    start = time.time()
    while time.time() - start < timeout:
        ok, status = send_command('MCO5', silent=True)
        if ok and status == '0':
            return True
        time.sleep(0.5)
    return False


def initialize_rate_table():
    """Home table and configure test parameters."""
    print("\nInitializing...")
    
    # Stop any motion
    send_command('STO', silent=True)
    time.sleep(1)
    
    # Home
    print("  Homing...")
    send_command('HOM')
    if not wait_for_motion_complete():
        print("  Home failed")
        return False
    
    # Try to zero position counter
    send_command('PZR', silent=True)  # or ZRO, POF0
    
    # Set test parameters
    print("  Setting parameters...")
    send_command(f'AMP{AMPLITUDE}')
    send_command(f'FRQ{FREQUENCY}')
    send_command(f'CYC{NUM_CYCLES}')
    
    # Try bipolar mode (may not be supported)
    send_command('SOS-1', silent=True)
    
    return True


def log_encoder_data():
    """Background thread: log position to CSV."""
    global logging_active, test_start_time
    
    test_start_time = time.time()
    sample_count = 0
    last_sample_time = 0
    last_valid_pos = 0
    
    # Outlier thresholds
    MIN_POS, MAX_POS = -30, 50
    MAX_JUMP = 30
    
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        f.write(f"# Rate Table Test - {datetime.now()}\n")
        f.write(f"# Amplitude: {AMPLITUDE} deg, Freq: {FREQUENCY} Hz\n")
        f.write("# ---\n")
        writer.writerow(['Timestamp', 'Time_Relative_sec', 'Position_deg'])
        
        while logging_active:
            now = time.time()
            if now - last_sample_time < MIN_SAMPLE_INTERVAL:
                time.sleep(0.01)
                continue
            
            pos = query_position()
            if pos is None:
                continue
                
            # Filter outliers
            if pos < MIN_POS or pos > MAX_POS:
                pos = last_valid_pos
            elif abs(pos - last_valid_pos) > MAX_JUMP and sample_count > 0:
                pos = last_valid_pos
            else:
                last_valid_pos = pos
            
            t_rel = now - test_start_time
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            writer.writerow([ts, f'{t_rel:.6f}', f'{pos:.4f}'])
            
            sample_count += 1
            last_sample_time = now
            
            # Progress (every 50 samples)
            if sample_count % 50 == 0:
                rate = sample_count / t_rel if t_rel > 0 else 0
                print(f"  {sample_count} samples | {t_rel:.0f}s | {pos:.1f} deg")
                f.flush()
    
    print(f"\nLogged {sample_count} samples to {LOG_FILE}")


def run_test():
    """Execute sinusoidal motion."""
    global logging_active
    
    print("\nStarting motion in 3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    
    send_command('SGO')
    print(f"Running for {DURATION} seconds...")
    
    # Wait for test duration
    start = time.time()
    while time.time() - start < DURATION + 5:
        time.sleep(1)
    
    send_command('STO')
    logging_active = False
    print("Test complete.")


def main():
    print("="*50)
    print("RATE TABLE SINUSOIDAL TEST")
    print("="*50)
    
    peak_vel = AMPLITUDE * 2 * 3.14159 * FREQUENCY
    print(f"Amplitude: {AMPLITUDE} deg | Freq: {FREQUENCY} Hz")
    print(f"Peak velocity: {peak_vel:.1f} deg/s | Duration: {DURATION}s")
    
    if not connect_rate_table():
        return
    if not initialize_rate_table():
        return
    
    print("\n*** Start your IMU logging now ***")
    input("Press ENTER when ready...")
    
    global logging_active
    logging_active = True
    log_thread = threading.Thread(target=log_encoder_data)
    log_thread.start()
    
    time.sleep(2)  # let logger start
    run_test()
    
    log_thread.join(timeout=10)
    ser.close()
    print("Done. Run imu_validation_v3.py to analyze.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging_active = False
        if ser and ser.is_open:
            send_command('STO', silent=True)
            ser.close()
