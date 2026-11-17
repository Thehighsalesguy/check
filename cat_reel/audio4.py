"""Soundtrack for reel #4 'Expensive bed vs. cardboard box'.
Usage: python3 audio4.py out.wav
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = 23.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
mix = np.zeros(N)


def add(sig, t0, gain=1.0):
    i = int(t0 * SR)
    j = min(N, i + len(sig))
    if i < N:
        mix[i:j] += sig[:j - i] * gain


def tt(d):
    return np.arange(int(d * SR)) / SR


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def env(d, a=0.005, r=None):
    t = tt(d)
    e = np.minimum(1, t / a)
    if r:
        e *= np.clip((d - t) / r, 0, 1)
    return e


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------- music ----------------
def pluck(f, d=0.45, bright=0.5):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) + 0.2 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t * 7) * env(d, 0.003)


def musicbox(f, d=0.9):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.01 * t)
    return s * np.exp(-t * 4) * env(d, 0.002)


BPM = 128
beat = 60 / BPM
chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]  # C Am F G
melody = [72, 74, 76, 79, 76, 74, 72, 74,  76, 72, 69, 72, 74, 72, 69, 67,
          69, 72, 77, 76, 74, 72, 69, 72,  71, 74, 79, 77, 76, 74, 71, 74]
music = np.zeros(N)


def mput(sig, t0, g):
    i = int(t0 * SR)
    j = min(N, i + len(sig))
    if i < N:
        music[i:j] += sig[:j - i] * g


t = 0.0
step = 0
while t < DUR:
    bar = int(step // 8)
    ch = chords[bar % 4]
    night = t >= 13.0
    if not night:
        if step % 4 == 0:
            mput(pluck(mtof(ch[0] - 24), 0.5, 0.2), t, 0.55)
        if step % 2 == 1:
            for n in ch:
                mput(pluck(mtof(n), 0.25, 0.3), t, 0.12)
        if step % 8 in (0, 3, 5, 6) or step % 2 == 0:
            mput(pluck(mtof(melody[step % 32]), 0.4, 0.6), t, 0.22)
        hat = rng.standard_normal(int(0.03 * SR)) * np.exp(-tt(0.03) * 150)
        mput(hat - lowpass(hat, 4), t, 0.05)
    else:  # gentle music-box lullaby at night
        if step % 2 == 0:
            mput(musicbox(mtof(melody[(step // 2) % 32] + 12)), t, 0.16)
        if step % 8 == 0:
            for n in ch:
                mput(musicbox(mtof(n), 1.6), t, 0.07)
    t += beat / 2
    step += 1

# music gain automation: cut for trombone, dip at "3 hours later", fade end
g = np.ones(N)
tl = np.arange(N) / SR
g[(tl > 10.1) & (tl < 12.2)] = 0.0   # sad trombone moment
g *= np.where(tl > 13.0, 0.8, 1.0)
g *= np.clip((DUR - tl) / 1.2, 0, 1)
mix += lowpass(music * g, 2)


# ---------------- sfx ----------------
def meow(d=0.75, f0=420, peak=780, gain=1.0):
    t = tt(d)
    x = t / d
    f = f0 + (peak - f0) * np.sin(np.pi * np.clip(x * 1.3, 0, 1)) ** 1.5 - 60 * x
    f *= 1 + 0.015 * np.sin(2 * np.pi * 6 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    formant = 700 + 1300 * np.sin(np.pi * np.clip(x * 1.2, 0, 1))
    s = np.zeros_like(t)
    for k in range(1, 14):
        w = np.exp(-((k * f - formant) / 500) ** 2) + 0.25 / k
        s += w * np.sin(k * ph)
    e = np.minimum(1, t / 0.06) * np.clip((d - t) / 0.25, 0, 1)
    return s / 3 * e * gain


def tap():
    n = rng.standard_normal(int(0.04 * SR))
    return lowpass(n, 12) * np.exp(-tt(0.04) * 90) * 3


def pop():
    t = tt(0.09)
    f = 500 + 900 * t / 0.09
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35)


def boing(d=0.35, f1=180, f2=620):
    t = tt(d)
    f = (f1 + (f2 - f1) * t / d) * (1 + 0.08 * np.sin(2 * np.pi * 18 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)


def keyclick():
    n = rng.standard_normal(int(0.012 * SR))
    return (n - lowpass(n, 6)) * np.exp(-tt(0.012) * 300)


def trombone():
    notes = [(58, 0.38), (57, 0.38), (56, 0.38), (55, 1.1)]
    out = []
    for i, (m, d) in enumerate(notes):
        t = tt(d)
        f = mtof(m - 12) * (1 + (0.03 * np.sin(2 * np.pi * 5 * t) if i == 3 else 0))
        ph = 2 * np.pi * np.cumsum(np.full_like(t, 1.0) * f) / SR
        wah = 0.5 + 0.5 * np.sin(np.pi * np.clip(t / d, 0, 1))
        s = sum((1 / k) * (wah if k > 3 else 1) * np.sin(k * ph) for k in range(1, 10))
        e = np.minimum(1, t / 0.03) * np.clip((d - t) / 0.06, 0, 1)
        out.append(s * e)
    return np.concatenate(out) * 0.45


def whoosh(d=0.45):
    n = rng.standard_normal(int(d * SR))
    t = tt(d)
    return (n - lowpass(n, 30)) * np.sin(np.pi * t / d) ** 2 * 0.35


def crash():
    d = 0.9
    t = tt(d)
    n = rng.standard_normal(len(t))
    s = (n - lowpass(n, 3) * 0.5) * np.exp(-t * 7) * 0.8
    for _ in range(14):
        st = rng.uniform(0, 0.45)
        f = rng.uniform(2500, 6500)
        tk = tt(0.25)
        tink = np.sin(2 * np.pi * f * tk) * np.exp(-tk * 25) * rng.uniform(0.2, 0.5)
        i = int(st * SR)
        s[i:i + len(tk)] += tink[:len(s) - i]
    return s


def purr(d):
    t = tt(d)
    n = lowpass(rng.standard_normal(len(t)), 120) * 6
    am = (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t)) ** 2
    breath = 0.6 + 0.4 * np.sin(2 * np.pi * 0.45 * t)
    fade = np.minimum(1, t / 0.6) * np.clip((d - t) / 0.6, 0, 1)
    return (n * am + 0.15 * np.sin(2 * np.pi * 26 * t) * am) * breath * fade


def ding():
    t = tt(1.6)
    return (np.sin(2 * np.pi * 1046.5 * t) + 0.5 * np.sin(2 * np.pi * 2093 * t)) * np.exp(-t * 3) * 0.5




def clink(f=3000):
    t = tt(0.4)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * np.exp(-t * 14) * 0.4


def sniff():
    n = rng.standard_normal(int(0.09 * SR))
    return (n - lowpass(n, 5)) * np.sin(np.pi * tt(0.09) / 0.09) * 0.5


def thud():
    t = tt(0.3)
    return np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 6) + 40) / SR) * np.exp(-t * 12) * 1.2


def squeak():
    t = tt(0.14)
    f = 1700 + 500 * np.sin(np.pi * t / 0.14)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.14) * 0.4


def chimes():
    out = np.zeros(int(1.2 * SR))
    for k, m in enumerate((84, 88, 91, 96)):
        t = tt(0.8)
        s = np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t * 5) * 0.3
        i = int(k * 0.09 * SR)
        out[i:i + len(t)] += s
    return out


def finish(path, label):
    global mix
    m = mix / (np.max(np.abs(mix)) / 0.89)
    pcm = (np.stack([m, m], axis=1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(label)


add(chimes(), 0.3, 0.8)
for tb in (0.5, 4.8, 8.5, 10.1, 13.8, 16.0):
    add(pop(), tb, 0.35)
for ts in (3.7, 3.85, 4.15, 4.3):
    add(sniff(), ts, 0.8)
add(boing(0.35, 220, 650), 7.5, 0.4)
add(thud(), 8.0, 0.7)
add(squeak(), 8.05, 0.5)
add(trombone(), 10.15, 0.7)
for tc in (19.45, 20.05):
    add(clink(2400), tc, 0.9)
add(ding(), 21.2, 0.5)

finish(sys.argv[1], 'audio4.py ok')
