"""Shared rendering and pixel encoding for the 16x16 sprite sheets."""

from typing import NamedTuple, Optional

from PIL import Image

from art_layout import _encode_tile
from render_graphics import (
    HACK_ART_PALETTE,
    SPRITE_TILE_POSITIONS,
    TILE_BYTES,
    TILE_WIDTH,
    decode_tiles,
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


class Piece(NamedTuple):
    """Tiles stored column-first, placed `left` tile columns and `top` tile rows into a figure.

    An offset of None is an empty tile slot: it renders as red filler and is never injected.
    """

    offset: Optional[int]
    columns: int
    rows: int
    top: int = 0
    left: int = 0


def _check_piece(rom_length: int, piece: Piece) -> None:
    if piece.offset is None:
        return
    size = piece.columns * piece.rows * TILE_BYTES
    if piece.offset < 0 or piece.offset + size > rom_length:
        raise ValueError("ROM does not contain complete sprite data")


def paste_piece(image: Image.Image, rom: bytes, piece: Piece, x: int, y: int) -> None:
    """Draw one piece with its top-left corner at (x, y) plus its tile offset within the figure."""
    left = x + piece.left * TILE_WIDTH
    top = y + piece.top * TILE_WIDTH
    if piece.offset is None:
        image.paste(SEPARATOR, (left, top, left + piece.columns * TILE_WIDTH, top + piece.rows * TILE_WIDTH))
        return
    _check_piece(len(rom), piece)
    size = piece.columns * piece.rows * TILE_BYTES
    tiles = decode_tiles(rom[piece.offset:piece.offset + size])
    for index, tile in enumerate(tiles):
        tile_column, tile_row = divmod(index, piece.rows)
        for py, row in enumerate(tile):
            for px, shade in enumerate(row):
                image.putpixel(
                    (left + tile_column * TILE_WIDTH + px, top + tile_row * TILE_WIDTH + py),
                    HACK_ART_PALETTE[shade],
                )


def apply_piece(rom: bytearray, gray: Image.Image, piece: Piece, x: int, y: int) -> None:
    """Encode one piece from a grayscale sheet; empty slots are skipped so the ROM keeps its bytes."""
    if piece.offset is None:
        return
    _check_piece(len(rom), piece)
    left = x + piece.left * TILE_WIDTH
    top = y + piece.top * TILE_WIDTH
    for index in range(piece.columns * piece.rows):
        tile_column, tile_row = divmod(index, piece.rows)
        rows = [
            [
                PALETTE_LUT[gray.getpixel((left + tile_column * TILE_WIDTH + px, top + tile_row * TILE_WIDTH + py))]
                for px in range(TILE_WIDTH)
            ]
            for py in range(TILE_WIDTH)
        ]
        start = piece.offset + index * TILE_BYTES
        rom[start:start + TILE_BYTES] = _encode_tile(rows)

