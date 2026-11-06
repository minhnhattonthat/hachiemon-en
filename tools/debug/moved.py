"""Stress ROM: every string and every graphics-row block moves to free space, recompressed by our encoders, and the old
bytes are wiped to FF, so a missed pointer slot reads FF rather than stale data.

    python -X utf8 tools/debug/moved.py                 # writes work/qa/moved.gba and work/qa/moved_blocks.txt
    python -X utf8 tools/debug/tour.py work/qa/moved.gba --out work/qa/tour_moved --jobs 7 --shots 900,1800
    python -X utf8 tools/debug/moved.py check work/qa/tour_moved    # exit 1 if a tour still unpacked a block at its old offset

Mesen keeps one save per ROM name: copy tools/mesen/Saves/<rom>.sav to moved.sav first, or the menus differ for that reason.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
from build import BANKS, ROM, Image, packed_spans, real_slots, repack_text, repoint, strings  # noqa: E402
from gbacomp import le_compress, le_decompress, lz_compress, lz_decompress  # noqa: E402
from gfxcover import rows  # noqa: E402
from tbl import Table  # noqa: E402

FREE = 0x3A8600
LIST = ROOT / "work/qa/moved_blocks.txt"


def make():
    orig = ROM.read_bytes()
    slots = real_slots(orig)
    ends = dict(packed_spans(orig))
    img = Image(orig)
    codec = Table.load(ROOT / "tbl/jp.tbl")
    repack_text(img, slots, codec, FREE)
    at = (FREE + sum(codec.decode(orig, s)[1] for s in strings(orig)) + 3) & ~3
    print(f"text ends {at:#x}")
    moved = []
    for _, _, spans in rows():
        for off in sorted(o for o in ends for lo, hi in spans if lo <= o <= hi):
            unpack, pack = (lz_decompress, lz_compress) if orig[off] == 0x10 else (le_decompress, le_compress)
            new = pack(unpack(orig, off)[0])
            new += b"\0" * (-len(new) % 4)
            img.write(at, new, f"gfx {off:#x}")
            repoint(img, slots, off, at, f"gfxptr {off:#x}")
            moved.append((off, at))
            at += len(new)
    print(f"{len(moved)} blocks moved, data ends {at:#x}")
    for off, _ in moved:
        img.out[off:ends[off]] = b"\xff" * (ends[off] - off)
    for lo, hi in BANKS:
        img.out[lo:hi] = b"\xff" * (hi - lo)
    (ROOT / "work/qa/moved.gba").write_bytes(img.out)
    LIST.write_text("".join(f"{o:06X} {a:06X}\n" for o, a in moved))


def check(out):
    pairs = dict(line.split() for line in LIST.read_text().splitlines())
    stale, fresh = set(), set()
    for log in Path(out).glob("*/log.txt"):
        for off in re.findall(r"^lz f\d+ ([0-9A-F]{6}) ->", log.read_text(encoding="utf8", errors="replace"), re.M):
            if off in pairs:
                stale.add(off)
            elif off in pairs.values():
                fresh.add(off)
    print(f"{len(fresh)} of {len(pairs)} moved blocks unpacked at the new address; old offsets read: {sorted(stale)}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(check(sys.argv[2]) if sys.argv[1:2] == ["check"] else make())
