# numpy port of M_JellyTrail_v2's PRE + outputs, to eyeball the look top-down without the editor.
#   blender -b --factory-startup -P preview_slime.py -- out.png
import sys, math, numpy as np, bpy
OUT = sys.argv[sys.argv.index('--') + 1]
W, Hh = 1500, 750
rng = np.random.default_rng(7)

def frac(x): return x - np.floor(x)
def sat(x): return np.clip(x, 0, 1)
def sstep(a, b, x): t = sat((x - a) / (b - a)); return t * t * (3 - 2 * t)

def piece(U, V, seed, age):
    s1, s2, s3 = frac(seed * 7.13 + 0.11), frac(seed * 13.7 + 0.37), frac(seed * 3.31 + 0.71)
    settle = 0.72 + 0.28 * min(age / 1.5, 1); E = 0.006; Hs = []; B0 = None
    for k in range(3):
        px = U * 2 - 1 + (E if k == 1 else 0); py = V * 2 - 1 + (E if k == 2 else 0)
        qx = px * (0.95 - 0.15 * s1) / settle; qy = py * (1.10 + 0.20 * s2) / settle
        qy = qy + 0.08 * np.sin(qx * 2.3 + s3 * 6.283)
        def g(cx, cy, w): return np.exp(-((qx - cx) ** 2 + (qy - cy) ** 2) / w)
        fm = (g(0, 0, 0.30 + 0.06 * s1) + 0.85 * g(0.30 + 0.20 * s2, 0.40 * (s3 - 0.5), 0.16 + 0.05 * s3)
              + (0.45 + 0.45 * s1) * g(-0.28 - 0.20 * s3, 0.44 * (s1 - 0.5), 0.10 + 0.08 * s2) + (0.30 + 0.40 * s3) * g(0.30 * (s2 - 0.5), 0.36 * (1 if s1 > 0.5 else -1), 0.05 + 0.05 * s2)
              + 0.90 * g(0.70 + 0.05 * s2, 0.25 * (s3 - 0.5), 0.006 + 0.006 * s1) + 0.90 * g(-0.72 - 0.04 * s3, 0.30 * (s1 - 0.5), 0.004 + 0.004 * s3)
              + 0.90 * (s3 >= 0.45) * g(0.40 * (s2 - 0.5), 0.62 + 0.05 * s1, 0.004))
        fm = fm * (1 + 0.10 * np.sin(qx * 6 + s2 * 20) * np.sin(qy * 7 + s3 * 20) + 0.04 * np.sin(qx * 17 + qy * 13 + s1 * 40))
        h = sat((fm - 0.45) / 0.55)
        body = h * h * (3 - 2 * h)
        lump = 0.10 * np.sin(qx * 8.7 + s2 * 20) * np.sin(qy * 10.3 + s3 * 20) + 0.05 * np.sin(qx * 19 + qy * 7 + s1 * 30)
        streak = 0.015 * np.sin(qy * 23 + 4.0 * np.sin(qx * 2.1 + s1 * 9)) * np.sin(qx * 5.3 + s2 * 11)
        gx, gy = qx * 6.5 + seed * 31, qy * 6.5 + seed * 31
        idx, idy = np.floor(gx), np.floor(gy); fx, fy = frac(gx) - 0.5, frac(gy) - 0.5
        hb = frac(np.sin(idx * 127.1 + idy * 311.7) * 43758.5453)
        br = 0.10 + 0.22 * frac(hb * 17.3); bx, by = (frac(hb * 7.7) - 0.5) * 0.4, (frac(hb * 3.9) - 0.5) * 0.4
        bub = (hb > 0.72) * np.sqrt(sat(1 - np.hypot(fx - bx, fy - by) / br)) * (body >= 0.35)
        if k == 0: B0 = bub
        Hs.append(np.where(body > 0, body + (lump + streak) * body + 0.18 * bub, 0))
    T = Hs[0]; dry = min(max((age - 12) / 8, 0), 1)
    c = np.zeros(T.shape + (3,))
    edgeC, midC, coreC = np.array([0.016, 0.022, 0.008]), np.array([0.040, 0.070, 0.008]), np.array([0.110, 0.160, 0.012])
    c = edgeC + (midC - edgeC) * sstep(0.02, 0.35, T)[..., None]
    c = c + (coreC - c) * sstep(0.45, 0.95, T)[..., None]
    c = c + (c * 1.8 + np.array([0.02, 0.04, 0]) - c) * (B0 * 0.5)[..., None]
    c = c + (np.array([0.030, 0.040, 0.018]) - c) * dry * 0.85
    glow = np.array([0.015, 0.05, 0.004]) * sstep(0.5, 1.0, T)[..., None] * (1 - dry)
    wet = 0.14 + (0.03 - 0.14) * sstep(0.05, 0.5, T); rough = wet + (0.62 - wet) * dry
    spec = 0.75 + (0.35 - 0.75) * dry
    k = 0.55 * (1 - dry * 0.7)
    n = np.stack([-(Hs[1] - T) / E * k * 0.25, (Hs[2] - T) / E * k * 0.25, np.ones_like(T)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    vis = 1 - min(max((age - 20) / 5, 0), 1)
    alpha = (T > 0) * sat(T / 0.14) * vis
    return c, glow, rough, spec, n, alpha

# grass ground (linear)
yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
gn = np.sin(xx * 0.9) * np.sin(yy * 1.3) * 0.5 + rng.random((Hh, W)) * 0.8
img = np.stack([0.030 + 0.012 * gn, 0.060 + 0.025 * gn, 0.014 + 0.006 * gn], -1)
Ld = np.array([-0.35, 0.45, 0.82]); Ld /= np.linalg.norm(Ld); Vd = np.array([0, 0.25, 1.0]); Vd /= np.linalg.norm(Vd)
Hv = (Ld + Vd) / np.linalg.norm(Ld + Vd)
sun = np.array([3.2, 3.0, 2.7]); sky = np.array([0.35, 0.42, 0.55])
img = img * (sun * Ld[2] + sky)

def path(x0, y0, x1, y1, n, ages):
    for i in range(n):
        t = i / (n - 1)
        cx = x0 + (x1 - x0) * t + rng.normal(0, 8); cy = y0 + (y1 - y0) * t + 18 * math.sin(t * 6) + rng.normal(0, 8)
        size = rng.uniform(95, 140); ang = math.atan2(y1 - y0, x1 - x0) + rng.normal(0, 0.35)
        x0i, x1i = int(max(cx - size, 0)), int(min(cx + size, W)); y0i, y1i = int(max(cy - size, 0)), int(min(cy + size, Hh))
        X, Y = np.meshgrid(np.arange(x0i, x1i) - cx, np.arange(y0i, y1i) - cy)
        ca, sa = math.cos(-ang), math.sin(-ang)
        U = (X * ca - Y * sa) / size + 0.5; V = (X * sa + Y * ca) / size + 0.5
        c, glow, rough, spec, nrm, al = piece(U, V, rng.random(), ages[i % len(ages)] if isinstance(ages, list) else ages)
        # rotate tangent normal back to world (top-down: tangent X = piece axis)
        nx = nrm[..., 0] * math.cos(ang) - nrm[..., 1] * math.sin(ang); ny = nrm[..., 0] * math.sin(ang) + nrm[..., 1] * math.cos(ang)
        N = np.stack([nx, ny, nrm[..., 2]], -1)
        ndl = sat(N @ Ld)[..., None]; ndh = sat(N @ Hv)
        a2 = np.maximum(rough ** 4, 1e-4); D = a2 / (math.pi * (ndh ** 2 * (a2 - 1) + 1) ** 2)
        F = 0.08 * spec
        lit = c * (sun * ndl + sky * 0.6) + (D * F * ndl[..., 0])[..., None] * sun + glow
        # sky reflection: fresnel-ish, stronger where the slope faces the viewer
        refl = (F + (1 - F) * (1 - sat(N @ Vd)) ** 5) * (1 - rough * 1.3).clip(0, 1)
        lit = lit + refl[..., None] * sky * 1.6
        # wet ground darkening under the thin film
        reg = img[y0i:y1i, x0i:x1i]
        reg[:] = reg * (1 - 0.35 * (al > 0)[..., None] * (1 - al)[..., None]) * 1.0
        reg[:] = reg * (1 - al[..., None]) + lit * al[..., None]

path(60, 200, 1440, 260, 22, [0.5, 2, 4, 6, 8])
path(80, 520, 1420, 470, 20, [9, 11, 13, 15, 17, 19])
img = img / (1 + img)   # simple tonemap
s = np.where(img <= 0.0031308, 12.92 * img, 1.055 * np.power(img, 1 / 2.4) - 0.055)
o = bpy.data.images.new('p', W, Hh); o.pixels = np.concatenate([s[::-1], np.ones((Hh, W, 1))], -1).astype(np.float32).ravel()
o.filepath_raw = OUT; o.file_format = 'PNG'; o.save(); print('PREVIEW', OUT)
