"""List the visible sprites of a ppudump.lua dump, to read how a sheet of tiles is laid out on screen.

    python -X utf8 tools/debug/oamlist.py DUMP.oam.bin [DUMP.io.bin]    # x y w h tile pal prio; plus DISPCNT and the BG registers
"""
import struct
import sys

SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
         (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def sprites(oam):
    """(x, y, w, h, tile, palette, priority) of each sprite the PPU would draw."""
    out = []
    for i in range(0, 1024, 8):
        a0, a1, a2 = struct.unpack_from("<HHH", oam, i)
        if a0 >> 8 & 3 == 2:  # hidden
            continue
        w, h = SIZES[(a0 >> 14, a1 >> 14)]
        out.append((a1 & 0x1FF if a1 & 0x1FF < 240 else (a1 & 0x1FF) - 512, a0 & 0xFF if a0 & 0xFF < 160 else (a0 & 0xFF) - 256, w, h, a2 & 0x3FF, a2 >> 12, a2 >> 10 & 3))
    return out


def bgmap(vram, io, bg, lo=1, hi=0x3FF):
    """Rows of BG `bg`'s text-mode map that show a tile in lo..hi: (row, first col, tile numbers; -- marks others)."""
    cnt = struct.unpack_from("<H", io, 8 + bg * 2)[0]
    base = (cnt >> 8 & 31) * 0x800
    out = []
    for y in range(32):
        tiles = [struct.unpack_from("<H", vram, base + (y * 32 + x) * 2)[0] for x in range(32)]
        shown = [t & 0x3FF if lo <= t & 0x3FF <= hi else None for t in tiles]
        if any(t is not None for t in shown):
            first = next(i for i, t in enumerate(shown) if t is not None)
            out.append((y, first, " ".join("--" if t is None else f"{t:x}" for t in shown[first:])))
    return (cnt >> 2 & 3) * 0x4000, out


def main():
    if sys.argv[1] == "--bg":  # --bg N LO HI DUMP.vram.bin DUMP.io.bin: tile rows, to read a BG picture's layout
        n, lo, hi, vram, io = int(sys.argv[2]), int(sys.argv[3], 16), int(sys.argv[4], 16), open(sys.argv[5], "rb").read(), open(sys.argv[6], "rb").read()
        char, rows = bgmap(vram, io, n, lo, hi)
        print(f"BG{n} tiles at VRAM {char:#x}")
        for row in rows:
            print("row %2d col %2d: %s" % row)
        return
    for s in sprites(open(sys.argv[1], "rb").read()):
        print("x%4d y%4d %2dx%-2d tile %03x pal %x prio %d" % s)
    if len(sys.argv) > 2:
        io = open(sys.argv[2], "rb").read()
        print(f"DISPCNT {struct.unpack_from('<H', io, 0)[0]:04x}", *(f"BG{n}CNT {struct.unpack_from('<H', io, 8 + n * 2)[0]:04x}" for n in range(4)))


if __name__ == "__main__":
    main()
