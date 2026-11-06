"""Static sweep of the game's Le blocks (tools/gbacomp.py): bitmaps in colour, tile sheets in grey, each labelled.

    python -X utf8 tools/lesweep.py ROM OUTDIR
Le blocks with a 16-byte header (u32 width, u32 height, ...) hold BGR555 bitmaps. Palettes (0x200) are skipped and counted.
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbacomp import le_decompress, le_scan

PAGE_W, PAGE_H = 1200, 1600


def bitmap_size(u):
    """(w, h) when the block is a 16-byte header plus w*h 16-bit pixels, else None."""
    if len(u) < 16:
        return None
    w, h = int.from_bytes(u[:4], "little"), int.from_bytes(u[4:8], "little")
    return (w, h) if w and h and 16 + w * h * 2 == len(u) else None


def bitmap(u, w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            v = u[16 + (y * w + x) * 2] | u[17 + (y * w + x) * 2] << 8
            px[x, y] = ((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8)
    return img


def tiles(u, cols=32):
    count = len(u) // 32
    rows = (count + cols - 1) // cols
    img = Image.new("L", (cols * 8, rows * 8))
    px = img.load()
    for n in range(count):
        t = u[n * 32:n * 32 + 32]
        for i in range(64):
            px[(n % cols) * 8 + i % 8, (n // cols) * 8 + i // 8] = (t[i // 2] >> (4 * (i & 1)) & 15) * 17
    return img


def main():
    rom = Path(sys.argv[1]).read_bytes()
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    items, skipped = [], 0
    for off, _, size in le_scan(rom):
        if size == 0x200:
            skipped += 1
            continue
        u = le_decompress(rom, off)[0]
        wh = bitmap_size(u)
        items.append((off, size, bitmap(u, *wh) if wh else tiles(u), "bmp" if wh else "tiles"))
    page, x, y, rowh = 0, 0, 0, 0
    sheet = Image.new("RGB", (PAGE_W, PAGE_H), (70, 0, 70))
    draw = ImageDraw.Draw(sheet)
    index = open(out / "index.txt", "w", encoding="utf8")

    def flush():
        nonlocal page, sheet, draw, x, y, rowh
        sheet.save(out / f"le_{page:03d}.png")
        page += 1
        sheet = Image.new("RGB", (PAGE_W, PAGE_H), (70, 0, 70))
        draw = ImageDraw.Draw(sheet)
        x = y = rowh = 0

    for kind in ("bmp", "tiles"):
        for off, size, img, k in items:
            if k != kind:
                continue
            w, h = img.size
            if x + w > PAGE_W:
                x, y, rowh = 0, y + rowh + 12, 0
            if y + h + 12 > PAGE_H:
                flush()
            draw.text((x + 1, y), f"{off:06x}", fill=(255, 255, 0))
            sheet.paste(img.convert("RGB"), (x, y + 11))
            index.write(f"{off:06x} {kind} {size:#x} {w}x{h} page {page}\n")
            x += max(w, 42) + 4
            rowh = max(rowh, h)
    flush()
    index.close()
    print(f"{page} pages, {len(items)} blocks, {skipped} palettes skipped")


if __name__ == "__main__":
    main()
