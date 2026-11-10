"""Render the documented town NPC and non-boss enemy sprites as an inject-ready sheet."""

from PIL import Image

from art_layout import _encode_tile
from render_graphics import (
    DEFAULT_PALETTE,
    SPRITE_TILE_POSITIONS,
    TILE_BYTES,
    TILE_WIDTH,
    render_sprites,
)


SPRITE_BYTES = 64
SPRITE_SIZE = 16
SEPARATOR = (255, 0, 0)
COLUMNS = 6
PITCH = SPRITE_SIZE + 1

def _entities(start: int, frames: int, count: int) -> list[tuple[int, ...]]:
    """Return each entity's frame offsets; entities are consecutive in ROM."""
    return [
        tuple(start + (entity * frames + frame) * SPRITE_BYTES for frame in range(frames))
        for entity in range(count)
    ]


def _layout() -> tuple[list[tuple[int, int, int]], int]:
    """Place entities in rows so each entity's frames stay together.

    Each four-pose set shares a row with one of the first seven enemy two-frame sets,
    filling the two cells it would otherwise leave empty. The remaining two-frame sets
    pack three to a row, and each six-pose set takes its own row.
    """
    two_frame = _entities(0x1861E, 2, 8) + _entities(0xE25A, 2, 28)
    four_pose = _entities(0xF05A, 4, 7)
    six_pose = _entities(0xF75A, 6, 4)
    paired = two_frame[8:15]
    unpaired = two_frame[:8] + two_frame[15:]

    rows = [unpaired[index:index + 3] for index in range(0, len(unpaired), 3)]
    rows += [[four, two] for four, two in zip(four_pose, paired)]
    rows += [[six] for six in six_pose]

    placements = []
    for row_index, row in enumerate(rows):
        column = 0
        for entity in row:
            for frame, offset in enumerate(entity):
                placements.append((offset, column + frame, row_index))
            column += len(entity)
    return placements, len(rows)


def _sheet(rom_length: int) -> tuple[list[tuple[int, int, int]], tuple[int, int]]:
    placements, rows = _layout()
    if max(offset for offset, _, _ in placements) + SPRITE_BYTES > rom_length:
        raise ValueError("ROM does not contain all documented NPC and enemy graphics")
    return placements, (COLUMNS * PITCH - 1, rows * PITCH - 1)


def render_npc_art(rom: bytes) -> Image.Image:
    """Render every documented NPC and non-boss enemy frame at 1:1 scale with a red grid."""
    placements, size = _sheet(len(rom))
    image = Image.new("RGB", size, SEPARATOR)
    for offset, column, row in placements:
        sprite = render_sprites(rom[offset:offset + SPRITE_BYTES], columns=1, scale=1)
        image.paste(sprite, (column * PITCH, row * PITCH))
    return image


def apply_npc_art(rom: bytearray, image: Image.Image) -> None:
    """Write each sheet cell back to its sprite, mapping every pixel to the nearest palette shade."""
    placements, size = _sheet(len(rom))
    if image.size != size:
        width, height = size
        raise ValueError(f"expected a {width}x{height} image, got {image.width}x{image.height}")
    gray = image.convert("L")
    shades = [color[0] for color in DEFAULT_PALETTE]
    lut = [min(range(len(shades)), key=lambda index: abs(shades[index] - level)) for level in range(256)]

    for offset, column, row in placements:
        x, y = column * PITCH, row * PITCH
        for tile, (tile_col, tile_row) in enumerate(SPRITE_TILE_POSITIONS):
            pixels = [
                [lut[gray.getpixel((x + tile_col * TILE_WIDTH + px, y + tile_row * TILE_WIDTH + py))]
                 for px in range(TILE_WIDTH)]
                for py in range(TILE_WIDTH)
            ]
            start = offset + tile * TILE_BYTES
            rom[start:start + TILE_BYTES] = _encode_tile(pixels)
