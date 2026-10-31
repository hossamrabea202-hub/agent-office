# #224 ballista shot (adjustedfilm, 2026-10-31): synthesised, licence-free.
#   "<blender python>" -I make_ballista_sfx.py -> ../sfx/SFX_Ballista_Shot.wav
# A heavy torsion release: wooden arm slam (low thump + knock), rope twang (decaying 110 Hz with partials), spear whoosh.
import os, wave
import numpy as np
SR = 48000; OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(224)
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
n = int(1.3 * SR); t = np.arange(n) / SR
slam = np.sin(2 * np.pi * (70 + 50 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.09) + lp(rng.standard_normal(n), 2500) * np.exp(-t / 0.012) * 1.2
tw = sum(a * np.sin(2 * np.pi * 110 * k * t * (1 - 0.02 * np.exp(-t / 0.05))) * np.exp(-t / d) for k, a, d in ((1, 0.6, 0.35), (2, 0.3, 0.2), (3, 0.15, 0.12), (5, 0.06, 0.07)))
wh = (rng.standard_normal(n) - lp(rng.standard_normal(n), 800)) * np.exp(-((t - 0.25) / 0.18) ** 2) * 0.35
x = slam + tw * 0.7 + wh
st = np.stack([x, np.roll(x, 25)], 1); st *= 10 ** (-3 / 20) / np.abs(st).max()
with wave.open(os.path.join(OUT, 'SFX_Ballista_Shot.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('SFX_Ballista_Shot', n / SR)
