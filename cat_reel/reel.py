"""'My Cat Loves Me (Allegedly)' - an animated funny cat reel for Instagram.

Renders 1080x1920 @30fps frames with pycairo and pipes them into ffmpeg.
Usage:
  python3 reel.py video out_silent.mp4      # render video
  python3 reel.py still  out.png  12.3      # render one frame at t=12.3s
"""
import math
import subprocess
import sys

import cairo

W, H, FPS, DUR = 1080, 1920, 30, 35.0
PI = math.pi


# ---------------------------------------------------------------- helpers
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def ease(x):
    return x * x * (3 - 2 * x)


def eob(x):  # ease-out-back
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, x):
    return a + (b - a) * x


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def window_on(t, a, b):
    return a <= t < b


INK = rgb('#2B1E1A')
WHITE = (1, 1, 1)
CAT = rgb('#FCFCFE')   # white British Shorthair coat
CAT_DK = rgb('#DCE2EC')  # soft grey shadow (far legs)
CREAM = rgb('#EEF1F7')   # muzzle/belly tint
PINK = rgb('#FF9DAA')
IRIS = rgb('#5FB8F0')    # blue eyes
STRIPES = False  # solid white coat, no tabby stripes
SKIN = rgb('#F6CBA8')
HAIR = rgb('#4A2E22')
SHIRT = rgb('#5B8DEF')
SHIRT_DK = rgb('#4373D0')
PANTS = rgb('#3A3F55')
SHOE = rgb('#F2F2F2')
WOOD = rgb('#B97A47')
WOOD_DK = rgb('#8E5A31')
YELLOW = rgb('#FFD93B')
RED = rgb('#FF4B3E')


def ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * PI)
    ctx.restore()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -PI / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI)
    ctx.arc(x + r, y + r, r, PI, 1.5 * PI)
    ctx.close_path()


def fs(ctx, fill, stroke=INK, lw=5, alpha=1.0):
    if alpha < 1:
        ctx.set_source_rgba(*fill, alpha)
    else:
        ctx.set_source_rgb(*fill)
    if stroke is None:
        ctx.fill()
        return
    ctx.fill_preserve()
    ctx.set_source_rgb(*stroke)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def fill(ctx, color, alpha=1.0):
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()


