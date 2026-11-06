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
CODE_LITERALS = [0x3D74, 0x71E8, 0x71E0, 0x28D0, 0x71F0, 0x863C, 0x71D8, 0x71F8, 0x24F0, 0x24F8, 0x3454, 0x10CF8, 0x2E850,  # the Le rows' loaders
                 0x2F20, 0x2F3C, 0x2F54, 0x862C, 0x2F64, 0x2FE4, 0x8634,  # 発, 目 at the stage start
                 0x3500, 0x10D00, 0x3D7C]  # the banners' maps
STAGE_SETS = 0x1A61C4  # 16 rows of {stage tileset, second block}: docs/re/graphics.md, Stage signs
WORD_SLOTS = [*range(0x1D5F5C, 0x1D6454, 4), *range(0x1A3D10, 0x1A3D60, 4), *range(STAGE_SETS, STAGE_SETS + 16 * 8, 8), *CODE_LITERALS]  # OBJ and BG set tables (flow.md), VS tiles and maps, stage tilesets


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


# 3x5 capitals for boards too small for the text font; own drawing, no licence issue. `wide` makes them 4x5 by doubling the middle column.
TINY = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'!-.", """
010101111101101 110101110101110 011100100100011 110101101101110 111100110100111 111100110100100 011100101101011 101101111101101 111010010010111
001001001101010 101101110101101 100100100100111 101111111101101 101111111111101 010101101101010 110101110100100 010101101111011 110101110101101
011100010001110 111010010010010 101101101101011 101101101010010 101101111111101 101101010101101 101101010010010 111001010100111
010101101101010 010110010010111 110001010100111 110001010001110 101101111001001 111100110001110 011100110101010 111001010010010 010101010101010
010101011001110 010010000000000 010010010000010 000000111000000 000000000000010
""".split()))


def tiny_rows(text, wide=False):
    """One line in TINY as rows of booleans; a space is 2 px."""
    out = [[] for _ in range(5)]
    for i, ch in enumerate(text):
        for y in range(5):
            cells = [False, False] if ch == " " else [c == "1" for c in TINY[ch][y * 3:y * 3 + 3]]
            if wide and ch == "N":  # doubling the column turns this one into an H
                cells = [c == "1" for c in ("1001", "1101", "1011", "1001", "1001")[y]]
            elif wide and ch != " ":
                cells.insert(1, cells[1])
            out[y] += ([False] if i else []) + cells
    return out


def letter(pic, text, clear=None, ink=None, outline=None, bold=False, scale=1, gap=1, center=None, prep=None, keep=False, paper=None, tiny=None):
    """Clear `clear` (x0, y0, x1, y1; default the whole picture) to `paper`, by default its commonest colour, then draw `text` centred in it.
    `ink` defaults to the rectangle's second commonest colour. Lines split on a newline. `prep(pic)` runs first; `keep` skips the clearing.
    `tiny` draws in TINY capitals instead of the text font: "narrow" or "wide"."""
    if prep:
        prep(pic)
    x0, y0, x1, y1 = clear or (0, 0, pic.w, pic.h)
    counts = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            counts[pic.get(x, y)] = counts.get(pic.get(x, y), 0) + 1
    order = sorted(counts, key=counts.get, reverse=True)
    paper = order[0] if paper is None else paper
    ink = order[1] if ink is None else ink
    for y in range(y0, y1):
        for x in range(x0, x1):
            if not keep:
                pic.set(x, y, paper)
    if not text:
        return
    lines = [tiny_rows(ln, tiny == "wide") if tiny else text_rows(ln, bold, scale) for ln in text.split("\n")]
    if tiny and scale > 1:
        lines = [[[px for px in row for _ in range(scale)] for row in ln for _ in range(scale)] for ln in lines]
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
    def prep(pic):  # kana start at x 4; the pill's edge is too near for the whole clear rectangle
        for y in range(3, 13):
            pic.set(4, y, 0xE)
            pic.set(5, y, 0xE)
    return (spr(start, 32, 16, 3), text, {"clear": (6, 1, 90, 15), "bold": True, "prep": prep, **kw})


def disc(start, text):
    # The unselected disc is scaled to about 2/3, which drops pixel rows: the 8 px text font read "Utt", so double TINY capitals.
    return (spr(start, 32, 32), text, {"clear": (4, 8, 28, 24), "tiny": "narrow", "scale": 2})


def strip(text):
    """A menu help strip: 15 x 3 tiles."""
    return (rows(0, 15, 3), text, {"clear": (0, 0, 120, 24), "gap": 0, "center": 59})  # 59: the strip sits a pixel right of its bubble's middle


def header(text):
    """A menu header: 16 x 2 tiles on an orange pill."""
    return (rows(0, 16, 2), text, {"clear": (12, 1, 116, 15), "bold": True})


def shout(start, text, **kw):
    """One 32x32 cell of the title's Kantele shout. They settle 22 px apart, the first (x -31) off screen, so it stays blank.
    Two 9 px letters fill the 22 px pitch; the text font at double size overlapped its neighbours."""
    return (spr(start, 32, 32), text, {"clear": (0, 0, 32, 32), "ink": 0xF, "outline": 1, "scale": 3, "tiny": "narrow", "center": 21, **kw})


def blank_stamp(pic):
    """Row 6: a clean ellipse where the swaying kana were. They run to the ellipse's edge, so no rectangle clears them."""
    for y in range(pic.h):
        for x in range(pic.w):
            pic.set(x, y, 0xE if ((x - 23.5) / 24) ** 2 + ((y - 15.5) / 12.5) ** 2 <= 1 else 7)


