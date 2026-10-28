# numpy port of M_XbowElectric's Custom node over a stand-in crossbow silhouette (local cm, z = 0), 3 time steps side by side.
#   blender -b --factory-startup -P preview_electric.py -- out.png
import sys, numpy as np, bpy
OUT = sys.argv[sys.argv.index('--') + 1]
W, H, S = 600, 420, 0.16   # pixels per panel, cm per pixel
ArcScale, ArcWidth, Intensity = 0.09, 0.022, 14.0
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
X = (xx - W / 2) * S * 1.0; Y = (H * 0.55 - yy) * S   # cm
# silhouette: stock along -Y..+Y, limbs as a shallow arc across X, string, stirrup
stock = (np.abs(X) < 2.6) & (Y > -30) & (Y < 26)
limb_y = 18 - 0.012 * X ** 2
limbs = (np.abs(Y - limb_y) < 1.6 + 0.8 * (1 - np.abs(X) / 42)) & (np.abs(X) < 42)
string = (np.abs(Y - (18 - 0.012 * 42 ** 2) - (np.abs(X) - 42) * 0 ) < 0.25) & (np.abs(X) < 42)
mask = stock | limbs | string
rim = np.clip(0.3 + 0.7 * (1 - np.minimum(1, np.abs(np.gradient(mask.astype(np.float32))[0]) + np.abs(np.gradient(mask.astype(np.float32))[1])) ), 0, 1)
edge = np.zeros_like(X)
for k in range(1, 4):  # cheap "fresnel": distance to the silhouette edge
    m = mask.copy(); m[k:] &= mask[:-k]; m[:-k] &= mask[k:]; m[:, k:] &= mask[:, :-k]; m[:, :-k] &= mask[:, k:]
    edge += (mask & ~m) * 0.33
fres = np.clip(edge, 0, 1)

def frac(v): return v - np.floor(v)
def field(now):
    P = np.stack([X, Y, np.zeros_like(X)], -1) * ArcScale; step_t = np.floor(now * 11.0); total = 0
    for L in range(2):
        o = np.array([now * (0.6 + L * 0.35), step_t * 1.37 + L * 5.1, now * 0.25])
        n = 0; amp = 0.55; fq = 1.0 + L * 0.9
        for O in range(3):
            x = P * fq + o + O * 17.3; i = np.floor(x); f = frac(x); f = f * f * (3 - 2 * f); v = 0
            for c in range(8):
                d = np.array([c & 1, (c >> 1) & 1, (c >> 2) & 1], np.float32)
                h = frac(np.sin(((i + d) * np.array([127.1, 311.7, 74.7])).sum(-1)) * 43758.5453)
                w = (1 - f) * (1 - d) + f * d
                v = v + h * w[..., 0] * w[..., 1] * w[..., 2]
            n = n + (v - 0.5) * amp; amp *= 0.5; fq *= 2.3
        w2 = ArcWidth * (1.0 if L == 0 else 0.6)
        core = np.clip(1 - np.abs(n) / w2, 0, 1) ** 3; halo = np.clip(1 - np.abs(n) / (w2 * 5), 0, 1) * 0.07
        gx = P * 0.45 + np.array([0, step_t * 0.73, L * 9.1]); gi = np.floor(gx); gf = frac(gx); gf = gf * gf * (3 - 2 * gf); gv = 0
        for c in range(8):
            d = np.array([c & 1, (c >> 1) & 1, (c >> 2) & 1], np.float32); w = (1 - gf) * (1 - d) + gf * d
            gv = gv + frac(np.sin(((gi + d) * np.array([269.5, 183.3, 246.1])).sum(-1)) * 43758.5453) * w[..., 0] * w[..., 1] * w[..., 2]
        total = total + (core + halo) * np.clip((gv - 0.52) * 6, 0, 1) * (1.0 if L == 0 else 0.55)
    flick = 0.55 + 0.45 * frac(np.sin(step_t * 12.9898) * 43758.5453)
    r = 0.30 + 0.70 * fres
    t = np.clip(total - 0.5, 0, 1)[..., None]
    col = np.array([0.35, 0.65, 1.0]) * (1 - t) + np.array([0.95, 0.97, 1.0]) * t
    return col * (total * flick * r * Intensity)[..., None]

panels = []
for now in (10.0, 10.09, 10.18):
    base = np.where(mask[..., None], np.array([0.05, 0.045, 0.04]), np.array([0.012, 0.013, 0.016]))
    img = base + field(now) * mask[..., None] * 0.12
    img = img / (1 + img)
    panels.append(np.where(img <= 0.0031308, 12.92 * img, 1.055 * np.power(img, 1 / 2.4) - 0.055))
img = np.concatenate(panels, 1); h, w = img.shape[:2]
o = bpy.data.images.new('p', w, h); o.pixels = np.concatenate([img[::-1], np.ones((h, w, 1))], -1).astype(np.float32).ravel()
o.filepath_raw = OUT; o.file_format = 'PNG'; o.save(); print('PREVIEW', OUT, w, h)
