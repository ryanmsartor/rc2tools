"""Shared rendering and pixel encoding for the 16x16 sprite sheets."""

from PIL import Image

from art_layout import _encode_tile
from render_graphics import (
    HACK_ART_PALETTE,
    SPRITE_TILE_POSITIONS,
    TILE_BYTES,
    TILE_WIDTH,
    render_sprites,
)


SPRITE_BYTES = 64
SPRITE_SIZE = 16
SEPARATOR = (255, 0, 0)
PITCH = SPRITE_SIZE + 1
PALETTE_SHADES = tuple(color[0] for color in HACK_ART_PALETTE)
PALETTE_LUT = tuple(
    min(range(len(PALETTE_SHADES)), key=lambda index: abs(PALETTE_SHADES[index] - level))
    for level in range(256)
)


def render_sprite(rom: bytes, offset: int) -> Image.Image:
    """Render one sprite using the NPC and character sprite palette."""
    return render_sprites(
        rom[offset:offset + SPRITE_BYTES],
        columns=1,
        scale=1,
        palette=HACK_ART_PALETTE,
    )


def render_sprite_sheet(
    rom: bytes,
    placements: list[tuple[int, int, int]],
    size: tuple[int, int],
) -> Image.Image:
    """Render sprites at (ROM offset, column, row) placements on a red sheet."""
    for offset, _, _ in placements:
        if offset < 0 or offset + SPRITE_BYTES > len(rom):
            raise ValueError("ROM does not contain all documented sprite data")

    image = Image.new("RGB", size, SEPARATOR)
    for offset, column, row in placements:
        image.paste(render_sprite(rom, offset), (column * PITCH, row * PITCH))
    return image


def sprite_sheet_size(sprite_count: int, columns: int) -> tuple[int, int]:
    """Return the size of a red-guttered sheet with the given sprite count."""
    if sprite_count < 1 or columns < 1:
        raise ValueError("sprite count and column count must be at least 1")
    rows = (sprite_count + columns - 1) // columns
    return columns * PITCH - 1, rows * PITCH - 1


def apply_sprite_art(rom: bytearray, gray: Image.Image, offset: int, x: int, y: int) -> None:
    """Encode one sprite from a grayscale art sheet using the shared sprite palette."""
    if offset < 0 or offset + SPRITE_BYTES > len(rom):
        raise ValueError("ROM does not contain complete sprite data")
    for tile, (tile_col, tile_row) in enumerate(SPRITE_TILE_POSITIONS):
        rows = [
            [
                PALETTE_LUT[gray.getpixel((x + tile_col * TILE_WIDTH + px, y + tile_row * TILE_WIDTH + py))]
                for px in range(TILE_WIDTH)
            ]
            for py in range(TILE_WIDTH)
        ]
        start = offset + tile * TILE_BYTES
        rom[start:start + TILE_BYTES] = _encode_tile(rows)
