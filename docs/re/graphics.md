# Graphics text survey

Static sweep of every LZ block and raw gap from 0x2B0000 to the end of data, read by eye: `tools/gfxsweep.py ROM OUT --raw --lo 2B0000` (26 pages, 956 blocks) and `tools/gfxsweep8.py ROM OUT` (36 8bpp pictures with their own palettes). 355 tilemap-shaped blocks were skipped and printed by the script. Regions before 0x2B0000 got a sampled render only (one strip per 64 KB): no tile text seen.

Every row has a warp scene that unpacks its blocks: `tools/debug/gfxcover.py OUT` after a tour prints the row-to-scene map (`lz` lines of `tools/debug/lzlog.lua`). Phase 5's marker tour still has to look at each element on screen and add anything this list missed; "Confirmed" below means seen on a tour shot. Reading of the Japanese is from the sheets, so a few words may be approximate. All blocks are LZ77 4bpp unless noted.

The game also holds 1336 blocks in its own Le codec (`le_decompress` in `tools/gbacomp.py`; pages from `tools/lesweep.py`), mostly bitmaps and palettes. Only rows 21 and 22 were read from them so far; the phase 5 tour must look at the rest.

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

**Not text:** Namco and Kansai TV logos (0x2CEAB8 and the Kansai TV block) stay (D5). The other 8bpp pictures from 0x2DD320 on show scenery and characters only at this sweep's scale; a sign could still hide in one, so the tour must look.

**Not graphics:** box dialogue and speech bubbles are font-drawn (`text.md`), so they follow the script, not this list.

## Effort
Rows 4, 15, 17 and 18 are most of the work. Hand-lettered kana suggests one English bitmap face in the same style, with the rows generated by script (`typeset.py` or a small renderer), then re-imported and recompressed. Recompressed blocks will rarely match their old size, so edited blocks move to free space and their pointers need repointing: phase 3 must find the block pointer tables.
