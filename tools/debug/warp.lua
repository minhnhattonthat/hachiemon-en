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

local warped, reached = false, false
local playing, settle, pressed
L.on_frame(function(f)
  local st, sub, step = r32(ST), r32(SUB), r32(STEP)
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
  if GOD and warped then w8(PLAYER + 0x1C, 5) end
end)
