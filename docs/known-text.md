# Rolan's Curse II (USA) known text

This document lists the text ranges identified so far. Each range is a physical ROM file offset, and each end address is exclusive. These are the ranges that `render-graphics --highlight-known` shades in yellow. Graphics are documented in [the ROM map](./rom-map.md).

## Character table

The table below is inferred from the decoded text and is not confirmed against the game's text routine.

| Byte | Meaning |
|---|---|
| `0x0A-0x23` | `a`-`z` (`0x0A` = `a`) |
| `0xB2` | Space |
| `0x24` | Apostrophe (`kyle's`) |
| `0x27` | `.` (`now...`, `other...`). Confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x28` | Probably a comma (`village, and`); not certain. Confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x29` | `?`, confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x2A` | `!` (`oh, i will wish for your victory!`). Confirmed by the alphabet tables at `0x17D4E` and `0x1BD4E` |
| `0x2B` | `-` (hyphen; `cock-a-doodle-doo`). Confirmed by the user and the alphabet tables |
| `0x2D` | `:`, confirmed by speaker labels such as `pit:` |
| `0xFD` | Line break (confirmed by the user from the game's text display). The renderer shows it as `+` |
| `0xFE` | Probable second line break, used between words in party messages such as `has left▎the▎party`. Not mapped, so it renders as `▎` |
| `0xFF` | End of a text segment; the renderer shows it as `#` |
| `0xE0-0xE3` | Hero name placeholder; the renderer shows the four-byte sequence as `HERO` |
| Other bytes (`0xDF`, `0xE4`, `0xE5`, `0xEB`, `0xEC`, `0xEE`, `0x7D`, `0x84`, `0xBF`, `0x04`, and others) | Control codes; not resolved |

### Probable page-advance sequence

At `0x1C0F5-0x1C10B`, inside the text that begins `ages have passed...` (`0x1C0C0`), the run `EC xx ED xx EB 04` repeats four times (`xx` = `FF`, `BF`, `7E`, `2D`). It renders as `.....` in `./rc2t render-text` output. The user believes it is the control code that scrolls to the next page when the player presses A. This is not yet verified against the game's text routine, and the byte meanings are unconfirmed.

### Rendering the whole ROM

`./rc2t render-text` decodes every byte of the ROM with the table above and writes one continuous string to `output/rom-text.txt`. Rules:

- Known letters are lowercase, `0xB2` is a space, and `0x28` is a comma.
- `0xE0-0xE3` render as `HERO`.
- `0xFF` renders as `#` (end of a text segment).
- `0xFD` renders as `+`, a line break; `0xFE` is not mapped and renders as `▎`.
- Bytes not yet in the table each get their own placeholder, so the output stays aligned with ROM offsets. The placeholder depends only on the byte value (`UNKNOWN_GLYPHS[byte]` in `bin/render_text.py`), so a byte keeps its symbol if it is mapped later. Symbols are chosen to avoid the 1bpp font's characters (digits, `A-Z`, and punctuation such as `? ! . : - ( ) /`). The pool is the ASCII symbols `^%&@*_=~[]{}<>|\`$`, then Latin-1 symbols `U+00A1-U+00FF`, then box-drawing and block characters `U+2500-U+259F`, taking the first 256.

## Cartridge title

| Physical ROM range | Text |
|---|---|
| `0x0134-0x0143` | Cartridge header title |

## Dialogue

These strings were found by scanning the ROM for runs of table bytes. In the rendered text, `#` represents `0xFF` and terminates the current string. The scan was a heuristic, so it may miss strings that contain placeholders or control codes. Pointers to these strings have not been traced, so the consumer of each one is not confirmed.

