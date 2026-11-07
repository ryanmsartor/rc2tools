# Rolan's Curse II save file analysis

These observations come from [save file analysis.txt](./save%20file%20analysis.txt), which describes a hex-dumped `.sav` file, not the ROM or live CPU memory. They are experimental observations, not independently verified field definitions. The original notes are retained for reference.

## Address notation

The supplied example, `save_castlep2_pitlv7.hex`, shows 16 bytes per row, with the row's starting file offset on the left and columns `00` through `0F`. The notes' labels are consistent with concatenating the row and column: `2004` means row `0x20`, column `0x04`, or save-file offset `0x24`; `A006` means offset `0xA6`. The example's name bytes at `0xB0-0xB7` match the notes' `RY__` example, and `0x88` is `F6`, consistent with the filename's Pit level 7 and the notes' level-minus-one interpretation. These support the notation, but a single snapshot does not verify each field's meaning.

The tables retain the original labels and list their corresponding **save-file offsets**. These offsets are not ROM offsets or live CPU addresses. The emulator and precise save format are not yet identified.

## Example dump

The supplied `save_castlep2_pitlv7.hex` is a UTF-16 hex dump with 32 contiguous 16-byte rows, representing 512 bytes at file offsets `0x000-0x1FF`. The reconstructed bytes have SHA-256 `b43fa456603f9309925060d7fd79e6de14c27ab9c5417df8145baaa3b98feac7`; this is the hash of the represented save bytes, not of the text dump. This example is a snapshot, not a before/after comparison.

| Save offset | Dump bytes | Interpretation from notes |
|---|---|---|
| `0x024` | `F5` | Chest flags with low-nibble bits `1` and `4` set. |
| `0x064` | `F9` | Potion count: low nibble `9`. |
| `0x072` | `F1` | Controlled character: low nibble `1` (Pit). |
| `0x088` | `F6` | Pit level minus 1: low nibble `6` (level 7). |
| `0x0B0-0x0B7` | `FB F1 F2 F2 FE FF FE FF` | `RY__` using the notes' name table. |

Every byte in this example from `0x000` through `0x0B7` has an upper nibble of `F`; the observations above use the low nibble where applicable. This is consistent with the ROM's MBC2 nibble RAM, but the file is 512 bytes and bytes from `0x0B8` onward are not all of that form. Do not assume the whole file is nibble-normalized or that its layout can be directly mapped to CPU addresses without tracing.

## Progression and chests

`+1`, `+2`, `+4`, and `+8` describe changes recorded in the notes. They suggest bit flags but have not been independently tested as masks.

| Original label | Save offset | Observation |
|---|---|---|
| `0004` | `0x004` | `+1` after Shroom boss. |
| `0006` | `0x006` | `+1` after getting Lane. |
| `0008` | `0x008` | `+1` after Shroom boss. |
| `0009` | `0x009` | `+8` after getting boomerang. |
| `2004` | `0x024` | `+1` Hero chest 1 (starting fields northwest); `+4` Pit chest 5 (fields north after Cadal). |
| `200A` | `0x02A` | `+8` Pit chest 2 (west of Shroom); `+4` Pit chest 3 (north of Shroom); `+2` Hero chest 2 (north of Shroom); `+1` Hero chest 3 (northeast of Shroom). |
| `200B` | `0x02B` | `+1` Pit chest 1 (south of Shroom); `+2` Pit chest 4 (southeast of Shroom). |
| `3007` | `0x037` | `+8` Lane chest 2 (castle third screen); `+4` Lane chest 3 (castle north). |
| `3008` | `0x038` | `+2` Lane chest 1 (castle first screen); `+4` Hero chest 4 (castle first screen again); `+8` Lane chest 4 (castle part 2, first screen south). |
| `3009` | `0x039` | `+1` Pit chest 6 (castle part 2, first screen northeast); `+4` Lane chest 5 (castle part 2, screen 3). |
| `9000` | `0x090` | `+2` after getting boomerang. |
| `900C` | `0x09C` | `+4` after Shroom boss. |
| `900E` | `0x09E` | `+4` after getting Pit; `+8` after getting Lane. |

## Inventory, position, and party

