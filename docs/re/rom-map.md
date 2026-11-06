# ROM map

Header: title `HACHIEMON`, game code `A8EJ`, maker `AF` (Namco), 4 MiB (4,194,304 bytes), SHA-1 `10c16950388599846c2a61cacc315ba81a752deb`. Save: EEPROM (`EEPROM_V122` at 0x1A3330).

| Range | Content | State |
|---|---|---|
| 0x000000-0x07FFFF | Thumb code plus literal pools | verified (disassembly) |
| 0x080000-0x1AFFFF | Mostly sound and level tables, no tile text in a sampled render (`work/re/audio_probe.png`, not kept) | guess from entropy and the render |
| 0x1B0000-0x1BFFFF | Sparse tables, 3 LZ blocks | guess |
| 0x1C0000-0x1C1FFF | Tutorial text and its table | verified |
| 0x1C2000-0x1D94FF | Tables and rows, including speech rows that point at the text bank | partly verified |
| 0x1D9554-0x1DCFC7 | Main text bank | verified |
| 0x1DD000-0x1EAFFF | Speech rows that point at the text bank | guess on layout |
| 0x1F0000-0x2B4AE3 | High entropy, no LZ blocks, no tile text in a sampled render: most likely PCM samples | guess |
| 0x2B4AE4-0x3A85D6 | Graphics: LZ77 tile blocks, raw palettes between them, raw font at 0x2FFC50 | verified |
| 0x3A85D7-0x3FFFFF | Zero fill, 0x57A29 bytes (358 KB) | **candidate only**, see below |

## Compression
**verified** BIOS LZ77 type 0x10: 1,198 blocks found by `tools/gbacomp.py scan` (2.3 MB unpacked), decoder and encoder in the same file, round trip tested on real blocks (`tests/test_recon.py`). PC 0xC08 in the BIOS writes the tile data, so the blocks are unpacked straight to VRAM: an edited block must keep the BIOS VRAM rule (no distance-1 matches), which `lz_compress` follows.

**verified** Le: `le_compress` is the encoder for the game's own codec. `tools/gbacomp.py verify ROM` recompresses every block and decodes it back: all 1,198 LZ77 and 1,336 Le blocks roundtrip (LZ77 822,180 bytes against 821,432 originally, Le 790,912 against 792,353; 28 s, so it stays out of the commit hook). The game's own decoders also accepted both: see the moved tour under Free space. Not checked: how Le writes to VRAM, so `le_compress` may use distance-1 copies that a 16-bit VRAM write would break. The moved tour showed row 21 and 22 banners without visible damage at the shots taken.

Neither encoder reproduces the original bytes, so the identity build (`tools/build.py`, `tests/test_build.py::test_identity_build`) keeps untouched blocks as they are and only edited ones get recompressed.

## Free space
- **Candidate** 0x3A85D7-0x3FFFFF, 358 KB of zeros. Not trap-tested: nothing has filled it with garbage. No pointer word in the ROM targets this range except possible chance matches. `tools/debug/moved.py` put all text and 236 recompressed blocks at 0x3A8600-0x3DF6FC with the old bytes wiped: tour 113/113 ok (2026-11-06). 307 of 446 shots were pixel-identical to the original's. The rest I sampled (15 side-by-side pairs, fights at low scale) showed the same art with a different animation phase, plus empty save slots on the menus because `moved.gba` had its own blank save. The original also differed from itself between runs in 5 of 11 scenes checked, so a pixel-exact pass isn't available. 0x3DF6FC-0x3FFFFF was not exercised.
- **Safe fallback** Past the original end. EEPROM games must stay at or under 16 MiB (at that size the EEPROM moves), so growing to 8 MiB is fine and gives 4 MiB of certain space. The text needs well under 100 KB. Recompressed graphics may also land there.

## Prior work
None found: a web search on 2026-11-06 turned up no fan patch, tool or table for this game.
