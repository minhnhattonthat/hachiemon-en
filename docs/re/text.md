# Text engine

Addresses are for the dump in `rom.sha1`. ROM offset + 0x08000000 = bus address.

## Encoding
- **verified** One byte per character; the byte is the font cell. No Shift-JIS anywhere. `tbl/jp.tbl` is the table. How: VRAM glyphs of the opening narration matched to font cells, the resulting bytes found at 0x1D9554 and decoded to what the screen shows (`tests/test_recon.py::test_known_string_decodes`).
- **verified** Font: ROM 0x2FFC50, raw 4bpp, 8x16, 64 bytes per glyph (top tile then bottom tile), 256 cells. Pointer literal loaded in the draw routines at 0x8038628 and 0x803A04C (`ldr r1,=082FFC50`). Sheet: `tools/fontsheet.py`.
- **verified** Layout: 00-4F hiragana, 50-9F katakana, A0-B9 A-Z, C0-D9 a-z, E0-E9 0-9, EA space (written `\s` in `tbl/jp.tbl`; EB-EF blank), F0 ー, F1 － (longer dash, used in runs for pauses), F2 「, F3 」, F4 ！, F5 ▼, F6 （, F7 ）, F8 ？, F9 ♥, FA 〜, FB 、, FC 。 The Latin glyphs already exist but are fixed 8 px with no comma, period or apostrophe in Latin style: phase 5 decides the English font.

## Control codes
| Code | Meaning | State |
|---|---|---|
| `FF m` | End of string; the next byte `m` belongs to the string | **verified** by disassembly at 0x80383CE-0x80384A0 (`ldrb r5,[r2,#1]`) and by every string walking cleanly |
| `m` bit 0 (`01`) | Finish at once, no wait | verified by disassembly |
| `m` bit 1 (`02`) | Blink the ▼ cursor while waiting (tiles base+0x5E/0x5F, glyphs 0x83036D0 / 0x8303990) | verified by disassembly |
| `m` = `00` | Wait for a press with no cursor | guess: the fall-through path reads the button byte at 0x3000104 |
| `FD` | Page break: blink the cursor, wait, clear the box, carry on | **guess** from the disassembly at 0x8038550; confirm at the marker build |
| `FE` | New line: cursor advances to the next multiple of 24 cells | **verified** by disassembly at 0x8038598 |

No other control bytes occur: every string in both banks walks with only these (`tools/strscan.py`).

## Two draw paths
1. **Box text** (cutscenes): `0x80383B8(r0=VRAM dest, r1=text)`, set up by `0x8038324`. Called once per frame per character. State block at 0x3005310: +0x0C string index, +0x11 cell number. Cell n draws glyph tiles at dest + n*64 and writes tilemap entries; column = n % 24, row = n / 24 (each row two tiles high). **Box is 24 cells x 2 rows, 192 px wide** when the cursor cell is respected: cell 47 (row 2, col 23) holds the cursor tile. Dialogue tiles live at VRAM 0x8400+, BG0, tilemap 0x0000.
2. **Speech bubbles** (in-stage comedy): sprite text, the routine around 0x8039C80-0x803A0A0, drawn to OBJ VRAM 0x06010000 (`ldr r3,=06010000` at 0x803A05E). Reads the same font and the same grammar. Bubble rows give the size in cells, so width varies per bubble: **measure at the width gate (phase 5)**.

## Banks
Both banks hold strings back to back with no pointer table of their own. Run `tools/strscan.py` for current numbers.
| Range | Strings | Chars | Content | Pointers |
|---|---|---|---|---|
| 0x1C0984-0x1C127C | 40 | 2,217 | Tutorial signboards | Table at 0x1C1280 |
| 0x1D9554-0x1DCFC8 | 873 | 13,217 | Story, bubbles, narration, ramen stand | Rows at 0x1C7000-0x1D7FFF and 0x1DD000-0x1EAFFF (810 words); literal pools in code at 0x3Dxxx, 0x4Bxxx, 0x4Exxx, 0x4Fxxx, 0x5Dxxx (34 words) |

Longest line today: 25 cells. **Text can move:** every string found so far is reached through a 32-bit pointer word, so English goes in new space and the words get repointed. In-place fitting is not needed. **verified** on the strings the tour reads: `tools/debug/moved.py` moved both banks and wiped them, and the talk scenes still drew their text. `real_slots` in `tools/build.py` drops words inside packed blocks and the banks as chance matches; it found none in either, and 885 words count as text slots (884 from `strscan.py` plus the 0x1DBDF4 literal). The row layout is still a guess until phase 4 decodes it.

### Pointer forms
- **verified** Literal pools in code, `ldr rN,=string` then `bl 0x80383B8`. Example: 0x4B354 -> 0x81D9554.
- **guess** Speech rows, 0x28 bytes each, e.g. at 0x1E903C: `{+0 animation ptr 0x081D48F8, +4 text ptr 0x081D9EBB, +8 2, +C 0x8F, +10 0, +14 0xAF, +18 0x110, ...}`. Layout read from the bytes, not yet from the reading code. Phase 4 must decode the owning structure rather than trust a value match (`AGENTS.md`).
- **verified** Tutorial table at 0x1C1280: one word per string.

### Open items for phase 4
- 40 strings in the main bank have no pointer word (one of them is 0x1DBDF3, below). They sit together: the tutorial's older copy at 0x1DCB9B-0x1DCDF9 and the ramen-stand talk at 0x1DCDFA-0x1DCFC7, plus a few singles (0x1DAA42, 0x1DAF84, 0x1DC4C7, 0x1DC4DF, 0x1DC782, 0x1DC7A1, 0x1DC7AB). **guess: dead.** Evidence: `tools/debug/textwatch.lua` watches every read of the bank whatever the path, and none of the 122 scenes (3000 frames, A mashed) nor the 44 talk scenes (9000 frames) read any of them; no pointer word in the ROM lands in those ranges; every other string is reached by an absolute pointer. Not proof: the same tours read only 549 of 873 main-bank strings and 2 of 40 tutorial strings, because stage bubbles need play. **Plan for phase 4:** keep them out of the script and leave their bytes in place; the leftover-Japanese scan is the net if one ever shows. `textcover.py ROM OUT...` re-checks after more play.
- 0x1DBDF3 is a stray byte: a code literal (0x4EC04) points at 0x1DBDF4, one past where the grammar walk starts a string. Use the pointer as the start.
- 0x1C1003 <- 0xE331C lands mid-string, and 0xE331C is outside the code and table areas: very likely a chance match. Do not repoint it.
- Graphics text and the marquee boss sprite are not in these banks: see `graphics.md`.
