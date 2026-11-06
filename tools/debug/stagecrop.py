"""Zoom rectangles of stage tilesets onto one sheet, each labelled, to read and place lettered boards.

    python -X utf8 tools/debug/stagecrop.py OUT.png ZOOM SET:COL,ROW,W,H ...     (tile units, decimal; ROM by --rom, default the original)
Each tile takes its commonest palette in the set's rooms (stagesheet.py).
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stagesheet import colours, default_pal, draw_tile, room_maps, tileset  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out")
    p.add_argument("zoom", type=int)
    p.add_argument("crops", nargs="+")
    p.add_argument("--rom", default="rom/Hachiemon (Japan).gba")
    p.add_argument("--per-row", type=int, default=3)
    a = p.parse_args()
    rom = Path(a.rom).read_bytes()
    orig = Path("rom/Hachiemon (Japan).gba").read_bytes()
    parts = []
    for c in a.crops:
        n, _, rect = c.partition(":")
        n = int(n)
        col, row, w, h = map(int, rect.split(","))
        tiles = tileset(rom, n)
        pal = default_pal(n)
        banks = {}
        for ar in range(2):
            for r in range(4):
                for mw, mh, words in room_maps(orig, n, ar, r):
                    for word in words:
                        d = banks.setdefault(word & 0x3FF, {})
                        d[word >> 12] = d.get(word >> 12, 0) + 1
        im = Image.new("RGB", (w * 8, h * 8), (60, 0, 60))
        px = im.load()
        for y in range(h):
            for x in range(w):
                t = (row + y) * 32 + col + x
                if t * 32 < len(tiles):
                    bank = max(banks[t], key=banks[t].get) if t in banks else 0
                    draw_tile(px, x * 8, y * 8, tiles[t * 32:t * 32 + 32], colours(pal, bank))
        parts.append((c, im.resize((im.width * a.zoom, im.height * a.zoom), Image.NEAREST)))
    cw, ch = max(p.width for _, p in parts) + 4, max(p.height for _, p in parts) + 12
    rows = (len(parts) + a.per_row - 1) // a.per_row
    sheet = Image.new("RGB", (cw * a.per_row, ch * rows), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(parts):
        x0, y0 = i % a.per_row * cw, i // a.per_row * ch
        d.text((x0 + 1, y0), label, fill=(0, 255, 255))
        sheet.paste(im, (x0, y0 + 12))
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
