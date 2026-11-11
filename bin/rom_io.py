#!/usr/bin/env python3
"""Load Rolan's Curse II ROM files, either as binaries or as hex dumps."""

import argparse
import re
from pathlib import Path

ROM_SIZE = 0x20000
BANK_SIZE = 0x4000

XXD_ROW = re.compile(
    r"^([0-9a-fA-F]{8}): ((?:[0-9a-fA-F]{4} ){7}[0-9a-fA-F]{4})  "
)
FORMAT_HEX_ROW = re.compile(
    r"^([0-9a-fA-F]{8})[ \t]+((?:[0-9a-fA-F]{2}[ \t]+){15}"
    r"[0-9a-fA-F]{2})(?:[ \t]|$)"
)
ROW_PREFIX = re.compile(r"^[0-9a-fA-F]{8}(?:[ \t]|:)")


def parse_offset(value: str) -> int:
    """Parse an offset written in decimal or with a 0x prefix."""
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid offset: {value}") from error


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
    """Return the ROM bytes from a .gb binary or .hex dump, checking size and header."""
    raw = path.read_bytes()
    rom = parse_hex_dump(raw) if path.suffix.lower() == ".hex" else raw
    if len(rom) != ROM_SIZE:
        raise ValueError(f"expected a {ROM_SIZE}-byte ROM, found {len(rom)} bytes")
    if rom[0x134:0x143] != b"ROLAN'S CURSE 2" or rom[0x147:0x149] != b"\x06\x02":
        raise ValueError("ROM header does not match Rolan's Curse II (USA), MBC2, 128 KiB")
    return rom
