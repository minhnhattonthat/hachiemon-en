"""A gallery of a stage tileset's rare objects: where lettered boards hide. Clusters map cells whose tile is rare across the set's rooms.

    python -X utf8 tools/debug/stageobjs.py SET OUT.png [--max-use 12] [--layers 0,1] [--zoom 2]
Each label is area.room.layer:x,y, the cluster's top left in cells, for `stagesheet.py crop`.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stagesheet import ROM, colours, default_pal, draw_tile, room_maps, tileset  # noqa: E402


def clusters(mw, mh, words, rare):
    """Connected cells (8-way, gap of 1) whose tile is in `rare`; each a bounding box."""
    live = {(i % mw, i // mw) for i, w in enumerate(words) if w & 0x3FF and w & 0x3FF in rare}
    out = []
    while live:
        stack = [live.pop()]
        cells = []
        while stack:
            x, y = stack.pop()
            cells.append((x, y))
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    c = (x + dx, y + dy)
                    if c in live:
                        live.remove(c)
                        stack.append(c)
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        out.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, len(cells)))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("set", type=int)
    p.add_argument("out")
    p.add_argument("--max-use", type=int, default=12)
    p.add_argument("--layers", default="0,1")
    p.add_argument("--zoom", type=int, default=2)
    a = p.parse_args()
    rom = ROM.read_bytes()
    tiles, pal = tileset(rom, a.set), default_pal(a.set)
    layers = [int(x) for x in a.layers.split(",")]
    rooms = {(ar, r): room_maps(rom, a.set, ar, r) for ar in range(2) for r in range(4)}
    use = {}
    for maps in rooms.values():
        for mw, mh, words in maps:
            for w in words:
                use[w & 0x3FF] = use.get(w & 0x3FF, 0) + 1
    rare = {t for t, n in use.items() if n <= a.max_use}
    seen, parts = set(), []
    for (ar, r), maps in rooms.items():
        for li in layers:
            if li >= len(maps):
                continue
            mw, mh, words = maps[li]
            for x0, y0, x1, y1, n in clusters(mw, mh, words, rare):
                if x1 - x0 < 3 or y1 - y0 < 2 or x1 - x0 > 40 or y1 - y0 > 24:
                    continue
                x0, y0, x1, y1 = max(0, x0 - 1), max(0, y0 - 1), min(mw, x1 + 1), min(mh, y1 + 1)
                key = frozenset(words[y * mw + x] & 0x3FF for y in range(y0, y1) for x in range(x0, x1))
                if key in seen or any(len(key & s) > len(key) * 0.8 for s in seen):
                    continue
                seen.add(key)
                im = Image.new("RGB", ((x1 - x0) * 8, (y1 - y0) * 8), (60, 0, 60))
                px = im.load()
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        w = words[y * mw + x]
                        t = w & 0x3FF
                        if t and t * 32 < len(tiles):
                            draw_tile(px, (x - x0) * 8, (y - y0) * 8, tiles[t * 32:t * 32 + 32], colours(pal, w >> 12), w >> 10 & 1, w >> 11 & 1)
                parts.append((f"{ar}.{r}.{li}:{x0},{y0}", im.resize((im.width * a.zoom, im.height * a.zoom), Image.NEAREST)))
    parts.sort(key=lambda p: -p[1].width * p[1].height)
    x = y = rowh = 0
    w_max = 1100
    sheet = Image.new("RGB", (w_max, 6000), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for label, im in parts:
        if x + im.width + 4 > w_max:
            x, y, rowh = 0, y + rowh + 12, 0
        if y + im.height + 12 > sheet.height:
            print("sheet full, dropped the rest")
            break
        d.text((x, y), label, fill=(0, 255, 255))
        sheet.paste(im, (x, y + 11))
        x += max(im.width, 70) + 4
        rowh = max(rowh, im.height + 2)
    sheet = sheet.crop((0, 0, w_max, y + rowh + 12))
    sheet.save(a.out)
    print(a.out, sheet.size, len(parts))


if __name__ == "__main__":
    main()
