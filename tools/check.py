"""One-command check: every test plus the text lint. The pre-commit hook runs this; its exit code gates the commit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tests = subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT)
text = subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/lint.py")], cwd=ROOT)
sys.exit(tests or text)
