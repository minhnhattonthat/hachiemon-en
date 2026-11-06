"""Which ids did a marker tour show, and where? Reads the bub/box lines of tools/debug/bublog.lua.

    python -X utf8 tools/debug/markercover.py MAP.tsv OUT [OUT...] [--tsv FILE]

Prints the count per kind, the ids never reached, and any bubble that left the screen or fell back to the ERROR string.
--tsv writes one row per id: id, kind, scenes, x range, y range, largest cols, largest rows.
"""
import argparse
import re
import sys
from pathlib import Path

BUB = re.compile(r"^bub f\d+ (\d) ([0-9A-F]{6}) x(\d+) y(\d+) c(\d+) r(\d+)", re.M)
BOX = re.compile(r"^box f\d+ ([0-9A-F]{6})", re.M)
FRAME = 8  # the bubble frame adds this much on each side of the text cells
SCREEN_W, SCREEN_H = 240, 160


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("map")
    p.add_argument("out", nargs="+")
    p.add_argument("--tsv", default="")
    a = p.parse_args()
    ids, kinds = {}, {}
    for line in Path(a.map).read_text(encoding="utf8").splitlines():
        id_, _, string, kind = line.split("\t")
        ids[int(string, 16)] = id_
        kinds[id_] = kind
    seen, unknown, off = {}, set(), {}
    for out in a.out:
        for log in sorted(Path(out).glob("*/log.txt")):
            text = log.read_text(encoding="utf8", errors="replace")
            scene = log.parent.name
            for slot, string, x, y, c, r in BUB.findall(text):
                string, x, y, c, r = int(string, 16), int(x), int(y), int(c), int(r)
                if not c:
                    continue  # the slot is set but not measured yet
                id_ = ids.get(string)
                if id_ is None:
                    unknown.add((string, scene))
                    continue
                s = seen.setdefault(id_, {"scenes": set(), "x": [], "y": [], "c": 0, "r": 0})
                s["scenes"].add(scene)
                s["x"].append(x)
                s["y"].append(y)
                s["c"], s["r"] = max(s["c"], c), max(s["r"], r)
                half = (c + (c & 1)) * 4 + FRAME
                if x - half < 0 or x + half > SCREEN_W or y - r * 8 - FRAME < 0 or y + r * 8 + FRAME > SCREEN_H:
                    off.setdefault(id_, (scene, x, y, c, r))
            for string in BOX.findall(text):
                id_ = ids.get(int(string, 16))
                if id_:
                    seen.setdefault(id_, {"scenes": set(), "x": [], "y": [], "c": 0, "r": 0})["scenes"].add(scene)
                elif int(string, 16) >= 0x400000:
                    unknown.add((int(string, 16), scene))
    by_kind = {}
    for id_, kind in kinds.items():
        got, total = by_kind.get(kind, (0, 0))
        by_kind[kind] = (got + (id_ in seen), total + 1)
    for kind, (got, total) in sorted(by_kind.items()):
        print(f"{kind}: {got}/{total} reached")
    print(f"not an id (ERROR fallback or a bad pointer): {sorted(unknown)[:12]}" if unknown else "no pointer outside the id list")
    print(f"{len(off)} ids left the screen at least once")
    for id_, where in sorted(off.items())[:20]:
        print(f"  {id_} {where}")
    missing = [i for i in kinds if i not in seen]
    print(f"{len(missing)} ids unreached: {' '.join(missing[:60])}{' ...' if len(missing) > 60 else ''}")
    if a.tsv:
        with open(a.tsv, "w", encoding="utf8", newline="\n") as f:
            for id_, s in sorted(seen.items()):
                xs, ys = s["x"] or [0], s["y"] or [0]
                f.write(f"{id_}\t{kinds[id_]}\t{','.join(sorted(s['scenes']))}\t{min(xs)}-{max(xs)}\t{min(ys)}-{max(ys)}\t{s['c']}\t{s['r']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
