import random
import sys
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

import art_layout  # noqa: E402

TITLE_START = 0x1A6AE
TITLE_END = 0x1B0FD
ROM_SIZE = 0x20000


def title_rom(seed=1):
    rng = random.Random(seed)
    return bytearray(rng.getrandbits(8) for _ in range(ROM_SIZE))


def different_shade(layout, shade):
    return next(value for value in layout.shades if value != shade)


class TitleLayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout = art_layout.ART_LAYOUTS["title"]

    def test_grid_places_every_title_tile_above_start_line(self):
        placed = {tile for row in self.layout.grid for tile in row if tile is not None}
        expected = set(range(0x30, 0xD3))
        self.assertEqual(placed, expected)

    def test_grid_is_20_by_13_cells(self):
        self.assertEqual(len(self.layout.grid), 13)
        self.assertTrue(all(len(row) == 20 for row in self.layout.grid))
        self.assertEqual(self.layout.image_size, (160, 104))

    def test_segments_cover_title_graphics_block(self):
        offsets = [self.layout.rom_offset(tile) for tile in (0x30, 0x7F, 0x80, 0xD4)]
        self.assertEqual(offsets[0], 0x1ABFE)
        self.assertEqual(offsets[1] + art_layout.TILE_BYTES - 1, TITLE_END)
        self.assertEqual(offsets[2], TITLE_START)
        self.assertEqual(offsets[3] + art_layout.TILE_BYTES - 1, 0x1ABFD)

    def test_rom_offset_rejects_unknown_tile(self):
        with self.assertRaises(ValueError):
            self.layout.rom_offset(0x00)

    def test_render_produces_only_palette_shades(self):
        image = art_layout.render_art(self.layout, title_rom())
        self.assertEqual(image.mode, "L")
        self.assertEqual(image.size, (160, 104))
        self.assertTrue(set(image.getdata()) <= set(self.layout.shades))

    def test_round_trip_preserves_title_bytes(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        restored = bytearray(rom)
        art_layout.apply_art(self.layout, restored, image)
        self.assertEqual(restored, rom)

    def test_apply_changes_only_the_edited_tile(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        # Tile 0x31 appears in one cell only, at row 1, column 12.
        x, y = 12 * 8, 1 * 8
        image.putpixel((x, y), different_shade(self.layout, image.getpixel((x, y))))
        edited = bytearray(rom)
        art_layout.apply_art(self.layout, edited, image)
        changed = [index for index in range(ROM_SIZE) if edited[index] != rom[index]]
        self.assertTrue(changed)
        offset = self.layout.rom_offset(0x31)
        self.assertTrue(all(offset <= index < offset + art_layout.TILE_BYTES for index in changed))

    def test_apply_rejects_wrong_size(self):
        image = Image.new("L", (160, 135), 255)
        with self.assertRaises(ValueError):
            art_layout.apply_art(self.layout, title_rom(), image)

    def test_apply_rejects_conflicting_shared_tile(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        # Tile 0x5A is used in many cells, so changing one cell alone conflicts.
        row, col = next(
            (row, col)
            for row, cells in enumerate(self.layout.grid)
            for col, tile in enumerate(cells)
            if tile == 0x5A
        )
        x, y = col * 8, row * 8
        image.putpixel((x, y), different_shade(self.layout, image.getpixel((x, y))))
        with self.assertRaises(ValueError):
            art_layout.apply_art(self.layout, bytearray(rom), image)

    def test_apply_snaps_gray_values_to_nearest_shade(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        noisy = image.point(lambda value: min(255, value + 5) if value < 255 else value)
        restored = bytearray(rom)
        art_layout.apply_art(self.layout, restored, noisy)
        self.assertEqual(restored, rom)


if __name__ == "__main__":
    unittest.main()
