#!/usr/bin/env python3
"""Render ROM tiles as sprites, portraits, or arbitrary tile grids."""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from rom_io import BANK_SIZE, parse_offset, read_rom
from known_graphics import KNOWN_GRAPHICS_RANGES
from tiles import TILE_BYTES, TILE_WIDTH, decode_tiles

SPRITE_TILE_POSITIONS = ((0, 0), (0, 1), (1, 0), (1, 1))
SPRITE_WIDTH = TILE_WIDTH * 2
SPRITE_GUTTER = 1
GUTTER_COLOR = (192, 192, 192)
# Cells without ROM bytes use lilac so they are not mistaken for all-white data.
EMPTY_COLOR = (200, 162, 200)
BANK_LABEL_PADDING = 4
BANK_DIVIDER_PADDING = 8
BANK_DIVIDER_THICKNESS = 2
BANK_DIVIDER_HEIGHT = 2 * BANK_DIVIDER_PADDING + BANK_DIVIDER_THICKNESS
BANK_DIVIDER_COLOR = (0, 0, 0)
# Known pixels keep their palette shade, mapped to blue (index 0 is darkest, 3 lightest).
BLUESCALE_PALETTE = (
    (0, 0, 96),
    (0, 0, 160),
    (96, 96, 224),
    (192, 192, 255),
)
# Changed pixels use the same shade progression in red.
REDSCALE_PALETTE = (
    (96, 0, 0),
    (160, 0, 0),
    (224, 96, 96),
    (255, 192, 192),
)
# Known text pixels use the same scheme in yellow.
YELLOWSCALE_PALETTE = (
    (96, 96, 0),
    (160, 160, 0),
    (224, 224, 96),
    (255, 255, 192),
)
# Known lookup-table pixels use the same scheme in green.
GREENSCALE_PALETTE = (
    (0, 40, 0),
    (0, 88, 32),
    (40, 136, 80),
    (136, 200, 160),
)
# Known structure pixels (tilemaps, pointer and record tables, and routines) use the same scheme in purple.
PURPLESCALE_PALETTE = (
    (32, 0, 64),
    (72, 32, 120),
    (112, 80, 168),
    (160, 128, 208),
)
PORTRAIT_TILE_COLUMNS = 4
PORTRAIT_TILE_COUNT = PORTRAIT_TILE_COLUMNS ** 2
PORTRAIT_BYTES = PORTRAIT_TILE_COUNT * TILE_BYTES
PORTRAIT_WIDTH = PORTRAIT_TILE_COLUMNS * TILE_WIDTH
# Exclusive physical-ROM ranges documented in docs/known-text.md, shaded in yellow.
KNOWN_TEXT_RANGES = (
    (0x00134, 0x00144),
    (0x040A2, 0x040AC),
    (0x040B0, 0x040BC),
    (0x040CC, 0x040D6),
    (0x040DA, 0x040E6),
    (0x040F6, 0x04100),
    (0x04104, 0x04110),
    (0x04120, 0x0412A),
    (0x0412E, 0x0413A),
    (0x041AF, 0x041B3),
    (0x041BB, 0x041BF),
    (0x041C1, 0x041C5),
    (0x041C7, 0x041CB),
    (0x043C3, 0x043FB),
    (0x0471B, 0x04721),
    (0x04722, 0x04727),
    (0x04728, 0x0472E),
    (0x0472F, 0x04736),
    (0x04736, 0x04823),
    (0x04998, 0x049A9),
    (0x049A7, 0x049AB),
    (0x049AB, 0x049B7),
    (0x04A7C, 0x04AC9),
    (0x04C77, 0x04C81),
    (0x050CB, 0x050E7),
    (0x05109, 0x0511B),
    (0x058EB, 0x0590F),
    (0x0BC8A, 0x0BCBD),
    (0x0BCBE, 0x0BCEC),
    (0x0BCED, 0x0BD16),
    (0x0BD24, 0x0BD54),
    (0x0BD55, 0x0BD64),
    (0x0BD6B, 0x0BDA0),
    (0x0BDA1, 0x0BDA7),
    (0x0BDAE, 0x0BDE0),
    (0x0BDE1, 0x0BE08),
    (0x0BE0F, 0x0BE3D),
    (0x0BE3E, 0x0BE55),
    (0x0BE5C, 0x0BE8F),
    (0x0BE96, 0x0BEC5),
    (0x0BECC, 0x0BEFE),
    (0x0BF05, 0x0BF32),
    (0x0BF33, 0x0BF64),
    (0x0BF65, 0x0BF98),
    (0x0BF99, 0x0BFAD),
    (0x13D3B, 0x13D40),
    (0x13D42, 0x13D4A),
    (0x13D60, 0x13D74),
    (0x13D88, 0x13D9C),
    (0x17C8E, 0x17C94),
    (0x17C94, 0x17C9B),
    (0x17C9B, 0x17CA1),
    (0x17CA1, 0x17CA7),
    (0x17CA7, 0x17CAC),
    (0x17CAC, 0x17CB1),
    (0x17CB1, 0x17CB7),
    (0x17CB7, 0x17CBF),
    (0x17CBF, 0x17CC5),
    (0x17CC5, 0x17CCB),
    (0x17CCB, 0x17CD0),
    (0x17CD0, 0x17CD5),
    (0x17CD5, 0x17CDC),
    (0x17CDC, 0x17CE3),
    (0x17CE3, 0x17CEB),
    (0x17CEB, 0x17CF3),
    (0x17D4E, 0x17D6F),
    (0x17D70, 0x17D80),
    (0x1B311, 0x1B315),
    (0x1B315, 0x1B319),
    (0x1B319, 0x1B31D),
    (0x1B31D, 0x1B321),
    (0x1B321, 0x1B325),
    (0x1B325, 0x1B329),
    (0x1B329, 0x1B32D),
    (0x1B32D, 0x1B331),
    (0x1B9A1, 0x1B9C7),
    (0x1BA08, 0x1BA0C),
    (0x1BABA, 0x1BACC),
    (0x1BD4E, 0x1BD6F),
    (0x1BD70, 0x1BD80),
    (0x1C0C0, 0x1C0F5),
    (0x1C10C, 0x1C13E),
    (0x1C1AC, 0x1C209),
    (0x1C222, 0x1C257),
    (0x1C258, 0x1C2A8),
    (0x1C2A9, 0x1C2D9),
    (0x1C2DA, 0x1C329),
    (0x1C32D, 0x1C35D),
    (0x1C35E, 0x1C3AD),
    (0x1C3AE, 0x1C441),
    (0x1C444, 0x1C48C),
    (0x1C492, 0x1C4B4),
    (0x1C4B7, 0x1C4DB),
    (0x1C4DC, 0x1C515),
    (0x1C51C, 0x1C51F),
    (0x1C522, 0x1C566),
    (0x1C567, 0x1C5C2),
    (0x1C5C5, 0x1C6A9),
    (0x1C6AC, 0x1C77F),
    (0x1C788, 0x1C7B5),
    (0x1C7B6, 0x1C7D9),
    (0x1C7DA, 0x1C81C),
    (0x1C820, 0x1C83C),
    (0x1C83D, 0x1C84C),
    (0x1C84D, 0x1C8B0),
    (0x1C8B3, 0x1C917),
    (0x1C91D, 0x1C921),
    (0x1C924, 0x1C94B),
    (0x1C94C, 0x1C98A),
    (0x1C991, 0x1C995),
    (0x1C998, 0x1C9B5),
    (0x1C9B8, 0x1C9EB),
    (0x1C9EC, 0x1CA06),
    (0x1CA09, 0x1CA4D),
    (0x1CA4E, 0x1CAC4),
    (0x1CAC7, 0x1CBD0),
    (0x1CBD9, 0x1CC2E),
    (0x1CC2F, 0x1CC8B),
    (0x1CC8C, 0x1CCB8),
    (0x1CCB9, 0x1CCCD),
    (0x1CCD0, 0x1CCFC),
    (0x1CCFD, 0x1CDCC),
    (0x1CDCD, 0x1CE91),
    (0x1CE92, 0x1CF22),
    (0x1CF23, 0x1CFA7),
    (0x1CFAB, 0x1CFC7),
    (0x1CFCA, 0x1D027),
    (0x1D028, 0x1D19D),
    (0x1D1A0, 0x1D230),
    (0x1D236, 0x1D23A),
    (0x1D23D, 0x1D26D),
    (0x1D270, 0x1D2BF),
    (0x1D2C8, 0x1D2FB),
    (0x1D2FC, 0x1D381),
    (0x1D382, 0x1D3C2),
    (0x1D3C9, 0x1D3CD),
    (0x1D3D0, 0x1D3F0),
    (0x1D3F4, 0x1D410),
    (0x1D411, 0x1D47B),
    (0x1D47C, 0x1D527),
    (0x1D52A, 0x1D55D),
    (0x1D563, 0x1D567),
    (0x1D56A, 0x1D58A),
    (0x1D58B, 0x1D61B),
    (0x1D61E, 0x1D696),
    (0x1D697, 0x1D6D4),
    (0x1D6D6, 0x1D778),
    (0x1D781, 0x1D7C1),
    (0x1D7C3, 0x1D7F7),
    (0x1D7F8, 0x1D83B),
    (0x1D842, 0x1D846),
    (0x1D849, 0x1D87D),
    (0x1D87E, 0x1D89A),
    (0x1D89B, 0x1D915),
    (0x1D918, 0x1D92F),
    (0x1D935, 0x1D938),
    (0x1D93B, 0x1D96A),
    (0x1D96B, 0x1D9A9),
    (0x1D9B0, 0x1D9B3),
    (0x1D9B6, 0x1D9E9),
    (0x1D9EA, 0x1DA2E),
    (0x1DA30, 0x1DB1B),
    (0x1DB1C, 0x1DB90),
    (0x1DB92, 0x1DBAD),
    (0x1DBB8, 0x1DBDF),
    (0x1DBE3, 0x1DBFF),
    (0x1DC00, 0x1DCC6),
    (0x1DCC9, 0x1DCFB),
    (0x1DD01, 0x1DD05),
    (0x1DD08, 0x1DD25),
    (0x1DD26, 0x1DD54),
    (0x1DD57, 0x1DDB4),
    (0x1DDB7, 0x1DE18),
    (0x1DE21, 0x1DE51),
    (0x1DE52, 0x1DE91),
    (0x1DE98, 0x1DE9C),
    (0x1DE9F, 0x1DF78),
    (0x1DF7B, 0x1DFAF),
    (0x1DFB5, 0x1DFB9),
    (0x1DFBC, 0x1DFDD),
    (0x1DFDE, 0x1E015),
    (0x1E01C, 0x1E020),
    (0x1E025, 0x1E13E),
    (0x1E143, 0x1E172),
    (0x1E17B, 0x1E1E1),
    (0x1E1E4, 0x1E20E),
    (0x1E20F, 0x1E230),
    (0x1E231, 0x1E256),
    (0x1E257, 0x1E26E),
    (0x1E26F, 0x1E294),
    (0x1E295, 0x1E2AA),
    (0x1E2AB, 0x1E2D4),
    (0x1E2E7, 0x1E313),
    (0x1E620, 0x1E647),
    (0x1E66B, 0x1E6AC),
)
# Exclusive physical-ROM ranges of documented lookup and character stat tables, shaded in green.
KNOWN_LOOKUP_RANGES = (
    (0x15449, 0x15459),
    (0x15459, 0x15489),
    (0x154AD, 0x154CD),
    (0x154DF, 0x154FF),
    (0x15511, 0x15541),
    (0x15709, 0x15719),
    (0x15719, 0x15739),
    (0x15799, 0x157C9),
    (0x157C9, 0x157D9),
    (0x157D9, 0x157F9),
    (0x15898, 0x158B8),
    (0x159B2, 0x159D2),
    (0x159E4, 0x15A04),
    (0x15A16, 0x15A36),
    (0x15B97, 0x15BA7),
    (0x15BA7, 0x15BC7),
    (0x15BC7, 0x15BF7),
    (0x15C34, 0x15C54),
    (0x15C66, 0x15C96),
    (0x15C96, 0x15CA6),
    (0x15CA6, 0x15CD6),
    (0x15CE8, 0x15D08),
    (0x17065, 0x17165),
    (0x17165, 0x17185),
    (0x17725, 0x17937),
)
# Exclusive physical-ROM ranges of the title tilemap, its record and pointer tables, and the routines that write and copy them, shaded in purple.
KNOWN_STRUCTURE_RANGES = (
    (0x077D, 0x07BC),
    (0x0A78, 0x0AA1),
    (0x0AD0, 0x0AD9),
    (0x0CCB, 0x0CD4),
    (0x13C30, 0x13D9D),
    (0x1800A, 0x1800C),
    (0x18110, 0x1811E),
)
HIGHLIGHT_PALETTES = {
    "graphics": BLUESCALE_PALETTE,
    "text": YELLOWSCALE_PALETTE,
    "lookup": GREENSCALE_PALETTE,
    "structure": PURPLESCALE_PALETTE,
}


