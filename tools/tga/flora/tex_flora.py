# Meadow flora atlas (#352, TGA): blender -b --factory-startup -P tex_flora.py   (env WORK) -> out/tex/T_MeadowFlora_BC/ORM/N (2K)
# 4x4 tiles of 512 (tile i: column i%4, row i//4, row 0 at the bottom = UV v 0). Inside a tile s = along the organ (UV u,
# base -> tip), t = across (UV v, 0.5 = midrib) or around for stems / lathes. The mesh outline gives the shape, so a tile only
# paints the interior: veins, striations, crumple, scales, fissures. Every value is calibrated for pbr_check (non-metal 30-240 sRGB).
#   0 DaisyPetal  1 DaisyDisc  2 PoppyPetal  3 PoppyHead   4 CornflowerFloret  5 YarrowFloret  6 HerbLeaf   7 Stem
#   8 HawthornLeaf 9 HazelLeaf 10 BrackenPinna 11 BarkHawthorn 12 BarkHazel  13 Haw  14 BrackenStipe  15 Involucre
import bpy, numpy as np, os
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
R, T = 2048, 512
def pn(f, seed, sx=1.0, sy=1.0):
    fx, fy = max(1, int(round(f * sx))), max(1, int(round(f * sy)))
    g = np.random.default_rng(seed).random((fy, fx))
    y, x = np.meshgrid(np.arange(T) * fy / T, np.arange(T) * fx / T, indexing='ij')
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); tx, ty = x - x0, y - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty); x1, y1 = (x0 + 1) % fx, (y0 + 1) % fy
    a = g[y0, x0] + (g[y0, x1] - g[y0, x0]) * tx; b = g[y1, x0] + (g[y1, x1] - g[y1, x0]) * tx
    return a + (b - a) * ty
def fbm(f, oct, seed, sx=1.0, sy=1.0):
    s, a, t = 0.0, 1.0, 0.0
    for k in range(oct): s = s + a * pn(f * 2 ** k, seed + k, sx, sy); t += a; a *= 0.5
    return s / t
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lin(*c): return np.array([((x / 255 + 0.055) / 1.055) ** 2.4 for x in c], np.float32)
def mix(a, b, t): return a + (b - a) * np.asarray(t, np.float32)[..., None]
def srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
y_, x_ = np.mgrid[0:T, 0:T]; S = (x_ + 0.5) / T; V = (y_ + 0.5) / T; A = (V - 0.5) * 2          # along, across, across -1..1
RAD = np.hypot(S - 0.5, V - 0.5) * 2; ANG = np.arctan2(V - 0.5, S - 0.5)                           # planar discs
BC = np.zeros((R, R, 3), np.float32); RO = np.zeros((R, R), np.float32); HH = np.zeros((R, R), np.float32); HS = np.ones((R, R), np.float32)
def put(i, col, rough, h, hscale):
    c, r = i % 4, i // 4; sl = (slice(r * T, (r + 1) * T), slice(c * T, (c + 1) * T))
    BC[sl] = col; RO[sl] = np.clip(rough, 0.05, 1); HH[sl] = h; HS[sl] = hscale
def veins(phase, width): f = phase - np.floor(phase); return ss(width, 0, np.minimum(f, 1 - f))
def leafveins(k, slant, width=0.035):                                          # pinnate laterals leaving the midrib towards the tip
    return veins(S * k - np.abs(A) * slant, width) * ss(0.98, 0.85, np.abs(A))
