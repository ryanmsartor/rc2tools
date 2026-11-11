"""Additional documented Rolan's Curse II (USA) physical ROM ranges.

All ends are exclusive. Point landmarks use one byte and do not imply that
the documented code or data ends there.
"""

from dump_text import TEXT_RANGES, TITLE_RANGE
from rom_stats import ABILITIES, ADDITIONAL_TABLES, CHARACTERS, LEVELS


LANDMARKS = (
    (0x0000, 0x0040, "Code", "Repeated short arithmetic/return sequences; purpose unknown"),
    (0x0040, 0x0041, "Code", "VBlank interrupt vector"),
    (0x0048, 0x0049, "Code", "LCD STAT interrupt vector"),
    (0x0050, 0x0051, "Code", "Timer interrupt vector"),
    (0x0058, 0x0059, "Code", "Serial interrupt vector"),
    (0x0060, 0x0061, "Code", "Joypad interrupt vector"),
    (0x0100, 0x0104, "Code", "Reset entry sequence"),
    (0x0104, 0x0134, "Header", "Nintendo logo data"),
    (0x0143, 0x0144, "Header", "Non-CGB flag; also title padding"),
    (0x0147, 0x0148, "Header", "Cartridge type: MBC2 with battery"),
    (0x0148, 0x0149, "Header", "ROM size code: 128 KiB"),
    (0x0149, 0x014A, "Header", "RAM-size code; MBC2 contains built-in RAM"),
    (0x0150, 0x0151, "Code", "Startup entry"),
    (0x01A4, 0x01AE, "Code", "Startup selects bank 1 and calls CPU address 0x5586"),
    (0x09DE, 0x09EC, "Code", "Selects and indexes bank-5 paired-byte lookup table; purpose unknown"),
    (0x0A78, 0x0A79, "Code", "Map layout loader entry"),
    (0x0CCB, 0x0CCC, "Code", "Bank-restore return path entry"),
    (0x0CD4, 0x0CD5, "Code", "Bank-1 selection helper entry"),
    (0x0D04, 0x0D05, "Code", "Bank-5 selection helper entry"),
    (0x0D3F, 0x0D40, "Code", "Bank selection helper entry; bank number in A"),
    (0x18C4, 0x18C5, "Code", "Bank-5 map-layout loader wrapper entry"),
    (0x18DE, 0x18DF, "Code", "Map graphics copy path selects bank 5"),
    (0x194F, 0x1951, "Code", "LDH operand at 0x1950 is not a CALL opcode"),
    (0x4ACB, 0x4ACC, "Data", "Pointer table; audited values are dereferenced in bank 5"),
    (0x4E77, 0x4F67, "Data", "Quarter-circle coordinate table; units and use unknown"),
    (0x4F67, 0x4F68, "Code", "Code following quarter-circle table"),
    (0x519D, 0x519E, "Code", "Bank-1 handler entry"),
    (0x5286, 0x5291, "Code", "Code overlay on bank-1 Hero graphics copy; ends in RET"),
    (0x5580, 0x5586, "Code", "Two JP stubs overlay bank-1 Hero graphics copy"),
    (0x5586, 0x5587, "Code", "Bank-1 startup call target"),
    (0x9024, 0x9064, "Data", "Eight presumed bank-2 graphics transfer descriptors"),
    (0x9064, 0x90B2, "Data", "Presumed six-byte graphics descriptors; loader unverified"),
    (0x90B2, 0x90B4, "Data", "Terminator for graphics descriptor list"),
    (0x90B4, 0x90E4, "Data", "Graphics descriptor list; record interpretation unverified"),
    (0x90E6, 0x9104, "Data", "Graphics descriptor list; record interpretation unverified"),
    (0xB606, 0xB706, "Graphics", "Presumed graphics descriptor source range"),
    (0xB706, 0xB726, "Graphics", "Presumed graphics descriptor source range"),
    (0xB726, 0xB886, "Graphics", "Presumed graphics descriptor source range"),
    (0xB886, 0xB986, "Graphics", "Presumed graphics descriptor source range"),
    (0xB986, 0xBB06, "Graphics", "Stacked 1bpp glyph tiles; loader layout unverified"),
    (0x17185, 0x17725, "Graphics", "World-map screen 2bpp tiles, loaded at VRAM 0x8900"),
    (0x176C5, 0x176D5, "Graphics", "World-map tile: right-facing arrow"),
    (0x176D5, 0x176E5, "Graphics", "World-map tile: left-facing arrow"),
    (0x176E5, 0x176F5, "Graphics", "World-map tile: ED name-entry symbol"),
    (0x176F5, 0x1770D, "Graphics", "Blank or near-blank tiles; unidentified"),
    (0x17715, 0x17725, "Graphics", "Downward cursor; text-scroll use unconfirmed"),
    (0x17725, 0x1782E, "Data", "First world-map layout: header, 260 tile IDs, terminator"),
    (0x17729, 0x1782D, "Data", "First world-map layout tile IDs"),
    (0x1782E, 0x17937, "Data", "Second world-map layout: header, 260 tile IDs, terminator"),
    (0x17832, 0x17936, "Data", "Second world-map layout tile IDs"),
    (0x18110, 0x1811C, "Data", "Two presumed title-screen graphics descriptors; loader unverified"),
    (0x1A6AE, 0x1ABFE, "Graphics", "Title-screen graphics, first descriptor source"),
    (0x1ABFE, 0x1B0FE, "Graphics", "Title-screen graphics, second descriptor source"),
    (0x1B767, 0x1B768, "Code", "World-map layout selection path"),
    (0x1B77D, 0x1B77E, "Code", "World-map layout passed to fixed-bank wrapper"),
    (0x1C0F5, 0x1C10B, "Data", "Possible page-advance control sequence; unconfirmed"),
    (0x1E620, 0x1E647, "Data", "Unclassified control-byte run; possibly tile data, not confirmed text"),
    (0x1E66B, 0x1E6AC, "Data", "Unclassified control-byte run; possibly tile data, not confirmed text"),
)

