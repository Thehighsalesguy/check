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

def grid_art(item, maxw, maxh):
    """2x2 (or n-up) sticker grid from cutout pngs named IMG_xxxx_a.png..."""
    cols = item.get('cols', 2); names = item['cuts']; rows = (len(names) + cols - 1) // cols
    cw, ch = maxw // cols, maxh // rows
    canvas = Image.new('RGBA', (maxw + 80, maxh + 80), (0, 0, 0, 0))
    tilts = item.get('tilts', [-4, 3, 3, -3])
    for k, nm in enumerate(names):
        c = trim(Image.open(f'{CUT_DIR}/{nm}.png').convert('RGBA'))
        if item.get('deskew', True):
            import cv2
            a = np.asarray(c.split()[3]); cnt = max(cv2.findContours((a > 128).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
            (_, _), (rw, rh), ang = cv2.minAreaRect(cnt)
            ang = ang % 90; ang = ang - 90 if ang > 45 else ang
            c = trim(c.rotate(ang, expand=True, resample=Image.BICUBIC)); print(nm, 'deskew', round(ang, 1))
        s = min(cw * 1.04 / c.width, ch * 1.0 / c.height)
        c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
        sp = sticker(c, border=item.get('border', 12), blur=14)
        sp = sp.rotate(tilts[k % len(tilts)], expand=True, resample=Image.BICUBIC)
        cx = 40 + (k % cols) * cw + cw / 2; cy = 40 + (k // cols) * ch + ch / 2
        canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))
    return trim(canvas)

_CLIPS = {}
CARD_W, CARD_H = 540, 720
def load_clip(it):
    """decode a video item to a list of RGB PIL frames cropped to the card ratio (cached)"""
    key = it['video']
    if key in _CLIPS: return _CLIPS[key]
    cy = it.get('cropy', .5)
    vf = f"eq=contrast=1.06:saturation=1.15,scale={CARD_W}:{CARD_H}:force_original_aspect_ratio=increase,crop={CARD_W}:{CARD_H}:(iw-{CARD_W})/2:(ih-{CARD_H})*{cy},fps=30,format=rgb24"
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', key, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fs = CARD_W * CARD_H * 3
    frames = [Image.frombytes('RGB', (CARD_W, CARD_H), raw[i:i + fs]) for i in range(0, len(raw) - fs + 1, fs)]
    base = photo_card(Image.new('RGB', (CARD_W, CARD_H), (20, 20, 20)), CARD_W, CARD_H)
    _CLIPS[key] = (frames, base); return _CLIPS[key]

def clip_sprite(it, lt):
    frames, base = load_clip(it)
    i = min(len(frames) - 1, int(max(0, lt) / it.get('slow', 1.0) * 30))
    sp = base.copy(); off = (sp.width - CARD_W) // 2, (sp.height - CARD_H) // 2
    sp.paste(frames[i].convert('RGBA'), off, rr_mask(CARD_W, CARD_H, 34)); return sp

def art(item, maxw, maxh):
    """sprite for one item; cached"""
    def mk():
        if item['mode'] == 'grid': return grid_art(item, maxw, maxh)
        if item['mode'] == 'cut':
            c = trim(cutout_of(item['src'], **item.get('cutkw', {})))
            if item.get('pop'):
                a = c.split()[3]; rgb = c.convert('RGB')
                rgb = ImageEnhance.Color(ImageEnhance.Contrast(rgb).enhance(1.22)).enhance(1.35); c = rgb.convert('RGBA'); c.putalpha(a)
            s = min(maxw / c.width, maxh / c.height) * item.get('scale', 1.0)
            c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)
            return sticker(c, border=item.get('border', 14))
        if item['mode'] == 'grid':
            return grid_art(item, maxw, maxh)
        im = load_photo(item['src'], crop=item.get('crop'))
        ar = im.width / im.height
        w = maxw; h = int(w / ar)
        if h > maxh: h = maxh; w = int(h * ar)
        w = int(w * item.get('scale', 1.0)); h = int(h * item.get('scale', 1.0))
        return photo_card(im, w - 28, h - 28, item.get('fx', .5), item.get('fy', .5), item.get('zoom', 1.0))
    return cached(('art', item['src'], item['mode'], tuple(item.get('cuts', ())), maxw, maxh, item.get('crop'), item.get('zoom'), item.get('scale')), mk)

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

