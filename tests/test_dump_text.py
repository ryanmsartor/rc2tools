import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import blank_rom, copy_tool_tree, load_bin_module

dump_text = load_bin_module("dump_text")


class DumpTextTests(unittest.TestCase):
    def setUp(self):
        self.rom = blank_rom(header=True)

    def test_exact_format_ranges_and_placeholders(self):
        self.rom[0x1BABA:0x1BACC] = bytes([0x0A, 0xFD, 0xFE, 0x01] + [0xB2] * 14)
        item_fragments = {
            (0x040A2, 0x040AC): " large    ",
            (0x040B0, 0x040BC): "  potions   ",
            (0x040CC, 0x040D6): " fairy's  ",
            (0x040DA, 0x040E6): "    tears   ",
            (0x040F6, 0x04100): " magic    ",
            (0x04104, 0x04110): "     ball   ",
            (0x04120, 0x0412A): " fairy    ",
            (0x0412E, 0x0413A): "    wings   ",
            (0x041AF, 0x041B3): " itm",
            (0x041BB, 0x041BF): " pow",
            (0x041C1, 0x041C5): " map",
            (0x041C7, 0x041CB): " sav",
            (0x043C3, 0x043CB): "    pit ",
            (0x043CB, 0x043D3): "    lane",
            (0x043D3, 0x043DB): "    kyle",
            (0x043DB, 0x043E3): "    jude",
            (0x043E3, 0x043EB): "    lee ",
            (0x043EB, 0x043F3): "    lora",
            (0x043F3, 0x043FB): "    zold",
            (0x04999, 0x0499F): "narrow",
            (0x0499F, 0x049A5): "middle",
            (0x049A5, 0x049AB): "  wide",
            (0x049AB, 0x049B1): " short",
            (0x049B1, 0x049B7): "  long",
            (0x04A7D, 0x04A83): "knight",
            (0x04A83, 0x04A87): "pit ",
            (0x04A87, 0x04A8A): "elf",
            (0x04A8A, 0x04A8E): "lane",
            (0x04A8E, 0x04A94): "cleric",
            (0x04A94, 0x04A98): "kyle",
            (0x04A98, 0x04A9E): "zombie",
            (0x04A9E, 0x04AA2): "jude",
            (0x04AA2, 0x04AA8): "wizard",
            (0x04AA8, 0x04AAC): "lee ",
            (0x04AAC, 0x04AB2): "kungfu",
            (0x04AB2, 0x04AB6): "lora",
            (0x04AB6, 0x04ABB): "cupid",
            (0x04ABB, 0x04ABF): "zold",
            (0x04ABF, 0x04AC5): "master",
        }
        for (start, end), text in item_fragments.items():
            data = bytes(
                0xFE if character == " " else 0x24 if character == "'" else 0x0A + ord(character) - ord("a")
                for character in text
            )
            self.assertEqual(len(data), end - start)
            self.rom[start:end] = data
        self.rom[0x04C77:0x04C81] = bytes([0x0C, 0x11, 0x1B, 0xFE, 0x0C, 0x11, 0x0A, 0x17, 0x10, 0x0E])

        lines = dump_text.dump_text(self.rom).splitlines()
        ranges = sorted((dump_text.TITLE_RANGE, *dump_text.TEXT_RANGES))
        self.assertEqual(len(ranges), 238)
        self.assertEqual(len(lines), len(ranges))
        self.assertEqual(len(ranges), len(set(ranges)))
        self.assertTrue(all(
            line.startswith(f"0x{start:05X}-0x{end:05X} : ")
            for line, (start, end) in zip(lines, ranges)
        ))
        self.assertIn("0x1BABA-0x1BACB : a+_%" + " " * 13, lines)
        self.assertIn("0x04C77-0x04C81 : chr_change", lines)
        self.assertIn("0x00134-0x00143 : ROLAN'S CURSE 2", lines)
        for (start, end), text in item_fragments.items():
            self.assertIn(f"0x{start:05X}-0x{end:05X} : {text.replace(' ', '_')}", lines)
        self.assertIn((0x1C0C0, 0x1C0F5), ranges)
        self.assertIn((0x1C10C, 0x1C13E), ranges)
        self.assertNotIn((0x1C0F5, 0x1C10B), ranges)
        self.assertIn((0x1CA4E, 0x1CAC4), ranges)
        self.assertNotIn((0x1CAAB, 0x1CAC5), ranges)
        self.assertNotIn((0x1D362, 0x1D382), ranges)
        self.assertNotIn((0x1E68A, 0x1E68B), ranges)
        self.assertNotIn((0x1E68A, 0x1E6AB), ranges)
        self.assertNotIn((0x1E2E6, 0x1E314), ranges)
        self.assertIn((0x1B9A1, 0x1B9C6), ranges)
        self.assertNotIn((0x1B9A1, 0x1B9B3), ranges)
        self.assertNotIn((0x1B9B3, 0x1B9C0), ranges)
        self.assertNotIn((0x1B9C0, 0x1B9C6), ranges)
        self.assertNotIn((0x1BABA, 0x1BACC), ranges)
        self.assertNotIn((0x1CCE9, 0x1CCFD), ranges)
        self.assertTrue(all(
            previous[1] <= current[0]
            for previous, current in zip(ranges, ranges[1:])
        ))

    def test_text_ranges_exclude_end_markers_and_marker_only_ranges(self):
        self.rom[0x1C221] = 0xFF
        self.rom[0x1C222:0x1C257] = bytes([0x0A] * (0x1C257 - 0x1C222))
        self.rom[0x1C257] = 0xFF

        output = dump_text.dump_text(self.rom)

        self.assertNotIn("#", output)
        self.assertNotIn("0x1C221-0x1C222", output)
        self.assertNotIn((0x1C221, 0x1C222), dump_text.TEXT_RANGES)
        self.assertIn(f"0x1C222-0x1C257 : {'a' * (0x1C257 - 0x1C222)}", output)

    def test_story_text_ranges_exclude_unknown_control_sequences(self):
        fragments = (
            (0x1C0C0, 0x1C0F5),
            (0x1C10C, 0x1C13E),
            (0x1C3AE, 0x1C441),
            (0x1C444, 0x1C48C),
            (0x1C492, 0x1C4B4),
            (0x1D028, 0x1D19D),
            (0x1D1A0, 0x1D230),
            (0x1E025, 0x1E13E),
            (0x1E143, 0x1E172),
            (0x1E2AB, 0x1E2D4),
            (0x1E2E7, 0x1E313),
        )
        control_spans = (
            (0x1C0F5, 0x1C10B), (0x1C13E, 0x1C1AC), (0x1C209, 0x1C221),
            (0x1C32A, 0x1C32D), (0x1C441, 0x1C444), (0x1C48C, 0x1C492),
            (0x1C515, 0x1C51C), (0x1C77F, 0x1C787), (0x1C81D, 0x1C820),
            (0x1C917, 0x1C91D), (0x1C98A, 0x1C991), (0x1CFA8, 0x1CFAB),
            (0x1D19D, 0x1D1A0), (0x1D230, 0x1D236), (0x1D2BF, 0x1D2C7),
            (0x1D55D, 0x1D563), (0x1D778, 0x1D780), (0x1DBAD, 0x1DBB5),
            (0x1DCFB, 0x1DD01), (0x1DE18, 0x1DE20), (0x1DF78, 0x1DF7B),
            (0x1DFAF, 0x1DFB5), (0x1E13E, 0x1E142), (0x1E172, 0x1E17A),
            (0x1E2D4, 0x1E2E6),
        )
        dump_ranges = set(dump_text.TEXT_RANGES)
        graphics = load_bin_module("render_graphics")
        graphics_ranges = set(graphics.KNOWN_TEXT_RANGES)
        self.assertTrue(set(fragments).issubset(dump_ranges))
        for start, end in fragments:
            with self.subTest(fragment=(hex(start), hex(end))):
                self.assertEqual(graphics.known_kind(start), "text")
                self.assertEqual(graphics.known_kind(end - 1), "text")
        for control_start, control_end in control_spans:
            with self.subTest(control=(hex(control_start), hex(control_end))):
                self.assertFalse(any(
                    start < control_end and control_start < end
                    for start, end in dump_ranges | graphics_ranges
                ))

    def test_story_fragment_excludes_leading_space(self):
        self.rom[0x1E142:0x1E148] = bytes([0xFE, 0x23, 0x18, 0x15, 0x0D, 0x2D])

        output = dump_text.dump_text(self.rom)

        self.assertIn("0x1E143-0x1E172 : zold:", output)
        self.assertNotIn("0x1E142-0x1E172", output)

    def test_ending_credit_ranges_exclude_control_codes_and_include_final_text(self):
        fragments = (
            (0x0BC8A, 0x0BCBD), (0x0BCBE, 0x0BCEC), (0x0BCED, 0x0BD16),
            (0x0BD24, 0x0BD54), (0x0BD55, 0x0BD64), (0x0BD6B, 0x0BDA0),
            (0x0BDA1, 0x0BDA7), (0x0BDAE, 0x0BDE0), (0x0BDE1, 0x0BE08),
            (0x0BE0F, 0x0BE3D), (0x0BE3E, 0x0BE55), (0x0BE5C, 0x0BE8F),
            (0x0BE96, 0x0BEC5), (0x0BECC, 0x0BEFE), (0x0BF05, 0x0BF32),
            (0x0BF33, 0x0BF64), (0x0BF65, 0x0BF98), (0x0BF99, 0x0BFAD),
        )
        ranges = set(dump_text.TEXT_RANGES)
        graphics_ranges = set(load_bin_module("render_graphics").KNOWN_TEXT_RANGES)
        self.assertTrue(set(fragments).issubset(ranges))
        self.assertTrue(set(fragments).issubset(graphics_ranges))
        self.assertNotIn((0x0BC86, 0x0BD1D), ranges)
        self.assertNotIn((0x0BD1E, 0x0BFAB), ranges)
        for control in (0x0BCBD, 0x0BCEC, 0x0BD16, 0x0BD1E, 0x0BD20, 0x0BD54, 0x0BD64, 0x0BD65, 0x0BD66, 0x0BD67, 0x0BDA0, 0x0BDA7, 0x0BDA8, 0x0BDA9, 0x0BDAA, 0x0BDE0, 0x0BE08, 0x0BE55, 0x0BE8F, 0x0BEC5, 0x0BEFE, 0x0BF32, 0x0BF64, 0x0BF98, 0x0BFAD):
            with self.subTest(control=hex(control)):
                self.assertFalse(any(start <= control < end for start, end in fragments))

    def test_character_names_and_level_are_individual_fragments(self):
        fragments = (
            (0x1B311, 0x1B315, "pit "),
            (0x1B315, 0x1B319, "lane"),
            (0x1B319, 0x1B31D, "kyle"),
            (0x1B31D, 0x1B321, "jude"),
            (0x1B321, 0x1B325, "lee "),
            (0x1B325, 0x1B329, "lora"),
            (0x1B329, 0x1B32D, "zold"),
            (0x1B32D, 0x1B331, " lv."),
        )
        for start, end, text in fragments:
            self.rom[start:end] = bytes(
                0xFE if character == " " else 0x27 if character == "." else ord(character) - ord("a") + 0x0A
                for character in text
            )

        ranges = set(dump_text.TEXT_RANGES)
        highlighted_ranges = load_bin_module("render_graphics").KNOWN_TEXT_RANGES
        lines = dump_text.dump_text(self.rom).splitlines()
        for start, end, text in fragments:
            with self.subTest(text=text):
                self.assertIn((start, end), ranges)
                self.assertIn((start, end), highlighted_ranges)
                self.assertIn(f"0x{start:05X}-0x{end:05X} : {text.replace(' ', '_')}", lines)
        self.assertNotIn((0x1B315, 0x1B32E), ranges)

    def test_short_rom_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "too short"):
            dump_text.dump_text(b"\0" * 100)

    def test_place_names_are_dumped_as_individual_fragments(self):
        fragments = (
            (0x17C8E, 0x17C94, "graves"),
            (0x17C94, 0x17C9B, "keepers"),
            (0x17C9B, 0x17CA1, "fields"),
            (0x17CA1, 0x17CA7, "castle"),
            (0x17CA7, 0x17CAC, "baroa"),
            (0x17CAC, 0x17CB1, "cadal"),
            (0x17CB1, 0x17CB7, "virgin"),
            (0x17CB7, 0x17CBF, "mushroom"),
            (0x17CBF, 0x17CC5, "duwane"),
            (0x17CC5, 0x17CCB, "metals"),
            (0x17CCB, 0x17CD0, "ruins"),
            (0x17CD0, 0x17CD5, "guild"),
            (0x17CD5, 0x17CDC, "fossils"),
            (0x17CDC, 0x17CE3, "canyons"),
            (0x17CE3, 0x17CEB, "farewell"),
            (0x17CEB, 0x17CF3, "dungeons"),
        )
        for start, end, text in fragments:
            self.rom[start:end] = bytes(ord(character) - ord("a") + 0x0A for character in text)

        ranges = set(dump_text.TEXT_RANGES)
        lines = dump_text.dump_text(self.rom).splitlines()
        self.assertNotIn((0x17C8D, 0x17CF4), ranges)
        for start, end, text in fragments:
            with self.subTest(fragment=text):
                self.assertIn((start, end), ranges)
                self.assertIn(f"0x{start:05X}-0x{end:05X} : {text}", lines)

    def test_only_selected_alphabet_table_is_dumped(self):
        included = (0x1BD4E, 0x1BD6F)
        excluded = (
            (0x050CB, 0x050E7),
            (0x05109, 0x0511B),
            (0x058EB, 0x0590F),
            (0x17D4E, 0x17D6F),
            (0x17D70, 0x17D80),
            (0x1BD70, 0x1BD80),
        )
        ranges = set(dump_text.TEXT_RANGES)
        graphics_ranges = load_bin_module("render_graphics").KNOWN_TEXT_RANGES
        self.assertIn(included, ranges)
        self.assertIn(included, graphics_ranges)
        for item in excluded:
            with self.subTest(range=item):
                self.assertNotIn(item, ranges)
                self.assertIn(item, graphics_ranges)
        lines = dump_text.dump_text(self.rom).splitlines()
        prefix = f"0x{included[0]:05X}-0x{included[1]:05X} : "
        self.assertTrue(any(line.startswith(prefix) for line in lines))

    def test_ability_and_stat_fragments_have_individual_lines(self):
        fragments = (
            (0x0471B, 0x04721, "damage"), (0x04722, 0x04727, "range"),
            (0x04728, 0x0472E, " range"), (0x0472F, 0x04736, " effect"),
            (0x04737, 0x04740, "pathmaker"), (0x04740, 0x0474A, "halfshield"),
            (0x0474A, 0x04750, "revive"), (0x04751, 0x04759, "nodamage"),
            (0x04759, 0x04761, "teleport"), (0x04761, 0x04764, "arc"),
            (0x04764, 0x04769, "sword"), (0x04769, 0x04770, " sabre "),
            (0x04770, 0x0477C, "electricball"), (0x0477C, 0x04783, "dagger "),
            (0x04783, 0x0478D, "boomer-ang"), (0x0478D, 0x04794, " bomb  "),
            (0x04794, 0x0479B, " staff "), (0x0479B, 0x047A1, "shield"),
            (0x047A1, 0x047A7, "  heal"), (0x047A7, 0x047B0, "   bone  "),
            (0x047B0, 0x047B8, "playdead"), (0x047B8, 0x047BF, "thunder"),
            (0x047BF, 0x047C7, "fireball"), (0x047C7, 0x047D0, "smashball"),
            (0x047D0, 0x047D6, " quake"), (0x047D6, 0x047DE, "   sai  "),
            (0x047DE, 0x047E7, "rapidfire"), (0x047E7, 0x047EF, "firework"),
            (0x047EF, 0x047F5, " arrow"), (0x047F5, 0x047FB, "  heal"),
            (0x047FB, 0x04804, "   wings "), (0x04804, 0x0480D, "darkblade"),
            (0x0480D, 0x04819, "specialblade"), (0x04819, 0x04821, "megaball"),
        )
        for start, end, text in fragments:
            data = bytes(0xFE if char == " " else 0x26 if char == "-" else ord(char) - ord("a") + 0x0A for char in text)
            self.assertEqual(len(data), end - start)
            self.rom[start:end] = data

        lines = dump_text.dump_text(self.rom).splitlines()
        for start, end, text in fragments:
            with self.subTest(start=hex(start)):
                self.assertIn((start, end), dump_text.TEXT_RANGES)
                dump_text_value = text.replace(" ", "_").replace("-", "=")
                self.assertIn(f"0x{start:05X}-0x{end:05X} : {dump_text_value}", lines)
        self.assertNotIn((0x04736, 0x04823), dump_text.TEXT_RANGES)

    def test_dump_uses_distinct_glyphs_for_fe_and_hyphens(self):
        self.rom[0x1BD6D] = 0x2B
        self.rom[0x1E143:0x1E147] = bytes([0xFE, 0x0B, 0x26, 0x2B])

        lines = dump_text.dump_text(self.rom).splitlines()
        alphabet = next(line for line in lines if line.startswith("0x1BD4E-0x1BD6F"))
        story = next(line for line in lines if line.startswith("0x1E143-0x1E172"))

        self.assertEqual(alphabet.split(" : ", 1)[1][31], "-")
        self.assertEqual(story.split(" : ", 1)[1][:4], "_b=-")

    def test_wrapper_defaults_explicit_paths_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input").mkdir()
            copy_tool_tree(root)
            rom = root / "input" / "Rolan's Curse II (USA).gb"
            rom.write_bytes(self.rom)
            result = subprocess.run(
                ["bash", str(root / "rc2h"), "dump-text"],
                cwd=root / "input", capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = root / "working" / "strings.txt"
            self.assertEqual(output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))

            rc2t_help = subprocess.run(
                ["bash", str(root / "rc2t"), "--help"],
                capture_output=True, text=True,
            )
            self.assertNotIn("dump-text", rc2t_help.stdout)

            self.rom[0x1BABA] = 0xFD
            rom.write_bytes(self.rom)
            result = subprocess.run(
                ["bash", str(root / "rc2h"), "dump-text", str(rom)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))

            custom_output = root / "custom output.txt"
            result = subprocess.run(
                ["bash", str(root / "rc2h"), "dump-text", str(rom), str(custom_output)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(custom_output.exists())

            hex_path = root / "game.hex"
            rows = []
            for offset in range(0, len(self.rom), 16):
                chunk = self.rom[offset:offset + 16]
                groups = " ".join(chunk[i:i + 2].hex() for i in range(0, 16, 2))
                rows.append(f"{offset:08x}: {groups}  ................")
            hex_path.write_text("\n".join(rows) + "\n", encoding="ascii")
            result = subprocess.run(
                ["bash", str(root / "rc2h"), "dump-text", str(hex_path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))

            rom.write_bytes(b"short")
            result = subprocess.run(
                ["bash", str(root / "rc2h"), "dump-text", str(rom)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected a 131072-byte ROM", result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))


if __name__ == "__main__":
    unittest.main()
