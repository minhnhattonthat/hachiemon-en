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
WORD_SLOTS = [*range(0x1D5F5C, 0x1D6454, 4), *range(0x1A3D10, 0x1A3D60, 4), *CODE_LITERALS]  # OBJ and BG set tables (flow.md), VS tiles and maps


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


def letter(pic, text, clear=None, ink=None, outline=None, bold=False, scale=1, gap=1, center=None, prep=None, keep=False, paper=None):
    """Clear `clear` (x0, y0, x1, y1; default the whole picture) to `paper`, by default its commonest colour, then draw `text` centred in it.
    `ink` defaults to the rectangle's second commonest colour. Lines split on a newline. `prep(pic)` runs first; `keep` skips the clearing."""
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


def shout(start, text, **kw):
    """One 32x32 cell of the title's Kantele shout. They settle 22 px apart, the first (x -31) off screen, so it stays blank."""
    return (spr(start, 32, 32), text, {"clear": (0, 0, 32, 32), "ink": 0xF, "outline": 1, "scale": 2, "bold": True, **kw})


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
    "Mystery\nFood", "Raw Food", "Hachi\nSet Meal", "Rice",
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
    0x2B98B0: [(spr(0, 32, 16, 4), "Hachi Slots", {"clear": (22, 2, 106, 14), "ink": 0xF, "outline": 1, "bold": True})],
    # After a stage card: N, then the two cells 発 and 目, then すた〜と. N comes from the digit blocks, first, so the words follow it.
    0x2A6EF0: [cell(0, "SH")],
    0x2A7038: [cell(0, "OT")],
    0x2A70DC: [cell(0x00, "S", center=24), cell(0x10, "TA"), cell(0x20, "RT"), cell(0x30, "!", center=6)],  # four cells, so the word sits centred
    0x2B7618: [
        (rows(0, 16, 2), "Press Start", {"ink": 8, "outline": 1, "bold": True}),
        shout(0x20, ""), shout(0x30, "K", center=22), shout(0x40, "AN"), shout(0x50, "TE"), shout(0x60, "LE"),
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
    for off in sorted(MAPPED):
        tiles, mapped, where = remap(rom, off)
        place(off, tiles, f"{off:#x}")
        place(where, mapped, f"{where:#x}")
    for off, (grid, text, kw) in RAW.items():
        data = bytearray(rom[off:off + len(grid) * len(grid[0]) * 32])
        letter(Picture(data, grid), text, **kw)
        img.write(off, bytes(data), f"gfx raw {off:#x}")
