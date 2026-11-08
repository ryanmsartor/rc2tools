# Rolan's Curse II (USA) ROM map

This is an initial, evidence-based map of the ROM. ROM file offsets and CPU addresses are distinct, especially in the banked window. The separate [save file analysis](./save-file-analysis.md) documents observations from a hex-dumped `.sav` file; its labels are not ROM or CPU addresses.

## ROM and cartridge layout

The source examined here is `input/Rolan's Curse II (USA).gb` (131,072 bytes). The header bytes are at their standard Game Boy header offsets:

| ROM offset | Bytes | Meaning |
|---|---|---|
| `0x0100` | `00 C3 50 01` | Entry sequence: `NOP`, then jump to CPU address `0x0150`. |
| `0x0104-0x0133` | Nintendo logo data | Header logo field. |
| `0x0134-0x0143` | `ROLAN'S CURSE 2` and padding | Cartridge title. |
| `0x0143` | `00` | Non-CGB header flag. |
| `0x0147` | `06` | Cartridge type: MBC2 with battery. |
| `0x0148` | `02` | ROM size: 128 KiB (8 banks of 16 KiB). |
| `0x0149` | `00` | Header RAM-size code. MBC2 has its own small built-in RAM; see below. |

With MBC2, the CPU sees a fixed ROM window at `0x0000-0x3FFF` and a banked ROM window at `0x4000-0x7FFF`. The cartridge's RAM is the small MBC2 nibble RAM at `0xA000-0xA1FF` (512 four-bit cells); it is not a general 8 KiB SRAM. MBC2 bank selection is controlled by writes in the `0x2000-0x3FFF` range. Keep a bank number alongside any CPU address in `0x4000-0x7FFF` when documenting code or data there.

## CPU address spaces

These are hardware address windows, not interpretations of game variables:

| CPU address range | Hardware use |
|---|---|
| `0x0000-0x7FFF` | Cartridge ROM and MBC control writes. |
| `0x8000-0x9FFF` | Video RAM (tile/map data while in use). |
| `0xA000-0xBFFF` | Cartridge RAM window; for this MBC2 cartridge, only `0xA000-0xA1FF` is the MBC2 RAM area. |
| `0xC000-0xDFFF` | Work RAM. `0xE000-0xFDFF` echoes this region. |
| `0xFE00-0xFE9F` | Object attribute memory (sprite attributes). |
| `0xFF00-0xFF7F` | Hardware I/O registers. |
| `0xFF80-0xFFFE` | High RAM. |
| `0xFFFF` | Interrupt enable register. |

## Confirmed code landmarks

Offsets below are ROM file offsets that are also CPU addresses in the fixed bank:

| ROM offset / CPU address | Observation |
|---|---|
| `0x0000-0x003F` | Repeated short instruction sequences (`LD HL,imm16; ADD HL,DE; RET`) with immediate values 0 through 7. Their callers and purpose are not identified. |
| `0x0040` | VBlank vector saves AF/BC/DE/HL and jumps to `0x039C`. |
| `0x0048` | LCD STAT vector jumps to `0x0594`. |
| `0x0050`, `0x0058`, `0x0060` | Timer, serial, and joypad vectors contain `RETI` (`0xD9`). |
| `0x0100` | Reset entry jumps to `0x0150`. |
| `0x0150` | Startup begins. It calls `0x0C95`, initializes SP to `0xCBFF`, clears `0xFF80-0xFFFE`, and clears work RAM `0xC000-0xDFFF`. It also initializes other locations and calls routines at `0x0C7D`, `0x0CA2`, `0x0CA7`, and `0x0CB6`. |
| `0x01A4-0x01AD` | Startup writes `1` to `0x3FFF` (selecting ROM bank 1), then calls CPU address `0x5586`. In this call context that is physical ROM offset `0x05586`. |

These are landmarks, not a complete disassembly. In particular, routine names and responsibilities have not yet been established. Other calls in startup include `0x047C`, `0x04F6`, and `0x0511`; these are candidates for the next control-flow tracing pass.

## Bank inventory

