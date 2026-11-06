-- Warp from a cold boot to any scene in scenes.lua. Facts: docs/re/flow.md.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --var "SCENE='stage05'" --frames 900 --sheet
-- Opt-in: --var GOD=1 (pins lives and the hit counter every frame). --var "DIFF=2" (1 easy, 2 normal, 4 hard, 8 very hard).
local mem = emu.memType.gbaMemory
local function r8(a) return emu.read(a, mem) end
local function w8(a, v) emu.write(a, v & 255, mem) end
local function r32(a) return r8(a) | r8(a + 1) << 8 | r8(a + 2) << 16 | r8(a + 3) << 24 end
local function w32(a, v) for i = 0, 3 do w8(a + i, v >> (i * 8)) end end

local ST, SUB, STEP, PROG, TALK = 0x03000C90, 0x03001A04, 0x03000830, 0x0300498C, 0x0300527C
local PLAYER = 0x03001970  -- cleared by the new-game routine 0x8007350

local scenes = dofile("../debug/scenes.lua")
local scene = scenes[assert(SCENE, "set --var \"SCENE='name'\"")]
if not scene then error("unknown scene " .. tostring(SCENE)) end

-- What 0x8037DAC (new game) and 0x8007350 do, so a warped scene has the state a real new game has.
local function new_game()
  for i = 0, 0x93 do w8(PLAYER + i, 0) end
  w8(PLAYER + 0x1C, 5)
  w8(PLAYER + 0x1E, DIFF or 1)
  for _, o in ipairs({ 0x61, 0x62, 0x7C, 0x76 }) do w8(0x03000050 + o, 0) end
  w32(PROG, 1)
end

-- A boss fight the way a player starts it: docs/re/flow.md, Boss fights. Teleports onto the room's boss door with the
-- lips quota met, then presses A through the bubbles. Runs only in plain play (st 0, step 2).
local G, PL = 0x03000050, 0x03001D20  -- PL: player object, slot 12 of the object array at 0x3001A20
local fight_phase, fight_wait, fight_held = 0, 0, 0
local function fight(st, step)
  if st ~= 0 or step ~= 2 or fight_phase == 3 then return end
  fight_wait = fight_wait + 1
  if fight_wait < 60 then return end
  fight_wait = 0
  if fight_phase == 0 then
    fight_phase = 1
    if scene.room then
      w8(G + 0x72, scene.room)  -- what the room-change step 0x1A reads
      w32(STEP, 0x1A)
      return
    end
  end
  if fight_phase == 1 then
    fight_phase = 2
    local idx = r8(0x03000D9E) | r8(0x03000D9F) << 8
    if idx ~= scene.boss then error(string.format("room holds boss %d, scene wants %d", idx, scene.boss)) end
    local x = r8(0x03000DA0) | r8(0x03000DA1) << 8
    local y = r8(0x03000DA2) | r8(0x03000DA3) << 8
    local h = r8(0x03000DA4) | r8(0x03000DA5) << 8
    w8(G + 0x61, r8(G + 0x62))
    -- Inside the door's hit band (0x8011DD4): door x*8 - 8, less the player's box. Its height counts in 16-pixel units.
    w32(PL + 0x10, x * 8 - 13)
    w32(PL + 0x14, y * 8 + h * 16 - 1)
    fight_phase = 3
    for _ = 1, 400 do L.press("a", 6); L.press("-", 24) end
  end
end

local warped, reached = false, false
local playing, settle, pressed
-- A defeat scene runs the boss's defeat script in place of its intro: the stage VM 0x8056990 takes the script in r0.
-- Nothing has won a fight, so this is how the defeat lines get on screen; actors may not stand where a real win leaves them.
if scene.swap then
  L.on_exec(0x08056990, 0x08056990, function()
    local s = emu.getState()
    if s["cpu.r0"] == scene.swap[1] then
      s["cpu.r0"] = scene.swap[2]
      emu.setState(s)
      if not reached then
        reached = true
        L.log(string.format("reached sub=%d step=%d at f%d (script %08X)", r32(SUB), r32(STEP), L.frame, scene.swap[2]))
      end
    end
  end)
end

