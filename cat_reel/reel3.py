"""'Keef: A British Shorthair' - reel #3.

A mock nature-documentary on British Shorthair personality traits, starring Keef:
a dignified gentleman, hates being picked up, follows you everywhere (but is NOT a
lap cat), utterly unbothered by chaos, rarely meows, and considers blinking cardio.

Usage:
  python3 reel3.py video out_silent.mp4
  python3 reel3.py still out.png 12.3
"""
import math
import subprocess
import sys

import cairo

import reel
from reel import (W, H, FPS, PI, INK, WHITE, CAT, CREAM, PINK, RED, YELLOW, SKIN,
                  clamp, seg, ease, eob, lerp, rgb, ellipse, rrect, fs, fill, line,
                  set_font, draw_lines, floaty_text, heart, bub, burst, thick,
                  cat_head, cat_sit, cat_walk, cat_curled, owner_stand, owner_sit,
                  arm, wall_floor, window, frame_pic, plant, bg_living, bg_night,
                  couch_back, caption, end_card, FLOOR_Y, WOOD, WOOD_DK)

DUR = 39.0
GOLD = rgb('#E8B931')


# ---------------------------------------------------------------- accessories
def bowler_hat(ctx):
    ctx.save()
    ctx.rotate(-0.12)
    ctx.translate(6, -52)
    ctx.move_to(-56, -8)
    ctx.curve_to(-56, -80, 56, -80, 56, -8)
    ctx.close_path()
    fs(ctx, rgb('#26262E'), INK, 5)
    rrect(ctx, -56, -26, 112, 18, 4)
    fill(ctx, rgb('#7A2E3A'))
    ellipse(ctx, 0, -6, 86, 15)
    fs(ctx, rgb('#26262E'), INK, 5)
    ctx.restore()


def monocle(ctx):
    ellipse(ctx, 35, -6, 31, 31)
    ctx.set_source_rgba(1, 1, 1, 0.18)
    ctx.fill_preserve()
    ctx.set_source_rgb(*GOLD)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.move_to(62, 8)
    ctx.curve_to(80, 40, 70, 70, 88, 92)
    ctx.set_source_rgb(*GOLD)
    ctx.set_line_width(3)
    ctx.stroke()


def gentleman(hat=True, mono=True):
    def extras(ctx):
        if mono:
            monocle(ctx)
        if hat:
            bowler_hat(ctx)
    return extras


def with_extras(fn, extras, *a, **kw):
    reel.HEAD_EXTRAS = extras
    try:
        fn(*a, **kw)
    finally:
        reel.HEAD_EXTRAS = None


def paw_pos(x, y, s, facing, paw):
    px, py = lerp(34, 130, paw), lerp(-12, -100, paw)
    return x + facing * s * px, y + s * py


