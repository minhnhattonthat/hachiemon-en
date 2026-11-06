"""One contact sheet from a warp tour: every shot of the chosen scenes, labelled by file name in the sheet's tile list.

python -X utf8 tools/debug/sheets.py OUT REGEX [--names f001000,final] [--div 2] [--cols 6] [--max 48]
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument("out")
p.add_argument("regex")
p.add_argument("--names", default="")
p.add_argument("--div", default="2")
p.add_argument("--cols", default="6")
p.add_argument("--max", default="48")
p.add_argument("--sheet", default="sheet")
a = p.parse_args()
out = Path(a.out)
tmp = out / "_all"
shutil.rmtree(tmp, ignore_errors=True)
tmp.mkdir(parents=True)
want = set(a.names.split(",")) if a.names else None
for d in sorted(out.iterdir()):
    if d.is_dir() and d.name != "_all" and re.search(a.regex, d.name):
        for png in sorted(d.glob("*.png")):
            if want is None or png.stem in want:
                shutil.copy(png, tmp / f"{d.name}__{png.name}")
sys.exit(subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), str(tmp / "*.png"),
                         "--div", a.div, "--cols", a.cols, "--max", a.max, "--out", str(out / f"{a.sheet}.png")]).returncode)
