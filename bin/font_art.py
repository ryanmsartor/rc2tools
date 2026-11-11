"""Render the stacked 1bpp font tiles as an inject-ready sheet."""

from PIL import Image

from render_graphics import render_stacked_glyphs
from tiles import TILE_BYTES, TILE_WIDTH


FONT_START = 0xB986
FONT_END = 0xBB06
FONT_TILES = (FONT_END - FONT_START) // TILE_BYTES
GLYPH_HEIGHT = TILE_WIDTH
FONT_GLYPHS = FONT_TILES * 2
SEPARATOR = (255, 0, 0)
COLUMNS = 6
ROWS = FONT_GLYPHS // COLUMNS
PITCH = TILE_WIDTH + 1
# Gray levels at or above this are background (a set bit); darker levels are ink (a clear bit).
INK_THRESHOLD = 128


def _sheet_size() -> tuple[int, int]:
    return COLUMNS * PITCH - 1, ROWS * PITCH - 1


def _glyph_cell(tile: int, half: int) -> tuple[int, int]:
    """Return the sheet cell (column, row) for a tile's top (half 0) or bottom (half 1) glyph.

    Glyphs fill the sheet in ROM order, left to right and then top to bottom.
    """
    glyph = tile * 2 + half
    row, column = divmod(glyph, COLUMNS)
    return column, row


def _check_rom(rom: bytes | bytearray) -> None:
    if len(rom) < FONT_END:
        raise ValueError("ROM does not contain the stacked font tiles")


def render_font_art(rom: bytes) -> Image.Image:
    """Render each stacked glyph in its own 8x8 cell with a red grid."""
    _check_rom(rom)
    image = Image.new("RGB", _sheet_size(), SEPARATOR)
    for tile in range(FONT_TILES):
        start = FONT_START + tile * TILE_BYTES
        tile_image = render_stacked_glyphs(rom[start:start + TILE_BYTES], columns=1, scale=1)
        for half in range(2):
            column, row = _glyph_cell(tile, half)
            glyph = tile_image.crop((0, half * GLYPH_HEIGHT, TILE_WIDTH, (half + 1) * GLYPH_HEIGHT))
            image.paste(glyph, (column * PITCH, row * PITCH))
    return image


def apply_font_art(rom: bytearray, image: Image.Image) -> None:
    """Write each glyph cell back to its font tile, thresholding every pixel to ink or background."""
    _check_rom(rom)
    width, height = _sheet_size()
    if image.size != (width, height):
        raise ValueError(f"expected a {width}x{height} image, got {image.width}x{image.height}")
    gray = image.convert("L")
    for tile in range(FONT_TILES):
        tile_bytes = bytearray(TILE_BYTES)
        for half in range(2):
            column, row = _glyph_cell(tile, half)
            x, y = column * PITCH, row * PITCH
            for py in range(GLYPH_HEIGHT):
                value = 0
                for px in range(TILE_WIDTH):
                    if gray.getpixel((x + px, y + py)) >= INK_THRESHOLD:
                        value |= 1 << (7 - px)
                tile_bytes[half * GLYPH_HEIGHT + py] = value
        start = FONT_START + tile * TILE_BYTES
        rom[start:start + TILE_BYTES] = tile_bytes
