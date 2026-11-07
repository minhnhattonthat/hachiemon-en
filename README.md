# Hachiemon English translation

Unofficial English fan translation of **Hachiemon** (Game Boy Advance, Namco, 2003): the source text and tools
that build the patch.

**Status: translation complete.** Get the patch from [Releases](../../releases); if none is listed yet, build it yourself
(below). This repository holds no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Story and speech bubbles | English |
| Tutorial signboards | English |
| Menus, stage cards, banners, shop signs, opening and ending art, credits | English |
| Title logo | Japanese (it already reads "hachiemon" beneath) |
| Namco and Kansai TV logos | As in the original |

Tested in MesenCE 2.2.1 from scripted runs: every scene reached by a debug warp and read from screenshots. Start from a
cold boot; savestates from another build carry its old code and text.

Known issues: nobody has played it from start to finish or run it on real hardware, and a save written by finishing a
real stage hasn't been tried. See also [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `tbl/` | Character table. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain and recon tools. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ with Pillow and your own dump of the Japanese game, copied to `rom/Hachiemon (Japan).gba`. The build
refuses any other dump (`rom.sha1`):

| | |
|---|---|
| Name | Hachiemon (Japan) |
| Size | 4,194,304 bytes |
| CRC32 | `47C45B41` |
| MD5 | `6c8460b00a7dcade834b0579116771db` |
| SHA-1 | `10c16950388599846c2a61cacc315ba81a752deb` |

```sh
git config core.hooksPath tools/hooks
python -X utf8 tools/build.py                          # build/hachiemon_en.gba
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. Hachiemon is (c) 2003 KTV and NAMCO LTD.; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
