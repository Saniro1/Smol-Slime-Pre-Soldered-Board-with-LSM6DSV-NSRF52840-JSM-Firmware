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


## Follow-up: fix4 did not correct left/right

The user tested fix4 and reported that left/right was still inverted, matching the symptom of fix2. Root cause in the fix4 trampoline: it loaded and negated Y, but branched back to `0x97E0`, where the original Y-load instruction overwrote that temporary value. Meanwhile, X was left un-negated.

Fix5 is therefore an X-only correction based on fix4: negate the signed X value in the trampoline, then return to `0x97E0` so the original code loads Y normally. Local static checks pass and the resulting UF2 SHA-256 is `2f69057c5a9f8ab98dcabc589d61b8299814b25cbf8eb5412d2003cfcd8ed419`. Hardware verification remains pending.


## Follow-up: latest direction symptoms and combined fix6

The latest user test reports that up/down is reversed and rolling left produces right/down while rolling right produces left/up. The prior fix5 artifact is byte-identical to fix3 and only negates X; it was not a complete XYZ remap. That limitation should have been stated clearly.

Fix6 is a more direct test of the observed direction errors: negate both reported gyro X and Y, leave Z unchanged because no Z-only test result establishes its sign, and resume after the original X/Y loads at 0x97E4. The trampoline is checked to ensure the Y value is not overwritten by the original load. This is still a hypothesis based on the reported directions; hardware testing is required to validate whether the IMU mounting/orientation needs a different axis permutation or a true 3D transform.

- [x] Create a patcher that validates the fix4 input, UF2 structure, branch destination, and fix6 return branch.
- [x] Generate fix6 locally and statically verify the return target is 0x97E4.
- [ ] Hardware test: left/right, up/down, and roll/Z.
- [ ] If roll still couples into both screen axes, capture a one-axis-at-a-time test and revisit the full coordinate transform.


## Follow-up: yaw versus roll response (fix7 candidate)

After flashing fix6, the user reports that the corrected directions are now right, but horizontal aiming responds to roll rather than yaw. This suggests the horizontal output is sourcing the wrong physical axis, not merely needing extra smoothing.

Fix7 is a diagnostic X/Z source-axis swap based on the current report-builder instruction sequence. It preserves the existing X sign inversion, changes the output-X gyro/accelerometer loads to source offset 4, and changes the output-Z loads to source offset 2. The Y output is untouched. This is a test candidate, not a confirmed physical solution; verify yaw, roll, pitch, and stability on hardware before accepting it.
