# Skill gotchas

One line each: the reference it belongs in, then the fact.

- `references/emulator-qa.md`: a tour can lose every remaining scene at once to exit code 0xC0000142 (Mesen failing to start; seen 2026-11-07 after 29 of 160 scenes, cause unknown). The tour still exits 0, so read the `N/M ok` line in its log, not the exit code.
- `references/emulator-qa.md`: `sheet.py` run from a subfolder with shell-relative paths writes `--out` relative to that folder, and the shell's working directory carries to the next call. Run it from the repo root.
- `references/pipeline.md` (Marker): a bubble or sign can have a byte cap on the whole string, across pages. Fill long multi-page strings to the limit in the at-limit build, or the cap only shows in a playtest.
