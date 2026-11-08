#!/usr/bin/env python3
"""Create an IPS patch swapping two characters' standard sprites."""

import argparse
import sys
from pathlib import Path

from extract_json import read_rom

ROOT = Path(__file__).resolve().parent.parent
ROM_PATH = ROOT / "input" / "Rolan's Curse II (USA).gb"
SPRITE_BYTES = 64
STANDARD_SPRITE_BYTES = 9 * SPRITE_BYTES
IPS_HEADER = b"PATCH"
IPS_EOF = b"EOF"

# Standard pose start, defeated sprite, and level-up face offsets.
CHARACTER_SPRITES = {
    "hero": (0x9106, 0x95C6, 0x860E),
    "pit": (0x9606, 0x9A06, 0x864E),
    "lane": (0x9A46, 0x9D86, 0x868E),
    "kyle": (0x9DC6, 0xA206, 0x86CE),
    "jude": (0xA306, 0xA786, 0x870E),
    "lee": (0xA7C6, 0xAC86, 0x874E),
    "lora": (0xACC6, 0xB0A6, 0x878E),
    "zold": (0xB0E6, 0xB526, 0x87CE),
}


def build_swap_artifacts(
    rom: bytes,
    character1: str,
    character2: str,
) -> tuple[bytes, bytes]:
    """Build an IPS patch and patched ROM for the requested character swap."""
    if character1 not in CHARACTER_SPRITES:
        raise ValueError(f"unknown character: {character1}")
    if character2 not in CHARACTER_SPRITES:
        raise ValueError(f"unknown character: {character2}")
    if character1 == character2:
        raise ValueError("characters must be different")

    first = CHARACTER_SPRITES[character1]
    second = CHARACTER_SPRITES[character2]
    segments = (
        (first[0], second[0], STANDARD_SPRITE_BYTES),
        (first[1], second[1], SPRITE_BYTES),
        (first[2], second[2], SPRITE_BYTES),
    )
    records = []
    for first_offset, second_offset, size in segments:
        first_data = rom[first_offset:first_offset + size]
        second_data = rom[second_offset:second_offset + size]
        if len(first_data) != size or len(second_data) != size:
            raise ValueError("ROM does not contain complete sprite data")
        records.extend(((first_offset, second_data), (second_offset, first_data)))

    patch = bytearray(IPS_HEADER)
    patched_rom = bytearray(rom)
    for offset, data in sorted(records):
        if offset > 0xFFFFFF or not data or len(data) > 0xFFFF:
            raise ValueError("sprite data cannot be represented in an IPS record")
        patch.extend(offset.to_bytes(3, "big"))
        patch.extend(len(data).to_bytes(2, "big"))
        patch.extend(data)
        patched_rom[offset:offset + len(data)] = data
    patch.extend(IPS_EOF)
    return bytes(patch), bytes(patched_rom)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "character1",
        type=str.lower,
        choices=tuple(CHARACTER_SPRITES),
        help="first character to swap",
    )
    parser.add_argument(
        "character2",
        type=str.lower,
        choices=tuple(CHARACTER_SPRITES),
        help="second character to swap",
    )
    args = parser.parse_args()
    if args.character1 == args.character2:
        parser.error("characters must be different")

    output_base = ROOT / "output" / f"swap-{args.character1}-{args.character2}-sprites"
    patch_output = output_base.with_suffix(".ips")
    rom_output = output_base.with_suffix(".gb")
    try:
        rom = read_rom(ROM_PATH)
        patch, patched_rom = build_swap_artifacts(rom, args.character1, args.character2)
        patch_output.parent.mkdir(parents=True, exist_ok=True)
        patch_output.write_bytes(patch)
        rom_output.write_bytes(patched_rom)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {patch_output}")
    print(f"Wrote {rom_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
