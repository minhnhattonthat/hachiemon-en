"""Which strings did a tour read? Uses the txt lines of tools/debug/textwatch.lua and the banks of tools/strscan.py.

python -X utf8 tools/debug/textcover.py ROM [OUT=work/qa/warp]...   per bank: strings read; every pointerless string, read or not
Writes the strings no scene read to the last OUT/text_unseen.tsv.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from strscan import BANKS, pointers, table, walk  # noqa: E402


def main():
    rom = Path(sys.argv[1]).read_bytes()
    outs = [Path(p) for p in sys.argv[2:]] or [Path("work/qa/warp")]
    read = {}
    for out in outs:
        for log in sorted(out.glob("*/log.txt")):
            for off in re.findall(r"^txt f\d+ ([0-9A-F]{6}) ", log.read_text(encoding="utf8", errors="replace"), re.M):
                read.setdefault(int(off, 16), set()).add(log.parent.name)
    tbl, ptr = table(), pointers(rom)
    unseen = []
    for lo, hi in BANKS:
        strs, _ = walk(rom, lo, hi, tbl)
        hit = sum(s in read for s, _, _ in strs)
        print(f"bank {lo:#x}-{hi:#x}: {hit}/{len(strs)} strings read")
        for s, e, _ in strs:
            text = "".join(tbl.get(b, "?") for b in rom[s:e - 2])
            if s not in read:
                unseen.append(f"{s:06X}\t{'ptr' if s in ptr else 'noptr'}\t{text}\n")
            if s not in ptr:
                scenes = sorted(read.get(s, ()))
                print(f"  noptr {s:06X} {'READ ' + ' '.join(scenes[:4]) if scenes else 'unread'}  {text[:24]}")
    (outs[-1] / "text_unseen.tsv").write_text("".join(unseen), encoding="utf8")
    print(f"{len(unseen)} strings unread: {outs[-1] / 'text_unseen.tsv'}")


if __name__ == "__main__":
    main()
