"""Named ROM art layouts for `rc2t hack dump-art` and `rc2t hack read-art`.

A layout places each tile of a ROM chunk in its on-screen cell. Tile IDs are
BG-map IDs under signed tile addressing (LCDC=0xE3).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image


TILE_SIZE = 8
TILE_BYTES = 16
EMPTY_CELL = "--"

# Cells of the title screen's BG map as tile IDs, for the rows above the
# START/CONTINUE line (row 13). Rows below it hold the menu cursor (sprite 0,
# tile 0xD4), the menu text, and the copyright tile 0xD3, so they are left out.
# `--` marks a cell that is not title art.
TITLE_GRID = """
30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30
30 C7 C8 C9 CA 30 30 30 30 30 30 30 31 32 30 30 33 34 35 36
30 CB CC CD CE 37 38 39 3A 3B 3C 3D 3E 3F 40 41 42 43 44 45
30 CF D0 D1 D2 46 47 48 49 4A 4B 4C 4D 4E 4F 50 51 52 53 54
30 55 56 57 58 59 5A 5A 5A 5A 5A 5A 5A 5A 5B 5C 5D 5E 5F 30
60 61 62 63 64 65 66 67 5A 5A 68 69 6A 6B 6C 6D 6E 6F 70 30
71 72 73 74 75 76 77 78 79 7A 7B 7C 7D 7E 7F 5A 80 81 82 30
83 84 85 86 87 88 89 8A 8B 8C 8D 8E 8F 90 91 92 93 94 95 30
96 97 98 99 9A 9B 9C 9D 9E 9F A0 A1 A2 A3 A4 A5 A6 A7 A8 A9
AA AB AC AD AE AF B0 B1 B2 B3 B4 B5 B6 B7 B8 B9 BA BB BC BD
30 BE BF 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A C0 C1 C2 C3 C4 30
30 30 30 BE BF 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A C5 C6 30 30 30
30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30
"""


@dataclass(frozen=True)
class ArtLayout:
    # (first tile ID, last tile ID, ROM offset of the first tile)
    tile_segments: Tuple[Tuple[int, int, int], ...]
    # Rows of tile IDs, one per 8x8 cell; None where the cell is not this art.
    grid: Tuple[Tuple[Optional[int], ...], ...]
    # Gray level of each colour index 0-3 as shown on screen.
    shades: Tuple[int, int, int, int]

    @property
    def image_size(self) -> Tuple[int, int]:
        return (len(self.grid[0]) * TILE_SIZE, len(self.grid) * TILE_SIZE)

    def rom_offset(self, tile_id: int) -> int:
        for first, last, offset in self.tile_segments:
            if first <= tile_id <= last:
                return offset + (tile_id - first) * TILE_BYTES
        raise ValueError(f"tile 0x{tile_id:02X} is not part of this art")


def _parse_grid(text: str) -> Tuple[Tuple[Optional[int], ...], ...]:
    return tuple(
        tuple(None if cell == EMPTY_CELL else int(cell, 16) for cell in line.split())
        for line in text.strip().splitlines()
    )


ART_LAYOUTS = {
    # The two tile blocks are the VRAM copies at 0x8800 and 0x9300 (docs/rom-map.md).
    # Shades are colour indices 0-3 under the title screen palette, BGP 0x2D.
    "title": ArtLayout(
        tile_segments=((0x80, 0xD4, 0x1A6AE), (0x30, 0x7F, 0x1ABFE)),
        grid=_parse_grid(TITLE_GRID),
        shades=(170, 0, 85, 255),
    ),
}


def _decode_tile(rom: bytes, offset: int) -> list:
    rows = []
    for y in range(TILE_SIZE):
        low, high = rom[offset + 2 * y], rom[offset + 2 * y + 1]
        rows.append([((high >> (7 - x)) & 1) << 1 | ((low >> (7 - x)) & 1) for x in range(TILE_SIZE)])
    return rows


def _encode_tile(rows: list) -> bytes:
    data = bytearray()
    for row in rows:
        low = sum((index & 1) << (7 - x) for x, index in enumerate(row))
        high = sum(((index >> 1) & 1) << (7 - x) for x, index in enumerate(row))
        data.extend((low, high))
    return bytes(data)


def render_art(layout: ArtLayout, rom: bytes) -> Image.Image:
    image = Image.new("L", layout.image_size, layout.shades[3])
    for row, cells in enumerate(layout.grid):
        for col, tile_id in enumerate(cells):
            if tile_id is None:
                continue
            pixels = _decode_tile(rom, layout.rom_offset(tile_id))
            for y, indices in enumerate(pixels):
                for x, index in enumerate(indices):
                    image.putpixel((col * TILE_SIZE + x, row * TILE_SIZE + y), layout.shades[index])
    return image


def _nearest_index(layout: ArtLayout, gray: int) -> int:
    return min(range(4), key=lambda index: abs(layout.shades[index] - gray))


def apply_art(layout: ArtLayout, rom: bytearray, image: Image.Image) -> None:
    if image.size != layout.image_size:
        width, height = layout.image_size
        raise ValueError(f"expected a {width}x{height} image, got {image.width}x{image.height}")
    gray = image.convert("L")
    tiles = {}
    for row, cells in enumerate(layout.grid):
        for col, tile_id in enumerate(cells):
            if tile_id is None:
                continue
            pixels = [
                [
                    _nearest_index(layout, gray.getpixel((col * TILE_SIZE + x, row * TILE_SIZE + y)))
                    for x in range(TILE_SIZE)
                ]
                for y in range(TILE_SIZE)
            ]
            if tiles.setdefault(tile_id, pixels) != pixels:
                raise ValueError(
                    f"tile 0x{tile_id:02X} appears in more than one cell with different pixels"
                )
    for tile_id, pixels in tiles.items():
        offset = layout.rom_offset(tile_id)
        rom[offset:offset + TILE_BYTES] = _encode_tile(pixels)
