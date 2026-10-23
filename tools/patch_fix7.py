#!/usr/bin/env python3
"""Generate fix7 from fix6 by swapping reported X/Z source axes, preserving the X sign correction."""
import hashlib
import struct
import sys
from pathlib import Path

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
SITE, CAVE = 0x97DC, 0xAC858
BRANCH = bytes.fromhex("a3 f0 3c b8")
FIX6 = bytes.fromhex("b0 f9 02 20 52 42 b1 f9 02 30 5b 42 5c f7 be bf")
# Output X now loads the original Z component; keep the known-good X sign correction.
FIX7 = bytes.fromhex("b0 f9 04 20 52 42 b1 f9 04 30 5b 42 5c f7 be bf")
# Z output's original gyro/accel loads change source offset 4 -> 2.
PATCHES = {
    0x980E: (bytes.fromhex("04 20"), bytes.fromhex("02 20")),
    0x9812: (bytes.fromhex("04 30"), bytes.fromhex("02 30")),
}

def parse_uf2(data):
    if not data or len(data) % 512:
        raise ValueError("UF2 size is not a multiple of 512 bytes")
    blocks = {}
    for off in range(0, len(data), 512):
        m0, m1, flags, target, size, num, total, family = struct.unpack_from("<8I", data, off)
        end = struct.unpack_from("<I", data, off + 508)[0]
        if (m0, m1, end) != (MAGIC0, MAGIC1, MAGIC_END):
            raise ValueError(f"Invalid UF2 magic at file offset {off:#x}")
        if size > 476 or 32 + size > 508:
            raise ValueError(f"Invalid UF2 payload size at file offset {off:#x}")
        if target in blocks:
            raise ValueError(f"Duplicate UF2 target address {target:#x}")
        blocks[target] = (off, size)
    return blocks

def locate(blocks, address, size):
    for target, (off, payload_size) in blocks.items():
        if target <= address and address + size <= target + payload_size:
            return off + 32 + address - target
    raise ValueError(f"UF2 is missing address range {address:#x}..{address + size:#x}")

def decode_bw_target(address, instruction):
    h1, h2 = struct.unpack("<HH", instruction)
    s = (h1 >> 10) & 1
    imm10 = h1 & 0x03ff
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    imm11 = h2 & 0x07ff
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    imm25 = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s:
        imm25 -= 1 << 25
    return address + 4 + imm25

def patch(src, dst):
    original = Path(src).read_bytes()
    blocks = parse_uf2(original)
    result = bytearray(original)
    site = locate(blocks, SITE, 4)
    cave = locate(blocks, CAVE, len(FIX7))
    if result[site:site + 4] != BRANCH:
        raise ValueError("Unexpected branch at 0x97DC; refusing to patch")
    if result[cave:cave + len(FIX6)] != FIX6:
        raise ValueError("Unexpected fix6 trampoline at 0xAC858; refusing to patch")

    result[cave:cave + len(FIX7)] = FIX7
    for address, (old, new) in PATCHES.items():
        pos = locate(blocks, address, len(old))
        if result[pos:pos + len(old)] != old:
            raise ValueError(f"Unexpected instruction bytes at {address:#x}: {result[pos:pos + len(old)].hex()}")
        result[pos:pos + len(old)] = new

    parse_uf2(result)
    if result[site:site + 4] != BRANCH:
        raise ValueError("Branch changed unexpectedly")
    if result[cave:cave + len(FIX7)] != FIX7:
        raise ValueError("Fix7 trampoline verification failed")
    if decode_bw_target(CAVE + 12, result[cave + 12:cave + 16]) != 0x97E4:
        raise ValueError("Fix7 return branch does not land at 0x97E4")
    if result[locate(blocks, 0x980C, 4):locate(blocks, 0x980C, 4) + 4] != bytes.fromhex("b0 f9 02 20"):
        raise ValueError("Z gyro source swap failed")
    if result[locate(blocks, 0x9810, 4):locate(blocks, 0x9810, 4) + 4] != bytes.fromhex("b1 f9 02 30"):
        raise ValueError("Z accelerometer source swap failed")

    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(result)
    print("Input SHA-256:", hashlib.sha256(original).hexdigest())
    print("Output SHA-256:", hashlib.sha256(result).hexdigest())
    print("UF2 size:", len(result), "bytes; blocks:", len(blocks))
    print("X-output trampoline:", result[cave:cave + len(FIX7)].hex(" "))
    print("Z-output loads:", result[locate(blocks, 0x980C, 8):locate(blocks, 0x980C, 8) + 8].hex(" "))
    print("Return target:", hex(decode_bw_target(CAVE + 12, result[cave + 12:cave + 16])))
    print("Changed byte count:", sum(a != b for a, b in zip(original, result)))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_fix7.py FIX6.UF2 FIX7.UF2")
    patch(sys.argv[1], sys.argv[2])
