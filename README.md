# rc2tools
A collection of tools for hacking Rolan's Curse 2 for Game Boy

For project licensing, game rights, and third-party credits, see
[LEGAL.md](LEGAL.md).

## Extract character stats

Requires Python 3.10 or later and Bash. From the repository root, run:

```sh
./rc2t extract-json
```

This reads `input/Rolan's Curse II (USA).gb` and writes
`output/<rom-sha256>.json`, using the lowercase SHA-256 hash of the ROM bytes
as the filename. A different ROM revision therefore gets a different output
file.
Alternatively, supply a ROM or a complete 16-byte-per-row `.hex` dump produced
by `xxd` or PowerShell `Format-Hex`:

```sh
./rc2t extract-json "input/Rolan's Curse II (USA).gb.hex"
```

The command reads the mapped bytes from the supplied input, so modified stat
values are reflected in the output. It checks the ROM size and header, not a
fixed hash or expected stat values. Arrays contain decimal byte values for
levels 1 through 16; the mappings and their unresolved interpretations are
documented in [the ROM map](docs/rom-map.md). The output file is overwritten
if a file with that ROM hash already exists.

## Disassemble a Game Boy ROM

Decode a ROM into an RGBDS-style assembly listing:

```sh
./rc2t decompile
./rc2t decompile path/to/game.gb output/game.asm
./rc2t decompile path/to/game.gb output/range.asm --start 0x100 --end 0x200
```

The listing defaults to `output/<rom-basename>.asm`. ROM bytes are decoded
linearly as LR35902 instructions, with sections split at 16 KiB ROM-bank
boundaries. Since a ROM contains both executable code and data, this simple
disassembler cannot identify code/data boundaries or reconstruct the original
high-level source; use `--start` and `--end` to focus on known code ranges.
Illegal CPU opcodes are emitted as `DB` directives. The `disassemble` command
is an alias for `decompile`.

For ROMs matching the size, title, and cartridge header of Rolan's Curse II
(USA), the listing also comments documented sprites, graphics, text, tables,
header fields and code landmarks from [the ROM map](docs/rom-map.md) and
[known text](docs/known-text.md). Ranges are physical offsets with exclusive
ends; one-byte code landmarks identify a location, not the extent of a routine.
Inferred or tentative identifications are marked. These checks do not
verify the ROM hash, so modified ROMs or other revisions may not match the
documented layout. Comments mark blocks that begin inside an instruction or
continue into a selected range without changing the linear disassembly.

### Recompile an assembly listing

The recompiler uses Python 3.10 or later and requires no external assembler.
Copy or move the `.asm` file into `input/`, then run:

```sh
./rc2t recompile
```

By default this reads `input/Rolan's Curse II (USA).asm` and writes
`output/Rolan's Curse II (USA) (recompiled).gb`. You can also supply another
filename in `input/` or an explicit path to an `.asm` file:

```sh
./rc2t recompile "other game.asm"
./rc2t recompile path/to/game.asm
```

The assembler uses the instructions and
directives, not the byte comments, so edits to the source affect the ROM.
It supports the LR35902 instructions, `DB` byte directives and fixed-address
`ROM0`/`ROMX` sections emitted by the disassembler, with numeric operands.
It is not a general RGBDS assembler: labels, macros, and other directives and
expressions are not supported. Unsupported syntax and overlapping or
out-of-bank sections produce errors. No header or checksum is automatically
changed. Gaps and incomplete ROM banks are zero-padded, with a minimum output
size of 32 KiB; listings made with `--start` or `--end` do not reconstruct the
omitted bytes. Regenerate listings made by older versions of the disassembler
before recompiling them.

## Render graphics as tile grids, sprites, and portraits

Rendering requires Pillow 10.0 or later. Install it with:

```sh
python3 -m pip install 'Pillow>=10.0'
```

To render the entire default ROM (including non-graphics data) to
`output/graphics.png`, run:

```sh
./rc2t render-graphics
```

To render from a start offset through the end of the ROM, run:

```sh
./rc2t render-graphics 0x8050
```

This also writes to `output/graphics.png`.

To combine a different number of tiles into each rendered image, pass the
tile grid as `WIDTHxHEIGHT` after the start and end offsets:

```sh
./rc2t render-graphics 0x880E 0x900E 4x4
./rc2t render-graphics 0x9106 0xB566 1x2
```

The dimensions mean tiles across by tiles down. Explicit grids are assembled
row-major, use four images per row by default, and can be any positive size.
Without an explicit grid, the existing 2×2 column-first sprite layout remains
the default. You can also pass the grid as `--tile-grid WIDTHxHEIGHT` when
providing an output path or invoking the Python script directly.

To render an inclusive-start, exclusive-end ROM byte range as a sheet of
assembled sprites, pass the range and output path:

```sh
./rc2t render-graphics 0x9106 0xB566 output/hero-sprites.png
```

Pass `--highlight-known` to shade documented graphics in blue, documented text
in yellow, and documented lookup or stat tables in green, making unmapped tiles easier to spot. Known pixels keep their relative
brightness, so dark, mid, and light pixels stay distinguishable:

```sh
./rc2t render-graphics --highlight-known
./rc2t render-graphics 0x9100 0x9200 output/scan.png --highlight-known
```

Decode the whole ROM through the documented character table into one string (`output/rom-text.txt`):

```sh
./rc2t render-text
```

Dump all identified text ranges, including overlapping fragments, credits,
name lists, alphabet tables, and unclassified control-byte runs:

```sh
./rc2t dump-text
./rc2t dump-text path/to/game.gb output/known-text.txt
```

