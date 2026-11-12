import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import blank_rom, copy_tool_tree, load_bin_module
from rom_io import read_rom

dump_text = load_bin_module("dump_text")
inject_text = load_bin_module("inject_text")


class InjectTextTests(unittest.TestCase):
    def setUp(self):
        self.rom = blank_rom(header=True)
        for start, end in dump_text.TEXT_RANGES:
            self.rom[start:end] = bytes([0x0A]) * (end - start)
        inject_text._update_checksums(self.rom)
        self.original = bytes(self.rom)
        self.text = dump_text.dump_text(self.original)
        self.lines = self.text.splitlines()

    def replace_segment(self, start, end, value):
        prefix = f"0x{start:05X}-0x{end:05X} : "
        for index, line in enumerate(self.lines):
            if line.startswith(prefix):
                self.lines[index] = prefix + value
                return
        self.fail(f"missing test segment {prefix}")

    def test_injecting_unmodified_dump_preserves_rom(self):
        self.assertEqual(inject_text.inject_text(self.original, self.text), self.original)

    def test_changed_characters_encode_fe_hyphens_and_space_bytes(self):
        start, end = 0x1B311, 0x1B315
        self.rom[start:end] = bytes([0x19, 0x12, 0x1D, 0xFE])
        self.rom[0x1B315:0x1B319] = bytes([0x15, 0x0A, 0x17, 0x0E])
        self.rom[0x13D60:0x13D74] = bytes([0x0A] * 20)
        self.rom[0x04783:0x0478D] = bytes([0x0A] * 10)
        self.rom[0x1E26F:0x1E294] = bytes([0x0A] * 37)
        source = bytes(self.rom)
        lines = dump_text.dump_text(source).splitlines()
        self.lines = lines

        self.replace_segment(0x1B311, 0x1B315, "cat_")
        self.replace_segment(0x1B315, 0x1B319, "la e")
        self.replace_segment(0x13D60, 0x13D74, " " + "a" * 19)
        self.replace_segment(0x04783, 0x0478D, "boomer=ang")
        self.replace_segment(0x1E26F, 0x1E294, "cock-a-doodle-doo!+wake up, would ya!")

        result = inject_text.inject_text(source, "\n".join(self.lines) + "\n")

        self.assertEqual(result[start:end], bytes([0x0C, 0x0A, 0x1D, 0xFE]))
        self.assertEqual(result[0x1B315:0x1B319], bytes([0x15, 0x0A, 0xB2, 0x0E]))
        self.assertEqual(result[0x13D60], 0x30)
        self.assertEqual(result[0x04783 + 6], 0x26)
        self.assertEqual(result[0x1E26F + 4], 0x2B)

    def test_short_segments_are_padded_with_their_space_byte(self):
        self.rom[0x1B311:0x1B315] = bytes([0x19, 0x12, 0x1D, 0xFE])
        source = bytes(self.rom)
        self.lines = dump_text.dump_text(source).splitlines()
        self.replace_segment(0x1B311, 0x1B315, "pi")
        self.replace_segment(0x13D60, 0x13D74, "x")

        result = inject_text.inject_text(source, "\n".join(self.lines) + "\n")

        self.assertEqual(result[0x1B311:0x1B315], bytes([0x19, 0x12, 0xB2, 0xB2]))
        self.assertEqual(result[0x13D60:0x13D74], bytes([0x21, *([0x30] * 19)]))

    def test_overlong_segment_reports_range_and_character_counts(self):
        self.replace_segment(0x1B311, 0x1B315, "abcde")

        with self.assertRaisesRegex(
            ValueError,
            r"0x1B311-0x1B315.*maximum length of 4 characters "
            r"\(attempted 5 characters\)",
        ):
            inject_text.inject_text(self.original, "\n".join(self.lines) + "\n")

    def test_allowed_characters_are_derived_from_the_base_rom_dump(self):
        base_dump = dump_text.dump_text(
            read_rom(inject_text.DEFAULT_ROM)
        )
        expected = frozenset(
            character
            for line in base_dump.splitlines()
            if not line.startswith(
                f"0x{dump_text.TITLE_RANGE[0]:05X}-"
                f"0x{dump_text.TITLE_RANGE[1]:05X} : "
            )
            for character in line.partition(" : ")[2]
        )

        self.assertEqual(inject_text.allowed_characters(), expected)
        self.assertTrue(set("2ACLNSU").isdisjoint(expected))
        self.assertTrue(set("HERO").issubset(expected))

    def test_title_is_excluded_from_identity_validation_but_not_length_validation(self):
        self.replace_segment(*dump_text.TITLE_RANGE, "ROLAN'S CURSE Z")
        result = inject_text.inject_text(self.original, "\n".join(self.lines) + "\n")
        self.assertEqual(result[dump_text.TITLE_RANGE[0]:dump_text.TITLE_RANGE[1]][-1], ord("Z"))

        self.replace_segment(*dump_text.TITLE_RANGE, "ROLAN'S CURSE 22")
        with self.assertRaisesRegex(
            ValueError,
            r"0x00134-0x00143.*maximum length of 15 characters "
            r"\(attempted 16 characters\)",
        ):
            inject_text.inject_text(self.original, "\n".join(self.lines) + "\n")

    def test_invalid_character_reports_character_range_and_dense_allowed_list(self):
        self.replace_segment(0x1B311, 0x1B315, "abéc")

        with self.assertRaises(ValueError) as raised:
            inject_text.inject_text(self.original, "\n".join(self.lines) + "\n")

        message = str(raised.exception)
        self.assertIn("invalid character 'é'", message)
        self.assertIn("range 0x1B311-0x1B315", message)
        self.assertIn(
            'allowed characters: " !\'+,-.:=?EHOR_abcdefghijklmnopqrstuvwxyz"',
            message,
        )
        self.assertNotIn("é", inject_text.allowed_characters())

    def test_ambiguous_placeholder_glyphs_round_trip_by_source_position(self):
        self.rom[0x040A2:0x040A4] = bytes([0x05, 0x06])
        inject_text._update_checksums(self.rom)
        source = bytes(self.rom)

        self.assertEqual(
            inject_text.inject_text(source, dump_text.dump_text(source)),
            source,
        )

    def test_missing_and_duplicate_ranges_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing range"):
            inject_text.inject_text(self.original, "\n".join(self.lines[1:]))
        duplicate = self.lines + [self.lines[1]]
        with self.assertRaisesRegex(ValueError, "duplicate text range"):
            inject_text.inject_text(self.original, "\n".join(duplicate))

    def test_cli_writes_working_output_and_does_not_replace_it_on_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom_path = root / "rom.gb"
            text_path = root / "strings.txt"
            output_path = root / "working" / "injected.gb"
            rom_path.write_bytes(self.original)
            text_path.write_text(self.text, encoding="utf-8")
            previous_text_path = inject_text.DEFAULT_TEXT_PATH
            previous_output_path = inject_text.DEFAULT_OUTPUT
            self.addCleanup(setattr, inject_text, "DEFAULT_TEXT_PATH", previous_text_path)
            self.addCleanup(setattr, inject_text, "DEFAULT_OUTPUT", previous_output_path)
            inject_text.DEFAULT_TEXT_PATH = text_path
            inject_text.DEFAULT_OUTPUT = output_path

            self.assertEqual(inject_text.main([str(rom_path)]), 0)
            self.assertEqual(output_path.read_bytes(), self.original)

            self.replace_segment(0x1B311, 0x1B315, "abcde")
            text_path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
            previous_output = output_path.read_bytes()
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                self.assertEqual(inject_text.main([str(rom_path)]), 1)

            self.assertIn("0x1B311-0x1B315", error.getvalue())
            self.assertIn("maximum length of 4 characters", error.getvalue())
            self.assertIn("attempted 5 characters", error.getvalue())
            self.assertEqual(output_path.read_bytes(), previous_output)

            self.replace_segment(0x1B311, 0x1B315, "abéc")
            text_path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                self.assertEqual(inject_text.main([str(rom_path)]), 1)

            self.assertIn("invalid character 'é'", error.getvalue())
            self.assertIn("0x1B311-0x1B315", error.getvalue())
            self.assertIn("allowed characters:", error.getvalue())
            self.assertEqual(output_path.read_bytes(), previous_output)

    def test_rc2h_exposes_inject_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_tool_tree(root)
            result = subprocess.run(
                ["bash", str(root / "rc2h"), "--help"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("inject-text", result.stdout)


if __name__ == "__main__":
    unittest.main()
