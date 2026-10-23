#!/usr/bin/env python3
"""Generate fix6 from fix4 by negating both reported gyro X and Y components.

fix4 negated Y only, and the user's latest test still indicates reversed horizontal
and vertical response. This trampoline loads X, negates it, loads Y, negates it,
then resumes after the original pair of loads at 0x97E4. Z is intentionally untouched
because the observed symptoms do not establish that Z's sign is wrong.
"""
import hashlib
import struct
import sys
from pathlib import Path

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
SITE, CAVE = 0x97DC, 0xAC858
BRANCH_TO_CAVE = bytes.fromhex("a3 f0 3c b8")
FIX4_TRAMPOLINE = bytes.fromhex("b0 f9 02 20 b1 f9 02 30 5b 42 5c f7 bf bf")
FIX6_TRAMPOLINE = bytes.fromhex("b0 f9 02 20 52 42 b1 f9 02 30 5b 42 5c f7 be bf")
RETURN_ADDRESS = 0x97E4

def parse(data):
    if len(data) % 512:
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
    offset = imm25 - (1 << 25) if s else imm25
    return address + 4 + offset

def main(src, dst):
    original = Path(src).read_bytes()
    blocks = parse(original)
    site = locate(blocks, SITE, 4)
    cave = locate(blocks, CAVE, len(FIX6_TRAMPOLINE))
    if original[site:site + 4] != BRANCH_TO_CAVE:
        raise ValueError("Unexpected branch at 0x97DC; refusing to patch")
    if original[cave:cave + len(FIX4_TRAMPOLINE)] != FIX4_TRAMPOLINE:
        raise ValueError("Unexpected fix4 trampoline at 0xAC858; refusing to patch")

    result = bytearray(original)
    result[cave:cave + len(FIX6_TRAMPOLINE)] = FIX6_TRAMPOLINE
    parsed = parse(result)
    if result[site:site + 4] != BRANCH_TO_CAVE:
        raise ValueError("Branch changed unexpectedly")
    if result[cave:cave + len(FIX6_TRAMPOLINE)] != FIX6_TRAMPOLINE:
        raise ValueError("Fix6 trampoline verification failed")
    if decode_bw_target(CAVE + 12, result[cave + 12:cave + 16]) != RETURN_ADDRESS:
        raise ValueError("Fix6 return branch does not land at 0x97E4")
    if len(parsed) != len(blocks):
        raise ValueError("UF2 block count changed unexpectedly")

    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(result)
    print("Input SHA-256:", hashlib.sha256(original).hexdigest())
    print("Output SHA-256:", hashlib.sha256(result).hexdigest())
    print("UF2 size:", len(result), "bytes")
    print("Trampoline at 0xAC858:", result[cave:cave + len(FIX6_TRAMPOLINE)].hex(" "))
    print("Return target:", hex(decode_bw_target(CAVE + 12, result[cave + 12:cave + 16])))
    print("Changed bytes:", sum(a != b for a, b in zip(original, result)))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_fix6.py FIX4.UF2 FIX6.UF2")
    main(sys.argv[1], sys.argv[2])
