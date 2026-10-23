#!/usr/bin/env python3
"""Invert only the horizontal gyro X component in the tested fix2 UF2.

At 0x97DC, the report builder loads swapped gyro X from [r0,#2]. Replace
that instruction with a Thumb-2 branch to erased-flash code at 0xAC858. The
trampoline reloads the same signed value, negates it, then returns to 0x97E0.
The patch is tied to exact fix2 bytes and refuses unexpected inputs.
"""
import hashlib, struct, sys
from pathlib import Path

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
SITE = 0x97DC
CAVE = 0xAC858
EXPECTED_SITE = bytes.fromhex('b0 f9 02 20')
BRANCH_TO_CAVE = bytes.fromhex('f0 a3 b8 3c')
TRAMPOLINE = bytes.fromhex('b0 f9 02 20 52 42 5c f7 bf bf')
EXPECTED_CAVE = b'\xff' * len(TRAMPOLINE)

def parse(data):
    if len(data) % 512:
        raise ValueError('Input size is not a multiple of 512 bytes.')
    blocks = {}
    for off in range(0, len(data), 512):
        m0,m1,flags,target,size,num,total,family = struct.unpack_from('<8I', data, off)
        end = struct.unpack_from('<I', data, off+508)[0]
        if (m0,m1,end) != (MAGIC0,MAGIC1,MAGIC_END):
            raise ValueError(f'Bad UF2 magic at file offset {off}.')
        if size > 476 or 32+size > 508:
            raise ValueError(f'Bad payload size at file offset {off}.')
        if target in blocks:
            raise ValueError(f'Duplicate UF2 target 0x{target:x}.')
        blocks[target] = (off,size)
    return blocks

def locate(blocks, address, size):
    for target,(off,n) in blocks.items():
        if target <= address and address+size <= target+n:
            return off+32+(address-target)
    raise ValueError(f'Address range 0x{address:x}..0x{address+size:x} missing from UF2 payloads.')

def patch(src,dst):
    original=bytearray(Path(src).read_bytes()); blocks=parse(original); result=bytearray(original)
    site=locate(blocks,SITE,len(EXPECTED_SITE)); cave=locate(blocks,CAVE,len(TRAMPOLINE))
    actual=bytes(original[site:site+4]); actual_cave=bytes(original[cave:cave+len(TRAMPOLINE)])
    if actual != EXPECTED_SITE:
        raise ValueError(f'Unexpected site bytes {actual.hex()} at 0x{SITE:x}; refusing to patch.')
    if actual_cave != EXPECTED_CAVE:
        raise ValueError(f'Code cave 0x{CAVE:x} is not erased flash; refusing to overwrite.')
    result[site:site+4]=BRANCH_TO_CAVE
    result[cave:cave+len(TRAMPOLINE)]=TRAMPOLINE
    parse(result)
    diffs=[i for i,(a,b) in enumerate(zip(original,result)) if a!=b]
    expected=set(range(site,site+4)) | set(range(cave,cave+len(TRAMPOLINE)))
    if set(diffs)!=expected:
        raise ValueError(f'Unexpected changed byte locations: {len(set(diffs)^expected)} mismatch(es).')
    Path(dst).parent.mkdir(parents=True,exist_ok=True); Path(dst).write_bytes(result)
    print('Input SHA-256: ',hashlib.sha256(original).hexdigest())
    print('Output SHA-256:',hashlib.sha256(result).hexdigest())
    print('UF2 size:',len(result),'bytes; changed bytes:',len(diffs))
    print(f'0x{SITE:05X}: {actual.hex(" ")} -> {BRANCH_TO_CAVE.hex(" ")}')
    print(f'0x{CAVE:05X}: erased flash -> {TRAMPOLINE.hex(" ")}')

if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('Usage: patch_x_sign.py INPUT_FIX2.UF2 OUTPUT_FIX3.UF2')
    patch(sys.argv[1],sys.argv[2])
