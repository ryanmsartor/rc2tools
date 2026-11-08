import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
SPEC = importlib.util.spec_from_file_location("render_graphics", ROOT / "bin" / "render_graphics.py")
render_graphics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render_graphics)


class RenderGraphicsTests(unittest.TestCase):
    def test_decodes_two_bitplanes_left_to_right(self):
        tile = bytes([0x80, 0x40]) + bytes(14)
        decoded = render_graphics.decode_tiles(tile)
        self.assertEqual(decoded[0][0], [1, 2, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][1], [0] * 8)

    def test_rejects_empty_or_partial_tile_data(self):
        for data in (b"", bytes(15), bytes(17)):
            with self.subTest(length=len(data)):
                with self.assertRaisesRegex(ValueError, "multiple of 16"):
                    render_graphics.decode_tiles(data)

    def test_assembles_four_tiles_in_column_first_sprite_order(self):
        tile_1 = bytes([0xFF, 0]) * 8
        tile_2 = bytes([0, 0xFF]) * 8
        tile_3 = bytes([0xFF, 0xFF]) * 8
        tile_0 = bytes(16)
        image = render_graphics.render_sprites(
            tile_1 + tile_2 + tile_3 + tile_0,
            columns=1,
            scale=2,
        )
        self.assertEqual(image.size, (32, 32))
        self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))
        self.assertEqual(image.getpixel((0, 16)), (170, 170, 170))
        self.assertEqual(image.getpixel((16, 0)), (255, 255, 255))
        self.assertEqual(image.getpixel((16, 16)), (0, 0, 0))

    def test_incomplete_sprite_keeps_tiles_and_leaves_missing_quadrants_blank(self):
        tile_1 = bytes([0xFF, 0]) * 8
        tile_2 = bytes([0, 0xFF]) * 8
        image = render_graphics.render_sprites(tile_1 + tile_2, columns=1, scale=1)
        self.assertEqual(image.size, (16, 16))
        self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))
        self.assertEqual(image.getpixel((0, 8)), (170, 170, 170))
        self.assertEqual(image.getpixel((8, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((16 - 1, 0)), (0, 0, 0))

    def test_cli_writes_png_for_a_rom_range(self):
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
        rom[0x1000] = 0x80

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "tiles.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1010", str(output_path),
                "--input", str(input_path), "--columns", "1", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                self.assertEqual(image.size, (16, 16))
                self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))

    def test_cli_writes_jpeg(self):
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "tiles.jpg"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1010", str(output_path),
                "--input", str(input_path), "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                self.assertEqual(image.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
