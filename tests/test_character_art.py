import random
import sys
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

from character_art import apply_character_art, render_character_art  # noqa: E402
from render_graphics import DEFAULT_PALETTE, HACK_ART_PALETTE, PORTRAIT_PALETTE  # noqa: E402
from swap_character_sprite import CHARACTER_SPRITES, SPRITE_BYTES  # noqa: E402


def solid_tile(index):
    return bytes((0xFF if index & 1 else 0, 0xFF if index & 2 else 0)) * 8


class CharacterArtTests(unittest.TestCase):
    def test_graphics_are_assembled_and_separated(self):
        rom = bytearray(0x20000)
        for character, (standard, defeated, face, portrait) in CHARACTER_SPRITES.items():
            offsets = [standard + index * SPRITE_BYTES for index in range(9)] + [defeated, face]
            for index, offset in enumerate(offsets):
                colors = (index % 4, index // 4, (index + 1) % 4, (index + 2) % 4)
                rom[offset:offset + SPRITE_BYTES] = b"".join(solid_tile(color) for color in colors)
            rom[portrait:portrait + 0x100] = b"".join(solid_tile(index % 4) for index in range(16))
        for character in CHARACTER_SPRITES:
            with self.subTest(character=character):
                self.assert_character_art(render_character_art(rom, character))

    def assert_character_art(self, image):
        self.assertEqual(image.size, (84, 50))
        for cell, index in enumerate((0, 1, 6, 4, 5, 8, 2, 3, 7, 9, 10)):
            if cell < 9:
                x, y = (cell % 3) * 17, (cell // 3) * 17
            else:
                x, y = 51 + (cell - 9) * 17, 34
            colors = (index % 4, index // 4, (index + 1) % 4, (index + 2) % 4)
            for tile, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
                self.assertEqual(image.getpixel((x + dx, y + dy)), HACK_ART_PALETTE[colors[tile]])
        for tile in range(16):
            self.assertEqual(
                image.getpixel((51 + (tile % 4) * 8, (tile // 4) * 8)),
                PORTRAIT_PALETTE[tile % 4],
            )
        for x in (16, 33, 50):
            self.assertTrue(all(image.getpixel((x, y)) == (255, 0, 0) for y in range(50)))
        self.assertTrue(all(image.getpixel((x, 16)) == (255, 0, 0) for x in range(51)))
        self.assertTrue(all(image.getpixel((x, 33)) == (255, 0, 0) for x in range(84)))
        self.assertTrue(all(image.getpixel((67, y)) == (255, 0, 0) for y in range(34, 50)))
        self.assertTrue(all(image.getpixel((x, 32)) == (255, 0, 0) for x in range(51, 84)))
        self.assertTrue(all(image.getpixel((83, y)) == (255, 0, 0) for y in range(33)))

    def test_short_rom_is_rejected(self):
        for character in CHARACTER_SPRITES:
            with self.subTest(character=character):
                with self.assertRaisesRegex(ValueError, f"complete {character} sprite data"):
                    render_character_art(bytes(0x9000), character)

    def test_unknown_character_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown character"):
            render_character_art(bytes(0x20000), "unknown")

    def test_round_trip_preserves_every_rom_byte_for_each_character(self):
        original = random.Random(42).randbytes(0x20000)
        for character in CHARACTER_SPRITES:
            with self.subTest(character=character):
                rom = bytearray(original)
                apply_character_art(rom, character, render_character_art(original, character))
                self.assertEqual(rom, original)

    def test_inject_maps_every_tile_and_ignores_separators(self):
        original = random.Random(41).randbytes(0x20000)
        for character, (standard, defeated, face, portrait) in CHARACTER_SPRITES.items():
            with self.subTest(character=character):
                rom = bytearray(original)
                expected = bytearray(original)
                image = render_character_art(original, character)
                offsets = [standard + index * SPRITE_BYTES for index in (0, 1, 6, 4, 5, 8, 2, 3, 7)]
                offsets += [defeated, face]
                for cell, offset in enumerate(offsets):
                    x = (cell % 3) * 17 if cell < 9 else 51 + (cell - 9) * 17
                    y = (cell // 3) * 17 if cell < 9 else 34
                    for tile, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
                        tile_offset = offset + tile * 16
                        color = (HACK_ART_PALETTE.index(image.getpixel((x + dx, y + dy))) + 1) % 4
                        image.putpixel((x + dx, y + dy), HACK_ART_PALETTE[color])
                        expected[tile_offset] = (expected[tile_offset] & 0x7F) | ((color & 1) << 7)
                        expected[tile_offset + 1] = (expected[tile_offset + 1] & 0x7F) | ((color >> 1) << 7)
                for tile in range(16):
                    x, y = 51 + tile % 4 * 8, tile // 4 * 8
                    tile_offset = portrait + tile * 16
                    color = (PORTRAIT_PALETTE.index(image.getpixel((x, y))) + 1) % 4
                    image.putpixel((x, y), PORTRAIT_PALETTE[color])
                    expected[tile_offset] = (expected[tile_offset] & 0x7F) | ((color & 1) << 7)
                    expected[tile_offset + 1] = (expected[tile_offset + 1] & 0x7F) | ((color >> 1) << 7)
                for point in ((16, 0), (51, 32), (83, 0), (67, 34)):
                    image.putpixel(point, (0, 255, 0))
                apply_character_art(rom, character, image)
                self.assertEqual(rom, expected)

    def test_inject_quantizes_using_each_region_palette(self):
        rom = bytearray(0x20000)
        image = render_character_art(rom, "hero")
        image.putpixel((0, 0), (90, 90, 90))
        image.putpixel((51, 0), (90, 90, 90))
        apply_character_art(rom, "hero", image)
        result = render_character_art(rom, "hero")
        self.assertEqual(result.getpixel((0, 0)), HACK_ART_PALETTE[2])
        self.assertEqual(result.getpixel((51, 0)), PORTRAIT_PALETTE[2])

    def test_inject_invalid_inputs_do_not_change_rom(self):
        original = bytes(0x20000)
        for character, image in (("hero", Image.new("RGB", (83, 50))), ("invalid", Image.new("RGB", (84, 50)))):
            rom = bytearray(original)
            with self.assertRaises(ValueError):
                apply_character_art(rom, character, image)
            self.assertEqual(rom, original)
        rom = bytearray(0x9000)
        with self.assertRaisesRegex(ValueError, "complete hero sprite data"):
            apply_character_art(rom, "hero", Image.new("RGB", (84, 50)))
        self.assertEqual(rom, bytes(0x9000))


if __name__ == "__main__":
    unittest.main()
