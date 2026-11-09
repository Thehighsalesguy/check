"""Original synthesized soundtracks (no samples, no copyrighted material). python3 music.py <style> <seconds> <out.wav>
styles: trap, synthwave, lofi, house, funk, drill"""
import sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=.003, d=.2, s=0.0, r=.05):
    e = np.zeros(n); na, nd = int(a * SR), int(d * SR)
    e[:na] = np.linspace(0, 1, max(na, 1)); e[na:na + nd] = np.linspace(1, s, max(nd, 1))[:max(0, n - na)] if n > na else 0
    e[na + nd:] = s
    nr = int(r * SR)
    if nr and n > nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def sine(f, d): t = t_(d); return np.sin(2 * np.pi * f * t)
def saw(f, d): t = t_(d); return 2 * ((f * t) % 1) - 1
def sq(f, d, w=.5): t = t_(d); return np.where((f * t) % 1 < w, 1.0, -1.0)
def lp(x, k):
    k = max(1, int(k)); c = np.cumsum(np.insert(x, 0, 0)); y = (c[k:] - c[:-k]) / k
    return np.concatenate([np.full(k - 1, y[0]), y])
def hp(x, k): return x - lp(x, k)

def kick(d=.35, f0=150, f1=42):
    t = t_(d); f = f1 + (f0 - f1) * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 1.1
def snare(d=.22):
    n = rng.standard_normal(int(SR * d)) * np.exp(-t_(d) * 22); return (hp(n, 8) * .8 + sine(190, d) * np.exp(-t_(d) * 30) * .5) * .8
def clap(d=.2):
    n = rng.standard_normal(int(SR * d)); e = np.exp(-t_(d) * 25) * (1 + .8 * (np.sin(t_(d) * 2 * np.pi * 70) > .3)); return hp(n, 6) * e * .6
def hat(d=.06, op=False):
    d = .22 if op else d; n = rng.standard_normal(int(SR * d)); return hp(n, 3) * np.exp(-t_(d) * (14 if op else 60)) * .35
def b808(f, d=.6):
    t = t_(d); x = np.sin(2 * np.pi * f * t + 1.6 * np.exp(-t * 20)); x = np.tanh(x * 1.8) * np.exp(-t * 3.2); return x * .9
def bell(f, d=.9): t = t_(d); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 4) * .35
def pluck(f, d=.35): t = t_(d); x = saw(f, d) * .6 + sq(f * 1.005, d) * .3; return lp(x, 6) * np.exp(-t * 7) * .5
def ep(f, d=.6): t = t_(d); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)) * np.exp(-t * 3) * .35
def pad(f, d=1.6):
    x = sum(saw(f * m, d) for m in (.995, 1.0, 1.006)) / 3
    return lp(x, 40) * env(len(x), .25, .3, .7, .4) * .3
def sbass(f, d=.4): x = sq(f, d, .4) * .5 + sine(f / 2, d) * .5; return lp(x, 12) * env(len(x), .004, .2, .6, .05) * .6
def whoosh(d=.5, up=True):
    n = rng.standard_normal(int(SR * d)); e = np.linspace(0, 1, len(n)) ** 2 if up else np.linspace(1, 0, len(n)) ** 2
    return lp(n, 4) * e * .35
def impact(d=.9): t = t_(d); return (np.sin(2 * np.pi * 48 * t * np.exp(-t * 1.2)) * np.exp(-t * 4) * 1.0 + hp(rng.standard_normal(len(t)), 5) * np.exp(-t * 6) * .3)
def pop(d=.14): t = t_(d); f = 900 * np.exp(-t * 25) + 260; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28) * .6
def chime(f, d=.7): t = t_(d); return (np.sin(2 * np.pi * f * t) * .6 + np.sin(2 * np.pi * f * 3 * t) * .2) * np.exp(-t * 6) * .4
def crackle(n, dens=40):
    x = np.zeros(n); idx = rng.integers(0, n, int(dens * n / SR)); x[idx] = rng.uniform(-1, 1, len(idx)); return lp(x, 2) * .12
