"""Measured text limits per string, from a marker tour's bub lines: writes tbl/limits.tsv, which tools/lint.py reads.

    python -X utf8 tools/debug/limits.py MAP.tsv OUT [OUT...]

Columns: id, kind, max_cols, max_rows, sprite_slots, tile_cells, with (ids sharing both budgets), x range, y range, source.
A bubble is centred on its x, y and has an 8 px frame, so its size follows from how close it sits to a screen edge. Strings
a tour never showed get the tightest limit seen anywhere, tagged guess. Facts and shots: docs/re/windows.md.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build import load_script  # noqa: E402
from vwf import cells_of  # noqa: E402
from tbl import Table  # noqa: E402

BUB = re.compile(r"^bub f\d+ (\d) ([0-9A-F]{6}) x(\d+) y(\d+) c(\d+) r(\d+) base(\d+)/(\d+) tile(\d+)", re.M)
PAST = re.compile(r"^bub f\d+ .* c[1-9]\d* .*tile(\d+)\+\d+ past(\d+)", re.M)
OAM = re.compile(r"^oam f\d+ (\d+)", re.M)
BOX = re.compile(r"^box f\d+ ([0-9A-F]{6})", re.M)
FRAME, W, H = 8, 240, 160
MAX_COLS, MAX_ROWS = 16, 3  # the largest bubble tested at the edges of the screen
BOX_COLS, BOX_ROWS = 23, 2
SIGN_COLS, SIGN_ROWS, SIGN_CELLS = 14, 2, 28
GUESS_COLS, GUESS_ROWS, GUESS_CELLS = 10, 2, 41


def tile_room(text):
    """text tile base -> cells before the scene's next OBJ tile. A cell takes 2 tiles and stays in VRAM after its bubble
    closes, so a cell past that tile paints over an actor for the rest of the scene (seen in talk10 at full width)."""
    past = {}
    for tile, end in PAST.findall(text):
        past[int(tile)] = max(past.get(int(tile), 0), int(end))
    used = sorted(int(t) for t in OAM.findall(text))
    rooms = {}
    for tile, end in past.items():
        ceiling = next((t for t in used if t >= end), 1024)
        rooms[tile] = (ceiling - tile) // 2
    return rooms


def fit_cols(xs):
    room = min(min(x, W - x) for x in xs) - FRAME
    return min(MAX_COLS, max(0, room // 4) & ~1)


def fit_rows(ys):
    room = min(min(y, H - y) for y in ys) - FRAME
    return min(MAX_ROWS, max(0, room // 8))


def main():
    map_file, outs = sys.argv[1], sys.argv[2:]
    ids, kinds = {}, {}
    for line in Path(map_file).read_text(encoding="utf8").splitlines():
        id_, _, string, kind = line.split("\t")
        ids[int(string, 16)], kinds[id_] = id_, kind
    seen = {}
    shown_in_box = set()
    for out in outs:
        for log in sorted(Path(out).glob("*/log.txt")):
            text = log.read_text(encoding="utf8", errors="replace")
            latest = {}
            rooms = tile_room(text)
            for slot, string, x, y, c, r, used, base, tile in BUB.findall(text):
                id_ = ids.get(int(string, 16))
                if id_ is None or c == "0":
                    continue
                s = seen.setdefault(id_, {"x": set(), "y": set(), "base": 0, "with": set(), "room": 128})
                s["x"].add(int(x))
                s["y"].add(int(y))
                s["base"] = max(s["base"], int(base))
                s["room"] = min(s["room"], rooms.get(int(tile), 128))
                latest[slot] = id_
                if int(used):
                    s["with"].update(v for k, v in latest.items() if k < slot)
            shown_in_box.update(ids.get(int(a, 16)) for a in BOX.findall(text))
    codec = Table.load(ROOT / "tbl/jp.tbl")
    rows = []
    for e in load_script():
        id_, kind = e["id"], kinds[e["id"]]
        jp_cols, jp_rows, _ = cells_of(codec.encode(e["jp"]))
        if kind == "box":
            rows.append((id_, kind, BOX_COLS, BOX_ROWS, 0, 0, "", "", "", "measured" if id_ in shown_in_box else "guess"))
        elif kind in ("sign", "none"):
            rows.append((id_, kind, SIGN_COLS, SIGN_ROWS, SIGN_CELLS, SIGN_CELLS, "", "", "", "measured" if id_ in seen else "guess"))
        elif id_ in seen:
            s = seen[id_]
            # A line the Japanese already shows at that size overflows no worse than the original did.
            cols = max(fit_cols(s["x"]), jp_cols + (jp_cols & 1))
            lines = max(fit_rows(s["y"]), jp_rows)
            xs, ys = sorted(s["x"]), sorted(s["y"])
            rows.append((id_, kind, cols, lines, 128 - s["base"], s["room"], ",".join(sorted(s["with"])),
                         f"{xs[0]}-{xs[-1]}", f"{ys[0]}-{ys[-1]}", "measured"))
        else:
            rows.append((id_, kind, max(GUESS_COLS, jp_cols + (jp_cols & 1)), max(GUESS_ROWS, jp_rows), GUESS_CELLS, GUESS_CELLS, "", "", "", "guess"))
    out = ROOT / "tbl/limits.tsv"
    with open(out, "w", encoding="utf8", newline="\n") as f:
        f.write("# id\tkind\tmax_cols\tmax_rows\tsprite_slots\ttile_cells\twith\tx\ty\tsource\n")
        for row in rows:
            f.write("\t".join(str(v) for v in row) + "\n")
    print(f"{out}: {len(rows)} rows, {sum(r[-1] == 'guess' for r in rows)} guessed")


if __name__ == "__main__":
    main()
