# Rolan's Curse II (USA) known text

The identified ranges are physical ROM offsets with exclusive end addresses.
Run `./rc2h dump-text` to decode the selected ranges from the ROM into
`working/strings.txt`. The exact, non-overlapping range list is maintained in
[dump_text.py](../bin/dump_text.py). The
corresponding bytes are shaded yellow by `render-graphics --highlight-known`;
the graphics ranges are documented in [the ROM map](./rom-map.md).

When identifying additional ranges, update the dump's range list and the
highlighted text ranges in [render_graphics.py](../bin/render_graphics.py).
The dump includes both confirmed text and the unclassified runs noted below;
inclusion does not establish that a range is actually text.

## Character table

The table below is inferred from the decoded text and is not confirmed against
the game's text routine.

| Byte | Meaning |
|---|---|
| `0x0A-0x23` | `a`-`z` (`0x0A` = `a`) |
| `0xB2` | Space |
| `0x24` | Apostrophe |
| `0x26` | `=` in `dump-text` notation (the dash-like glyph in `boomer-ang`); maps back to `0x26` for injection |
| `0x27` | Period, confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x28` | Probably a comma; interpretation remains tentative, although the alphabet tables support it |
| `0x29` | `?`, confirmed by the alphabet tables |
| `0x2A` | `!`, confirmed by the alphabet tables |
| `0x2B` | `-` (hyphen), confirmed by the user and the alphabet tables |
| `0x2D` | `:`, confirmed by speaker labels |
| `0x30` | Space, inferred from its use between words in `licensed by nintendo` and `american sammy corp.` |
| `0xFD` | Line break, confirmed by the user from the game's display; rendered as `+` |
| `0xFE` | `_` in `dump-text` notation for this space byte, identified by the user from `chr change` at `0x04C77-0x04C81` |
| `0xFF` | End of a text segment; rendered as `#` |
| `0xE0-0xE3` | Hero name placeholder, rendered as `HERO` |
| Other bytes (`0xDF`, `0xE4`, `0xE5`, `0xEB`, `0xEC`, `0xEE`, `0x7D`, `0x84`, `0xBF`, `0x04`, and others) | Control codes; not resolved |

### Probable page-advance sequence

At `0x1C0F5-0x1C10B`, within the opening text beginning at `0x1C0C0`,
the run `EC xx ED xx EB 04` repeats four times (`xx` = `FF`, `BF`, `7E`,
`2D`). The user believes it is the control code that scrolls to the next page
when the player presses A. This is not yet verified against the game's text
routine, and the byte meanings are unconfirmed.

### Rendering

`./rc2t render-text` decodes every ROM byte with this table into one
continuous string in `output/rom-text.txt`. `./rc2h dump-text` instead
outputs the selected ranges, one per line with padded start and exclusive end
offsets to `working/strings.txt`. In its editable notation, `0xFE` is `_`,
`0x26` is `=`, and `0x2B` is `-`; this distinguishes the two dash-like bytes
and preserves the `0xFE` space encoding. Ordinary spaces represent `0xB2`,
except for the `0x30` space ranges listed below. By default, both render unknown
bytes as distinct placeholders indexed by byte value; the title range in
`dump-text` uses ASCII for printable bytes.
Dump ranges exclude `0xFF` end markers by their exclusive end address;
marker-only locations are not included as ranges.
For `render-text`, `--known-only` replaces unknown bytes with `_`, and
`--omit-sprites` replaces bytes in the known graphics ranges with `%`. Both
options can be combined with `--wrap`.
Placeholder symbols avoid the 1bpp font's characters and known glyphs. The
pool and exact mapping are defined in [render_text.py](../bin/render_text.py).
The full-ROM `render-text` command retains its existing glyph rendering, where
`0xFE` and `0x26` display as spaces and a dash, respectively.

### Space and injection encoding notes

The two `0x30` space ranges are exceptional and should retain that byte when
injecting new spaces:

| Physical ROM range | Text |
|---|---|
| `0x13D60-0x13D74` | `licensed by nintendo` |
| `0x13D88-0x13D9C` | `american sammy corp.` |

Ordinary spaces in dump notation map to `0xB2`, except in the two ranges above,
where they map to `0x30`. `./rc2h inject-text` reads the edited
`working/strings.txt`, requires every documented range exactly once, and
writes `working/injected.gb`. Shorter replacements are padded at the end with
the applicable space byte; the cartridge title uses ASCII spaces. An
overlong segment fails before the output ROM is written and reports the range,
maximum character count, and attempted character count. The ROM header and
global checksums are recalculated.

