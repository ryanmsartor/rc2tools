import tempfile
import unittest
from pathlib import Path

from tests.support import load_bin_module

render_text = load_bin_module("render_text")


class RenderTextTests(unittest.TestCase):
    def test_known_bytes_decode_to_their_glyphs(self):
        self.assertEqual(render_text.decode(bytes([0x0A, 0x23])), "az")
        self.assertEqual(render_text.decode(bytes([0xB2, 0xFE, 0x24, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2D, 0xFD, 0xFF])), "  '-.,?!-:+#")

    def test_hero_placeholders_render_as_capital_hero(self):
        self.assertEqual(render_text.decode(bytes([0xE0, 0xE1, 0xE2, 0xE3])), "HERO")

    def test_unknown_bytes_render_as_unique_placeholders(self):
        placeholders = [render_text.glyph_for(byte) for byte in range(256) if byte not in render_text.CHARACTER_TABLE]
        self.assertEqual(len(placeholders), len(set(placeholders)))
        self.assertEqual(render_text.decode(bytes([0x00, 0xDF, 0x24])), render_text.UNKNOWN_GLYPHS[0x00] + render_text.UNKNOWN_GLYPHS[0xDF] + "'")

    def test_known_only_decode_uses_underscores_for_unknown_bytes(self):
        data = bytes([0x0A, 0x00, 0x26, 0xFD, 0xFE, 0xFF, 0xB2])

        self.assertEqual(render_text.decode(data, known_only=True), "a_-+ # ")

    def test_placeholders_avoid_font_and_known_glyphs(self):
        font_and_known = set(render_text.CHARACTER_TABLE.values()) | set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-:.?!/()'\";")
        self.assertFalse(font_and_known & set(render_text.UNKNOWN_GLYPHS))
        self.assertEqual(len(render_text.UNKNOWN_GLYPHS), 256)
        self.assertEqual(len(set(render_text.UNKNOWN_GLYPHS)), 256)

    def test_wrap_text_splits_at_64_characters_and_adds_rom_addresses(self):
        data = bytes([0x0A] * 64 + [0xFD])

        wrapped = render_text.wrap_text(data)

        self.assertEqual(wrapped, "0x00000: " + "a" * 64 + "\n0x00040: +")

    def test_wrap_text_addresses_track_rom_offsets_after_known_glyphs(self):
        data = bytes([0x0A] * 63 + [0xE0, 0xFD])

        self.assertEqual(
            render_text.wrap_text(data),
            "0x00000: " + "a" * 63 + "H\n0x00040: +",
        )

    def test_main_writes_one_string_for_whole_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "rom.gb"
            output = Path(directory) / "out" / "rom-text.txt"
            rom.write_bytes(bytes([0x0A, 0xFF, 0x00]))
            self.assertEqual(render_text.main([str(rom), str(output)]), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "a#" + render_text.UNKNOWN_GLYPHS[0x00])

    def test_main_wraps_output_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "rom.gb"
            output = Path(directory) / "wrapped.txt"
            rom.write_bytes(bytes([0x0A] * 65))

            self.assertEqual(render_text.main(["--wrap", str(rom), str(output)]), 0)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "0x00000: " + "a" * 64 + "\n0x00040: a",
            )

    def test_main_combines_known_only_and_wrap(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "rom.gb"
            output = Path(directory) / "wrapped.txt"
            rom.write_bytes(bytes([0x0A] * 63 + [0x00, 0xFD, 0xFF, 0xFE]))

            self.assertEqual(
                render_text.main(["--known-only", "--wrap", str(rom), str(output)]),
                0,
            )
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "0x00000: " + "a" * 63 + "_\n0x00040: +# ",
            )

    def test_omit_sprites_masks_exact_known_graphics_ranges(self):
        data = bytes([0x0A]) * 0x20000
        decoded = render_text.decode(data, omit_sprites=True)
        mask = bytearray(len(data))
        for start, end in render_text.KNOWN_GRAPHICS_RANGES:
            mask[start:end] = b"\x01" * (end - start)
        self.assertEqual(len(decoded), len(data))
        for address, is_graphics in enumerate(mask):
            self.assertEqual(decoded[address], "%" if is_graphics else "a", hex(address))
        self.assertEqual(render_text.decode(data), "a" * len(data))

    def test_main_omit_sprites_combines_with_known_only_and_wrap(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / "rom.gb"
            output = Path(directory) / "out.txt"
            data = bytearray([0x0A] * 0x52C0)
            data[0x528F:0x5293] = bytes([0x00, 0xFD, 0xFF, 0x00])
            rom.write_bytes(data)
            for options in (["--omit-sprites"], ["--omit-sprites", "--known-only"],
                            ["--omit-sprites", "--wrap"],
                            ["--omit-sprites", "--known-only", "--wrap"]):
                with self.subTest(options=options):
                    self.assertEqual(render_text.main([*options, str(rom), str(output)]), 0)
                    result = output.read_text(encoding="utf-8")
                    line = next(line for line in result.splitlines() if line.startswith("0x05280: ")) if "--wrap" in options else result[0x5280:0x52C0]
                    expected_prefix = "_" if "--known-only" in options else render_text.UNKNOWN_GLYPHS[0x00]
                    self.assertTrue(line.endswith(expected_prefix + "+" + "%" * 47))


if __name__ == "__main__":
    unittest.main()
