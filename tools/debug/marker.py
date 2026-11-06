"""Marker build: every string becomes `[id] filler` at a chosen pixel width, keeping its pages and lines. script/ stays as it is.

    python -X utf8 tools/debug/marker.py [--bubble PX] [--box PX] [--out work/qa/marker.gba] [--only ID,ID --text "literal"]

--bubble 0 uses each string's Japanese width. Writes OUT and OUT.map.tsv (id, first byte, string address, kind), which
tools/debug/markercover.py reads to say which ids a tour reached.
"""
import argparse
import copy
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build import ROM, build, load_script  # noqa: E402
from lint import load_limits  # noqa: E402
from romdiff import check as romdiff_check  # noqa: E402
from vwf import line_width, load_font  # noqa: E402

FILLER = "The quick brown fox jumps over the lazy dog, then Hachiemon's lips! "
SIGN_WIDTH = 112
BOX_ROWS = (184, 184)  # 23 cells: a full 24th cell plus {nl} skips a row, and cell 47 holds the page cursor (docs/re/text.md)


def kind(entry):
    """box, sign or bubble, from who points at the string."""
    refs = entry["refs"]
    if not refs:
        return "none"
    return {"code": "box", "sign": "sign"}.get(refs[0]["scene"], "bubble")


def filler_line(prefix, width, font):
    """prefix plus filler, cut to the last character that still fits width."""
    text = prefix
    for ch in FILLER * 8:
        if line_width(text + ch, font) > width:
            break
        text += ch
    return text.rstrip()


def at_limit(entry, limit, font):
    """The string filled to its limit in tbl/limits.tsv, keeping the Japanese page count: the width gate's own test.
    Bubbles sharing their cell budget split it, as lint.py makes them do."""
    jp = entry["jp"]
    end = re.search(r"\{end:..\}$", jp).group(0)
    cols, rows = limit["cols"], limit["rows"]
    if limit["cells"] and limit["kind"] != "box":
        group = len(limit["with"]) + 1
        share = min(limit["cells"], limit["room"]) // group
        # A bubble reserves one row more than it shows for the next one (vwf.tile_cells), so a shared budget counts rows + 1.
        need = (lambda c, r: c * (r + 1)) if group > 1 else (lambda c, r: c * r)
        while need(cols, rows) > share and rows > 1:
            rows -= 1
        while need(cols, rows) > share and cols > 2:
            cols -= 2
    pages = jp[:-len(end)].split("{page}")
    out = []
    for number, _ in enumerate(pages):
        lines = []
        for n in range(rows):
            cost = 8 if limit["kind"] != "box" and number < len(pages) - 1 and n == rows - 1 else 0
            prefix = f"[{entry['id']}] " if n == 0 else ""
            lines.append(filler_line(prefix, max(cols * 8 - cost, line_width(prefix, font)), font))
        out.append("{nl}".join(lines))
    return "{page}".join(out) + end


def marker_text(entry, a, font):
    jp = entry["jp"]
    end = re.search(r"\{end:..\}$", jp).group(0)
    what = kind(entry)
    pages = []
    all_pages = jp[:-len(end)].split("{page}")
    for number, page in enumerate(all_pages):
        lines = []
        split = page.split("{nl}")
        for n, line in enumerate(split):
            if what != "box" and number < len(all_pages) - 1 and n == len(split) - 1:
                # the bubble measure counts the page break as a cell on its line (vwf.cells_of)
                width = (a.bubble or len(line.replace("\\s", " ")) * 8) if what == "bubble" else SIGN_WIDTH
                prefix = f"[{entry['id']}] " if n == 0 else ""
                lines.append(filler_line(prefix, max(width - 8, line_width(prefix, font)), font))
                continue
            if what == "bubble":
                width = a.bubble or len(line.replace("\\s", " ")) * 8
            elif what in ("sign", "none"):
                width = SIGN_WIDTH  # signs are bubbles with only 28 cells to spend: the caller passes +0x30 = 100 (docs/re/text.md)
            else:
                width = a.box or BOX_ROWS[min(n, 1)]
            prefix = f"[{entry['id']}] " if n == 0 else ""
            lines.append(filler_line(prefix, max(width, line_width(prefix, font)), font))
        pages.append("{nl}".join(lines))
    return "{page}".join(pages) + end


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--limits", action="store_true", help="fill every string to its limit in tbl/limits.tsv")
    p.add_argument("--bubble", type=int, default=0)
    p.add_argument("--box", type=int, default=0)
    p.add_argument("--out", default=str(ROOT / "work/qa/marker.gba"))
    p.add_argument("--only", default="", help="comma list of ids; the rest stay Japanese")
    p.add_argument("--text", default="", help="literal text for --only ids, with its {end:MM}")
    a = p.parse_args()
    orig = ROM.read_bytes()
    font = load_font()
    entries = copy.deepcopy(load_script())
    only = set(a.only.split(",")) if a.only else None
    limits = load_limits() if a.limits else {}
    for e in entries:
        if only is None or e["id"] in only:
            e["en"] = a.text or (at_limit(e, limits[e["id"]], font) if a.limits else marker_text(e, a, font))
    img = build(orig, entries)
    errs, _ = romdiff_check(orig, bytes(img.out), set(), img.writes)
    if errs:
        sys.exit("\n".join(errs))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img.out)
    with open(str(out) + ".map.tsv", "w", encoding="utf8", newline="\n") as f:
        for e in entries:
            first, string = img.where[e["id"]]
            f.write(f"{e['id']}\t{first:06X}\t{string:06X}\t{kind(e)}\n")
    print(f"{out}: {len(img.out)} bytes, sha1 {hashlib.sha1(img.out).hexdigest()}, text ends {max(s for _, s in img.where.values()):#x}")


if __name__ == "__main__":
    main()
