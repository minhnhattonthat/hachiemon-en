"""Phase 4: script/ holds every string, byte-exact, and the VMs own every text pointer in the script regions."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build import BANKS, ERROR_SLOT, ERROR_STRING, GLYPH_LOADS, SIZE_EN, STRAY, TEXT_BASE, build, jp_script, load_script, real_slots, strings, text_slots  # noqa: E402
from extract import entries  # noqa: E402
from romdiff import check  # noqa: E402
from tbl import Table  # noqa: E402
from vmscript import BASE, TALK, scripts, script_words, stage_starts, u32, walk  # noqa: E402
from vwf import MAX_CELLS, Stream, cells_of, encode_en, load_font  # noqa: E402

ROM = next(iter((ROOT / "rom").glob("*.gba")), None) if (ROOT / "rom").is_dir() else None
needs_rom = pytest.mark.skipif(ROM is None, reason="no ROM")
CODEC = Table.load(ROOT / "tbl/jp.tbl")


def word(n):
    return n.to_bytes(4, "little")


def test_walk_follows_lengths_and_stops_at_end():
    data = b"".join(word(x) for x in (2, 0x8F, 0, 1, 4))
    assert walk(data, 0, TALK) == [(0, 2, 1), (4, 0x8F, 2), (12, 1, 1)]


def test_walk_refuses_an_opcode_the_vm_would_not_run():
    with pytest.raises(ValueError, match="bad opcode 0x9b"):
        walk(word(0x9B) + word(4), 0, TALK)


@needs_rom
def test_every_string_roundtrips():
    rom = ROM.read_bytes()
    for e in load_script():
        off = int(e["offset"], 16)
        data = CODEC.encode(e["jp"])
        assert rom[off:off + len(data)] == data, e["id"]
        assert CODEC.decode(data)[1] == len(data), e["id"]  # exactly one {end}, at the end


@needs_rom
def test_strings_cover_the_banks_with_no_gap():
    spans = sorted((int(e["offset"], 16), int(e["offset"], 16) + len(CODEC.encode(e["jp"]))) for e in load_script())
    assert spans[0][0] == BANKS[0][0] and spans[-1][1] == BANKS[1][1]
    gaps = [(a[1], b[0]) for a, b in zip(spans, spans[1:]) if a[1] != b[0]]
    assert gaps == sorted([(BANKS[0][1], BANKS[1][0]), *STRAY.items()])  # only the space between banks and the stray byte


@needs_rom
def test_script_file_matches_the_rom():
    rom = ROM.read_bytes()
    fresh = entries(rom, CODEC, strings(rom))
    saved = load_script()
    assert [(e["id"], e["offset"], e["jp"], e["refs"]) for e in saved] == [
        (e["id"], e["offset"], e["jp"], e["refs"]) for name in ("signs", "main") for e in fresh[name]]


@needs_rom
def test_every_script_reaches_its_end_and_every_row_slot_is_owned():
    rom = ROM.read_bytes()
    assert len(stage_starts(rom)) == 14
    names = scripts(rom)
    assert len(names) == 96  # 88 table entries, 6 of them stage format, plus the 14 stage scripts
    words = script_words(rom)
    assert len(words) == 810
    assert {w["op"] for w in words.values()} == {"AF", "8E"}


@needs_rom
def test_owned_slots_equal_every_pointer_a_value_scan_finds():
    """Two independent routes to the same words: the structures, and the old value scan they replace."""
    rom = ROM.read_bytes()
    owned = text_slots(rom)
    by_value = real_slots(rom)
    starts = set(strings(rom))
    assert set(owned) <= starts
    for s in starts:
        assert sorted(owned.get(s, [])) == sorted(by_value.get(s, [])), hex(s)


@needs_rom
def test_english_moves_only_what_it_should():
    rom = ROM.read_bytes()
    script = jp_script()
    edited = next(e for e in script if e["refs"] and e["jp"].endswith("{end:02}"))
    edited["en"] = "HELLO{end:02}"
    img = build(rom, script)
    assert check(rom, bytes(img.out), set(), img.writes)[0] == []
    cells, data = encode_en(edited["en"], load_font(), rom)
    for r in edited["refs"]:
        new = u32(img.out, int(r["word"], 16)) - BASE
        assert new >= TEXT_BASE and img.out[new:new + len(data)] == data
        assert img.out[new - len(cells):new] == cells
    other = next(e for e in script if e["refs"] and e is not edited)
    new = u32(img.out, int(other["refs"][0]["word"], 16)) - BASE
    raw = CODEC.encode(other["jp"])
    drawn = [b for b in raw[:-2] if b not in (0xFD, 0xFE)]
    shown = [b for b in img.out[new:new + len(raw) - 2] if b not in (0xFD, 0xFE)]
    assert [img.out[new - (b + 1) * 64:new - b * 64] for b in shown] == [rom[0x2FFC50 + b * 64:0x2FFC50 + (b + 1) * 64] for b in drawn]


@needs_rom
def test_english_build_patches_exactly_the_two_glyph_loads():
    rom = ROM.read_bytes()
    script = jp_script()
    script[0]["en"] = "HELLO{end:02}"
    out = build(rom, script).out
    assert len(out) == SIZE_EN
    for off, _, now in GLYPH_LOADS:
        assert out[off:off + len(now)] == now
    assert rom.count((BASE + 0x2FFC50).to_bytes(4, "little"), 0, 0x80000) == 2  # no third reader of the font
    new = u32(out, ERROR_SLOT) - BASE
    assert new >= TEXT_BASE and out[new:new + 2] != rom[ERROR_STRING:ERROR_STRING + 2]


def test_rendered_line_layout():
    font = load_font()
    rom = ROM.read_bytes() if ROM else bytes(0x300000 + 256 * 64)
    cells, data = encode_en("Hi{nl}Hi{page}♥{end:01}", font, rom)
    assert data[-2:] == b"\xff\x01" and data.count(0xFE) == 1 and data.count(0xFD) == 1
    assert len(cells) % 64 == 0
    assert cells_of(data)[1:] == (2, 2)
    with pytest.raises(ValueError):
        encode_en("no end code", font, rom)
    with pytest.raises(ValueError):
        encode_en("x{end:00}y", font, rom)


def test_cell_limit_raises():
    stream = Stream()
    for n in range(MAX_CELLS + 1):
        stream.cell(n.to_bytes(64, "little"))
    with pytest.raises(ValueError):
        stream.packed()
