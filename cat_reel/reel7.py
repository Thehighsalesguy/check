"""Reel #7: 'Keef vs. the Cucumber' - the internet prank meets a British Shorthair.

Usage: python3 reel7.py video out.mp4  |  python3 reel7.py still out.png 12.3
"""
import math

from reel import (INK, WHITE, YELLOW, SKIN, seg, ease, lerp, rgb, ellipse, fs, fill, line,
                  floaty_text, bub, cat_sit, owner_stand, bg_living)
from reel2 import bowl
import reelkit
import soundkit as sk

DUR = 19.0


def cucumber(ctx, x, y, rot=0.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ellipse(ctx, 0, 0, 85, 24)
    fs(ctx, rgb('#3A7D44'), INK, 5)
    for k in (-50, -10, 30):
        line(ctx, [(k, -10), (k + 30, -10)], rgb('#6DB36F'), 5)
    for (dx, dy) in ((-60, 6), (-20, 10), (20, 4), (55, 9)):
        ellipse(ctx, dx, dy, 3, 3)
        fill(ctx, rgb('#B8E0B0'))
    ellipse(ctx, 84, 0, 7, 9)
    fill(ctx, rgb('#9C6B3E'))
    ctx.restore()


def s_sneak(ctx, t):
    bg_living(ctx, t)
    p = seg(t, 0.2, 3.8)
    ox = lerp(80, 360, p)
    owner_stand(ctx, ox, 1545, 'hold', walk=t * 4, head=dict(eyes='open', mouth='big', look=(1, 0.5), brow=1))
    cucumber(ctx, ox + 70, 1080, -1.3, 0.8)
    ellipse(ctx, ox + 60, 1095, 25, 25)
    fs(ctx, SKIN, INK, 5)
    cat_sit(ctx, 760, 1560, 1.0, facing=-1, eyes='closed', mouth=0.3 + 0.3 * math.sin(t * 18), tail=t * 2)
    bowl(ctx, 760, 1640, 0.8)
    for i in range(2):
        k = ((t * 1.2) + i / 2) % 1
        floaty_text(ctx, 'nom', 900 + i * 40, 1240 - k * 120, 38, math.sin(k * math.pi), 0.15)
    bub(ctx, t, 0.6, 2.8, 380, 620, 'Hehehe... let\'s try the cucumber trick.', (320, 790), size=44, maxw=560)


def s_stare(ctx, t):
    bg_living(ctx, t)
    owner_stand(ctx, 230, 1545, 'down', head=dict(eyes='wide', mouth='grit', look=(1, 0.6)))
    cucumber(ctx, 560, 1640, 0.0)
    eyes = 'closed' if t < 0.6 else ('open' if t < 3.0 else 'half')
    look = (0, 0) if t < 0.6 else (-1, 0.7)
    cat_sit(ctx, 760, 1560, 1.0, facing=-1, eyes=eyes, look=look, tail=t * 1.2)
    bowl(ctx, 760, 1640, 0.4)
    floaty_text(ctx, '*silence*', 540, 1000, 44, seg(t, 1.0, 1.3) * (1 - seg(t, 2.6, 2.9)), -0.05, YELLOW)
    bub(ctx, t, 1.6, 2.9, 760, 1120, '...', (760, 1280), size=60)
    bub(ctx, t, 3.1, 5.0, 760, 1080, 'Is this... a salad?', (760, 1280), size=50)


def s_push(ctx, t):
    bg_living(ctx, t)
    owner_stand(ctx, 230, 1545, 'down', head=dict(eyes='flat', mouth='flat', look=(1, 0.6)))
    paw = 0.5 * ease(seg(t, 0.2, 0.6)) * (1 - ease(seg(t, 2.6, 3.0)))
    cx = lerp(760, 690, ease(seg(t, 0.6, 2.4)))
    cuc_x = 560 - (760 - cx) * 1.6
    cucumber(ctx, cuc_x, 1640, 0.0)
    bowl(ctx, 870, 1650, 0.4)
    cat_sit(ctx, cx, 1560, 1.0, facing=-1, eyes='half', look=(-1, 0), paw=paw, tail=t * 1.2)
    floaty_text(ctx, '*nudge*', cuc_x, 1540, 40, seg(t, 0.6, 0.8) * (1 - seg(t, 2.2, 2.4)), 0.1)
    bub(ctx, t, 1.0, 3.0, 700, 1060, 'You dropped your vegetable.', (690, 1290), size=46, maxw=560)
    bub(ctx, t, 3.1, 5.5, 700, 1060, 'Now fetch my REAL snacks.', (690, 1290), size=46, maxw=560)


SCENES = [(0.0, 4.5, s_sneak), (4.5, 9.5, s_stare), (9.5, 15.0, s_push)]
CAPTIONS = [
    (0.15, 4.5, 'The internet: "Cats are\nscared of cucumbers!"'),
    (4.55, 9.5, 'Keef:'),
    (9.55, 15.0, 'British Shorthair:\nunbothered since forever.'),
]
render = reelkit.make_render(SCENES, CAPTIONS, (15.0, ('Unbothered.', 'Unimpressed.'), 'Follow Keef for more'),
                             punches=(8.0,))


def soundtrack(path):
    tr = sk.Track(DUR)
    tr.music(mute=[(4.6, 7.6)], soft=[(0.0, 4.5)])
    for k in range(8):  # tiptoe plucks
        tr.add(sk.pluck(sk.mtof(72 if k % 2 == 0 else 79), 0.2, 0.2), 0.3 + k * 0.45, 0.45)
    tr.add(sk.cricket(2.8), 5.0, 0.8)
    tr.add(sk.pop(), 0.6, 0.35)
    for tb in (6.1, 7.6, 10.5, 12.6):
        tr.add(sk.pop(), tb, 0.35)
    tr.add(sk.scrape(1.6), 10.1, 0.9)
    tr.add(sk.ding(), 15.0, 0.6)
    tr.save(path)


if __name__ == '__main__':
    reelkit.main(render, DUR, soundtrack)
