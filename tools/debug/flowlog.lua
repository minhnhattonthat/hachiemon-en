-- Logs every change of the game's flow variables (docs/re/flow.md). Add to any emu.py run: --script tools/debug/flowlog.lua
local mem = emu.memType.gbaMemory
local function r32(a) return emu.read(a, mem) | emu.read(a + 1, mem) << 8 | emu.read(a + 2, mem) << 16 | emu.read(a + 3, mem) << 24 end
local last
L.on_frame(function(f)
  local s = string.format("st=%d sub=%d step=%d stage=%08X", r32(0x03000C90), r32(0x03001A04), r32(0x03000830), r32(0x0300498C))
  if s ~= last then L.log(string.format("f%d %s", f, s)); last = s end
end)
