"""Render the documented town NPC and non-boss enemy sprites as an inject-ready sheet."""

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
COLUMNS = 12
PITCH = SPRITE_SIZE + 1

# Idle NPC frames that are byte-identical to enemy frames. Only the enemy copy is dumped;
# injection writes the edited bytes to the idle copy as well.
DUPLICATE_FRAMES = {
    0x1869E: 0xE25A,
    0x186DE: 0xE29A,
    0x1889E: 0xE2DA,
    0x188DE: 0xE31A,
}


def _entities(start: int, frames: int, count: int) -> list[tuple[int, ...]]:
    """Return each entity's frame offsets; entities are consecutive in ROM."""
    return [
        tuple(start + (entity * frames + frame) * SPRITE_BYTES for frame in range(frames))
        for entity in range(count)
    ]


def _layout() -> tuple[list[tuple[int, int, int]], int]:
    """Place entities in 12-cell rows so each entity's frames stay together.

    Rows run in three sections: the two-frame sets, then the four-pose sets, then the
    six-pose sets. The first boundary row holds the last four two-frame sets and one
    four-pose set, so all 120 cells are used in 10 rows.
    """
    idle = [entity for entity in _entities(0x1861E, 2, 8) if entity[0] not in DUPLICATE_FRAMES]
    enemy = _entities(0xE25A, 2, 28)
    four_pose = _entities(0xF05A, 4, 7)
    six_pose = _entities(0xF75A, 6, 4)

    two_frame = idle + enemy
    rows = [two_frame[index:index + 6] for index in range(0, 30, 6)]
    rows.append(two_frame[30:] + four_pose[0:1])
    rows += [four_pose[1:4], four_pose[4:7]]
    rows += [six_pose[0:2], six_pose[2:4]]

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
        sprite = render_sprites(rom[offset:offset + SPRITE_BYTES], columns=1, scale=1, palette=HACK_ART_PALETTE)
        image.paste(sprite, (column * PITCH, row * PITCH))
    return image


def apply_npc_art(rom: bytearray, image: Image.Image) -> None:
    """Write each sheet cell back to its sprite, mapping every pixel to the nearest palette shade."""
    placements, size = _sheet(len(rom))
    if image.size != size:
        width, height = size
        raise ValueError(f"expected a {width}x{height} image, got {image.width}x{image.height}")
    gray = image.convert("L")
    shades = [color[0] for color in HACK_ART_PALETTE]
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

    for duplicate, original in DUPLICATE_FRAMES.items():
        rom[duplicate:duplicate + SPRITE_BYTES] = rom[original:original + SPRITE_BYTES]
