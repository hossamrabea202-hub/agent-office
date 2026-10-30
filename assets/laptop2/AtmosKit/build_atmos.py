# Atmosphere sprites (owner list 4, 5, 19; laptop2 2026-10-30): numpy sheets for Niagara / fog cards. No bake.
#   blender -b --factory-startup -P build_atmos.py   -> tex/T_Atmos_*.png
#   T_Atmos_DustMotes   4x4 flipbook of soft specks (pollen / dust in sunbeams); alpha = mote, RGB warm white
#   T_Atmos_FogCard     1 large wispy fog sheet (valley / dawn mist), seamless in u for scrolling planes
#   T_Atmos_RealmFog    the realm's pink low fog: wispier, with faint vein streaks; seamless in u
#   T_Atmos_Sunbeam     a soft vertical beam with dust inside, for god-ray cards at the gate and in the barracks
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(D, 'tex')
def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def pnoise(u, v, s, p=None):
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64); fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    w = (lambda k: k % p) if p else (lambda k: k)
    a, b, c, d = _hash(w(iu), iv, s), _hash(w(iu + 1), iv, s), _hash(w(iu), iv + 1, s), _hash(w(iu + 1), iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def fbm(u, v, s, oct=5, p=None, gain=0.5):
    t, amp, f, tot = 0, 1.0, 1, 0
    for o in range(oct): t = t + amp * pnoise(u * f, v * f, s + o * 17, p * f if p else None); tot += amp; amp *= gain; f *= 2
    return t / tot
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def save(name, rgb, a, w, h):
    px = np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]], -1)[::-1]
    im = bpy.data.images.new(name, w, h, alpha=True); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(px.astype(np.float32).ravel()); im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

# dust motes 4x4 (each 256): 1-3 specks per frame, soft, slightly elongated, a faint halo; frames are random so Niagara can pick sub-images
S = 256; rng = np.random.default_rng(5)
i = np.arange(S); u, v = np.meshgrid((i + 0.5) / S, (i + 0.5) / S, indexing='xy'); X, Y = u * 2 - 1, v * 2 - 1
sheet = np.zeros((4 * S, 4 * S));
for f in range(16):
    fr = np.zeros((S, S))
    for k in range(rng.integers(1, 4)):
        cx, cy = rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5); a = rng.uniform(0, math.pi); sx, sy = rng.uniform(0.04, 0.09), rng.uniform(0.03, 0.06)
        dx, dy = X - cx, Y - cy; x_, y_ = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
        fr = np.maximum(fr, np.exp(-((x_ / sx) ** 2 + (y_ / sy) ** 2) * 2.5) + 0.25 * np.exp(-((x_ / (sx * 3)) ** 2 + (y_ / (sy * 3)) ** 2)))
    sheet[(f // 4) * S:(f // 4 + 1) * S, (f % 4) * S:(f % 4 + 1) * S] = np.clip(fr, 0, 1)
save('T_Atmos_DustMotes', np.stack([sheet, sheet * 0.96, sheet * 0.85], -1), sheet, 4 * S, 4 * S)

# fog card 2048x1024, seamless in u: layered wisps, denser at the bottom, torn at the top
W, H = 2048, 1024; iu = np.arange(W); iv = np.arange(H); u, v = np.meshgrid((iu + 0.5) / W, (iv + 0.5) / H, indexing='xy')
base = fbm(u * 6, v * 3, 11, 5, p=6, gain=0.55)
wisp = fbm(u * 14 + 2 * base, v * 7 + 1.5 * base, 12, 4, p=14, gain=0.5)          # domain-warped wisps
m = sstep(0.35, 0.75, 0.55 * base + 0.45 * wisp) * sstep(1.0, 0.55, v) * sstep(0.0, 0.12, v)
m = m * (0.6 + 0.4 * fbm(u * 40, v * 20, 13, 3, p=40))
save('T_Atmos_FogCard', np.stack([m * 0.0 + 0.92, m * 0.0 + 0.94, m * 0.0 + 0.98], -1), m * 0.85, W, H)

# realm fog: the same build, pinker, wispier, with faint drifting vein streaks and a glow core
base = fbm(u * 5, v * 3, 21, 5, p=5, gain=0.6); wisp = fbm(u * 18 + 3 * base, v * 9 + 2 * base, 22, 4, p=18, gain=0.5)
m = sstep(0.4, 0.8, 0.5 * base + 0.5 * wisp) * sstep(1.0, 0.5, v) * sstep(0.0, 0.1, v)
veins = sstep(0.62, 0.7, fbm(u * 30 + base * 4, v * 6, 23, 3, p=30)) * m
col = np.stack([0.85 + 0.15 * veins, 0.35 + 0.1 * (1 - veins), 0.6 + 0.2 * veins], -1)
save('T_Atmos_RealmFog', col, np.clip(m * 0.8 + veins * 0.4, 0, 1), W, H)

# sunbeam card 512x1024: a vertical soft beam, brighter at the top, with streaky dust inside
W2, H2 = 512, 1024; iu = np.arange(W2); iv = np.arange(H2); u, v = np.meshgrid((iu + 0.5) / W2, (iv + 0.5) / H2, indexing='xy')
beam = np.exp(-((u - 0.5) / 0.22) ** 2) * (1 - v) ** 0.8 * sstep(0.0, 0.08, v) * sstep(1.0, 0.9, v)
streaks = 0.7 + 0.3 * fbm(u * 30, v * 4, 31, 3); dust = sstep(0.75, 0.95, fbm(u * 60, v * 60, 32, 2)) * 0.5
m = np.clip(beam * streaks + beam * dust, 0, 1) * 0.6
save('T_Atmos_Sunbeam', np.stack([np.ones_like(m), np.full_like(m, 0.95), np.full_like(m, 0.82)], -1), m, W2, H2)
print('ATMOS OK')
