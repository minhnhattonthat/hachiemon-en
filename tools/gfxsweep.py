"""Static graphics-text sweep: render every LZ77 block and raw gap of the ROM's graphics area into labelled sheets.

    python -X utf8 tools/gfxsweep.py ROM OUTDIR [--fmt gba4|gba8] [--lo HEX --hi HEX] [--raw]
Prints every skipped block with its reason. Index and page per block goes to OUTDIR/index.txt.
"""
import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbacomp import lz_decompress, scan

COLS, ROWS, Z = 64, 84, 2
LABEL = 10


def is_tilemap(b):
    """16-bit map words carry tile numbers below 0x400 plus small palette nibbles: high bytes cluster, pixels don't."""
    if len(b) < 64 or len(b) % 2:
        return False
    hi = b[1::2]
    return sum(1 for x in hi if x & 0x0F < 4) > len(hi) * 0.95 and len(set(hi)) < 40


def decode_row(t, fmt):
    if fmt == "gba8":
        return list(t[:64])
    return [t[i // 2] >> (4 * (i & 1)) & 15 for i in range(64)]


ap = argparse.ArgumentParser()
ap.add_argument("rom")
ap.add_argument("out")
ap.add_argument("--fmt", default="gba4")
ap.add_argument("--lo", default="0")
ap.add_argument("--hi", default="3A8600")
ap.add_argument("--raw", action="store_true", help="also render raw gaps between LZ blocks")
a = ap.parse_args()
rom = Path(a.rom).read_bytes()
lo, hi = int(a.lo, 16), int(a.hi, 16)
os.makedirs(a.out, exist_ok=True)
size = 32 if a.fmt == "gba4" else 64
blocks = []
hits = [h for h in scan(rom) if lo <= h[0] < hi]
pos = lo
for off, packed, unpacked in hits:
    if a.raw and off - pos >= 0x200:
        blocks.append((pos, "raw", rom[pos:off]))
    data, _ = lz_decompress(rom, off)
    if is_tilemap(data):
        print(f"skip {off:07x} {unpacked:#x}: tilemap")
    elif unpacked < size * 2:
        print(f"skip {off:07x} {unpacked:#x}: too small")
    else:
        blocks.append((off, "lz", data))
    pos = off + packed
if a.raw and hi - pos >= 0x200:
    blocks.append((pos, "raw", rom[pos:hi]))

W = COLS * 8 * Z
H = ROWS * 8 * Z
page = 0
img = Image.new("RGB", (W, H), (70, 0, 70))
dr = ImageDraw.Draw(img)
y = 0
index = open(os.path.join(a.out, "index.txt"), "w", encoding="utf-8")


def flush():
    global page, img, dr, y
    img.save(os.path.join(a.out, f"sweep_{a.fmt}_{page:03d}.png"))
    page += 1
    img = Image.new("RGB", (W, H), (70, 0, 70))
    dr = ImageDraw.Draw(img)
    y = 0


for off, kind, data in blocks:
    count = len(data) // size
    if not count:
        print(f"skip {off:07x}: under a tile")
        continue
    t = 0
    while t < count:
        rows = (count - t + COLS - 1) // COLS
        fit = (H - y - LABEL) // (8 * Z)
        if fit < 1:
            flush()
            continue
        rows = min(rows, fit)
        dr.text((2, y), f"{kind} {off:07x} tile {t:#x}/{count:#x}", fill=(255, 255, 0))
        index.write(f"{off:07x} {kind} {len(data):#x} tile {t:#x} page {page}\n")
        y += LABEL
        for r in range(rows):
            for c in range(COLS):
                n = t + r * COLS + c
                if n >= count:
                    break
                px = decode_row(data[n * size:n * size + size], a.fmt)
                for i, v in enumerate(px):
                    if v:
                        g = v * 17 if a.fmt == "gba4" else v
                        x0 = c * 8 * Z + (i % 8) * Z
                        y0 = y + (i // 8) * Z
                        dr.rectangle((x0, y0, x0 + Z - 1, y0 + Z - 1), fill=(g, g, g))
            y += 8 * Z
        t += rows * COLS
flush()
index.close()
print(f"{page} pages, {len(blocks)} blocks")
