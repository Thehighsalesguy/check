"""Reel #8: 'Keef's Job Interview'.

Usage: python3 reel8.py video out.mp4  |  python3 reel8.py still out.png 12.3
"""
import math

from reel import (INK, WHITE, YELLOW, SKIN, seg, ease, lerp, rgb, ellipse, rrect, fs, fill, line,
                  set_font, draw_lines, floaty_text, bub, cat_sit, owner_sit, owner_stand, bg_office)
import reelkit
import soundkit as sk

DUR = 25.5
SWAP = 17.4  # Keef takes the interviewer's chair


def office_chair(ctx, x, seat_y, back=True):
    if back:
        rrect(ctx, x - 120, seat_y - 380, 240, 330, 50)
        fs(ctx, rgb('#3D405B'), INK, 6)
    rrect(ctx, x - 150, seat_y - 20, 300, 56, 24)
    fs(ctx, rgb('#5B5F7E'), INK, 6)
    ctx.rectangle(x - 12, seat_y + 36, 24, 120)
    fs(ctx, rgb('#9AA0AA'), INK, 4)
    for dx in (-110, 0, 110):
        line(ctx, [(x, seat_y + 156), (x + dx, seat_y + 190)], INK, 10)
        ellipse(ctx, x + dx, seat_y + 196, 14, 10)
        fill(ctx, INK)


def tie(ctx, x, y, s):
    ctx.move_to(x - 14 * s, y - 150 * s)
    ctx.line_to(x + 14 * s, y - 150 * s)
    ctx.line_to(x + 8 * s, y - 128 * s)
    ctx.line_to(x - 8 * s, y - 128 * s)
    ctx.close_path()
    fs(ctx, rgb('#9D0208'), INK, 4)
    ctx.move_to(x - 8 * s, y - 128 * s)
    ctx.line_to(x + 8 * s, y - 128 * s)
    ctx.line_to(x + 22 * s, y - 50 * s)
    ctx.line_to(x, y - 30 * s)
    ctx.line_to(x - 22 * s, y - 50 * s)
    ctx.close_path()
    fs(ctx, rgb('#C1121F'), INK, 4)
    for k in (-105, -80):
        line(ctx, [(x - 10 * s, y + k * s), (x + 12 * s, y + (k - 12) * s)], rgb('#FFB703'), 4)


def clipboard(ctx, x, y):
    rrect(ctx, x - 55, y - 75, 110, 140, 8)
    fs(ctx, rgb('#B5835A'), INK, 4)
    rrect(ctx, x - 44, y - 58, 88, 112, 4)
    fill(ctx, WHITE)
    for k in range(4):
        line(ctx, [(x - 32, y - 36 + k * 24), (x + 30, y - 36 + k * 24)], rgb('#AAB2BD'), 4)


def coffee_table(ctx):
    rrect(ctx, 400, 1410, 280, 28, 8)
    fs(ctx, rgb('#B97A47'), INK, 5)
    for lx in (420, 650):
        ctx.rectangle(lx, 1436, 16, 130)
        fs(ctx, rgb('#8E5A31'), INK, 4)
    rrect(ctx, 460, 1350, 150, 60, 6)
    fs(ctx, WHITE, INK, 4)
    set_font(ctx, 24)
    draw_lines(ctx, ['CANDIDATE:', 'KEEF'], 535, 1380, 24, INK)


def keef_seated(ctx, x, seat_y, t, eyes='half', look=(-1, 0)):
    cat_sit(ctx, x, seat_y, 0.95, facing=-1, eyes=eyes, look=look, tail=t * 1.2)
    tie(ctx, x, seat_y, 0.95)


QA = [  # (question start, question, answer)
    (3.0, 'So, Keef. What are your strengths?', 'Sitting.'),
    (7.2, '...And your weaknesses?', 'Standing.'),
    (11.4, 'Where do you see yourself in 5 years?', 'In your chair.'),
    (15.6, 'Why should we hire you?', None),
]


