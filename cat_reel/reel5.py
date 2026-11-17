"""Reel #5: 'Keef at 3PM vs Keef at 3AM'.

Usage:
  python3 reel5.py video out_silent.mp4
  python3 reel5.py still out.png 12.3
"""
import math
import subprocess
import sys

import cairo

from reel import (W, H, FPS, PI, INK, WHITE, CAT, YELLOW, RED, SKIN, clamp, seg, ease, eob, lerp, rgb,
                  ellipse, rrect, fs, fill, line, set_font, draw_lines, floaty_text, bub, burst,
                  cat_sit, cat_walk, cat_curled, owner_stand, owner_head, bg_living, bg_bedroom,
                  bed_back, blanket, window, caption, end_card, zzz)
from reel2 import cat_run, dust

DUR = 23.0


def toy_mouse(ctx, x, y, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.move_to(-30, 0)
    ctx.curve_to(-70, 10, -80, -20, -100, -10)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    ellipse(ctx, 0, -14, 36, 22)
    fs(ctx, rgb('#9AA0AA'), INK, 4)
    ellipse(ctx, 24, -32, 11, 11)
    fs(ctx, rgb('#FFB4C2'), INK, 3)
    ellipse(ctx, 32, -10, 3, 3)
    fill(ctx, INK)
    ctx.restore()


def wall_clock(ctx, cx, cy, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ellipse(ctx, 0, 0, 78, 78)
    fs(ctx, WHITE, INK, 7)
    line(ctx, [(0, 0), (0, -55)], INK, 6)
    line(ctx, [(0, 0), (34, 20)], INK, 8)
    ellipse(ctx, 0, 0, 7, 7)
    fill(ctx, RED)
    ctx.restore()


def eye_bags(ctx, x, y):
    for sx in (-1, 1):
        ctx.new_sub_path()
        ctx.arc(x + sx * 30, y + 6, 15, PI * 0.15, PI * 0.85)
        ctx.set_source_rgba(0.45, 0.3, 0.55, 0.9)
        ctx.set_line_width(5)
        ctx.stroke()


def mug(ctx, x, y, t):
    rrect(ctx, x - 30, y - 50, 60, 70, 10)
    fs(ctx, rgb('#E76F51'), INK, 4)
    ctx.new_sub_path()
    ctx.arc(x + 34, y - 15, 15, -PI / 2, PI / 2)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    for i in (-10, 10):
        ctx.move_to(x + i, y - 60)
        ctx.curve_to(x + i + 10 * math.sin(t * 3 + i), y - 80, x + i - 10, y - 95, x + i, y - 115)
        ctx.set_source_rgba(1, 1, 1, 0.8)
        ctx.set_line_width(4)
        ctx.stroke()


def scene_day(ctx, t):
    """0-6s: 3PM - certified furniture."""
    bg_living(ctx, t)
    owner_stand(ctx, 230, 1545, 'down', 'hold', ease(seg(t, 0.8, 1.3)) * (1 - ease(seg(t, 1.6, 1.9))),
                head=dict(eyes='open', mouth='smile' if t < 4.5 else 'flat', look=(1, 0.5), brow=0 if t < 4.5 else 0.8))
    # toy mouse thrown in an arc
    if t >= 1.5:
        p = seg(t, 1.5, 2.1)
        mx = lerp(300, 800, p)
        my = lerp(1100, 1610, p) - math.sin(p * PI) * 260
        toy_mouse(ctx, mx, my, (1 - p) * 4)
    look = (1, 0.4) if 2.1 <= t < 2.8 else (-0.3, -0.2)
    eyes = 'open' if 2.1 <= t < 2.8 else 'half'
    cat_curled(ctx, 600, 1600, 1.05, facing=-1, eyes=eyes, look=look, breath=t * 1.5)
    floaty_text(ctx, '*has not moved in 4 hours*', 560, 1320, 42, seg(t, 0.3, 0.6) * (1 - seg(t, 1.4, 1.6)), -0.05, YELLOW)
    bub(ctx, t, 2.9, 4.5, 700, 1080, 'Not now. I\'m busy.', (690, 1420), size=48)
    bub(ctx, t, 4.6, 6.0, 330, 640, 'Busy doing WHAT?', (250, 790))


def night_overlay(ctx):
    ctx.rectangle(-300, -300, W + 600, H + 600)
    ctx.set_source_rgba(0.05, 0.05, 0.22, 0.5)
    ctx.fill()


def scene_night(ctx, t):
    """6-14.5s: 3AM - zoomies."""
    bg_bedroom(ctx, t)
    window(ctx, 650, 520, 300, 300, rgb('#1D2B53'), rgb('#3E4C8A'), night=True)
    # the wall clock gets knocked off
    falling = t >= 3.0
    if falling:
        ellipse(ctx, 250, 640, 84, 84)
        fill(ctx, rgb('#FBE7D3'))
    bed_back(ctx)
    awake = t >= 3.4
    hd = dict(eyes='sleep', mouth='snore') if not awake else dict(eyes='wide', mouth='flat', look=(1, -0.2))
    if t >= 5.2:
        hd = dict(eyes='flat', mouth='flat', look=(1, -0.2))
    owner_head(ctx, 268, 1135, 78, **hd)
    blanket(ctx)
    night_overlay(ctx)
    if not awake:
        zzz(ctx, t, 300, 1030)
    if falling:
        p = clamp((t - 3.0) / 0.4)
        wall_clock(ctx, 250 + p * 30, lerp(640, 1560, p * p), p * 3)
        burst(ctx, 280, 1450, 'BONK!', t, 3.4, 4.1, size=80, rot=-0.1)
    # zoomies
    if 0.4 <= t < 1.0:
        p = seg(t, 0.4, 1.0)
        cat_run(ctx, lerp(-250, 1350, p), 1660, 0.85, 1, t)
    elif 1.2 <= t < 1.8:
        p = seg(t, 1.2, 1.8)
        cat_run(ctx, lerp(1300, -250, p), 1180, 0.7, -1, t, look=(-1, 0))
    elif 2.0 <= t < 2.9:
        p = ease(seg(t, 2.0, 2.9))
        cat_sit(ctx, lerp(900, 330, p), lerp(1650, 900, p) - math.sin(p * PI) * 250, 0.7,
                facing=-1, eyes='wide', look=(-1, 0), squash=-0.5 * math.sin(p * PI), tail=t * 6)
    elif 2.9 <= t < 3.6:
        p = ease(seg(t, 2.9, 3.6))
        cat_sit(ctx, lerp(330, 560, p), lerp(900, 1180, p) - math.sin(p * PI) * 120, 0.7,
                facing=1, eyes='wide', look=(1, 0), tail=t * 6)
    elif t >= 3.6:
        cat_sit(ctx, 430, 1185, 0.75, facing=-1, eyes='wide', look=(-1, 0), tail=t * 3)
    if 2.4 <= t < 3.1:
        floaty_text(ctx, 'PARKOUR!', 380, 760, 60, 1 - seg(t, 2.9, 3.1), -0.1, YELLOW)
    floaty_text(ctx, 'brrrrrrrm', 420, 1430, 44, seg(t, 0.4, 0.5) * (1 - seg(t, 1.8, 2.0)), 0.08)
    dust(ctx, 640, 1600, t - 0.7)
    bub(ctx, t, 5.2, 6.7, 380, 800, 'Keef. It\'s 3AM.', (290, 1040), size=50)
    bub(ctx, t, 6.8, 8.5, 640, 860, 'I\'m aware.', (470, 1000), size=52)


def scene_after(ctx, t):
    """14.5-20s: next day, 3PM again."""
    bg_living(ctx, t)
    hd = dict(eyes='flat', mouth='flat', look=(1, 0.6), brow=-0.5)
    owner_stand(ctx, 260, 1545, 'hold', head=hd)
    eye_bags(ctx, 260, 880)
    mug(ctx, 320, 1100, t)
    ellipse(ctx, 320, 1095, 25, 25)
    fs(ctx, SKIN, INK, 5)
    cat_curled(ctx, 700, 1600, 1.05, facing=-1, eyes='sleep', breath=t * 1.5, blush=0.6)
    zzz(ctx, t, 760, 1400)
    bub(ctx, t, 0.6, 2.6, 330, 640, 'Oh NOW he\'s sleeping.', (260, 790), size=48)
    bub(ctx, t, 2.8, 5.5, 700, 1000, 'Must rest. Big night tonight.', (720, 1400), thought=True, size=44, maxw=560)


CAPTIONS5 = [
    (0.15, 6.0, 'Keef at 3PM:'),
    (6.05, 14.5, 'Keef at 3AM:'),
    (14.55, 20.0, 'The next day, 3PM:'),
]
SCENES5 = [0.0, 6.0, 14.5, 23.0]
PUNCH5 = [9.4]


def render(ctx, t):
    ctx.save()
    z = 1.0
    for p in PUNCH5:
        if t >= p:
            z += 0.06 * math.exp(-(t - p) * 7)
    ctx.translate(540, 1150)
    ctx.scale(z * 1.1, z * 1.1)
    ctx.translate(-540, -1150)
    if t < 6.0:
        scene_day(ctx, t)
    elif t < 14.5:
        scene_night(ctx, t - 6.0)
    else:
        scene_after(ctx, t - 14.5)
    ctx.restore()
    caption(ctx, t, CAPTIONS5)
    if t >= 20.0:
        end_card(ctx, t - 20.0, ('Calm by day.', 'Chaos by night.'), 'Follow Keef for more')
    for s in SCENES5[1:-1]:
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
