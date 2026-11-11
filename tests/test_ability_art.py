import random
import unittest

from PIL import Image

from tests.support import blank_rom

from ability_art import (  # noqa: E402
    ABILITY_COUNT,
    ABILITY_START,
    apply_ability_art,
    render_ability_art,
)
from sprite_art import SPRITE_BYTES, SPRITE_SIZE  # noqa: E402
from render_graphics import HACK_ART_PALETTE  # noqa: E402


class AbilityArtTests(unittest.TestCase):
    def test_round_trip_preserves_rom(self):
        original = random.Random(42).randbytes(0x20000)
        rom = bytearray(original)
        apply_ability_art(rom, render_ability_art(original))
        self.assertEqual(rom, original)

    def test_inject_maps_palette_pixels_and_ignores_gutters(self):
        rom = blank_rom()
        image = render_ability_art(rom)
        expected = bytearray(rom)
        for index in range(ABILITY_COUNT):
            x = (index % 6) * (SPRITE_SIZE + 1)
            y = (index // 6) * (SPRITE_SIZE + 1)
            color = index % len(HACK_ART_PALETTE)
            image.putpixel((x, y), HACK_ART_PALETTE[color])
            offset = ABILITY_START + index * SPRITE_BYTES
            expected[offset] = 0x80 if color & 1 else 0
            expected[offset + 1] = 0x80 if color & 2 else 0

        image.putpixel((16, 0), (0, 255, 0))
        image.putpixel((85, 51), (0, 255, 0))
        apply_ability_art(rom, image)
        self.assertEqual(rom, expected)

    def test_invalid_inputs_leave_rom_unchanged(self):
        original = bytes(0x20000)
        wrong_size = Image.new("RGB", (100, 67))
        wrong_size_rom = bytearray(original)
        short_rom = bytearray(ABILITY_START + ABILITY_COUNT * SPRITE_BYTES - 1)

        with self.assertRaisesRegex(ValueError, "expected a 101x67 image"):
            apply_ability_art(wrong_size_rom, wrong_size)
        self.assertEqual(wrong_size_rom, original)
        with self.assertRaisesRegex(ValueError, "all 23 ability sprites"):
            apply_ability_art(short_rom, Image.new("RGB", (101, 67)))
        self.assertEqual(short_rom, bytes(len(short_rom)))

        with self.assertRaisesRegex(ValueError, "all 23 ability sprites"):
            render_ability_art(bytes(ABILITY_START + ABILITY_COUNT * SPRITE_BYTES - 1))


if __name__ == "__main__":
    unittest.main()