def s_interview(ctx, t):
    bg_office(ctx, t)
    if t < SWAP:
        office_chair(ctx, 270, 1330)
        office_chair(ctx, 810, 1330)
        coffee_table(ctx)
        talking = any(q <= t < q + 1.8 for q, _, _ in QA) or t < 2.6
        hd = dict(eyes='open', mouth='smile' if talking else 'flat', look=(1, 0.2))
        if 9.2 <= t < 11.2 or 13.4 <= t < 15.4:
            hd = dict(eyes='flat', mouth='flat', look=(1, 0.2), brow=0.6)
        owner_sit(ctx, 270, 1330, head=hd, hands=[(310, 1150), (380, 1170)])
        clipboard(ctx, 345, 1120)
        ellipse(ctx, 380, 1170, 25, 25)
        fs(ctx, SKIN, INK, 5)
        keef_seated(ctx, 810, 1310, t)
    else:
        lt = t - SWAP
        office_chair(ctx, 810, 1330)
        office_chair(ctx, 270, 1330)
        coffee_table(ctx)
        keef_seated(ctx, 270, 1310, t, eyes='closed' if lt < 1.8 else 'half', look=(1, 0))
        owner_stand(ctx, 810, 1545, 'hold', head=dict(eyes='wide' if lt < 1.5 else 'flat', mouth='o' if lt < 1.5 else 'flat', look=(-1, 0.3)))
        clipboard(ctx, 870, 1095)
        ellipse(ctx, 870, 1095, 25, 25)
        fs(ctx, SKIN, INK, 5)
        floaty_text(ctx, 'POOF!', 540, 1150, 70, 1 - seg(lt, 0.4, 0.7), -0.1, YELLOW)
    bub(ctx, t, 0.4, 2.6, 340, 640, 'Thank you for coming in, Keef.', (300, 840), size=46, maxw=560)
    for q, question, answer in QA:
        bub(ctx, t, q, q + 1.8, 380, 640, question, (300, 840), size=46, maxw=600)
        if answer:
            bub(ctx, t, q + 1.9, q + 4.1, 790, 900, answer, (800, 1060), size=56)
    bub(ctx, t, 15.6 + 1.9, 15.6 + 3.9, 380, 900, 'I already took your chair.', (300, 1060), size=48, maxw=560)
    bub(ctx, t, 19.6, 21.0, 790, 700, '...You\'re hired.', (810, 840), size=50)
    bub(ctx, t, 21.0, 22.5, 380, 900, 'Obviously.', (300, 1060), size=54)


SCENES = [(0.0, 22.5, s_interview)]
CAPTIONS = [
    (0.15, 19.5, 'Keef\'s first job interview.'),
    (19.55, 22.5, 'Keef got the job.'),
]
render = reelkit.make_render(SCENES, CAPTIONS, (22.5, ('Keef: Head of the', 'Sitting Department'), 'Follow Keef for more'),
                             punches=(SWAP,))


def soundtrack(path):
    tr = sk.Track(DUR)
    tr.music(soft=[(0.0, 22.5)])
    for q, _, a in QA:
        tr.add(sk.pop(), q, 0.35)
        tr.add(sk.pop(), q + 1.9, 0.35)
        if a:
            tr.add(sk.rimshot(), q + 2.6, 0.8)
    tr.add(sk.whoosh(0.4), SWAP, 0.9)
    tr.add(sk.boing(0.3, 300, 900), SWAP + 0.1, 0.5)
    tr.add(sk.rimshot(), SWAP + 0.9, 0.8)
    for tb in (0.4, 19.6, 21.0):
        tr.add(sk.pop(), tb, 0.35)
    tr.add(sk.chimes(), 22.5, 0.8)
    tr.save(path)


if __name__ == '__main__':
    reelkit.main(render, DUR, soundtrack)
