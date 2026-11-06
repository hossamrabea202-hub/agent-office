# #90 Berserk VFX textures (laptop2, 2026-10-29). Run with Blender's python (numpy only):
#   python -I make_textures.py <out_dir>
# T_BerserkNoise  512  tileable 2-octave-set fbm: R fine, G medium, B large (pan them at different speeds)
# T_BerserkWisp   256  a flame tongue sprite (R shape, G erosion noise inside it)
# T_BerserkEmber  64   a soft hot dot with a hard core
# T_BerserkRing   1024 the ground ring: a cracked burning circle (R ring+cracks, G soft glow, B radial 0..1)
import sys, os, zlib, struct
import numpy as np
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)

def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def pnoise(u, v, s, p):
    """value noise, periodic with period p on both axes (seamless tiles)."""
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv; fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b = _hash(iu % p, iv % p, s), _hash((iu + 1) % p, iv % p, s)
    c, d = _hash(iu % p, (iv + 1) % p, s), _hash((iu + 1) % p, (iv + 1) % p, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def pfbm(u, v, s, p, oct=5):
    t, amp, tot = 0, 1.0, 0
    for o in range(oct):
        f = 2 ** o; t = t + amp * pnoise(u * f, v * f, s + o * 13, p * f); tot += amp; amp *= 0.5
    return t / tot
def norm(a): return (a - a.min()) / (a.max() - a.min() + 1e-9)
def png(name, rgb):
    a = (np.clip(rgb, 0, 1) * 255).astype(np.uint8); H, W = a.shape[:2]
    if a.ndim == 2: a = np.stack([a] * 3, -1)
    raw = b''.join(b'\x00' + a[::-1][r].tobytes() for r in range(H))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(os.path.join(OUT, name + '.png'), 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))

# noise: three bands for layered panning (flames that boil, not slide)
N = 512; y, x = np.mgrid[0:N, 0:N] / N
r = norm(pfbm(x * 16, y * 16, 1, 16, 5))
g = norm(pfbm(x * 6, y * 6, 2, 6, 5))
b = norm(pfbm(x * 3, y * 3, 3, 3, 4))
# a little ridged character in the fine band: licks of flame
r = norm(1 - np.abs(r * 2 - 1)) ** 1.6
png('T_BerserkNoise', np.stack([r, g, b], -1))

# wisp: a flame tongue, wide soft base, curling thin tip; G = erosion noise for the material's threshold
N = 256; y, x = np.mgrid[0:N, 0:N] / N
xc = x - 0.5 - 0.08 * np.sin(y * 7.0 + 1.3) * y
wd = 0.30 * (1 - y) ** 0.8 + 0.02
shape = np.clip(1 - np.abs(xc) / wd, 0, 1) ** 1.4 * np.clip(y * 6, 0, 1) * np.clip((1 - y) * 2.5, 0, 1)
ero = norm(pfbm(x * 8, y * 8, 4, 8, 5))
shape = norm(shape)
png('T_BerserkWisp', np.stack([shape, ero, np.zeros_like(shape)], -1))

# ember: hot core + soft halo
N = 64; y, x = np.mgrid[0:N, 0:N] / N
d = np.hypot(x - 0.5, y - 0.5) * 2
emb = np.clip(1 - d, 0, 1) ** 3 * 0.6 + np.clip(1 - d * 3.5, 0, 1) ** 1.5
png('T_BerserkEmber', np.stack([np.clip(emb, 0, 1)] * 3, -1))

# ground ring: cracked circle, cracks run radially out of it
N = 1024; y, x = np.mgrid[0:N, 0:N] / N
u, v = x - 0.5, y - 0.5; rr = np.hypot(u, v) * 2; ang = np.arctan2(v, u)
ringw = 0.035 + 0.02 * pnoise(ang / (2 * np.pi) * 24 % 24, np.zeros_like(ang), 5, 24)
ring = np.clip(1 - np.abs(rr - 0.72) / ringw, 0, 1) ** 0.7
# radial cracks: thin wedges at hashed angles, fading with distance from the ring
cr = np.zeros_like(rr)
rng = np.random.default_rng(90)
for a0 in np.linspace(-np.pi, np.pi, 19, endpoint=False) + rng.uniform(-0.12, 0.12, 19):
    jag = 0.05 * (pnoise(rr * 40 + a0 * 7, np.zeros_like(rr), 7, 4096) - 0.5) + 0.02 * (pnoise(rr * 140 + a0, np.ones_like(rr), 8, 4096) - 0.5)
    da = np.angle(np.exp(1j * (ang - a0 - jag)))
    w = 0.0035 + 0.006 * np.clip(1 - np.abs(rr - 0.72) / 0.25, 0, 1)
    cr = np.maximum(cr, np.clip(1 - np.abs(da) * rr / w, 0, 1) * np.clip(1 - np.abs(rr - 0.72) / rng.uniform(0.12, 0.26), 0, 1))
inner = np.clip(1 - np.abs(rr - 0.45) / 0.012, 0, 1) * (np.mod(ang * 12 / np.pi, 2) < 1.4) * 0.6     # a broken inner ring
glow = np.clip(1 - np.abs(rr - 0.72) / 0.22, 0, 1) ** 2 * np.clip(1 - rr, 0, 1) * 1.6
mask = np.clip(np.maximum.reduce([ring, cr, inner]), 0, 1) * (rr < 0.99)
png('T_BerserkRing', np.stack([mask, np.clip(glow, 0, 1), np.clip(rr, 0, 1)], -1))
print('TEX OK', OUT)
