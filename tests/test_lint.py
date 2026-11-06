"""The text lint catches what a player would see: too wide, too many rows, over the cell budget, wrong end code."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from lint import check_entry, lint, load_glossary, load_limits, size  # noqa: E402
from vwf import cells_of, encode_en, load_font, tile_cells  # noqa: E402

FONT = load_font()
ROM = bytes(0x300000 + 256 * 64)
BUBBLE = {"kind": "bubble", "cols": 12, "rows": 2, "cells": 65, "room": 56, "with": [], "source": "measured"}
BOX = {"kind": "box", "cols": 23, "rows": 2, "cells": 0, "room": 0, "with": [], "source": "measured"}
SIGN = {"kind": "sign", "cols": 14, "rows": 2, "cells": 28, "room": 28, "with": [], "source": "measured"}


def errs(en, limit=BUBBLE, jp="あ{end:00}", glossary=(), sizes=None):
    return check_entry({"id": "x", "jp": jp, "en": en}, limit, FONT, ROM, list(glossary), sizes)


def test_a_line_inside_its_limits_passes():
    assert errs("Hello there!{end:00}") == []
    assert errs("Hello{nl}there!{page}Bye.{end:00}") == []


def test_width_counts_cells_and_the_page_break():
    assert any("cols" in e for e in errs("x" * 40 + "{end:00}"))
    wide = "n" * 13  # 13 letters of 7 px: 92 px, 12 cells; the page break makes 13, even 14
    assert not any("cols" in e for e in errs(wide + "{end:00}"))
    assert any("cols" in e for e in errs(wide + "{page}x{end:00}"))


def test_the_box_has_no_page_break_cost():
    line = "n" * 26  # 183 px: 23 cells
    assert errs(line + "{page}x{end:00}", BOX) == []
    assert any("cols" in e for e in errs("n" * 27 + "{end:00}", BOX))


def test_rows_and_the_shared_cell_budget():
    assert any("rows" in e for e in errs("a{nl}b{nl}c{end:00}"))
    shared = dict(BUBBLE, **{"with": ["y"]})
    assert any("ERROR" in e for e in errs("Hello{nl}there{end:00}", shared, sizes={"y": (64, 0)}))
    assert any("paint over" in e for e in errs("Hello{nl}there{end:00}", shared, sizes={"y": (0, 64)}))


def test_a_bubble_reserves_a_row_more_than_it_shows():
    _, data = encode_en("Hello there{nl}Hello there{end:00}", FONT, ROM)
    cols, rows, _ = cells_of(data)
    assert tile_cells(data) == rows * cols + cols
    _, short = encode_en("Hello there{nl}Hi{end:00}", FONT, ROM)
    assert tile_cells(short) == 2 * cells_of(short)[0] + 2  # "Hi" spans two cells


def test_sign_budget():
    assert errs("Hello{nl}there{end:00}", SIGN) == []
    assert any("cols" in e for e in errs("n" * 18 + "{end:00}", SIGN))


def test_control_codes_and_characters():
    assert any("end code" in e for e in errs("Hi{end:02}"))
    assert any("no {end" in e for e in errs("Hi"))
    assert any("Japanese" in e for e in errs("あ{end:00}"))
    assert any("glyph" in e for e in errs("café{end:00}"))
    assert any("blank" in e for e in errs(" Hi{end:00}"))
    assert any("ordinal" in e for e in errs("{nl}th{end:00}"))


def test_glossary_rows_are_binding():
    rows = [("ハチエモン", "Hachiemon", ["Hatiemon"])]
    assert errs("Hachiemon!{end:00}", jp="ハチエモン{end:00}", glossary=rows) == []
    assert any("should be" in e for e in errs("Him!{end:00}", jp="ハチエモン{end:00}", glossary=rows))
    assert any("avoid" in e for e in errs("Hatiemon, Hachiemon{end:00}", jp="ハチエモン{end:00}", glossary=rows))
    assert ("ハチエモン", "Hachiemon", ["Hachi-emon", "Hatiemon"]) in load_glossary()


def test_a_name_may_wrap_and_overrides_sit_on_the_limits():
    rows = [("マッスルハチエモン", "Muscle Hachiemon", [])]
    assert errs("I am Muscle{nl}Hachiemon!{end:00}", jp="マッスルハチエモン{end:00}", glossary=rows) == []
    assert load_limits()["m034"]["cols"] == 12  # 8 in the generated tbl/limits.tsv; the build pulls it in (D15)


def test_size_helper_matches_engine_rule():
    _, data = encode_en("Hi{page}Hi{end:00}", FONT, ROM)
    assert size(data, "bubble")[0] == size(data, "box")[0] + 1


def test_untranslated_lines_fail_only_in_final():
    entries = [{"id": "m000", "jp": "あ{end:00}", "en": ""}]
    assert lint(entries, ROM) == ([], 1)
    assert lint(entries, ROM, final=True)[0] == [("m000", "untranslated")]
