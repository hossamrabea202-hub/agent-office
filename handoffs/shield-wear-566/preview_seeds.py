# #566 offline preview of shield_paint_var.hlsl (a numpy port, BaseColor + simple bump light, no UE needed).
#   blender -b --factory-startup -P preview_seeds.py -- <out.png> [seed ...]
# Seed 0 = the original M_Shield_Paint_AAA look. The Megascans wood is replaced by a flat stand-in brown here,
# so judge the LAYOUT (chips, scratches, cuts, dirt), not the exact wood colour. Real lookdev happens in UE.
import sys, numpy as np, bpy
F = np.float32
def frac(x): return x - np.floor(x)
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def h21(px, py):
    px = frac(px * F(233.34)); py = frac(py * F(851.73))
    d = px * (px + 23.45) + py * (py + 23.45); px = px + d; py = py + d
    return frac(px * py)
def vn(px, py):
    ix, iy = np.floor(px), np.floor(py); fx, fy = px - ix, py - iy
    ux = fx ** 3 * (fx * (fx * 6 - 15) + 10); uy = fy ** 3 * (fy * (fy * 6 - 15) + 10)
    a, b = h21(ix, iy), h21(ix + 1, iy); c, d = h21(ix, iy + 1), h21(ix + 1, iy + 1)
    return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy
def fbm(px, py):
    s, a = 0.0, 0.5
    for k in range(5): s = s + a * vn(px, py); px = px * 2.03 + 17.1; py = py * 2.03 + 9.2; a *= 0.5
    return s / 0.97
def scratches(px, py, seed):
    s = np.zeros_like(px)
    for k in range(4):
        ang = h21(np.full_like(px, seed), np.full_like(px, k * 1.37)) * 3.14159
        dx, dy = np.cos(ang), np.sin(ang)
        qx = px * (1.3 + k * 0.7) + seed * 3.1; qy = py * (1.3 + k * 0.7) + seed * 3.1
        l = np.abs(frac((qx * -dy + qy * dx) * 5.0 + vn(qx * 1.7, qy * 1.7) * 0.8) - 0.5)
        m = sstep(0.62, 0.78, vn(qx * 0.9 + k * 4.3, qy * 0.9 + k * 4.3))
        s = np.maximum(s, (1 - sstep(0.0, 0.028, l)) * m)
    return s
def h1(a, b): return float(h21(np.array([a], F), np.array([b], F))[0])
def cut(ux, uy, seed, c):
    a = 0.6 + (h1(c * 1.9, seed * 3.3) - 0.5) * 1.6; dx, dy = np.cos(a), np.sin(a)
    cx = (h1(seed, c + 5.1) - 0.5) * 34.0; cy = 8.0 - h1(seed, c + 8.3) * 34.0
    ddx, ddy = ux - cx, uy - cy; along = ddx * dx + ddy * dy; across = -ddx * dy + ddy * dx
    ln = 7.0 + h1(c, seed + 2.2) * 13.0; w = 0.65 * np.clip(1 - np.abs(along) / ln, 0, 1)
    across = across + (vn(along * 0.9, np.full_like(along, c * 3.0 + seed)) - 0.5) * 0.22
    return (1 - sstep(w * 0.35, w + 0.02, np.abs(across))) * (np.abs(along) <= ln)
