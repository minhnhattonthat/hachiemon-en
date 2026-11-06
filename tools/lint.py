"""Text lint: every English line against the measured limits, the control codes and the glossary. Part of tools/check.py.

    python -X utf8 tools/lint.py             # exit 1 on any error; untranslated lines are only counted
    python -X utf8 tools/lint.py --final     # also fails on untranslated lines (script/keep_jp.txt lists allowed ones)
    python -X utf8 tools/lint.py --fit "text{end:00}" ID    # check one line while writing it, and print its size

Limits: tbl/limits.tsv (tools/debug/limits.py), explained in docs/re/windows.md. Limits are in 8 px cells.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from vwf import TOKEN, cells_of, encode_en, line_width, load_font, tile_cells  # noqa: E402

SCRIPT = [ROOT / "script/signs.json", ROOT / "script/main.json"]
LIMITS = ROOT / "tbl/limits.tsv"
OVERRIDE = ROOT / "tbl/limits_override.tsv"
GLOSSARY = ROOT / "glossary.md"
KEEP = ROOT / "script/keep_jp.txt"
JAPANESE = re.compile(r"[぀-ヿ一-鿿＀-￯]")
MAX_BUBBLE_BYTES = 254  # the bubble's string index +0x21 is a byte
ORDINAL = re.compile(r"\}(st|nd|rd|th)\b")


def load_limits(path=LIMITS):
    limits = {}
    if not Path(path).exists():
        return limits
    for line in Path(path).read_text(encoding="utf8").splitlines():
        if line.startswith("#"):
            continue
        p = line.split("\t")
        limits[p[0]] = {"kind": p[1], "cols": int(p[2]), "rows": int(p[3]), "cells": int(p[4]), "room": int(p[5]),
                        "with": [w for w in p[6].split(",") if w], "source": p[9]}
    if Path(path) == LIMITS and OVERRIDE.exists():
        for line in OVERRIDE.read_text(encoding="utf8").splitlines():
            if not line.startswith("#"):
                id_, cols, _ = line.split("\t")
                limits[id_]["cols"] = int(cols)
    return limits


def load_glossary(path=GLOSSARY):
    """(jp, en, avoid list) from the glossary tables that have JP | EN | ... | Avoid columns."""
    rows = []
    for line in Path(path).read_text(encoding="utf8").splitlines():
        p = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(p) >= 5 and p[0] not in ("JP", "---") and JAPANESE.search(p[0]):
            rows.append((p[0], p[1], [a.strip() for a in p[4].split(",") if a.strip()]))
    return rows


def size(data, kind):
    """(cols, rows, pages) the way the engine sees them. The box has no measure routine, so a page break costs it nothing."""
    cols, rows, pages = cells_of(data)
    if kind == "box":
        cols = cells_of(data.replace(b"\xfd", b"\xfe"))[0]
    return cols, rows, pages


def check_entry(e, limit, font, rom, glossary, sizes=None):
    """Error strings for one entry with English."""
    en, jp, errs = e["en"], e["jp"], []
    if JAPANESE.search(en):
        errs.append("Japanese characters in the English")
    if ORDINAL.search(en):
        errs.append("ordinal suffix glued to a code")
    if en.split("{end:")[0] != en.split("{end:")[0].strip():
        errs.append("leading or trailing blank")
    jp_end, en_end = re.search(r"\{end:..\}$", jp), re.search(r"\{end:..\}$", en)
    if not en_end:
        return errs + ["no {end:MM}"]
    if jp_end.group(0) != en_end.group(0):
        errs.append(f"end code {en_end.group(0)}, the Japanese has {jp_end.group(0)}")
    bad = sorted({ch for ch in TOKEN.sub("", en) if ch not in font and ch != "♥"})
    if bad:
        return errs + [f"no glyph for {bad}"]
    try:
        _, data = encode_en(en, font, rom)
    except ValueError as err:
        return errs + [str(err)]
    flat = TOKEN.sub(" ", en)  # a name may wrap between lines
    for jp_term, en_term, avoid in glossary:
        if jp_term in jp and en_term and en_term.lower() not in flat.lower():
            errs.append(f"glossary: {jp_term} should be {en_term}")
        errs += [f"glossary: avoid {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", flat)]
    if limit is None:
        return errs + ["no limit in tbl/limits.tsv"]
    cols, rows, _ = size(data, limit["kind"])
    even = cols + (cols & 1)
    if limit["kind"] != "box" and even > limit["cols"]:
        errs.append(f"{even} cols (a page break counts as one), limit {limit['cols']}")
    if limit["kind"] == "box" and cols > limit["cols"]:
        errs.append(f"{cols} cols, limit {limit['cols']}")
    if rows > limit["rows"]:
        errs.append(f"{rows} rows, limit {limit['rows']}")
    if limit["kind"] != "box":
        if len(data) > MAX_BUBBLE_BYTES:
            errs.append(f"{len(data)} bytes, limit {MAX_BUBBLE_BYTES}")
        others = [(sizes or {}).get(w, (0, 0)) for w in limit["with"]]
        slots = even * rows + sum(o[0] for o in others)
        if limit["cells"] and slots > limit["cells"]:
            errs.append(f"{slots} sprite slots with bubbles open beside it {limit['with']}, limit {limit['cells']}: the game would show ERROR")
        tiles = even * rows + sum(o[1] for o in others)
        if limit["room"] and tiles > limit["room"]:
            errs.append(f"{tiles} tile cells with bubbles open beside it {limit['with']}, limit {limit['room']}: text would paint over an actor")
    last = re.split(r"\{nl\}|\{page\}|\{end:..\}", en)[-2]
    if "{nl}" in en and 0 < len(last.strip()) < 3 and len(en) > 20:
        errs.append(f"stub last line {last!r}")
    return errs


def lint(entries, rom, final=False):
    font, limits, glossary = load_font(), load_limits(), load_glossary()
    keep = set()
    if KEEP.exists():
        keep = {ln.split()[0] for ln in KEEP.read_text(encoding="utf8").splitlines() if ln.strip() and not ln.startswith("#")}
    sizes = {}
    for e in entries:
        if e["en"] and e["id"] in limits and limits[e["id"]]["kind"] != "box":
            try:
                data = encode_en(e["en"], font, rom)[1]
                cols, rows, _ = cells_of(data)
                sizes[e["id"]] = ((cols + (cols & 1)) * rows, tile_cells(data))
            except (ValueError, KeyError):
                pass
    errors, missing = [], 0
    for e in entries:
        if not e["en"]:
            has_text = len(e["jp"]) > len("{end:00}")
            if has_text and e["id"] not in keep:
                missing += 1
                if final:
                    errors.append((e["id"], "untranslated"))
            continue
        errors += [(e["id"], msg) for msg in check_entry(e, limits.get(e["id"]), font, rom, glossary, sizes)]
    return errors, missing


def rom_bytes():
    rom = next(iter((ROOT / "rom").glob("*.gba")), None) if (ROOT / "rom").is_dir() else None
    return rom.read_bytes() if rom else bytes(0x300000 + 256 * 64)


def main():
    import json
    args = sys.argv[1:]
    rom = rom_bytes()
    if args[:1] == ["--fit"]:
        text, id_ = args[1], args[2]
        font, limits = load_font(), load_limits()
        entry = next(e for path in SCRIPT for e in json.loads(path.read_text(encoding="utf8")) if e["id"] == id_)
        limit = limits.get(id_)
        probe = dict(entry, en=text)
        for ln in re.split(r"\{nl\}|\{page\}|\{end:..\}", text)[:-1]:
            print(f"{line_width(ln, font):4d} px  {ln}")
        print(f"limit {limit}")
        errs = check_entry(probe, limit, font, rom, load_glossary())
        print("\n".join(errs) or "OK")
        return 1 if errs else 0
    entries = [e for path in SCRIPT for e in json.loads(path.read_text(encoding="utf8"))]
    errors, missing = lint(entries, rom, "--final" in args)
    for id_, msg in errors[:60]:
        print(f"{id_}: {msg}")
    if len(errors) > 60:
        print(f"... and {len(errors) - 60} more")
    print(f"lint: {len(errors)} errors, {sum(bool(e['en']) for e in entries)} translated, {missing} untranslated")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
