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
| 0x1C0984-0x1C127F | 41 | 2,217 | Tutorial signboards (the last is empty) | Table at 0x1C1280 |
| 0x1D9554-0x1DCFC7 | 873 | 13,217 | Story, bubbles, narration, ramen stand | Script VMs (810 words); literal pools in code at 0x3Dxxx, 0x4Bxxx, 0x4Exxx, 0x4Fxxx, 0x5Dxxx (35 words) |

Longest line today: 25 cells. **Text can move:** every string found so far is reached through a 32-bit pointer word, so English goes in new space and the words get repointed. In-place fitting is not needed. **verified** on the strings the tour reads: `tools/debug/moved.py` moved both banks and wiped them, and the talk scenes still drew their text. `text_slots` in `tools/build.py` takes its 886 words from the structures in `tools/vmscript.py` (810 script, 35 code, 41 sign), not from value matches. `test_owned_slots_equal_every_pointer_a_value_scan_finds` holds them equal to the old value scan.

### Pointer forms
- **verified** Literal pools in code, `ldr rN,=string` then `bl 0x80383B8`. Example: 0x4B354 -> 0x81D9554.
- **verified** Script VM arguments, below.
- **verified** Tutorial table at 0x1C1280: 41 words, read at 0x8002D54 and 0x8003FF4. Entry 40 points at the empty string at 0x1C127D. The next word is not a pointer.

### Script VMs
The "speech rows" were never rows. They are u32 bytecode: an opcode word, then its arguments. **verified** by walking every script from its entry to its op 4 with lengths read from the handlers (`tools/vmscript.py`, `tests/test_script.py`): none hits an opcode its VM wouldn't run, and the walks own all 810 script words.

| VM | Entry | Scripts come from | Jump table |
|---|---|---|---|
| Talk | 0x803B4B0, id in 0x3003E0C, pc in 0x3003E10 | Table 0x81C2E18, 88 entries (6 of them stage-format, so the stage VM owns those) | 0x803B4F0 |
| Stage | 0x8056990, script pointer in r0 | 36 `bl` callers load 14 scripts from literals | 0x80569C8 |

- Both share a state block at 0x3003E00 and opcode numbers, but not all lengths: op 1 is 1 word in talk and 2 in stage, 0x9B runs only in stage. Op 4 ends a script. In the talk VM an unlisted opcode resets the pc to 0.
- **Text args:** `AF slot a b c anim text` (7 words) sets a bubble in 0x30042A8 + slot*0x44 with text at +0x10; `8E slot a b c text x y` (8 words) is the same with a position and no anim. 715 AF and 95 8E. No other argument of any walked op points into a bank, and `script_words` raises if one ever does.
- `anim` tells speakers apart (e.g. 0x1C6CC0, 0x1D4540): extraction records it in each ref. It has no name mapping yet.

### Strings with no pointer
39 strings in the main bank have no pointer word. They sit together: the tutorial's older copy at 0x1DCB9B-0x1DCDF9 and the ramen-stand talk at 0x1DCDFA-0x1DCFC6, plus a few singles (0x1DAA42, 0x1DAF84, 0x1DC4C7, 0x1DC4DF, 0x1DC782, 0x1DC7A1, 0x1DC7AB). **guess: dead.** Evidence: every script is now walked and none points at them; the box callers of 0x80383B8 all load r1 from a literal; `tools/debug/textwatch.lua` saw no read of them in any tour. Not proof: a computed pointer wouldn't show, and the tours read only 681 of 873 main-bank strings. They are in `script/` with empty `refs`, so they get translated and written; only the leftover-Japanese scan or a read in `textcover.py` would change the guess.

### Other notes
- 0x1DBDF3 is a stray byte: a code literal (0x4EC04) points at 0x1DBDF4, one past where the grammar walk starts a string. Use the pointer as the start.
- A sweep for FF-terminated kana runs outside the banks (2,203 hits) found only code, sound and table bytes in what I sampled, no second text bank. I read the ones at 0x80000+ with a pointer or mostly kana, up to about 0xB1000, and the output past that was cut off, so this is a sample rather than a full reading.
- 0x1C1003 <- 0xE331C lands mid-string, and 0xE331C is outside the code and table areas: very likely a chance match. Do not repoint it.
- Graphics text and the marquee boss sprite are not in these banks: see `graphics.md`.
