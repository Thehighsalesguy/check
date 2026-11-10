"""Munchie opens a bag of Cheetos Masala Balls (animated), with text-to-speech voice + lip sync."""
import os, math, json, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
import design as D
from design import W, H, FPS, paste, tspr, sticker, star, eb, eo, cl, bg, header, flash, rgb_split
import music
from mascot import draw_munchie
INK=(17,15,22); YEL=(255,214,40); CREAM=(255,244,224)
TTS = '/home/claude/work/tts'
_L = json.load(open(f'{TTS}/lines2.json'))
SCHED = []; CAPS = []; VP = []; _t = 0.4
for _i, _l in enumerate(_L):
    SCHED.append((_t, _t + _l['dur'])); CAPS.append((_t, _t + _l['dur'] + .25, _l['cap'])); VP.append((_t, f'{TTS}/m2_line{_i}.wav'))
    _t += _l['dur'] + (1.15 if _i == 1 else .32)
DUR = round(_t + .45, 2)
TEAR = SCHED[1][1] + .55                 # bag rips after "...Masala Balls!"
BAG_IN = SCHED[1][0] - .15
S_GREEN = TEAR - .02; S_PINK = SCHED[5][0] - .2
_SR = 24000; _voice = np.zeros(int(DUR * _SR) + _SR)
for _t0, _p in VP:
    _x, _sr = sf.read(_p, dtype='float32'); _i0 = int(_t0 * _SR); _voice[_i0:_i0 + len(_x)] += _x
_win = int(.04 * _SR)
_env = np.array([np.sqrt(np.mean(_voice[max(0, int(i / FPS * _SR) - _win):int(i / FPS * _SR) + _win] ** 2)) for i in range(int(DUR * FPS) + 2)])
_env = _env / (np.percentile(_env[_env > .005], 90) + 1e-6)
def mouth_open(t):
    i = int(t * FPS); o = float(min(1.0, _env[i])) if 0 <= i < len(_env) else 0.0
    if TEAR <= t < TEAR + .45: o = max(o, .95 * (1 - (t - TEAR) / .45))   # "ooh" at the rip
    return o

# ---------- bag (real photo cutout), split along a torn edge ----------
BAG_H = 560; BAG_X, BAG_Y = 800, 1255
def bag_parts():
    def mk():
        c = D.cutout_of('IMG_2459', min_frac=.3, trim_thin=.4).convert('RGBA'); c = D.trim(c)
        s = BAG_H / c.height; c = c.resize((int(c.width * s), BAG_H), Image.LANCZOS)
        w, h = c.size; y0 = int(h * .15); xs = np.arange(w)
        edge = y0 + 15 * (2 * ((xs / 38.0) % 1) - 1) + 8 * np.sin(xs / 17.0)
        yy = np.arange(h)[:, None]; top = (yy < edge[None, :]).astype(np.uint8) * 255
        a = np.asarray(c.split()[3]).astype(np.float32)
        def part(m):
            p = c.copy(); p.putalpha(Image.fromarray((a * (m / 255.0)).astype(np.uint8))); return sticker(p, border=10, blur=14)
        return sticker(c, border=10, blur=14), part(top), part(255 - top), edge
    return D.cached('bag_parts', mk)

