"""Recon check: walk the two text banks by the string grammar and tie every string to its ROM pointers.

    python -X utf8 tools/strscan.py ROM       # bank totals, pointer sources, unreferenced and mid-string pointers
Grammar: (text byte | FD | FE)* FF mode, mode in 0..2. See docs/re/text.md.
"""
import collections
import struct
import sys
from pathlib import Path

from tbl import Table

ROOT = Path(__file__).resolve().parents[1]
BANKS = [(0x1C0984, 0x1C127C), (0x1D9554, 0x1DCFC8)]


def table():
    t = {code[0]: val for code, val in Table.load(ROOT / "tbl/jp.tbl").dec.items()}
    t[0xFD] = "<P>"
    t[0xFE] = "<N>"
    return t


def walk(rom, lo, hi, tbl):
    """Yields (start, end_after_mode, mode). Skips forward a byte past anything that breaks the grammar, and says so."""
    i = lo
    bad = []
    out = []
    while i < hi:
        j = i
        while j < hi and rom[j] != 0xFF and rom[j] in tbl:
            j += 1
        if j < hi and rom[j] == 0xFF and rom[j + 1] in (0, 1, 2):
            out.append((i, j + 2, rom[j + 1]))
            i = j + 2
        else:
            bad.append(i)
            i = j + 1
    return out, bad


def pointers(rom):
    p = collections.defaultdict(list)
    for i in range(0, len(rom) - 3, 4):
        v = struct.unpack_from("<I", rom, i)[0]
        if 0x08000000 <= v < 0x08400000:
            p[v - 0x08000000].append(i)
    return p


if __name__ == "__main__":
    rom = Path(sys.argv[1]).read_bytes()
    tbl = table()
    ptr = pointers(rom)
    total = 0
    for lo, hi in BANKS:
        strs, bad = walk(rom, lo, hi, tbl)
        starts = {s for s, _, _ in strs}
        refs = [s for s in starts if s in ptr]
        inside = sorted(t for t in ptr if lo <= t < hi and t not in starts)
        src = collections.Counter()
        for s in refs:
            for w in ptr[s]:
                src["code 0-0x7FFFF" if w < 0x80000 else "table 0x1B0000-0x1F0000" if 0x1B0000 <= w < 0x1F0000 else f"other {w >> 16:#x}"] += 1
        chars = sum(e - s - 2 for s, e, _ in strs)
        total += len(strs)
        print(f"bank {lo:#x}-{hi:#x}: {len(strs)} strings, {chars} chars, {len(refs)} with pointers, "
              f"{len(strs) - len(refs)} without, grammar breaks {[hex(b) for b in bad][:12]}")
        print("  pointer sources:", dict(src))
        print("  pointers landing mid-string:", [f"{t:#x}<-{ptr[t][0]:#x}" for t in inside][:20], len(inside))
        print("  modes:", collections.Counter(m for _, _, m in strs))
        print("  longest line:", max(len(x) for s, e, _ in strs for x in rom[s:e - 2].replace(b"\xfd", b"\xfe").split(b"\xfe")))
    print("total strings", total)
    tail = rom[0x3A85D7:]
    print("end padding 00 only:", not any(tail), hex(len(tail)))
