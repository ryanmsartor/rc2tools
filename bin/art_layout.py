"""Named ROM art layouts for `rc2t hack dump-art` and `rc2t hack inject-art`.

The title screen's BG map is a tilemap in the ROM. Its tiles are loaded by a
copy list: six-byte records (length, source CPU address, VRAM destination, all
little-endian) ending with a zero length. Tile IDs are BG-map IDs under signed
tile addressing (LCDC=0xE3).

`inject-art` rewrites the tilemap and copy list. Stock tiles are rewritten in
place, and any extra tiles are copied from free ROM space.
"""

import struct
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PIL import Image


TILE_SIZE = 8
TILE_BYTES = 16
RECORD_SIZE = 6
BANK_SIZE = 0x4000
BANK_6_OFFSET = 0x18000
VRAM_BASE = 0x8000
VRAM_WINDOW = 0x2000


@dataclass(frozen=True)
class ArtLayout:
    # Tilemap cells, row-major, one byte per cell, starting at tilemap_offset.
    tilemap_offset: int
    columns: int
    rows: int
    # Blank grid rows at the top and bottom. They stay as they are in the ROM
    # and are not part of the image.
    margin_top: int
    margin_bottom: int
    # File offset of the word holding the CPU address of the copy list.
    pointer_offset: int
    # Stock copy records (length, source CPU address, VRAM destination).
    stock_copies: Tuple[Tuple[int, int, int], ...]
    # (first tile ID, last tile ID, ROM offset of the first tile). These tiles
    # are rewritten in place.
    in_place_blocks: Tuple[Tuple[int, int, int], ...]
    # Tiles beyond the in-place ones take IDs counting up from here.
    extra_first_id: int
    # Free ROM ranges (start, end exclusive), in fill order. The copy list goes
    # in whichever range that holds it leaves the most 16-byte slots for extra
    # tile bytes.
    free_runs: Tuple[Tuple[int, int], ...]
    # Gray level of each colour index 0-3 as shown on screen.
    shades: Tuple[int, int, int, int]

    @property
    def image_rows(self) -> int:
        return self.rows - self.margin_top - self.margin_bottom

    @property
    def image_size(self) -> Tuple[int, int]:
        return (self.columns * TILE_SIZE, self.image_rows * TILE_SIZE)

    def in_place_ids(self) -> List[int]:
        return [tile_id for first, last, _ in self.in_place_blocks for tile_id in range(first, last + 1)]

    def in_place_offset(self, tile_id: int) -> int:
        for first, last, offset in self.in_place_blocks:
            if first <= tile_id <= last:
                return offset + (tile_id - first) * TILE_BYTES
        raise ValueError(f"tile 0x{tile_id:02X} is not an in-place tile")


ART_LAYOUTS = {
    # The stock list copies tile blocks 0x80-0xD4 to VRAM 0x8800 and 0x30-0x7F
    # to VRAM 0x9300. Tiles 0x30, 0x3E, 0xD3 and 0xD4 (blank, a menu glyph
    # shared with the title's tilemap rows 13-17, copyright and menu cursor)
    # are not rewritten. Grid rows 0 and 12 are blank margins (tile 0x30), so
    # the image is rows 1-11. Shades are colour indices 0-3 under the title
    # screen palette, BGP 0x2D.
    "title": ArtLayout(
        tilemap_offset=0x13C34,
        columns=20,
        rows=13,
        margin_top=1,
        margin_bottom=1,
        pointer_offset=0x1800A,
        stock_copies=((0x0550, 0x66AE, 0x8800), (0x0500, 0x6BFE, 0x9300)),
        in_place_blocks=((0x31, 0x3D, 0x1AC0E), (0x3F, 0x7F, 0x1ACEE), (0x80, 0xD2, 0x1A6AE)),
        extra_first_id=0xD5,
        free_runs=((0x61, 0x100), (0x3FC6, 0x3FFF), (0x1BF80, 0x1C000)),
        shades=(170, 0, 85, 255),
    ),
}


def _cpu_to_file(cpu: int) -> int:
    if cpu < BANK_SIZE:
        return cpu
    if cpu < 2 * BANK_SIZE:
        return BANK_6_OFFSET + (cpu - BANK_SIZE)
    raise ValueError(f"CPU address 0x{cpu:04X} is outside banks 0 and 6")


def _file_to_cpu(offset: int) -> int:
    if offset < BANK_SIZE:
        return offset
    if BANK_6_OFFSET <= offset < BANK_6_OFFSET + BANK_SIZE:
        return BANK_SIZE + (offset - BANK_6_OFFSET)
    raise ValueError(f"file offset 0x{offset:05X} is not in bank 0 or bank 6")


def _tile_vram(tile_id: int) -> int:
    signed = tile_id - 256 if tile_id >= 0x80 else tile_id
    return 0x9000 + signed * TILE_BYTES


def _read_u16(rom: bytes, offset: int) -> int:
    return rom[offset] | rom[offset + 1] << 8


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


