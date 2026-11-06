"""Which packed block holds the tiles a screen shows at a pixel? For finding the source of lettering seen in a shot.

    python -X utf8 tools/debug/whichblock.py DUMP_STEM X Y [W H]     (DUMP_STEM from ppudump.lua; screen pixels, default a 16x16 area)
Reads every enabled text BG's scroll and map, and every sprite over the area; prints each distinct tile's matches among all packed blocks.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import packed_spans  # noqa: E402
from gfxview import ROM, unpack  # noqa: E402
from oamlist import sprites  # noqa: E402


def main():
    stem, x, y, *rest = sys.argv[1:]
    x, y = int(x), int(y)
    w, h = (int(rest[0]), int(rest[1])) if rest else (16, 16)
    vram, io, oam = (Path(f"{stem}.{e}.bin").read_bytes() for e in ("vram", "io", "oam"))
    disp = struct.unpack_from("<H", io, 0)[0]
    tiles = {}
    for bg in range(4):
        if not disp >> (8 + bg) & 1:
            continue
        cnt = struct.unpack_from("<H", io, 8 + bg * 2)[0]
        sx, sy = struct.unpack_from("<HH", io, 0x10 + bg * 4)
        base, chars = (cnt >> 8 & 31) * 0x800, (cnt >> 2 & 3) * 0x4000
        for py in range(y, y + h, 8):
            for px in range(x, x + w, 8):
                mx, my = (px + sx) % 512 // 8, (py + sy) % 512 // 8
                screen = (mx // 32 if cnt >> 14 & 1 else 0) + (my // 32 * (2 if cnt >> 14 & 1 else 1) if cnt >> 15 & 1 else 0)
                word = struct.unpack_from("<H", vram, base + screen * 0x800 + (my % 32 * 32 + mx % 32) * 2)[0]
                tile = vram[chars + (word & 0x3FF) * 32:chars + (word & 0x3FF) * 32 + 32]
                if any(tile):
                    tiles.setdefault(tile, []).append(f"BG{bg} tile {word & 0x3FF:#x} pal {word >> 12:x}")
    for sx, sy, sw, sh, t, pal, _ in sprites(oam):
        if sx < x + w and x < sx + sw and sy < y + h and y < sy + sh:
            for n in range(sw // 8 * (sh // 8)):
                tile = vram[0x10000 + (t + n) * 32:0x10000 + (t + n) * 32 + 32]
                if any(tile):
                    tiles.setdefault(tile, []).append(f"OBJ tile {t + n:#x} pal {pal:x}")
    rom = ROM.read_bytes()
    blocks = [(o, unpack(rom, o)) for o, _ in packed_spans(rom)]
    for tile, where in tiles.items():
        hits = [f"{o:06x}+{u.find(tile) // 32:#x}" for o, u in blocks if u.find(tile) % 32 == 0 and u.find(tile) >= 0]
        raw = rom.find(tile)
        print(where[0], "packed:", hits[:6], "raw:", hex(raw) if raw >= 0 else None)


if __name__ == "__main__":
    main()
