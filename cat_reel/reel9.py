"""Reel #9: 'The Spot' - when I sit in Keef's spot.

Usage: python3 reel9.py video out.mp4  |  python3 reel9.py still out.png 12.3
"""
import math

from reel import (INK, WHITE, YELLOW, RED, seg, ease, lerp, rgb, rrect, fs, set_font, draw_lines,
                  floaty_text, bub, cat_sit, cat_walk, owner_stand, owner_sit, bg_living, couch_back)
import reelkit
import soundkit as sk

DUR = 21.0
STARES = (6.6, 8.1, 9.6)


def reserved_sign(ctx, x, y):
    rrect(ctx, x - 90, y - 30, 180, 60, 10)
    fs(ctx, rgb('#E8B931'), INK, 4)
    set_font(ctx, 22)
    draw_lines(ctx, ['RESERVED:', 'KEEF'], x, y, 22, INK)


def s_spot(ctx, t):
    bg_living(ctx, t)
    couch_back(ctx)
    reserved_sign(ctx, 735, 1110)
    sat = 1.5 <= t < 11.5
    # owner
    if t < 1.5:
        owner_stand(ctx, lerp(100, 640, seg(t, 0.0, 1.4)), 1600, 'down', walk=t * 9,
                    head=dict(eyes='open', mouth='smile', look=(1, 0)))
    elif sat:
        n = clamp01((t - 5.6) / 5.0)
        if t < 5.6:
            hd = dict(eyes='closed', mouth='big', blush=0.6)
        else:
            hd = dict(eyes='wide' if t > 9.0 else 'open', mouth='grit' if t > 8.0 else 'flat',
                      look=(1, 0.6), brow=-1, sweat=n)
        owner_sit(ctx, 640 + (math.sin(t * 50) * 3 if t > 9.0 else 0), 1330, head=hd)
    else:
        owner_stand(ctx, 220, 1600, 'down', head=dict(eyes='open', mouth='o' if t < 15.5 else 'flat', look=(1, 0.2), brow=-1))
    # Keef
    if 4.5 <= t < 5.6:
        cat_walk(ctx, lerp(1300, 880, seg(t, 4.5, 5.6)), 1680, 0.85, -1, t * 10, eyes='open', look=(-1, 0), tail=t * 3)
    elif 5.6 <= t < 11.6:
        eyes = 'open' if t < 6.6 else 'evil'
        cat_sit(ctx, 880, 1680, 0.85, facing=-1, eyes=eyes, look=(-1, -0.6), tail=t * 0.6)
    elif 11.6 <= t < 12.1:
        p = ease(seg(t, 11.6, 12.1))
        cat_sit(ctx, lerp(880, 700, p), lerp(1680, 1320, p) - math.sin(p * math.pi) * 150, 0.85,
                facing=-1, eyes='open', look=(-1, 0), squash=-0.4 * math.sin(p * math.pi), tail=t * 3)
    elif 12.1 <= t < 13.2:
        cat_sit(ctx, 700, 1320, 0.85, facing=-1, eyes='closed', blush=0.6, tail=t * 3)
    elif 13.2 <= t < 13.6:
        p = ease(seg(t, 13.2, 13.6))
        cat_sit(ctx, lerp(700, 880, p), lerp(1320, 1680, p) - math.sin(p * math.pi) * 100, 0.85,
                facing=1, eyes='half', tail=t * 3)
    elif 13.6 <= t < 14.8:
        cat_walk(ctx, lerp(880, 1350, seg(t, 13.6, 14.8)), 1680, 0.85, 1, t * 8, eyes='half', look=(1, 0), tail=t * 3)
    for s in STARES:
        floaty_text(ctx, '*stare*', 880, 1290, 48, seg(t, s, s + 0.1) * (1 - seg(t, s + 1.0, s + 1.3)), -0.08, YELLOW)
    floaty_text(ctx, 'ahhh...', 760, 950, 44, seg(t, 1.6, 1.8) * (1 - seg(t, 2.6, 2.9)), 0.1)
    bub(ctx, t, 2.4, 4.4, 380, 640, 'Finally. Some me time.', (560, 860), size=50)
    bub(ctx, t, 7.0, 8.0, 420, 640, '...what?', (580, 860), size=54)
    bub(ctx, t, 8.2, 9.4, 880, 1180, '...', (880, 1360), size=60)
    bub(ctx, t, 9.6, 11.4, 420, 640, 'OKAY OKAY. I\'m moving!', (580, 860), size=50)
    bub(ctx, t, 14.6, 16.2, 330, 700, 'You didn\'t even WANT it?!', (220, 900), size=48, maxw=560)
    bub(ctx, t, 16.3, 17.5, 720, 1050, 'It\'s about the principle.', (1040, 1400), size=46, maxw=560)


def clamp01(v):
    return max(0.0, min(1.0, v))


SCENES = [(0.0, 17.5, s_spot)]
CAPTIONS = [
    (0.15, 11.5, 'When I sit in Keef\'s spot:'),
    (11.55, 17.5, 'He sat there for 1 second.'),
]
render = reelkit.make_render(SCENES, CAPTIONS, (17.5, ('It\'s about', 'the principle.'), 'Follow Keef for more'),
                             punches=STARES + (11.6,))


def soundtrack(path):
    tr = sk.Track(DUR)
    tr.music(mute=[(5.6, 11.5)])
    tr.add(sk.drone(5.9, 55), 5.6, 0.9)
    tr.add(sk.heartbeat(5.6, 100), 5.8, 0.8)
    for s in STARES:
        tr.add(sk.whoosh(0.3), s - 0.05, 0.9)
    for tb in (2.4, 7.0, 8.2, 9.6, 14.6, 16.3):
        tr.add(sk.pop(), tb, 0.35)
    tr.add(sk.whoosh(0.4), 11.5, 0.8)
    tr.add(sk.boing(0.35, 220, 650), 11.6, 0.4)
    tr.add(sk.boing(0.3, 600, 250), 13.2, 0.4)
    tr.add(sk.ding(), 17.5, 0.6)
    tr.save(path)


if __name__ == '__main__':
    reelkit.main(render, DUR, soundtrack)
