"""Labelled sheet of the 8x16 font (one byte code = cell index): reading it builds tbl/jp.tbl.

    python -X utf8 tools/fontsheet.py ROM OUT.png [--base 2FFC50] [--count 256] [--zoom 3]
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("rom")
ap.add_argument("out")
ap.add_argument("--base", default="2FFC50")
ap.add_argument("--count", type=int, default=256)
ap.add_argument("--zoom", type=int, default=3)
a = ap.parse_args()
d = Path(a.rom).read_bytes()
base = int(a.base, 16)
COLS = 16
Z = a.zoom
cw, ch = 8 * Z + 20, 16 * Z + 14
img = Image.new("RGB", (COLS * cw, (a.count // COLS + 1) * ch), (40, 40, 60))
dr = ImageDraw.Draw(img)
for i in range(a.count):
    g = d[base + i * 64:base + i * 64 + 64]
    x0 = (i % COLS) * cw
    y0 = (i // COLS) * ch
    dr.text((x0 + 2, y0), f"{i:02X}", fill=(255, 255, 0))
    for t in range(2):
        for p in range(64):
            b = g[t * 32 + p // 2] >> (4 * (p & 1)) & 15
            if b:
                x = p % 8
                y = p // 8 + t * 8
                v = 255 - (b - 1) * 8
                dr.rectangle((x0 + x * Z, y0 + 12 + y * Z, x0 + x * Z + Z - 1, y0 + 12 + y * Z + Z - 1), fill=(v, v, v))
img.save(a.out)
