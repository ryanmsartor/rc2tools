import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
try:
    SPEC = importlib.util.spec_from_file_location("recompile_rom", ROOT / "bin" / "recompile_rom.py")
    recompile_rom = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(recompile_rom)
finally:
    sys.path.pop(0)


class RecompileRomTests(unittest.TestCase):
    def test_instruction_encodings_and_ranges(self):
        examples = (
            ("ld bc,$1234", 0x100, b"\x01\x34\x12"),
            ("add a, e", 0x100, b"\x83"),
            ("ldh [$ff00+$ab],a", 0x100, b"\xe0\xab"),
            ("jr $0100", 0x100, b"\x18\xfe"),
            ("jr @+2-128", 0, b"\x18\x80"),
            ("add sp,-128", 0x100, b"\xe8\x80"),
            ("ld hl,sp+127", 0x100, b"\xf8\x7f"),
            ("bit 7,a", 0x100, b"\xcb\x7f"),
            ("stop", 0x100, b"\x10\x00"),
            ("db $10, 0x42, 255", 0x100, b"\x10\x42\xff"),
        )
        for text, address, expected in examples:
            with self.subTest(text=text):
                self.assertEqual(recompile_rom.encode_instruction(text, address), expected)

        for text in ("LD A,$100", "JP $10000", "JR $0200", "ADD SP,128",
                     "LD HL,SP-129", "DB $100", "DB 1,", "NOT_AN_INSTRUCTION"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                recompile_rom.encode_instruction(text, 0x100)

    def test_sections_place_bytes_and_pad_gaps(self):
        source = (
            'SECTION "second; bank", ROMX[$4002], BANK[2] ; comment\n'
            '  DB $AA, $BB\n'
            'SECTION "first", ROM0[$0001]\n'
            '  NOP\n'
        )
        rom = recompile_rom.assemble(source)
        self.assertEqual(len(rom), 0xC000)
        self.assertEqual(rom[:2], b"\0\0")
        self.assertEqual(rom[0x8002:0x8004], b"\xaa\xbb")
        self.assertEqual(sum(rom), 0xAA + 0xBB)

    def test_errors_include_line_and_do_not_accept_invalid_sections(self):
        cases = (
            ("NOP\n", "line 1: instruction or directive outside"),
            ('SECTION "x", ROMX[$4000], BANK[0]\nDB 1', "line 1: ROMX requires"),
            ('SECTION "x", ROMX[$4000], BANK[512]\nDB 1', "line 1: ROMX requires"),
            ('SECTION "x", ROM0[$4000]\nDB 1', "line 1: ROM0 requires"),
            ('SECTION "x", ROM0[$3FFF]\nLD A,$01', "line 2: instruction or data crosses"),
            ('SECTION "x", ROM0[$0000]\nDB 1\nSECTION "y", ROM0[$0000]\nDB 2',
             "line 4: overlapping"),
            ('SECTION "x", ROM0[$0000]\nlabel:', "line 2: unsupported"),
            ('SECTION "x", ROM0[$0000]\nDB nope', "line 2: DB requires"),
        )
        for source, expected in cases:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, expected):
                recompile_rom.assemble(source)
        for source in ("", "; no data", 'SECTION "empty", ROM0[$0000]'):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "no ROM data"):
                recompile_rom.assemble(source)


if __name__ == "__main__":
    unittest.main()