def line(ctx, pts, color=INK, lw=5, alpha=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgba(*color, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def set_font(ctx, size, bold=True):
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def tw(ctx, s):
    return ctx.text_extents(s).x_advance


def wrap(ctx, text, maxw):
    out = []
    for para in text.split('\n'):
        cur = ''
        for w in para.split(' '):
            test = (cur + ' ' + w).strip()
            if tw(ctx, test) <= maxw or not cur:
                cur = test
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def draw_lines(ctx, lines, cx, cy, size, color, outline=None, ow=0, lh=1.22):
    total = len(lines) * size * lh
    y0 = cy - total / 2 + size * lh / 2
    for i, ln in enumerate(lines):
        x = cx - tw(ctx, ln) / 2
        y = y0 + i * size * lh + size * 0.36
        ctx.move_to(x, y)
        ctx.text_path(ln)
        if outline:
            ctx.set_source_rgb(*outline)
            ctx.set_line_width(ow)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke_preserve()
        ctx.set_source_rgb(*color)
        ctx.fill()


def heart(ctx, x, y, s, color=rgb('#FF4D6D'), alpha=1.0, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(0, 1)
    ctx.curve_to(-1.5, 0, -1.05, -1.3, 0, -0.45)
    ctx.curve_to(1.05, -1.3, 1.5, 0, 0, 1)
    ctx.close_path()
    ctx.restore()
    ctx.set_source_rgba(*color, alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK, alpha)
    ctx.set_line_width(4)
    ctx.stroke()


def paw_print(ctx, x, y, s, color, alpha, rot=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ellipse(ctx, 0, 0.35, 0.55, 0.45)
    for (px, py) in ((-0.62, -0.35), (-0.22, -0.72), (0.22, -0.72), (0.62, -0.35)):
        ellipse(ctx, px, py, 0.2, 0.25)
    ctx.restore()
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()


# ---------------------------------------------------------------- bubbles
def bubble(ctx, cx, cy, text, tail_to, pop=1.0, size=50, maxw=700,
           thought=False, color=WHITE, alpha=1.0):
    if pop <= 0:
        return
    set_font(ctx, size)
    lines = wrap(ctx, text, maxw - 70)
    w = max(tw(ctx, l) for l in lines) + 80
    h = len(lines) * size * 1.22 + 52
    # keep bubble on screen
    cx = clamp(cx, 80 + w / 2, 1000 - w / 2)  # world-space safe zone (world is zoomed 1.1x)
    s = lerp(0.4, 1.0, eob(clamp(pop)))
    tx, ty = tail_to
    ctx.push_group()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.translate(-cx, -cy)
    if thought:
        # trail of small circles
        for i, r in enumerate((26, 17, 10)):
            f = (i + 1) / 4.0
            ellipse(ctx, lerp(cx, tx, f + 0.1), lerp(cy + h / 2, ty, f + 0.1), r, r)
            fs(ctx, color, INK, 5)
        rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
        fs(ctx, color, INK, 6)
    else:
        below = ty > cy
        by = cy + (h / 2 - 4 if below else -h / 2 + 4)
        bx = clamp(tx, cx - w / 2 + 60, cx + w / 2 - 60)
        dx, dy = tx - bx, ty - by
        d = math.hypot(dx, dy) or 1
        L = min(95, d * 0.8)
        tipx, tipy = bx + dx / d * L, by + dy / d * L
        tail = lambda: (ctx.move_to(bx - 26, by), ctx.line_to(tipx, tipy),
                        ctx.line_to(bx + 26, by), ctx.close_path())
        rrect(ctx, cx - w / 2, cy - h / 2, w, h, 40)
        tail()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(12)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
        rrect(ctx, cx - w / 2, cy - h / 2, w, h, 40)
        fill(ctx, color)
        tail()
        fill(ctx, color)
    draw_lines(ctx, lines, cx, cy, size, INK)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)


def bub(ctx, t, a, b, *args, **kw):
    """Bubble visible on [a,b) with pop-in and quick fade-out."""
    if not (a <= t < b):
        return
    pop = seg(t, a, a + 0.28)
    alpha = 1 - seg(t, b - 0.15, b)
    bubble(ctx, *args, pop=pop, alpha=alpha, **kw)


def burst(ctx, x, y, text, t, a, b, size=110, rot=-0.12, fillc=YELLOW, textc=RED):
    if not (a <= t < b):
        return
    p = seg(t, a, a + 0.2)
    s = lerp(0.3, 1.0, eob(p)) * (1 + 0.04 * math.sin(t * 40))
    alpha = 1 - seg(t, b - 0.15, b)
    ctx.push_group()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    set_font(ctx, size)
    w = tw(ctx, text)
    n = 16
    R1, R2 = w / 2 + 90, w / 2 + 30
    for i in range(2 * n):
        r = R1 if i % 2 == 0 else R2
        a_ = i * PI / n
        px, py = math.cos(a_) * r, math.sin(a_) * r * 0.55
        (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    ctx.close_path()
    fs(ctx, fillc, INK, 7)
    draw_lines(ctx, [text], 0, 0, size, textc, outline=WHITE, ow=12)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)


def floaty_text(ctx, text, x, y, size, alpha, rot=0, color=WHITE):
    if alpha <= 0:
        return
    ctx.push_group()
    ctx.translate(x, y)
    ctx.rotate(rot)
    set_font(ctx, size)
    draw_lines(ctx, [text], 0, 0, size, color, outline=INK, ow=8)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)


# ---------------------------------------------------------------- the cat
def cat_head(ctx, eyes='open', look=(0, 0), mouth=0.0, blush=0.0):
    lx, ly = look
    # small, rounded, wide-set ears (British Shorthair)
    for sx in (-1, 1):
        ctx.move_to(sx * 92, -20)
        ctx.curve_to(sx * 96, -70, sx * 86, -96, sx * 70, -96)
        ctx.curve_to(sx * 58, -94, sx * 42, -80, sx * 30, -66)
        ctx.close_path()
        fs(ctx, CAT, INK, 5)
        ctx.move_to(sx * 80, -36)
        ctx.curve_to(sx * 82, -66, sx * 78, -82, sx * 68, -82)
        ctx.curve_to(sx * 60, -80, sx * 50, -72, sx * 44, -64)
        ctx.close_path()
        fill(ctx, PINK)
    # round, chubby-cheeked face
    ellipse(ctx, 0, 4, 100, 78)
    fs(ctx, CAT, INK, 5)
    ellipse(ctx, 0, 30, 46, 30)
    fill(ctx, CREAM)
    # stripes
    for a, b in (((-17, -71), (-12, -47)), ((0, -74), (0, -49)), ((17, -71), (12, -47))):
        if STRIPES: line(ctx, [a, b], CAT_DK, 8)
    for sx in (-1, 1):
        if STRIPES: line(ctx, [(sx * 89, -8), (sx * 70, -4)], CAT_DK, 7)
        if STRIPES: line(ctx, [(sx * 87, 12), (sx * 68, 11)], CAT_DK, 7)
    if blush > 0:
        for sx in (-1, 1):
            ellipse(ctx, sx * 58, 26, 15, 9)
            fill(ctx, PINK, 0.7 * blush)

    def eye(sx, st):
        ex, ey = sx * 35, -6
        if st in ('open', 'half', 'evil', 'wide'):
            rx, ry = (26, 28) if st == 'wide' else (22, 24)
            ellipse(ctx, ex, ey, rx, ry)
            fs(ctx, IRIS, INK, 4)
            if st == 'wide':
                ellipse(ctx, ex + lx * 4, ey + ly * 4, 15, 19)
            else:
                ellipse(ctx, ex + lx * 7, ey + ly * 6, 8, 17)
            fill(ctx, INK)
            ellipse(ctx, ex - 6 + lx * 4, ey - 9, 5.5, 5.5)
            fill(ctx, WHITE)
            if st == 'half':
                ctx.rectangle(ex - 25, ey - 32, 50, 31)
                fill(ctx, CAT)
                line(ctx, [(ex - 21, ey - 1), (ex + 21, ey - 1)], INK, 5)
            elif st == 'evil':
                inner = ex - sx * 25
                outer = ex + sx * 25
                ctx.move_to(outer, ey - 34)
                ctx.line_to(inner, ey - 34)
                ctx.line_to(inner, ey + 5)
                ctx.line_to(outer, ey - 14)
                ctx.close_path()
                fill(ctx, CAT)
                line(ctx, [(ex - sx * 20, ey + 3), (ex + sx * 21, ey - 13)], INK, 5)
        elif st == 'closed':  # happy ^
            ctx.new_sub_path()
            ctx.arc(ex, ey + 8, 16, PI * 1.12, PI * 1.88)
            line_only(ctx, 6)
        else:  # 'sleep' u-shaped closed
            ctx.new_sub_path()
            ctx.arc(ex, ey - 6, 16, PI * 0.15, PI * 0.85)
            line_only(ctx, 6)

    if eyes == 'one':
        eye(-1, 'sleep')
        eye(1, 'half')
    else:
        eye(-1, eyes)
        eye(1, eyes)
    # nose + mouth
    if mouth > 0.05:
        ellipse(ctx, 0, 44 + 6 * mouth, 16 + 4 * mouth, 7 + 22 * mouth)
        fill(ctx, INK)
        ellipse(ctx, 0, 52 + 18 * mouth, 10, 3 + 6 * mouth)
        fill(ctx, PINK)
    ctx.move_to(0, 25)
    ctx.curve_to(-2, 37, -14, 39, -20, 33)
    ctx.move_to(0, 25)
    ctx.curve_to(2, 37, 14, 39, 20, 33)
    line_only(ctx, 4)
    ctx.move_to(-11, 13)
    ctx.line_to(11, 13)
    ctx.line_to(0, 25)
    ctx.close_path()
    fs(ctx, PINK, INK, 3)
    for sx in (-1, 1):
        for (a, b) in (((44, 22), (118, 10)), ((46, 31), (124, 33)), ((44, 40), (114, 57))):
            line(ctx, [(sx * a[0], a[1]), (sx * b[0], b[1])], INK, 3, 0.8)


def line_only(ctx, lw, color=INK):
    ctx.set_source_rgb(*color)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def thick(ctx, pts, w, color, outline=INK, curve=False):
    for lw, col in ((w + 9, outline), (w, color)):
        ctx.move_to(*pts[0])
        if curve:
            ctx.curve_to(*pts[1], *pts[2], *pts[3])
        else:
            for p in pts[1:]:
                ctx.line_to(*p)
        ctx.set_source_rgb(*col)
        ctx.set_line_width(lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def cat_sit(ctx, x, y, s=1.0, facing=1, eyes='open', look=(0, 0), mouth=0.0,
            tail=0.0, paw=0.0, squash=0.0, knead=None, blush=0.0, tilt=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * facing * (1 + squash * 0.14), s * (1 - squash * 0.14))
    look = (look[0] * facing, look[1])
    sw = math.sin(tail) * 32
    thick(ctx, [(-55, -30), (-160, -20), (-170 + sw * 0.3, -120), (-128 + sw, -190)], 24, CAT, curve=True)
    ellipse(ctx, 0, -88, 86, 95)
    fs(ctx, CAT, INK, 5)
    ellipse(ctx, 0, -72, 46, 62)
    fill(ctx, CREAM)
    for sx in (-1, 1):
        if STRIPES: line(ctx, [(sx * 84, -122), (sx * 60, -116)], CAT_DK, 7)
        if STRIPES: line(ctx, [(sx * 86, -90), (sx * 62, -88)], CAT_DK, 7)
    kl = kr = 0
    if knead is not None:
        kl = max(0, math.sin(knead)) * 26
        kr = max(0, -math.sin(knead)) * 26
    ellipse(ctx, -34, -12 - kl, 28, 17)
    fs(ctx, CAT, INK, 5)
    if paw > 0.02:
        px, py = lerp(34, 130, paw), lerp(-12, -100, paw)
        thick(ctx, [(28, -75), (px, py)], 30, CAT)
        ellipse(ctx, px, py, 26, 18)
        fs(ctx, CAT, INK, 5)
    else:
        ellipse(ctx, 34, -12 - kr, 28, 17)
        fs(ctx, CAT, INK, 5)
    ctx.save()
    ctx.translate(0, -205)
    ctx.rotate(tilt)
    cat_head(ctx, eyes, look, mouth, blush)
    ctx.restore()
    ctx.restore()


def cat_walk(ctx, x, y, s, facing, phase, eyes='open', look=(1, 0), tail=0.0, mouth=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * facing, s)
    bob = abs(math.sin(phase)) * 7
    sw = math.sin(tail) * 25
    hips = [(-88, 0.0), (72, PI)]

    def leg(hx, off, col):
        a = math.sin(phase + off) * 0.5
        fx, fy = hx + math.sin(a) * 85, -85 + math.cos(a) * 85 - bob * 0
        thick(ctx, [(hx, -85 - bob), (fx, fy - 4)], 24, col)
        ellipse(ctx, fx + 6, fy - 6, 17, 10)
        fs(ctx, col, INK, 4)

    for hx, off in hips:  # far legs
        leg(hx + 18, off + PI, CAT_DK)
    thick(ctx, [(-112, -112 - bob), (-175, -120), (-195, -205 + sw), (-150, -255 + sw)], 24, CAT, curve=True)
    ellipse(ctx, 0, -105 - bob, 128, 60)
    fs(ctx, CAT, INK, 5)
    for bx in (-60, -20, 20):
        if STRIPES: line(ctx, [(bx, -163 - bob), (bx + 6, -138 - bob)], CAT_DK, 8)
    for hx, off in hips:  # near legs
        leg(hx, off, CAT)
    ctx.save()
    ctx.translate(122, -175 - bob)
    ctx.scale(0.9, 0.9)
    cat_head(ctx, eyes, (look[0] * facing, look[1]), mouth)
    ctx.restore()
    ctx.restore()


def cat_curled(ctx, x, y, s, facing=1, eyes='sleep', breath=0.0, look=(0, 0), blush=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * facing, s)
    b = 1 + 0.035 * math.sin(breath)
    ellipse(ctx, 10, -62 * b, 140, 64 * b)
    fs(ctx, CAT, INK, 5)
    for bx in (10, 50, 90):
        if STRIPES: line(ctx, [(bx, -122 * b), (bx - 4, -96 * b)], CAT_DK, 8)
    ellipse(ctx, -40, -10, 26, 13)
    fs(ctx, CAT, INK, 4)
    ctx.save()
    ctx.translate(-100, -92)
    ctx.rotate(-0.25)
    ctx.scale(0.82, 0.82)
    cat_head(ctx, eyes, (look[0] * facing, look[1]), 0, blush)
    ctx.restore()
    thick(ctx, [(135, -40), (160, 12), (10, 20), (-120, -4)], 24, CAT, curve=True)
    ctx.restore()


# ---------------------------------------------------------------- the owner
def owner_head(ctx, cx, cy, r=86, eyes='open', mouth='smile', blush=0.0,
               look=(0, 0), brow=0.0, sweat=0.0):
    lx, ly = look
    ellipse(ctx, cx + 6, cy - r * 1.02, r * 0.4, r * 0.38)
    fs(ctx, HAIR, INK, 5)
    ellipse(ctx, cx, cy + 6, r * 1.1, r * 1.06)
    fs(ctx, HAIR, INK, 5)
    ellipse(ctx, cx, cy + 12, r * 0.93, r * 0.95)
    fs(ctx, SKIN, INK, 5)
    ctx.save()
    ellipse(ctx, cx, cy + 12, r * 0.93, r * 0.95)
    ctx.clip()
    ellipse(ctx, cx + 18, cy - r * 0.72, r * 1.05, r * 0.5)
    fill(ctx, HAIR)
    ctx.restore()
    if blush > 0:
        for sx in (-1, 1):
            ellipse(ctx, cx + sx * r * 0.55, cy + r * 0.45, 16, 10)
            fill(ctx, PINK, 0.8 * blush)
    for sx in (-1, 1):
        ex, ey = cx + sx * r * 0.34, cy + r * 0.15
        if eyes in ('open', 'flat'):
            ellipse(ctx, ex + lx * 5, ey + ly * 5, 7.5, 11)
            fill(ctx, INK)
            ellipse(ctx, ex + lx * 5 - 2, ey + ly * 5 - 4, 2.5, 2.5)
            fill(ctx, WHITE)
            if eyes == 'flat':
                ctx.rectangle(ex - 14, ey - 16, 28, 16)
                fill(ctx, SKIN)
                line(ctx, [(ex - 13, ey), (ex + 13, ey)], INK, 5)
        elif eyes == 'wide':
            ellipse(ctx, ex, ey, 17, 17)
            fs(ctx, WHITE, INK, 4)
            ellipse(ctx, ex + lx * 6, ey + ly * 6, 5, 5)
            fill(ctx, INK)
        elif eyes == 'closed':
            ctx.new_sub_path()
            ctx.arc(ex, ey + 6, 13, PI * 1.15, PI * 1.85)
            line_only(ctx, 5)
        else:  # sleep
            ctx.new_sub_path()
            ctx.arc(ex, ey - 5, 13, PI * 0.15, PI * 0.85)
            line_only(ctx, 5)
        inner = (ex - sx * 13, ey - 27 + brow * 8)
        outer = (ex + sx * 13, ey - 27 - brow * 8)
        line(ctx, [inner, outer], INK, 5)
    mx, my = cx, cy + r * 0.6
    if mouth == 'smile':
        ctx.new_sub_path()
        ctx.arc(mx, my - 14, 22, PI * 0.2, PI * 0.8)
        line_only(ctx, 5)
    elif mouth == 'big':
        ctx.move_to(mx - 26, my - 8)
        ctx.line_to(mx + 26, my - 8)
        ctx.curve_to(mx + 22, my + 26, mx - 22, my + 26, mx - 26, my - 8)
        ctx.close_path()
        fs(ctx, INK, INK, 4)
        ellipse(ctx, mx, my + 10, 11, 5)
        fill(ctx, PINK)
    elif mouth == 'flat':
        line(ctx, [(mx - 15, my), (mx + 15, my)], INK, 5)
    elif mouth == 'o':
        ellipse(ctx, mx, my + 2, 10, 13)
        fill(ctx, INK)
    elif mouth == 'snore':
        ellipse(ctx, mx, my, 6, 7)
        fill(ctx, INK)
    elif mouth == 'sad':
        ctx.new_sub_path()
        ctx.arc(mx, my + 18, 19, PI * 1.2, PI * 1.8)
        line_only(ctx, 5)
    elif mouth == 'grit':
        rrect(ctx, mx - 27, my - 12, 54, 24, 8)
        fs(ctx, WHITE, INK, 4)
        for gx in (-13, 0, 13):
            line(ctx, [(mx + gx, my - 12), (mx + gx, my + 12)], INK, 3)
        line(ctx, [(mx - 27, my), (mx + 27, my)], INK, 3)
    if sweat > 0:
        sx_, sy_ = cx + r * 0.95, cy - r * 0.15
        ctx.move_to(sx_, sy_ - 24)
        ctx.curve_to(sx_ + 16, sy_, sx_ + 14, sy_ + 16, sx_, sy_ + 16)
        ctx.curve_to(sx_ - 14, sy_ + 16, sx_ - 16, sy_, sx_, sy_ - 24)
        fs(ctx, rgb('#9FD8FF'), INK, 3, sweat)


def arm(ctx, sh, hand):
    thick(ctx, [sh, hand], 40, SHIRT)
    ellipse(ctx, hand[0], hand[1], 25, 25)
    fs(ctx, SKIN, INK, 5)


ARMS = {
    'down': ((-122, -290), (122, -290)),
    'open': ((-255, -700), (255, -700)),
    'phone': ((-122, -290), (5, -430)),
    'hold': ((-122, -290), (60, -450)),
    'pour': ((-122, -290), (160, -430)),
}


def owner_stand(ctx, x, y, armA='down', armB=None, arm_t=0.0, head=None, dx=0.0):
    head = head or {}
    for sx in (-1, 1):
        rrect(ctx, x + sx * 52 - 32, y - 270, 64, 258, 28)
        fs(ctx, PANTS, INK, 5)
        ellipse(ctx, x + sx * 60, y - 10, 46, 20)
        fs(ctx, SHOE, INK, 5)
    x += dx
    rrect(ctx, x - 110, y - 585, 220, 345, 70)
    fs(ctx, SHIRT, INK, 5)
    rrect(ctx, x - 62, y - 372, 124, 62, 22)
    fs(ctx, SHIRT_DK, INK, 4)
    owner_head(ctx, x, y - 680, 88, **head)
    A = ARMS[armA]
    B = ARMS[armB] if armB else A
    hands = [(lerp(A[i][0], B[i][0], arm_t), lerp(A[i][1], B[i][1], arm_t)) for i in (0, 1)]
    for i, sx in enumerate((-1, 1)):
        arm(ctx, (x + sx * 92, y - 530), (x + hands[i][0], y + hands[i][1]))
    if armA == 'phone':
        hx, hy = x + hands[1][0], y + hands[1][1]
        rrect(ctx, hx - 30, hy - 72, 60, 100, 10)
        fs(ctx, rgb('#333344'), INK, 4)
        rrect(ctx, hx - 23, hy - 64, 46, 80, 6)
        fill(ctx, rgb('#9BE2FF'))
        ellipse(ctx, hx, hy, 25, 25)
        fs(ctx, SKIN, INK, 5)


def owner_sit(ctx, x, seat_y, head=None, hands=None, legs=True):
    head = head or {}
    if legs:
        for sx in (-1, 1):
            rrect(ctx, x + sx * 55 - 32, seat_y, 64, 222, 28)
            fs(ctx, PANTS, INK, 5)
            ellipse(ctx, x + sx * 62, seat_y + 222, 46, 20)
            fs(ctx, SHOE, INK, 5)
    rrect(ctx, x - 110, seat_y - 345, 220, 330, 70)
    fs(ctx, SHIRT, INK, 5)
    rrect(ctx, x - 128, seat_y - 45, 256, 82, 38)
    fs(ctx, PANTS, INK, 5)
    owner_head(ctx, x, seat_y - 440, 88, **head)
    hands = hands or [(x - 80, seat_y - 40), (x + 80, seat_y - 40)]
    for i, sx in enumerate((-1, 1)):
        arm(ctx, (x + sx * 92, seat_y - 290), hands[i])


# ---------------------------------------------------------------- rooms
FLOOR_Y = 1420


def wall_floor(ctx, wall, floor, floor_dk, checker=False):
    ctx.rectangle(0, 0, W, FLOOR_Y)
    fill(ctx, wall)
    ctx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    fill(ctx, floor)
    if checker:
        for i in range(-2, 14):
            for j in range(8):
                if (i + j) % 2 == 0:
                    y0 = FLOOR_Y + j * 70
                    x0 = i * 100 + (j * 18)
                    ctx.rectangle(x0, y0, 100, 70)
        fill(ctx, floor_dk, 0.6)
    else:
        y = FLOOR_Y + 40
        step = 46
        while y < H:
            line(ctx, [(0, y), (W, y)], floor_dk, 4, 0.7)
            off = (y * 7) % 260
            for x in range(-int(off), W, 260):
                line(ctx, [(x, y - step + 4), (x, y)], floor_dk, 3, 0.5)
            step += 14
            y += step
    ctx.rectangle(0, FLOOR_Y - 26, W, 30)
    fs(ctx, WHITE, INK, 4)


def window(ctx, x, y, w, h, top, bot, night=False):
    rrect(ctx, x - 14, y - 14, w + 28, h + 28, 14)
    fs(ctx, WHITE, INK, 5)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, *top)
    g.add_color_stop_rgb(1, *bot)
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()
    if night:
        ellipse(ctx, x + w * 0.7, y + h * 0.3, 40, 40)
        fill(ctx, rgb('#FFF4C2'))
        ellipse(ctx, x + w * 0.7 + 18, y + h * 0.3 - 10, 34, 34)
        fill(ctx, top)
        for (sx, sy) in ((0.2, 0.2), (0.35, 0.6), (0.15, 0.75), (0.55, 0.15), (0.85, 0.7)):
            ellipse(ctx, x + w * sx, y + h * sy, 4, 4)
            fill(ctx, WHITE)
    ctx.rectangle(x, y, w, h)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    line(ctx, [(x + w / 2, y), (x + w / 2, y + h)], WHITE, 14)
    line(ctx, [(x, y + h / 2), (x + w, y + h / 2)], WHITE, 14)


def cloud(ctx, x, y, s):
    for (dx, dy, r) in ((0, 0, 30), (30, -14, 34), (62, 0, 28), (30, 8, 30)):
        ellipse(ctx, x + dx * s, y + dy * s, r * s, r * s)
    fill(ctx, WHITE)


def plant(ctx, x, y, s=1.0):
    for a in (-0.9, -0.45, 0, 0.45, 0.9):
        ctx.save()
        ctx.translate(x, y - 90 * s)
        ctx.rotate(a)
        ellipse(ctx, 0, -70 * s, 26 * s, 75 * s)
        fs(ctx, rgb('#5CB85C'), INK, 4)
        ctx.restore()
    ctx.move_to(x - 60 * s, y - 100 * s)
    ctx.line_to(x + 60 * s, y - 100 * s)
    ctx.line_to(x + 45 * s, y)
    ctx.line_to(x - 45 * s, y)
    ctx.close_path()
    fs(ctx, rgb('#E07A5F'), INK, 5)


def frame_pic(ctx, x, y, w, h, kind='fish'):
    rrect(ctx, x, y, w, h, 8)
    fs(ctx, rgb('#F2C14E'), INK, 5)
    ctx.rectangle(x + 16, y + 16, w - 32, h - 32)
    fs(ctx, rgb('#BDE0FE'), INK, 3)
    cx, cy = x + w / 2, y + h / 2
    if kind == 'fish':
        ellipse(ctx, cx - 6, cy, 34, 20)
        fs(ctx, rgb('#FF8C42'), INK, 3)
        ctx.move_to(cx + 24, cy)
        ctx.line_to(cx + 46, cy - 16)
        ctx.line_to(cx + 46, cy + 16)
        ctx.close_path()
        fs(ctx, rgb('#FF8C42'), INK, 3)
    else:
        heart(ctx, cx, cy, 26)


def bg_bedroom(ctx, t):
    wall_floor(ctx, rgb('#FBE7D3'), rgb('#D6A06C'), WOOD_DK)
    window(ctx, 650, 520, 300, 300, rgb('#FFB4A2'), rgb('#FFE5B4'))
    ellipse(ctx, 800, 760, 60, 60)
    fill(ctx, rgb('#FFD166'))
    window_cover = rgb('#FBE7D3')
    ctx.rectangle(650, 818, 300, 2)
    fill(ctx, window_cover)
    # wall clock 6:00
    cx, cy = 250, 640
    ellipse(ctx, cx, cy, 78, 78)
    fs(ctx, WHITE, INK, 7)
    for i in range(12):
        a = i * PI / 6
        line(ctx, [(cx + math.cos(a) * 60, cy + math.sin(a) * 60),
                   (cx + math.cos(a) * 68, cy + math.sin(a) * 68)], INK, 4)
    line(ctx, [(cx, cy), (cx, cy - 55)], INK, 6)
    line(ctx, [(cx, cy), (cx, cy + 40)], INK, 8)
    ellipse(ctx, cx, cy, 7, 7)
    fill(ctx, RED)


def bed_back(ctx):
    rrect(ctx, 70, 980, 80, 470, 30)
    fs(ctx, WOOD, INK, 5)
    rrect(ctx, 100, 1330, 900, 80, 20)
    fs(ctx, WOOD, INK, 5)
    for lx in (120, 960):
        ctx.rectangle(lx, 1400, 26, 60)
        fs(ctx, WOOD_DK, INK, 4)
    rrect(ctx, 110, 1220, 880, 125, 30)
    fs(ctx, WHITE, INK, 5)
    ellipse(ctx, 265, 1200, 135, 55)
    fs(ctx, rgb('#F7F7FF'), INK, 5)


def blanket(ctx):
    ctx.move_to(320, 1215)
    ctx.curve_to(400, 1150, 520, 1135, 620, 1170)
    ctx.curve_to(720, 1205, 820, 1210, 880, 1180)
    ctx.curve_to(930, 1160, 975, 1180, 990, 1220)
    ctx.line_to(990, 1350)
    ctx.line_to(320, 1350)
    ctx.close_path()
    fs(ctx, rgb('#B9A3E3'), INK, 5)
    for (dx, dy) in ((420, 1260), (560, 1300), (700, 1250), (840, 1300), (480, 1210), (900, 1240)):
        heart(ctx, dx, dy, 12, rgb('#E4D7FF'), 1.0)


def bg_office(ctx, t):
    wall_floor(ctx, rgb('#E3EFD9'), rgb('#C89463'), WOOD_DK)
    window(ctx, 690, 520, 290, 300, rgb('#8ED1FC'), rgb('#D7F0FF'))
    cloud(ctx, 740 + (t * 8) % 120, 600, 1.0)
    # bookshelf
    rrect(ctx, 60, 520, 230, 560, 10)
    fs(ctx, WOOD, INK, 5)
    cols = ['#E76F51', '#2A9D8F', '#E9C46A', '#8E7DBE', '#F4A261', '#457B9D']
    for row in range(3):
        y0 = 540 + row * 180
        line(ctx, [(70, y0 + 160), (280, y0 + 160)], INK, 5)
        x0 = 80
        for k in range(6):
            bw = 26 + (k * 7) % 12
            bh = 110 + (k * 13 + row * 17) % 40
            ctx.rectangle(x0, y0 + 158 - bh, bw, bh)
            fs(ctx, rgb(cols[(k + row) % 6]), INK, 3)
            x0 += bw + 4
    plant(ctx, 960, FLOOR_Y + 40, 0.9)


def desk_top(ctx):
    rrect(ctx, 50, 1228, 980, 40, 10)
    fs(ctx, WOOD, INK, 5)


def desk_front(ctx):
    ctx.rectangle(80, 1266, 920, 150)
    fs(ctx, WOOD_DK, INK, 5)
    for lx in (80, 974):
        ctx.rectangle(lx, 1266, 26, 290)
        fs(ctx, WOOD_DK, INK, 5)
    rrect(ctx, 680, 1290, 260, 50, 10)
    fs(ctx, WOOD, INK, 4)
    ellipse(ctx, 810, 1315, 9, 9)
    fill(ctx, INK)


def laptop(ctx, cx):
    rrect(ctx, cx - 150, 1095, 300, 152, 16)
    fs(ctx, rgb('#C9CED6'), INK, 5)
    paw_print(ctx, cx, 1175, 22, rgb('#9AA1AC'), 1.0)
    rrect(ctx, cx - 175, 1240, 350, 14, 6)
    fs(ctx, rgb('#AEB4BD'), INK, 4)


def bg_living(ctx, t):
    wall_floor(ctx, rgb('#F7D6CF'), rgb('#C98E5F'), WOOD_DK)
    frame_pic(ctx, 760, 500, 220, 170, 'fish')
    frame_pic(ctx, 110, 470, 150, 130, 'heart')
    plant(ctx, 120, FLOOR_Y + 20, 1.0)
    ellipse(ctx, 560, 1610, 470, 120)
    fs(ctx, rgb('#9AD1D4'), INK, 5)
    ellipse(ctx, 560, 1610, 380, 90)
    ctx.set_source_rgba(1, 1, 1, 0.45)
    ctx.set_line_width(8)
    ctx.stroke()


def bg_kitchen(ctx, t):
    wall_floor(ctx, rgb('#FFF3CC'), rgb('#F5F5F5'), rgb('#9BB7D4'), checker=True)
    # backsplash tiles
    ctx.rectangle(0, 860, W, 300)
    fill(ctx, rgb('#DFF3F0'))
    for gx in range(0, W, 90):
        line(ctx, [(gx, 860), (gx, 1160)], rgb('#B5DCD6'), 3)
    for gy in range(860, 1161, 75):
        line(ctx, [(0, gy), (W, gy)], rgb('#B5DCD6'), 3)
    window(ctx, 640, 470, 320, 280, rgb('#8ED1FC'), rgb('#D7F0FF'))
    cloud(ctx, 690, 560, 0.9)
    # hanging pans
    line(ctx, [(80, 470), (420, 470)], INK, 8)
    for i, px in enumerate((140, 250, 360)):
        line(ctx, [(px, 470), (px, 520)], INK, 4)
        ellipse(ctx, px, 575, 42 - i * 4, 42 - i * 4)
        fs(ctx, rgb('#5A5A6E'), INK, 4)


def table(ctx):
    for lx in (500, 980):
        ctx.rectangle(lx - 14, 1180, 28, 360)
        fs(ctx, WOOD_DK, INK, 5)
    rrect(ctx, 465, 1150, 570, 34, 10)
    fs(ctx, WOOD, INK, 5)


def glass(ctx, x, ybot, rot=0.0):
    ctx.save()
    ctx.translate(x, ybot)
    ctx.rotate(rot)
    ctx.move_to(-28, -92)
    ctx.line_to(28, -92)
    ctx.line_to(22, 0)
    ctx.line_to(-22, 0)
    ctx.close_path()
    fs(ctx, rgb('#EAF8FF'), INK, 4)
    ctx.move_to(-25, -60)
    ctx.line_to(25, -60)
    ctx.line_to(22, -3)
    ctx.line_to(-22, -3)
    ctx.close_path()
    fill(ctx, rgb('#7CC6FE'), 0.8)
    line(ctx, [(-14, -80), (-12, -20)], WHITE, 5, 0.8)
    ctx.restore()


def bg_night(ctx, t, dim=0.0):
    wall_floor(ctx, rgb('#6B5B95'), rgb('#7A5638'), rgb('#5A3E27'))
    window(ctx, 90, 470, 260, 300, rgb('#1D2B53'), rgb('#3E4C8A'), night=True)
    frame_pic(ctx, 760, 480, 200, 160, 'heart')
    # lamp glow
    g = cairo.RadialGradient(930, 1000, 10, 930, 1000, 520)
    g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.55)
    g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0.0)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(g)
    ctx.fill()
    ctx.rectangle(925, 1020, 12, 400)
    fs(ctx, INK, None)
    ctx.move_to(860, 1030)
    ctx.line_to(1000, 1030)
    ctx.line_to(970, 920)
    ctx.line_to(890, 920)
    ctx.close_path()
    fs(ctx, rgb('#FFE8A3'), INK, 5)
    ellipse(ctx, 930, 1420, 60, 14)
    fill(ctx, INK)


