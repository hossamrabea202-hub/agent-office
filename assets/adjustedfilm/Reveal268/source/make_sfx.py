# #268 reveal sounds (adjustedfilm, 2026-10-31): synthesised, no samples, no licences.
#   "<blender python>" -I make_sfx.py   ->  ../sfx/SFX_Reveal_Whoosh.wav, SFX_Reveal_Hit.wav, SFX_Reveal_Shimmer.wav
# 48 kHz, 16-bit, stereo, peaks at -3 dBFS. Each one starts on its beat (no silence at the head).
#   Whoosh  0.55 s  reveal (t = 0.12 s): band-passed noise whose centre sweeps 300 Hz -> 2.2 kHz -> 900 Hz, slow attack, air tail
#   Hit     1.10 s  peak (t = 0.47 s): 58 -> 36 Hz sub thump + soft felt transient + a low "room" bloom
#   Shimmer 1.60 s  title (t = 0.95 s): inharmonic gold bell partials, staggered like a sparkle run, wide stereo
import os, wave
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(268)


def svf_bandpass(x, fc, q):
    """state-variable band-pass with a per-sample centre frequency (array)."""
    lp = bp = 0.0
    y = np.empty_like(x)
    for i in range(len(x)):
        f = 2.0 * np.sin(np.pi * min(fc[i], SR * 0.45) / SR)
        hp = x[i] - lp - bp / q
        bp += f * hp
        lp += f * bp
        y[i] = bp
    return y


def onepole_lp(x, fc):
    a = np.exp(-2.0 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def save(name, L, R):
    st = np.stack([L, R], 1)
    st *= 10 ** (-3 / 20) / max(1e-9, np.abs(st).max())
    fade = min(len(st), int(0.02 * SR))
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype('<i2').tobytes())
    print(name, '%.2f s' % (len(st) / SR))


# ---------------------------------------------------------------- whoosh
n = int(0.55 * SR); t = np.arange(n) / SR
u = t / t[-1]
fc = 300 * (2200 / 300) ** np.clip(u / 0.55, 0, 1)
fc = np.where(u > 0.55, 2200 - (2200 - 900) * (u - 0.55) / 0.45, fc)
env = np.clip(u / 0.45, 0, 1) ** 1.6 * np.clip((1 - u) / 0.55, 0, 1) ** 1.3
chans = []
for k in range(2):
    nz = rng.standard_normal(n)
    body = svf_bandpass(nz, fc * (1.0 + 0.04 * k), 1.6)
    air = svf_bandpass(rng.standard_normal(n), fc * 2.6, 3.0) * 0.25
    chans.append((body + air) * env)
pan = np.clip(u * 1.4, 0, 1)                       # moves left -> centre as the item flies in
save('SFX_Reveal_Whoosh', chans[0] * (1.0 - 0.35 * (1 - pan)) , chans[1] * (0.65 + 0.35 * pan))

# ---------------------------------------------------------------- hit
n = int(1.10 * SR); t = np.arange(n) / SR
f = 36 + (58 - 36) * np.exp(-t / 0.09)
ph = 2 * np.pi * np.cumsum(f) / SR
sub = np.sin(ph) * np.exp(-t / 0.32) * np.clip(t / 0.004, 0, 1)
click = onepole_lp(rng.standard_normal(n), 1800) * np.exp(-t / 0.012) * 0.9
bloom = onepole_lp(rng.standard_normal(n), 220) * np.exp(-t / 0.45) * np.clip(t / 0.03, 0, 1) * 2.2
body = sub + click + bloom
side = onepole_lp(rng.standard_normal(n), 400) * np.exp(-t / 0.35) * 0.6
save('SFX_Reveal_Hit', np.tanh(1.4 * (body + side)), np.tanh(1.4 * (body - side)))

# ---------------------------------------------------------------- shimmer
n = int(1.60 * SR); t = np.arange(n) / SR
L = np.zeros(n); R = np.zeros(n)
notes = [1568.0, 2093.0, 2349.3, 2637.0, 3136.0, 3520.0, 4186.0]   # G6 C7 D7 E7 G7 A7 C8, a bright gold run
for i, fr in enumerate(notes):
    t0 = 0.035 * i + rng.uniform(0, 0.012)
    tt = np.clip(t - t0, 0, None); on = (t >= t0).astype(float)
    tone = np.zeros(n)
    for ratio, amp, dec in ((1.0, 1.0, 0.55), (2.76, 0.35, 0.22), (5.40, 0.16, 0.10), (8.93, 0.06, 0.05)):   # bell partials
        tone += amp * np.sin(2 * np.pi * fr * ratio * tt * (1 + rng.uniform(-0.002, 0.002))) * np.exp(-tt / dec)
    tone *= on * np.clip(tt / 0.002, 0, 1) * (0.9 ** i)
    p = (i / (len(notes) - 1)) * 1.6 - 0.8          # sweeps left -> right like the gold shine on the title
    L += tone * np.sqrt(0.5 * (1 - p)); R += tone * np.sqrt(0.5 * (1 + p))
sparkle = svf_bandpass(rng.standard_normal(n), np.full(n, 7500.0), 4.0) * np.exp(-t / 0.5) * np.clip(t / 0.05, 0, 1) * 0.25
save('SFX_Reveal_Shimmer', L + sparkle, R + sparkle[::-1] * 0.9)
