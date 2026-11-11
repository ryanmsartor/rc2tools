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

The ROM has eight physical banks. The character tables described below are in bank 5. Graphics/tile-data regions and related descriptors have been identified in banks 2 and 6; details and confidence are documented below. Other banks are not yet reliably classified by subsystem.

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

### Bank 1 quarter-circle coordinate table

Physical ROM offsets `0x4E77-0x4F66` (CPU addresses `0x4E77-0x4F66` with bank 1 selected) contain 15 records of 16 bytes each. Each record is eight little-endian 16-bit values, which form four `(x, y)` coordinate pairs. For example, the record at `0x4E97` is `(64, 0)`, `(59, 25)`, `(45, 45)`, `(25, 59)`. Across records, these pairs approximate points at 0°, 22.5°, 45°, and 67.5° on a quarter circle, with the first point's x-coordinate ranging from 16 to 768.

This numeric structure is not raw 2bpp graphics data. It is likely a geometric/vector lookup table, but its units, consuming routine, and exact in-game use have not been established. The following code begins at `0x4F67`.

## Graphics and tile data (preliminary)

The following identification is based on decoding bytes as Game Boy 2bpp tiles and matching them to screenshots. The tile matches confirm the format and the listed sprite tiles; descriptor fields are interpreted from their layout, but their consuming code has not been traced.

Screenshot references previously stored in this repository:

