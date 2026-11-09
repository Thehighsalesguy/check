"""Design engine: one post per product group. Carousels (1080x1350) and animated reels (1080x1920).
Every photo is used exactly once per post; the last slide / outro is text-only.
Usage: python3 design.py <post_key> [still|all]   (see posts.py for specs)"""
import os, sys, math, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from PIL import ImageEnhance
import cutout as CUT

PHOTO_DIR = os.environ.get('VM_PHOTO_DIR', '/home/claude/work/new')
CUT_DIR = os.environ.get('VM_CUT_DIR', '/home/claude/work/cuts')
W, H, FPS = 1080, 1920, 30
CW, CH = 1080, 1350
ADDRESS = '934B BRUNETTE AVE'

THEMES = {
    'orange': dict(c1=(245, 130, 31), c2=(255, 160, 62)),
    'blue': dict(c1=(36, 164, 212), c2=(68, 198, 240)),
    'purple': dict(c1=(66, 40, 124), c2=(92, 60, 160)),
    'ink': dict(c1=(20, 17, 30), c2=(40, 34, 60)),
    'green': dict(c1=(30, 146, 82), c2=(56, 176, 104)),
    'pink': dict(c1=(238, 62, 136), c2=(255, 100, 168)),
    'yellow': dict(c1=(250, 196, 30), c2=(255, 220, 84)),
    'red': dict(c1=(214, 48, 48), c2=(240, 82, 70)),
}

_c = {}
def cached(k, fn):
    if k not in _c: _c[k] = fn()
    return _c[k]

