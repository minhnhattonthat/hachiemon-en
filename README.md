# Hachiemon English translation

Unofficial English fan translation of **Hachiemon** (Game Boy Advance, Namco, 2003): the source text and tools
that build the patch.

**Status: in progress, no patch yet.** This repository holds no game data you can play; you need your own dump of the
Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Story and speech bubbles | Not started |
| Tutorial signboards | Not started |
| Menus, stage cards and other drawn text | Not started |
| Title logo | Staying in Japanese (it already reads "hachiemon" beneath) |

Known issues: see [Issues](../../issues).

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

Not buildable yet. Needs Python 3.12+ and your own dump of the Japanese game, copied to `rom/Hachiemon (Japan).gba`
(4,194,304 bytes, SHA-1 `10c16950388599846c2a61cacc315ba81a752deb`; the build refuses any other dump, see `rom.sha1`).

```sh
git config core.hooksPath tools/hooks
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. Hachiemon is (c) 2003 KTV and NAMCO LTD.; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