def known_kind(address: int) -> str | None:
    if any(start <= address < end for start, end in KNOWN_GRAPHICS_RANGES):
        return "graphics"
    if any(start <= address < end for start, end in KNOWN_TEXT_RANGES):
        return "text"
    if any(start <= address < end for start, end in KNOWN_LOOKUP_RANGES):
        return "lookup"
    if any(start <= address < end for start, end in KNOWN_STRUCTURE_RANGES):
        return "structure"
    return None


def pixel_highlight_palette(
    low_kind: str | None, high_kind: str | None, low_set: bool, high_set: bool
) -> tuple | None:
    """Return the shade palette for a pixel, or None to keep its palette color.

    A pixel belongs to whichever plane's byte sets its bit, so a row that is only
    partly known highlights only the pixels its known byte contributes.
    """
    if low_kind == high_kind:
        owner = low_kind
    elif low_kind and low_set and not high_set:
        owner = low_kind
    elif high_kind and high_set and not low_set:
        owner = high_kind
    else:
        owner = None
    return HIGHLIGHT_PALETTES[owner] if owner else None


def pixel_compare_color(
    color: int,
    palette: tuple[tuple[int, int, int], ...],
    same_low: bool,
    same_high: bool,
    low_set: bool,
    high_set: bool,
) -> tuple[int, int, int]:
    """Shade unchanged byte contributions blue and changed ones red."""
    if same_low and same_high:
        return BLUESCALE_PALETTE[color]
    if same_low and low_set and not high_set:
        return BLUESCALE_PALETTE[color]
    if same_high and high_set and not low_set:
        return BLUESCALE_PALETTE[color]
    return REDSCALE_PALETTE[color]


