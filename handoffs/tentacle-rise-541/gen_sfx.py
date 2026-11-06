# #541 tentacle sounds, synthesised (no recordings in the project to reuse): blender -b --factory-startup -P gen_sfx.py -- <out dir>
# 44.1 kHz mono 16-bit WAV. Numbers only: nobody has listened to these yet. Layered: sub rumble, filtered noise, formant-like resonances, wet transient clicks.
import sys, os, wave, numpy as np
OUT = sys.argv[sys.argv.index('--') + 1]; os.makedirs(OUT, exist_ok=True); SR = 44100; rng = np.random.default_rng(533)
def t_(sec): return np.arange(int(sec * SR)) / SR
def lp(x, fc):     # one-pole low-pass; fc may vary per sample
    fc = np.broadcast_to(fc, x.shape); a = 1 - np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y
def hp(x, fc): return x - lp(x, fc)
def bp(x, f, q):   # resonator, f may vary per sample
    f = np.broadcast_to(f, x.shape); r = np.exp(-np.pi * f / q / SR); y = np.zeros_like(x); y1 = y2 = 0.0
    for i in range(len(x)):
        c = 2 * r[i] * np.cos(2 * np.pi * f[i] / SR); v = (1 - r[i]) * x[i] + c * y1 - r[i] * r[i] * y2; y[i] = v; y2, y1 = y1, v
    return y
def env(t, a, d, p=1.0): return np.clip(t / a, 0, 1) ** p * np.exp(-np.clip(t - a, 0, None) / d)
def noise(n): return rng.normal(0, 1, n)
def slow(n, hz): return np.interp(np.arange(n), np.linspace(0, n, max(4, int(n / SR * hz))), rng.normal(0, 1, max(4, int(n / SR * hz))))
def write(name, x, peak=0.85, fade=0.02):
    x = x - x.mean(); n = int(fade * SR); x[-n:] *= np.linspace(1, 0, n); x[:64] *= np.linspace(0, 1, 64); x = np.tanh(1.6 * x / np.max(np.abs(x))) ; x = x / np.max(np.abs(x)) * peak
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
    print('SFX', name, '%.2f s' % (len(x) / SR), 'peak %.2f rms %.3f' % (np.max(np.abs(x)), np.sqrt(np.mean(x * x))))
def voice(sec, f0a, f0b, rough=0.5, form=(280, 720, 1500), seed=0):   # a throat: a rough low pulse through moving resonances
    t = t_(sec); n = len(t); f0 = f0a + (f0b - f0a) * (t / sec) ** 1.5 + 5 * slow(n, 9) + 1.4 * np.sin(2 * np.pi * 27 * t) ; ph = np.cumsum(f0) / SR
    src = 2 * (ph % 1) - 1; src = src * (1 + rough * np.sin(2 * np.pi * ph * 0.5)) + rough * 0.9 * lp(noise(n), 2400) * np.abs(np.sin(np.pi * ph))    # subharmonic and breath
    y = 0.0
    for i_, (f, q, g) in enumerate(zip(form, (6, 9, 11), (1.0, 0.7, 0.32))): y = y + g * bp(src, f * (1 + 0.16 * slow(n, 2.5 + i_)), q)
    return y
# rumble: the warning under the ground, swelling
t = t_(3.6); n = len(t); sub = np.sin(2 * np.pi * np.cumsum(30 + 8 * slow(n, 3)) / SR) * (0.65 + 0.35 * slow(n, 7)); grit = lp(noise(n), 190) * 3.0 + bp(noise(n), 90, 2) * 2.0
stones = np.zeros(n)
for k in range(46):
    i = int(rng.random() * (n - 5000)); L = 1500 + int(rng.random() * 3000); stones[i:i + L] += rng.normal() * np.exp(-np.arange(L) / (L / 5)) * bp(noise(L), 300 + rng.random() * 900, 4)
