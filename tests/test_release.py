"""tools/release.py: --help builds nothing, and an existing version isn't overwritten without --force."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def release(*args):
    return subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/release.py"), *args], capture_output=True, text=True, cwd=ROOT)


def test_help_builds_nothing():
    built = ROOT / "build/hachiemon_en.gba"
    before = built.stat().st_mtime_ns if built.exists() else None
    assert release("--help").returncode == 0
    assert (built.stat().st_mtime_ns if built.exists() else None) == before


def test_refuses_to_overwrite():
    patch = ROOT / "release/Hachiemon_EN_vtest.bps"
    patch.parent.mkdir(exist_ok=True)
    patch.write_bytes(b"keep")
    try:
        done = release("--version", "test")
        assert done.returncode != 0 and "--force" in done.stderr and patch.read_bytes() == b"keep"
    finally:
        patch.unlink()
