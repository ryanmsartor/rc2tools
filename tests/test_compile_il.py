import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import copy_tool_tree, load_bin_module

compile_il = load_bin_module("compile_il")
recompile_rom = load_bin_module("recompile_rom")


class CompileSourceTests(unittest.TestCase):
    def test_assembly_without_directives_is_unchanged(self):
        source = 'SECTION "a; b", ROM0[$0000]\r\n    JR @+2-2 ; comment\r\n'
        self.assertEqual(compile_il.compile_source(source), source)
        self.assertEqual(recompile_rom.assemble(source), recompile_rom.assemble(compile_il.compile_source(source)))

    def test_forward_nested_calls_and_parameters(self):
        source = """SECTION "test", ROM0[$0000]
    @call load and increment($42) ; first call
    @call load and increment($7F)
@function load and increment(value)
    @call load accumulator({{value}})
    INC A
@end
@function load accumulator(value)
    LD A,{{value}}
@end
"""
        output = compile_il.compile_source(source)
        self.assertIn("; first call\n", output)
        self.assertNotIn("@call", output)
        self.assertEqual(recompile_rom.assemble(output)[:6], bytes([0x3E, 0x42, 0x3C, 0x3E, 0x7F, 0x3C]))

    def test_constants_memory_variables_and_mutable_values(self):
        source = """@const initial_health = $42
@var player_health = $C000
@let amount = {{initial_health}}
SECTION "test", ROM0[$0000]
    @call update health({{amount}})
    @set amount = $05
    @call update health({{amount}})
@function update health(value)
    LD A,{{value}} ; {{player_health}}
    LD [{{player_health}}],A
@end
"""
        output = compile_il.compile_source(source)
        self.assertIn("LD A,$42 ; $C000", output)
        self.assertEqual(
            recompile_rom.assemble(output)[:10],
            bytes([0x3E, 0x42, 0xEA, 0x00, 0xC0, 0x3E, 0x05, 0xEA, 0x00, 0xC0]),
        )

    def test_reassignments_in_routines_and_parameter_shadowing(self):
        source = """@let amount = $01
@const value = $AA
@function use and change(value)
    LD A,{{value}}
    @set amount = $02
@end
SECTION "test", ROM0[$0000] ; {{ordinary_comment}}
    @call use and change({{amount}})
    LD A,{{amount}}
    LD A,{{value}}
"""
        output = compile_il.compile_source(source)
        self.assertIn("; {{ordinary_comment}}", output)
        self.assertEqual(recompile_rom.assemble(output)[:6], b"\x3e\x01\x3e\x02\x3e\xaa")

    def test_address_aliases_accept_decimal_and_signed_positive_hex(self):
        source = """@var decimal_address = 49152
@var hex_address = +0xC001
SECTION "test", ROM0[$0000]
 LD [{{decimal_address}}],A
 LD [{{hex_address}}],A
"""
        output = compile_il.compile_source(source)
        self.assertEqual(recompile_rom.assemble(output)[:6], b"\xea\x00\xc0\xea\x01\xc0")

    def test_invalid_named_values(self):
        cases = [
            ("@const limit = A\n", "line 1: const requires a numeric value"),
            ("@var health = -$01\n", "line 1: variable address must be in 0..$FFFF"),
            ("@var health = $10000\n", "line 1: variable address must be in 0..$FFFF"),
            ("@let item =\n", "line 1: expected a name and value"),
            ("@const x = 1\n@let x = 2\n", "line 2: duplicate name"),
            ("@const x = 1\n@set x = 2\n", "line 2: 'x' is not a compile-time variable"),
            ("@var x = $C000\n@set x = 2\n", "line 2: 'x' is not a compile-time variable"),
            ("@set x = 2\n", "line 1: undefined name"),
            ("@let x = {{later}}\n@const later = 1\n", "line 1: undefined name"),
            ("@let x = 1\n LD A,{{missing}}\n", "line 2: undefined name"),
            ("@function f()\n@let x = 1\n@end\n", "line 2: declarations must be outside functions"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(ValueError) as error:
                    compile_il.compile_source(source)
                self.assertIn(message, str(error.exception))

    def test_invalid_definitions_and_calls_report_source_lines(self):
        cases = [
            ("@function a()\n", "line 1: function 'a' has no @end"),
            ("@end\n", "line 1: unexpected"),
            ("@function a(x,x)\n@end\n", "line 1: invalid or duplicate parameter"),
            ("@function a()\n@end\n@function a()\n@end\n", "line 3: duplicate"),
            ("@function a()\n@function b()\n", "line 2: nested"),
            ("@function a(x)\n LD A,{{y}}\n@end\n", "line 2: unknown parameter"),
            ("@call missing()\n", "line 1: unknown function"),
            ("@function a(x)\n@end\n@call a()\n", "line 3: 'a' expects 1 arguments, got 0"),
            ("@call a(,)\n", "line 1: empty"),
            ("@function a()\n@call b()\n@end\n@function b()\n@call a()\n@end\n@call a()\n",
             "line 5: recursive function call: a -> b -> a"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, message.replace("(", r"\(").replace(")", r"\)")):
                    compile_il.compile_source(source)


class CompileWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        copy_tool_tree(self.root)

    def run_wrapper(self, *args):
        return subprocess.run(
            ["bash", str(self.root / "rc2t"), *args],
            cwd=self.root, capture_output=True, text=True,
        )

    def test_compile_then_recompile_and_preserve_output_on_error(self):
        source = self.root / "game.rc2asm"
        source.write_text(
            '@function set accumulator(value)\n LD A,{{value}}\n@end\n'
            'SECTION "test", ROM0[$0000]\n @call set accumulator($12)\n',
            encoding="utf-8",
        )
        result = self.run_wrapper("compile-il", str(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        assembly = self.root / "output" / "game.asm"
        expected = assembly.read_text(encoding="utf-8")
        result = self.run_wrapper("recompile", str(assembly))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "output" / "game (recompiled).gb").read_bytes()[:2], b"\x3e\x12")

        source.write_text("@const bad = A\n", encoding="utf-8")
        result = self.run_wrapper("compile-il", str(source))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("line 1: const requires a numeric value", result.stderr)
        self.assertEqual(assembly.read_text(encoding="utf-8"), expected)

    def test_explicit_output_and_same_file_rejected(self):
        source = self.root / "game.rc2asm"
        source.write_bytes(b'SECTION "test", ROM0[$0000]\r\n NOP\r\n')
        result = self.run_wrapper("compile-il", str(source), str(self.root / "custom.asm"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "custom.asm").read_bytes(), source.read_bytes())
        result = self.run_wrapper("compile-il", str(source), str(source))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input and output must be different", result.stderr)
        self.assertIn("NOP", source.read_text(encoding="utf-8"))

    def test_disassembly_passes_through_and_round_trips(self):
        rom = self.root / "original.gb"
        data = bytes([0x3E, 0x42, 0x18, 0xFE]) + bytes(0x7FFC)
        rom.write_bytes(data)
        listing = self.root / "listing.asm"
        result = self.run_wrapper("decompile", str(rom), str(listing))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_wrapper("compile-il", str(listing))
        self.assertEqual(result.returncode, 0, result.stderr)
        compiled = self.root / "output" / "listing.asm"
        self.assertEqual(compiled.read_bytes(), listing.read_bytes())
        result = self.run_wrapper("recompile", str(compiled))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "output" / "listing (recompiled).gb").read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