-- A swapped-in defeat script can wait on a boss state a real win would have set up. When its pc holds still for STALL
-- frames, step over that op so the rest of the script's text still shows. Lengths: STAGE in tools/vmscript.py.
local STAGE_LEN = { [1] = 2, [2] = 1, [0x80] = 4, [0x81] = 4, [0x92] = 4, [0x93] = 4, [0x86] = 4, [0xB0] = 4, [0x87] = 2, [0x8E] = 8,
  [0x8F] = 2, [0x91] = 2, [0x96] = 3, [0x97] = 2, [0x98] = 2, [0x9E] = 4, [0x9F] = 1, [0xA3] = 17, [0xA4] = 17, [0xA6] = 2, [0xA7] = 4,
  [0xAA] = 3, [0xAF] = 7, [0xB3] = 1, [0xB4] = 4, [0x9A] = 3, [0x9B] = 6, [0xA1] = 5, [0xA2] = 4, [0xA5] = 2, [0xB1] = 1, [0xB2] = 2,
  [0xB5] = 1, [0xB7] = 1 }
for op = 0xC0, 0xDE do STAGE_LEN[op] = 9 end
local PC, STALL = 0x03003E10, 400
local last_pc, held = -1, 0
local function unstick(f)
  local pc = r32(PC)
  if pc ~= last_pc then
    last_pc, held = pc, 0
    return
  end
  held = held + 1
  if held < STALL then return end
  held = 0
  local op = r32(scene.swap[2] + pc * 4)
  local len = STAGE_LEN[op]
  if len and op ~= 4 then
    w32(PC, pc + len)
    L.log(string.format("unstick f%d pc %d op %02X", f, pc, op))
  end
end

L.on_frame(function(f)
  local st, sub, step = r32(ST), r32(SUB), r32(STEP)
  if scene.swap and reached then unstick(f) end
  if scene.boss and warped then fight(st, step) end
  -- The title's wait step is the first safe screen: the logos have run and the save has been read.
  if not warped and st == 1 and sub == 2 and step == 2 then
    warped = true
    new_game()
    local node = NODE or scene.node  -- --var NODE=n picks any map node
    if node then w32(PROG, 1 | node << 1 | node << 7) end
    if scene.talk then w8(TALK, scene.talk) end
    for a, v in pairs(scene.w or {}) do w8(a, v) end
    w32(ST, scene.st or 1)
    w32(SUB, scene.sub)
    w32(STEP, scene.step or 0)
    L.log(string.format("warp %s at f%d", SCENE, f))
  elseif warped and not reached and scene.boss then
    -- Step 104 is the VS banner: the game itself has started the fight. Rooms 0-2 of stage 22 have no banner, so the
    -- proof there is the boss object in slot 30 (its type is 38 in all four rooms).
    if st == 0 and (step == 104 or (scene.no_vs and fight_phase == 3 and r8(0x03001A20 + 30 * 0x40 + 0x1E) == 38)) then
      reached = true
      L.log(string.format("reached sub=%d step=%d at f%d", sub, step, f))
    end
  elseif warped and not reached and sub == (scene.check or scene.sub) and st == (scene.st or 1) and step > 0 then
    reached = true
    L.log(string.format("reached sub=%d step=%d at f%d", sub, step, f))
  end
  -- A scene's "then": once play has run THEN_WAIT frames (st 0, step 2), force a play step (stage clear, death...).
  local poke = THEN or scene.play_step
  if poke and warped and st == 0 and step == 2 then
    playing = (playing or 0) + 1
    if playing == (THEN_WAIT or 120) then
      for a, v in pairs(scene.at_step or {}) do w8(a, v) end
      w32(STEP, poke)
      L.log(string.format("play step %d forced at f%d", poke, f))
    end
  end
  -- Press scene.keys, one every 60 frames, once the scene has settled: menus at once, stages when play has begun.
  if scene.keys and reached and not pressed and (not scene.play or (st == 0 and step == 2)) then
    settle = (settle or 0) + 1
    if settle == 120 then
      pressed = true
      if scene.cursor then w8(0x03005256, scene.cursor) end
      for key in scene.keys:gmatch("[^,]+") do L.press(key, 6); L.press("-", 54) end
    end
  end
  if reached then for a, v in pairs(scene.pin or {}) do w8(a, v) end end
  -- shortcut: forces fight6 past boss state 2, whose helpers (slots 32, 38) never finish after a warp; find out why if its later states matter.
  if scene.boss == 6 and r8(0x03001A20 + 30 * 0x40 + 0x1E) == 38 and r8(0x03001A20 + 30 * 0x40 + 0x1F) == 2 then
    fight_held = fight_held + 1
    if fight_held == 120 then
      w8(0x03001A20 + 32 * 0x40 + 0x2A, 0)
      w8(0x03001A20 + 38 * 0x40 + 0x2A, 0)
    end
  end
  if GOD and warped then w8(PLAYER + 0x1C, 5) end
end)
