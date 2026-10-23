#!/usr/bin/env python3
"""Preserve the tested fix3 as an inverted reference and make fix4 reverse both observed directions.

fix4 is based on corrected fix3. It replaces the X-negating trampoline with one that
loads both signed gyro values, leaves X un-negated, negates Y, and resumes at 0x97E4.
This reverses both reported directions relative to fix3 while keeping the axis mapping.
"""
import hashlib
import struct
import sys
from pathlib import Path

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
SITE, CAVE = 0x97DC, 0xAC858
BRANCH = bytes.fromhex("a3 f0 3c b8")
OLD_TRAMPOLINE = bytes.fromhex("b0 f9 02 20 52 42 5c f7 bf bf")
NEW_TRAMPOLINE = bytes.fromhex("b0 f9 02 20 b1 f9 02 30 5b 42 5c f7 bf bf")

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
            raise ValueError(f"Invalid UF2 payload size at {off:#x}")
        if target in blocks:
            raise ValueError(f"Duplicate UF2 target address {target:#x}")
        blocks[target] = (off, size)
    return blocks

def locate(blocks, address, size):
    for target, (off, payload_size) in blocks.items():
        if target <= address and address + size <= target + payload_size:
            return off + 32 + address - target
    raise ValueError(f"UF2 does not contain address range {address:#x}..{address+size:#x}")

def main(src, inverted_path, fix4_path):
    original = Path(src).read_bytes()
    blocks = parse(original)
    site_off = locate(blocks, SITE, 4)
    cave_off = locate(blocks, CAVE, len(NEW_TRAMPOLINE))
    if original[site_off:site_off+4] != BRANCH:
        raise ValueError("Unexpected branch at 0x97DC; refusing to patch")
    if original[cave_off:cave_off+len(OLD_TRAMPOLINE)] != OLD_TRAMPOLINE:
        raise ValueError("Unexpected fix3 trampoline at 0xAC858; refusing to patch")
    if original[cave_off+len(OLD_TRAMPOLINE):cave_off+len(NEW_TRAMPOLINE)] != b"\xff" * (len(NEW_TRAMPOLINE)-len(OLD_TRAMPOLINE)):
        raise ValueError("Unexpected bytes after fix3 trampoline; refusing to patch")

    Path(inverted_path).parent.mkdir(parents=True, exist_ok=True)
    Path(inverted_path).write_bytes(original)

    result = bytearray(original)
    result[cave_off:cave_off+len(NEW_TRAMPOLINE)] = NEW_TRAMPOLINE
    parse(result)
    if result[site_off:site_off+4] != BRANCH:
        raise ValueError("Branch changed unexpectedly")
    Path(fix4_path).parent.mkdir(parents=True, exist_ok=True)
    Path(fix4_path).write_bytes(result)

    print("Preserved fix3-Inverted SHA-256:", hashlib.sha256(original).hexdigest())
    print("Generated fix4 SHA-256:", hashlib.sha256(result).hexdigest())
    print("UF2 size:", len(result), "bytes")
    print("Branch at 0x97DC:", result[site_off:site_off+4].hex(" "))
    print("fix4 trampoline at 0xAC858:", result[cave_off:cave_off+len(NEW_TRAMPOLINE)].hex(" "))
    print("Changed bytes versus fix3:", sum(a != b for a, b in zip(original, result)))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: patch_both_signs.py FIX3.UF2 FIX3-INVERTED.UF2 FIX4.UF2")
    main(*sys.argv[1:])