The ROM has eight physical banks. The character tables described below are in bank 5. A graphics/tile-data region and related descriptors have been tentatively identified in bank 2; details and confidence are documented below. Other banks are not yet reliably classified by subsystem.

| Physical bank | ROM file offsets |
|---:|---|
| 0 | `0x00000-0x03FFF` |
| 1 | `0x04000-0x07FFF` |
| 2 | `0x08000-0x0BFFF` |
| 3 | `0x0C000-0x0FFFF` |
| 4 | `0x10000-0x13FFF` |
| 5 | `0x14000-0x17FFF` |
| 6 | `0x18000-0x1BFFF` |
| 7 | `0x1C000-0x1FFFF` |

The title is the only clear long ASCII string found in the initial string scan. Most game text, graphics, maps, and audio are likely stored as encoded or packed binary, so a plain-text scan cannot locate them. Some early bank bytes look table-like (for example, bank 2 starts with little-endian values `0x404E`, `0x408E`, `0x40CE`), but those are not yet proven pointers or assigned to any asset.

## Graphics and tile data (preliminary)

The following identification is based on decoding bytes as Game Boy 2bpp tiles and matching a Hero sprite in `docs/screenshot_1.png`. The tile match confirms the format and the listed sprite tiles; the surrounding descriptor tables look like graphics transfer lists, but their consuming code has not been traced. Treat their field meanings as tentative.

All source ranges below are physical ROM offsets in **bank 2**. For a CPU source pointer in the banked window, add `0x4000` to obtain the physical offset; conversely, subtract `0x4000` from the physical offset to obtain the CPU address with bank 2 selected. Each uncompressed 2bpp tile is 16 bytes (8×8 pixels).

### Hero sprite tiles

The four tiles matching the screenshot are consecutive 16-byte tiles at `0x9106-0x9145` (inclusive). Their file order is column-first, not row-first:

| Screen position | Physical ROM range | CPU address (bank 2 selected) |
|---|---|---|
| Top-left | `0x9106-0x9115` | `0x5106-0x5115` |
| Bottom-left | `0x9116-0x9125` | `0x5116-0x5125` |
| Top-right | `0x9126-0x9135` | `0x5126-0x5135` |
| Bottom-right | `0x9136-0x9145` | `0x5136-0x5145` |

Thus the on-screen arrangement is:

| | Left | Right |
|---|---|---|
| Top | `0x9106` | `0x9126` |
| Bottom | `0x9116` | `0x9136` |

The top-right tile at `0x9126` was an exact 2bpp match; the other three tiles also match the screenshot's opaque pixels when transparent tile color 0 is allowed to show the background through. The top-left tile bytes also recur at `0x9146`; the four addresses above are supported as one sprite by the consecutive tile layout and the matches of all four quadrants.

### Main bank-2 tile-data batch

A sequence of eight 8-byte records at `0x9024-0x9063` appears to contain a length, a bank-2 CPU source address, a VRAM destination (`0x8000` in each record), and two zero bytes. Interpreting those fields this way yields eight contiguous source ranges:

| Record ROM offset | Length | CPU source (bank 2) | Physical ROM range | Tile count |
|---|---:|---:|---|---:|
| `0x9024` | `0x0500` | `0x5106` | `0x9106-0x9605` | 80 |
| `0x902C` | `0x0440` | `0x5606` | `0x9606-0x9A45` | 68 |
| `0x9034` | `0x0380` | `0x5A46` | `0x9A46-0x9DC5` | 56 |
| `0x903C` | `0x0540` | `0x5DC6` | `0x9DC6-0xA305` | 84 |
| `0x9044` | `0x04C0` | `0x6306` | `0xA306-0xA7C5` | 76 |
| `0x904C` | `0x0500` | `0x67C6` | `0xA7C6-0xACC5` | 80 |
| `0x9054` | `0x0420` | `0x6CC6` | `0xACC6-0xB0E5` | 66 |
| `0x905C` | `0x0480` | `0x70E6` | `0xB0E6-0xB565` | 72 |

Together these occupy `0x9106-0xB565` inclusive (`0x2460` bytes, 582 tiles). The sprite's four tiles are at the start of the first range. The ranges are multiples of 16 bytes and meet exactly end-to-start; this supports, but does not by itself prove, their interpretation as tile data.

