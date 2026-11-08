#!/usr/bin/env python3
"""Render ROM tiles as sprites, portraits, or arbitrary tile grids."""

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
PORTRAIT_TILE_COLUMNS = 4
PORTRAIT_TILE_COUNT = PORTRAIT_TILE_COLUMNS ** 2
PORTRAIT_BYTES = PORTRAIT_TILE_COUNT * TILE_BYTES
PORTRAIT_WIDTH = PORTRAIT_TILE_COLUMNS * TILE_WIDTH
DEFAULT_ROM = Path(__file__).resolve().parent.parent / "input" / "Rolan's Curse II (USA).gb"
DEFAULT_PALETTE = (
    (0, 0, 0),
    (85, 85, 85),
    (170, 170, 170),
    (255, 255, 255),
)
PORTRAIT_PALETTE = (
    (168, 168, 168),
    (0, 0, 0),
    (96, 96, 96),
    (248, 248, 248),
)


def parse_offset(value: str) -> int:
    """Parse an offset written in decimal or with a 0x prefix."""
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid offset: {value}") from error


def parse_tile_grid(value: str) -> tuple[int, int]:
    """Parse tile grid dimensions written as WIDTHxHEIGHT."""
    parts = value.lower().split("x")
    if len(parts) != 2 or not all(part.isdecimal() for part in parts):
        raise argparse.ArgumentTypeError("tile grid must be written as WIDTHxHEIGHT, e.g. 2x2")
    width, height = (int(part) for part in parts)
    if width < 1 or height < 1:
        raise argparse.ArgumentTypeError("tile grid dimensions must be at least 1")
    return width, height


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

    for image_index in range(image_count):
        source_x = image_index % columns * source_pitch_x
        source_y = image_index // columns * source_pitch_y
        sprite = image.crop((source_x, source_y, source_x + cell_width, source_y + cell_height))
        target_x = left_margin + image_index % columns * column_pitch
        target_y = top_margin + image_index // columns * row_pitch
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
    image = Image.new("RGB", (width, height), palette[0])
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
        for y, row in enumerate(tile):
            for x, color in enumerate(row):
                pixels[tile_x + x, tile_y + y] = palette[color]

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
    )


def render_portraits(
    data: bytes,
    columns: int = 4,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = PORTRAIT_PALETTE,
    start_address: int | None = None,
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
    )


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
        if args.tile_grid is not None:
            tile_columns, tile_rows = args.tile_grid
            columns = args.columns if args.columns is not None else 4
            palette = PORTRAIT_PALETTE if args.mode == "portraits" else DEFAULT_PALETTE
            image = render_tile_grid(
                data,
                tile_columns,
                tile_rows,
                columns,
                args.scale,
                palette,
                args.start,
            )
        elif args.mode == "portraits":
            columns = args.columns if args.columns is not None else 4
            image = render_portraits(data, columns, args.scale, start_address=args.start)
        else:
            columns = args.columns if args.columns is not None else 16
            image = render_sprites(data, columns, args.scale, start_address=args.start)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
