# Step 2.3 – Invert horizontal X direction

Status: binary patch generated and committed; hardware acceptance test pending.

## User test result
After testing `CURRENT_1_gyro-accel-fix2.UF2`, the user reported that the axes behaved correctly, but horizontal X was reversed: left turned right and right turned left.

## Fix3 implementation
`build/CURRENT_1_gyro-accel-fix3.UF2` preserves fix2's X/Y mapping and negates only the signed gyro-X value used by the report builder. The code at `0x97DC` now branches to a small Thumb-2 trampoline in erased flash at `0xAC858`; it reloads gyro X from `[r0,#2]`, applies `RSBS r2,r2,#0`, and returns to `0x97E0`. The existing report packing, Y, Z, and accelerometer values are otherwise unchanged.

The patcher `tools/patch_x_sign.py` checks the exact expected instruction bytes and verifies the code-cave bytes are erased (`0xFF`) before writing. It also validates UF2 block structure and asserts that only 14 payload bytes change. Output SHA-256: `679848e09972272553104249232a775a1d30d8f8db2e220d33b1179f91f7b7b3`.

## Validation status
- [x] Static instruction review: branch enters the trampoline, loads signed gyro X, negates it, and branches back to the original report builder.
- [x] UF2 structure and exact changed-byte checks pass in the patcher.
- [x] Generated and committed on `jsm-calibration`; `main` remains untouched.
- [ ] Hardware acceptance test: confirm left turns left and right turns right.
- [ ] Confirm up/down direction, Z/roll, jitter, connection stability, and boot behavior remain correct.

Because this is a binary patch to firmware without a reproducible source build, treat fix3 as a test build until those hardware checks pass. Keep fix2 available as the fallback.
