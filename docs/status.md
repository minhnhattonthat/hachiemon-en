# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool built, 4 boss scenes not proven. Last build: none yet (original ROM smoke passes, 2026-11-06).
- **Done:** Step 0 (repo, MesenCE 2.2.1 + BIOS in `tools/mesen/`, commit gate, guard hook proven, instructions file). Phase 1 recon: `docs/re/` records encoding, pointers, text ranges, free-space candidates and the graphics survey.
Phase 2 so far: `tools/debug/` warps from a cold boot (`tour.py`, scenes in `scenes.lua`, facts in `docs/re/flow.md`). Last full tour (2026-11-06, 122 scenes before dropping 15 empty talk ids, so 107 now): only `boss_m`, `boss_g`, `boss_b`, `boss_t` and four of the dropped ids failed, all with "every shot blank". `gfxcover.py` ties every row of `docs/re/graphics.md` to a scene, but the 0x2B4AE4 twin of row 3 was never unpacked (guess: unused) and row 17 only unpacks inside black `boss_t`. The 40 pointerless strings were never read (guess: dead, `docs/re/text.md`). I checked contact sheets by eye at one shot per scene, not every shot.
- **Next:** Finish phase 2: get the boss scenes on screen or show players can't reach them (`docs/re/flow.md`, Open), and add a scene for a real boss fight in a stage. Then phase 3, the identity build.
- **Open bugs:** none.
- **Waiting on the user:** nothing blocking. Not verified: Mesen's GUI taking keyboard input (this run is headless and Step 0 wants a human check); `tools/emu-config/settings.json` holds the working settings.
