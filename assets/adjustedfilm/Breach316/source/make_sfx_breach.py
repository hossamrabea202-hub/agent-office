# #316 wall breach sound, synthesised (licence-free) by adjustedfilm, 2026-10-31.
#   "<blender python>" -I make_sfx_breach.py <out_dir>  ->  SFX_WallBreach.wav (4.2 s, 44.1 kHz, 16-bit stereo)
# Layers: blast thump (45 Hz sine sweep + low noise, 0.4 s) -> masonry rumble (brown noise through two low resonances,
# swelling and dying over 3 s) -> 70 stone impacts (short filtered noise bursts with a rocky body mode, dense at 0.3-1.5 s,
# thinning) -> grit trickle (high, quiet, last 1.5 s).
import os, sys, wave
import numpy as np

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
os.makedirs(OUT, exist_ok=True)
SR, DUR = 44100, 4.2
n = int(SR * DUR); t = np.arange(n) / SR
rng = np.random.default_rng(316)


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = a * acc + (1 - a) * x[i]; y[i] = acc
    return y


def env(t0, att, dec):
    e = np.zeros(n); m = t >= t0
    tt = t[m] - t0; e[m] = (1 - np.exp(-tt / att)) * np.exp(-tt / dec); return e


L = np.zeros(n); R = np.zeros(n)
# blast thump
f = np.interp(t, [0, 0.4], [70, 38]); ph = np.cumsum(2 * np.pi * f / SR)
thump = np.sin(ph) * env(0.0, 0.004, 0.25) * 1.0 + lp(rng.standard_normal(n), 180) * env(0.0, 0.002, 0.18) * 2.5
L += thump; R += thump
# rumble
brown = np.cumsum(rng.standard_normal(n)); brown -= lp(brown, 15); brown /= np.abs(brown).max()
rum = lp(brown, 220) * np.interp(t, [0.05, 0.4, 1.6, 3.6], [0, 1, 0.6, 0]) * 1.6
L += rum; R += rum * 0.92
# stone impacts
times = np.sort(np.concatenate([rng.uniform(0.25, 1.5, 45), rng.uniform(1.2, 3.2, 25)]))
for tc in times:
    i = int(tc * SR); k = min(int(0.18 * SR), n - i)
    if k <= 0: continue
    tt = np.arange(k) / SR
    burst = rng.standard_normal(k) * np.exp(-tt / rng.uniform(0.01, 0.04))
    body = np.sin(2 * np.pi * rng.uniform(180, 650) * tt) * np.exp(-tt / rng.uniform(0.02, 0.06))
    s = (lp(burst, rng.uniform(1500, 4500)) * 0.7 + body * 0.6) * rng.uniform(0.25, 0.8) * (1.3 - 0.35 * min(tc, 3))
    pan = rng.uniform(0.2, 0.8)
    L[i:i + k] += s * (1 - pan) * 2; R[i:i + k] += s * pan * 2
# grit trickle
grit = rng.standard_normal(n); grit = grit - lp(grit, 3000)
gr = grit * np.interp(t, [2.2, 2.8, 4.1], [0, 0.12, 0]) * (rng.random(n) < 0.15)
L += gr; R += gr
st = np.stack([L, R], 1); st = st / np.abs(st).max() * 0.89
st[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))[:, None]
with wave.open(os.path.join(OUT, 'SFX_WallBreach.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('wrote SFX_WallBreach.wav %.1f s' % DUR)
