# Phase 9 story pass

One fresh read-only read of all 914 strings in story order, chapter by chapter (`tools/pairs.py --chapters`, chapter table from `docs/synopsis.md`). Same model as the translator, not Codex: Codex is out of credit until 2026-11-11 (`codex exec` still reports the limit on 2026-11-07), and this run's brief bars nested workers, so D14 applies. A Codex read after that date is still worth having: `tools/codex_review.py docs/story-reviewer-brief.md work/qa/reviews work/qa/story/chapters/*.txt`.

The story order of the middle stages is inferred (`docs/synopsis.md`), so a callback between far-apart talk scenes was judged on what the script shows, not on a played route.

| Chapter | Verdict | Notes |
|---|---|---|
| ch1_opening | ok | Signs and opening carry. "What's with this guy--" into "With! My! Proud! Physique!" keeps the interrupted boast. |
| ch2_auntie | ok | Takoyaki gags land (m701-m702, m708, m720). |
| ch3_osaka | fixed | The merchant greeting stays word for word from m080-m081 to m339, m342. m086 loosened, `~.` lines. |
| ch4_rescues_a | ok | m103 "Me!" is flat but the limit is 6 columns. m175-m176, m181-m182 punchlines hold. |
| ch4_rescues_b | ok | Panda dub, Tyranno's delayed answers (m547-m560), the "So I just get you some lips, yeah?" refrain hold. `~.` lines only. |
| ch4_rescues_c | ok | Egg, octopus, permit and Lamaze runs all hold. |
| ch5_gang | fixed | Tough-guy lines stay plain until m224, so the reveal isn't given away. m205 Gunman lost a "pal" that was out of voice. m238, m256 from the polish list. |
| ch6_lipland | fixed | m287 and m291 keep the kids callback across both villains. m262 was too cheerful for Yamata. |
| ch7_ending | ok | |
| ch8_misc | ok | Bungee callback (m596, m823-m830) stays one word. Lines m841-m872 aren't reachable. |

No Critical or Important finding. All changes are minors from `docs/polish.md`.

m103 and m181 stay as they are: both are at their measured width limits (`docs/polish.md`). Rechecked in game on the rebuilt ROM: see `docs/status.md`.
