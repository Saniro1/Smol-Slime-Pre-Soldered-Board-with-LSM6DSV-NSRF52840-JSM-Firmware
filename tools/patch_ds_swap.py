#!/usr/bin/env python3
"""Fix gyro/accel slot swap in the DualSense-emulating SlimeVR build (CURRENT_1.UF2).

The HID report builder (function at 0x9770) copies two int16[3] buffers into the
DualSense input report:   bytes 16-21 <- *0x20005106   bytes 22-27 <- *0x2000510c
but the converter (0x99b8) fills 0x20005106 with ACCEL (x8192) and 0x2000510c with
GYRO (x16).  JoyShockLibrary reads gyro at 16-21 and accel at 22-27, so it was
fed gravity as angular rate.  We swap the two literal-pool words at 0x9938/0x993c.

usage: patch_ds_swap.py in.UF2 out.UF2
"""
import struct, sys

MAGIC = (0x0A324655, 0x9E5D5157, 0x0AB16F30)
PATCHES = {  # flash address -> (expected old word, new word)
    0x9938: (0x20005106, 0x2000510C),
    0x993C: (0x2000510C, 0x20005106),
}

def main(src, dst):
    d = bytearray(open(src, 'rb').read())
    done = set()
    for off in range(0, len(d), 512):
        m0, m1, flags, addr, size, bno, nblk, fam = struct.unpack_from('<8I', d, off)
        if (m0, m1) != MAGIC[:2] or struct.unpack_from('<I', d, off + 508)[0] != MAGIC[2]:
            sys.exit('bad UF2 block at %d' % off)
        for a, (old, new) in PATCHES.items():
            if addr <= a and a + 4 <= addr + size:
                p = off + 32 + (a - addr)
                cur = struct.unpack_from('<I', d, p)[0]
                if cur != old:
                    sys.exit('unexpected word 0x%x at 0x%x (expected 0x%x): wrong firmware?' % (cur, a, old))
                struct.pack_into('<I', d, p, new)
                done.add(a)
    if done != set(PATCHES):
        sys.exit('patch locations not found')
    open(dst, 'wb').write(d)
    print('patched', ', '.join(hex(a) for a in sorted(done)))

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
