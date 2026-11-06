# Skill gotchas

One line each: the reference it belongs in, then the fact.

- `references/graphics.md` (Survey): a sweep of packed blocks and "raw gaps" can miss raw tiles that sit between packed blocks: 28 slot reel words at 0x303C70 were never listed. Search the ROM for tiles taken from a VRAM dump (`rom.find` on a run of 4 tiles) whenever a screen's lettering has no block.
- `references/graphics.md` (Edit): tile-and-map banners dedupe tiles and use flips, so drawing on tiles corrupts repeats. Flatten block and map to one picture, draw, then dedupe again. Worth doing first: it removes every "keep text off that tile" rule.
- `references/graphics.md` (Edit): "clear to the commonest colour" picks the ink on a heavy glyph (white boxes on big lettering). Pass the paper colour for big cells.
- `references/emulator-qa.md` (emu.py): `--var DUMP_EVERY=N` dumps only at multiples of N, so a dump at frame 780 with N=120 never happens; pick frames that are multiples.

- `references/pipeline.md` (Checks, Leftover Japanese): `jp_left.py --tbl --slots` passes falsely with per-string pre-rendered cells: strings start with cell byte 00, so a NUL ends its reach at once, and later bytes aren't font codes. It said 0 runs on a build with 50 lines blank. A game like this needs a cell-side check (`tools/jp_cells.py`): walk each slot's string and compare the cells it would draw with the font's kana cells.

- `references/emulator-qa.md`: a tour can lose every remaining scene at once to exit code 0xC0000142 (Mesen failing to start; seen 2026-11-07 after 29 of 160 scenes, cause unknown). The tour still exits 0, so read the `N/M ok` line in its log, not the exit code.
- `references/emulator-qa.md`: `sheet.py` run from a subfolder with shell-relative paths writes `--out` relative to that folder, and the shell's working directory carries to the next call. Run it from the repo root.
- `assets/batches.py`: its `_selftest` assumes `[n]`-style tokens and a `max` field, so it breaks once the ADAPTER is fitted to another format; its Avoid column splits on `/` while `glossary.md` and `lint.py` use commas; `merge` adds a `status` key per entry. Fitted and removed here.
- `references/translation.md` (Validation): a glossary check on raw English fails when a name wraps across a line code (`Muscle{nl}Hachiemon`). Flatten codes to spaces first. A JP term that is a prefix of another (タコ in タコヤキ) can't have its own row in a substring check.
- `references/translation.md` (Review): `codex exec` exits 1 with a usage-limit error (hit 2026-11-07, resets 2026-11-11) and writes no report: check the exit code rather than assuming an independent review ran.
- `references/emulator-qa.md` (emu.py): Mesen kills a Lua callback that runs over 1 second (`lua_error.txt`: "Maximum execution time"), exit 2. Under a parallel tour this hit about 1 scene in 30, on no fault of the scene. Rerun the failed ones at low load before reading anything into them.
- `references/emulator-qa.md` (Visual QA): `sheet.py --changed` keeps nearly every shot of a stage scene because the background animates, which made 570k tokens of sheets. Pick shots from the game's own text log plus a box-region diff (`tools/debug/qasheets.py`): 114k.
- `references/graphics.md` (Lettering): a sprite the game scales (an unselected menu disc at about 2/3) drops pixel rows, so 8 px text turned "Off" into "Utt" and shifting y only changed which rows died. Use doubled capitals. Look at each label in both its states.
- `references/graphics.md` (Survey): count raw cells from the data, not from the words you read. Here a reel table stopped 2 cells short, and only a lucky pull on the slots showed Japanese.
- `references/emulator-qa.md` (Debug tool): a boss's defeat can be reached with no win: find its state table and force the state a lost fight enters. The state object need not be the object carrying the boss's type (here slot 33, not 30). Check with a state log: a forced state that never advances means the wrong object.
- `references/emulator-qa.md` (Debug tool): a position measured once can follow the player. Rerun the scene with the player moved and diff the logged x before trusting a width limit.
- `references/pipeline.md` (Fitting): before ruling a bubble too narrow, try the script op's always-zero arguments. Here one turned on the game's own screen-edge clamp.
- `references/pipeline.md` (Marker): a bubble or sign can have a byte cap on the whole string, across pages. Fill long multi-page strings to the limit in the at-limit build, or the cap only shows in a playtest.
- `references/graphics.md` (Survey): stage tilesets can be deduplicated tile soups, unreadable as a sheet. Find the room-map table and render maps with tile words instead; shared objects then show up at once (here a board misread as バリアール from a sheet was ハチアイル).
- `references/emulator-qa.md` (Debug tool): a credits scene that "still shows the end screen" may have already scrolled by; shoot from the warp on before hunting for what starts it.
- `references/graphics.md` (Lettering): doc tables parsed by tests can swallow new tables with bare numbers in column 1 (gfxcover read a set number as row 2): label such columns.
- references/emulator-qa.md: a tour scene can die on Mesen's Lua limit ("Maximum execution time (1 seconds) exceeded" in lua_error.txt) and leave a dir with no shots; a contact sheet just has one tile fewer, so check every scene dir has shots.
- references/graphics.md: a font cell labelled as a symbol can be a glyph (Hachiemon F9 "♥" is a bold あ); render every non-letter cell once, and include them in the leftover-Japanese check.
