"""Every release gate, then the patch, its re-apply check and the zip. Stops at the first failure; never publishes (D8).

    python -X utf8 tools/release.py [--version 1.0] [--force]

Output: release/Hachiemon_EN_vX.Y.bps and .zip (patch + README). The playable ROM stays in build/.
The visual tour is not rerun here: a full tour costs most sheets their verdicts (status.md), and qa_gate.py check fails
on any build that has no tour or waiver of its own, so a release can't skip it.
jp_cells.py stands in for the skill's jp_left.py, which passes falsely on this game's pre-rendered text (phase 7).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bps  # noqa: E402
from skill import SKILL  # noqa: E402

BUILT = ROOT / "build/hachiemon_en.gba"
ORIG = ROOT / "rom/Hachiemon (Japan).gba"
TEXT_TOURS = "tour_jpm tour_jp stalljp talklong long mash warp final".split()  # the original's tours: their logs carry original offsets
PLACEHOLDER = re.compile(r"Not started|in progress|Not buildable|TODO|\{\{|<[A-Z_ ]+>")


def run(*cmd):
    print("==", " ".join(str(c) for c in cmd[1:]), flush=True)
    if subprocess.call([str(c) for c in cmd], cwd=ROOT):
        sys.exit(f"release stopped: {cmd[1:]} failed")


def py(*args):
    run(sys.executable, "-X", "utf8", *args)


def gate(ok, message):
    print("==", message, "ok" if ok else "FAILED", flush=True)
    if not ok:
        sys.exit(f"release stopped: {message}")


def hashes(data):
    return {"size": f"{len(data):,}", "crc32": f"{zlib.crc32(data):08X}", "md5": hashlib.md5(data).hexdigest(), "sha1": hashlib.sha1(data).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default="1.0")
    p.add_argument("--force", action="store_true", help="overwrite this version's files")
    a = p.parse_args()
    out = ROOT / "release"
    patch, archive = out / f"Hachiemon_EN_v{a.version}.bps", out / f"Hachiemon_EN_v{a.version}.zip"
    if not a.force and (patch.exists() or archive.exists()):
        sys.exit(f"{patch.name} or {archive.name} exists; pass --force to overwrite")

    py("tools/build.py")
    py("tools/check.py")  # tests and lint --final
    py(f"{SKILL}/scripts/emu.py", BUILT, "--out", "work/qa/smoke", "--route", "tools/routes/boot.txt", "--smoke")
    py("tools/jp_cells.py", BUILT)
    for manifest in sorted((ROOT / "work/qa").rglob("manifest.tsv")):
        py(f"{SKILL}/scripts/qa_gate.py", "check", manifest, manifest.parent / "verdicts")
    py("tools/debug/textcover.py", ORIG, *[f"work/qa/{t}" for t in TEXT_TOURS])
    unticked = re.findall(r"^- \[ \].*", (ROOT / "docs/polish.md").read_text(encoding="utf8"), re.M)
    gate(not unticked, f"docs/polish.md, {len(unticked)} unticked")
    readme = (ROOT / "README.md").read_text(encoding="utf8")
    gate(not PLACEHOLDER.search(readme) and hashlib.sha1(ORIG.read_bytes()).hexdigest() in readme, "README.md has no placeholder and has the base hash")
    # The warp tool is Lua that only emu.py loads; the build must not pull tools/debug in. Debug ROMs (marker, moved) have their own paths.
    gate("tools/debug" not in (ROOT / "tools/build.py").read_text(encoding="utf8"), "debug tool off in the build")

    src, tgt = ORIG.read_bytes(), BUILT.read_bytes()
    out.mkdir(exist_ok=True)
    patch.write_bytes(bps.make(src, tgt))
    gate(bps.apply(src, patch.read_bytes()) == tgt, "patch re-applied to a clean original equals the build")
    base, patched = hashes(src), hashes(tgt)
    text = (ROOT / "docs/release_readme.txt").read_text(encoding="utf8")
    text = text.replace("@VERSION@", a.version).replace("@PATCH@", patch.name).replace("@PATCHED_CRC32@", patched["crc32"]).replace("@PATCHED_SHA1@", patched["sha1"])
    for key, value in base.items():
        text = text.replace(f"@BASE_{key.upper()}@", value)
    gate("@" not in re.sub(r"\S+@\S+\.\S+", "", text), "zip README filled in")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", text)
    gate(sorted(zipfile.ZipFile(archive).namelist()) == sorted([patch.name, "README.txt"]), "zip holds patch + README only")
    print(json.dumps({"patch": str(patch), "zip": str(archive), "patch_bytes": patch.stat().st_size, "base": base, "patched": patched}, indent=1))
    print("Built and verified. Publishing is the owner's call.")


if __name__ == "__main__":
    main()
