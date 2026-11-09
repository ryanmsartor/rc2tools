#!/usr/bin/env python3
"""Decode an entire ROM into one long string using the documented character table."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROM = ROOT / "input" / "Rolan's Curse II (USA).gb"
DEFAULT_OUTPUT = ROOT / "output" / "rom-text.txt"

# Mirrors docs/known-text.md. Lowercase letters are used for known letters.
CHARACTER_TABLE = {
    **{0x0A + index: chr(ord("a") + index) for index in range(26)},
    0xB2: " ",
    0x24: "'",
    0x27: ".",
    0x28: ",",
    0x2A: "!",
    0x2B: "-",
    0xFD: "+",
    0xFF: "#",
    # Hero name placeholders render as the capital word HERO.
    0xE0: "H",
    0xE1: "E",
    0xE2: "R",
    0xE3: "O",
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


def decode(data: bytes) -> str:
    return "".join(glyph_for(byte) for byte in data)


def main(argv: list[str]) -> int:
    rom_path = Path(argv[0]) if len(argv) > 0 else DEFAULT_ROM
    output_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    if len(argv) > 2:
        print("Usage: render_text.py [rom [output]]", file=sys.stderr)
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(decode(rom_path.read_bytes()), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
