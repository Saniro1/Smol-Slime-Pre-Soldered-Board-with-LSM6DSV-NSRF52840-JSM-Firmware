# JSM calibration project – progress log

Goal: make the Smol Slime (SuperMini nRF52840 + single LSM6DSV) work properly with
JoyShockMapper by porting the calibration ideas from
[DGB-SOURCE-CODE-JSM](https://github.com/Saniro1/DGB-SOURCE-CODE-JSM) (dual BMI160, RP2040)
to a single-IMU design.

| # | Step | Status |
|---|------|--------|
| 1 | Inspect both repos + both UF2 files, record findings | done |
| 2 | Find why aim "bounces" on `CURRENT_1.UF2` – gyro/accel report swap identified and patched | done; user reports improvement |
| 2.1 | Diagnose X/Y mapping | done: user confirmed left/right drives vertical aim and up/down drives horizontal aim |
| 2.2 | Apply X/Y axis swap to the tested UF2 | `build/CURRENT_1_gyro-accel-fix2.UF2` generated and committed; user reports improved mapping but horizontal X sign was reversed |
| 2.3 | Correct gyro direction signs | fix3/fix4/fix5 retained as diagnostic variants; `build/CURRENT_1_gyro-accel-fix6.UF2` negates reported gyro X and Y together; hardware test pending |
| 3 | Specify the DGB calibration algorithm precisely (and its flaws) | pending |
| 4 | Design single-IMU calibration (bias, stationary detect, auto-recal) | pending |
| 5 | Implement calibration core (pure C) + host tests | pending |
| 6 | Implement LSM6DSV scaling / axis map / DS4 report for JSL | pending |
| 7 | Zephyr app + board definition + CI workflow | pending |
| 8 | Get CI green, produce .uf2 | pending |
| 9 | Flash/test guide, recovery paths, JSM config tuning | pending |
| 10 | Final docs, release, cleanup | pending |

See `docs/STEP1_ANALYSIS.md`, `docs/STEP2_ROOT_CAUSE.md`, `docs/STEP2_1_AXIS_MAPPING.md`, and `docs/STEP2_3_X_SIGN.md`.