def couch_back(ctx):
    rrect(ctx, 150, 960, 780, 420, 70)
    fs(ctx, rgb('#3E9C9E'), INK, 6)
    for cx in (345, 735):
        rrect(ctx, cx - 180, 1000, 360, 300, 50)
        fs(ctx, rgb('#58B4B5'), INK, 4)
    rrect(ctx, 190, 1300, 700, 130, 34)
    fs(ctx, rgb('#58B4B5'), INK, 5)
    for ax in (90, 850):
        rrect(ctx, ax, 1150, 140, 330, 50)
        fs(ctx, rgb('#2F8486'), INK, 6)
    for lx in (180, 880):
        ctx.rectangle(lx, 1475, 24, 40)
        fs(ctx, WOOD_DK, INK, 4)


# ---------------------------------------------------------------- scenes
def zzz(ctx, t, x, y):
    for i in range(3):
        p = ((t * 0.7) + i / 3.0) % 1.0
        floaty_text(ctx, 'Z', x + p * 120 + math.sin(p * 6) * 10, y - p * 200,
                    30 + p * 40, math.sin(p * PI), rot=-0.2, color=rgb('#A0C4FF'))


def scene1(ctx, t):
    bg_bedroom(ctx, t)
    bed_back(ctx)
    awake = t >= 2.95
    if not awake:
        hd = dict(eyes='sleep', mouth='snore')
    elif t < 3.7:
        hd = dict(eyes='wide', mouth='o', look=(1, -0.3), brow=-1)
    else:
        hd = dict(eyes='flat', mouth='flat', look=(1, -0.3))
    hy = 1135
    tap = max([max(0.0, 1 - abs(t - tc) / 0.2) for tc in (1.0, 1.6, 2.2)])
    owner_head(ctx, 268 - tap * 6, hy, 78, **hd)
    blanket(ctx)
    if not awake:
        zzz(ctx, t, 300, 1030)
    for tc in (1.0, 1.6, 2.2):
        a = seg(t, tc, tc + 0.5)
        if 0 < a < 1:
            floaty_text(ctx, 'boop', 320, 1010 - a * 60, 40, 1 - a, -0.15)
    paw = ease(tap)
    meow = window_on(t, 2.75, 3.45)
    eyes = 'half' if t < 2.7 else ('open' if t < 3.6 else 'closed')
    shake = math.sin(t * 90) * 4 if meow else 0
    cat_sit(ctx, 470 + shake, 1188, 0.78, facing=-1, eyes=eyes, look=(1, 0),
            mouth=1.0 if meow else 0.0, tail=t * 3, paw=paw, blush=0.9 if t > 3.6 else 0)
    burst(ctx, 690, 870, 'MEOW!!!', t, 2.8, 3.6)
    bub(ctx, t, 3.65, 5.5, 650, 820, 'I love you.\nNow FEED ME.', (520, 990))