def stamp(sway):
    """A frame of the menu's Kantele stamp: 6 x 4 tiles, top left of every menu. The old frames sway, so the word does too."""
    return (rows(0, 6, 4), "Kantele", {"prep": blank_stamp, "keep": True, "clear": (1, 8, 47, 24), "ink": 1, "center": 24 + sway})


def area(text):
    """A wooden area banner: twelve 8x16 sprites."""
    return (spr(0, 8, 16, 12), text, {"clear": (1, 1, 95, 15)})


def cell(start, text, **kw):
    """A 32x32 cell of big lettering on BG0 or a sprite: white with a dark edge."""
    return (spr(start, 32, 32), text, {"paper": 0, "ink": 7, "outline": 1, "scale": 2, "bold": True, **kw})  # a heavy glyph can outnumber the paper


def card(part, title, quota=True):
    """A stage card: "Part n", the title, and the lip quota beside the digit sprite at x 160, y 115."""
    ink = {"ink": 0xF, "outline": 1, "bold": True}
    return [
        ("", {"clear": (0, 0, 240, 160)}),
        (f"Part {part}", {**ink, "clear": (0, 24, 240, 40)}),
        (title, {**ink, "clear": (0, 42, 240, 104)}),
        ("Lip Quota", {**ink, "clear": (60, 114, 142, 130), "center": 104}),
    ]


def banner(text, **kw):
    """A word banner on BG0: white with a dark edge, double size."""
    return [(text, {"ink": 7, "outline": 1, "scale": 2, "bold": True, **kw})]


def blank_vs(pic):
    """The VS ellipse without the name: 224x32, pink 5 on clear 0. The old names ran past its edge, so no rectangle clears them. VS, left of x 72, stays."""
    for y in range(pic.h):
        for x in range(72, pic.w):
            pic.set(x, y, 5 if ((x - 112) / 112) ** 2 + ((y - 15.5) / 16) ** 2 <= 1 else 0)


def vs(text):
    """The right of a VS banner: a name, over the ellipse."""
    return [(text, {"prep": blank_vs, "keep": True, "clear": (72, 1, 188, 31), "ink": 0xD, "outline": 7, "bold": True, "gap": 0, "center": 140})]


def message(lines):
    """A white message screen: dark words on white, in the old lines' place."""
    return [(lines, {"clear": (0, 40, 240, 80), "ink": 1, "bold": True, "gap": 3})]


# はい and いいえ dim by palette on their map cells, so the words stay on those cells: x 72-104 and x 128-168.
YES_NO = [("", {"clear": (0, 88, 240, 120), "paper": 0xF}), ("Yes", {"clear": (72, 96, 104, 112), "ink": 1, "bold": True}), ("No", {"clear": (128, 96, 168, 112), "ink": 1, "bold": True})]

