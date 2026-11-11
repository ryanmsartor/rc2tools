import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tests.support import blank_rom, copy_tool_tree


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
# (idle frame offset, enemy frame offset) for the egghead and dog copies, which the real ROM
# stores twice with identical bytes. Each frame is 64 bytes.
NPC_MIRRORED_FRAMES = (
    (0x1869E, 0xE25A),
    (0x186DE, 0xE29A),
    (0x1889E, 0xE2DA),
    (0x188DE, 0xE31A),
)


class HackWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "input").mkdir()
        (self.root / "output").mkdir()
        copy_tool_tree(self.root)
        self.rom = bytes(range(256)) * 0x200
        (self.root / "input" / ROM_NAME).write_bytes(self.rom)
        self.working = self.root / "working" / WORKING_NAME
        self.hacks_log = self.root / "working" / "hacks.txt"

    def build_sprite_rom(self):
        rom = blank_rom()
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

    def use_npc_rom(self):
        rom = bytearray(self.rom)
        for idle, enemy in NPC_MIRRORED_FRAMES:
            rom[idle:idle + 64] = rom[enemy:enemy + 64]
        self.use_input_rom(bytes(rom))
        return bytes(rom)

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
        self.assertEqual((self.root / "output" / "hack finalized.txt").read_bytes(), b"")

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

    def test_finalize_custom_tag_via_rc2h(self):
        self.run_wrapper("reset")
        log_content = b"first hack\nsecond hack\n"
        self.hacks_log.write_bytes(log_content)
        log_output = self.root / "output" / "my hack.txt"
        log_output.write_bytes(b"old content\n")
        edited = bytearray(self.rom)
        edited[0x150:0x153] = b"\xAA\xBB\xCC"
        self.working.write_bytes(edited)
        result = subprocess.run(
            [str(self.root / "rc2h"), "finalize", "my hack"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        stem = "Rolan's Curse II (USA) (my hack)"
        self.assertEqual((self.root / "output" / f"{stem}.gb").read_bytes(), edited)
        patch = (self.root / "output" / f"{stem}.ips").read_bytes()
        self.assertEqual(patch, b"PATCH\x00\x01\x50\x00\x03\xAA\xBB\xCCEOF")
        self.assertEqual(log_output.read_bytes(), log_content)
        self.assertIn(str(log_output), result.stdout)
        self.assertFalse((self.root / "output" / f"{FINALIZED_STEM}.gb").exists())
        self.assertEqual(self.working.read_bytes(), edited)
        self.assertEqual(self.hacks_log.read_bytes(), log_content)

    def test_finalize_rejects_invalid_tags_before_creating_working_copy(self):
        for tag in ("", "  ", "../outside", "a\\b", "bad\nname"):
            with self.subTest(tag=tag):
                result = self.run_wrapper("finalize", tag)
                self.assertEqual(result.returncode, 2)
                self.assertIn("tag must be nonempty", result.stderr)
                self.assertFalse(self.working.exists())
                self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_finalize_rejects_multiple_tags(self):
        result = self.run_wrapper("finalize", "one", "two")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)
        self.assertFalse(self.working.exists())

    def test_any_subcommand_creates_empty_hacks_log(self):
        self.run_wrapper("finalize")
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_clear_deletes_hacks_log(self):
        self.run_wrapper("reset")
        self.run_wrapper("swap-char-sprite", "hero", "pit")
        result = self.run_wrapper("clear")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.hacks_log.exists())

    def test_reset_clears_hacks_log(self):
        self.run_wrapper("reset")
        self.run_wrapper("swap-char-sprite", "hero", "pit")
        result = self.run_wrapper("reset")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_swap_edits_working_copy_in_place(self):
        rom = self.build_sprite_rom()
        self.use_input_rom(rom)
        self.run_wrapper("reset")
        result = self.run_wrapper("swap-char-sprite", "hero", "pit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.expected_swapped(rom))
        self.assertEqual((self.root / "input" / ROM_NAME).read_bytes(), rom)

    def test_swap_writes_no_output_files(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        self.run_wrapper("swap-char-sprite", "hero", "pit")
        self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_swap_appends_each_hack_to_hacks_log(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        self.run_wrapper("swap-char-sprite", "hero", "pit")
        result = self.run_wrapper("swap-char-sprite", "lane", "kyle")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.hacks_log.read_text(),
            "swap-char-sprite hero pit\nswap-char-sprite lane kyle\n",
        )

    def test_swap_accepts_mixed_case_names(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        result = self.run_wrapper("swap-char-sprite", "HERO", "Pit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "swap-char-sprite hero pit\n")

    def test_old_swap_name_is_an_alias_logged_under_new_name(self):
        rom = self.build_sprite_rom()
        self.use_input_rom(rom)
        self.run_wrapper("reset")
        result = self.run_wrapper("swap-character-sprite", "hero", "pit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.expected_swapped(rom))
        self.assertEqual(self.hacks_log.read_text(), "swap-char-sprite hero pit\n")

    def test_old_swap_name_rejects_identical_characters(self):
        self.run_wrapper("reset")
        result = self.run_wrapper("swap-character-sprite", "hero", "hero")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be different", result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_help_lists_swap_without_old_name(self):
        result = self.run_wrapper("-h")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("swap-char-sprite", result.stdout)
        self.assertNotIn("swap-character-sprite", result.stdout)

    def test_invalid_character_fails_without_changing_working_copy(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("swap-char-sprite", "hero", "unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_identical_characters_fail_without_changing_working_copy(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("swap-char-sprite", "hero", "hero")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be different", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_short_rom_fails_without_changing_working_copy(self):
        self.use_input_rom(bytes(0x2000))
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("swap-char-sprite", "hero", "pit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error:", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_finalize_after_swap_outputs_rom_patch_and_log(self):
        rom = self.build_sprite_rom()
        self.use_input_rom(rom)
        self.run_wrapper("reset")
        self.run_wrapper("swap-char-sprite", "hero", "pit")
        result = self.run_wrapper("finalize")
        self.assertEqual(result.returncode, 0, result.stderr)
        output_rom = self.root / "output" / f"{FINALIZED_STEM}.gb"
        patch = self.root / "output" / f"{FINALIZED_STEM}.ips"
        log = self.root / "output" / "hack finalized.txt"
        self.assertEqual(output_rom.read_bytes(), self.expected_swapped(rom))
        self.assertTrue(patch.read_bytes().startswith(b"PATCH"))
        self.assertTrue(patch.read_bytes().endswith(b"EOF"))
        self.assertEqual(log.read_bytes(), self.hacks_log.read_bytes())
        self.assertEqual(log.read_text(), "swap-char-sprite hero pit\n")
        self.assertIn(str(log), result.stdout)
        self.assertEqual(
            sorted(path.name for path in (self.root / "output").iterdir()),
            sorted([output_rom.name, patch.name, log.name]),
        )

    def test_missing_subcommand_fails(self):
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)

    def test_rc2h_forwards_arguments_and_exit_status(self):
        for args in (("",), ("dump-art", "not a title"), ("dump-art", "--help"), ("bogus",)):
            with self.subTest(args=args):
                expected = self.run_wrapper(*args)
                result = subprocess.run(
                    [str(self.root / "rc2h"), *args],
                    cwd=self.root / "input",
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected.returncode)
                self.assertEqual(result.stdout, expected.stdout)
                self.assertEqual(result.stderr, expected.stderr)

    def test_rc2h_help_aliases(self):
        expected = self.run_wrapper("--help")
        self.assertEqual(expected.returncode, 0)
        help_text = expected.stdout.replace("usage: rc2t hack ", "usage: rc2h ", 1)
        for args in ((), ("h",), ("help",), ("-h",), ("-help",), ("--h",), ("--help",)):
            with self.subTest(args=args):
                result = subprocess.run(
                    [str(self.root / "rc2h"), *args],
                    cwd=self.root / "input",
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, help_text)
                self.assertEqual(result.stderr, "")
                self.assertFalse(self.working.exists())

    def test_rc2h_runs_hack_subcommand(self):
        result = subprocess.run(
            [str(self.root / "rc2h"), "reset"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.rom)

    def test_dump_art_writes_title_png_without_logging(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        result = self.run_wrapper("dump-art", "title")
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "working" / "title-art.png") as image:
            self.assertEqual(image.size, (160, 88))
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_dump_hero_art_from_working_copy_without_logging(self):
        self.use_input_rom(self.build_sprite_rom())
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = subprocess.run(
            [str(self.root / "rc2h"), "dump-art", "hero"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "working" / "hero-art.png") as image:
            self.assertEqual(image.size, (118, 67))
            self.assertEqual(image.getpixel((16, 0)), (255, 0, 0))
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_dump_each_character_from_working_copy(self):
        starts = {
            "hero": 0x9106, "pit": 0x9606, "lane": 0x9A46, "kyle": 0x9DC6,
            "jude": 0xA306, "lee": 0xA7C6, "lora": 0xACC6, "zold": 0xB0E6,
        }
        rom = bytearray(self.rom)
        for index, offset in enumerate(starts.values()):
            color = index % 4
            rom[offset:offset + 16] = bytes((0xFF if color & 1 else 0, 0xFF if color & 2 else 0)) * 8
        self.use_input_rom(bytes(rom))
        self.run_wrapper("reset")
        for index, character in enumerate(starts):
            with self.subTest(character=character):
                result = subprocess.run(
                    [str(self.root / "rc2h"), "dump-art", character],
                    cwd=self.root / "input",
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                with Image.open(self.root / "working" / f"{character}-art.png") as image:
                    expected = {
                        "hero": (118, 67), "pit": (84, 84), "lane": (84, 67), "kyle": (84, 93),
                        "jude": (135, 50), "lee": (110, 67), "lora": (84, 76), "zold": (101, 67),
                    }
                    self.assertEqual(image.size, expected.get(character, (84, 50)))
                    shade = (170, 0, 85, 255)[index % 4]
                    x = 17 if character == "zold" else 0
                    self.assertEqual(image.getpixel((x, 0)), (shade, shade, shade))
        self.assertEqual(self.working.read_bytes(), bytes(rom))
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_weapons_is_not_an_art_name(self):
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        before = self.working.read_bytes()

        result = subprocess.run(
            [str(self.root / "rc2h"), "dump-art", "weapons"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

        result = self.run_wrapper("inject-art", "weapons")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)
        self.assertFalse((self.root / "working" / "weapons-art.png").exists())
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_dump_ability_art_in_rom_order(self):
        rom = bytearray(self.rom)
        starts = range(0x804E, 0x860E, 0x40)
        markers = ((0x00, 0x00), (0xFF, 0x00), (0x00, 0xFF), (0xFF, 0xFF))
        for index, offset in enumerate(starts):
            low, high = markers[index % len(markers)]
            rom[offset:offset + 0x40] = bytes((low, high)) * 0x20
        self.use_input_rom(bytes(rom))
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        before = self.working.read_bytes()

        result = subprocess.run(
            [str(self.root / "rc2h"), "dump-art", "abilities"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "working" / "abilities-art.png") as image:
            self.assertEqual(image.size, (101, 67))
            self.assertEqual(image.mode, "RGB")
            shades = ((170, 170, 170), (0, 0, 0), (85, 85, 85), (255, 255, 255))
            for index in range(23):
                x = (index % 6) * 17
                y = (index // 6) * 17
                self.assertEqual(image.getpixel((x, y)), shades[index % 4])
            self.assertEqual(image.getpixel((16, 0)), (255, 0, 0))
            self.assertEqual(image.getpixel((85, 51)), (255, 0, 0))
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_inject_ability_art_from_working_copy(self):
        self.use_input_rom(bytes(0x20000))
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        self.assertEqual(self.run_wrapper("dump-art", "abilities").returncode, 0)
        path = self.root / "working" / "abilities-art.png"
        with Image.open(path) as image:
            edited = image.copy()
        edited.putpixel((0, 0), (0, 0, 0))
        edited.putpixel((16, 0), (0, 255, 0))
        edited.save(path)

        result = subprocess.run(
            [str(self.root / "rc2h"), "inject-art", "abilities"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = bytearray(0x20000)
        expected[0x804E] = 0x80
        self.assertEqual(self.working.read_bytes(), expected)
        self.assertEqual(self.hacks_log.read_text(), "inject-art abilities\n")

    def test_dump_npc_art_includes_documented_ranges(self):
        rom = bytearray(self.rom)
        rom[0x1861E:0x18A1E] = bytes([0xFF, 0]) * ((0x18A1E - 0x1861E) // 2)
        rom[0xE25A:0xFD5A] = bytes([0xFF, 0]) * ((0xFD5A - 0xE25A) // 2)
        self.use_input_rom(bytes(rom))
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        result = subprocess.run(
            [str(self.root / "rc2h"), "dump-art", "npc"],
            cwd=self.root / "input",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "working" / "npc-art.png") as image:
            self.assertEqual(image.size, (203, 169))
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.getpixel((16, 0)), (255, 0, 0))
            self.assertEqual(image.getpixel((0, 16)), (255, 0, 0))
        self.assertEqual(self.working.read_bytes(), bytes(rom))
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_dump_and_inject_all_matches_individual_commands(self):
        dump_names = (
            "title", "hero", "pit", "lane", "kyle", "jude", "lee", "lora", "zold",
            "npc", "abilities", "font",
        )
        self.use_input_rom(self.build_sprite_rom())
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        before = self.working.read_bytes()
        result = self.run_wrapper("dump-art", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")
        for name in dump_names:
            path = self.root / "working" / f"{name}-art.png"
            with Image.open(path) as image:
                edited = image.copy()
            sizes = {
                "title": (160, 88), "npc": (203, 169), "hero": (118, 67),
                "pit": (84, 84), "lane": (84, 67), "kyle": (84, 93),
                "jude": (135, 50), "lee": (110, 67), "lora": (84, 76), "zold": (101, 67),
                "abilities": (101, 67), "font": (53, 71),
            }
            self.assertEqual(edited.size, sizes.get(name, (84, 50)))
            if name == "zold":
                point = (17, 0)
                edited.putpixel(point, (85, 85, 85) if edited.getpixel(point) != (85, 85, 85) else (255, 255, 255))
            elif name == "title":
                edited.putpixel((0, 0), 0 if edited.getpixel((0, 0)) != 0 else 255)
            elif name == "font":
                edited.putpixel((0, 0), (0, 0, 0) if edited.getpixel((0, 0)) != (0, 0, 0) else (255, 255, 255))
            else:
                edited.putpixel((0, 0), (85, 85, 85) if edited.getpixel((0, 0)) != (85, 85, 85) else (255, 255, 255))
            edited.save(path)

        result = subprocess.run(
            [str(self.root / "rc2h"), "inject-art", "all"],
            cwd=self.root / "input", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        combined = self.working.read_bytes()
        expected_log = "".join(f"inject-art {name}\n" for name in dump_names)
        self.assertEqual(self.hacks_log.read_text(), expected_log)
        self.assertNotEqual(combined, before)

        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        for name in dump_names:
            result = self.run_wrapper("inject-art", name)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), combined)
        self.assertEqual(self.hacks_log.read_text(), expected_log)

    def test_inject_all_logs_only_changed_targets(self):
        rom = self.build_sprite_rom()
        self.use_input_rom(rom)
        self.assertEqual(self.run_wrapper("dump-art", "all").returncode, 0)
        path = self.root / "working" / "hero-art.png"
        with Image.open(path) as image:
            edited = image.copy()
        old = edited.getpixel((0, 0))
        edited.putpixel((0, 0), (0, 0, 0) if old != (0, 0, 0) else (255, 255, 255))
        edited.save(path)
        result = self.run_wrapper("inject-art", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        changed_rom = self.working.read_bytes()
        self.assertNotEqual(changed_rom, rom)
        self.assertEqual(self.hacks_log.read_text(), "inject-art title\ninject-art hero\n")
        result = self.run_wrapper("inject-art", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), changed_rom)
        self.assertEqual(self.hacks_log.read_text(), "inject-art title\ninject-art hero\n")


    def test_inject_all_stops_at_missing_image_and_keeps_prior_results(self):
        self.use_input_rom(self.build_sprite_rom())
        self.assertEqual(self.run_wrapper("dump-art", "all").returncode, 0)
        path = self.root / "working" / "hero-art.png"
        with Image.open(path) as image:
            edited = image.copy()
        edited.putpixel((0, 0), (85, 85, 85))
        edited.save(path)
        (self.root / "working" / "lane-art.png").unlink()
        result = self.run_wrapper("inject-art", "all")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lane-art.png", result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "inject-art title\ninject-art hero\n")

    def test_inject_each_character_and_log(self):
        starts = {
            "hero": 0x9106, "pit": 0x9606, "lane": 0x9A46, "kyle": 0x9DC6,
            "jude": 0xA306, "lee": 0xA7C6, "lora": 0xACC6, "zold": 0xB0E6,
        }
        self.use_input_rom(bytes(0x20000))
        self.run_wrapper("reset")
        expected = bytearray(0x20000)
        for character, offset in starts.items():
            with self.subTest(character=character):
                self.assertEqual(self.run_wrapper("dump-art", character).returncode, 0)
                png = self.root / "working" / f"{character}-art.png"
                with Image.open(png) as image:
                    edited = image.copy()
                edited.putpixel((17 if character == "zold" else 0, 0), (85, 85, 85))
                edited.save(png)
                result = subprocess.run(
                    [str(self.root / "rc2h"), "inject-art", character],
                    cwd=self.root / "input",
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                # (85, 85, 85) is palette index 2, which sets the high bit plane.
                expected[offset + 1] = 0x80
                self.assertEqual(self.working.read_bytes(), expected)
        self.assertEqual(
            self.hacks_log.read_text(),
            "".join(f"inject-art {character}\n" for character in starts),
        )

    def test_character_injection_wrong_size_does_not_change_rom_or_log(self):
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        Image.new("RGB", (1, 1)).save(self.root / "working" / "hero-art.png")
        result = self.run_wrapper("inject-art", "hero")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected a 118x67 image", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_read_art_applies_png_and_logs_hack(self):
        rom = bytearray(self.build_sprite_rom())
        self.use_input_rom(bytes(rom))
        self.run_wrapper("reset")
        self.run_wrapper("dump-art", "title")
        png = self.root / "working" / "title-art.png"
        with Image.open(png) as image:
            edited = image.convert("L")
        edited.putpixel((12 * 8, 1 * 8), 0)
        edited.save(png)
        result = self.run_wrapper("inject-art", "title")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hacks_log.read_text(), "inject-art title\n")
        self.assertNotEqual(self.working.read_bytes(), bytes(rom))

    def test_read_art_without_png_fails_and_leaves_rom_unchanged(self):
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        result = self.run_wrapper("inject-art", "title")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error:", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_art_subcommands_reject_unknown_name(self):
        result = self.run_wrapper("dump-art", "logo")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)

    def test_npc_art_round_trip_leaves_rom_unchanged(self):
        rom = self.use_npc_rom()
        self.run_wrapper("reset")
        self.assertEqual(self.run_wrapper("dump-art", "npc").returncode, 0)
        result = self.run_wrapper("inject-art", "npc")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), rom)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_npc_art_edit_changes_only_its_sprite_tile_bytes(self):
        # Sheet pixels (0, 0) and (136, 85) are the top-left corners of the first idle NPC
        # frame (0x1861E) and the first four-pose enemy frame (0xF05A), which sits in row 6.
        for x, y, offset in ((0, 0, 0x1861E), (136, 85, 0xF05A)):
            with self.subTest(offset=hex(offset)):
                rom = self.use_npc_rom()
                self.run_wrapper("reset")
                self.assertEqual(self.run_wrapper("dump-art", "npc").returncode, 0)
                png = self.root / "working" / "npc-art.png"
                with Image.open(png) as image:
                    edited = image.copy()
                edited.putpixel((x, y), (0, 0, 0) if edited.getpixel((x, y)) != (0, 0, 0) else (255, 255, 255))
                edited.save(png)
                self.assertEqual(self.run_wrapper("inject-art", "npc").returncode, 0)
                changed = [index for index, (old, new) in enumerate(zip(rom, self.working.read_bytes())) if old != new]
                self.assertTrue(changed)
                self.assertTrue(all(offset <= index < offset + 16 for index in changed), changed)
                self.run_wrapper("reset")

    def test_npc_injection_writes_egghead_edit_to_both_copies(self):
        # Sheet pixel (0, 17) is the top-left corner of the first egghead enemy frame (0xE25A).
        rom = self.use_npc_rom()
        self.run_wrapper("reset")
        self.assertEqual(self.run_wrapper("dump-art", "npc").returncode, 0)
        png = self.root / "working" / "npc-art.png"
        with Image.open(png) as image:
            edited = image.copy()
        edited.putpixel((0, 17), (0, 0, 0) if edited.getpixel((0, 17)) != (0, 0, 0) else (255, 255, 255))
        edited.save(png)
        self.assertEqual(self.run_wrapper("inject-art", "npc").returncode, 0)
        out = self.working.read_bytes()
        self.assertNotEqual(out[0xE25A:0xE29A], rom[0xE25A:0xE29A])
        self.assertNotEqual(out[0x1869E:0x186DE], rom[0x1869E:0x186DE])
        self.assertEqual(out[0x1869E:0x186DE], out[0xE25A:0xE29A])

    def test_npc_injection_wrong_size_does_not_change_rom_or_log(self):
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        Image.new("RGB", (1, 1)).save(self.root / "working" / "npc-art.png")
        result = self.run_wrapper("inject-art", "npc")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected a 203x169 image", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_npc_injection_short_rom_fails_without_changing_working_copy(self):
        self.use_input_rom(bytes(0x1000))
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        Image.new("RGB", (203, 169)).save(self.root / "working" / "npc-art.png")
        result = self.run_wrapper("inject-art", "npc")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ROM does not contain all documented NPC and enemy graphics", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_dump_font_writes_six_by_eight_glyph_sheet_with_red_grid(self):
        self.run_wrapper("reset")
        result = self.run_wrapper("dump-font")
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.root / "working" / "font-art.png") as image:
            self.assertEqual(image.size, (53, 71))
            red = (255, 0, 0)
            # Red lines separate the glyphs horizontally (x=8) and vertically (y=8).
            self.assertEqual(image.getpixel((0, 8)), red)
            self.assertEqual(image.getpixel((8, 0)), red)
            self.assertNotEqual(image.getpixel((0, 9)), red)

    def test_font_synonyms_match_and_log_their_own_spelling(self):
        self.run_wrapper("reset")
        self.assertEqual(self.run_wrapper("dump-art", "font").returncode, 0)
        dumped = (self.root / "working" / "font-art.png").read_bytes()
        self.assertEqual(self.run_wrapper("dump-font").returncode, 0)
        self.assertEqual((self.root / "working" / "font-art.png").read_bytes(), dumped)
        png = self.root / "working" / "font-art.png"
        with Image.open(png) as image:
            edited = image.copy()
        original_pixel = edited.getpixel((0, 0))
        changed_pixel = (0, 0, 0) if original_pixel != (0, 0, 0) else (255, 255, 255)
        edited.putpixel((0, 0), changed_pixel)
        edited.save(png)
        self.assertEqual(self.run_wrapper("inject-art", "font").returncode, 0)
        changed_rom = self.working.read_bytes()
        self.assertNotEqual(changed_rom, self.rom)
        self.assertEqual(self.run_wrapper("inject-font").returncode, 0)
        self.assertEqual(self.hacks_log.read_text(), "inject-art font\n")
        edited.putpixel((0, 0), original_pixel)
        edited.save(png)
        self.assertEqual(self.run_wrapper("inject-font").returncode, 0)
        self.assertEqual(self.working.read_bytes(), self.rom)
        self.assertEqual(self.hacks_log.read_text(), "inject-art font\ninject-font\n")

    def test_font_round_trip_leaves_rom_unchanged(self):
        self.run_wrapper("reset")
        self.assertEqual(self.run_wrapper("dump-font").returncode, 0)
        result = self.run_wrapper("inject-font")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), self.rom)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_font_edit_changes_only_its_glyph_byte(self):
        # Glyphs fill the sheet in ROM order: glyph 2t is the top of tile t and 2t+1 is its bottom.
        # Each cell is 8x8 on a 9-pixel pitch, so sheet pixel (x, y) is row 0 of the glyph at
        # cell (x // 9, y // 9). Pixel (9, 0) is glyph 1 (tile 0, bottom), (0, 9) is glyph 6
        # (tile 3, top), and (0, 18) is glyph 12 (tile 6, top).
        for x, y, offset in ((0, 0, 0xB986), (9, 0, 0xB98E), (0, 9, 0xB9B6), (0, 18, 0xB9E6)):
            with self.subTest(offset=hex(offset)):
                self.run_wrapper("reset")
                self.assertEqual(self.run_wrapper("dump-font").returncode, 0)
                png = self.root / "working" / "font-art.png"
                with Image.open(png) as image:
                    edited = image.copy()
                edited.putpixel((x, y), (0, 0, 0) if edited.getpixel((x, y)) != (0, 0, 0) else (255, 255, 255))
                edited.save(png)
                self.assertEqual(self.run_wrapper("inject-font").returncode, 0)
                changed = [index for index, (old, new) in enumerate(zip(self.rom, self.working.read_bytes())) if old != new]
                self.assertEqual(changed, [offset])

    def test_font_injection_ignores_separator_pixels(self):
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        self.assertEqual(self.run_wrapper("dump-font").returncode, 0)
        png = self.root / "working" / "font-art.png"
        with Image.open(png) as image:
            edited = image.copy()
        edited.putpixel((8, 0), (0, 0, 0))
        edited.putpixel((0, 8), (0, 0, 0))
        edited.save(png)
        self.assertEqual(self.run_wrapper("inject-font").returncode, 0)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_font_injection_wrong_size_does_not_change_rom_or_log(self):
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        Image.new("RGB", (1, 1)).save(self.root / "working" / "font-art.png")
        result = self.run_wrapper("inject-font")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected a 53x71 image", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_font_injection_short_rom_fails_without_changing_working_copy(self):
        self.use_input_rom(bytes(0x1000))
        self.run_wrapper("reset")
        before = self.working.read_bytes()
        Image.new("RGB", (53, 71)).save(self.root / "working" / "font-art.png")
        result = self.run_wrapper("inject-font")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ROM does not contain the stacked font tiles", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")

    def test_dump_stats_writes_aligned_arrays_without_logging(self):
        rom = blank_rom(header=True)
        rom[0x17065] = 7
        self.use_input_rom(bytes(rom))
        self.run_wrapper("reset")
        log_before = self.hacks_log.read_text() if self.hacks_log.exists() else ""
        result = self.run_wrapper("dump-stats")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = (self.root / "working" / "stats.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 63)
        self.assertEqual(len({line.index(":") for line in lines}), 1)
        self.assertTrue(lines[0].startswith("hero_hp"))
        self.assertIn("[  7,", lines[0])
        self.assertEqual(lines[0].count(", "), 15)
        log_after = self.hacks_log.read_text() if self.hacks_log.exists() else ""
        self.assertEqual(log_after, log_before)

    def test_dump_stats_rejects_wrong_rom_without_writing(self):
        self.use_input_rom(bytes(0x1000))
        result = self.run_wrapper("dump-stats", str(self.root / "input" / ROM_NAME))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected a 131072-byte ROM", result.stderr)
        self.assertFalse((self.root / "working" / "stats.txt").exists())

    def test_inject_stats_partial_stock_unknown_and_repeat(self):
        stock = blank_rom(header=True)
        self.use_input_rom(bytes(stock))
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        working = bytearray(stock)
        working[0x17065:0x17075] = bytes([7] * 16)
        working[0x170E5:0x170F5] = bytes([9] * 16)
        working[0x15459:0x1545C] = bytes([3, 4, 5])
        self.working.write_bytes(working)
        stats = self.root / "working" / "stats.txt"
        stats.write_text(
            "unknown_array : [anything]\n"
            "hero_hp : [" + ", ".join(["0"] * 16) + "]\n"
            "hero_electricball_range : [\n" + ",\n".join(str(i + 10) for i in range(16)) + "]\n"
            "hero_mp : [" + ",".join(["9"] * 16) + "]\n",
            encoding="utf-8",
        )
        result = self.run_wrapper("inject-stats")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unknown_array", result.stdout)
        expected = bytearray(working)
        for level in range(16):
            expected[0x15459 + level * 3 + 1] = level + 10
        self.assertEqual(self.working.read_bytes(), expected)
        self.assertEqual(
            self.hacks_log.read_text(),
            "inject-stats hero_electricball_range: [" + ", ".join(str(i + 10) for i in range(16)) + "]\n",
        )
        result = self.run_wrapper("inject-stats")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), expected)
        self.assertEqual(len(self.hacks_log.read_text().splitlines()), 1)

    def test_inject_stats_dump_round_trip_and_multiple_changes(self):
        self.use_input_rom(bytes(blank_rom(header=True)))
        self.assertEqual(self.run_wrapper("dump-stats").returncode, 0)
        before = self.working.read_bytes()
        result = self.run_wrapper("inject-stats")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")
        stats = self.root / "working" / "stats.txt"
        stats.write_text(
            "hero_hp:[" + ",".join(["1"] * 16) + "]\n"
            "lookup_0x17165_table:[" + ",".join(["255"] * 16) + "]\n"
            "zold_specialblade_damage:[" + ",".join(["8"] * 16) + "]\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [str(self.root / "rc2h"), "inject-stats"],
            cwd=self.root / "input", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = bytearray(before)
        expected[0x17065:0x17075] = bytes([1] * 16)
        expected[0x17165:0x17175] = bytes([255] * 16)
        expected[0x15CA6:0x15CB6] = bytes([8] * 16)
        self.assertEqual(self.working.read_bytes(), expected)
        self.assertEqual(
            self.hacks_log.read_text(),
            "inject-stats hero_hp: [" + ", ".join(["1"] * 16) + "]\n"
            "inject-stats lookup_0x17165_table: [" + ", ".join(["255"] * 16) + "]\n"
            "inject-stats zold_specialblade_damage: [" + ", ".join(["8"] * 16) + "]\n",
        )

    def test_inject_stats_invalid_data_preserves_rom_and_log(self):
        self.use_input_rom(bytes(blank_rom(header=True)))
        self.assertEqual(self.run_wrapper("reset").returncode, 0)
        before = self.working.read_bytes()
        stats = self.root / "working" / "stats.txt"
        stats.write_text(
            "hero_hp:[" + ",".join(["1"] * 16) + "]\nhero_mp: [256]\n",
            encoding="utf-8",
        )
        result = self.run_wrapper("inject-stats")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hero_mp", result.stderr)
        self.assertEqual(self.working.read_bytes(), before)
        self.assertEqual(self.hacks_log.read_text(), "")


if __name__ == "__main__":
    unittest.main()
