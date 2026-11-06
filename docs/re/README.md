# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| `rom-map.md` | Header, region map, LZ77 and Le, free space, prior work | Both encoders verified, Le safe to VRAM; English text past the original end; some regions guessed |
| `text.md` | Encoding, control codes, draw paths, English text cells, text banks, script VMs, speakers, pointer forms | Encoding, VMs, FD and cells verified; speaker names and the 39 pointerless strings still guesses |
| `windows.md` | Text limits per variant, the rules behind them, how they were measured | Width gate met; 96 limits guessed, listed there |
| `graphics.md` | Survey of Japanese drawn as tiles, block pointer slots | Every row unpacked by a warp scene; slots found for every row; rows 23-27 and the slot machine and area banner blocks still to read closely or pin |
| `flow.md` | Game states, scene ids, loaders behind `tools/debug/` | Warps verified by the tour; boss fights verified; defeat lines by swapped script, except boss 5's m206-m261 |
