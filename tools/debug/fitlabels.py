"""Draw every graphics label and list all that don't fit, instead of failing on the first in a build."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gfxtext import LABELS, MAPPED, RAW, Picture, letter, relabel, remap  # noqa: E402
from gfxview import ROM  # noqa: E402


def main():
    rom = ROM.read_bytes()
    bad = 0
    for off in LABELS:
        try:
            relabel(rom, off)
        except ValueError as e:
            print(f"{off:#x} {e}")
            bad += 1
    for off in MAPPED:
        try:
            tiles, _, _ = remap(rom, off)
        except ValueError as e:
            print(f"{off:#x} {e}")
            bad += 1
    for off, (grid, text, kw) in RAW.items():
        try:
            letter(Picture(bytearray(rom[off:off + len(grid) * len(grid[0]) * 32]), grid), text, **kw)
        except ValueError as e:
            print(f"{off:#x} {e}")
            bad += 1
    print(bad, "don't fit;", len(LABELS), "labelled,", len(MAPPED), "mapped,", len(RAW), "raw")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
