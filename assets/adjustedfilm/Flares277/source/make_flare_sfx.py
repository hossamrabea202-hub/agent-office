# #277 flare sounds (adjustedfilm, 2026-10-31): synthesised, no samples, no licences.
#   "<blender python>" -I make_flare_sfx.py -> ../sfx/SFX_Flare_Launch.wav, SFX_Flare_Ignite.wav, SFX_Flare_Burn.wav (6 s loop)
# Launch: a crossbow-like thunk + a rising rocket whoosh. Ignite: a sharp pop with a short fizz. Burn: magnesium hiss with
# crackle, the last 0.4 s cross-faded into the head so it loops cleanly (mono-ish, it is played attached in 3D).
import os, wave
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(277)


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def bp(x, fc):
    """per-sample centre band-pass (state variable)."""
    l = b = 0.0; y = np.empty_like(x)
    for i in range(len(x)):
        f = 2 * np.sin(np.pi * min(fc[i], SR * 0.45) / SR); h = x[i] - l - b / 1.5; b += f * h; l += f * b; y[i] = b
    return y


def save(name, L, R, peak_db=-3.0):
    st = np.stack([L, R], 1); st *= 10 ** (peak_db / 20) / max(1e-9, np.abs(st).max())
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
    print(name, '%.2f s' % (len(st) / SR))


n = int(1.6 * SR); t = np.arange(n) / SR
thunk = np.sin(2 * np.pi * (90 + 60 * np.exp(-t / 0.03)) * t) * np.exp(-t / 0.07) + lp(rng.standard_normal(n), 1200) * np.exp(-t / 0.02)
whoosh = bp(rng.standard_normal(n), 400 * (6.0 ** np.clip(t / 1.2, 0, 1))) * np.clip(t / 0.15, 0, 1) * np.exp(-np.clip(t - 0.9, 0, None) / 0.25)
save('SFX_Flare_Launch', thunk * 1.2 + whoosh, thunk * 1.2 + np.roll(whoosh, 40))

n = int(0.9 * SR); t = np.arange(n) / SR
pop = lp(rng.standard_normal(n), 3000) * np.exp(-t / 0.015) * 2 + np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.04)
fizz = (rng.standard_normal(n) - lp(rng.standard_normal(n), 2500)) * np.exp(-t / 0.3) * np.clip(t / 0.02, 0, 1) * 0.5
save('SFX_Flare_Ignite', pop + fizz, pop + fizz * 0.9)

n = int(6.4 * SR); t = np.arange(n) / SR
hiss = rng.standard_normal(n) - lp(rng.standard_normal(n), 1800)
hiss *= 0.75 + 0.25 * lp(np.abs(rng.standard_normal(n)), 3) / 0.8
crack = np.zeros(n)
for _ in range(700):
    i = rng.integers(0, n - 600); crack[i:i + 400] += rng.uniform(0.2, 1.0) * rng.standard_normal(400) * np.exp(-np.arange(400) / 60)
x = hiss * 0.6 + crack * 0.5
fade, body = int(0.4 * SR), int(6.0 * SR)
w = np.linspace(0, 1, fade); x[:fade] = x[:fade] * w + x[body:body + fade] * (1 - w); x = x[:body]
save('SFX_Flare_Burn', x, x, -6.0)
