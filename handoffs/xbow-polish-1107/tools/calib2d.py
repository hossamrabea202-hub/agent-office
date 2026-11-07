# #561 crossbow polish, pass 1 (texture space, no mesh needed). checkking (Claude), 2026-11-07.
#   blender -b --factory-startup -P calib2d.py -- <BaseColor.png> <ORM.png> <out_dir> [size=2048] [prefix=T_Crossbow561]
# Keeps the artist's design (layout, grain, engraving, inlay pattern) and rebuilds the values physically:
#   classes  : steel, brass, dark stock wood, light wood, bone/antler inlay, other (from BaseColor hue/sat + metallic)
#   values   : calibrated albedo (knowledge base §1.1), metallic strictly 0/1 (in-between only on the oxide/patina edge)
#   wear     : physical order: base -> grain -> edges (UV-island border = hard edge, rubbed bright) -> cavities (baked AO:
#              oxide on steel, patina on brass, grime in wood pores) -> 3-scale roughness, never flat
# Output: <prefix>_BaseColor.png (sRGB), <prefix>_ORM.png (R=AO G=Rough B=Metal, linear). Same UVs as the original.
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
BC, ORM, OUT = a[0], a[1], a[2]
SIZE = int(a[3]) if len(a) > 3 else 2048
PFX = a[4] if len(a) > 4 else 'T_Crossbow561'
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(561)

def load(p, n):
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'Non-Color'
    w, h = im.size
    if w != n: im.scale(n, n)
    x = np.empty(n * n * 4, np.float32); im.pixels.foreach_get(x); bpy.data.images.remove(im)
    return x.reshape(n, n, 4)[..., :3].copy()
def save(arr, path):
    n = arr.shape[0]; im = bpy.data.images.new(os.path.basename(path), n, n, alpha=False, float_buffer=False)
    im.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((n, n, 4), np.float32); rgba[..., :3] = np.clip(arr, 0, 1)
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

