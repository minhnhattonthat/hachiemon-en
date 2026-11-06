"""What changed between two sets of QA sheets, tile by tile, so a recheck reads only the shots that differ.

    python -X utf8 tools/debug/sheetdiff.py OLD_TOUR NEW_TOUR [--out work/qa/sheetdiff] [--tol 12]
Compares each scene's shots frame for frame (TOUR/{a,b}/SCENE/fNNNNNN.png). A frame differs when more than `--tol` pixels do. Prints per scene the
frames that differ and writes OUT/SCENE.png: new frames, each beside its old one, for reading. A frame only one tour has is listed as new or gone.
Sheets' shots are picked from these frames, so a scene with no differing frame has a sheet with nothing new to read.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


def differing_pixels(a, b):
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 8 else 0)
    return sum(1 for v in diff.getdata() if v)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--out", default="work/qa/sheetdiff")
    p.add_argument("--tol", type=int, default=12)
    p.add_argument("--max", type=int, default=24, help="frames per scene image")
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for part in ("a", "b"):
        for d in sorted((Path(a.new) / part).iterdir()):
            if not d.is_dir():
                continue
            old = Path(a.old) / part / d.name
            changed, new_only = [], []
            for png in sorted(d.glob("f[0-9]*.png")):
                ref = old / png.name
                if not ref.exists():
                    new_only.append(png.stem)
                    continue
                im, rf = Image.open(png).convert("RGB"), Image.open(ref).convert("RGB")
                n = differing_pixels(im, rf)
                if n > a.tol:
                    changed.append((png.stem, n, im, rf))
            gone = sorted(x.stem for x in old.glob("f[0-9]*.png") if not (d / x.name).exists())
            if changed or new_only or gone:
                total += 1
                print(f"{d.name}: {len(changed)} differ {[f'{f}:{n}' for f, n, _, _ in changed[:4]]}{' ...' if len(changed) > 4 else ''} new {len(new_only)} gone {len(gone)}")
            if changed:
                shown = changed if len(changed) <= a.max else [changed[i * len(changed) // a.max] for i in range(a.max)]
                cols = 4
                sheet = Image.new("RGB", (cols * 484, ((len(shown) + cols - 1) // cols) * 172), (60, 0, 60))
                dr = ImageDraw.Draw(sheet)
                for i, (f, n, im, rf) in enumerate(shown):
                    x0, y0 = i % cols * 484, i // cols * 172
                    dr.text((x0 + 2, y0), f"{f} new/old {n}px", fill=(0, 255, 255))
                    sheet.paste(im, (x0, y0 + 12))
                    sheet.paste(rf, (x0 + 241, y0 + 12))
                sheet.save(out / f"{d.name}.png")
    print(total, "scenes differ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
