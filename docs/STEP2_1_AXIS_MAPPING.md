# Step 2.1 – X/Y axis swap test firmware generated

Status: patch generated, structurally validated, and committed. Physical hardware validation remains pending.

## User-observed problem
The user confirmed:
- Physical left/right rotation moves aim vertically.
- Physical up/down rotation moves aim horizontally.

This indicates an X/Y axis swap rather than a simple sign inversion.

## Fix2 artifact
`build/CURRENT_1_gyro-accel-fix2.UF2` was generated from the user-uploaded working `CURRENT_1_gyro-accel-fix.UF2` by changing four 16-bit Thumb instruction halfwords in the report builder so that gyro X/Y and accelerometer X/Y fields are exchanged. Z remains unchanged. The earlier gyro/accelerometer report-slot correction is preserved.

- Original SHA-256: `4c2285c3f37ee3947d0c775e972c2ff6f74fadffd0e960e895b458a7d646731d`
- Fix2 SHA-256: `6ae70b770439f23933224ca5fed58d4bba54180d270e4267534b4134cadb2fa5`
- Size: 1,908,736 bytes (same as original)
- Only 4 byte positions changed; the four 16-bit instruction halfwords matched the expected values before patching.
- UF2 block magic and structure validated.
- The GitHub Actions workflow successfully generated and committed the artifact on `jsm-calibration`.

This is a binary patch, not a source rebuild. Do not claim the physical controller behavior is confirmed until the user flashes and tests it.

## Hardware test
1. Keep the previous working `CURRENT_1_gyro-accel-fix.UF2` as a recovery file.
2. Flash `CURRENT_1_gyro-accel-fix2.UF2` from this branch.
3. Test slow left/right and up/down movements in JoyShockMapper.
4. Check roll/Z behavior and ensure no new jitter, disconnects, or DFU problems.
5. Report the result before making any further patch.
