-- Logs each change of the boss object's state (slot 30, or --var BOSS_SLOT=n: +0x1E type, +0x1F, +0x26 state, +0x28 step), play step and the stage VM pc.
local mem = emu.memType.gbaMemory
local function r8(a) return emu.read(a, mem) end
local function r32(a) return r8(a) | r8(a + 1) << 8 | r8(a + 2) << 16 | r8(a + 3) << 24 end
local B = 0x03001A20 + (BOSS_SLOT or 30) * 0x40
local last
L.on_frame(function(f)
  local line = string.format("type%d b1F=%d st%d s28=%d step%d sub%d pc%d", r8(B + 0x1E), r8(B + 0x1F), r8(B + 0x26), r8(B + 0x28), r32(0x03000830), r32(0x03001A04), r32(0x03003E10))
  if line ~= last then
    last = line
    L.log(string.format("boss f%d %s", f, line))
  end
end)
