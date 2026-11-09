#!/usr/bin/env python3
"""Linear-sweep disassembler for Game Boy (LR35902) ROMs."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROM = ROOT / "input" / "Rolan's Curse II (USA).gb"
BANK_SIZE = 0x4000

REGISTERS = ("B", "C", "D", "E", "H", "L", "[HL]", "A")
STACK_REGISTERS = ("BC", "DE", "HL", "AF")
CONDITIONS = ("NZ", "Z", "NC", "C")
ALU_OPERATIONS = ("ADD A", "ADC A", "SUB", "SBC A", "AND", "XOR", "OR", "CP")

BASE_OPCODES = (
    "NOP", "LD BC,d16", "LD [BC],A", "INC BC", "INC B", "DEC B", "LD B,d8", "RLCA",
    "LD [a16],SP", "ADD HL,BC", "LD A,[BC]", "DEC BC", "INC C", "DEC C", "LD C,d8", "RRCA",
    "STOP", "LD DE,d16", "LD [DE],A", "INC DE", "INC D", "DEC D", "LD D,d8", "RLA",
    "JR r8", "ADD HL,DE", "LD A,[DE]", "DEC DE", "INC E", "DEC E", "LD E,d8", "RRA",
    "JR NZ,r8", "LD HL,d16", "LD [HLI],A", "INC HL", "INC H", "DEC H", "LD H,d8", "DAA",
    "JR Z,r8", "ADD HL,HL", "LD A,[HLI]", "DEC HL", "INC L", "DEC L", "LD L,d8", "CPL",
    "JR NC,r8", "LD SP,d16", "LD [HLD],A", "INC SP", "INC [HL]", "DEC [HL]", "LD [HL],d8", "SCF",
    "JR C,r8", "ADD HL,SP", "LD A,[HLD]", "DEC SP", "INC A", "DEC A", "LD A,d8", "CCF",
)

HIGH_OPCODES = {
    0xC0: "RET NZ", 0xC1: "POP BC", 0xC2: "JP NZ,a16", 0xC3: "JP a16",
    0xC4: "CALL NZ,a16", 0xC5: "PUSH BC", 0xC6: "ADD A,d8", 0xC7: "RST $00",
    0xC8: "RET Z", 0xC9: "RET", 0xCA: "JP Z,a16", 0xCC: "CALL Z,a16",
    0xCD: "CALL a16", 0xCE: "ADC A,d8", 0xCF: "RST $08",
    0xD0: "RET NC", 0xD1: "POP DE", 0xD2: "JP NC,a16", 0xD4: "CALL NC,a16",
    0xD5: "PUSH DE", 0xD6: "SUB d8", 0xD7: "RST $10", 0xD8: "RET C",
    0xD9: "RETI", 0xDA: "JP C,a16", 0xDC: "CALL C,a16", 0xDE: "SBC A,d8",
    0xDF: "RST $18",
    0xE0: "LDH [$FF00+d8],A", 0xE1: "POP HL", 0xE2: "LDH [$FF00+C],A",
    0xE5: "PUSH HL", 0xE6: "AND d8", 0xE7: "RST $20", 0xE8: "ADD SP,r8",
    0xE9: "JP HL", 0xEA: "LD [a16],A", 0xEE: "XOR d8", 0xEF: "RST $28",
    0xF0: "LDH A,[$FF00+d8]", 0xF1: "POP AF", 0xF2: "LDH A,[$FF00+C]",
    0xF3: "DI", 0xF5: "PUSH AF", 0xF6: "OR d8", 0xF7: "RST $30",
    0xF8: "LD HL,SP+r8", 0xF9: "LD SP,HL", 0xFA: "LD A,[a16]", 0xFB: "EI",
    0xFE: "CP d8", 0xFF: "RST $38",
}

ILLEGAL_OPCODES = {0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD}


def decode_instruction(data: bytes, offset: int, address: int) -> tuple[str, int]:
    """Return one instruction's text and size; emit DB for invalid/truncated opcodes."""
    opcode = data[offset]
    if opcode in ILLEGAL_OPCODES:
        return f"DB ${opcode:02X}", 1

    if opcode < 0x40:
        template = BASE_OPCODES[opcode]
    elif opcode < 0x80:
        if opcode == 0x76:
            template = "HALT"
        else:
            destination, source = divmod(opcode - 0x40, 8)
            template = f"LD {REGISTERS[destination]},{REGISTERS[source]}"
    elif opcode < 0xC0:
        operation, operand = divmod(opcode - 0x80, 8)
        separator = "," if operation in (0, 1, 3) else " "
        template = f"{ALU_OPERATIONS[operation]}{separator}{REGISTERS[operand]}"
    else:
        template = HIGH_OPCODES.get(opcode)
        if template is None and opcode & 0xC7 == 0xC0:
            template = f"RET {CONDITIONS[(opcode >> 3) & 3]}"
        elif template is None and opcode & 0xCF == 0xC1:
            template = f"POP {STACK_REGISTERS[(opcode >> 4) & 3]}"
        elif template is None and opcode & 0xC7 == 0xC2:
            template = f"JP {CONDITIONS[(opcode >> 3) & 3]},a16"
        elif template is None and opcode & 0xCF == 0xC5:
            template = f"PUSH {STACK_REGISTERS[(opcode >> 4) & 3]}"
        elif template is None and opcode & 0xC7 == 0xC4:
            template = f"CALL {CONDITIONS[(opcode >> 3) & 3]},a16"
        elif template is None and opcode & 0xC7 == 0xC6:
            template = f"{ALU_OPERATIONS[(opcode >> 3) & 7]} d8"

    if opcode == 0xCB:
        if offset + 1 >= len(data):
            return f"DB ${opcode:02X}", 1
        extended = data[offset + 1]
        group = extended >> 6
        operation = (extended >> 3) & 7
        if group == 0:
            template = f"{('RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SWAP', 'SRL')[operation]} {REGISTERS[extended & 7]}"
        elif group == 1:
            template = f"BIT {operation},{REGISTERS[extended & 7]}"
        elif group == 2:
            template = f"RES {operation},{REGISTERS[extended & 7]}"
        else:
            template = f"SET {operation},{REGISTERS[extended & 7]}"
        return template, 2

    if opcode == 0x10:
        if offset + 1 >= len(data):
            return f"DB ${opcode:02X}", 1
        if data[offset + 1] != 0:
            return f"DB ${opcode:02X},${data[offset + 1]:02X}", 2
        return "STOP", 2

    if template is None:
        return f"DB ${opcode:02X}", 1

    size = 1 + ("d8" in template or "r8" in template) + 2 * ("d16" in template or "a16" in template)
    if offset + size > len(data):
        return f"DB ${opcode:02X}", 1

    if "a16" in template or "d16" in template:
        value = data[offset + 1] | data[offset + 2] << 8
        rendered = f"${value:04X}"
        template = template.replace("a16", rendered).replace("d16", rendered)
    if "r8" in template:
        displacement = data[offset + 1]
        if displacement >= 0x80:
            displacement -= 0x100
        if opcode in (0xE8, 0xF8):
            if opcode == 0xF8:
                template = template.replace("+r8", f"{displacement:+d}")
            else:
                template = template.replace("r8", str(displacement))
        else:
            target = address + 2 + displacement
            if not 0 <= target <= 0xFFFF:
                template = template.replace("r8", f"@+2{displacement:+d}")
            else:
                template = template.replace("r8", f"${target:04X}")
    if "d8" in template:
        template = template.replace("d8", f"${data[offset + 1]:02X}")
    return template, size