- Opening dialogue: [LaunchBox image](https://images.launchbox-app.com/bd8cb660-d917-483a-96c5-a3e28dc8de02.png).
- Character status screens: [Mattozoic image](https://mattozoic.com/wp-content/uploads/2017/04/Status-1.png).
- Title screen: [Mattozoic image](https://mattozoic.com/wp-content/uploads/2017/04/Title-2.png).

The latter two appear in [Mattozoic's Rolan's Curse 2 article](https://mattozoic.com/?p=1296).

Unless noted otherwise, source ranges below are physical ROM offsets in **bank 2**. For a CPU source pointer in the banked window, add `0x4000` to obtain the physical offset; conversely, subtract `0x4000` from the physical offset to obtain the CPU address with bank 2 selected. Each uncompressed 2bpp tile is 16 bytes (8×8 pixels).

### Title-screen graphics

Matching tiles against the [title-screen image](https://mattozoic.com/wp-content/uploads/2017/04/Title-2.png) identifies a contiguous `0xA50`-byte title-screen graphics block in physical bank 6, from `0x1A6AE` through `0x1B0FD` inclusive. The bytes decode as raw, uncompressed Game Boy 2bpp tiles (165 tiles at 16 bytes each).

A descriptor table at physical offset `0x18110` (CPU address `0x4110` with bank 6 selected) contains two adjacent six-byte entries. Interpreting each entry as little-endian byte length, source CPU address, and VRAM destination gives:

| Length | Source CPU address (bank 6 selected) | Physical ROM range | VRAM destination |
|---:|---:|---:|---:|
| `0x0550` | `0x66AE` | `0x1A6AE-0x1ABFD` | `0x8800` |
| `0x0500` | `0x6BFE` | `0x1ABFE-0x1B0FD` | `0x9300` |

The physical source ranges are contiguous and their 85- and 80-tile blocks together account for all `0xA50` bytes. Tiles from both blocks match the title artwork in the screenshot. The six-byte field interpretation is based on the entries' structure, transfer-sized lengths, bank-6 source pointers, and VRAM destination addresses; the consuming loader is traced in the [title-screen trace notes](./rom-map-title-screen-trace.md#tile-data-loader). Each record gives the length, source CPU address, and VRAM destination, and the loader accepts a source in bank 0 as well as in bank 6.

The title screen's arrangement above the START/CONTINUE line is a 20×13 grid of 8×8 cells (LCDC `0xE3`, BG map at `0x9800`). The top and bottom rows (0 and 12) are blank `0x30` filler and form a margin. The editable art is the 20×11 cells in between, 160×88 pixels. Cells hold tile IDs `0x30`-`0xD2` and map to the two blocks above: IDs `0x80`-`0xD2` come from `0x1A6AE` and IDs `0x30`-`0x7F` from `0x1ABFE`. The grid is the top 13 rows of the title tilemap, which is stored in bank 4 at `0x7C30` as a single record of 18 rows × 20 columns: `rows`, `width`, destination (little-endian `0x9800`), then row-major tile IDs. The bank-0 routine `0x0A78` decodes this record stream (zero row count ends it), and bank-4 `0x7BAE` calls it with `HL=0x7C30` about 79 frames into boot. The title palette is shadowed at `0xFFC7` with `0x2D` by the same bank-4 routine at `0x7BA5`. The grid was checked against live VRAM at frame 90 with 0 mismatches. It omits the menu cursor (sprite 0, tile `0xD4`, at x=16, y=104), the menu text, and the copyright tile `0xD3` below the START/CONTINUE line. The grid lives in `bin/art_layout.py` and is used by `rc2t hack dump-art title` and `rc2t hack inject-art title`. The bank-0 loader at `0x077D`-`0x07BB` reads these blocks through the pointer table at `0x18000` (see the [title-screen trace notes](./rom-map-title-screen-trace.md#tile-data-loader)).

Major findings from the title-screen trace:

- The title BG map is written by bank-4 `0x7BAE` through the bank-0 writer `0x0A78`, using the record stream at bank 4 `0x7C30` (verified).
- Bank switches in this path go through the fixed trampoline `0x0CCB`, which writes the MBC2 bank register at `0x21FF` (verified).
- The tilemap write happens before the bank-4 calls to `0x7BFB`, `0x0C9B`, `0x0636`, and `0x1467` (verified call order).
- The title's tile loader reads pointer-table word 5 (`0x1800A`) with index `caller A − 0x20`. The `0x25` caller appears to be the `0x075F` call (inferred). The `0x075F` call with A=`0x09` is not identified.
- Repointing the two source fields at bank-6 boss-sprite tiles (`0x4A1E` and `0x4F6E`, four changed bytes at `0x18112`-`0x18119`) makes the title show those tiles in the logo slots at frame 300. The tilemap and tile bytes are unchanged. Details and the cursor side effect (shared tile `0xD4`) are in the [title-screen trace notes](./rom-map-title-screen-trace.md#source-swap-test-verified-at-frame-300).
- A single repeated cell can take a different tile without changing the others. This needs a new tile ID for that cell and one more descriptor record, which moves the list. Verified at frame 300 ([single-cell test](./rom-map-title-screen-trace.md#single-cell-replacement-test-verified-at-frame-300)).
- The title's tilemap grid is 13×20 cells at file `0x13C34` (the record header is four bytes at `0x13C30`, and the cells start at `0x13C34`). Cells index tile IDs through LCDC bit 4 = `0`, so one frame can address 256 BG patterns. The text rows use IDs `0x30`, `0x3E`, `0xD3`, and the other menu IDs, which leaves 161 IDs for the art. Using `rc2t hack inject-art title` on the 20×11 art (the blank margin rows are skipped), the art can have 175 unique tiles: 161 rewritten in place, and 14 extras at IDs `0xD5`-`0xE2`. The copy list (98 bytes) goes at bank 0 `0x61`, and the extra tiles are at free `0xFF` runs in bank 0 `0x3FC6` and bank 6 `0x1BF80`. The result was checked at a static title frame (500) against the original screen; rows 104+ match. Details are in the [title-screen trace notes](./rom-map-title-screen-trace.md#art-capacity-and-inject-art-layout).
- `--highlight-known` shades these structures in purple: the title tilemap stream at `0x13C30`-`0x13D9C`, pointer-table word 5 at `0x1800A`-`0x1800B`, the descriptor list at `0x18110`-`0x1811D`, and the routines that load, write, copy, and switch banks for them (`0x077D`-`0x07BB`, `0x0A78`-`0x0AA0`, `0x0AD0`-`0x0AD8`, `0x0CCB`-`0x0CD3`). The other pointer-table entries are not marked.

Full experiment record, call-order table, dead ends, and open questions: [title-screen trace notes](./rom-map-title-screen-trace.md).

### In-UI character weapon and ability icons

A sequence of 23 consecutive 16×16 sprites beginning at physical ROM offset `0x804E` contains the in-UI icons below, in order. Each sprite occupies 64 bytes (`0x40`), or four consecutive tiles.

| # | Character | Icon | Physical ROM start |
|---:|---|---|---:|
| 1 | Hero | Sword | `0x804E` |
| 2 | Hero | Magic Ball | `0x808E` |
| 3 | Pit | Dagger | `0x80CE` |
| 4 | Pit | Boomerang | `0x810E` |
| 5 | Pit | Bomb | `0x814E` |
| 6 | Lane | Rod | `0x818E` |
| 7 | Lane | Shield | `0x81CE` |
| 8 | Lane | Heal | `0x820E` |
| 9 | Kyle | Bone | `0x824E` |
| 10 | Kyle | Play dead | `0x828E` |
| 11 | Kyle | Lightning rod | `0x82CE` |
| 12 | Jude | Fireball | `0x830E` |
| 13 | Jude | Smash ball | `0x834E` |
| 14 | Jude | Earthquake spell | `0x838E` |
| 15 | Lee | Sai | `0x83CE` |
| 16 | Lee | Fist | `0x840E` |
| 17 | Lee | Firecracker | `0x844E` |
| 18 | Lora | Bow | `0x848E` |
| 19 | Lora | Heal | `0x84CE` |
| 20 | Lora | Fairy Wings | `0x850E` |
| 21 | Zold | Sword | `0x854E` |
| 22 | Zold | Wave | `0x858E` |
| 23 | Zold | Magic | `0x85CE` |

The block occupies `0x804E-0x860D` inclusive; the next address after the final icon is `0x860E`. With bank 2 selected, the corresponding CPU address range is `0x404E-0x460D`.

### Character level-up faces

The next eight 16×16 sprites are the character faces used for level-up pickups, in character order. Each occupies 64 bytes (`0x40`).

| # | Character | Physical ROM start |
|---:|---|---:|
| 1 | Hero | `0x860E` |
| 2 | Pit | `0x864E` |
| 3 | Lane | `0x868E` |
| 4 | Kyle | `0x86CE` |
| 5 | Jude | `0x870E` |
| 6 | Lee | `0x874E` |
| 7 | Lora | `0x878E` |
| 8 | Zold | `0x87CE` |

These faces occupy `0x860E-0x880D` inclusive. The next address is `0x880E`; with bank 2 selected, the CPU range is `0x460E-0x480D`.

### POW-screen character portraits

The POW screen's larger portraits are eight contiguous 32×32 images beginning
at physical offset `0x880E`. Each image contains sixteen consecutive 8×8 tiles
in row-major order (four tiles across by four down), occupying `0x100` bytes.
Rendering `0x880E-0x900D` in portrait mode produces eight recognizable faces.
The first three match Hero (shown as COOL), Pit, and Lane in the POW screenshot.
The following five are Kyle, Jude, Lee, Lora, and Zold, in that order.

| # | Character | Physical ROM range | CPU range (bank 2 selected) | Evidence |
|---:|---|---|---|---|
| 1 | Hero | `0x880E-0x890D` | `0x480E-0x490D` | POW screenshot match |
| 2 | Pit | `0x890E-0x8A0D` | `0x490E-0x4A0D` | POW screenshot match |
| 3 | Lane | `0x8A0E-0x8B0D` | `0x4A0E-0x4B0D` | POW screenshot match |
| 4 | Kyle | `0x8B0E-0x8C0D` | `0x4B0E-0x4C0D` | Portrait sequence confirmed |
| 5 | Jude | `0x8C0E-0x8D0D` | `0x4C0E-0x4D0D` | Portrait sequence confirmed |
| 6 | Lee | `0x8D0E-0x8E0D` | `0x4D0E-0x4E0D` | Portrait sequence confirmed |
| 7 | Lora | `0x8E0E-0x8F0D` | `0x4E0E-0x4F0D` | Portrait sequence confirmed |
| 8 | Zold | `0x8F0E-0x900D` | `0x4F0E-0x500D` | Portrait sequence confirmed |

These are separate from the 16×16 level-up faces above. The existing
`render-graphics` sprite layout groups four tiles into a 16×16 image and does
not preserve this row-major 4×4 arrangement; use `--mode portraits` to render
the larger faces.

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

### Hero animation, weapon, and spell sprites

After the level-up faces and POW portraits, the intervening graphics are only partly intelligible in the current rendering. Recognizable Hero art resumes at `0x9106` and continues through `0x9605`, matching the first `0x500`-byte tile-data batch below. The sequence contains 19 complete 16×16 sprites and two 8×16 left halves, totaling 20 sprite-equivalents:

| Physical ROM range | Contents |
|---|---|
| `0x9106-0x9185` | Hero idling down (2 sprites) |
| `0x9186-0x9205` | Hero idling up (2 sprites) |
| `0x9206-0x9285` | Hero idling left (2 sprites) |
| `0x9286-0x92C5` | Hero attacking down |
| `0x92C6-0x9305` | Hero attacking up |
| `0x9306-0x9345` | Hero attacking left |
| `0x9346-0x9385` | Hero sword, downward |
| `0x9386-0x93C5` | Hero sword, upward |
| `0x93C6-0x9405` | Hero sword, left |
| `0x9406-0x9585` | Six sprite-equivalents of sword arcs; difficult to interpret in the current rendering |
| `0x9586-0x95A5` | Left half of Hero's low-level electric ball |
| `0x95A6-0x95C5` | Left half of Hero's high-level electric ball |
| `0x95C6-0x9605` | Hero defeated |

The sequence ends at `0x9605` inclusive; the next address is `0x9606` (CPU address `0x5606` with bank 2 selected).

### Bank-1 copy and code overlays

Physical bank-1 range `0x5286-0x5585` is aligned with the Hero graphics at bank-2 range `0x9286-0x9585` (the bank-1 offsets are `0x4000` lower). A byte-for-byte comparison finds 751 of the 768 bytes identical. The differing bytes are `0x5286-0x5290` and `0x5580-0x5585`.

| Bank-1 range | Matching bank-2 range | Contents |
|---|---|---|
| `0x5291-0x52C5` | `0x9291-0x92C5` | Tail of Hero attacking down; the preceding 11 bytes are overwritten |
| `0x52C6-0x5305` | `0x92C6-0x9305` | Hero attacking up |
| `0x5306-0x5345` | `0x9306-0x9345` | Hero attacking left |
| `0x5346-0x5385` | `0x9346-0x9385` | Hero sword, downward |
| `0x5386-0x53C5` | `0x9386-0x93C5` | Hero sword, upward |
| `0x53C6-0x5405` | `0x93C6-0x9405` | Hero sword, left |
| `0x5406-0x557F` | `0x9406-0x957F` | First five and most of the sixth sword-arc sprite-equivalent; the final six bytes are overwritten |

The first differing run is part of a code sequence that ends with `RET` (`0xC9`) at `0x5290`. The last six bytes, `0x5580-0x5585`, are two `JP` instructions to `0x55C0` and `0x55AA`, not sprite data. Fixed-bank code contains calls to CPU addresses `0x5580` and `0x5583` at ROM offsets `0x04FD` and `0x0517`.

Static bank-state tracing resolves the apparent data pointers into this range as references to other banks: for example, the pointer `0x5382` is later dereferenced after selecting bank 5, and the pointer `0x5449` is dereferenced after the bank-5 selection at `0x1D77`. The `0x53E1` reads are in helpers called while bank 5 is selected, and the pointer table at `0x4ACB` is consumed after switching to bank 5. These do not show the copied bank-1 graphics being loaded as graphics.

A raw scan initially suggested a `CALL 0x54EA` at ROM offset `0x1950`, which would have been bank-sensitive. This is a false positive: the `0xCD` byte is the immediate operand of the preceding `LDH A,(0xFFCD)` instruction at `0x194F`, not a `CALL` opcode. No control flow to `0x54EA` is established by that byte sequence. Based on the traced references, there is no confirmed read of the interior bank-1 copy as graphics; static analysis is not a runtime proof against every indirect or data-driven access. Startup also selects bank 1 before calling `0x5586`, immediately after this range, so the interval as a whole is not dead code.

The per-reference bank-state audit and its limitations are recorded in the [bank-1 copy reference audit](./rom-map-bank1-copy-reference-audit.md).

### Pit animation and weapon sprites

The sequence beginning at `0x9606` starts with Pit's nine movement and attack sprites in the same pose order as Hero's: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. They are followed by two full-size boomerangs, two 32-byte dagger halves, a bomb, three full-size light balls, and Pit's defeated sprite.

| Physical ROM range | Contents |
|---|---|
| `0x9606-0x9685` | Pit idling down (2 sprites) |
| `0x9686-0x9705` | Pit idling up (2 sprites) |
| `0x9706-0x9785` | Pit idling left (2 sprites) |
| `0x9786-0x97C5` | Pit attacking down |
| `0x97C6-0x9805` | Pit attacking up |
| `0x9806-0x9845` | Pit attacking left |
| `0x9846-0x9885` | Pit's boomerang facing left |
| `0x9886-0x98C5` | Pit's boomerang facing right |
| `0x98C6-0x98E5` | Pit's downward-facing dagger half |
| `0x98E6-0x9905` | Pit's left-facing dagger half |
| `0x9906-0x9945` | Pit's bomb |
| `0x9946-0x9A05` | Three full-size light balls |
| `0x9A06-0x9A45` | Pit defeated |

In the current visualization, each dagger half appears split and stacked vertically. The sequence ends at `0x9A45` inclusive; the next address is `0x9A46` (CPU address `0x5A46` with bank 2 selected).

### Lane animation, rod, and particle sprites

The sequence beginning at `0x9A46` starts with Lane's nine movement and attack sprites in the same pose order as Hero's and Pit's: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. These are followed by Lane's rod facing down, up, and left; one composite sprite containing three particle effects and a fully transparent tile; and Lane's defeated sprite.

| Physical ROM range | Contents |
|---|---|
| `0x9A46-0x9AC5` | Lane idling down (2 sprites) |
| `0x9AC6-0x9B45` | Lane idling up (2 sprites) |
| `0x9B46-0x9BC5` | Lane idling left (2 sprites) |
| `0x9BC6-0x9C05` | Lane attacking down |
| `0x9C06-0x9C45` | Lane attacking up |
| `0x9C46-0x9C85` | Lane attacking left |
| `0x9C86-0x9CC5` | Lane's rod facing down |
| `0x9CC6-0x9D05` | Lane's rod facing up |
| `0x9D06-0x9D45` | Lane's rod facing left |
| `0x9D46-0x9D85` | Three particle effects and one fully transparent tile |
| `0x9D86-0x9DC5` | Lane defeated |

The sequence ends at `0x9DC5` inclusive; the next address is `0x9DC6` (CPU address `0x5DC6` with bank 2 selected).

### Kyle animation, weapons, and effects

The sequence beginning at `0x9DC6` starts with nine standard movement and attack sprites in the same pose order as the other characters: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. These are followed by Kyle's bone, two Play Dead frames, lightning, bomb/lightning-rod effect graphics, defeated sprite, and three light orbs.

| Physical ROM range | Contents |
|---|---|
| `0x9DC6-0x9E45` | Kyle idling down (2 sprites) |
| `0x9E46-0x9EC5` | Kyle idling up (2 sprites) |
| `0x9EC6-0x9F45` | Kyle idling left (2 sprites) |
| `0x9F46-0x9F85` | Kyle attacking down |
| `0x9F86-0x9FC5` | Kyle attacking up |
| `0x9FC6-0xA005` | Kyle attacking left |
| `0xA006-0xA045` | Kyle's bone facing down |
| `0xA046-0xA085` | Kyle's bone facing up |
| `0xA086-0xA0C5` | Kyle's bone facing left |
| `0xA0C6-0xA105` | First frame of Kyle's Play Dead animation |
| `0xA106-0xA145` | Second frame of Kyle's Play Dead animation |
| `0xA146-0xA185` | Kyle lightning sprite 1 |
| `0xA186-0xA1C5` | Kyle lightning sprite 2 |
| `0xA1C6-0xA205` | Bomb/lightning-rod effect area: two quarter-sprites stacked vertically and two fully transparent quarter-sprites |
| `0xA206-0xA245` | Kyle defeated |
| `0xA246-0xA305` | Three light orbs, matching the ones after Pit's bomb |

The sequence ends at `0xA305` inclusive; the next address is `0xA306` (CPU address `0x6306` with bank 2 selected).

### Jude animation, rod, and fireball sprites

The sequence beginning at `0xA306` starts with nine standard movement and attack sprites in the same pose order as the other characters: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. These are followed by Jude's rod, weak fireball, and smash ball sprites, the earthquake spell pose, and his defeated sprite. `dump-art jude` and `inject-art jude` handle the rod, fireball, smash ball, and earthquake pieces; the standard poses and defeated sprite are handled the same way as the other characters.

| Physical ROM range | Contents |
|---|---|
| `0xA306-0xA385` | Jude idling down (2 sprites) |
| `0xA386-0xA405` | Jude idling up (2 sprites) |
| `0xA406-0xA485` | Jude idling left (2 sprites) |
| `0xA486-0xA4C5` | Jude attacking down |
| `0xA4C6-0xA505` | Jude attacking up |
| `0xA506-0xA545` | Jude attacking left |
| `0xA546-0xA585` | Jude's rod facing down |
| `0xA586-0xA5C5` | Jude's rod facing up |
| `0xA5C6-0xA605` | Jude's rod facing left |
| `0xA606-0xA625` | Half-sprite of Jude's weak fireball facing down |
| `0xA626-0xA645` | Half-sprite of Jude's weak fireball facing left; it appears split in two in the current visualization, like Pit's dagger |
| `0xA646-0xA6A5` | First smash ball (large fireball), 6 tiles, facing down |
| `0xA6A6-0xA705` | Second smash ball (large fireball), 6 tiles, facing left |
| `0xA706-0xA745` | Top half of Jude holding the rod above his head |
| `0xA746-0xA785` | Lower half of that pose, containing his body and all but the tip of his hat |
| `0xA786-0xA7C5` | Jude defeated |

The sequence ends at `0xA7C5` inclusive; the next address is `0xA7C6` (CPU address `0x67C6` with bank 2 selected).

### Lee animation, sai, fist, and firecracker sprites

The sequence beginning at `0xA7C6` starts with Lee's nine standard movement and attack sprites in the same pose order as the other characters: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. These are followed by Lee's sai and fist sprites, particle effects, firecracker effects, and defeated sprite.

| Physical ROM range | Contents |
|---|---|
| `0xA7C6-0xA845` | Lee idling down (2 sprites) |
| `0xA846-0xA8C5` | Lee idling up (2 sprites) |
| `0xA8C6-0xA945` | Lee idling left (2 sprites) |
| `0xA946-0xA985` | Lee attacking down |
| `0xA986-0xA9C5` | Lee attacking up |
| `0xA9C6-0xAA05` | Lee attacking left |
| `0xAA06-0xAA45` | Lee's sai facing down |
| `0xAA46-0xAA85` | Lee's sai facing up |
| `0xAA86-0xAAC5` | Lee's sai facing left |
| `0xAAC6-0xAB05` | Lee's fists facing down |
| `0xAB06-0xAB45` | Lee's fists facing up |
| `0xAB46-0xAB85` | Lee's fists facing left |
| `0xAB86-0xAB95` | One particle effect |
| `0xAB96-0xABA5` | Another particle effect |
| `0xABA6-0xAC65` | Firecracker effects arranged as 2×1, 2×2, and 2×3 tile groups; orientations remain uncertain |
| `0xAC66-0xAC85` | Half-sprite of full transparency |
| `0xAC86-0xACC5` | Lee defeated |

The sequence ends at `0xACC5` inclusive; the next address is `0xACC6` (CPU address `0x6CC6` with bank 2 selected).

### Lora animation, arrow, and healing sprites

The sequence beginning at `0xACC6` starts with Lora's nine standard movement and attack sprites in the same pose order as the other characters: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. These are followed by two half-sprites of her arrow, three wing-unfolding frames, her body during the flight animation, the drop shadow and transparent quarters, a heart particle, and her defeated sprite.

| Physical ROM range | Contents |
|---|---|
| `0xACC6-0xAD45` | Lora idling down (2 sprites) |
| `0xAD46-0xADC5` | Lora idling up (2 sprites) |
| `0xADC6-0xAE45` | Lora idling left (2 sprites) |
| `0xAE46-0xAE85` | Lora attacking down |
| `0xAE86-0xAEC5` | Lora attacking up |
| `0xAEC6-0xAF05` | Lora attacking left |
| `0xAF06-0xAF25` | Half-sprite of Lora's arrow facing down |
| `0xAF26-0xAF45` | Half-sprite of Lora's arrow facing left; it appears split like Pit's and Jude's weak attacks |
| `0xAF46-0xAF85` | Lora's wing-unfolding frame 1 |
| `0xAF86-0xAFC5` | Lora's wing-unfolding frame 2 |
| `0xAFC6-0xB005` | Lora's wing-unfolding frame 3 |
| `0xB006-0xB045` | Lora's body during the flight animation |
| `0xB046-0xB065` | Two quarter-sprites that combine into a ground drop shadow |
| `0xB066-0xB085` | Two fully transparent quarter-sprites |
| `0xB086-0xB095` | Quarter-sprite of the heart particle from Lora's healing animation |
| `0xB096-0xB0A5` | Quarter-sprite of transparent space |
| `0xB0A6-0xB0E5` | Lora defeated |

The sequence occupies `0xACC6-0xB0E5` inclusive, a total of `0x420` bytes (16½ 64-byte sprite-equivalents). The next address is `0xB0E6` (CPU address `0x70E6` with bank 2 selected).

### Zold animation, sword, blade-wave, and Megaball sprites

The sequence beginning at `0xB0E6` starts with Zold's nine standard movement and attack sprites in the same pose order as the other characters: two each idling down, up, and left, followed by one attack sprite facing down, up, and left. These are followed by Zold's sword, two half-sprites of blade waves, his Megaball ability, and his defeated sprite.

| Physical ROM range | Contents |
|---|---|
| `0xB0E6-0xB165` | Zold idling down (2 sprites) |
| `0xB166-0xB1E5` | Zold idling up (2 sprites) |
| `0xB1E6-0xB265` | Zold idling left (2 sprites) |
| `0xB266-0xB2A5` | Zold attacking down |
| `0xB2A6-0xB2E5` | Zold attacking up |
| `0xB2E6-0xB325` | Zold attacking left |
| `0xB326-0xB365` | Zold's sword facing down |
| `0xB366-0xB3A5` | Zold's sword facing up |
| `0xB3A6-0xB3E5` | Zold's sword facing left |
| `0xB3E6-0xB405` | Half-sprite of Zold's downward blade wave, appearing split in two |
| `0xB406-0xB425` | Half-sprite of Zold's left-facing blade wave |
| `0xB426-0xB525` | Zold's Megaball ability (16 tiles, arranged row-major in a 4×4 grid) |
| `0xB526-0xB565` | Zold defeated |

The sequence occupies `0xB0E6-0xB565` inclusive (`0x480` bytes, or 18 sprite-equivalents). The next address is `0xB566` (CPU address `0x7566` with bank 2 selected).

### Numeric and HUD glyph tiles

The 16-byte tiles immediately following Zold's sprites render as single 8×8 characters or HUD marks. The first 12 tiles are digits `0` through `9`, followed by `H` and `P`; the next four are `M`, another `P`, the arrow at the start of the MP gauge, and a forward slash.

| Physical ROM range | Contents |
|---|---|
| `0xB566-0xB575` | `0` |
| `0xB576-0xB585` | `1` |
| `0xB586-0xB595` | `2` |
| `0xB596-0xB5A5` | `3` |
| `0xB5A6-0xB5B5` | `4` |
| `0xB5B6-0xB5C5` | `5` |
| `0xB5C6-0xB5D5` | `6` |
| `0xB5D6-0xB5E5` | `7` |
| `0xB5E6-0xB5F5` | `8` |
| `0xB5F6-0xB605` | `9` |
| `0xB606-0xB615` | `H` |
| `0xB616-0xB625` | `P` |
| `0xB626-0xB635` | `M` |
| `0xB636-0xB645` | `P` |
| `0xB646-0xB655` | Arrow marking the start of the MP gauge |
| `0xB656-0xB665` | Forward slash (`/`) |

This sequence occupies `0xB566-0xB665` inclusive (16 tiles) and ends immediately before `0xB666`. Its last six tiles (`0xB606-0xB665`) fall within the broader descriptor source range `0xB606-0xB705` listed below; that source-range overlap does not conflict with the visual glyph identification.

### MP gauge, controls, cursors, and text-box tiles

The next 26 single-tile graphics begin at `0xB666`. They include MP-gauge states, button icons, UI markers, and pieces of a text-box border. The two special top-middle variants and the final text-box tile's intended exact use have not been identified.

| Physical ROM range | Contents |
|---|---|
| `0xB666-0xB675` | Two full MP bars |
| `0xB676-0xB685` | One full and one empty MP bar |
| `0xB686-0xB695` | Two empty MP bars |
| `0xB696-0xB6A5` | One full MP bar |
| `0xB6A6-0xB6B5` | One empty MP bar |
| `0xB6B6-0xB6C5` | A-button icon |
| `0xB6C6-0xB6D5` | B-button icon |
| `0xB6D6-0xB6E5` | Rectangle, variant 1 |
| `0xB6E6-0xB6F5` | Rectangle, variant 2 |
| `0xB6F6-0xB705` | Rectangle, variant 3 |
| `0xB706-0xB715` | Rightward cursor |
| `0xB716-0xB725` | Downward cursor |
| `0xB726-0xB735` | Period |
| `0xB736-0xB745` | Thin forward slash |
| `0xB746-0xB755` | Hyphen |
| `0xB756-0xB765` | Text-box top-left corner |
| `0xB766-0xB775` | Text-box top-middle segment |
| `0xB776-0xB785` | Text-box top-right corner |
| `0xB786-0xB795` | Text-box bottom-left corner |
| `0xB796-0xB7A5` | Text-box bottom-middle segment |
| `0xB7A6-0xB7B5` | Text-box bottom-right corner |
| `0xB7B6-0xB7C5` | Text-box left-middle segment |
| `0xB7C6-0xB7D5` | Text-box right-middle segment |
| `0xB7D6-0xB7E5` | Special top-middle segment, variant 1; usage unclear |
| `0xB7E6-0xB7F5` | Special top-middle segment, variant 2; usage unclear |
| `0xB7F6-0xB805` | Special bottom-middle segment with a downward cursor, indicating more text |

These tiles occupy `0xB666-0xB805` inclusive (26 tiles). They fall within the descriptor source ranges `0xB606-0xB705`, `0xB706-0xB725`, and `0xB726-0xB885` listed below. The descriptor ranges identify broader data blocks; exact transfer behavior and screen usage have not been traced.

### POW portrait frame and level marker tiles

The eight tiles from `0xB806` through `0xB885` continue the single-tile UI graphics. They contain a small rightward cursor, the corners and solid side segment of the frame around the POW portraits, and the two-tile `LV.` marker.

| Physical ROM range | Contents |
|---|---|
| `0xB806-0xB815` | Small rightward cursor |
| `0xB816-0xB825` | POW portrait frame, top-left corner |
| `0xB826-0xB835` | POW portrait frame, top-right corner |
| `0xB836-0xB845` | POW portrait frame, bottom-left corner |
| `0xB846-0xB855` | POW portrait frame, bottom-right corner |
| `0xB856-0xB865` | Solid side segment of the POW portrait frame |
| `0xB866-0xB875` | `LV.` marker, first tile |
| `0xB876-0xB885` | `LV.` marker, second tile |

This ends the documented run of single-tile graphics at `0xB886`; larger sprite graphics follow.

### Stockable inventory item sprites

Four stockable items follow at `0xB886`. Their names are documented in the
text table above. Each sprite is 2×2 tiles (64 bytes), and the four sprites
are stored consecutively:

| Physical ROM range | Contents |
|---|---|
| `0xB886-0xB8C5` | Large Potions |
| `0xB8C6-0xB905` | Fairy's Tears |
| `0xB906-0xB945` | Magic Ball |
| `0xB946-0xB985` | Fairy Wings |

Together these occupy `0xB886-0xB985` inclusive and exactly match the separately listed descriptor source range `0xB886-0xB985` below.

### Stacked 1bpp glyph tiles

The 24 tiles at `0xB986-0xBB05` are not sprites. Each 16-byte tile holds two 8×8 monochrome glyphs stacked vertically: the first 8 bytes are the top glyph and the last 8 bytes are the bottom glyph. Each byte is one row, with bit 7 at the left. A set bit is background and a clear bit is ink. Row 8 of each glyph is usually `0xFF` (blank), which gives spacing between the stacked glyphs.

Read as 2bpp tiles, these bytes look like noise. Read as this 1bpp layout, the glyphs are clear, and `./rc2t render-graphics 0xB986 0xBB06 output/glyphs.png --stacked-glyphs` renders them in black. Each 16-byte tile is drawn as one 8×16 cell, which matches the in-game look of solid black characters at double height. `rc2t hack dump-font` and `rc2t hack inject-font` (synonyms `dump-art font` and `inject-art font`) edit this range through a 1:1 sheet of 48 separated 8×8 glyph cells, six per row across eight rows; see the README.

Whether the game's loader uses this exact layout is not yet verified; it is the layout that renders as legible glyphs.

| Tile range | Top glyph bytes | Top | Bottom glyph bytes | Bottom |
|---|---|---|---|---|
| `0xB986-0xB995` | `0xB986-0xB98D` | 0 | `0xB98E-0xB995` | 1 |
| `0xB996-0xB9A5` | `0xB996-0xB99D` | 2 | `0xB99E-0xB9A5` | 3 |
| `0xB9A6-0xB9B5` | `0xB9A6-0xB9AD` | 4 | `0xB9AE-0xB9B5` | 5 |
| `0xB9B6-0xB9C5` | `0xB9B6-0xB9BD` | 6 | `0xB9BE-0xB9C5` | 7 |
| `0xB9C6-0xB9D5` | `0xB9C6-0xB9CD` | 8 | `0xB9CE-0xB9D5` | 9 |
| `0xB9D6-0xB9E5` | `0xB9D6-0xB9DD` | A | `0xB9DE-0xB9E5` | B |
| `0xB9E6-0xB9F5` | `0xB9E6-0xB9ED` | C | `0xB9EE-0xB9F5` | D |
| `0xB9F6-0xBA05` | `0xB9F6-0xB9FD` | E | `0xB9FE-0xBA05` | F |
| `0xBA06-0xBA15` | `0xBA06-0xBA0D` | G | `0xBA0E-0xBA15` | H |
| `0xBA16-0xBA25` | `0xBA16-0xBA1D` | I | `0xBA1E-0xBA25` | J |
| `0xBA26-0xBA35` | `0xBA26-0xBA2D` | K | `0xBA2E-0xBA35` | L |
| `0xBA36-0xBA45` | `0xBA36-0xBA3D` | M | `0xBA3E-0xBA45` | N |
| `0xBA46-0xBA55` | `0xBA46-0xBA4D` | O | `0xBA4E-0xBA55` | P |
| `0xBA56-0xBA65` | `0xBA56-0xBA5D` | Q | `0xBA5E-0xBA65` | R |
| `0xBA66-0xBA75` | `0xBA66-0xBA6D` | S | `0xBA6E-0xBA75` | T |
| `0xBA76-0xBA85` | `0xBA76-0xBA7D` | U | `0xBA7E-0xBA85` | V |
| `0xBA86-0xBA95` | `0xBA86-0xBA8D` | W | `0xBA8E-0xBA95` | X |
| `0xBA96-0xBAA5` | `0xBA96-0xBA9D` | Y | `0xBA9E-0xBAA5` | Z |
| `0xBAA6-0xBAB5` | `0xBAA6-0xBAAD` | `'` (apostrophe) | `0xBAAE-0xBAB5` | `:` |
| `0xBAB6-0xBAC5` | `0xBAB6-0xBABD` | `-` | `0xBABE-0xBAC5` | `.` |
| `0xBAC6-0xBAD5` | `0xBAC6-0xBACD` | `,` | `0xBACE-0xBAD5` | `?` |
| `0xBAD6-0xBAE5` | `0xBAD6-0xBADD` | `!` | `0xBADE-0xBAE5` | `-` (short) |
| `0xBAE6-0xBAF5` | `0xBAE6-0xBAED` | `/` | `0xBAEE-0xBAF5` | `)` (thick) |
| `0xBAF6-0xBB05` | `0xBAF6-0xBAFD` | `)` | `0xBAFE-0xBB05` | `(` |

The two final parenthesis tiles may be used to indicate a highlight or something else - I (Ryan) don't recall ever seeing them used in game. The stacking itself is clear, but the characters' usage in the game's text has not been traced.

### Healing item and energy sprites

Four 2×2 sprites (64 bytes each) follow the stacked glyphs. Unlike the stockable items, these take effect immediately rather than entering the inventory, per in-game observation.

| Physical ROM range | Contents |
|---|---|
| `0xBB06-0xBB45` | Small MP fruit |
| `0xBB46-0xBB85` | Large MP fruit |
| `0xBB86-0xBBC5` | Small healing potion |
| `0xBBC6-0xBC05` | Small healing potion on a solid background instead of transparent (the grayscale render does not show this difference, so it is from in-game observation; the source of the background is not traced) |

Four 1×1 tiles and one 2×2 sprite follow:

| Physical ROM range | Contents |
|---|---|
| `0xBC06-0xBC15` | 1×1 light energy particle |
| `0xBC16-0xBC25` | 1×1 dark energy particle |
| `0xBC26-0xBC35` | Top half of the left side of a medium-light energy ball |
| `0xBC36-0xBC45` | Bottom half of the left side of a medium-light energy ball |
| `0xBC46-0xBC85` | Large light energy ball (2×2) |

These sprites occupy `0xBB06-0xBC85` inclusive. The descriptor source table above stops at `0xBB05`, so the source pointers for this run have not been traced. They are included in `--highlight-known`.

### Ending credits text

The ending credits at `0xBC86-0xBFAB` are documented in [the known-text document](./known-text.md), along with the character table, the cartridge title, and the dialogue strings. Those ranges are shaded in yellow by `--highlight-known`.

### Terrain and world-object tiles (preliminary)

The range `0xC46A-0xE259` (7,664 bytes, exactly 479 16-byte 2bpp tiles) contains terrain sprites and tiles: the nonpassable objects that make up the overworld and dungeons, which the character cannot walk through. A rendered sample shows tile-style artwork rather than code or text. The range is included in `--highlight-known`. NPC and enemy sprites begin at `0xE25A`; see the section below.

This is a coarse range, not a map. Individual tile and sprite boundaries, how they are grouped into terrain objects, the tile-map and collision data that reference them, and the routines that load them have not been traced. Go back and map this range more thoroughly later.

### NPC, enemy, and orb sprites (preliminary)

The range `0xE25A-0xFD59` (6,912 bytes, exactly 432 16-byte 2bpp tiles) contains NPC and enemy sprites. The first 56 16×16 sprites are listed below as 28 two-frame animations. This identification is based on the rendered artwork; names marked `(?)` are tentative.

| NPC or enemy | Frame 1 | Frame 2 |
|---|---|---|
| Egghead | `0xE25A-0xE299` | `0xE29A-0xE2D9` |
| Dog | `0xE2DA-0xE319` | `0xE31A-0xE359` |
| Kyle | `0xE35A-0xE399` | `0xE39A-0xE3D9` |
| Skull sorceror (?) | `0xE3DA-0xE419` | `0xE41A-0xE459` |
| Jude | `0xE45A-0xE499` | `0xE49A-0xE4D9` |
| Jude's pupil | `0xE4DA-0xE519` | `0xE51A-0xE559` |
| Lora | `0xE55A-0xE599` | `0xE59A-0xE5D9` |
| Zold | `0xE5DA-0xE619` | `0xE61A-0xE659` |
| Dark knight (?) | `0xE65A-0xE699` | `0xE69A-0xE6D9` |
| White blob | `0xE6DA-0xE719` | `0xE71A-0xE759` |
| Spiny beetle | `0xE75A-0xE799` | `0xE79A-0xE7D9` |
| Medusa head | `0xE7DA-0xE819` | `0xE81A-0xE859` |
| Carnivorous plant | `0xE85A-0xE899` | `0xE89A-0xE8D9` |
| Demon head | `0xE8DA-0xE919` | `0xE91A-0xE959` |
| Knight armor head | `0xE95A-0xE999` | `0xE99A-0xE9D9` |
| Nautilus | `0xE9DA-0xEA19` | `0xEA1A-0xEA59` |
| Ghost | `0xEA5A-0xEA99` | `0xEA9A-0xEAD9` |
| Mosquito | `0xEADA-0xEB19` | `0xEB1A-0xEB59` |
| Flying book | `0xEB5A-0xEB99` | `0xEB9A-0xEBD9` |
| Zombie | `0xEBDA-0xEC19` | `0xEC1A-0xEC59` |
| Wood head | `0xEC5A-0xEC99` | `0xEC9A-0xECD9` |
| Worm blob | `0xECDA-0xED19` | `0xED1A-0xED59` |
| Living jar (?) | `0xED5A-0xED99` | `0xED9A-0xEDD9` |
| Ghost | `0xEDDA-0xEE19` | `0xEE1A-0xEE59` |
| Magic carp | `0xEE5A-0xEE99` | `0xEE9A-0xEED9` |
| Blowfish | `0xEEDA-0xEF19` | `0xEF1A-0xEF59` |
| Crow | `0xEF5A-0xEF99` | `0xEF9A-0xEFD9` |
| Steer skull | `0xEFDA-0xF019` | `0xF01A-0xF059` |

Each frame is a 2×2 sprite (64 bytes); the two sprites in each row form a simple two-frame animation. This accounts for `0xE25A-0xF059`.

The next seven NPC/enemy sets each contain four 2×2 sprite poses: downward walking, upward walking, leftward standing, and leftward stepping.

| NPC or enemy | Downward walking | Upward walking | Leftward standing | Leftward stepping |
|---|---|---|---|---|
| Shadow man | `0xF05A-0xF099` | `0xF09A-0xF0D9` | `0xF0DA-0xF119` | `0xF11A-0xF159` |
| Sorceror | `0xF15A-0xF199` | `0xF19A-0xF1D9` | `0xF1DA-0xF219` | `0xF21A-0xF259` |
| Monkey | `0xF25A-0xF299` | `0xF29A-0xF2D9` | `0xF2DA-0xF319` | `0xF31A-0xF359` |
| Evil knight | `0xF35A-0xF399` | `0xF39A-0xF3D9` | `0xF3DA-0xF419` | `0xF41A-0xF459` |
| Monster duck | `0xF45A-0xF499` | `0xF49A-0xF4D9` | `0xF4DA-0xF519` | `0xF51A-0xF559` |
| Mushroom head | `0xF55A-0xF599` | `0xF59A-0xF5D9` | `0xF5DA-0xF619` | `0xF61A-0xF659` |
| Walking frog | `0xF65A-0xF699` | `0xF69A-0xF6D9` | `0xF6DA-0xF719` | `0xF71A-0xF759` |

These four-pose sets occupy `0xF05A-0xF759`; the next address is `0xF75A`.

The next four characters have six 2×2 sprite poses each, in the order of two walking-down frames, two walking-up frames, and two walking-left frames. Names marked `(?)` are tentative.

| NPC or enemy | Down 1 | Down 2 | Up 1 | Up 2 | Left 1 | Left 2 |
|---|---|---|---|---|---|---|
| Lizard soldier | `0xF75A-0xF799` | `0xF79A-0xF7D9` | `0xF7DA-0xF819` | `0xF81A-0xF859` | `0xF85A-0xF899` | `0xF89A-0xF8D9` |
| Rhino soldier (?) | `0xF8DA-0xF919` | `0xF91A-0xF959` | `0xF95A-0xF999` | `0xF99A-0xF9D9` | `0xF9DA-0xFA19` | `0xFA1A-0xFA59` |
| Ninja (?) | `0xFA5A-0xFA99` | `0xFA9A-0xFAD9` | `0xFADA-0xFB19` | `0xFB1A-0xFB59` | `0xFB5A-0xFB99` | `0xFB9A-0xFBD9` |
| Cyclops wizard (?) | `0xFBDA-0xFC19` | `0xFC1A-0xFC59` | `0xFC5A-0xFC99` | `0xFC9A-0xFCD9` | `0xFCDA-0xFD19` | `0xFD1A-0xFD59` |

These six-pose sets occupy `0xF75A-0xFD59`; the next address is `0xFD5A`. Together, the two-frame, four-pose, and six-pose entries above account for the 2×2 sprite artwork from `0xE25A` through `0xFD59`.

The last two tiles of the artwork are a light and a dark energy orb, 1×1 tiles each:

| Physical ROM range | Contents |
|---|---|
| `0xFD5A-0xFD69` | Light orb (1×1 tile) |
| `0xFD6A-0xFD79` | Dark orb (1×1 tile) |

The bytes from `0xFD7A` onward do not look like 2bpp artwork. They repeat 4-byte groups, such as `34 00 08 00`, `35 00 00 08`, and `36 00 08 08`. The second byte of each group is often `0x00` or `0x20`, and tile numbers climb through runs such as `0x34-0x37` and `0x28-0x2B`. This pattern fits sprite-part records (position offsets, tile number, and attributes) that would assemble multi-tile sprites, but this is unconfirmed. The records are not in `--highlight-known` yet, and the end of this data has not been found.

The routines or tables that reference these sprites have not been traced.

### Chest, junk, house, and terrain tiles (preliminary)

The range `0x1811E-0x1861D` (1,280 bytes, 80 16-byte 2bpp tiles) holds 2×2 sprites and terrain. Each 2×2 sprite is 64 bytes. The rendered sample shows tile artwork, not code or text.

| Physical ROM range | Contents |
|---|---|
| `0x1811E-0x1815D` | Chest (2×2 sprite) |
| `0x1815E-0x1819D` | Destructible junk (2×2 sprite) |
| `0x1819E-0x1829D` | House pieces seen inside towns: top left, top right, bottom left, and bottom right (four 2×2 blocks) |
| `0x1829E-0x1861D` | More terrain tiles |

The chest and junk are described from the user's observation and matched against the render. The house split is inferred from the block size. Terrain tile and sprite boundaries in this range have not been traced. Go back and map this range more thoroughly later.

### Idle NPC sprites (preliminary)

The range `0x1861E-0x18A1D` (1,024 bytes, 16 2×2 sprites of 64 bytes each) appears to hold two idle-animation frames for each of eight townsfolk. The frame pairing is inferred from the bytes: adjacent frames differ by 41 to 108 bits, while frames 8 sprites apart differ by 154 to 189. The NPC identities come from observation; the rendered sprites have not yet been checked against them.

| NPC (tentative) | Frame 1 | Frame 2 |
|---|---:|---:|
| Elder | `0x1861E-0x1865D` | `0x1865E-0x1869D` |
| Egghead | `0x1869E-0x186DD` | `0x186DE-0x1871D` |
| Man | `0x1871E-0x1875D` | `0x1875E-0x1879D` |
| Woman | `0x1879E-0x187DD` | `0x187DE-0x1881D` |
| Child | `0x1881E-0x1885D` | `0x1885E-0x1889D` |
| Dog | `0x1889E-0x188DD` | `0x188DE-0x1891D` |
| Chicken | `0x1891E-0x1895D` | `0x1895E-0x1899D` |
| Frog | `0x1899E-0x189DD` | `0x189DE-0x18A1D` |

#### Egghead and dog duplicates (investigation)

Egghead and dog each appear twice in the input ROM. The other six idle NPCs have no second copy. All four 64-byte frames match byte for byte:

| Sprite | Idle NPC copy | Enemy copy |
|---|---|---|
| Egghead frame 1 | `0x1869E` | `0x0E25A` |
| Egghead frame 2 | `0x186DE` | `0x0E29A` |
| Dog frame 1 | `0x1889E` | `0x0E2DA` |
| Dog frame 2 | `0x188DE` | `0x0E31A` |

Static reference scan of the input ROM (read-only):

- **Enemy copies are referenced.** Each is the source of a VRAM-load record. A record is six bytes: a little-endian VRAM destination, a byte length, and a CPU source address. This layout was inferred from neighboring records and has not been checked against the code that reads them.
  - Dog record at `0x0C3BE`: destination `0x8200`, length `0x0080`, source `0x62DA`. It is part of a six-record list at `0x0C3BE-0x0C3E1`.
  - Egghead record at `0x0C434`: destination `0x8200`, length `0x0080`, source `0x625A`. It is part of a four-record list at `0x0C434-0x0C44B`.
  - Length `0x80` is 128 bytes, which is two 64-byte frames, matching the two-frame animation.
- **Idle copies are not referenced directly.** No pointer in the ROM holds their CPU addresses (`0x469E`, `0x489E`). They may be reached through computed addressing, or they may be unused.
- **The list starts have no direct pointers.** The lists are reached indirectly. The routine that reads them has not been found.

Status: unresolved. It is not known whether the idle copies are used, whether either copy is dead, or which list runs in each context. A runtime read trace in an emulator would settle this. The existing trace scripts use PyBoy, which is not installed in this environment. The scan scripts are in the gitignored `scratch/rom-trace/` folder (`npc_refs.py` and `vram_records.py`).

For art tooling, the NPC sheet dumps only the enemy copies, and `inject-art npc` writes each edited frame to both copies.

### Boss sprites (tentative)

The range `0x18A1E-0x1A6AD` (7,312 bytes, exactly 457 16-byte 2bpp tiles) holds the bosses of the game. The rendered sample shows large tile artwork rather than code or text. It is marked as known in `--highlight-known`.

The addresses are tentative. Individual boss boundaries, their animation frames, and the tables that reference them have not been traced, so this section does not list per-boss offsets. The range ends where the title-screen art begins at `0x1A6AE`.

### World-map screen graphics and layouts

The map screen uses two 20×13 tile layouts in physical ROM bank 5, along with a set of 90 2bpp tiles at `0x17185-0x17724`. These are **overview screen graphics**, not the individual playable rooms or their collision data.

| Physical ROM range (inclusive) | Contents |
|---|---|
| `0x17185-0x17724` | 90 2bpp tiles loaded at VRAM `0x8900`, corresponding to tile IDs `0x90-0xE9` |
| `0x17725-0x1782D` | First map layout: header, 260 tile IDs, and a zero terminator |
| `0x1782E-0x17936` | Second map layout: header, 260 tile IDs, and a zero terminator |

Both layouts begin with `0D 14 00 9C`: 13 rows, 20 columns, and destination `0x9C00` in little-endian order. The tile IDs are row-major: the first layout's IDs are at `0x17729-0x1782C`, and the second's at `0x17832-0x17935`. Both end with `00`. Rendering the IDs against the tile set above produces two different bordered world-map images. The first includes more roads and a settlement at the lower right; the second has a different terrain and road arrangement. Their geographic names and the in-game condition choosing each layout are not yet established.

The loader supports this interpretation independently of the rendered images. Fixed-bank code at `0x18DE` selects bank 5 and copies `0x05A0` bytes from CPU address `0x7185` to VRAM `0x8900`. Bank-6 code at physical `0x1B767` selects CPU pointer `0x7725` or `0x782E`; the path at `0x1B77D` passes it to the fixed-bank wrapper at `0x18C4`, which selects bank 5 and calls the loader at `0x0A78`. That loader reads the dimensions and destination, copies each row, and advances the destination by `0x20` bytes per row. Later code in the same path can apply additional VRAM updates; the base layouts alone do not necessarily show every marker or label.

The graphics are shaded blue and the two layout records are shaded green by `--highlight-known`.

Tiles within the range, aligned to that grid:

| Physical ROM range | Contents |
|---|---|
| `0x176C5-0x176D4` | Right-facing arrow |
| `0x176D5-0x176E4` | Left-facing arrow |
| `0x176E5-0x176F4` | "ED" symbol (the "end" key when entering the player's name) |
| `0x176F5-0x1770C` | Blank or near-blank tiles, not identified |
| `0x17715-0x17724` | Downward cursor, likely the prompt to press A to continue scrolling text (interpretation unconfirmed) |

Some tiles in the set have not been individually identified; the repeated patterns include terrain and border details visible in the reconstructed maps.

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

The `./rc2t render-graphics` command groups every four consecutive tiles in a supplied range into a 16×16 image, using the observed column-first order (top-left, bottom-left, top-right, bottom-right). For example, `./rc2t render-graphics 0x9106 0xB566 output/graphics.png` renders the main batch as an experimental sprite sheet. This uniform grouping is intended to help spot other sprites; it does not reconstruct the game's actual sprite/tile maps or palettes. An incomplete final group is padded with lilac empty quadrants, so missing data is distinct from real white pixels. Add `--stacked-glyphs` to decode each 16-byte tile as two stacked 1bpp glyphs instead, as described above.

## Character stat and ability tables

The right-margin annotations in [rc2.hex](./rc2.hex) identify these tables by matching values to known character stats at each level. All 8,192 rows of the dump were compared with the local ROM and their bytes matched. These are annotated identifications, not yet verified by tracing the game's table-reading code. All ranges below are inclusive physical ROM offsets in **bank 5**; subtract `0x10000` for the CPU address when bank 5 is selected.

Each listed table has 16 entries, ordered as levels 1 through 16 according to the annotations and the repeating layout. Values are raw hexadecimal bytes, not decimal: e.g. `1E` is decimal 30. For multi-byte records, a slash separates fields within one level; spaces separate successive levels. The byte order and field labels follow the margin notes; uncertain fields are retained as such.

The `./rc2h dump-stats` command reads these ranges from the working ROM by default, or from a supplied ROM or `.hex` dump, and writes `working/stats.txt`. Each line is one array, `name: [v1, ..., v16]`, with decimal values for levels 1 through 16 in level order. Names are `<character>_hp`, `<character>_mp`, and `<character>_<ability>_<field>` for each ability field. The standalone damage table is `zold_specialblade_damage`, separate from `zold_darkblade_damage`. The two paired-byte lookup tables are flattened into 16 values, one per byte. The repeated bytes in Lane's healing and Lora's heal are named `unknown_1` and `unknown_2` because their roles are uncertain; other `unknown` fields are likewise unidentified. The table labels below retain the original annotation names. The tentative table boundaries and field interpretations below also apply to these arrays.

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

These lookup tables and the character stat and ability tables above are shaded in green by `--highlight-known`.

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
| Maps / collision / encounters | Two world-map overview layouts and their graphics are identified above. Playable room layouts, collision, and encounters have no confirmed ROM offsets or formats yet. |
| Text / character graphics | The cartridge title is at `0x0134-0x0143`; title-screen graphics in bank 6 and character graphics in bank 2 are documented above. The title screen's tilemap is the bank-4 record stream at `0x7C30`, written to the BG map by `0x0A78` (see the title-screen graphics section). The routines that consume text and the routines that consume other graphics descriptors remain unidentified. Known text ranges are listed in [the known-text document](./known-text.md). |
| Audio / music / sound effects | No code or data ranges identified yet. Game Boy sound registers are in `0xFF10-0xFF3F`, but that hardware fact does not identify the ROM routines or music data. |

## Next steps to turn this into a byte-level map

1. Disassemble from the confirmed vectors and startup entry, tracking the active MBC2 ROM bank at each call and data read.
2. Follow pointers and callers into banks 1-7; distinguish code, pointer tables, graphics/tilemaps, map/collision data, text, and audio by their consumers and decoding routines before assigning names.
3. Use an emulator debugger to connect observed saved fields to live RAM addresses and ROM read/write routines.
4. Add each variable or asset range with the evidence used to identify it (write site, read site, pointer, controlled change, or decoded output).