def _load_vram(layout: ArtLayout, rom: bytes) -> bytearray:
    vram = bytearray(VRAM_WINDOW)
    pos = _cpu_to_file(_read_u16(rom, layout.pointer_offset))
    while True:
        length = _read_u16(rom, pos)
        if length == 0:
            return vram
        src = _cpu_to_file(_read_u16(rom, pos + 2))
        dst = _read_u16(rom, pos + 4) - VRAM_BASE
        vram[dst:dst + length] = rom[src:src + length]
        pos += RECORD_SIZE


def render_art(layout: ArtLayout, rom: bytes) -> Image.Image:
    vram = _load_vram(layout, rom)
    image = Image.new("L", layout.image_size, layout.shades[3])
    for image_row in range(layout.image_rows):
        row = layout.margin_top + image_row
        for col in range(layout.columns):
            tile_id = rom[layout.tilemap_offset + row * layout.columns + col]
            pixels = _decode_tile(vram, _tile_vram(tile_id) - VRAM_BASE)
            for y, indices in enumerate(pixels):
                for x, index in enumerate(indices):
                    image.putpixel((col * TILE_SIZE + x, image_row * TILE_SIZE + y), layout.shades[index])
    return image


def _nearest_index(layout: ArtLayout, gray: int) -> int:
    return min(range(4), key=lambda index: abs(layout.shades[index] - gray))


def _storage_slots(runs: List[Tuple[int, int]]) -> List[int]:
    return [offset for start, end in runs for offset in range(start, end - TILE_BYTES + 1, TILE_BYTES)]


def _place_list(free_runs: Tuple[Tuple[int, int], ...], size: int) -> Tuple[int, List[Tuple[int, int]]]:
    best = None
    for i, (start, end) in enumerate(free_runs):
        if end - start < size:
            continue
        remaining = list(free_runs)
        remaining[i] = (start + size, end)
        key = (len(_storage_slots(remaining)), -(end - start))
        if best is None or key > best[0]:
            best = (key, start, remaining)
    if best is None:
        raise ValueError(f"no free ROM run holds the {size}-byte copy list")
    return best[1], best[2]


def apply_art(layout: ArtLayout, rom: bytearray, image: Image.Image) -> int:
    """Write the image into the ROM and return the number of unique tiles it uses."""
    if image.size != layout.image_size:
        width, height = layout.image_size
        raise ValueError(f"expected a {width}x{height} image, got {image.width}x{image.height}")
    gray = image.convert("L")
    lut = [_nearest_index(layout, level) for level in range(256)]
    patterns: List[Tuple[int, ...]] = []
    pattern_index: Dict[Tuple[int, ...], int] = {}
    cells: List[int] = []
    for image_row in range(layout.image_rows):
        for col in range(layout.columns):
            pattern = tuple(
                lut[gray.getpixel((col * TILE_SIZE + x, image_row * TILE_SIZE + y))]
                for y in range(TILE_SIZE)
                for x in range(TILE_SIZE)
            )
            index = pattern_index.get(pattern)
            if index is None:
                index = pattern_index[pattern] = len(patterns)
                patterns.append(pattern)
            cells.append(index)

    in_ids = layout.in_place_ids()
    extra_count = max(0, len(patterns) - len(in_ids))
    if extra_count and layout.extra_first_id + extra_count > 0x100:
        raise ValueError(f"{extra_count} extra tiles do not fit in tile IDs above 0x{layout.extra_first_id:02X}")
    list_size = RECORD_SIZE * (len(layout.stock_copies) + extra_count) + 2
    list_start, runs = _place_list(layout.free_runs, list_size)
    slots = _storage_slots(runs)
    if extra_count > len(slots):
        raise ValueError(f"{extra_count} extra tiles need free ROM, but only {len(slots)} 16-byte slots remain")

    writes: List[Tuple[int, bytes]] = []
    records = list(layout.stock_copies)
    tile_ids: List[int] = []
    for index, pattern in enumerate(patterns):
        data = _encode_tile([list(pattern[y * TILE_SIZE:(y + 1) * TILE_SIZE]) for y in range(TILE_SIZE)])
        if index < len(in_ids):
            tile_id = in_ids[index]
            writes.append((layout.in_place_offset(tile_id), data))
        else:
            extra = index - len(in_ids)
            tile_id = layout.extra_first_id + extra
            storage = slots[extra]
            writes.append((storage, data))
            records.append((TILE_BYTES, _file_to_cpu(storage), _tile_vram(tile_id)))
        tile_ids.append(tile_id)

    for cell, index in enumerate(cells):
        offset = layout.tilemap_offset + layout.margin_top * layout.columns + cell
        writes.append((offset, bytes([tile_ids[index]])))

    copy_list = bytearray()
    for length, src, dst in records:
        copy_list += struct.pack("<HHH", length, src, dst)
    copy_list += b"\x00\x00"
    writes.append((list_start, bytes(copy_list)))
    writes.append((layout.pointer_offset, struct.pack("<H", _file_to_cpu(list_start))))

    for offset, data in writes:
        rom[offset:offset + len(data)] = data
    return len(patterns)
