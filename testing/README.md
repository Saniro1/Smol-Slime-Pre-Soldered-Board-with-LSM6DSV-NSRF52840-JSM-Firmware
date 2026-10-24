# testing/ – experimental UF2 builds (Smol Slime, DualSense-emulating SlimeVR build)

Flash: double-tap reset → drag the .uf2 onto the drive. Recovery: double-tap reset and flash
`../CURRENT.UF2` (stock SlimeVR) again. The bootloader is never touched.

| file | what it is |
|---|---|
| `CURRENT_1_gyro-accel-fix16-gyro-sign-preserved.uf2` | your fix16 (gyro/accel slots swapped + axis tweaks). Works with the IMU pointing **left**. |
| `CURRENT_1_gyro-accel-fix17.uf2` | fix16 + 90° yaw re-orientation so it works with the pad held **normally** (IMU pointing at the TV). Report = `(-Gy, -Gx, -Gz)` for gyro and accel. |
| `CURRENT_1_gyro-accel-fix17-alt.uf2` | same but turned the other way (`(+Gy, -Gx, +Gz)`). Use only if fix17 has **pitch (up/down) inverted**. |

| `CURRENT_1_gyro-accel-fix18.uf2` | After testing fix17: pitch inverted, yaw dead, roll fine. Axes re-derived: pitch=Gy, yaw=Gz, roll=Gx. Report = `(+Gy, -Gz, -Gx)` for gyro and accel. |
| `CURRENT_1_gyro-accel-fix18-alt.uf2` | same axes, yaw and roll signs flipped `(+Gy, +Gz, +Gx)`. Use only if fix18 yaw (turn left/right) goes the wrong way. |
| `CURRENT_1_gyro-accel-fix19.uf2` | fix18 + HID endpoint polling interval set to 1 ms (was 0 = invalid for full-speed USB). Same axes as fix18. |

Notes
* fix16 sent `gyro=(-Gz,-Gx,+Gz)`, `accel=(+Az,-Ax,+Az)`: the sensor's Y axis was never sent and Z was sent twice.
  That is invisible while only yaw/pitch are used, but a re-orientation needs all three axes, so fix17 sends all three
  (a proper rotation) for both gyro and accel.
* Yaw (left/right) is unchanged from fix16; only pitch/roll are mixed.
* Rebuild: `python3 ../tools/make_axis_variant.py <fix16.uf2> <out.uf2> "+1,-2,-0"` (term = sign + sensor axis for report slots X,Y,Z).
* JoyShockMapper test: set `GYRO_SPACE = LOCAL` (X slot = vertical, Y slot = horizontal; the Z slot is ignored there).

## 1000 Hz
Report thread already sleeps 33 ticks of 32768 Hz (~1.007 ms) between reports; fix19 makes the USB side explicit (bInterval=1).
Sensor ODR is a runtime setting: in the serial shell run `read_config sensor_gyro_odr`, then `write_config sensor_gyro_odr 1000`,
`write_config sensor_accel_odr 1000`, `reboot` (driver rounds up to the next LSM6DSV ODR, 1920 Hz).
