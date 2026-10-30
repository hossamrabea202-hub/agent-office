# #180 blue shield skill VFX textures (laptop2 2026-10-30): numpy sheets for the four skill levels, Niagara/material ready.
#   blender -b --factory-startup -P build_shieldfx.py     -> tex/T_ShieldFX_*.png (1K, linear masks; alpha = the mask)
#   T_ShieldFX_RimGlow      LV1: a soft ring that hugs the shield's rim (radial falloff, use as a decal/overlay mask)
#   T_ShieldFX_Shockwave    LV2: bash shockwave ring with cracks, 8 frames in a 4x2 flipbook (expanding ring, fading)
#   T_ShieldFX_Runes        LV3: a ring of 12 runes around a centre sigil (emissive mask; pan a noise over it for flicker)
#   T_ShieldFX_DomeCells    LV4: block dome: hex cells with bright edges, a fresnel-friendly tile (seamless u)
#   T_ShieldFX_Spark        a 3-pointed spark sprite for hits
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(D, 'tex')
N = 1024
i = np.arange(N); U, V = np.meshgrid((i + 0.5) / N, (i + 0.5) / N, indexing='xy'); X, Y = U * 2 - 1, V * 2 - 1
R, A = np.hypot(X, Y), np.arctan2(Y, X)
def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def vnoise(u, v, s):
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64); fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = _hash(iu, iv, s), _hash(iu + 1, iv, s), _hash(iu, iv + 1, s), _hash(iu + 1, iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def fbm(u, v, s, oct=4):
    t, amp, f, tot = 0, 1.0, 1.0, 0
    for o in range(oct): t = t + amp * vnoise(u * f, v * f, s + o * 17); tot += amp; amp *= 0.5; f *= 2.03
    return t / tot
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def save(name, rgb, a):
    px = np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]], -1)[::-1]
    im = bpy.data.images.new(name, px.shape[1], px.shape[0], alpha=True); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(px.astype(np.float32).ravel()); im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

# LV1 rim glow: ring at r 0.9 +- 0.08, soft inner falloff, slight pulse texture
ring = np.exp(-((R - 0.9) / 0.06) ** 2) + 0.35 * np.exp(-((R - 0.9) / 0.16) ** 2)
ring = ring * (0.85 + 0.3 * fbm(np.cos(A) * 3, np.sin(A) * 3, 1, 3)) * (R < 1.0)
save('T_ShieldFX_RimGlow', np.stack([ring, ring * 0.8, ring], -1), ring)

# LV2 shockwave flipbook 4x2: expanding ring, cracks radiating, fading
frames = []
for f in range(8):
    t = (f + 0.5) / 8; r0 = 0.15 + 0.8 * t; w = 0.05 + 0.05 * t
    rg = np.exp(-((R - r0) / w) ** 2) * (1 - t) ** 0.8
    cracks = sstep(0.02, 0.0, np.abs(np.sin(A * 9 + 1.3 * fbm(np.cos(A) * 2, np.sin(A) * 2, 2, 3) * 4))) * (R < r0) * (R > r0 * 0.4) * (1 - t)
    inner = np.exp(-(R / (0.25 * (1 - t) + 0.02)) ** 2) * (1 - t) * 0.8
    frames.append(np.clip(rg + cracks * 0.6 + inner, 0, 1))
S = 512; sheet = np.zeros((2 * S, 4 * S), np.float32)
for f, fr in enumerate(frames): sheet[(f // 4) * S:(f // 4 + 1) * S, (f % 4) * S:(f % 4 + 1) * S] = fr[::2, ::2]
save('T_ShieldFX_Shockwave', np.stack([sheet, sheet * 0.9, sheet * 0.7], -1), sheet)

# LV3 runes: 12 glyphs on a ring + centre sigil; glyphs are random strokes on a 5x5 grid, mirrored for symmetry
runes = np.zeros_like(U)
def glyph(cx, cy, size, seed):
    g = np.zeros_like(U); rng = np.random.default_rng(seed)
    pts = [(rng.integers(0, 3), rng.integers(0, 5)) for _ in range(5)]
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        for sx in (-1, 1):
            x0, y0 = cx + sx * (a0 - 1) * size / 4, cy + (b0 - 2) * size / 4; x1, y1 = cx + sx * (a1 - 1) * size / 4, cy + (b1 - 2) * size / 4
            L = max(math.hypot(x1 - x0, y1 - y0), 1e-4); tx, ty = (x1 - x0) / L, (y1 - y0) / L
            t = np.clip((X - x0) * tx + (Y - y0) * ty, 0, L); d = np.hypot(X - (x0 + tx * t), Y - (y0 + ty * t))
            g = np.maximum(g, sstep(size * 0.09, size * 0.03, d))
    return g
for k in range(12):
    a = 2 * math.pi * k / 12; runes = np.maximum(runes, glyph(0.72 * math.cos(a), 0.72 * math.sin(a), 0.18, 100 + k))
runes = np.maximum(runes, glyph(0, 0, 0.42, 200))
runes = np.maximum(runes, np.exp(-((R - 0.72) / 0.012) ** 2) * 0.6 + np.exp(-((R - 0.55) / 0.008) ** 2) * 0.4)
save('T_ShieldFX_Runes', np.stack([runes * 0.6, runes * 0.85, runes], -1), runes)

# LV4 dome cells: hex grid edges, seamless in u (tile 8 cells across), fading to the top
hx = 8; hy = 7
def hexdist(u, v):
    # distance to the nearest hex edge on a pointy-top hex grid, periodic in u
    q = u * hx; r = v * hy * 1.1547
    best = np.full(u.shape, 9.0)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx = np.round(q) + dx; cy = np.round(r) + dy
            px = cx + 0.5 * (np.mod(cy, 2)); py = cy * 0.8660
            d = np.hypot((q + 0.5 * np.mod(np.round(r), 2)) - px, r * 0.8660 - py)
            best = np.minimum(best, d)
    return best
d1 = hexdist(U, V); cells = sstep(0.36, 0.5, d1) + 0.25 * sstep(0.25, 0.5, d1)
cells = np.clip(cells, 0, 1) * (0.8 + 0.4 * fbm(U * 6, V * 6, 7, 3)) * sstep(1.0, 0.8, V)
save('T_ShieldFX_DomeCells', np.stack([cells * 0.5, cells * 0.8, cells], -1), cells)

# spark sprite
sp = np.exp(-(R / 0.08) ** 2)
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.4; t = X * math.cos(a) + Y * math.sin(a); s = -X * math.sin(a) + Y * math.cos(a)
    sp = np.maximum(sp, np.exp(-(s / (0.02 + 0.03 * (1 - np.abs(t)))) ** 2) * (np.abs(t) < 0.7) * (1 - np.abs(t) / 0.7))
save('T_ShieldFX_Spark', np.stack([sp, sp * 0.95, sp * 0.8], -1), sp)
print('SHIELDFX OK')
