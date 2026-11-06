"""English lettering for graphics text: redraw labels inside packed tile sheets. docs/re/graphics.md lists the rows.

A label says which tiles make up its picture, the words, and which rectangle to clear. The build unpacks each block,
redraws its labels, packs it again past the text and repoints the slots of the structures that own it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gbacomp import le_compress, le_decompress, lz_compress, lz_decompress
from vwf import load_font

GFX_BASE = 0x600000  # past the longest text can get (docs/re/text.md, English text: 0x52FD34 with every string at its limit)
ROWS_16 = {  # tables of {block, VRAM dest, 0, 0}: docs/re/graphics.md, Block pointers
    "row4_5": (0x79010, 0x790D0), "row6": (0x7EC10, 0x7EC80), "row16": (0x77A2C, 0x77B0C), "row17": (0x7A6F4, 0x7AB94), "row18": (0x7C978, 0x7CDF8),
}
CODE_LITERALS = [0x3D74, 0x71E8, 0x71E0, 0x28D0, 0x71F0, 0x863C, 0x71D8, 0x71F8, 0x24F0, 0x24F8, 0x3454, 0x10CF8, 0x2E850]  # the Le rows' loaders
WORD_SLOTS = [*range(0x1D5F5C, 0x1D6454, 4), *range(0x1A3D10, 0x1A3D38, 4), *CODE_LITERALS]  # OBJ and BG set tables (flow.md), VS table


def owned_slots(rom):
    """block offset -> pointer words, from the tables that own the graphics rows' pointers."""
    words = [*WORD_SLOTS, *(w for lo, hi in ROWS_16.values() for w in range(lo, hi + 1, 16))]
    slots = {}
    for w in words:
        value = int.from_bytes(rom[w:w + 4], "little")
        if 0x08000000 <= value < 0x09000000:
            slots.setdefault(value - 0x08000000, []).append(w)
    return slots


def spr(start, w, h, n=1):
    """n sprites of w x h px side by side, tiles one after another (1D mapping): a grid of tile numbers."""
    cols, rows = w // 8, h // 8
    return [[start + s * cols * rows + y * cols + x for s in range(n) for x in range(cols)] for y in range(rows)]


def rows(start, cols, count):
    """A picture stored row after row."""
    return [[start + y * cols + x for x in range(cols)] for y in range(count)]


