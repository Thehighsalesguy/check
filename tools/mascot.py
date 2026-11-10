"""Munchie - original cartoon mascot presenter reel for Vape & Munchies."""
import os, re, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import design as D
from design import W, H, FPS, paste, tspr, sticker, star, pill, eb, eo, cl, bg, header, flash, rgb_split, F, BUNGEE
import music
INK=(17,15,22); BLUE=(62,193,232); BLUE_D=(36,150,200); ORANGE=(245,130,31); CREAM=(255,244,224); YEL=(255,214,40); WHITE=(255,255,255)

import json, soundfile as sf
TTS = '/home/claude/work/tts'
_L = json.load(open(f'{TTS}/lines.json'))
SCHED = []; CAPS = []; VOICE_PARTS = []; _t = 0.4
for _i, _l in enumerate(_L):
    SCHED.append((_t, _t + _l['dur'])); CAPS.append((_t, _t + _l['dur'] + .25, _l['cap'])); VOICE_PARTS.append((_t, f'{TTS}/line{_i}.wav')); _t += _l['dur'] + .32
DUR = round(_t + .5, 2)
PT = SCHED[1][0] - .1; S2 = SCHED[2][0] - .2; S3 = SCHED[4][0] - .2
_SR = 24000
_voice = np.zeros(int(DUR * _SR) + _SR)
for _t0, _p in VOICE_PARTS:
    _x, _sr = sf.read(_p, dtype='float32'); assert _sr == _SR; _i0 = int(_t0 * _SR); _voice[_i0:_i0 + len(_x)] += _x
_win = int(.04 * _SR)
_env = np.array([np.sqrt(np.mean(_voice[max(0, int(i / FPS * _SR) - _win):int(i / FPS * _SR) + _win] ** 2)) for i in range(int(DUR * FPS) + 2)])
_env = _env / (np.percentile(_env[_env > .005], 90) + 1e-6)
def mouth_open(t):
    i = int(t * FPS); return float(min(1.0, _env[i])) if 0 <= i < len(_env) else 0.0

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
    prod = t > PT
    look = (.8, .2) if prod else (0, 0)
    wave = math.sin(t * 9)
    armL = 200 + 8 * math.sin(t * 3) if True else 0       # viewer-left arm down-out
    armL = 125 + 6 * math.sin(t * 3)
    if t < SCHED[1][0] - .2: armR = -50 + 22 * wave                      # waving hello
    elif SCHED[1][0] <= t < SCHED[2][0] - .3: armR = -35 + 10 * math.sin(t * 5)  # pointing up/right at product
    elif t >= SCHED[4][0]: armR = -60 + 25 * wave
    else: armR = 25 + 6 * math.sin(t * 3)
    key = (op, blink, look, round(armL), round(armR / 2) * 2)
    if key not in _cache:
        sp = draw_munchie(op, blink, look, armL, armR, squash=op)
        _cache[key] = sticker(sp, border=14, blur=16)
    return _cache[key]

PRODUCT = dict(src='IMG_2459', mode='cut', cutkw=dict(min_frac=.3, trim_thin=.4), name='x', sub='x', theme='green')

def frame(i):
    t = i / FPS
    th = 'purple' if t < S2 else ('green' if t < S3 else 'pink')
    img = bg(W, H, th, ang=t * .5, cy=H * .5, n=20)
    gp = eb(cl((t - .1) / .6), 1.4); big = star(360 * gp + 5, (255, 255, 255), 5, .46, rot=-90 + t * 20); big.putalpha(big.split()[3].point(lambda v: int(v * .13))); paste(img, big, 540, 1180)
    header(img, W, D.TOP)
    # mascot
    ent = eb(cl(t / .6), 1.6); bob = 10 * math.sin(t * 4.2)
    msp = mascot_sprite(t); paste(img, msp, 350, 1190 + bob + (1 - ent) * 500, scale=.8 * (.4 + .6 * ent))
    # product
    if t > PT:
        p = eb(cl((t - PT) / .5), 2.2); spr = D.art(PRODUCT, 480, 560)
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
    for tc in (S2, S3, PT):
        dt = t - tc
        if 0 <= dt < .25: flash(img, .6 * (1 - dt / .25)); 
        if 0 <= dt < .2 and tc != PT: img = rgb_split(img, 12 * (1 - dt / .2))
    return img.convert('RGB')

def _chunk(a):
    s, e, path = a
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(s, e): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); return path

def audio(path):
    n = DUR + .5; buf = np.zeros(int(music.SR * (n + 1)))
    base = music.TRACKS['trap'](n, 150); buf[:len(base)] = base * .3
    for tc in (PT, S2, S3): music.put(buf, music.whoosh(.4), tc - .3, .7); music.put(buf, music.pop(), tc + .1, .6)
    music.put(buf, music.impact(.7), 0.0, .45)
    bed = music.finish(buf, DUR) * .38
    vo = np.interp(np.arange(int(DUR * music.SR)) / music.SR * _SR, np.arange(len(_voice)), _voice)
    vo = vo / (np.max(np.abs(vo)) + 1e-6) * .9
    duck = 1 - .55 * np.clip(np.convolve(np.abs(vo), np.ones(2000) / 2000, 'same') * 6, 0, 1)
    mix = bed[:len(vo)] * duck[:len(bed)] if len(bed) >= len(vo) else bed * duck[:len(bed)]
    out = np.zeros(len(vo)); out[:len(mix)] += mix; out += vo
    music.write_wav(path, np.clip(out, -1, 1))

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