### Related graphics descriptors and source ranges

The 6-byte records at `0x9064-0x90B1` appear to encode a byte length, bank-2 CPU source address, and VRAM destination. A zero word at `0x90B2` terminates this list. The source pointers resolve to the main batch above or to these additional bank-2 ranges:

| CPU source (bank 2) | Physical ROM range | Length |
|---|---|---:|
| `0x7606` | `0xB606-0xB705` | `0x0100` |
| `0x7706` | `0xB706-0xB725` | `0x0020` |
| `0x7726` | `0xB726-0xB885` | `0x0160` |
| `0x7886` | `0xB886-0xB985` | `0x0100` |
| `0x7986` | `0xB986-0xBB05` | `0x0180` |

This puts related referenced data as far as `0xBB05`; it is not evidence that all graphics in the game end there. Additional zero-terminated 6-byte-record lists occur at `0x90B4-0x90E3` and `0x90E6-0x9103`. They reuse source pointers from the ranges above and the main batch. Some 16-bit first fields in these lists have their high bit set (for example, `0x8180` and `0x80A0`), so the simple length interpretation may not apply to every record. The record layouts, flags, and actual loader behavior remain unverified.

The `./rc2t render-graphics` command groups every four consecutive tiles in a supplied range into a 16×16 image, using the observed column-first order (top-left, bottom-left, top-right, bottom-right). For example, `./rc2t render-graphics 0x9106 0xB566 output/graphics.png` renders the main batch as an experimental sprite sheet. This uniform grouping is intended to help spot other sprites; it does not reconstruct the game's actual sprite/tile maps or palettes. An incomplete final group is padded with blank quadrants.

## Character stat and ability tables

The right-margin annotations in [rc2.hex](./rc2.hex) identify these tables by matching values to known character stats at each level. All 8,192 rows of the dump were compared with the local ROM and their bytes matched. These are annotated identifications, not yet verified by tracing the game's table-reading code. All ranges below are inclusive physical ROM offsets in **bank 5**; subtract `0x10000` for the CPU address when bank 5 is selected.

Each listed table has 16 entries, ordered as levels 1 through 16 according to the annotations and the repeating layout. Values are raw hexadecimal bytes, not decimal: e.g. `1E` is decimal 30. For multi-byte records, a slash separates fields within one level; spaces separate successive levels. The byte order and field labels follow the margin notes; uncertain fields are retained as such.

The `./rc2t extract-json` command reads these ranges from the input ROM and writes `output/<rom-sha256>.json`, where the lowercase SHA-256 is computed from the ROM bytes (also when the input is a hex dump). It also accepts a full ROM hex dump as an argument. Its `characters` object groups HP, MP, and ability field arrays by character; array index 0 corresponds to level 1. Each ability field is a separate array. `additional_tables` contains the standalone Zold A damage table and two paired-byte lookup tables described below. The repeated bytes in Lane's healing and Lora's heal are named `unknown_1` and `unknown_2` because their roles are uncertain; other `unknown` fields are likewise unidentified. The tentative table boundaries and field interpretations below also apply to the JSON.

### HP and MP by level

These are contiguous single-byte tables: eight HP tables followed by eight MP tables. For example, Hero HP level 1 is `0x1E` at `0x17065`; level 16 is `0xFF` at `0x17074`.

