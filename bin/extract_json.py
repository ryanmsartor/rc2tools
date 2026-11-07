#!/usr/bin/env python3
"""Extract documented character tables from a ROM or its hex dump."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROM_SIZE = 0x20000
LEVELS = 16
CHARACTERS = ("hero", "pit", "lane", "kyle", "jude", "lee", "lora", "zold")

# Offsets and record fields are documented in docs/rom-map.md.
ABILITIES = {
    "hero": (
        ("a", 0x15449, ("damage",)),
        ("b", 0x15459, ("cost", "range", "damage")),
    ),
    "pit": (
        ("dagger", 0x154AD, ("range", "damage")),
        ("boomerang", 0x154DF, ("range", "damage")),
        ("bomb", 0x15511, ("cost", "damage", "unknown")),
    ),
    "lane": (
        ("a", 0x15709, ("damage",)),
        ("shield", 0x15719, ("cost", "unknown")),
        ("healing", 0x15799, ("cost", "unknown_1", "unknown_2")),
    ),
    "kyle": (
        ("a", 0x157C9, ("damage",)),
        ("play_dead", 0x157D9, ("cost", "unknown")),
        ("rod", 0x15898, ("cost", "damage")),
    ),
    "jude": (
        ("weak_a", 0x159B2, ("range", "damage")),
        ("strong_a", 0x159E4, ("range", "damage")),
        ("quake", 0x15A16, ("cost", "damage")),
    ),
    "lee": (
        ("a", 0x15B97, ("damage",)),
        ("rapidfire", 0x15BA7, ("cost", "damage")),
        ("firework", 0x15BC7, ("cost", "damage", "range")),
    ),
    "lora": (
        ("a", 0x15C34, ("range", "damage")),
        ("heal", 0x15C66, ("cost", "unknown_1", "unknown_2")),
        ("wing", 0x15C96, ("cost",)),
    ),
    "zold": (
        ("a", 0x15CB6, ("range", "damage")),
        ("b", 0x15CE8, ("cost", "damage")),
    ),
}

ADDITIONAL_TABLES = {
    "zold_a_damage": (0x15CA6, LEVELS, 1),
    "lookup_0x17165": (0x17165, 8, 2),
    "lookup_0x17175": (0x17175, 8, 2),
}

XXD_ROW = re.compile(
    r"^([0-9a-fA-F]{8}): ((?:[0-9a-fA-F]{4} ){7}[0-9a-fA-F]{4})  "
)
FORMAT_HEX_ROW = re.compile(
    r"^([0-9a-fA-F]{8})[ \t]+((?:[0-9a-fA-F]{2}[ \t]+){15}"
    r"[0-9a-fA-F]{2})(?:[ \t]|$)"
)
ROW_PREFIX = re.compile(r"^[0-9a-fA-F]{8}(?:[ \t]|:)")


def parse_hex_dump(raw: bytes) -> bytes:
    """Parse contiguous, full-width xxd or PowerShell Format-Hex rows."""
    encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    text = raw.decode(encoding)
    data = bytearray()
    for line_number, line in enumerate(text.split("\n"), 1):
        match = XXD_ROW.match(line) or FORMAT_HEX_ROW.match(line)
        if match:
            offset = int(match.group(1), 16)
            if offset != len(data):
                raise ValueError(
                    f"hex dump line {line_number}: expected offset "
                    f"0x{len(data):08X}, found 0x{offset:08X}"
                )
            data.extend(bytes.fromhex(match.group(2)))
        elif ROW_PREFIX.match(line):
            raise ValueError(f"invalid hex dump row at line {line_number}")
    if not data:
        raise ValueError("hex dump contains no recognizable rows")
    return bytes(data)


def read_rom(path: Path) -> bytes:
    raw = path.read_bytes()
    rom = parse_hex_dump(raw) if path.suffix.lower() == ".hex" else raw
    if len(rom) != ROM_SIZE:
        raise ValueError(f"expected a {ROM_SIZE}-byte ROM, found {len(rom)} bytes")
    if rom[0x134:0x143] != b"ROLAN'S CURSE 2" or rom[0x147:0x149] != b"\x06\x02":
        raise ValueError("ROM header does not match Rolan's Curse II (USA), MBC2, 128 KiB")
    return rom


def extract_json(rom: bytes) -> dict:
    """Read each mapped record directly from ROM, in level order."""
    characters = {}
    for index, name in enumerate(CHARACTERS):
        hp_start = 0x17065 + index * LEVELS
        mp_start = 0x170E5 + index * LEVELS
        character = {
            "hp": list(rom[hp_start:hp_start + LEVELS]),
            "mp": list(rom[mp_start:mp_start + LEVELS]),
            "abilities": {},
        }
        for ability, offset, fields in ABILITIES[name]:
            width = len(fields)
            character["abilities"][ability] = {
                field: [rom[offset + level * width + column] for level in range(LEVELS)]
                for column, field in enumerate(fields)
            }
        characters[name] = character
    additional_tables = {}
    for name, (offset, entries, width) in ADDITIONAL_TABLES.items():
        if width == 1:
            additional_tables[name] = list(rom[offset:offset + entries])
        else:
            additional_tables[name] = [
                list(rom[offset + index * width:offset + (index + 1) * width])
                for index in range(entries)
            ]
    return {"characters": characters, "additional_tables": additional_tables}


def output_path(root: Path, rom: bytes) -> Path:
    """Return the output path named by the source ROM's SHA-256."""
    digest = hashlib.sha256(rom).hexdigest()
    return root / "output" / f"{digest}.json"


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=root / "input" / "Rolan's Curse II (USA).gb",
        help="ROM (.gb) or full xxd/Format-Hex dump (.hex)",
    )
    args = parser.parse_args()
    try:
        rom = read_rom(args.input)
        game = extract_json(rom)
        output = output_path(root, rom)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(game, indent=2) + "\n", encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
