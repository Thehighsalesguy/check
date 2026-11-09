"""Shared drawing helpers for Vape & Munchies Instagram content."""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get('VM_FONT_DIR', os.path.join(HERE, 'fonts', 'node_modules', '@fontsource'))
BUNGEE = FONT_DIR + '/bungee/files/bungee-latin-400-normal.woff'
BARLOW = FONT_DIR + '/barlow/files/barlow-latin-800-normal.woff'

ORANGE = (245, 130, 31); BLUE = (62, 193, 232); INK = (17, 15, 22); CREAM = (255, 244, 224)
YEL = (255, 214, 40); WHITE = (255, 255, 255); PINK = (255, 88, 150); GREEN = (96, 214, 90); PURPLE = (120, 80, 220)

_fc = {}
def F(size, path=BUNGEE):
    k = (size, path)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

def tw(txt, font): return font.getlength(txt)

def fit(txt, maxw, size, path=BUNGEE, stroke=0):
    s = size
    while s > 14 and tw(txt, F(s, path)) + 2 * stroke > maxw: s -= 2
    return F(s, path)

def text(img, txt, cx, cy, size, fill=WHITE, f=BUNGEE, maxw=980, stroke=8, scol=INK, shadow=(6, 8), rot=0, shcol=(0, 0, 0, 150)):
    """centered text with outline + hard drop shadow, optional rotation"""
    fnt = fit(txt, maxw, size, f, stroke)
    pad = 60
    w = int(tw(txt, fnt)) + 2 * pad + 2 * stroke + 40
    h = int(fnt.size * 1.5) + 2 * pad
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    c = (w // 2, h // 2)
    if shadow:
        d.text((c[0] + shadow[0], c[1] + shadow[1]), txt, font=fnt, fill=shcol, anchor='mm', stroke_width=stroke, stroke_fill=shcol)
    d.text(c, txt, font=fnt, fill=fill + ((255,) if len(fill) == 3 else ()), anchor='mm', stroke_width=stroke, stroke_fill=scol + (255,))
    if rot: lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))

def vgrad(w, h, c1, c2):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(c1, np.float32) * (1 - a) + np.array(c2, np.float32) * a)
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    return Image.fromarray(arr).convert('RGBA')

def burst(w, h, cx, cy, c1, c2, n=18, ang=0.0):
    im = Image.new('RGBA', (w, h), c1 + (255,)); d = ImageDraw.Draw(im); R = math.hypot(w, h)
    for i in range(n):
        a0 = ang + i * 2 * math.pi / n; a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=c2 + (255,))
    return im

def halftone(w, h, col=(255, 255, 255, 40), step=38):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step):
            r = 3 + 7 * (y / h); d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    return ov

def vignette(w, h, strength=140):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = np.clip((r - .55) / .9, 0, 1) ** 1.6 * strength
    o = np.zeros((h, w, 4), np.uint8); o[..., 3] = a.astype(np.uint8); return Image.fromarray(o)

def paste(img, spr, cx, cy, rot=0, scale=1.0):
    if scale != 1: spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.LANCZOS)
    if rot: spr = spr.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))

def soft_shadow(w, h, op=120, blur=24):
    s = Image.new('RGBA', (w + 4 * blur, h + 4 * blur), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((2 * blur, 2 * blur, 2 * blur + w, 2 * blur + h), fill=(0, 0, 0, op))
    return s.filter(ImageFilter.GaussianBlur(blur))

def sticker(cut, border=16, col=WHITE, shadow=True, blur=18):
    """die-cut sticker: white outline around an RGBA cutout + soft drop shadow"""
    import cv2
    pad = border + (blur * 3 if shadow else 4)
    base = Image.new('RGBA', (cut.width + 2 * pad, cut.height + 2 * pad), (0, 0, 0, 0)); base.alpha_composite(cut, (pad, pad))
    a = np.asarray(base.split()[3])
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (border * 2 + 1, border * 2 + 1))
    grown = cv2.dilate((a > 90).astype(np.uint8) * 255, k)
    grown = Image.fromarray(grown).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new('RGBA', base.size, (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', base.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 150), (0, 0), grown)
        sh = sh.filter(ImageFilter.GaussianBlur(blur)); out.alpha_composite(sh, (6, blur // 2 + 8))
    ol = Image.new('RGBA', base.size, col + (255,)); ol.putalpha(grown); out.alpha_composite(ol)
    out.alpha_composite(base)
    return out

def trim(im, pad=0):
    bb = im.getbbox()
    if not bb: return im
    return im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))

def star(r, col=YEL, n=5, inner=.5, rot=-90):
    s = Image.new('RGBA', (int(r * 2 + 20), int(r * 2 + 20)), (0, 0, 0, 0)); d = ImageDraw.Draw(s); c = r + 10
    pts = []
    for i in range(n * 2):
        rr = r if i % 2 == 0 else r * inner; a = math.radians(rot + i * 180 / n); pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=col + (255,), outline=INK + (255,)); return s

def pill(txt, bg=INK, fg=CREAM, h=64, size=30, pad=28, f=BUNGEE, outline=None):
    fnt = F(size, f); w = int(tw(txt, fnt)) + 2 * pad
    s = Image.new('RGBA', (w + 16, h + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle((8, 12, w + 8, h + 12), h // 2, fill=(0, 0, 0, 110))
    d.rounded_rectangle((8, 8, w + 8, h + 8), h // 2, fill=bg + (255,), outline=(outline or INK) + (255,), width=5)
    d.text((w // 2 + 8, h // 2 + 10), txt, font=fnt, fill=fg + (255,), anchor='mm'); return s

def badge19(size=110):
    s = Image.new('RGBA', (size + 20, size + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.ellipse((12, 16, size + 12, size + 16), fill=(0, 0, 0, 120))
    d.ellipse((6, 6, size + 6, size + 6), fill=INK + (255,), outline=YEL + (255,), width=7)
    d.text(((size + 20) / 2, (size + 20) / 2 - 2), '19+', font=F(int(size * .46)), fill=YEL + (255,), anchor='mm'); return s

def arrow_pill(txt='SWIPE', size=34):
    return pill(txt + '  ➜' if False else txt + ' >>', ORANGE, INK, h=66, size=size, pad=30)

def wordmark(img, cx, cy, size=34, col=CREAM):
    d = ImageDraw.Draw(img); d.text((cx, cy), 'VAPE & MUNCHIES', font=F(size), fill=col + (255,), anchor='mm')
