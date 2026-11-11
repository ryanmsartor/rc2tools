import argparse
import tempfile
import unittest
from pathlib import Path

from tests.support import load_bin_module

rom_io = load_bin_module("rom_io")


def hex_dump(data, powershell=False):
    rows = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        if powershell:
            rows.append(f"{offset:08X}   {chunk.hex(' ').upper()}  ................")
        else:
            groups = " ".join(chunk[i:i + 2].hex() for i in range(0, 16, 2))
            rows.append(f"{offset:08x}: {groups}  ................")
    text = "\n".join(rows) + "\n"
    return text.encode("utf-16" if powershell else "utf-8")


class RomIoTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytearray((i * 37 + i // 256) % 256 for i in range(0x20000))
        self.rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        self.rom[0x147:0x149] = b"\x06\x02"

    def test_parse_offset_accepts_decimal_and_hex(self):
        self.assertEqual(rom_io.parse_offset("16"), 16)
        self.assertEqual(rom_io.parse_offset("0x10"), 16)
        with self.assertRaises(argparse.ArgumentTypeError):
            rom_io.parse_offset("zz")

    def test_hex_dump_formats_and_invalid_rows(self):
        for powershell in (False, True):
            with self.subTest(powershell=powershell):
                self.assertEqual(rom_io.parse_hex_dump(hex_dump(self.rom, powershell)), self.rom)
        with self.assertRaisesRegex(ValueError, "expected offset"):
            rom_io.parse_hex_dump(b"00000010: 0000 0000 0000 0000 0000 0000 0000 0000  ................\n")
        with self.assertRaisesRegex(ValueError, "invalid hex dump row"):
            rom_io.parse_hex_dump(b"00000000: 0000 broken\n")
        with self.assertRaisesRegex(ValueError, "no recognizable rows"):
            rom_io.parse_hex_dump(b"not a dump\n")

    def test_read_rom_accepts_binary_and_hex_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "game.gb"
            binary.write_bytes(self.rom)
            self.assertEqual(rom_io.read_rom(binary), self.rom)
            dump = Path(directory) / "game.hex"
            dump.write_bytes(hex_dump(self.rom))
            self.assertEqual(rom_io.read_rom(dump), self.rom)

    def test_read_rom_rejects_truncated_or_wrong_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game.gb"
            path.write_bytes(self.rom[:-1])
            with self.assertRaisesRegex(ValueError, "expected a 131072-byte ROM"):
                rom_io.read_rom(path)
            self.rom[0x134] = 0
            path.write_bytes(self.rom)
            with self.assertRaisesRegex(ValueError, "ROM header does not match"):
                rom_io.read_rom(path)


if __name__ == "__main__":
    unittest.main()
