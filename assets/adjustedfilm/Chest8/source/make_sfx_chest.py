# #8 treasure chest sounds, synthesised (licence-free) by adjustedfilm, 2026-10-31.
#   "<blender python>" -I make_sfx_chest.py <out_dir>  ->  SFX_ChestOpen.wav (latch + wood creak + lid thud, 1.1 s)
#                                                          SFX_GoldCash.wav  (ka-ching chime + coin shower, 1.7 s)
# 44.1 kHz, 16-bit, stereo. Coins = inharmonic metal partials with fast exponential decay (real coin modes are
# inharmonic, ~3-11 kHz); the chime = two struck-bell hits with bell partial ratios 1 / 2.76 / 5.40 / 8.93.
import os, sys, wave
import numpy as np

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
os.makedirs(OUT, exist_ok=True)
SR = 44100
rng = np.random.default_rng(8)


def env_exp(n, tau): return np.exp(-np.arange(n) / (tau * SR))


def write(name, L, R):
    st = np.stack([L, R], 1)
    st = st / max(1e-9, np.abs(st).max()) * 0.89            # about -1 dBFS peak
    fade = min(len(st), int(0.02 * SR)); st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    with wave.open(os.path.join(OUT, name), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype('<i2').tobytes())
    print('wrote', name, '%.2f s' % (len(st) / SR))


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); acc = 0.0
    for i, v in enumerate(x): acc = a * acc + (1 - a) * v; y[i] = acc
    return y


# ---------------------------------------------------------------- SFX_ChestOpen
n = int(1.1 * SR); L = np.zeros(n); R = np.zeros(n)
# latch click at 0.02 s: two short bright transients
for t0, amp in ((0.02, 1.0), (0.045, 0.6)):
    k = int(0.012 * SR); i = int(t0 * SR)
    burst = rng.standard_normal(k) * env_exp(k, 0.0025) * amp
    burst = burst - lowpass(burst, 1800)                     # keep the bright part
    L[i:i + k] += burst; R[i:i + k] += burst * 0.9
# wood creak 0.08-0.8 s: stick-slip pulses whose rate glides 140 -> 95 Hz, through a woody resonance
t = np.arange(n) / SR
rate = np.interp(t, [0.08, 0.8], [140, 95])
phase = np.cumsum(rate / SR) + 0.02 * np.cumsum(rng.standard_normal(n)) / SR * 40
pulses = (np.diff(np.floor(phase), prepend=0) > 0).astype(float)
amp = np.interp(t, [0.08, 0.15, 0.6, 0.8], [0, 1, 0.8, 0]) * (0.7 + 0.3 * rng.random(n))
creak = pulses * amp
res = np.zeros(n)
for f, q, g in ((420, 0.012, 1.0), (980, 0.008, 0.6), (1900, 0.004, 0.3)):   # wood body modes
    kk = int(0.05 * SR); ir = np.sin(2 * np.pi * f * np.arange(kk) / SR) * env_exp(kk, q) * g
    res += np.convolve(creak, ir)[:n]
L += res * 0.5; R += res * 0.45
# lid lands back at 0.9 s: low thud + a little rattle
i = int(0.9 * SR); k = int(0.2 * SR)
thud = np.sin(2 * np.pi * 70 * np.arange(k) / SR) * env_exp(k, 0.05) + lowpass(rng.standard_normal(k), 400) * env_exp(k, 0.03) * 0.6
L[i:i + k] += thud * 0.9; R[i:i + k] += thud * 0.9
write('SFX_ChestOpen.wav', L, R)

# ---------------------------------------------------------------- SFX_GoldCash
n = int(1.7 * SR); L = np.zeros(n); R = np.zeros(n)
# ka-ching: two struck bells (bell partials), the second higher, 90 ms later
for t0, f0, g in ((0.03, 1760.0, 1.0), (0.12, 2349.0, 0.85)):
    i = int(t0 * SR); k = n - i; tt = np.arange(k) / SR; s = np.zeros(k)
    for ratio, amp, tau in ((1.0, 1.0, 0.55), (2.76, 0.5, 0.25), (5.40, 0.28, 0.12), (8.93, 0.15, 0.06)):
        s += amp * np.sin(2 * np.pi * f0 * ratio * tt) * np.exp(-tt / tau)
    s *= g * (1 - np.exp(-tt / 0.0008))                       # tiny attack
    L[i:] += s * 0.55; R[i:] += s * 0.5
# coin shower: ~55 coin hits, dense first, thinning out; each = 4 inharmonic partials, fast decay, random pan
times = np.sort(np.concatenate([rng.uniform(0.05, 0.45, 30), rng.uniform(0.3, 1.2, 18), rng.uniform(0.9, 1.5, 7)]))
for tc in times:
    i = int(tc * SR); k = min(int(0.25 * SR), n - i)
    if k <= 0: continue
    tt = np.arange(k) / SR; base = rng.uniform(2600, 4200); s = np.zeros(k)
    for ratio, amp in ((1.0, 1.0), (1.83, 0.7), (2.96, 0.45), (4.07, 0.3)):
        s += amp * np.sin(2 * np.pi * base * ratio * rng.uniform(0.985, 1.015) * tt + rng.uniform(0, 6.28)) * np.exp(-tt / rng.uniform(0.03, 0.11))
    s *= rng.uniform(0.25, 0.6) * (1.2 - 0.6 * min(tc / 1.5, 1))
    pan = rng.uniform(0.25, 0.75)
    L[i:i + k] += s * (1 - pan); R[i:i + k] += s * pan
# a soft low "pile" bed under the shower
bed = lowpass(rng.standard_normal(n), 900) * np.interp(np.arange(n) / SR, [0.05, 0.3, 1.2, 1.6], [0, 0.35, 0.12, 0])
L += bed; R += bed
write('SFX_GoldCash.wav', L, R)