DEFAULT_ROM = Path(__file__).resolve().parent.parent / "input" / "Rolan's Curse II (USA).gb"
WORKING_ROM = Path(__file__).resolve().parent.parent / "working" / "Rolan's Curse II (USA) (hack in progress).gb"
DEFAULT_PALETTE = (
    (0, 0, 0),
    (85, 85, 85),
    (170, 170, 170),
    (255, 255, 255),
)
PORTRAIT_PALETTE = (
    (170, 170, 170),
    (0, 0, 0),
    (85, 85, 85),
    (255, 255, 255),
)
# Used by the hack dump-art and inject-art commands for NPC and character sprites; index 0 is transparent.
HACK_ART_PALETTE = (
    (170, 170, 170),
    (0, 0, 0),
    (85, 85, 85),
    (255, 255, 255),
)


def parse_tile_grid(value: str) -> tuple[int, int]:
    """Parse tile grid dimensions written as WIDTHxHEIGHT."""
    parts = value.lower().split("x")
    if len(parts) != 2 or not all(part.isdecimal() for part in parts):
        raise argparse.ArgumentTypeError("tile grid must be written as WIDTHxHEIGHT, e.g. 2x2")
    width, height = (int(part) for part in parts)
    if width < 1 or height < 1:
        raise argparse.ArgumentTypeError("tile grid dimensions must be at least 1")
    return width, height


