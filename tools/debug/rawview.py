"""Render raw 4bpp data in the ROM as WxH-tile cells, grey by palette index, labelled by offset: for tiles no packed block holds.

    python -X utf8 tools/debug/rawview.py OUT.png LO HI W H PER_ROW [ZOOM=2]    # LO, HI in hex
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROM = Path(__file__).resolve().parents[2] / "rom/Hachiemon (Japan).gba"


def main():
    out, lo, hi, w, h, per_row, *zoom = sys.argv[1:]
    lo, hi, w, h, per_row = int(lo, 16), int(hi, 16), int(w), int(h), int(per_row)
    zoom = int(zoom[0]) if zoom else 2
    rom = ROM.read_bytes()
    size = w * h * 32
    cells = list(range(lo, hi, size))
    cw, ch = w * 8 * zoom + 4, h * 8 * zoom + 12
    sheet = Image.new("RGB", (cw * per_row, ch * ((len(cells) + per_row - 1) // per_row)), (60, 0, 60))
    d = ImageDraw.Draw(sheet)
    for n, off in enumerate(cells):
        im = Image.new("L", (w * 8, h * 8))
        px = im.load()
        for t in range(w * h):
            for y in range(8):
                for x in range(8):
                    px[t % w * 8 + x, t // w * 8 + y] = 255 - (rom[off + t * 32 + y * 4 + x // 2] >> (4 * (x & 1)) & 15) * 17
        x0, y0 = n % per_row * cw, n // per_row * ch
        d.text((x0 + 1, y0), f"{off:06x}", fill=(0, 255, 255))
        sheet.paste(im.resize((w * 8 * zoom, h * 8 * zoom), Image.NEAREST).convert("RGB"), (x0, y0 + 12))
    sheet.save(out)
    print(sheet.size, len(cells), "cells")


if __name__ == "__main__":
    main()
