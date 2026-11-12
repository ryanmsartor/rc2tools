#!/usr/bin/env python3
"""Decode an entire ROM into one long string using the documented character table."""

import argparse
import sys
from collections.abc import Iterator
from pathlib import Path

from known_graphics import KNOWN_GRAPHICS_RANGES

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROM = ROOT / "input" / "Rolan's Curse II (USA).gb"
DEFAULT_OUTPUT = ROOT / "output" / "rom-text.txt"
WRAP_WIDTH = 64

# Mirrors docs/known-text.md. Lowercase letters are used for known letters.
CHARACTER_TABLE = {
    **{0x0A + index: chr(ord("a") + index) for index in range(26)},
    0xB2: " ",
    0x24: "'",
    0x26: "-",
    0x27: ".",
    0x28: ",",
    0x29: "?",
    0x2A: "!",
    0x2B: "-",
    0x2D: ":",
    0x30: " ",
    0xFD: "+",
    0xFF: "#",
    # Hero name placeholders render as the capital word HERO.
    0xE0: "H",
    0xE1: "E",
    0xE2: "R",
    0xE3: "O",
    0xFE: " ",
}
# Unknown bytes each get their own placeholder, indexed by byte value so a byte keeps
# the same symbol if it is mapped later. Symbols avoid the 1bpp font's characters
# (digits, A-Z, and punctuation such as ? ! . : - ( ) ') and the known glyphs above.
# Pool order: ASCII symbols, Latin-1 symbols (U+00AD skipped as zero-width), then box drawing and blocks.
_UNKNOWN_POOL = (
    "^%&@*_=~[]{}<>|\\`$"
    + "".join(chr(code) for code in range(0xA1, 0x100) if code != 0xAD)
    + "".join(chr(code) for code in range(0x2500, 0x25A0))
)
UNKNOWN_GLYPHS = _UNKNOWN_POOL[:256]


def glyph_for(byte: int) -> str:
    return CHARACTER_TABLE.get(byte, UNKNOWN_GLYPHS[byte])


def render_glyphs(
    data: bytes, known_only: bool = False, omit_sprites: bool = False
) -> Iterator[str]:
    graphics_mask = bytearray(len(data))
    if omit_sprites:
        for start, end in KNOWN_GRAPHICS_RANGES:
            if start < len(data):
                length = min(end, len(data)) - start
                graphics_mask[start:start + length] = b"\x01" * length
    for address, byte in enumerate(data):
        if graphics_mask[address]:
            yield "%"
        elif known_only:
            yield CHARACTER_TABLE.get(byte, "_")
        else:
            yield glyph_for(byte)


def decode(data: bytes, known_only: bool = False, omit_sprites: bool = False) -> str:
    return "".join(render_glyphs(data, known_only, omit_sprites))


def wrap_text(data: bytes, known_only: bool = False, omit_sprites: bool = False) -> str:
    lines: list[tuple[int, str]] = []
    line_chars: list[str] = []
    line_address = 0

    for address, glyph in enumerate(render_glyphs(data, known_only, omit_sprites)):
        for character in glyph:
            if len(line_chars) == WRAP_WIDTH:
                lines.append((line_address, "".join(line_chars)))
                line_chars = []
            if not line_chars:
                line_address = address
            line_chars.append(character)

    if line_chars:
        lines.append((line_address, "".join(line_chars)))
    return "\n".join(f"0x{address:05X}: {line}" for address, line in lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wrap", action="store_true", help="wrap output every 64 characters")
    parser.add_argument(
        "--known-only",
        action="store_true",
        help="render unknown or undefined bytes as underscores",
    )
    parser.add_argument(
        "--omit-sprites",
        action="store_true",
        help="render bytes in known graphics ranges as percent signs",
    )
    parser.add_argument("rom", nargs="?", type=Path, default=DEFAULT_ROM)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = args.rom.read_bytes()
    if args.wrap:
        text = wrap_text(data, known_only=args.known_only, omit_sprites=args.omit_sprites)
    else:
        text = decode(data, known_only=args.known_only, omit_sprites=args.omit_sprites)
    args.output.write_text(text, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
