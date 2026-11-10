# Title-screen trace notes

This addendum records the experiments used to find how the title screen's tilemap is written, plus the open questions that remain. Major findings are summarized in the [ROM map](./rom-map.md#title-screen-graphics).

Labels: **verified** means the claim was checked against ROM bytes or live VRAM. **inferred** means it follows from disassembly or hook timing but has not been checked directly.

## Method

- **Emulator:** PyBoy 2.9.0, run from a venv outside the repository. The ROM is loaded from `input/Rolan's Curse II (USA).gb` (MBC2, 128 KiB).
- **Frame probes:** the BG map at `0x9800` was sampled each frame. Changes occur only in frames ~72–79. LCDC is `0xE3` during the title screen.
- **Hooks:** PyBoy code hooks at specific bank/address pairs logged PC, registers, and the active ROM bank. A hook patches the opcode byte to `0xDB`, so hooks must only be placed on instruction addresses, never on data.
- **ROM search:** a scan for `LD rr,nn` and `LD (nn),A`/`LD (nn),SP` whose target is `0x98xx` or `0x9Cxx` found 66 hits. Most are false positives where the operand bytes are data.
- **Static disassembly:** a partial SM83 disassembler (`sm83dis.py`) decodes the routines around each hook. It does not decode every opcode (`DI`, `EI`, and some others are unsupported).

The helper scripts live in `scratch/rom-trace/`, which is gitignored and local only. They are not part of the repository.

## Title tilemap (verified)

The title's BG map is written from a record stream in bank 4 at CPU `0x7C30` (physical offset `0x13C30`).

Record format, as decoded by the writer `0x0A78` (bank 0):

| Field | Size | Meaning |
|---|---|---|
| `rows` | 1 byte | Row count. `0` ends the stream. |
| `width` | 1 byte | Columns per row. |
| `dest` | 2 bytes, little-endian | Start address in the BG map. |
| tiles | `rows × width` bytes | Tile IDs, row-major. The destination advances by `0x20` per row. |

The stream at `0x7C30` is a single record, `12 14 00 98`: 18 rows × 20 columns at `0x9800`. The terminator follows at `0x7D9C`. HL after the stream is `0x7D9D`, which matches the terminator read.

Verification: the parsed grid matched live VRAM at frame 90 in all 360 cells (0 mismatches). `parse_tilestream.py` and `verify_tilemap.py` produce this check.

The top 13 rows form the art above the START/CONTINUE line, and this matches `TITLE_GRID` in [art_layout.py](../bin/art_layout.py). Rows 13–17 hold the menu text. Tile `0xD3` (copyright) sits in row 16, and the cursor is sprite 0 (tile `0xD4`), which is not in the tilemap. Tile `0x30` is blank filler, and `0x5A` is the most frequent tile.

## Call-order trace (verified hook timing)

Frames are PyBoy frame counts from the boot-up run.

| Frame | PC | Event |
|---|---|---|
| 66 | bank-0 `0x0153` | Trampoline target (see below). |
| 75 | bank-1 `0x01B4` | Trampoline target. |
| 76 | bank-1 `0x03D8` | Trampoline target. |
| 76 | bank-4 `0x7B8F` | Title init. Calls `0x075F` with A=`0x09`. |
| 77 | bank-4 `0x7B98` | Calls `0x075F` with A=`0x25`. |
| 79 | bank-4 `0x7B9D` | Trampoline target. |
| 79 | bank-4 `0x7BAE` | `LD HL,0x7C30`, then calls `0x0A78`, which writes the BG map. |
| 79 | bank-4 `0x7BB1` | Calls `0x7BFB`. Sets `FFC3=0xFF` and `FFC4=0x0010` as a counter (inferred). |
| 79 | bank-4 `0x7BB9` | Calls `0x0C9B`. |
| 80 | bank-4 `0x7BC5` | Calls `0x0636`. |
| 80 | bank-4 `0x7BCA` | Calls `0x1467`. |
| 80–90 | bank-0 `0x03C7`, `0x0438`, `0x0444` | Repeating loop with DE=`0006` and DE=`C0AA`. |

The tilemap write (`0x0A78`) happens before the calls to `0x7BFB` and `0x0C9B`. That ordering is verified by the hook sequence.

## Bank switching through the trampoline `0x0CCB` (verified)

`0x0CCB` is a fixed-bank routine. Its bytes are `F3 F1 EA FF 21 E0 8E FB C9`, which decode to `DI; POP AF; LD (0x21FF),A; LD HL,0x8EE0; EI; RET`.

