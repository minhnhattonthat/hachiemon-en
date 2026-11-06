-- Logs the first read of each byte in the two text banks: "txt f<frame> <rom offset> <pc>". Catches every path that
-- reaches a string (box writer, bubble writer, computed address), so a string no scene ever reads is shown dead or missed.
-- Add with --script tools/debug/textwatch.lua; summary: tools/debug/textcover.py
local seen = {}
local function watch(addr)
  if not seen[addr] then
    seen[addr] = true
    L.log(string.format("txt f%d %06X %08X", L.frame, addr & 0x1FFFFFF, L.pc()))
  end
end
L.on_read(0x081C0984, 0x081C127C, watch)
L.on_read(0x081D9554, 0x081DCFC8, watch)
