# Farm textures for #223 (TGA): blender -b --factory-startup -P paint_farm.py   env RES (2048)
# T_FieldSoil_*: seamless 2 m tilled-soil tile (clods, pebbles, straw bits, damp patches).
# T_Crops_*: trim sheet painted in UV space, same regions as build_farm.py (stalks, ears, leaves, cabbage outer/inner).
import bpy, numpy as np, os
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '2048'))
def vn(p, f, seed=0):
    q = p * f; i = np.floor(q).astype(np.int64); t = q - i; t = t * t * (3 - 2 * t)
    def h(dx, dy, dz):
        n = ((i[:, 0] + dx) * 73856093) ^ ((i[:, 1] + dy) * 19349663) ^ ((i[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float32) / 65535.0
    x0 = h(0, 0, 0) + (h(1, 0, 0) - h(0, 0, 0)) * t[:, 0]; x1 = h(0, 1, 0) + (h(1, 1, 0) - h(0, 1, 0)) * t[:, 0]
    x2 = h(0, 0, 1) + (h(1, 0, 1) - h(0, 0, 1)) * t[:, 0]; x3 = h(0, 1, 1) + (h(1, 1, 1) - h(0, 1, 1)) * t[:, 0]
    y0 = x0 + (x1 - x0) * t[:, 1]; y1 = x2 + (x3 - x2) * t[:, 1]; return y0 + (y1 - y0) * t[:, 2]
def fbm(p, f, oct=4, seed=0):
    s, a, tot = 0.0, 1.0, 0.0
    for k in range(oct): s = s + a * vn(p, f * 2 ** k, seed + k); tot += a; a *= 0.5
    return s / tot
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lin(*srgb): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in srgb], np.float32)
def mix(a, b, t): t = np.asarray(t, np.float32); return a + (b - a) * (t[:, None] if t.ndim else t)
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb.reshape(RES, RES, 3)
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
def normals(h, scale, name, wrap):
    H = h.reshape(RES, RES)
    if wrap: gx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) / 2; gy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) / 2
    else: gy, gx = np.gradient(H)
    n = np.stack([-gx * scale, -gy * scale, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    g = n * 0.5 + 0.5; save(name + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(name + '_N', g)
v_, u_ = np.meshgrid((np.arange(RES) + 0.5) / RES, (np.arange(RES) + 0.5) / RES, indexing='ij'); U = u_.ravel(); V = v_.ravel()
# ---- soil tile (2 m, seamless by blending four shifted copies) -----------------------------------------------------
def tile(fn):
    p = lambda du, dv: np.stack([(U + du) * 2.0, (V + dv) * 2.0, np.zeros_like(U)], 1)
    return fn(p(0, 0)) * (1 - U) * (1 - V) + fn(p(-1, 0)) * U * (1 - V) + fn(p(0, -1)) * (1 - U) * V + fn(p(-1, -1)) * U * V
big = tile(lambda p: fbm(p, 1.5, 3, 1)); clod = tile(lambda p: fbm(p, 14, 4, 2)); fine = tile(lambda p: fbm(p, 90, 3, 3))
peb = tile(lambda p: ss(0.86, 0.9, vn(p, 40, 4))); straw = tile(lambda p: ss(0.83, 0.88, vn(p * [1, 8, 1], 18, 5)))
damp = ss(0.45, 0.65, big)
h = 0.004 * ss(0.35, 0.75, clod) + 0.0008 * (fine - 0.5) + 0.002 * peb + 0.0008 * straw
col = mix(lin(104, 80, 60), lin(84, 64, 48), ss(0.3, 0.7, clod)) * (0.9 + 0.2 * fine)[:, None]
col = mix(col, lin(68, 52, 40), damp * 0.7)
col = mix(col, lin(138, 130, 118) * (0.85 + 0.3 * fine)[:, None], peb * 0.85)
col = mix(col, lin(150, 128, 86), straw * 0.45)
rg = 0.88 + 0.06 * (fine - 0.5) - 0.2 * damp - 0.1 * peb; ao = 0.75 + 0.25 * ss(0.2, 0.8, clod)
normals(h, RES / 2.0, 'T_FieldSoil', True)
save('T_FieldSoil_BC', to_srgb(col)); save('T_FieldSoil_ORM', np.stack([ao, np.clip(rg, 0.3, 0.97), np.zeros_like(rg)], 1))
# ---- crop trim sheet ---------------------------------------------------------------------------------------------------
P = np.stack([U * 8, V * 8, np.zeros_like(U)], 1); n1 = fbm(P, 4, 3, 10); n2 = fbm(P * [1, 0.08, 1], 30, 3, 11)   # n2: streaks along v
col = np.zeros((len(U), 3), np.float32); rg = np.full(len(U), 0.6, np.float32); h = np.zeros(len(U), np.float32); ao = np.ones(len(U), np.float32)
def region(u0, u1, v0=0.0, v1=1.0):
    m = (U >= u0) & (U < u1) & (V >= v0) & (V < v1); return m, (U - u0) / (u1 - u0), (V - v0) / (v1 - v0)
for reg, green in (((0.0, 0.125), True), ((0.125, 0.25), False)):            # stalks: v = root -> tip
    m, a, v = region(*reg); node = ss(0.985, 0.998, np.cos(v * 2 * np.pi * 4) * 0.5 + 0.5)
    c0, c1 = (lin(84, 112, 50), lin(120, 150, 70)) if green else (lin(150, 120, 66), lin(200, 174, 104))
    c = mix(c0, c1, v[m] ** 0.7) * (0.85 + 0.3 * n2[m])[:, None]; c = mix(c, c0 * 0.75, node[m] * 0.6)
    col[m] = c; rg[m] = 0.55 + 0.15 * n2[m] + (0 if green else 0.1); h[m] = 0.0004 * (np.sin(a[m] * np.pi * 6) * 0.5) + 0.0008 * node[m]
    ao[m] = 0.55 + 0.45 * ss(0.0, 0.5, v[m])
for reg, green in (((0.25, 0.375), True), ((0.375, 0.5), False)):            # ears: spikelets in rows
    m, a, v = region(*reg); sp = (np.sin(v * np.pi * 26) * 0.5 + 0.5) * (np.sin(a * np.pi * 8) * 0.5 + 0.5)
    c0, c1 = (lin(96, 126, 58), lin(134, 162, 84)) if green else (lin(170, 136, 74), lin(214, 186, 116))
    col[m] = mix(c0, c1, sp[m]) * (0.9 + 0.2 * n1[m])[:, None]; rg[m] = 0.5 + 0.2 * (1 - sp[m]) + 0.1 * (n1[m] - 0.5)
    h[m] = 0.0012 * sp[m]; ao[m] = 0.7 + 0.3 * sp[m]
for reg, green in (((0.5, 0.625), True), ((0.625, 0.75), False)):            # leaves: midrib at a = 0.5, parallel veins
    m, a, v = region(*reg); mid = ss(0.06, 0.0, np.abs(a - 0.5)); vein = ss(0.75, 1.0, np.cos(a * np.pi * 22) * 0.5 + 0.5)
    c0, c1 = (lin(62, 100, 40), lin(96, 134, 58)) if green else (lin(150, 128, 82), lin(186, 162, 108))
    c = mix(c0, c1, 0.5 * n2[m] + 0.5 * v[m]); c = mix(c, c1 * 1.15, mid[m] * 0.6); c = c * (1 - 0.08 * vein[m])[:, None]
    c = mix(c, lin(150, 124, 76), ss(0.82, 1.0, v[m]) * (0.6 if green else 0.2))   # dry tip
    col[m] = c; rg[m] = 0.5 + 0.12 * n2[m] + 0.1 * (not green); h[m] = 0.0006 * mid[m] + 0.0002 * vein[m]; ao[m] = 0.6 + 0.4 * ss(0.0, 0.4, v[m])
m, a, v = region(0.75, 1.0, 0.0, 0.5)                                         # cabbage wrapper leaves: base -> frilly edge
mid = ss(0.05, 0.0, np.abs(a - 0.5)); ang = np.abs(a - 0.5)
vein = ss(0.93, 1.0, np.cos((v * 5.0 - ang * 4.5) * 2 * np.pi) * 0.5 + 0.5) * ss(0.05, 0.3, ang)
c = mix(lin(78, 116, 88), lin(108, 144, 104), n1[m] * 0.6 + 0.4 * v[m]); c = mix(c, lin(182, 200, 164), np.clip(mid[m] * 0.8 + vein[m] * 0.6, 0, 1))
c = mix(c, lin(70, 98, 66), ss(0.85, 1.0, v[m]) * 0.5)
col[m] = c; rg[m] = 0.42 + 0.14 * n1[m] + 0.1 * ss(0.8, 1.0, v[m]); h[m] = 0.0015 * mid[m] + 0.0008 * vein[m] + 0.0006 * (fbm(P[m], 30, 3, 12) - 0.5)
ao[m] = 0.55 + 0.45 * ss(0.0, 0.5, v[m])
m, a, v = region(0.75, 1.0, 0.5, 1.0)                                         # cabbage head: pale, tight overlapping leaves
lap = np.sin(v * np.pi * 10 + np.sin(a * np.pi * 6) * 1.5) * 0.5 + 0.5; vein = ss(0.95, 1.0, np.cos((a * 9 + v * 3) * 2 * np.pi) * 0.5 + 0.5)
c = mix(lin(150, 178, 120), lin(186, 206, 150), lap[m] * 0.6 + 0.4 * n1[m]); c = mix(c, lin(206, 220, 180), vein[m] * 0.5)
col[m] = c; rg[m] = 0.4 + 0.12 * lap[m] + 0.06 * (n1[m] - 0.5); h[m] = 0.0012 * lap[m] + 0.0004 * vein[m]; ao[m] = 0.7 + 0.3 * lap[m]
normals(h, RES / 0.25, 'T_Crops', False)
save('T_Crops_BC', to_srgb(col)); save('T_Crops_ORM', np.stack([ao, np.clip(rg, 0.2, 0.95), np.zeros_like(rg)], 1))
print('PAINT OK', flush=True)