def scene2(ctx, t):
    bg_office(ctx, t)
    sat = t >= 2.85
    if t < 2.85:
        hd = dict(eyes='open', mouth='smile' if t < 2.4 else 'o', look=(0.6, 0.8 if t < 2.3 else 0))
    else:
        hd = dict(eyes='flat', mouth='flat', look=(0.5, 0))
    owner_sit(ctx, 460, 1300, head=hd, hands=[(400, 1225), (560, 1225)], legs=True)
    desk_top(ctx)
    # cat walking along the desk (behind laptop depth)
    if 1.0 <= t < 2.3:
        p = seg(t, 1.0, 2.3)
        cat_walk(ctx, lerp(1200, 820, p), 1236, 0.68, -1, t * 13, eyes='open', tail=t * 4)
    laptop(ctx, 545)
    # cat hops ONTO the laptop keyboard (drawn in front)
    if 2.3 <= t < 2.85:
        p = ease(seg(t, 2.3, 2.85))
        cx = lerp(820, 560, p)
        cy = 1248 - math.sin(p * PI) * 130
        cat_sit(ctx, cx, cy, 0.74, facing=-1, eyes='open', look=(-1, 0), squash=-0.4 * math.sin(p * PI), tail=t * 3)
    elif sat:
        sq = math.exp(-(t - 2.85) * 9) * math.cos((t - 2.85) * 30) * 0.8
        cat_sit(ctx, 560, 1250, 0.74, facing=1, eyes='half', look=(0, 0), squash=sq, tail=t * 2.5)
    desk_front(ctx)
    # chat popup
    if sat:
        p = seg(t, 2.9, 3.15)
        n = int(clamp((t - 2.9) / 1.1) * 26)
        msg = ('jjjjjjjjjkkkkkkkk;;;;;;;;;;;;;'[:n] or ' ')
        ctx.save()
        s = lerp(0.6, 1, eob(p))
        ctx.translate(770, 600)
        ctx.scale(s, s)
        rrect(ctx, -240, -95, 480, 190, 26)
        fs(ctx, WHITE, INK, 6)
        rrect(ctx, -240, -95, 480, 58, 26)
        fill(ctx, rgb('#5B8DEF'))
        ctx.rectangle(-240, -60, 480, 23)
        fill(ctx, rgb('#5B8DEF'))
        set_font(ctx, 30)
        draw_lines(ctx, ['Team Call  •  chat'], 0, -66, 30, WHITE)
        set_font(ctx, 34, bold=False)
        ctx.move_to(-218, 20)
        ctx.text_path('You: ')
        fill(ctx, rgb('#888888'))
        set_font(ctx, 34)
        ctx.move_to(-133, 20)
        ctx.text_path(msg[:13])
        ctx.move_to(-218, 66)
        ctx.text_path(msg[13:])
        fill(ctx, INK)
        ctx.restore()
    bub(ctx, t, 0.35, 2.5, 380, 700, 'Okay team, let me share my scree—', (440, 800))
    bub(ctx, t, 4.0, 5.5, 300, 720, '...Biscuit is presenting now.', (420, 830), size=46, maxw=470)


