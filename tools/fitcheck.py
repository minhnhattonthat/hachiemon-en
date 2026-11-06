"""Check proposed lines against the width limits: one `id<TAB>text` per line in FILE; text without {end:..} keeps the line's own.

    python -X utf8 tools/fitcheck.py FILE

Prints each id's current JP and EN with the result of `lint.py --fit` and exits 1 if any fail. Edits nothing.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build import load_script  # noqa: E402


def main():
    entries = {e["id"]: e for e in load_script()}
    bad = 0
    for line in Path(sys.argv[1]).read_text(encoding="utf8").splitlines():
        if not line.strip():
            continue
        id_, text = line.split("\t", 1)
        e = entries[id_]
        if "{end:" not in text:
            text += re.search(r"\{end:..\}$", e["en"]).group(0)
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "lint.py"), "--fit", text, id_], capture_output=True, text=True, encoding="utf8")
        bad += r.returncode != 0
        print(f"{id_} {'ok' if r.returncode == 0 else 'FAIL'} {r.stdout.strip()} {r.stderr.strip()}\n  jp {e['jp']}\n  en {e['en']}\n  -> {text}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
