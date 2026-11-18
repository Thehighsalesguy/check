"""Rebrand slides 2 and 3 of the reference carousel to Vape & Munchies."""
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = '/home/user/check/media/gta6_bags/'
CUTS = '/home/user/check/media/gta6/cuts/'
F = lambda n, s: ImageFont.truetype(HERE + 'ttf/' + n + '.ttf', s)
BLUE, ORANGE, INK, CREAM = (62, 193, 232), (245, 130, 31), (17, 15, 22), (255, 244, 224)
LOGO = Image.open(HERE + 'logo.png').convert('RGBA')


def load(name):
    return cv2.imread(HERE + name)


def inpaint(img, mask, r=7):
    return cv2.inpaint(img, (mask > 0).astype(np.uint8), r, cv2.INPAINT_TELEA)


def box_mask(shape, box, cond=None, dil=2):
    m = np.zeros(shape[:2], np.uint8)
    x0, y0, x1, y1 = box
    m[y0:y1, x0:x1] = 1 if cond is None else cond[y0:y1, x0:x1]
    return cv2.dilate(m, np.ones((5, 5), np.uint8), iterations=dil) if dil else m


def remove_ui(img, boxes, solid=()):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    white = ((img.min(axis=2) > 200) & (hsv[..., 1] < 40)).astype(np.uint8)
    m = np.zeros(img.shape[:2], np.uint8)
    for b in boxes: m |= box_mask(img.shape, b, white, 4)
    for b in solid: m |= box_mask(img.shape, b, None, 0)
    return inpaint(img, m, 9)


def red_to_orange(img, region):
    """Recolour Slap Burger red (bricks, checkers, neon) to V&M orange inside region mask."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red = ((h <= 9) | (h >= 172)) & (s > 100) & (v > 80) & (region > 0)
    hsv[..., 0] = np.where(red, 13, h)
    hsv[..., 1] = np.where(red, np.minimum(255, s * 1.05), s)
    hsv[..., 2] = np.where(red, np.minimum(255, v * 1.12), v)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def to_pil(img): return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')
def to_cv(im): return cv2.cvtColor(np.asarray(im.convert('RGB')), cv2.COLOR_RGB2BGR)


def text_w(d, t, f, ls=0):
    return sum(d.textlength(c, font=f) for c in t) + ls * (len(t) - 1)


def draw_spaced(d, xy, t, f, fill, ls=0, stroke=0, sfill=None):
    x, y = xy
    for c in t:
        d.text((x, y), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
        x += d.textlength(c, font=f) + ls


def make_sign(w, h, shading):
    """Storefront sign panel: checker strips in brand colours, V&M wordmark, product line."""
    s = Image.new('RGBA', (w, h), CREAM + (255,))
    d = ImageDraw.Draw(s)
    cs = max(8, h // 14)
    for row, y in enumerate([int(h * .06), int(h * .06) + cs, int(h * .60), int(h * .60) + cs]):
        for i, x in enumerate(range(int(w * .02), int(w * .98), cs)):
            if (i + row) % 2 == 0: d.rectangle((x, y, x + cs - 1, y + cs - 1), fill=ORANGE)
    # wordmark
    fs = int(h * .40)
    f = F('Bungee', fs)
    parts = [('VAPE ', BLUE), ('& ', (255, 255, 255)), ('MUNCHIES', ORANGE)]
    while sum(d.textlength(t, font=f) for t, _ in parts) > w * .92:
        fs -= 2; f = F('Bungee', fs)
    tw = sum(d.textlength(t, font=f) for t, _ in parts)
    x = (w - tw) / 2; y = int(h * .21) - int(fs * .1)
    for t, c in parts:
        d.text((x, y), t, font=f, fill=c, stroke_width=max(2, fs // 14), stroke_fill=INK)
        x += d.textlength(t, font=f)
    sub = 'SNACKS • DRINKS • CANDY • GLASS • AND MORE'
    fs2 = int(h * .14); f2 = F('Barlow800', fs2)
    while text_w(d, sub, f2, 2) > w * .86: fs2 -= 1; f2 = F('Barlow800', fs2)
    draw_spaced(d, ((w - text_w(d, sub, f2, 2)) / 2, int(h * .77)), sub, f2, (206, 96, 14), 2)
    d.rectangle((0, 0, w - 1, h - 1), outline=(200, 186, 170), width=3)
    # keep the painted texture/lighting of the original panel
    sh = np.clip(shading / np.percentile(shading, 70), .78, 1.04)[..., None]
    a = np.asarray(s).astype(np.float32); a[..., :3] *= sh
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def place_sign(img, box):
    x0, y0, x1, y1 = box
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.GaussianBlur(cv2.resize(g, (8, 3), interpolation=cv2.INTER_AREA), (0, 0), 0.8) if False else cv2.resize(cv2.resize(g, (6, 2), interpolation=cv2.INTER_AREA), (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
    pil = to_pil(img); pil.alpha_composite(make_sign(x1 - x0, y1 - y0, g), (x0, y0))
    return to_cv(pil)


def neon(img, erase_box, lines, center, size):
    """Erase old neon sign in a window and draw new neon text lines [(text, colour)]."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    bright = ((hsv[..., 2] > 140) & (hsv[..., 1] > 60)).astype(np.uint8)
    img = inpaint(img, box_mask(img.shape, erase_box, bright, 3), 9)
    pil = to_pil(img)
    layer = Image.new('RGBA', pil.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cx, cy = center; y = cy - size * len(lines) * .62
    for t, c, sz in lines:
        f = F('Bungee', int(sz)); tw = d.textlength(t, font=f)
        d.text((cx - tw / 2, y), t, font=f, fill=c + (255,))
        y += sz * 1.12
    glow = layer.filter(ImageFilter.GaussianBlur(10))
    glow2 = layer.filter(ImageFilter.GaussianBlur(3))
    core = Image.new('RGBA', pil.size, (0, 0, 0, 0))
    a = np.asarray(layer).astype(np.float32)
    a[..., :3] = a[..., :3] * .7 + 255 * .3   # hot white-ish core like a real tube
    core = Image.fromarray(a.astype(np.uint8), 'RGBA')
    big = layer.filter(ImageFilter.GaussianBlur(22))
    for g in (big, big, glow, glow, glow, glow2, glow2): pil.alpha_composite(g)
    pil.alpha_composite(core)
    return to_cv(pil)


def erase_item(img, box, sat=70):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    item = ((hsv[..., 1] > sat) | (hsv[..., 2] > 215) | (hsv[..., 2] < 70)).astype(np.uint8)
    m = box_mask(img.shape, box, item, 3)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    return inpaint(img, m, 13)


def paste(pil, path, center, maxw, maxh, rot=0, shadow=True):
    p = Image.open(path).convert('RGBA')
    p.thumbnail((maxw, maxh), Image.LANCZOS)
    if rot: p = p.rotate(rot, resample=Image.BICUBIC, expand=True)
    x, y = int(center[0] - p.width / 2), int(center[1] - p.height / 2)
    if shadow:
        sh = Image.new('RGBA', (p.width + 40, p.height + 40), (0, 0, 0, 0))
        a = p.split()[3].point(lambda v: v * .55)
        sh.paste(Image.new('RGBA', p.size, (20, 8, 30, 255)), (20, 30), a)
        pil.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)), (x - 20, y - 20))
    pil.alpha_composite(p, (x, y))