def scene3(ctx, t):
    bg_living(ctx, t)
    up = ease(seg(t, 0.2, 0.6))
    down = ease(seg(t, 2.8, 3.6))
    arm_t = up * (1 - down)
    if t < 2.6:
        hd = dict(eyes='closed', mouth='big', blush=1.0)
    elif t < 3.2:
        hd = dict(eyes='open', mouth='o', brow=-1, look=(1, 0))
    elif t < 4.7:
        hd = dict(eyes='open', mouth='sad', brow=-1, look=(1, 0.3))
    else:
        hd = dict(eyes='open', mouth='flat', brow=-0.5, look=(1, 0))
    owner_stand(ctx, 290, 1540, 'down', 'open', arm_t, head=hd)
    if 0.5 < t < 2.6:
        for i in range(5):
            p = ((t - 0.5) * 0.8 + i / 5) % 1
            heart(ctx, 290 + math.sin(i * 2.3 + t * 2) * 200, 900 - p * 260, 16 + i * 2,
                  alpha=math.sin(p * PI), rot=math.sin(t * 3 + i) * 0.3)
    if t < 2.5:
        eyes = 'open' if t < 1.6 else 'half'
        cat_sit(ctx, 790, 1540, 1.0, facing=-1, eyes=eyes, look=(-1, 0), tail=t * 2)
    elif t < 4.3:
        p = seg(t, 2.5, 4.3)
        cat_walk(ctx, lerp(790, 1350, p), 1540, 0.95, 1, t * 11, eyes='half', look=(1, 0), tail=t * 3)
    if t >= 4.8:
        p = ease(seg(t, 4.8, 5.15))
        ctx.save()
        ctx.translate(lerp(1150, 935, p), 1180)
        ctx.rotate(-0.35)
        cat_head(ctx, 'half', (-1, 0))
        ctx.restore()
    bub(ctx, t, 0.5, 2.5, 330, 590, 'Come here, my baby!', (300, 770))
    bub(ctx, t, 1.9, 2.6, 800, 1080, 'Ew. No.', (800, 1240))
    bub(ctx, t, 3.4, 4.7, 300, 600, '...ok.', (300, 770))
    bub(ctx, t, 5.1, 6.0, 640, 960, 'But don\'t go anywhere.', (880, 1100), size=46)


