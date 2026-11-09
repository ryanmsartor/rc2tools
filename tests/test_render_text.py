import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("render_text", ROOT / "bin" / "render_text.py")
render_text = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render_text)


class RenderTextTests(unittest.TestCase):
    def test_known_bytes_decode_to_their_glyphs(self):
        self.assertEqual(render_text.decode(bytes([0x0A, 0x23])), "az")
        self.assertEqual(render_text.decode(bytes([0xB2, 0x24, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2D, 0xFD, 0xFF])), " '.,?!-:+#")

    def test_hero_placeholders_render_as_capital_hero(self):
        self.assertEqual(render_text.decode(bytes([0xE0, 0xE1, 0xE2, 0xE3])), "HERO")

    def test_unknown_bytes_render_as_unique_placeholders(self):
        placeholders = [render_text.glyph_for(byte) for byte in range(256) if byte not in render_text.CHARACTER_TABLE]
        self.assertEqual(len(placeholders), len(set(placeholders)))
        self.assertEqual(render_text.decode(bytes([0x00, 0xDF, 0x24])), render_text.UNKNOWN_GLYPHS[0x00] + render_text.UNKNOWN_GLYPHS[0xDF] + "'")

    def test_placeholders_avoid_font_and_known_glyphs(self):
        font_and_known = set(render_text.CHARACTER_TABLE.values()) | set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-:.?!/()'\";")
        self.assertFalse(font_and_known & set(render_text.UNKNOWN_GLYPHS))
        self.assertEqual(len(render_text.UNKNOWN_GLYPHS), 256)
        self.assertEqual(len(set(render_text.UNKNOWN_GLYPHS)), 256)

    def test_main_writes_one_string_for_whole_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "rom.gb"
            output = Path(directory) / "out" / "rom-text.txt"
            rom.write_bytes(bytes([0x0A, 0xFF, 0x00]))
            self.assertEqual(render_text.main([str(rom), str(output)]), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "a#" + render_text.UNKNOWN_GLYPHS[0x00])


if __name__ == "__main__":
    unittest.main()
