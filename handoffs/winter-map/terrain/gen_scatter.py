"""WinterKeep #390: dressing by rules -> instance lists for UE (and 2 small tileable textures).

python.exe -I gen_scatter.py      (after gen_terrain.py)
Writes out/scatter.json: {kind: {cell: [[x_cm, y_cm, z_cm, yaw_deg, scale], ...]}} in UE world cm, grouped by a 256 m
World Partition grid cell, so each cell becomes one HISM actor that streams with its cell.
Writes out/T_WK_MacroNoise.png (tileable grey, linear) and out/T_WK_SnowRipple_N.png (tileable wind-ripple normal).
"""
import json, math, os, struct, zlib
import numpy as np
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
H = np.load(os.path.join(OUT, 'height_m.npy')); N = H.shape[0]; HALF = (N - 1) / 2
LAY = np.load(os.path.join(OUT, 'layers.npz')); L = json.load(open(os.path.join(OUT, 'layout.json')))
rng = np.random.default_rng(390); CELL = 256.0

def m(k): return LAY['M_' + k].astype(np.float32) / 255
def hz(x, y):                                      # bilinear height (m) at image metres
    x = np.clip(x, 0, N - 1.001); y = np.clip(y, 0, N - 1.001); i = x.astype(int); j = y.astype(int); fx = x - i; fy = y - j
    return (H[j, i] * (1 - fx) + H[j, i + 1] * fx) * (1 - fy) + (H[j + 1, i] * (1 - fx) + H[j + 1, i + 1] * fx) * fy
def scatter(mask, spacing, density, smin, smax, sink, clump=None):
    ys, xs = np.mgrid[0:N - 1:spacing, 0:N - 1:spacing].astype(np.float32)
    xs = np.clip(xs + rng.uniform(0, spacing, xs.shape), 0, N - 1.01).ravel(); ys = np.clip(ys + rng.uniform(0, spacing, ys.shape), 0, N - 1.01).ravel()
    p = mask[ys.astype(int), xs.astype(int)] * density
    if clump is not None: p *= clump[ys.astype(int), xs.astype(int)]
    k = rng.uniform(0, 1, p.shape) < p; xs, ys = xs[k], ys[k]
    return xs, ys, hz(xs, ys) - sink, rng.uniform(0, 360, len(xs)), rng.uniform(smin, smax, len(xs))

# clumping: seeds fall near the parent, so stands are patchy (knowledge rule 7: vegetation by rules, not uniform scatter)
def blur(a, r):
    for ax in (0, 1):
        c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge'), axis=ax)
        a = (np.take(c, np.arange(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, np.arange(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a
clump = np.clip(blur(rng.uniform(0, 1, (N, N)).astype(np.float32), 12) * 6 - 2.5, 0.25, 1.0)
exposed = m('WindExposure'); rocks = m('Rocks'); drift = m('Drift'); forest = m('Forest'); birch = m('Birch')
road = LAY['Road'].astype(np.float32) / 255; ice = LAY['Ice'].astype(np.float32) / 255; melt = LAY['RealmMelt'].astype(np.float32) / 255
clear = (1 - np.clip(road * 3, 0, 1)) * (1 - ice) * (1 - melt)
K = {
    'Spruce':       scatter(forest * clear, 5.0, 0.85, 0.75, 1.25, 0.6, clump),                     # tall dense stands
    'Spruce_Young': scatter(np.clip(forest * 2.5, 0, 1) * (forest < 0.5) * clear, 7.0, 0.35, 0.35, 0.7, 0.3),   # forest edge
    'Birch':        scatter(birch * clear, 8.0, 0.3, 0.8, 1.2, 0.3),
    'Rock_Large':   scatter(rocks * clear * (1 - forest), 14.0, 0.35, 0.8, 2.2, 0.8),               # on scoured slopes
    'Rock_Small':   scatter(np.clip(rocks + exposed * 0.3, 0, 1) * clear, 6.0, 0.2, 0.4, 1.0, 0.2),
    'DeadShrub':    scatter(np.clip(exposed - 0.5, 0, 1) * 2 * clear * (1 - forest), 9.0, 0.25, 0.6, 1.1, 0.1),  # tufts poking through thin snow
    'Drift_Mound':  scatter(np.clip(drift - 0.55, 0, 1) * 2.2 * clear, 22.0, 0.25, 0.8, 1.6, 0.4),  # wind-shaped mounds on the lee
}
def cell(x, y): return '%d_%d' % (int(x // CELL), int(y // CELL))
out = {'cell_m': CELL, 'note': 'UE cm; z = landscape height; yaw deg; uniform scale', 'kinds': {}}
for k, (xs, ys, zs, yaw, sc) in K.items():
    d = {}
    for x, y, z, a, s in zip(xs, ys, zs, yaw, sc):
        d.setdefault(cell(x, y), []).append([round((x - HALF) * 100, 1), round((y - HALF) * 100, 1), round(z * 100, 1), round(a, 1), round(s, 3)])
    out['kinds'][k] = d; print(k, len(xs))
json.dump(out, open(os.path.join(OUT, 'scatter.json'), 'w'), separators=(',', ':'))

# ---- two small tileable textures (procedural, calibrated; pbr_check them)
def tnoise(n, cells, seed, octv=5):
    r = np.random.default_rng(seed); tot = np.zeros((n, n)); amp = 1; nm = 0
    for o in range(octv):
        c = cells * 2 ** o; lat = r.uniform(-1, 1, (c, c)); u = np.arange(n) * c / n; i = u.astype(int); f = u - i; f = f * f * (3 - 2 * f)
        a = lat[np.ix_(i, i)]; b = lat[np.ix_(i, (i + 1) % c)]; cc = lat[np.ix_((i + 1) % c, i)]; dd = lat[np.ix_((i + 1) % c, (i + 1) % c)]
        fx = f[None, :]; fy = f[:, None]; tot += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (cc * (1 - fx) + dd * fx) * fy); nm += amp; amp *= 0.5
    return tot / nm
def png(path, arr, ct):
    hh, ww = arr.shape[:2]; raw = b''.join(b'\x00' + arr[y].astype(np.uint8).tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', ww, hh, 8, ct, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))
n = 1024
macro = tnoise(n, 4, 1) * 0.6 + tnoise(n, 16, 2) * 0.4
png(os.path.join(OUT, 'T_WK_MacroNoise.png'), np.clip(128 + macro * 160, 0, 255), 0)
# wind ripples: anisotropic bands across the wind, broken by noise (sastrugi-like), then a normal map
y = np.arange(n)[:, None] / n; x = np.arange(n)[None, :] / n
warp = tnoise(n, 6, 3) * 0.06
hgt = np.sin(2 * math.pi * (12 * (x + y) / 1.0 + warp * 12)) * 0.5 + 0.5
hgt = hgt ** 1.8 * (0.6 + 0.4 * (tnoise(n, 8, 4) * 0.5 + 0.5)) + tnoise(n, 32, 5) * 0.15
gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 6; gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 6
nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
nrm = np.dstack([(-gx * nz) * 127.5 + 127.5, (gy * nz) * 127.5 + 127.5, nz * 127.5 + 127.5])   # DirectX green (UE)
png(os.path.join(OUT, 'T_WK_SnowRipple_N.png'), np.clip(nrm, 0, 255), 2)
print('textures written')
