"""Render and inject the character graphics targeted by the sprite swap."""

from PIL import Image, ImageDraw

from art_layout import _encode_tile
from render_graphics import (
    PORTRAIT_PALETTE,
    TILE_BYTES,
    TILE_WIDTH,
    render_portraits,
)
from sprite_art import Piece, apply_piece, apply_sprite_art, paste_piece, render_sprite
from swap_character_sprite import CHARACTER_SPRITES, POW_PORTRAIT_BYTES, SPRITE_BYTES

DEFAULT_SHEET_SIZE = (84, 50)
HERO_ARC_START = 0x9406
SHEET_SIZES = {
    "hero": (118, 67), "pit": (84, 84), "lane": (84, 67), "kyle": (84, 93),
    "jude": (135, 50), "lee": (84, 93), "lora": (84, 84), "zold": (84, 84),
}


def _arc_tiles(grid: tuple) -> tuple[Piece, ...]:
    """Pieces for a row-major grid of arc tile numbers (1-24), where None is an empty slot."""
    return tuple(
        Piece(None if tile is None else HERO_ARC_START + (tile - 1) * TILE_BYTES, 1, 1, top=row, left=column)
        for row, cells in enumerate(grid)
        for column, tile in enumerate(cells)
    )


# Each figure is (x, y, pieces) on the hero sheet. The sword and electric-ball halves sit below the
# standard poses, and all four sword arcs cluster to the right of the portrait.
HERO_FIGURES = (
    (0, 51, (Piece(0x9346, 2, 2),)),
    (17, 51, (Piece(0x9386, 2, 2),)),
    (34, 51, (Piece(0x93C6, 2, 2),)),
    (51, 51, (Piece(0x9586, 1, 2),)),
    (68, 51, (Piece(0x95A6, 1, 2),)),
    (85, 0, _arc_tiles(((7, 8), (9, None), (10, None), (11, 12)))),
    (102, 0, _arc_tiles(((19, 20), (21, None), (22, None), (23, 24)))),
    (85, 34, _arc_tiles(((1, None, None, 2), (3, 4, 5, 6)))),
    (85, 51, _arc_tiles(((13, None, None, 14), (15, 16, 17, 18)))),
)


