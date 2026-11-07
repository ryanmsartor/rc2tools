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
