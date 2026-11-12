# rc2tools
A collection of tools for hacking Rolan's Curse 2 for Game Boy

For project licensing, game rights, and third-party credits, see
[LEGAL.md](LEGAL.md).

## Requirements and dependencies

- Python 3.10 or later.
- Bash, to run the `rc2t` and `rc2h` launchers.
- Pillow 10.0 or later, required by `render-graphics` and by `dump-art` and
  `inject-art`. Install it with:

  ```sh
  python3 -m pip install 'Pillow>=10.0'
  ```

- A copy of Rolan's Curse II (USA) in `input/` as `Rolan's Curse II (USA).gb`
  (131,072 bytes). These tools were built and tested against this exact ROM
  version. Use these identifiers to confirm you have this file:
  - SHA-256: `cf3f8f41498cdd32f5b3ee0cdccde1901b073798f3edac1a7d9ccc0141cb16be`
  - MD5: `27f2c99b13cbdb5a5be4afce87b9039b`
  Other versions of Rolan's Curse II may work, but are untested and not guaranteed to be compatible.

- Optional: `xxd` or PowerShell `Format-Hex`, to create the `.hex` dump that `dump-stats` can read.

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
in yellow, documented lookup or stat tables in green, and the title-screen tilemap, its tables, and the routines that write and copy them in purple, making unmapped tiles easier to spot. Known pixels keep their relative
brightness, so dark, mid, and light pixels stay distinguishable:

```sh
./rc2t render-graphics --highlight-known
./rc2t render-graphics 0x9100 0x9200 output/scan.png --highlight-known
```

Decode the whole ROM through the documented character table into one string (`output/rom-text.txt`):

```sh
./rc2t render-text
./rc2t render-text --wrap
./rc2t render-text --known-only
./rc2t render-text --known-only --wrap
./rc2t render-text --wrap --known-only --omit-sprites
```

Pass `--wrap` to insert line breaks every 64 characters, prefixed with the
zero-padded ROM byte address (for example, `0x00000: `).
Pass `--known-only` to show `_` for unknown or undefined bytes while retaining
known mappings such as `+` for line breaks and `#` for end of string.
Pass `--omit-sprites` to replace each byte in the documented graphics ranges
(the blue `--highlight-known` ranges, including glyphs) with `%`. Outside
those ranges, `%` can also be the normal placeholder for an unknown byte; use
`--known-only` to distinguish it. The options can be combined.

Dump all identified text ranges, including text fragments, credits,
name lists, the retained alphabet table, and unclassified control-byte runs:

```sh
./rc2h dump-text
./rc2h dump-text path/to/game.gb
```

The command writes `working/strings.txt`; it is not part of `rc2t`. Each line
has the format `0xSSSSS-0xEEEEE : text`, using zero-padded physical ROM
offsets and exclusive end addresses. The ranges do not overlap. In this
editable notation, `_` represents byte `0xFE`, `=` represents `0x26`, and `-`
represents `0x2B`; a regular space represents `0xB2`, except in the two
documented `0x30` space ranges. The ASCII cartridge title is included.
The ROM must match the Rolan's Curse II (USA) size and header; a complete
`.hex` dump is also accepted. Existing output is overwritten. Update the range
list in `bin/dump_text.py` when documenting new text.

After editing `working/strings.txt`, inject its segments into a ROM:

```sh
./rc2h inject-text
./rc2h inject-text path/to/game.gb
```

`inject-text` writes `working/injected.gb`; it reads the same default ROM as
`dump-text` unless a ROM path is supplied. Every documented range must appear
exactly once in the strings file. Shorter replacements are padded at the end
with the applicable space byte (`0xB2` by default, `0x30` in the two
exception ranges, and ASCII space for the cartridge title). An overlong
replacement or invalid strings file fails before the output ROM is written.
The error reports the range and, for overlong segments, the maximum and
attempted character counts. Text characters are restricted to those present in
the non-title ranges in the dump of the base input ROM; the cartridge title is
excluded from character identity validation but still obeys the range length.
Invalid-character errors identify the character and range and print the dense
allowed-character list. The ROM header and global checksums are recalculated.

The highlighted physical-ROM ranges follow the graphics and text documented in
[the ROM map](./docs/rom-map.md) and [the known-text list](./docs/known-text.md). Highlighting follows the known byte ranges,
even when a range starts or ends inside a rendered tile. A pixel is blue when
its color data comes only from bytes inside a known graphics range, yellow
when it comes only from a known text range, and green when it comes only from a
known lookup-table range, and purple when it comes only from a known structure
range (the title tilemap, its tables, and the routines that write and copy them). If only one of a tile row's two
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

Use `--compare` to render the selected range from the input ROM and the
in-progress working ROM side by side, input on the left and working on the
right. Each panel has its own address axes. Bytes identical between the ROMs
are highlighted in bluescale; different bytes are highlighted in redscale.
This option
requires an existing `working/Rolan's Curse II (USA) (hack in progress).gb`
and cannot be combined with `--highlight-known`. Other render options, such as
`--mode`, `--tile-grid`, `--columns`, and `--scale`, still apply to both panels.

The default sprite sheet uses 16 sprites per row. Its grayscale palette
displays transparent color index 0 as black, while the inverted
non-transparent palette displays index 3 as white. Empty cells, such as the
missing quadrants of an incomplete sprite, are filled with lilac so they are
not confused with real white data. Portrait mode uses the grayscale palette
observed on the POW screen.
The output extension can be `.png`, `.jpg`, or `.jpeg`. Options include
`--input` for a different ROM or full hex dump, `--columns` for images per
row, `--scale` for nearest-neighbor enlargement, and `--highlight-known` to
mark documented sprite areas. The specified output file is overwritten if it
exists. You can also invoke
`python3 bin/render_graphics.py` directly with the same range, output path,
and options. When run without a range, `./rc2t render-graphics` applies the
default sprite grouping to the entire ROM, including non-graphics data. That
sheet is split into one block per 16 KiB ROM bank, labeled `Bank N` and
separated by a horizontal rule. Each bank starts a new row and has its own
address labels. Ranges that span several banks use the same layout.

