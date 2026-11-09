import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ROM_NAME = "Rolan's Curse II (USA).gb"
WORKING_NAME = "Rolan's Curse II (USA) (hack in progress).gb"
FINALIZED_STEM = "Rolan's Curse II (USA) (hack finalized)"
# (hero offset, pit offset, size, hero marker, pit marker) for each swapped block.
HERO_PIT_SEGMENTS = (
    (0x9106, 0x9606, 0x240, 0x11, 0x22),
    (0x95C6, 0x9A06, 64, 0x33, 0x44),
    (0x860E, 0x864E, 64, 0x55, 0x66),
    (0x880E, 0x890E, 0x100, 0x77, 0x88),
)


class HackWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "bin").mkdir()
        (self.root / "input").mkdir()
        (self.root / "output").mkdir()
        shutil.copy2(ROOT / "rc2t", self.root / "rc2t")
        for name in ("hack_rom.py", "swap_character_sprite.py"):
            shutil.copy2(ROOT / "bin" / name, self.root / "bin" / name)
        self.rom = bytes(range(256)) * 0x200
        (self.root / "input" / ROM_NAME).write_bytes(self.rom)
        self.working = self.root / "working" / WORKING_NAME
        self.hacks_log = self.root / "working" / "hacks.txt"

    def build_sprite_rom(self):
        rom = bytearray(0x20000)
        for hero, pit, size, hero_marker, pit_marker in HERO_PIT_SEGMENTS:
            rom[hero:hero + size] = bytes([hero_marker]) * size
            rom[pit:pit + size] = bytes([pit_marker]) * size
        return bytes(rom)

    def expected_swapped(self, rom):
        expected = bytearray(rom)
        for hero, pit, size, _, _ in HERO_PIT_SEGMENTS:
            expected[hero:hero + size] = rom[pit:pit + size]
            expected[pit:pit + size] = rom[hero:hero + size]
        return bytes(expected)

    def use_input_rom(self, rom):
        (self.root / "input" / ROM_NAME).write_bytes(rom)

    def run_wrapper(self, *args):
        return subprocess.run(
            ["bash", str(self.root / "rc2t"), "hack", *args],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )

    def test_any_subcommand_creates_missing_working_copy(self):
        result = self.run_wrapper("finalize")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.rom)

    def test_clear_deletes_working_copy(self):
        self.run_wrapper("reset")
        self.working.write_bytes(b"edited")
        result = self.run_wrapper("clear")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.working.exists())

    def test_reset_replaces_edited_working_copy(self):
        self.run_wrapper("reset")
        self.working.write_bytes(b"edited")
        result = self.run_wrapper("reset")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.rom)

    def test_finalize_writes_tagged_rom_and_matching_ips_patch(self):
        self.run_wrapper("reset")
        edited = bytearray(self.rom)
        edited[0x150:0x153] = b"\xAA\xBB\xCC"
        self.working.write_bytes(bytes(edited))
        result = self.run_wrapper("finalize")
        self.assertEqual(result.returncode, 0, result.stderr)
        output_rom = self.root / "output" / f"{FINALIZED_STEM}.gb"
        patch = self.root / "output" / f"{FINALIZED_STEM}.ips"
        self.assertEqual(output_rom.read_bytes(), bytes(edited))
        self.assertTrue(patch.read_bytes().startswith(b"PATCH"))
        self.assertTrue(patch.read_bytes().endswith(b"EOF"))
        self.assertIn(b"\x00\x01\x50\x00\x03\xAA\xBB\xCC", patch.read_bytes())

    def test_finalize_fails_without_input_rom(self):
        (self.root / "input" / ROM_NAME).unlink()
        result = self.run_wrapper("finalize")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error:", result.stderr)
        self.assertFalse((self.root / "output" / f"{FINALIZED_STEM}.ips").exists())

    def test_any_subcommand_creates_empty_hacks_log(self):
        self.run_wrapper("finalize")
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_clear_deletes_hacks_log(self):
        self.run_wrapper("reset")
        self.run_wrapper("swap-character-sprite", "hero", "pit")
        result = self.run_wrapper("clear")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.hacks_log.exists())

    def test_reset_clears_hacks_log(self):
        self.run_wrapper("reset")
        self.run_wrapper("swap-character-sprite", "hero", "pit")
        result = self.run_wrapper("reset")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_swap_edits_working_copy_in_place(self):
        rom = self.build_sprite_rom()
        self.use_input_rom(rom)
        self.run_wrapper("reset")
        result = self.run_wrapper("swap-character-sprite", "hero", "pit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.expected_swapped(rom))
        self.assertEqual((self.root / "input" / ROM_NAME).read_bytes(), rom)

    def test_swap_writes_no_output_files(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        self.run_wrapper("swap-character-sprite", "hero", "pit")
        self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_swap_appends_each_hack_to_hacks_log(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        self.run_wrapper("swap-character-sprite", "hero", "pit")
        result = self.run_wrapper("swap-character-sprite", "lane", "kyle")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.hacks_log.read_text(),
            "swap-character-sprite hero pit\nswap-character-sprite lane kyle\n",
        )

    def test_swap_accepts_mixed_case_names(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        result = self.run_wrapper("swap-character-sprite", "HERO", "Pit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "swap-character-sprite hero pit\n")

    def test_invalid_character_fails_without_changing_working_copy(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("swap-character-sprite", "hero", "unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_identical_characters_fail_without_changing_working_copy(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("swap-character-sprite", "hero", "hero")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be different", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_short_rom_fails_without_changing_working_copy(self):
        self.use_input_rom(bytes(0x2000))
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("swap-character-sprite", "hero", "pit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error:", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_finalize_after_swap_outputs_only_rom_and_patch(self):
        rom = self.build_sprite_rom()
        self.use_input_rom(rom)
        self.run_wrapper("reset")
        self.run_wrapper("swap-character-sprite", "hero", "pit")
        result = self.run_wrapper("finalize")
        self.assertEqual(result.returncode, 0, result.stderr)
        output_rom = self.root / "output" / f"{FINALIZED_STEM}.gb"
        patch = self.root / "output" / f"{FINALIZED_STEM}.ips"
        self.assertEqual(output_rom.read_bytes(), self.expected_swapped(rom))
        self.assertTrue(patch.read_bytes().startswith(b"PATCH"))
        self.assertTrue(patch.read_bytes().endswith(b"EOF"))
        self.assertEqual(
            sorted(path.name for path in (self.root / "output").iterdir()),
            sorted([output_rom.name, patch.name]),
        )

    def test_missing_subcommand_fails(self):
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)


if __name__ == "__main__":
    unittest.main()
