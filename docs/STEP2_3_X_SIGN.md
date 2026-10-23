# Step 2.3 – Invert horizontal X direction

Status: corrected branch encoding generated and committed; hardware acceptance test pending.

## User test result
The user reported that fix2 mapped the axes correctly but horizontal X was reversed: left turned right and right turned left. The first fix3 attempt failed because I encoded the Thumb-2 branch bytes in the wrong byte order. That binary must not be used.

## Corrected fix3
`build/CURRENT_1_gyro-accel-fix3.UF2` has been regenerated from the working fix2 input using the corrected little-endian Thumb-2 `B.W` instruction. It branches from `0x97DC` to the trampoline at `0xAC858`, which reloads the signed gyro-X value from `[r0,#2]`, negates it with `NEGS r2,r2`, and branches back to `0x97E0`.

The patcher checks the exact original instruction bytes and verifies the code-cave bytes are erased (`0xFF`). It also decodes and verifies both branch destinations, validates UF2 structure, and checks that exactly 14 payload bytes change. Corrected fix3 SHA-256: `2f69057c5a9f8ab98dcabc589d61b8299814b25cbf8eb5412d2003cfcd8ed419`.

## Validation status
- [x] Corrected branch destination decodes to `0xAC858`.
- [x] Trampoline return branch decodes to `0x97E0`.
- [x] UF2 structure and exact changed-byte checks pass.
- [x] Corrected fix3 committed on `jsm-calibration`; `main` untouched.
- [ ] Hardware acceptance test: confirm left turns left and right turns right.
- [ ] Confirm up/down direction, Z/roll, jitter, connection stability, and boot behavior remain correct.

This is still a binary patch to firmware without a reproducible source build. Keep fix2 as the fallback until the corrected fix3 is tested on the board.
