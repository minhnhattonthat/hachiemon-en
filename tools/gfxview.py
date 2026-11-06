"""Show packed graphics blocks by palette index, with a tile ruler, to place English on them.

    python -X utf8 tools/gfxview.py OUT.png COLS ZOOM OFFSET[@HEXPAL] ...    # OFFSET: an LZ77 or Le block, in hex
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gbacomp import le_decompress, lz_decompress

ROM = Path(__file__).resolve().parents[1] / "rom/Hachiemon (Japan).gba"
INDEX = [(0, 0, 80), (235, 235, 235), (120, 120, 120), (40, 40, 40), (255, 80, 80), (80, 200, 80), (80, 120, 255), (255, 220, 60),
         (255, 150, 200), (60, 220, 220), (190, 100, 240), (160, 110, 60), (255, 160, 60), (160, 200, 255), (200, 255, 160), (255, 255, 255)]


def unpack(rom, off):
    return (lz_decompress if rom[off] == 0x10 else le_decompress)(rom, off)[0]


def sheet(data, cols, zoom):
    """A 4bpp tile sheet with a ruler: tile number every 8 tiles across and at each row start."""
    count = len(data) // 32
    rows = (count + cols - 1) // cols
    im = Image.new("RGB", (cols * 8, rows * 8), (70, 0, 70))
    px = im.load()
    for t in range(count):
        for y in range(8):
            for x in range(8):
                px[t % cols * 8 + x, t // cols * 8 + y] = INDEX[data[t * 32 + y * 4 + x // 2] >> (4 * (x & 1)) & 15]
    im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    out = Image.new("RGB", (im.width + 30, im.height + 12), (0, 0, 0))
    out.paste(im, (30, 12))
    d = ImageDraw.Draw(out)
    for c in range(0, cols, 4):
        d.text((30 + c * 8 * zoom, 0), f"{c:x}", fill=(255, 255, 0))
    for r in range(rows):
        d.text((0, 12 + r * 8 * zoom), f"{r * cols:03x}", fill=(255, 255, 0))
    return out


def main():
    out, cols, zoom, *offs = sys.argv[1:]
    rom = ROM.read_bytes()
    parts = []
    for a in offs:
        off = int(a, 16)
        data = unpack(rom, off)
        parts.append((f"{off:06x} {len(data):#x} bytes, {len(data) // 32:#x} tiles", sheet(data, int(cols), int(zoom))))
    h = sum(p.height + 12 for _, p in parts)
    s = Image.new("RGB", (max(p.width for _, p in parts), h), (40, 0, 40))
    d = ImageDraw.Draw(s)
    y = 0
    for label, p in parts:
        d.text((1, y), label, fill=(0, 255, 255))
        s.paste(p, (0, y + 12))
        y += p.height + 12
    s.save(out)
    print(s.size)


if __name__ == "__main__":
    main()
