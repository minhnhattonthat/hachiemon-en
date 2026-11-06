"""Recon facts the later phases build on. ROM-dependent tests skip when the dump is absent."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gbacomp import lz_compress, lz_decompress, scan  # noqa: E402
from strscan import BANKS, table, walk  # noqa: E402
from tbl import Table  # noqa: E402

ROM = next(iter((ROOT / "rom").glob("*.gba")), None) if (ROOT / "rom").is_dir() else None
needs_rom = pytest.mark.skipif(ROM is None, reason="no ROM")


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
