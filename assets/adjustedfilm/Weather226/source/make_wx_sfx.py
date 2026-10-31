# #226 weather sounds (adjustedfilm, 2026-10-31): synthesised, no samples, no licences.
#   "<blender python>" -I make_wx_sfx.py  ->  ../sfx/SFX_Rain_Loop.wav (8 s, seamless loop), SFX_Thunder_A.wav, SFX_Thunder_B.wav
# Rain: brown + pink noise bed (the wash) band-limited 200 Hz - 9 kHz, plus thousands of tiny decaying droplet clicks with
#       random pitch / pan; the last 0.5 s is cross-faded into the head so the loop has no seam.
# Thunder: a sharp crack (high-passed noise burst) then a long rolling rumble (low-passed noise with slow random swells),
#          A = close (crack loud, 5 s), B = distant (no crack, 7 s, darker).
import os, wave
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(226)


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def hp(x, fc): return x - lp(x, fc)


def pink(n):
    w = rng.standard_normal(n); f = np.fft.rfft(w); k = np.arange(len(f)); k[0] = 1
    return np.fft.irfft(f / np.sqrt(k), n)


def save(name, L, R, peak_db=-3.0):
    st = np.stack([L, R], 1); st *= 10 ** (peak_db / 20) / max(1e-9, np.abs(st).max())
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
    print(name, '%.2f s' % (len(st) / SR))


# ---------------------------------------------------------------- rain loop
n = int(8.5 * SR)
chans = []
for c in range(2):
    bed = hp(lp(pink(n), 9000), 200) * 0.6 + lp(np.cumsum(rng.standard_normal(n)) * 0.002, 400) * 0.3
    drops = np.zeros(n)
    for _ in range(9000):
        i = rng.integers(0, n - 4000); f = rng.uniform(1800, 7000); d = rng.uniform(0.002, 0.008); a = rng.uniform(0.05, 0.4) ** 2
        t = np.arange(int(d * 8 * SR)) / SR
        drops[i:i + len(t)] += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    chans.append(bed + drops * 0.8)
fade = int(0.5 * SR); body = int(8.0 * SR)
for k in range(2):
    x = chans[k]; head = x[:fade].copy(); tail = x[body:body + fade]
    w = np.linspace(0, 1, fade)
    x[:fade] = head * w + tail * (1 - w)
    chans[k] = x[:body]
save('SFX_Rain_Loop', chans[0], chans[1], -6.0)


# ---------------------------------------------------------------- thunder
def thunder(name, dur, crack, dark):
    n = int(dur * SR); t = np.arange(n) / SR
    swell = lp(np.abs(rng.standard_normal(n)), 1.5); swell /= swell.max()
    rumble = lp(lp(rng.standard_normal(n), dark), dark) * (0.3 + swell) * np.exp(-t / (dur * 0.35)) * np.clip(t / 0.25, 0, 1)
    out = rumble * 3.0
    if crack:
        cr = hp(rng.standard_normal(n), 1500) * np.exp(-t / 0.05) * 0.9 + lp(rng.standard_normal(n), 900) * np.exp(-t / 0.4) * 1.4
        out = out + cr
    side = lp(rng.standard_normal(n), dark) * np.exp(-t / (dur * 0.3)) * 0.8
    save(name, np.tanh(out + side), np.tanh(out - side), -2.0)


thunder('SFX_Thunder_A', 5.0, True, 160)
thunder('SFX_Thunder_B', 7.0, False, 90)
