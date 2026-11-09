"""Swap two characters' sprites and POW portraits within a ROM."""

SPRITE_BYTES = 64
STANDARD_SPRITE_BYTES = 9 * SPRITE_BYTES
POW_PORTRAIT_BYTES = 0x100

# Standard pose start, defeated sprite, level-up face, and POW portrait offsets.
CHARACTER_SPRITES = {
    "hero": (0x9106, 0x95C6, 0x860E, 0x880E),
    "pit": (0x9606, 0x9A06, 0x864E, 0x890E),
    "lane": (0x9A46, 0x9D86, 0x868E, 0x8A0E),
    "kyle": (0x9DC6, 0xA206, 0x86CE, 0x8B0E),
    "jude": (0xA306, 0xA786, 0x870E, 0x8C0E),
    "lee": (0xA7C6, 0xAC86, 0x874E, 0x8D0E),
    "lora": (0xACC6, 0xB0A6, 0x878E, 0x8E0E),
    "zold": (0xB0E6, 0xB526, 0x87CE, 0x8F0E),
}


def swap_character_sprites(rom: bytearray, character1: str, character2: str) -> None:
    """Swap two characters' sprites and POW portraits in rom, in place."""
    if character1 not in CHARACTER_SPRITES:
        raise ValueError(f"unknown character: {character1}")
    if character2 not in CHARACTER_SPRITES:
        raise ValueError(f"unknown character: {character2}")
    if character1 == character2:
        raise ValueError("characters must be different")

    first = CHARACTER_SPRITES[character1]
    second = CHARACTER_SPRITES[character2]
    segments = (
        (first[0], second[0], STANDARD_SPRITE_BYTES),
        (first[1], second[1], SPRITE_BYTES),
        (first[2], second[2], SPRITE_BYTES),
        (first[3], second[3], POW_PORTRAIT_BYTES),
    )
    for first_offset, second_offset, size in segments:
        if max(first_offset, second_offset) + size > len(rom):
            raise ValueError("ROM does not contain complete sprite data")
    for first_offset, second_offset, size in segments:
        first_data = rom[first_offset:first_offset + size]
        rom[first_offset:first_offset + size] = rom[second_offset:second_offset + size]
        rom[second_offset:second_offset + size] = first_data