write('SW_TentacleRumble', (sub + grit + 0.5 * stones) * np.clip(t / 2.2, 0, 1) ** 1.4 * (1 - np.clip((t - 3.2) / 0.4, 0, 1)))
# burst: the ground breaks: a thump, a crack, tumbling rock
t = t_(4.0); n = len(t); thump = np.sin(2 * np.pi * (46 * t + 18 * (1 - np.exp(-t / 0.07)))) * env(t, 0.004, 0.55); crack = hp(noise(n), 1400) * env(t, 0.001, 0.07) * 0.8; body = lp(noise(n), 500) * env(t, 0.01, 0.8) * 3.0
tumble = np.zeros(n)
for k in range(90):
    i = int((rng.random() ** 1.4) * (n - 7000)) + 900; L = 900 + int(rng.random() * 5000); tumble[i:i + L] += (rng.normal() * (1 - i / n)) * np.exp(-np.arange(L) / (L / 6)) * bp(noise(L), 160 + rng.random() * 1400, 3)
write('SW_TentacleBurst', thump * 1.6 + crack + body + 0.75 * tumble)
# roar: wide, huge, rising then failing
t = t_(4.2); n = len(t); v = voice(4.2, 44, 78, 0.75, (240, 640, 1500)) + 0.6 * voice(4.2, 66, 104, 0.6, (360, 980, 2100)); write('SW_TentacleRoar', v * (np.clip(t / 0.35, 0, 1) ** 1.5) * np.exp(-np.clip(t - 2.3, 0, None) / 0.8) + 0.16 * lp(noise(n), 3200) * env(t, 0.3, 1.0))
# groan: slow, wet, close
t = t_(3.0); n = len(t); wet = np.zeros(n)
for k in range(16):
    i = int(rng.random() * (n - 3000)); L = 600 + int(rng.random() * 1800); wet[i:i + L] += rng.normal() * np.exp(-np.arange(L) / (L / 4)) * bp(noise(L), 500 + rng.random() * 1500, 7)
write('SW_TentacleGroan', voice(3.0, 52, 37, 0.85, (220, 560, 1250)) * np.sin(np.pi * np.clip(t / 3.0, 0, 1)) ** 0.7 + 0.18 * wet)
# spit: a retch, then a wet release
t = t_(1.4); n = len(t); ret = voice(1.4, 70, 140, 0.9, (340, 900, 2000)) * np.clip(t / 0.45, 0, 1) ** 1.5 * (t < 0.56); rel = bp(noise(n), 900, 1.4) * env(np.clip(t - 0.54, 0, None), 0.008, 0.16) * 3.0 * (t >= 0.54); gl = np.zeros(n)
for k in range(10):
    i = int(0.6 * SR + rng.random() * (n - 0.6 * SR - 2500)); L = 500 + int(rng.random() * 1400); gl[i:i + L] += rng.normal() * np.exp(-np.arange(L) / (L / 4)) * np.sin(2 * np.pi * (400 + rng.random() * 900) * np.arange(L) / SR * (1 + np.arange(L) / L))
write('SW_TentacleSpit', ret + rel + 0.4 * gl)
# splat: a heavy wet hit, with drips after it
t = t_(1.2); n = len(t); hit = np.sin(2 * np.pi * (90 * t + 14 * (1 - np.exp(-t / 0.03)))) * env(t, 0.002, 0.07) * 1.1; sq = bp(noise(n), 1050, 1.1) * env(t, 0.002, 0.075) * 3.2 + hp(noise(n), 2500) * env(t, 0.001, 0.016) * 0.8; dr = np.zeros(n)
for k in range(12):
    i = int(0.05 * SR + rng.random() ** 1.3 * (n - 0.05 * SR - 2500)); L = 300 + int(rng.random() * 1000); dr[i:i + L] += (0.3 + rng.random()) * np.exp(-np.arange(L) / (L / 3)) * np.sin(2 * np.pi * (600 + rng.random() * 1500) * np.arange(L) / SR * (1 + 0.7 * np.arange(L) / L))
write('SW_BlobSplat', hit + sq + 0.28 * dr)
print('SFX DONE')
