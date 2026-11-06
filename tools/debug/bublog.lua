-- Logs what the text engine shows, for a build whose text sits at 0x400000+ (tools/debug/marker.py).
--   "bub f<frame> <slot> <string> x<x> y<y> c<cols> r<rows> base<+0x2A>/<+0x30>"  each bubble slot, once per string and position
--   "box f<frame> <string>"                                    each box string, on the first read of its first bytes
--   "oam f<frame> <tile>"                                      each OBJ tile number, the first time OAM uses it
-- Bubble slots: 3 at 0x30042A8, 0x44 bytes each: +0x10 text, +0x1A x, +0x1C y, +0x28 cols, +0x29 rows-1 (docs/re/text.md).
local mem = emu.memType.gbaMemory
local function r8(a) return emu.read(a, mem) end
local function r16(a) return r8(a) | r8(a + 1) << 8 end
local function r32(a) return r16(a) | r16(a + 2) << 16 end
local seen, tiles = {}, {}
L.on_frame(function(f)
  for slot = 0, 2 do
    local b = 0x030042A8 + slot * 0x44
    local text = r32(b + 0x10)
    if text >= 0x08400000 and text < 0x08800000 then
      local line = string.format("bub %d %06X x%d y%d c%d r%d base%d/%d", slot, text & 0x1FFFFFF, r16(b + 0x1A), r16(b + 0x1C), r8(b + 0x28), r8(b + 0x29) + 1, r8(b + 0x2A), r8(b + 0x30)) .. string.format(" tile%d+%d", r16(b + 0x34), r8(b + 0x26))
      if not seen[line] then
        seen[line] = true
        local cols, rows = r8(b + 0x28), r8(b + 0x29) + 1
        local past = r16(b + 0x34) + (r8(b + 0x26) + (cols + (cols & 1)) * rows) * 2
        L.log(string.format("bub f%d %s past%d", f, line:sub(5), past))
      end
    end
  end
  -- Every OBJ tile the scene ever uses, visible or not yet: text cells stay in VRAM after a bubble closes, so a cell that
  -- reaches an actor's tiles paints over that actor for the rest of the scene (tools/debug/limits.py sets the room from this).
  if f % 4 == 0 then
    for n = 0, 127 do
      local a = 0x07000000 + n * 8
      if (r16(a) >> 8) & 3 ~= 2 then
        local t = r16(a + 4) & 0x3FF
        if not tiles[t] then
          tiles[t] = true
          L.log(string.format("oam f%d %d", f, t))
        end
      end
    end
  end
end)
local read = {}
L.on_exec(0x080383B8, 0x080383B8, function()
  local s = emu.getState()
  local text = s["cpu.r1"]
  if not read[text] then
    read[text] = true
    L.log(string.format("box f%d %06X", L.frame, text & 0x1FFFFFF))
  end
end)
