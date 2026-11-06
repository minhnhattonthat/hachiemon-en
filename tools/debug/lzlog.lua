-- Logs each compressed block the game unpacks: "lz f<frame> <rom offset> -> <dest>" for the BIOS LZ77 wrapper
-- 0x8075B74 (the only svc 0x12) and the game's own Le decoder 0x80009D8/0x8000A34. Ties scenes to docs/re/graphics.md rows.
-- Add with --script tools/debug/lzlog.lua
local function hook(addr)
  L.on_exec(addr, addr, function()
    local s = emu.getState()
    L.log(string.format("lz f%d %06X -> %08X", L.frame, s["cpu.r0"] & 0x1FFFFFF, s["cpu.r1"]))
  end)
end
hook(0x08075B74)
hook(0x080009D8)
hook(0x08000A34)
