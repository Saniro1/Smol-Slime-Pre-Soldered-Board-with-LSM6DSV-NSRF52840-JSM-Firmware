#!/usr/bin/env python3
"""Set the HID interrupt-IN endpoint polling interval (bInterval) to N ms (default 1) in the
DualSense-emulating SlimeVR build.  The 64-byte HID endpoint template sits at flash 0x3A783:
07 05 80 03 40 00 <bInterval>; in fix16-fix18 bInterval is 0 (invalid for full-speed).

usage: patch_binterval.py in.uf2 out.uf2 [ms]
"""
import struct, sys
ADDR, EXPECT = 0x3A783, bytes.fromhex('07058003400000')
src, dst = sys.argv[1], sys.argv[2]
ms = int(sys.argv[3]) if len(sys.argv) > 3 else 1
d = bytearray(open(src, 'rb').read())
for o in range(0, len(d), 512):
    a, n = struct.unpack_from('<II', d, o + 12)
    if a <= ADDR and ADDR + 7 <= a + n:
        p = o + 32 + ADDR - a
        if bytes(d[p:p + 7]) != EXPECT: sys.exit('unexpected descriptor bytes %s' % d[p:p + 7].hex())
        d[p + 6] = ms; open(dst, 'wb').write(d); print('bInterval ->', ms); break
else: sys.exit('descriptor not found')
