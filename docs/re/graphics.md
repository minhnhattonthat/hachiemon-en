# Graphics text survey

Static sweep of every LZ block and raw gap from 0x2B0000 to the end of data, read by eye: `tools/gfxsweep.py ROM OUT --raw --lo 2B0000` (26 pages, 956 blocks) and `tools/gfxsweep8.py ROM OUT` (36 8bpp pictures with their own palettes). 355 tilemap-shaped blocks were skipped and printed by the script. Regions before 0x2B0000 got a sampled render only (one strip per 64 KB): no tile text seen.

Every row has a warp scene that unpacks its blocks: `tools/debug/gfxcover.py OUT` after a tour prints the row-to-scene map (`lz` lines of `tools/debug/lzlog.lua`). Phase 5's marker tour still has to look at each element on screen and add anything this list missed; "Confirmed" below means seen on a tour shot. Reading of the Japanese is from the sheets, so a few words may be approximate. All blocks are LZ77 4bpp unless noted.

The game also holds 1336 blocks in its own Le codec (`le_decompress` in `tools/gbacomp.py`; pages from `tools/lesweep.py`), mostly bitmaps and palettes. Rows 21-27 came from them. The phase 5 marker tour read a sample of shots, not every Le page, so phase 8 still has to read `tools/lesweep.py` pages 0-4 for anything lettered that this list missed.

