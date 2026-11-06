"""The two cutscene interpreters and the text pointers their scripts own. See docs/re/text.md, Script VMs.

Scripts are u32 streams: an opcode, then its arguments. Lengths below are read from the handlers (jump tables 0x803B4F0
and 0x80569C8) and count the opcode word. Both VMs share opcode numbers but not every length: op 1 differs.

    python -X utf8 tools/vmscript.py ROM     # per script: start, end, ops, text words
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strscan import BANKS

BASE = 0x08000000
TALK_TABLE, TALK_ENTRIES = 0x1C2E18, 88  # read by 0x803B4B0 with the id in 0x3003E0C; the word after entry 87 is no pointer
STAGE_VM = 0x8056990  # takes the script pointer in r0: every caller loads it from a literal
STAGE_CALLERS = 36
SIGN_TABLE, SIGN_ENTRIES = 0x1C1280, 41  # read at 0x8002D54 and 0x8003FF4; entry 40 is the empty string at 0x1C127D
END = 4  # op 0 also stops the VM but holds forever: no script uses it as its end
ANIM_ARG, TALK_ARG = {0xAF: 5}, {0xAF: 6, 0x8E: 5}  # word index after the opcode's own word 0: AF sets the speaker's anim

SHARED = {
    2: 1, 0x80: 4, 0x81: 4, 0x92: 4, 0x93: 4, 0x86: 4, 0xB0: 4, 0x87: 2, 0x8E: 8, 0x8F: 2, 0x91: 2, 0x96: 3, 0x97: 2,
    0x98: 2, 0x9E: 4, 0x9F: 1, 0xA3: 17, 0xA4: 17, 0xA6: 2, 0xA7: 4, 0xAA: 3, 0xAF: 7, 0xB3: 1, 0xB4: 4,
    **{op: 9 for op in range(0xC0, 0xDF)},
}
TALK = {
    **SHARED, 1: 1, 0x10: 18, 0x11: 18, 0x12: 18, 0x8B: 8, 0x90: 5, 0x94: 2, 0x95: 2, 0xA0: 2, 0xA8: 1, 0xA9: 3,
    0xAB: 2, 0xAC: 17, 0xAD: 17, 0xAE: 2, 0xB6: 4,
}
STAGE = {
    **SHARED, 1: 2, 0x9A: 3, 0x9B: 6, 0xA1: 5, 0xA2: 4, 0xA5: 2, 0xB1: 1, 0xB2: 2, 0xB5: 1, 0xB7: 1,
}


def u32(rom, off):
    return struct.unpack_from("<I", rom, off)[0]


def walk(rom, start, lengths):
    """Ops (offset, opcode, words) from start up to its op 4. An opcode the VM would not run raises."""
    ops, at = [], start
    while (op := u32(rom, at)) != END:
        if op not in lengths:
            raise ValueError(f"script {start:#x}: bad opcode {op:#x} at {at:#x}")
        ops.append((at, op, lengths[op]))
        at += lengths[op] * 4
    return ops


def _bl_callers(rom, target):
    for at in range(0, 0x80000, 2):
        hi, lo = struct.unpack_from("<HH", rom, at)
        if hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800:
            off = (hi & 0x7FF) << 12 | (lo & 0x7FF) << 1
            if BASE + at + 4 + (off - 0x800000 if off & 0x400000 else off) == target:
                yield at


def stage_starts(rom):
    """Each caller of the stage VM loads its script with `ldr r0,[pc,#n]` a few instructions before the call."""
    starts, callers = set(), 0
    for call in _bl_callers(rom, STAGE_VM):
        callers += 1
        for at in range(call - 2, call - 18, -2):
            hw = struct.unpack_from("<H", rom, at)[0]
            if hw & 0xFF00 == 0x4800:
                starts.add(u32(rom, ((at + 4) & ~3) + (hw & 0xFF) * 4) - BASE)
                break
        else:
            raise ValueError(f"stage VM caller {call:#x}: no literal for r0")
    if callers != STAGE_CALLERS:
        raise ValueError(f"expected {STAGE_CALLERS} stage VM callers, found {callers}")
    return sorted(starts)


def scripts(rom):
    """name -> (start, ops). Six talk table entries are stage-format scripts, so the stage walk owns them."""
    stage = stage_starts(rom)
    out = {}
    for i in range(TALK_ENTRIES):
        start = u32(rom, TALK_TABLE + i * 4) - BASE
        if start not in stage:
            out[f"talk{i:02d}"] = (start, walk(rom, start, TALK))
    for start in stage:
        out[f"stage_{start:06X}"] = (start, walk(rom, start, STAGE))
    return out


def in_bank(value):
    return any(BASE + lo <= value < BASE + hi for lo, hi in BANKS)


def script_words(rom):
    """word offset -> {scene, seq, op, slot, anim}. Any bank pointer in an argument that is not a known text argument raises."""
    words = {}
    for name, (_, ops) in scripts(rom).items():
        for seq, (at, op, count) in enumerate(ops):
            for k in range(1, count):
                if in_bank(u32(rom, at + k * 4)):
                    if TALK_ARG.get(op) != k:
                        raise ValueError(f"{name}: text pointer in arg {k} of op {op:#x} at {at:#x}")
                    anim = ANIM_ARG.get(op)
                    words[at + k * 4] = {"scene": name, "seq": seq, "op": f"{op:02X}", "slot": u32(rom, at + 4),
                                         "anim": f"{u32(rom, at + anim * 4) - BASE:06X}" if anim else ""}
    return words


def code_words(rom):
    """Literal-pool words that an `ldr rN,[pc,#n]` in code really loads and that point into a text bank."""
    found = set()
    for at in range(0, 0x80000, 2):
        hw = struct.unpack_from("<H", rom, at)[0]
        if hw & 0xF800 == 0x4800:
            lit = ((at + 4) & ~3) + (hw & 0xFF) * 4
            if in_bank(u32(rom, lit)):
                found.add(lit)
    return sorted(found)


def sign_words():
    return [SIGN_TABLE + i * 4 for i in range(SIGN_ENTRIES)]


if __name__ == "__main__":
    data = Path(sys.argv[1]).read_bytes()
    all_words = script_words(data)
    for script, (first, body) in scripts(data).items():
        last = body[-1][0] + body[-1][2] * 4 if body else first
        print(f"{script} {first:06X}-{last:06X} ops {len(body)} text {sum(w['scene'] == script for w in all_words.values())}")
    print(f"{len(all_words)} script words, {len(code_words(data))} code literals, {SIGN_ENTRIES} sign entries")
