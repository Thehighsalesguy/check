import numpy as np, soundfile as sf, json, sys
from kokoro_onnx import Kokoro
k = Kokoro('kokoro.onnx', 'voices.bin')
LINES = [
 ("Hey! I'm Munchie!", ["HEY!", "I'M MUNCHIE!"]),
 ("Check out Cheetos Masala Balls! A crunchy snack with that bold masala flavour.", ["CHEETOS MASALA BALLS!", "CRUNCHY. BOLD MASALA FLAVOUR."]),
 ("Perfect for a late night snack run. We're open twenty four seven!", ["LATE NIGHT SNACK RUN?", "OPEN 24/7!"]),
 ("Find us at nine thirty four B Brunette Avenue, Coquitlam.", ["934B BRUNETTE AVE,", "COQUITLAM!"]),
 ("Come snack with me!", ["COME SNACK", "WITH ME!"]),
]
voice = sys.argv[1] if len(sys.argv) > 1 else 'am_puck'
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.08
out = []
for i, (txt, cap) in enumerate(LINES):
    s, sr = k.create(txt, voice=voice, speed=speed, lang='en-us')
    # cartoon pitch-up by resampling 7%
    f = 1.07; n = int(len(s) / f); s = np.interp(np.linspace(0, len(s) - 1, n), np.arange(len(s)), s).astype(np.float32)
    # trim silence
    a = np.abs(s); idx = np.where(a > .01)[0]; s = s[idx[0]:idx[-1] + 1]
    sf.write(f'line{i}.wav', s, sr); out.append(dict(txt=txt, cap=cap, dur=len(s) / sr, sr=int(sr)))
    print(i, round(len(s) / sr, 2), flush=True)
json.dump(out, open('lines.json', 'w'))
print('total', round(sum(o['dur'] for o in out), 2))
