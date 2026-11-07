Hachiemon English translation, v@VERSION@
Unofficial fan translation of Hachiemon (Game Boy Advance, Namco, 2003).

APPLYING THE PATCH
You need your own dump of the Japanese game. This zip holds no game data.
Apply @PATCH@ with a BPS patcher (Rom Patcher JS, Floating IPS, beat).

Base ROM: Hachiemon (Japan).gba
  Size    @BASE_SIZE@ bytes
  CRC32   @BASE_CRC32@
  MD5     @BASE_MD5@
  SHA-1   @BASE_SHA1@

Patched ROM: 8,388,608 bytes (the patch grows the ROM from 4 MiB to 8 MiB to make room for the English text)
  CRC32   @PATCHED_CRC32@
  SHA-1   @PATCHED_SHA1@

Start from a cold boot. Savestates made on another build carry its old code and text, so don't load them.

TRANSLATION STATUS
  Story and speech bubbles    English
  Tutorial signboards         English
  Menus, stage cards, banners, shop signs, opening and ending art, credits    English
  Title logo                  Japanese: it already reads "hachiemon" beneath it
  Namco and Kansai TV logos   As in the original

Honorifics are kept (Hachiemon-san). Names are in Western order.

TESTED IN
MesenCE 2.2.1 on Windows, from scripted runs: every scene reached by a debug warp and read from screenshots.
Saving was checked by writing and reading the save file across cold boots.

KNOWN ISSUES
- Nobody has played this build from start to finish, and it hasn't run on real hardware.
- A save written by finishing a real stage hasn't been tried.
- Some text rests on the size checks rather than on a screenshot: boss 5's defeat lines were mostly caught still typing.
- Things the original does too, left alone: the tan block and timer over the bubbles in fight 4, and the ON/OFF discs over the Sound FX pill.
Report bugs at https://github.com/minhnhattonthat/hachiemon-en/issues (a savestate helps most).

CREDITS
Translation and tools: minhnhattonthat, with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
Font: Pixel Operator by Jayvee Enaguas (HarvettFox96), CC0.

Hachiemon is (c) 2003 KTV and NAMCO LTD. This project is unofficial and not affiliated with them.
Please don't share patched ROMs.