The default output is `output/known-text.txt`. Each line has the format
`0xSSSSS-0xEEEEE : decoded text`, using zero-padded physical ROM offsets;
the end is exclusive. Exact duplicate ranges are listed once, but distinct
overlapping ranges are kept. Output follows the character table and unknown
byte placeholders used by `render-text`; the ASCII cartridge title is decoded
as ASCII, with its non-printable padding shown as a placeholder. Name lists
are raw decoded bytes, including unidentified separators. The ROM must match
the Rolan's Curse II (USA) size and header;
a complete `.hex` dump is also accepted. Existing output is overwritten.
Update the range list in `bin/dump_text.py` when documenting new text.

The highlighted physical-ROM ranges follow the graphics and text documented in
[the ROM map](./docs/rom-map.md) and [the known-text list](./docs/known-text.md). Highlighting follows the known byte ranges,
even when a range starts or ends inside a rendered tile. A pixel is blue when
its color data comes only from bytes inside a known graphics range, yellow
when it comes only from a known text range, and green when it comes only from a
known lookup-table range. If only one of a tile row's two
bitplane bytes is known, only pixels attributable to that byte are shaded.
Portrait, sprite, and custom tile-grid layouts all use the same ranges.

Offsets are physical ROM offsets. Each 16-byte tile is decoded as 8×8 pixels;
every four consecutive tiles are assembled into one 16×16 sprite in
top-left, bottom-left, top-right, bottom-right input order. This column-first
layout was observed in the Hero sprite and is applied uniformly to the entire
range as an experiment. Any final group with fewer than four tiles is rendered
with missing quadrants left blank. A one-pixel gutter separates sprites.
The selected range may end at any byte, but must contain at least one byte. If
it ends in the middle of a pixel row, the missing byte is zero-padded; missing
rows in the final 16-byte tile are left blank.
The rendered sheet labels each column along the top with the address where its
first cel begins, and each row along the left with the address where its first
cel begins. Each cel uses 64 bytes; each row's left-axis address advances by
one full row (`columns * 64` bytes).

Use `--mode portraits` to render complete 32×32 portrait blocks with the
POW-screen palette. Each block is `0x100` bytes containing a row-major 4×4
grid of 8×8 tiles. For example, to render the eight portraits beginning at
`0x880E`:

```sh
./rc2t render-graphics 0x880E 0x900E 4x4 --mode portraits
```

Portrait mode uses four images per row by default and labels each portrait with
its starting ROM offset. The range must contain a whole number of portraits;
the command above writes to `output/graphics.png`.

Use `--stacked-glyphs` for the stacked 1bpp character tiles documented at
`0xB986-0xBB05`. Each 16-byte tile is drawn as two 8×8 glyphs, top then bottom,
with set bits as background and clear bits as black ink:

```sh
./rc2t render-graphics 0xB986 0xBB06 output/glyphs.png --stacked-glyphs
```

Stacked-glyph mode cannot be combined with `--tile-grid` or `--mode`.

The default sprite sheet uses 16 sprites per row. Its grayscale palette
displays transparent color index 0 as black, while the inverted
non-transparent palette displays index 3 as white. Portrait mode uses the
grayscale palette observed on the POW screen.
The output extension can be `.png`, `.jpg`, or `.jpeg`. Options include
`--input` for a different ROM or full hex dump, `--columns` for images per
row, `--scale` for nearest-neighbor enlargement, and `--highlight-known` to
mark documented sprite areas. The specified output file is overwritten if it
exists. You can also invoke
`python3 bin/render_graphics.py` directly with the same range, output path,
and options. When run without a range, `./rc2t render-graphics` applies the
default sprite grouping to the entire ROM, including non-graphics data.

## Hack the ROM

`./rc2t hack` edits an in-progress copy of the ROM in `working/`, named
`Rolan's Curse II (USA) (hack in progress).gb`. Every `hack` subcommand creates
that copy from `input/` first if it does not exist.

```sh
./rc2t hack reset     # delete the in-progress copy and replace it with a fresh copy of input/
./rc2t hack clear     # delete the in-progress copy
./rc2t hack finalize  # copy the in-progress copy to output/ and write an IPS patch
./rc2t hack swap-char-sprite hero pit  # edit the in-progress copy in place
./rc2t hack dump-art title   # write working/title-art.png from the in-progress copy
./rc2t hack read-art title   # apply an edited working/title-art.png to the in-progress copy
```

Character names for `swap-char-sprite` are `hero`, `pit`, `lane`, `kyle`,
`jude`, `lee`, `lora`, and `zold`. The swap exchanges the nine standard poses,
defeat sprite, level-up face, and POW-screen portrait of the two characters.

`dump-art title` writes the title screen's logo above the START/CONTINUE line to
`working/title-art.png`. The image is 160×104 pixels, the top 13 rows of the
Game Boy screen, and the art is arranged as it appears on screen. The four
shades are the title screen's palette (BGP `0x2D`): index 0 is light gray, 1 is
black, 2 is dark gray, and 3 is white. The menu cursor, the START and CONTINUE
text, and the copyright line are not part of the image.

`read-art title` reads `working/title-art.png` and writes the tiles back into
the in-progress copy. The image must be exactly 160×104 pixels. Each pixel is
mapped to the nearest of the four shades. Some tiles appear in more than one
cell, such as the blank filler tile `0x30`, so every cell that uses such a tile
must have the same pixels. Otherwise `read-art` fails and changes nothing.

Each applied hack is recorded in `working/hacks.txt`, one line per hack. `reset`
and `clear` delete this file, and `swap-char-sprite` and `read-art` append to it.
`finalize` does not copy it to `output/`.

`finalize` writes `output/Rolan's Curse II (USA) (hack finalized).gb` and
`output/Rolan's Curse II (USA) (hack finalized).ips`. The patch is a diff from
the original `input/` ROM to the finalized ROM, and it replaces any previous
finalized files. The `working/` directory is ignored by git.