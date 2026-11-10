"""Munchie - original cartoon mascot presenter reel for Vape & Munchies."""
import os, re, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import design as D
from design import W, H, FPS, paste, tspr, sticker, star, pill, eb, eo, cl, bg, header, flash, rgb_split, F, BUNGEE
import music
INK=(17,15,22); BLUE=(62,193,232); BLUE_D=(36,150,200); ORANGE=(245,130,31); CREAM=(255,244,224); YEL=(255,214,40); WHITE=(255,255,255)

LINES = [  # (start, text spoken, caption lines)
    (0.4, "Hey! I'm Munchie!", ["HEY!", "I'M MUNCHIE!"]),
    (2.8, "Meet Cheetos Masala Balls!", ["MEET CHEETOS", "MASALA BALLS!"]),
    (6.0, "Find it in store, open twenty four seven!", ["FIND IT IN STORE,", "OPEN 24/7!"]),
    (9.2, "On Brunette Ave, Coquitlam!", ["ON BRUNETTE AVE,", "COQUITLAM!"]),
    (12.4, "Come snack with me!", ["COME SNACK", "WITH ME!"]),
]
DUR = 15.0
SYL = .17

def syllables(txt):
    out = []
    for w in txt.split():
        n = max(1, len(re.findall(r'[aeiouy]+', w.lower()))); out.append(n)
    return out

def build_sched():
    sch = []; caps = []
    for k, (t0, txt, cap) in enumerate(LINES):
        t = t0; rng = np.random.default_rng(k + 3)
        for n in syllables(txt):
            for s in range(n):
                sch.append((t, SYL * .9, float(rng.uniform(.65, 1.0)), float(rng.uniform(430, 620)))); t += SYL
            t += .07
        caps.append((t0, t + .35, cap))
    return sch, caps
SCHED, CAPS = build_sched()

def mouth_open(t):
    m = 0.0
    for s, d, a, _ in SCHED:
        if s <= t < s + d: m = max(m, a * math.sin(math.pi * (t - s) / d))
    return m

