"""Every block a tour unpacked to OBJ VRAM that gfxtext.py hasn't lettered, in 4bpp and 8bpp, to find art the 4bpp survey garbled.

    python -X utf8 tools/debug/objsweep.py OUTDIR TOUR_DIR [TOUR_DIR..] [--rom ROM]
Writes obj_NN.png pages; each block is labelled with its offset, tile count and first scene, 8bpp shown beside 4bpp. Colours are by index,
because a block's palette isn't stored with it: read the shapes. Sprites are sheets of 1D tiles, so lettering shows in sprite-sized runs.
"""
import argparse
import colorsys
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gfxtext import LABELS, MAPPED, unpack

COLS = 32
PAGE_H = 1000
RAMP = [(0, 0, 60)] + [tuple(int(c * 255) for c in colorsys.hsv_to_rgb(i * 0.618 % 1, 0.45 + (i % 3) * 0.2, 0.55 + (i % 5) * 0.1)) for i in range(1, 256)]


def blocks(tours):
    found = {}
    for tour in tours:
        for log in sorted(Path(tour).glob("*/log.txt")):
            text = log.read_text(encoding="utf8", errors="replace")
            for off, dest in re.findall(r"^lz f\d+ ([0-9A-F]+) -> (06[0-9A-F]{6})", text, re.M):
                if int(dest, 16) >= 0x06010000:
                    found.setdefault(int(off, 16), log.parent.name)
    return found


def tiles_image(data, size):
    """size 32: 4bpp cols 32; size 64: 8bpp cols 16. Both 256 px wide, so a sheet's rows line up."""
    cols = COLS if size == 32 else COLS // 2
    n = len(data) // size
    im = Image.new("RGB", (cols * 8, max(1, (n + cols - 1) // cols) * 8), (60, 0, 60))
    px = im.load()
    for t in range(n):
        x0, y0 = t % cols * 8, t // cols * 8
        for y in range(8):
            for x in range(8):
                if size == 32:
                    b = data[t * 32 + y * 4 + x // 2]
                    c = b >> (4 * (x & 1)) & 15
                else:
                    c = data[t * 64 + y * 8 + x]
                px[x0 + x, y0 + y] = RAMP[c]
    return im


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out")
    p.add_argument("tours", nargs="+")
    p.add_argument("--rom", default="rom/Hachiemon (Japan).gba")
    a = p.parse_args()
    rom = Path(a.rom).read_bytes()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    found = blocks(a.tours)
    done = set(LABELS) | set(MAPPED)
    rest = [(b, s) for b, s in sorted(found.items()) if b < 0x400000 and b not in done]
    page, y = 0, 0
    sheet = Image.new("RGB", (520, PAGE_H), (30, 0, 30))
    skipped = []
    for off, scene in rest:
        data = unpack(rom, off)[0]
        if len(data) < 32:
            skipped.append(off)
            continue
        a4, a8 = tiles_image(data, 32), tiles_image(data, 64)
        h = max(a4.height, a8.height) + 12
        if y + h > PAGE_H:
            sheet.save(out / f"obj_{page:02d}.png")
            page += 1
            y = 0
            sheet = Image.new("RGB", (520, max(PAGE_H, h)), (30, 0, 30))
        ImageDraw.Draw(sheet).text((1, y), f"{off:06X} {len(data) // 32:#x} {scene}", fill=(255, 255, 0))
        sheet.paste(a4, (0, y + 12))
        sheet.paste(a8, (262, y + 12))
        y += h
    sheet.save(out / f"obj_{page:02d}.png")
    print(len(rest), "blocks,", page + 1, "pages; too small:", " ".join(f"{o:06X}" for o in skipped))


if __name__ == "__main__":
    main()
