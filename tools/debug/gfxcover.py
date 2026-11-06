"""Which warp scenes unpack which docs/re/graphics.md rows? Reads the lz lines of a tour's logs (tools/debug/lzlog.lua).

python -X utf8 tools/debug/gfxcover.py [OUT=work/qa/warp]    prints one line per row: blocks seen, scenes; exit 1 if a row has none
"""
import re
import sys
from pathlib import Path


def rows():
    """(row number, label, [(lo, hi)...]) per table row; a single offset is a one-address range."""
    out = []
    for line in Path("docs/re/graphics.md").read_text(encoding="utf8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|", line)
        if not m:
            continue
        spans = []
        src = re.sub(r"palette 0x[0-9A-Fa-f]+", "", m.group(3))  # a palette is copied, not unpacked
        for lo, hi in re.findall(r"0x([0-9A-Fa-f]{6})(?:-0x([0-9A-Fa-f]{6}))?", src):
            spans.append((int(lo, 16), int(hi or lo, 16)))
        out.append((int(m.group(1)), m.group(2).strip(), spans))
    return out


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "work/qa/warp")
    seen = {}
    for log in sorted(out.glob("*/log.txt")):
        for off in re.findall(r"^lz f\d+ ([0-9A-F]{6}) ->", log.read_text(encoding="utf8", errors="replace"), re.M):
            seen.setdefault(int(off, 16), set()).add(log.parent.name)
    missing = 0
    for num, label, spans in rows():
        hit, scenes = 0, set()
        for off, names in seen.items():
            if any(lo <= off <= hi for lo, hi in spans):
                hit += 1
                scenes |= names
        total = sum(1 for lo, hi in spans if lo == hi) or "range"
        if not scenes:
            missing += 1
        print(f"row {num:2d} {label[:34]:34s} blocks {hit}/{total}  scenes {len(scenes)}: {' '.join(sorted(scenes)[:6])}")
    print(f"{missing} rows with no scene")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
