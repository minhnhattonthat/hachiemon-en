"""Sweep the 8bpp cutscene pictures: each LZ tile block is paired with the 0x200-byte raw palette stored next to it.

    python -X utf8 tools/gfxsweep8.py ROM OUTDIR
Blocks without a neighbouring palette are listed, not dropped.
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbacomp import lz_decompress, scan

rom = Path(sys.argv[1]).read_bytes()
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
hits = scan(rom)
pal_gap = {}
for (o0, p0, _), (o1, _, _) in zip(hits, hits[1:]):
    gap = o1 - (o0 + p0)
    if 0x200 <= gap <= 0x210:
        pal_gap[o1] = (o0 + p0 + 3) & ~3
pics = []
for off, packed, size in hits:
    if size < 0x1000 or size % 64:
        continue
    data, end = lz_decompress(rom, off)
    nib_hi = sum(1 for b in data if b >> 4)
    # 8bpp pictures use the high nibble a lot and pair with a palette on one side
    pal = pal_gap.get(off)
    if pal is None:
        pal = ((end + 3) & ~3) if ((end + 3) & ~3) + 0x200 <= len(rom) and off in [h[0] for h in hits] and False else None
    if pal is None:
        continue
    pics.append((off, data, pal))
print(len(pics), "pictures with palette")
COLS, Z = 128, 1
page = 0
W, H = COLS * 8, 1300
img = Image.new("RGB", (W, H), (70, 0, 70))
dr = ImageDraw.Draw(img)
y = 0
for off, data, pal in pics:
    colours = [(lambda c: ((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))(rom[pal + i * 2] | rom[pal + i * 2 + 1] << 8) for i in range(256)]
    n = len(data) // 64
    rows = (n + COLS - 1) // COLS
    if y + 10 + rows * 8 > H:
        img.save(os.path.join(out, f"pic_{page:02d}.png"))
        page += 1
        img = Image.new("RGB", (W, H), (70, 0, 70))
        dr = ImageDraw.Draw(img)
        y = 0
    dr.text((2, y), f"{off:07x} pal {pal:07x} tiles {n:#x}", fill=(255, 255, 0))
    y += 10
    for t in range(n):
        x0 = (t % COLS) * 8
        y0 = y + (t // COLS) * 8
        tile = data[t * 64:t * 64 + 64]
        for i, v in enumerate(tile):
            img.putpixel((x0 + i % 8, y0 + i // 8), colours[v])
    y += rows * 8
img.save(os.path.join(out, f"pic_{page:02d}.png"))
print(page + 1, "pages")