| # | Screen / element | Source (ROM offset) | Tiles | Japanese seen | Notes |
|---|---|---|---|---|---|
| 1 | Title logo | 0x2F2E34 (8bpp) | 0x1DC | ハチエモン + "hachiemon" | **Keep** (D5). The block also holds ©2003 KTV / NAMCO in Latin: leave. |
| 2 | Title prompt | 0x2B7618 | 0x70 | すた〜とぼたんおして | Confirmed on title screen by eye. |
| 3 | Main menu, difficulty, save slot art | 0x2B4AE4, twin 0x2BCD3C | 0x321, 0x34B | めにゅ〜, はじめから, つづきから, おぷしょん, なんいど, ふつう, むずかしい, げきむず, せ〜ぶふぁいる, はい, いいえ... | Confirmed: `menu`, `menu_diff`, `menu_opts`. Only 0x2BCD3C is loaded (case 1 of 0x8048994); 0x2B4AE4 sits in slot 0 of table 0x81D5F5C and no code reads that slot, no tour unpacked it: **guess** unused, edit only 0x2BCD3C. |
| 4 | Menu help strips | 0x30E2E0, 0x30E61C, 0x30E944, 0x30EC44, 0x30EED0, 0x30F284, 0x30F64C, 0x30F980, 0x30FC44 | 0x2D each | めにゅ〜こうもくをえらんでや〜; わしといっしょにだいはっけん！; せっていをへんこうできるで〜; まだえらばんのん〜？; おんがくをならすかやめるかやね; こうかおんをならすかやめるかやね; せ〜ぶふぁいるをえらんでや〜; なんいどをえらんでや〜; すて〜じくりあしたらまえので〜たきえるけどええか？ | Fixed-width strips, tight for English. Confirmed: `help0`-`help8` (pinned index 0x3005263) in table order. |
| 5 | Menu headers | 0x3100DC, 0x31031C, 0x3105B8, 0x310810 | 0x20 each | めにゅ〜, おぷしょん, なんいど, せ〜ぶふぁいる | |
| 6 | Save slot labels | 0x310B2C, 0x310D14, 0x310EF8, 0x3110DC, 0x3112C4, 0x3114AC, 0x311694, 0x311878 | 0x18 each | Numbers and small kana, 8 variants | Read closer at the marker tour. |
| 7 | Save messages | 0x2D05F4, 0x2D0E10 | 0x5C, 0x2F | せ〜ぶをさくじょします, よろしいですか？, さくじょしました, はい, いいえ... | Confirmed: `delete` (0x2D05F4, ask), `delete_done` (0x2D0E10, done). |
| 8 | Stage result and HUD labels | 0x2BAA24 | 0x370 | すて〜じ, くりあ, たいむ, digits | Shared with level art. |
| 9 | Labels with digits | 0x2C4168 | 0xC6 | Digits plus short lettered labels | |
| 10 | Strip text | 0x2C1C00, 0x2C23A8 | 0x100, 0x68 | Hand lettering on a grey band | |
| 11 | Failed-load message | 0x2D50CC | 0x41 | せ〜ぶで〜た N が こわれました。 | Confirmed: `save_error`. **guess:** the slot number is the tile picked by slot at 0x80496D4 (0x2A00 + slot), so the digit may be a separate tile. |
| 12 | Large lettering | 0x2BFDD0 | 0x1E4 | Large strokes, last rows of the sheet | Could be a banner. Confirm on screen. |
| 13 | Failed-load sprite | 0x2C7E5C | 0xC | None seen: the small character on `save_error` | Loaded with row 11. Probably no text; check at the marker tour. |
| 14 | Kana label sheet | 0x2CCF8C | 0x180 | White kana on grey, many short words | Same look as row 18. |
| 15 | Stage title cards | 0x35CDA0, 0x35DA14, 0x35E3F8, 0x35EE50, 0x35F9A0, 0x3606DC, 0x36103C, 0x36194C, 0x362458, 0x362FB0, 0x363B14, 0x364678, 0x3650EC, 0x365B80, 0x366764, 0x3674C8, 0x367F34, 0x368BA8, 0x3695D8, 0x369D2C, 0x36A5A0, 0x36B1D8, 0x36C0BC, 0x36C938, 0x36D178, 0x36DF60, 0x36E768, 0x36F170 | 0x57-0xC6 | Each: その<n>, a stage title, then くちびるのまき | **28 cards**, the largest graphics job. English must fit the same tile count or the block's tile budget grows. |
| 16 | Short labels | 0x380A84, 0x380C20, 0x380DE4, 0x380F28, 0x381104, 0x381218, 0x3813A4, 0x3814BC, 0x3815D4, 0x381780, 0x381930, 0x381A80, 0x381CB0, 0x381E40, 0x382014 | 0x18 each | Dark kana on a grey band, 15 labels | Same shape as save slot labels; possibly option or item names. |
| 17 | Boss marquee | 0x38D664-0x39106C, about 65 blocks | 0xC each | Scrolling katakana frames: ブッ・トバス, タイキチュウ, エネルギージュウデン, カンリョウ, ハイジョ | A robot boss's scrolling display: one block per scroll position. Redraw all frames, probably by generating them. Unpacked in real play by `fight1` (33 blocks so far, boss object type 33); the robot is on screen there. The lettering itself still needs a zoomed check at phase 5. |
| 18 | Kana labels | 0x39E128-0x3A71BC, about 70 blocks | 0x20 each | White kana on grey, one or two lines of short words | Likely level or area names. Largest count after the marquee; confirm on screen. |
| 19 | Large lettering | 0x3A7D14 | 0x81 | Large katakana lettering, white with shadow | Confirmed: `title_clear`. The ハチエモン logo of the title shown after a full clear (0x3003DDE != 0), with 0x3A7260 behind it. **Keep** with row 1 (D5). |
| 20 | Cutscene picture with caption | 0x2D1EC4 (8bpp, palette 0x2D1CC4) | 0xA2 | Pink picture with a line of white kana, ...のなぞにきもちくだ... | Confirm on screen. |
| 21 | VS banners (Le) | 0x2A8A9C, 0x2A901C, 0x2A94FC, 0x2A9990, 0x2A9F14, 0x2AA5C0, 0x2AAB40 | Le, to VRAM 0x6001400 | VS plus a name and ハチエモン: マッスル, ダウー?, はちのす, ピカルク, はちだいがったい, カツマン, ヤママノ (read off a small sheet) | Confirmed: `vs0`-`vs6`, in table order (0x81A3D10, index 0x3000D9E). Index 7 repeats 0x2AAB40. |
| 22 | All-lips banner (Le) | 0x2A8454 | Le, to VRAM 0x6001400 | くちびるぜんぶげっと！ | Confirmed: `step96`. |
| 23 | Stage HUD art (Le) | 0x2A5F78, 0x2A6234, 0x2A64A8, 0x2A70DC, 0x2A7408, 0x2A7668 | Le, to BG VRAM 0x6000020-0x6001C00 | Lettered sheets, not read word by word | Unpacked by `death`, `death_last`, `defeat*` and every stage: read each on screen before phase 8. |
| 24 | Pause art (Le) | 0x2A7364, 0x2A7FB4 | Le, to 0x2030000 | Kana lines, read closer at phase 8 | `pause`, `pause_down`, `pause_exit`. |
| 25 | Stage clear art (Le) | 0x2A7784 | Le, to VRAM 0x6001400 | Large lettering | `stage_clear`. |
| 26 | Stage 26 art (Le) | 0x2A7B88 | Le, to 0x2030000 | Large lettering | `stage26`. |
| 27 | Latin letter sheet (Le) | 0x2A5DC0 | Le | A-Z, 0-9 | Already Latin; no tour unpacked it. Probably no work. |

