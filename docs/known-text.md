# Rolan's Curse II (USA) known text

The identified ranges are physical ROM offsets with exclusive end addresses.
Run `./rc2t dump-text` to decode them from the ROM into
`output/known-text.txt`. The exact range list, including overlapping
fragments, is maintained in [dump_text.py](../bin/dump_text.py). The
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
| `0x26` | `-` (dash), inferred from `boomer-ang` and mapped at the user's request |
| `0x27` | Period, confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x28` | Probably a comma; interpretation remains tentative, although the alphabet tables support it |
| `0x29` | `?`, confirmed by the alphabet tables |
| `0x2A` | `!`, confirmed by the alphabet tables |
| `0x2B` | `-` (hyphen), confirmed by the user and the alphabet tables |
| `0x2D` | `:`, confirmed by speaker labels |
| `0x30` | Space, inferred from its use between words in `licensed by nintendo` and `american sammy corp.` |
| `0xFD` | Line break, confirmed by the user from the game's display; rendered as `+` |
| `0xFE` | Space, identified by the user from `chr change` at `0x04C77-0x04C81` |
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
continuous string in `output/rom-text.txt`. `./rc2t dump-text` instead
outputs the selected ranges, one per line with padded start and exclusive end
offsets. By default, both render unknown bytes as distinct placeholders indexed
by byte value; the title range in `dump-text` uses ASCII for printable bytes.
For `render-text`, `--known-only` replaces unknown bytes with `_`, and
`--omit-sprites` replaces bytes in the known graphics ranges with `%`. Both
options can be combined with `--wrap`.
Placeholder symbols avoid the 1bpp font's characters and known glyphs. The
pool and exact mapping are defined in [render_text.py](../bin/render_text.py).

## Cartridge title

The ASCII cartridge title and its padding are at `0x0134-0x0144`.

## Dialogue and story text

The candidate dialogue and story ranges are mostly `0xFF`-terminated. They
were identified by a heuristic text scan, which may miss strings containing
placeholders or control codes. Pointers to the strings have not been traced,
so their consumers are unconfirmed. Some documented candidate starts are
inside longer strings, and the dump retains those overlapping fragments.

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
| `0x050CB-0x050E7` | Alphabet table. |
| `0x05109-0x0511B` | Alphabet table. |
| `0x058EB-0x0590F` | Alphabet table with repeated letters. |
| `0x13D3B-0x13D40` | `start`. |
| `0x13D42-0x13D4A` | `continue`. |
| `0x13D60-0x13D74` | `licensed by nintendo`. |
| `0x13D88-0x13D9C` | `american sammy corp.`. |
| `0x17C8D-0x17CF4` | Place names |
| `0x17D08-0x17D12` | Input-name screen label `input name`. |
| `0x17D4E-0x17D6F` | Alphabet and punctuation table; the first string, from `a` through the space after `-`, is the input-name screen keyboard. |
| `0x17D70-0x17D80` | Alphabet table followed by one selection byte. |
| `0x1B315-0x1B32E` | Character names separated by `0xFE`. |
| `0x1B32E-0x1B331` | Character level abbreviation `lv.`. |
| `0x1B9A1-0x1B9C7` | Concatenated party-menu prompts and a trailing `0x04` byte. |
| `0x1BD4E-0x1BD6F` | Same as `0x17D4E-0x17D6F`. |
| `0x1BD70-0x1BD80` | Same as `0x17D70-0x17D80`. |

### Place-name fragments

These labels are concatenated within `0x17C8D-0x17CF4`; the leading `w`
rendered before `graves` remains unverified.

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

## Ending credits decode ranges

Bytes starting at `0xBC86` are not machine code. The ranges
`0xBC86-0xBD1D` and `0xBD1E-0xBFAB` decode to English text using the table
above, but are not `#`-terminated strings. The last documented segment ends
at `0xBFAB`, with `0x2A` at `0xBFAC`. The bytes after that are control codes
and non-text data, up to a `0xFF` at `0xBFDB`. Where the credits data ends
and what reads these bytes is not yet traced.