def eo(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def eb(t, s=1.9): t = min(max(t, 0), 1); return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def cl(x, a=0, b=1): return max(a, min(b, x))

# ---------------- images ----------------
def load_photo(name, maxside=1600, crop=None):
    def mk():
        im = ImageOps.exif_transpose(Image.open(f'{PHOTO_DIR}/{name}.JPG')).convert('RGB')
        if crop:
            l, t, r, b = crop; im = im.crop((int(l * im.width), int(t * im.height), int(r * im.width), int(b * im.height)))
        im.thumbnail((maxside, maxside), Image.LANCZOS)
        im = ImageEnhance.Contrast(im).enhance(1.07); im = ImageEnhance.Color(im).enhance(1.14); im = im.filter(ImageFilter.UnsharpMask(1.4, 70, 3))
        return im
    return cached(('ph', name, crop, maxside), mk)

def cutout_of(name, **kw):
    def mk():
        p = f'{CUT_DIR}/{name}.png'
        if os.path.exists(p): return Image.open(p).convert('RGBA')
        os.makedirs(CUT_DIR, exist_ok=True)
        c = CUT.cut(f'{PHOTO_DIR}/{name}.JPG', **kw); c.save(p); return c
    return cached(('cut', name), mk)

def rr_mask(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m

def photo_card(im, w, h, fx=.5, fy=.5, zoom=1.0, border=14, r=34):
    iw, ih = im.size; s = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * s) + 1, int(ih * s) + 1
    big = im.resize((nw, nh), Image.LANCZOS)
    x0 = int(cl(fx * nw - w / 2, 0, nw - w)); y0 = int(cl(fy * nh - h / 2, 0, nh - h))
    inner = big.crop((x0, y0, x0 + w, y0 + h)).convert('RGBA')
    pad = 40; out = Image.new('RGBA', (w + 2 * border + 2 * pad, h + 2 * border + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((pad + 8, pad + 16, pad + w + 2 * border + 8, pad + h + 2 * border + 16), r + border, fill=(0, 0, 0, 140))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d.rounded_rectangle((pad, pad, pad + w + 2 * border, pad + h + 2 * border), r + border, fill=WHITE + (255,), outline=INK + (255,), width=5)
    out.paste(inner, (pad + border, pad + border), rr_mask(w, h, r))
    return out

def art(item, maxw, maxh):
    """sprite for one item; cached"""
    def mk():
        if item['mode'] == 'cut':
            c = trim(cutout_of(item['src'], **item.get('cutkw', {})))
            c = ImageEnhance.Contrast(c.convert('RGBA'), ) .enhance(1.04) if False else c
            s = min(maxw / c.width, maxh / c.height) * item.get('scale', 1.0)
            c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)
            return sticker(c, border=item.get('border', 14))
        im = load_photo(item['src'], crop=item.get('crop'))
        ar = im.width / im.height
        w = maxw; h = int(w / ar)
        if h > maxh: h = maxh; w = int(h * ar)
        w = int(w * item.get('scale', 1.0)); h = int(h * item.get('scale', 1.0))
        return photo_card(im, w - 28, h - 28, item.get('fx', .5), item.get('fy', .5), item.get('zoom', 1.0))
    return cached(('art', item['src'], item['mode'], maxw, maxh, item.get('crop'), item.get('zoom'), item.get('scale')), mk)

def tspr(txt, size, fill=WHITE, stroke=8, maxw=980, f=BUNGEE, rot=0, shadow=(6, 8), scol=INK):
    def mk():
        cv = Image.new('RGBA', (maxw + 300, int(size * 1.9) + 200), (0, 0, 0, 0))
        text(cv, txt, cv.width / 2, cv.height / 2, size, fill, f=f, maxw=maxw, stroke=stroke, scol=scol, shadow=shadow, rot=rot)
        return trim(cv)
    return cached(('t', txt, size, fill, stroke, maxw, f, rot, shadow, scol), mk)

def bg(w, h, theme, ang=0.0, cx=None, cy=None, n=16, dots=True):
    t = THEMES[theme]
    im = burst(w, h, cx or w / 2, cy or h * .46, t['c1'], t['c2'], n, ang)
    if dots: im.alpha_composite(halftone(w, h, (255, 255, 255, 34) if theme != 'ink' else (255, 255, 255, 14)))
    im.alpha_composite(vignette(w, h, 110))
    return im

def rgb_split(img, px):
    px = int(px)
    if px < 1: return img
    a = np.asarray(img.convert('RGB')).copy()
    a[:, :, 0] = np.roll(a[:, :, 0], px, axis=1); a[:, :, 2] = np.roll(a[:, :, 2], -px, axis=1)
    return Image.fromarray(a).convert('RGBA')

def flash(img, a, col=(255, 255, 255)):
    if a > .01: img.alpha_composite(Image.new('RGBA', img.size, col + (int(255 * min(a, 1)),)))

# ---------------- carousel ----------------
def bar(img, post, w, h):
    d = ImageDraw.Draw(img); y0 = h - 92
    d.rectangle([0, y0, w, h], fill=INK + (255,)); d.rectangle([0, y0, w, y0 + 6], fill=ORANGE + (255,))
    d.text((44, y0 + 50), 'VAPE & MUNCHIES', font=F(32), fill=CREAM + (255,), anchor='lm')
    d.text((w - 44, y0 + 50), '19+ ONLY · OPEN 24/7' if post.get('adult') else 'OPEN 24/7 · COQUITLAM', font=F(28, BARLOW), fill=BLUE + (255,), anchor='rm')

def carousel_slide(post, idx):
    items = post['items']; single = post.get('single'); n = len(items) + (0 if single else 1)
    img = None
    if idx == len(items) and not single:  # CTA, text only
        img = bg(CW, CH, 'ink', ang=.3, cy=CH * .4, n=14)
        for k, (x, y, r) in enumerate([(150, 220, 60), (930, 300, 44), (110, 1000, 40), (960, 1050, 66), (540, 120, 30)]):
            paste(img, star(r, [YEL, ORANGE, BLUE][k % 3]), x, y, rot=k * 17)
        paste(img, tspr(post.get('cta1', 'COME GET IT'), 150, YEL, 12, 980, rot=-3), 540, 330)
        paste(img, tspr(post.get('cta2', 'IN STORE NOW'), 56, WHITE, 8, 960), 540, 520)
        paste(img, tspr(ADDRESS, 82, CREAM, 9, 980), 540, 740)
        paste(img, tspr('COQUITLAM BC', 58, BLUE, 7, 900), 540, 840)
        paste(img, pill('OPEN 24/7', ORANGE, INK, h=118, size=74, pad=60), 540, 1010)
        if post.get('adult'): paste(img, tspr('19+ ONLY · VALID ID REQUIRED', 40, YEL, 6, 980), 540, 1160)
        paste(img, tspr('@VAPEANDMUNCHIES', 44, WHITE, 6, 900), 540, 1090 if not post.get('adult') else 1230)
        bar(img, post, CW, CH); return img.convert('RGB')
    it = items[idx]
    img = bg(CW, CH, it.get('theme', 'orange'), ang=idx * .21, cy=CH * .52)
    if idx == 0:
        lines = post['title']
        for k, ln in enumerate(lines): paste(img, tspr(ln, 118 if k == 0 else 104, WHITE if k == 0 else YEL, 11, 980, rot=-2 + k * 3), 540, 175 + k * 130)
        ay = 800; spr = art(it, 880, 730)
    else:
        paste(img, tspr(it['name'], 112, WHITE, 11, 980, rot=-2), 540, 180)
        if it.get('sub'): paste(img, tspr(it['sub'], 54, YEL, 7, 960, rot=1.5), 540, 300)
        ay = 760; spr = art(it, 920, 780)
    paste(img, spr, 540, ay, rot=it.get('rot', -2 if idx % 2 == 0 else 2))
    if idx == 0:
        paste(img, pill(it['name'], INK, CREAM, h=74, size=38, pad=34), 540, 1180)
        if not single: paste(img, pill('SWIPE >>', ORANGE, INK, h=66, size=34, pad=34), 905, 1180, rot=-3)
    if not single: paste(img, pill(f'{idx + 1}/{n}', INK, CREAM, h=54, size=28, pad=22), 140, 70)
    if post.get('adult'): paste(img, badge19(104), 960, 78)
    bar(img, post, CW, CH)
    return img.convert('RGB')

# ---------------- reels ----------------
def timeline(spec):
    b = 60 / spec['bpm']; segs = []; t = 0.0
    hb = spec.get('hook_beats', 4); segs.append(dict(kind='hook', t0=t, t1=t + hb * b)); t += hb * b
    for i, it in enumerate(spec['items']):
        nb = it.get('beats', spec.get('item_beats', 4)); segs.append(dict(kind='item', i=i, t0=t, t1=t + nb * b)); t += nb * b
    ob = spec.get('outro_beats', 6); segs.append(dict(kind='outro', t0=t, t1=t + ob * b)); t += ob * b
    return segs, t

def reel_footer(img, spec):
    d = ImageDraw.Draw(img)
    if spec.get('adult'):
        paste(img, pill('19+ ONLY · VALID ID REQUIRED', INK, YEL, h=56, size=26, pad=24, outline=YEL), 540, 1560)
    else:
        paste(img, tspr('VAPE & MUNCHIES · OPEN 24/7', 30, CREAM, 5, 900), 540, 1565)

def make_frame(spec, segs, i):
    t = i / FPS
    seg = next((s for s in segs if s['t0'] <= t < s['t1']), segs[-1]); lt = t - seg['t0']; sl = seg['t1'] - seg['t0']
    items = spec['items']; b = 60 / spec['bpm']
    if seg['kind'] == 'hook':
        img = bg(W, H, spec.get('hook_theme', 'ink'), ang=t * .5, cy=H * .5, n=20)
        gp = eb(cl((lt - .1) / .5), 1.5); big = star(330 * gp + 5, (255, 255, 255), 5, .46, rot=-90 + t * 25); big.putalpha(big.split()[3].point(lambda v: int(v * .16))); paste(img, big, 540, 1260)
        lines = spec['hook']
        for k, (ln, sz, col) in enumerate(lines):
            p = (lt - k * b * .8) / .28
            if p <= 0: continue
            sc = eb(p, 2.3); shake = 10 * max(0, 1 - p) * math.sin(t * 90)
            paste(img, tspr(ln, sz, col, 12, 990, rot=(-3, 2, -2)[k % 3]), 540 + shake, 640 + k * 230, scale=max(.05, sc))
        if lt > b * 2.2:
            q = eb((lt - b * 2.2) / .3); paste(img, star(120 * q + 5, YEL), 880, 360, rot=t * 80)
        if spec.get('adult'): paste(img, badge19(120), 140, 330)
        reel_footer(img, spec)
        if lt < .12: flash(img, .8 * (1 - lt / .12))
        return img.convert('RGB')
    if seg['kind'] == 'outro':
        img = bg(W, H, 'ink', ang=t * .4, cy=H * .46, n=14)
        for k, (x, y, r) in enumerate([(160, 380, 60), (930, 470, 46), (120, 1250, 44), (960, 1280, 66)]):
            paste(img, star(r * (1 + .1 * math.sin(t * 6 + k)), [YEL, ORANGE, BLUE][k % 3]), x, y, rot=t * 40 * (1 if k % 2 else -1))
        seq = [(spec.get('out1', 'IN STORE NOW'), 128, YEL, 560, -3), (ADDRESS, 86, CREAM, 800, 0), ('COQUITLAM BC', 58, BLUE, 905, 0)]
        for k, (ln, sz, col, y, r) in enumerate(seq):
            p = (lt - k * .22) / .3
            if p > 0: paste(img, tspr(ln, sz, col, 10, 980, rot=r), 540, y, scale=max(.05, eb(p)))
        p = (lt - .75) / .3
        if p > 0: paste(img, pill('OPEN 24/7', ORANGE, INK, h=124, size=78, pad=60), 540, 1090, scale=max(.05, eb(p)) * (1 + .03 * math.sin(t * 9)))
        if spec.get('cta') and lt > 1.1:
            p = (lt - 1.1) / .3; paste(img, tspr(spec['cta'], 62, WHITE, 8, 980), 540, 1290, scale=max(.05, eb(p)))
        reel_footer(img, spec)
        if lt < .12: flash(img, .7 * (1 - lt / .12))
        return img.convert('RGB')
    k = seg['i']; it = items[k]
    img = bg(W, H, it.get('theme', 'orange'), ang=t * .4 + k, cy=H * .5, n=18)
    p = lt / .42
    spr = art(it, 900, it.get('maxh', 900))
    float_y = 10 * math.sin(lt * 2 * math.pi / (b * 2)); base_y = 1000 + (it.get('maxh', 900) - 900) * .5; tilt = it.get('rot', -3 if k % 2 == 0 else 3) + 2.5 * math.sin(lt * 2 * math.pi / (b * 4))
    grow = 1 + .05 * lt / sl
    if k % 2 == 0: ax, ay, sc = 540, base_y + float_y, max(.05, eb(p, 2.2))
    else: ax, ay, sc = 540 + (1 - eo(p)) * 1000, base_y + float_y, 1.0
    paste(img, spr, ax, ay, rot=tilt, scale=sc * grow)
    pn = (lt - .16) / .3
    if pn > 0:
        shake = 8 * max(0, 1 - pn) * math.sin(t * 80)
        paste(img, tspr(it['name'], 124, WHITE, 11, 990, rot=-2 if k % 2 == 0 else 2), 540 + shake, 330, scale=max(.05, eb(pn, 2.0)))
    ps = (lt - .38) / .25
    if ps > 0 and it.get('sub'): paste(img, tspr(it['sub'], 54, YEL, 7, 980, rot=1.5), 540, 470 + (1 - eo(ps)) * 60, scale=1.0)
    paste(img, pill(f'{k + 1}/{len(items)}', INK, CREAM, h=58, size=30, pad=24), 150, 190)
    if spec.get('adult'): paste(img, badge19(110), 930, 190)
    reel_footer(img, spec)
    if lt < .13: flash(img, .75 * (1 - lt / .13)); img = rgb_split(img, 16 * (1 - lt / .13))
    return img.convert('RGB')

_STATE = {}
def _chunk(args):
    a, b2, path = args
    spec, segs = _STATE['spec'], _STATE['segs']
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(a, b2): p.stdin.write(make_frame(spec, segs, i).tobytes())
    p.stdin.close(); p.wait(); return path

def render_reel(spec, out, tmp):
    import music
    from multiprocessing import get_context
    segs, dur = timeline(spec); n = int(dur * FPS)
    os.makedirs(tmp, exist_ok=True)
    # pre-build sprites in the parent so forked workers share them
    for it in spec['items']: art(it, 900, it.get('maxh', 900))
    _STATE['spec'], _STATE['segs'] = spec, segs
    step = math.ceil(n / 4); jobs = [(k * step, min(n, (k + 1) * step), f'{tmp}/c{k}.mp4') for k in range(4)]
    with get_context('fork').Pool(2) as pool: paths = pool.map(_chunk, jobs)
    open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in paths))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', f'{tmp}/video.mp4'], check=True)
    # audio: music + sfx on every segment start
    base = music.TRACKS[spec['track']](dur + .5, spec['bpm']); buf = np.zeros(len(base) + music.SR); buf[:len(base)] = base * .8
    for s in segs:
        music.put(buf, music.whoosh(.4), max(0, s['t0'] - .3), .9); music.put(buf, music.impact(.7), s['t0'], .55)
        if s['kind'] == 'item': music.put(buf, music.pop(), s['t0'] + .16, .9)
    music.put(buf, music.riser(1.2), 0, .6)
    wav = f'{tmp}/audio.wav'; music.write_wav(wav, music.finish(buf, dur))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{tmp}/video.mp4', '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], check=True)
    return dur

def reel_still(spec, secs, out):
    segs, dur = timeline(spec)
    for s in secs:
        make_frame(spec, segs, int(s * FPS)).save(out.replace('.jpg', f'_{s}.jpg'), quality=88)