| Physical ROM range | Text | Notes |
|---|---|---|
| `0x1BABA-0x1BACC` | `hasleft▎the▎party%` | The `0xFE` bytes render as `▎`; trailing `0x01` renders as `%` and may be a period. The leading `0x20` (`w`) is excluded. This entry is not `0xFF`-terminated. |
| `0x1C32D-0x1C35E` | `stop at the house+of healing to +recover health.#` | |
| `0x1C35E-0x1C38B` | `you will find+many willing to+help you fight.` | |
| `0x1C820-0x1C83D` | `you look weary.+please rest.#` | |
| `0x1CAAB-0x1CAC5` | `learn more by+travelling.#` | |
| `0x1CCE9-0x1CCFD` | `  i+loved him so...#` | Begins with two spaces; not yet confirmed as real. |
| `0x1CFAB-0x1CFC8` | `you look weary.+please rest.#` | |
| `0x1D23D-0x1D26E` | `i guess no one+wants to be seen+with a zombie...#` | |
| `0x1D362-0x1D382` | `was drawn into+his influence...#` | |
| `0x1D3D0-0x1D3F1` | `there is no road+from here on...#` | |
| `0x1D3F4-0x1D411` | `you look weary.+please rest.#` | |
| `0x1DBE3-0x1DC00` | `you look weary.+please rest.#` | |
| `0x1DD26-0x1DD55` | `i've been caring+for her until her+wings heal.#` | |
| `0x1E2E7-0x1E314` | `don't charge into+battle without+thinking...#` | |
| `0x1E20F-0x1E231` | `oh, i will wish+for your victory!#` | NPC dialogue; line break after `wish`. |
| `0x1E231-0x1E257` | `when i grow up i+want to be like+you!#` | NPC dialogue; line break after `up i`. |
| `0x1E257-0x1E26F` | `arf! it's a dog's+life!#` | Dog NPC. |
| `0x1E26F-0x1E295` | `cock-a-doodle-doo!+wake up, would ya!#` | Chicken NPC. |
| `0x1E295-0x1E2AB` | `croak! i'm no+prince!#` | Frog NPC. |

Each `#` terminates the current string. Entries with multiple terminated strings are split at the terminators.

## Story text runs (0x1C0C0-0x1E314)

Every run below was found by the text scan in `output/text-scan.txt` (generated, git-ignored). The text is the `render-text` decode: lowercase, `+` for `0xFD`, `#` for `0xFF`, `.` for `0x27`, `?` for `0x29`, `!` for `0x2A`, `-` for `0x2B`, `:` for `0x2D`, and unknown-byte placeholders for unmapped bytes (for example, `▎` for `0xFE`). Ranges are end-exclusive. Each `#` terminates the string, so entries are split at `#`; unterminated strings and fragments end at the last byte in their documented range. Some runs share bytes with the dialogue table above, and some are fragments of longer strings. This list is an overcollection on purpose; the scan does not confirm each run is a complete string. Tile noise from the same region is not included.