def ball_sprite(r, rot):
    def mk():
        S2 = 3; R = r * S2; sz = int(2 * R + 40 * S2)
        im = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = sz / 2
        d.ellipse([c - R - 8 * S2, c - R - 8 * S2, c + R + 8 * S2, c + R + 8 * S2], fill=INK + (255,))
        d.ellipse([c - R, c - R, c + R, c + R], fill=(255, 150, 34, 255))
        rng = np.random.default_rng(int(r))
        for _ in range(26):
            a = rng.uniform(0, 2 * math.pi); rr = R * math.sqrt(rng.uniform(0, .85)); x, y = c + rr * math.cos(a), c + rr * math.sin(a); q = rng.uniform(.05, .13) * R
            d.ellipse([x - q, y - q, x + q, y + q], fill=(226, 96, 18, 255))
        for _ in range(10):
            a = rng.uniform(0, 2 * math.pi); rr = R * math.sqrt(rng.uniform(0, .8)); x, y = c + rr * math.cos(a), c + rr * math.sin(a); q = rng.uniform(.03, .07) * R
            d.ellipse([x - q, y - q, x + q, y + q], fill=(255, 205, 90, 255))
        d.arc([c - R * .78, c - R * .78, c + R * .78, c + R * .78], 200, 260, fill=(255, 255, 255, 200), width=int(R * .1))
        return im.resize((sz // S2, sz // S2), Image.LANCZOS)
    base = D.cached(('ball', r), mk)
    return base.rotate(rot, resample=Image.BICUBIC)

_rng = np.random.default_rng(11)
BALLS = [dict(r=r, v=(vx, vy), spin=sp) for r, vx, vy, sp in [(46, -700, -1000, 380), (38, 620, -1050, -420), (52, -250, -1100, 300), (36, 850, -950, 500), (44, 200, -1150, -260)]]
PART = [(float(_rng.uniform(-1, 1)) * math.pi, float(_rng.uniform(220, 760)), float(_rng.uniform(10, 24)), float(_rng.uniform(.5, .9))) for _ in range(34)]
OPEN_X, OPEN_Y = BAG_X, BAG_Y - BAG_H / 2 + 40
G = 2500
HERO = (BAG_X, 935)

def mascot_sprite(t):
    op = round(mouth_open(t) * 8) / 8; blink = 1 if (t % 2.3) < .11 else 0
    look = (.8, -.2) if t > TEAR else ((.8, .3) if t > BAG_IN else (0, 0))
    wave = math.sin(t * 9)
    armL = 125 + 6 * math.sin(t * 3)
    if t < SCHED[1][0] - .1: armR = -50 + 22 * wave
    elif t < TEAR + 1.4: armR = -30 + 8 * math.sin(t * 6)
    elif t >= SCHED[5][0]: armR = -60 + 25 * wave
    else: armR = 25 + 6 * math.sin(t * 3)
    key = (op, blink, look, round(armL), round(armR / 2) * 2)
    if key not in _CACHE: _CACHE[key] = sticker(draw_munchie(op, blink, look, armL, armR, squash=op), border=14, blur=16)
    return _CACHE[key]
_CACHE = {}

def frame(i):
    t = i / FPS
    th = 'purple' if t < S_GREEN else ('green' if t < S_PINK else 'pink')
    img = bg(W, H, th, ang=t * .5, cy=H * .5, n=20)
    gp = eb(cl((t - .1) / .6), 1.4); big = star(360 * gp + 5, (255, 255, 255), 5, .46, rot=-90 + t * 20); big.putalpha(big.split()[3].point(lambda v: int(v * .13))); paste(img, big, 540, 1180)
    header(img, W, D.TOP)
    ent = eb(cl(t / .6), 1.6); bob = 10 * math.sin(t * 4.2)
    paste(img, mascot_sprite(t), 350, 1190 + bob + (1 - ent) * 500, scale=.8 * (.4 + .6 * ent))
    whole, top, bot, edge = bag_parts()
    # flying balls (behind the bag front so they emerge from the opening)
    if t >= TEAR:
        dt0 = t - TEAR
        for k, b in enumerate(BALLS):
            dt = dt0 - .04 - k * .07
            if dt < 0: continue
            x = OPEN_X + b['v'][0] * dt; y = OPEN_Y + b['v'][1] * dt + .5 * G * dt * dt
            sc = 1.0 if y < 1330 else max(0.0, 1 - (y - 1330) / 160)
            if sc > 0.03 and -50 < x < W + 50: paste(img, ball_sprite(b['r'], b['spin'] * dt), x, y, scale=sc)
    # bag
    if t < BAG_IN: pass
    elif t < TEAR:
        p = eb(cl((t - BAG_IN) / .55), 2.0); shake = 0.0
        if t > TEAR - .55: a = (t - (TEAR - .55)) / .55; shake = (4 + 14 * a) * math.sin(t * 70)
        paste(img, whole, BAG_X + shake, BAG_Y + (1 - cl(p, 0, 1.2)) * 700, rot=shake * .5, scale=max(.05, min(p, 1.15)))
    else:
        dt = t - TEAR
        paste(img, bot, BAG_X, BAG_Y + 0 * dt, rot=0)
        if dt < 1.1:
            px = BAG_X + 560 * dt; py = BAG_Y - 1050 * dt + .5 * G * dt * dt
            tp = top.copy()
            if dt > .6: tp.putalpha(tp.split()[3].point(lambda v: int(v * max(0, 1 - (dt - .6) / .5))))
            paste(img, tp, px, py, rot=-380 * dt)
        # hero ball pops out and hovers
        hd = dt - .1
        if hd > 0:
            hp = eb(cl(hd / .6), 1.8); hy = OPEN_Y + (HERO[1] - OPEN_Y) * min(1, eo(hd / .6)) + 12 * math.sin(t * 3.4)
            paste(img, ball_sprite(78, 25 * math.sin(t * 1.7) + hd * 40), HERO[0], hy, scale=max(.05, hp))
            for k in range(3):
                ang = t * 1.7 + k * 2.1; paste(img, star(22 + 5 * math.sin(t * 5 + k), YEL), HERO[0] + 150 * math.cos(ang), hy + 120 * math.sin(ang), rot=t * 90)
        # powder burst
        for ang, sp, sz, life in PART:
            if dt < life:
                f = dt / life; r = sp * dt * (1 - .5 * f); x = OPEN_X + r * math.cos(ang) * .9; y = OPEN_Y - abs(r * math.sin(ang)) - 60 * f
                col = (255, 160 + int(60 * f), 40)
                lay = Image.new('RGBA', (60, 60), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse([30 - sz * (1 - f * .5), 30 - sz * (1 - f * .5), 30 + sz * (1 - f * .5), 30 + sz * (1 - f * .5)], fill=col + (int(220 * (1 - f)),)); paste(img, lay, x, y)
    # captions
    for (c0, c1, cap) in CAPS:
        if c0 - .05 <= t < c1:
            lt = t - c0
            for j, ln in enumerate(cap):
                p = cl((lt - j * .12 + .05) / .22)
                if p <= 0: continue
                paste(img, tspr(ln, 92, YEL if j == 1 else D.WHITE, 10, 940), 540, 680 + j * 108, scale=max(.05, eb(p, 2.0)))
    paste(img, tspr('VAPE & MUNCHIES · OPEN 24/7', 30, CREAM, 5, 900), 540, 1568)
    for tc in (S_GREEN, S_PINK):
        dt = t - tc
        if 0 <= dt < .25: flash(img, .7 * (1 - dt / .25))
        if 0 <= dt < .2: img = rgb_split(img, 12 * (1 - dt / .2))
    return img.convert('RGB')

def rip(d=.45):
    t = music.t_(d); n = np.random.default_rng(5).standard_normal(len(t)); n = music.hp(n, 3)
    am = (np.random.default_rng(6).uniform(.3, 1, len(t) // 220 + 1)).repeat(220)[:len(t)]
    return n * am * np.exp(-t * 5) * .8
def crunch(d=.14):
    t = music.t_(d); n = music.hp(np.random.default_rng(9).standard_normal(len(t)), 4); return n * np.exp(-t * 38) * .9

def audio(path):
    n = DUR + .5; buf = np.zeros(int(music.SR * (n + 1)))
    base = music.TRACKS['trap'](n, 150); buf[:len(base)] = base * .3
    music.put(buf, music.whoosh(.4), BAG_IN - .3, .7); music.put(buf, music.pop(), BAG_IN + .1, .7)
    music.put(buf, rip(), TEAR - .02, 1.0); music.put(buf, music.impact(.7), TEAR, .5)
    for k in range(len(BALLS)): music.put(buf, crunch(), TEAR + .06 + k * .07, .7); music.put(buf, music.pop(), TEAR + .12 + k * .07, .5)
    for tc in (S_PINK,): music.put(buf, music.whoosh(.4), tc - .3, .6)
    bed = music.finish(buf, DUR) * .36
    vo = np.interp(np.arange(int(DUR * music.SR)) / music.SR * _SR, np.arange(len(_voice)), _voice); vo = vo / (np.max(np.abs(vo)) + 1e-6) * .9
    duck = 1 - .55 * np.clip(np.convolve(np.abs(vo), np.ones(2000) / 2000, 'same') * 6, 0, 1)
    out = np.zeros(len(vo)); m = min(len(bed), len(vo)); out[:m] += bed[:m] * duck[:m]; out += vo
    music.write_wav(path, np.clip(out, -1, 1))

def _chunk(a):
    s, e, path = a
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(s, e): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); return path

def render(out, tmp):
    from multiprocessing import get_context
    os.makedirs(tmp, exist_ok=True); n = int(DUR * FPS); D.logo_sprite(250); bag_parts()
    for b in BALLS: ball_sprite(b['r'], 0)
    ball_sprite(78, 0)
    step = math.ceil(n / 4); jobs = [(k * step, min(n, (k + 1) * step), f'{tmp}/c{k}.mp4') for k in range(4)]
    with get_context('fork').Pool(2) as pool: paths = pool.map(_chunk, jobs)
    open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in paths))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', f'{tmp}/video.mp4'], check=True)
    audio(f'{tmp}/audio.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{tmp}/video.mp4', '-i', f'{tmp}/audio.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], check=True)

if __name__ == '__main__':
    out = os.environ.get('VM_OUT', '/home/claude/work/out')
    if len(sys.argv) > 1 and sys.argv[1] == 'still':
        for s in sys.argv[2:]: frame(int(float(s) * FPS)).save(f'{out}/m2_still_{s}.jpg', quality=88)
    else:
        render(f'{out}/munchie2.mp4', f'{out}/tmp_munchie2'); print('done', DUR)
