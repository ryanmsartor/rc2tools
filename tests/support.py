"""Shared helpers for loading bin/ modules, building ROMs, and copying the tool tree."""

import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
ROM_SIZE = 0x20000

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))


def load_bin_module(name):
    """Load bin/<name>.py as a fresh module object."""
    spec = importlib.util.spec_from_file_location(name, BIN / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blank_rom(fill=0x00, header=False):
    """Return a ROM-sized bytearray, optionally with the Rolan's Curse II header."""
    rom = bytearray([fill]) * ROM_SIZE
    if header:
        rom[0x134:0x143] = b"ROLAN'S CURSE 2"
        rom[0x147:0x149] = b"\x06\x02"
    return rom


def copy_tool_tree(root):
    """Copy the rc2t and rc2h wrappers and every bin/*.py module into root."""
    (root / "bin").mkdir(exist_ok=True)
    for wrapper in ("rc2t", "rc2h"):
        shutil.copy2(ROOT / wrapper, root / wrapper)
    for module in BIN.glob("*.py"):
        shutil.copy2(module, root / "bin" / module.name)
