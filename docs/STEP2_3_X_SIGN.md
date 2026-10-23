# Step 2.3 – Gyro direction signs

Status: fix3 preserved as an inverted reference; fix4 generated for hardware testing.

## User test result

The user reports that the corrected fix3 behaves better, but both left/right and up/down directions are inverted in their current adapter orientation. The existing corrected fix3 binary is retained unchanged as `CURRENT_1_gyro-accel-fix3-Inverted.UF2` so it remains available as a known reference.

## fix4 direction adjustment

`build/CURRENT_1_gyro-accel-fix4.UF2` reverses both observed directions relative to fix3 while preserving the existing X/Y axis mapping. At `0x97DC`, execution branches to the trampoline at `0xAC858`. The trampoline reloads the signed gyro values from `[r0,#2]` and `[r1,#2]`, leaves X un-negated, negates Y, and returns to `0x97E4` after the original pair of loads.

The binary patcher refuses unexpected branch/trampoline bytes, checks UF2 structure, and verifies that the intended code cave bytes are available. This is still a binary patch to firmware without a reproducible source build.

## Build checks and hardware status

- [x] Preserve the corrected fix3 byte-for-byte as `CURRENT_1_gyro-accel-fix3-Inverted.UF2`.
- [x] Assemble and inspect the fix4 trampoline instructions and return branch.
- [x] Validate UF2 block structure and confirm only the trampoline bytes change in fix4.
- [ ] Hardware test: confirm left turns left and right turns right.
- [ ] Hardware test: confirm up moves up and down moves down.
- [ ] Confirm Z/roll, jitter, connection stability, and boot behavior remain correct.

Keep fix2 as the earlier fallback and fix3-Inverted as the reference until fix4 is tested on the actual board. The new direction behavior is not considered hardware-validated yet.
