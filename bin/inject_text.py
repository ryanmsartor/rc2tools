#!/usr/bin/env python3
"""Inject edited documented text ranges into a ROM."""

import argparse
import re
import sys
from functools import cache
from pathlib import Path

from dump_text import DUMP_GLYPHS, TEXT_RANGES, TITLE_RANGE, dump_text as dump_documented_text
from render_text import CHARACTER_TABLE, DEFAULT_ROM, UNKNOWN_GLYPHS, glyph_for
from rom_io import read_rom

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEXT_PATH = ROOT / "working" / "strings.txt"
DEFAULT_OUTPUT = ROOT / "working" / "injected.gb"
SPACE_30_RANGES = ((0x13D60, 0x13D74), (0x13D88, 0x13D9C))
LINE_PATTERN = re.compile(r"^0x([0-9A-Fa-f]{5})-0x([0-9A-Fa-f]{5}) : (.*)$")


def _dump_glyph(byte: int, title: bool = False) -> str:
    if title and 0x20 <= byte <= 0x7E:
        return chr(byte)
    return DUMP_GLYPHS.get(byte, glyph_for(byte))


def _glyph_to_byte() -> dict[str, int]:
    mapping = {
        DUMP_GLYPHS.get(byte, glyph): byte
        for byte, glyph in CHARACTER_TABLE.items()
        if byte not in (0x30, 0xFF)
    }
    mapping[" "] = 0xB2
    for byte, glyph in enumerate(UNKNOWN_GLYPHS):
        if byte not in CHARACTER_TABLE:
            mapping.setdefault(glyph, byte)
    return mapping


GLYPH_TO_BYTE = _glyph_to_byte()
EXPECTED_RANGES = tuple(sorted((TITLE_RANGE, *TEXT_RANGES)))


@cache
def allowed_characters() -> frozenset[str]:
    """Return characters emitted by dumping the base input ROM."""
    base_rom = read_rom(DEFAULT_ROM)
    lines = dump_documented_text(base_rom).splitlines()
    return frozenset(
        character
        for line in lines
        if not line.startswith(f"0x{TITLE_RANGE[0]:05X}-0x{TITLE_RANGE[1]:05X} : ")
        for character in line.partition(" : ")[2]
    )


def _format_allowed_characters(characters: frozenset[str]) -> str:
    return repr("".join(sorted(characters)))


def _parse_segments(text: str) -> dict[tuple[int, int], str]:
    segments: dict[tuple[int, int], str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        match = LINE_PATTERN.fullmatch(line)
        if match is None:
            raise ValueError(f"strings line {line_number}: expected an addressed text segment")
        start, end = (int(match.group(index), 16) for index in (1, 2))
        segment = (start, end)
        if segment not in EXPECTED_RANGES:
            raise ValueError(
                f"strings line {line_number}: unknown text range "
                f"0x{start:05X}-0x{end:05X}"
            )
        if segment in segments:
            raise ValueError(
                f"strings line {line_number}: duplicate text range "
                f"0x{start:05X}-0x{end:05X}"
            )
        segments[segment] = match.group(3)

    return segments


def _encode_segment(
    rom: bytes,
    segment: tuple[int, int],
    text: str,
) -> bytes:
    start, end = segment
    title = segment == TITLE_RANGE
    output = bytearray()
    for index, character in enumerate(text):
        original = rom[start + index]
        if character == _dump_glyph(original, title):
            output.append(original)
        elif title and 0x20 <= ord(character) <= 0x7E:
            output.append(ord(character))
        elif character == " " and segment in SPACE_30_RANGES:
            output.append(0x30)
        elif character in GLYPH_TO_BYTE:
            output.append(GLYPH_TO_BYTE[character])
        else:
            raise ValueError(
                f"range 0x{start:05X}-0x{end:05X}: "
                f"character {character!r} cannot be encoded"
            )

    if len(output) < end - start:
        padding = 0x20 if title else 0x30 if segment in SPACE_30_RANGES else 0xB2
        output.extend(bytes([padding]) * (end - start - len(output)))
    return bytes(output)


def inject_text(rom: bytes, text: str) -> bytes:
    """Return a ROM with all documented text ranges replaced from the dump."""
    if len(rom) < max(end for _, end in EXPECTED_RANGES):
        raise ValueError("ROM is too short to contain the documented text ranges")

    segments = _parse_segments(text)
    for (start, end), value in segments.items():
        attempted = len(value)
        maximum = end - start
        if attempted > maximum:
            raise ValueError(
                f"range 0x{start:05X}-0x{end:05X} exceeds maximum length "
                f"of {maximum} characters (attempted {attempted} characters)"
            )

    missing = [segment for segment in EXPECTED_RANGES if segment not in segments]
    if missing:
        start, end = missing[0]
        raise ValueError(f"strings file is missing range 0x{start:05X}-0x{end:05X}")

    allowed = allowed_characters()
    allowed_display = _format_allowed_characters(allowed)
    for (start, end), value in segments.items():
        if (start, end) == TITLE_RANGE:
            continue
        invalid = next((character for character in value if character not in allowed), None)
        if invalid is not None:
            raise ValueError(
                f"range 0x{start:05X}-0x{end:05X}: invalid character {invalid!r}; "
                f"allowed characters: {allowed_display}"
            )

    modified = bytearray(rom)
    for segment in EXPECTED_RANGES:
        start, end = segment
        modified[start:end] = _encode_segment(rom, segment, segments[segment])

    _update_checksums(modified)
    return bytes(modified)


def _update_checksums(rom: bytearray) -> None:
    header_checksum = 0
    for byte in rom[0x134:0x14D]:
        header_checksum = (header_checksum - byte - 1) & 0xFF
    rom[0x14D] = header_checksum

    global_checksum = sum(rom[:0x14E]) + sum(rom[0x150:])
    rom[0x14E:0x150] = (global_checksum & 0xFFFF).to_bytes(2, "big")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_ROM,
        help="source ROM or full .hex dump",
    )
    args = parser.parse_args(argv)
    try:
        source = read_rom(args.input)
        text = DEFAULT_TEXT_PATH.read_text(encoding="utf-8")
        result = inject_text(source, text)
        DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_OUTPUT.write_bytes(result)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {DEFAULT_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