When a displayed character is ambiguous with an unknown-byte placeholder,
inject-text preserves the original byte if that character remains at its
original position. This lets an unedited dump be injected without changing
unknown bytes.

The injector only accepts characters found in non-title ranges of the dump of
the base input ROM. The cartridge title is excluded from character identity
validation but remains subject to range length validation. The allowed
character set is:

```text
" !'+,-.:=?HERO_abcdefghijklmnopqrstuvwxyz"
```

The surrounding double quotes delimit the list; its first character is a
space. Invalid-character errors include the offending character, attempted
range, and this dense allowed-character list.

## Cartridge title

The ASCII cartridge title and its padding are at `0x0134-0x0144`.

## Dialogue and story text

The candidate dialogue and story ranges are mostly `0xFF`-terminated. They
were identified by a heuristic text scan, which may miss strings containing
placeholders or control codes. Pointers to the strings have not been traced,
so their consumers are unconfirmed. Some candidate strings start within
longer ROM strings; dump ranges do not overlap.
Within `0x1C0C0-0x1E314`, ranges are split at unknown control-code sequences;
both the code bytes and payload bytes are excluded from dumping and highlighting.
The exact fragments are maintained in [dump_text.py](../bin/dump_text.py).

- The candidate at `0x1CCE9-0x1CCFD` begins with two spaces; its start is not
  yet confirmed.
- `0x1E20F-0x1E231` and `0x1E231-0x1E257` are NPC dialogue.
- `0x1E257-0x1E26F`, `0x1E26F-0x1E295`, and `0x1E295-0x1E2AB`
  correspond to dog, chicken, and frog NPCs, respectively.
- The candidate at `0x1BABA-0x1BACC` contains `hasleft the party`, followed by
  a trailing `0x01` that renders as `%` and may be a period. The preceding
  `0x20` (rendered as `w`) is excluded.

## Menu labels, name lists, party fragments, and alphabet tables

These are text-table data rather than sentences. The dump displays the raw
decoded bytes, including placeholders for unidentified separators and
selection bytes.

The eight item-name fragments below form the names of four inventoried items,
split into two words each: **Large Potions**, **Fairy's Tears**, **Magic Ball**,
and **Fairy Wings**. The ranges include surrounding `0xFE` spaces but exclude
adjacent non-space control bytes. For adjacent fragments, space ownership
follows the user's choices; see the ranges for exact boundaries.