# Tile block -> (map block, labels on the flattened picture, tile limit). Most stay within the old count; banners may use BG0 up to its map at 0x3000.
BG0_TILES = (0x3000 - 0x1400) // 32
CARDS = {
    0x35CDA0: (0x35D820, 1, "That Darn Rascal\nwith the Red Lips"), 0x35DA14: (0x35E238, 2, "Bulging Muscles"), 0x35E3F8: (0x35EC98, 3, "Before We\nHead to Osaka"),
    0x35EE50: (0x35F7C8, 4, "Scarier\nThan Auntie"), 0x35F9A0: (0x3604D4, 5, "Melt the Ice!\nLips of Justice"), 0x3606DC: (0x360E94, 6, "It's Slippery, Though"),
    0x36103C: (0x3617AC, 7, "The Bee Returns"), 0x36194C: (0x362288, 8, "It Hurts When\nYou Poke Me"), 0x362458: (0x362DE4, 9, "Got a Hole?\nI Wanna Crawl In"),
    0x362FB0: (0x363944, 10, "The More You Dig,\nthe More Mole-san"), 0x363B14: (0x3644A8, 11, "Got a Hole?\nI Wanna Dive In"), 0x364678: (0x364F0C, 12, "Mother Nature\nand Hachiemon"),
    0x3650EC: (0x3659B8, 13, "Huff, Puff, Need Water!"), 0x365B80: (0x366580, 14, "One Big Fight!\nMountain Climb"), 0x366764: (0x3672C0, 15, "I Climb Because\nthe Mountain's There"),
    0x3674C8: (0x367D60, 16, "Sky, Wings\nand Hachiemon"), 0x367F34: (0x368998, 17, "Thunder, a Narcissist\nand Hachiemon"), 0x368BA8: (0x36941C, 18, "Beyond Red and Black"),
    0x3695D8: (0x369BC4, 19, "Escape"), 0x369D2C: (0x36A40C, 20, "The Battlefield Is..."), 0x36A5A0: (0x36AFE4, 21, "Two Pistols\nat Sunset"),
    0x36B1D8: (0x36BE6C, 22, "The Bee Repays Its Debt\nThat Darn Rascal\nwith the Hot Heart"), 0x36C0BC: (0x36C7AC, "?", "Still Just an Egg"), 0x36C938: (0x36CFF0, "?", "An Egg After All"),
    0x36D178: (0x36DD48, "?", "Infiltrate!\nThe Aunties' Battlefield"), 0x36DF60: (0x36E5E8, "?", "Auntie Is Coming!"), 0x36E768: (0x36EFAC, "?", "Octopus from Outer Space"),
    0x36F170: (0x36F918, "?", "Everyone's Paradise"),
}
MAPPED = {
    0x2A7784: (0x2AB148, banner("STAGE CLEAR"), BG0_TILES),
    0x2A7B88: (0x2AB220, banner("TIME OVER"), BG0_TILES),
    0x2A8454: (0x2AB3AC, [("All Lips\nCollected!", {"ink": 0xF, "outline": 1, "scale": 2, "bold": True})], BG0_TILES),
    0x2A8A9C: (0x2AB510, vs("Muscle\nHachiemon"), BG0_TILES),
    0x2A901C: (0x2AB5F8, vs("Tower\nHachiemon"), BG0_TILES),
    0x2A94FC: (0x2AB6D8, vs("Beehive"), BG0_TILES),
    0x2A9990: (0x2AB7C8, vs("Colorful\nHachiemon"), BG0_TILES),
    0x2A9F14: (0x2AB8B0, vs("Eight-in-One\nHachiemon"), BG0_TILES),
    0x2AA5C0: (0x2AB9A4, vs("Gunman\nHachiemon"), BG0_TILES),
    0x2AAB40: (0x2ABA8C, vs("Yamata no\nHachiemon"), BG0_TILES),
    0x2D05F4: (0x2D0CA4, [*message("Delete this save data.\nAre you sure?"), *YES_NO], None),
    0x2D0E10: (0x2D11DC, message("Save data deleted."), None),
    # The slot's digit is a tile the code puts at columns 18-19 of row 5: x 144-160. "Save data" ends left of it, "is" starts right of it.
    0x2D50CC: (0x2D5564, [
        ("", {"clear": (0, 40, 240, 80)}),
        ("Save data", {"clear": (40, 40, 142, 56), "ink": 0xF, "bold": True, "center": 104}),
        ("is", {"clear": (162, 40, 200, 56), "ink": 0xF, "bold": True}),
        ("corrupted.", {"clear": (40, 56, 200, 72), "ink": 0xF, "bold": True}),
    ], None),
}
for tiles, (where, part, title) in CARDS.items():
    MAPPED[tiles] = (where, card(part, title), None)

# Raw tiles the code reads by index: same size, so they stay in place. Offset -> (grid, text, options).
REEL = {0x303C70 + i * 0x400: t for i, t in enumerate([
    "Super", "Very", "Pretty", "Kinda", "Slightly",  # reel 1, how
    "Sweet", "Spicy", "Salty", "Bitter", "Sour", "Fresh", "Stinky", "Tasty", "Deadly",  # reel 2, what kind
    "Cream\nPuff", "Bean\nSoup", "Natto", "Curry\nRice", "Milk", "Ramen", "Veggie\nJuice", "Coffee", "Yogurt", "Kyoho\nGrapes",  # reel 3, what
    "Mystery\nFood", "Raw Food", "Hachi\nSet Meal", "Rice", "Meat", "Hot Pot",
])}
RAW = {off: (rows(0, 8, 4), text, {"ink": 1, "bold": True, "gap": 0}) for off, text in REEL.items()}

AREAS = {0x380A84: "Ranch", 0x380C20: "Under the Sea", 0x380DE4: "Osaka", 0x380F28: "On the Ice", 0x381104: "Forest", 0x381218: "Underground", 0x3813A4: "River",
         0x3814BC: "Mountain", 0x3815D4: "In the Sky", 0x381780: "Downtown", 0x381930: "Wilderness", 0x381A80: "Lip Land", 0x381CB0: "Farm Village",
         0x381E40: "Shopping", 0x382014: "Cove"}


def credit(text, start=0):
    """One credits line: 128x16, four 32x16 sprites."""
    return (spr(start, 32, 16, 4), text, {})  # not bold: the longest names need the width