## Hack the ROM

`./rc2t hack` edits an in-progress copy of the ROM in `working/`, named
`Rolan's Curse II (USA) (hack in progress).gb`. Every `hack` subcommand creates
that copy from `input/` first if it does not exist.

`./rc2h` is a shorthand for `./rc2t hack` and accepts the same arguments.
It also provides `dump-text` to write the selected ROM strings to
`working/strings.txt`.
Run `./rc2h` without arguments, or with `h`, `help`, `-h`, `-help`, `--h`,
or `--help`, to see its commands.

```sh
./rc2h reset                           # delete the in-progress copy and replace it with a fresh copy of input/
./rc2h clear                           # delete the in-progress copy
./rc2h finalize [tag]                  # copy the hack, IPS patch, and hack log to output/
./rc2h swap-char-sprite hero pit       # edit the in-progress copy in place
./rc2h dump-art <name>                 # export named art to working/<name>-art.png
./rc2h inject-art <name>               # apply working/<name>-art.png to the in-progress copy
./rc2h dump-font                       # synonym for dump-art font
./rc2h inject-font                     # synonym for inject-art font
./rc2h dump-stats [rom-or-hex]         # write character stat arrays to working/stats.txt
./rc2h inject-stats                    # apply modified arrays from working/stats.txt
```

Both `dump-art` and `inject-art` accept the same names:

- `title`
- `hero`, `pit`, `lane`, `kyle`, `jude`, `lee`, `lora`, or `zold`
- `npc`
- `abilities`
- `font`
- `all`

The `all` targets process the title first, then the characters, NPC art,
ability icons, and font.
They use the same files and behavior as each individual command: dumping overwrites
existing PNGs, and injection records each image that changes ROM bytes in `hacks.txt`.
Processing stops on the first error; earlier dumps or injections remain in
place.

Each target exports one PNG to `working/` at native pixel size, and injection reads
that PNG back. Red marks separators and empty space, which injection ignores. Each
pixel is mapped to the nearest shade. If the image is not the expected size,
injection fails and changes nothing.

`dump-art npc` exports the town NPC frames and the NPC and non-boss enemy sprites as
one sheet. Injection writes each edited egghead or dog frame to both of its identical
copies, so the copies stay the same.

`dump-art font` (also `dump-font`) exports the font glyphs as one sheet. Injection
thresholds each pixel to ink or background. The font is included in `dump-art all`
and `inject-art all`.

`dump-stats` writes the character stat arrays to `working/stats.txt`, one array per
line, with values for levels 1 through 16. It reads the in-progress copy by default.
Pass a ROM (`.gb`) or a complete 16-byte-per-row `.hex` dump to read another file
instead. It checks the ROM size and header, not a fixed hash or expected stat values.
It does not record anything in `hacks.txt`. The mappings and their unresolved
interpretations are documented in [the ROM map](docs/rom-map.md).

`inject-stats` reads `working/stats.txt`, accepting whitespace around names,
punctuation, and values, including line breaks within arrays. Each recognized array
must have 16 decimal byte values (0–255); duplicate recognized names and malformed
entries are errors. Unknown array names are printed and ignored. Omitted arrays
remain unchanged. Arrays matching the original `input/` ROM are skipped even if
the working ROM differs; arrays already matching the working ROM are also skipped.
Each array actually changed is recorded with its new values in `hacks.txt`.
To restore stock values, use `reset` (which also discards other working changes).
Some stat array names have been renamed; older files must be updated before injection
because old names are reported as unknown and ignored. Re-dump only if replacing
any edits in the existing file is acceptable.

Character names for `swap-char-sprite` are `hero`, `pit`, `lane`, `kyle`,
`jude`, `lee`, `lora`, and `zold`. The swap exchanges the nine standard poses,
defeat sprite, level-up face, and POW-screen portrait of the two characters.

`dump-art <character>` exports one character's sprites, including its poses, POW
portrait, defeat sprite, level-up face, and attack and particle sprites. `inject-art
<character>` writes them back.

`dump-art abilities` exports the in-UI weapon and ability icons. `inject-art
abilities` writes them back.

`dump-art title` exports the title screen logo, the art above the START/CONTINUE
line. The menu cursor, the START and CONTINUE text, and the copyright line are not
part of the image, and the blank margin around the logo stays untouched in the ROM.

`inject-art title` writes the logo back into the in-progress copy. Injection fails
and changes nothing if the image is the wrong size, or if tiles that appear in more
than one place disagree.

Each applied hack is recorded in `working/hacks.txt`, one line per hack. `reset`
and `clear` delete this file, and `swap-char-sprite`, `inject-art`, `inject-font`,
and `inject-stats` append to it. Injection commands log only changes to ROM bytes.

`finalize` writes `output/Rolan's Curse II (USA) (hack finalized).gb` and
`output/Rolan's Curse II (USA) (hack finalized).ips`, and a copy of the log at
`output/hack finalized.txt`. The patch is a diff from
the original `input/` ROM to the finalized ROM, and it replaces any previous
finalized files. The `working/` directory is ignored by git.
An optional tag replaces `hack finalized` in all three output filenames. For
example, `./rc2h finalize "my hack"` writes
`output/Rolan's Curse II (USA) (my hack).gb`, the matching `.ips` file, and
`output/my hack.txt`.
Quote tags containing spaces. Tags must be nonempty and cannot contain path
separators or control characters; existing files with the same tag are replaced.