def _row_major_tiles(offset: int, columns: int, rows: int) -> tuple[Piece, ...]:
    """Single-tile pieces that show consecutive ROM tiles left to right, then top to bottom."""
    return tuple(
        Piece(offset + index * TILE_BYTES, 1, 1, top=index // columns, left=index % columns)
        for index in range(columns * rows)
    )


# Attack and particle sprites for each character, grouped by the character they belong to.
PIT_ATTACK_FIGURES = (
    (Piece(0x9846, 2, 2),),
    (Piece(0x9886, 2, 2),),
    (Piece(0x98C6, 1, 2),),
    (Piece(0x98E6, 2, 1),),
    (Piece(0x9906, 2, 2),),
    (Piece(0x9946, 2, 2),),
    (Piece(0x9986, 2, 2),),
    (Piece(0x99C6, 2, 2),),
)
LANE_ATTACK_FIGURES = tuple((Piece(offset, 2, 2),) for offset in (0x9C86, 0x9CC6, 0x9D06, 0x9D46))
# The lightning sprite's two transparent right-hand tiles (0xA1E6, 0xA1F6) are dropped. Its
# bottom-left tile is read as the second tile of a one-row piece, so it sits right of the top-left.
KYLE_ATTACK_FIGURES = tuple((Piece(offset, 2, 2),) for offset in (
    0xA006, 0xA046, 0xA086, 0xA0C6, 0xA106, 0xA146, 0xA186, 0xA246, 0xA286, 0xA2C6,
)) + ((Piece(0xA1C6, 2, 1),),)
JUDE_ROD_DOWN = (Piece(0xA546, 2, 2),)
JUDE_ROD_UP = (Piece(0xA586, 2, 2),)
JUDE_ROD_LEFT = (Piece(0xA5C6, 2, 2),)
JUDE_WEAK_FIREBALL_DOWN = (Piece(0xA606, 1, 2),)
JUDE_WEAK_FIREBALL_LEFT = (Piece(0xA626, 2, 1),)
JUDE_EARTHQUAKE_FIGURE = (Piece(0xA706, 2, 2), Piece(0xA746, 2, 2, top=2))
JUDE_SMASHBALL_DOWN = _row_major_tiles(0xA646, 2, 3)
JUDE_SMASHBALL_LEFT = _row_major_tiles(0xA6A6, 3, 2)
LEE_ATTACK_FIGURES = (
    (Piece(0xAA06, 2, 2),),
    (Piece(0xAA46, 2, 2),),
    (Piece(0xAA86, 2, 2),),
    (Piece(0xAAC6, 2, 2),),
    (Piece(0xAB06, 2, 2),),
    (Piece(0xAB46, 2, 2),),
    (Piece(0xAB86, 2, 2),),
    (Piece(0xABC6, 2, 2),),
    (Piece(0xAC06, 2, 2),),
    (Piece(0xAC46, 2, 1),),
    (Piece(0xAC66, 2, 1),),
)
LORA_ATTACK_FIGURES = (
    (Piece(0xAF06, 1, 2),),
    (Piece(0xAF26, 2, 1),),
    (Piece(0xAF46, 2, 2),),
    (Piece(0xAF86, 2, 2),),
    (Piece(0xAFC6, 2, 2),),
    (Piece(0xB006, 2, 2),),
    (Piece(0xB046, 2, 1),),
    (Piece(0xB066, 2, 1),),
    (Piece(0xB086, 1, 1),),
    (Piece(0xB096, 1, 1),),
)
ZOLD_ATTACK_FIGURES = (
    (Piece(0xB326, 2, 2),),
    (Piece(0xB366, 2, 2),),
    (Piece(0xB3A6, 2, 2),),
    (Piece(0xB3E6, 2, 1),),
    (Piece(0xB406, 1, 2),),
    (Piece(0xB426, 2, 2),),
    (Piece(0xB466, 2, 2),),
    (Piece(0xB4A6, 2, 2),),
    (Piece(0xB4E6, 2, 2),),
)


def _figure_size(figure: tuple[Piece, ...]) -> tuple[int, int]:
    return (
        max(piece.left + piece.columns for piece in figure) * TILE_WIDTH,
        max(piece.top + piece.rows for piece in figure) * TILE_WIDTH,
    )


def _cell_layout(figures, top: int, columns: int = 5) -> tuple[tuple[int, int, tuple[Piece, ...]], ...]:
    """Place figures in cells at least 16 pixels wide (wider if a figure needs it), each row as tall as its
    tallest figure, with 1-pixel red gutters."""
    cell_width = max([16] + [_figure_size(figure)[0] for figure in figures])
    placements = []
    for row_start in range(0, len(figures), columns):
        row = figures[row_start:row_start + columns]
        sizes = [_figure_size(figure) for figure in row]
        row_height = max(height for _, height in sizes)
        for column, (figure, (width, height)) in enumerate(zip(row, sizes)):
            x = column * (cell_width + 1) + (cell_width - width) // 2
            placements.append((x, top + (row_height - height) // 2, figure))
        top += row_height + 1
    return tuple(placements)


# Attack sheets below each character's poses. inject-art writes every one of them back.
ATTACK_FIGURES = {
    "pit": _cell_layout(PIT_ATTACK_FIGURES, 51),
    "lane": _cell_layout(LANE_ATTACK_FIGURES, 51),
    "kyle": _cell_layout(KYLE_ATTACK_FIGURES, 51),
    # Explicit positions: the pose and smashballs sit right of the POW portrait, and the rods are stacked
    # in a column past the right edge.
    "jude": (
        (85, 0, JUDE_EARTHQUAKE_FIGURE),
        (102, 0, JUDE_SMASHBALL_DOWN),
        (102, 25, JUDE_WEAK_FIREBALL_LEFT),
        (85, 34, JUDE_SMASHBALL_LEFT),
        (110, 34, JUDE_WEAK_FIREBALL_DOWN),
        (119, 0, JUDE_ROD_DOWN),
        (119, 17, JUDE_ROD_UP),
        (119, 34, JUDE_ROD_LEFT),
    ),
    "lee": _cell_layout(LEE_ATTACK_FIGURES, 51),
    "lora": _cell_layout(LORA_ATTACK_FIGURES, 51),
    "zold": _cell_layout(ZOLD_ATTACK_FIGURES, 51),
}
# Figures written back by inject-art, in addition to the standard poses and portrait.
EXTRA_FIGURES = {"hero": HERO_FIGURES, **ATTACK_FIGURES}


def _band_figures(character: str) -> tuple:
    """Figures drawn below a character's standard poses."""
    return EXTRA_FIGURES.get(character, ())


def character_sheet_size(character: str) -> tuple[int, int]:
    return SHEET_SIZES.get(character, DEFAULT_SHEET_SIZE)


def _character_offsets(rom: bytes | bytearray, character: str) -> tuple[list[int], int]:
    if character not in CHARACTER_SPRITES:
        raise ValueError(f"unknown character: {character}")
    standard, defeated, face, portrait = CHARACTER_SPRITES[character]
    offsets = [standard + index * SPRITE_BYTES for index in (0, 1, 6, 4, 5, 8, 2, 3, 7)]
    offsets += [defeated, face]
    band = [piece for _, _, pieces in _band_figures(character) for piece in pieces if piece.offset is not None]
    if (
        any(offset + SPRITE_BYTES > len(rom) for offset in offsets)
        or portrait + POW_PORTRAIT_BYTES > len(rom)
        or any(piece.offset + piece.columns * piece.rows * TILE_BYTES > len(rom) for piece in band)
    ):
        raise ValueError(f"ROM does not contain complete {character} sprite data")
    return offsets, portrait


def _sprite_position(index: int) -> tuple[int, int]:
    if index < 9:
        return (index % 3) * 17, (index // 3) * 17
    return 51 + (index - 9) * 17, 34


def render_character_art(rom: bytes, character: str) -> Image.Image:
    offsets, portrait = _character_offsets(rom, character)

    image = Image.new("RGB", character_sheet_size(character), (255, 0, 0))
    draw = ImageDraw.Draw(image)
    for x in (16, 33, 50):
        draw.line((x, 0, x, 49), fill=(255, 0, 0))
    draw.line((0, 16, 50, 16), fill=(255, 0, 0))
    draw.line((0, 33, 83, 33), fill=(255, 0, 0))
    draw.line((67, 34, 67, 49), fill=(255, 0, 0))

    for index, offset in enumerate(offsets):
        image.paste(render_sprite(rom, offset), _sprite_position(index))
    portrait_image = render_portraits(rom[portrait:portrait + POW_PORTRAIT_BYTES], columns=1, scale=1)
    image.paste(portrait_image, (51, 0))
    for x, y, pieces in _band_figures(character):
        for piece in pieces:
            paste_piece(image, rom, piece, x, y)
    return image


def apply_character_art(rom: bytearray, character: str, image: Image.Image) -> None:
    offsets, portrait = _character_offsets(rom, character)
    size = character_sheet_size(character)
    if image.size != size:
        raise ValueError(f"expected a {size[0]}x{size[1]} image, got {image.width}x{image.height}")
    gray = image.convert("L")
    writes = []

    def encode_tiles(offset, x, y, positions, palette):
        shades = [color[0] for color in palette]
        lut = [min(range(4), key=lambda index: abs(shades[index] - level)) for level in range(256)]
        for tile, (col, row) in enumerate(positions):
            rows = [
                [lut[gray.getpixel((x + col * TILE_WIDTH + px, y + row * TILE_WIDTH + py))]
                 for px in range(TILE_WIDTH)]
                for py in range(TILE_WIDTH)
            ]
            writes.append((offset + tile * TILE_BYTES, _encode_tile(rows)))

    for index, offset in enumerate(offsets):
        x, y = _sprite_position(index)
        apply_sprite_art(rom, gray, offset, x, y)
    portrait_positions = tuple((index % 4, index // 4) for index in range(16))
    encode_tiles(portrait, 51, 0, portrait_positions, PORTRAIT_PALETTE)

    for x, y, pieces in EXTRA_FIGURES.get(character, ()):
        for piece in pieces:
            apply_piece(rom, gray, piece, x, y)

    for offset, data in writes:
        rom[offset:offset + TILE_BYTES] = data
