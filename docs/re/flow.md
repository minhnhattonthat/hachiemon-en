# Game flow and how the warp reaches each screen

All **verified** by running the warp from a cold boot unless a line says otherwise; proof is `tools/debug/tour.py` (one shot set and `report.tsv` per run).

## State variables
| Address | Meaning | Proof |
|---|---|---|
| 0x3000C90 | `st`, main state, table 0x81A34B4 | disassembly of the main loop at 0x80004FC; writes change the screen |
| 0x3001A04 | `sub`, substate of `st` 1, table 0x81C2508 (handler 0x803791C) | every `sub` scene in the tour |
| 0x3000830 | `step` inside the substate; each handler is a table of step functions | tour |
| 0x300498C | Progress word. The warp writes `1 \| node<<1 \| node<<7`; the field meanings past that are a **guess**, read by the map logic 0x8052F60 | stage scenes land on the right stage |
| 0x81C4190 | Map node table, 24-byte records | `stage_nodes` in `scenes.lua` gives the card for each stage |
| 0x300527C | Talk scene id, table 0x81C265C has 0x2C entries | talk scenes |
| 0x3005256 | Menu row | `menu_*` |
| 0x3005263 | Help strip index (0x30051D0+0x93) | `help0`-`help8` |
| 0x3003DDE | Clear bits, one per difficulty with all 28 stages cleared; set by 0x8049558-0x804956E | `title_clear` |
| 0x3000D9E | VS banner index, table 0x81A3D10, read when play step 104 runs | `vs0`-`vs6` |
| 0x3001970 | Player block, cleared by 0x8007350 (+0x1C lives, +0x1E difficulty) | `new_game()` in `warp.lua` |

## Substates (`sub`)
| sub | Handler | Screen | Scene |
|---|---|---|---|
| 0 | 0x8048F51 | Logos | `logos` |
| 1 | 0x804919D | Save delete: step 2 asks, step 7 says done | `delete`, `delete_done` |
| 2 | 0x8045C05 | Title (decorated when 0x3003DDE != 0) | `title`, `title_clear` |
| 3 | 0x80461F9 | Menu pages | `menu*`, `help*` |
| 5 | 0x804E919 | Continue cutscene; step 0x38 is the DME ending | `continue_cut`, `dme_ending` |
| 6 | 0x804B0ED | Opening | `opening` |
| 7 | 0x8051DE1 | Map | `map` |
| 8 | 0x8055C2D | Game over | `gameover` |
| 9 | 0x80506A9 | Save slot | `slot` |
| 10 | 0x803B349 | Talk scenes; the map enters them with events 0xE-0x10 and the id in 0x300527C | `talk01`-`talk29` |
| 11-14 | 0x80568FD... | Debug-page test harnesses (BOM, BOG, BOB, BOT) around code real fights also use. Players can't reach them: see Boss fights | none; use `fight0`-`fight9` |
| 15 | 0x8049585 | Save check at boot; step 2 is the failed-load screen | `des`, `save_error` |
| 16 | 0x80655B5 | Stage load, then `st` 0 play | `stage01`-`stage28`, plus forced play steps |
| 17 | 0x8065DAD | Credits | `credits` |
| 18 | 0x8043141 | Leftover debug menu; `tools/debug` does not depend on it | none |

## Play steps
In a stage `st` is 0 and `step` indexes the table at 0x81A3A38. `warp.lua` forces a step after THEN_WAIT frames of play. Known: 4 death, 32 sign, 48 stage clear, 104-107 VS banner. Forcing a step on stage 1 did not fire in the tour; on stage 5 (node 7) it does, so the scene list uses stage 5. **guess:** stage 1's opening sign holds play.

## Graphics loaders
- LZ77: all through the BIOS wrapper 0x8075B74. `tools/debug/lzlog.lua` logs each block with its destination; `tools/debug/gfxcover.py OUT` ties the log to `graphics.md`.
- Le codec: 0x80009D8, 0x8000A34, `le_decompress` in `tools/gbacomp.py`.
- Two switches take a resource id: 0x8048994 (31 cases, OBJ sets, jump table 0x80489A8) and 0x804A46C (17 cases, BG sets, jump table 0x804A490). Their entries read block tables 0x81D5F5C and 0x81D61DC, palettes 0x81D6060 and 0x81D6454.
- Menu strips: 0x8046FF0 (help, table 0x807900C), 0x8047010 (headers, 0x807909C), 0x8047030 (0x80790DC).

