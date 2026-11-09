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
        lines = dump_text.dump_text(self.rom).splitlines()
        ranges = sorted((dump_text.TITLE_RANGE, *dump_text.TEXT_RANGES))
        self.assertEqual(len(ranges), 100)
        self.assertEqual(len(lines), len(ranges))
        self.assertEqual(len(ranges), len(set(ranges)))
        self.assertTrue(all(
            line.startswith(f"0x{start:05X}-0x{end:05X} : ")
            for line, (start, end) in zip(lines, ranges)
        ))
        self.assertIn("0x1BABA-0x1BACC : a+▎%" + " " * 14, lines)
        self.assertIn("0x00134-0x00144 : ROLAN'S CURSE 2^", lines)
        self.assertIn((0x1C0C0, 0x1C0F7), ranges)
        self.assertIn((0x1C0F5, 0x1C10B), ranges)
        self.assertIn((0x1CA4E, 0x1CAC5), ranges)
        self.assertIn((0x1CAAB, 0x1CAC5), ranges)
        self.assertIn((0x1E68A, 0x1E68B), ranges)
        self.assertIn((0x1E68A, 0x1E6AB), ranges)

    def test_short_rom_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "too short"):
            dump_text.dump_text(b"\0" * 100)

    def test_wrapper_defaults_explicit_paths_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bin").mkdir()
            (root / "input").mkdir()
            shutil.copy2(ROOT / "rc2t", root / "rc2t")
            for name in ("dump_text.py", "render_text.py", "extract_json.py"):
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