def add_address_axes(
    image: Image.Image,
    image_count: int,
    columns: int,
    start_address: int,
    scale: int,
    image_width: int = SPRITE_WIDTH,
    image_height: int = SPRITE_WIDTH,
    bytes_per_image: int = 4 * TILE_BYTES,
) -> Image.Image:
    """Add ROM address labels for the first image in each column and row."""
    rows = math.ceil(image_count / columns)
    column_addresses = [
        f"0x{start_address + column * bytes_per_image:04X}"
        for column in range(min(columns, image_count))
    ]
    row_addresses = [
        f"0x{start_address + row * columns * bytes_per_image:04X}"
        for row in range(rows)
    ]
    font = ImageFont.load_default()
    column_bounds = [font.getbbox(address) for address in column_addresses]
    row_bounds = [font.getbbox(address) for address in row_addresses]
    column_label_width = max(right - left for left, _, right, _ in column_bounds)
    row_label_width = max(right - left for left, _, right, _ in row_bounds)
    label_height = max(bottom - top for _, top, _, bottom in column_bounds + row_bounds)

    cell_width = image_width * scale
    cell_height = image_height * scale
    source_pitch_x = (image_width + SPRITE_GUTTER) * scale
    source_pitch_y = (image_height + SPRITE_GUTTER) * scale
    column_pitch = max(source_pitch_x, column_label_width + 8)
    row_pitch = max(source_pitch_y, label_height + 8)
    top_margin = label_height + 8
    left_margin = row_label_width + 8
    graphic_width = columns * cell_width + (columns - 1) * (column_pitch - cell_width)
    graphic_height = rows * cell_height + (rows - 1) * (row_pitch - cell_height)
    output = Image.new(
        "RGB",
        (left_margin + graphic_width, top_margin + graphic_height),
        (255, 255, 255),
    )

    for image_index in range(rows * columns):
        target_x = left_margin + image_index % columns * column_pitch
        target_y = top_margin + image_index // columns * row_pitch
        if image_index < image_count:
            source_x = image_index % columns * source_pitch_x
            source_y = image_index // columns * source_pitch_y
            sprite = image.crop((source_x, source_y, source_x + cell_width, source_y + cell_height))
        else:
            sprite = Image.new("RGB", (cell_width, cell_height), EMPTY_COLOR)
        output.paste(sprite, (target_x, target_y))

    draw = ImageDraw.Draw(output)
    for column, address in enumerate(column_addresses):
        left, top, right, bottom = font.getbbox(address)
        center_x = left_margin + column * column_pitch + cell_width / 2
        draw.text(
            (center_x - (right - left) / 2 - left, (top_margin - (bottom - top)) / 2 - top),
            address,
            fill=(0, 0, 0),
            font=font,
        )
    for row, address in enumerate(row_addresses):
        left, top, right, bottom = font.getbbox(address)
        center_y = top_margin + row * row_pitch + cell_height / 2
        draw.text(
            ((left_margin - (right - left)) / 2 - left, center_y - (bottom - top) / 2 - top),
            address,
            fill=(0, 0, 0),
            font=font,
        )

    for column in range(1, columns):
        x = left_margin + column * column_pitch - SPRITE_GUTTER * scale
        draw.line((x, top_margin, x, top_margin + graphic_height - 1), fill=GUTTER_COLOR)
    for row in range(1, rows):
        y = top_margin + row * row_pitch - SPRITE_GUTTER * scale
        draw.line((left_margin, y, left_margin + graphic_width - 1, y), fill=GUTTER_COLOR)
    return output