def riser(d=1.5):
    t = t_(d); f = 200 + 2600 * (t / d) ** 2; ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * .25 + lp(rng.standard_normal(len(t)), 3) * .3) * np.linspace(0, 1, len(t)) ** 1.5

def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def put(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf): return
    x = x[:len(buf) - i]; buf[i:i + len(x)] += x * g
def sidechain(x, kicks, amt=.55, rel=.18):
    g = np.ones(len(x))
    for t in kicks:
        i = int(t * SR); n = int(rel * SR); seg = 1 - amt * np.exp(-np.arange(n) / (n / 4)); seg = np.minimum(seg, 1)
        j = min(len(g), i + n)
        if j > i: g[i:j] = np.minimum(g[i:j], seg[:j - i])
    return x * g
def finish(buf, d):
    buf = np.tanh(buf * 1.15) * .92
    n = int(.4 * SR); buf[-n:] *= np.linspace(1, 0, n)
    buf = buf[:int(d * SR)]; pk = np.max(np.abs(buf)) or 1
    return (buf / pk * .9)

# ---------- styles ----------
def trap(d, bpm=140):
    b = 60 / bpm; buf = np.zeros(int(SR * (d + 1))); kicks = []; roots = [45, 45, 48, 43]
    nb = int(d / b) + 2
    for i in range(nb):
        t = i * b; bar = (i // 4) % 4; r = roots[bar]
        if i % 4 in (0, 2) or i % 8 == 7: put(buf, kick(), t); kicks.append(t)
        if i % 4 == 2: put(buf, snare(), t + b * .0); put(buf, clap(), t)
        for h in range(4): put(buf, hat(), t + h * b / 4, .8 if h % 2 == 0 else .45)
        if i % 4 == 3: put(buf, hat(op=True), t + b * .5)
        if i % 4 in (0, 3): put(buf, b808(mtof(r), b * 1.5), t, .9)
        arp = [0, 3, 7, 12, 10, 7, 3, 7]
        for k in range(2): put(buf, bell(mtof(r + 24 + arp[(i * 2 + k) % 8]), .5), t + k * b / 2, .5)
    put(buf, riser(min(2.0, d / 3)), 0, .5)
    return finish(sidechain(buf, kicks, .25), d)

def synthwave(d, bpm=100):
    b = 60 / bpm; buf = np.zeros(int(SR * (d + 1))); kicks = []; ch = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    nb = int(d / b) + 2
    for i in range(nb):
        t = i * b; bar = (i // 4) % 4; c = ch[bar]
        put(buf, kick(.3, 130, 48), t); kicks.append(t)
        if i % 4 in (1, 3): put(buf, snare(.25), t)
        for h in range(2): put(buf, hat(), t + h * b / 2)
        for k in range(4): put(buf, sbass(mtof(c[0] - 24), b / 4 * .9), t + k * b / 4, .8)
        if i % 4 == 0:
            for n in c: put(buf, pad(mtof(n), b * 4), t, .5)
        for k, n in enumerate((c[0] + 12, c[1] + 12, c[2] + 12, c[1] + 12)): put(buf, pluck(mtof(n + 12), b / 2), t + k * b / 4 * 1, .45)
    return finish(sidechain(buf, kicks, .3), d)

def lofi(d, bpm=78):
    b = 60 / bpm; buf = np.zeros(int(SR * (d + 1))); ch = [(60, 64, 67, 71), (57, 60, 64, 67), (53, 57, 60, 64), (55, 59, 62, 65)]
    nb = int(d / b) + 2
    for i in range(nb):
        t = i * b; bar = (i // 4) % 4; c = ch[bar]
        if i % 4 == 0 or i % 8 == 6: put(buf, kick(.4, 110, 45), t, .8)
        if i % 4 in (1, 3): put(buf, snare(.2), t + .015, .45)
        for h in range(2): put(buf, hat(.05), t + h * b / 2 + (.02 if h else 0), .5)
        if i % 4 == 0:
            for n in c: put(buf, ep(mtof(n), b * 3.5), t + rng.uniform(0, .02), .6)
        put(buf, sbass(mtof(c[0] - 24), b * .9), t, .6)
        if i % 2 == 1: put(buf, ep(mtof(c[(i // 2) % 4] + 24), b), t + b * .5, .4)
    buf += crackle(len(buf), 60)
    buf = lp(buf, 3)
    return finish(buf, d)

def house(d, bpm=126):
    b = 60 / bpm; buf = np.zeros(int(SR * (d + 1))); kicks = []; roots = [45, 45, 43, 48]
    nb = int(d / b) + 2
    for i in range(nb):
        t = i * b; bar = (i // 4) % 4; r = roots[bar]
        put(buf, kick(.3, 140, 50), t); kicks.append(t)
        if i % 2 == 1: put(buf, clap(), t, .8)
        put(buf, hat(op=True), t + b / 2, .55)
        for k in range(4): put(buf, hat(), t + k * b / 4, .35)
        for k in range(2): put(buf, sbass(mtof(r), b / 2 * .8), t + b / 2 + k * 0, .85 if k == 0 else 0)
        for k, o in enumerate((0, 7, 12, 7)): put(buf, pluck(mtof(r + 24 + o), b / 4), t + k * b / 4, .35)
        if i % 8 == 0:
            for n in (r + 24, r + 27, r + 31): put(buf, pad(mtof(n), b * 8), t, .35)
    return finish(sidechain(buf, kicks, .5), d)

def funk(d, bpm=108):
    b = 60 / bpm; buf = np.zeros(int(SR * (d + 1))); kicks = []; roots = [40, 40, 43, 45]
    nb = int(d / b) + 2
    for i in range(nb):
        t = i * b; bar = (i // 4) % 4; r = roots[bar]
        if i % 4 in (0, 2): put(buf, kick(.28, 120, 52), t); kicks.append(t)
        if i % 4 in (1, 3): put(buf, snare(.2), t, .8)
        for h in range(4): put(buf, hat(.05), t + h * b / 4, .5 if h % 2 == 0 else .3)
        for k, o in enumerate((0, 0, 12, 0, 10, 7, 12, 0)): put(buf, sbass(mtof(r + o), b / 4), t + k * b / 8, .7)
        if i % 2 == 0:
            for n in (r + 24, r + 28, r + 31): put(buf, pluck(mtof(n), .2), t + b * .75, .5)
    return finish(sidechain(buf, kicks, .2), d)

def drill(d, bpm=142):
    b = 60 / bpm; buf = np.zeros(int(SR * (d + 1))); kicks = []; roots = [42, 42, 45, 40]
    nb = int(d / b) + 2
    for i in range(nb):
        t = i * b; bar = (i // 4) % 4; r = roots[bar]
        if i % 4 in (0,) or i % 8 == 5: put(buf, kick(), t); kicks.append(t)
        if i % 4 == 2: put(buf, snare(.2), t)
        for h in range(3): put(buf, hat(), t + h * b / 3, .6)
        put(buf, b808(mtof(r), b * 1.2), t + (b * .5 if i % 4 == 1 else 0), .9)
        for k, o in enumerate((0, 3, 7, 3)): put(buf, chime(mtof(r + 36 + o), .4), t + k * b / 4, .45)
    return finish(sidechain(buf, kicks, .2), d)

TRACKS = dict(trap=trap, synthwave=synthwave, lofi=lofi, house=house, funk=funk, drill=drill)

def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()

if __name__ == '__main__':
    name, d, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    bpm = int(sys.argv[4]) if len(sys.argv) > 4 else None
    f = TRACKS[name]; write_wav(out, f(d, bpm) if bpm else f(d)); print('wrote', out)
