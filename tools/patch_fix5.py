#!/usr/bin/env python3
"""Create fix5 by negating only gyro X in fix4, leaving the original Y load unchanged."""
import hashlib
import struct
import sys
from pathlib import Path

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
SITE, CAVE = 0x97DC, 0xAC858
BRANCH = bytes.fromhex("a3 f0 3c b8")
FIX4_TRAMPOLINE = bytes.fromhex("b0 f9 02 20 b1 f9 02 30 5b 42 5c f7 bf bf")
FIX5_TRAMPOLINE = bytes.fromhex("b0 f9 02 20 52 42 5c f7 bf bf")
CAVE_SIZE = len(FIX4_TRAMPOLINE)

def parse(data):
    if len(data) % 512:
        raise ValueError("UF2 size is not a multiple of 512 bytes")
    blocks = {}
    for off in range(0, len(data), 512):
        m0, m1, flags, target, size, num, total, family = struct.unpack_from("<8I", data, off)
        end = struct.unpack_from("<I", data, off + 508)[0]
        if (m0, m1, end) != (MAGIC0, MAGIC1, MAGIC_END):
            raise ValueError(f"Invalid UF2 magic at offset {off:#x}")
        if size > 476 or 32 + size > 508:
            raise ValueError(f"Invalid UF2 payload size at offset {off:#x}")
        if target in blocks:
            raise ValueError(f"Duplicate UF2 target address {target:#x}")
        blocks[target] = (off, size)
    return blocks

def locate(blocks, address, size):
    for target, (off, payload_size) in blocks.items():
        if target <= address and address + size <= target + payload_size:
            return off + 32 + address - target
    raise ValueError(f"UF2 is missing address range {address:#x}..{address+size:#x}")

def main(src, dst):
    original = Path(src).read_bytes()
    blocks = parse(original)
    site = locate(blocks, SITE, len(BRANCH))
    cave = locate(blocks, CAVE, CAVE_SIZE)
    if original[site:site+4] != BRANCH:
        raise ValueError("Unexpected branch at 0x97DC; refusing to patch")
    if original[cave:cave+CAVE_SIZE] != FIX4_TRAMPOLINE:
        raise ValueError("Unexpected fix4 trampoline at 0xAC858; refusing to patch")
    result = bytearray(original)
    result[cave:cave+CAVE_SIZE] = FIX5_TRAMPOLINE + b"\\xff" * (CAVE_SIZE-len(FIX5_TRAMPOLINE))
    parse(result)
    if result[site:site+4] != BRANCH:
        raise ValueError("Branch changed unexpectedly")
    if result[cave:cave+len(FIX5_TRAMPOLINE)] != FIX5_TRAMPOLINE:
        raise ValueError("Fix5 trampoline verification failed")
    if result[cave+len(FIX5_TRAMPOLINE):cave+CAVE_SIZE] != b"\\xff" * (CAVE_SIZE-len(FIX5_TRAMPOLINE)):
        raise ValueError("Unused code-cave bytes are not erased")
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(result)
    print("Input SHA-256:", hashlib.sha256(original).hexdigest())
    print("Output SHA-256:", hashlib.sha256(result).hexdigest())
    print("UF2 size:", len(result), "bytes")
    print("Trampoline at 0xAC858:", result[cave:cave+CAVE_SIZE].hex(" "))
    print("Changed bytes:", sum(a != b for a, b in zip(original, result)))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_fix5.py FIX4.UF2 FIX5.UF2")
    main(sys.argv[1], sys.argv[2])