def render_tile_grid(
    data: bytes,
    tile_columns: int,
    tile_rows: int,
    columns: int = 4,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = DEFAULT_PALETTE,
    start_address: int | None = None,
    tile_positions: tuple[tuple[int, int], ...] | None = None,
    highlight_known: bool = False,
    comparison: bytes | None = None,
) -> Image.Image:
    """Render tiles grouped into fixed-size images, in row-major order by default."""
    if tile_columns < 1 or tile_rows < 1:
        raise ValueError("tile grid dimensions must be at least 1")
    if columns < 1:
        raise ValueError("columns must be at least 1")
    if scale < 1:
        raise ValueError("scale must be at least 1")
    if len(palette) != 4:
        raise ValueError("palette must contain exactly four colors")
    if highlight_known and start_address is None:
        raise ValueError("start address is required to highlight known graphics")
    if comparison is not None and len(comparison) != len(data):
        raise ValueError("comparison data must have the same length as the rendered data")

    tiles = decode_tiles(data)
    tiles_per_image = tile_columns * tile_rows
    if tile_positions is None:
        tile_positions = tuple(
            (index % tile_columns, index // tile_columns)
            for index in range(tiles_per_image)
        )
    if len(tile_positions) != tiles_per_image or any(
        x < 0 or x >= tile_columns or y < 0 or y >= tile_rows
        for x, y in tile_positions
    ):
        raise ValueError("tile positions must match the selected grid dimensions")

    image_width = tile_columns * TILE_WIDTH
    image_height = tile_rows * TILE_WIDTH
    image_count = math.ceil(len(tiles) / tiles_per_image)
    rows = math.ceil(image_count / columns)
    width = columns * image_width + (columns - 1) * SPRITE_GUTTER
    height = rows * image_height + (rows - 1) * SPRITE_GUTTER
    image = Image.new("RGB", (width, height), EMPTY_COLOR)
    draw = ImageDraw.Draw(image)
    for column in range(1, columns):
        x = column * (image_width + SPRITE_GUTTER) - SPRITE_GUTTER
        draw.line((x, 0, x, height - 1), fill=GUTTER_COLOR)
    for row in range(1, rows):
        y = row * (image_height + SPRITE_GUTTER) - SPRITE_GUTTER
        draw.line((0, y, width - 1, y), fill=GUTTER_COLOR)

    pixels = image.load()
    for tile_index, tile in enumerate(tiles):
        image_index, tile_index_in_image = divmod(tile_index, tiles_per_image)
        image_column, image_row = image_index % columns, image_index // columns
        tile_column, tile_row = tile_positions[tile_index_in_image]
        tile_x = image_column * (image_width + SPRITE_GUTTER) + tile_column * TILE_WIDTH
        tile_y = image_row * (image_height + SPRITE_GUTTER) + tile_row * TILE_WIDTH
        tile_start = start_address + tile_index * TILE_BYTES if start_address is not None else 0
        tile_data = data[tile_index * TILE_BYTES:(tile_index + 1) * TILE_BYTES].ljust(
            TILE_BYTES, b"\x00"
        )
        for y, row in enumerate(tile):
            if tile_index * TILE_BYTES + y * 2 >= len(data):
                break
            low_byte, high_byte = tile_data[y * 2:y * 2 + 2]
            row_offset = tile_index * TILE_BYTES + y * 2
            same_low = comparison is not None and data[row_offset] == comparison[row_offset]
            same_high = (
                comparison is not None
                and row_offset + 1 < len(data)
                and data[row_offset + 1] == comparison[row_offset + 1]
            )
            row_address = tile_start + y * 2
            low_kind = known_kind(row_address) if highlight_known else None
            high_kind = known_kind(row_address + 1) if highlight_known else None
            for x, color in enumerate(row):
                bit_mask = 1 << (7 - x)
                shades = pixel_highlight_palette(
                    low_kind,
                    high_kind,
                    bool(low_byte & bit_mask),
                    bool(high_byte & bit_mask),
                )
                if comparison is not None:
                    pixel_color = pixel_compare_color(
                        color,
                        palette,
                        same_low,
                        same_high,
                        bool(low_byte & bit_mask),
                        bool(high_byte & bit_mask),
                    )
                else:
                    pixel_color = shades[color] if shades else palette[color]
                pixels[tile_x + x, tile_y + y] = pixel_color

    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    if start_address is not None:
        image = add_address_axes(
            image,
            image_count,
            columns,
            start_address,
            scale,
            image_width=image_width,
            image_height=image_height,
            bytes_per_image=tiles_per_image * TILE_BYTES,
        )
    return image


def render_sprites(
    data: bytes,
    columns: int = 16,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = DEFAULT_PALETTE,
    start_address: int | None = None,
    highlight_known: bool = False,
    comparison: bytes | None = None,
) -> Image.Image:
    """Render groups of four column-first tiles as 16x16 sprites."""
    return render_tile_grid(
        data,
        2,
        2,
        columns,
        scale,
        palette,
        start_address,
        tile_positions=SPRITE_TILE_POSITIONS,
        highlight_known=highlight_known,
        comparison=comparison,
    )


def render_portraits(
    data: bytes,
    columns: int = 4,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = PORTRAIT_PALETTE,
    start_address: int | None = None,
    highlight_known: bool = False,
    comparison: bytes | None = None,
) -> Image.Image:
    """Render complete 32x32 portraits from row-major 4x4 tile blocks."""
    if len(data) % PORTRAIT_BYTES:
        raise ValueError(f"portrait data length must be a multiple of 0x{PORTRAIT_BYTES:X} bytes")
    return render_tile_grid(
        data,
        PORTRAIT_TILE_COLUMNS,
        PORTRAIT_TILE_COLUMNS,
        columns,
        scale,
        palette,
        start_address,
        highlight_known=highlight_known,
        comparison=comparison,
    )


def render_stacked_glyphs(
    data: bytes,
    columns: int = 16,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = DEFAULT_PALETTE,
    start_address: int | None = None,
    highlight_known: bool = False,
    comparison: bytes | None = None,
) -> Image.Image:
    """Render each 16-byte tile as two stacked 8x8 1bpp glyphs (bit 0 is ink)."""
    if columns < 1:
        raise ValueError("columns must be at least 1")
    if scale < 1:
        raise ValueError("scale must be at least 1")
    if len(palette) != 4:
        raise ValueError("palette must contain exactly four colors")
    if highlight_known and start_address is None:
        raise ValueError("start address is required to highlight known graphics")
    if comparison is not None and len(comparison) != len(data):
        raise ValueError("comparison data must have the same length as the rendered data")

    tile_count = math.ceil(len(data) / TILE_BYTES)
    cell_height = TILE_BYTES
    rows = math.ceil(tile_count / columns)
    width = columns * TILE_WIDTH + (columns - 1) * SPRITE_GUTTER
    height = rows * cell_height + (rows - 1) * SPRITE_GUTTER
    image = Image.new("RGB", (width, height), EMPTY_COLOR)
    draw = ImageDraw.Draw(image)
    for column in range(1, columns):
        x = column * (TILE_WIDTH + SPRITE_GUTTER) - SPRITE_GUTTER
        draw.line((x, 0, x, height - 1), fill=GUTTER_COLOR)
    for row in range(1, rows):
        y = row * (cell_height + SPRITE_GUTTER) - SPRITE_GUTTER
        draw.line((0, y, width - 1, y), fill=GUTTER_COLOR)

    pixels = image.load()
    for tile_index in range(tile_count):
        tile_x = (tile_index % columns) * (TILE_WIDTH + SPRITE_GUTTER)
        tile_y = (tile_index // columns) * (cell_height + SPRITE_GUTTER)
        tile_data = data[tile_index * TILE_BYTES:(tile_index + 1) * TILE_BYTES]
        for y, row_byte in enumerate(tile_data):
            row_offset = tile_index * TILE_BYTES + y
            row_address = (
                start_address + row_offset if start_address is not None else None
            )
            row_kind = known_kind(row_address) if highlight_known else None
            same = comparison is not None and row_byte == comparison[row_offset]
            for x in range(TILE_WIDTH):
                ink = row_byte & (1 << (7 - x))
                if same:
                    shades = BLUESCALE_PALETTE
                    color = shades[3] if ink else shades[0]
                elif comparison is not None:
                    shades = REDSCALE_PALETTE
                    color = shades[3] if ink else shades[0]
                elif row_kind:
                    shades = HIGHLIGHT_PALETTES[row_kind]
                    color = shades[3] if ink else shades[0]
                elif ink:
                    color = palette[3]
                else:
                    color = palette[0]
                pixels[tile_x + x, tile_y + y] = color

    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    if start_address is not None:
        image = add_address_axes(
            image,
            tile_count,
            columns,
            start_address,
            scale,
            image_width=TILE_WIDTH,
            image_height=cell_height,
            bytes_per_image=TILE_BYTES,
        )
    return image


def render_banked_sprites(
    data: bytes,
    start_address: int,
    columns: int = 16,
    scale: int = 4,
    highlight_known: bool = False,
    comparison: bytes | None = None,
) -> Image.Image:
    """Render sprites with one labeled block per 16 KiB ROM bank, separated by rules.

    Each bank is rendered on its own, so it starts a new row and gets its own address labels.
    """
    if comparison is not None and len(comparison) != len(data):
        raise ValueError("comparison data must have the same length as the rendered data")
    blocks = []
    address = start_address
    end_address = start_address + len(data)
    while address < end_address:
        bank = address // BANK_SIZE
        block_end = min(end_address, (bank + 1) * BANK_SIZE)
        block = render_sprites(
            data[address - start_address:block_end - start_address],
            columns,
            scale,
            start_address=address,
            highlight_known=highlight_known,
            comparison=(
                comparison[address - start_address:block_end - start_address]
                if comparison is not None else None
            ),
        )
        blocks.append((f"Bank {bank}", block))
        address = block_end

    font = ImageFont.load_default()
    _, label_top, _, label_bottom = font.getbbox("Bank 0")
    header_height = label_bottom - label_top + 2 * BANK_LABEL_PADDING
    width = max(block.width for _, block in blocks)
    height = sum(header_height + block.height for _, block in blocks)
    height += (len(blocks) - 1) * BANK_DIVIDER_HEIGHT
    output = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(output)

    y = 0
    for index, (label, block) in enumerate(blocks):
        if index:
            rule_top = y + BANK_DIVIDER_PADDING
            draw.rectangle(
                (0, rule_top, width - 1, rule_top + BANK_DIVIDER_THICKNESS - 1),
                fill=BANK_DIVIDER_COLOR,
            )
            y += BANK_DIVIDER_HEIGHT
        draw.text(
            (BANK_LABEL_PADDING, y + BANK_LABEL_PADDING - label_top),
            label,
            fill=(0, 0, 0),
            font=font,
        )
        y += header_height
        output.paste(block, (0, y))
        y += block.height
    return output


def render_range(
    data: bytes,
    start_address: int,
    *,
    mode: str,
    tile_grid: tuple[int, int] | None,
    stacked_glyphs: bool,
    columns: int | None,
    scale: int,
    highlight_known: bool,
    comparison: bytes | None = None,
) -> Image.Image:
    if stacked_glyphs:
        if tile_grid is not None or mode != "sprites":
            raise ValueError("--stacked-glyphs cannot be combined with --tile-grid or --mode")
        return render_stacked_glyphs(
            data,
            columns if columns is not None else 16,
            scale,
            start_address=start_address,
            highlight_known=highlight_known,
            comparison=comparison,
        )
    if tile_grid is not None:
        tile_columns, tile_rows = tile_grid
        palette = PORTRAIT_PALETTE if mode == "portraits" else DEFAULT_PALETTE
        return render_tile_grid(
            data,
            tile_columns,
            tile_rows,
            columns if columns is not None else 4,
            scale,
            palette,
            start_address,
            highlight_known=highlight_known,
            comparison=comparison,
        )
    if mode == "portraits":
        return render_portraits(
            data,
            columns if columns is not None else 4,
            scale,
            start_address=start_address,
            highlight_known=highlight_known,
            comparison=comparison,
        )
    return render_banked_sprites(
        data,
        start_address,
        columns if columns is not None else 16,
        scale,
        highlight_known=highlight_known,
        comparison=comparison,
    )


def combine_comparison_images(input_image: Image.Image, working_image: Image.Image) -> Image.Image:
    font = ImageFont.load_default()
    _, label_top, _, label_bottom = font.getbbox("Input ROM")
    label_height = label_bottom - label_top
    header_height = label_height + 12
    gap = 24
    width = input_image.width + gap + working_image.width
    height = header_height + max(input_image.height, working_image.height)
    combined = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(combined)
    for label, x, image in (
        ("Input ROM", 0, input_image),
        ("Working ROM", input_image.width + gap, working_image),
    ):
        draw.text(
            (x + 4, (header_height - label_height) // 2 - label_top),
            label,
            fill=(0, 0, 0),
            font=font,
        )
        combined.paste(image, (x, header_height))
    divider_x = input_image.width + gap // 2
    draw.line((divider_x, 0, divider_x, height - 1), fill=(192, 192, 192))
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=parse_offset, help="start ROM offset (inclusive)")
    parser.add_argument("end", type=parse_offset, help="end ROM offset (exclusive)")
    parser.add_argument("output", type=Path, help="output .png, .jpg, or .jpeg path")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_ROM,
        help="ROM or full xxd/Format-Hex dump (default: %(default)s)",
    )
    parser.add_argument(
        "--mode",
        choices=("sprites", "portraits"),
        default="sprites",
        help="preset tile layout to render (default: sprites)",
    )
    parser.add_argument(
        "--tile-grid",
        type=parse_tile_grid,
        metavar="WIDTHxHEIGHT",
        help="combine this many tiles across and down into each image",
    )
    highlight_options = parser.add_mutually_exclusive_group()
    highlight_options.add_argument(
        "--highlight-known",
        action="store_true",
        help="shade pixels in documented graphics in blue, text in yellow, lookup or stat tables in green, and tilemaps, tables, and routines in purple",
    )
    highlight_options.add_argument(
        "--compare",
        action="store_true",
        help=f"compare the input ROM with {WORKING_ROM}",
    )
    parser.add_argument(
        "--stacked-glyphs",
        action="store_true",
        help="render each 16-byte tile as two stacked 8x8 1bpp glyphs (bit 0 is ink)",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=None,
        help="images per row (default: 16 sprites, 4 portraits or grids)",
    )
    parser.add_argument("--scale", type=int, default=4, help="integer nearest-neighbor scale (default: 4)")
    args = parser.parse_args()

    try:
        if args.output.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            raise ValueError("output extension must be .png, .jpg, or .jpeg")
        if args.start < 0 or args.end <= args.start:
            raise ValueError("range must have a nonnegative start and an end greater than the start")

        rom = read_rom(args.input)
        if args.end > len(rom):
            raise ValueError(f"range end 0x{args.end:X} exceeds ROM size 0x{len(rom):X}")
        data = rom[args.start:args.end]
        if args.compare:
            if not WORKING_ROM.is_file():
                raise ValueError(f"--compare requires the working ROM at {WORKING_ROM}")
            working_rom = read_rom(WORKING_ROM)
            if args.end > len(working_rom):
                raise ValueError(
                    f"range end 0x{args.end:X} exceeds working ROM size 0x{len(working_rom):X}"
                )
            working_data = working_rom[args.start:args.end]
            input_image = render_range(
                data,
                args.start,
                mode=args.mode,
                tile_grid=args.tile_grid,
                stacked_glyphs=args.stacked_glyphs,
                columns=args.columns,
                scale=args.scale,
                highlight_known=args.highlight_known,
                comparison=working_data,
            )
            working_image = render_range(
                working_data,
                args.start,
                mode=args.mode,
                tile_grid=args.tile_grid,
                stacked_glyphs=args.stacked_glyphs,
                columns=args.columns,
                scale=args.scale,
                highlight_known=args.highlight_known,
                comparison=data,
            )
            image = combine_comparison_images(input_image, working_image)
        else:
            image = render_range(
                data,
                args.start,
                mode=args.mode,
                tile_grid=args.tile_grid,
                stacked_glyphs=args.stacked_glyphs,
                columns=args.columns,
                scale=args.scale,
                highlight_known=args.highlight_known,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
