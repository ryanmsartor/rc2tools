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
| `0x27` | Period, confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x28` | Probably a comma; interpretation remains tentative, although the alphabet tables support it |
| `0x29` | `?`, confirmed by the alphabet tables |
| `0x2A` | `!`, confirmed by the alphabet tables |
| `0x2B` | `-` (hyphen), confirmed by the user and the alphabet tables |
| `0x2D` | `:`, confirmed by speaker labels |
| `0xFD` | Line break, confirmed by the user from the game's display; rendered as `+` |
| `0xFE` | Probable second line break, unconfirmed; rendered as `▎` |
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
offsets. Both render unknown bytes as distinct placeholders indexed by byte
value; the title range in `dump-text` uses ASCII for printable bytes.
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
- The candidate at `0x1BABA-0x1BACC` is unterminated. Its `0xFE` bytes
  render as `▎`; the trailing `0x01` renders as `%` and may be a period.
  The preceding `0x20` (rendered as `w`) is excluded.

## Name lists, party fragments, and alphabet tables

These are text-table data rather than sentences. The dump displays the raw
decoded bytes, including placeholders for unidentified separators and
selection bytes.

| Physical ROM range | Contents and observations |
|---|---|
| `0x4736-0x4823` | Ability and weapon names; ends with `0xD9`. Bytes `0x25`, `0x26`, and `0xD9` are unidentified. |
| `0x4998-0x49A9` | Range names; the leading `0x20` (rendered as `w`) is unverified. |
| `0x4A7C-0x4AC9` | Character and class names; ends with `0x9D`. |
| `0x050CB-0x050E7` | Alphabet table. |
| `0x05109-0x0511B` | Alphabet table. |
| `0x058EB-0x0590F` | Alphabet table with repeated letters. |
| `0x17C8D-0x17CF4` | Place names; the leading `0x20` (rendered as `w`) is unverified. |
| `0x17D4E-0x17D6F` | Alphabet and punctuation table supporting the character mapping. |
| `0x17D70-0x17D80` | Alphabet table followed by one selection byte. |
| `0x1B315-0x1B32E` | Character names separated by `0xFE`. |
| `0x1B9AA-0x1B9C7` | Party-message fragments separated by `0xFE` and an unmapped byte; ends with `0x04`. |
| `0x1BD4E-0x1BD6F` | Same as `0x17D4E-0x17D6F`. |
| `0x1BD70-0x1BD80` | Same as `0x17D70-0x17D80`. |

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