class Picture:
    """A tile grid over a 4bpp sheet, addressed in pixels."""

    def __init__(self, data, grid):
        self.data, self.grid = data, grid
        self.w, self.h = len(grid[0]) * 8, len(grid) * 8

    def _at(self, x, y):
        return self.grid[y // 8][x // 8] * 32 + (y & 7) * 4 + (x & 7) // 2

    def get(self, x, y):
        return self.data[self._at(x, y)] >> (4 * (x & 1)) & 15

    def set(self, x, y, v):
        at, shift = self._at(x, y), 4 * (x & 1)
        self.data[at] = self.data[at] & (0xF0 >> shift) | v << shift


def text_rows(text, bold=False, scale=1):
    """One line as rows of booleans, trimmed to its ink."""
    font = load_font()
    rows16 = [[False] * sum(font[ch][0] + bold for ch in text) for _ in range(16)]
    x = 0
    for ch in text:
        adv, glyph = font[ch]
        for y, row in enumerate(glyph):
            for gx, px in enumerate(row):
                if px == "#":
                    rows16[y][x + gx] = True
                    if bold:
                        rows16[y][x + gx + 1] = True
        x += adv + bold
    rows16 = [r for r in rows16 if any(r)]
    left = min(r.index(True) for r in rows16)
    right = max(len(r) - r[::-1].index(True) for r in rows16)
    rows16 = [r[left:right] for r in rows16]
    return [[px for px in r for _ in range(scale)] for r in rows16 for _ in range(scale)]


def letter(pic, text, clear=None, ink=None, outline=None, bold=False, scale=1, gap=1, center=None):
    """Clear `clear` (x0, y0, x1, y1; default the whole picture) to its commonest colour, then draw `text` centred in it.
    `ink` defaults to the rectangle's second commonest colour. Lines split on a newline."""
    x0, y0, x1, y1 = clear or (0, 0, pic.w, pic.h)
    counts = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            counts[pic.get(x, y)] = counts.get(pic.get(x, y), 0) + 1
    order = sorted(counts, key=counts.get, reverse=True)
    paper = order[0]
    ink = order[1] if ink is None else ink
    for y in range(y0, y1):
        for x in range(x0, x1):
            pic.set(x, y, paper)
    lines = [text_rows(ln, bold, scale) for ln in text.split("\n")]
    height = sum(len(ln) for ln in lines) + gap * (len(lines) - 1)
    cx, y = center if center is not None else (x0 + x1) // 2, (y0 + y1 - height) // 2
    if height > y1 - y0 or y < 0:
        raise ValueError(f"{text!r} is {height} px tall in {y1 - y0}")
    for ln in lines:
        width = len(ln[0])
        x = cx - width // 2
        if x < x0 or x + width > x1:
            raise ValueError(f"{text!r} is {width} px wide in {x1 - x0}")
        for ry, row in enumerate(ln):
            for rx, on in enumerate(row):
                if on:
                    if outline is not None:
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                px, py = x + rx + dx, y + ry + dy
                                if 0 <= px < pic.w and 0 <= py < pic.h and pic.get(px, py) != ink:
                                    pic.set(px, py, outline)
                    pic.set(x + rx, y + ry, ink)
        y += len(ln) + gap


def pill(start, text, **kw):
    """A 96x16 menu pill, three 32x16 sprites; the digit sprites of a save slot sit over its right part."""
    return (spr(start, 32, 16, 3), text, {"clear": (6, 1, 90, 15), "bold": True, **kw})


def disc(start, text):
    return (spr(start, 32, 32), text, {"clear": (4, 8, 28, 24), "bold": True})


def strip(text):
    """A menu help strip: 15 x 3 tiles."""
    return (rows(0, 15, 3), text, {"clear": (1, 0, 119, 24), "gap": 0})


def header(text):
    """A menu header: 16 x 2 tiles on an orange pill."""
    return (rows(0, 16, 2), text, {"clear": (12, 1, 116, 15), "bold": True})


LABELS = {
    0x2BCD3C: [
        pill(0x060, "Main Game"), pill(0x078, "Options"), pill(0x090, "Music"), pill(0x0A8, "Sound FX"),
        pill(0x0C0, "Normal"), pill(0x0D8, "Hard"), pill(0x0F0, "Very Hard"),
        pill(0x108, "Stage", center=40), pill(0x120, "Lips", center=40),
        pill(0x279, "New Game"), pill(0x291, "Continue"), pill(0x2C1, "Lives", center=40),
        pill(0x2D9, "Delete Data"), pill(0x2F1, "You sure?"), pill(0x309, "Main Game"), pill(0x333, "Clear~"),
        disc(0x040, "On"), disc(0x050, "Off"), disc(0x255, "Yes"), disc(0x265, "No"), disc(0x323, "Yes"),
    ],
    0x30E2E0: [strip("Pick something\nfrom the menu~")],
    0x30E61C: [strip("Let's go exploring\ntogether!")],
    0x30E944: [strip("You can change\nthe settings~")],
    0x30EC44: [strip("Still haven't\npicked yet~?")],
    0x30EED0: [strip("Music on or off,\nyour call.")],
    0x30F284: [strip("Sound effects on\nor off, your call.")],
    0x30F64C: [strip("Pick a save file~")],
    0x30F980: [strip("Pick a difficulty~")],
    0x30FC44: [strip("Clearing a stage\nwipes old data. OK?")],
    0x3100DC: [header("Menu")],
    0x31031C: [header("Options")],
    0x3105B8: [header("Difficulty")],
    0x310810: [header("Save File!")],
}


def unpack(rom, off):
    """(bytes, codec) of a packed block."""
    if rom[off] == 0x10:
        return bytearray(lz_decompress(rom, off)[0]), lz_compress
    return bytearray(le_decompress(rom, off)[0]), le_compress


def relabel(rom, off, labels=None):
    """A block's bytes with its labels redrawn, packed again."""
    data, pack = unpack(rom, off)
    for grid, text, kw in LABELS[off] if labels is None else labels:
        letter(Picture(data, grid), text, **kw)
    return pack(bytes(data))


def write_labels(img, rom, base=GFX_BASE):
    """Move every relabelled block past the text. Every block must have an owned slot."""
    slots, at = owned_slots(rom), base
    for off in sorted(LABELS):
        if off not in slots:
            raise ValueError(f"graphics block {off:#x} has no owned slot")
        block = relabel(rom, off)
        block += b"\xff" * (-len(block) % 4)
        img.write(at, block, f"gfx {off:#x}")
        for w in slots[off]:
            img.write(w, (0x08000000 + at).to_bytes(4, "little"), f"gfxptr {off:#x}")
        at += len(block)