| Physical ROM range | Text |
|---|---|
| `0x1C0C0-0x1C0F5` | `ages have passed+since the peaceful+land of rolan was` |
| `0x1C10C-0x1C13D` | `released of the+evil king barius'+wicked curse...` |
| `0x1C1AC-0x1C1D9` | `now the peace is+shattered as evil+events and` |
| `0x1C1DA-0x1C209` | `terrible monsters+once again appear+in rolan...` |
| `0x1C222-0x1C258` | `have you heard of+the legend of the+evil king barius?#` |
| `0x1C258-0x1C27E` | `where are these+creatures coming+from?` |
| `0x1C27F-0x1C298` | `why are they+coming here?` |
| `0x1C299-0x1C2A9` | `what can we do?#` |
| `0x1C2A9-0x1C2DA` | `every day i'm+scared.  how can i+live like this?#` |
| `0x1C2DA-0x1C307` | `i can't play+outside because of+the monsters!` |
| `0x1C308-0x1C32A` | `when will those+monsters go away?#` |
| `0x1C32D-0x1C35E` | `stop at the house+of healing to +recover health.#` |
| `0x1C35E-0x1C38B` | `you will find+many willing to+help you fight.` |
| `0x1C38C-0x1C3AE` | `choose your+companions+carefully!#` |
| `0x1C3AE-0x1C3CC` | `hey! you must be+that warrior!` |
| `0x1C3CD-0x1C3F5` | `are you here to+get rid of the+monsters?` |
| `0x1C3F6-0x1C40A` | `i'm pit! i'm an+elf!` |
| `0x1C40B-0x1C430` | `can i join you?+let's fight+together!` |
| `0x1C444-0x1C474` | `really? first we+should destroy +the monsters at` |
| `0x1C475-0x1C48B` | `the far end of+forest!` |
| `0x1C491-0x1C4B4` | `epit has become+one of the+members.` |
| `0x1C4B7-0x1C4DC` | `ah, come on!+don't be a spoil+sport!#` |
| `0x1C4DC-0x1C504` | `oh goody, can we+go on adventures+again?` |
| `0x1C522-0x1C54C` | `you shouldn't get+mixed up with the+elf...` |
| `0x1C54D-0x1C567` | `he's a big+trouble maker!#` |
| `0x1C567-0x1C593` | `pit is such a+rascal.  he was+so mischievous` |
| `0x1C594-0x1C5C3` | `that we took his+boomerang away to+punish him!#` |
| `0x1C5C5-0x1C5EB` | `pit:+i'm off to fight+the monsters in ` |
| `0x1C5EC-0x1C615` | `the forest...+so, hand over my+boomerang!` |
| `0x1C616-0x1C639` | `man:+not you again!+i said i'd give` |
| `0x1C63A-0x1C667` | `it back only if+you rid us of+these monsters,` |
| `0x1C668-0x1C699` | `if i gave it to+you now, i bet you+would run away` |
| `0x1C69A-0x1C6AA` | `and do nothing!#` |
| `0x1C6AC-0x1C6BF` | `pit:+hey! i did it!` |
| `0x1C6C0-0x1C6F0` | `i rid the forest+of monsters! now+give it to me!` |
| `0x1C6F1-0x1C70D` | `give me back my+boomerang!!!` |
| `0x1C70E-0x1C72D` | `man:+you did what!?+no kidding?` |
| `0x1C72E-0x1C75B` | `well, a promise +is a promise.+here you go...` |
| `0x1C75C-0x1C77F` | `now, please try to+behave yourself!` |
| `0x1C788-0x1C7B6` | `how've you been?+don't pull any +more pranks!#` |
| `0x1C7B6-0x1C7DA` | `pit has been on +his best behavior!#` |
| `0x1C7DA-0x1C805` | `pit's pranks are+cruel.  he blew+up my wall` |
| `0x1C806-0x1C81D` | `with one of his+bombs!#` |
| `0x1C820-0x1C83D` | `you look weary.+please rest.#` |
| `0x1C83D-0x1C84D` | `pit, take care!#` |
| `0x1C84D-0x1C870` | `hi! i'm lane.+you look very+strong!` |
| `0x1C871-0x1C89F` | `join me and we+will go and fight+the monsters!` |
| `0x1C8B3-0x1C8E2` | `ok, let's go!+men in this town+are so helpless!` |
| `0x1C8E3-0x1C916` | `we should destroy+the monsters in+the castle first.` |
| `0x1C924-0x1C94C` | `what?  are you+wearing armor as+a joke?#` |
| `0x1C94C-0x1C979` | `i thought so!  you+couldn't go on+without me!` |
| `0x1C998-0x1C9B4` | `you look weary.+please rest.` |
| `0x1C9B8-0x1C9EC` | `that's lane, i'm+training her to+be a great cleric!#` |
| `0x1C9EC-0x1CA05` | `please look after+lane...` |
| `0x1CA09-0x1CA36` | `i know you won't+listen, but try+not to be so` |
| `0x1CA37-0x1CA4E` | `stubborn all the+time!#` |
| `0x1CA4E-0x1CA7D` | `lane would be a+great cleric if+only she didn't` |
| `0x1CA7E-0x1CAAA` | `have such a hot+temper! i hope+that she will` |
| `0x1CAAB-0x1CAC5` | `learn more by+travelling.#` |
| `0x1CAC7-0x1CAEF` | `lane:+sir, i've beaten+the ghosts in the` |
| `0x1CAF0-0x1CB1A` | `castle...+i think that i+can better use my` |
| `0x1CB1B-0x1CB2C` | `skills out there!` |
| `0x1CB2D-0x1CB5A` | `high cleric:+i see.  you want+to go forth and` |
| `0x1CB5B-0x1CB8B` | `destroy evil?+i won't stop you.+remember to help` |
| `0x1CB8C-0x1CBC0` | `those in distress.+for your journey,+i will give you` |
| `0x1CBC1-0x1CBD0` | `the heal spell!` |
| `0x1CBD9-0x1CC03` | `you've been out+travelling?  are+you nuts?` |
| `0x1CC04-0x1CC2F` | `the countryside+is crawling with+monsters!#` |
| `0x1CC2F-0x1CC5C` | `the monsters are+getting bolder+and stronger!` |
| `0x1CC5D-0x1CC8C` | `soon they may+attack the town.+i am so scared!#` |
| `0x1CC8C-0x1CCB9` | `did you talk to+lane?  she is +really tough!#` |
| `0x1CCB9-0x1CCCE` | `lane, make us+proud!#` |
| `0x1CCD0-0x1CCFD` | `why, oh why did+kyle die?  i+loved him so...#` |
| `0x1CCFD-0x1CD33` | `this town's most+prized treasure is+an ancient weapon!` |
| `0x1CD34-0x1CD6C` | `the thunder rod is+endowed with great+and awesome magic!` |
| `0x1CD6D-0x1CD95` | `we could've used+it at a time like+this!` |
| `0x1CD96-0x1CDCD` | `unfortunately, it+has been stolen by+a rogue magician!#` |
| `0x1CDCD-0x1CE01` | `late in the night,+the rogue magician+broke in here!` |
| `0x1CE02-0x1CE32` | `he made off with+the thunder rod+and then ran to` |
| `0x1CE33-0x1CE64` | `the graveyard!+kyle, a warrior,+chased after him.` |
| `0x1CE65-0x1CE92` | `after that, kyle+was never heard+from again!#` |
| `0x1CE92-0x1CEC8` | `kyle was a brave+warrior and a fine+man.  it's so sad!` |
| `0x1CEC9-0x1CEF7` | `he must have been+defeated by that+magician...` |
| `0x1CEF8-0x1CF23` | `it's too dangerous+to go to the+graveyard!#` |
| `0x1CF23-0x1CF55` | `legend has it that+when the thunder+rod is shaken,` |
| `0x1CF56-0x1CF87` | `it will destroy+all monsters in+range and it will` |
| `0x1CF88-0x1CFA8` | `clear obstacles+from your path!#` |
| `0x1CFAB-0x1CFC8` | `you look weary.+please rest.#` |
| `0x1CFCA-0x1CFF7` | `you have the +thunder rod?! that+must mean...` |
| `0x1CFF8-0x1D028` | `kyle, take the +rod and use it+for good causes!#` |
| `0x1D028-0x1D05A` | `how do i look? am+i scary? i was+once called kyle!` |
| `0x1D05B-0x1D08E` | `i went after a +magician who stole+the thunder rod.` |
| `0x1D08F-0x1D0C3` | `the magician put+a curse on me and+made me a zombie!` |
| `0x1D0C4-0x1D0F5` | `i can't even die,+so i'm resigned to+stay here...` |
| `0x1D0F6-0x1D12A` | `even though i got+the thunder rod+back, the magician` |
| `0x1D12B-0x1D15E` | `removed the magic+power from it,+i must restore it!` |
| `0x1D15F-0x1D18C` | `until then i may+not rest.  will+you help me?` |
| `0x1D1A0-0x1D1CB` | `good! the rod is+buried in this +graveyard.` |
| `0x1D1CC-0x1D1F0` | `after we've +conquered the+magician,` |
| `0x1D1F1-0x1D222` | `we will return+here to dig up the+thunder rod and` |
| `0x1D223-0x1D22F` | `power it up!` |
| `0x1D23D-0x1D26E` | `i guess no one+wants to be seen+with a zombie...#` |
| `0x1D270-0x1D2A4` | `the thunder rod is+buried under here+... here it is!` |
| `0x1D2A5-0x1D2BF` | `i've got the +thunder rod!` |
| `0x1D2C8-0x1D2F0` | `kyle:+the thunder rod is+useless without` |
| `0x1D2F1-0x1D2FC` | `its magic!#` |
| `0x1D2FC-0x1D32F` | `i wanted to be a+powerful magician+with the thunder` |
| `0x1D330-0x1D361` | `rod, but the will+of barius entered+my mind and i` |
| `0x1D362-0x1D382` | `was drawn into+his influence...#` |
| `0x1D382-0x1D3B1` | `make no bones+about it.  i'll be+happy to help!` |
| `0x1D3D0-0x1D3F1` | `there is no road+from here on...#` |
| `0x1D3F4-0x1D411` | `you look weary.+please rest.#` |
| `0x1D411-0x1D443` | `the other day, a+sorcerer asked+about the tower...` |
| `0x1D444-0x1D47C` | `he was on a quest+for wisdom. he has+gone to the tower!#` |
| `0x1D47C-0x1D49D` | `i am a sorcerer.+my name is jude!` |
| `0x1D49E-0x1D4CB` | `i am searching for+the true secrets+of magic!` |
| `0x1D4CC-0x1D500` | `i came inside to+find out if there+are secrets here!` |
| `0x1D501-0x1D527` | `will you join my+quest?+    yes     no` |
| `0x1D52A-0x1D55C` | `great! the room+yonder may contain+ancient wisdom!` |
| `0x1D56A-0x1D58B` | `where is your+thirst for wisdom?#` |
| `0x1D58B-0x1D5BB` | `i'm jude's pupil.+he never teaches+me any useful` |
| `0x1D5BC-0x1D5E8` | `magic! all he+cares about is his+dumb quest.` |
| `0x1D5E9-0x1D616` | `have i come all+this way to be+left behind by` |
| `0x1D61E-0x1D645` | `jude:+i'm leaving you+here.  i'm off on` |
| `0x1D646-0x1D658` | `a grand adventure!` |
| `0x1D659-0x1D683` | `student:+this is not fair!+you're going to` |
| `0x1D684-0x1D697` | `leave me stranded?#` |
| `0x1D697-0x1D6C1` | `student:+master? you've +come back for me?` |
| `0x1D6C2-0x1D6D3` | `i was so forlorn!` |
| `0x1D6D6-0x1D6FE` | `jude:+where did you get+that book?  fork` |
| `0x1D6FF-0x1D70C` | `it over, now!` |
| `0x1D70D-0x1D743` | `yow! the spells in+this book are very+hard to learn...` |
| `0x1D744-0x1D778` | `i can figure out+some now, the rest+will need study!` |
| `0x1D781-0x1D7AD` | `student:+i want to go home!+i miss my mommy!` |
| `0x1D7AE-0x1D7C0` | `how can i get out?` |
| `0x1D7C3-0x1D7ED` | `jude:+what a baby.  you+want out?  find it` |
| `0x1D7EE-0x1D7F8` | `yourself!#` |
| `0x1D7F8-0x1D82A` | `ah! long time no+see! do you need+my magical help?` |
| `0x1D849-0x1D87E` | `hi! he's still+so stingy with his+magical knowledge!#` |
| `0x1D87E-0x1D89B` | `yo! where did you+come from?#` |
| `0x1D89B-0x1D8BE` | `greetings guys!+are you on a+quest?` |
| `0x1D8BF-0x1D8D0` | `are you fighters?` |
| `0x1D8D1-0x1D904` | `i'm out to fight+monsters too! do+you want to come?` |
| `0x1D918-0x1D92E` | `okay! let's get+going!` |
| `0x1D93B-0x1D96B` | `don't you need+a fighter with my+type of skill?#` |
| `0x1D96B-0x1D998` | `hi ya! my skills+are always at your+disposal!` |
| `0x1D9B6-0x1D9EA` | `that martial arts+guy sure looks+like he can fight!#` |
| `0x1D9EA-0x1DA1B` | `elder master:+you must earn the+right to learn my` |
| `0x1DA1C-0x1DA2D` | `secret technique!` |
| `0x1DA30-0x1DA55` | `lee:+how can i earn+the right master?` |
| `0x1DA56-0x1DA7A` | `master:+you must prove+your worth in` |
| `0x1DA7B-0x1DAA7` | `battle!+only then will you+be deemed worthy!` |
| `0x1DAA8-0x1DACE` | `lee:+i will strive to+bring you honor,` |
| `0x1DACF-0x1DADE` | `oh wise master!` |
| `0x1DADF-0x1DB08` | `master:+one must listen+carefully to hear` |
| `0x1DB09-0x1DB1C` | `one hand clapping!#` |
| `0x1DB1C-0x1DB44` | `master:+so, you return+with the smell of` |
| `0x1DB45-0x1DB54` | `triumph on you!` |
| `0x1DB55-0x1DB86` | `you are indeed+worthy of learning+this technique!` |
| `0x1DB92-0x1DBAD` | `lee:+gee, it's so+simple...` |
| `0x1DBB8-0x1DBC4` | `lee:+master!` |
| `0x1DBC5-0x1DBE0` | `master:+how are you doing?#` |
| `0x1DBE3-0x1DC00` | `you look weary.+please rest.#` |
| `0x1DC00-0x1DC30` | `it's a secret, but+i was sent by my+boss, venus!` |
| `0x1DC31-0x1DC60` | `i'm lora.  i'm+supposed to help+save the world!` |
| `0x1DC61-0x1DC92` | `during my quest,+my wings were hurt+in a scuffle!` |
| `0x1DC93-0x1DCC6` | `let's go get those+naughty monsters!+    yes     no` |
| `0x1DCC9-0x1DCFA` | `lovely! when my+wings heal, i'll+be of real help!` |
| `0x1DD08-0x1DD26` | `oh pooh, i won't+be a burden!#` |
| `0x1DD26-0x1DD55` | `i've been caring+for her until her+wings heal.#` |
| `0x1DD57-0x1DD80` | `lora:+you have been so+kind to me, i will` |
| `0x1DD81-0x1DD93` | `continue my quest!` |
| `0x1DD94-0x1DDB5` | `elder person:+please be careful!#` |
| `0x1DDB7-0x1DDE3` | `elder person:+i'm so glad that+you are fine!` |
| `0x1DDE4-0x1DE0E` | `lora:+i will tell all i+meet of your great` |
| `0x1DE0F-0x1DE18` | `kindness!` |
| `0x1DE21-0x1DE52` | `i hope with your+powers, you can+save the world!#` |
| `0x1DE52-0x1DE80` | `how is your quest+going.  do you+need my help?` |
| `0x1DE9F-0x1DECD` | `i'm zold, the+black knight!+i am on a quest...` |
| `0x1DECE-0x1DF04` | `the sword i carry+is the grim sword.+the other half of` |
| `0x1DF05-0x1DF31` | `the sword was+stolen by an evil+swordsman...` |
| `0x1DF32-0x1DF67` | `when the two are+joined, the sword+is a great weapon!` |
| `0x1DF7B-0x1DFAE` | `grand!  without+the other half, my+spirit is empty!` |
| `0x1DFBC-0x1DFDE` | `then i must go on+my quest alone!#` |
| `0x1DFDE-0x1E004` | `greetings to you!+can i be of+service?` |
| `0x1E025-0x1E052` | `swordsman:+i thought that i+could control the` |
| `0x1E053-0x1E063` | `sword's power...` |
| `0x1E064-0x1E094` | `i wanted both+halves so i could+be unbeatable...` |
| `0x1E095-0x1E0C7` | `it is clear to me+now that i would+have never been` |
| `0x1E0C8-0x1E0FA` | `able to wield the+complete sword.+only the pure of` |
| `0x1E0FB-0x1E12F` | `spirit can use+the weapon without+being corrupted...` |
| `0x1E130-0x1E13E` | `ack, ack, ack!` |
| `0x1E143-0x1E169` | `zold:+now the two blades+will be whole` |
| `0x1E17B-0x1E1AB` | `we have heard of+great warriors+coming this way!` |
| `0x1E1AC-0x1E1E0` | `barius is trying+to come back and+enslave the world!` |
| `0x1E1E4-0x1E20F` | `you must prevent+that from coming+to pass!#` |
| `0x1E20F-0x1E231` | `oh, i will wish+for your victory!#` |
| `0x1E231-0x1E257` | `when i grow up i+want to be like+you!#` |
| `0x1E257-0x1E26F` | `arf! it's a dog's+life!#` |
| `0x1E26F-0x1E295` | `cock-a-doodle-doo!+wake up, would ya!#` |
| `0x1E295-0x1E2AB` | `croak! i'm no+prince!#` |
| `0x1E2AB-0x1E2D4` | `the fate of the+world is in your+hands...` |
| `0x1E2E7-0x1E314` | `don't charge into+battle without+thinking...#` |

