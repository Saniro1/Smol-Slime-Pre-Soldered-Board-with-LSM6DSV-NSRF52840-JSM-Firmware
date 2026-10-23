# Step 2.1 – X/Y axes are swapped

Status: diagnosis confirmed by user; implementation pending verified firmware patch.

## Observation
The user tested the Step 2 report-slot fix in JoyShockMapper:
- Physical left/right rotation moves aim vertically.
- Physical up/down rotation moves aim horizontally.

This is an **axis swap**, not merely a sign inversion. The next intended mapping is to exchange the X and Y gyro components while preserving Z. Do not negate both axes as that would not correct the observed cross-axis response.

## Intended correction
For the DualSense-style input report described in `docs/STEP2_ROOT_CAUSE.md`, gyro X/Y are signed 16-bit little-endian values at report bytes 16–19:
- bytes 16–17: gyro X
- bytes 18–19: gyro Y
- bytes 20–21: gyro Z

The intended correction is:
- report gyro X <- prior gyro Y
- report gyro Y <- prior gyro X
- report gyro Z <- prior gyro Z

The accelerometer occupies bytes 22–27 after the Step 2 slot fix. Whether its X/Y values should also be exchanged must follow the same physical coordinate-frame mapping for a coherent 3-axis sensor frame. Do not change its mapping independently without verifying the sensor-to-controller orientation.

## Safety and current state
No new UF2 was generated in this update. The repository does not contain the original source for the modified DualSense SlimeVR binary, and the current tool context does not provide the actual `CURRENT_1_gyro-accel-fix.UF2` bytes to inspect or patch. A blind binary edit could corrupt the firmware or patch the wrong instruction/data. The Step 2 report-slot fix remains the known-good fallback and should be kept unchanged.

To implement this correctly, obtain the exact tested `CURRENT_1_gyro-accel-fix.UF2` file (or a reproducible source/build for that modified firmware), inspect the report-builder disassembly and literal/data references, patch only the verified X/Y assignments, then verify the patched UF2 structure and byte-level diff. Test left/right, up/down, and roll/Z behavior on hardware before marking this step complete.

## Hardware validation checklist
- [ ] Left/right physical rotation moves horizontal aim.
- [ ] Up/down physical rotation moves vertical aim.
- [ ] Each direction has the expected sign.
- [ ] Z/roll behavior remains unchanged.
- [ ] No new jitter, disconnect, or bootloader/DFU regression.
