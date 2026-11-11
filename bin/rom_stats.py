#!/usr/bin/env python3
"""Read and update documented character stat tables in a ROM."""

import re

LEVELS = 16
VALUE_WIDTH = 3
CHARACTERS = ("hero", "pit", "lane", "kyle", "jude", "lee", "lora", "zold")

# Offsets and record fields are documented in docs/rom-map.md.
ABILITIES = {
    "hero": (
        ("sabre", 0x15449, ("damage",)),
        ("electricball", 0x15459, ("cost", "range", "damage")),
    ),
    "pit": (
        ("dagger", 0x154AD, ("range", "damage")),
        ("boomerang", 0x154DF, ("range", "damage")),
        ("bomb", 0x15511, ("cost", "damage", "unknown")),
    ),
    "lane": (
        ("staff", 0x15709, ("damage",)),
        ("shield", 0x15719, ("cost", "unknown")),
        ("healing", 0x15799, ("cost", "unknown_1", "unknown_2")),
    ),
    "kyle": (
        ("bone", 0x157C9, ("damage",)),
        ("playdead", 0x157D9, ("cost", "unknown")),
        ("thunder", 0x15898, ("cost", "damage")),
    ),
    "jude": (
        ("fireball", 0x159B2, ("range", "damage")),
        ("smashball", 0x159E4, ("range", "damage")),
        ("quake", 0x15A16, ("cost", "damage")),
    ),
    "lee": (
        ("sai", 0x15B97, ("damage",)),
        ("rapidfire", 0x15BA7, ("cost", "damage")),
        ("firework", 0x15BC7, ("cost", "damage", "range")),
    ),
    "lora": (
        ("arrow", 0x15C34, ("range", "damage")),
        ("heal", 0x15C66, ("cost", "unknown_1", "unknown_2")),
        ("wing", 0x15C96, ("cost",)),
    ),
    "zold": (
        ("darkblade", 0x15CB6, ("range", "damage")),
        ("megaball", 0x15CE8, ("cost", "damage")),
    ),
}

ADDITIONAL_TABLES = {
    "zold_specialblade_damage": (0x15CA6, LEVELS, 1),
    "lookup_0x17165_table": (0x17165, 8, 2),
    "lookup_0x17175_table": (0x17175, 8, 2),
}


def stat_offsets() -> dict[str, tuple[int, ...]]:
    """Return the ROM byte offsets for every documented stat array."""
    offsets = {}
    for index, name in enumerate(CHARACTERS):
        hp_start = 0x17065 + index * LEVELS
        mp_start = 0x170E5 + index * LEVELS
        offsets[f"{name}_hp"] = tuple(range(hp_start, hp_start + LEVELS))
        offsets[f"{name}_mp"] = tuple(range(mp_start, mp_start + LEVELS))
        for ability, offset, fields in ABILITIES[name]:
            width = len(fields)
            for column, field in enumerate(fields):
                offsets[f"{name}_{ability}_{field}"] = tuple(
                    offset + level * width + column for level in range(LEVELS)
                )
    for name, (offset, entries, width) in ADDITIONAL_TABLES.items():
        offsets[name] = tuple(range(offset, offset + entries * width))
    return offsets


def read_stats(rom: bytes | bytearray) -> list[tuple[str, list[int]]]:
    """Return (name, values) for each stat array, with LEVELS values per array."""
    return [(name, [rom[offset] for offset in offsets]) for name, offsets in stat_offsets().items()]


def parse_stats(text: str) -> tuple[dict[str, list[int]], list[str]]:
    """Parse known arrays and return them along with unrecognized array names."""
    offsets = stat_offsets()
    stats = {}
    unknown = []
    entry = re.compile(r"\s*([A-Za-z_][A-Za-z_0-9]*)\s*:\s*\[([^\[\]]*)\]")
    position = 0
    while position < len(text):
        if not text[position:].strip():
            break
        match = entry.match(text, position)
        if match is None:
            line = text.count("\n", 0, position) + 1
            raise ValueError(f"invalid stats entry near line {line}")
        name, contents = match.groups()
        position = match.end()
        if name not in offsets:
            unknown.append(name)
            continue
        if name in stats:
            raise ValueError(f"duplicate stats array: {name}")
        cells = contents.split(",")
        if len(cells) != len(offsets[name]) or any(
            not re.fullmatch(r"[0-9]+", cell.strip(), flags=re.ASCII) for cell in cells
        ):
            raise ValueError(f"{name} must contain {len(offsets[name])} decimal byte values")
        values = [int(cell.strip()) for cell in cells]
        if any(value > 255 for value in values):
            raise ValueError(f"{name} contains a value outside 0-255")
        stats[name] = values
    return stats, unknown


def apply_stats(rom: bytearray, stats: dict[str, list[int]]) -> None:
    """Validate and write stat arrays to their corresponding ROM offsets."""
    offsets = stat_offsets()
    for name, values in stats.items():
        if name not in offsets:
            raise ValueError(f"unknown stat array: {name}")
        if len(values) != len(offsets[name]) or any(not 0 <= value <= 255 for value in values):
            raise ValueError(f"{name} must contain {len(offsets[name])} byte values")
        if offsets[name][-1] >= len(rom):
            raise ValueError(f"ROM does not contain complete {name} stat data")
    for name, values in stats.items():
        for offset, value in zip(offsets[name], values):
            rom[offset] = value


def format_stats(stats: list[tuple[str, list[int]]]) -> str:
    """Format arrays as `name: [v1, ...]`, aligning colons and right-aligning values."""
    name_width = max(len(name) for name, _ in stats)
    lines = []
    for name, values in stats:
        cells = ", ".join(f"{value:>{VALUE_WIDTH}}" for value in values)
        lines.append(f"{name:<{name_width}}: [{cells}]")
    return "\n".join(lines) + "\n"
