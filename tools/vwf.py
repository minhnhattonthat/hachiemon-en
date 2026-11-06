"""Pre-rendered proportional text. See docs/re/text.md, English text.

The game draws one 8x16 cell per text byte and sizes bubbles from the byte count. So the build renders each English
line to pixels, slices it into 8 px cells and stores those cells directly before the string. A text byte b then means
"the cell at string - (b + 1) * 64": two 6-byte code patches, no new code, no new RAM, and every layout rule of the
game (line breaks, pages, bubble size, reveal) keeps working on cells.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "tbl/vwf_font.txt"
GAME_FONT, CELL = 0x2FFC50, 64
PAPER, SHADOW, INK = 1, 2, 4  # the palette indices the game's own glyphs use
HEART = 0xF9  # the game's own glyph cell for ♥
MAX_CELLS = 0xFD  # byte values FD, FE, FF are control codes
TOKEN = re.compile(r"\{nl\}|\{page\}|\{end:([0-9A-Fa-f]{2})\}")
NL, PAGE, END = 0xFE, 0xFD, 0xFF


def load_font(path=FONT):
    """char -> (advance, rows of '#'/'.')"""
    font, lines = {}, [ln for ln in Path(path).read_text(encoding="utf8").splitlines() if not ln.startswith("# ")]
    for i in range(0, len(lines), 17):
        _, code, adv = lines[i].split()
        font[chr(int(code))] = (int(adv), lines[i + 1:i + 17])
    return font


def _game_glyph(rom, code):
    """A game font cell as rows of palette indices."""
    data = rom[GAME_FONT + code * CELL:GAME_FONT + (code + 1) * CELL]
    return [[(data[y * 4 + x // 2] >> (4 * (x & 1))) & 15 for x in range(8)] for y in range(16)]


def line_width(text, font):
    """Pixel width of one line, including the 1 px shadow of its last letter."""
    return sum(8 if ch == "♥" else font[ch][0] for ch in text) + 1 if text else 0


def render_line(text, font, rom):
    """One line as 16 rows of palette indices."""
    width = line_width(text, font)
    canvas = [[PAPER] * width for _ in range(16)]
    x = 0
    for ch in text:
        if ch == "♥":
            for y, row in enumerate(_game_glyph(rom, HEART)):
                canvas[y][x:x + 8] = row
            x += 8
            continue
        adv, rows = font[ch]
        for y, row in enumerate(rows):
            for gx, px in enumerate(row):
                if px == "#":
                    canvas[y][x + gx] = INK
                    if x + gx + 1 < width and canvas[y][x + gx + 1] == PAPER:
                        canvas[y][x + gx + 1] = SHADOW
                    if y < 15 and canvas[y + 1][x + gx] == PAPER:
                        canvas[y + 1][x + gx] = SHADOW
        x += adv
    return canvas


def slice_cells(canvas):
    """A line's canvas as 8 px cells in the game's layout: top tile, bottom tile, low nibble first."""
    width = len(canvas[0]) if canvas else 0
    cells = []
    for cx in range(0, width, 8):
        cell = bytearray()
        for row in canvas:
            part = row[cx:cx + 8] + [PAPER] * (8 - len(row[cx:cx + 8]))
            cell += bytes(part[i] | part[i + 1] << 4 for i in range(0, 8, 2))
        cells.append(bytes(cell))
    return cells


class Stream:
    """The text bytes of one string plus its cell list, sharing identical cells."""

    def __init__(self):
        self.cells, self.index, self.data = [], {}, bytearray()

    def cell(self, raw):
        if raw not in self.index:
            self.index[raw] = len(self.cells)
            self.cells.append(raw)
        self.data.append(self.index[raw])

    def packed(self):
        """Cells in reverse order followed by the string, so that cell b sits at string - (b + 1) * 64."""
        if len(self.cells) > MAX_CELLS:
            raise ValueError(f"{len(self.cells)} different cells, the limit is {MAX_CELLS}")
        return b"".join(reversed(self.cells)), bytes(self.data)


def encode_en(text, font, rom):
    """Table-style English (with {nl} {page} {end:MM}) to (cell block, string bytes)."""
    stream, pos = Stream(), 0

    def line(chunk):
        for raw in slice_cells(render_line(chunk, font, rom)):
            stream.cell(raw)

    ended = False
    for m in TOKEN.finditer(text):
        if ended:
            raise ValueError(f"text after the end code: {text!r}")
        line(text[pos:m.start()])
        pos = m.end()
        if m.group(0) == "{nl}":
            stream.data.append(NL)
        elif m.group(0) == "{page}":
            stream.data.append(PAGE)
        else:
            stream.data += bytes((END, int(m.group(1), 16)))
            ended = True
    if not ended or pos != len(text):
        raise ValueError(f"no end code, or text after it: {text!r}")
    return stream.packed()


def encode_raw(data, rom):
    """Original Japanese string bytes to (cell block, string bytes): the same text, its glyphs copied from the game font."""
    stream, i = Stream(), 0
    while i < len(data):
        b = data[i]
        if b == END:
            stream.data += data[i:i + 2]
            break
        if b in (NL, PAGE):
            stream.data.append(b)
        else:
            stream.cell(bytes(rom[GAME_FONT + b * CELL:GAME_FONT + (b + 1) * CELL]))
        i += 1
    return stream.packed()


def tile_cells(data):
    """Tile cells a bubble reserves for the bubble opened after it: +0x27 in the measure routine, rows * cols + the last
    line's cells. That is one row more than it shows, so a second bubble's tiles start further on than its sprite slots."""
    cols, rows, _ = cells_of(data)
    return rows * cols + len(data[data.rfind(PAGE) + 1:data.index(END)].rsplit(bytes([NL]), 1)[-1])


def cells_of(data):
    """Layout the game computes from the string bytes: (columns, rows, pages), as its measure routine 0x8038660 does.
    It counts a page break as one more cell on its line, so a line ending in {page} costs a column."""
    cols = rows = run = row = 0
    pages = 1
    for b in data:
        if b == END:
            break
        if b == PAGE:
            pages += 1
            cols, run, row = max(cols, run + 1), 0, 0
        elif b == NL:
            cols, run = max(cols, run), 0
            row += 1
            rows = max(rows, row)
        else:
            run += 1
    return max(cols, run), rows + 1, pages