def label(pil, box, text, bg, fg, font='Barlow800', size=26, ls=1, align='c'):
    d = ImageDraw.Draw(pil)
    if bg is not None: d.rectangle(box, fill=bg)
    f = F(font, size); tw = text_w(d, text, f, ls)
    x0, y0, x1, y1 = box
    x = (x0 + x1 - tw) / 2 if align == 'c' else x0
    bb = d.textbbox((0, 0), 'H', font=f)
    draw_spaced(d, (x, (y0 + y1) / 2 - (bb[1] + bb[3]) / 2), text, f, fg, ls)


def finish(img, out, box=None):
    H = img.shape[0]; w = int(H * .8)
    crop = img[:, :w] if box is None else img[box[1]:box[3], box[0]:box[2]]
    Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).resize((1080, 1350), Image.LANCZOS).save(HERE + out, quality=95)


UI_RIGHT = [(1030, 830, 1130, 915), (1040, 940, 1115, 990), (1030, 1045, 1130, 1130), (1055, 1150, 1100, 1200),
            (1030, 1255, 1130, 1350), (1050, 1385, 1105, 1430)]

# ---------------- slide 2: storefront ----------------
def slide2():
    img = load('art2_raw.png')   # Instagram buttons sit at x>1030: cropped away in finish()
    H, W = img.shape[:2]
    region = np.zeros((H, W), np.uint8); region[320:965, :] = 1
    region[590:, 210:940] = 0          # people
    region[790:860, 255:1080] = 0; region[860:1200, 255:1170] = 0     # car
    img = red_to_orange(img, region)
    img = place_sign(img, (282, 364, 911, 519))
    img = neon(img, (895, 660, 1080, 790), [('VAPE &', BLUE, 25), ('MUNCHIES', ORANGE, 27)], (928, 735), 26)
    # cup logo
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    redish = (((hsv[..., 0] <= 22) | (hsv[..., 0] >= 165)) & (hsv[..., 1] > 70)).astype(np.uint8)
    img = inpaint(img, box_mask(img.shape, (472, 1118, 543, 1180), redish, 1), 5)
    pil = to_pil(img)
    L = LOGO.copy(); L.thumbnail((66, 50), Image.LANCZOS); L = L.rotate(-4, resample=Image.BICUBIC, expand=True)
    pil.alpha_composite(L, (474, 1124))
    # door number
    d = ImageDraw.Draw(pil)
    d.rectangle((556, 636, 620, 666), fill=tuple(np.asarray(pil)[650, 545][:3]))
    label(pil, (540, 634, 636, 668), '934B', None, (235, 232, 240), 'Barlow700', 26, 4)
    finish(to_cv(pil), 'vm_gta6_slide2.jpg', (0, 1448 - 1281, 1025, 1448))