# ---------------- shared brand pieces ----------------
LOGO = os.path.join(HERE, 'assets', 'logo.png')

def logo_sprite(wd):
    def mk():
        im = Image.open(LOGO).convert('RGBA'); im = im.resize((wd, int(im.height * wd / im.width)), Image.LANCZOS)
        pad = 26; out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        blk = Image.new('RGBA', im.size, (0, 0, 0, 255)); blk.putalpha(im.split()[3].point(lambda v: int(v * .45)))
        sh = Image.new('RGBA', out.size, (0, 0, 0, 0)); sh.alpha_composite(blk, (pad + 3, pad + 7))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7))); out.alpha_composite(im, (pad, pad)); return out
    return cached(('logo', wd), mk)

def header(img, w, top, counter=None):
    """one fixed header band: counter pill left, logo + '19+ STORE' tag right (same x axis)"""
    if counter: paste(img, pill(counter, INK, CREAM, h=54, size=28, pad=22), 140, top + 80)
    cx = w - 165
    paste(img, logo_sprite(250), cx, top + 112)
    paste(img, pill('19+ STORE', INK, YEL, h=54, size=28, pad=26, outline=YEL), cx, top + 250)

# ---------------- carousel ----------------
def bar(img, post, w, h):
    d = ImageDraw.Draw(img); y0 = h - 92
    d.rectangle([0, y0, w, h], fill=INK + (255,)); d.rectangle([0, y0, w, y0 + 6], fill=ORANGE + (255,))
    d.text((44, y0 + 50), 'VAPE & MUNCHIES', font=F(32), fill=CREAM + (255,), anchor='lm')
    d.text((w - 44, y0 + 50), '19+ ONLY · OPEN 24/7' if post.get('adult') else 'OPEN 24/7 · COQUITLAM', font=F(28, BARLOW), fill=BLUE + (255,), anchor='rm')

HEAD_SZ, SUB_SZ = 96, 46

