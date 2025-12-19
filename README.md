# GM IMU Validation Test Suite

User guide for validating Bosch gyroscope sensors using an Ideal Aerosmith rate table. This toolkit supports GM's SAE Level 2 to Level 3 autonomy transition by characterizing IMU noise performance through Allan Deviation analysis.

---

## Overview

This suite contains three Python scripts for end-to-end IMU validation:

| Script | Purpose |
|--------|---------|
| `imu_stationary_noise_test.py` | Collects stationary data for Allan Deviation analysis |
| `rate_table_sinusoid_test.py` | Collects dynamic sinusoidal motion data for accuracy validation |
| `adev_analysis.py` | Generates Allan Deviation plots from collected data |

---

## Hardware Requirements

- **Rate Table:** Ideal Aerosmith single-axis rate table with serial interface
- **IMU Sensor:** Bosch gyroscope with RPMABO interface
- **Connection:** USB-to-serial adapter (FTDI recommended)
- **Computer:** Windows or macOS with Python 3.8+

---

## Software Setup

### 1. Install Dependencies

```bash
pip install pyserial pandas numpy matplotlib allantools
```

### 2. Identify Your COM Port

**Windows:**
1. Open Device Manager
2. Expand "Ports (COM & LPT)"
3. Note the COM port (e.g., `COM10`)

**macOS/Linux:**
```bash
ls /dev/tty.usb*
```
Note the device path (e.g., `/dev/tty.usbserial-FTEIZBTE`)

### 3. Configure Scripts

Edit the `COM_PORT` variable in each script:

```python
# Windows
COM_PORT = 'COM10'

# macOS
COM_PORT = '/dev/tty.usbserial-FTEIZBTE'
```

---

## Test Procedures

### Test 1: Stationary Noise Test (Allan Deviation)

This test collects 11 minutes of stationary data at 125 Hz for noise characterization.

**Parameters:**
- Duration: 660 seconds (11 min)
- Sample Rate: 125 Hz
- Position: 0° (stationary)
- Filtering: None (raw data required for ADEV)

**Steps:**

1. Mount the Bosch IMU securely on the rate table platform
2. Ensure all cables are strain-relieved to prevent vibration coupling
3. Power on the rate table and allow 5 minutes for thermal stabilization
4. Run the script:

```bash
python imu_stationary_noise_test.py
```

5. The script will:
   - Home the rate table
   - Move to 0° position
   - Prompt you to start IMU logging
   - Collect encoder position data for 11 minutes

6. **Important:** Start your Bosch IMU data logging software when prompted, before pressing ENTER

**Output:** `imu_stationary_noise_test.csv`

---

### Test 2: Sinusoidal Motion Test

This test validates IMU accuracy during controlled sinusoidal motion.

**Default Parameters:**
- Amplitude: ±20°
- Frequency: 0.3 Hz
- Duration: 180 seconds
- Peak Velocity: ~37.7°/s
- Sample Rate: 5 Hz

**Steps:**

1. Verify IMU is securely mounted
2. Run the script:

```bash
python rate_table_sinusoid_test.py
```

3. Start your IMU logging when prompted
4. Press ENTER to begin oscillation
5. The table will perform 54 cycles of sinusoidal motion

**Output:** `rate_table_sinusoid_test.csv`

**Customizing Parameters:**

Edit these variables at the top of the script:

```python
AMPLITUDE = 20      # degrees (adjust for your test range)
FREQUENCY = 0.3     # Hz (adjust for desired dynamics)
DURATION = 180      # seconds
NUM_CYCLES = 54     # should match DURATION * FREQUENCY
```

---

### Test 3: Allan Deviation Analysis

After collecting stationary data, run this script to generate ADEV plots.

**Steps:**

1. Export your Bosch IMU data to CSV format
2. Ensure the CSV contains columns for Time and Rate (deg/s) for each axis
3. Update the input filename:

```python
INPUT_FILE = 'your_imu_data.csv'
```

4. Run the analysis:

```bash
python adev_analysis.py
```

**Output:** `adev_3axis_plot.png`

**Expected CSV Format:**

```
Time,Rate_1,Unit,Rate_2,Unit,Rate_3,Unit
0.000,0.0123,deg/s,0.0045,deg/s,-0.0078,deg/s
0.008,0.0134,deg/s,0.0056,deg/s,-0.0067,deg/s
...
```

The script automatically skips the first 10% of data to remove startup transients.

---

## Interpreting Allan Deviation Results

The ADEV plot shows noise characteristics vs. averaging time (tau):

| Slope | Noise Type | Typical Source |
|-------|------------|----------------|
| -1 | Quantization Noise | ADC resolution |
| -0.5 | Angle Random Walk (ARW) | White noise in rate |
| 0 | Bias Instability | Flicker noise, temperature |
| +0.5 | Rate Random Walk | Brownian motion |
| +1 | Rate Ramp | Drift, aging |

**Key Metrics:**
- **ARW (Angle Random Walk):** Read at τ = 1 second on the -0.5 slope region
- **Bias Instability:** Minimum point of the ADEV curve

---

## Troubleshooting

### Connection Issues

| Problem | Solution |
|---------|----------|
| "Connection failed" | Verify COM port, check USB connection |
| No response from table | Confirm baud rate is 9600 |
| Garbled responses | Check serial cable shielding |

### Data Quality Issues

| Problem | Solution |
|---------|----------|
| Low sample rate | Reduce other serial traffic, use dedicated USB port |
| Position spikes | Check encoder cable connections |
| Inconsistent timing | Close background applications |

### Analysis Issues

| Problem | Solution |
|---------|----------|
| "Could not determine sample rate" | Verify Time column is numeric |
| Flat ADEV curve | Check IMU was actually stationary |
| No data plotted | Ensure column names match script expectations |

---

## File Outputs

| File | Contents |
|------|----------|
| `imu_stationary_noise_test.csv` | Timestamped encoder positions (stationary) |
| `rate_table_sinusoid_test.csv` | Timestamped encoder positions (sinusoidal) |
| `adev_3axis_plot.png` | Allan Deviation plot for 3 gyro axes |

---

## Safety Notes

- Always ensure the rate table area is clear before starting motion
- Use the emergency stop if unexpected behavior occurs
- The scripts include `Ctrl+C` interrupt handling to safely stop the table
- Allow the table to complete homing before walking away

---

## Rate Table Command Reference

Common Ideal Aerosmith commands used by these scripts:

| Command | Function |
|---------|----------|
| `HOM` | Home the table |
| `PPO` | Query current position |
| `STO` | Stop all motion |
| `SGO` | Start oscillation |
| `AMP#` | Set amplitude (degrees) |
| `FRQ#` | Set frequency (Hz) |
| `CYC#` | Set number of cycles |
| `P#` | Move to position (degrees) |

---

## Contact

For questions about this test suite, contact the GM Senior Design team at Tufts University.
