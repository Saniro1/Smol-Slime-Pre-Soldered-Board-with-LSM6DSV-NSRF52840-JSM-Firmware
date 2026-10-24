# Step 1 – Analysis of the inputs

## `CURRENT_1.UF2` (the firmware that is currently detected by JSM)
* UF2 family `0x239a00b3` (SlimeVR/Adafruit bootloader), app range `0x1000–0xEA000`, 954,368 bytes,
  same layout as the stock SlimeVR dump.
* It is **not** a small hand-written sketch: it is the full **SlimeVR-Tracker-nRF** firmware
  (Zephyr / nRF Connect SDK v3.1.1, target `promicro_uf2/nrf52840/stackedspi`, commit `cbfff16ebed1`,
  built by `Shine-Bright-Meow/SlimeNRF-Firmware-CI`) modified to enumerate over USB as
  **"Sony Interactive Entertainment Wireless Controller"** and to send **DualSense** HID reports
  (`Failed to submit DualSense report`, `connection_over_hid`, `New protocol: %s`).
* Compared with the stock dump only the USB/HID parts, product strings and some code differ; the
  sensor drivers (incl. `lsm_gyro_read`) and the **USB serial shell are still present**, so these
  commands exist: `calibrate` (gyro zero-rate), `6-side` (accelerometer), `reset_data (zro|acc|mag|bat|all)`,
  `list_config / read_config / write_config` with `sensor_gyro_odr`, `sensor_gyro_fs`,
  `sensor_accel_odr`, `sensor_accel_fs`, `sensor_fusion`, `sensor_use_6_side_calibration`, `dfu`.
* The firmware source of the DualSense patch is not available to me, so I cannot rebuild this exact
  file; the work will be a new firmware in this repo (Zephyr, same board definition) that keeps
  the SlimeVR bootloader/DFU compatibility.

## `Normal DGB Firmware (auto touch detection) (2).uf2` / `DGB-SOURCE-CODE-JSM`
RP2040-Zero, **two BMI160** on SPI0, capacitive touch gate. The repo source is a *reconstruction*
from the UF2. Calibration-relevant behaviour:
1. Boot: ~1000 samples at 1 kHz while still; per-sensor integer mean = zero-rate offset (`bias1`, `bias2`).
2. Run: subtract bias per sensor, then **average the two sensors** (noise /√2). Not possible with 1 IMU.
3. Gyro is **zeroed when the touch button is not touched** ("ratcheting"), accel always on.
4. Sensor 1 ±500 dps, sensor 2 ±2000 dps, yet raw LSBs are averaged directly – the two have different
   LSB/dps (65.5 vs 16.4) so this only works if the reconstruction is wrong or sensor 2 dominates;
   do **not** copy that part.
5. No scaling to the DualShock 4 unit (JoyShockLibrary expects 2000/32767 dps per LSB for
   DS4 over USB), no temperature/auto re-calibration, report is not byte-exact DS4.
6. JSM config used with it: `REAL_WORLD_CALIBRATION=64`, `AUTO_CALIBRATE=YES`, `GYRO_SMOOTH_TIME=0.05`.

## Likely causes for the "bouncing" aim (hypotheses to test in step 2)
* gyro bias not calibrated/applied or stored calibration invalid (`calibrate` never run);
* gyro full-scale/ODR config does not match the units sent in the HID report;
* report cadence/timestamp jitter (SlimeVR sends at its own tracker rate, not 1 kHz);
* axis mapping/sign.

## Quick test that needs no rebuild
Put the board flat and still, open the USB serial port, run `calibrate`, then `read_config all`.