mid = ss(0.05, 0.0, np.abs(A))
# 0 daisy ray petal: white, faint lengthwise striations, greenish-cream base
st = veins(A * 4.5, 0.12); n = fbm(6, 3, 1)
col = mix(lin(232, 230, 222), lin(214, 214, 200), st * 0.6) * (0.97 + 0.05 * n)[..., None]
col = mix(col, lin(205, 210, 160), ss(0.14, 0.0, S))
put(0, col, 0.62 + 0.06 * (n - 0.5), 0.3 * st + 0.2 * n, 0.0006)
# 1 daisy disc (planar): golden florets in a Fibonacci-ish cell pattern, greener in the unopened centre
cell = 0.5 + 0.5 * np.cos(RAD * 60) * np.cos(ANG * 34 + RAD * 18); n = fbm(10, 3, 2)
col = mix(lin(222, 168, 22), lin(196, 140, 18), cell * 0.7) * (0.92 + 0.12 * n)[..., None]
col = mix(col, lin(176, 168, 52), ss(0.35, 0.0, RAD)); col = mix(col, lin(150, 120, 40), ss(0.92, 1.0, RAD))
put(1, col, 0.66 + 0.08 * cell, cell * 0.8 + 0.3 * n, 0.0015)
# 2 poppy petal: scarlet, fanning veins, dark basal blotch (KB floor: >= 30 sRGB), crepe-paper crumple
fan = veins(A / (0.22 + S) * 3.0, 0.08); cr = fbm(5, 4, 3); cr2 = fbm(14, 3, 4)
col = mix(lin(212, 34, 20), lin(186, 22, 16), fan * 0.5) * (0.92 + 0.12 * cr2)[..., None]
col = mix(col, lin(228, 62, 30), ss(0.75, 1.0, S) * 0.35)
blot = ss(0.2, 0.12, S + 0.08 * np.abs(A) ** 2) * ss(0.95, 0.7, np.abs(A)); col = mix(col, lin(52, 26, 34), blot)
put(2, col, 0.5 + 0.1 * (cr2 - 0.5), 0.6 * cr + 0.3 * cr2 + 0.2 * fan, 0.0012)
# 3 poppy head (lathe, s up the capsule): stamen ring (dark), grey-green capsule with bloom, purple-grey stigma disc rays on top
n = fbm(8, 3, 5); rib = veins(V * 9, 0.18)
col = mix(lin(118, 140, 96), lin(140, 158, 120), n) * (0.95 + 0.06 * rib)[..., None]
col = mix(col, lin(56, 44, 60), ss(0.22, 0.16, S)); col = mix(col, lin(92, 74, 98) * (0.8 + 0.4 * rib)[..., None], ss(0.82, 0.88, S))
put(3, col, np.where(S < 0.2, 0.7, 0.45 + 0.1 * n), rib * 0.5 + 0.2 * n, 0.0006)
# 4 cornflower floret: violet-white base, saturated blue tube, fine veins
n = fbm(8, 3, 6); vv = veins(A * 3, 0.1)
col = mix(lin(118, 70, 150), lin(58, 98, 204), ss(0.15, 0.45, S)) * (0.93 + 0.1 * n)[..., None]
col = mix(col, lin(44, 78, 176), vv * 0.4)
put(4, col, 0.56 + 0.06 * (n - 0.5), 0.3 * vv + 0.2 * n, 0.0005)
# 5 yarrow floret (planar, 5 lobes): off-white with a cream eye
lob = 0.5 + 0.5 * np.cos(ANG * 5); n = fbm(8, 2, 7)
col = mix(lin(228, 224, 206), lin(212, 202, 156), ss(0.35, 0.1, RAD)) * (0.96 + 0.05 * n)[..., None]
col = mix(col, lin(204, 200, 182), ss(0.6, 1.0, RAD) * (1 - lob) * 0.6)
put(5, col, 0.68 + 0.05 * (n - 0.5), 0.3 * lob * ss(0.3, 0.9, RAD) + 0.2 * n, 0.0004)
# 6 herb leaf (daisy, poppy, yarrow, cornflower rosettes): mid green, pale raised midrib, sunken laterals, mottled
n = fbm(4, 4, 8); n2 = fbm(20, 3, 9); lv = leafveins(9, 2.6)
col = mix(lin(70, 102, 40), lin(88, 118, 50), n) * (0.94 + 0.08 * n2)[..., None]
col = mix(col, lin(122, 146, 82), np.maximum(mid, lv * 0.45)); col = mix(col, lin(98, 122, 56), ss(0.25, 0.0, S) * 0.5)
put(6, col, 0.5 + 0.08 * (n2 - 0.5) + 0.06 * mid, mid * 0.6 - lv * 0.4 + 0.15 * n2, 0.0004)
# 7 stem (around = t): green, lengthwise ridges, fine hairs speckle
rid = veins(V * 7, 0.2); hair = ss(0.8, 0.9, pn(160, 10, 0.5, 2.0)); n = fbm(3, 3, 11, 0.3, 1)
col = mix(lin(72, 104, 44), lin(96, 126, 62), rid * 0.5 + 0.4 * n) ; col = mix(col, lin(150, 162, 120), hair * 0.35)
put(7, col, 0.58 + 0.08 * rid, rid * 0.5 + hair * 0.2, 0.0003)
# 8 hawthorn leaf: dark glossy green, some autumn yellowing / bronzing
n = fbm(3, 4, 12); n2 = fbm(18, 3, 13); lv = leafveins(6, 1.6); au = ss(0.7, 0.85, fbm(2, 3, 14))
col = mix(lin(58, 88, 34), lin(74, 102, 40), n) * (0.94 + 0.08 * n2)[..., None]
col = mix(col, lin(96, 120, 56), np.maximum(mid, lv * 0.35)); col = mix(col, lin(150, 118, 48), au * 0.4)
put(8, col, 0.38 + 0.08 * (n2 - 0.5) + 0.15 * au, mid * 0.5 - lv * 0.3 + 0.2 * n2, 0.0004)
# 9 hazel leaf: matte, hairy, strong straight laterals, quilted between them; late-October yellowing
n = fbm(3, 4, 15); n2 = fbm(22, 3, 16); lv = leafveins(7, 1.1, 0.045); au = ss(0.5, 0.78, fbm(2, 3, 17) + 0.2 * S)
quilt = np.sin(np.pi * (S * 7 - np.abs(A) * 1.1)) ** 2
col = mix(lin(86, 112, 44), lin(104, 128, 52), n) * (0.93 + 0.09 * n2)[..., None]
col = mix(col, lin(130, 150, 80), np.maximum(mid, lv * 0.5)); col = mix(col, lin(176, 148, 58), au * 0.6)
col = mix(col, lin(140, 104, 50), ss(0.85, 1.0, np.abs(A)) * au * 0.6)
put(9, col, 0.66 + 0.06 * (n2 - 0.5), mid * 0.4 - lv * 0.6 + quilt * 0.4 + 0.1 * n2, 0.0006)
# 10 bracken pinna: yellow-green, midrib, browning towards the tips (late season)
n = fbm(4, 4, 18); n2 = fbm(20, 3, 19); lv = leafveins(14, 3.0, 0.05); br = ss(0.55, 1.0, S + 0.3 * (fbm(3, 3, 20) - 0.5))
col = mix(lin(94, 120, 40), lin(110, 132, 48), n) * (0.94 + 0.08 * n2)[..., None]
col = mix(col, lin(130, 148, 72), np.maximum(mid, lv * 0.35)); col = mix(col, lin(150, 104, 52), br * 0.55)
put(10, col, 0.52 + 0.08 * (n2 - 0.5), mid * 0.5 - lv * 0.3 + 0.15 * n2, 0.0004)
# 11 hawthorn bark (s along the branch, t around): grey-brown, lengthwise fissures and flakes, grey-green lichen
fis = ss(0.72, 0.9, 1 - np.abs(2 * fbm(3, 4, 21, 0.25, 4) - 1)); n = fbm(6, 4, 22); lich = ss(0.66, 0.74, fbm(4, 4, 23))
col = mix(lin(104, 92, 80), lin(86, 76, 66), n) ; col = mix(col, lin(52, 44, 38), fis * 0.8); col = mix(col, lin(132, 138, 104), lich * 0.8)
put(11, col, 0.84 + 0.08 * fis - 0.1 * lich, -fis * 0.8 + 0.3 * n + 0.2 * lich, 0.0012)
# 12 hazel bark: smooth, shiny red-brown to grey, pale lenticels elongated across the stem
n = fbm(3, 4, 24, 0.5, 1); len_ = ss(0.86, 0.93, pn(40, 25, 0.25, 3.0)) ; peel = ss(0.7, 0.8, fbm(4, 3, 26, 0.4, 2))
col = mix(lin(112, 84, 62), lin(124, 112, 98), n * 0.7 + 0.3 * peel); col = mix(col, lin(176, 160, 128), len_ * 0.8)
put(12, col, 0.5 + 0.12 * n + 0.2 * len_, len_ * 0.5 + 0.2 * n, 0.0005)
# 13 haw (lathe, s bottom -> top): glossy deep red, dark sepal crown at the top
n = fbm(6, 3, 27)
col = mix(lin(160, 32, 24), lin(132, 24, 22), n); col = mix(col, lin(68, 44, 36), ss(0.84, 0.92, S)); col = mix(col, lin(120, 96, 50), ss(0.08, 0.0, S))
put(13, col, np.where(S > 0.86, 0.75, 0.28 + 0.1 * n), 0.2 * n, 0.0003)
# 14 bracken stipe: brown base turning green
rid = veins(V * 5, 0.2); n = fbm(3, 3, 28, 0.3, 1)
col = mix(lin(96, 72, 46), lin(104, 124, 52), ss(0.12, 0.35, S)) * (0.92 + 0.1 * rid + 0.06 * n)[..., None]
put(14, col, 0.55 + 0.08 * rid, rid * 0.5, 0.0003)
# 15 involucre / buds (lathe): overlapping green scales with brown fringed tips (cornflower, daisy bracts, buds)
row = S * 7 + 0.5 * np.floor(V * 9) % 2 * 0.5; frac = row - np.floor(row); ang = (V * 9) % 1
scale_tip = ss(0.7, 0.95, frac) * ss(0.5, 0.15, np.abs(ang - 0.5)); n = fbm(8, 3, 29)
col = mix(lin(88, 112, 58), lin(104, 126, 70), n); col = mix(col, lin(76, 60, 44), scale_tip * 0.85)
put(15, col, 0.6 + 0.1 * scale_tip, frac * 0.6 - scale_tip * 0.2, 0.0005)
# ---- normals from height (per tile scale), cavity AO ----
H = HH * HS * 2000.0                                                          # -> mm-ish, tile = 1 unit
gx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) * 0.5; gy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) * 0.5
for k in range(1, 4): gx[:, k * T - 1:k * T + 1] = 0; gy[k * T - 1:k * T + 1, :] = 0    # no seams between tiles
nrm = np.stack([-gx, -gy, np.ones_like(H)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm = nrm * 0.5 + 0.5; nrm[..., 1] = 1 - nrm[..., 1]  # DirectX
b = H.copy()
for ax in (0, 1): b = sum(np.roll(b, k, ax) for k in range(-5, 6)) / 11
ao = np.clip(1 + (H - b) * 0.8, 0.6, 1)
def save(name, rgb):
    im = bpy.data.images.new(name, R, R, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((R, R, 4), np.float32); a[..., :3] = rgb; im.pixels.foreach_set(np.clip(a, 0, 1).ravel())
    im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
save('T_MeadowFlora_BC', srgb(BC)); save('T_MeadowFlora_ORM', np.stack([ao, RO, np.zeros_like(RO)], -1)); save('T_MeadowFlora_N', nrm)
print('TEX OK flora', flush=True)
