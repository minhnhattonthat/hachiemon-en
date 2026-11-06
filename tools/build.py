"""Build the ROM: write the text in script/ and its pointers back.

    python -X utf8 tools/build.py    # build/hachiemon_en.gba and build/writes.txt; exit 1 on a bad write

With no English in script/ every string stays where it was and the output is byte-identical to the dump
(tests/test_build.py). Once any entry has English, all text moves to TEXT_BASE. Packed graphics stay as they are unless
edited, because lz_compress does not reproduce the original bytes (docs/re/rom-map.md).
"""
import bisect
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_rom import check
from gbacomp import le_scan, scan
from romdiff import check as romdiff_check
from strscan import BANKS, pointers, table, walk
from tbl import Table
from vmscript import code_words, script_words, sign_words, u32

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/Hachiemon (Japan).gba"
OUT = ROOT / "build/hachiemon_en.gba"
SCRIPT = [ROOT / "script/signs.json", ROOT / "script/main.json"]
STRAY = {0x1DBDF3: 0x1DBDF4}  # a lone byte before this string: its code pointer gives the true start (docs/re/text.md)
BASE = 0x08000000
TEXT_BASE = 0x3A8600  # candidate free space, not trap-tested yet (docs/re/rom-map.md)


class Image:
    """The output ROM plus a romdiff write log."""

    def __init__(self, orig):
        self.orig = orig
        self.out = bytearray(orig)
        self.writes = []

    def write(self, off, data, who):
        end = off + len(data)
        if end > len(self.out):
            raise ValueError(f"{who}: write past the end of the ROM at {off:#x}")
        self.writes.append((off, bytes(self.orig[off:end]), bytes(data), who))
        self.out[off:end] = data


def strings(rom):
    """Start offset of every string in both banks, in ROM order."""
    t = table()
    return [STRAY.get(s, s) for lo, hi in BANKS for s, _, _ in walk(rom, lo, hi, t)[0]]


def packed_spans(rom):
    return sorted((o, o + p) for o, p, _ in scan(rom) + le_scan(rom))


def load_script():
    return [e for path in SCRIPT for e in json.loads(path.read_text(encoding="utf8"))]


def text_slots(rom):
    """string start -> pointer words, from the structures that own them: scripts, the sign table, code literals."""
    slots = {}
    for w in [*script_words(rom), *sign_words(), *code_words(rom)]:
        slots.setdefault(u32(rom, w) - BASE, []).append(w)
    return slots


def real_slots(rom):
    """target -> pointer words by value, for graphics blocks, without words inside packed blocks or the text banks: those are chance matches."""
    spans = packed_spans(rom) + [(lo, hi) for lo, hi in BANKS]
    spans.sort()
    starts = [a for a, _ in spans]

    def is_data(w):
        i = bisect.bisect_right(starts, w) - 1
        return i >= 0 and w < spans[i][1]

    return {t: [w for w in words if not is_data(w)] for t, words in pointers(rom).items()}


def repoint(img, slots, old, new, who):
    for w in slots.get(old, []):
        img.write(w, (BASE + new).to_bytes(4, "little"), who)


def repack_text(img, slots, codec, entries, base=None):
    """Encode every entry, English if it has any. base=None keeps each where it is; otherwise they run back to back from base."""
    at = base
    for e in entries:
        s = int(e["offset"], 16)
        data = codec.encode(e["en"] or e["jp"])
        new = s if base is None else at
        img.write(new, data, f"text {s:#x}")
        repoint(img, slots, s, new, f"textptr {s:#x}")
        if base is not None:
            at += len(data)


def build(orig, entries=None):
    entries = load_script() if entries is None else entries
    img = Image(orig)
    base = TEXT_BASE if any(e["en"] for e in entries) else None
    repack_text(img, text_slots(orig), Table.load(ROOT / "tbl/jp.tbl"), entries, base)
    return img


def main():
    check()
    orig = ROM.read_bytes()
    img = build(orig)
    errs, _ = romdiff_check(orig, bytes(img.out), set(), img.writes)
    if errs:
        sys.exit("\n".join(errs))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(img.out)
    with open(OUT.with_name("writes.txt"), "w", encoding="utf8", newline="\n") as f:
        for off, was, now, who in img.writes:
            f.write(f"{off:x} {was.hex()} {now.hex()} {who}\n")
    state = "identical to the dump" if img.out == orig else "differs from the dump"
    print(f"{OUT}: {len(img.out)} bytes, {len(img.writes)} writes, sha1 {hashlib.sha1(img.out).hexdigest()}, {state}")


if __name__ == "__main__":
    main()
