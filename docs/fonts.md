# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `fonts/PixelOperator.ttf` -> `tbl/vwf_font.txt` | Pixel Operator by Jayvee Enaguas (HarvettFox96), https://www.dafont.com/pixel-operator.font, zip dated 2018-10-04; author's repo https://notabug.org/HarvettFox96/ttf-pixeloperator | CC0 1.0 (`fonts/PixelOperator-LICENSE.txt`, the file inside the zip. DaFont's own label also lists GPL/OFL; the zip's licence text is what this row relies on) | Yes | All box and bubble English | Rasterised at its native 16 px; ASCII only; the build adds a 1 px shadow in the game's palette |

The heart (♥) comes from the game's own font cell 0xF9. The game's Latin glyphs (0xA0-0xD9) are fixed 8 px with no comma or apostrophe, so English doesn't use them.
