-- Logs the first frame a visible sprite uses an OBJ tile in OBJ_LO..OBJ_HI, per tile, with its position. Add to a run:
--   --script tools/debug/oamtile.lua --var OBJ_LO=0x86 --var OBJ_HI=0xC5
local mem = emu.memType.gbaMemory
local seen = {}
L.on_frame(function(f)
  for i = 0, 127 do
    local a = 0x07000000 + i * 8
    local attr0 = emu.read(a, mem) | emu.read(a + 1, mem) << 8
    if attr0 & 0x0300 ~= 0x0200 then -- 0x200 without the affine bit means hidden
      local tile = (emu.read(a + 4, mem) | emu.read(a + 5, mem) << 8) & 0x3FF
      if tile >= OBJ_LO and tile <= OBJ_HI and not seen[tile] then
        seen[tile] = true
        local x = (emu.read(a + 2, mem) | emu.read(a + 3, mem) << 8) & 0x1FF
        L.log(string.format("oam tile %03X f%d x%d y%d", tile, f, x, attr0 & 0xFF))
      end
    end
  end
end)
