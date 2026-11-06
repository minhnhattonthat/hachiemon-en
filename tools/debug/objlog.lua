-- Logs each object type >= 32 (boss types, dispatch table 0x81A3D60) the first time a slot holds it. Add to any emu.py run: --script tools/debug/objlog.lua
local mem = emu.memType.gbaMemory
local seen = {}
L.on_frame(function(f)
  for slot = 0, 99 do
    local t = emu.read(0x03001A20 + slot * 0x40 + 0x1E, mem)
    if t >= 32 and t < 64 and not seen[t] then
      seen[t] = true
      L.log(string.format("object type %d slot %d at f%d", t, slot, f))
    end
  end
end)
