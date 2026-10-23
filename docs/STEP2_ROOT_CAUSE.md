# Step 2 – Why the aim "bounces" with `CURRENT_1.UF2`

Method: disassembled the Thumb-2 image (base 0x1000) and followed the data from the IMU read to the
USB report. Addresses below are flash addresses in `CURRENT_1.UF2`.

## USB identity
Device descriptor at 0xA714 → VID `0x054C`, PID `0x0CE6` = **DualSense**. JoyShockLibrary therefore
parses it with its DualSense code (`InputHelpers.cpp`, `controller_type == s_ds`), USB `indexOffset = 1`:

| report byte | JSL meaning |
|---|---|
| 16–21 | **gyro** X,Y,Z, `× 2000/32767` dps |
| 22–27 | **accel** X,Y,Z, `÷ 8192` g |

## What the firmware does
* Sensor loop (0x4F4A…): reads IMU → accel buffer `sp+0x3C`, gyro buffer `sp+0x48`; the gyro gets the stored
  zero-rate bias subtracted (0xA10C) and goes to the fusion; accel likewise (0xA080).
* Converter (0x99B8): gyro floats `× 16.0` → int16 into buffer **0x2000510C**; accel floats `× 8192.0` →
  int16 into buffer **0x20005106**.
* Report builder (0x9770): report id 1, sticks 0x80, hat 8, then
  bytes 16–21 ← buffer **0x20005106** (accel!), bytes 22–27 ← buffer **0x2000510C** (gyro!).

**=> gyro and accelerometer are swapped in the report.** JoyShockMapper receives gravity
(≈ 1 g × 8192 ≈ "500 °/s" on the vertical axis, changing with every tilt) as angular velocity,
and the real rotation rate as acceleration. That produces exactly the symptom "aim bounces all over
the screen" and no amount of calibration can fix it.

## Secondary findings (not fixed yet)
* Gyro scale is `×16` LSB/dps, JSL assumes 32767/2000 = 16.384 → sensitivity 2.3 % low (JSM's
  `REAL_WORLD_CALIBRATION` can absorb that).
* Sensor timestamp in bytes 28–31 has 1 ms granularity (cycle counter → ms → ×1000) and the wrong unit
  for a real DualSense (1/3 µs). JSL does not use it for DualSense, harmless for now.
* ZRO (gyro bias) comes from SlimeVR's stored calibration; if `calibrate` was never run the bias is 0.
* Report cadence = whenever the sensor thread posts new data; not locked to 1 kHz. To be measured in later steps.

## Fix delivered in this step
`tools/patch_ds_swap.py` swaps the two literal-pool words at 0x9938/0x993C (8 bytes in total, verified
to be referenced only by the report builder). Output: `build/CURRENT_1_gyro-accel-fix.UF2`
(2 bytes differ from `CURRENT_1.UF2`; bootloader and UF2 family untouched, so double-tap reset / `dfu`
still work and you can always re-flash `CURRENT.UF2`).

Not tested on hardware by me – please test (see PROGRESS.md / chat message).

> ⚠️ `build/firmware.uf2` and `build/imu_finder.uf2` in this repo are the old Arduino builds that
> bricked the bootloader flow on this board. Do **not** flash them.
