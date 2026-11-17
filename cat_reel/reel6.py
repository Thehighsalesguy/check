"""Reel #6: 'The Vet Carrier' - Keef's 3 stages of vet-day grief.

Usage: python3 reel6.py video out.mp4  |  python3 reel6.py still out.png 12.3
"""
import math

from reel import (INK, WHITE, YELLOW, SKIN, clamp, seg, ease, lerp, rgb, ellipse, rrect, fs, fill, line,
                  set_font, draw_lines, floaty_text, bub, cat_sit, cat_curled, owner_stand,
                  bg_living, couch_back, zzz)
from reel2 import exclaim
import reelkit
import soundkit as sk

DUR = 22.0


def carrier(ctx, x, y, s=1.0, door_open=True, inside=None):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.new_sub_path()
    ctx.arc(0, -262, 70, math.pi, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(22)
    ctx.stroke()
    ctx.new_sub_path()
    ctx.arc(0, -262, 70, math.pi, 2 * math.pi)
    ctx.set_source_rgb(*rgb('#5E8FB8'))
    ctx.set_line_width(12)
    ctx.stroke()
    rrect(ctx, -210, -270, 420, 270, 44)
    fs(ctx, rgb('#7FB3D5'), INK, 6)
    rrect(ctx, -140, -225, 280, 200, 30)
    fs(ctx, rgb('#2C2A3A'), INK, 5)
    if inside:
        ctx.save()
        rrect(ctx, -140, -225, 280, 200, 30)
        ctx.clip()
        inside(ctx)
        ctx.restore()
    if door_open:
        rrect(ctx, -300, -228, 80, 206, 10)
        fs(ctx, rgb('#BFC7D1'), INK, 4)
        for gx in range(-290, -225, 16):
            line(ctx, [(gx, -220), (gx, -30)], rgb('#7A8494'), 4)
    else:
        for gx in range(-120, 121, 30):
            line(ctx, [(gx, -222), (gx, -28)], rgb('#BFC7D1'), 7)
    for vx in (-170, 170):
        for vy in (-200, -150, -100):
            ellipse(ctx, vx, vy, 10, 10)
            fill(ctx, rgb('#5E8FB8'))
    ctx.restore()


def keef_in_carrier(eyes, blush=0.0, t=0.0):
    def draw(ctx):
        cat_sit(ctx, 0, 30, 0.62, facing=-1, eyes=eyes, blush=blush, tail=t)
    return draw


def plinth(ctx, x, y):
    rrect(ctx, x - 170, y, 340, 150, 8)
    fs(ctx, rgb('#ECE6DA'), INK, 5)
    rrect(ctx, x - 190, y - 22, 380, 30, 6)
    fs(ctx, rgb('#F7F2E8'), INK, 5)
    rrect(ctx, x - 110, y + 40, 220, 70, 6)
    fs(ctx, rgb('#E8B931'), INK, 3)
    set_font(ctx, 22)
    draw_lines(ctx, ['"Keef, Refusing"', 'Marble, 2026'], x, y + 75, 22, INK)


def owner_with_carrier(ctx, x, t, hd):
    owner_stand(ctx, x, 1545, 'hold', head=hd)
    hx, hy = x + 60, 1095
    carrier(ctx, hx + 10, hy + 210, 0.55, door_open=True)
    ellipse(ctx, hx, hy, 25, 25)
    fs(ctx, SKIN, INK, 5)


def s_tuesday(ctx, t, later=False):
    bg_living(ctx, t)
    hd = dict(eyes='closed', mouth='big', blush=1.0) if not later else dict(eyes='flat', mouth='flat', look=(1, 0.5), brow=0.8)
    owner_stand(ctx, 220, 1545, 'down', head=hd)
    carrier(ctx, 680, 1600, 1.0, True, keef_in_carrier('sleep' if later else 'closed', 0.9, t))
    if later:
        zzz(ctx, t, 720, 1300)
        bub(ctx, t, 1.0, 3.6, 330, 640, 'Unbelievable.', (240, 790), size=56)
    else:
        bub(ctx, t, 0.5, 2.4, 330, 640, 'Aww, he LOVES his carrier!', (240, 790), size=48, maxw=560)
        bub(ctx, t, 2.6, 5.4, 720, 1100, 'My house. My rules.', (690, 1400), size=50)


def s_vetday(ctx, t):
    bg_living(ctx, t)
    owner_with_carrier(ctx, 220, t, dict(eyes='closed', mouth='big', blush=0.6))
    cat_sit(ctx, 780, 1600, 1.0, facing=-1, eyes='wide' if t > 0.7 else 'open', look=(-1, 0), tail=t * 2)
    exclaim(ctx, 780, 1240, t, 0.7)
    bub(ctx, t, 0.1, 1.5, 360, 620, 'Keef~ time for the VET!', (260, 790), size=48)


def s_puddle(ctx, t):
    bg_living(ctx, t)
    owner_with_carrier(ctx, 220, t, dict(eyes='open', mouth='flat', look=(1, 0.6)))
    ctx.save()
    ctx.translate(720, 1620)
    ctx.scale(1.5, 0.5 + 0.03 * math.sin(t * 6))
    ctx.translate(-720, -1620)
    cat_curled(ctx, 720, 1620, 1.0, facing=-1, eyes='wide', look=(-1, 0))
    ctx.restore()
    floaty_text(ctx, '*becomes liquid*', 720, 1380, 46, seg(t, 0.3, 0.5), -0.05, YELLOW)


def s_statue(ctx, t):
    bg_living(ctx, t)
    owner_with_carrier(ctx, 220, t, dict(eyes='open', mouth='flat', look=(1, 0), brow=1))
    plinth(ctx, 760, 1470)
    cat_sit(ctx, 760, 1450, 0.95, facing=-1, eyes='wide', look=(-1, 0), tail=0.0)
    floaty_text(ctx, '*refuses to bend*', 760, 1060, 46, seg(t, 0.3, 0.5), 0.05, YELLOW)


def s_nothome(ctx, t):
    bg_living(ctx, t)
    couch_back(ctx)
    rrect(ctx, 200, 1478, 680, 44, 6)
    fill(ctx, rgb('#1B1724'))
    blink = (t % 1.6) < 0.12
    for sx in (-1, 1):
        if blink:
            line(ctx, [(560 + sx * 26 - 10, 1500), (560 + sx * 26 + 10, 1500)], rgb('#C8F07A'), 4)
        else:
            ellipse(ctx, 560 + sx * 26, 1500, 11, 8)
            fill(ctx, rgb('#C8F07A'))
    owner_with_carrier(ctx, 170, t, dict(eyes='open', mouth='smile' if t > 1.6 else 'flat', look=(1, 1)))
    bub(ctx, t, 0.2, 1.5, 330, 640, 'Keef?', (200, 790), size=56)
    bub(ctx, t, 1.6, 3.0, 360, 640, '...Treats?', (200, 790), size=56)
    bub(ctx, t, 1.9, 3.6, 640, 1100, 'Keef is not home. Leave a message.', (560, 1470), size=44, maxw=560)


SCENES = [
    (0.0, 5.5, lambda c, t: s_tuesday(c, t)),
    (5.5, 7.0, s_vetday),
    (7.0, 9.2, s_puddle),
    (9.2, 11.4, s_statue),
    (11.4, 15.0, s_nothome),
    (15.0, 19.0, lambda c, t: s_tuesday(c, t, later=True)),
]
CAPTIONS = [
    (0.15, 5.5, 'Keef on a normal Tuesday:'),
    (5.55, 7.0, 'Keef on vet day:'),
    (7.05, 9.2, 'Stage 1: Puddle.'),
    (9.25, 11.4, 'Stage 2: Statue.'),
    (11.45, 15.0, 'Stage 3: He\'s not home.'),
    (15.05, 19.0, 'The next normal Tuesday:'),
]
render = reelkit.make_render(SCENES, CAPTIONS, (19.0, ('Tag someone whose cat', 'hates the vet'), 'Follow Keef for more'),
                             punches=(6.2, 7.0, 9.2, 11.4))


def soundtrack(path):
    tr = sk.Track(DUR)
    tr.music(mute=[(6.1, 7.0)], soft=[(11.4, 15.0)])
    for tb in (0.5, 2.6, 5.6, 13.0, 13.9, 16.0):
        tr.add(sk.pop(), tb, 0.35)
    tr.add(sk.sting(), 6.2, 0.9)
    tr.add(sk.squish(), 7.05, 0.9)
    tr.add(sk.doink(), 9.25, 0.7)
    tr.add(sk.whoosh(0.4), 11.4, 0.9)
    tr.add(sk.crinkle(0.8), 12.6, 0.8)
    tr.add(sk.ding(), 19.0, 0.6)
    tr.save(path)


if __name__ == '__main__':
    reelkit.main(render, DUR, soundtrack)
