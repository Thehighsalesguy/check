"""Reel #4: 'Expensive bed vs. cardboard box' starring Keef.

Usage:
  python3 reel4.py video out_silent.mp4
  python3 reel4.py still out.png 12.3
"""
import math
import subprocess
import sys

import cairo

from reel import (W, H, FPS, PI, INK, WHITE, CAT, YELLOW, RED, clamp, seg, ease, eob, lerp, rgb,
                  ellipse, rrect, fs, fill, line, set_font, draw_lines, floaty_text, bub,
                  cat_sit, cat_walk, owner_stand, owner_sit, bg_living, bg_night, caption, end_card, zzz)
from reel2 import cat_bed, cardboard_box

DUR = 23.0
GOLD = rgb('#E8B931')


def sparkle(ctx, x, y, r, alpha):
    ctx.move_to(x, y - r)
    for a in range(1, 8):
        ang = a * PI / 4
        rr = r if a % 2 == 0 else r * 0.3
        ctx.line_to(x + math.sin(ang) * rr, y - math.cos(ang) * rr)
    ctx.close_path()
    ctx.set_source_rgba(*YELLOW, alpha)
    ctx.fill()


def luxury_bed(ctx, x, y, t, shine=True):
    cat_bed(ctx, x, y)
    # little crown + tag
    ctx.move_to(x - 40, y - 95)
    for px, py in ((-40, -135), (-20, -110), (0, -145), (20, -110), (40, -135), (40, -95)):
        ctx.line_to(x + px, y + py)
    ctx.close_path()
    fs(ctx, GOLD, INK, 4)
    rrect(ctx, x - 240, y - 150, 130, 50, 10)
    fs(ctx, WHITE, INK, 4)
    set_font(ctx, 26)
    draw_lines(ctx, ['LUXURY'], x - 175, y - 125, 26, rgb('#B5212E'))
    line(ctx, [(x - 110, y - 125), (x - 70, y - 80)], INK, 3)
    if shine:
        for i, (dx, dy) in enumerate(((-170, -110), (150, -60), (-60, -170), (200, -170))):
            sparkle(ctx, x + dx, y + dy, 22, 0.5 + 0.5 * math.sin(t * 5 + i * 1.7))


