#!/usr/bin/env python3
"""Render a ROM byte range as assembled 16x16 Game Boy sprites."""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from extract_json import read_rom

TILE_BYTES = 16
TILE_WIDTH = 8
SPRITE_TILE_POSITIONS = ((0, 0), (0, 1), (1, 0), (1, 1))
SPRITE_WIDTH = TILE_WIDTH * 2
SPRITE_GUTTER = 1
GUTTER_COLOR = (192, 192, 192)
DEFAULT_ROM = Path(__file__).resolve().parent.parent / "input" / "Rolan's Curse II (USA).gb"
DEFAULT_PALETTE = (
    (0, 0, 0),
    (85, 85, 85),
    (170, 170, 170),
    (255, 255, 255),
)


def parse_offset(value: str) -> int:
    """Parse an offset written in decimal or with a 0x prefix."""
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid offset: {value}") from error


def decode_tiles(data: bytes) -> list[list[int]]:
    """Decode Game Boy 2bpp tiles, allowing a final tile to end at any byte."""
    if not data:
        raise ValueError("range must contain at least one byte")

    pixels = []
    for tile_start in range(0, len(data), TILE_BYTES):
        tile_data = data[tile_start:tile_start + TILE_BYTES].ljust(TILE_BYTES, b"\x00")
        tile = []
        for row in range(TILE_WIDTH):
            low, high = tile_data[row * 2:row * 2 + 2]
            tile.append([
                ((low >> bit) & 1) | (((high >> bit) & 1) << 1)
                for bit in range(7, -1, -1)
            ])
        pixels.append(tile)
    return pixels


def add_address_axes(
    image: Image.Image,
    sprite_count: int,
    columns: int,
    start_address: int,
    scale: int,
) -> Image.Image:
    """Add ROM address labels for the first cel in each column and row."""
    rows = math.ceil(sprite_count / columns)
    column_addresses = [
        f"0x{start_address + column * 4 * TILE_BYTES:04X}"
        for column in range(min(columns, sprite_count))
    ]
    row_addresses = [
        f"0x{start_address + row * columns * 4 * TILE_BYTES:04X}"
        for row in range(rows)
    ]
    font = ImageFont.load_default()
    column_bounds = [font.getbbox(address) for address in column_addresses]
    row_bounds = [font.getbbox(address) for address in row_addresses]
    column_label_width = max(right - left for left, _, right, _ in column_bounds)
    row_label_width = max(right - left for left, _, right, _ in row_bounds)
    label_height = max(bottom - top for _, top, _, bottom in column_bounds + row_bounds)

    cell_size = SPRITE_WIDTH * scale
    source_pitch = (SPRITE_WIDTH + SPRITE_GUTTER) * scale
    column_pitch = max(source_pitch, column_label_width + 8)
    row_pitch = max(source_pitch, label_height + 8)
    top_margin = label_height + 8
    left_margin = row_label_width + 8
    graphic_width = columns * cell_size + (columns - 1) * (column_pitch - cell_size)
    graphic_height = rows * cell_size + (rows - 1) * (row_pitch - cell_size)
    output = Image.new(
        "RGB",
        (left_margin + graphic_width, top_margin + graphic_height),
        (255, 255, 255),
    )

    for sprite_index in range(sprite_count):
        source_x = sprite_index % columns * source_pitch
        source_y = sprite_index // columns * source_pitch
        sprite = image.crop((source_x, source_y, source_x + cell_size, source_y + cell_size))
        target_x = left_margin + sprite_index % columns * column_pitch
        target_y = top_margin + sprite_index // columns * row_pitch
        output.paste(sprite, (target_x, target_y))

    draw = ImageDraw.Draw(output)
    for column, address in enumerate(column_addresses):
        left, top, right, bottom = font.getbbox(address)
        center_x = left_margin + column * column_pitch + cell_size / 2
        draw.text(
            (center_x - (right - left) / 2 - left, (top_margin - (bottom - top)) / 2 - top),
            address,
            fill=(0, 0, 0),
            font=font,
        )
    for row, address in enumerate(row_addresses):
        left, top, right, bottom = font.getbbox(address)
        center_y = top_margin + row * row_pitch + cell_size / 2
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


def render_sprites(
    data: bytes,
    columns: int = 16,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = DEFAULT_PALETTE,
    start_address: int | None = None,
) -> Image.Image:
    """Render groups of four column-first tiles as 16x16 sprites."""
    if columns < 1:
        raise ValueError("columns must be at least 1")
    if scale < 1:
        raise ValueError("scale must be at least 1")
    if len(palette) != 4:
        raise ValueError("palette must contain exactly four colors")

    tiles = decode_tiles(data)
    sprite_count = math.ceil(len(tiles) / len(SPRITE_TILE_POSITIONS))
    rows = math.ceil(sprite_count / columns)
    width = columns * SPRITE_WIDTH + (columns - 1) * SPRITE_GUTTER
    height = rows * SPRITE_WIDTH + (rows - 1) * SPRITE_GUTTER
    image = Image.new("RGB", (width, height), palette[0])
    draw = ImageDraw.Draw(image)
    for column in range(1, columns):
        x = column * (SPRITE_WIDTH + SPRITE_GUTTER) - SPRITE_GUTTER
        draw.line((x, 0, x, height - 1), fill=GUTTER_COLOR)
    for row in range(1, rows):
        y = row * (SPRITE_WIDTH + SPRITE_GUTTER) - SPRITE_GUTTER
        draw.line((0, y, width - 1, y), fill=GUTTER_COLOR)
    pixels = image.load()
    for tile_index, tile in enumerate(tiles):
        sprite_index, tile_position = divmod(tile_index, len(SPRITE_TILE_POSITIONS))
        sprite_column, sprite_row = sprite_index % columns, sprite_index // columns
        tile_column, tile_row = SPRITE_TILE_POSITIONS[tile_position]
        tile_x = sprite_column * (SPRITE_WIDTH + SPRITE_GUTTER) + tile_column * TILE_WIDTH
        tile_y = sprite_row * (SPRITE_WIDTH + SPRITE_GUTTER) + tile_row * TILE_WIDTH
        for y, row in enumerate(tile):
            for x, color in enumerate(row):
                pixels[tile_x + x, tile_y + y] = palette[color]

    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    if start_address is not None:
        image = add_address_axes(image, sprite_count, columns, start_address, scale)
    return image


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
    parser.add_argument("--columns", type=int, default=16, help="sprites per row (default: 16)")
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
        image = render_sprites(data, args.columns, args.scale, start_address=args.start)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
