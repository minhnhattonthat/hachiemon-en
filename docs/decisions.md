# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-06 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's answer in the run brief. |
| D2 | 2026-11-06 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. Owner's answer. No earlier patch found (web search, 2026-11-06); the title screen's own "hachiemon" is the official spelling. |
| D3 | 2026-11-06 | Credits | stay Japanese, translate | English. Owner's answer. |
| D4 | 2026-11-06 | Abbreviations | engine work first (default), abbreviate | Engine work first; abbreviate only as a flagged last resort. Skill default; the owner's brief says to use sensible defaults. |
| D5 | 2026-11-06 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards). Leave the original Japanese logo only if it has no official English version. Owner's answer. The game never had an English release, so the ハチエモン title logo stays; it already carries "hachiemon" beneath it. Publisher and broadcaster logos (Namco, Kansai TV) stay as they are. |
| D6 | 2026-11-06 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. Owner's answer. |
| D7 | 2026-11-06 | Existing saves or savestates | use, none | None provided; build the debug tool as usual. Owner's answer. |
| D8 | 2026-11-06 | Publishing | release, stop at a verified zip | Never run `gh release create` or change repo visibility: the run ends at a built and verified release zip. Owner's answer. |
| D9 | 2026-11-07 | English font path (agent's call under D4 and D6, not the owner's) | hook the draw routine for a VWF; half-width font; pre-rendered proportional cells | Pre-rendered cells: the build renders each line in PixelOperator (CC0), slices it into 8 px cells and stores them before the string, so a text byte means "cell at string start + b". No new code or RAM, proven in the marker tour. |
| D10 | 2026-11-07 | Where English text goes (agent's call under D6) | free-space candidates in the ROM, past the original end | Past the end: text at 0x400000, ROM grows to 8 MiB. Past-end space needs no trap test, and pre-rendered cells need the room. |