# ---------------- slide 3: game menu ----------------
def slide3():
    img = load('art3_raw.png')
    # clone clean pavement over the Instagram buttons column (feathered)
    for (y0, y1, dx) in [(822, 1192, 1015), (1192, 1448, 450)]:   # sources: clear pavement left / below wheel
        x0, x1 = 1015, 1150
        patch = img[y0:y1, x0 - dx:x1 - dx].astype(np.float32)
        m = np.ones(patch.shape[:2], np.float32); m[:, :18] = np.linspace(0, 1, 18)[None]
        if y0 == 822: m[:18, :] *= np.linspace(0, 1, 18)[:, None]
        img[y0:y1, x0:x1] = (patch * m[..., None] + img[y0:y1, x0:x1] * (1 - m[..., None])).astype(np.uint8)
    img = remove_ui(img, UI_RIGHT, solid=[(1022, 42, 1140, 125), (1048, 1318, 1132, 1400)])
    H, W = img.shape[:2]
    region = np.zeros((H, W), np.uint8); region[135:830, :] = 1
    yy, xx = np.mgrid[:H, :W]; region[np.hypot(xx - 575, yy - 735) < 440] = 0
    img = red_to_orange(img, region)
    img = place_sign(img, (270, 175, 922, 321))
    img = neon(img, (920, 480, 1085, 600), [('VAPE &', BLUE, 30), ('MUNCHIES', ORANGE, 32)], (1003, 548), 31)
    wheel = {  # (erase box, product, centre, max w/h, rotation)
        'top': ((480, 352, 690, 500), 'hbaf_green_p.png', (585, 425), (150, 150), 0),
        'ul': ((262, 430, 472, 615), 'hbaf_red_p.png', (368, 520), (150, 160), 8),
        'hi': ((782, 660, 968, 845), 'cheetos_p.png', (875, 752), (150, 170), -6),
        'll': ((300, 848, 440, 1055), 'cd_red_p.png', (372, 952), (110, 190), 4),
        'bot': ((500, 952, 665, 1148), 'dew_trolli_p.png', (580, 1050), (110, 190), -4),
        't1': ((32, 1215, 162, 1318), 'cd_blue_p.png', (97, 1266), (100, 96), 0),
        't2': ((176, 1192, 304, 1318), 'dew_dirty_p.png', (240, 1266), (100, 96), 0),
        't3': ((316, 1235, 448, 1318), 'alpine_p.png', (382, 1266), (100, 96), 0),
    }
    for k, (b, *_r) in wheel.items():
        if k in ('t1', 't2', 't3'): continue
        img = erase_item(img, b, 80 if k != 'hi' else 95)
    img = inpaint(img, box_mask(img.shape, (172, 1186, 308, 1216), None, 0), 9)   # fries box poking above tile
    pil = to_pil(img); d = ImageDraw.Draw(pil)
    for x0, x1 in [(30, 162), (175, 304), (317, 448)]:
        d.rounded_rectangle((x0, 1215, x1, 1318), 14, fill=(66, 40, 60, 255))
        d.rectangle((x0, 1300, x1, 1318), fill=(66, 40, 60, 255))
    for k, (b, path, c, (mw, mh), rot) in wheel.items():
        paste(pil, CUTS + path, c, mw, mh, rot)
    # tabs + money HUD
    label(pil, (440, 88, 586, 122), 'SNACKS', (250, 248, 250), (20, 18, 24), 'Barlow800', 25, 1)
    label(pil, (600, 88, 732, 122), 'DRINKS', (40, 32, 44), (245, 245, 245), 'Barlow800', 25, 1)
    d = ImageDraw.Draw(pil)
    d.text((972, 52), '$70', font=F('Barlow800', 40), fill=(255, 255, 255), stroke_width=3, stroke_fill=(40, 20, 50))
    finish(to_cv(pil), 'vm_gta6_slide3.jpg')


if __name__ == '__main__':
    slide2(); slide3()