def scene4(ctx, t):
    bg_kitchen(ctx, t)
    crashed = t >= 3.55
    if t < 1.0:
        hd = dict(eyes='open', mouth='flat', look=(0.3, 1))
    elif t < 3.55:
        hd = dict(eyes='open', mouth='flat', brow=1, look=(1, 0))
    elif t < 4.4:
        hd = dict(eyes='wide', mouth='o', look=(1, 0.5))
    else:
        hd = dict(eyes='flat', mouth='flat', brow=1, look=(1, 0))
    owner_stand(ctx, 215, 1545, 'phone', head=hd)
    table(ctx)
    catx = lerp(700, 600, ease(seg(t, 2.5, 3.1)))
    paw = ease(seg(t, 2.0, 2.5)) * (1 - ease(seg(t, 3.3, 3.7)))
    # glass
    if t < 3.1:
        gx = 585 - (700 - catx)
        glass(ctx, gx, 1150)
    elif not crashed:
        p = (t - 3.1) / 0.45
        glass(ctx, 485 - 70 * p, 1150 + 390 * p * p, -2.0 * p)
    else:
        # puddle + shards
        ellipse(ctx, 410, 1560, 120, 24)
        fs(ctx, rgb('#7CC6FE'), INK, 4, 0.8)
        for i, (dx, dy, r) in enumerate(((-70, -6, 0.3), (-20, 4, -0.6), (40, -4, 1.1), (80, 6, 0.2), (0, -14, 2.0))):
            k = clamp((t - 3.55) * 6)
            ctx.save()
            ctx.translate(410 + dx * (0.4 + 0.6 * k), 1555 + dy - math.sin(k * PI) * 40)
            ctx.rotate(r)
            ctx.move_to(-14, 8)
            ctx.line_to(0, -16)
            ctx.line_to(12, 8)
            ctx.close_path()
            fs(ctx, rgb('#EAF8FF'), INK, 3)
            ctx.restore()
    if t < 3.6:
        eyes, blush, look = 'evil', 0, (-1, 0)
    else:
        eyes, blush, look = 'open', 0.9, (-1, 0)
    cat_sit(ctx, catx, 1152, 0.85, facing=-1, eyes=eyes, look=look, paw=paw, tail=t * 1.6, blush=blush)
    burst(ctx, 400, 1330, 'CRASH!', t, 3.55, 4.6, size=100, rot=0.1)
    bub(ctx, t, 1.1, 2.8, 330, 640, 'Don\'t. You. Dare.', (240, 780))
    bub(ctx, t, 4.0, 5.5, 760, 820, 'oops.', (640, 960))


