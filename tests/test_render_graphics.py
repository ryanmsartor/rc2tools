import argparse
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
    def test_parses_tile_grid_dimensions(self):
        self.assertEqual(render_graphics.parse_tile_grid("2x3"), (2, 3))
        self.assertEqual(render_graphics.parse_tile_grid("1X2"), (1, 2))
        for value in ("0x2", "2x0", "2by2", "2x2x2"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                render_graphics.parse_tile_grid(value)

    def test_decodes_two_bitplanes_left_to_right(self):
        tile = bytes([0x80, 0x40]) + bytes(14)
        decoded = render_graphics.decode_tiles(tile)
        self.assertEqual(decoded[0][0], [1, 2, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][1], [0] * 8)

    def test_rejects_empty_data(self):
        with self.assertRaisesRegex(ValueError, "at least one byte"):
            render_graphics.decode_tiles(b"")

    def test_decodes_partial_tiles_at_byte_granularity(self):
        for length in range(1, render_graphics.TILE_BYTES):
            with self.subTest(length=length):
                tile = render_graphics.decode_tiles(bytes(length))[0]
                self.assertEqual(tile, [[0] * 8 for _ in range(8)])

        one_byte_tile = render_graphics.decode_tiles(b"\x80")[0]
        self.assertEqual(one_byte_tile[0], [1, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(one_byte_tile[1:], [[0] * 8 for _ in range(7)])

        decoded = render_graphics.decode_tiles(bytes([0x80, 0, 0x40, 0]))
        self.assertEqual(decoded[0][0], [1, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][1], [0, 1, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][2:], [[0] * 8 for _ in range(6)])

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

    def test_assembles_arbitrary_tile_grid_in_row_major_order(self):
        def tile_data(color):
            low = 0xFF if color & 1 else 0
            high = 0xFF if color & 2 else 0
            return bytes((low, high)) * 8

        data = b"".join(tile_data(index % 4) for index in range(6))
        image = render_graphics.render_tile_grid(data, 2, 3, columns=1, scale=1)
        self.assertEqual(image.size, (16, 24))
        self.assertEqual(image.getpixel((8, 0)), render_graphics.DEFAULT_PALETTE[1])
        self.assertEqual(image.getpixel((0, 8)), render_graphics.DEFAULT_PALETTE[2])

    def test_incomplete_sprite_keeps_tiles_and_leaves_missing_quadrants_blank(self):
        tile_1 = bytes([0xFF, 0]) * 8
        tile_2 = bytes([0, 0xFF]) * 8
        image = render_graphics.render_sprites(tile_1 + tile_2, columns=1, scale=1)
        self.assertEqual(image.size, (16, 16))
        self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))
        self.assertEqual(image.getpixel((0, 8)), (170, 170, 170))
        self.assertEqual(image.getpixel((8, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((16 - 1, 0)), (0, 0, 0))

    def test_assembles_portrait_tiles_in_row_major_order(self):
        def tile_data(color):
            low = 0xFF if color & 1 else 0
            high = 0xFF if color & 2 else 0
            return bytes((low, high)) * 8

        data = b"".join(tile_data(index % 4) for index in range(16))
        image = render_graphics.render_portraits(data, columns=1, scale=1)
        self.assertEqual(image.size, (32, 32))
        self.assertEqual(image.getpixel((8, 0)), render_graphics.PORTRAIT_PALETTE[1])
        self.assertEqual(image.getpixel((0, 8)), render_graphics.PORTRAIT_PALETTE[0])

    def test_portrait_renderer_requires_complete_portraits(self):
        with self.assertRaisesRegex(ValueError, "multiple of 0x100 bytes"):
            render_graphics.render_portraits(bytes(0xFF))

    def test_address_axes_label_cel_starts(self):
        with patch.object(render_graphics.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            render_graphics.render_sprites(
                bytes(3 * 4 * render_graphics.TILE_BYTES),
                columns=2,
                scale=1,
                start_address=0x1000,
            )
        self.assertEqual(
            [call.args[2] for call in draw_text.call_args_list],
            ["0x1000", "0x1040", "0x1000", "0x1080"],
        )

    def test_tile_grid_address_axes_use_grid_byte_size(self):
        tile_count = 3 * 2 * 3
        with patch.object(render_graphics.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            render_graphics.render_tile_grid(
                bytes(tile_count * render_graphics.TILE_BYTES),
                2,
                3,
                columns=2,
                scale=1,
                start_address=0x1000,
            )
        self.assertEqual(
            [call.args[2] for call in draw_text.call_args_list],
            ["0x1000", "0x1060", "0x1000", "0x10C0"],
        )

    def test_portrait_address_axes_label_each_256_byte_block(self):
        with patch.object(render_graphics.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            render_graphics.render_portraits(
                bytes(2 * render_graphics.PORTRAIT_BYTES),
                columns=2,
                scale=1,
                start_address=0x880E,
            )
        self.assertEqual(
            [call.args[2] for call in draw_text.call_args_list],
            ["0x880E", "0x890E", "0x880E"],
        )

    def test_cli_renders_portrait_mode(self):
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "portraits.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1100", str(output_path),
                "--input", str(input_path), "--mode", "portraits", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertIn(render_graphics.PORTRAIT_PALETTE[0], colors)

    def test_cli_renders_custom_tile_grid(self):
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
        rom[0x1000] = 0x80

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "grid.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1060", str(output_path),
                "--input", str(input_path), "--tile-grid", "2x3",
                "--columns", "1", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertIn(render_graphics.DEFAULT_PALETTE[1], colors)

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
                self.assertGreater(image.width, 16)
                self.assertGreater(image.height, 16)
                colors = image.getcolors(image.width * image.height)
                self.assertIn((85, 85, 85), [color for _, color in colors])
                top_axis = image.crop((0, 0, image.width, 16))
                self.assertTrue(any(pixel != (255, 255, 255) for pixel in top_axis.getdata()))

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
