import argparse
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tests.support import blank_rom, load_bin_module

render_graphics = load_bin_module("render_graphics")


def blue_count(colors):
    """Count pixels from a {color: count} mapping that use a bluescale shade."""
    return sum(
        count
        for color, count in colors.items()
        if color in render_graphics.BLUESCALE_PALETTE
    )


def yellow_count(colors):
    """Count pixels from a {color: count} mapping that use a yellowscale shade."""
    return sum(
        count
        for color, count in colors.items()
        if color in render_graphics.YELLOWSCALE_PALETTE
    )


def green_count(colors):
    """Count pixels from a {color: count} mapping that use a greenscale shade."""
    return sum(
        count
        for color, count in colors.items()
        if color in render_graphics.GREENSCALE_PALETTE
    )


def purple_count(colors):
    """Count pixels from a {color: count} mapping that use a purplescale shade."""
    return sum(
        count
        for color, count in colors.items()
        if color in render_graphics.PURPLESCALE_PALETTE
    )


def color_counts(image):
    return {color: count for count, color in image.getcolors(image.width * image.height)}


class RenderGraphicsTests(unittest.TestCase):
    def test_compare_shades_matching_bytes_blue_and_changed_bytes_red(self):
        data = bytes([0xC0, 0x00]) + bytes(14)
        comparison = bytes([0xC0, 0x80]) + bytes(14)
        image = render_graphics.render_tile_grid(
            data, 1, 1, columns=1, scale=1, comparison=comparison
        )
        self.assertEqual(image.getpixel((0, 0)), render_graphics.BLUESCALE_PALETTE[1])
        self.assertEqual(image.getpixel((1, 0)), render_graphics.BLUESCALE_PALETTE[1])
        self.assertEqual(image.getpixel((2, 0)), render_graphics.REDSCALE_PALETTE[0])

        working_image = render_graphics.render_tile_grid(
            comparison, 1, 1, columns=1, scale=1, comparison=data
        )
        self.assertEqual(working_image.getpixel((0, 0)), render_graphics.REDSCALE_PALETTE[3])
        self.assertEqual(working_image.getpixel((1, 0)), render_graphics.BLUESCALE_PALETTE[1])

        same = render_graphics.render_tile_grid(
            data, 1, 1, columns=1, scale=1, comparison=data
        )
        self.assertEqual(same.getpixel((0, 0)), render_graphics.BLUESCALE_PALETTE[1])
        self.assertEqual(same.getpixel((2, 0)), render_graphics.BLUESCALE_PALETTE[0])

    def test_compare_requires_equal_range_lengths(self):
        with self.assertRaisesRegex(ValueError, "same length"):
            render_graphics.render_tile_grid(
                bytes(16), 1, 1, comparison=bytes(15)
            )

    def test_compare_glyphs_shade_matching_bytes_blue(self):
        data = bytes([0x80]) + bytes(15)
        comparison = bytes([0x80]) + bytes([0x01]) + bytes(14)
        image = render_graphics.render_stacked_glyphs(
            data, columns=1, scale=1, comparison=comparison
        )
        self.assertEqual(image.getpixel((0, 0)), render_graphics.BLUESCALE_PALETTE[3])
        self.assertEqual(image.getpixel((1, 0)), render_graphics.BLUESCALE_PALETTE[0])
        self.assertEqual(image.getpixel((7, 1)), render_graphics.REDSCALE_PALETTE[0])

    def test_comparison_composes_labeled_panels_with_independent_axes(self):
        base = bytes([0xFF, 0]) * 8
        working = bytes([0x7F, 0]) * 8
        base_panel = render_graphics.render_sprites(
            base, columns=1, scale=1, start_address=0x1000, comparison=working
        )
        working_panel = render_graphics.render_sprites(
            working, columns=1, scale=1, start_address=0x1000, comparison=base
        )
        combined = render_graphics.combine_comparison_images(base_panel, working_panel)
        font = render_graphics.ImageFont.load_default()
        header_height = font.getbbox("Input ROM")[3] - font.getbbox("Input ROM")[1] + 12
        gap = 24
        self.assertEqual(combined.size, (base_panel.width + gap + working_panel.width,
                                         header_height + max(base_panel.height, working_panel.height)))
        self.assertEqual(
            combined.crop((0, header_height, base_panel.width, header_height + base_panel.height)).tobytes(),
            base_panel.tobytes(),
        )
        self.assertEqual(
            combined.crop((base_panel.width + gap, header_height,
                           base_panel.width + gap + working_panel.width,
                           header_height + working_panel.height)).tobytes(),
            working_panel.tobytes(),
        )

    def test_parses_tile_grid_dimensions(self):
        self.assertEqual(render_graphics.parse_tile_grid("2x3"), (2, 3))
        self.assertEqual(render_graphics.parse_tile_grid("1X2"), (1, 2))
        for value in ("0x2", "2x0", "2by2", "2x2x2"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                render_graphics.parse_tile_grid(value)

    def test_decodes_two_bitplanes_left_to_right(self):
        tile = bytes([0x80, 0x40]) + bytes(14)
        decoded = render_graphics.decode_tiles(tile)
        self.assertEqual(decoded[0][0], [1, 2, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][1], [0] * 8)

    def test_rejects_empty_data(self):
        with self.assertRaisesRegex(ValueError, "at least one byte"):
            render_graphics.decode_tiles(b"")

    def test_decodes_partial_tiles_at_byte_granularity(self):
        for length in range(1, render_graphics.TILE_BYTES):
            with self.subTest(length=length):
                tile = render_graphics.decode_tiles(bytes(length))[0]
                self.assertEqual(tile, [[0] * 8 for _ in range(8)])

        one_byte_tile = render_graphics.decode_tiles(b"\x80")[0]
        self.assertEqual(one_byte_tile[0], [1, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(one_byte_tile[1:], [[0] * 8 for _ in range(7)])

        decoded = render_graphics.decode_tiles(bytes([0x80, 0, 0x40, 0]))
        self.assertEqual(decoded[0][0], [1, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][1], [0, 1, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoded[0][2:], [[0] * 8 for _ in range(6)])

    def test_assembles_four_tiles_in_column_first_sprite_order(self):
        tile_1 = bytes([0xFF, 0]) * 8
        tile_2 = bytes([0, 0xFF]) * 8
        tile_3 = bytes([0xFF, 0xFF]) * 8
        tile_0 = bytes(16)
        image = render_graphics.render_sprites(
            tile_1 + tile_2 + tile_3 + tile_0,
            columns=1,
            scale=2,
        )
        self.assertEqual(image.size, (32, 32))
        self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))
        self.assertEqual(image.getpixel((0, 16)), (170, 170, 170))
        self.assertEqual(image.getpixel((16, 0)), (255, 255, 255))
        self.assertEqual(image.getpixel((16, 16)), (0, 0, 0))

    def test_assembles_arbitrary_tile_grid_in_row_major_order(self):
        def tile_data(color):
            low = 0xFF if color & 1 else 0
            high = 0xFF if color & 2 else 0
            return bytes((low, high)) * 8

        data = b"".join(tile_data(index % 4) for index in range(6))
        image = render_graphics.render_tile_grid(data, 2, 3, columns=1, scale=1)
        self.assertEqual(image.size, (16, 24))
        self.assertEqual(image.getpixel((8, 0)), render_graphics.DEFAULT_PALETTE[1])
        self.assertEqual(image.getpixel((0, 8)), render_graphics.DEFAULT_PALETTE[2])

    def test_incomplete_sprite_keeps_tiles_and_leaves_missing_quadrants_blank(self):
        tile_1 = bytes([0xFF, 0]) * 8
        tile_2 = bytes([0, 0xFF]) * 8
        image = render_graphics.render_sprites(tile_1 + tile_2, columns=1, scale=1)
        self.assertEqual(image.size, (16, 16))
        self.assertEqual(image.getpixel((0, 0)), (85, 85, 85))
        self.assertEqual(image.getpixel((0, 8)), (170, 170, 170))
        self.assertEqual(image.getpixel((8, 0)), render_graphics.EMPTY_COLOR)
        self.assertEqual(image.getpixel((16 - 1, 0)), render_graphics.EMPTY_COLOR)

    def test_highlights_only_rows_inside_known_sprite_ranges(self):
        tile = bytes([0xFF, 0]) * 8
        image = render_graphics.render_tile_grid(
            tile * 2,
            1,
            1,
            columns=2,
            scale=1,
            start_address=0x8030,
            highlight_known=True,
        )
        colors = {
            color: count
            for count, color in image.getcolors(image.width * image.height)
        }
        self.assertEqual(colors[render_graphics.DEFAULT_PALETTE[1]], 120)
        self.assertEqual(blue_count(colors), 8)

    def test_partial_sprite_edge_tiles_do_not_highlight_overlapping_code(self):
        tile = bytes([0xFF]) * render_graphics.TILE_BYTES
        front = render_graphics.render_tile_grid(
            tile,
            1,
            1,
            columns=1,
            scale=1,
            start_address=0x5286,
            highlight_known=True,
        )
        back = render_graphics.render_tile_grid(
            tile,
            1,
            1,
            columns=1,
            scale=1,
            start_address=0x5576,
            highlight_known=True,
        )
        front_colors = {
            color: count
            for count, color in front.getcolors(front.width * front.height)
        }
        back_colors = {
            color: count
            for count, color in back.getcolors(back.width * back.height)
        }
        self.assertEqual(blue_count(front_colors), 16)
        self.assertEqual(blue_count(back_colors), 40)

    def test_known_kind_covers_chest_through_npc_block(self):
        self.assertEqual(render_graphics.known_kind(0x1811E), "graphics")
        self.assertEqual(render_graphics.known_kind(0x1861D), "graphics")
        self.assertEqual(render_graphics.known_kind(0x1811D), "structure")
        self.assertEqual(render_graphics.known_kind(0x1861E), "graphics")
        self.assertEqual(render_graphics.known_kind(0x18A1D), "graphics")
        self.assertEqual(render_graphics.known_kind(0x18A1E), "graphics")
        self.assertEqual(render_graphics.known_kind(0x1A6AD), "graphics")
        self.assertEqual(render_graphics.known_kind(0x17185), "graphics")
        self.assertEqual(render_graphics.known_kind(0x17724), "graphics")
        self.assertEqual(render_graphics.known_kind(0x17725), "lookup")
        self.assertIsNone(render_graphics.known_kind(0x1B0FE))
        self.assertEqual(render_graphics.known_kind(0x17165), "lookup")
        self.assertEqual(render_graphics.known_kind(0x17184), "lookup")
        self.assertIsNone(render_graphics.known_kind(0x15448))
        self.assertEqual(render_graphics.known_kind(0x15449), "lookup")
        self.assertEqual(render_graphics.known_kind(0x15D07), "lookup")
        self.assertIsNone(render_graphics.known_kind(0x15D08))
        self.assertIsNone(render_graphics.known_kind(0x17064))
        self.assertEqual(render_graphics.known_kind(0x17065), "lookup")
        self.assertEqual(render_graphics.known_kind(0x17164), "lookup")

    def test_lookup_tables_shade_in_green(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        lookup = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0x17165, highlight_known=True
        )
        lookup_colors = color_counts(lookup)
        self.assertEqual(green_count(lookup_colors), 64)
        self.assertEqual(blue_count(lookup_colors), 0)
        self.assertEqual(yellow_count(lookup_colors), 0)
        # 0x17185 starts the map-screen graphics, which stay blue.
        graphics = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0x17185, highlight_known=True
        )
        self.assertEqual(green_count(color_counts(graphics)), 0)
        self.assertEqual(blue_count(color_counts(graphics)), 64)

    def test_highlights_graphics_through_bc85_but_not_bc86(self):
        first_glyph = render_graphics.render_tile_grid(
            bytes(render_graphics.TILE_BYTES),
            1,
            1,
            columns=1,
            scale=1,
            start_address=0xB566,
            highlight_known=True,
        )
        first_ui_tile = render_graphics.render_tile_grid(
            bytes(render_graphics.TILE_BYTES),
            1,
            1,
            columns=1,
            scale=1,
            start_address=0xB666,
            highlight_known=True,
        )
        first_frame_tile = render_graphics.render_tile_grid(
            bytes(render_graphics.TILE_BYTES),
            1,
            1,
            columns=1,
            scale=1,
            start_address=0xB806,
            highlight_known=True,
        )
        first_item_tile = render_graphics.render_tile_grid(
            bytes(render_graphics.TILE_BYTES),
            1,
            1,
            columns=1,
            scale=1,
            start_address=0xB886,
            highlight_known=True,
        )
        boundary_tile = render_graphics.render_tile_grid(
            bytes([0xFF]) * render_graphics.TILE_BYTES,
            1,
            1,
            columns=1,
            scale=1,
            start_address=0xBAF6,
            highlight_known=True,
        )
        after_range_tile = render_graphics.render_tile_grid(
            bytes([0xFF]) * render_graphics.TILE_BYTES,
            1,
            1,
            columns=1,
            scale=1,
            start_address=0xBC86,
            highlight_known=True,
        )
        first_colors = {
            color: count
            for count, color in first_glyph.getcolors(first_glyph.width * first_glyph.height)
        }
        boundary_colors = {
            color: count
            for count, color in boundary_tile.getcolors(
                boundary_tile.width * boundary_tile.height
            )
        }
        self.assertEqual(blue_count(first_colors), 64)
        first_ui_colors = {
            color: count
            for count, color in first_ui_tile.getcolors(
                first_ui_tile.width * first_ui_tile.height
            )
        }
        self.assertEqual(blue_count(first_ui_colors), 64)
        first_frame_colors = {
            color: count
            for count, color in first_frame_tile.getcolors(
                first_frame_tile.width * first_frame_tile.height
            )
        }
        self.assertEqual(blue_count(first_frame_colors), 64)
        first_item_colors = {
            color: count
            for count, color in first_item_tile.getcolors(
                first_item_tile.width * first_item_tile.height
            )
        }
        self.assertEqual(blue_count(first_item_colors), 64)
        self.assertEqual(blue_count(boundary_colors), 64)
        after_range_colors = {
            color: count
            for count, color in after_range_tile.getcolors(
                after_range_tile.width * after_range_tile.height
            )
        }
        self.assertEqual(blue_count(after_range_colors), 0)

    def test_stacked_glyphs_render_each_half_as_one_glyph(self):
        # Bit 0 is ink, so 0x00 is solid black and 0xFF is blank.
        tile = bytes([0x00] * 8 + [0xFF] * 8)
        image = render_graphics.render_stacked_glyphs(tile, columns=1, scale=1)
        self.assertEqual(image.size, (render_graphics.TILE_WIDTH, render_graphics.TILE_BYTES))
        colors = {color: count for count, color in image.getcolors(image.width * image.height)}
        self.assertEqual(colors[render_graphics.DEFAULT_PALETTE[0]], 64)
        self.assertEqual(colors[render_graphics.DEFAULT_PALETTE[3]], 64)
        self.assertEqual(image.getpixel((0, 0)), render_graphics.DEFAULT_PALETTE[0])
        self.assertEqual(image.getpixel((0, 8)), render_graphics.DEFAULT_PALETTE[3])

    def test_stacked_glyphs_highlight_only_known_rows(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        image = render_graphics.render_stacked_glyphs(
            tile, columns=1, scale=1, start_address=0xBC80, highlight_known=True
        )
        colors = {color: count for count, color in image.getcolors(image.width * image.height)}
        # Rows at 0xBC80-0xBC85 are inside the known range; 0xBC86-0xBC8F are not.
        self.assertEqual(blue_count(colors), 48)


        with self.assertRaisesRegex(ValueError, "start address is required"):
            render_graphics.render_tile_grid(
                bytes(render_graphics.TILE_BYTES),
                1,
                1,
                highlight_known=True,
            )

    def test_bluescale_keeps_each_palette_shade_distinct(self):
        # Row 0 uses all four color indices: 3, 3, 1, 1, 2, 2, 0, 0.
        tile = bytes([0xF0, 0xCC]) + bytes(render_graphics.TILE_BYTES - 2)
        image = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0xBB00, highlight_known=True
        )
        colors = {color for _, color in image.getcolors(image.width * image.height)}
        blue_colors = {color for color in colors if color in render_graphics.BLUESCALE_PALETTE}
        self.assertEqual(blue_colors, set(render_graphics.BLUESCALE_PALETTE))

    def test_text_ranges_shade_in_yellow(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        credits = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0xBC86, highlight_known=True
        )
        title = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0x0134, highlight_known=True
        )
        credits_colors = color_counts(credits)
        self.assertEqual(yellow_count(credits_colors), 64)
        self.assertEqual(blue_count(credits_colors), 0)
        self.assertEqual(yellow_count(color_counts(title)), 64)

    def test_item_name_fragments_shade_exact_bytes_in_yellow(self):
        ranges = (
            (0x040A2, 0x040AC),
            (0x040B0, 0x040BC),
            (0x040CC, 0x040D6),
            (0x040DA, 0x040E6),
            (0x040F6, 0x04100),
            (0x04104, 0x04110),
            (0x04120, 0x0412A),
            (0x0412E, 0x0413A),
        )
        image = render_graphics.render_tile_grid(
            bytes([0xFF] * render_graphics.TILE_BYTES * 6),
            6,
            1,
            columns=6,
            scale=1,
            start_address=0x040A0,
            highlight_known=True,
        )
        expected_rows = sum(
            any(start <= address and address + 1 < end for start, end in ranges)
            for address in range(0x040A0, 0x04100, 2)
        )
        self.assertEqual(yellow_count(color_counts(image)), expected_rows * 8)
        for start, end in ranges:
            with self.subTest(start=hex(start), end=hex(end)):
                self.assertEqual(render_graphics.known_kind(start), "text")
                self.assertEqual(render_graphics.known_kind(end - 1), "text")
                self.assertIsNone(render_graphics.known_kind(end))

    def test_text_highlight_stops_at_its_end_address(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        # 0xBFAB is the exclusive end of the documented credits range.
        image = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0xBFA8, highlight_known=True
        )
        self.assertEqual(yellow_count(color_counts(image)), 8)
        self.assertEqual(blue_count(color_counts(image)), 0)
        self.assertEqual(render_graphics.known_kind(0xBFAA), "text")
        self.assertIsNone(render_graphics.known_kind(0xBFAB))

    def test_pause_menu_labels_highlight_only_their_bytes(self):
        ranges = (
            (0x041AF, 0x041B3),
            (0x041BB, 0x041BF),
            (0x041C1, 0x041C5),
            (0x041C7, 0x041CB),
        )
        for start, end in ranges:
            with self.subTest(start=hex(start)):
                self.assertIsNone(render_graphics.known_kind(start - 1))
                for address in range(start, end):
                    self.assertEqual(render_graphics.known_kind(address), "text")
                self.assertIsNone(render_graphics.known_kind(end))

    def test_character_name_ranges_highlight_only_their_bytes(self):
        self.assertIsNone(render_graphics.known_kind(0x043C2))
        for address in range(0x043C3, 0x043FB):
            self.assertEqual(render_graphics.known_kind(address), "text")
        self.assertIsNone(render_graphics.known_kind(0x043FB))

    def test_stat_labels_before_ability_table_are_highlighted(self):
        for start, end in ((0x0471B, 0x04721), (0x04722, 0x04727),
                           (0x04728, 0x0472E), (0x0472F, 0x04736)):
            with self.subTest(start=hex(start)):
                self.assertIsNone(render_graphics.known_kind(start - 1))
                for address in range(start, end):
                    self.assertEqual(render_graphics.known_kind(address), "text")
        self.assertEqual(render_graphics.known_kind(0x04736), "text")

    def test_range_labels_extend_existing_highlighting(self):
        for start, end in ((0x04999, 0x0499F), (0x0499F, 0x049A5),
                           (0x049A5, 0x049AB), (0x049AB, 0x049B1),
                           (0x049B1, 0x049B7)):
            with self.subTest(start=hex(start)):
                for address in range(start, end):
                    self.assertEqual(render_graphics.known_kind(address), "text")
        self.assertIsNone(render_graphics.known_kind(0x049B7))

    def test_character_change_label_highlighting(self):
        self.assertIsNone(render_graphics.known_kind(0x04C76))
        for address in range(0x04C77, 0x04C81):
            self.assertEqual(render_graphics.known_kind(address), "text")
        self.assertIsNone(render_graphics.known_kind(0x04C81))

    def test_documented_text_and_table_ranges_shade_in_yellow(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        for address in (0x050CB, 0x17D4E, 0x1BD4E, 0x1C0F5, 0x1E620):
            with self.subTest(address=hex(address)):
                image = render_graphics.render_tile_grid(
                    tile,
                    1,
                    1,
                    columns=1,
                    scale=1,
                    start_address=address,
                    highlight_known=True,
                )
                self.assertEqual(yellow_count(color_counts(image)), 64)
        self.assertEqual(render_graphics.known_kind(0x050CA), None)
        self.assertEqual(render_graphics.known_kind(0x050CB), "text")
        self.assertEqual(render_graphics.known_kind(0x050E6), "text")
        self.assertEqual(render_graphics.known_kind(0x050E7), None)
        table = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0x1717C, highlight_known=True
        )
        self.assertEqual(green_count(color_counts(table)), 32)
        self.assertEqual(render_graphics.known_kind(0x17184), "lookup")
        self.assertEqual(render_graphics.known_kind(0x17185), "graphics")

    def test_world_map_layouts_are_highlighted_as_lookup_data(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        for address in (0x17725, 0x1782E, 0x17927):
            with self.subTest(address=hex(address)):
                image = render_graphics.render_tile_grid(
                    tile, 1, 1, columns=1, scale=1, start_address=address, highlight_known=True
                )
                self.assertEqual(green_count(color_counts(image)), 64)
        self.assertEqual(render_graphics.known_kind(0x17724), "graphics")
        self.assertEqual(render_graphics.known_kind(0x17725), "lookup")
        self.assertEqual(render_graphics.known_kind(0x17936), "lookup")
        self.assertIsNone(render_graphics.known_kind(0x17937))

    def test_title_tilemap_routines_and_tables_are_highlighted_as_structure(self):
        tile = bytes([0xFF] * render_graphics.TILE_BYTES)
        image = render_graphics.render_tile_grid(
            tile, 1, 1, columns=1, scale=1, start_address=0x13C30, highlight_known=True
        )
        self.assertEqual(purple_count(color_counts(image)), 64)
        self.assertEqual(render_graphics.known_kind(0x13C30), "structure")
        self.assertEqual(render_graphics.known_kind(0x13D9C), "structure")
        self.assertIsNone(render_graphics.known_kind(0x13D9D))
        self.assertEqual(render_graphics.known_kind(0x0A78), "structure")
        self.assertEqual(render_graphics.known_kind(0x0AA0), "structure")
        self.assertIsNone(render_graphics.known_kind(0x0AA1))
        self.assertEqual(render_graphics.known_kind(0x077D), "structure")
        self.assertIsNone(render_graphics.known_kind(0x077C))
        self.assertEqual(render_graphics.known_kind(0x0CCB), "structure")
        self.assertIsNone(render_graphics.known_kind(0x0CD4))
        self.assertEqual(render_graphics.known_kind(0x1800A), "structure")
        self.assertIsNone(render_graphics.known_kind(0x1800C))
        self.assertEqual(render_graphics.known_kind(0x1811E), "graphics")

    def test_mixed_planes_use_the_plane_that_owns_each_pixel(self):
        # Low byte is graphics, high byte is text: pixels from each plane take that shade.
        self.assertEqual(
            render_graphics.pixel_highlight_palette("graphics", "text", True, False),
            render_graphics.BLUESCALE_PALETTE,
        )
        self.assertEqual(
            render_graphics.pixel_highlight_palette("graphics", "text", False, True),
            render_graphics.YELLOWSCALE_PALETTE,
        )
        self.assertIsNone(
            render_graphics.pixel_highlight_palette("graphics", "text", True, True)
        )

    def test_highlighting_requires_a_start_address(self):
        with self.assertRaisesRegex(ValueError, "start address is required"):
            render_graphics.render_tile_grid(
                bytes(render_graphics.TILE_BYTES),
                1,
                1,
                highlight_known=True,
            )

    def test_assembles_portrait_tiles_in_row_major_order(self):
        def tile_data(color):
            low = 0xFF if color & 1 else 0
            high = 0xFF if color & 2 else 0
            return bytes((low, high)) * 8

        data = b"".join(tile_data(index % 4) for index in range(16))
        image = render_graphics.render_portraits(data, columns=1, scale=1)
        self.assertEqual(image.size, (32, 32))
        self.assertEqual(image.getpixel((8, 0)), render_graphics.PORTRAIT_PALETTE[1])
        self.assertEqual(image.getpixel((0, 8)), render_graphics.PORTRAIT_PALETTE[0])

    def test_portrait_renderer_requires_complete_portraits(self):
        with self.assertRaisesRegex(ValueError, "multiple of 0x100 bytes"):
            render_graphics.render_portraits(bytes(0xFF))

    def test_address_axes_label_cel_starts(self):
        with patch.object(render_graphics.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            render_graphics.render_sprites(
                bytes(3 * 4 * render_graphics.TILE_BYTES),
                columns=2,
                scale=1,
                start_address=0x1000,
            )
        self.assertEqual(
            [call.args[2] for call in draw_text.call_args_list],
            ["0x1000", "0x1040", "0x1000", "0x1080"],
        )

    def test_tile_grid_address_axes_use_grid_byte_size(self):
        tile_count = 3 * 2 * 3
        with patch.object(render_graphics.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            render_graphics.render_tile_grid(
                bytes(tile_count * render_graphics.TILE_BYTES),
                2,
                3,
                columns=2,
                scale=1,
                start_address=0x1000,
            )
        self.assertEqual(
            [call.args[2] for call in draw_text.call_args_list],
            ["0x1000", "0x1060", "0x1000", "0x10C0"],
        )

    def test_portrait_address_axes_label_each_256_byte_block(self):
        with patch.object(render_graphics.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            render_graphics.render_portraits(
                bytes(2 * render_graphics.PORTRAIT_BYTES),
                columns=2,
                scale=1,
                start_address=0x880E,
            )
        self.assertEqual(
            [call.args[2] for call in draw_text.call_args_list],
            ["0x880E", "0x890E", "0x880E"],
        )

    def test_cli_renders_portrait_mode(self):
        rom = blank_rom(header=True)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "portraits.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1100", str(output_path),
                "--input", str(input_path), "--mode", "portraits", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertIn(render_graphics.PORTRAIT_PALETTE[0], colors)

    def test_cli_renders_custom_tile_grid(self):
        rom = blank_rom(header=True)
        rom[0x1000] = 0x80

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "grid.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1060", str(output_path),
                "--input", str(input_path), "--tile-grid", "2x3",
                "--columns", "1", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertIn(render_graphics.DEFAULT_PALETTE[1], colors)

    def test_cli_highlights_known_sprites(self):
        rom = blank_rom(header=True)
        rom[0x8040:0x8060] = bytes([0xFF, 0]) * 16

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "known.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x8040", "0x8060", str(output_path),
                "--input", str(input_path), "--highlight-known", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertTrue(any(color in render_graphics.BLUESCALE_PALETTE for color in colors))

    def test_cli_highlights_known_tiles_in_custom_grid(self):
        rom = blank_rom(header=True)
        rom[0x8040:0x80A0] = bytes([0xFF, 0]) * 48

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "known-grid.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x8040", "0x80A0", str(output_path),
                "--input", str(input_path), "--tile-grid", "1x1",
                "--highlight-known", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertTrue(any(color in render_graphics.BLUESCALE_PALETTE for color in colors))

    def test_cli_highlights_known_tiles_in_portrait_mode(self):
        rom = blank_rom(header=True)
        rom[0x8800:0x8900] = bytes([0xFF, 0]) * 128

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "known-portraits.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x8800", "0x8900", str(output_path),
                "--input", str(input_path), "--mode", "portraits",
                "--highlight-known", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                colors = [color for _, color in image.getcolors(image.width * image.height)]
                self.assertTrue(any(color in render_graphics.BLUESCALE_PALETTE for color in colors))

    def test_cli_writes_png_for_a_rom_range(self):
        rom = blank_rom(header=True)
        rom[0x1000] = 0x80

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "tiles.png"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1010", str(output_path),
                "--input", str(input_path), "--columns", "1", "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                self.assertGreater(image.width, 16)
                self.assertGreater(image.height, 16)
                colors = image.getcolors(image.width * image.height)
                self.assertIn((85, 85, 85), [color for _, color in colors])
                top_axis = image.crop((0, 0, image.width, 16))
                self.assertTrue(any(pixel != (255, 255, 255) for pixel in top_axis.getdata()))

    def test_cli_writes_jpeg(self):
        rom = blank_rom(header=True)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "game.gb"
            output_path = root / "tiles.jpg"
            input_path.write_bytes(rom)
            arguments = [
                "render_graphics.py", "0x1000", "0x1010", str(output_path),
                "--input", str(input_path), "--scale", "1",
            ]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(render_graphics.main(), 0)
            with Image.open(output_path) as image:
                self.assertEqual(image.format, "JPEG")

    def test_banked_sprites_split_at_rom_bank_boundaries(self):
        data = b"\xff" * 0x20
        image = render_graphics.render_banked_sprites(data, 0x3FF0, columns=1, scale=1)
        bank_zero = render_graphics.render_sprites(data[:0x10], 1, 1, start_address=0x3FF0)
        bank_one = render_graphics.render_sprites(data[0x10:], 1, 1, start_address=0x4000)
        header = (
            image.height - bank_zero.height - bank_one.height - render_graphics.BANK_DIVIDER_HEIGHT
        ) // 2
        bank_one_top = bank_zero.height + header * 2 + render_graphics.BANK_DIVIDER_HEIGHT
        self.assertEqual(image.size[0], max(bank_zero.width, bank_one.width))
        self.assertEqual(
            image.crop((0, bank_one_top, bank_one.width, bank_one_top + bank_one.height)).tobytes(),
            bank_one.tobytes(),
        )

    def test_banked_sprites_draw_labels_and_full_width_dividers(self):
        image = render_graphics.render_banked_sprites(b"\xff" * 0xC000, 0, columns=16, scale=1)
        full_black_rows = [
            y for y in range(image.height)
            if all(image.getpixel((x, y)) == render_graphics.BANK_DIVIDER_COLOR for x in range(image.width))
        ]
        self.assertEqual(len(full_black_rows), 2 * render_graphics.BANK_DIVIDER_THICKNESS)
        header_pixels = [image.getpixel((x, y)) for y in range(full_black_rows[0]) for x in range(40)]
        self.assertTrue(any(sum(pixel) < 200 for pixel in header_pixels))

    def test_empty_sprite_cells_render_lilac(self):
        image = render_graphics.render_sprites(bytes([0xFF, 0]) * 8, columns=2, scale=1)
        self.assertEqual(image.size, (33, 16))
        self.assertEqual(image.getpixel((20, 4)), render_graphics.EMPTY_COLOR)
        self.assertEqual(image.getpixel((8, 0)), render_graphics.EMPTY_COLOR)


if __name__ == "__main__":
    unittest.main()