to_lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
to_srgb = lambda c: np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
sstep = lambda e0, e1, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - e0) / (e1 - e0), 0, 1))
def noise(n, cells, octaves=3):          # value noise, several octaves, 0..1
    out = np.zeros((n, n), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = int(cells * 2 ** o); g = rng.random((c + 1, c + 1)).astype(np.float32)
        t = np.linspace(0, c, n, endpoint=False); i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
        a0 = g[i][:, i] * (1 - f)[None, :] + g[i][:, i + 1] * f[None, :]
        a1 = g[i + 1][:, i] * (1 - f)[None, :] + g[i + 1][:, i + 1] * f[None, :]
        out += amp * (a0 * (1 - f)[:, None] + a1 * f[:, None]); tot += amp; amp *= 0.5
    return out / tot
def blur(x, r):                           # box blur, radius r px, 2 passes (about gaussian)
    k = 2 * r + 1
    for _ in range(2):
        for ax in (0, 1):
            p = np.pad(x, [(r + 1, r) if i == ax else (0, 0) for i in (0, 1)], mode='edge').cumsum(ax)
            x = (np.take(p, range(k, p.shape[ax]), ax) - np.take(p, range(0, p.shape[ax] - k), ax)) / k
    return x.astype(np.float32)

src_bc = load(BC, SIZE); orm = load(ORM, SIZE)
AO, R0, M0 = orm[..., 0], orm[..., 1], orm[..., 2]
lin = to_lin(src_bc)
Y = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
mx, mn = src_bc.max(-1), src_bc.min(-1); sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
r, g, b = src_bc[..., 0], src_bc[..., 1], src_bc[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
used = (src_bc.max(-1) > 0.002) | (orm.max(-1) > 0.002)

# ---- classes (soft) ----
metal = sstep(0.4, 0.6, M0)
warm = sstep(18, 24, hue) * (1 - sstep(60, 70, hue))
brass = metal * warm * sstep(0.25, 0.40, sat)
steel = metal * (1 - brass)
nonm = 1 - metal
bone = nonm * warm * (1 - sstep(0.30, 0.40, sat)) * sstep(0.30, 0.42, Y)
redw = nonm * (1 - sstep(16, 22, hue) * (1 - sstep(330, 340, hue))) * sstep(0.3, 0.5, sat)   # hue < ~20 or > 340
lightw = nonm * warm * (1 - bone) * sstep(0.30, 0.42, sat)
other = np.clip(nonm - bone - redw - lightw, 0, 1)

# ---- shared wear masks ----
inside = used.astype(np.float32)
# distance to the UV-island border in px (hard-surface islands end at hard edges): erosion by shifts
d = np.zeros_like(inside); cur = inside.copy(); EDGE = max(2, SIZE // 512)   # 4 px at 2K = ~2-3 mm on a 0.8 m crossbow
for k in range(1, EDGE * 2 + 1):
    nb = cur.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): nb = np.minimum(nb, np.roll(np.roll(cur, dy, 0), dx, 1))
    d += nb; cur = nb
edge = inside * (1 - np.clip(d / (EDGE * 2), 0, 1))                       # 1 at the border, 0 inside
n_lo, n_mid, n_hi = noise(SIZE, 6), noise(SIZE, 24), noise(SIZE, 96, 2)
edge = edge * sstep(0.35, 0.65, n_mid * 0.7 + n_hi * 0.3)                # broken up: wear is never a clean line
cav = sstep(0.88, 0.45, AO)                                               # baked AO -> cavity (grime, oxide, patina)
grain = np.clip(Y / np.maximum(blur(np.where(used, Y, 0), 12) / np.maximum(blur(inside, 12), 1e-3), 1e-4), 0.4, 2.0)  # local contrast = the painted grain
# fine scratches for metal roughness: thin streaks along one UV axis + random direction cells
scr = sstep(0.82, 0.97, noise(SIZE, 160, 1) * 0.6 + noise(SIZE, 40, 1) * 0.4) * sstep(0.55, 0.9, n_mid)

col = np.zeros_like(lin); rough = np.zeros_like(Y); met = np.zeros_like(Y)
def add(mask, c, rgh, mt):
    global col, rough, met
    col += mask[..., None] * c; rough += mask * rgh; met += mask * mt

# STEEL: bare worn iron 0.50-0.56 linear (~190 sRGB), faint blue-grey from the design. Dark look = oxide film (non-metal),
# in cavities and in patches, rubbed back to bare metal at the edges.
st_c = np.array([0.50, 0.515, 0.53], np.float32)[None, None] * (0.94 + 0.12 * n_mid)[..., None]
ox = np.clip(cav * 1.1 + sstep(0.40, 0.60, n_lo) * 0.55 + 0.25 * n_mid - edge * 1.6, 0, 1); oxm = sstep(0.45, 0.6, ox)
ox_c = np.array([0.042, 0.039, 0.036], np.float32)[None, None] * (0.85 + 0.3 * n_hi)[..., None]
st_col = st_c * (1 - oxm[..., None]) + ox_c * oxm[..., None]
st_r = np.clip(0.30 + 0.10 * (n_mid - 0.5) + 0.10 * scr - 0.10 * edge, 0.16, 0.5) * (1 - oxm) + (0.72 + 0.1 * n_hi) * oxm
add(steel, st_col, st_r, 1 - oxm)

# BRASS fittings and rivets: aged brass ~(0.72,0.54,0.27) linear; dark brown tarnish/patina in cavities (non-metal),
# polished bright where it gets rubbed (edges).
br_c = np.array([0.72, 0.54, 0.27], np.float32)[None, None] * (0.92 + 0.12 * n_mid + 0.08 * edge)[..., None]
pt = sstep(0.5, 0.65, np.clip(cav * 1.2 - edge, 0, 1)); pt_c = np.array([0.075, 0.055, 0.032], np.float32)[None, None]
add(brass, br_c * (1 - pt[..., None]) + pt_c * pt[..., None], (0.36 + 0.08 * (n_mid - 0.5) - 0.12 * edge) * (1 - pt) + 0.75 * pt, 1 - pt)

# DARK STOCK WOOD: the design's near-black red (22 sRGB, 88 % sat) becomes oiled red walnut, ~70 sRGB, ~60 % sat.
# Grain kept as relative brightness; edges rubbed lighter (finish worn through), cavities grimed.
wd = np.array([0.105, 0.048, 0.026], np.float32)[None, None]
gk = grain ** 0.75
wd_col = wd * gk[..., None] * (1 + 0.35 * edge)[..., None] * (1 - 0.35 * cav)[..., None] * (0.92 + 0.16 * n_lo)[..., None]
wd_r = np.clip(0.52 + 0.12 * (1 - np.clip(gk, 0, 1.3) / 1.3) + 0.06 * (n_mid - 0.5) - 0.10 * edge + 0.12 * cav, 0.35, 0.85)
add(redw, wd_col, wd_r, 0)

# LIGHT WOOD (maple/ash parts): keep the design colour, cap saturation at 50 %, same wear logic, drier finish
lw = lin * 1.0
lwY = (lw @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
lw = lwY + (lw - lwY) * 0.85
lw_col = lw * (1 + 0.25 * edge)[..., None] * (1 - 0.35 * cav)[..., None]
add(lightw, lw_col, np.clip(0.62 + 0.1 * (n_mid - 0.5) - 0.08 * edge + 0.12 * cav, 0.4, 0.9), 0)

# BONE / ANTLER INLAY: measured bone 0.79,0.79,0.66; aged staghorn is warmer and a bit darker. Keep the engraving.
bn = lin * 0.95 + np.array([0.02, 0.0, -0.02], np.float32)[None, None]
add(bone, bn * (1 - 0.4 * cav)[..., None], np.clip(0.48 + 0.08 * (n_mid - 0.5) + 0.15 * cav - 0.06 * edge, 0.3, 0.8), 0)

# OTHER non-metal (string, cord, small bits): keep, lift to the 30 sRGB floor (0.013 linear), roughness from the design
add(other, np.maximum(lin, 0.016), np.clip(np.maximum(R0, 0.55) + 0.08 * (n_mid - 0.5), 0.4, 0.95), 0)

# ---- clamp to the calibrated ranges and write ----
# non-metal floor 30 sRGB / ceiling 240 sRGB (by luminance), metal floor 180 sRGB
cY = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
is_m = met > 0.5
lo = np.where(is_m, 0.456, 0.0130); hi = np.where(is_m, 0.95, 0.871)
scale = np.where(cY < lo, lo / np.maximum(cY, 1e-5), np.where(cY > hi, hi / np.maximum(cY, 1e-5), 1.0))
col = col * scale[..., None]
met = np.where(met > 0.9, 1.0, np.where(met < 0.1, 0.0, met))           # strictly 0/1 except the thin oxide/patina edge
pad = ~used
out_bc = to_srgb(col); out_bc[pad] = 0
out_orm = np.stack([AO, np.clip(rough, 0.05, 1), met], -1); out_orm[pad] = 0
save(out_bc, os.path.join(OUT, PFX + '_BaseColor.png'))
save(out_orm, os.path.join(OUT, PFX + '_ORM.png'))
for k, m in (('steel', steel), ('brass', brass), ('redwood', redw), ('lightwood', lightw), ('bone', bone), ('other', other)):
    print('CLASS %-9s %5.1f%%' % (k, (m[used] > 0.5).mean() * 100))
print('CALIB561 DONE', OUT)
