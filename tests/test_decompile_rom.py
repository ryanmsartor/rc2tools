import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
try:
    SPEC = importlib.util.spec_from_file_location("decompile_rom", ROOT / "bin" / "decompile_rom.py")
    decompile_rom = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(decompile_rom)
finally:
    sys.path.pop(0)


class DecompileRomTests(unittest.TestCase):
    @staticmethod
    def target_rom():
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
        return rom

    def test_sprite_registry_matches_documented_character_and_item_ranges(self):
        documentation = (ROOT / "docs" / "rom-map.md").read_text(encoding="utf-8")
        blocks = {(start, end) for start, end, _ in decompile_rom.SPRITE_BLOCKS}
        for heading, next_heading in (
            ("### Hero animation, weapon, and spell sprites", "### Numeric and HUD glyph tiles"),
            ("### Stockable inventory item sprites", "### Stacked 1bpp glyph tiles"),
            ("### Healing item and energy sprites", "### Ending credits text"),
        ):
            section = documentation.split(heading, 1)[1].split(next_heading, 1)[0]
            ranges = re.findall(r"^\| `0x([0-9A-F]+)-0x([0-9A-F]+)` \|", section, re.M)
            self.assertTrue(ranges)
            for first, last in ranges:
                with self.subTest(first=first, last=last):
                    self.assertIn((int(first, 16), int(last, 16) + 1), blocks)

    def test_all_sprite_blocks_are_annotated_at_their_boundaries(self):
        rom = self.target_rom()
        for start, end, label in decompile_rom.SPRITE_BLOCKS:
            with self.subTest(start=start, label=label):
                self.assertLess(start, end)
                listing = decompile_rom.disassemble(rom, start, start + 1)
                self.assertIn(f"; Sprite: {label} [0x{start:06X}, 0x{end:06X})", listing)
                listing = decompile_rom.disassemble(rom, end - 1, end)
                self.assertIn(f"; Sprite: {label} [0x{start:06X}, 0x{end:06X})", listing)
                self.assertIn("continued from before selected range", listing)

    def test_sprite_annotations_require_matching_header_and_size(self):
        rom = self.target_rom()
        self.assertIn("Hero UI icon: sword", decompile_rom.disassemble(rom, 0x804E, 0x804F))
        for offset in (0x134, 0x147, 0x148):
            modified = rom.copy()
            modified[offset] ^= 1
            with self.subTest(offset=offset):
                self.assertNotIn("; Sprite:", decompile_rom.disassemble(modified, 0x804E, 0x804F))
        self.assertNotIn("; Sprite:", decompile_rom.disassemble(rom[:-1], 0x804E, 0x804F))

    def test_sprite_boundary_inside_instruction_and_partial_range(self):
        rom = self.target_rom()
        rom[0x808D:0x8090] = b"\xc3\x00\x00"
        listing = decompile_rom.disassemble(rom, 0x808D, 0x8090)
        self.assertIn("Hero UI icon: sword", listing)
        self.assertIn("continued from before selected range", listing)
        self.assertIn("Hero UI icon: Magic Ball [0x00808E, 0x0080CE); starts within instruction at 0x00808D", listing)
        self.assertIn("; 00808D: C3 00 00\n    JP $0000", listing)
        self.assertNotIn("Hero UI icon: Magic Ball", decompile_rom.disassemble(rom, 0x808C, 0x808E))
        self.assertNotIn("Hero UI icon: sword", decompile_rom.disassemble(rom, 0x808E, 0x808F))

    def test_overlapping_blocks_and_bank_boundaries(self):
        rom = self.target_rom()
        blocks = ((0x3FFE, 0x4002, "first"), (0x3FFF, 0x4001, "second"))
        with patch.object(decompile_rom, "SPRITE_BLOCKS", blocks):
            listing = decompile_rom.disassemble(rom, 0x3FFF, 0x4002)
        self.assertEqual(listing.count("; Sprite: first"), 1)
        self.assertEqual(listing.count("; Sprite: second"), 1)
        self.assertIn('SECTION "ROM bank 01", ROMX[$4000], BANK[1]', listing)

    def test_all_other_annotations_are_emitted_and_exclusive(self):
        rom = self.target_rom()
        for start, end, category, label in decompile_rom.ROM_ANNOTATIONS:
            with self.subTest(start=start, category=category, label=label):
                self.assertLess(start, end)
                expected = f"; {category}: {label} [0x{start:06X}, 0x{end:06X})"
                self.assertIn(expected, decompile_rom.disassemble(rom, start, start + 1))
                self.assertIn(expected, decompile_rom.disassemble(rom, end - 1, end))
                if end < len(rom):
                    self.assertNotIn(expected, decompile_rom.disassemble(rom, end, end + 1))

    def test_additional_annotations_cover_documented_tables_and_text(self):
        import dump_text
        import extract_json

        annotations = decompile_rom.ROM_ANNOTATIONS
        text_ranges = {(start, end) for start, end, category, label in annotations
                       if category == "Text" or label == "Unclassified control-byte fragment; not confirmed text"}
        self.assertEqual(text_ranges, {dump_text.TITLE_RANGE, *dump_text.TEXT_RANGES})
        table_ranges = {(start, end) for start, end, category, _ in annotations if category == "Table"}
        for abilities in extract_json.ABILITIES.values():
            for _, start, fields in abilities:
                self.assertIn((start, start + extract_json.LEVELS * len(fields)), table_ranges)
        for start, count, width in extract_json.ADDITIONAL_TABLES.values():
            self.assertIn((start, start + count * width), table_ranges)
        self.assertEqual(len([a for a in annotations if a[2] == "Table"]), 16 + 22 + 3)

    def test_other_annotations_are_gated_and_overlap_sprite_blocks(self):
        rom = self.target_rom()
        listing = decompile_rom.disassemble(rom, 0xB886, 0xB887)
        self.assertIn("; Sprite: Stockable Large Potions", listing)
        self.assertIn("; Graphics: Presumed graphics descriptor source range", listing)
        rom[0x147] = 0
        self.assertNotIn("; Graphics:", decompile_rom.disassemble(rom, 0xB886, 0xB887))
        self.assertNotIn("; Text:", decompile_rom.disassemble(rom, 0x1C0C0, 0x1C0C1))
        self.assertNotIn("; Table:", decompile_rom.disassemble(rom, 0x15449, 0x1544A))

    def test_documented_graphics_tiles_are_annotated(self):
        documentation = (ROOT / "docs" / "rom-map.md").read_text(encoding="utf-8")
        blocks = {(start, end) for start, end, category, _ in decompile_rom.ROM_ANNOTATIONS
                  if category == "Graphics"}
        section = documentation.split("### Numeric and HUD glyph tiles", 1)[1].split(
            "### Stockable inventory item sprites", 1)[0]
        ranges = re.findall(r"^\| `0x([0-9A-F]+)-0x([0-9A-F]+)` \|", section, re.M)
        self.assertEqual(len(ranges), 50)
        for first, last in ranges:
            with self.subTest(first=first):
                self.assertIn((int(first, 16), int(last, 16) + 1), blocks)
        self.assertEqual(len([a for a in decompile_rom.ROM_ANNOTATIONS
                              if "Stacked 1bpp glyphs:" in a[3]]), 24)

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