S = 2  # supersample
def draw_munchie(op, blink, look, armL, armR, squash=0.0):
    cw, ch = 800, 860
    im = Image.new('RGBA', (cw * S, ch * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def E(b, **k): d.ellipse([v * S for v in b], **k)
    def L(pts, w, fill): d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(w * S), joint='curve')
    cx = 400; by = 520 - squash * 10; ry = 290 * (1 + squash * .03); rx = 270 * (1 - squash * .02)
    # feet
    for fx in (310, 490): E((fx - 62, 770, fx + 62, 835), fill=ORANGE + (255,), outline=INK + (255,), width=8 * S)
    # arms behind body
    def arm(sx, sy, ang, flip):
        ex, ey = sx + 150 * math.cos(math.radians(ang)), sy + 150 * math.sin(math.radians(ang))
        L([(sx, sy), (ex, ey)], 50, INK + (255,)); L([(sx, sy), (ex, ey)], 36, BLUE + (255,))
        E((ex - 38, ey - 38, ex + 38, ey + 38), fill=WHITE + (255,), outline=INK + (255,), width=8 * S)
    arm(165, 540, armL, False); arm(635, 540, armR, True)
    # body
    E((cx - rx - 8, by - ry - 8, cx + rx + 8, by + ry + 8), fill=INK + (255,))
    E((cx - rx, by - ry, cx + rx, by + ry), fill=BLUE + (255,))
    hl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).ellipse([(cx - rx * .75) * S, (by - ry * .9) * S, (cx + rx * .2) * S, (by - ry * .1) * S], fill=(255, 255, 255, 70))
    hl = hl.filter(ImageFilter.GaussianBlur(26)); body_mask = Image.new('L', im.size, 0); ImageDraw.Draw(body_mask).ellipse([(cx - rx) * S, (by - ry) * S, (cx + rx) * S, (by + ry) * S], fill=255)
    hl.putalpha(Image.fromarray(np.minimum(np.asarray(hl.split()[3]), np.asarray(body_mask)))); im.alpha_composite(hl); d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([(cx - rx * .9) * S, (by + ry * .25) * S, (cx + rx * 1.1) * S, (by + ry * 1.1) * S], fill=(0, 40, 90, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(30)); sh.putalpha(Image.fromarray(np.minimum(np.asarray(sh.split()[3]), np.asarray(body_mask)))); im.alpha_composite(sh); d = ImageDraw.Draw(im)
    # cap
    d.pieslice([(cx - 215) * S, (by - ry - 90) * S, (cx + 215) * S, (by - ry + 190) * S], 180, 360, fill=ORANGE + (255,), outline=INK + (255,), width=8 * S)
    d.rounded_rectangle([(cx - 20) * S, (by - ry + 38) * S, (cx + 250) * S, (by - ry + 74) * S], 18 * S, fill=(214, 100, 14, 255), outline=INK + (255,), width=8 * S)
    E((cx - 38, by - ry - 5, cx + 38, by - ry + 55), fill=WHITE + (255,), outline=INK + (255,), width=6 * S)
    d.text((cx * S, (by - ry + 25) * S), 'M', font=F(48 * S), fill=INK + (255,), anchor='mm')
    # eyes
    for ex in (cx - 85, cx + 85):
        ey = by - 80
        if blink > .5: L([(ex - 50, ey), (ex + 50, ey)], 10, INK + (255,))
        else:
            E((ex - 58, ey - 74, ex + 58, ey + 74), fill=WHITE + (255,), outline=INK + (255,), width=8 * S)
            px, py = ex + look[0] * 20, ey + look[1] * 20
            E((px - 30, py - 34, px + 30, py + 34), fill=INK + (255,)); E((px - 12, py - 22, px + 4, py - 6), fill=WHITE + (255,))
        L([(ex - 55, ey - 105 - op * 12), (ex + 55, ey - 112 - op * 20)], 12, INK + (255,))
    # cheeks
    for chx in (cx - 165, cx + 165): E((chx - 38, by + 5, chx + 38, by + 50), fill=(255, 110, 150, 150))
    # mouth
    my = by + 55; mw = 105; mh = 10 + op * 100
    d.pieslice([(cx - mw) * S, (my - 20) * S, (cx + mw) * S, (my - 20 + 2 * mh + 20) * S], 0, 180, fill=(70, 18, 40, 255), outline=INK + (255,), width=8 * S)
    if mh > 40:
        d.pieslice([(cx - mw * .6) * S, (my + mh * .35) * S, (cx + mw * .6) * S, (my + mh * 1.5) * S], 0, 180, fill=(255, 110, 140, 255))
    return im.resize((cw, ch), Image.LANCZOS)

_cache = {}
def mascot_sprite(t):
    op = round(mouth_open(t) * 8) / 8
    cyc = t % 2.3; blink = 1 if cyc < .11 else 0
    prod = t > 2.7
    look = (.8, .2) if prod else (0, 0)
    wave = math.sin(t * 9)
    armL = 200 + 8 * math.sin(t * 3) if True else 0       # viewer-left arm down-out
    armL = 125 + 6 * math.sin(t * 3)
    if t < 2.6: armR = -50 + 22 * wave                      # waving hello
    elif 2.8 <= t < 5.8: armR = -35 + 10 * math.sin(t * 5)  # pointing up/right at product
    elif t >= 12.4: armR = -60 + 25 * wave
    else: armR = 25 + 6 * math.sin(t * 3)
    key = (op, blink, look, round(armL), round(armR / 2) * 2)
    if key not in _cache:
        sp = draw_munchie(op, blink, look, armL, armR, squash=op)
        _cache[key] = sticker(sp, border=14, blur=16)
    return _cache[key]

PRODUCT = dict(src='IMG_2459', mode='cut', cutkw=dict(min_frac=.3, trim_thin=.4), name='x', sub='x', theme='green')

def frame(i):
    t = i / FPS
    th = 'purple' if t < 6.0 else ('green' if t < 12.2 else 'pink')
    img = bg(W, H, th, ang=t * .5, cy=H * .5, n=20)
    gp = eb(cl((t - .1) / .6), 1.4); big = star(360 * gp + 5, (255, 255, 255), 5, .46, rot=-90 + t * 20); big.putalpha(big.split()[3].point(lambda v: int(v * .13))); paste(img, big, 540, 1180)
    header(img, W, D.TOP)
    # mascot
    ent = eb(cl(t / .6), 1.6); bob = 10 * math.sin(t * 4.2)
    msp = mascot_sprite(t); paste(img, msp, 350, 1190 + bob + (1 - ent) * 500, scale=.8 * (.4 + .6 * ent))
    # product
    if t > 2.7:
        p = eb(cl((t - 2.7) / .5), 2.2); spr = D.art(PRODUCT, 480, 560)
        paste(img, spr, 800, 1210 + 14 * math.sin(t * 3.1), rot=6 * math.sin(t * 2.2) + (1 - p) * 40, scale=max(.05, p) * (1 + .03 * math.sin(t * 6)))
        for k in range(3):
            ang = t * 1.6 + k * 2.1; paste(img, star(26 + 6 * math.sin(t * 5 + k), YEL), 800 + 330 * math.cos(ang) * .8, 1210 + 300 * math.sin(ang), rot=t * 90)
    # caption
    for (c0, c1, cap) in CAPS:
        if c0 - .05 <= t < c1:
            lt = t - c0
            for j, ln in enumerate(cap):
                p = cl((lt - j * .12 + .05) / .22)
                if p <= 0: continue
                paste(img, tspr(ln, 92, YEL if j == 1 else WHITE, 10, 940), 540, 680 + j * 108, scale=max(.05, eb(p, 2.0)))
    # footer
    paste(img, tspr('VAPE & MUNCHIES · OPEN 24/7', 30, CREAM, 5, 900), 540, 1568)
    for tc in (6.0, 12.2, 2.7):
        dt = t - tc
        if 0 <= dt < .25: flash(img, .6 * (1 - dt / .25)); 
        if 0 <= dt < .2 and tc != 2.7: img = rgb_split(img, 12 * (1 - dt / .2))
    return img.convert('RGB')

def _chunk(a):
    s, e, path = a
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(s, e): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); return path

