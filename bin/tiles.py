"""Game Boy 2bpp tile codec shared by the art and sprite tools."""

TILE_WIDTH = 8
TILE_BYTES = 16


def decode_tile(data, offset: int = 0) -> list[list[int]]:
    """Return the 8x8 grid of pixel indices for the tile starting at offset."""
    rows = []
    for row in range(TILE_WIDTH):
        low, high = data[offset + 2 * row], data[offset + 2 * row + 1]
        rows.append([((low >> bit) & 1) | (((high >> bit) & 1) << 1) for bit in range(7, -1, -1)])
    return rows


def decode_tiles(data: bytes) -> list[list[list[int]]]:
    """Decode Game Boy 2bpp tiles, allowing a final tile to end at any byte."""
    if not data:
        raise ValueError("range must contain at least one byte")
    return [
        decode_tile(data[start:start + TILE_BYTES].ljust(TILE_BYTES, b"\x00"))
        for start in range(0, len(data), TILE_BYTES)
    ]


def encode_tile(rows: list) -> bytes:
    """Pack a grid of pixel indices into 16 bytes of 2bpp tile data."""
    data = bytearray()
    for row in rows:
        low = sum((index & 1) << (7 - x) for x, index in enumerate(row))
        high = sum(((index >> 1) & 1) << (7 - x) for x, index in enumerate(row))
        data.extend((low, high))
    return bytes(data)
