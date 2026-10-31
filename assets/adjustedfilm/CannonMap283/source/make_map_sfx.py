# #283 scroll map sounds (adjustedfilm, 2026-10-31): synthesised, licence-free.
#   "<blender python>" -I make_map_sfx.py -> ../sfx/SFX_Scroll_Open.wav, SFX_Scroll_Close.wav, SFX_Map_Mark.wav, SFX_Map_Confirm.wav
# Open: parchment unrolling (band-passed noise swish with paper crackles, a soft wooden rod knock at the end). Close: reversed and
# shorter. Mark: a quill scratch. Confirm: a wax-seal stamp (low thud + dry knock).
import os, wave
import numpy as np
SR = 48000; OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(283)
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def save(name, x, peak=-4.0):
    st = np.stack([x, np.roll(x, 30)], 1); st *= 10 ** (peak / 20) / max(1e-9, np.abs(st).max())
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
    print(name, '%.2f s' % (len(x) / SR))
def unroll(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    sw = rng.standard_normal(n); sw = lp(sw, 3500) - lp(sw, 500)
    sw *= np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    cr = np.zeros(n)
    for _ in range(int(160 * dur)):
        i = rng.integers(0, n - 300); cr[i:i + 200] += rng.uniform(0.2, 1) * rng.standard_normal(200) * np.exp(-np.arange(200) / 30)
    knock = np.zeros(n); k = int((dur - 0.08) * SR); tt = np.arange(n - k) / SR
    knock[k:] = np.sin(2 * np.pi * 320 * tt) * np.exp(-tt / 0.03) * 0.8
    return sw * 0.8 + cr * 0.6 + knock
save('SFX_Scroll_Open', unroll(0.75))
save('SFX_Scroll_Close', unroll(0.5)[::-1])
n = int(0.25 * SR); t = np.arange(n) / SR
save('SFX_Map_Mark', (rng.standard_normal(n) - lp(rng.standard_normal(n), 2000)) * np.exp(-t / 0.06) * (1 + 0.5 * np.sin(2 * np.pi * 40 * t)))
n = int(0.5 * SR); t = np.arange(n) / SR
save('SFX_Map_Confirm', np.sin(2 * np.pi * (90 + 40 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.08) + lp(rng.standard_normal(n), 1500) * np.exp(-t / 0.015) * 1.5)
