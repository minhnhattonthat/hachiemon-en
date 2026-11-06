"""Show many packed blocks at once in real colours, each drawn as a WxH-tile picture, labelled by ROM offset.

    python -X utf8 tools/gfxview_blocks.py OUT.png WxH[*N] PER_ROW ZOOM PAL.bin PALNUM OFFSET|LO-HI ...
WxH in tiles; *N lays them out as N sprites side by side; +T (hex) starts at tile T. PALNUM is a BG palette number in hex, or oN for OBJ palette N.
LO-HI takes every packed block in that span.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import packed_spans
from gfxview import ROM, unpack


def main():
    out, size, per_row, zoom, pal, num, *offs = sys.argv[1:]
    size, _, first = size.partition("+")  # WxH+T: start at tile T, hex
    first = int(first or "0", 16)
    size, _, n_spr = size.partition("*")  # WxH*N: N sprites of WxH tiles side by side (1D mapping)
    sw, h = map(int, size.split("x"))
    w = sw * int(n_spr or 1)
    per_row, zoom = int(per_row), int(zoom)
    rom = ROM.read_bytes()
    colors = []
    if num == "g":  # no palette at hand: index 0 blue, then a grey ramp
        colors = [(0, 0, 120)] + [(i * 17,) * 3 for i in range(1, 16)]
    else:
        pal = Path(pal).read_bytes()
        base = 0x200 + int(num[1:], 16) * 32 if num[0] == "o" else int(num, 16) * 32
        for i in range(16):
            c = int.from_bytes(pal[base + i * 2:base + i * 2 + 2], "little")
            colors.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
    starts = [a for a, _ in packed_spans(rom)]
    blocks = []
    for a in offs:
        lo, _, hi = a.partition("-")
        blocks += [o for o in starts if int(lo, 16) <= o <= int(hi, 16)] if hi else [int(lo, 16)]
    cw, ch = w * 8 * zoom + 4, h * 8 * zoom + 12
    sheet = Image.new("RGB", (cw * per_row, ch * ((len(blocks) + per_row - 1) // per_row)), (60, 0, 60))
    d = ImageDraw.Draw(sheet)
    for n, off in enumerate(blocks):
        data = unpack(rom, off)
        im = Image.new("RGB", (w * 8, h * 8), (90, 0, 90))
        px = im.load()
        for t in range(min(w * h, len(data) // 32 - first)):
            for y in range(8):
                for x in range(8):
                    spr_n, in_spr = t // (sw * h), t % (sw * h)
                    at = (t + first) * 32 + y * 4 + x // 2
                    px[(spr_n * sw + in_spr % sw) * 8 + x, in_spr // sw * 8 + y] = colors[data[at] >> (4 * (x & 1)) & 15]
        x0, y0 = n % per_row * cw, n // per_row * ch
        d.text((x0 + 1, y0), f"{off:06x}", fill=(0, 255, 255))
        sheet.paste(im.resize((w * 8 * zoom, h * 8 * zoom), Image.NEAREST), (x0, y0 + 12))
    sheet.save(out)
    print(sheet.size, len(blocks), "blocks")


if __name__ == "__main__":
    main()