def scene56(ctx, t, later=False):
    bg_night(ctx, t)
    couch_back(ctx)
    seat = 1330
    jitter = math.sin(t * 45) * 2.5 if later and t > 0.4 else 0
    if later:
        hd = dict(eyes='flat', mouth='grit', brow=-1, sweat=0.6 + 0.4 * math.sin(t * 6), look=(0.6, 0.6))
        hands = [(430, seat - 40), (650 + math.sin(t * 2) * 6, seat - 120)]
    else:
        if t < 1.8:
            hd = dict(eyes='open', mouth='smile', look=(1, 0.5))
        elif t < 2.5:
            hd = dict(eyes='wide', mouth='big', look=(0.3, 1))
        else:
            hd = dict(eyes='closed', mouth='big', blush=1.0)
        if t >= 2.5:
            hands = [(430, seat - 40), (610 + math.sin(t * 2.5) * 45, seat - 118)]
        else:
            hands = None
    owner_sit(ctx, 540 + jitter, seat, head=hd, hands=None)
    # cat
    if not later and t < 1.3:
        if t >= 0.1:
            p = seg(t, 0.1, 1.3)
            cat_walk(ctx, lerp(1180, 840, p), 1660, 0.75, -1, t * 12, eyes='open', look=(-1, 0), tail=t * 3)
    elif not later and t < 1.8:
        p = ease(seg(t, 1.3, 1.8))
        cx = lerp(840, 560, p)
        cy = lerp(1660, 1325, p) - math.sin(p * PI) * 170
        cat_sit(ctx, cx, cy, lerp(0.75, 0.8, p), facing=-1, eyes='open', look=(-1, 0),
                squash=-0.5 * math.sin(p * PI), tail=t * 3)
    elif not later and t < 2.5:
        cat_sit(ctx, 560, 1325, 0.8, facing=-1, eyes='closed', knead=t * 16, tail=t * 3, blush=0.8)
        floaty_text(ctx, 'knead knead', 790, 1130 - (t - 1.8) * 40, 40, 1 - seg(t, 2.3, 2.5), 0.1)
    else:
        eyes = 'sleep'
        if later and t > 2.2:
            eyes = 'one'
        cat_curled(ctx, 545, 1330, 0.85, facing=-1, eyes=eyes, breath=t * 3, look=(-1, -0.5), blush=0.6)
    # petting hand on top
    if hands:
        arm(ctx, (540 + jitter + 92, seat - 290), hands[1])
    if later:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0.08, 0.06, 0.25, 0.25)
        ctx.fill()
    # hearts + purr
    if (not later and t >= 2.6) or later:
        t0 = 2.6 if not later else 0
        for i in range(6):
            p = ((t - t0) * 0.45 + i / 6) % 1
            if not later and (t - t0) * 0.45 < i / 6 and p > 0.9:
                continue
            heart(ctx, 560 + math.sin(i * 1.7 + t * 1.5) * 150 + (i - 3) * 30, 1180 - p * 330,
                  14 + (i % 3) * 5, alpha=math.sin(p * PI) * (0.5 if later else 1), rot=math.sin(t * 2 + i) * 0.3)
        floaty_text(ctx, 'prrrrrr', 810 + math.sin(t * 20) * 3, 1170, 44,
                    0.6 + 0.4 * math.sin(t * 4), -0.08, rgb('#FFE8A3'))
    if not later:
        bub(ctx, t, 3.0, 5.0, 420, 640, 'She loves me!! She REALLY loves me!', (500, 790))
        bub(ctx, t, 5.0, 6.5, 760, 720, 'Mmm. Heated seat. 10/10.', (640, 1190), thought=True, size=46)
    else:
        bub(ctx, t, 0.5, 2.5, 420, 640, 'I really... REALLY need to pee.', (500, 790))
        bub(ctx, t, 2.6, 4.3, 760, 1010, 'You live here now.', (650, 1200))