**Seen in the marker tour, blocks not pinned yet:** the post-stage slot machine (scene `slot`; its blocks are among the `lz` lines of `work/qa/*/slot/log.txt`) and the wooden area-name banner. Give each a row once pinned: `tests/test_build.py` requires every row to have a real block.

**Not text:** Namco and Kansai TV logos (0x2CEAB8 and the Kansai TV block) stay (D5). The other 8bpp pictures from 0x2DD320 on show scenery and characters only at this sweep's scale; a sign could still hide in one, so the tour must look.

**Not graphics:** box dialogue and speech bubbles are font-drawn (`text.md`), so they follow the script, not this list.

## Effort
Rows 4, 15, 17 and 18 are most of the work. Hand-lettered kana suggests one English bitmap face in the same style, with the rows generated by script (`typeset.py` or a small renderer), then re-imported and recompressed. Recompressed blocks will rarely match their old size, so edited blocks move to free space and their pointers get repointed (`repoint` in `tools/build.py` writes every slot of a block).

## Block pointers
**verified** statically for all 236 row blocks (`tests/test_build.py::test_every_graphics_row_has_a_real_slot`); 185 of them also by the emulator: `tools/debug/moved.py` moved them, wiped the old bytes, and the tour unpacked them at the new address and never at the old one. The other 51 were not unpacked by that tour, so their slots have only the static proof.

