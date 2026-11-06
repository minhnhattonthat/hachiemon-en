# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build not started; phase 2 done-when met. Last build: none yet (original ROM smoke passes, 2026-11-06).
- **Done:** Step 0 (repo, MesenCE 2.2.1 + BIOS in `tools/mesen/`, commit gate, guard hook proven, instructions file). Phase 1 recon: `docs/re/` records encoding, pointers, text ranges, free-space candidates and the graphics survey.
Phase 2: `tools/debug/` warps from a cold boot (`tour.py`, scenes in `scenes.lua`, facts in `docs/re/flow.md`). Last full tour (2026-11-06): 113/113 scenes ok, states in `work/states/`. The four black `boss_*` scenes are gone: subs 11-14 are debug-page harnesses players can't reach (static proof in `flow.md`). `fight0`-`fight9` replace them with the real fights in stages. `fight6` is forced past a wait, and `fight6`-`fight8` show no VS banner. `gfxcover.py`: every row of `graphics.md` has a scene, including row 17 in `fight1`; the 0x2B4AE4 twin of row 3 was never unpacked (guess: unused). I checked one sheet of two shots per fight by eye, and earlier contact sheets at one shot per scene, not every shot.
- **Next:** Phase 3, the identity build (`tools/build.py`, byte-identical test). Before phase 8, add scenes for what the warp can't reach yet (`flow.md`, Boss fights and Text): winning a fight (boss defeat lines), each stage signboard text, and a `GOD` that also stops damage. 230 strings are still unread (main bank 681/873, sign bank 2/40), list in `work/qa/long/text_unseen.tsv`. Don't treat them as dead: 190 have pointers. The 40 pointerless ones are still only a guess (`text.md`), so extract them anyway.
- **Open bugs:** none.
- **Waiting on the user:** nothing blocking. Not verified: Mesen's GUI taking keyboard input (this run is headless and Step 0 wants a human check); `tools/emu-config/settings.json` holds the working settings.