def end_card(ctx, t, title=('Tag someone whose', 'cat owns them'), sub='Follow for more cat chaos'):
    a = ease(seg(t, 0, 0.4))
    ctx.rectangle(0, 0, W, H)
    ctx.set_source_rgba(0.1, 0.06, 0.2, 0.6 * a)
    ctx.fill()
    for i in range(8):
        k = seg(t, i * 0.12, i * 0.12 + 0.15)
        if k > 0:
            paw_print(ctx, 160 + i * 110, 1250 - (i % 2) * 60, 30, rgb('#FFB4A2'), k, 0.3)
    p = seg(t, 0.15, 0.5)
    if p > 0:
        ctx.save()
        s = lerp(0.5, 1, eob(p))
        ctx.translate(540, 820)
        ctx.scale(s, s)
        set_font(ctx, 82)
        draw_lines(ctx, list(title), 0, 0, 82, WHITE, outline=INK, ow=14)
        ctx.restore()
    p2 = seg(t, 0.5, 0.8)
    if p2 > 0:
        ctx.push_group()
        set_font(ctx, 46)
        draw_lines(ctx, [sub], 540, 1010, 46, YELLOW, outline=INK, ow=10)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(p2)


CAPTIONS = [
    (0.15, 5.5, '6:00 AM. How my cat\nsays "I love you":'),
    (5.6, 11.0, 'Working from home\nwith a cat:'),
    (11.1, 13.6, 'When I want cuddles:'),
    (13.6, 17.0, 'Rejected. In my own home.'),
    (17.1, 20.8, 'When I ignore her\nfor 5 minutes:'),
    (20.8, 22.5, '...with FULL eye contact.'),
    (22.6, 29.0, 'But at night...'),
    (29.1, 33.2, '3 hours later...'),
]
SCENES = [0.0, 5.5, 11.0, 17.0, 22.5, 29.0, 35.0]
PUNCH = [2.8, 20.55, 23.8]


def caption(ctx, t, caps=None):
    for a, b, text in (caps or CAPTIONS):
        if a <= t < b:
            p = seg(t, a, a + 0.25)
            alpha = 1 - seg(t, b - 0.12, b)
            set_font(ctx, 58)
            lines = text.split('\n')
            w = max(tw(ctx, l) for l in lines) + 90
            h = len(lines) * 58 * 1.22 + 54
            ctx.push_group()
            ctx.translate(540, 300)
            s = lerp(0.8, 1, eob(p))
            ctx.scale(s, s)
            rrect(ctx, -w / 2 + 8, -h / 2 + 10, w, h, 30)
            fill(ctx, (0, 0, 0), 0.25)
            rrect(ctx, -w / 2, -h / 2, w, h, 30)
            fs(ctx, WHITE, INK, 6)
            draw_lines(ctx, lines, 0, 0, 58, INK)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(alpha * clamp(p * 3))


def render(ctx, t):
    ctx.save()
    z = 1.0
    for p in PUNCH:
        if t >= p:
            z += 0.07 * math.exp(-(t - p) * 7)
    ctx.translate(540, 1150)
    ctx.scale(z * 1.1, z * 1.1)
    ctx.translate(-540, -1150)
    if t < 5.5:
        scene1(ctx, t)
    elif t < 11:
        scene2(ctx, t - 5.5)
    elif t < 17:
        scene3(ctx, t - 11)
    elif t < 22.5:
        scene4(ctx, t - 17)
    elif t < 29:
        scene56(ctx, t - 22.5)
    else:
        scene56(ctx, t - 29, later=True)
    ctx.restore()
    caption(ctx, t)
    if t >= 33.2:
        end_card(ctx, t - 33.2)
    # transitions
    for s in SCENES[1:-1]:
        if s <= t < s + 0.25:
            ctx.rectangle(0, 0, W, H)
            ctx.set_source_rgba(1, 1, 1, 1 - seg(t, s, s + 0.25))
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
    mode = sys.argv[1]
    out = sys.argv[2]
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
        surf = frame_surface(i / FPS)
        proc.stdin.write(bytes(surf.get_data()))
        if i % 150 == 0:
            print(f'frame {i}/{n}', flush=True)
    proc.stdin.close()
    proc.wait()


if __name__ == '__main__':
    main()