def disassemble(rom: bytes, start: int = 0, end: int | None = None) -> str:
    """Create a bank-aware RGBDS-style assembly listing for a ROM byte range."""
    if end is None:
        end = len(rom)
    if not rom:
        raise ValueError("ROM is empty")
    if start < 0 or start >= len(rom):
        raise ValueError(f"start offset must be between 0 and 0x{len(rom) - 1:X}")
    if end <= start or end > len(rom):
        raise ValueError(f"end offset must be greater than start and at most 0x{len(rom):X}")

    lines = [
        "; Generated by rc2tools. Linear sweep: embedded data may be decoded as instructions.",
        "; Reassemble with rc2t recompile to reproduce the decoded bytes.",
    ]
    cursor = start
    while cursor < end:
        bank = cursor // BANK_SIZE
        bank_end = min(end, (bank + 1) * BANK_SIZE)
        bank_start = bank * BANK_SIZE
        cpu_base = 0 if bank == 0 else 0x4000
        cpu_start = cpu_base + cursor - bank_start
        section_name = f"ROM bank {bank:02X}"
        if bank == 0:
            lines.append(f'\nSECTION "{section_name}", ROM0[${cpu_start:04X}]')
        else:
            lines.append(f'\nSECTION "{section_name}", ROMX[${cpu_start:04X}], BANK[{bank}]')

        bank_data = rom[bank_start:bank_end]
        while cursor < bank_end:
            relative = cursor - bank_start
            address = cpu_base + relative
            instruction, size = decode_instruction(bank_data, relative, address)
            raw_bytes = " ".join(f"{byte:02X}" for byte in bank_data[relative:relative + size])
            lines.append(f"; {cursor:06X}: {raw_bytes}")
            lines.append(f"    {instruction}")
            cursor += size
    return "\n".join(lines) + "\n"


def parse_offset(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid offset: {value}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_ROM, help="Game Boy ROM")
    parser.add_argument("output", nargs="?", type=Path, help="assembly output path")
    parser.add_argument("--start", type=parse_offset, default=0, help="physical ROM start offset (default: 0)")
    parser.add_argument("--end", type=parse_offset, help="exclusive physical ROM end offset (default: end of ROM)")
    args = parser.parse_args(argv)
    output_path = args.output or ROOT / "output" / f"{args.input.stem}.asm"
    try:
        output = disassemble(args.input.read_bytes(), args.start, args.end)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8", newline="\n")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
