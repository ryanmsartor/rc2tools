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

## Render graphics as assembled sprites

Rendering requires Pillow 10.0 or later. Install it with:

```sh
python3 -m pip install 'Pillow>=10.0'
```

To render the entire default ROM (including non-graphics data) to
`output/graphics.png`, run:

```sh
./rc2t render-graphics
```

To render an inclusive-start, exclusive-end ROM byte range as a sheet of
assembled sprites, pass the range and output path:

```sh
./rc2t render-graphics 0x9106 0xB566 output/hero-sprites.png
```

Offsets are physical ROM offsets. Each 16-byte tile is decoded as 8×8 pixels;
every four consecutive tiles are assembled into one 16×16 sprite in
top-left, bottom-left, top-right, bottom-right input order. This column-first
layout was observed in the Hero sprite and is applied uniformly to the entire
range as an experiment. Any final group with fewer than four tiles is rendered
with missing quadrants left blank. A one-pixel gutter separates sprites.

The default sheet uses 16 sprites per row. Its grayscale palette displays
transparent color index 0 as black, while the inverted non-transparent
palette displays index 3 as white.
The output extension can be `.png`, `.jpg`, or `.jpeg`. Options include
`--input` for a different ROM or full hex dump, `--columns` for sprites per
row, and `--scale` for nearest-neighbor enlargement. The specified output
file is overwritten if it exists. You can also invoke
`python3 bin/render_graphics.py` directly with the same range, output path,
and options. When run without a range, `./rc2t render-graphics` applies this
grouping to the entire ROM, including non-graphics data.
