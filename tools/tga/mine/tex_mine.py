# Tileable mine texture sets (#309, TGA): blender -b --factory-startup -P tex_mine.py   (env WORK)
# Each set is a seamless heightfield "high poly" patch (periodic noise, so it tiles) baked to BC / ORM / N (DirectX):
#   T_MineRock 2K (fire-set mine rock: smooth, rounded, spalled flakes; KB: wet dark rock albedo 0.1-0.3 linear),
#   T_MineOak 1K (old oak, grain along U, splits), T_MineIron 1K (wrought iron, rust patches: metal 0 where rusted),
#   T_MineOre 1K (rock with brassy chalcopyrite / iron-ore veins: metallic glints for #201).
import bpy, numpy as np, os
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
def pn(R, f, seed, sx=1.0, sy=1.0):
    """periodic value noise on an RxR tile, f cells across (integer -> seamless)"""
    fx, fy = max(1, int(round(f * sx))), max(1, int(round(f * sy)))
    g = np.random.default_rng(seed).random((fy, fx))
    y, x = np.meshgrid(np.arange(R) * fy / R, np.arange(R) * fx / R, indexing='ij')
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); tx, ty = x - x0, y - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty); x1, y1 = (x0 + 1) % fx, (y0 + 1) % fy
    a = g[y0, x0] + (g[y0, x1] - g[y0, x0]) * tx; b = g[y1, x0] + (g[y1, x1] - g[y1, x0]) * tx
    return a + (b - a) * ty
def fbm(R, f, oct, seed, sx=1.0, sy=1.0):
    s, a, t = 0.0, 1.0, 0.0
    for k in range(oct): s = s + a * pn(R, f * 2 ** k, seed + k, sx, sy); t += a; a *= 0.5
    return s / t
def ridged(R, f, oct, seed): return 1 - np.abs(2 * fbm(R, f, oct, seed) - 1)
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
def lin(*c): return np.array([((x / 255 + 0.055) / 1.055) ** 2.4 for x in c], np.float32)
def mix(a, b, t): return a + (b - a) * np.asarray(t, np.float32)[..., None]
def save(name, rgb):
    R = rgb.shape[0]; im = bpy.data.images.new(name, R, R, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((R, R, 4), np.float32); a[..., :3] = rgb; im.pixels.foreach_set(np.clip(a, 0, 1).ravel())
    im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
def normal(h, tile_m):
    R = h.shape[0]; px = tile_m / R
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * px); gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * px)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True); n = n * 0.5 + 0.5
    n[..., 1] = 1 - n[..., 1]; return n                                              # DirectX
def cavity(h, r=6):
    b = h.copy()
    for ax in (0, 1):
        b = sum(np.roll(b, k, ax) for k in range(-r, r + 1)) / (2 * r + 1)
    return h - b
def out(name, col, rough, metal, h, tile_m, ao_k):
    cv = cavity(h); ao = np.clip(1 + cv / ao_k, 0.35, 1)
    save(name + '_BC', srgb(col)); save(name + '_ORM', np.stack([ao, np.clip(rough, 0.05, 1), metal], -1)); save(name + '_N', normal(h, tile_m))

# ---- rock 2K, 2 m tile ----
R = 2048
facets = ridged(R, 5, 3, 1); big = fbm(R, 3, 4, 2); fine = fbm(R, 48, 3, 3); grit = pn(R, 400, 4)
spall = np.floor(fbm(R, 6, 3, 5) * 6) / 6                                                     # fire-set spalled flakes (no pick marks)
h = 0.008 * big + 0.002 * facets + 0.0025 * spall + 0.002 * fine + 0.0006 * grit   # big shapes live in the mesh
col = mix(lin(92, 86, 78), lin(108, 100, 92), big) * (0.88 + 0.24 * fine)[..., None]          # ~0.08-0.16 linear, KB dark rock
col = mix(col, lin(112, 98, 78), ss(0.62, 0.9, fbm(R, 8, 3, 7)) * 0.25)                    # ochre iron staining
col = mix(col, lin(150, 146, 136), ss(0.85, 0.95, facets) * 0.1)                             # pale spalled edges
rough = 0.82 + 0.08 * (fine - 0.5) - 0.12 * ss(0.82, 0.9, facets)
out('T_MineRock', col, rough, np.zeros_like(h), h, 2.0, 0.012)
# ---- oak 1K, 1 m tile, grain along U ----
R = 1024
grain = fbm(R, 3, 4, 20, sx=0.25, sy=12); rings = np.sin(2 * np.pi * (fbm(R, 2, 3, 21, 0.3, 3) * 9)); fine = fbm(R, 60, 2, 22, 0.3, 4)
split = ss(0.985, 0.995, fbm(R, 2, 3, 23, 0.2, 10)) * ss(0.4, 0.6, fbm(R, 3, 2, 24))
h = 0.002 * grain + 0.0008 * rings + 0.0004 * fine - 0.003 * split
col = mix(lin(64, 50, 36), lin(96, 78, 56), grain) * (0.9 + 0.12 * rings)[..., None]
col = mix(col, lin(40, 34, 28), split * 0.8); col = mix(col, lin(70, 68, 62), ss(0.6, 0.8, fbm(R, 4, 3, 25)) * 0.3)   # grey weathering
rough = 0.6 + 0.28 * ss(0.38, 0.62, fbm(R, 5, 3, 26)) + 0.06 * (grain - 0.5) + 0.1 * split           # polished by hands / dry patches
out('T_MineOak', col, rough, np.zeros_like(h), h, 1.0, 0.002)
# ---- wrought iron 1K, 1 m tile ----
rust = ss(0.5, 0.65, fbm(R, 5, 4, 30)); pit = ss(0.75, 0.85, pn(R, 180, 31)) * rust; fine = fbm(R, 40, 3, 32)
h = 0.0015 * rust + 0.0006 * fine - 0.0008 * pit
rust = ss(0.4, 0.46, rust)                                                                   # crisp rust edge: metal 0 or 1
col = mix(lin(192, 188, 182) * (0.92 + 0.1 * fine)[..., None], mix(lin(104, 56, 30), lin(70, 40, 26), fbm(R, 20, 2, 33)), rust)
rough = 0.45 + 0.15 * fine + 0.45 * rust; metal = 1 - rust
out('T_MineIron', col, rough, metal, h, 1.0, 0.002)
# ---- ore 1K, 1 m tile: rock with metallic veins ----
big = fbm(R, 3, 4, 40); facets = ridged(R, 6, 3, 41); fine = fbm(R, 50, 3, 42)
vein = ss(0.06, 0.0, np.abs(fbm(R, 3, 4, 43) - 0.5)) ; spark = vein * ss(0.6, 0.8, pn(R, 120, 44))
h = 0.012 * big + 0.008 * facets + 0.003 * vein + 0.002 * fine
col = mix(lin(84, 78, 72), lin(112, 104, 96), big) * (0.85 + 0.3 * fine)[..., None]
col = mix(col, lin(98, 64, 46), ss(0.6, 0.8, fbm(R, 6, 3, 45)) * 0.5)                      # haematite red-brown
vein = ss(0.45, 0.55, vein)
col = mix(col, lin(216, 186, 112), vein)                                                     # brassy chalcopyrite (metal)
rough = np.where(vein > 0.5, 0.3 - 0.1 * spark, 0.8 + 0.08 * (fine - 0.5)); metal = vein
out('T_MineOre', col, rough, metal, h, 1.0, 0.006)
print('TEX OK mine', flush=True)
