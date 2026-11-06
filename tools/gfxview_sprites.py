"""Show runs of a packed block assembled the way sprites draw them, in real colours from a ppudump palette.

    python -X utf8 tools/gfxview_sprites.py OUT.png ZOOM BLOCK PAL.bin SPEC ...
    SPEC = START:COUNT:WxH:N[:PAL]   COUNT labels from tile START, each N sprites of WxH px side by side, palette PAL
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gfxview import ROM, unpack


def main():
    out, zoom, block, pal, *specs = sys.argv[1:]
    data = unpack(ROM.read_bytes(), int(block, 16))
    pal = open(pal, "rb").read()
    zoom, y, parts = int(zoom), 0, []
    for spec in specs:
        f = spec.split(":")
        start, count, (sw, sh), n, p = int(f[0], 16), int(f[1]), map(int, f[2].split("x")), int(f[3]), int(f[4], 16) if len(f) > 4 else 3
        rgb = [(lambda c: (c & 31) * 8, lambda c: (c >> 5 & 31) * 8, lambda c: (c >> 10 & 31) * 8)]
        colors = []
        for i in range(16):
            c = int.from_bytes(pal[0x200 + (p * 16 + i) * 2:0x200 + (p * 16 + i) * 2 + 2], "little")
            colors.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
        tile = start
        for _ in range(count):
            im = Image.new("RGB", (sw * n, sh))
            px, t = im.load(), tile
            for s in range(n):
                for ty in range(sh // 8):
                    for tx in range(sw // 8):
                        for iy in range(8):
                            for ix in range(8):
                                at = t * 32 + iy * 4 + ix // 2
                                v = data[at] >> (4 * (ix & 1)) & 15 if at < len(data) else 0
                                px[s * sw + tx * 8 + ix, ty * 8 + iy] = colors[v] if v else (255, 0, 255)
                        t += 1
            parts.append((f"{tile:03x}", im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)))
            tile = t
    cols = max(1, 720 // (parts[0][1].width + 30))
    rows = (len(parts) + cols - 1) // cols
    cw = max(p.width for _, p in parts) + 30
    ch = max(p.height for _, p in parts) + 2
    s = Image.new("RGB", (cw * cols, ch * rows), (0, 0, 0))
    d = ImageDraw.Draw(s)
    for i, (label, p) in enumerate(parts):
        x, y = i % cols * cw, i // cols * ch
        d.text((x, y), label, fill=(255, 255, 0))
        s.paste(p, (x + 28, y))
    s.save(out)
    print(s.size)


if __name__ == "__main__":
    main()
