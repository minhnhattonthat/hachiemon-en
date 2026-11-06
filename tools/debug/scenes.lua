-- Scene list for tools/debug/warp.lua. Facts behind it: docs/re/flow.md.
-- sub   = flow substate written to 0x3001A04 (st = 0x3000C90, default 1)
-- node  = map node (0x1C4190 table), written to both node fields of 0x300498C
-- talk  = talk scene id, byte 0x300527C
-- check = substate the game must reach for the warp to count (default sub)
local S = {
  logos     = { sub = 0 },
  delete    = { sub = 1 },
  title     = { sub = 2 },
  menu      = { sub = 3 },
  continue_cut = { sub = 5 },
  opening   = { sub = 6 },
  map       = { sub = 7, node = 1 },
  gameover  = { sub = 8 },
  slot      = { sub = 9 },
  credits   = { sub = 17 },
  -- Same flow names as the leftover debug page (strings at 0x78488): DME, DES, BOM, BOG, BOB, BOT.
  dme_ending = { sub = 5, step = 0x38 },
  des       = { sub = 15 },
  -- Real boss fights, by the room header's boss index (table 0x81C1878): docs/re/flow.md, Boss fights.
  -- room = room inside the stage, reached through the room-change step.
  fight0    = { sub = 16, node = 2,  boss = 0 },            -- stage 2
  fight1    = { sub = 16, node = 5,  boss = 1, room = 1 },  -- stage 4
  fight2    = { sub = 16, node = 11, boss = 2 },            -- stage 8
  fight3    = { sub = 16, node = 20, boss = 3, room = 2 },  -- stage 13
  fight4    = { sub = 16, node = 26, boss = 4 },            -- stage 17
  fight5    = { sub = 16, node = 31, boss = 5 },            -- stage 21
  fight6    = { sub = 16, node = 33, boss = 6, no_vs = true },            -- stage 22
  fight7    = { sub = 16, node = 33, boss = 7, room = 1, no_vs = true },
  fight8    = { sub = 16, node = 33, boss = 8, room = 2, no_vs = true },
  fight9    = { sub = 16, node = 33, boss = 9, room = 3 },
  -- Each boss's defeat script, run in place of its intro (warp.lua, swap): the fight scene plus {intro, defeat}.
  defeat0   = { sub = 16, node = 2,  boss = 0, swap = { 0x081C7100, 0x081C7738 } },
  defeat1   = { sub = 16, node = 5,  boss = 1, room = 1, swap = { 0x081D36BC, 0x081D3CB4 } },
  defeat2   = { sub = 16, node = 11, boss = 2, swap = { 0x081D1F28, 0x081D2640 } },
  defeat3   = { sub = 16, node = 20, boss = 3, room = 2, swap = { 0x081E8B98, 0x081E8FB4 } },
  defeat4   = { sub = 16, node = 26, boss = 4, swap = { 0x081E9258, 0x081E9664 } },
  defeat5   = { sub = 16, node = 31, boss = 5, swap = { 0x081CF868, 0x081CFF94 } },
  -- The fight, then the boss's own defeat states from state `win` on (warp.lua): actors and rooms as in a real win.
  win5      = { sub = 16, node = 31, boss = 5, win = 33, win_slot = 33 },
  win5l     = { sub = 16, node = 31, boss = 5, win = 33, win_slot = 33, win_dx = -60 },
  win5r     = { sub = 16, node = 31, boss = 5, win = 33, win_slot = 33, win_dx = 40 },
  defeat9   = { sub = 16, node = 33, boss = 9, room = 3, swap = { 0x081E98AC, 0x081E9C68 } },
  -- Menu pages, reached with the game's own cursor.
  -- cursor: 0x3005256, the menu row; the default row depends on whether a save exists.
  menu_diff = { sub = 3, cursor = 0, keys = "a" },
  menu_slot = { sub = 3, cursor = 0, keys = "a,a" },
  menu_load = { sub = 3, cursor = 1, keys = "a" },
  menu_opts = { sub = 3, cursor = 2, keys = "a" },
  menu_bgm  = { sub = 3, cursor = 2, keys = "a,down" },
  menu_se   = { sub = 3, cursor = 2, keys = "a,down,down" },
  -- Title with the clear decoration: 0x3003DDE holds one bit per difficulty with all 28 stages cleared.
  title_clear = { sub = 2, w = { [0x03003DDE] = 7 } },
  -- Failed-load screen: sub 15 step 1 goes here when slot data fails its check. Rows 11 and 13.
  save_error  = { sub = 15, step = 2 },
  -- Delete flow step 7, 0x2D0E10: the "deleted" message.
  delete_done = { sub = 1, step = 7 },
  -- In a stage, on stage 5 (no opening sign). Steps are the table at 0x81A3A38: docs/re/flow.md.
  pause       = { sub = 16, node = 7, check = 16, play = true, keys = "start" },
  pause_down  = { sub = 16, node = 7, check = 16, play = true, keys = "start,down" },
  pause_exit  = { sub = 16, node = 7, check = 16, play = true, keys = "start,down,a" },
  stage_clear = { sub = 16, node = 7, check = 16, play_step = 48 },
  sign        = { sub = 16, node = 7, check = 16, play_step = 32 },
  death       = { sub = 16, node = 7, check = 16, play_step = 4 },
  death_last  = { sub = 16, node = 7, check = 16, play_step = 4, w = { [0x0300198C] = 0 } },  -- lives 0: game over
  step96      = { sub = 16, node = 7, check = 16, play_step = 96 },
  -- TIME OVER, row 26: 0x8010C08 runs when bit 4 of byte 0x3000D29 is set; play_step 2 is the step play already sits on.
  time_over   = { sub = 16, node = 7, check = 16, play_step = 2, at_step = { [0x03000D29] = 4 } },
  step64      = { sub = 16, node = 7, check = 16, play_step = 64 },
  -- VS banners, steps 104-107: the table at 0x1A3D10, indexed by the 16-bit value at 0x3000D9E (set as the step is forced).
  vs0         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 0 } },
  vs1         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 1 } },
  vs2         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 2 } },
  vs3         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 3 } },
  vs4         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 4 } },
  vs5         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 5 } },
  vs6         = { sub = 16, node = 7, check = 16, play_step = 104, at_step = { [0x03000D9E] = 6 } },
}
-- Stage N (1-28): map node holding stage N in the table at 0x1C4190; the card shows, then play starts.
local stage_nodes = { 1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 19, 20, 22, 23, 25, 26, 28, 29, 30, 31, 33, 34, 35, 36, 37, 38, 39 }
for n, node in ipairs(stage_nodes) do
  S[string.format("stage%02d", n)] = { sub = 16, node = node, check = 16 }
end
-- Signboard text by table index (0x1C1280): play step 32 reads the index from byte 0x3000DED (0x8002D02). Entry 40 is empty.
for n = 0, 39 do
  S[string.format("sign%02d", n)] = { sub = 16, node = 7, check = 16, play_step = 32, at_step = { [0x03000DED] = n } }
end
-- Help strips by index (0x79010 table): byte 0x3005263 picks the strip the menu's idle cycle reloads.
for n = 0, 8 do S["help" .. n] = { sub = 3, pin = { [0x03005263] = n } } end
-- Talk scenes (bubble comedy) by id. Ids 1-0x1D read text; 0 and 0x1E-0x2B read none in 9000 frames and no map node uses them.
for id = 1, 0x1D do
  S[string.format("talk%02d", id)] = { sub = 10, talk = id, node = 1 }
end
return S
