import shutil
import subprocess
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
        for name in ("render_graphics.py", "extract_json.py"):
            shutil.copy2(ROOT / "bin" / name, self.root / "bin" / name)
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
        rom[0x1000] = 0x80
        rom[0x1FFF0] = 0x80
        (self.root / "input" / "Rolan's Curse II (USA).gb").write_bytes(rom)

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
        with Image.open(self.root / "output" / "graphics.png") as image:
            self.assertEqual(image.size, (1084, 8700))
            self.assertEqual(image.getpixel((1052, 8668)), (85, 85, 85))

    def test_arguments_and_options_are_forwarded(self):
        output = self.root / "tiles with spaces.png"
        rom = self.root / "input" / "Rolan's Curse II (USA).gb"
        result = self.run_wrapper(
            "render-graphics", "0x1000", "0x1010", str(output),
            "--input", str(rom), "--columns", "1", "--scale", "1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output) as image:
            self.assertEqual(image.size, (16, 16))
            self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))

    def test_incomplete_arguments_fail(self):
        result = self.run_wrapper("render-graphics", "0x1000")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stderr)


if __name__ == "__main__":
    unittest.main()
