#!/usr/bin/env python3
"""Manage an in-progress hack copy of Rolan's Curse II and finalize it as an IPS patch."""

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image

from art_layout import ART_LAYOUTS, apply_art, render_art
from swap_character_sprite import CHARACTER_SPRITES, swap_character_sprites


ROOT = Path(__file__).resolve().parent.parent
ROM_NAME = "Rolan's Curse II (USA).gb"
INPUT_ROM_PATH = ROOT / "input" / ROM_NAME
WORKING_DIR = ROOT / "working"
WORKING_ROM_PATH = WORKING_DIR / "Rolan's Curse II (USA) (hack in progress).gb"
HACKS_LOG_PATH = WORKING_DIR / "hacks.txt"
OUTPUT_DIR = ROOT / "output"
FINALIZED_STEM = "Rolan's Curse II (USA) (hack finalized)"
SWAP_SUBCOMMAND = "swap-char-sprite"
SWAP_ALIAS = "swap-character-sprite"
IPS_HEADER = b"PATCH"
IPS_EOF = b"EOF"
IPS_EOF_OFFSET = int.from_bytes(IPS_EOF, "big")
IPS_MAX_RECORD_SIZE = 0xFFFF
IPS_MAX_OFFSET = 0xFFFFFF


def build_ips_patch(original: bytes, modified: bytes) -> bytes:
    """Return an IPS patch that turns original into modified."""
    patch = bytearray(IPS_HEADER)
    index = 0
    while index < len(modified):
        if index < len(original) and original[index] == modified[index]:
            index += 1
            continue
        start = index
        while (
            index < len(modified)
            and index - start < IPS_MAX_RECORD_SIZE
            and (index >= len(original) or original[index] != modified[index])
        ):
            index += 1
        if start > IPS_MAX_OFFSET or start == IPS_EOF_OFFSET:
            raise ValueError(f"offset 0x{start:X} cannot be represented in an IPS record")
        data = modified[start:index]
        patch.extend(start.to_bytes(3, "big"))
        patch.extend(len(data).to_bytes(2, "big"))
        patch.extend(data)

    patch.extend(IPS_EOF)
    if len(modified) < len(original):
        # IPS truncation: the trailing 3-byte value sets the final file length.
        patch.extend(len(modified).to_bytes(3, "big"))
    return bytes(patch)


def copy_input_to_working() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(INPUT_ROM_PATH, WORKING_ROM_PATH)
    HACKS_LOG_PATH.write_text("")


def ensure_working_copy() -> None:
    if not WORKING_ROM_PATH.is_file():
        copy_input_to_working()
    HACKS_LOG_PATH.touch(exist_ok=True)


def remove_working_files() -> None:
    WORKING_ROM_PATH.unlink(missing_ok=True)
    HACKS_LOG_PATH.unlink(missing_ok=True)


def clear_working_copy() -> None:
    remove_working_files()
    print(f"Deleted {WORKING_ROM_PATH}")


def reset_working_copy() -> None:
    remove_working_files()
    copy_input_to_working()
    print(f"Reset {WORKING_ROM_PATH}")


def record_hack(description: str) -> None:
    with HACKS_LOG_PATH.open("a") as log:
        log.write(f"{description}\n")


def apply_swap_character_sprite(character1: str, character2: str) -> None:
    rom = bytearray(WORKING_ROM_PATH.read_bytes())
    swap_character_sprites(rom, character1, character2)
    WORKING_ROM_PATH.write_bytes(rom)
    record_hack(f"{SWAP_SUBCOMMAND} {character1} {character2}")
    print(f"Swapped {character1} and {character2} sprites in {WORKING_ROM_PATH}")


def art_png_path(name: str) -> Path:
    return WORKING_DIR / f"{name}-art.png"


def dump_art(name: str) -> None:
    image = render_art(ART_LAYOUTS[name], WORKING_ROM_PATH.read_bytes())
    path = art_png_path(name)
    image.save(path)
    print(f"Wrote {path}")


def read_art(name: str) -> None:
    rom = bytearray(WORKING_ROM_PATH.read_bytes())
    path = art_png_path(name)
    with Image.open(path) as image:
        apply_art(ART_LAYOUTS[name], rom, image)
    WORKING_ROM_PATH.write_bytes(rom)
    record_hack(f"inject-art {name}")
    print(f"Applied {path} to {WORKING_ROM_PATH}")


def finalize_working_copy() -> None:
    original = INPUT_ROM_PATH.read_bytes()
    modified = WORKING_ROM_PATH.read_bytes()
    patch = build_ips_patch(original, modified)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rom_output = OUTPUT_DIR / f"{FINALIZED_STEM}.gb"
    patch_output = OUTPUT_DIR / f"{FINALIZED_STEM}.ips"
    rom_output.write_bytes(modified)
    patch_output.write_bytes(patch)
    print(f"Wrote {rom_output}")
    print(f"Wrote {patch_output}")


def _add_swap_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "character1",
        type=str.lower,
        choices=tuple(CHARACTER_SPRITES),
        help="first character to swap",
    )
    parser.add_argument(
        "character2",
        type=str.lower,
        choices=tuple(CHARACTER_SPRITES),
        help="second character to swap",
    )


def _add_art_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("name", choices=tuple(ART_LAYOUTS), help="named art to use")


def main() -> int:
    parser = argparse.ArgumentParser(prog="rc2t hack", description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True, metavar="<subcommand>")
    subparsers.add_parser("clear", help="delete the in-progress hack copy and hacks.txt")
    subparsers.add_parser("reset", help="replace the in-progress hack copy with a fresh copy of the input ROM")
    subparsers.add_parser(
        "finalize",
        help="copy the in-progress hack into output/ and write an IPS patch against the input ROM",
    )
    swap_parser = subparsers.add_parser(
        SWAP_SUBCOMMAND,
        help="swap two characters' sprites and POW portraits in the in-progress hack copy",
    )
    _add_swap_arguments(swap_parser)
    dump_parser = subparsers.add_parser(
        "dump-art",
        help="export named art from the in-progress hack to working/<name>-art.png",
    )
    _add_art_arguments(dump_parser)
    read_parser = subparsers.add_parser(
        "inject-art",
        help="apply working/<name>-art.png to the in-progress hack",
    )
    _add_art_arguments(read_parser)
    argv = sys.argv[1:]
    # Accept the original command name without listing it in help.
    if argv[:1] == [SWAP_ALIAS]:
        argv[0] = SWAP_SUBCOMMAND
    args = parser.parse_args(argv)
    if args.subcommand == SWAP_SUBCOMMAND and args.character1 == args.character2:
        swap_parser.error("characters must be different")

    try:
        ensure_working_copy()
        if args.subcommand == "clear":
            clear_working_copy()
        elif args.subcommand == "reset":
            reset_working_copy()
        elif args.subcommand == "finalize":
            finalize_working_copy()
        elif args.subcommand == SWAP_SUBCOMMAND:
            apply_swap_character_sprite(args.character1, args.character2)
        elif args.subcommand == "dump-art":
            dump_art(args.name)
        elif args.subcommand == "inject-art":
            read_art(args.name)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
