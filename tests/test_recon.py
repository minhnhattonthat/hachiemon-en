"""Recon facts the later phases build on. ROM-dependent tests skip when the dump is absent."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gbacomp import le_decompress, le_scan, lz_compress, lz_decompress, scan  # noqa: E402
from strscan import BANKS, table, walk  # noqa: E402
from tbl import Table  # noqa: E402

ROM = next(iter((ROOT / "rom").glob("*.gba")), None) if (ROOT / "rom").is_dir() else None
needs_rom = pytest.mark.skipif(ROM is None, reason="no ROM")


def test_gfxcover_reads_ranges_and_skips_palettes():
    sys.path.insert(0, str(ROOT / "tools" / "debug"))
    from gfxcover import rows
    by_row = {n: spans for n, _, spans in rows()}
    assert (0x38D664, 0x39106C) in by_row[17]
    assert by_row[20] == [(0x2D1EC4, 0x2D1EC4)]  # its palette is copied, not unpacked


def test_tour_lists_the_generated_scenes():
    sys.path.insert(0, str(ROOT / "tools" / "debug"))
    from tour import scene_names
    names = scene_names()
    assert {"stage28", "talk29", "help8", "save_error", "vs6"} <= set(names)
    assert "talk00" not in names and "talk30" not in names
    assert len(names) == len(set(names))


def test_lz_roundtrip_synthetic():
    data = bytes(range(256)) * 3 + b"\x00" * 300 + b"abcabcabc"
    packed = lz_compress(data)
    assert lz_decompress(packed)[0] == data


def test_lz_rejects_bad_backreference():
    with pytest.raises(ValueError):
        lz_decompress(b"\x10\x10\x00\x00\x80\x00\x05" + b"\x00" * 16)


@needs_rom
def test_lz_roundtrip_real_blocks():
    rom = ROM.read_bytes()
    hits = scan(rom)
    assert len(hits) > 1000
    small = [off for off, _, size in hits if size < 0x400][:40]  # the greedy Python compressor is slow on big blocks
    assert small
    for off in small:
        data, _ = lz_decompress(rom, off)
        assert lz_decompress(lz_compress(data))[0] == data


def test_le_ops():
    # literals "ABC" (op 3), one literal "D" (op 2), short copy dist 2 len 2 (op 1, byte 0x01), long copy dist 5 len 3 (op 0)
    block = b"Le\x09\x00\x00\x00" + bytes([0b00011011]) + b"ABC" + b"D" + b"\x01" + b"\x00\x00"
    assert le_decompress(block)[0] == b"ABCDCDBCD"


@needs_rom
def test_le_blocks_decode_and_abut():
    rom = ROM.read_bytes()
    hits = le_scan(rom)
    assert len(hits) == 1336
    assert hits[0][0] == 0x1EA284 and hits[-1][0] + hits[-1][1] == 0x2B4AE3
    # A wrong decoder walks off the stream; nearly every block must end where the next one starts (4-aligned).
    abut = sum((a[0] + a[1] + 3) & ~3 == b[0] for a, b in zip(hits, hits[1:]))
    assert abut > 1200


@needs_rom
def test_known_string_decodes():
    """The opening narration, as seen on screen in the emulator."""
    rom = ROM.read_bytes()
    t = table()
    text = "".join(t[b] for b in rom[0x1D9554:0x1D9554 + 7])
    assert text == "ハチエモンと "


def test_table_control_codes_keep_the_mode_byte():
    tbl_path = ROOT / "tbl" / "jp.tbl"
    t = Table.load(tbl_path)
    text, used = t.decode(bytes([0x69, 0xFE, 0x60, 0xFD, 0xEA, 0xFF, 0x02, 0x00]))
    assert used == 7  # stops after FF and its mode byte, not at the next string
    assert t.encode(text) == bytes([0x69, 0xFE, 0x60, 0xFD, 0xEA, 0xFF, 0x02])


@needs_rom
def test_banks_walk_with_the_grammar():
    rom = ROM.read_bytes()
    t = table()
    strs, _ = walk(rom, *BANKS[1], t)
    assert len(strs) > 850
    assert all(rom[e - 2] == 0xFF and rom[e - 1] in (0, 1, 2) for _, e, _ in strs)
