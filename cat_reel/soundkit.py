"""Shared synth engine for the Keef reels: music bed + cartoon sound effects."""
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(11)


def tt(d):
    return np.arange(int(d * SR)) / SR


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- instruments / sfx
def pluck(f, d=0.45, bright=0.5):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) + 0.2 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t * 7) * np.minimum(1, t / 0.003)


def musicbox(f, d=0.9):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.01 * t)) * np.exp(-t * 4) * np.minimum(1, t / 0.002)


def meow(d=0.75, f0=420, peak=780):
    t = tt(d)
    x = t / d
    f = (f0 + (peak - f0) * np.sin(np.pi * np.clip(x * 1.3, 0, 1)) ** 1.5 - 60 * x) * (1 + 0.015 * np.sin(2 * np.pi * 6 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    formant = 700 + 1300 * np.sin(np.pi * np.clip(x * 1.2, 0, 1))
    s = sum((np.exp(-((k * f - formant) / 500) ** 2) + 0.25 / k) * np.sin(k * ph) for k in range(1, 14))
    return s / 3 * np.minimum(1, t / 0.06) * np.clip((d - t) / 0.25, 0, 1)


def pop():
    t = tt(0.09)
    return np.sin(2 * np.pi * np.cumsum(500 + 900 * t / 0.09) / SR) * np.exp(-t * 35)


def boing(d=0.35, f1=180, f2=620):
    t = tt(d)
    f = (f1 + (f2 - f1) * t / d) * (1 + 0.08 * np.sin(2 * np.pi * 18 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)


def click():
    n = rng.standard_normal(int(0.012 * SR))
    return (n - lowpass(n, 6)) * np.exp(-tt(0.012) * 300)


def whoosh(d=0.45):
    n = rng.standard_normal(int(d * SR))
    return (n - lowpass(n, 30)) * np.sin(np.pi * tt(d) / d) ** 2 * 0.35


def ding():
    t = tt(1.6)
    return (np.sin(2 * np.pi * 1046.5 * t) + 0.5 * np.sin(2 * np.pi * 2093 * t)) * np.exp(-t * 3) * 0.5


def chimes():
    out = np.zeros(int(1.2 * SR))
    for k, m in enumerate((84, 88, 91, 96)):
        t = tt(0.8)
        i = int(k * 0.09 * SR)
        out[i:i + len(t)] += np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t * 5) * 0.3
    return out


def thud():
    t = tt(0.3)
    return np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 6) + 40) / SR) * np.exp(-t * 12) * 1.2


def squish():
    t = tt(0.35)
    f = 300 * np.exp(-t * 4) + 80
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8) * 0.8


def doink():
    t = tt(0.6)
    f = 140 * (1 + 0.25 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 4))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * 0.9


def sting():
    """Dramatic 'dun dun DUNNN'."""
    out = np.zeros(int(1.6 * SR))
    for m, st, d in ((50, 0.0, 0.3), (51, 0.3, 0.3), (47, 0.6, 1.0)):
        t = tt(d)
        s = sum(np.sin(2 * np.pi * mtof(m) * h * t) / h for h in range(1, 7)) * np.exp(-t * 2.5)
        i = int(st * SR)
        out[i:i + len(t)] += s[:len(out) - i]
    return out * 0.35


def crinkle(d):
    out = np.zeros(int(d * SR))
    for st in np.arange(0, d - 0.05, 0.07):
        n = rng.standard_normal(int(0.05 * SR))
        b = (n - lowpass(n, 3)) * np.exp(-tt(0.05) * 60) * rng.uniform(0.4, 1)
        i = int(st * SR)
        out[i:i + len(b)] += b[:len(out) - i]
    return out * 0.6


def cricket(d):
    out = np.zeros(int(d * SR))
    for st in np.arange(0, d - 0.3, 0.55):
        for k in range(3):
            t = tt(0.04)
            b = np.sin(2 * np.pi * 4400 * t) * np.sin(np.pi * t / 0.04) * 0.25
            i = int((st + k * 0.06) * SR)
            out[i:i + len(b)] += b[:len(out) - i]
    return out


