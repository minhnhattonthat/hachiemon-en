# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next. Last build: none yet (original ROM smoke passes, 2026-11-06).
- **Done:** Step 0 (repo, MesenCE 2.2.1 + BIOS in `tools/mesen/`, commit gate, guard hook proven, instructions file). Phase 1 recon: `docs/re/` records encoding, pointers, text ranges, free-space candidates and the graphics survey.
- **Next:** Phase 2, `tools/debug/` warp: `references/emulator-qa.md` §Debug tool. Needs scene ids, story flags and a stage select found with `ramsearch.py`. A warp list must reach every row of `docs/re/graphics.md` so those rows get confirmed on screen. While touring, log `r1` at 0x80383B8 and the bubble entry to settle the 40 pointerless strings (`docs/re/text.md`, open items).
- **Open bugs:** none.
- **Waiting on the user:** nothing blocking. Not verified: Mesen's GUI taking keyboard input (this run is headless and Step 0 wants a human check); `tools/emu-config/settings.json` holds the working settings.