# Credits, in the order of the blocks. Names Western order, Hepburn without macrons (D1, D2), read from the kana.
CREDITS = {
    0x39E128: "Staff", 0x39E2C4: "Voices", 0x39E3E8: "Teruyuki Okada", 0x39E690: "Editing", 0x39E844: "Toshifumi Onishi", 0x39EAE8: "Osamu Kasedo",
    0x39ED80: "Art", 0x39EF20: "Teruyuki Hiraoka", 0x39F1EC: "Hideaki Kuroda", 0x39F478: "Set Construction", 0x39F67C: "Wataru Kitamura", 0x39F908: "Props",
    0x39FAA4: "Mitsugu Takamiya", 0x39FD1C: "Wigs", 0x39FE84: "Kanae Fujishima", 0x3A00F4: "Sound", 0x3A02B0: "Iku Mizutani", 0x3A04D4: "Tetsuari Watanabe",
    0x3A0784: "Noriko Fujimura", 0x3A09EC: "Lighting", 0x3A0BB0: "Naohiko Morimoto", 0x3A0E58: "Katsuya Honda", 0x3A10B8: "Kazuhito Hamasuna", 0x3A13A8: "Camera",
    0x3A150C: "Seiko Hisaki", 0x3A1758: "Yasuji Nakano", 0x3A19A8: "Daisuke Miki", 0x3A1BF0: "Costumes", 0x3A1D78: "Maki Mukai", 0x3A1F90: "Momoko Kato",
    0x3A21C0: "Akiko Yukawa", 0x3A2410: "Stylist", 0x3A2608: "Hideaki Ito", 0x3A288C: "Special Effects", 0x3A2AC8: "Katsuro Tajima", 0x3A2D44: "Yasuhiro Fukaya",
    0x3A2FE0: "Script Supervisor", 0x3A314C: "Emiko Akechi", 0x3A3384: "Promotion", 0x3A35A8: "Taku Tsuge", 0x3A375C: "Yasuko Sato", 0x3A398C: "Old Guy",
    0x3A3B3C: "Taisuke Ishida", 0x3A3DA0: "Grandpa", 0x3A3FCC: "Jun Moriwaki", 0x3A4234: "Rider", 0x3A43C8: "Seiji Hirai", 0x3A45F8: "Special Thanks",
    0x3A48B4: "Ryoji Yamamoto", 0x3A4B68: "Tatsuya Tsujinaka", 0x3A4DC8: "(Dentsu)", 0x3A4FB8: "Assistant Director", 0x3A5128: "Yoichi Arakawa", 0x3A53E4: "Director",
    0x3A55C8: "Toshinori Sone", 0x3A57EC: "Koji Kadosaka", 0x3A5A54: "Supervisor", 0x3A5C88: "Kazuhisa Azuma", 0x3A5F24: "Toshikazu Iwasa", 0x3A619C: "Producer",
    0x3A63A8: "Toshiya Hara", 0x3A6590: "Production", 0x3A69C4: "Young Lady", 0x3A6BD0: "Yoko Sugise",
}