| Character | Stat | ROM range | Values for levels 1-16 (hex) |
|---|---|---|---|
| Hero | HP | `0x17065-0x17074` | `1E 2D 3C 4B 5A 69 78 87 96 A5 B4 C3 D2 E1 F0 FF` |
| Pit  | HP | `0x17075-0x17084` | `28 32 3C 46 50 5A 64 6E 73 78 7D 82 87 8C 91 96` |
| Lane | HP | `0x17085-0x17094` | `3C 4B 5A 69 78 82 8C 96 9D A4 AB B2 B9 BE C3 C8` |
| Kyle | HP | `0x17095-0x170A4` | `50 54 58 5C 64 6C 74 7C 88 94 A0 AC BC CC DC F0` |
| Jude | HP | `0x170A5-0x170B4` | `32 37 3C 41 46 4B 50 55 5A 5F 64 69 6E 73 78 82` |
| Lee  | HP | `0x170B5-0x170C4` | `78 82 8C 96 A0 A8 B0 B8 C0 C6 CC D0 D4 D6 D8 DC` |
| Lora | HP | `0x170C5-0x170D4` | `50 5A 64 78 82 8C 96 AA B4 BE C8 D2 DC E6 F0 FF` |
| Zold | HP | `0x170D5-0x170E4` | `B4 B9 BE C3 C8 CD D2 D7 DC E1 E6 EB F0 F5 FA FF` |
| Hero | MP | `0x170E5-0x170F4` | `0A 14 1E 28 32 3C 46 50 5A 64 6E 78 82 8C 96 A0` |
| Pit  | MP | `0x170F5-0x17104` | `28 2E 34 3A 40 46 4C 52 56 5C 62 68 6E 74 7A 82` |
| Lane | MP | `0x17105-0x17114` | `14 19 1E 23 28 2D 32 37 3C 41 46 50 5A 64 6E 78` |
| Kyle | MP | `0x17115-0x17124` | `28 32 3C 46 50 5A 64 6E 73 78 7D 82 87 8C 91 96` |
| Jude | MP | `0x17125-0x17134` | `64 66 68 6C 72 78 80 88 8E 96 A0 AA B4 BE C8 C8` |
| Lee  | MP | `0x17135-0x17144` | `14 1A 20 26 2C 32 38 3E 46 4E 56 5E 66 6E 76 82` |
| Lora | MP | `0x17145-0x17154` | `50 5A 64 6E 73 78 7D 82 87 8C 91 96 9B A0 AA B4` |
| Zold | MP | `0x17155-0x17164` | `32 3C 46 50 5A 64 6E 78 82 8C 96 A0 AA B4 BE C8` |

### Attacks and abilities by level

