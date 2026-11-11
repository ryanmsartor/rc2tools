import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
try:
    SPEC = importlib.util.spec_from_file_location("dump_text", ROOT / "bin" / "dump_text.py")
    dump_text = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(dump_text)
finally:
    sys.path.pop(0)


class DumpTextTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytearray(0x20000)
        self.rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        self.rom[0x147:0x149] = b"\x06\x02"

    def test_exact_format_ranges_overlaps_and_placeholders(self):
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
            (0x043C3, 0x043CA): "    pit",
            (0x043CA, 0x043D3): "     lane",
            (0x043D3, 0x043DB): "    kyle",
            (0x043DB, 0x043E3): "    jude",
            (0x043E3, 0x043EA): "    lee",
            (0x043EA, 0x043F3): "     lora",
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
        self.assertEqual(len(ranges), 174)
        self.assertEqual(len(lines), len(ranges))
        self.assertEqual(len(ranges), len(set(ranges)))
        self.assertTrue(all(
            line.startswith(f"0x{start:05X}-0x{end:05X} : ")
            for line, (start, end) in zip(lines, ranges)
        ))
        self.assertIn("0x1BABA-0x1BACC : a+ %" + " " * 14, lines)
        self.assertIn("0x04C77-0x04C81 : chr change", lines)
        self.assertIn("0x00134-0x00144 : ROLAN'S CURSE 2^", lines)
        for (start, end), text in item_fragments.items():
            self.assertIn(f"0x{start:05X}-0x{end:05X} : {text}", lines)
        self.assertIn((0x1C0C0, 0x1C0F7), ranges)
        self.assertIn((0x1C0F5, 0x1C10B), ranges)
        self.assertIn((0x1CA4E, 0x1CAC5), ranges)
        self.assertIn((0x1CAAB, 0x1CAC5), ranges)
        self.assertIn((0x1E68A, 0x1E68B), ranges)
        self.assertIn((0x1E68A, 0x1E6AB), ranges)

    def test_short_rom_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "too short"):
            dump_text.dump_text(b"\0" * 100)

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
                self.assertIn(f"0x{start:05X}-0x{end:05X} : {text}", lines)
        self.assertIn((0x04736, 0x04823), dump_text.TEXT_RANGES)

    def test_wrapper_defaults_explicit_paths_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bin").mkdir()
            (root / "input").mkdir()
            shutil.copy2(ROOT / "rc2t", root / "rc2t")
            for name in ("dump_text.py", "render_text.py", "known_graphics.py", "rom_stats.py"):
                shutil.copy2(ROOT / "bin" / name, root / "bin" / name)
            rom = root / "input" / "Rolan's Curse II (USA).gb"
            rom.write_bytes(self.rom)
            result = subprocess.run(
                ["bash", str(root / "rc2t"), "dump-text"],
                cwd=root / "input", capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = root / "output" / "known-text.txt"
            self.assertEqual(output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))

            self.rom[0x1BABA] = 0xFD
            rom.write_bytes(self.rom)
            custom_output = root / "custom output.txt"
            result = subprocess.run(
                ["bash", str(root / "rc2t"), "dump-text", str(rom), str(custom_output)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(custom_output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))

            hex_path = root / "game.hex"
            rows = []
            for offset in range(0, len(self.rom), 16):
                chunk = self.rom[offset:offset + 16]
                groups = " ".join(chunk[i:i + 2].hex() for i in range(0, 16, 2))
                rows.append(f"{offset:08x}: {groups}  ................")
            hex_path.write_text("\n".join(rows) + "\n", encoding="ascii")
            result = subprocess.run(
                ["bash", str(root / "rc2t"), "dump-text", str(hex_path), str(custom_output)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(custom_output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))

            rom.write_bytes(b"short")
            result = subprocess.run(
                ["bash", str(root / "rc2t"), "dump-text", str(rom), str(custom_output)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected a 131072-byte ROM", result.stderr)
            self.assertEqual(custom_output.read_text(encoding="utf-8"), dump_text.dump_text(self.rom))


if __name__ == "__main__":
    unittest.main()
