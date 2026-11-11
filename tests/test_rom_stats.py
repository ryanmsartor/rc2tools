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
            stats["hero_electricball_range"],
            [self.rom[0x15459 + 3 * level + 1] for level in range(16)],
        )
        self.assertEqual(
            stats["pit_bomb_unknown"],
            [self.rom[0x15511 + 3 * level + 2] for level in range(16)],
        )
        self.assertEqual(stats["zold_specialblade_damage"], list(self.rom[0x15CA6:0x15CB6]))
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

    def test_renamed_arrays_use_original_offsets_and_old_names_are_unknown(self):
        renamed = {
            "hero_sabre_damage": ("hero_a_damage", 0x15449, 1),
            "hero_electricball_cost": ("hero_b_cost", 0x15459, 3),
            "hero_electricball_range": ("hero_b_range", 0x1545A, 3),
            "hero_electricball_damage": ("hero_b_damage", 0x1545B, 3),
            "lane_staff_damage": ("lane_a_damage", 0x15709, 1),
            "kyle_bone_damage": ("kyle_a_damage", 0x157C9, 1),
            "kyle_playdead_cost": ("kyle_play_dead_cost", 0x157D9, 2),
            "kyle_playdead_unknown": ("kyle_play_dead_unknown", 0x157DA, 2),
            "kyle_thunder_cost": ("kyle_rod_cost", 0x15898, 2),
            "kyle_thunder_damage": ("kyle_rod_damage", 0x15899, 2),
            "jude_fireball_range": ("jude_weak_a_range", 0x159B2, 2),
            "jude_fireball_damage": ("jude_weak_a_damage", 0x159B3, 2),
            "jude_smashball_range": ("jude_strong_a_range", 0x159E4, 2),
            "jude_smashball_damage": ("jude_strong_a_damage", 0x159E5, 2),
            "lee_sai_damage": ("lee_a_damage", 0x15B97, 1),
            "lora_arrow_range": ("lora_a_range", 0x15C34, 2),
            "lora_arrow_damage": ("lora_a_damage", 0x15C35, 2),
            "zold_darkblade_range": ("zold_a_range", 0x15CB6, 2),
            "zold_darkblade_damage": ("zold_a_damage", 0x15CB7, 2),
            "zold_specialblade_damage": ("zold_a_damage_table", 0x15CA6, 1),
            "zold_megaball_cost": ("zold_b_cost", 0x15CE8, 2),
            "zold_megaball_damage": ("zold_b_damage", 0x15CE9, 2),
        }
        stats = dict(rom_stats.read_stats(self.rom))
        offsets = rom_stats.stat_offsets()
        values = {name: [index] * 16 for index, name in enumerate(renamed, 1)}
        text = rom_stats.format_stats(list(values.items()))
        parsed, unknown = rom_stats.parse_stats(text)
        self.assertEqual(parsed, values)
        self.assertEqual(unknown, [])
        rom = bytearray(self.rom)
        rom_stats.apply_stats(rom, parsed)
        expected = bytearray(self.rom)
        for name, (old_name, start, stride) in renamed.items():
            with self.subTest(name=name):
                positions = tuple(start + stride * level for level in range(16))
                self.assertEqual(offsets[name], positions)
                self.assertEqual(stats[name], [self.rom[position] for position in positions])
                self.assertNotIn(old_name, offsets)
                for position in positions:
                    expected[position] = values[name][0]
        self.assertEqual(rom, expected)
        old_text = "\n".join(f"{old_name}: []" for old_name, _, _ in renamed.values())
        parsed, unknown = rom_stats.parse_stats(old_text)
        self.assertEqual(parsed, {})
        self.assertEqual(unknown, [old_name for old_name, _, _ in renamed.values()])

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
        self.assertEqual(changed["zold_specialblade_damage"][0], self.rom[0x15CA6])
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

    def test_parse_dump_and_whitespace_with_unknown_arrays(self):
        stats = rom_stats.read_stats(self.rom)
        parsed, unknown = rom_stats.parse_stats(rom_stats.format_stats(stats))
        self.assertEqual(parsed, dict(stats))
        self.assertEqual(unknown, [])
        text = " \tunknown_name : [ ignored ] \n hero_hp \t: [\n" + ",\n ".join(
            str(value) for value in range(16)
        ) + "\t]\n"
        parsed, unknown = rom_stats.parse_stats(text)
        self.assertEqual(parsed, {"hero_hp": list(range(16))})
        self.assertEqual(unknown, ["unknown_name"])

    def test_parse_rejects_bad_known_arrays_and_duplicate_names(self):
        valid = "hero_hp: [" + ",".join(["0"] * 16) + "]"
        invalid = (
            valid + "\n" + valid,
            "hero_hp: [" + ",".join(["0"] * 15) + "]",
            "hero_hp: [" + ",".join(["0"] * 15 + ["256"]) + "]",
            "hero_hp: [" + ",".join(["0"] * 15 + ["-1"]) + "]",
            "hero_hp: [" + ",".join(["0"] * 15 + ["oops"]) + "]",
            valid + "\ninvalid",
            "hero_hp: [0",
        )
        for text in invalid:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    rom_stats.parse_stats(text)

    def test_apply_every_array_round_trips_without_overlapping(self):
        offsets = rom_stats.stat_offsets()
        all_offsets = [offset for positions in offsets.values() for offset in positions]
        self.assertEqual(len(all_offsets), len(set(all_offsets)))
        values = {
            name: [(index + level + 1) % 256 for level in range(16)]
            for index, name in enumerate(offsets)
        }
        expected = bytearray(self.rom)
        for name, positions in offsets.items():
            for position, value in zip(positions, values[name]):
                expected[position] = value
        rom = bytearray(self.rom)
        rom_stats.apply_stats(rom, values)
        self.assertEqual(rom, expected)
        self.assertEqual(dict(rom_stats.read_stats(rom)), values)
        self.assertEqual(rom[0x15459:0x1545C], bytes((
            values["hero_electricball_cost"][0], values["hero_electricball_range"][0],
            values["hero_electricball_damage"][0],
        )))
        self.assertEqual(rom[0x17165:0x17175], bytes(values["lookup_0x17165_table"]))

    def test_apply_invalid_arrays_does_not_change_rom(self):
        for stats in (
            {"hero_hp": [1] * 16, "hero_mp": [2] * 15},
            {"hero_hp": [1] * 16, "hero_mp": [256] * 16},
            {"hero_hp": [1] * 16, "unknown": [2] * 16},
        ):
            rom = bytearray(self.rom)
            with self.subTest(stats=stats), self.assertRaises(ValueError):
                rom_stats.apply_stats(rom, stats)
            self.assertEqual(rom, self.rom)


if __name__ == "__main__":
    unittest.main()