| Character / ability | Fields in byte order | ROM range | Values for levels 1-16 (hex) |
|---|---|---|---|
| Hero A | damage | `0x15449-0x15458` | `07 0F 17 1F 27 2F 37 3F 47 4F 57 5F 67 6F 77 7F` |
| Hero B | cost / range / damage | `0x15459-0x15488` | `01/09/0F 01/09/10 01/09/11 01/09/12 01/0A/14 01/0A/16 01/0A/18 01/0B/1C 01/0B/20 01/0B/24 01/0C/28 01/0C/2C 01/0C/32 01/0D/38 01/0D/3E 00/0D/44` |
| Pit dagger | range / damage | `0x154AD-0x154CC` | `08/01 08/02 09/04 09/06 0A/08 0A/0A 0B/0E 0B/12 0C/16 0C/1A 0D/1E 0D/22 0E/26 0E/2A 0F/2E 0F/32` |
| Pit boomerang | range / damage | `0x154DF-0x154FE` | `08/0F 08/13 08/17 09/1B 09/1F 09/23 0A/27 0A/2B 0A/2F 0B/33 0B/37 0B/3B 0C/3F 0C/43 0C/47 0D/4F` |
| Pit bomb | cost / damage / unknown | `0x15511-0x15540` | `08/3F/10 08/3F/10 08/3F/10 08/3F/10 06/4F/0C 06/4F/0C 06/4F/0C 06/4F/0C 04/5F/08 04/5F/08 04/5F/08 02/5F/08 02/6F/04 02/6F/04 01/6F/04 00/7F/02` |
| Lane A | damage | `0x15709-0x15718` | `13 17 1B 1F 23 27 2B 2F 35 3B 41 47 4F 57 5F 67` |
| Lane shield | cost / unknown | `0x15719-0x15738` | `14/28 15/32 16/3C 17/46 18/50 19/5A 1A/64 1B/6E 1C/78 1D/82 1E/8C 20/96 22/A0 24/AA 26/B4 28/BE` |
| Lane healing | cost / damage / damage, per note | `0x15799-0x157C8` | `14/0A/0A 14/0A/0A 14/0F/0F 14/0F/0F 14/14/14 14/14/14 14/19/19 14/19/19 14/1E/1E 14/1E/1E 14/23/23 14/23/23 14/28/28 14/28/28 14/2D/2D 14/32/32` |
| Kyle A | damage | `0x157C9-0x157D8` | `33 37 3B 3F 43 47 4B 4F 53 57 5B 5F 63 67 6B 6F` |
| Kyle play dead | cost / unknown | `0x157D9-0x157F8` | `14/50 13/5A 12/64 11/6E 10/78 0F/82 0E/8C 0D/96 0C/A0 0B/AA 0A/B4 09/BE 07/C8 05/D2 03/DC 01/E6` |
| Kyle rod | cost / damage | `0x15898-0x158B7` | `0A/B3 0A/B7 0A/BB 0A/BF 08/C3 08/C7 08/CB 08/CF 06/D3 06/D7 06/DB 06/DF 04/E3 04/E7 02/EB 02/EF` |
| Jude weak A | range / damage | `0x159B2-0x159D1` | `08/0F 08/11 09/13 09/15 0A/17 0A/19 0B/1D 0B/21 0C/25 0C/29 0D/2D 0D/33 0E/39 0E/3F 0F/45 0F/4B` |
| Jude strong A | range / damage | `0x159E4-0x15A03` | `08/2F 08/31 08/33 08/35 09/37 09/39 09/3B 09/3D 0A/3F 0A/41 0A/45 0A/49 0B/4D 0B/51 0B/55 0B/59` |
| Jude quake | cost / damage | `0x15A16-0x15A35` | `32/87 32/8F 2D/97 2D/9F 28/A7 28/AF 23/B7 23/BF 1E/C7 1E/CF 19/D7 19/DF 14/E7 0F/EF 0A/F7 05/FF` |
| Lee A | damage | `0x15B97-0x15BA6` | `2F 33 37 3B 3F 43 47 4B 4F 53 57 5B 5F 67 6F 77` |
| Lee rapidfire | cost / damage | `0x15BA7-0x15BC6` | `04/3F 04/43 04/47 04/4B 03/4F 03/53 03/57 03/5B 02/5F 02/63 02/67 02/6B 01/6F 01/73 01/77 01/7B` |
| Lee firework | cost / damage / range | `0x15BC7-0x15BF6` | `0F/3F/04 0F/43/04 0F/47/04 0F/4B/04 0F/4F/04 0F/53/04 0F/57/05 0F/5B/05 0F/5F/05 0F/63/05 0F/67/06 0F/6B/06 0F/6F/06 0F/73/07 0F/77/07 0F/7B/08` |
| Lora A | range / damage | `0x15C34-0x15C53` | `07/3F 07/43 08/47 08/4B 09/4F 09/53 0A/57 0A/5B 0B/5F 0B/63 0C/67 0C/6B 0D/6F 0D/73 0E/7B 0E/7F` |
| Lora heal | cost / damage / damage (uncertain) | `0x15C66-0x15C95` | `08/14/14 0C/16/16 10/18/18 14/1A/1A 18/1C/1C 1C/1E/1E 20/20/20 24/22/22 28/24/24 2C/26/26 30/28/28 34/2A/2A 38/2C/2C 3C/2E/2E 40/30/30 44/32/32` |
| Lora wing | cost | `0x15C96-0x15CA5` | `0F 0E 0D 0C 0B 0A 09 08 07 06 05 04 03 02 01 00` |
| Zold A | range / damage | `0x15CB6-0x15CD5` | `0A/87 0A/8F 0A/97 0A/9F 0B/A7 0B/AF 0B/B7 0B/BF 0C/C7 0C/CF 0C/D7 0C/DF 0D/E7 0D/EF 0D/F7 0D/FF` |
| Zold B | cost / damage | `0x15CE8-0x15D07` | `14/97 14/9F 14/A7 14/AF 14/B7 14/BF 14/C7 14/CF 14/D3 14/D7 14/DB 14/DF 14/E3 14/E7 14/EB 14/EF` |

### Additional tables