def empty_box(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    by = -60
    for sx in (-1, 1):
        ctx.move_to(sx * 150, by - 190)
        ctx.line_to(sx * 200, by - 250)
        ctx.line_to(sx * 70, by - 250)
        ctx.line_to(sx * 20, by - 190)
        ctx.close_path()
        fs(ctx, rgb('#C8955E'), INK, 5)
    rrect(ctx, -150, by - 190, 300, 250, 6)
    fs(ctx, rgb('#D9A86C'), INK, 5)
    line(ctx, [(-60, by - 120), (60, by - 120)], rgb('#A87A45'), 5)
    set_font(ctx, 28)
    draw_lines(ctx, ['FRAGILE'], 0, by - 80, 28, rgb('#A87A45'))
    ctx.restore()


def scene_present(ctx, t):
    """0-6.5s: owner presents the bed, Keef inspects it."""
    bg_living(ctx, t)
    luxury_bed(ctx, 480, 1600, t)
    empty_box(ctx, 830, 1580, 0.9)
    arm_t = ease(seg(t, 0.3, 0.6)) * (1 - ease(seg(t, 2.6, 3.0)))
    hd = dict(eyes='closed', mouth='big', blush=1.0) if t < 3.0 else dict(eyes='open', mouth='smile', look=(1, 0.5))
    owner_stand(ctx, 190, 1545, 'down', 'open', arm_t, head=hd)
    if 2.2 <= t < 3.6:
        p = seg(t, 2.2, 3.6)
        cat_walk(ctx, lerp(1300, 700, p), 1650, 0.8, -1, t * 10, eyes='open', look=(-1, 0), tail=t * 3)
    elif t >= 3.6:
        cat_sit(ctx, 700, 1650, 0.8, facing=-1, eyes='half' if t > 4.6 else 'open', look=(-1, 0.6), tail=t * 2)
        floaty_text(ctx, 'sniff sniff', 640, 1290, 42, seg(t, 3.7, 3.9) * (1 - seg(t, 4.6, 4.8)), -0.08)
    bub(ctx, t, 0.5, 2.6, 360, 640, 'Ta-da! Only the BEST for my boy!', (220, 790), size=46, maxw=560)
    bub(ctx, t, 4.8, 6.5, 720, 1100, 'Hm. No.', (700, 1340), size=52)


def scene_box(ctx, t):
    """6.5-13s: Keef chooses the box."""
    bg_living(ctx, t)
    luxury_bed(ctx, 480, 1600, t, shine=False)
    hd = dict(eyes='open', mouth='smile', look=(1, 0.5))
    if t >= 1.7:
        hd = dict(eyes='wide', mouth='o', look=(1, 0.5))
    if t >= 3.2:
        hd = dict(eyes='open', mouth='sad', brow=-1, look=(1, 0.5))
    owner_stand(ctx, 190, 1545, 'down', head=hd)
    if t < 1.0:
        p = seg(t, 0.0, 1.0)
        empty_box(ctx, 830, 1580, 0.9)
        cat_walk(ctx, lerp(700, 760, p), 1650, 0.8, 1, t * 10, eyes='open', look=(1, 0), tail=t * 3)
    elif t < 1.5:
        p = ease(seg(t, 1.0, 1.5))
        empty_box(ctx, 830, 1580, 0.9)
        cat_sit(ctx, lerp(760, 830, p), lerp(1650, 1380, p) - math.sin(p * PI) * 160, 0.7,
                facing=1, eyes='open', look=(1, 1), squash=-0.4 * math.sin(p * PI), tail=t * 3)
    else:
        sq = math.exp(-(t - 1.5) * 7) * 0.12
        ctx.save()
        ctx.translate(830, 1580)
        ctx.scale(1 + sq, 1 - sq)
        ctx.translate(-830, -1580)
        cardboard_box(ctx, 830, 1580, 0.9, None, eyes='closed', look=(0, 0))
        ctx.restore()
        floaty_text(ctx, '*squish*', 760, 1180, 44, seg(t, 1.5, 1.7) * (1 - seg(t, 2.6, 2.9)), 0.1, YELLOW)
    bub(ctx, t, 2.0, 3.6, 720, 1020, 'Perfect.', (820, 1260), size=54)
    bub(ctx, t, 3.6, 6.5, 360, 640, 'That box was FREE.', (220, 790), size=50)


def scene_later(ctx, t):
    """13-19s: three days later."""
    bg_night(ctx, t)
    owner_sit(ctx, 230, 1585, head=dict(eyes='flat', mouth='flat', look=(1, 0.3)), legs=False)
    luxury_bed(ctx, 530, 1620, t, shine=False)
    cardboard_box(ctx, 850, 1600, 0.9, None, eyes='sleep', look=(0, 0))
    zzz(ctx, t, 900, 1230)
    bub(ctx, t, 0.8, 3.0, 380, 820, '...he still won\'t use it.', (240, 1010), size=48)
    bub(ctx, t, 3.0, 5.8, 380, 820, 'I\'m keeping the receipt.', (240, 1010), size=48)


def review_card(ctx, t):
    """19-23s: Keef's official ratings."""
    a = ease(seg(t, 0, 0.3))
    ctx.rectangle(0, 0, W, H)
    ctx.set_source_rgba(0.1, 0.06, 0.2, 0.65 * a)
    ctx.fill()
    rows = [('Luxury bed', '2/10', '"No."'), ('Cardboard box', '11/10', '"Exquisite."')]
    set_font(ctx, 64)
    draw_lines(ctx, ['KEEF\'S REVIEWS'], 540, 560, 64, YELLOW, outline=INK, ow=12) if a > 0.5 else None
    for i, (name, score, quote) in enumerate(rows):
        p = seg(t, 0.4 + i * 0.6, 0.7 + i * 0.6)
        if p <= 0:
            continue
        ctx.save()
        ctx.translate(540, 780 + i * 290)
        s = lerp(0.6, 1, eob(p))
        ctx.scale(s, s)
        rrect(ctx, -400, -110, 800, 220, 30)
        fs(ctx, WHITE, INK, 6)
        set_font(ctx, 52)
        ctx.move_to(-360, -20)
        ctx.text_path(name)
        fill(ctx, INK)
        set_font(ctx, 40, bold=False)
        ctx.move_to(-360, 55)
        ctx.text_path(quote + '  — Keef')
        fill(ctx, rgb('#666666'))
        set_font(ctx, 76)
        sc = RED if i == 0 else rgb('#2A9D8F')
        ext = ctx.text_extents(score)
        ctx.move_to(370 - ext.x_advance, 25)
        ctx.text_path(score)
        fill(ctx, sc)
        ctx.restore()
    p = seg(t, 2.2, 2.5)
    if p > 0:
        ctx.push_group()
        set_font(ctx, 46)
        draw_lines(ctx, ['Follow Keef for more'], 540, 1420, 46, YELLOW, outline=INK, ow=10)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(p)


CAPTIONS4 = [
    (0.15, 6.5, 'Bought Keef a fancy\nnew bed.'),
    (6.55, 13.0, 'He chose... the box.'),
    (13.05, 19.0, '3 days later:'),
]
SCENES4 = [0.0, 6.5, 13.0, 23.0]


def render(ctx, t):
    ctx.save()
    ctx.translate(540, 1150)
    ctx.scale(1.1, 1.1)
    ctx.translate(-540, -1150)
    if t < 6.5:
        scene_present(ctx, t)
    elif t < 13.0:
        scene_box(ctx, t - 6.5)
    else:
        scene_later(ctx, min(t, 19.0) - 13.0)
    ctx.restore()
    caption(ctx, t, CAPTIONS4)
    if t >= 19.0:
        review_card(ctx, t - 19.0)
    for s in SCENES4[1:-1]:
        if s <= t < s + 0.2:
            ctx.rectangle(0, 0, W, H)
            ctx.set_source_rgba(1, 1, 1, 1 - seg(t, s, s + 0.2))
            ctx.fill()
    if t < 0.4:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0, 0, 0, 1 - seg(t, 0, 0.4))
        ctx.fill()
    if t > DUR - 0.3:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0, 0, 0, seg(t, DUR - 0.3, DUR))
        ctx.fill()


def frame_surface(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    render(ctx, t)
    surf.flush()
    return surf


def main():
    mode, out = sys.argv[1], sys.argv[2]
    if mode == 'still':
        frame_surface(float(sys.argv[3])).write_to_png(out)
        return
    proc = subprocess.Popen([
        'ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out
    ], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        proc.stdin.write(bytes(frame_surface(i / FPS).get_data()))
    proc.stdin.close()
    proc.wait()


if __name__ == '__main__':
    main()