HUD_TILES = (
    *tuple(f"HUD glyph {c}" for c in "0123456789HPMP"),
    "MP gauge start arrow", "HUD forward slash",
    "Two full MP bars", "One full and one empty MP bar", "Two empty MP bars",
    "One full MP bar", "One empty MP bar", "A-button icon", "B-button icon",
    "Rectangle variant 1", "Rectangle variant 2", "Rectangle variant 3",
    "Rightward cursor", "Downward cursor", "Period", "Thin forward slash", "Hyphen",
    "Text-box top-left corner", "Text-box top-middle", "Text-box top-right corner",
    "Text-box bottom-left corner", "Text-box bottom-middle", "Text-box bottom-right corner",
    "Text-box left-middle", "Text-box right-middle",
    "Special top-middle variant 1; usage unclear", "Special top-middle variant 2; usage unclear",
    "Text-box bottom-middle with downward cursor",
    "Small rightward cursor", "POW frame top-left corner", "POW frame top-right corner",
    "POW frame bottom-left corner", "POW frame bottom-right corner", "POW frame solid side",
    "LV. marker first tile", "LV. marker second tile",
)

GLYPH_PAIRS = (
    *tuple(f"{chr(a)} / {chr(a + 1)}" for a in range(ord("0"), ord("9"), 2)),
    *tuple(f"{chr(a)} / {chr(a + 1)}" for a in range(ord("A"), ord("Z"), 2)),
    "apostrophe / colon", "hyphen / period", "comma / question mark",
    "exclamation mark / short hyphen", "slash / thick right parenthesis",
    "right parenthesis / left parenthesis",
)

TEXT_LABELS = {
    0x41AF: "Pause-menu item selection label: itm",
    0x41BB: "Pause-menu character power label: pow",
    0x41C1: "Pause-menu map label: map",
    0x41C7: "Pause-menu save label: sav",
    0x43C3: "Character name: Pit",
    0x43CA: "Character name: Lane",
    0x43D3: "Character name: Kyle",
    0x43DB: "Character name: Jude",
    0x43E3: "Character name: Lee",
    0x43EA: "Character name: Lora",
    0x43F3: "Character name: Zold",
    0x4736: "Ability and weapon names; some separators unidentified",
    0x4998: "Range names; leading byte unverified",
    0x4999: "Range label: narrow",
    0x499F: "Range label: middle",
    0x49A5: "Range label: wide",
    0x49AB: "Range label: short",
    0x49B1: "Range label: long",
    0x4A7C: "Character and class names",
    0x4A7D: "Class name: knight",
    0x4A83: "Character name: Pit",
    0x4A87: "Class name: elf",
    0x4A8A: "Character name: Lane",
    0x4A8E: "Class name: cleric",
    0x4A94: "Character name: Kyle",
    0x4A98: "Class name: zombie",
    0x4A9E: "Character name: Jude",
    0x4AA2: "Class name: wizard",
    0x4AA8: "Character name: Lee",
    0x4AAC: "Class name: kungfu",
    0x4AB2: "Character name: Lora",
    0x4AB6: "Class name: cupid",
    0x4ABB: "Character name: Zold",
    0x4ABF: "Class name: master",
    0x4C77: "Character change label: chr change",
    0x50CB: "Alphabet table",
    0x5109: "Alphabet table",
    0x58EB: "Alphabet table with repeated letters",
    0xBC86: "Ending credits decode range; boundaries unverified",
    0xBD1E: "Ending credits decode range; boundaries unverified",
    0x17C8D: "Place names; leading byte unverified",
    0x17D4E: "Alphabet and punctuation table",
    0x17D70: "Alphabet table and selection byte",
    0x1B315: "Character names",
    0x1B9AA: "Party-message fragments",
    0x1BABA: "Unterminated party fragment; punctuation uncertain",
    0x1BD4E: "Alphabet and punctuation table",
    0x1BD70: "Alphabet table and selection byte",
    0x1CCE9: "Dialogue fragment candidate; start unconfirmed",
    0x1E20F: "NPC dialogue candidate",
    0x1E231: "NPC dialogue candidate",
    0x1E257: "Dog dialogue candidate",
    0x1E26F: "Chicken dialogue candidate",
    0x1E295: "Frog dialogue candidate",
}

