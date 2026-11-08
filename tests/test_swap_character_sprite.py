import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
SPEC = importlib.util.spec_from_file_location(
    "swap_character_sprite",
    ROOT / "bin" / "swap_character_sprite.py",
)
swap_character_sprite = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(swap_character_sprite)


def parse_ips(patch):
    if not patch.startswith(b"PATCH"):
        raise ValueError("missing IPS header")
    records = {}
    offset = 5
    while patch[offset:offset + 3] != b"EOF":
        address = int.from_bytes(patch[offset:offset + 3], "big")
        size = int.from_bytes(patch[offset + 3:offset + 5], "big")
        if size == 0:
            raise ValueError("unexpected RLE record")
        records[address] = patch[offset + 5:offset + 5 + size]
        offset += 5 + size
    if patch[offset + 3:]:
        raise ValueError("trailing IPS data")
    return records


class SwapCharacterSpriteTests(unittest.TestCase):
    def test_patch_swaps_only_the_eleven_sprite_regions(self):
        rom = bytearray(0x20000)
        first = swap_character_sprite.CHARACTER_SPRITES["hero"]
        second = swap_character_sprite.CHARACTER_SPRITES["pit"]
        segments = (
            (first[0], second[0], swap_character_sprite.STANDARD_SPRITE_BYTES),
            (first[1], second[1], swap_character_sprite.SPRITE_BYTES),
            (first[2], second[2], swap_character_sprite.SPRITE_BYTES),
        )
        for index, (first_offset, second_offset, size) in enumerate(segments):
            rom[first_offset:first_offset + size] = bytes([0x10 + index]) * size
            rom[second_offset:second_offset + size] = bytes([0x20 + index]) * size

        patch, patched_rom = swap_character_sprite.build_swap_artifacts(rom, "hero", "pit")
        records = parse_ips(patch)
        self.assertEqual(patch[-3:], b"EOF")
        self.assertEqual(
            {offset: len(data) for offset, data in records.items()},
            {
                first[0]: swap_character_sprite.STANDARD_SPRITE_BYTES,
                second[0]: swap_character_sprite.STANDARD_SPRITE_BYTES,
                first[1]: swap_character_sprite.SPRITE_BYTES,
                second[1]: swap_character_sprite.SPRITE_BYTES,
                first[2]: swap_character_sprite.SPRITE_BYTES,
                second[2]: swap_character_sprite.SPRITE_BYTES,
            },
        )

        patched = bytearray(rom)
        for offset, data in records.items():
            patched[offset:offset + len(data)] = data
        expected = bytearray(rom)
        for first_offset, second_offset, size in segments:
            expected[first_offset:first_offset + size] = rom[second_offset:second_offset + size]
            expected[second_offset:second_offset + size] = rom[first_offset:first_offset + size]
        self.assertEqual(patched, expected)
        self.assertEqual(patched_rom, expected)

    def test_rejects_unknown_or_identical_characters(self):
        for character1, character2 in (("hero", "unknown"), ("hero", "hero")):
            with self.subTest(characters=(character1, character2)):
                with self.assertRaises(ValueError):
                    swap_character_sprite.build_swap_artifacts(
                        bytes(0x20000),
                        character1,
                        character2,
                    )


if __name__ == "__main__":
    unittest.main()