## Boss fights
Fights run in plain stage play (`st` 0), not in subs 11-14. **Verified** by `fight0`-`fight9`, cold boot, no forced play step except where noted.
- **Room bytes:** 0x3000050+0x5D, +0x5E, +0x5F select the stage file, area and room. Stage to 0x5D/0x5E: table 0x81AC794, read by 0x800408C. Writing the room to +0x72 and setting step 0x1A changes room.
- **Room header:** table 0x81C1878, index `5D*8 + 5E*4 + 5F`. 0x8008A14 copies 12 bytes to 0x3000D9C: flag, boss index (0x3000D9E, also the VS banner index), door x, door y, door height, walk-to x. Ten rooms have the flag set.
- **Door:** 0x8011DD4 tests the player (object slot 12, 0x3001D20: +0x10 x, +0x14 y, +0x1F state) against the door's band. If lips +0x61 >= quota +0x62, the player enters states 24-28, then 48. Short of the quota it only sets a flag.
- **Boss object:** door opening spawns the boss in object slot 30. Type byte +0x1E indexes table 0x81A3D60. Proof: `tools/debug/objlog.lua`.

| Scene | Stage, room | Boss index | Object type | VS banner seen (step 104) |
|---|---|---|---|---|
| `fight0` | 2, 0 | 0 | 32 | yes |
| `fight1` | 4, 1 | 1 | 33 | yes |
| `fight2` | 8, 0 | 2 | 34 | yes |
| `fight3` | 13, 2 | 3 | 35 | yes |
| `fight4` | 17, 0 | 4 | 36 | yes |
| `fight5` | 21, 0 | 5 | 37 | yes |
| `fight6` | 22, 0 | 6 | 38 | no |
| `fight7` | 22, 1 | 7 | 38 | no |
| `fight8` | 22, 2 | 8 | 38 | no |
| `fight9` | 22, 3 | 9 | 38 | yes |

Limits of these scenes:
- The warp teleports the player onto the door and fills the lips quota, so it skips the walk through the stage. Rooms 1-3 are entered by the room-change step, not through the previous room.
- `fight6` is forced: boss state 2 waits on helper slots 32 and 38 (byte +0x2A), which never finish after a warp, so `warp.lua` clears them. Why they hold is not known, and this path may not match real play.
- `fight6`-`fight8` showed no banner in 7000 frames. **guess:** the final boss only has one, in its last room. Their proof is the object type plus the shots.
- The player takes damage and often dies soon after the banner: `GOD` pins lives only. No scene has won a fight. The `defeat*` scenes swap each boss's defeat script into its intro slot, which shows the lines but not a real win (`windows.md`); boss 5's m206-m261 still need a real win.

**Subs 11-14 can't be reached in play (verified statically, with `disasm.py xref`; a computed jump would not show).**
- Events 0x15-0x18 set them, and all 27 callers of 0x8037B8C pass other constants.
- The only other writes that take `sub` from a variable are 0x802E946 and 0x802EC62. Both hang from the nested step tables under 0x81A5AA8, whose dispatcher 0x802E800 has no references.
- Sub 18, the debug menu that lists BOM to BOT, is set only by event 0x1E. Its one caller 0x8044024 (held L+R+Select+Start) has no references either.

So the black screens were never a player-visible bug. Shared code: sub 11 with type 32 (0x8058B88, 0x8058C04), sub 12 with type 37 (0x805B1A8). **guess:** sub 13 with type 34 and sub 14 with type 33; the old `boss_t` scene and `fight1` unpack the same marquee, which supports the second.

## Text
- `tools/debug/textwatch.lua` logs the first read of each byte of the two text banks; `tools/debug/textcover.py ROM OUT...` says which strings a tour read. Bubbles wait for a press, so reading a scene's text needs `--mash 20` and more frames.
- Coverage (2026-11-07, marker tour of 160 scenes, `markercover.py`): box 27/27, bubble 751/807, sign 40/41 (s040 is empty). Not reached: boss 5's defeat lines m206-m261, and the 39 pointerless strings (`text.md`).