BANK5_REFERENCE_POINTS = {
    0x025F: "Stores CPU pointer 0x5382; audited reader selects bank 5",
    0x0568: "Access to CPU 0x5382 after selecting bank 5",
    0x1D5C: "CPU pointer 0x5449; audited path selects bank 5",
    0x1EBD: "CPU pointer 0x53E1; audited callers select bank 5",
    0x1EE1: "CPU pointer 0x5459; audited path selects bank 5",
    0x1EF4: "CPU pointer 0x5489; audited path selects bank 5",
    0x1EFD: "CPU pointer 0x549B; audited path selects bank 5",
    0x1FA5: "CPU pointer 0x53E1; audited callers select bank 5",
    0x1FEE: "CPU pointer 0x54AD; audited path selects bank 5",
    0x1FF9: "CPU pointer 0x54CD; audited path selects bank 5",
    0x2018: "CPU pointer 0x54DF; audited path selects bank 5",
    0x2027: "CPU pointer 0x54FF; audited path selects bank 5",
    0x20A9: "CPU pointer 0x5511; audited path selects bank 5",
    0x2166: "CPU pointer 0x5541; audited path selects bank 5",
    0x2171: "CPU pointer 0x5541; audited path selects bank 5",
    0x300A: "CPU pointer 0x5308; audited path selects bank 5",
    0x300F: "CPU pointer 0x533F; audited path selects bank 5",
}


def text_label(start: int) -> str:
    if start >= 0x1E620:
        return "Unclassified control-byte fragment; not confirmed text"
    if 0x471B <= start < 0x4821 and start != 0x4736:
        return "Ability, weapon, or stat label fragment"
    return TEXT_LABELS.get(start, "Dialogue or story text candidate; boundaries and consumer unverified")


ROM_ANNOTATIONS = tuple(sorted((
    *LANDMARKS,
    *((offset, offset + 1, "Code", label) for offset, label in BANK5_REFERENCE_POINTS.items()),
    *((0xB566 + i * 0x10, 0xB576 + i * 0x10, "Graphics", label)
      for i, label in enumerate(HUD_TILES)),
    *((0xB986 + i * 0x10, 0xB996 + i * 0x10, "Graphics", f"Stacked 1bpp glyphs: {label}")
      for i, label in enumerate(GLYPH_PAIRS)),
    (TITLE_RANGE[0], TITLE_RANGE[1], "Text", "ASCII cartridge title and padding"),
    *((start, end, "Data" if start >= 0x1E620 else "Text", text_label(start))
      for start, end in TEXT_RANGES),
    *((0x17065 + i * LEVELS, 0x17065 + (i + 1) * LEVELS, "Table",
       f"{name.title()} HP by level; interpretation unverified")
      for i, name in enumerate(CHARACTERS)),
    *((0x170E5 + i * LEVELS, 0x170E5 + (i + 1) * LEVELS, "Table",
       f"{name.title()} MP by level; interpretation unverified")
      for i, name in enumerate(CHARACTERS)),
    *((offset, offset + LEVELS * len(fields), "Table",
       f"{name.title()} {ability.replace('_', ' ')} by level; fields: {', '.join(fields)}; interpretation unverified")
      for name, abilities in ABILITIES.items() for ability, offset, fields in abilities),
    *((offset, offset + entries * width, "Table",
       f"{name.replace('_', ' ')}; interpretation unverified")
      for name, (offset, entries, width) in ADDITIONAL_TABLES.items()),
)))
