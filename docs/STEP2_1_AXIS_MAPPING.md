# Step 2.1 – Diagnose X/Y axis behavior

Status: in progress. The user reports the gyro/accelerometer slot-swap patch improved aiming, but X/Y feel inverted. No new UF2 is generated in this step because the description alone does not distinguish an axis swap from a sign inversion.

## Why we need one directional observation
These are different fixes:
- **Axis swap:** a physical left/right rotation is interpreted as vertical aim (or vice versa). Swap the X and Y gyro values.
- **Sign inversion:** physical left/right remains horizontal, but aiming goes the opposite way. Negate the corresponding gyro axis.
- **Coordinate-frame/orientation mismatch:** behavior can depend on how the board is mounted; the sensor-to-controller mapping must be defined from the board's physical axes.

Blindly negating both X and Y or swapping them may fix one motion while breaking another. The report-slot fix from Step 2 must be preserved.

## Safe test
1. Keep the currently working `CURRENT_1_gyro-accel-fix.UF2` available as a recovery file.
2. Open JoyShockMapper and make a small, slow **left/right** rotation while observing the aim.
3. Then make a small, slow **up/down** rotation.
4. Report which behavior applies:
   - A. Left/right motion moves aim vertically, and up/down moves it horizontally (axes swapped).
   - B. Left/right motion stays horizontal but direction is reversed (X sign inverted).
   - C. Up/down motion stays vertical but direction is reversed (Y sign inverted).
   - D. Both horizontal and vertical directions are reversed (both signs inverted).
   - E. Something else; describe it.

Only one short observation is required before choosing a change. Do not flash the original unpatched `CURRENT_1.UF2` to compare, because it has the previously identified gyro/accelerometer report-slot bug.

## Implementation boundary
The existing modified DualSense firmware's source is not available. A source-level correction requires a reproducible build from the source; alternatively a binary patch must be justified by verified disassembly and regression checks. Do not create a guessed UF2 or claim hardware validation without a physical test.

Once the behavior is identified, record the exact mapping and make the smallest change possible on `jsm-calibration`, keeping `main` untouched.
