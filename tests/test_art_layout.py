import random
import struct
import sys
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

import art_layout  # noqa: E402

TITLE_START = 0x1A6AE
TITLE_END = 0x1B0FD
TILEMAP = 0x13C34
POINTER = 0x1800A
STOCK_LIST = 0x18110
ROM_SIZE = 0x20000
CELLS = 20 * 13
FREE_RUNS = ((0x61, 0x100), (0x3FC6, 0x3FFF), (0x1BF80, 0x1C000))


def title_rom(seed=1):
    rng = random.Random(seed)
    rom = bytearray(b"\xff" * ROM_SIZE)
    for offset in range(TITLE_START, TITLE_END + 1):
        rom[offset] = rng.getrandbits(8)
    stock_ids = list(range(0x31, 0xD3))
    for cell in range(CELLS):
        row, col = divmod(cell, 20)
        rom[TILEMAP + row * 20 + col] = rng.choice(stock_ids)
    rom[STOCK_LIST:STOCK_LIST + 14] = (
        struct.pack("<HHH", 0x0550, 0x66AE, 0x8800) + struct.pack("<HHH", 0x0500, 0x6BFE, 0x9300) + b"\x00\x00"
    )
    rom[POINTER:POINTER + 2] = struct.pack("<H", 0x4110)
    return rom


def distinct_tiles(layout, count, seed=2):
    rng = random.Random(seed)
    seen = set()
    tiles = []
    while len(tiles) < count:
        tile = tuple(rng.choice(layout.shades) for _ in range(64))
        if tile not in seen:
            seen.add(tile)
            tiles.append(tile)
    return tiles


def image_from_cells(layout, cell_tiles):
    image = Image.new("L", layout.image_size)
    for cell, pixels in enumerate(cell_tiles):
        row, col = divmod(cell, layout.columns)
        for y in range(8):
            for x in range(8):
                image.putpixel((col * 8 + x, row * 8 + y), pixels[y * 8 + x])
    return image


class TitleLayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout = art_layout.ART_LAYOUTS["title"]

    def test_in_place_pool_is_161_tiles_and_skips_text_and_cursor(self):
        ids = self.layout.in_place_ids()
        self.assertEqual(len(ids), 161)
        self.assertEqual(ids[0], 0x31)
        self.assertEqual(ids[-1], 0xD2)
        self.assertFalse({0x30, 0x3E, 0xD3, 0xD4} & set(ids))

    def test_in_place_offsets_match_stock_blocks(self):
        self.assertEqual(self.layout.in_place_offset(0x31), 0x1AC0E)
        self.assertEqual(self.layout.in_place_offset(0x3F), 0x1ACEE)
        self.assertEqual(self.layout.in_place_offset(0x80), TITLE_START)
        self.assertEqual(self.layout.in_place_offset(0xD2), TITLE_START + 0x52 * art_layout.TILE_BYTES)

    def test_in_place_offset_rejects_unknown_tile(self):
        with self.assertRaises(ValueError):
            self.layout.in_place_offset(0x30)
        with self.assertRaises(ValueError):
            self.layout.in_place_offset(0x3E)

    def test_image_is_20_by_13_cells(self):
        self.assertEqual(self.layout.image_size, (160, 104))

    def test_list_goes_where_it_leaves_most_slots(self):
        size = 6 * (2 + 14) + 2
        start, remaining = art_layout._place_list(FREE_RUNS, size)
        self.assertEqual(start, 0x61)
        self.assertEqual(remaining[0], (0x61 + size, 0x100))

    def test_storage_slots_give_14_slots_for_14_extra_tiles(self):
        size = 6 * (2 + 14) + 2
        start, remaining = art_layout._place_list(FREE_RUNS, size)
        self.assertEqual(len(art_layout._storage_slots(remaining)), 14)

    def test_render_produces_only_palette_shades(self):
        image = art_layout.render_art(self.layout, title_rom())
        self.assertEqual(image.mode, "L")
        self.assertEqual(image.size, (160, 104))
        self.assertTrue(set(image.getdata()) <= set(self.layout.shades))

    def test_round_trip_of_stock_render_is_identity(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        restored = bytearray(rom)
        art_layout.apply_art(self.layout, restored, image)
        self.assertEqual(art_layout.render_art(self.layout, restored).tobytes(), image.tobytes())

    def test_maximum_unique_tiles_round_trip(self):
        tiles = distinct_tiles(self.layout, 175)
        cells = tiles + [tiles[0]] * (CELLS - 175)
        image = image_from_cells(self.layout, cells)
        rom = title_rom()
        count = art_layout.apply_art(self.layout, rom, image)
        self.assertEqual(count, 175)
        self.assertEqual(art_layout.render_art(self.layout, rom).tobytes(), image.tobytes())
        self.assertEqual(rom[POINTER:POINTER + 2], b"\x61\x00")

    def test_copy_list_terminates_after_stock_and_extra_records(self):
        tiles = distinct_tiles(self.layout, 175)
        image = image_from_cells(self.layout, tiles + [tiles[0]] * (CELLS - 175))
        rom = title_rom()
        art_layout.apply_art(self.layout, rom, image)
        self.assertEqual(rom[0x61 + 6 * 15:0x61 + 6 * 15 + 2], b"\x10\x00")
        self.assertEqual(rom[0x61 + 6 * 16:0x61 + 6 * 16 + 2], b"\x00\x00")

    def test_too_many_unique_tiles_fails_without_writing(self):
        tiles = distinct_tiles(self.layout, 176)
        image = image_from_cells(self.layout, tiles + [tiles[0]] * (CELLS - 176))
        rom = title_rom()
        original = bytes(rom)
        with self.assertRaises(ValueError):
            art_layout.apply_art(self.layout, rom, image)
        self.assertEqual(bytes(rom), original)

    def test_apply_changes_only_title_tiles_tilemap_pointer_and_free_runs(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        image.putpixel((12 * 8, 1 * 8), different_shade(self.layout, image.getpixel((12 * 8, 1 * 8))))
        edited = bytearray(rom)
        art_layout.apply_art(self.layout, edited, image)
        allowed = [
            (TITLE_START, TITLE_END + 1),
            (TILEMAP, TILEMAP + CELLS),
            (POINTER, POINTER + 2),
            (0x1BF80, 0x1C000),
            (0x61, 0x100),
            (0x3FC6, 0x3FFF),
        ]
        changed = [index for index in range(ROM_SIZE) if edited[index] != rom[index]]
        self.assertTrue(changed)
        self.assertTrue(all(any(start <= index < end for start, end in allowed) for index in changed))

    def test_apply_rejects_wrong_size(self):
        image = Image.new("L", (160, 135), 255)
        with self.assertRaises(ValueError):
            art_layout.apply_art(self.layout, title_rom(), image)

    def test_apply_snaps_gray_values_to_nearest_shade(self):
        rom = title_rom()
        image = art_layout.render_art(self.layout, rom)
        noisy = image.point(lambda value: min(255, value + 5) if value < 255 else value)
        restored = bytearray(rom)
        art_layout.apply_art(self.layout, restored, noisy)
        self.assertEqual(art_layout.render_art(self.layout, restored).tobytes(), image.tobytes())


def different_shade(layout, shade):
    return next(value for value in layout.shades if value != shade)


if __name__ == "__main__":
    unittest.main()

