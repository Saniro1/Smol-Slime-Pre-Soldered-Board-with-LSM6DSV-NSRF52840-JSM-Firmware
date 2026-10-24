#!/usr/bin/env python3
"""Build CURRENT_1_gyro-accel-fix17 from the fix16 UF2 (IMU turned 90 degrees about the vertical axis).

Input must be 'CURRENT_1_gyro-accel-fix16-gyro-sign-preserved.uf2' (gyro/accel slot swap already applied).

fix16 sends   gyro = (-Gz, -Gx, +Gz)   accel = (+Az, -Ax, +Az)   (Gy / Ay never used, Gz duplicated).
Worked out so that it behaves correctly when the IMU points LEFT.  Holding the pad normally the IMU
points at the TV, i.e. the sensor is yawed 90 deg.  Re-expressing the (fully repaired, proper-rotation)
fix16 frame (-Gz,-Gx,+Gy) after a -90/+90 deg turn about the yaw axis gives
    variant P (fix17)     : out = (-Gy, -Gx, -Gz)   for gyro AND accel
    variant N (fix17-alt) : out = (+Gy, -Gx, +Gz)   for gyro AND accel
(P and N differ by 180 deg about yaw: pitch and roll are negated.)  Yaw channel (-Gx) is unchanged.

The report-builder block at 0x97DC..0x9827 is replaced by a branch to a cave at 0xAC858 (free flash,
same place fix16 used) that stores the six int16 values at report bytes 16-27 and returns to 0x9828.

usage: make_fix17.py in.uf2 out.uf2 P|N
"""
import struct, sys

CAVE = 0xAC858
HOOK, RET = 0x97DC, 0x9828
CODE = {
 'P': bytes.fromhex('b0f90220b1f9023052425b422274a375c2f30722c3f307236274e375b0f90020b1f9003052425b42a2742376c2f30722c3f30723e2746376b0f90420b1f9043052425b422275a376c2f30722c3f3072384f808806275e376'),
 'N': bytes.fromhex('b0f90220b1f9023012461b462274a375c2f30722c3f307236274e375b0f90020b1f9003052425b42a2742376c2f30722c3f30723e2746376b0f90420b1f9043012461b462275a376c2f30722c3f3072384f808806275e376'),
}
EXPECT_HOOK = bytes.fromhex('a3f03cb8')           # fix16: b.w 0xac858
EXPECT_POOL = {0x9938: 0x2000510C, 0x993C: 0x20005106}   # swap from step 2

def enc_bw(src, dst):                              # Thumb-2 B.W (T4)
    off = dst - (src + 4)
    s = (off >> 24) & 1
    i1 = (off >> 23) & 1; i2 = (off >> 22) & 1
    j1 = (~(i1 ^ s)) & 1; j2 = (~(i2 ^ s)) & 1
    h = 0xF000 | (s << 10) | ((off >> 12) & 0x3FF)
    l = 0x9000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF)
    return struct.pack('<HH', h, l)

def main(src, dst, var):
    d = bytearray(open(src, 'rb').read())
    blocks = []
    for off in range(0, len(d), 512):
        addr, size = struct.unpack_from('<II', d, off + 12)
        blocks.append((off, addr, size))
    def find(a, n):
        for off, addr, size in blocks:
            if addr <= a and a + n <= addr + size:
                return off + 32 + (a - addr)
        sys.exit('address 0x%x not in image' % a)
    for a, v in EXPECT_POOL.items():
        if struct.unpack_from('<I', d, find(a, 4))[0] != v:
            sys.exit('input is not the fix16 file (pool word 0x%x)' % a)
    if bytes(d[find(HOOK, 4):find(HOOK, 4) + 4]) != EXPECT_HOOK:
        sys.exit('input is not the fix16 file (hook)')
    code = CODE[var] + enc_bw(CAVE + len(CODE[var]), RET)
    p = find(CAVE, len(code))
    d[p:p + len(code)] = code
    # clear the 2nd old fix16 cave (0xAC870) tail that is now overwritten/unused: leave as-is (dead data)
    h = find(HOOK, 4)
    d[h:h + 4] = enc_bw(HOOK, CAVE)
    open(dst, 'wb').write(d)
    print('variant', var, 'cave bytes', len(code))

if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[3] not in 'PN': sys.exit(__doc__)
    main(*sys.argv[1:])
