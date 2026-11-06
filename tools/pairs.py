"""Reviewer input: JP and English side by side with speakers, in script order.

    python -X utf8 tools/pairs.py [OUTDIR]     # default work/qa/pairs: one file per work/tl batch, +-2 context lines

Speakers are the guesses in docs/re/text.md, Speakers by anim. Lines with no anim are captions or narration.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build import load_script  # noqa: E402

SPEAKERS = {
    "1D4540": "Hachiemon", "1C6CC0": "Muscle Hachiemon", "1D2B84": "Tower Hachiemon", "1CF84C": "Gunman",
    "1CF830": "Gang", "1CF814": "Gang", "1D494C": "Pegasus-eating gentleman", "1D4914": "Hunter wife",
    "1D48F8": "Hunter husband", "1D4930": "Hunter son", "1D4968": "Yamata", "1D4984": "Yamata, beaten",
    "1D48DC": "Park villain", "1D1908": "Boss lady", "1D18D0": "Kid brother", "1D18EC": "Kid brother",
    "1D3684": "Osaka merchant", "1D36A0": "Osaka merchant", "1D45CC": "Auntie", "1D45E8": "Auntie's friend",
    "1D478C": "Space alien", "1D47A8": "Space alien", "1D47FC": "Tough guy", "1D4818": "Tough guy",
    "1D4834": "Tough guy", "1D4700": "Pegasus (carrier)", "1D4770": "Egg", "1D4658": "Panda",
    "1D455C": "Cow", "1D4578": "Cow", "1D45B0": "Whale", "1D4604": "Penguin", "1D4620": "Penguin",
    "1D4674": "Mole", "1D4690": "Mole", "1D46C8": "Gator", "1D46E4": "Bear", "1D471C": "Pegasus",
    "1D4738": "Tyranno", "1D4754": "Lion",
}


def speaker(entry):
    for ref in entry.get("refs") or []:
        if ref.get("anim"):
            return SPEAKERS.get(ref["anim"], ref["anim"])
    return "caption" if entry.get("refs") else "unused"


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "work/qa/pairs"
    out.mkdir(parents=True, exist_ok=True)
    script = load_script()
    at = {e["id"]: i for i, e in enumerate(script)}
    for batch in sorted((ROOT / "work/tl").glob("b[0-9][0-9][0-9].tsv")):
        ids = {at[ln.split("\t")[0]] for ln in batch.read_text(encoding="utf8").splitlines() if ln}
        shown = sorted({i + d for i in ids for d in range(-2, 3) if 0 <= i + d < len(script)})  # a batch can span both files
        rows = []
        for i in shown:
            e = script[i]
            mark = ">>" if i in ids else "  "
            rows.append(f"{mark} {e['id']} | {speaker(e)} | {e['jp']}\n   {e['en']}")
        (out / f"{batch.stem}.txt").write_text("\n".join(rows) + "\n", encoding="utf8", newline="\n")
    print(f"{out}: done")


if __name__ == "__main__":
    main()
