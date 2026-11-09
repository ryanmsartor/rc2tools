import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("decompile_rom", ROOT / "bin" / "decompile_rom.py")
decompile_rom = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decompile_rom)


class DecompileRomTests(unittest.TestCase):
    def test_decodes_immediates_and_relative_targets(self):
        cases = (
            (bytes([0x01, 0x34, 0x12]), 0x100, ("LD BC,$1234", 3)),
            (bytes([0x18, 0xFE]), 0x100, ("JR $0100", 2)),
            (bytes([0xC6, 0xA5]), 0x200, ("ADD A,$A5", 2)),
            (bytes([0x83]), 0x200, ("ADD A,E", 1)),
            (bytes([0x99]), 0x200, ("SBC A,C", 1)),
            (bytes([0xE8, 0xFE]), 0x200, ("ADD SP,-2", 2)),
            (bytes([0xF8, 0xFE]), 0x200, ("LD HL,SP-2", 2)),
            (bytes([0xF8, 0x02]), 0x200, ("LD HL,SP+2", 2)),
            (bytes([0x18, 0x80]), 0, ("JR @+2-128", 2)),
            (bytes([0xCB, 0x7F]), 0x300, ("BIT 7,A", 2)),
            (bytes([0x22]), 0x400, ("LD [HLI],A", 1)),
            (bytes([0x32]), 0x500, ("LD [HLD],A", 1)),
            (bytes([0xE9]), 0x600, ("JP HL", 1)),
        )
        for data, address, expected in cases:
            with self.subTest(data=data):
                self.assertEqual(decompile_rom.decode_instruction(data, 0, address), expected)

    def test_decodes_all_opcodes_and_reports_correct_sizes(self):
        illegal = decompile_rom.ILLEGAL_OPCODES
        two_byte = {
            0x06, 0x0E, 0x10, 0x16, 0x18, 0x1E, 0x20, 0x26, 0x28, 0x2E,
            0x30, 0x36, 0x38, 0x3E, 0xC6, 0xCE, 0xD6, 0xDE, 0xE0, 0xE6,
            0xE8, 0xEE, 0xF0, 0xF6, 0xF8, 0xFE,
        }
        three_byte = {
            0x01, 0x08, 0x11, 0x21, 0x31, 0xC2, 0xC3, 0xC4, 0xCA, 0xCC,
            0xCD, 0xD2, 0xD4, 0xDA, 0xDC, 0xEA, 0xFA,
        }
        for opcode in range(256):
            with self.subTest(opcode=opcode):
                instruction, size = decompile_rom.decode_instruction(
                    bytes([opcode, 0, 0]), 0, 0x100
                )
                expected_size = (
                    1 if opcode in illegal else
                    2 if opcode == 0xCB or opcode in two_byte else
                    3 if opcode in three_byte else
                    1
                )
                self.assertEqual(size, expected_size)
                if opcode not in illegal:
                    self.assertFalse(instruction.startswith("DB"))

    def test_stop_padding_and_truncated_operands_preserve_bytes(self):
        self.assertEqual(decompile_rom.decode_instruction(bytes([0x10, 0]), 0, 0), ("STOP", 2))
        self.assertEqual(
            decompile_rom.decode_instruction(bytes([0x10, 0x42]), 0, 0),
            ("DB $10,$42", 2),
        )
        self.assertEqual(decompile_rom.decode_instruction(bytes([0xC3]), 0, 0), ("DB $C3", 1))

    def test_splits_sections_at_physical_rom_bank_boundaries(self):
        rom = bytearray(0x4003)
        rom[0x3FFF] = 0x00
        rom[0x4000:0x4003] = bytes([0x01, 0x34, 0x12])
        listing = decompile_rom.disassemble(rom, 0x3FFF)
        self.assertIn('SECTION "ROM bank 00", ROM0[$3FFF]', listing)
        self.assertIn('SECTION "ROM bank 01", ROMX[$4000], BANK[1]', listing)
        self.assertIn("; 004000: 01 34 12\n    LD BC,$1234", listing)

    def test_invalid_ranges_are_rejected(self):
        for start, end in ((-1, 1), (4, None), (0, 0), (0, 5)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ValueError):
                    decompile_rom.disassemble(b"\x00" * 4, start, end)

    def test_main_writes_assembly_to_the_requested_path(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "game.gb"
            output = Path(directory) / "out" / "game.asm"
            rom.write_bytes(bytes([0x00, 0xC3, 0x34, 0x12]))
            self.assertEqual(
                decompile_rom.main([str(rom), str(output), "--start", "0x1", "--end", "0x4"]),
                0,
            )
            self.assertIn("JP $1234", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
