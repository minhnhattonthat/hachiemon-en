import sys
sys.path.insert(0, 'tools')
from PIL import Image, ImageDraw
from gbacomp import le_decompress
from lesweep import tiles
d = open('rom/Hachiemon (Japan).gba', 'rb').read()
out, cols, zoom, *offs = sys.argv[1:]
cols, zoom = int(cols), int(zoom)
ims = []
for a in offs:
    o = int(a, 16)
    u = le_decompress(d, o)[0]
    ims.append((o, tiles(u, cols)))
W = max(i.size[0] for _, i in ims) * zoom
H = sum(i.size[1] * zoom + 12 for _, i in ims)
s = Image.new('RGB', (W, H), (70, 0, 70))
dr = ImageDraw.Draw(s)
y = 0
for o, i in ims:
    dr.text((1, y), f'{o:06x} {i.size}', fill=(255, 255, 0))
    s.paste(i.resize((i.size[0] * zoom, i.size[1] * zoom), Image.NEAREST).convert('RGB'), (0, y + 11))
    y += i.size[1] * zoom + 12
s.save(out)
print(s.size)
