import unittest

from tests.support import blank_rom, load_bin_module

swap_character_sprite = load_bin_module("swap_character_sprite")


class SwapCharacterSpriteTests(unittest.TestCase):
    def test_swaps_sprite_regions_and_pow_portrait_in_place(self):
        rom = blank_rom()
        first = swap_character_sprite.CHARACTER_SPRITES["hero"]
        second = swap_character_sprite.CHARACTER_SPRITES["pit"]
        segments = (
            (first[0], second[0], swap_character_sprite.STANDARD_SPRITE_BYTES),
            (first[1], second[1], swap_character_sprite.SPRITE_BYTES),
            (first[2], second[2], swap_character_sprite.SPRITE_BYTES),
            (first[3], second[3], swap_character_sprite.POW_PORTRAIT_BYTES),
        )
        for index, (first_offset, second_offset, size) in enumerate(segments):
            rom[first_offset:first_offset + size] = bytes([0x10 + index]) * size
            rom[second_offset:second_offset + size] = bytes([0x20 + index]) * size
        original = bytes(rom)

        swap_character_sprite.swap_character_sprites(rom, "hero", "pit")

        expected = bytearray(original)
        for first_offset, second_offset, size in segments:
            expected[first_offset:first_offset + size] = original[second_offset:second_offset + size]
            expected[second_offset:second_offset + size] = original[first_offset:first_offset + size]
        self.assertEqual(rom, expected)

    def test_swapping_same_pair_twice_restores_original_rom(self):
        rom = bytearray(range(256)) * 0x200
        original = bytes(rom)
        swap_character_sprite.swap_character_sprites(rom, "lane", "zold")
        self.assertNotEqual(bytes(rom), original)
        swap_character_sprite.swap_character_sprites(rom, "zold", "lane")
        self.assertEqual(bytes(rom), original)

    def test_rejects_rom_without_complete_sprite_data_and_leaves_it_unchanged(self):
        rom = bytearray(0x1000)
        original = bytes(rom)
        with self.assertRaises(ValueError):
            swap_character_sprite.swap_character_sprites(rom, "hero", "pit")
        self.assertEqual(bytes(rom), original)

    def test_rejects_unknown_or_identical_characters(self):
        for character1, character2 in (("hero", "unknown"), ("hero", "hero")):
            with self.subTest(characters=(character1, character2)):
                with self.assertRaises(ValueError):
                    swap_character_sprite.swap_character_sprites(
                        blank_rom(),
                        character1,
                        character2,
                    )


if __name__ == "__main__":
    unittest.main()
