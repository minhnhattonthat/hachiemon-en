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
| 11-14 | 0x80568FD... | **Not proven on screen.** Script scenes named BOM, BOG, BOB, BOT on the debug page: see Open | `boss_m`, `boss_g`, `boss_b`, `boss_t` (tour fails them) |
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

## Open: subs 11-14
The four `boss_*` scenes pass their flags but every shot is black, from the title and from running play alike. Known so far:
- The handlers run: `boss_t` keeps unpacking marquee frames (row 17) and `boss_g` its own blocks, and `boss_b` and `boss_t` read main-bank text.
- BLDCNT 0x00FF and BLDY 0x10 hold (fade to black) with a filled palette. Forcing BLDY to 0 from Lua did not show a picture; whether those writes took effect was not checked.
- `boss_m`'s script (0x81C7100, words read through 0x8056990) stays at index 21, op 2. The op's wait condition is not understood.
- No static caller passes events 0x15-0x18, which are what set these subs in 0x8037B8C. The debug page (0x802EC5C) writes st, sub, step directly. **guess:** the subs are reached only from that page, and real boss fights run in stage play after the VS banner (play step 104).
- Row 17's marquee has been seen unpacking only here. Whether players ever see it is open.

Next tries: drive the debug page (`sub` 18) to a boss and compare state; find which stages hold the fights and add a scene for one.

## Text
- `tools/debug/textwatch.lua` logs the first read of each byte of the two text banks; `tools/debug/textcover.py ROM OUT` says which strings a tour read.
