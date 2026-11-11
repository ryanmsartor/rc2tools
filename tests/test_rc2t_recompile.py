import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT, copy_tool_tree, load_bin_module

decompile_rom = load_bin_module("decompile_rom")


class RecompileWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "input").mkdir()
        copy_tool_tree(self.root)

    def run_wrapper(self, command, *args, env=None):
        return subprocess.run(
            ["bash", str(self.root / "rc2t"), command, *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_missing_source_and_invalid_extension_are_reported(self):
        result = self.run_wrapper("recompile")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assembly file not found", result.stderr)
        self.assertIn("Rolan's Curse II (USA).asm", result.stderr)
        result = self.run_wrapper("recompile", "missing.asm")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assembly file not found", result.stderr)
        result = self.run_wrapper("recompile", "game.gb")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be an .asm file", result.stderr)

    def test_default_input_matches_default_rom_basename(self):
        source = self.root / "input" / "Rolan's Curse II (USA).asm"
        source.write_text('SECTION "game", ROM0[$0000]\nDB $42\n', encoding="utf-8")
        result = self.run_wrapper("recompile")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / "output" / "Rolan's Curse II (USA) (recompiled).gb"
        self.assertEqual(output.read_bytes(), b"\x42" + bytes(0x7FFF))

    def test_works_without_external_assembler(self):
        (self.root / "input" / "game.asm").write_text(
            'SECTION "game", ROM0[$0000]\n    NOP\n', encoding="utf-8"
        )
        output = self.root / "output" / "game (recompiled).gb"
        tools = self.root / "tools"
        tools.mkdir()
        os.symlink(shutil.which("python3"), tools / "python3")
        env = dict(os.environ, PATH=str(tools))
        result = subprocess.run(
            ["/bin/bash", str(self.root / "rc2t"), "recompile", "game.asm"],
            cwd=self.root, capture_output=True, text=True, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), bytes(0x8000))

    def test_round_trip_and_source_edits(self):
        data = bytearray(b"\0" * 0x8000)
        data[:8] = bytes([0x18, 0x80, 0xE8, 0xFE, 0xF8, 0x02, 0xCB, 0xFF])
        data[0x4000:0x4003] = bytes([0xEA, 0x80, 0xFF])
        rom = self.root / "input" / "game name.gb"
        rom.write_bytes(data)
        result = self.run_wrapper("decompile", str(rom))
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = self.root / "output" / "game name.asm"
        source = self.root / "input" / listing.name
        shutil.copy2(listing, source)
        result = self.run_wrapper("recompile", source.name)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / "output" / "game name (recompiled).gb"
        self.assertEqual(output.read_bytes(), data)

        text = source.read_text(encoding="utf-8")
        source.write_text(text.replace("    ADD SP,-2", "    ADD SP,-3", 1), encoding="utf-8")
        result = self.run_wrapper("recompile", str(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        data[3] = 0xFD
        self.assertEqual(output.read_bytes(), data)

        source.write_text('SECTION "bad", ROM0\n    NOT_AN_INSTRUCTION\n', encoding="utf-8")
        result = self.run_wrapper("recompile", source.name)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), data)

    def test_round_trip_all_opcodes_and_byte_operands(self):
        data = bytearray()
        for opcode in range(256):
            for value in range(256):
                instruction = bytes([opcode, value, 0xFF if value % 2 else 0])
                _, size = decompile_rom.decode_instruction(instruction, 0, 0x100)
                remaining = 0x4000 - len(data) % 0x4000
                if size > remaining:
                    data.extend(bytes(remaining))
                data.extend(instruction[:size])
        data.extend(bytes(-len(data) % 0x4000))
        rom = self.root / "input" / "all-opcodes.gb"
        rom.write_bytes(data)
        result = self.run_wrapper("decompile", str(rom), str(self.root / "input" / "all-opcodes.asm"))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_wrapper("recompile", "all-opcodes.asm")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "output" / "all-opcodes (recompiled).gb").read_bytes(), data)

    @unittest.skipUnless(
        (ROOT / "input" / "Rolan's Curse II (USA).gb").is_file(),
        "default ROM not available",
    )
    def test_round_trip_default_rom(self):
        rom = ROOT / "input" / "Rolan's Curse II (USA).gb"
        source = self.root / "input" / "game.asm"
        result = self.run_wrapper("decompile", str(rom), str(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = source.read_text(encoding="utf-8")
        self.assertIn("; Sprite: Hero idling down", listing)
        self.assertIn("; Sprite: Boss sprites (tentative", listing)
        self.assertIn("; Text: Dialogue or story text candidate", listing)
        self.assertIn("; Table: Hero HP by level", listing)
        self.assertIn("; Graphics: Stacked 1bpp glyphs:", listing)
        self.assertIn("; Code: Startup entry", listing)
        result = self.run_wrapper("recompile", source.name)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "output" / "game (recompiled).gb").read_bytes(), rom.read_bytes())


if __name__ == "__main__":
    unittest.main()