def teacup(ctx, x, y, s=1.0, t=0.0, steam=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ellipse(ctx, 0, 18, 52, 11)
    fs(ctx, WHITE, INK, 4)
    ctx.move_to(-38, -30)
    ctx.line_to(38, -30)
    ctx.curve_to(36, 10, 20, 16, 0, 16)
    ctx.curve_to(-20, 16, -36, 10, -38, -30)
    ctx.close_path()
    fs(ctx, WHITE, INK, 4)
    line(ctx, [(-34, -14), (34, -14)], rgb('#7FA7D9'), 6)
    ctx.new_sub_path()
    ctx.arc(42, -12, 13, -PI / 2, PI / 2)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    ellipse(ctx, 0, -30, 38, 8)
    fs(ctx, rgb('#B07A4A'), INK, 3)
    if steam:
        for i in (-14, 10):
            ph = t * 3 + i
            ctx.move_to(i, -44)
            ctx.curve_to(i + 12 * math.sin(ph), -64, i - 12 * math.sin(ph), -84, i + 4, -104)
            ctx.set_source_rgba(1, 1, 1, 0.85)
            ctx.set_line_width(5)
            ctx.stroke()
    ctx.restore()


def gent_cat(ctx, x, y, s, facing=-1, eyes='half', look=(0, 0), t=0.0, sip=0.0, tail=0.0, hat=True, mono=True):
    """Keef sitting with bowler hat + monocle holding a cup of tea (sip 0..1 lifts it)."""
    paw = lerp(0.42, 0.62, sip)
    with_extras(cat_sit, gentleman(hat, mono), ctx, x, y, s, facing=facing, eyes=eyes,
                look=look, paw=paw, tail=tail)
    px, py = paw_pos(x, y, s, facing, paw)
    teacup(ctx, px - facing * 4 * s, py - 30 * s, 0.75 * s, t)
    ellipse(ctx, px, py, 26 * s, 18 * s)
    fs(ctx, CAT, INK, 5 * s)


def cat_dangle(ctx, x, y, s, t, eyes='half', look=(0, 0)):
    """Keef held up under the armpits: rigid as a plank. (x, y) = hand height."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.sin(t * 7) * 0.035)
    ctx.scale(s, s)
    for sx in (-1, 1):
        thick(ctx, [(sx * 34, 230), (sx * 36, 330)], 30, CAT)
        ellipse(ctx, sx * 38, 336, 24, 14)
        fs(ctx, CAT, INK, 5)
    thick(ctx, [(10, 250), (14, 330), (16, 400), (18, 450)], 24, CAT)
    ellipse(ctx, 0, 125, 82, 135)
    fs(ctx, CAT, INK, 5)
    ellipse(ctx, 0, 140, 46, 100)
    fill(ctx, CREAM)
    for sx in (-1, 1):
        thick(ctx, [(sx * 55, 40), (sx * 112, 0)], 30, CAT)
    ctx.save()
    ctx.translate(0, -60)
    cat_head(ctx, eyes, look)
    ctx.restore()
    ctx.restore()


def owner_hands(ctx, pts):
    for (hx, hy) in pts:
        ellipse(ctx, hx, hy, 25, 25)
        fs(ctx, SKIN, INK, 5)


def door(ctx, x, y, w, h, open_amt=0.0):
    rrect(ctx, x - 12, y - 12, w + 24, h + 12, 6)
    fs(ctx, WHITE, INK, 5)
    ctx.rectangle(x, y, w, h)
    fill(ctx, rgb('#3A3346'))
    dw = w * (1 - open_amt * 0.85)
    ctx.rectangle(x, y, dw, h - 8)
    fs(ctx, rgb('#C68B59'), INK, 5)
    if open_amt < 0.5:
        for (py, ph) in ((y + 40, h * 0.38), (y + 70 + h * 0.4, h * 0.38)):
            rrect(ctx, x + 26, py, dw - 52, ph, 8)
            ctx.set_source_rgb(*WOOD_DK)
            ctx.set_line_width(4)
            ctx.stroke()
        ellipse(ctx, x + dw - 28, y + h * 0.52, 12, 12)
        fs(ctx, GOLD, INK, 4)
        rrect(ctx, x + w / 2 - 60, y + 60, 120, 44, 10)
        fs(ctx, WHITE, INK, 3)
        set_font(ctx, 26)
        draw_lines(ctx, ['WC'], x + w / 2, y + 82, 26, INK)


def feather_toy(ctx, hand, tip, fx, fy, t):
    line(ctx, [hand, tip], rgb('#8E5A31'), 9)
    ctx.move_to(*tip)
    ctx.curve_to(tip[0], tip[1] + 80, fx, fy - 80, fx, fy)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(2.5)
    ctx.stroke()
    for i, (c, a) in enumerate(((rgb('#FF6B9A'), -0.5), (rgb('#4CC9F0'), 0.0), (rgb('#FFD166'), 0.5))):
        ctx.save()
        ctx.translate(fx, fy)
        ctx.rotate(a + math.sin(t * 9 + i) * 0.15)
        ellipse(ctx, 0, 38, 13, 42)
        fs(ctx, c, INK, 3)
        ctx.restore()


# ---------------------------------------------------------------- scenes
def scene_intro(ctx, t):
    """0-4s: meet Keef, a gentleman."""
    bg_living(ctx, t)
    sip = ease(seg(t, 2.6, 3.1)) * (1 - ease(seg(t, 3.5, 3.9)))
    gent_cat(ctx, 560, 1560, 1.15, facing=-1, eyes='half', t=t, sip=sip, tail=t * 1.2)
    bub(ctx, t, 0.7, 2.5, 560, 760, 'Ah. You\'re awake.', (560, 1040))
    bub(ctx, t, 2.5, 4.0, 560, 760, 'Tea?', (560, 1040), size=60)


def scene_pickup(ctx, t):
    """4-10.5s: Trait #1 - hates being picked up."""
    bg_living(ctx, t)
    if t < 1.2:
        owner_stand(ctx, 300, 1545, 'down', 'open', ease(seg(t, 0.2, 0.6)),
                    head=dict(eyes='closed', mouth='big', blush=1.0))
        cat_sit(ctx, 760, 1545, 1.0, facing=-1, eyes='wide' if t > 0.7 else 'open', look=(-1, 0), tail=t * 2)
        bub(ctx, t, 0.15, 1.2, 330, 640, 'Who wants cuddles?!', (300, 780))
    elif t < 4.8:
        hd = dict(eyes='closed', mouth='big', blush=1.0) if t < 3.0 else dict(eyes='open', mouth='flat', look=(0.4, 0.6))
        ox = 420
        owner_stand(ctx, ox, 1545, 'carry', head=hd)
        cat_dangle(ctx, ox, 1120, 0.8, t, eyes='half', look=(1, 0))
        owner_hands(ctx, [(ox - 100, 1120), (ox + 100, 1120)])
        floaty_text(ctx, '*becomes a plank*', 760, 1300 + math.sin(t * 3) * 6, 44, seg(t, 1.4, 1.7) * (1 - seg(t, 4.5, 4.8)), -0.08, YELLOW)
        bub(ctx, t, 1.6, 3.2, 700, 820, 'This is most undignified.', (500, 1000), size=46, maxw=520)
        bub(ctx, t, 3.3, 4.8, 700, 820, 'Unhand me, human.', (500, 1000), size=48)
    else:
        owner_stand(ctx, 300, 1545, 'down', head=dict(eyes='open', mouth='sad', brow=-1, look=(1, 0.3)))
        with_extras(cat_sit, None, ctx, 700, 1545, 1.0, facing=1, eyes='closed', look=(1, 0), tail=t * 2)
        bub(ctx, t, 4.9, 6.5, 720, 1060, 'We shall never speak of this.', (720, 1250), size=46, maxw=560)


def scene_follow(ctx, t):
    """10.5-17s: Trait #2 - not a lap cat, but must supervise."""
    bg_living(ctx, t)
    door_open = 1.0 if t < 4.3 else 0.0
    door(ctx, 800, 900, 210, 520, door_open)
    # owner
    if t < 2.0:
        p = seg(t, 0.1, 2.0)
        owner_stand(ctx, lerp(200, 520, p), 1545, 'down', walk=t * 9, head=dict(eyes='open', mouth='smile', look=(1, 0)))
    elif t < 3.6:
        hd = dict(eyes='open', mouth='flat', look=(-1, 0.4), brow=0.6)
        owner_stand(ctx, 520, 1545, 'down', head=hd)
    elif t < 4.3:
        p = seg(t, 3.6, 4.3)
        ctx.push_group()
        owner_stand(ctx, lerp(520, 905, p), 1545, 'down', walk=t * 9, head=dict(eyes='open', mouth='smile', look=(1, 0)))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - seg(t, 4.0, 4.3))
    # Keef
    if t < 2.15:
        p = seg(t, 0.4, 2.15)
        cat_walk(ctx, lerp(-150, 250, p), 1560, 0.8, 1, t * 10, eyes='open', look=(1, 0), tail=t * 3)
    elif t < 4.4:
        with_extras(cat_sit, None, ctx, 250, 1560, 0.8, facing=1, eyes='half' if 2.3 < t < 3.7 else 'open',
                    look=(0.3, -1) if 2.3 < t < 3.7 else (1, 0), tail=t * 2)
    elif t < 5.2:
        p = seg(t, 4.4, 5.2)
        cat_walk(ctx, lerp(250, 640, p), 1560, 0.8, 1, t * 10, eyes='open', look=(1, 0), tail=t * 3)
    else:
        cat_sit(ctx, 640, 1560, 0.8, facing=1, eyes='open', look=(1, -0.3), tail=t * 2)
    if 4.3 <= t < 4.9:
        floaty_text(ctx, '*click*', 905, 870, 40, 1 - seg(t, 4.6, 4.9), 0.1)
    bub(ctx, t, 2.1, 3.3, 520, 650, 'Are you following me?', (520, 790))
    bub(ctx, t, 2.6, 3.7, 300, 1020, 'No.', (260, 1330), size=56)
    bub(ctx, t, 5.0, 6.5, 640, 760, 'Keef, I\'m in the BATHROOM.', (880, 1000), size=44, maxw=600)
    floaty_text(ctx, '*supervising*', 620, 1200 + math.sin(t * 3) * 5, 44, seg(t, 5.3, 5.6), -0.06, YELLOW)