def rimshot():
    """Ba-dum-tss."""
    out = np.zeros(int(1.2 * SR))
    for f, st in ((180, 0.0), (120, 0.14)):
        t = tt(0.2)
        b = np.sin(2 * np.pi * np.cumsum(f * (1 + np.exp(-t * 30))) / SR) * np.exp(-t * 14)
        i = int(st * SR)
        out[i:i + len(b)] += b
    n = rng.standard_normal(int(0.9 * SR))
    cym = (n - lowpass(n, 2)) * np.exp(-tt(0.9) * 5) * 0.35
    i = int(0.3 * SR)
    out[i:i + len(cym)] += cym
    return out


def scrape(d=0.6):
    n = rng.standard_normal(int(d * SR))
    t = tt(d)
    return (lowpass(n, 6) - lowpass(n, 30)) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * np.sin(np.pi * t / d) * 1.2


def drone(d, f0=55):
    t = tt(d)
    f = f0 * (1 + 0.25 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3.01 * ph)
    return s * np.minimum(1, t / 0.5) * np.clip((d - t) / 0.3, 0, 1) * 0.35


def heartbeat(d, bpm=110):
    out = np.zeros(int(d * SR))
    for st in np.arange(0, d - 0.4, 60 / bpm):
        for k, g in ((0, 1.0), (0.16, 0.7)):
            b = thud() * g * 0.6
            i = int((st + k) * SR)
            out[i:i + len(b)] += b[:len(out) - i]
    return out


# ---------------------------------------------------------------- track
class Track:
    def __init__(self, dur):
        self.dur = dur
        self.n = int(SR * dur)
        self.mix = np.zeros(self.n)

    def add(self, sig, t0, gain=1.0):
        i = int(t0 * SR)
        j = min(self.n, i + len(sig))
        if 0 <= i < self.n:
            self.mix[i:j] += sig[:j - i] * gain

    def music(self, mute=(), soft=(), lullaby=(), gain=1.0):
        """Bouncy C-Am-F-G bed. mute/soft/lullaby: lists of (a, b) time ranges."""
        bpm = 128
        beat = 60 / bpm
        chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
        mel = [72, 74, 76, 79, 76, 74, 72, 74, 76, 72, 69, 72, 74, 72, 69, 67,
               69, 72, 77, 76, 74, 72, 69, 72, 71, 74, 79, 77, 76, 74, 71, 74]
        m = np.zeros(self.n)

        def put(sig, t0, g):
            i = int(t0 * SR)
            j = min(self.n, i + len(sig))
            if i < self.n:
                m[i:j] += sig[:j - i] * g
        t, step = 0.0, 0
        while t < self.dur:
            ch = chords[(step // 8) % 4]
            if any(a <= t < b for a, b in lullaby):
                if step % 2 == 0:
                    put(musicbox(mtof(mel[(step // 2) % 32] + 12)), t, 0.16)
                if step % 8 == 0:
                    for nt in ch:
                        put(musicbox(mtof(nt), 1.6), t, 0.07)
            else:
                if step % 4 == 0:
                    put(pluck(mtof(ch[0] - 24), 0.5, 0.2), t, 0.55)
                if step % 2 == 1:
                    for nt in ch:
                        put(pluck(mtof(nt), 0.25, 0.3), t, 0.12)
                if step % 8 in (0, 3, 5, 6) or step % 2 == 0:
                    put(pluck(mtof(mel[step % 32]), 0.4, 0.6), t, 0.22)
                hat = rng.standard_normal(int(0.03 * SR)) * np.exp(-tt(0.03) * 150)
                put(hat - lowpass(hat, 4), t, 0.05)
            t += beat / 2
            step += 1
        tl = np.arange(self.n) / SR
        g = np.ones(self.n) * gain
        for a, b in mute:
            g[(tl >= a) & (tl < b)] = 0
        for a, b in soft:
            g[(tl >= a) & (tl < b)] *= 0.35
        g = lowpass(g, 2000)  # smooth gain changes
        g *= np.clip((self.dur - tl) / 1.2, 0, 1)
        self.mix += lowpass(m * g, 2)

    def save(self, path):
        m = self.mix / (np.max(np.abs(self.mix)) / 0.89)
        pcm = (np.stack([m, m], axis=1) * 32767).astype(np.int16)
        with wave.open(path, 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
