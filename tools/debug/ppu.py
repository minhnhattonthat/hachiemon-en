"""Dump video memory of warp scenes on any ROM, and list what is on screen, to read how graphics are laid out.

    python -X utf8 tools/debug/ppu.py SCENE[:FRAMES] ... [--rom ROM] [--out work/qa/ppu] [--at N,N..]
With --at, dumps and a shot at those frames (the scene then runs to the last one). Prints each dump's stem.
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402


def dump(scene, frames, a):
    out = Path(a.out) / scene
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/emu.py"), a.rom, "--out", str(out), "--script", "tools/debug/warp.lua",
           "--script", "tools/debug/lzlog.lua", "--var", f"SCENE='{scene}'", "--timeout", "600"]
    if a.at:
        at = [int(x) for x in a.at.split(",")]
        every = at[1] - at[0] if len(at) > 1 else None
        frames = at[-1] + 1
        cmd += ["--shots", a.at]
        cmd += ["--var", f"DUMP_EVERY={every}"] if every else ["--var", f"DUMP_AT={at[0]}"]
    cmd += ["--frames", str(frames), "--script", str(Path(SKILL) / "scripts/lua/probes/ppudump.lua")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return scene, r.returncode, sorted(p.name[:-9] for p in out.glob("ppu_*.vram.bin"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenes", nargs="+")
    p.add_argument("--rom", default="rom/Hachiemon (Japan).gba")
    p.add_argument("--out", default="work/qa/ppu")
    p.add_argument("--at", default="")
    p.add_argument("--jobs", type=int, default=4)
    a = p.parse_args()
    jobs = [(s.partition(":")[0], int(s.partition(":")[2] or 1800)) for s in a.scenes]
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda j: dump(j[0], j[1], a), jobs))
    for scene, rc, stems in results:
        print(scene, "exit", rc, " ".join(stems[-6:]))
    return max(rc for _, rc, _ in results)


if __name__ == "__main__":
    sys.exit(main())
