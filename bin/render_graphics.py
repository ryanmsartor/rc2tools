#!/usr/bin/env python3
"""Render a ROM byte range as assembled 16x16 Game Boy sprites."""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

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
    """Decode consecutive 16-byte Game Boy 2bpp tiles into color indices."""
    if not data or len(data) % TILE_BYTES:
        raise ValueError("range must contain a nonzero multiple of 16 bytes")

    pixels = []
    for tile_start in range(0, len(data), TILE_BYTES):
        tile = []
        for row in range(TILE_WIDTH):
            low, high = data[tile_start + row * 2:tile_start + row * 2 + 2]
            tile.append([
                ((low >> bit) & 1) | (((high >> bit) & 1) << 1)
                for bit in range(7, -1, -1)
            ])
        pixels.append(tile)
    return pixels


def render_sprites(
    data: bytes,
    columns: int = 16,
    scale: int = 4,
    palette: tuple[tuple[int, int, int], ...] = DEFAULT_PALETTE,
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
        image = render_sprites(data, args.columns, args.scale)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
