"""Warp to every scene in scenes.lua from a cold boot and collect the proof shots.

python -X utf8 tools/debug/tour.py ROM [--out work/qa/warp] [--only REGEX] [--frames 1500] [--jobs 4] [--shots a,b,c] [--mash N] [--states work/states]

Each scene is its own cold boot in OUT/<scene>/. OUT/report.tsv says, per scene, whether the warp fired and whether
the game reached the scene's substate; exit 1 if any scene failed. Contact sheets go to OUT/sheet*.png.
"""
import argparse
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402


FIGHT_FRAMES = 7000  # stage 8 reaches its VS banner at f4024
WIN_FRAMES = 14000  # boss 5's defeat script ends at about f11900 on the marker build, later in English


def scene_names():
    # shortcut: reads names by running the scene list's own rules in Python; keep the loops in scenes.lua simple.
    text = (Path(__file__).parent / "scenes.lua").read_text(encoding="utf8")
    names = re.findall(r"^\s*(\w+)\s*=\s*\{", text, re.M)
    names = [n for n in names if n != "S"]
    nodes = re.search(r"stage_nodes = \{([^}]*)\}", text).group(1).split(",")
    names += [f"stage{n:02d}" for n in range(1, len(nodes) + 1)]
    first, last = re.search(r"for id = (\d+), (0x\w+)", text).groups()
    names += [f"talk{i:02d}" for i in range(int(first), int(last, 16) + 1)]
    names += [f"help{i}" for i in range(int(re.search(r'for n = 0, (\d+) do S\["help"', text).group(1)) + 1)]
    names += [f"sign{i:02d}" for i in range(int(re.search(r"for n = 0, (\d+) do\s+S\[string.format\(\"sign", text).group(1)) + 1)]
    return names


def run(rom, out, name, a):
    d = Path(out) / name
    if d.exists():
        shutil.rmtree(d)
    frames = max(a.frames, FIGHT_FRAMES) if name.startswith("fight") else max(a.frames, WIN_FRAMES) if name.startswith("win") else a.frames
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), rom, "--out", str(d),
           "--script", "tools/debug/warp.lua", "--script", "tools/debug/lzlog.lua", "--script", "tools/debug/textwatch.lua", "--script", "tools/debug/bublog.lua",
           "--var", f"SCENE='{name}'", "--frames", str(frames),
           "--timeout", str(max(280, frames // 20))]
    if name.startswith(("fight", "win")):
        cmd += ["--shot-every", "300"]  # the door, bubbles and VS banner come at different frames per boss
    elif a.shots:
        cmd += ["--shots", a.shots]
    if a.mash:
        cmd += ["--mash", str(a.mash), "--mash-key", "a"]
    state = Path(a.states) / f"{name}.mss" if a.states else None
    if state:
        cmd += ["--state-out", str(state)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = (d / "log.txt").read_text(encoding="utf8", errors="replace") if (d / "log.txt").exists() else ""
    warped = "warp " in log
    reached = re.search(r"reached sub=(\d+) step=(\d+) at f(\d+)", log)
    ok = r.returncode == 0 and warped and reached is not None
    shots = sorted(d.glob("f*.png")) + sorted(d.glob("final.png"))
    blank = ok and shots and all(Image.open(s).convert("RGB").getcolors(8) for s in shots)  # flags alone don't prove the screen
    ok = ok and not blank
    if state and not ok:
        state.unlink(missing_ok=True)  # a state from a scene that was never reached is silently wrong later
    return name, ok, r.returncode, "every shot blank" if blank else reached.group(0) if reached else "not reached"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("rom")
    p.add_argument("--out", default="work/qa/warp")
    p.add_argument("--only", default="")
    p.add_argument("--frames", type=int, default=1500)
    p.add_argument("--shots", default="")
    p.add_argument("--mash", type=int, default=0)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--states", default="", help="also save OUT state per scene into this folder, e.g. work/states")
    a = p.parse_args()
    names = [n for n in scene_names() if re.search(a.only, n)]
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.states:
        Path(a.states).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        rows = list(ex.map(lambda n: run(a.rom, a.out, n, a), names))
    report = Path(a.out) / "report.tsv"
    report.write_text("".join(f"{n}\t{'ok' if ok else 'FAIL'}\t{rc}\t{msg}\n" for n, ok, rc, msg in rows), encoding="utf8")
    bad = [r for r in rows if not r[1]]
    print(f"{len(rows) - len(bad)}/{len(rows)} ok; {report}")
    for r in bad:
        print("FAIL", r)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