- On entry the stack holds `[F][A = bank][target low][target high]`.
- `LD (0x21FF),A` writes the MBC2 ROM bank register. The MBC2 uses only the low nibble.
- `RET` jumps to the target. The routine is jumped to, not called, so no return address is left on the stack.
- Targets below `0x4000` ignore the bank number and always use bank 0.

Bank values seen during the intro were 00, 01, and 04. The bank-4 hook at `0x7B8F` fired at the decoded target, which supports this reading.

## Other routines

**Palette shadows (verified by the writes):**

- `FFC7` is the BGP shadow (`FF47`). Boot code writes `0x27` there.
- `FFC8` is the OBP0 shadow (`FF48`). Boot code writes `0x39` there.
- Bank-4 `0x7BA5` writes `0x2D` to both. Bank-4 `0x7BBE` writes `0xFF` to both.
- The title BGP is `0x2D` (inferred from the shadow write and consistent with the VRAM snapshot).

**VBlank and scroll loop (inferred from disassembly, not run-verified):**

- `0x0040` is the VBlank vector. It jumps to `0x039C` per the [ROM map](./rom-map.md#confirmed-code-landmarks).
- Bank-0 `0x03C7` sets bit 7 of `FF8A`, then pops registers and executes `RETI`. It appears to signal completion.
- Bank-0 `0x0411`–`0x0425` sets `FF8A=0x40`, executes `HALT`, waits for bit 7, then copies `FF9C` to SCX (`FF43`) and `FF9B` to SCY (`FF42`).
- Bank-0 `0x0438` compares the low nibble of `FFCA` with `0x0F`. If equal, it jumps to `0x0150`.
- Bank-0 `0x0444` calls `0x14F9`, then runs frame logic.

**Unidentified:**

- `0x075F` clears bit 7 of A, returns early if it equals `FFCD`, stores the value, and branches on the range of A (<`0x0B`, <`0x20`, otherwise) into `0x0CE0`, `0x0CEC`, or `0x0D10`, then to `0x0C2A`. Its purpose is not established.
- `0x0C9B`, `0x0636`, and `0x1467` have not been analyzed.
- `0x0D35` saves B, C, and A into `FF8B`–`FF8D`.

## Tile-data loader

The title tile blocks are at physical `0x1A6AE` (CPU `0x66AE` in bank 6, IDs `0x80`–`0xD4`, VRAM `0x8800`) and `0x1ABFE` (CPU `0x6BFE` in bank 6, IDs `0x30`–`0x7F`, VRAM `0x9300`). The descriptor list at `0x18110` is described in the [ROM map](./rom-map.md#title-screen-graphics).

The loader is bank-0 code at `0x077D`–`0x07BB`. For each record it calls the copy routine `0x0AD0`, which copies BC bytes from DE to HL with `LD A,(DE)` and `LD (HL+),A`, and does not switch banks.

- **Pointer table:** CPU `0x4000` in bank 6 (physical `0x18000`). Word `i` points to a record list. Word 5 (physical `0x1800A`) is `0x4110`.
- **Index:** `0x0C2A` computes HL = table + 2×A and loads that word. At `0x0785` the index is the caller's A minus `0x20`. The index logged at frame 77 was `05`. The caller passed `0x25` (inferred: bank-4 `0x7B98` calls `0x075F` with `A=0x25` at frame 77).
- **Records:** 6 bytes each: length (BC, little-endian), source (DE), VRAM destination (HL). A zero length ends the list (`00 00` at `0x1811C`). The title list has two records: `0x0550` from `0x66AE` to `0x8800`, and `0x0500` from `0x6BFE` to `0x9300`. Both were logged at frames 77 and 78.
- **Other lists:** the same loader ran other lists at frames 76–77 (lengths `0x80`, `0xF0`, `0x100`, `0x10`, to VRAM `0x8600`–`0x8F00`). Their contents are not identified.
- **Bank rule:** sources in bank 0 (`0x0000`–`0x3FFF`) are readable whatever bank is selected. `0x0D10`, reached from `0x0782`, loads `6` and writes it to `0x21FF`, the MBC2 ROM bank register. During the copy, CPU `0x4000`–`0x7FFF` therefore shows bank 6. A source in another bank there is read from bank 6 without any error. Whether bank 6 is restored after the copy has not been checked.
- **Length bit 7 (not analyzed):** when set, the loader takes a different path at `0x07A7`–`0x07B2` that writes `0xFF` before each byte. The title records do not use it.

### Redirect test (verified at frame 90)

`scratch/rom-trace/loader_redirect_test.py` changed record 1's source in a scratch ROM copy from `0x66AE` to `0x2000` (bank 0). VRAM `0x8800`–`0x8D4F` then held the bytes at file offset `0x2000`, and VRAM `0x9300` was unchanged. The source address in the record alone sets where the data comes from.

The tilemap still refers to tile IDs, so changing a destination also means changing the tile IDs in the bank-4 record stream to match.

### Addressing check (verified by arithmetic and VRAM)

LCDC is `0xE3`, so bit 4 is 0 and the BG uses signed tile addressing (base `0x9000`, with IDs `0x80`–`0xFF` read as negative). Under that rule:

- ID `0x80` → `0x8800`, which matches the first block's VRAM destination.
- ID `0x30` → `0x9300`, which matches the second block's VRAM destination.
- ID `0xD4` → `0x8D40`. This is the last tile of block 1, so block 1 is exactly 85 tiles (`0x80`–`0xD4`) and fills its `0x550` bytes.

The cursor is sprite 0 with tile `0xD4`. Sprites use unsigned addressing, so tile `0xD4` is also at `0x8D40`. The cursor and the BG tile `0xD4` therefore share bytes (inferred from the addressing rules, not run-verified).

### Tile replacement test (verified at frame 90)

`scratch/rom-trace/patch_tile_test.py` inverted the bytes of tile `0x5A` (physical `0x1AE9E`, VRAM `0x95A0`) in a scratch copy of the ROM. At frame 90 the VRAM at `0x95A0` held the inverted bytes, and the unpatched ROM still produced the original bytes. So the game copies the title tile bytes from their physical addresses at these positions, with no intermediate transformation.

This test checks only that these bytes are copied and shown on the title screen at frame 90. It does not show that no other screen reads the same bytes, or that the loader reads them the same way on every run.

### Limits on using replacement tiles (from code analysis; not yet tested)

- **Bank:** a source in bank 0 works from anywhere. A source in CPU `0x4000`–`0x7FFF` must be in bank 6, the bank the loader maps. Data in bank 4 or any other bank would be read as bank 6 data.
- **Contiguity:** each record copies one contiguous run, `BC` bytes from `DE` to `HL`. Tiles from several places need several records.
- **Record count:** the title list at `0x18110` has exactly two records and a terminator. Adding more means repointing pointer word 5 to a new list. That list is read through the same mapped bank, so it must also be in bank 0 or bank 6.
- **VRAM slot:** the destination in a record fixes the VRAM slot. The tilemap refers to slots by ID, so to show a new tile in a different slot the bank-4 stream at `0x7C30` must use the new IDs.
- **Shared tile:** the cursor sprite uses tile `0xD4`, the same bytes as BG tile `0xD4`, so changing that slot also changes the cursor.
- **Free space:** none is confirmed yet. Free runs in bank 0 or bank 6 have not been searched for.

## Dead ends

- **Bank-6 leads:** the table at `0x1BA40`, routines `0x71D0`, `0x720A`, and `0x727B`, and the decoder at `0x0E0B` did not run during the intro in any hook run. They are not the title writer.
- **ROM-search guesses:** `0x41E1`, `0x4217`, and `0x7A40` turned out to be data, not code.
- **Per-instruction hooks:** stepping every instruction with a hook pinned one CPU core at 100% and was too slow to be useful. Use hooks only on specific routines.

## Open questions

- Which routine reads the tile blocks, and how its tile IDs relate to the `0x0A78` tile IDs.
- What `0x075F` selects with A=`0x09` and A=`0x25`. The sound or track interpretation is a guess.
- Whether `0x03C7` is the actual VBlank completion path. The vector target `0x0040` has not been checked against the run.
- An earlier hook run logged `0x0CCB` being called from bank-0 `0x0170` with A stepping `0x13`, `0x26`, `0x39`, and DE=`C0AA`. A later run did not reproduce this. The caller chain and the meaning of A are unresolved.
- Whether the 306 logo cells counted earlier include the `0x30` filler. They probably do.
- Whether the copyright tile (`0xD3`) and cursor should be exported. The user said no for both.

## Tooling pitfalls

- PyBoy's `hook_register(bank, addr, cb, ctx)` patches the byte to `0xDB`. Hooks must be on instruction addresses. Do not deregister a hook from inside its callback.
- The register file exposes `A`, `B`, `C`, `D`, `E`, `F`, `HL`, `PC`, and `SP`. There are no `H`, `L`, `DE`, or `BC` attributes, so compose them.
- `memory[bank, addr]` reads banked ROM. `pyboy.tick(1, False)` advances one frame.
- Do not name a script `dis.py`. It shadows the standard library `dis` module and breaks NumPy.
