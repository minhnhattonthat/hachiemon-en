"""Read stage art: a stage tileset by tile number, or a room's map layers as the game composes them, for finding lettered boards.

    python -X utf8 tools/debug/stagesheet.py tiles SET OUT.png [--zoom 3] [--pal PAL.bin]     SET 0-15: table 0x1A61C4, tile sheet with each tile's commonest palette
    python -X utf8 tools/debug/stagesheet.py room SET AREA ROOM LAYER OUT.png                 a room's map, 120 x 120 tiles
    python -X utf8 tools/debug/stagesheet.py uses SET TILE[-TILE]                             rooms, layers and map cells that use those tiles
    python -X utf8 tools/debug/stagesheet.py crop SET AREA ROOM LAYER X Y W H OUT.png         part of a room in cells, zoomed, and its tile numbers
Rooms: table 0x1A6244, 20-byte rows of 4 map blocks and one more, index SET*8 + AREA*4 + ROOM (flow.md, Room header).
"""
import argparse
import os
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gfxtext import unpack  # noqa: E402

ORIG = Path("rom/Hachiemon (Japan).gba")
ROM = Path(os.environ.get("STAGE_ROM", ORIG))  # STAGE_ROM=build/hachiemon_en.gba reads a build's tiles
SETS, ROOMS = 0x1A61C4, 0x1A6244
DUMMY = 0x231A04  # rows that all point here are unused rooms


def tileset(rom, n):
    return bytes(unpack(rom, struct.unpack_from("<I", rom, SETS + n * 8)[0] - 0x8000000)[0])


def room_maps(rom, n, area, room):
    """The room's map layers, each (w, h, words), or [] for an unused room."""
    row = struct.unpack_from("<3I", rom, ROOMS + (n * 8 + area * 4 + room) * 20)  # the fourth block is 120 x 120 bytes, not tile words
    if row[0] - 0x8000000 == DUMMY and n:
        return []
    out = []
    for w in row:
        d = bytes(unpack(rom, w - 0x8000000)[0])
        mw, mh = struct.unpack_from("<II", d, 0)
        out.append((mw, mh, struct.unpack_from(f"<{mw * mh}H", d, 16)))
    return out


def colours(pal, bank):
    return [((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8) for c in struct.unpack_from("<16H", pal, bank * 32)]


def draw_tile(px, x, y, tile, cols, h=0, v=0):
    for ty in range(8):
        for tx in range(8):
            b = tile[ty * 4 + tx // 2] >> (4 * (tx & 1)) & 15
            if b:
                px[x + (7 - tx if h else tx), y + (7 - ty if v else ty)] = cols[b]


def default_pal(n):
    """A palette dump of a stage on this set: tour dumps in work/qa/stg (the set's block appears in each log)."""
    want = f"{struct.unpack_from('<I', ORIG.read_bytes(), SETS + n * 8)[0] - 0x8000000:06X}"
    for log in sorted(Path("work/qa/stg").glob("*/log.txt")):
        if want in log.read_text(errors="ignore"):
            return next(log.parent.glob("ppu_*.pal.bin")).read_bytes()
    raise SystemExit(f"no dump of set {n}: run ppu.py on a stage that uses it")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode")
    p.add_argument("args", nargs="+")
    p.add_argument("--zoom", type=int, default=3)
    p.add_argument("--pal")
    a = p.parse_args()
    rom = ROM.read_bytes()
    n = int(a.args[0])
    if a.mode == "uses":
        lo, _, hi = a.args[1].partition("-")
        lo, hi = int(lo, 16), int(hi or lo, 16)
        for ar in range(2):
            for r in range(4):
                for li, (mw, mh, words) in enumerate(room_maps(rom, n, ar, r)):
                    cells = [(i % mw, i // mw, w & 0x3FF) for i, w in enumerate(words) if lo <= (w & 0x3FF) <= hi]
                    if cells:
                        print(f"set {n} area {ar} room {r} layer {li}: {len(cells)} cells, first {cells[:4]}")
        return
    pal = Path(a.pal).read_bytes() if a.pal else default_pal(n)
    tiles = tileset(rom, n)
    if a.mode == "crop":
        ar, r, layer, x0, y0, w, h, out = *map(int, a.args[1:8]), a.args[8]
        mw, mh, words = room_maps(rom, n, ar, r)[layer]
        im = Image.new("RGB", (w * 8, h * 8), (60, 0, 60))
        px = im.load()
        for y in range(h):
            print(" ".join(f"{words[(y0 + y) * mw + x0 + x] & 0x3FF:03x}{'hv'[0] if words[(y0 + y) * mw + x0 + x] >> 10 & 1 else '.'}{'v' if words[(y0 + y) * mw + x0 + x] >> 11 & 1 else '.'}" for x in range(w)))
            for x in range(w):
                word = words[(y0 + y) * mw + x0 + x]
                t = word & 0x3FF
                if t * 32 < len(tiles):
                    draw_tile(px, x * 8, y * 8, tiles[t * 32:t * 32 + 32], colours(pal, word >> 12), word >> 10 & 1, word >> 11 & 1)
        im.resize((w * 8 * a.zoom, h * 8 * a.zoom), Image.NEAREST).save(out)
        return
    if a.mode == "tiles":
        banks, out = {}, a.args[1]
        for ar in range(2):
            for r in range(4):
                for mw, mh, words in room_maps(rom, n, ar, r)[:3]:
                    for w in words:
                        banks.setdefault(w & 0x3FF, {}).setdefault(w >> 12, 0)
                        banks[w & 0x3FF][w >> 12] += 1
        count = len(tiles) // 32
        im = Image.new("RGB", (32 * 8, (count + 31) // 32 * 8), (60, 0, 60))
        px = im.load()
        for t in range(count):
            bank = max(banks[t], key=banks[t].get) if t in banks else 0
            draw_tile(px, t % 32 * 8, t // 32 * 8, tiles[t * 32:t * 32 + 32], colours(pal, bank))
        im.resize((im.width * a.zoom, im.height * a.zoom), Image.NEAREST).save(out)
    else:
        ar, r, layer, out = int(a.args[1]), int(a.args[2]), int(a.args[3]), a.args[4]
        mw, mh, words = room_maps(rom, n, ar, r)[layer]
        im = Image.new("RGB", (mw * 8, mh * 8), (60, 0, 60))
        px = im.load()
        base = (800 - len(tiles) // 32) if False else 0
        for i, w in enumerate(words):
            t = (w & 0x3FF) - base
            if 0 <= t < len(tiles) // 32:
                draw_tile(px, i % mw * 8, i // mw * 8, tiles[t * 32:t * 32 + 32], colours(pal, w >> 12), w >> 10 & 1, w >> 11 & 1)
        im.save(out)
    print(out)


if __name__ == "__main__":
    main()
