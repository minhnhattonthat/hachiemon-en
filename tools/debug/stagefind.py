"""Find where stage tiles are used and show them in place, for reading a lettered board and getting its tile grid.

    python -X utf8 tools/debug/stagefind.py OUT.png SET:TILE[:WxH] ...     (TILE hex; window W x H cells around its first use, default 10x6)
Prints each window's location and tile numbers (`.` no flip, h/v flips).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stagesheet import ROM, colours, default_pal, draw_tile, room_maps, tileset  # noqa: E402


def first_use(rom, n, tile):
    for ar in range(2):
        for r in range(4):
            for li, (mw, mh, words) in enumerate(room_maps(rom, n, ar, r)):
                for i, w in enumerate(words):
                    if w & 0x3FF == tile:
                        return ar, r, li, i % mw, i // mw, mw, mh, words
    return None


def main():
    out, *asks = sys.argv[1:]
    rom = ROM.read_bytes()
    parts = []
    for ask in asks:
        n, t, *size = ask.split(":")
        n, t = int(n), int(t, 16)
        w, h = map(int, size[0].split("x")) if size else (10, 6)
        hit = first_use(rom, n, t)
        if not hit:
            print(ask, "not used")
            continue
        ar, r, li, x, y, mw, mh, words = hit
        x0, y0 = max(0, x - w // 2), max(0, y - h // 2)
        tiles, pal = tileset(rom, n), default_pal(n)
        im = Image.new("RGB", (w * 8, h * 8), (60, 0, 60))
        px = im.load()
        print(f"{ask} at area {ar} room {r} layer {li} x {x} y {y}, window from {x0},{y0}")
        for yy in range(h):
            row = []
            for xx in range(w):
                i = min(y0 + yy, mh - 1) * mw + min(x0 + xx, mw - 1)
                word = words[i]
                n_t = word & 0x3FF
                row.append(f"{n_t:03x}{'h' if word >> 10 & 1 else '.'}{'v' if word >> 11 & 1 else '.'}")
                if n_t and n_t * 32 < len(tiles):
                    draw_tile(px, xx * 8, yy * 8, tiles[n_t * 32:n_t * 32 + 32], colours(pal, word >> 12), word >> 10 & 1, word >> 11 & 1)
            print("  " + " ".join(row))
        parts.append((ask, im.resize((w * 24, h * 24), Image.NEAREST)))
    per = 4
    cw, ch = max(p.width for _, p in parts) + 4, max(p.height for _, p in parts) + 12
    sheet = Image.new("RGB", (cw * per, ch * ((len(parts) + per - 1) // per)), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(parts):
        x, y = i % per * cw, i // per * ch
        d.text((x, y), label, fill=(0, 255, 255))
        sheet.paste(im, (x, y + 12))
    sheet.save(out)


if __name__ == "__main__":
    main()
