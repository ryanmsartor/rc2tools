import random
import unittest

from PIL import Image

from tests.support import blank_rom

from character_art import (  # noqa: E402
    ATTACK_FIGURES, HERO_FIGURES, apply_character_art, character_sheet_size, render_character_art,
)
from render_graphics import DEFAULT_PALETTE, HACK_ART_PALETTE, PORTRAIT_PALETTE  # noqa: E402
from tiles import TILE_BYTES, TILE_WIDTH, encode_tile  # noqa: E402
from sprite_art import Piece, paste_piece  # noqa: E402
from swap_character_sprite import CHARACTER_SPRITES, SPRITE_BYTES, STANDARD_SPRITE_BYTES  # noqa: E402


HERO_BAND_START = 0x9346
HERO_BAND_END = 0x95C6


def solid_tile(index):
    return bytes((0xFF if index & 1 else 0, 0xFF if index & 2 else 0)) * 8


def id_tile(tile_id):
    """Encode a 16-bit id in the eight pixels of a tile's top row so each placed tile can be traced."""
    rows = [[0] * 8 for _ in range(8)]
    rows[0] = [(tile_id >> shift) & 3 for shift in range(0, 16, 2)]
    return encode_tile(rows)


def read_tile_id(image, x, y):
    shades = [HACK_ART_PALETTE.index(image.getpixel((x + px, y))) for px in range(8)]
    return sum(shade << (2 * index) for index, shade in enumerate(shades))