| Original label | Save offset | Observation |
|---|---|---|
| `6004` | `0x064` | Potion count. |
| `6006` | `0x066` | Magic ball count. |
| `6007` | `0x067` | Wing count. |
| `6008` | `0x068` | Warp town: `0` start, `1` Cadal (Pit), `2` Baroa (Lane). |
| `600A` | `0x06A` | Character Y position on screen, in whole 8-pixel sprites. |
| `600B` | `0x06B` | Possibly area: `0` first town, `1` first field. |
| `600C` | `0x06C` | Character X position on screen, in whole 8-pixel sprites. |
| `600D` | `0x06D` | Possibly current screen. |
| `600E` | `0x06E` | Possibly tied to story progression. |
| `600F` | `0x06F` | Unclear; possibly tied to character and location. |
| `7000` | `0x070` | Facing direction. |
| `7002` | `0x072` | Controlled character: `0` Hero, `1` Pit, `2` Lane. |
| `7004` | `0x074` | Character ID in slot 2. |
| `7005` | `0x075` | Character ID in slot 3. |
| `800F` | `0x08F` | `1` as Hero, `0` as Pit; possibly facing direction. |
| `A006` | `0x0A6` | Y fraction: `F0` for no fraction, `F8` for half a sprite down. |
| `A007` | `0x0A7` | X fraction: `F0` for no fraction, `F8` for half a sprite right. |

## HP, MP, and levels

The notes call these "small" and "large" digits. The example has `FC` at `0x079`, so the low nibble can exceed 9; these are not necessarily decimal digits. The exact numerical encoding needs verification.

| Original label | Save offset | Observation |
|---|---|---|
| `7007` | `0x077` | Hero HP, small digit. |
| `7008` | `0x078` | Hero HP, large digit. |
| `7009` | `0x079` | Party member 2 HP, small digit. |
| `700A` | `0x07A` | Party member 2 HP, large digit. |
| `700B` | `0x07B` | Party member 3 HP, small digit. |
| `700C` | `0x07C` | Party member 3 HP, large digit. |
| `700F` | `0x07F` | Hero HP, small digit, as written in the notes. This may be a typo for MP because `8000` is recorded as Hero MP's large digit; verify before relying on it. |
| `8000` | `0x080` | Hero MP, large digit. |
| `8001` | `0x081` | Party member 2 MP, small digit. |
| `8002` | `0x082` | Party member 2 MP, large digit. |
| `8003` | `0x083` | Party member 3 MP, small digit. |
| `8004` | `0x084` | Party member 3 MP, large digit. |
| `8007` | `0x087` | Hero level minus 1. |
| `8008` | `0x088` | Pit level minus 1. |
| `8009` | `0x089` | Lane level minus 1. |

## Player name encoding

The notes identify `B000-B007` as the player name, using two bytes per character. The example's bytes at save offsets `0x0B0-0x0B7` match the `RY__` example below.

| Bytes | Character | Bytes | Character | Bytes | Character | Bytes | Character |
|---|---|---|---|---|---|---|---|
| `FA F0` | A | `FB F0` | B | `FC F0` | C | `FD F0` | D |
| `FE F0` | E | `FF F0` | F | `F0 F1` | G | `F1 F1` | H |
| `F2 F1` | I | `F3 F1` | J | `F4 F1` | K | `F5 F1` | L |
| `F6 F1` | M | `F7 F1` | N | `F8 F1` | O | `F9 F1` | P |
| `FA F1` | Q | `FB F1` | R | `FC F1` | S | `FD F1` | T |
| `FE F1` | U | `FF F1` | V | `F0 F2` | W | `F1 F2` | X |
| `F2 F2` | Y | `F3 F2` | Z | `F4 F2` | `'` | `F7 F2` | `.` |
| `F9 F2` | `?` | `FA F2` | `!` | `FB F2` | `-` | `FE FF` | Null or space |

Examples from the notes:

| Name | Bytes |
|---|---|
| `RY__` | `FB F1 F2 F2 FE FF FE FF` |
| `TYAN` | `FD F1 F2 F2 FA F0 F7 F1` |
| `?!'.` | `F9 F2 FA F2 F4 F2 F7 F2` |
| `-- .` | `FB F2 FB F2 FE FF F7 F2` |

The first example uses underscores to show the two blank positions. Whether `FE FF` is a space, a null, or both is unresolved.

## Next steps

1. Identify the emulator and exact save format; confirm the row/column interpretation against more of the original observations.
2. Compare before-and-after saves for one controlled change at a time, retaining both raw values and byte offsets. Verify flags by changing individual chests and progression events.
3. Test the suspected `700F` HP/MP typo and the uncertain position, area, and character flags.
4. Use an emulator debugger to relate save bytes to live RAM and the ROM routines that read and write them; do not assume the `.sav` layout is identical to CPU memory.
