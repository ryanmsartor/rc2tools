import unittest

from tests.support import load_bin_module

hack_rom = load_bin_module("hack_rom")


def apply_ips(original, patch):
    if not patch.startswith(b"PATCH"):
        raise ValueError("missing IPS header")
    rom = bytearray(original)
    offset = 5
    while patch[offset:offset + 3] != b"EOF":
        address = int.from_bytes(patch[offset:offset + 3], "big")
        size = int.from_bytes(patch[offset + 3:offset + 5], "big")
        if size == 0:
            raise ValueError("unexpected RLE record")
        data = patch[offset + 5:offset + 5 + size]
        if len(rom) < address + size:
            rom.extend(bytes(address + size - len(rom)))
        rom[address:address + size] = data
        offset += 5 + size
    offset += 3
    if offset < len(patch):
        length = int.from_bytes(patch[offset:offset + 3], "big")
        del rom[length:]
        offset += 3
    if offset != len(patch):
        raise ValueError("trailing IPS data")
    return bytes(rom)


class BuildIpsPatchTests(unittest.TestCase):
    def test_identical_roms_produce_empty_patch(self):
        rom = bytes(range(256)) * 4
        self.assertEqual(hack_rom.build_ips_patch(rom, rom), b"PATCHEOF")

    def test_patch_round_trips_scattered_changes(self):
        original = bytes([0x00]) * 0x400
        modified = bytearray(original)
        modified[0x10:0x14] = b"\x01\x02\x03\x04"
        modified[0x3FE] = 0xFF
        modified = bytes(modified)
        patch = hack_rom.build_ips_patch(original, modified)
        self.assertEqual(apply_ips(original, patch), modified)

    def test_long_change_is_split_into_maximum_sized_records(self):
        original = bytes(0x20000)
        modified = bytes([0xAB]) * 0x20000
        patch = hack_rom.build_ips_patch(original, modified)
        self.assertEqual(apply_ips(original, patch), modified)
        # 0x20000 bytes need three records: two of 0xFFFF bytes and one of 2 bytes.
        self.assertEqual(len(patch), 5 + 3 * 5 + 0x20000 + 3)

    def test_growing_rom_is_patched_past_original_end(self):
        original = b"\x00" * 8
        modified = b"\x00" * 6 + b"\x7F\x7F\x7F"
        patch = hack_rom.build_ips_patch(original, modified)
        self.assertEqual(apply_ips(original, patch), modified)

    def test_shrinking_rom_writes_truncation_length(self):
        original = b"\x00" * 8
        modified = b"\x00" * 4
        patch = hack_rom.build_ips_patch(original, modified)
        self.assertEqual(patch[-3:], (4).to_bytes(3, "big"))
        self.assertEqual(apply_ips(original, patch), modified)

    def test_offset_colliding_with_eof_marker_is_rejected(self):
        original = bytes(0x454F47)
        modified = bytearray(original)
        modified[0x454F46] = 0x01
        with self.assertRaises(ValueError):
            hack_rom.build_ips_patch(original, bytes(modified))


if __name__ == "__main__":
    unittest.main()
