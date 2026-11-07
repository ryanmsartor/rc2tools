import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("extract_json", ROOT / "bin" / "extract_json.py")
extract_json = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extract_json)


def hex_dump(data, powershell=False):
    rows = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        if powershell:
            rows.append(f"{offset:08X}   {chunk.hex(' ').upper()}  ................")
        else:
            groups = " ".join(chunk[i:i + 2].hex() for i in range(0, 16, 2))
            rows.append(f"{offset:08x}: {groups}  ................")
    text = "\n".join(rows) + "\n"
    return text.encode("utf-16" if powershell else "utf-8")


class ExtractGameTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytearray((i * 37 + i // 256) % 256 for i in range(0x20000))
        self.rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        self.rom[0x147:0x149] = b"\x06\x02"

    def test_hex_dump_formats_and_invalid_rows(self):
        for powershell in (False, True):
            with self.subTest(powershell=powershell):
                self.assertEqual(extract_json.parse_hex_dump(hex_dump(self.rom, powershell)), self.rom)
        with self.assertRaisesRegex(ValueError, "expected offset"):
            extract_json.parse_hex_dump(b"00000010: 0000 0000 0000 0000 0000 0000 0000 0000  ................\n")
        with self.assertRaisesRegex(ValueError, "invalid hex dump row"):
            extract_json.parse_hex_dump(b"00000000: 0000 broken\n")
        with self.assertRaisesRegex(ValueError, "no recognizable rows"):
            extract_json.parse_hex_dump(b"not a dump\n")

    def test_all_fields_read_at_mapped_offsets(self):
        expected = {
            "hero": {"a": (0x15449, ("damage",)), "b": (0x15459, ("cost", "range", "damage"))},
            "pit": {"dagger": (0x154AD, ("range", "damage")), "boomerang": (0x154DF, ("range", "damage")), "bomb": (0x15511, ("cost", "damage", "unknown"))},
            "lane": {"a": (0x15709, ("damage",)), "shield": (0x15719, ("cost", "unknown")), "healing": (0x15799, ("cost", "unknown_1", "unknown_2"))},
            "kyle": {"a": (0x157C9, ("damage",)), "play_dead": (0x157D9, ("cost", "unknown")), "rod": (0x15898, ("cost", "damage"))},
            "jude": {"weak_a": (0x159B2, ("range", "damage")), "strong_a": (0x159E4, ("range", "damage")), "quake": (0x15A16, ("cost", "damage"))},
            "lee": {"a": (0x15B97, ("damage",)), "rapidfire": (0x15BA7, ("cost", "damage")), "firework": (0x15BC7, ("cost", "damage", "range"))},
            "lora": {"a": (0x15C34, ("range", "damage")), "heal": (0x15C66, ("cost", "unknown_1", "unknown_2")), "wing": (0x15C96, ("cost",))},
            "zold": {"a": (0x15CB6, ("range", "damage")), "b": (0x15CE8, ("cost", "damage"))},
        }
        characters = extract_json.extract_json(self.rom)["characters"]
        self.assertEqual(set(characters), set(expected))
        for index, (name, abilities) in enumerate(expected.items()):
            char = characters[name]
            self.assertEqual(char["hp"], list(self.rom[0x17065 + 16 * index:0x17075 + 16 * index]))
            self.assertEqual(char["mp"], list(self.rom[0x170E5 + 16 * index:0x170F5 + 16 * index]))
            self.assertEqual(set(char["abilities"]), set(abilities))
            for ability, (offset, fields) in abilities.items():
                actual = char["abilities"][ability]
                self.assertEqual(set(actual), set(fields))
                for column, field in enumerate(fields):
                    self.assertEqual(actual[field], list(self.rom[offset + column:offset + 16 * len(fields):len(fields)]))

    def test_additional_tables_are_read_at_mapped_offsets(self):
        game = extract_json.extract_json(self.rom)
        additional = game["additional_tables"]
        self.assertEqual(
            additional["zold_a_damage"],
            list(self.rom[0x15CA6:0x15CB6]),
        )
        self.assertEqual(
            additional["lookup_0x17165"],
            [list(self.rom[offset:offset + 2]) for offset in range(0x17165, 0x17175, 2)],
        )
        self.assertEqual(
            additional["lookup_0x17175"],
            [list(self.rom[offset:offset + 2]) for offset in range(0x17175, 0x17185, 2)],
        )

    def test_changed_rom_bytes_change_extracted_values(self):
        original = extract_json.extract_json(self.rom)
        self.rom[0x17065] = (self.rom[0x17065] + 1) % 256
        self.rom[0x15511 + 3 * 7 + 2] = (self.rom[0x15511 + 3 * 7 + 2] + 1) % 256
        self.rom[0x15CA6] = (self.rom[0x15CA6] + 1) % 256
        self.rom[0x17165] = (self.rom[0x17165] + 1) % 256
        self.rom[0x17166] = (self.rom[0x17166] + 1) % 256
        changed = extract_json.extract_json(self.rom)
        self.assertEqual(changed["characters"]["hero"]["hp"][0], self.rom[0x17065])
        self.assertNotEqual(changed["characters"]["hero"]["hp"][0], original["characters"]["hero"]["hp"][0])
        self.assertEqual(changed["characters"]["pit"]["abilities"]["bomb"]["unknown"][7], self.rom[0x15511 + 3 * 7 + 2])
        self.assertNotEqual(changed["characters"]["pit"]["abilities"]["bomb"]["unknown"][7], original["characters"]["pit"]["abilities"]["bomb"]["unknown"][7])
        self.assertEqual(changed["additional_tables"]["zold_a_damage"][0], self.rom[0x15CA6])
        self.assertEqual(changed["additional_tables"]["lookup_0x17165"][0], list(self.rom[0x17165:0x17167]))
        self.assertNotEqual(
            changed["additional_tables"]["lookup_0x17165"][0],
            original["additional_tables"]["lookup_0x17165"][0],
        )

    def test_output_path_uses_sha256_of_rom_bytes(self):
        root = Path("repo")
        path = extract_json.output_path(root, self.rom)
        self.assertEqual(
            path,
            root / "output" / f"{hashlib.sha256(self.rom).hexdigest()}.json",
        )
        changed_rom = bytes(self.rom[:-1]) + bytes([self.rom[-1] ^ 1])
        self.assertNotEqual(path, extract_json.output_path(root, changed_rom))

    def test_read_rom_rejects_truncated_or_wrong_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game.gb"
            path.write_bytes(self.rom[:-1])
            with self.assertRaisesRegex(ValueError, "expected a 131072-byte ROM"):
                extract_json.read_rom(path)
            self.rom[0x134] = 0
            path.write_bytes(self.rom)
            with self.assertRaisesRegex(ValueError, "ROM header does not match"):
                extract_json.read_rom(path)


if __name__ == "__main__":
    unittest.main()