| Physical ROM range | Contents and observations |
|---|---|
| `0x040A2-0x040AC` | `large`, with surrounding spaces. |
| `0x040B0-0x040BC` | `potions`, with surrounding spaces. |
| `0x040CC-0x040D6` | `fairy's`, with surrounding spaces. |
| `0x040DA-0x040E6` | `tears`, with surrounding spaces. |
| `0x040F6-0x04100` | `magic`, with surrounding spaces. |
| `0x04104-0x04110` | `ball`, with surrounding spaces. |
| `0x04120-0x0412A` | `fairy`, with surrounding spaces. |
| `0x0412E-0x0413A` | `wings`, with surrounding spaces. |
| `0x041AF-0x041B3` | Pause-menu `itm`: select items. |
| `0x041BB-0x041BF` | Pause-menu `pow`: view character power levels. |
| `0x041C1-0x041C5` | Pause-menu `map`: view the map. |
| `0x041C7-0x041CB` | Pause-menu `sav`: save the game. |
| `0x043C3-0x043CA` | Character name `pit`. |
| `0x043CA-0x043D3` | Character name `lane`. |
| `0x043D3-0x043DB` | Character name `kyle`. |
| `0x043DB-0x043E3` | Character name `jude`. |
| `0x043E3-0x043EA` | Character name `lee`. |
| `0x043EA-0x043F3` | Character name `lora`. |
| `0x043F3-0x043FB` | Character name `zold`. |
| `0x4736-0x4823` | Ability and weapon name table; ends with `0xD9`. Individual fragments are listed below. Bytes `0x25` and `0xD9` are unidentified. |
| `0x4998-0x49A9` | Earlier partial range-name table; the leading `0x20` (rendered as `w`) is unverified, and the range ends inside `wide`. Individual complete labels follow. |
| `0x04999-0x0499F` | Range label `narrow`. |
| `0x0499F-0x049A5` | Range label `middle`. |
| `0x049A5-0x049AB` | Range label `wide`. |
| `0x049AB-0x049B1` | Range label `short`. |
| `0x049B1-0x049B7` | Range label `long`. |
| `0x4A7C-0x4AC9` | Character and class names; ends with `0x9D`. Individual names and classes are listed below. |
| `0x04C77-0x04C81` | Character change label `chr change`; `0xFE` is the space. |
| `0x050CB-0x050E7` | Alphabet table; documented and highlighted, but not included in `dump-text`. |
| `0x05109-0x0511B` | Alphabet table; documented and highlighted, but not included in `dump-text`. |
| `0x058EB-0x0590F` | Alphabet table with repeated letters; documented and highlighted, but not included in `dump-text`. |
| `0x13D3B-0x13D40` | `start`. |
| `0x13D42-0x13D4A` | `continue`. |
| `0x13D60-0x13D74` | `licensed by nintendo`. |
| `0x13D88-0x13D9C` | `american sammy corp.`. |
| `0x17D08-0x17D12` | Input-name screen label `input name`. |
| `0x17D4E-0x17D6F` | Alphabet and punctuation table; the first string, from `a` through the space after `-`, is the input-name screen keyboard. Documented and highlighted, but not included in `dump-text`. |
| `0x17D70-0x17D80` | Alphabet table followed by one selection byte; documented and highlighted, but not included in `dump-text`. |
| `0x1B311-0x1B315` | `pit ` (includes trailing space). |
| `0x1B315-0x1B319` | `lane`. |
| `0x1B319-0x1B31D` | `kyle`. |
| `0x1B31D-0x1B321` | `jude`. |
| `0x1B321-0x1B325` | `lee ` (includes trailing space). |
| `0x1B325-0x1B329` | `lora`. |
| `0x1B329-0x1B32D` | `zold`. |
| `0x1B32D-0x1B331` | ` lv.` (includes leading space). |
| `0x1B9A1-0x1B9C6` | Concatenated party-menu prompts through `member`. |
| `0x1BD4E-0x1BD6F` | Same as `0x17D4E-0x17D6F`; the only alphabet table included in `dump-text`. |
| `0x1BD70-0x1BD80` | Same as `0x17D70-0x17D80`; documented and highlighted, but not included in `dump-text`. |

### Place-name fragments

These labels are dumped as individual fragments from the concatenated
`0x17C8D-0x17CF4` region. The leading byte at `0x17C8D` and trailing byte at
`0x17CF3` are not included in the fragments; the leading `w` remains
unverified.

| Physical ROM range | Fragment |
|---|---|
| `0x17C8E-0x17C94` | `graves` |
| `0x17C94-0x17C9B` | `keepers` |
| `0x17C9B-0x17CA1` | `fields` |
| `0x17CA1-0x17CA7` | `castle` |
| `0x17CA7-0x17CAC` | `baroa` |
| `0x17CAC-0x17CB1` | `cadal` |
| `0x17CB1-0x17CB7` | `virgin` |
| `0x17CB7-0x17CBF` | `mushroom` |
| `0x17CBF-0x17CC5` | `duwane` |
| `0x17CC5-0x17CCB` | `metals` |
| `0x17CCB-0x17CD0` | `ruins` |
| `0x17CD0-0x17CD5` | `guild` |
| `0x17CD5-0x17CDC` | `fossils` |
| `0x17CDC-0x17CE3` | `canyons` |
| `0x17CE3-0x17CEB` | `farewell` |
| `0x17CEB-0x17CF3` | `dungeons` |

### Party-menu and party-status fragments

The first three prompts are concatenated without separators.

| Physical ROM range | Fragment |
|---|---|
| `0x1B9A1-0x1B9B3` | `your party is full` |
| `0x1B9B3-0x1B9C0` | `exchange your` |
| `0x1B9C0-0x1B9C6` | `member` |
| `0x1BA08-0x1BA0C` | `quit` |
| `0x1BABA-0x1BACB` | `hasleft the party` |

### Character and class fragments

These are individual text ranges within the existing `0x04A7C-0x04AC9`
table range; some fragments are adjacent without separators.

