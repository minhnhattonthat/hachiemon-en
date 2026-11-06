"""Show tile blocks through their maps, in real colours: for screens and banners stored as a tile sheet plus a map.

    python -X utf8 tools/gfxview_maps.py OUT.png PER_ROW ZOOM PAL.bin PALNUM TILES:MAP ...     (hex; PALNUM a BG palette, or oN)
With an oN or BG PALNUM of `w`, a Le map's own palette nibble picks the colours.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gfxtext import MapPicture, unpack
from gfxview import ROM


def colors(pal, base):
    out = []
    for i in range(16):
        c = int.from_bytes(pal[base + i * 2:base + i * 2 + 2], "little")
        out.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
    return out


def render(pic, pal, num):
    im = Image.new("RGB", (pic.w, pic.h))
    px = im.load()
    for y in range(pic.h):
        for x in range(pic.w):
            word = pic.words[y // 8 * pic.cols + x // 8]
            base = (word >> 12) * 32 if num == "w" else 0x200 + int(num[1:], 16) * 32 if num[0] == "o" else int(num, 16) * 32
            px[x, y] = colors(pal, base)[pic.get(x, y)]
    return im


def main():
    out, per_row, zoom, pal, num, *pairs = sys.argv[1:]
    per_row, zoom = int(per_row), int(zoom)
    rom = ROM.read_bytes()
    pal = Path(pal).read_bytes()
    parts = []
    for pair in pairs:
        t, m = (int(x, 16) for x in pair.split(":"))
        pic = MapPicture(unpack(rom, t)[0], unpack(rom, m)[0])
        parts.append((f"{t:06x}", render(pic, pal, num).resize((pic.w * zoom, pic.h * zoom), Image.NEAREST)))
    cw, ch = max(p.width for _, p in parts) + 4, max(p.height for _, p in parts) + 12
    sheet = Image.new("RGB", (cw * per_row, ch * ((len(parts) + per_row - 1) // per_row)), (60, 0, 60))
    d = ImageDraw.Draw(sheet)
    for n, (label, p) in enumerate(parts):
        x0, y0 = n % per_row * cw, n // per_row * ch
        d.text((x0 + 1, y0), label, fill=(0, 255, 255))
        sheet.paste(p, (x0, y0 + 12))
    sheet.save(out)
    print(sheet.size, len(parts))


if __name__ == "__main__":
    main()