def carousel_slide(post, idx):
    items = post['items']; single = post.get('single'); n = len(items) + (0 if single else 1)
    label = None if single else f'{idx + 1}/{n}'
    if idx == len(items) and not single:  # closing slide, text only
        img = bg(CW, CH, 'ink', ang=.3, cy=CH * .46, n=14)
        for k, (x, y, r) in enumerate([(120, 420, 44), (960, 460, 40), (110, 1040, 38), (965, 1060, 56)]):
            paste(img, star(r, [YEL, ORANGE, BLUE][k % 3]), x, y, rot=k * 17)
        header(img, CW, 0, label)
        paste(img, tspr(post.get('cta1', 'COME GET IT'), 140, YEL, 11, 960), 540, 420)
        paste(img, tspr(post.get('cta2', 'IN STORE NOW'), 48, WHITE, 7, 960), 540, 560)
        paste(img, tspr(ADDRESS, 76, CREAM, 9, 960), 540, 730)
        paste(img, tspr('COQUITLAM BC', 52, BLUE, 7, 900), 540, 820)
        paste(img, pill('OPEN 24/7', ORANGE, INK, h=112, size=70, pad=58), 540, 980)
        paste(img, tspr('19+ ONLY · VALID ID REQUIRED', 38, YEL, 6, 960), 540, 1110)
        paste(img, tspr('@VAPEANDMUNCHIES', 42, WHITE, 6, 900), 540, 1180)
        bar(img, post, CW, CH); return img.convert('RGB')
    it = items[idx]
    img = bg(CW, CH, it.get('theme', 'orange'), ang=idx * .21, cy=CH * .55)
    header(img, CW, 0, label)
    if idx == 0:
        for k, ln in enumerate(post['title']): paste(img, tspr(ln, 100, WHITE if k == 0 else YEL, 11, 960), 540, 335 + k * 112)
        spr = art(it, 880, 600); ay = 835
    else:
        paste(img, tspr(it['name'], HEAD_SZ, WHITE, 10, 960), 540, 345)
        if it.get('sub'): paste(img, tspr(it['sub'], SUB_SZ, YEL, 6, 960), 540, 440)
        spr = art(it, it.get('aw', 900), it.get('ah', 660)); ay = it.get('ay', 850)
    if it.get('glow'):
        gl = Image.new('RGBA', (900, 900), (0, 0, 0, 0)); yy, xx = np.mgrid[0:900, 0:900].astype(np.float32)
        r = np.sqrt((xx - 450) ** 2 + (yy - 450) ** 2) / 450; al = (np.clip(1 - r, 0, 1) ** 1.8 * 150).astype(np.uint8)
        arr = np.zeros((900, 900, 4), np.uint8); arr[..., :3] = (255, 244, 224); arr[..., 3] = al; paste(img, Image.fromarray(arr), 540, ay - 10, scale=1.25)
        paste(img, soft_shadow(int(spr.width * .8), 56, 150, 18), 540, ay + spr.height // 2 - 8)
    paste(img, spr, 540, ay)
    if idx == 0:
        paste(img, pill(it['name'], INK, CREAM, h=72, size=36, pad=34), 540, 1202)
        if not single: paste(img, pill('SWIPE >>', ORANGE, INK, h=66, size=34, pad=34), 905, 1202)
    bar(img, post, CW, CH)
    return img.convert('RGB')

# ---------------- reels ----------------
TOP = 235          # header band offset in reels (clear of the Reels UI)
NAME_Y, SUB_Y, ART_Y, ART_H = 610, 705, 1140, 740

def timeline(spec):
    b = 60 / spec['bpm']; segs = []; t = 0.0
    hb = spec.get('hook_beats', 4); segs.append(dict(kind='hook', t0=t, t1=t + hb * b)); t += hb * b
    for i, it in enumerate(spec['items']):
        nb = it.get('beats', spec.get('item_beats', 4)); segs.append(dict(kind='item', i=i, t0=t, t1=t + nb * b)); t += nb * b
    ob = spec.get('outro_beats', 6); segs.append(dict(kind='outro', t0=t, t1=t + ob * b)); t += ob * b
    return segs, t

def reel_footer(img, spec):
    if spec.get('adult'): paste(img, pill('19+ ONLY · VALID ID REQUIRED', INK, YEL, h=56, size=26, pad=24, outline=YEL), 540, 1545)
    else: paste(img, tspr('VAPE & MUNCHIES · OPEN 24/7', 30, CREAM, 5, 900), 540, 1548)

def make_frame(spec, segs, i):
    t = i / FPS
    seg = next((s for s in segs if s['t0'] <= t < s['t1']), segs[-1]); lt = t - seg['t0']; sl = seg['t1'] - seg['t0']
    items = spec['items']; b = 60 / spec['bpm']; N = len(items)
    if seg['kind'] == 'hook':
        img = bg(W, H, spec.get('hook_theme', 'ink'), ang=t * .5, cy=H * .5, n=20)
        gp = eb(cl((lt - .1) / .5), 1.5); big = star(330 * gp + 5, (255, 255, 255), 5, .46, rot=-90 + t * 25); big.putalpha(big.split()[3].point(lambda v: int(v * .16))); paste(img, big, 540, 1230)
        header(img, W, TOP)
        for k, (ln, sz, col) in enumerate(spec['hook']):
            p = (lt - k * b * .8) / .28
            if p <= 0: continue
            shake = 10 * max(0, 1 - p) * math.sin(t * 90)
            paste(img, tspr(ln, sz, col, 12, 960), 540 + shake, 800 + k * 220, scale=max(.05, eb(p, 2.3)))
        if lt > b * 2.2: paste(img, star(70 * eb((lt - b * 2.2) / .3) + 5, YEL), 540, 1230, rot=t * 80)
        reel_footer(img, spec)
        if lt < .12: flash(img, .8 * (1 - lt / .12))
        return img.convert('RGB')
    if seg['kind'] == 'outro':
        img = bg(W, H, 'ink', ang=t * .4, cy=H * .46, n=14)
        for k, (x, y, r) in enumerate([(130, 1300, 50), (950, 1320, 60), (300, 1430, 30), (780, 1440, 34)]):
            paste(img, star(r * (1 + .1 * math.sin(t * 6 + k)), [YEL, ORANGE, BLUE][k % 3]), x, y, rot=t * 40 * (1 if k % 2 else -1))
        header(img, W, TOP)
        seq = [(spec.get('out1', 'IN STORE NOW'), 120, YEL, 720), (ADDRESS, 80, CREAM, 910), ('COQUITLAM BC', 54, BLUE, 1010)]
        for k, (ln, sz, col, y) in enumerate(seq):
            p = (lt - k * .22) / .3
            if p > 0: paste(img, tspr(ln, sz, col, 10, 960), 540, y, scale=max(.05, eb(p)))
        p = (lt - .75) / .3
        if p > 0: paste(img, pill('OPEN 24/7', ORANGE, INK, h=118, size=74, pad=58), 540, 1160, scale=max(.05, eb(p)) * (1 + .03 * math.sin(t * 9)))
        if spec.get('cta') and lt > 1.1: paste(img, tspr(spec['cta'], 56, WHITE, 8, 960), 540, 1340, scale=max(.05, eb((lt - 1.1) / .3)))
        reel_footer(img, spec)
        if lt < .12: flash(img, .7 * (1 - lt / .12))
        return img.convert('RGB')
    k = seg['i']; it = items[k]
    img = bg(W, H, it.get('theme', 'orange'), ang=t * .4 + k, cy=H * .52, n=18)
    header(img, W, TOP, f'{k + 1}/{N}')
    mh = it.get('maxh', ART_H); spr = clip_sprite(it, lt) if it.get('video') else art(it, 900, mh)
    float_y = 10 * math.sin(lt * 2 * math.pi / (b * 2)); tilt = 1.5 * math.sin(lt * 2 * math.pi / (b * 4)); grow = 1 + .05 * lt / sl
    base_y = (1130 if it.get('video') else ART_Y) + (mh - ART_H) * .5
    p = lt / .42
    if k % 2 == 0: ax, ay, sc = 540, base_y + float_y, max(.05, eb(p, 2.2))
    else: ax, ay, sc = 540 + (1 - eo(p)) * 1000, base_y + float_y, 1.0
    paste(img, spr, ax, ay, rot=tilt, scale=sc * grow)
    pn = (lt - .16) / .3
    if pn > 0: paste(img, tspr(it['name'], 104, WHITE, 10, 960), 540 + 8 * max(0, 1 - pn) * math.sin(t * 80), NAME_Y, scale=max(.05, eb(pn, 2.0)))
    ps = (lt - .38) / .25
    if ps > 0 and it.get('sub'): paste(img, tspr(it['sub'], 46, YEL, 6, 960), 540, SUB_Y + (1 - eo(ps)) * 50)
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
    for it in spec['items']:
        if it.get('video'): load_clip(it)
        else: art(it, 900, it.get('maxh', ART_H))
    for wd in (250,): logo_sprite(wd)
    _STATE['spec'], _STATE['segs'] = spec, segs
    step = math.ceil(n / 4); jobs = [(k * step, min(n, (k + 1) * step), f'{tmp}/c{k}.mp4') for k in range(4)]
    with get_context('fork').Pool(2) as pool: paths = pool.map(_chunk, jobs)
    open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in paths))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', f'{tmp}/video.mp4'], check=True)
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
    for s in secs: make_frame(spec, segs, int(s * FPS)).save(out.replace('.jpg', f'_{s}.jpg'), quality=88)