| Physical ROM range | Fragment |
|---|---|
| `0x04A7D-0x04A83` | `knight` |
| `0x04A83-0x04A87` | `pit` |
| `0x04A87-0x04A8A` | `elf` |
| `0x04A8A-0x04A8E` | `lane` |
| `0x04A8E-0x04A94` | `cleric` |
| `0x04A94-0x04A98` | `kyle` |
| `0x04A98-0x04A9E` | `zombie` |
| `0x04A9E-0x04AA2` | `jude` |
| `0x04AA2-0x04AA8` | `wizard` |
| `0x04AA8-0x04AAC` | `lee` |
| `0x04AAC-0x04AB2` | `kungfu` |
| `0x04AB2-0x04AB6` | `lora` |
| `0x04AB6-0x04ABB` | `cupid` |
| `0x04ABB-0x04ABF` | `zold` |
| `0x04ABF-0x04AC5` | `master` |

### Ability, weapon, and stat label fragments

These fragments have individual dump ranges; the existing broader table range
is also retained. Some labels are adjacent without separators. The dash in
`boomer-ang` is byte `0x26`, distinct from the `0x2B` hyphen.

| Physical ROM range | Fragment |
|---|---|
| `0x0471B-0x04721` | `damage` |
| `0x04722-0x04727` | `range` |
| `0x04728-0x0472E` | `range` |
| `0x0472F-0x04736` | `effect` |
| `0x04737-0x04740` | `pathmaker` |
| `0x04740-0x0474A` | `halfshield` |
| `0x0474A-0x04750` | `revive` |
| `0x04751-0x04759` | `nodamage` |
| `0x04759-0x04761` | `teleport` |
| `0x04761-0x04764` | `arc` |
| `0x04764-0x04769` | `sword` |
| `0x04769-0x04770` | `sabre` |
| `0x04770-0x0477C` | `electricball` |
| `0x0477C-0x04783` | `dagger` |
| `0x04783-0x0478D` | `boomer-ang` |
| `0x0478D-0x04794` | `bomb` |
| `0x04794-0x0479B` | `staff` |
| `0x0479B-0x047A1` | `shield` |
| `0x047A1-0x047A7` | `heal` |
| `0x047A7-0x047B0` | `bone` |
| `0x047B0-0x047B8` | `playdead` |
| `0x047B8-0x047BF` | `thunder` |
| `0x047BF-0x047C7` | `fireball` |
| `0x047C7-0x047D0` | `smashball` |
| `0x047D0-0x047D6` | `quake` |
| `0x047D6-0x047DE` | `sai` |
| `0x047DE-0x047E7` | `rapidfire` |
| `0x047E7-0x047EF` | `firework` |
| `0x047EF-0x047F5` | `arrow` |
| `0x047F5-0x047FB` | `heal` |
| `0x047FB-0x04804` | `wings` |
| `0x04804-0x0480D` | `darkblade` |
| `0x0480D-0x04819` | `specialblade` |
| `0x04819-0x04821` | `megaball` |

## Unclassified control-byte runs

The runs at `0x1E620-0x1E647` and `0x1E66B-0x1E6AC` are dense with
control bytes and do not decode to readable text. They were found by the scan
and may be tile data that happens to contain table bytes. The dump retains
the individual and overlapping ranges originally identified within them.

The candidate `0x1717C-0x17185` is not included in the dump or highlighting:
it resembles a list of letters rather than dialogue and remains unclassified
until its consumer is traced.

## Ending credits text ranges

These ROM areas contain English text separated by unknown control codes.
Each range below contains only contiguous text bytes; control codes are
excluded. The second area continues through `come!` at `0x0BFAD`, extending
past the former end at `0x0BFAB`. Control data follows, including a `0xFF` at
`0x0BFDB`; what reads these bytes is not yet traced.

| Physical ROM range |
|---|
| `0x0BC8A-0x0BCBD` |
| `0x0BCBE-0x0BCEC` |
| `0x0BCED-0x0BD16` |
| `0x0BD24-0x0BD54` |
| `0x0BD55-0x0BD64` |
| `0x0BD6B-0x0BDA0` |
| `0x0BDA1-0x0BDA7` |
| `0x0BDAE-0x0BDE0` |
| `0x0BDE1-0x0BE08` |
| `0x0BE0F-0x0BE3D` |
| `0x0BE3E-0x0BE55` |
| `0x0BE5C-0x0BE8F` |
| `0x0BE96-0x0BEC5` |
| `0x0BECC-0x0BEFE` |
| `0x0BF05-0x0BF32` |
| `0x0BF33-0x0BF64` |
| `0x0BF65-0x0BF98` |
| `0x0BF99-0x0BFAD` |
