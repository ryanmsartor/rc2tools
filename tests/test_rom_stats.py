import unittest

from tests.support import load_bin_module

rom_stats = load_bin_module("rom_stats")


class RomStatsTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytearray((i * 37 + i // 256) % 256 for i in range(0x20000))
        self.rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        self.rom[0x147:0x149] = b"\x06\x02"

    def test_read_stats_names_and_offsets(self):
        stats = dict(rom_stats.read_stats(self.rom))
        self.assertEqual(
            stats["hero_hp"],
            list(self.rom[0x17065:0x17075]),
        )
        self.assertEqual(
            stats["zold_hp"],
            list(self.rom[0x17065 + 16 * 7:0x17075 + 16 * 7]),
        )
        self.assertEqual(
            stats["zold_mp"],
            list(self.rom[0x170E5 + 16 * 7:0x170F5 + 16 * 7]),
        )
        self.assertEqual(
            stats["hero_b_range"],
            [self.rom[0x15459 + 3 * level + 1] for level in range(16)],
        )
        self.assertEqual(
            stats["pit_bomb_unknown"],
            [self.rom[0x15511 + 3 * level + 2] for level in range(16)],
        )
        self.assertEqual(stats["zold_a_damage_table"], list(self.rom[0x15CA6:0x15CB6]))
        self.assertEqual(stats["lookup_0x17165_table"], list(self.rom[0x17165:0x17175]))
        self.assertEqual(stats["lookup_0x17175_table"], list(self.rom[0x17175:0x17185]))

    def test_read_stats_covers_every_field_once(self):
        stats = rom_stats.read_stats(self.rom)
        names = [name for name, _ in stats]
        self.assertEqual(len(names), len(set(names)))
        # hp and mp for 8 characters, 44 ability fields, and 3 additional tables.
        self.assertEqual(len(names), 8 * 2 + 44 + 3)
        for name, values in stats:
            with self.subTest(name=name):
                self.assertEqual(len(values), 16)

    def test_changed_rom_bytes_change_stats(self):
        original = dict(rom_stats.read_stats(self.rom))
        self.rom[0x17065] = (self.rom[0x17065] + 1) % 256
        self.rom[0x15511 + 3 * 7 + 2] = (self.rom[0x15511 + 3 * 7 + 2] + 1) % 256
        self.rom[0x15CA6] = (self.rom[0x15CA6] + 1) % 256
        self.rom[0x17165] = (self.rom[0x17165] + 1) % 256
        changed = dict(rom_stats.read_stats(self.rom))
        self.assertEqual(changed["hero_hp"][0], self.rom[0x17065])
        self.assertNotEqual(changed["hero_hp"][0], original["hero_hp"][0])
        self.assertEqual(changed["pit_bomb_unknown"][7], self.rom[0x15511 + 3 * 7 + 2])
        self.assertNotEqual(changed["pit_bomb_unknown"][7], original["pit_bomb_unknown"][7])
        self.assertEqual(changed["zold_a_damage_table"][0], self.rom[0x15CA6])
        self.assertEqual(changed["lookup_0x17165_table"][0], self.rom[0x17165])
        self.assertNotEqual(changed["lookup_0x17165_table"][0], original["lookup_0x17165_table"][0])

    def test_format_stats_aligns_colons_and_right_aligns_values(self):
        stats = [("a", [1] * 16), ("longer_name", [255] + [0] * 15)]
        lines = rom_stats.format_stats(stats).splitlines()
        self.assertEqual(lines[0], "a" + " " * 10 + ": [" + ", ".join(["  1"] * 16) + "]")
        self.assertEqual(lines[1], "longer_name: [" + ", ".join(["255"] + ["  0"] * 15) + "]")

    def test_format_stats_output_for_full_rom(self):
        stats = rom_stats.read_stats(self.rom)
        text = rom_stats.format_stats(stats)
        self.assertTrue(text.endswith("]\n"))
        lines = text.splitlines()
        self.assertEqual(len(lines), len(stats))
        name_width = max(len(name) for name, _ in stats)
        self.assertEqual({line.index(":") for line in lines}, {name_width})
        for line in lines:
            with self.subTest(line=line):
                self.assertEqual(line.count(", "), 15)


if __name__ == "__main__":
    unittest.main()
