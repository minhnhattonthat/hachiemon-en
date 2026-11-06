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


def main():
    for s in sprites(open(sys.argv[1], "rb").read()):
        print("x%4d y%4d %2dx%-2d tile %03x pal %x prio %d" % s)
    if len(sys.argv) > 2:
        io = open(sys.argv[2], "rb").read()
        print(f"DISPCNT {struct.unpack_from('<H', io, 0)[0]:04x}", *(f"BG{n}CNT {struct.unpack_from('<H', io, 8 + n * 2)[0]:04x}" for n in range(4)))


if __name__ == "__main__":
    main()
