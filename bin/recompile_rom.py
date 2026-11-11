#!/usr/bin/env python3
"""Assemble the LR35902 listing format produced by decompile_rom.py."""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

from decompile_rom import DEFAULT_ROM, ILLEGAL_OPCODES, decode_instruction
from rom_io import BANK_SIZE

ROOT = Path(__file__).resolve().parent.parent
MAX_BANKS = 512
NUMBER = r"(?:\$[0-9A-F]+|0X[0-9A-F]+|[0-9]+)"
SIGNED_NUMBER = rf"[+-]?{NUMBER}"
JR_TARGET = rf"(?:{NUMBER}|@\+2[+-]{NUMBER})"
SECTION = re.compile(
    rf'^SECTION\s+"[^"]+"\s*,\s*(ROM0|ROMX)\s*\[\s*({NUMBER})\s*\]'
    rf'(?:\s*,\s*BANK\s*\[\s*({NUMBER})\s*\])?\s*$',
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    """Normalize whitespace without joining a mnemonic to its first operand."""
    parts = text.upper().strip().split(None, 1)
    if len(parts) == 1:
        return parts[0]
    return parts[0] + " " + re.sub(r"\s+", "", parts[1])


def number(text: str) -> int:
    sign = 1
    if text.startswith(("+", "-")):
        if text[0] == "-":
            sign = -1
        text = text[1:]
    if text.startswith("$"):
        return sign * int(text[1:], 16)
    if text.startswith("0X"):
        return sign * int(text[2:], 16)
    return sign * int(text, 10)


def instruction_tables() -> tuple[dict[str, bytes], list[tuple[re.Pattern, int, str]]]:
    """Derive encodings from the disassembler's single opcode definition."""
    fixed = {}
    variable = []
    for opcode in range(256):
        if opcode in ILLEGAL_OPCODES:
            continue
        if opcode == 0x10:
            fixed["STOP"] = bytes((opcode, 0))
            continue
        if opcode == 0xCB:
            for extended in range(256):
                text, _ = decode_instruction(bytes((opcode, extended)), 0, 0x100)
                fixed[normalize(text)] = bytes((opcode, extended))
            continue
        text, size = decode_instruction(bytes((opcode, 0x12, 0x34)), 0, 0x100)
        if size == 1:
            fixed[normalize(text)] = bytes((opcode,))
        else:
            if size == 3:
                marker, operand, kind = "$3412", NUMBER, "word"
            elif opcode in (0x18, 0x20, 0x28, 0x30, 0x38):
                marker, operand, kind = "$0114", JR_TARGET, "relative"
            elif opcode in (0xE8, 0xF8):
                marker = "+18" if opcode == 0xF8 else "18"
                operand, kind = SIGNED_NUMBER, "signed"
                if opcode == 0xF8:
                    operand = rf"[+-]{NUMBER}"
            else:
                marker, operand, kind = "$12", NUMBER, "byte"
            text = normalize(text)
            before, after = text.split(marker)
            pattern = re.compile(re.escape(before) + f"({operand})" + re.escape(after) + r"\Z")
            variable.append((pattern, opcode, kind))
    return fixed, variable


FIXED, VARIABLE = instruction_tables()


def encode_instruction(text: str, address: int) -> bytes:
    text = normalize(text)
    if text.startswith("DB "):
        items = text[3:].split(",")
        if not items or any(not re.fullmatch(NUMBER, item) for item in items):
            raise ValueError("DB requires comma-separated byte values")
        values = [number(item) for item in items]
        if any(value > 0xFF for value in values):
            raise ValueError("DB value out of byte range")
        return bytes(values)
    if text in FIXED:
        return FIXED[text]
    for pattern, opcode, kind in VARIABLE:
        match = pattern.fullmatch(text)
        if not match:
            continue
        operand = match.group(1)
        if kind == "relative" and operand.startswith("@+2"):
            value = number(operand[3:])
        else:
            value = number(operand)
            if kind == "relative":
                value -= address + 2
        if kind in ("relative", "signed"):
            if not -128 <= value <= 127:
                raise ValueError("signed operand or relative jump is outside -128..127")
            return bytes((opcode, value & 0xFF))
        limit = 0xFFFF if kind == "word" else 0xFF
        if not 0 <= value <= limit:
            raise ValueError(f"{kind} operand out of range")
        return bytes((opcode, value & 0xFF, value >> 8)) if kind == "word" else bytes((opcode, value))
    raise ValueError(f"unsupported instruction or directive: {text}")


def assemble(source: str) -> bytes:
    """Assemble fixed-address ROM sections and pad gaps and final banks with zero."""
    rom = bytearray()
    occupied = bytearray()
    cursor = None
    bank_end = 0
    seen_section = False
    for line_number, line in enumerate(source.splitlines(), 1):
        # A semicolon inside a quoted section name is not a comment.
        line = re.split(r';(?=(?:[^"]*"[^"]*")*[^"]*$)', line, maxsplit=1)[0].strip()
        if not line:
            continue
        try:
            if line.upper().startswith("SECTION"):
                match = SECTION.fullmatch(line)
                if not match:
                    raise ValueError("expected SECTION with a fixed ROM address and bank")
                kind, address_text, bank_text = match.groups()
                kind = kind.upper()
                address = number(address_text.upper())
                bank = number(bank_text.upper()) if bank_text else 0
                if kind == "ROM0":
                    if bank_text is not None or not 0 <= address < BANK_SIZE:
                        raise ValueError("ROM0 requires an address in $0000..$3FFF and no bank")
                elif bank_text is None or not 1 <= bank < MAX_BANKS or not 0x4000 <= address < 0x8000:
                    raise ValueError("ROMX requires an address in $4000..$7FFF and bank 1..511")
                cursor = bank * BANK_SIZE + address - (BANK_SIZE if bank else 0)
                bank_end = (bank + 1) * BANK_SIZE
                seen_section = True
                continue
            if cursor is None:
                raise ValueError("instruction or directive outside a section")
            address = cursor if cursor < BANK_SIZE else BANK_SIZE + cursor % BANK_SIZE
            encoded = encode_instruction(line, address)
            end = cursor + len(encoded)
            if end > bank_end:
                raise ValueError("instruction or data crosses a ROM bank boundary")
            if end > len(rom):
                rom.extend(bytes(end - len(rom)))
                occupied.extend(bytes(end - len(occupied)))
            if any(occupied[cursor:end]):
                raise ValueError("overlapping ROM sections")
            rom[cursor:end] = encoded
            occupied[cursor:end] = b"\x01" * len(encoded)
            cursor = end
        except ValueError as error:
            raise ValueError(f"line {line_number}: {error}") from error
    if not seen_section or not rom:
        raise ValueError("assembly contains no ROM data")
    padded_size = max(2 * BANK_SIZE, (len(rom) + BANK_SIZE - 1) // BANK_SIZE * BANK_SIZE)
    rom.extend(bytes(padded_size - len(rom)))
    return bytes(rom)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", nargs="?", type=Path, default=DEFAULT_ROM.with_suffix(".asm"),
        help="assembly filename in input/, or path to an assembly file (default: ROM basename)",
    )
    args = parser.parse_args(argv)
    source = args.input if args.input.parent != Path(".") else ROOT / "input" / args.input
    output = ROOT / "output" / f"{source.stem} (recompiled).gb"
    try:
        if source.suffix.lower() != ".asm":
            raise ValueError("input must be an .asm file")
        if not source.is_file():
            raise FileNotFoundError(f"assembly file not found: {source}")
        rom = assemble(source.read_text(encoding="utf-8"))
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".rc2t-recompile-", dir=output.parent) as directory:
            temporary_output = Path(directory) / "rom.gb"
            temporary_output.write_bytes(rom)
            os.replace(temporary_output, output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
