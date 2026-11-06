"""ROM-side leftover-Japanese check for this game's pre-rendered text. Phase 9 runs it; a test runs it on every commit.

    python -X utf8 tools/jp_cells.py build/hachiemon_en.gba    # exit 1 if a pointer still reaches a kana or kanji cell

The skill's jp_left.py can't see Japanese here: every packed string starts with cell byte 00, so --slots reads nothing
(a NUL ends its reach), and later bytes are per-string cell numbers, not font codes. So walk the string the way the
game does and compare each cell it would draw with the game font's kana cells. script/keep_jp.txt lists allowed ids.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build import BASE, ERROR_SLOT, ROM, SCRIPT, text_slots  # noqa: E402
from lint import KEEP  # noqa: E402
from vmscript import u32  # noqa: E402
from vwf import CELL, END, GAME_FONT, NL, PAGE  # noqa: E402

KANA = [*range(0x00, 0xA0), 0xF9]  # docs/re/text.md: 00-4F hiragana, 50-9F katakana, F9 a bold あ


def kana_cells(orig):
    """The game font's kana cells, without blank ones: a blank cell looks the same in any font."""
    cells = {orig[GAME_FONT + b * CELL:GAME_FONT + (b + 1) * CELL] for b in KANA}
    return {c for c in cells if len(set(c)) > 1}


def drawn_kana(built, string, cells):
    """Text bytes of the string at `string` whose cell is a kana cell of the game font."""
    found, at = [], string
    while built[at] != END:
        b = built[at]
        if b not in (NL, PAGE) and bytes(built[string - (b + 1) * CELL:string - b * CELL]) in cells:
            found.append(b)
        at += 1
    return found


def leftover(orig, built, entries):
    """Ids (or slot offsets, for the ERROR string) of strings a pointer reaches that still draw kana."""
    ids = {int(e["offset"], 16): e["id"] for e in entries}
    keep = set()
    if KEEP.exists():
        keep = {ln.split()[0] for ln in KEEP.read_text(encoding="utf8").splitlines() if ln.strip() and not ln.startswith("#")}
    cells, bad = kana_cells(orig), []
    targets = {old: words[0] for old, words in text_slots(orig).items()}
    targets[None] = ERROR_SLOT
    for old, word in targets.items():
        id_ = ids.get(old, hex(word))
        if id_ not in keep and drawn_kana(built, u32(built, word) - BASE, cells):
            bad.append(id_)
    return bad


def main():
    entries = [e for path in SCRIPT for e in json.loads(path.read_text(encoding="utf8"))]
    bad = leftover(ROM.read_bytes(), Path(sys.argv[1]).read_bytes(), entries)
    print(f"jp_cells: {len(bad)} strings still draw kana {bad[:40]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
