#!/usr/bin/env python3
"""Read documented character stat tables from a ROM or its hex dump."""

import re
from pathlib import Path

ROM_SIZE = 0x20000
LEVELS = 16
VALUE_WIDTH = 3
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


def read_stats(rom: bytes) -> list[tuple[str, list[int]]]:
    """Return (name, values) for each stat array, with LEVELS values per array."""
    stats = []
    for index, name in enumerate(CHARACTERS):
        hp_start = 0x17065 + index * LEVELS
        mp_start = 0x170E5 + index * LEVELS
        stats.append((f"{name}_hp", list(rom[hp_start:hp_start + LEVELS])))
        stats.append((f"{name}_mp", list(rom[mp_start:mp_start + LEVELS])))
        for ability, offset, fields in ABILITIES[name]:
            width = len(fields)
            for column, field in enumerate(fields):
                values = [rom[offset + level * width + column] for level in range(LEVELS)]
                stats.append((f"{name}_{ability}_{field}", values))
    for name, (offset, entries, width) in ADDITIONAL_TABLES.items():
        stats.append((f"{name}_table", list(rom[offset:offset + entries * width])))
    return stats


def format_stats(stats: list[tuple[str, list[int]]]) -> str:
    """Format arrays as `name: [v1, ...]`, aligning colons and right-aligning values."""
    name_width = max(len(name) for name, _ in stats)
    lines = []
    for name, values in stats:
        cells = ", ".join(f"{value:>{VALUE_WIDTH}}" for value in values)
        lines.append(f"{name:<{name_width}}: [{cells}]")
    return "\n".join(lines) + "\n"