## Name lists, party fragments, and alphabet tables

These are not sentences, but they are text-table data. The decode shows `▎` where the byte has no mapping yet.

| Physical ROM range | Contents | Notes |
|---|---|---|
| `0x4736-0x4823` | `pathmaker, halfshield, revive, nodamage, teleport, arcsword, sabre, electricball, dagger, boomerang, bomb, staff, shield, heal, bone, playdead, thunder, fireball, smashball, quake, sai, rapidfire, firework, arrow, wings, darkblade, specialblade, megaball` | Ends with `0xD9`; bytes `0x25`, `0x26`, and `0xD9` are unidentified. |
| `0x4A7C-0x4AC9` | `knight, pit, elf, lane, clerick, kyle, zombie, jude, wizard, lee, kungfu, lora, cupid, zold, master` | Ends with `0x9D`. |
| `0x4998-0x49A9` | `narrow, middle` | The leading `0x20` (`w`) is unverified. |
| `0x17C8D-0x17CF4` | `graves, keepers, fields, castle, baroa, cadal, virgin, mushroom, duwane, metal, ruins, guild, fossils, canyons, farewell, dungeons` | The leading `0x20` (`w`) is unverified. |
| `0x1B315-0x1B32E` | `lane, kyle, jude, lee, lora, zold` | Names are separated by `0xFE`. |
| `0x1B9AA-0x1B9C7` | `y, is, full, exchange, your, member` | Words are separated by `0xFE` and an unmapped byte; ends with `0x04`. |
| `0x050CB-0x050E7` | `abcdefghijklmnopqrstuvwxyz'` | Alphabet table. |
| `0x05109-0x0511B` | `fghijklmnopqrstz'` | Alphabet table. |
| `0x058EB-0x0590F` | `abcdefcdefghijklmnopqropqrstuvwxyz'` | Alphabet table with repeated letters. |
| `0x17D4E-0x17D6F` | `abcdefghijklmnopqrstuvwxyz?!'.,-` | Alphabet table; matches the punctuation mapping in `render_text.py`. |
| `0x17D70-0x17D80` | `abcdefghijklmno` | Alphabet table followed by one selection byte. |
| `0x1BD4E-0x1BD6F` | `abcdefghijklmnopqrstuvwxyz?!'.,-` | Same as `0x17D4E`. |
| `0x1BD70-0x1BD80` | `abcdefghijklmno` | Same as `0x17D70`. |

