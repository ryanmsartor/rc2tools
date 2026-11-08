import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class SwapCharacterSpriteWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "bin").mkdir()
        (self.root / "input").mkdir()
        shutil.copy2(ROOT / "rc2t", self.root / "rc2t")
        for name in ("swap_character_sprite.py", "extract_json.py"):
            shutil.copy2(ROOT / "bin" / name, self.root / "bin" / name)
        rom = bytearray(0x20000)
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
        rom[0x9106:0x9346] = bytes([0x11]) * 0x240
        rom[0x9606:0x9846] = bytes([0x22]) * 0x240
        (self.root / "input" / "Rolan's Curse II (USA).gb").write_bytes(rom)

    def run_wrapper(self, *args):
        return subprocess.run(
            ["bash", str(self.root / "rc2t"), *args],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )

    def test_command_writes_semantically_named_ips_patch(self):
        result = self.run_wrapper("swap-character-sprite", "hero", "pit")
        self.assertEqual(result.returncode, 0, result.stderr)
        patch = self.root / "output" / "swap-hero-pit-sprites.ips"
        self.assertTrue(patch.is_file())
        self.assertTrue(patch.read_bytes().startswith(b"PATCH"))
        self.assertTrue(patch.read_bytes().endswith(b"EOF"))
        patched_rom = self.root / "output" / "swap-hero-pit-sprites.gb"
        self.assertTrue(patched_rom.is_file())
        self.assertEqual(patched_rom.stat().st_size, 0x20000)
        patched_bytes = patched_rom.read_bytes()
        self.assertEqual(patched_bytes[0x9106], 0x22)
        self.assertEqual(patched_bytes[0x9606], 0x11)

    def test_unknown_character_fails_without_writing_patch(self):
        result = self.run_wrapper("swap-character-sprite", "hero", "unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)
        self.assertFalse((self.root / "output" / "swap-hero-unknown-sprites.ips").exists())


if __name__ == "__main__":
    unittest.main()
