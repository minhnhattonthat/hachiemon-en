"""Contact sheets for the visual-QA gate from the two tours of phase 8, into work/qa/tour/sheets/ (AGENTS.md, Tour).

    python -X utf8 tools/debug/qasheets.py [TOUR=work/qa/tour]
TOUR/a holds scenes without text pages, one sheet per group of chosen frames. TOUR/b holds mashed text scenes, one sheet
per scene of the frames that changed. Then: qa_gate.py init work/qa/manifest.tsv work/qa/tour/sheets --build build/hachiemon_en.gba
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402

SHEET = str(Path(SKILL) / "scripts" / "sheet.py")
GROUPS = {  # sheet name: (scene regex, frames)
    "front": (r"^(logos|title|title_clear|menu|menu_.*|delete|delete_done|save_error|continue_cut|gameover|map)$", "f000900,f001800"),
    "help": (r"^help", "f001500"),
    "cards": (r"^stage\d\d$", "f000810"),
    "play": (r"^stage\d\d$", "f001800"),
    "banners": (r"^(vs\d|step\d+|stage_clear)$", "f001245"),
    "time_over": (r"^time_over$", "f000960,f001020,f001080,f001215,f001290"),
    "pause": (r"^(pause.*|death.*)$", "f001500,f002400"),
    "slot": (r"^slot$", "f001215,f001500,f001800,f002400"),
    "credits": (r"^credits$", "f000720,f000780,f000900,f001020,f001140,f001215,f001350,f001470"),
    "fights": (r"^fight\d$", ""),
}


def sheet(args):
    subprocess.run([sys.executable, "-X", "utf8", SHEET, *args], check=True, capture_output=True)


def box_rows(path):
    """A sign or story box as bytes, or None: rows with a long run of black, which stage art rarely has."""
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    rows = [y for y in range(h) if sum(px[x, y] < 16 for x in range(w)) >= 120]
    if len(rows) < 12:
        return None
    return im.crop((0, rows[0], w, rows[-1] + 1)).tobytes()


def pages(d):
    """The shots worth reading in a mashed scene: for each string the bubble log names, the last shot before the next
    string (and one midway through a long one, for extra pages); for boxes, each shot whose box changed.
    shortcut: a page shorter than the shot spacing can fall between shots; lower the spacing if a line matters."""
    shots = {int(p.stem[1:]): p for p in d.glob("f[0-9]*.png")}
    frames = sorted(shots)
    log = (d / "log.txt").read_text(encoding="utf8", errors="replace")
    starts = sorted({int(f) for f, x in re.findall(r"^bub f(\d+) \d \w+ x(\d+) ", log, re.M) if int(x)})
    keep = set()
    for a, b in zip(starts, [*starts[1:], starts[-1] + 200] if starts else []):
        inside = [f for f in frames if a < f < b]
        if inside:
            keep.add(inside[-1])
            if b - a > 200:
                keep.add(inside[len(inside) // 2])
    last = None
    for f in frames:
        box = box_rows(shots[f])
        if box and (last is None or len(box) != len(last) or sum(x != y for x, y in zip(box, last)) > len(box) // 100):
            keep.add(f)
            last = box
    return [shots[f] for f in sorted(keep)]


def main():
    tour = Path(sys.argv[1] if len(sys.argv) > 1 else "work/qa/tour")
    out = tour / "sheets"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    tmp = out / "_tmp"
    for name, (regex, frames) in GROUPS.items():
        want = set(frames.split(",")) if frames else None
        tmp.mkdir()
        for d in sorted((tour / "a").iterdir()):
            if d.is_dir() and re.search(regex, d.name):
                for png in sorted(d.glob("f*.png")):
                    if want is None or png.stem in want:
                        shutil.copy(png, tmp / f"{d.name}__{png.name}")
        sheet([str(tmp / "*.png"), "--div", "1", "--cols", "6", "--max", "48", "--out", str(out / f"sheet_{name}.png")])
        shutil.rmtree(tmp)
    tiles = 0
    for d in sorted((tour / "b").iterdir()):
        if d.is_dir():
            picks = pages(d)
            tiles += len(picks)
            if picks:
                sheet([*map(str, picks), "--div", "1", "--cols", "6", "--max", "48", "--out", str(out / f"sheet_{d.name}.png")])
            else:
                print("no text pages:", d.name)
    print(f"{len(list(out.glob('*.png')))} sheets, {tiles} text-page tiles: {out}")


if __name__ == "__main__":
    main()