def scene_storm(ctx, t):
    """17-23.5s: Trait #3 - completely unbothered."""
    strikes = [0.7, 2.5, 4.3]
    flash = sum(math.exp(-(t - s) * 9) for s in strikes if t >= s)
    bg_night(ctx, t)
    # lightning bolt in the window
    for s in strikes:
        if s <= t < s + 0.25:
            ctx.move_to(250, 480)
            for (bx, by) in ((215, 560), (255, 580), (205, 680), (245, 690), (200, 760)):
                ctx.line_to(bx, by)
            ctx.set_source_rgb(*YELLOW)
            ctx.set_line_width(10)
            ctx.stroke()
    couch_back(ctx)
    jit = math.sin(t * 50) * 5
    hd = dict(eyes='wide', mouth='grit', brow=-1, sweat=1.0, look=(0.5, -0.5))
    owner_sit(ctx, 520 + jit, 1330, head=hd)
    # blanket pulled up to the chin
    ctx.move_to(370 + jit, 1010)
    ctx.curve_to(450 + jit, 975, 590 + jit, 975, 670 + jit, 1010)
    ctx.line_to(700 + jit, 1360)
    ctx.line_to(340 + jit, 1360)
    ctx.close_path()
    fs(ctx, rgb('#B9A3E3'), INK, 5)
    for (dx, dy) in ((430, 1100), (560, 1150), (480, 1260), (620, 1270)):
        heart(ctx, dx + jit, dy, 12, rgb('#E4D7FF'))
    owner_hands(ctx, [(450 + jit, 1010), (590 + jit, 1010)])
    sip = ease(seg(t, 5.0, 5.4)) * (1 - ease(seg(t, 6.0, 6.3)))
    gent_cat(ctx, 840, 1610, 1.0, facing=-1, eyes='half', t=t, sip=sip, tail=t)
    for s in strikes:
        burst(ctx, 330, 860, 'BOOM!', t, s, s + 0.7, size=96, rot=-0.15, fillc=rgb('#9EC5FF'), textc=rgb('#1D2B53'))
    if flash > 0.01:
        ctx.rectangle(-200, -200, W + 400, H + 400)
        ctx.set_source_rgba(1, 1, 1, min(0.75, flash * 0.75))
        ctx.fill()
    bub(ctx, t, 1.2, 2.5, 470, 700, 'WE\'RE ALL GONNA DIE!!', (500, 860), size=50)
    bub(ctx, t, 3.0, 4.6, 760, 1060, 'Bit of weather.', (830, 1330), size=50)
    floaty_text(ctx, '*sips tea*', 700, 1240, 44, seg(t, 5.0, 5.2) * (1 - seg(t, 6.2, 6.5)), -0.08, YELLOW)


