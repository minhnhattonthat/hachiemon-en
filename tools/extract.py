"""Extract both text banks to script/signs.json and script/main.json. Every string, including the pointerless ones.

    python -X utf8 tools/extract.py    # refuses to overwrite a script that already holds English

Entry: id, offset (hex), jp (table text, ends with {end:MM}), en (empty until translated; keep {end:MM} too), refs.
refs say who points at the string: script refs carry scene and seq for story order, op AF has the speaker's anim.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import strings
from check_rom import check
from strscan import BANKS
from tbl import Table
from vmscript import BASE, code_words, script_words, sign_words, u32

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/Hachiemon (Japan).gba"
FILES = {"signs": ROOT / "script/signs.json", "main": ROOT / "script/main.json"}


def entries(rom, codec, starts):
    """{file: [entry]} from the string starts, in ROM order."""
    refs = {}
    for word, info in script_words(rom).items():
        refs.setdefault(u32(rom, word) - BASE, []).append({"word": f"{word:06X}", **info})
    for word in code_words(rom):
        refs.setdefault(u32(rom, word) - BASE, []).append({"word": f"{word:06X}", "scene": "code"})
    for seq, word in enumerate(sign_words()):
        refs.setdefault(u32(rom, word) - BASE, []).append({"word": f"{word:06X}", "scene": "sign", "seq": seq})
    out = {"signs": [], "main": []}
    for s in starts:
        name, prefix = ("signs", "s") if s < BANKS[0][1] else ("main", "m")
        out[name].append({"id": f"{prefix}{len(out[name]):03d}", "offset": f"{s:06X}", "jp": codec.decode(rom, s)[0],
                          "en": "", "refs": sorted(refs.get(s, []), key=lambda r: r["word"])})
    return out


def main():
    check()
    for path in FILES.values():
        if path.exists() and any(e["en"] for e in json.loads(path.read_text(encoding="utf8"))):
            sys.exit(f"{path} holds English: not overwriting it")
    rom = ROM.read_bytes()
    data = entries(rom, Table.load(ROOT / "tbl/jp.tbl"), strings(rom))
    for name, path in FILES.items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(data[name], ensure_ascii=False, indent=1) + "\n", encoding="utf8", newline="\n")
        print(f"{path}: {len(data[name])} strings, {sum(not e['refs'] for e in data[name])} without a pointer")


if __name__ == "__main__":
    main()
