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
| `0x0134-0x0144` | Cartridge header title |

## Dialogue

These are complete strings ending in `0xFF`, rendered as `#`. They were identified by scanning for runs of table bytes; the scan is heuristic and may miss strings containing placeholders or control codes. Pointers to these strings have not been traced, so their consumers are unconfirmed.

| Physical ROM range | Text | Notes |
|---|---|---|
| `0x1C32D-0x1C35E` | `stop at the house+of healing to +recover health.#` |  |
| `0x1C35E-0x1C3AE` | `you will find+many willing to+help you fight.▎choose your+companions+carefully!#` |  |
| `0x1C820-0x1C83D` | `you look weary.+please rest.#` |  |
| `0x1CAAB-0x1CAC5` | `learn more by+travelling.#` |  |
| `0x1CCE9-0x1CCFD` | `  i+loved him so...#` | Begins with two spaces; not yet confirmed as real. |
| `0x1CFAB-0x1CFC8` | `you look weary.+please rest.#` |  |
| `0x1D23D-0x1D26E` | `i guess no one+wants to be seen+with a zombie...#` |  |
| `0x1D362-0x1D382` | `was drawn into+his influence...#` |  |
| `0x1D3D0-0x1D3F1` | `there is no road+from here on...#` |  |
| `0x1D3F4-0x1D411` | `you look weary.+please rest.#` |  |
| `0x1DBE3-0x1DC00` | `you look weary.+please rest.#` |  |
| `0x1DD26-0x1DD55` | `i've been caring+for her until her+wings heal.#` |  |
| `0x1E20F-0x1E231` | `oh, i will wish+for your victory!#` | NPC dialogue; line break after `wish`. |
| `0x1E231-0x1E257` | `when i grow up i+want to be like+you!#` | NPC dialogue; line break after `up i`. |
| `0x1E257-0x1E26F` | `arf! it's a dog's+life!#` | Dog NPC. |
| `0x1E26F-0x1E295` | `cock-a-doodle-doo!+wake up, would ya!#` | Chicken NPC. |
| `0x1E295-0x1E2AB` | `croak! i'm no+prince!#` | Frog NPC. |
| `0x1E2E7-0x1E314` | `don't charge into+battle without+thinking...#` |  |


Unterminated candidate fragment (not a complete string) at `0x1BABA-0x1BACC`: `hasleft▎the▎party%`. Its `0xFE` bytes render as `▎`; trailing `0x01` renders as `%` and may be a period. The leading `0x20` (`w`) is excluded.

## Story text strings (0x1C0C0-0x1E314)

Each entry below is a complete `0xFF`-terminated string gathered from candidate starts found by the text scan in `output/text-scan.txt` (generated, git-ignored). The decode uses lowercase letters, `+` for `0xFD`, and placeholders for unmapped bytes. Ranges are end-exclusive and include the terminator rendered as the final `#`. Some entries overlap the dialogue table above.