def scene_meow(ctx, t):
    """23.5-30s: Trait #4 - rarely meows."""
    bg_living(ctx, t)
    if t < 4.6:
        hd = dict(eyes='open', mouth='big' if t < 1.6 or 3.4 <= t < 4.4 else 'smile', look=(1, 0.4))
        if 3.4 <= t:
            hd = dict(eyes='open', mouth='sad', brow=-1, look=(1, 0.4))
        owner_stand(ctx, 300, 1545, 'phone', head=hd)
    elif t < 5.2:
        owner_stand(ctx, 300, 1545, 'down', head=dict(eyes='open', mouth='sad', brow=-1, look=(-1, 0.5)))
    else:
        owner_stand(ctx, 300, 1545, 'down', head=dict(eyes='wide', mouth='o', look=(1, 0.3)))
    cat_sit(ctx, 760, 1545, 1.0, facing=-1, eyes='open', look=(-1, 0) if t < 5.2 else (0, 0), tail=t * 1.5)
    if 4.6 <= t:
        p = seg(t, 4.75, 5.4)
        floaty_text(ctx, 'mip.', 760, 1270 - p * 50, 34, (1 - seg(t, 5.8, 6.2)) * clamp(p * 6), 0.1)
    bub(ctx, t, 0.3, 1.9, 360, 640, 'Keef! Say meow for the video!', (300, 790), size=46, maxw=560)
    bub(ctx, t, 2.0, 3.2, 760, 1060, '...', (760, 1240), size=60)
    bub(ctx, t, 3.3, 4.4, 330, 640, 'Pleeeease?', (300, 790))
    bub(ctx, t, 3.7, 4.5, 760, 1060, '...', (760, 1240), size=60)
    if t >= 5.2:
        floaty_text(ctx, '!!', 300, 760, 80, 1 - seg(t, 6.2, 6.5), 0.1, RED)


