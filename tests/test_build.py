"""Phase 3: unpack then repack with no edits gives the dump back, and the writers can really move things."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
from build import Image, build, load_script, packed_spans, real_slots, repack_text, repoint, strings, text_slots  # noqa: E402
from gbacomp import le_compress, le_decompress, le_scan, lz_compress, lz_decompress, scan  # noqa: E402
from gfxcover import rows  # noqa: E402
from romdiff import check  # noqa: E402
from tbl import Table  # noqa: E402

ROM = next(iter((ROOT / "rom").glob("*.gba")), None) if (ROOT / "rom").is_dir() else None
needs_rom = pytest.mark.skipif(ROM is None, reason="no ROM")
FREE = 0x3A8600  # candidate free space, docs/re/rom-map.md


@needs_rom
def test_identity_build():
    orig = ROM.read_bytes()
    img = build(orig)
    assert bytes(img.out) == orig
    assert check(orig, bytes(img.out), set(), img.writes)[0] == []
    assert sum(who.startswith("textptr") for *_, who in img.writes) == 886  # 810 script, 35 code, 41 sign


@needs_rom
def test_moved_text_reads_the_same_through_every_pointer():
    orig = ROM.read_bytes()
    codec = Table.load(ROOT / "tbl/jp.tbl")
    slots = text_slots(orig)
    img = Image(orig)
    repack_text(img, slots, codec, load_script(), FREE)
    assert check(orig, bytes(img.out), set(), img.writes)[0] == []
    for s in strings(orig):
        for w in slots.get(s, []):
            new = int.from_bytes(img.out[w:w + 4], "little") - 0x08000000
            assert new >= FREE
            assert codec.decode(img.out, new) == codec.decode(orig, s)


@needs_rom
def test_every_graphics_row_has_a_real_slot():
    orig = ROM.read_bytes()
    slots = real_slots(orig)
    starts = [a for a, _ in packed_spans(orig)]
    for num, _, spans in rows():
        blocks = [o for lo, hi in spans for o in starts if lo <= o <= hi]
        assert blocks, num
        assert all(slots.get(o) for o in blocks), num


@needs_rom
def test_moved_block_repoints_and_decodes():
    orig = ROM.read_bytes()
    slots = real_slots(orig)
    old = 0x2A8454  # row 22, the all-lips banner; its slot is a code literal
    data, _ = le_decompress(orig, old)
    img = Image(orig)
    img.write(FREE, le_compress(data), "gfx")
    repoint(img, slots, old, FREE, "gfxptr")
    assert int.from_bytes(img.out[0x3D74:0x3D78], "little") == 0x08000000 + FREE
    assert le_decompress(img.out, FREE)[0] == data


def test_le_compress_ops():
    for data in (b"A", b"AB", b"ABC" * 40, b"\x00" * 500, bytes(range(256)) * 2, b"xy" + bytes(range(200)) + b"xy" * 3):
        assert le_decompress(le_compress(data))[0] == data


@needs_rom
def test_compressors_roundtrip_small_real_blocks():
    """The full sweep over every block is tools/gbacomp.py verify: too slow for the commit hook."""
    rom = ROM.read_bytes()
    for off in [o for o, _, size in scan(rom) if size < 0x400][:40]:
        data, _ = lz_decompress(rom, off)
        assert lz_decompress(lz_compress(data))[0] == data
    for off in [o for o, _, size in le_scan(rom) if size < 0x400][:40]:
        data, _ = le_decompress(rom, off)
        assert le_decompress(le_compress(data))[0] == data
