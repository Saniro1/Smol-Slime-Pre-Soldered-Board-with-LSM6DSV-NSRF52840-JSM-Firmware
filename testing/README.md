# testing/ – experimental UF2 builds (Smol Slime, DualSense-emulating SlimeVR build)

Flash: double-tap reset → drag the .uf2 onto the drive. Recovery: double-tap reset and flash
`../CURRENT.UF2` (stock SlimeVR) again. The bootloader is never touched.

| file | what it is |
|---|---|
| `CURRENT_1_gyro-accel-fix16-gyro-sign-preserved.uf2` | your fix16 (gyro/accel slots swapped + axis tweaks). Works with the IMU pointing **left**. |
| `CURRENT_1_gyro-accel-fix17.uf2` | fix16 + 90° yaw re-orientation so it works with the pad held **normally** (IMU pointing at the TV). Report = `(-Gy, -Gx, -Gz)` for gyro and accel. |
| `CURRENT_1_gyro-accel-fix17-alt.uf2` | same but turned the other way (`(+Gy, -Gx, +Gz)`). Use only if fix17 has **pitch (up/down) inverted**. |

Notes
* fix16 sent `gyro=(-Gz,-Gx,+Gz)`, `accel=(+Az,-Ax,+Az)`: the sensor's Y axis was never sent and Z was sent twice.
  That is invisible while only yaw/pitch are used, but a re-orientation needs all three axes, so fix17 sends all three
  (a proper rotation) for both gyro and accel.
* Yaw (left/right) is unchanged from fix16; only pitch/roll are mixed.
* Rebuild: `python3 ../tools/make_fix17.py <fix16.uf2> <out.uf2> P|N`.