`0xFE` is not in the `render_text.py` table; the decoder prints it as `▎`. Whether `0xFE` is a second line break is unconfirmed.

## Unclassified control-byte runs

These runs are dense with control bytes and do not decode to readable text. They were found by the scan and are listed so they are not lost. They may be tile data that happens to contain table bytes.

| Physical ROM range | Decode |
|---|---|
| `0x1E620-0x1E646` | `j&Öi^_ÛÁ^▎&┬i^_┓Á^▎_┇Á^&Åi^▎_┥Á^&┻i^+#` |
| `0x1E646-0x1E647` | `Â` |
| `0x1E66B-0x1E68A` | `x@Ê┃&▎@Ã┃&▎^╬y=b╗y^▌┊ö▎b╧y^▌┒ö#` |
| `0x1E68A-0x1E68B` | `h` |
| `0x1E68A-0x1E6AB` | `h@Ü┃&▎@l┃&@╥┃&▎^jy=^╃y=▎^ny=^╇y=#` |
| `0x1E6AB-0x1E6AC` | `%` |

Not included: `0x01717C-0x017185` decodes to `acdefhjlm`. It has the right byte shape but looks like a list of letters, not dialogue, so it is left unclassified until its consumer is traced.

## Ending credits

Bytes starting at `0xBC86` are not machine code. They decode to English text with the character table above.

