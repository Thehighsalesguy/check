"""'Food Radar' - reel #2: Keef ignores everything... except food.

Reuses the characters and rooms from reel.py.
Usage:
  python3 reel2.py video out_silent.mp4
  python3 reel2.py still out.png 12.3
"""
import math
import subprocess
import sys

import cairo

from reel import (W, H, FPS, PI, INK, WHITE, CAT, CAT_DK, PINK, RED, YELLOW, SKIN,
                  clamp, seg, ease, eob, lerp, rgb, ellipse, rrect, fs, fill, line,
                  set_font, draw_lines, floaty_text, heart, bub, burst, thick,
                  cat_head, cat_sit, cat_walk, cat_curled, owner_stand, owner_head, arm,
                  bg_living, bg_bedroom, bg_kitchen, bed_back, blanket, caption, end_card, zzz)

DUR = 30.0


# ---------------------------------------------------------------- props
def food_bag(ctx, x, y, rot=0.0, s=1.0):
    """Bag held at its top-centre (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(-62, 0)
    ctx.line_to(62, 0)
    ctx.line_to(78, 190)
    ctx.curve_to(60, 205, -60, 205, -78, 190)
    ctx.close_path()
    fs(ctx, rgb('#E63946'), INK, 5)
    rrect(ctx, -66, -22, 132, 26, 6)
    fs(ctx, rgb('#B5212E'), INK, 4)
    for zx in range(-60, 61, 15):
        line(ctx, [(zx, -22), (zx + 7, -12)], INK, 2)
    ellipse(ctx, -4, 85, 40, 22)
    fs(ctx, rgb('#FFD166'), INK, 3)
    ctx.move_to(30, 85)
    ctx.line_to(52, 68)
    ctx.line_to(52, 102)
    ctx.close_path()
    fs(ctx, rgb('#FFD166'), INK, 3)
    ellipse(ctx, -24, 80, 4, 4)
    fill(ctx, INK)
    set_font(ctx, 30)
    draw_lines(ctx, ['YUM'], 0, 150, 30, WHITE)
    ctx.restore()


def bowl(ctx, x, y, full=0.0, kibble_n=0):
    if full > 0:
        for i in range(int(14 * full)):
            kx = x - 70 + (i * 37) % 140
            ky = y - 62 - (i % 3) * 10 - full * 8
            ellipse(ctx, kx, ky, 12, 9)
            fs(ctx, rgb('#A0612F'), INK, 2)
    ctx.move_to(x - 105, y - 62)
    ctx.line_to(x + 105, y - 62)
    ctx.line_to(x + 80, y)
    ctx.line_to(x - 80, y)
    ctx.close_path()
    fs(ctx, rgb('#FF8FAB'), INK, 5)
    ellipse(ctx, x, y - 62, 105, 14)
    fs(ctx, rgb('#FFC2D1'), INK, 4)
    set_font(ctx, 26)
    set_font(ctx, 30)
    draw_lines(ctx, ['KEEF'], x, y - 30, 30, WHITE)


def cat_bed(ctx, x, y):
    ellipse(ctx, x, y - 30, 210, 60)
    fs(ctx, rgb('#B983FF'), INK, 5)
    ellipse(ctx, x, y - 48, 160, 34)
    fs(ctx, rgb('#D7B9FF'), INK, 4)


def yarn(ctx, x, y, rot):
    ellipse(ctx, x, y, 48, 48)
    fs(ctx, rgb('#FF6B9A'), INK, 5)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    for k in (-24, 0, 24):
        ctx.move_to(-40, k)
        ctx.curve_to(-10, k - 22, 10, k + 22, 40, k)
    ctx.set_source_rgb(*rgb('#C9406E'))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()


def exclaim(ctx, x, y, t, t0):
    if t < t0:
        return
    p = seg(t, t0, t0 + 0.18)
    floaty_text(ctx, '!', x, y - 30 * eob(p), 140 * lerp(0.4, 1, eob(p)), min(1, p * 3), 0.1, RED)


def speed_lines(ctx, x, y, direction, s=1.0, alpha=1.0):
    for i, (dy, ln) in enumerate(((-150, 170), (-100, 240), (-50, 200), (0, 150))):
        x0 = x - direction * (150 + (i % 2) * 40) * s
        line(ctx, [(x0, y + dy * s), (x0 - direction * ln * s, y + dy * s)], INK, 6, 0.6 * alpha)


def dust(ctx, x, y, age):
    if age < 0 or age > 1.3:
        return
    a = 1 - age / 1.3
    for i, (dx, dy, r) in enumerate(((0, 0, 60), (-70, 10, 45), (60, 15, 50), (-20, -50, 40), (30, -40, 38))):
        rr = r * (0.6 + age * 0.8)
        ellipse(ctx, x + dx * (1 + age), y + dy - age * 40, rr, rr)
        fs(ctx, rgb('#E8E2D6'), rgb('#9C9284'), 4, a)
    if age < 0.7:
        floaty_text(ctx, 'ZOOM!', x + 10, y - 150 - age * 40, 70, 1 - age / 0.7, -0.15, YELLOW)


def cat_run(ctx, x, y, s, facing, t, look=(1, 0)):
    cat_walk(ctx, x, y, s, facing, t * 34, eyes='wide', look=look, tail=t * 10, mouth=0.25)
    speed_lines(ctx, x, y - 110 * s, facing, s)


def cardboard_box(ctx, x, y, s, legs_phase=None, eyes='sleep', look=(0, 0), t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    bob = 0
    if legs_phase is not None:
        bob = abs(math.sin(legs_phase)) * 10
        for i, lx in enumerate((-110, -60, 60, 110)):
            a = math.sin(legs_phase + (i % 2) * PI) * 0.6
            fx, fy = lx + math.sin(a) * 70, -70 + math.cos(a) * 70
            thick(ctx, [(lx, -60 - bob), (fx, fy)], 22, CAT)
            ellipse(ctx, fx + 5, fy - 4, 16, 10)
            fs(ctx, CAT, INK, 4)
        thick(ctx, [(-150, -150 - bob), (-200, -170), (-215, -240), (-180, -270)], 20, CAT, curve=True)
    by = -60 - bob
    # back flaps
    for sx in (-1, 1):
        ctx.move_to(sx * 150, by - 190)
        ctx.line_to(sx * 200, by - 250)
        ctx.line_to(sx * 70, by - 250)
        ctx.line_to(sx * 20, by - 190)
        ctx.close_path()
        fs(ctx, rgb('#C8955E'), INK, 5)
    # cat head peeking out
    ctx.save()
    ctx.translate(0, by - 205)
    ctx.scale(0.85, 0.85)
    cat_head(ctx, eyes, look)
    ctx.restore()
    rrect(ctx, -150, by - 190, 300, 190 + (60 if legs_phase is None else 0), 6)
    fs(ctx, rgb('#D9A86C'), INK, 5)
    line(ctx, [(-60, by - 120), (60, by - 120)], rgb('#A87A45'), 5)
    set_font(ctx, 28)
    draw_lines(ctx, ['FRAGILE'], 0, by - 80, 28, rgb('#A87A45'))
    if legs_phase is None:
        for sx in (-1, 1):
            ellipse(ctx, sx * 45, by - 192, 26, 14)
            fs(ctx, CAT, INK, 4)
    ctx.restore()


# ---------------------------------------------------------------- scenes
def scene_call(ctx, t):
    """0-5s: owner calls his name. Total ignore."""
    bg_living(ctx, t)
    cat_bed(ctx, 760, 1560)
    calls = [(0.5, 1.7), (1.9, 3.0), (3.1, 4.6)]
    loud = 3.1 <= t < 4.6
    hd = dict(eyes='open', mouth='big' if any(a <= t < b for a, b in calls) else 'flat',
              look=(1, 0.4), brow=1 if loud else 0)
    owner_stand(ctx, 280, 1545, 'down', head=hd)
    eyes = 'one' if 2.4 <= t < 2.9 else 'sleep'
    cat_curled(ctx, 760, 1505, 0.9, facing=-1, eyes=eyes, breath=t * 3, look=(-1, -0.3))
    zzz(ctx, t, 820, 1340)
    bub(ctx, t, 0.5, 1.7, 330, 640, 'Keef!', (300, 780))
    bub(ctx, t, 1.9, 3.0, 330, 640, 'Keef? Come here!', (300, 780))
    bub(ctx, t, 3.1, 4.6, 330, 620, 'KEEF!!!', (300, 780), size=64)
    bub(ctx, t, 3.4, 5.0, 760, 1120, 'Who is Keef?', (760, 1380), thought=True, size=44)


def scene_bag(ctx, t):
    """5-9.5s: owner shakes the food bag."""
    bg_living(ctx, t)
    cat_bed(ctx, 760, 1560)
    shaking = 0.4 <= t < 1.6
    sh = math.sin(t * 38) * 0.35 if shaking else 0
    if t < 2.0:
        hd = dict(eyes='closed', mouth='smile')
    elif t < 3.0:
        hd = dict(eyes='wide', mouth='o', look=(1, 0))
    else:
        hd = dict(eyes='flat', mouth='flat', look=(-1, 0))
    blown = 2.0 <= t < 2.6
    ox = 280 + (math.sin(t * 60) * 4 if blown else 0)
    owner_stand(ctx, ox, 1545, 'hold', head=hd)
    hx, hy = ox + 60 + sh * 30, 1095
    food_bag(ctx, hx, hy, sh, 0.9)
    ellipse(ctx, hx, hy, 25, 25)
    fs(ctx, SKIN, INK, 5)
    if shaking:
        for i, (dx, dy) in enumerate(((-150, -60), (150, -20))):
            floaty_text(ctx, 'shake', 300 + dx, 980 + dy + math.sin(t * 30 + i) * 6, 46,
                        1.0, 0.2 * (1 if i else -1))
    if t < 1.85:
        eyes = 'sleep' if t < 1.2 else 'wide'
        cat_curled(ctx, 760, 1505, 0.9, facing=-1, eyes=eyes, breath=t * 3, look=(-1, 0))
        exclaim(ctx, 680, 1300, t, 1.25)
    elif t < 2.25:
        p = ease(seg(t, 1.85, 2.25))
        cat_run(ctx, lerp(760, -250, p), 1560, 0.9, -1, t, look=(-1, 0))
    dust(ctx, 760, 1480, t - 1.9)
    bub(ctx, t, 3.0, 4.5, 330, 640, '...I have been calling you for 20 minutes.', (300, 780), size=44, maxw=600)


def scene_sleep(ctx, t):
    """9.5-13.5s: deep sleep -> can opens -> launch."""
    bg_bedroom(ctx, t)
    bed_back(ctx)
    blanket(ctx)
    if t < 1.7:
        eyes = 'sleep' if t < 1.3 else 'wide'
        # belly-up sleep: curled cat, legs relaxed
        cat_curled(ctx, 560, 1185, 0.95, facing=1, eyes=eyes, breath=t * 2.4)
        if t < 1.3:
            zzz(ctx, t, 470, 1060)
        exclaim(ctx, 470, 980, t, 1.3)
    elif t < 2.1:
        p = ease(seg(t, 1.7, 2.1))
        y = 1185 + 330 * p - math.sin(p * PI) * 120
        cat_run(ctx, lerp(560, 1350, p), y, 0.9, 1, t)
    # Zs left behind drop to the floor
    if t >= 1.7:
        for i in range(3):
            p = clamp((t - 1.7 - i * 0.06) / 0.5)
            floaty_text(ctx, 'Z', 470 + i * 50, lerp(1000 - i * 50, 1430, p * p), 46, 1 - seg(t, 3.2, 3.6), 1.4 * p, rgb('#A0C4FF'))
    dust(ctx, 600, 1160, t - 1.75)
    floaty_text(ctx, '*can opens*', 860, 860 + math.sin(t * 20) * 3, 46, seg(t, 0.9, 1.1) * (1 - seg(t, 2.6, 2.8)), -0.1, YELLOW)
    floaty_text(ctx, 'pssshht', 860, 940, 40, seg(t, 1.0, 1.15) * (1 - seg(t, 2.6, 2.8)), -0.1)


def scene_play(ctx, t):
    """13.5-17.5s: mid-play with a yarn ball."""
    bg_living(ctx, t)
    yx = 520 + math.sin(t * 3) * 30 if t < 1.6 else 520 + (t - 1.6) * 260
    yarn(ctx, yx, 1495, t * (3 if t < 1.6 else 8))
    line(ctx, [(yx - 40, 1520), (yx - 200, 1540), (yx - 330, 1535)], rgb('#FF6B9A'), 4)
    if t < 1.5:
        paw = 0.5 + 0.5 * math.sin(t * 9) if t < 1.1 else 0
        eyes = 'open' if t < 1.1 else 'wide'
        cat_sit(ctx, 720, 1545, 0.95, facing=-1, eyes=eyes, look=(-1, 0.6) if t < 1.1 else (1, 0),
                paw=paw, tail=t * 5)
        exclaim(ctx, 720, 1220, t, 1.12)
    elif t < 1.9:
        p = ease(seg(t, 1.5, 1.9))
        cat_run(ctx, lerp(720, 1350, p), 1545, 0.95, 1, t)
    dust(ctx, 720, 1460, t - 1.55)
    floaty_text(ctx, '*crinkle crinkle*', 540, 900, 50, seg(t, 0.8, 1.0) * (1 - seg(t, 2.5, 2.7)), -0.06, YELLOW)


def scene_box(ctx, t):
    """17.5-21.5s: in a box, very busy. The box leaves too."""
    bg_living(ctx, t)
    if t < 1.6:
        eyes = 'half' if t < 1.2 else 'wide'
        cardboard_box(ctx, 600, 1560, 1.0, None, eyes=eyes, look=(0, 0))
        exclaim(ctx, 600, 1180, t, 1.22)
    else:
        p = ease(seg(t, 1.6, 2.3))
        cardboard_box(ctx, lerp(600, 1400, p), 1560, 1.0, t * 30, eyes='wide', look=(1, 0))
        speed_lines(ctx, lerp(600, 1400, p) - 60, 1440, 1)
    dust(ctx, 600, 1480, t - 1.65)
    floaty_text(ctx, '*bowl clinks*', 540, 900, 50, seg(t, 0.9, 1.1) * (1 - seg(t, 2.6, 2.8)), 0.06, YELLOW)


def scene_bowl(ctx, t):
    """21.5-27s: meanwhile at the food bowl."""
    bg_kitchen(ctx, t)
    pour = 0.3 <= t < 1.4
    if t < 1.5:
        hd = dict(eyes='open', mouth='smile', look=(1, 1))
    elif t < 2.2:
        hd = dict(eyes='wide', mouth='o', look=(1, 0.5))
    else:
        hd = dict(eyes='flat', mouth='flat', look=(1, 0.6), brow=1)
    pour_t = ease(seg(t, 0.2, 0.5)) * (1 - ease(seg(t, 1.4, 1.7)))
    OX = 360
    owner_stand(ctx, OX, 1545, 'hold', 'pour', pour_t, head=hd)
    hx, hy = OX + lerp(60, 160, pour_t), 1545 - lerp(450, 430, pour_t)
    food_bag(ctx, hx, hy, 2.4 * pour_t, 0.85)
    ellipse(ctx, hx, hy, 25, 25)
    fs(ctx, SKIN, INK, 5)
    bowl_x = 560
    if pour:
        for i in range(8):
            k = ((t * 3) + i / 8) % 1
            ellipse(ctx, bowl_x - 20 + math.sin(i * 3) * 14, lerp(hy + 30, 1470, k), 11, 8)
            fs(ctx, rgb('#A0612F'), INK, 2)
    full = seg(t, 0.4, 1.4)
    eating = t >= 1.95
    bowl_front = lambda: bowl(ctx, bowl_x, 1580, full * (1 - 0.5 * seg(t, 2.0, 5.0)))
    # cat skids in from the left
    if 1.2 <= t < 1.95:
        p = ease(seg(t, 1.2, 1.7))
        cx = lerp(1400, 660, p)
        if t < 1.7:
            cat_run(ctx, cx, 1540, 0.95, -1, t, look=(-1, 0))
        else:
            sq = math.exp(-(t - 1.7) * 8) * 0.8
            cat_sit(ctx, 640, 1540, 0.95, facing=-1, eyes='wide', look=(-1, 1), squash=sq, tail=t * 4)
        if t >= 1.6:
            dust(ctx, 760, 1480, t - 1.6)
    elif eating:
        bobh = abs(math.sin(t * 10)) * 0.12
        cat_sit(ctx, 640, 1540, 0.95, facing=-1, eyes='closed', look=(-1, 1),
                mouth=0.4 + 0.4 * math.sin(t * 20), tail=t * 4, tilt=-0.25 - bobh, blush=0.8)
        for i in range(3):
            k = ((t - 1.95) * 1.3 + i / 3) % 1
            floaty_text(ctx, 'nom', 820 + i * 40, 1180 - k * 160, 40, math.sin(k * PI), 0.15)
        for i in range(4):
            heart(ctx, 660 + math.sin(t * 2 + i * 2) * 120, 1150 - ((t * 0.5 + i / 4) % 1) * 260, 14,
                  alpha=0.8 * math.sin(((t * 0.5 + i / 4) % 1) * PI))
    bowl_front()
    bub(ctx, t, 2.4, 4.0, 400, 650, 'Oh, NOW you can hear me?', (360, 790))
    bub(ctx, t, 4.1, 5.5, 720, 960, 'I only speak Food.', (650, 1230), size=48)


CAPTIONS2 = [
    (0.15, 5.0, 'My cat when I\ncall his name:'),
    (5.05, 7.4, 'Now watch this:'),
    (7.4, 9.5, '0 to 100 in 0.2 seconds'),
    (9.55, 13.5, 'Deep sleep? Doesn\'t matter.'),
    (13.55, 17.5, 'Busy playing?\nDoesn\'t matter.'),
    (17.55, 21.5, 'In a box?\nDoesn\'t matter.'),
    (21.55, 27.0, 'Meanwhile at the bowl:'),
]
SCENES2 = [0.0, 5.0, 9.5, 13.5, 17.5, 21.5, 30.0]
PUNCH2 = [6.2, 10.8, 15.0, 19.1, 22.7]


def render(ctx, t):
    ctx.save()
    z = 1.0
    for p in PUNCH2:
        if t >= p:
            z += 0.06 * math.exp(-(t - p) * 7)
    ctx.translate(540, 1150)
    ctx.scale(z * 1.1, z * 1.1)
    ctx.translate(-540, -1150)
    if t < 5.0:
        scene_call(ctx, t)
    elif t < 9.5:
        scene_bag(ctx, t - 5.0)
    elif t < 13.5:
        scene_sleep(ctx, t - 9.5)
    elif t < 17.5:
        scene_play(ctx, t - 13.5)
    elif t < 21.5:
        scene_box(ctx, t - 17.5)
    else:
        scene_bowl(ctx, t - 21.5)
    ctx.restore()
    caption(ctx, t, CAPTIONS2)
    if t >= 27.0:
        end_card(ctx, t - 27.0, ('Tag a cat who only', 'listens to food'), 'Follow for more cat chaos')
    for s in SCENES2[1:-1]:
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
    n = int(DUR * FPS)
    proc = subprocess.Popen([
        'ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out
    ], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(bytes(frame_surface(i / FPS).get_data()))
    proc.stdin.close()
    proc.wait()


if __name__ == '__main__':
    main()