class CharacterArtTests(unittest.TestCase):
    def test_graphics_are_assembled_and_separated(self):
        rom = blank_rom()
        for character, (standard, defeated, face, portrait) in CHARACTER_SPRITES.items():
            offsets = [standard + index * SPRITE_BYTES for index in range(9)] + [defeated, face]
            for index, offset in enumerate(offsets):
                colors = (index % 4, index // 4, (index + 1) % 4, (index + 2) % 4)
                rom[offset:offset + SPRITE_BYTES] = b"".join(solid_tile(color) for color in colors)
            rom[portrait:portrait + 0x100] = b"".join(solid_tile(index % 4) for index in range(16))
        for character in CHARACTER_SPRITES:
            with self.subTest(character=character):
                self.assert_character_art(render_character_art(rom, character), character)

    def assert_character_art(self, image, character):
        self.assertEqual(image.size, character_sheet_size(character))
        shift = 17 if character == "zold" else 0
        for cell, index in enumerate((0, 1, 6, 4, 5, 8, 2, 3, 7, 9, 10)):
            if cell < 9:
                x, y = shift + (cell % 3) * 17, (cell // 3) * 17
            elif character == "zold":
                x, y = 0, (cell - 9) * 17
            else:
                x, y = 51 + (cell - 9) * 17, 34
            colors = (index % 4, index // 4, (index + 1) % 4, (index + 2) % 4)
            for tile, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
                self.assertEqual(image.getpixel((x + dx, y + dy)), HACK_ART_PALETTE[colors[tile]])
        for tile in range(16):
            self.assertEqual(
                image.getpixel((shift + 51 + (tile % 4) * 8, (tile // 4) * 8)),
                PORTRAIT_PALETTE[tile % 4],
            )
        for x in (16, 33, 50):
            self.assertTrue(all(image.getpixel((x + shift, y)) == (255, 0, 0) for y in range(50)))
        self.assertTrue(all(image.getpixel((x + shift, 16)) == (255, 0, 0) for x in range(51)))
        self.assertTrue(all(image.getpixel((x + shift, 33)) == (255, 0, 0) for x in range(84)))
        if character != "zold":
            self.assertTrue(all(image.getpixel((67, y)) == (255, 0, 0) for y in range(34, 50)))
        self.assertTrue(all(image.getpixel((x + shift, 32)) == (255, 0, 0) for x in range(51, 84)))
        self.assertTrue(all(image.getpixel((83 + shift, y)) == (255, 0, 0) for y in range(33)))

    def test_short_rom_is_rejected(self):
        for character in CHARACTER_SPRITES:
            with self.subTest(character=character):
                with self.assertRaisesRegex(ValueError, f"complete {character} sprite data"):
                    render_character_art(bytes(0x9000), character)

    def test_unknown_character_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown character"):
            render_character_art(bytes(0x20000), "unknown")

    def test_hero_band_places_each_tile_at_its_figure_position(self):
        rom = blank_rom()
        for offset in range(HERO_BAND_START, HERO_BAND_END, TILE_BYTES):
            rom[offset:offset + TILE_BYTES] = id_tile((offset // TILE_BYTES) & 0x3F)
        image = render_character_art(bytes(rom), "hero")
        self.assertEqual(image.size, (118, 67))
        for x, y, pieces in HERO_FIGURES:
            for piece in pieces:
                for index in range(piece.columns * piece.rows):
                    tile_column, tile_row = divmod(index, piece.rows)
                    px = x + (piece.left + tile_column) * 8
                    py = y + (piece.top + tile_row) * 8
                    if piece.offset is None:
                        self.assertTrue(all(
                            image.getpixel((px + dx, py + dy)) == (255, 0, 0)
                            for dx in range(8) for dy in range(8)
                        ))
                    else:
                        tile_offset = piece.offset + index * TILE_BYTES
                        self.assertEqual(read_tile_id(image, px, py), (tile_offset // TILE_BYTES) & 0x3F)

    def test_hero_band_covers_sword_arcs_and_electric_halves_exactly_once(self):
        tile_offsets = [
            piece.offset + index * TILE_BYTES
            for _, _, pieces in HERO_FIGURES
            for piece in pieces if piece.offset is not None
            for index in range(piece.columns * piece.rows)
        ]
        self.assertEqual(sorted(tile_offsets), list(range(HERO_BAND_START, HERO_BAND_END, TILE_BYTES)))

    def test_inject_skips_empty_hero_slots(self):
        original = random.Random(7).randbytes(0x20000)
        image = render_character_art(original, "hero")
        for x, y, pieces in HERO_FIGURES:
            for piece in pieces:
                if piece.offset is None:
                    px, py = x + piece.left * 8, y + piece.top * 8
                    image.paste((0, 0, 0), (px, py, px + 8, py + 8))
        rom = bytearray(original)
        apply_character_art(rom, "hero", image)
        self.assertEqual(rom, original)

    def test_round_trip_preserves_every_rom_byte_for_each_character(self):
        original = random.Random(42).randbytes(0x20000)
        for character in CHARACTER_SPRITES:
            with self.subTest(character=character):
                rom = bytearray(original)
                apply_character_art(rom, character, render_character_art(original, character))
                self.assertEqual(rom, original)

    def test_lee_particles_and_row_major_effects_render_and_inject(self):
        original = bytearray(random.Random(103).randbytes(0x20000))
        for offset in range(0xAA06, 0xAC86, TILE_BYTES):
            original[offset:offset + TILE_BYTES] = id_tile(offset)
        image = render_character_art(original, "lee")
        self.assertEqual(image.size, (110, 67))
        expected = bytearray(original)
        positions = [(0xAB86, 102, 0), (0xAB96, 102, 9)]
        for figure in range(6):
            for tile in range(4):
                positions.append((0xAA06 + figure * 64 + tile * TILE_BYTES,
                                  figure * 17 + tile // 2 * 8, 51 + tile % 2 * 8))
        for start, y, tile_count in ((0xABA6, 0, 2), (0xABC6, 9, 4), (0xAC06, 26, 6)):
            for tile in range(tile_count):
                positions.append((start + tile * TILE_BYTES, 85 + tile % 2 * 8, y + tile // 2 * 8))
        for index, (offset, x, y) in enumerate(positions):
            with self.subTest(offset=hex(offset)):
                self.assertEqual(read_tile_id(image, x, y), offset)
                color = index % 4
                image.paste(HACK_ART_PALETTE[color], (x, y, x + 8, y + 8))
                expected[offset:offset + TILE_BYTES] = solid_tile(color)
        for point in ((16, 51), (84, 51), (101, 0), (102, 8), (85, 8), (85, 25)):
            self.assertEqual(image.getpixel(point), (255, 0, 0))
            image.putpixel(point, (0, 0, 0))
        rom = bytearray(original)
        apply_character_art(rom, "lee", image)
        self.assertEqual(rom, expected)
        self.assertEqual(rom[0xAC66:0xAC86], original[0xAC66:0xAC86])

    def test_lora_attack_layout_and_injection(self):
        figures = (
            (0xAF06, 1, 2, 4, 51),
            (0xAF46, 2, 2, 17, 51),
            (0xAF86, 2, 2, 34, 51),
            (0xAFC6, 2, 2, 51, 51),
            (0xB006, 2, 2, 68, 51),
            (0xAF26, 2, 1, 0, 68),
            (0xB046, 2, 1, 17, 68),
            (0xB086, 1, 1, 38, 68),
        )
        original = bytearray(random.Random(101).randbytes(0x20000))
        for offset, columns, rows, _, _ in figures:
            for index in range(columns * rows):
                start = offset + index * TILE_BYTES
                original[start:start + TILE_BYTES] = id_tile(start & 0xFFFF)

        image = render_character_art(original, "lora")
        self.assertEqual(image.size, (84, 76))
        expected = bytearray(original)
        for offset, columns, rows, x, y in figures:
            for index in range(columns * rows):
                tile_column, tile_row = divmod(index, rows)
                px, py = x + tile_column * 8, y + tile_row * 8
                start = offset + index * TILE_BYTES
                self.assertEqual(read_tile_id(image, px, py), start & 0xFFFF)
                image.paste(HACK_ART_PALETTE[3], (px, py, px + 8, py + 8))
                expected[start:start + TILE_BYTES] = solid_tile(3)

        for x, y in ((34, 68), (46, 68), (51, 68), (68, 68)):
            self.assertEqual(image.getpixel((x, y)), (255, 0, 0))
            image.putpixel((x, y), (0, 0, 0))
        rom = bytearray(original)
        apply_character_art(rom, "lora", image)
        self.assertEqual(rom, expected)
        self.assertEqual(rom[0xB066:0xB086], original[0xB066:0xB086])
        self.assertEqual(rom[0xB096:0xB0A6], original[0xB096:0xB0A6])

    def test_zold_megaball_and_relocated_figures_render_and_inject(self):
        original = bytearray(random.Random(102).randbytes(0x20000))
        figures = (
            (0xB326, 17, 51), (0xB366, 34, 51), (0xB3A6, 51, 51),
            (0xB3E6, 0, 38), (0xB406, 4, 51),
            (CHARACTER_SPRITES["zold"][1], 0, 0), (CHARACTER_SPRITES["zold"][2], 0, 17),
        )
        for offset, _, _ in figures:
            original[offset:offset + TILE_BYTES] = id_tile(offset)
        for index in range(16):
            offset = 0xB426 + index * TILE_BYTES
            original[offset:offset + TILE_BYTES] = id_tile(index + 1)

        image = render_character_art(original, "zold")
        self.assertEqual(image.size, (101, 67))
        for offset, x, y in figures:
            self.assertEqual(read_tile_id(image, x, y), offset)
        expected = bytearray(original)
        for offset, x, y in figures:
            image.paste(HACK_ART_PALETTE[3], (x, y, x + 8, y + 8))
            expected[offset:offset + TILE_BYTES] = solid_tile(3)
        for index in range(16):
            x, y = 68 + (index % 4) * 8, 34 + (index // 4) * 8
            offset = 0xB426 + index * TILE_BYTES
            with self.subTest(tile=index + 1):
                self.assertEqual(read_tile_id(image, x, y), index + 1)
                color = index % 4
                image.paste(HACK_ART_PALETTE[color], (x, y, x + 8, y + 8))
                expected[offset:offset + TILE_BYTES] = solid_tile(color)

        self.assertEqual(image.getpixel((67, 34)), (255, 0, 0))
        image.putpixel((67, 34), (0, 0, 0))
        rom = bytearray(original)
        apply_character_art(rom, "zold", image)
        self.assertEqual(rom, expected)

    def test_inject_maps_every_tile_and_ignores_separators(self):
        original = random.Random(41).randbytes(0x20000)
        for character, (standard, defeated, face, portrait) in CHARACTER_SPRITES.items():
            with self.subTest(character=character):
                rom = bytearray(original)
                expected = bytearray(original)
                image = render_character_art(original, character)
                offsets = [standard + index * SPRITE_BYTES for index in (0, 1, 6, 4, 5, 8, 2, 3, 7)]
                offsets += [defeated, face]
                shift = 17 if character == "zold" else 0
                for cell, offset in enumerate(offsets):
                    if cell < 9:
                        x, y = shift + (cell % 3) * 17, (cell // 3) * 17
                    elif character == "zold":
                        x, y = 0, (cell - 9) * 17
                    else:
                        x, y = 51 + (cell - 9) * 17, 34
                    for tile, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
                        tile_offset = offset + tile * 16
                        color = (HACK_ART_PALETTE.index(image.getpixel((x + dx, y + dy))) + 1) % 4
                        image.putpixel((x + dx, y + dy), HACK_ART_PALETTE[color])
                        expected[tile_offset] = (expected[tile_offset] & 0x7F) | ((color & 1) << 7)
                        expected[tile_offset + 1] = (expected[tile_offset + 1] & 0x7F) | ((color >> 1) << 7)
                for tile in range(16):
                    x, y = shift + 51 + tile % 4 * 8, tile // 4 * 8
                    tile_offset = portrait + tile * 16
                    color = (PORTRAIT_PALETTE.index(image.getpixel((x, y))) + 1) % 4
                    image.putpixel((x, y), PORTRAIT_PALETTE[color])
                    expected[tile_offset] = (expected[tile_offset] & 0x7F) | ((color & 1) << 7)
                    expected[tile_offset + 1] = (expected[tile_offset + 1] & 0x7F) | ((color >> 1) << 7)
                points = [(16 + shift, 0), (51 + shift, 32), (83 + shift, 0)]
                if character != "zold":
                    points.append((67, 34))
                for point in points:
                    image.putpixel(point, (0, 255, 0))
                apply_character_art(rom, character, image)
                self.assertEqual(rom, expected)

    def test_inject_quantizes_using_each_region_palette(self):
        rom = blank_rom()
        image = render_character_art(rom, "hero")
        image.putpixel((0, 0), (90, 90, 90))
        image.putpixel((51, 0), (90, 90, 90))
        apply_character_art(rom, "hero", image)
        result = render_character_art(rom, "hero")
        self.assertEqual(result.getpixel((0, 0)), HACK_ART_PALETTE[2])
        self.assertEqual(result.getpixel((51, 0)), PORTRAIT_PALETTE[2])

    def test_inject_invalid_inputs_do_not_change_rom(self):
        original = bytes(0x20000)
        for character, image in (("hero", Image.new("RGB", (83, 50))), ("hero", Image.new("RGB", (84, 50))),
                                 ("invalid", Image.new("RGB", (84, 50)))):
            rom = bytearray(original)
            with self.assertRaises(ValueError):
                apply_character_art(rom, character, image)
            self.assertEqual(rom, original)
        rom = bytearray(0x9000)
        with self.assertRaisesRegex(ValueError, "complete hero sprite data"):
            apply_character_art(rom, "hero", Image.new("RGB", (84, 50)))
        self.assertEqual(rom, bytes(0x9000))


# Attack and particle sprites sit between the hero's defeated sprite and Zold's defeated sprite.
ATTACK_START = 0x95C6
ATTACK_END = 0xB566
# Transparent tiles omitted by dump and injection.
DROPPED_TRANSPARENT_RANGES = (
    (0xA1E6, 0xA206), (0xAC66, 0xAC86), (0xB066, 0xB086), (0xB096, 0xB0A6),
)


def _attack_pieces():
    return [piece for placements in ATTACK_FIGURES.values()
            for _, _, figure in placements for piece in figure if piece.offset is not None]


def _character_sprite_ranges():
    """Standard and defeated character sprites, which dump-art <character> already covers."""
    ranges = []
    for standard, defeated, _, _ in CHARACTER_SPRITES.values():
        ranges.append((standard, standard + STANDARD_SPRITE_BYTES))
        ranges.append((defeated, defeated + SPRITE_BYTES))
    return [(max(start, ATTACK_START), min(end, ATTACK_END)) for start, end in ranges
            if end > ATTACK_START and start < ATTACK_END]


class AttackArtCoverageTests(unittest.TestCase):
    def setUp(self):
        self.spans = sorted(
            (piece.offset, piece.offset + piece.columns * piece.rows * TILE_BYTES) for piece in _attack_pieces()
        )

    def test_pieces_do_not_overlap(self):
        for (_, end), (start, _) in zip(self.spans, self.spans[1:]):
            self.assertLessEqual(end, start)

    def test_pieces_cover_attack_range_outside_character_sprites(self):
        covered = set()
        for start, end in self.spans:
            covered.update(range(start, end))
        expected = set(range(ATTACK_START, ATTACK_END))
        for start, end in _character_sprite_ranges() + list(DROPPED_TRANSPARENT_RANGES):
            expected.difference_update(range(start, end))
        self.assertEqual(covered, expected)


class AttackArtRenderTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytes(range(256)) * 0x200

    def test_every_attack_sheet_renders_at_its_declared_size(self):
        for character in ATTACK_FIGURES:
            image = render_character_art(self.rom, character)
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.size, character_sheet_size(character))

    def test_empty_slot_renders_solid_red(self):
        image = Image.new("RGB", (8, 8))
        paste_piece(image, self.rom, Piece(None, 1, 1), 0, 0)
        self.assertEqual(set(image.getdata()), {(255, 0, 0)})

    def test_multi_tile_piece_is_stored_column_first(self):
        rom = bytearray(self.rom)
        offset = 0x9000
        colors = (0, 1, 2, 3)
        for index, color in enumerate(colors):
            rom[offset + index * TILE_BYTES:offset + (index + 1) * TILE_BYTES] = bytes(
                (0xFF if color & 1 else 0, 0xFF if color & 2 else 0)
            ) * 8
        image = Image.new("RGB", (16, 16))
        paste_piece(image, bytes(rom), Piece(offset, 2, 2), 0, 0)
        # Tiles run down each column before moving right: 0 top-left, 1 bottom-left, 2 top-right, 3 bottom-right.
        for index, color in enumerate(colors):
            tile_column, tile_row = divmod(index, 2)
            self.assertEqual(image.getpixel((tile_column * 8, tile_row * 8)), HACK_ART_PALETTE[color])


class AttackArtInjectionTests(unittest.TestCase):
    def test_every_attack_sheet_writes_back_its_pixels(self):
        original = random.Random(7).randbytes(0x20000)
        for character, placements in ATTACK_FIGURES.items():
            with self.subTest(character=character):
                x, y, figure = placements[0]
                piece = figure[0]
                px, py = x + piece.left * TILE_WIDTH, y + piece.top * TILE_WIDTH
                image = render_character_art(original, character)
                current = HACK_ART_PALETTE.index(image.getpixel((px, py)))
                image.putpixel((px, py), HACK_ART_PALETTE[(current + 1) % 4])
                rom = bytearray(original)
                apply_character_art(rom, character, image)
                self.assertNotEqual(rom, original)
                self.assertEqual(render_character_art(bytes(rom), character).getpixel((px, py)),
                                 HACK_ART_PALETTE[(current + 1) % 4])


if __name__ == "__main__":
    unittest.main()