| Physical ROM range | Text |
|---|---|
| `0xBC86-0xBD1D` | `╴╻*╵evil king barius+is defeated and+his plot to regain╯his evil grasp on+the world is ended+for now..╯the warriors bid+farewell to each+other..╻└╼╏╻*╼` |
| `0xBD1E-0xBFAB` | `▌w╴╻*╵pit has returned+to his village,+and is again to╯his old pranks!╾m┍╴╻*╵lane is back in+her town using her+skills to help the╯needy.╾m┍╴╻*╵kyle will finally+find the peace+that he deserves.╯kyle's town has+holidays in his+memory.╾m┍╴╻*╵jude's search for+knowledge+continues with his╯only pupil at his+side.╾m┍╴╻*╵lee returns to his+town to teach the+ways of peace.╾m┍╴╻*╵lora leaves this+world with the+spirit of love.╾m┍╴╻*╵zold has retired+to a peaceful life+in his palace.╾m┍╴╻*╵HERO continues in+search of grand+adventures.╯the legend of HERO+and his great+struggle against╯the forces of evil+will be told and+retold for many╯generations to+com` |

The last credits segment ends at `0xBFAB`, with `0x2A` at `0xBFAC`. The bytes after that are control codes and non-text data, up to a `0xFF` at `0xBFDB`. Where the credits data ends and what reads these bytes is not yet traced.