LABELS = {
    **{off: [credit(text)] for off, text in CREDITS.items()},
    # The credits' first page unpacks as one block before the per-line blocks take over: the same 12 lines.
    0x2CCF8C: [credit(text, i * 0x20) for i, text in enumerate(list(CREDITS.values())[:12])],
    **{off: [area(text)] for off, text in AREAS.items()},
    0x2C23A8: [(spr(0x50, 8, 16, 12), "Ranch", {"clear": (1, 1, 95, 15)})],  # row 16's first banner, loaded over it at once; kept English for the frame between
    **{0x310B2C: [stamp(0)], 0x310D14: [stamp(1)], 0x310EF8: [stamp(1)], 0x3110DC: [stamp(1)], 0x3112C4: [stamp(0)], 0x3114AC: [stamp(-1)], 0x311694: [stamp(-1)], 0x311878: [stamp(-1)]},
    # GA~ME OV~ER~: tile 0x74 is the 〜 three cells share, as in げ〜むお〜ば〜; it stays.
    0x2BFDD0: [cell(0x64, "GA", bold=False), cell(0x84, "ME", bold=False), cell(0x94, "OV", bold=False), cell(0xA4, "ER", bold=False)],  # not bold: the gap between ME and OV is the space
    0x2BAA24: [  # the map panel. The digits are sprites from x 102, so labels end by x 100 (x 16 is the picture's left).
        (spr(0x29E, 32, 16, 4), "Stage", {"clear": (8, 5, 84, 16), "ink": 0xF, "center": 26}),
        (spr(0x2BE, 32, 16, 4), "Lips", {"clear": (8, 0, 84, 16), "ink": 0xF, "center": 22}),
        (spr(0x2DE, 32, 16, 4), "Clear Time", {"clear": (8, 0, 84, 12), "ink": 0xF, "center": 42}),
    ],
    # [前編], [後編]: two 32x32 sprites each. No sprite used them in 53 stage and fight scenes, so where they show is unknown; "Part" is taken by the cards.
    0x2C4168: [(spr(0x86, 32, 32, 2), "[1st Half]", {}), (spr(0xA6, 32, 32, 2), "[2nd Half]", {})],
    0x2B98B0: [(spr(0, 32, 16, 4), "Hachi Slots", {"clear": (22, 2, 106, 14), "ink": 0xF, "outline": 1, "bold": True})],
    # After a stage card: N, then the two cells 発 and 目, then すた〜と. N comes from the digit blocks, first, so the words follow it.
    0x2A6EF0: [cell(0, "SH")],
    0x2A7038: [cell(0, "OT")],
    0x2A70DC: [cell(0x00, "S", center=24), cell(0x10, "TA"), cell(0x20, "RT"), cell(0x30, "!", center=6)],  # four cells, so the word sits centred
    0x2B7618: [
        (rows(0, 16, 2), "Press Start", {"ink": 8, "outline": 1, "bold": True}),
        shout(0x20, ""), shout(0x30, "KA"), shout(0x40, "NT"), shout(0x50, "EL"), shout(0x60, "E", center=16),
    ],
    0x2A7408: [([[*range(8, 15)], [*range(0x17, 0x1E)]], "Kantele", {"ink": 0xD})],  # the HUD's shout gauge, bottom right: tiles 9-F, 18-1E of BG0, palette D
    # The pause menu's BG0 map repeats tiles 4 and F at columns 0 and 9 of its first item, so text keeps off column 9.
    0x2A7FB4: [
        ([[*range(4, 0xF)], [*range(0xF, 0x1A)]], "Continue", {"ink": 0xD, "outline": 1, "bold": True, "center": 40}),
        ([[*range(0x1A, 0x28)], [*range(0x28, 0x36)]], "To Hachi Isle", {"ink": 0xD, "outline": 1, "bold": True}),
    ],
    0x2A7668: [([[*range(1, 7)], [*range(7, 0xD)]], "Pause", {"ink": 7, "outline": 1, "bold": True})],
    0x2BCD3C: [
        pill(0x060, "Main Game"), pill(0x078, "Options"), pill(0x090, "Music"), pill(0x0A8, "Sound FX"),
        pill(0x0C0, "Normal"), pill(0x0D8, "Hard"), pill(0x0F0, "Very Hard"),
        pill(0x108, "Stage", center=40), pill(0x120, "Lips", center=40),
        pill(0x279, "New Game"), pill(0x291, "Continue"), pill(0x2C1, "Lives", center=40),
        pill(0x2D9, "Delete Data"), pill(0x2F1, "You sure?"), pill(0x309, "Main Game"), pill(0x333, "Clear~"),
        disc(0x040, "ON"), disc(0x050, "OFF"), disc(0x255, "YES"), disc(0x265, "NO"), disc(0x323, "YES"),
        # The save header's digit sprites carry the tail of its last kana る.
        *[(spr(t, 16, 16), "", {"clear": (0, 2, 3, 14), "paper": 0xC}) for t in (0x201, 0x205, 0x209)],
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
    0x310810: [header("Save File")],  # the game adds its own ! sprite at the header's right
}


WAIT_SCREEN = 0x2D1EC4
MARQUEE = ["CRUSH", "BLAST", "SMASH", "GWAH!", "STANDBY", "ENERGY", "CHARGE", "READY", "PURGE"]  # フミツブス ブッパナス ブットバス グワッ! タイキチュウ エネルギー ジュウデン カンリョウ ハイジョ


def marquee_frames(rom):
    """Row 17, Tower Hachiemon's scrolling display: 75 frames of 48x16, one block each. Every word takes 9 frames, 8 px a frame: full at step 0, gone by 5, the next coming in.
    The display is x 6-41, rows 7-14. Its shading comes back as each pixel's commonest colour across the frames. Returns {block: packed}."""
    lo, hi = ROWS_16["row17"]
    offs = [int.from_bytes(rom[w:w + 4], "little") - 0x08000000 for w in range(lo, hi + 1, 16)]
    datas = [unpack(rom, off)[0] for off in offs]
    grid = spr(0, 16, 16, 3)
    pics = [Picture(d, grid) for d in datas]
    shade = {}
    for y in range(7, 15):
        for x in range(6, 42):
            colours = [p.get(x, y) for p in pics]
            shade[x, y] = max(set(colours), key=colours.count)
    words = [(tiny_rows(w, True), 24 - len(tiny_rows(w, True)[0]) // 2) for w in MARQUEE]
    for i, pic in enumerate(pics):
        for (x, y), c in shade.items():
            pic.set(x, y, c)
        step = i % 9
        drawn = [(i // 9, -8 * step)] + ([(i // 9 + 1, 8 * (9 - step))] if i // 9 + 1 < len(words) else [])
        for n, dx in drawn:
            glyphs, x0 = words[n]
            for ry, row in enumerate(glyphs):
                for rx, on in enumerate(row):
                    x = x0 + dx + rx
                    if on and 6 <= x < 42:
                        pic.set(x, 8 + ry, 4 if x < 9 or x >= 39 else 5 if x < 12 or x >= 36 else 0xF)  # dims toward the display's curved ends
    return {off: unpack(rom, off)[1](bytes(d)) for off, d in zip(offs, datas)}


class Picture8(Picture):
    """A tile grid over an 8bpp sheet."""

    def _at(self, x, y):
        return self.grid[y // 8][x // 8] * 64 + (y & 7) * 8 + (x & 7)

    def get(self, x, y):
        return self.data[self._at(x, y)]

    def set(self, x, y, v):
        self.data[self._at(x, y)] = v


def wait_screen(rom):
    """Row 20, しばらくおまちください before a fight: 8bpp BG2. Tile 7 is the bare background; tiles 8-C are the kana's tips above the two text rows, D-36 those rows."""
    data, pack = unpack(rom, WAIT_SCREEN)
    for t in (8, 9, 0xA, 0xB, 0xC, *range(0xD, 0x37)):
        data[t * 64:t * 64 + 64] = data[7 * 64:8 * 64]
    letter(Picture8(data, [[*range(0xD, 0x22)], [*range(0x22, 0x37)]]), "Please wait a moment", keep=True, ink=0xEE, outline=0xEF, bold=True)
    return pack(bytes(data))


def gradient(pic, text, ramp, outlines, scale, bold=False):
    """Shouting art: `text` centred on a clear picture, `ramp` running top to bottom, then one ring of pixels per colour in `outlines`, inner first."""
    for y in range(pic.h):
        for x in range(pic.w):
            pic.set(x, y, 0)
    glyphs = text_rows(text, bold, scale)
    h, w = len(glyphs), len(glyphs[0])
    x0, y0 = (pic.w - w - 1) // 2, (pic.h - h - 1) // 2
    margin = len(outlines)
    if x0 < margin or y0 < margin:
        raise ValueError(f"{text!r} is {w}x{h} in {pic.w}x{pic.h} with {margin} px of outline")
    inked = {(x0 + x + dx, y0 + y + dy) for y, row in enumerate(glyphs) for x, on in enumerate(row) if on for dx in (0, 1) for dy in (0, 1)}  # a pixel fatter: scaled text is thin next to the old brush lettering
    for x, y in inked:
        pic.set(x, y, ramp[(y - y0) * len(ramp) // (h + 1)])
    for colour in outlines:
        ring = {(x + dx, y + dy) for x, y in inked for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - inked
        for x, y in ring:
            pic.set(x, y, colour)
        inked |= ring


FLAME = [5, 5, 6, 7, 8, 9]  # the colours of ん〜 and めでたし, top to bottom
ART = {  # sprite art, which the 4bpp survey garbled or never placed: block -> (picture class, grid, text, gradient arguments). docs/re/graphics.md, rows 28 and 29.
    0x2B7CA0: [
        (Picture, [[0x184 + y * 8 + x for x in range(8)] + [0x1A4 + y * 8 + x for x in range(8)] + [0x1C4 + y] for y in range(4)], "I got this!!",  # まかせんかい!!
         {"ramp": [3, 5, 6, 7, 8, 9, 0xA, 0xB, 0xC], "outlines": [1, 0xF], "scale": 2}),
        (Picture, [[0xDE + y * 8 + x for x in range(8)] + [0xFE + y * 2 + x for x in range(2)] + [0x106 + y] for y in range(4)]
         + [[0x10A + x for x in range(8)] + [0x112 + x for x in range(3)]], "Mm~", {"ramp": FLAME, "outlines": [1], "scale": 3, "bold": True}),  # ん〜: mouths with no lips
    ],
    0x2C7924: [
        (Picture8, [row for r in range(3) for row in ([r * 0x24 + s * 8 + y * 4 + x for s in range(4) for x in range(4)] + [r * 0x24 + 0x20 + y * 2 + x for x in range(2)] for y in range(2))],
         "The End", {"ramp": FLAME, "outlines": [1], "scale": 3}),  # めでたし, drawn twice by the same tiles, closing the tale
    ],
}


def art(rom, off):
    """An ART block redrawn and packed again."""
    data, pack = unpack(rom, off)
    for cls, grid, text, kw in ART[off]:
        gradient(cls(data, grid), text, **kw)
    return pack(bytes(data))


def recolor(old, new, y0=0, y1=99):
    """A `prep` that turns colours in `old` to `new` between two rows, to lift lettering off art that no rectangle separates from it."""
    def run(pic):
        for y in range(y0, min(y1, pic.h)):
            for x in range(pic.w):
                if pic.get(x, y) in old:
                    pic.set(x, y, new)
    return run


def go_round_prep(pic):
    """The ride's pole runs through the sign at x 49-55: clear the word around it and redraw the pole's stripes."""
    for y in range(16):
        for x in range(80):
            if 49 <= x < 56:
                pic.set(x, y, [8, 7, 6, 7, 7, 8, 0][x - 49])
            elif y > 2:
                pic.set(x, y, 0)


def stall(top, bottom, text):
    """A food stall's sign: 48x16, two rows of six tiles. The frame's rings stay above row 3 and its border from row 14."""
    return ([[*range(top, top + 6)], [*range(bottom, bottom + 6)]], text, {"clear": (3, 3, 45, 14), "paper": 0xA, "ink": 0xD, "tiny": "wide"})


def isle(top, bottom, **kw):
    """The Hachi Isle board at a stage's start: 32x16, two rows of four tiles, 21 px inside its frame."""
    return ([[*range(top, top + 4)], [*range(bottom, bottom + 4)]], "HACHI\nISLE", {"clear": (6, 3, 27, 14), "tiny": "narrow", **kw})


# Stage tileset by table row -> its labels. Tiles come from the room maps (`tools/debug/stagesheet.py crop`).
STAGE_SIGNS = {
    0: [stall(0x92, 0x99, "HACHI'S\nSTALL"), isle(0x31, 0x35)],
    1: [stall(0xB1, 0xB9, "HACHI\nPARADISE"), isle(0x74, 0x7A)],
    2: [
        stall(0x293, 0x29A, "IT'S\nHACHI!"), isle(0x31, 0x37),  # ハチだがね, in Pops's own voice
        ([[*range(0x8C, 0x96)], [*range(0xAA, 0xB4)]], "HACHI\nGROCER", {"clear": (10, 1, 70, 15), "paper": 2, "ink": 5, "tiny": "wide"}),  # 八百ハチ, all three boards
        ([[*range(0x10E, 0x116)]], "HACHI MEATS", {"prep": recolor({1, 2, 3}, 7, 2, 7), "keep": True, "clear": (0, 2, 64, 7), "ink": 1, "tiny": "narrow"}),  # on the awning's strip
        ([[*range(0xC8, 0xCC)], [*range(0xE6, 0xEA)]], "HACHI\nPLACE", {"clear": (0, 2, 32, 13), "paper": 0xC, "ink": 7, "tiny": "wide"}),  # ハチ処
        # Its side panels and the roof's small words sit on tiles mirrored on the right, so they stay wordless.
        ([[0xC4, 0xC5, 0xC6, 0xC7], [0xE2, 0xE3, 0xE4, 0xE5]], "", {"clear": (3, 3, 22, 13), "paper": 0xC}),
        ([[0xC5, 0xC6, 0xC7], [0xE3, 0xE4, 0xE5]], "", {"clear": (17, 2, 24, 13), "paper": 0xC}),
        ([[*range(0x9E, 0xA8)]], "", {"clear": (38, 3, 58, 8), "paper": 0xC}),
    ],
    3: [isle(0xD1, 0xE8, ink=9)],  # its stall reads 558 HACHIMART, already in Latin
    4: [stall(0x12C, 0x133, "WOW!\nHACHI"), isle(0x5E, 0x68)],
    5: [stall(0x1A5, 0x1AC, "CLUB 8"), isle(0x57, 0x6B)],
    6: [stall(0x266, 0x26D, "HACHI\nPARADISE")],
    7: [stall(0x99, 0xA0, "SUSHI\nHACHI"), isle(0x40, 0x44)],
    8: [stall(0xD0, 0xD8, "MOUNTAIN\nHACHI"), isle(0xED, 0xFA)],
    9: [stall(0x34, 0x3B, "CHICKEN\nHACHI"), isle(0x84, 0x88)],
    10: [stall(0x15E, 0x16A, "HACHI\nBOY"), isle(0x28, 0x2C)],
    11: [stall(0x1A2, 0x1A9, "HACHI\nBURGER"), isle(0x123, 0x132)],
    12: [
        # This board's end tiles repeat mirrored, which leaves 16 px of free tiles: too narrow for HACHI, so it says ISLE.
        ([[0x4A], [0x4F]], "", {"clear": (6, 3, 8, 14), "paper": 0xE}),
        ([[0x4B, 0x4C], [0x50, 0x51]], "ISLE", {"clear": (0, 3, 16, 14), "paper": 0xE, "ink": 3, "tiny": "narrow"}),
        ([[*range(0xCD, 0xD6)], [*range(0xE8, 0xF1)]], "LIP LAND", {"prep": recolor({5, 0xD, 0xE}, 3, 10), "clear": (0, 0, 72, 10), "paper": 0, "ink": 0xD, "outline": 5, "bold": True}),  # くちびるらんど
        ([[*range(0x117, 0x11D)], [*range(0x126, 0x12C)]], "LIP\nMOUNTAIN", {"clear": (1, 2, 45, 13), "paper": 6, "ink": 0xD, "tiny": "narrow", "center": 27}),  # a pole covers the sign's left end
        ([[*range(0xDE, 0xE8)], [*range(0xF7, 0x101)]], "LIP-GO", {"prep": go_round_prep, "keep": True, "clear": (0, 8, 49, 16), "ink": 9, "outline": 3, "tiny": "wide"}),  # blocks cover the top rows
        ([[*range(0xDE, 0xE8)], [*range(0xF7, 0x101)]], "ROUND", {"keep": True, "clear": (56, 8, 80, 16), "ink": 9, "outline": 3, "tiny": "wide"}),
        ([[*range(0x187, 0x18C)]], "RIDES", {"clear": (0, 0, 40, 6), "paper": 4, "ink": 6, "tiny": "wide"}),
        ([[*range(0x1A6, 0x1AC)], [*range(0x1C7, 0x1CD)]], "LIP SPIN", {"prep": recolor({0xB, 3, 6, 0xC, 4, 0xD, 2}, 0, 3, 13), "keep": True, "clear": (0, 5, 48, 12), "ink": 3, "outline": 0xB, "tiny": "wide"}),
    ],
    13: [stall(0x98, 0x9F, "HACHI'S\nSTALL")],
    14: [
        stall(0x20, 0x29, "HACHI\nBOY"), isle(0x187, 0x191),
        ([[*range(0x96, 0x9C)], [*range(0xA7, 0xAD)]], "BARGAIN", {"clear": (3, 2, 45, 14), "paper": 0xA, "ink": 0xC, "tiny": "wide"}),  # ザ・バーゲン
    ],
    15: [stall(0xB9, 0xC0, "SUSHI\nHACHI")],
}


class MapPicture(Picture):
    """A tile block plus its map, flattened to one picture. `pack()` gives both back with tiles found again, flips included.
    Maps are 30x20 tile numbers, or Le maps with a 16-byte header (w, h, 0x10, size) and full BG words. Tile 0 stays tile 0."""

    def __init__(self, tiles, mapdata):
        self.head = bytes(mapdata[:16]) if int.from_bytes(mapdata[8:12], "little") == 0x10 and len(mapdata) != 0x4B0 else b""
        self.cols = int.from_bytes(self.head[:4], "little") if self.head else 30
        rows_ = (len(mapdata) - len(self.head)) // 2 // self.cols
        self.words = [int.from_bytes(mapdata[len(self.head) + i * 2:len(self.head) + i * 2 + 2], "little") for i in range(self.cols * rows_)]
        self.tile0 = bytes(tiles[:32])
        canvas = bytearray(self.cols * rows_ * 32)
        for i, w in enumerate(self.words):
            src = tiles[(w & 0x3FF) * 32:(w & 0x3FF) * 32 + 32].ljust(32, b"\0")
            canvas[i * 32:i * 32 + 32] = _flip(src, w >> 10 & 1, w >> 11 & 1)
        super().__init__(canvas, rows(0, self.cols, rows_))
        self.old_count = len(tiles) // 32

    def pack(self):
        """(tile bytes, map bytes). Each cell keeps its palette and priority bits."""
        seen = {self.tile0: (0, 0, 0)}
        for h, v in ((1, 0), (0, 1), (1, 1)):
            seen.setdefault(_flip(self.tile0, h, v), (0, h, v))
        out, words = bytearray(self.tile0), []
        for i, old in enumerate(self.words):
            tile = bytes(self.data[i * 32:i * 32 + 32])
            if tile not in seen:
                n = len(out) // 32
                out += tile
                for h, v in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    seen.setdefault(_flip(tile, h, v), (n, h, v))
            n, h, v = seen[tile]
            words.append(old & 0xF000 | v << 11 | h << 10 | n)
        return bytes(out), self.head + b"".join(w.to_bytes(2, "little") for w in words)


def _flip(tile, h, v):
    """A 4bpp tile mirrored: h swaps the nibbles of each row, end to end; v swaps the rows."""
    lines = [tile[y * 4:y * 4 + 4] for y in range(8)]
    if h:
        lines = [bytes((b >> 4 | b << 4) & 0xFF for b in reversed(ln)) for ln in lines]
    return b"".join(reversed(lines) if v else lines)


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


def remap(rom, tiles):
    """A MAPPED entry redrawn: (packed tiles, packed map, map offset). Fails when the tiles outgrow their limit."""
    data, pack_tiles = unpack(rom, tiles)
    where = MAPPED[tiles][0]
    mapdata, pack_map = unpack(rom, where)
    pic = MapPicture(data, mapdata)
    _, labels, limit = MAPPED[tiles]
    for text, kw in labels:
        letter(pic, text, **kw)
    new_tiles, new_map = pic.pack()
    limit = len(data) // 32 if limit is None else limit
    if len(new_tiles) // 32 > limit:
        raise ValueError(f"{tiles:#x} needs {len(new_tiles) // 32} tiles, limit {limit}")
    return pack_tiles(new_tiles), pack_map(new_map), where


def write_labels(img, rom, base=GFX_BASE):
    """Move every relabelled block past the text. Every block must have an owned slot."""
    slots, at = owned_slots(rom), base

    def place(off, block, who):
        nonlocal at
        if off not in slots:
            raise ValueError(f"graphics block {off:#x} has no owned slot")
        block += b"\xff" * (-len(block) % 4)
        img.write(at, block, f"gfx {who}")
        for w in slots[off]:
            img.write(w, (0x08000000 + at).to_bytes(4, "little"), f"gfxptr {who}")
        at += len(block)

    for off in sorted(LABELS):
        place(off, relabel(rom, off), f"{off:#x}")
    for off, block in marquee_frames(rom).items():
        place(off, block, f"{off:#x}")
    place(WAIT_SCREEN, wait_screen(rom), f"{WAIT_SCREEN:#x}")
    for off in sorted(ART):
        place(off, art(rom, off), f"{off:#x}")
    for row, labels in STAGE_SIGNS.items():
        off = int.from_bytes(rom[STAGE_SETS + row * 8:STAGE_SETS + row * 8 + 4], "little") - 0x08000000
        place(off, relabel(rom, off, labels), f"{off:#x}")
    for off in sorted(MAPPED):
        tiles, mapped, where = remap(rom, off)
        place(off, tiles, f"{off:#x}")
        place(where, mapped, f"{where:#x}")
    for off, (grid, text, kw) in RAW.items():
        data = bytearray(rom[off:off + len(grid) * len(grid[0]) * 32])
        letter(Picture(data, grid), text, **kw)
        img.write(off, bytes(data), f"gfx raw {off:#x}")