def shield(seed, tint=(1, 1, 1), wear=0.0, res=8):
    Y, Z = np.meshgrid(np.arange(-28, 28, 1 / res, dtype=F), np.arange(36, -39, -1 / res, dtype=F))
    s0 = seed; sv = 1.0 if s0 > 0 else 0.0
    r1, r2, r3, r4, r5 = (h1(s0, v) for v in (0.11, 0.37, 0.73, 0.91, 1.29))
    ox, oy = (r1 - 0.5) * 240 * sv, (r2 - 0.5) * 240 * sv
    wearV = (1.0 + (0.55 + (1.4 - 0.55) * r3 - 1.0) * sv) + wear * 1.5
    dirtV = 1.0 + (0.6 + 0.85 * r4 - 1.0) * sv; fade = sv * r5 * r5 * 0.3; ss = 1.7 + s0 * 37.0 * sv
    t = np.clip(-Z / 38.0, 0, 1); hw = 27.0 * (1 - t ** 1.9 * 0.97); edgeD = np.minimum(hw - np.abs(Y), 35.0 - Z)
    n1 = fbm((Y + ox) * 0.11, (Z + oy) * 0.11); n2 = fbm((Y + ox) * 0.55 + 3.1, (Z + oy) * 0.55 + 3.1)
    n3 = fbm((Y + ox) * 2.3 + 7.7, (Z + oy) * 2.3 + 7.7)
    seam = sstep(0.93, 0.99, np.abs(frac(Y / 9.0 + 0.5) - 0.5) * 2)
    wood = np.stack([0.30 + 0.08 * vn(Y * 0.9, Z * 0.05), 0.20 + 0.05 * vn(Y * 0.9, Z * 0.05), 0.11 + 0.0 * Y], -1)
    chipEdge = 1 - sstep(1.5, 1.5 + 7.0 * wearV, edgeD + (n2 - 0.5) * 9); cT = (wearV - 1) * 0.09
    chip = np.clip(chipEdge * sstep(0.30, 0.50, n3) + sstep(0.76 - cT, 0.80 - cT, n2 * 0.55 + n3 * 0.62), 0, 1)
    scr = scratches(Y * 0.045 + ox * 0.01, Z * 0.045 + oy * 0.01, ss)
    scr = np.maximum(scr, scratches(Y * 0.07 + ox * 0.013 + 5.3, Z * 0.07 + oy * 0.013 + 5.3, ss + 11.0) * np.clip((wearV - 1) * 1.6, 0, 1))
    cuts = np.zeros_like(Y)
    for c in range(3):
        on = sv * (h1(s0 * 7.3, c * 2.71) <= 0.15 + 0.35 * wearV - c * 0.22)
        if on: cuts = np.maximum(cuts, cut(Y, Z, s0, c))
    cuts *= edgeD >= 0.8
    brush = vn(Y * 0.8, Z * 0.045) * 0.55 + vn(Y * 2.4, Z * 0.11) * 0.45
    paint = np.array([0.022, 0.058, 0.205], F) * ((0.8 + brush * 0.38) * (0.88 + n1 * 0.28))[..., None]
    lum = paint.mean(-1, keepdims=True) * 1.25 + 0.012; paint = paint + (lum - paint) * fade
    k = (sstep(0.55, 0.82, n1) * 0.55)[..., None]; paint = paint + (paint * 0.6 + np.array([0.018, 0.015, 0.011]) - paint) * k
    dirt = np.clip(np.clip((1 - sstep(0, 9, edgeD)) * 0.55 + t * 0.4, 0, 1) * (0.55 + n2 * 0.7) * dirtV, 0, 1)
    paint = paint + (np.array([0.032, 0.026, 0.019]) - paint) * (dirt * 0.55)[..., None]
    paint = paint * (1 - seam * 0.55)[..., None]
    col = paint + (wood * 0.5 - paint) * chip[..., None]
    col = col + (np.array([0.30, 0.28, 0.25]) * 0.75 - col) * (scr * (1 - chip) * 0.65)[..., None]
    col = col + (wood * 0.42 - col) * cuts[..., None]
    h = (1 - chip) * 0.6 - seam * 0.9 + brush * 0.07 - scr * 0.3 + n3 * 0.06 + wood.mean(-1) * chip * 0.4 - cuts * 0.9
    gy, gz = np.gradient(h * 0.07 * res * 6)
    shade = np.clip(0.85 + (-gz * 0.6 + gy * 0.4), 0.5, 1.25)[..., None]
    rgb = np.clip(col * np.array(tint, F) * shade, 0, 1); rgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)
    inside = (edgeD > 0)[..., None]
    return np.where(inside, rgb, np.array([0.55, 0.56, 0.58]))
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; seeds = [float(s) for s in args[1:]] or [0.0, 0.137, 0.291, 0.448, 0.602, 0.777, 0.913]
tints = [(1, 1, 1)] + [tuple(0.55 + (1.15 - 0.55) * a for a in [x] * 3) for x in np.linspace(0.1, 0.9, len(seeds) - 1)]
tiles = [shield(s, (1, 1, 1), 0.0 if s == 0 else (i * 0.05) % 0.3) for i, s in enumerate(seeds)]
img = np.concatenate([np.pad(t, ((8, 8), (8, 8), (0, 0)), constant_values=0.55) for t in tiles], 1)
h, w, _ = img.shape
im = bpy.data.images.new('prev', w, h, alpha=True)
px = np.concatenate([img[::-1], np.ones((h, w, 1))], -1).astype(np.float32).ravel()
im.pixels.foreach_set(px); im.filepath_raw = out; im.file_format = 'PNG'; im.save()
print('PREVIEW', out, w, h, 'seeds', seeds)
