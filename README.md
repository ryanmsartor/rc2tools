# rc2tools
A collection of tools for hacking Rolan's Curse 2 for Game Boy

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

Pass `--highlight-known` to paint documented graphics blue, making unmapped
tiles easier to spot:

```sh
./rc2t render-graphics --highlight-known
./rc2t render-graphics 0x9100 0x9200 output/scan.png --highlight-known
```

The highlighted physical-ROM ranges follow the graphics documented in
[the ROM map](./docs/rom-map.md). Highlighting follows the known byte ranges,
even when a range starts or ends inside a rendered tile. A pixel is blue when
its color data comes only from bytes inside a known range; if only one of a
tile row's two bitplane bytes is known, only pixels attributable to that byte
are blue. Portrait, sprite, and custom tile-grid layouts all use the same
ranges.

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

## Swap character sprites

To create an IPS patch that swaps two characters' nine standard poses, defeat
sprite, level-up face, and POW-screen portrait, run:

```sh
./rc2t swap-character-sprite hero pit
```

This writes `output/swap-hero-pit-sprites.ips`, using the default ROM. Character
names are `hero`, `pit`, `lane`, `kyle`, `jude`, `lee`, `lora`, and `zold`.
When `input/Rolan's Curse II (USA).gb` is present and valid, the command also
writes the fully patched ROM to `output/Rolan's Curse II (USA) (hero-pit).gb`.
