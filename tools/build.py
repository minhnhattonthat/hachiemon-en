"""Build the ROM: write the text in script/ and its pointers back.

    python -X utf8 tools/build.py    # build/hachiemon_en.gba and build/writes.txt; exit 1 on a bad write

With no English in script/ every string stays where it was and the output is byte-identical to the dump
(tests/test_build.py). Once any entry has English the ROM grows to SIZE_EN, all text moves to TEXT_BASE as pre-rendered
cells (tools/vwf.py) and the two glyph loads get patched. Packed graphics stay as they are unless edited, because
lz_compress does not reproduce the original bytes (docs/re/rom-map.md).
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
from vwf import encode_en, encode_raw, load_font

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/Hachiemon (Japan).gba"
OUT = ROOT / "build/hachiemon_en.gba"
SCRIPT = [ROOT / "script/signs.json", ROOT / "script/main.json"]
STRAY = {0x1DBDF3: 0x1DBDF4}  # a lone byte before this string: its code pointer gives the true start (docs/re/text.md)
BASE = 0x08000000
TEXT_BASE = 0x400000  # past the original end: 4 MiB of certain space (docs/re/rom-map.md)
SIZE_EN = 0x800000  # EEPROM games stay at or under 16 MiB
# Each glyph load `lsls r0,#6; ldr r1,=font; adds r0,r0,r1` becomes `adds r0,#1; lsls r0,#6; subs r0,<text>,r0`:
# text byte b reads the cell at string - (b + 1) * 64 (tools/vwf.py). r1 is reloaded by the code after both.
GLYPH_LOADS = (
    (0x038626, bytes.fromhex("8001 0c49 4018"), bytes.fromhex("0130 8001 381a")),  # box, r7 = string
    (0x03A04A, bytes.fromhex("8001 1849 4018"), bytes.fromhex("0130 8001 281a")),  # bubble, r5 = string
)
ERROR_STRING, ERROR_SLOT = 0x1C2554, 0x038B18  # the bubble set-up shows this when a bubble is over its cell budget
ERROR_TEXT = "ERROR{end:00}"


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
        self.writes.append((off, bytes(self.orig[off:end]).ljust(len(data), b"\xff"), bytes(data), who))
        self.out[off:end] = data

    def grow(self, size):
        self.out += b"\xff" * (size - len(self.out))


def strings(rom):
    """Start offset of every string in both banks, in ROM order."""
    t = table()
    return [STRAY.get(s, s) for lo, hi in BANKS for s, _, _ in walk(rom, lo, hi, t)[0]]


def packed_spans(rom):
    return sorted((o, o + p) for o, p, _ in scan(rom) + le_scan(rom))


def load_script():
    return [e for path in SCRIPT for e in json.loads(path.read_text(encoding="utf8"))]


def jp_script():
    """The script as if nothing were translated, for the identity build and the debug builds."""
    return [dict(e, en="") for e in load_script()]


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


def pack_text(img, slots, codec, entries, base=TEXT_BASE):
    """Every string as cells plus bytes (tools/vwf.py), back to back from base. Returns {id: (first byte, string)}, and every
    string needs it once the glyph loads are patched: an untranslated line carries its Japanese glyphs the same way."""
    font, orig, at, where = load_font(), img.orig, base, {}

    def put(cells, data, who):
        nonlocal at
        block = cells + data
        block += b"\0" * (-len(block) % 4)
        img.write(at, block, who)
        string = at + len(cells)
        at += len(block)
        return string

    for e in entries:
        s = int(e["offset"], 16)
        try:
            cells, data = encode_en(e["en"], font, orig) if e["en"] else encode_raw(codec.encode(e["jp"]), orig)
        except ValueError as err:
            raise ValueError(f"{e['id']}: {err}") from err
        new = put(cells, data, f"text {s:#x}")
        repoint(img, slots, s, new, f"textptr {s:#x}")
        where[e["id"]] = (new - len(cells), new)
    cells, data = encode_en(ERROR_TEXT, font, orig)
    new = put(cells, data, "text error")
    img.write(ERROR_SLOT, (BASE + new).to_bytes(4, "little"), "textptr error")
    return where


def build(orig, entries=None):
    entries = load_script() if entries is None else entries
    img = Image(orig)
    codec = Table.load(ROOT / "tbl/jp.tbl")
    img.where = {}
    if not any(e["en"] for e in entries):
        repack_text(img, text_slots(orig), codec, entries)
        return img
    img.grow(SIZE_EN)
    for off, was, now in GLYPH_LOADS:
        if orig[off:off + len(was)] != was:
            raise ValueError(f"glyph load at {off:#x} holds {orig[off:off + len(was)].hex()}")
        img.write(off, now, f"glyph load {off:#x}")
    img.where = pack_text(img, text_slots(orig), codec, entries)
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
