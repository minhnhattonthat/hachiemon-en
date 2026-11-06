"""Independent read-only review with `codex exec`, one process per file, reports in OUTDIR/<stem>.md.

    python -X utf8 tools/codex_review.py docs/reviewer-brief.md work/qa/reviews work/qa/pairs/b*.txt
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def review(brief, out, path):
    report = out / f"{path.stem}.md"
    prompt = (f"Read {brief} and follow it for the file {path}. Also read glossary.md, docs/style-reference.md and "
              "docs/synopsis.md. Space in this game is very tight, so judge meaning and voice rather than asking for longer "
              "lines, and give any suggested English at about the same length. Read-only: edit nothing. "
              "Your final message is the report the brief asks for, nothing else.")
    done = subprocess.run(["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(report), prompt],
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf8", errors="replace", shell=sys.platform == "win32")
    return path.name, done.returncode


def main():
    brief, out, files = sys.argv[1], Path(sys.argv[2]), [Path(p) for p in sys.argv[3:]]
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(lambda p: review(brief, out, p), files))
    for name, code in results:
        print(name, "ok" if code == 0 else f"exit {code}")
    return 1 if any(code for _, code in results) else 0


if __name__ == "__main__":
    sys.exit(main())
