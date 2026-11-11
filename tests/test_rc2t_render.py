import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent


class RenderGraphicsWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "bin").mkdir()
        (self.root / "input").mkdir()
        shutil.copy2(ROOT / "rc2t", self.root / "rc2t")
        for name in ("render_graphics.py", "known_graphics.py", "extract_json.py"):
            shutil.copy2(ROOT / "bin" / name, self.root / "bin" / name)
        bin_path = str(self.root / "bin")
        sys.path.insert(0, bin_path)
        self.addCleanup(sys.path.remove, bin_path)
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
        rom[0x1000] = 0x80
        rom[0x1FFF0] = 0x80
        rom[0x1FFFF] = 0x80
        (self.root / "input" / "Rolan's Curse II (USA).gb").write_bytes(rom)
        self.working = self.root / "working" / "Rolan's Curse II (USA) (hack in progress).gb"

    def run_wrapper(self, *args):
        return subprocess.run(
            ["bash", str(self.root / "rc2t"), *args],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )

    def test_default_renders_entire_rom(self):
        result = self.run_wrapper("render-graphics")
        self.assertEqual(result.returncode, 0, result.stderr)
        rom = (self.root / "input" / "Rolan's Curse II (USA).gb").read_bytes()
        spec = importlib.util.spec_from_file_location(
            "render_graphics", self.root / "bin" / "render_graphics.py"
        )
        render_graphics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render_graphics)
        with Image.open(self.root / "output" / "graphics.png") as image:
            self.assertEqual(image.size, (1135, 9054))
            bank_seven = render_graphics.render_sprites(
                rom[0x1C000:0x20000], 16, 4, start_address=0x1C000
            )
            bank_seven_top = 7 * (bank_seven.height + 16 + 18) + 16
            self.assertEqual(
                image.crop((0, bank_seven_top, bank_seven.width, bank_seven_top + bank_seven.height)).tobytes(),
                bank_seven.tobytes(),
            )

    def test_arguments_and_options_are_forwarded(self):
        output = self.root / "tiles with spaces.png"
        rom = self.root / "input" / "Rolan's Curse II (USA).gb"
        result = self.run_wrapper(
            "render-graphics", "0x1000", "0x1010", str(output),
            "--input", str(rom), "--columns", "1", "--scale", "1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output) as image:
            self.assertEqual(image.size, (59, 48))
            self.assertEqual(image.getpixel((43, 32)), (85, 85, 85))

    def test_highlight_known_works_with_default_full_rom_range(self):
        result = self.run_wrapper("render-graphics", "--highlight-known", "--scale", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "output" / "graphics.png") as image:
            colors = [color for _, color in image.getcolors(image.width * image.height)]
            self.assertTrue(any(r == g < b for r, g, b in colors))

    def test_compare_renders_input_left_and_working_right(self):
        original_path = self.root / "input" / "Rolan's Curse II (USA).gb"
        original = bytearray(original_path.read_bytes())
        original[0x1000:0x1010] = bytes([0xFF, 0]) * 8
        original_path.write_bytes(original)
        working = bytearray(original)
        working[0x1000] = 0x7F
        self.working.parent.mkdir()
        self.working.write_bytes(working)

        result = self.run_wrapper(
            "render-graphics", "0x1000", "0x1010", "--compare", "--columns", "1", "--scale", "1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        spec = importlib.util.spec_from_file_location(
            "render_graphics", self.root / "bin" / "render_graphics.py"
        )
        render_graphics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render_graphics)
        input_panel = render_graphics.render_banked_sprites(
            bytes(original[0x1000:0x1010]), 0x1000, columns=1, scale=1,
            comparison=bytes(working[0x1000:0x1010]),
        )
        working_panel = render_graphics.render_banked_sprites(
            bytes(working[0x1000:0x1010]), 0x1000, columns=1, scale=1,
            comparison=bytes(original[0x1000:0x1010]),
        )
        font = render_graphics.ImageFont.load_default()
        header_height = font.getbbox("Input ROM")[3] - font.getbbox("Input ROM")[1] + 12
        with Image.open(self.root / "output" / "graphics.png") as image:
            self.assertEqual(
                image.crop((0, header_height, input_panel.width, header_height + input_panel.height)).tobytes(),
                input_panel.tobytes(),
            )
            right_x = input_panel.width + 24
            self.assertEqual(
                image.crop((right_x, header_height, right_x + working_panel.width,
                            header_height + working_panel.height)).tobytes(),
                working_panel.tobytes(),
            )
            self.assertIn(render_graphics.BLUESCALE_PALETTE[1],
                          [color for _, color in image.getcolors(image.width * image.height)])
            self.assertIn(render_graphics.REDSCALE_PALETTE[1],
                          [color for _, color in image.getcolors(image.width * image.height)])

    def test_compare_requires_working_rom(self):
        result = self.run_wrapper("render-graphics", "--compare", "--scale", "1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires the working ROM", result.stderr)

    def test_compare_rejects_highlight_known(self):
        self.working.parent.mkdir()
        self.working.write_bytes(bytes(0x20000))
        result = self.run_wrapper(
            "render-graphics", "--compare", "--highlight-known", "--scale", "1"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)

    def test_start_and_end_accept_highlight_known_without_output_path(self):
        rom_path = self.root / "input" / "Rolan's Curse II (USA).gb"
        rom = bytearray(rom_path.read_bytes())
        rom[0x8040:0x8060] = bytes([0xFF, 0]) * 16
        rom_path.write_bytes(rom)

        result = self.run_wrapper(
            "render-graphics", "0x8040", "0x8060", "--highlight-known", "--scale", "1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "output" / "graphics.png") as image:
            colors = [color for _, color in image.getcolors(image.width * image.height)]
            self.assertTrue(any(r == g < b for r, g, b in colors))

    def test_positional_tile_grid_renders_to_default_output(self):
        result = self.run_wrapper(
            "render-graphics", "0x1000", "0x1060", "2x3", "--scale", "1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "output" / "graphics.png") as image:
            self.assertGreater(image.width, 16)
            self.assertGreater(image.height, 24)
            colors = [color for _, color in image.getcolors(image.width * image.height)]
            self.assertIn((85, 85, 85), colors)

    def test_start_only_renders_one_byte_range_through_end_of_rom(self):
        result = self.run_wrapper("render-graphics", "0x1FFFF")
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "output" / "graphics.png") as image:
            colors = image.getcolors(image.width * image.height)
            self.assertIn((85, 85, 85), [color for _, color in colors])


if __name__ == "__main__":
    unittest.main()
