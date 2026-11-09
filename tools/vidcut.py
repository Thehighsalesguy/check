"""Per-frame cutout of a video, stabilised: returns list of RGBA frames (fixed canvas) with the subject centred/scaled."""
import os, subprocess, numpy as np, cv2
from PIL import Image, ImageFilter
import cutout

def decode(path, w=720, h=1280, fps=30):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h},fps={fps},format=rgb24', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    fs = w * h * 3
    return [np.frombuffer(raw[i:i + fs], np.uint8).reshape(h, w, 3) for i in range(0, len(raw) - fs + 1, fs)]

def two_pass_matte(fr):
    im = Image.fromarray(fr); m0 = cutout.matte(im)
    ys, xs = np.where(m0 > .5)
    if len(xs) < 50: return m0
    pad = 40; x0, x1 = max(0, xs.min() - pad), min(fr.shape[1], xs.max() + pad); y0, y1 = max(0, ys.min() - pad), min(fr.shape[0], ys.max() + pad)
    sub = im.crop((x0, y0, x1, y1)); m1 = cutout.matte(sub)
    m = np.zeros_like(m0); m[y0:y1, x0:x1] = m1
    return m

def process(path, out_w=900, out_h=820, subj_h=760, thr=.5, ema=.55, t0=0.0, t1=99.0):
    frs = decode(path)[int(t0 * 30):int(t1 * 30)]; n = len(frs); mats = [None] * n
    prev = None
    for i in range(0, n, 2):
        m = two_pass_matte(frs[i])
        k = cutout.keep_main(m, thr, .05).astype(np.float32)
        k = cv2.GaussianBlur(k, (0, 0), 1.5)
        if prev is not None: k = ema * k + (1 - ema) * prev
        prev = k; mats[i] = k
    for i in range(1, n, 2): mats[i] = (mats[i - 1] + mats[i + 1]) / 2 if i + 1 < n and mats[i + 1] is not None else mats[i - 1]
    frs = frs[:n]
    boxes = []
    for k in mats:
        ys, xs = np.where(k > .5)
        boxes.append((xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None)
    def sm(vals, win=9):
        a = np.array(vals, np.float32); pad = win // 2; ap = np.pad(a, pad, mode='edge'); return np.convolve(ap, np.ones(win) / win, 'valid')
    last = next(b for b in boxes if b); boxes = [b or last for b in boxes]
    cx = sm([(b[0] + b[2]) / 2 for b in boxes]); cy = sm([(b[1] + b[3]) / 2 for b in boxes]); hh = sm([b[3] - b[1] for b in boxes])
    out = []
    for i, (f, k) in enumerate(zip(frs, mats)):
        a = np.clip((k - .3) / .4, 0, 1)
        rgba = np.dstack([f, (a * 255).astype(np.uint8)])
        s = subj_h / max(hh[i], 50)
        M = np.array([[s, 0, out_w / 2 - s * cx[i]], [0, s, out_h / 2 - s * cy[i]]], np.float32)
        warped = cv2.warpAffine(rgba, M, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        out.append(Image.fromarray(warped, 'RGBA'))
    return out

if __name__ == '__main__':
    import sys
    name, t0 = sys.argv[1], float(sys.argv[2])
    fr = process(f'/home/claude/work/pp2/{name}.MOV', t0=t0); print(name, len(fr), flush=True)
    np.save(f'/home/claude/work/pp2/{name}.npy', np.stack([np.asarray(f) for f in fr]))
