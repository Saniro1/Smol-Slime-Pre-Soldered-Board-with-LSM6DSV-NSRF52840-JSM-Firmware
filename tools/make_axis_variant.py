#!/usr/bin/env python3
"""Rebuild the DualSense report axis mapping of the SlimeVR/DualSense build (based on fix16).

mapping = three terms for report slots X,Y,Z (JSL gyro X=pitch, Y=yaw, Z=roll); each term is a sign and
the sensor axis 0/1/2 (Gx,Gy,Gz) it is taken from.  The SAME mapping is applied to the accelerometer.
  fix17      "-1,-0,-2"   (fix16 + 90 deg yaw turn)       -> pitch inverted, yaw dead (measured)
  fix18      "+1,-2,-0"   (yaw on Gz, roll on Gx)
  fix18-alt  "+1,+2,+0"   (same axes, yaw/roll signs flipped)

usage: make_axis_variant.py fix16.uf2 out.uf2 "+1,-2,-0"
"""
import struct, sys
CAVE, HOOK, RET = 0xAC858, 0x97DC, 0x9828
EXPECT_HOOK = bytes.fromhex('a3f03cb8')
EXPECT_POOL = {0x9938: 0x2000510C, 0x993C: 0x20005106}

def enc_bw(src, dst):
    off = dst - (src + 4)
    s = (off >> 24) & 1; i1 = (off >> 23) & 1; i2 = (off >> 22) & 1
    j1 = (~(i1 ^ s)) & 1; j2 = (~(i2 ^ s)) & 1
    return struct.pack('<HH', 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       0x9000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF))

def cave2(mapping):
    h = lambda *w: struct.pack('<%dH' % len(w), *w)
    strb = lambda rt, off: 0x7000 | (off << 6) | (4 << 3) | rt   # strb rt,[r4,#off]
    out = b''
    for k, (neg, src) in enumerate(mapping):
        out += h(0xF9B0, 0x2000 | 2 * src, 0xF9B1, 0x3000 | 2 * src)
        out += h(0x4252 if neg else 0x4612, 0x425B if neg else 0x461B)
        out += h(strb(2, 16 + 2 * k), strb(3, 22 + 2 * k))
        out += h(0xF3C2, 0x2207, 0xF3C3, 0x2307)                      # ubfx r2/r3,#8,#8
        if k == 2:
            out += h(0xF884, 0x8008)                                  # strb.w r8,[r4,#8] (hat)
        out += h(strb(2, 17 + 2 * k), strb(3, 23 + 2 * k))
    return out

def parse(spec):
    m = []
    for t in spec.split(','):
        t = t.strip(); assert t[0] in '+-' and t[1] in '012' and len(t) == 2, t
        m.append((t[0] == '-', int(t[1])))
    assert sorted(s for _, s in m) == [0, 1, 2], 'each sensor axis exactly once'
    return m

def main(src, dst, spec):
    d = bytearray(open(src, 'rb').read())
    blocks = [(o,) + struct.unpack_from('<II', d, o + 12) for o in range(0, len(d), 512)]
    def find(a, n):
        for o, addr, size in blocks:
            if addr <= a and a + n <= addr + size: return o + 32 + (a - addr)
        sys.exit('address 0x%x not in image' % a)
    for a, v in EXPECT_POOL.items():
        if struct.unpack_from('<I', d, find(a, 4))[0] != v: sys.exit('input is not fix16/17 (pool)')
    if bytes(d[find(HOOK, 4):find(HOOK, 4) + 4]) != EXPECT_HOOK: sys.exit('input is not fix16/17 (hook)')
    code = cave2(parse(spec)); code += enc_bw(CAVE + len(code), RET)
    p = find(CAVE, len(code)); d[p:p + len(code)] = code
    open(dst, 'wb').write(d); print('mapping', spec, 'cave bytes', len(code))

if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
