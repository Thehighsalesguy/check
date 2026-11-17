"""Instagram profile picture: cartoon Keef in his bowler hat + monocle.
Usage: python3 profile_pic.py out.png
"""
import math
import sys

import cairo

import reel
from reel import rgb, ellipse, fs, fill, INK, CAT, cat_head
from reel3 import gentleman

S = 1080
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
ctx = cairo.Context(surf)
# background: warm peach with soft rays (Instagram crops to a circle)
ctx.rectangle(0, 0, S, S)
ctx.set_source_rgb(*rgb('#FBD9C9'))
ctx.fill()
for i in range(16):
    a0 = i * 2 * math.pi / 16
    ctx.move_to(S / 2, S / 2)
    ctx.arc(S / 2, S / 2, S, a0, a0 + math.pi / 16)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.22)
    ctx.fill()
# shoulders / chest
ellipse(ctx, S / 2, S * 0.98, 330, 260)
fs(ctx, CAT, INK, 10)
# head
ctx.save()
ctx.translate(S / 2, S * 0.55)
ctx.scale(3.3, 3.3)
reel.HEAD_EXTRAS = gentleman(hat=True, mono=True)
cat_head(ctx, 'open', (0.15, 0.1), 0.0, 0.5)
reel.HEAD_EXTRAS = None
ctx.restore()
surf.write_to_png(sys.argv[1])
