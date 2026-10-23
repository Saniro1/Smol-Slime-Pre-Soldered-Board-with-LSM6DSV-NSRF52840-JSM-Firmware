#!/usr/bin/env python3
"""Swap X/Y sensor components in the tested DualSense-emulating UF2.

This preserves the Step 2 gyro/accelerometer report-slot fix. It swaps the first
two signed 16-bit components for BOTH gyro and accelerometer in the HID report
builder. Z is unchanged. Addresses are absolute flash addresses from the
verified disassembly (the application image starts at 0x1000).

Usage:
  python tools/patch_ds_xy_swap.py build/CURRENT_1_gyro-accel-fix.UF2 build/CURRENT_1_gyro-accel-fix2.UF2
"""
import hashlib
import struct
import sys
from pathlib import Path

UF2_MAGIC0 = 0x0A324655
UF2_MAGIC1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30

# Absolute flash address of the second halfword in each Thumb-2 LDRSH.W:
# gyro X load [r0,#0] -> [r0,#2]; gyro Y load [r0,#2] -> [r0,#0]
# accel X load [r1,#0] -> [r1,#2]; accel Y load [r1,#2] -> [r1,#0]
PATCHES = {
    0x97DE: (0x2000, 0x2002),
    0x97F6: (0x2002, 0x2000),
    0x97E2: (0x3000, 0x3002),
    0x97FA: (0x3002, 0x3000),
}


def validate_uf2(data):
    if not data or len(data) % 512:
        raise ValueError("Input is not a complete UF2 file (size must be a multiple of 512).")
    blocks = {}
    for offset in range(0, len(data), 512):
        m0, m1, flags, target, size, block_no, total, family = struct.unpack_from("<8I", data, offset)
        end_magic = struct.unpack_from("<I", data, offset + 508)[0]
        if (m0, m1, end_magic) != (UF2_MAGIC0, UF2_MAGIC1, UF2_MAGIC_END):
            raise ValueError(f"Invalid UF2 magic in block at file offset {offset}.")
        if size > 476 or 32 + size > 508:
            raise ValueError(f"Invalid UF2 payload size in block at file offset {offset}.")
        if target in blocks:
            raise ValueError(f"Duplicate UF2 target address 0x{target:x}.")
        blocks[target] = (offset, size)
    return blocks


def patch(input_path, output_path):
    original = bytearray(Path(input_path).read_bytes())
    blocks = validate_uf2(original)
    result = bytearray(original)
    applied = []
    for address, (expected, replacement) in PATCHES.items():
        match = None
        for target, (block_offset, size) in blocks.items():
            if target <= address and address + 2 <= target + size:
                match = (target, block_offset)
                break
        if match is None:
            raise ValueError(f"Patch address 0x{address:x} was not present in UF2 payloads.")
        target, block_offset = match
        file_offset = block_offset + 32 + (address - target)
        actual = struct.unpack_from("<H", result, file_offset)[0]
        if actual != expected:
            raise ValueError(
                f"Unexpected instruction halfword 0x{actual:04x} at 0x{address:x}; "
                f"expected 0x{expected:04x}. Refusing to patch a different firmware."
            )
        struct.pack_into("<H", result, file_offset, replacement)
        applied.append((file_offset, address, expected, replacement))

    validate_uf2(result)
    differences = [i for i, (a, b) in enumerate(zip(original, result)) if a != b]
    expected_differences = sorted(item[0] + j for item in applied for j in range(2)
                                  if original[item[0] + j] != result[item[0] + j])
    if differences != expected_differences:
        raise ValueError("Unexpected bytes changed; refusing to write output.")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(result)
    print(f"Input SHA-256:  {hashlib.sha256(original).hexdigest()}")
    print(f"Output SHA-256: {hashlib.sha256(result).hexdigest()}")
    print(f"UF2 size:       {len(result)} bytes")
    print("Applied axis-swap patches:")
    for _, address, old, new in applied:
        print(f"  0x{address:04X}: 0x{old:04X} -> 0x{new:04X}")
    print(f"Changed byte count: {len(differences)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    patch(sys.argv[1], sys.argv[2])