def blip(f0, d=.15):
    t = music.t_(d); f = f0 * (1 + .18 * np.exp(-t * 25)); ph = 2 * np.pi * np.cumsum(f) / music.SR
    x = np.sin(ph) + .35 * np.sin(2 * ph) + .15 * np.sin(3 * ph); return x * music.env(len(x), .004, d * .8, 0.0, .03) * .55

def audio(path):
    n = DUR + .5; buf = np.zeros(int(music.SR * (n + 1)))
    base = music.TRACKS['trap'](n, 150); buf[:len(base)] = base * .32
    for s, d, a, f0 in SCHED: music.put(buf, blip(f0, d), s, a * .9)
    for tc in (2.7, 6.0, 12.2): music.put(buf, music.whoosh(.4), tc - .3, .8); music.put(buf, music.pop(), tc + .1, .8)
    music.put(buf, music.impact(.7), 0.0, .5)
    music.write_wav(path, music.finish(buf, DUR))

def render(out, tmp):
    from multiprocessing import get_context
    os.makedirs(tmp, exist_ok=True); n = int(DUR * FPS)
    D.art(PRODUCT, 480, 560); D.logo_sprite(250)
    step = math.ceil(n / 4); jobs = [(k * step, min(n, (k + 1) * step), f'{tmp}/c{k}.mp4') for k in range(4)]
    with get_context('fork').Pool(2) as pool: paths = pool.map(_chunk, jobs)
    open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in paths))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', f'{tmp}/video.mp4'], check=True)
    audio(f'{tmp}/audio.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{tmp}/video.mp4', '-i', f'{tmp}/audio.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], check=True)

if __name__ == '__main__':
    out = os.environ.get('VM_OUT', '/home/claude/work/out')
    if len(sys.argv) > 1 and sys.argv[1] == 'still':
        D.art(PRODUCT, 480, 560)
        for s in sys.argv[2:]: frame(int(float(s) * FPS)).save(f'{out}/munchie_still_{s}.jpg', quality=88)
    else:
        render(f'{out}/munchie.mp4', f'{out}/tmp_munchie'); print('done')
