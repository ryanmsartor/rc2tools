import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class DecompileWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "bin").mkdir()
        shutil.copy2(ROOT / "rc2t", self.root / "rc2t")
        shutil.copy2(ROOT / "bin" / "decompile_rom.py", self.root / "bin" / "decompile_rom.py")
        rom = self.root / "game.gb"
        rom.write_bytes(bytes([0x00, 0x18, 0xFD]))
        self.rom = rom

    def run_wrapper(self, command, *args):
        return subprocess.run(
            ["bash", str(self.root / "rc2t"), command, *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_decompile_command_and_alias_write_listing(self):
        for command, output_name in (("decompile", "game.asm"), ("disassemble", "alias.asm")):
            with self.subTest(command=command):
                output = self.root / output_name
                result = self.run_wrapper(command, str(self.rom), str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("JR $0000", output.read_text(encoding="utf-8"))

    def test_default_output_uses_input_basename(self):
        result = self.run_wrapper("decompile", str(self.rom))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "output" / "game.asm").is_file())

    def test_default_rom_output_uses_default_rom_basename(self):
        (self.root / "input").mkdir()
        (self.root / "input" / "Rolan's Curse II (USA).gb").write_bytes(b"\x00")
        result = self.run_wrapper("decompile")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "output" / "Rolan's Curse II (USA).asm").is_file())


if __name__ == "__main__":
    unittest.main()