def scene_cardio(ctx, t):
    """30-36s: Trait #5 - cardio? No thanks."""
    bg_living(ctx, t)
    owner_stand(ctx, 220, 1545, 'hold', head=dict(eyes='closed' if t < 3.2 else 'flat', mouth='big' if t < 3.2 else 'flat', look=(1, 0.5)))
    hand = (280, 1095)
    sw = math.sin(t * 4.2)
    fx = 640 + sw * 190 if t < 2.6 else 600
    fy = 1250 + math.cos(t * 8.4) * 30 if t < 2.6 else 1300
    tip = (lerp(520, 600, (sw + 1) / 2) if t < 2.6 else 560, 980)
    cx, cy, cs = 640, 1580, 1.05
    head_x = cx + 100 * cs * 0.82 + 20
    if t < 3.0:
        look = (clamp((fx - head_x) / 140, -1, 1), -0.8)
        cat_curled(ctx, cx, cy, cs, facing=-1, eyes='open', look=look, breath=t * 2)
    else:
        cat_curled(ctx, cx, cy, cs, facing=-1, eyes='sleep', breath=t * 2)
    # one lazy swat
    if 2.6 <= t < 3.0:
        a = math.sin(seg(t, 2.6, 3.0) * PI)
        thick(ctx, [(head_x - 40, 1530), (lerp(head_x - 40, fx + 10, a), lerp(1530, fy + 40, a))], 26, CAT)
    feather_toy(ctx, hand, tip, fx, fy, t)
    ellipse(ctx, hand[0], hand[1], 25, 25)
    fs(ctx, SKIN, INK, 5)
    if t < 2.6:
        floaty_text(ctx, '*only eyes move*', 760, 1170, 42, seg(t, 0.5, 0.8), -0.06, YELLOW)
    floaty_text(ctx, 'swat.', fx + 90, fy - 30, 40, seg(t, 2.65, 2.75) * (1 - seg(t, 3.2, 3.4)), 0.1)
    bub(ctx, t, 3.3, 6.0, 640, 940, 'Right. That\'s my cardio for the month.', (740, 1420), size=44, maxw=560)


CAPTIONS3 = [
    (0.15, 4.0, 'Meet Keef. A British\nShorthair. A gentleman.'),
    (4.05, 10.5, 'Trait #1: Does NOT\nlike being picked up.'),
    (10.55, 17.0, 'Trait #2: Not a lap cat.\nBut MUST supervise.'),
    (17.05, 23.5, 'Trait #3: Completely\nunbothered.'),
    (23.55, 28.2, 'Trait #4: Rarely meows.'),
    (28.2, 30.0, '...only when you\nstop recording.'),
    (30.05, 36.0, 'Trait #5: Cardio?\nNo, thank you.'),
]
SCENES3 = [0.0, 4.0, 10.5, 17.0, 23.5, 30.0, 39.0]
PUNCH3 = [17.7, 19.5, 21.3, 28.7]


def render(ctx, t):
    ctx.save()
    z = 1.0
    for p in PUNCH3:
        if t >= p:
            z += 0.05 * math.exp(-(t - p) * 7)
    ctx.translate(540, 1150)
    ctx.scale(z * 1.1, z * 1.1)
    ctx.translate(-540, -1150)
    if t < 4.0:
        scene_intro(ctx, t)
    elif t < 10.5:
        scene_pickup(ctx, t - 4.0)
    elif t < 17.0:
        scene_follow(ctx, t - 10.5)
    elif t < 23.5:
        scene_storm(ctx, t - 17.0)
    elif t < 30.0:
        scene_meow(ctx, t - 23.5)
    else:
        scene_cardio(ctx, t - 30.0)
    ctx.restore()
    caption(ctx, t, CAPTIONS3)
    if t >= 36.0:
        end_card(ctx, t - 36.0, ('British Shorthair:', '10% cat,', '90% furniture'), 'Follow Keef for more')
    for s in SCENES3[1:-1]:
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
