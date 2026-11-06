"""BIOS LZ77 (type 0x10) codec plus a ROM block scanner.

    python -X utf8 tools/gbacomp.py scan ROM [--min 32]   # lists plausible LZ77 blocks: offset, packed, unpacked
    python -X utf8 tools/gbacomp.py x ROM HEXOFF OUT      # one block to a file
"""
import struct
import sys


def lz_decompress(d, off=0, limit=None):
    """Returns (data, end_offset). Raises ValueError on a block that isn't LZ77."""
    if d[off] != 0x10:
        raise ValueError("not LZ77")
    size = int.from_bytes(d[off + 1:off + 4], "little")
    if not size or (limit and size > limit):
        raise ValueError("bad size")
    out = bytearray()
    i = off + 4
    n = len(d)
    while len(out) < size:
        if i >= n:
            raise ValueError("ran off the end")
        flags = d[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                if i + 1 >= n:
                    raise ValueError("ran off the end")
                ln = (d[i] >> 4) + 3
                dist = ((d[i] & 15) << 8 | d[i + 1]) + 1
                i += 2
                if dist > len(out):
                    raise ValueError("back-reference before start")
                for _ in range(ln):
                    out.append(out[-dist])
            else:
                if i >= n:
                    raise ValueError("ran off the end")
                out.append(d[i])
                i += 1
    if len(out) != size:
        raise ValueError("overrun")  # a real block ends exactly on its size
    return bytes(out), i


def lz_compress(data):
    """Greedy VRAM-safe LZ77 (no distance-1 matches, the BIOS VRAM variant writes 16 bits at a time)."""
    out = bytearray(b"\x10" + len(data).to_bytes(3, "little"))
    i = 0
    n = len(data)
    while i < n:
        flag_at = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len = 0
            best_dist = 0
            for dist in range(2, min(i, 0x1000) + 1):
                ln = 0
                while ln < 18 and i + ln < n and data[i + ln] == data[i + ln - dist]:
                    ln += 1
                if ln > best_len:
                    best_len, best_dist = ln, dist
                    if ln == 18:
                        break
            if best_len >= 3:
                flags |= 0x80 >> bit
                out.append((best_len - 3) << 4 | (best_dist - 1) >> 8)
                out.append((best_dist - 1) & 255)
                i += best_len
            else:
                out.append(data[i])
                i += 1
        out[flag_at] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def scan(d, min_size=32, max_size=0x80000):
    """Every 4-aligned offset that decodes as a whole LZ77 block, skipping past each hit."""
    hits = []
    off = 0
    while off < len(d) - 4:
        if d[off] == 0x10:
            size = int.from_bytes(d[off + 1:off + 4], "little")
            if min_size <= size <= max_size:
                try:
                    data, end = lz_decompress(d, off, max_size)
                except ValueError:
                    data = None
                if data is not None and end - off < size * 2:
                    hits.append((off, end - off, size))
                    off = (end + 3) & ~3
                    continue
        off += 4
    return hits


def le_decompress(d, off=0):
    """The game's own "Le" codec (0x8000A34): 'Le', u24 size, one pad byte, then control bytes.

    Each control byte holds four 2-bit ops, low bits first: 0 = long copy (u16: dist (w & 0xFFF) + 5, len (w >> 12) + 3),
    1 = short copy (u8: dist (b & 3) + 1, len (b >> 2) + 2), 2 = one literal, 3 = three literals. Returns (data, end).
    """
    if d[off:off + 2] != b"Le":
        raise ValueError("not Le")
    size = int.from_bytes(d[off + 2:off + 5], "little")
    if not size:
        raise ValueError("bad size")
    out = bytearray()
    i = off + 6
    n = len(d)
    while len(out) < size:
        if i >= n:
            raise ValueError("ran off the end")
        ctrl = d[i]
        i += 1
        for shift in (0, 2, 4, 6):
            if len(out) >= size:
                break
            op = ctrl >> shift & 3
            if op == 0 or op == 1:
                if op == 0:
                    w = d[i] | d[i + 1] << 8
                    i += 2
                    dist, ln = (w & 0xFFF) + 5, (w >> 12) + 3
                else:
                    b = d[i]
                    i += 1
                    dist, ln = (b & 3) + 1, (b >> 2) + 2
                if dist > len(out):
                    raise ValueError("back-reference before start")
                for _ in range(ln):
                    out.append(out[-dist])
            else:
                count = 1 if op == 2 else 3
                out += d[i:i + count]
                i += count
    if len(out) != size:
        raise ValueError("overrun")
    return bytes(out), i


def le_scan(d, max_size=0x100000):
    """Every 4-aligned offset that decodes as a whole Le block."""
    hits = []
    off = 0
    while True:
        off = d.find(b"Le", off)
        if off < 0:
            return hits
        if off % 4 == 0:
            size = int.from_bytes(d[off + 2:off + 5], "little")
            if 0 < size <= max_size:
                try:
                    _, end = le_decompress(d, off)
                except (ValueError, IndexError):
                    end = None
                if end is not None and end - off <= size * 2:
                    hits.append((off, end - off, size))
                    off = (end + 3) & ~3
                    continue
        off += 2


if __name__ == "__main__":
    rom = open(sys.argv[2], "rb").read()
    if sys.argv[1] == "le":
        for off, packed, size in le_scan(rom):
            print(f"{off:07x} {packed:6x} {size:6x}")
    elif sys.argv[1] == "scan":
        for off, packed, size in scan(rom):
            print(f"{off:07x} {packed:6x} {size:6x}")
    elif sys.argv[1] == "x":
        data, end = lz_decompress(rom, int(sys.argv[3], 16))
        open(sys.argv[4], "wb").write(data)
        print(f"{len(data):#x} bytes, ends at {end:#x}")
    else:
        sys.exit(__doc__)
