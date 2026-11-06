# Hachiemon (GBA) English translation

Skill: translate-retro-game; `python tools/skill.py` prints its folder. Read its SKILL.md before ROM, text or QA work. `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path.

## Commands (run from repo root)
- Setup once per clone: `git config core.hooksPath tools/hooks`
- Build:    `python -X utf8 tools/build.py` -> build/hachiemon_en.gba + build/writes.txt (checks the dump against `rom.sha1` first; with no English in `script/` the output is byte-identical)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/hachiemon_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/hachiemon_en.gba --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (phase 2 adds it; scenes: `tools/debug/scenes.*`; never ask the user to play to a scene)
- Tour:     `python -X utf8 tools/debug/tour.py "rom/Hachiemon (Japan).gba" --out work/qa/warp --jobs 7 --shots 900,1800` (every scene from a cold boot; `--only REGEX`, `--states work/states`; `--frames 7000 --mash 20` to read bubble text), then `tools/debug/gfxcover.py OUT`, `tools/debug/textcover.py ROM OUT`
- Release:  `python -X utf8 tools/release.py` (phase 9 adds it; patch + verify; never publish without the user)
- Text:     `python -X utf8 tools/batches.py check|merge bNNN`, `tools/lint.py --fit "text{end:00}" ID`, `tools/pairs.py` (reviewer input), `tools/codex_review.py`
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)
- Recon:    `python -X utf8 tools/strscan.py rom/*.gba` (text banks), `tools/gfxsweep.py` + `tools/gfxsweep8.py` (graphics sheets), `tools/fontsheet.py` (font), `tools/gbacomp.py` (LZ77)

## Paths
- Original ROM: `rom/Hachiemon (Japan).gba` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1, https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip, plus `Firmware/gba_bios.bin` from `fetch_emu.py gba-bios`; gitignored; settings in `tools/emu-config/`). Savestates: `work/states/`.
- Text: `script/signs.json`, `script/main.json` (from `tools/extract.py`; `en` empty = untranslated, keep `{end:MM}`). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Text is one byte per font cell, no Shift-JIS. `FF` ends a string and is followed by a mode byte that belongs to it: keep the pair. `FD` waits for a press and clears, `FE` is a new line. Details: `docs/re/text.md`.
- Repoint text only through `text_slots` (`tools/build.py`, from `tools/vmscript.py`). Never patch by scanning for a value: some matches are data.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