The Zold A damage values also appear as a standalone 16-byte array immediately before the range/damage records. The ROM has code references to this array at CPU address `0x5CA6`; its values match the damage byte of each Zold A record:

| Table | ROM range | Values (hex) |
|---|---|---|
| Zold A standalone damage | `0x15CA6-0x15CB5` | `87 8F 97 9F A7 AF B7 BF C7 CF D7 DF E7 EF F7 FF` |

Two more arrays follow the character MP tables. Each has eight two-byte entries. These are stored in the JSON as arrays of two-byte arrays under `additional_tables`; values below are shown as `first/second` bytes. Their exact purpose and second-byte meaning are unknown.

| Table | ROM range | Entries (hex) |
|---|---|---|
| Lookup at `0x17165` | `0x17165-0x17174` | `00/01 02/04 05/06 08/09 0B/0D 0E/10 11/12 14/16` |
| Lookup at `0x17175` | `0x17175-0x17184` | `00/01 03/04 05/07 08/0A 0C/0D 0E/0F 11/13 15/16` |

Fixed-bank code at `0x009DE-0x009EB` loads one of these table bases (`0x7165` or `0x7175` in the banked CPU window), indexes with the value previously read from `0xC3F8` using a two-byte stride, reads the first byte of that pair, and stores it at `0xC340`. The branch selecting the base depends on flags from a preceding helper call operating on work RAM at `0xC405`; the meaning of that state and what the lookup result represents have not been identified. The banked CPU addresses correspond to the listed physical offsets when ROM bank 5 is selected.

**Boundary and interpretation caveats:**

- Lane's shield annotation ends with `0F 31`, but the 16 cost/unknown pairs starting at `0x15719` end with `28 BE` at `0x15738`; `0F 31` occurs at `0x1573D-0x1573E`. The range above follows the 16-entry layout, not the annotated end marker.
- The Lane healing annotation ends `32 32 14`, and the Kyle A annotation begins `[ 32 ...`. With 16 three-byte healing records, Lane ends in `14 32 32` at `0x157C6-0x157C8`, and 16 Kyle A values then start with `33` at `0x157C9`. The annotated `32` would overlap Lane's final record. The boundary needs code or gameplay verification.
- Kyle's play-dead annotation identifies cost but does not explain the second byte. Lane and Lora healing notes use “damage” for the repeated values; whether those fields mean healing, damage, or another quantity is not established.
- Range, cost, damage, and level assignments are the notes' interpretations. No consuming routine has been traced yet, and the unknown bytes and any scaling or special values remain to be verified.

## What is and is not mapped yet

| Subsystem | Current mapping |
|---|---|
| Engine / startup | Entry point, interrupt-vector targets, startup range, and several called CPU addresses are identified above. Most routines still need disassembly and naming. |
| Runtime variables / character state | CPU addresses and the code that updates them are not yet established. See the separate save analysis for observed saved fields. |
| Character templates / stats | HP, MP, attack, and ability tables are identified from the annotated dump in bank 5 above; consumers and some field meanings/boundaries remain to be verified. Other character data is not yet located. |
| Maps / collision / encounters | No ROM file offsets or table format confirmed. |
| Text / character graphics | The title is at `0x0134-0x0143`; a preliminary bank-2 tile-data batch and matching four-tile Hero sprite are documented above. Dialogue/text tables, font data, tile maps, palettes, and the loader that consumes the graphics descriptors remain unidentified. |
| Audio / music / sound effects | No code or data ranges identified yet. Game Boy sound registers are in `0xFF10-0xFF3F`, but that hardware fact does not identify the ROM routines or music data. |

## Next steps to turn this into a byte-level map

1. Disassemble from the confirmed vectors and startup entry, tracking the active MBC2 ROM bank at each call and data read.
2. Follow pointers and callers into banks 1-7; distinguish code, pointer tables, graphics/tilemaps, map/collision data, text, and audio by their consumers and decoding routines before assigning names.
3. Use an emulator debugger to connect observed saved fields to live RAM addresses and ROM read/write routines.
4. Add each variable or asset range with the evidence used to identify it (write site, read site, pointer, controlled change, or decoded output).
