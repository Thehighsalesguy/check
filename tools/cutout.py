"""Background removal with the U2-Net ONNX model (no rembg package needed).
Model: u2net.onnx from github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx -> /tmp/u2net.onnx (or $U2NET_PATH)"""
import os, sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter
import cv2

MODEL = os.environ.get('U2NET_PATH', '/tmp/u2net.onnx')
_sess = None

def session():
    global _sess
    if _sess is None:
        import onnxruntime as ort
        _sess = ort.InferenceSession(MODEL, providers=['CPUExecutionProvider'])
    return _sess

def matte(im, size=320):
    """returns float mask 0..1 same size as im"""
    s = session()
    a = np.asarray(im.convert('RGB').resize((size, size), Image.LANCZOS), np.float32) / 255.0
    a = (a - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    x = a.transpose(2, 0, 1)[None].astype(np.float32)
    out = s.run(None, {s.get_inputs()[0].name: x})[0][0, 0]
    out = (out - out.min()) / (out.max() - out.min() + 1e-8)
    return np.asarray(Image.fromarray((out * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC), np.float32) / 255.0

def keep_main(mask, thr=.5, min_frac=.02):
    """keep components bigger than min_frac of the largest; fill holes"""
    m = (mask > thr).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1: return m
    areas = stats[1:, cv2.CC_STAT_AREA]; big = areas.max()
    keep = np.zeros_like(m)
    for i, a in enumerate(areas):
        if a >= big * min_frac: keep[lab == i + 1] = 1
    # fill holes
    inv = (1 - keep).astype(np.uint8); h, w = inv.shape
    ff = inv.copy(); msk = np.zeros((h + 2, w + 2), np.uint8); cv2.floodFill(ff, msk, (0, 0), 2)
    holes = (ff == 1)
    keep[holes] = 1
    return keep

def cut(path, maxside=1500, thr=.5, grow=0, crop_box=None, min_frac=.02, open_px=0, trim_thin=0):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    if crop_box: im = im.crop(crop_box)
    im.thumbnail((maxside, maxside), Image.LANCZOS)
    m = matte(im)
    k = keep_main(m, thr, min_frac)
    if grow < 0: k = cv2.erode(k, np.ones((3, 3), np.uint8), iterations=-grow)
    if grow > 0: k = cv2.dilate(k, np.ones((3, 3), np.uint8), iterations=grow)
    if open_px: k = cv2.morphologyEx(k, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_px, open_px)))
    if trim_thin:
        rows = k.sum(axis=1); ok = np.where(rows >= trim_thin * rows.max())[0]
        if len(ok): k = k.copy(); k[ok.max() + 1:, :] = 0; k[:ok.min(), :] = 0
    a = Image.fromarray((k * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))
    a = a.point(lambda v: 0 if v < 70 else (255 if v > 190 else int((v - 70) * 255 / 120)))
    out = im.convert('RGBA'); out.putalpha(a)
    bb = out.getbbox()
    return out.crop(bb) if bb else out

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    cut(src).save(dst)