| Physical ROM range | Text |
|---|---|
| `0x1C0C0-0x1C0F7` | `ages have passed+since the peaceful+land of rolan was╼#` |
| `0x1C10C-0x1C14A` | `released of the+evil king barius'+wicked curse...▎╺h╼:╽Ì╻%╼╏╽#` |
| `0x1C1AC-0x1C222` | `now the peace is+shattered as evil+events and▎terrible monsters+once again appear+in rolan...╻Ð╼┦╽┦╻*╼ù╽ù╻*╼:╽:╻*╺a▌%#` |
| `0x1C222-0x1C258` | `have you heard of+the legend of the+evil king barius?#` |
| `0x1C258-0x1C2A9` | `where are these+creatures coming+from?▎why are they+coming here?▎what can we do?#` |
| `0x1C2A9-0x1C2DA` | `every day i'm+scared.  how can i+live like this?#` |
| `0x1C2DA-0x1C32A` | `i can't play+outside because of+the monsters!▎when will those+monsters go away?#` |
| `0x1C32D-0x1C35E` | `stop at the house+of healing to +recover health.#` |
| `0x1C35E-0x1C3AE` | `you will find+many willing to+help you fight.▎choose your+companions+carefully!#` |
| `0x1C3AE-0x1C4B7` | `hey! you must be+that warrior!▎are you here to+get rid of the+monsters?▎i'm pit! i'm an+elf!▎can i join you?+let's fight+together!▎++    yes     no▊╇Ôreally? first we+should destroy +the monsters at▎the far end of+forest!▎╿%▀~╺epit has become+one of the+members.╻Ä#` |
| `0x1C4B7-0x1C4DC` | `ah, come on!+don't be a spoil+sport!#` |
| `0x1C4DC-0x1C567` | `oh goody, can we+go on adventures+again?▎++    yes     no▊╇Ô╿%╺epit╾┥Ôyou shouldn't get+mixed up with the+elf...▎he's a big+trouble maker!#` |
| `0x1C567-0x1C5C3` | `pit is such a+rascal.  he was+so mischievous▎that we took his+boomerang away to+punish him!#` |
| `0x1C5C5-0x1C6AA` | `pit:+i'm off to fight+the monsters in ▎the forest...+so, hand over my+boomerang!▎man:+not you again!+i said i'd give▎it back only if+you rid us of+these monsters,▎if i gave it to+you now, i bet you+would run away▎and do nothing!#` |
| `0x1C6AC-0x1C788` | `pit:+hey! i did it!▎i rid the forest+of monsters! now+give it to me!▎give me back my+boomerang!!!▎man:+you did what!?+no kidding?▎well, a promise +is a promise.+here you go...▎now, please try to+behave yourself!▀n╶%╺]╻Â#` |
| `0x1C788-0x1C7B6` | `how've you been?+don't pull any +more pranks!#` |
| `0x1C7B6-0x1C7DA` | `pit has been on +his best behavior!#` |
| `0x1C7DA-0x1C81D` | `pit's pranks are+cruel.  he blew+up my wall▎with one of his+bombs!#` |
| `0x1C820-0x1C83D` | `you look weary.+please rest.#` |
| `0x1C83D-0x1C84D` | `pit, take care!#` |
| `0x1C84D-0x1C94C` | `hi! i'm lane.+you look very+strong!▎join me and we+will go and fight+the monsters!▎++    yes     no▊'Ùok, let's go!+men in this town+are so helpless!▎we should destroy+the monsters in+the castle first.▎╿&▀[╺elane╾┥Ôwhat?  are you+wearing armor as+a joke?#` |
| `0x1C94C-0x1C9EC` | `i thought so!  you+couldn't go on+without me!▎++    yes     no▊ÛÙ╿&╺elane╾┥Ôyou look weary.+please rest.▎█▉&that's lane, i'm+training her to+be a great cleric!#` |
| `0x1C9EC-0x1CA4E` | `please look after+lane...▎█▉&i know you won't+listen, but try+not to be so▎stubborn all the+time!#` |
| `0x1CA4E-0x1CAC5` | `lane would be a+great cleric if+only she didn't▎have such a hot+temper! i hope+that she will▎learn more by+travelling.#` |
| `0x1CAC7-0x1CBD9` | `lane:+sir, i've beaten+the ghosts in the▎castle...+i think that i+can better use my▎skills out there!▎high cleric:+i see.  you want+to go forth and▎destroy evil?+i won't stop you.+remember to help▎those in distress.+for your journey,+i will give you▎the heal spell!▀o╶&╺]╻Â#` |
| `0x1CBD9-0x1CC2F` | `you've been out+travelling?  are+you nuts?▎the countryside+is crawling with+monsters!#` |
| `0x1CC2F-0x1CC8C` | `the monsters are+getting bolder+and stronger!▎soon they may+attack the town.+i am so scared!#` |
| `0x1CC8C-0x1CCB9` | `did you talk to+lane?  she is +really tough!#` |
| `0x1CCB9-0x1CCCE` | `lane, make us+proud!#` |
| `0x1CCD0-0x1CCFD` | `why, oh why did+kyle die?  i+loved him so...#` |
| `0x1CCFD-0x1CDCD` | `this town's most+prized treasure is+an ancient weapon!▎the thunder rod is+endowed with great+and awesome magic!▎we could've used+it at a time like+this!▎unfortunately, it+has been stolen by+a rogue magician!#` |
| `0x1CDCD-0x1CE92` | `late in the night,+the rogue magician+broke in here!▎he made off with+the thunder rod+and then ran to▎the graveyard!+kyle, a warrior,+chased after him.▎after that, kyle+was never heard+from again!#` |
| `0x1CE92-0x1CF23` | `kyle was a brave+warrior and a fine+man.  it's so sad!▎he must have been+defeated by that+magician...▎it's too dangerous+to go to the+graveyard!#` |
| `0x1CF23-0x1CFA8` | `legend has it that+when the thunder+rod is shaken,▎it will destroy+all monsters in+range and it will▎clear obstacles+from your path!#` |
| `0x1CFAB-0x1CFC8` | `you look weary.+please rest.#` |
| `0x1CFCA-0x1D028` | `you have the +thunder rod?! that+must mean...▎kyle, take the +rod and use it+for good causes!#` |
| `0x1D028-0x1D26E` | `how do i look? am+i scary? i was+once called kyle!▎i went after a +magician who stole+the thunder rod.▎the magician put+a curse on me and+made me a zombie!▎i can't even die,+so i'm resigned to+stay here...▎even though i got+the thunder rod+back, the magician▎removed the magic+power from it,+i must restore it!▎until then i may+not rest.  will+you help me?▎++    yes     no▊Íâgood! the rod is+buried in this +graveyard.▎after we've +conquered the+magician,▎we will return+here to dig up the+thunder rod and▎power it up!▎╿@▀]╺ekyle╾┥Ôi guess no one+wants to be seen+with a zombie...#` |
| `0x1D270-0x1D2C8` | `the thunder rod is+buried under here+... here it is!▎i've got the +thunder rod!▀p╶@╺]╻Â#` |
| `0x1D2C8-0x1D2FC` | `kyle:+the thunder rod is+useless without▎its magic!#` |
| `0x1D2FC-0x1D382` | `i wanted to be a+powerful magician+with the thunder▎rod, but the will+of barius entered+my mind and i▎was drawn into+his influence...#` |
| `0x1D382-0x1D3F1` | `make no bones+about it.  i'll be+happy to help!▎++    yes     no▊Íâ╿@╺ekyle╾┥Ôthere is no road+from here on...#` |
| `0x1D3F4-0x1D411` | `you look weary.+please rest.#` |
| `0x1D411-0x1D47C` | `the other day, a+sorcerer asked+about the tower...▎he was on a quest+for wisdom. he has+gone to the tower!#` |
| `0x1D47C-0x1D58B` | `i am a sorcerer.+my name is jude!▎i am searching for+the true secrets+of magic!▎i came inside to+find out if there+are secrets here!▎will you join my+quest?+    yes     no▊úågreat! the room+yonder may contain+ancient wisdom!▎╿*▀a╺ejude╾┥Ôwhere is your+thirst for wisdom?#` |
| `0x1D58B-0x1D61C` | `i'm jude's pupil.+he never teaches+me any useful▎magic! all he+cares about is his+dumb quest.▎have i come all+this way to be+left behind by▎him?#` |
| `0x1D61E-0x1D697` | `jude:+i'm leaving you+here.  i'm off on▎a grand adventure!▎student:+this is not fair!+you're going to▎leave me stranded?#` |
| `0x1D697-0x1D781` | `student:+master? you've +come back for me?▎i was so forlorn!▎╷*jude:+where did you get+that book?  fork▎it over, now!▎yow! the spells in+this book are very+hard to learn...▎i can figure out+some now, the rest+will need study!▀q╶*╺]╻Â#` |
| `0x1D781-0x1D7F8` | `student:+i want to go home!+i miss my mommy!▎how can i get out?▎╷*jude:+what a baby.  you+want out?  find it▎yourself!#` |
| `0x1D7F8-0x1D87E` | `ah! long time no+see! do you need+my magical help?▎++    yes     no▊úå╿*╺ejude╾┥Ôhi! he's still+so stingy with his+magical knowledge!#` |
| `0x1D87E-0x1D89B` | `yo! where did you+come from?#` |
| `0x1D89B-0x1D96B` | `greetings guys!+are you on a+quest?▎are you fighters?▎i'm out to fight+monsters too! do+you want to come?▎++    yes     no▊Ëéokay! let's get+going!▎╿_▀b╺elee╾┥Ôdon't you need+a fighter with my+type of skill?#` |
| `0x1D96B-0x1D9EA` | `hi ya! my skills+are always at your+disposal!▎++    yes     no▊Ëé╿_╺elee╾┥Ôthat martial arts+guy sure looks+like he can fight!#` |
| `0x1D9EA-0x1DB1C` | `elder master:+you must earn the+right to learn my▎secret technique!▎╷_lee:+how can i earn+the right master?▎master:+you must prove+your worth in▎battle!+only then will you+be deemed worthy!▎lee:+i will strive to+bring you honor,▎oh wise master!▎master:+one must listen+carefully to hear▎one hand clapping!#` |
| `0x1DB1C-0x1DBB6` | `master:+so, you return+with the smell of▎triumph on you!▎you are indeed+worthy of learning+this technique!▎hoo haa!▎╷_lee:+gee, it's so+simple...▀r╶_╺]╻Â#` |
| `0x1DBB8-0x1DBE0` | `lee:+master!▎master:+how are you doing?#` |
| `0x1DBE3-0x1DC00` | `you look weary.+please rest.#` |
| `0x1DC00-0x1DD26` | `it's a secret, but+i was sent by my+boss, venus!▎i'm lora.  i'm+supposed to help+save the world!▎during my quest,+my wings were hurt+in a scuffle!▎let's go get those+naughty monsters!+    yes     no▊[ílovely! when my+wings heal, i'll+be of real help!▎╿=▀c╺elora╾┥Ôoh pooh, i won't+be a burden!#` |
| `0x1DD26-0x1DD55` | `i've been caring+for her until her+wings heal.#` |
| `0x1DD57-0x1DDB5` | `lora:+you have been so+kind to me, i will▎continue my quest!▎elder person:+please be careful!#` |
| `0x1DDB7-0x1DE21` | `elder person:+i'm so glad that+you are fine!▎lora:+i will tell all i+meet of your great▎kindness!▀s╶=╺]╻Â#` |
| `0x1DE21-0x1DE52` | `i hope with your+powers, you can+save the world!#` |
| `0x1DE52-0x1DFDE` | `how is your quest+going.  do you+need my help?▎++    yes     no▊[í╿=╺elora╾┥Ôi'm zold, the+black knight!+i am on a quest...▎the sword i carry+is the grim sword.+the other half of▎the sword was+stolen by an evil+swordsman...▎when the two are+joined, the sword+is a great weapon!▎++    yes     no▊╌ïgrand!  without+the other half, my+spirit is empty!▎╿~▀d╺ezold╾┥Ôthen i must go on+my quest alone!#` |
| `0x1DFDE-0x1E17B` | `greetings to you!+can i be of+service?▎++    yes     no▊╌ï╿~╺ezold╾┥Ô╷~swordsman:+i thought that i+could control the▎sword's power...▎i wanted both+halves so i could+be unbeatable...▎it is clear to me+now that i would+have never been▎able to wield the+complete sword.+only the pure of▎spirit can use+the weapon without+being corrupted...▎ack, ack, ack!▂t┊ñ▎zold:+now the two blades+will be whole▎again...▀t╶~╺]╻Â#` |
| `0x1E17B-0x1E20F` | `we have heard of+great warriors+coming this way!▎barius is trying+to come back and+enslave the world!▎█▉=you must prevent+that from coming+to pass!#` |
| `0x1E20F-0x1E231` | `oh, i will wish+for your victory!#` |
| `0x1E231-0x1E257` | `when i grow up i+want to be like+you!#` |
| `0x1E257-0x1E26F` | `arf! it's a dog's+life!#` |
| `0x1E26F-0x1E295` | `cock-a-doodle-doo!+wake up, would ya!#` |
| `0x1E295-0x1E2AB` | `croak! i'm no+prince!#` |
| `0x1E2AB-0x1E314` | `the fate of the+world is in your+hands...╻*╼╏╽╏╻*╼┎╽┎╻*╼:╽:▎don't charge into+battle without+thinking...#` |

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

