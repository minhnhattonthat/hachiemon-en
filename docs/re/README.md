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
| `rom-map.md` | Header, region map, LZ77, free space, prior work | Compression verified; free space is a candidate; some regions guessed |
| `text.md` | Encoding, control codes, draw paths, text banks, pointer forms | Encoding verified; FD and speech rows still guesses |
| `graphics.md` | Survey of Japanese drawn as tiles | Sources from the static sweep; screens to confirm at phases 2 and 5 |
