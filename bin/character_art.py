"""Render and inject the character graphics targeted by the sprite swap."""

from PIL import Image, ImageDraw

from art_layout import _encode_tile
from render_graphics import (
    DEFAULT_PALETTE,
    PORTRAIT_PALETTE,
    SPRITE_TILE_POSITIONS,
    TILE_BYTES,
    TILE_WIDTH,
    render_portraits,
    render_sprites,
)
from swap_character_sprite import CHARACTER_SPRITES, POW_PORTRAIT_BYTES, SPRITE_BYTES


def _character_offsets(rom: bytes | bytearray, character: str) -> tuple[list[int], int]:
    if character not in CHARACTER_SPRITES:
        raise ValueError(f"unknown character: {character}")
    standard, defeated, face, portrait = CHARACTER_SPRITES[character]
    offsets = [standard + index * SPRITE_BYTES for index in (0, 1, 6, 4, 5, 8, 2, 3, 7)]
    offsets += [defeated, face]
    if any(offset + SPRITE_BYTES > len(rom) for offset in offsets) or portrait + POW_PORTRAIT_BYTES > len(rom):
        raise ValueError(f"ROM does not contain complete {character} sprite data")
    return offsets, portrait


def _sprite_position(index: int) -> tuple[int, int]:
    if index < 9:
        return (index % 3) * 17, (index // 3) * 17
    return 51 + (index - 9) * 17, 34


def render_character_art(rom: bytes, character: str) -> Image.Image:
    offsets, portrait = _character_offsets(rom, character)

    image = Image.new("RGB", (84, 50), (255, 0, 0))
    draw = ImageDraw.Draw(image)
    for x in (16, 33, 50):
        draw.line((x, 0, x, 49), fill=(255, 0, 0))
    draw.line((0, 16, 50, 16), fill=(255, 0, 0))
    draw.line((0, 33, 83, 33), fill=(255, 0, 0))
    draw.line((67, 34, 67, 49), fill=(255, 0, 0))

    for index, offset in enumerate(offsets):
        sprite = render_sprites(rom[offset:offset + SPRITE_BYTES], columns=1, scale=1)
        image.paste(sprite, _sprite_position(index))
    image.paste(render_portraits(rom[portrait:portrait + POW_PORTRAIT_BYTES], columns=1, scale=1), (51, 0))
    return image


def apply_character_art(rom: bytearray, character: str, image: Image.Image) -> None:
    offsets, portrait = _character_offsets(rom, character)
    if image.size != (84, 50):
        raise ValueError(f"expected a 84x50 image, got {image.width}x{image.height}")
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
        encode_tiles(offset, x, y, SPRITE_TILE_POSITIONS, DEFAULT_PALETTE)
    portrait_positions = tuple((index % 4, index // 4) for index in range(16))
    encode_tiles(portrait, 51, 0, portrait_positions, PORTRAIT_PALETTE)

    for offset, data in writes:
        rom[offset:offset + TILE_BYTES] = data