## Ending credits decode ranges

Bytes starting at `0xBC86` are not machine code. They decode to English text with the character table above, but these ranges are not `#`-terminated strings.

| Physical ROM range | Text |
|---|---|
| `0xBC86-0xBD1D` | `╴╻*╵evil king barius+is defeated and+his plot to regain╯his evil grasp on+the world is ended+for now..╯the warriors bid+farewell to each+other..╻└╼╏╻*╼` |
| `0xBD1E-0xBFAB` | `▌w╴╻*╵pit has returned+to his village,+and is again to╯his old pranks!╾m┍╴╻*╵lane is back in+her town using her+skills to help the╯needy.╾m┍╴╻*╵kyle will finally+find the peace+that he deserves.╯kyle's town has+holidays in his+memory.╾m┍╴╻*╵jude's search for+knowledge+continues with his╯only pupil at his+side.╾m┍╴╻*╵lee returns to his+town to teach the+ways of peace.╾m┍╴╻*╵lora leaves this+world with the+spirit of love.╾m┍╴╻*╵zold has retired+to a peaceful life+in his palace.╾m┍╴╻*╵HERO continues in+search of grand+adventures.╯the legend of HERO+and his great+struggle against╯the forces of evil+will be told and+retold for many╯generations to+com` |

The last credits segment ends at `0xBFAB`, with `0x2A` at `0xBFAC`. The bytes after that are control codes and non-text data, up to a `0xFF` at `0xBFDB`. Where the credits data ends and what reads these bytes is not yet traced.