| Rows | Blocks | Slots |
|---|---|---|
| 1-3, 7-15, 19, 20 | 42 | Table from 0x1D5F5C, one word per block. Row 3's 0x2B4AE4 has a second slot at 0x1D605C. |
| 4, 5 | 13 | Rows of 0x10 bytes `{block, VRAM dest, 0, 0}`: 0x79010-0x790D0 |
| Row 6 | 8 | Same shape: 0x7EC10-0x7EC80 |
| Row 16 | 15 | Same shape: 0x77A2C-0x77B0C |
| Row 17 | 75 | Same shape: 0x7A6F4-0x7AB94 (the sweep's "about 65" was low) |
| Row 18 | 73 | Same shape: 0x7C978-0x7CDF8 |
| Row 21 | 7 | Table 0x1A3D10-0x1A3D34, 10 slots: some blocks repeat, so move all of a block's slots together |
| Row 22 | 1 | Code literal 0x3D74 |

Across the whole ROM 186 packed blocks have more than one slot. None of the row blocks has a slot in 0x80000-0x1A2FFF; the only block that does is 0x280828 (not a row, words at 0x888B8, 0x8907C, 0x890A0, not examined).

## English lettering (phase 8)
`tools/gfxtext.py` holds every redraw. `MAPPED` is for a tile block plus its map: `MapPicture` flattens them, letters the picture and finds tiles again, flips included, within a tile limit (the old count, or BG0's room). `RAW` is tiles in place. `tools/debug/fitlabels.py` lists every label that doesn't fit; `tools/gfxview_blocks.py` and `gfxview_maps.py` show blocks in real colours, `tools/debug/rawview.py` raw tiles, `tools/debug/ppu.py` dumps scenes. `LABELS` maps a block to (tile grid, words, options). The build unpacks the block, clears a rectangle, draws in the text font (`tbl/vwf_font.txt`) and packs it again from `GFX_BASE` (0x600000), repointing through `owned_slots` (the tables above plus the Le rows' code literals; a test holds them equal to the value scan). Unpacked size never changes, so VRAM layouts hold.

To read a screen, dump it:

    python -X utf8 "$(python tools/skill.py)/scripts/emu.py" "rom/Hachiemon (Japan).gba" --out work/qa/ppu/SCENE --script tools/debug/warp.lua --var "SCENE='SCENE'" --frames 1800 --script "$(python tools/skill.py)/scripts/lua/probes/ppudump.lua"

Then `tools/debug/oamlist.py DUMP.oam.bin DUMP.io.bin` lists sprites and `oamlist.py --bg N 1 3ff DUMP.vram.bin DUMP.io.bin` a BG's tile rows. Tile = (VRAM dest - char base) / 0x20; the `lz` log lines give each block's dest. `tools/gfxview.py` shows a block by palette index, `tools/gfxview_sprites.py` assembles sprites in real colours. Take the palette bank from the map word's top nibble (HUD and pause items D, pause title F): reading indices through the wrong bank gave dark text twice. Stage scenes are still black at frame 900.

| Row | State | Layout |
|---|---|---|
| Row 2 | **English** | Prompt: 16 x 2 tiles from 0. Then five 32x32 cells of the Kantele shout, 22 px apart; the first settles off screen, so it stays blank. |
| Row 3 | **English** | Pills are three 32x16 sprites, 0x18 tiles. Discs 32x32. The save slot's digit sprites cover the right of Stage, Lips and Lives, so those labels sit left. Tiles 1FC-238 are digits, pill 2A9 is an empty dash. **Not seen on screen yet:** 2C1, 2D9, 2F1, 309, 333, 255, 265, 323. |
| Rows 4, 5 | **English** | Help strip 15 x 3, header 16 x 2. Seen: help0, help8, the Options and Difficulty screens. Others not looked at. |
| Row 6 | **English** | 6 x 4 tiles, 8 sway frames of the カンテーレ stamp. The kana ran to the ellipse's edge, so each frame gets a clean ellipse (`blank_stamp`) and "Kantele" moved a pixel per frame. Seen on `menu`, not zoomed. |
| Rows 7, 11 | **English** | Through `MAPPED`, so repeated tiles no longer matter. `delete` Yes/No keep the cells that dim by palette: x 72-104 and x 128-168, rows 12-13. Row 11's slot digit is a tile the code writes at cols 18-19 of row 5, so "Save data" ends left of x 144 and "is" starts at x 162. Its screen has sparks above the character, one crosses "corrupted": sprites of row 13, the original's too. |
| Row 8 | **English** | Map panel: tiles 0x29E, 0x2BE, 0x2DE, each four 32x16 sprites. Digit sprites start at x 102, so labels end by x 100. Plain weight: bold "Clear Time" touched the digits. |
| Row 9 | **Not read** | Digits, then short white lettering around tiles 0xB2-0xC5, 8x16 or 16x16. No dump shows those tiles on screen. Unpacks in every stage. |
| Row 10 | **Part** | 0x2C23A8's tiles 0x50-0x5B say Ranch: row 16's first banner, overwritten the same frame. 0x2C1C00 only unpacks in `boss_*`, debug harnesses players can't reach (`flow.md`), so it stays Japanese. |
| Row 12 | **English** | 32x32 sprites from x 8: 64, 74, 84, 94, 74, A4, 74. The kana's 〜 is tile 74, shared by three cells and kept, so it reads GA~ME OV~ER~, like げ〜むお〜ば〜 (D17). |
| Rows 14, 18 | **English, unseen** | Each line 128x16, four 32x16 sprites. Row 14 is the first 12 lines in one block. Names Western order, Hepburn (D1, D2). 0x3A6738, 0x3A68B8 are the namco logo; 0x3A6DFC on are blank. The `credits` scene at frame 1800 still shows the namco screen: **no English credit line seen yet**. |
| Row 15 | **English** | 28 cards through `MAPPED` (`CARDS`). Digit is a sprite at x 160, y 115. Card 2 seen; the other 27 not. Readings of the kana in `CARDS` are from a small sheet, and wordplay titles were translated freely. |
| Row 16 | **English, 1 seen** | The wooden area banner: twelve 8x16 sprites (`spr(0, 8, 16, 12)`), not a 12 x 2 sheet. The block goes to 0x6016A00. |
| Row 17 | **Not done** | Scrolling marquee, 75 blocks. Not read closer than the survey's list. |
| Row 20 | **Not done** | 0x2D1EC4, 8bpp, unpacks in `fight2` at f3536. Not looked at on screen. |
| Rows 21, 22, 25 | **English** | `MAPPED`. BG0 from tile A0, Le maps with a 16-byte header. VS names ran past the ellipse, so `blank_vs` redraws it from x 72: an approximation, compared with the old edge only on one printed block. `vs0`, `vs2`, `vs4`, `vs5` seen; `vs1`, `vs3`, `vs6` not. |
| Row 26 | **English, unseen** | たいむお〜ば〜, TIME OVER (it isn't "stage 26 art"). Map 0x2AB220. **No scene reaches it**: add one (timer to 0). |
| Row 23 | **English** | 0x2A7408's カンテーレ. Stage start: `N` digit blocks 0x2A6670-0x2A6E2C to 0x6001400, 0x6001600; 発 0x2A6EF0 and 目 0x2A7038, now "SH" and "OT", read "5 SHOT" (D17). すた〜と 0x2A70DC is four cells, "S TA RT !". The digit comes first in code, so the word can't lead. |
| Row 24 | **Part** | 0x2A7668 and 0x2A7FB4 English. 0x2A7364 (0xC tiles, "icons" by index counts) not read. |
| Slot reels | **English, 3 of 28 seen each pull** | Raw tiles, not in the survey: 28 cells of 8 x 4 tiles at 0x303C70, three reels by code literals 0x51884, 0x518A8, 0x518D4. In place, same size (`RAW`). Header in 0x2B98B0. Words read off a small sheet; ちょ?ふどう read as きょほう. |

## Stage signs
**English** (`STAGE_SIGNS` in `gfxtext.py`). 16 tilesets, table 0x1A61C4, rows of {tileset, second block}. Rooms: table 0x1A6244, 20-byte rows of three 120x120 word maps (16-byte header) and a 120x120 byte block (collision, **guess**), index `set*8 + area*4 + room`; a row of 0x231A04 is unused. Layer 0 holds the boards. Tiles aren't laid out as pictures, so read a board with `tools/debug/stagesheet.py crop` (or `tiles`, `room`, `uses`), `stagefind.py`, `stagecrop.py`; `STAGE_ROM=build/hachiemon_en.gba` shows a build. `stageobjs.py` is a noisy gallery of rare objects.

The earlier "バリアール" is ハチアイル, Hachi Isle: the board at a stage's start. Tile numbers: the map cell's, tile 0 is the block's first.

| Set | Stall sign (6 x 2 tiles) | Other lettering |
|---|---|---|
| Sets 0, 13 | ハチの屋: HACHI'S STALL | |
| Sets 1, 6 | ハチ道楽: HACHI PARADISE | |
| Set 2 | ハチだがね: IT'S HACHI! | Osaka: 八百ハチ (three boards) HACHI GROCER, ハチ肉店 HACHI MEATS, ハチ処 HACHI PLACE. Its side panels' small kanji are mirrored tiles, so they are now blank. CAFE Hachi is Latin. |
| Set 3 | 558 + a Latin line: **kept, not read closely** | The other stall is the takoyaki one, no text |
| Set 4 | ビックリハチー: WOW! HACHI | |
| Set 5 | クラブ8: CLUB 8 | |
| Sets 7, 15 | すしはち: SUSHI HACHI | |
| Set 8 | やまのハチ: MOUNTAIN HACHI | |
| Set 9 | とりはち: CHICKEN HACHI | |
| Sets 10, 14 | ハチボーイ: HACHI BOY | Set 14: ザ・バーゲン BARGAIN; 50%OFF and HACHINEL are Latin |
| Set 11 | ハチバーガー: HACHI BURGER | HOTEL, HOSPITAL, POLICE, BAR, WELCOME are Latin |
| Set 12 | no stall | くちびるらんど LIP LAND, りっぷまうんてん LIP MOUNTAIN, りっぷごーらんど LIP-GO ROUND (a pole splits it), のりものあんない RIDES (five tiles), りっぷすぴん LIP SPIN |

The Hachi Isle board is in sets 0-5, 7-12, 14. **Set 12's says ISLE:** its end tiles repeat mirrored, leaving 16 px. These were checked by rendering rooms from the build's tiles, not in the running game, except where the tour shows them. Only rooms 0 of each area were read by eye; set 10 area 1, set 12 rooms 2-3 and set 11 area 1 share these tiles but weren't viewed. Lettering uses `TINY`, 3x5 capitals drawn here, doubled to 4x5 with `wide`.
