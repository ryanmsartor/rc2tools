"""Render the in-UI character ability icons as a sprite sheet."""

from PIL import Image

from sprite_art import (
    PITCH,
    SPRITE_BYTES,
    apply_sprite_art,
    render_sprite_sheet,
    sprite_sheet_size,
)


ABILITY_START = 0x804E
ABILITY_COUNT = 23
ABILITY_COLUMNS = 6


def render_ability_art(rom: bytes) -> Image.Image:
    end = ABILITY_START + ABILITY_COUNT * SPRITE_BYTES
    if end > len(rom):
        raise ValueError("ROM does not contain all 23 ability sprites")
    placements = [
        (ABILITY_START + index * SPRITE_BYTES, index % ABILITY_COLUMNS, index // ABILITY_COLUMNS)
        for index in range(ABILITY_COUNT)
    ]
    return render_sprite_sheet(rom, placements, sprite_sheet_size(ABILITY_COUNT, ABILITY_COLUMNS))


def apply_ability_art(rom: bytearray, image: Image.Image) -> None:
    """Apply the 23 ability sprites from their dump sheet layout."""
    size = sprite_sheet_size(ABILITY_COUNT, ABILITY_COLUMNS)
    if image.size != size:
        raise ValueError(f"expected a {size[0]}x{size[1]} image, got {image.width}x{image.height}")
    end = ABILITY_START + ABILITY_COUNT * SPRITE_BYTES
    if end > len(rom):
        raise ValueError("ROM does not contain all 23 ability sprites")

    gray = image.convert("L")
    for index in range(ABILITY_COUNT):
        x = index % ABILITY_COLUMNS * PITCH
        y = index // ABILITY_COLUMNS * PITCH
        apply_sprite_art(rom, gray, ABILITY_START + index * SPRITE_BYTES, x, y)
