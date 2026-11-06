"""Phase 3: unpack then repack with no edits gives the dump back, and the writers can really move things."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
from build import ERROR_SLOT, GLYPH_LOADS, KEEP_ON_SCREEN, TEXT_BASE, Image, build, jp_script, load_script, packed_spans, real_slots, repack_text, repoint, strings, text_slots  # noqa: E402
from gbacomp import le_compress, le_decompress, le_scan, lz_compress, lz_decompress, scan  # noqa: E402
from gfxcover import rows  # noqa: E402
from jp_cells import leftover  # noqa: E402
from romdiff import check  # noqa: E402
from strscan import BANKS  # noqa: E402
from tbl import Table  # noqa: E402

ROM = next(iter((ROOT / "rom").glob("*.gba")), None) if (ROOT / "rom").is_dir() else None
needs_rom = pytest.mark.skipif(ROM is None, reason="no ROM")
FREE = 0x3A8600  # candidate free space, docs/re/rom-map.md


@needs_rom
def test_identity_build():
    orig = ROM.read_bytes()
    img = build(orig, jp_script())
    assert bytes(img.out) == orig
    assert check(orig, bytes(img.out), set(), img.writes)[0] == []
    assert sum(who.startswith("textptr") for *_, who in img.writes) == 886  # 810 script, 35 code, 41 sign


@needs_rom
def test_jp_cells_sees_blank_lines_and_passes_the_real_build():
    orig = ROM.read_bytes()
    entries = load_script()
    assert leftover(orig, build(orig, entries).out, entries) == []
    blanked = [dict(e, en="") if e["id"] in ("m100", "m159", "s000") else e for e in entries]
    assert sorted(leftover(orig, build(orig, blanked).out, blanked)) == ["m100", "m159", "s000"]


# Words outside the banks that aim into them once flag bits are masked, read as chance matches: 13 are code or sample
# data, the last 2 sit in packed blocks. A new one means a pointer form the extractor missed.
CHANCE_WORDS = {0x3A368, 0x6560C, 0xAE5B8, 0xE331C, 0x112974, 0x120D80, 0x158DF8, 0x15D360, 0x172E98, 0x17B5BC, 0x185640, 0x19348C, 0x194078, 0x20DEA4, 0x358064}


@needs_rom
def test_no_flagged_pointer_into_the_banks_is_left_unowned():
    orig = ROM.read_bytes()
    owned = {w for words in text_slots(orig).values() for w in words}
    hits = set()
    for at in range(0, len(orig) - 3, 4):
        t = (int.from_bytes(orig[at:at + 4], "little") & 0x0FFFFFFF) - 0x08000000
        if any(lo <= t < hi for lo, hi in BANKS) and not any(lo <= at < hi for lo, hi in BANKS):
            hits.add(at)
    assert hits - owned == CHANCE_WORDS


def thumb_branch_target(rom, at):
    """Where the Thumb B, Bcc or BL at `at` lands, else None."""
    op = int.from_bytes(rom[at:at + 2], "little")
    if op >> 8 in range(0xD0, 0xDE):
        return at + 4 + (((op & 0xFF) ^ 0x80) - 0x80) * 2
    if op >> 11 == 0x1C:
        return at + 4 + (((op & 0x7FF) ^ 0x400) - 0x400) * 2
    low = int.from_bytes(rom[at + 2:at + 4], "little")
    if op >> 11 == 0x1E and low >> 11 == 0x1F:
        return at + 4 + ((((op & 0x7FF) ^ 0x400) - 0x400) << 12) + (low & 0x7FF) * 2
    return None


@needs_rom
def test_english_build_writes_only_where_it_should():
    orig = ROM.read_bytes()
    entries = load_script()
    img = build(orig, entries)
    assert check(orig, bytes(img.out), set(), img.writes)[0] == []
    slots = {w for words in text_slots(orig).values() for w in words}
    allowed = slots | {ERROR_SLOT} | {off for off, *_ in GLYPH_LOADS}
    allowed |= {int(r["word"], 16) - 12 for e in entries if e["id"] in KEEP_ON_SCREEN for r in e["refs"]}
    assert [off for off, *_ in img.writes if off < TEXT_BASE and off not in allowed] == []
    # every string written, and every pointer aimed at its own string
    assert len(img.where) == len(entries)
    offsets = {int(e["offset"], 16): e["id"] for e in entries}
    for old, words in text_slots(orig).items():
        for w in words:
            assert int.from_bytes(img.out[w:w + 4], "little") - 0x08000000 == img.where[offsets[old]][1]


@needs_rom
def test_keep_on_screen_args_were_clear():
    orig = ROM.read_bytes()
    img = build(orig, load_script())
    assert sum(who.startswith("keep on screen") for *_, who in img.writes) == len(KEEP_ON_SCREEN)  # each line is set once


@needs_rom
def test_glyph_hooks_swallow_no_branch_target():
    orig = ROM.read_bytes()
    for off, was, _ in GLYPH_LOADS:
        for at in range(off - 4096, off + 4096, 2):
            target = thumb_branch_target(orig, at)
            assert target is None or not off < target < off + len(was), f"{at:#x} lands inside the hook at {off:#x}"


def test_thumb_branch_target():
    assert thumb_branch_target(bytes.fromhex("fee7"), 0) == 0  # b .
    assert thumb_branch_target(bytes.fromhex("00d0"), 0) == 4  # beq
    assert thumb_branch_target(bytes.fromhex("00f0 01f8".replace(" ", "")), 0) == 6  # bl
    assert thumb_branch_target(bytes.fromhex("0020"), 0) is None  # movs


@needs_rom
def test_moved_text_reads_the_same_through_every_pointer():
    orig = ROM.read_bytes()
    codec = Table.load(ROOT / "tbl/jp.tbl")
    slots = text_slots(orig)
    img = Image(orig)
    repack_text(img, slots, codec, jp_script(), FREE)
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
