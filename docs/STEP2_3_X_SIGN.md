# Step 2.3 – Invert horizontal X direction

Status: diagnosis confirmed; safe binary patch not yet implemented.

## User test result
After testing `CURRENT_1_gyro-accel-fix2.UF2`, the user reports the axes now work better, but horizontal X is reversed: left turns right and right turns left.

## Required change
This is a sign inversion, not another axis swap. Preserve the X/Y swap from fix2 and negate only the gyro component JoyShockMapper uses for horizontal aim. Do not change Y or Z. Whether the accelerometer X component should also be negated depends on the firmware's coordinate-frame conventions; do not alter it without confirming the report semantics.

## Safety
Do not use a guessed byte edit or simply rename the existing fix2 binary as fix3. The modified DualSense firmware does not have a reproducible source build in this repository. A safe patch requires verified disassembly of the report-building routine and a regression check that only the intended X sign operation changes. No `CURRENT_1_gyro-accel-fix3.UF2` is published by this documentation update.

## Acceptance test
- [ ] Left physical rotation moves horizontal aim left.
- [ ] Right physical rotation moves horizontal aim right.
- [ ] Up/down remains on the vertical axis with the current correct direction.
- [ ] Z/roll remains unchanged.
- [ ] No new jitter, disconnect, or bootloader regression.
