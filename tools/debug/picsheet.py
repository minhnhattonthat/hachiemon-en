"""Box-scene pictures as the player sees them: every tile block a tour unpacked to BG VRAM, flattened through the map unpacked right after it.

    python -X utf8 tools/debug/picsheet.py OUT.png TOUR_DIR [TOUR_DIR..] [--rom ROM] [--lo HEX --hi HEX] [--cols 4]
Reads `lz` lines of each scene's log.txt. Blocks with no map after them are printed, not dropped. The palette is the raw 0x200 or 0x20 words
stored after the map (**guess**, true where the picture comes out in real colours; a wrong one still shows lettering's shapes).
"""
import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gbacomp import lz_decompress


def pairs(tours):
    """(tiles, map) seen in logs, in first-seen order; and tile blocks that had no map."""
    found, lone = {}, set()
    for tour in tours:
        for log in sorted(Path(tour).glob("*/log.txt")):
            lines = re.findall(r"^lz f\d+ ([0-9A-F]+) -> ([0-9A-F]+)", log.read_text(encoding="utf8", errors="replace"), re.M)
            for (off, dest), (nxt, ndest) in zip(lines, [*lines[1:], ("0", "0")]):
                off, dest = int(off, 16), int(dest, 16)
                if 0x06000000 <= dest < 0x06010000:
                    if int(ndest, 16) == 0x02030000:
                        found.setdefault((off, int(nxt, 16)), log.parent.name)
                    else:
                        lone.add(off)
    return found, lone - {t for t, _ in found}


def colours(rom, at, n):
    out = []
    for i in range(n):
        c = int.from_bytes(rom[at + i * 2:at + i * 2 + 2], "little")
        out.append(((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8))
    return out


def render(rom, off, mp):
    tiles, _ = lz_decompress(rom, off)
    words, end = lz_decompress(rom, mp)
    cols, rows = (28, 12) if len(words) == 0x2A0 else (30, len(words) // 60) if len(words) % 60 == 0 else (32, len(words) // 64)  # 0x2A0: the box scenes' 224x96 window
    wide = max(words[i] | words[i + 1] << 8 & 0x300 for i in range(0, len(words), 2))
    depth8 = (wide + 1) * 64 <= len(tiles)
    pal = colours(rom, (end + 3) & ~3, 256)
    im = Image.new("RGB", (cols * 8, rows * 8))
    px = im.load()
    for cy in range(rows):
        for cx in range(cols):
            w = int.from_bytes(words[(cy * cols + cx) * 2:(cy * cols + cx) * 2 + 2], "little")
            n, h, v = w & 0x3FF, w >> 10 & 1, w >> 11 & 1
            bank = w >> 12
            for y in range(8):
                for x in range(8):
                    sx, sy = 7 - x if h else x, 7 - y if v else y
                    if depth8:
                        at = n * 64 + sy * 8 + sx
                        c = tiles[at] if at < len(tiles) else 0
                    else:
                        at = n * 32 + sy * 4 + sx // 2
                        c = (tiles[at] >> (4 * (sx & 1)) & 15 if at < len(tiles) else 0) + bank * 16
                    px[cx * 8 + x, cy * 8 + y] = pal[c]
    return im


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out")
    p.add_argument("tours", nargs="+")
    p.add_argument("--rom", default="rom/Hachiemon (Japan).gba")
    p.add_argument("--lo", default="0")
    p.add_argument("--hi", default="FFFFFFF")
    p.add_argument("--cols", type=int, default=4)
    a = p.parse_args()
    rom = Path(a.rom).read_bytes()
    found, lone = pairs(a.tours)
    lo, hi = int(a.lo, 16), int(a.hi, 16)
    items = [(t, m, s) for (t, m), s in sorted(found.items()) if lo <= t < hi]
    sheet = Image.new("RGB", (a.cols * 244, ((len(items) + a.cols - 1) // a.cols) * 176), (60, 0, 60))
    d = ImageDraw.Draw(sheet)
    for i, (t, m, scene) in enumerate(items):
        x0, y0 = i % a.cols * 244, i // a.cols * 176
        d.text((x0 + 1, y0), f"{t:06X}:{m:06X} {scene}", fill=(0, 255, 255))
        try:
            sheet.paste(render(rom, t, m).crop((0, 0, 240, 160)), (x0, y0 + 12))
        except Exception as e:  # a pair that isn't a tile block and a map gets a label saying so
            d.text((x0 + 1, y0 + 14), f"{type(e).__name__}: {e}", fill=(255, 80, 80))
    sheet.save(a.out)
    print(len(items), "pictures;", "no map:", " ".join(f"{t:06X}" for t in sorted(lone) if lo <= t < hi))


if __name__ == "__main__":
    main()
