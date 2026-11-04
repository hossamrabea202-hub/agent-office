# #502 medic look (checkking medic, 2026-11-04): white linen cape textures + herb-sprig emblem + physician's staff.
#   blender -b --factory-startup -P build_medic502.py -- <repo>
# Writes (all procedural numpy, no external assets):
#   assets/checkking/MedicCape/textures/  T_MedicCape_BC / _ORM / _N (_N_GL) / _Wear   1024^2 tileable bleached linen,
#                                         plain weave 64 threads per tile (12 cm tile, ~5.3 threads/cm homespun)
#                                         T_MedicEmblem_BCA / _ORM                    1024^2 herb sprig in green wool
#                                         satin stitch, alpha = thread, clamp border (projected in UE, not UV-mapped)
#   assets/checkking/MedicStaff/          SM_MedicStaff.fbx (pivot = grip centre, staff axis +Z), medic502_staff.blend
#                                         textures/T_MedicStaff_BC / _ORM / _N (_N_GL)  512x2048, ~1067 px/m
# Values (KB + INDUSTRY_SECRETS 1.1): bleached linen lin 0.56/0.54/0.47 (196 sRGB, never 255), cloth roughness 0.82-0.94;
# oiled hazel ~100 sRGB luminance, R 0.55-0.7; leather 66 sRGB; iron 0.55 metallic 1, rust 118/68/35 metallic 0 R 1.
import bpy, bmesh, os, sys, math, zlib, struct
import numpy as np

REPO = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.getcwd()
CAPE = os.path.join(REPO, 'assets', 'checkking', 'MedicCape', 'textures')
STAFF = os.path.join(REPO, 'assets', 'checkking', 'MedicStaff')
os.makedirs(CAPE, exist_ok=True); os.makedirs(os.path.join(STAFF, 'textures'), exist_ok=True)
rng = np.random.default_rng(502)


# ---------------------------------------------------------------- helpers
def save_png(path, a, bits=8):
    """a: float HxWxC (C 1/3/4) in 0..1, row 0 = BOTTOM (Blender / UV order). Written top-first, no colour management."""
    a = np.clip(a, 0, 1)
    if a.ndim == 2: a = a[..., None]
    h, w, c = a.shape; a = a[::-1]
    mx = 65535 if bits == 16 else 255
    q = np.round(a * mx).astype('>u2' if bits == 16 else 'u1')
    raw = b''.join(b'\x00' + q[y].tobytes() for y in range(h))
    ct = {1: 0, 3: 2, 4: 6}[c]
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, bits, ct, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    print('WROTE', path, flush=True)


def to_srgb(l): return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.clip(l, 0, None) ** (1 / 2.4) - 0.055)
def lin(r, g, b): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in (r, g, b)])
def smooth(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def tnoise(h, w, sy, sx, seed):
    """Periodic (tileable) gaussian-filtered noise, zero mean, unit std. sy/sx = blur sigma in pixels."""
    r = np.random.default_rng(seed); F = np.fft.fft2(r.normal(size=(h, w)))
    fy, fx = np.fft.fftfreq(h)[:, None], np.fft.fftfreq(w)[None, :]
    n = np.real(np.fft.ifft2(F * np.exp(-2 * math.pi ** 2 * ((sy * fy) ** 2 + (sx * fx) ** 2))))
    return (n - n.mean()) / (n.std() + 1e-9)


def fbm(h, w, s0, seed, octs=4):
    acc = np.zeros((h, w)); a = 1.0; t = 0.0
    for o in range(octs): acc += a * tnoise(h, w, s0 / 2 ** o, s0 / 2 ** o, seed + o); t += a; a *= 0.5
    return acc / t


def normal_from_height(hgt, k, wrap=True):
    """hgt row 0 = bottom (v up). Returns (DX, GL) normal maps 0..1. k = slope scale."""
    if wrap:
        dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5; dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(hgt)
    n = np.stack([-k * dx, -k * dy, np.ones_like(hgt)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    gl = n * 0.5 + 0.5; dxn = gl.copy(); dxn[..., 1] = 1 - dxn[..., 1]     # UE = DirectX (green down)
    return dxn, gl


# ---------------------------------------------------------------- 1. bleached linen (tileable)
N, P = 1024, 16                                   # 64 threads per 12 cm tile
y, x = np.mgrid[0:N, 0:N].astype(float)
i, j = (x // P).astype(int), (y // P).astype(int)
fx, fy = (x % P) / P, (y % P) / P
slub_w = tnoise(N, N, 38, 0.01, 11)[:, (i[0] * P + P // 2)]              # thickness along each warp thread
slub_f = tnoise(N, N, 0.01, 38, 12)[(j[:, 0] * P + P // 2), :]           # ... and each weft thread
pw = np.clip(np.cos(math.pi * (fx - 0.5) * (1.05 - 0.12 * slub_w)), 0, 1) ** 0.6
pf = np.clip(np.cos(math.pi * (fy - 0.5) * (1.05 - 0.12 * slub_f)), 0, 1) ** 0.6
sw = np.cos(math.pi * (y / P - 0.5) + math.pi * i); sf = -np.cos(math.pi * (x / P - 0.5) + math.pi * j)
hw = pw * (0.62 + 0.38 * sw) * (1 + 0.15 * slub_w); hf = pf * (0.62 + 0.38 * sf) * (1 + 0.15 * slub_f)
weave = np.maximum(hw, hf); weave = (weave - weave.min()) / (weave.max() - weave.min())
fibre = tnoise(N, N, 0.7, 0.7, 13)
hgt = weave + 0.06 * fibre
tv_w = rng.normal(size=N // P)[i]; tv_f = rng.normal(size=N // P)[j]
thread_var = np.where(hw >= hf, tv_w, tv_f)
mottle = fbm(N, N, 90, 14)                          # uneven crofting (sun bleaching), low frequency
base = np.array([0.56, 0.54, 0.47])
bc = base[None, None, :] * (1 + 0.035 * thread_var + 0.03 * mottle + 0.02 * slub_w * (hw >= hf))[..., None]
bc *= (0.94 + 0.06 * weave)[..., None]              # thinner fibre in the gaps (albedo, not shading)
save_png(os.path.join(CAPE, 'T_MedicCape_BC.png'), to_srgb(bc))
ao = 0.76 + 0.24 * weave
rough = np.clip(0.955 - 0.15 * weave + 0.06 * tnoise(N, N, 30, 30, 15) + 0.015 * tnoise(N, N, 3, 3, 18), 0.78, 0.97)   # thread crowns polish
save_png(os.path.join(CAPE, 'T_MedicCape_ORM.png'), np.stack([ao, rough, np.zeros_like(ao)], -1))
dxn, gl = normal_from_height(hgt, 2.4)
save_png(os.path.join(CAPE, 'T_MedicCape_N.png'), dxn, 16); save_png(os.path.join(CAPE, 'T_MedicCape_N_GL.png'), gl, 16)
br = fbm(N, N, 60, 16); br = (br - br.min()) / (br.max() - br.min())                       # R: breakup for dirt edges
sp = tnoise(N, N, 2.2, 2.2, 17); sp = smooth(1.2, 2.2, sp)                                   # G: mud splash speckle
save_png(os.path.join(CAPE, 'T_MedicCape_Wear.png'), np.stack([br, sp, np.zeros_like(br)], -1))

# ---------------------------------------------------------------- 2. herb-sprig emblem (embroidered, green wool)
E = 1024
ey, ex = np.mgrid[0:E, 0:E].astype(float); U, V = ex / E, ey / E               # V up (row 0 = bottom of the emblem)
def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay; t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(px - ax - t * vx, py - ay - t * vy), t
stem_pts = [(0.5 + 0.035 * math.sin(k * 0.55) - 0.012 * k / 10, 0.17 + 0.064 * k) for k in range(11)]   # gentle S
stem = np.full((E, E), 9.0); stem_t = np.zeros((E, E))
for a, b in zip(stem_pts[:-1], stem_pts[1:]):
    d, t = seg_dist(U, V, a[0], a[1], b[0], b[1]); m = d < stem; stem = np.where(m, d, stem)
stem_m = smooth(0.0135, 0.0105, stem)                 # stem stitch line ~ 2.4 % wide (7 mm on a 30 cm emblem)
leaf_m = np.zeros((E, E)); leaf_stitch = np.zeros((E, E))
for k in range(1, 10):                                # alternate lanceolate leaves (sage), smaller to the top
    sx_, sy_ = stem_pts[k]; side = 1 if k % 2 else -1; L = 0.17 - 0.011 * k; Wd = 0.42 * L
    ang = math.radians(48 - 2.5 * k); dx_, dy_ = side * math.sin(ang), math.cos(ang)     # leaf axis, up and out
    lx, ly = U - sx_, V - sy_
    along = lx * dx_ + ly * dy_; across = -lx * dy_ + ly * dx_
    t = along / L; prof = np.where((t > 0) & (t < 1), Wd * 0.5 * np.sin(math.pi * np.clip(t, 0, 1) ** 0.8) ** 0.9, -1)
    inside = smooth(0.003, -0.002, np.abs(across) - prof) * (t > 0) * (t < 1)
    leaf_m = np.maximum(leaf_m, inside)
    st = 0.5 + 0.5 * np.cos(2 * math.pi * (along * 0.6 + across * side) / 0.0075)           # satin stitch, slanted
    leaf_stitch = np.where(inside > 0.5, st, leaf_stitch)
    vein = smooth(0.0035, 0.0018, np.abs(across)) * (t > 0.05) * (t < 0.85)              # midrib in darker thread
    leaf_m = np.maximum(leaf_m, inside)
    leaf_stitch = np.where((inside > 0.5) & (vein > 0.5), 2.0, leaf_stitch)
top_bud = smooth(0.022, 0.017, np.hypot(U - stem_pts[-1][0], V - stem_pts[-1][1] - 0.012))
cut = smooth(0.012, 0.009, np.hypot(U - stem_pts[0][0], V - stem_pts[0][1]))           # cut end of the sprig
ring_r = np.hypot(U - 0.5, V - 0.5); ring = smooth(0.016, 0.011, np.abs(ring_r - 0.455))  # bordering ring
ring_st = 0.5 + 0.5 * np.cos(np.arctan2(V - 0.5, U - 0.5) * 260)                         # chain stitch beads
alpha = np.clip(np.maximum.reduce([stem_m, leaf_m, top_bud, cut, ring]), 0, 1)
alpha *= (np.minimum.reduce([U, V, 1 - U, 1 - V]) > 8 / E)                               # clamp border stays clear
green, dark = lin(62, 104, 54), lin(42, 74, 40)
thread = np.where((leaf_stitch == 2.0)[..., None], dark, green)
thread = np.where((stem_m > 0.5)[..., None] | (cut > 0.5)[..., None] | (ring > 0.5)[..., None], dark, thread)
stv = np.where(leaf_m > 0.5, np.where(leaf_stitch == 2.0, 0.5, leaf_stitch), np.where(ring > 0.5, ring_st, 0.5))
thread = thread * (0.92 + 0.16 * stv)[..., None]
linen_e = base[None, None, :] * (1 + 0.03 * fbm(E, E, 40, 21))[..., None]
ecol = linen_e * (1 - alpha[..., None]) + thread * alpha[..., None]
save_png(os.path.join(CAPE, 'T_MedicEmblem_BCA.png'), np.concatenate([to_srgb(ecol), alpha[..., None]], -1))
erough = np.clip(0.9 + 0.02 * tnoise(E, E, 4, 4, 22), 0, 1) * (1 - alpha) + (0.68 + 0.14 * (1 - stv)) * alpha
eao = 1 - 0.18 * alpha * (1 - stv)
save_png(os.path.join(CAPE, 'T_MedicEmblem_ORM.png'), np.stack([eao, erough, np.zeros_like(eao)], -1))

# ---------------------------------------------------------------- 3. physician's staff mesh
LS, ZG = 1.68, 1.02                                 # length (m), grip centre height from the ground
W0, W1 = 0.93, 1.11                                 # leather wrap
FH = 0.065                                          # iron ferrule height
SEG = 16
def radius(z):
    t = z / LS; r = 0.0170 + (0.0130 - 0.0170) * t
    r += 0.0075 * smooth(LS - 0.11, LS - 0.04, z) * (1 - smooth(LS - 0.025, LS, z) * 0.0)   # natural knob (root burl)
    for kz in (0.35, 0.62, 1.30, 1.48): r += 0.0018 * math.exp(-((z - kz) / 0.012) ** 2)
    return r
def centre(z): return (0.012 * math.sin(math.pi * z / LS) + 0.004 * math.sin(3.1 * math.pi * z / LS + 0.6),
                       0.006 * math.sin(2.0 * math.pi * z / LS + 1.1))
TW, TH = 512, 2048
def uvpx(px, py): return (px / TW, py / TH)

bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
def tube(rings, x0, x1, close_top=None):
    """rings: list of (z, r, vpx); U from x0..x1 px around, seam duplicated. close_top: (z, vpx) pole."""
    grid = []
    for z, r, vp in rings:
        cx, cy = centre(z); row = []
        for s in range(SEG + 1):
            a = 2 * math.pi * s / SEG; row.append((bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z - ZG)), x0 + (x1 - x0) * s / SEG, vp))
        grid.append(row)
    for a_, b_ in zip(grid[:-1], grid[1:]):
        for s in range(SEG):
            q = [a_[s], a_[s + 1], b_[s + 1], b_[s]]; f = bm.faces.new([e[0] for e in q])
            for lp, e in zip(f.loops, q): lp[uvl].uv = uvpx(e[1], e[2])
    if close_top:
        z, vp = close_top; cx, cy = centre(z); pole = bm.verts.new((cx, cy, z - ZG)); last = grid[-1]
        for s in range(SEG):
            f = bm.faces.new([last[s][0], last[s + 1][0], pole])
            for lp, (u_, v_) in zip(f.loops, [(last[s][1], last[s][2]), (last[s + 1][1], last[s][2]), ((last[s][1] + last[s + 1][1]) / 2, vp)]):
                lp[uvl].uv = uvpx(u_, v_)
    return grid
def disc(z, r, cxp, cyp, rp, down=True):
    cx, cy = centre(z); ctr = bm.verts.new((cx, cy, z - ZG)); ring = []
    for s in range(SEG):
        a = 2 * math.pi * s / SEG; ring.append((bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z - ZG)), cxp + rp * math.cos(a), cyp + rp * math.sin(a)))
    for s in range(SEG):
        q = [ring[(s + 1) % SEG], ring[s]] if down else [ring[s], ring[(s + 1) % SEG]]
        f = bm.faces.new([ctr, q[0][0], q[1][0]])
        for lp, (u_, v_) in zip(f.loops, [(cxp, cyp), (q[0][1], q[0][2]), (q[1][1], q[1][2])]): lp[uvl].uv = uvpx(u_, v_)

SH_V = 1792 / LS                                   # shaft px per metre along V
zs = list(np.linspace(0.02, LS - 0.012, 64)); dome = [LS - 0.012 + 0.012 * math.sin(math.pi / 2 * k / 6) for k in range(1, 6)]
shaft_rings = [(z, radius(z), z * SH_V) for z in zs] + [(z, radius(LS - 0.012) * math.cos(math.asin(min(1, (z - (LS - 0.012)) / 0.0125))), z * SH_V) for z in dome]
tube(shaft_rings, 0, 128, close_top=(LS, LS * SH_V))
rw = lambda z: radius(z) + 0.0028                                                         # wrap: 2 mm edge bevels
wrap = [(W0, radius(W0) + 0.0004, 0), (W0 + 0.002, rw(W0), 2)] + [(z, rw(z), (z - W0) / (W1 - W0) * 192) for z in np.linspace(W0 + 0.004, W1 - 0.004, 10)] + [(W1 - 0.002, rw(W1), 190), (W1, radius(W1) + 0.0004, 192)]
tube(wrap, 160, 288)
rf = radius(FH) + 0.0032                                                                  # ferrule: 3 mm bottom bevel
fer = [(0.0, rf - 0.003, 0), (0.003, rf, 3)] + [(z, rf - 0.0006 * z / FH, 3 + (z - 0.003) / (FH - 0.003) * 64) for z in np.linspace(0.006, FH - 0.002, 12)] + [(FH, rf - 0.0012, 69), (FH + 0.001, radius(FH) + 0.0003, 72)]
tube(fer, 320, 448)
disc(0.0, rf - 0.003, 384, 120, 32, down=True)
bm.normal_update()
me = bpy.data.meshes.new('SM_MedicStaff'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
try: me.set_sharp_from_angle(angle=math.radians(40))
except Exception: pass
ob = bpy.data.objects.new('SM_MedicStaff', me); bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('MI_MedicStaff'); me.materials.append(mat)
print('STAFF tris', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)

# ---------------------------------------------------------------- 4. staff textures (512 x 2048, row 0 = V 0 = ground end)
BC = np.zeros((TH, TW, 3)); ORM = np.zeros((TH, TW, 3)); ORM[..., 0] = 1; HG = np.zeros((TH, TW))
wood = np.array([0.20, 0.115, 0.055])
# shaft: x 0..128, y 0..1792 (+ dome to 1792*LS/LS)
sh = slice(0, 1800), slice(0, 128); H_, W_ = 1800, 128
zz = (np.arange(H_)[:, None] / SH_V) * np.ones((1, W_)); uu = np.ones((H_, 1)) * (np.arange(W_)[None, :] / W_)
grain = tnoise(H_, W_, 55, 1.2, 31); grain2 = tnoise(H_, W_, 14, 2.5, 32)
col = wood * (1 + 0.14 * grain + 0.06 * grain2)[..., None]
rgh = 0.62 + 0.05 * grain + 0.03 * tnoise(H_, W_, 4, 4, 33); hh = 0.35 * grain + 0.25 * grain2
for kz, ku in zip((0.35, 0.62, 1.30, 1.48), rng.random(4)):
    du = np.minimum(np.abs(uu - ku), 1 - np.abs(uu - ku)) * 0.10; dz = zz - kz
    kd = np.hypot(du / 0.007, dz / 0.011)
    col *= (1 - 0.45 * smooth(1.0, 0.3, kd) + 0.08 * smooth(1.4, 1.0, kd) * smooth(0.9, 1.0, kd))[..., None]
    rgh = np.where(kd < 1, 0.55, rgh); hh += 1.4 * smooth(1.2, 0.0, kd) - 0.6 * smooth(0.45, 0.0, kd)
grip = smooth(0.80, 0.90, zz) * (1 - smooth(1.15, 1.25, zz))                     # hand oil above / below the wrap
col *= (1 - 0.15 * grip)[..., None]; rgh = rgh * (1 - grip) + 0.42 * grip
bleach = smooth(LS - 0.10, LS - 0.01, zz)                                        # top of the knob takes the sun
col = col * (1 - 0.22 * bleach[..., None]) + np.array([0.22, 0.19, 0.15]) * 0.22 * bleach[..., None]
soilm = smooth(0.32, 0.08, zz) * smooth(0.2, 0.75, (0.5 + 0.5 * tnoise(H_, W_, 6, 3, 34)) * (1.2 - zz / 0.32))
soil = np.array([0.17, 0.14, 0.10])
col = col * (1 - soilm[..., None]) + soil * soilm[..., None]; rgh = rgh * (1 - soilm) + 0.9 * soilm
ao = 1 - 0.22 * (smooth(FH + 0.02, FH, zz) + smooth(W0 - 0.015, W0, zz) * (1 - smooth(W1, W1 + 0.015, zz)))
BC[sh] = col; ORM[sh][..., 0] = np.clip(ao, 0.6, 1); ORM[sh][..., 1] = rgh; HG[sh] = hh * 0.4
# leather wrap: x 160..288, y 0..192 (+ cap strip)
wy, wx = np.mgrid[0:192, 0:128].astype(float); zl = wy / 192 * (W1 - W0); ul = wx / 128
phase = zl / 0.026 - ul * 1.0                                                     # one helix turn per 2.6 cm strip
fr = phase - np.floor(phase); step = fr ** 0.6                                    # overlapping strip edge
pore = tnoise(192, 128, 0.8, 0.8, 41); lea = np.array([0.085, 0.05, 0.03])
mid = np.exp(-((zl - (W1 - W0) / 2) / 0.05) ** 2)                                # palm contact in the middle
lc = lea * (1 + 0.10 * pore - 0.10 * mid + 0.05 * tnoise(192, 128, 10, 10, 42))[..., None]
BC[0:192, 160:288] = lc; ORM[0:192, 160:288, 0] = 0.8 + 0.2 * smooth(0, 0.12, fr)
ORM[0:192, 160:288, 1] = 0.64 - 0.18 * mid + 0.04 * pore; HG[0:192, 160:288] = 1.6 * step + 0.1 * pore
BC[196:220, 160:288] = lea; ORM[196:220, 160:288, 1] = 0.62
# iron ferrule: x 320..448, y 0..72 ; bottom disc centre (384,120) r 32
fy_, fx_ = np.mgrid[0:160, 320:448].astype(float)
dent = fbm(160, 128, 3, 51); rustn = fbm(160, 128, 8, 52) + 0.6 * smooth(40, 72, fy_)             # rust near the lip
disc_d = np.hypot(fx_ - 384, fy_ - 120); on_disc = disc_d < 34
mud = np.where(on_disc, smooth(0.05, -0.4, tnoise(160, 128, 2, 2, 53)) * smooth(30, 18, disc_d), smooth(14, 2, fy_) * smooth(-0.3, 0.4, tnoise(160, 128, 3, 3, 54)))
rust = smooth(0.62, 0.72, rustn) * (1 - mud)                                          # small rust spots, mostly at the lip
# bare iron only where it is scraped: the bottom bevel / disc rim hits the ground, raised hammer marks get rubbed;
# everywhere else a thin dark oxide + grime film (non-metal), as on handled old iron
scrape = np.maximum(smooth(6, 2, fy_) * (~on_disc), smooth(26, 32, disc_d) * on_disc)
scrape = np.maximum(scrape, smooth(0.55, 0.9, dent) * 0.9)
film = (1 - scrape) * (1 - rust) * (1 - mud)
iron, rustc, mudc, filmc = np.array([0.55, 0.55, 0.55]), lin(118, 68, 35), np.array([0.09, 0.075, 0.055]), lin(74, 66, 58)
c = iron[None, None] * (1 - 0.05 * dent[..., None])
fm = (film > 0.5).astype(float); rm = (rust > 0.5).astype(float) * (1 - fm); mm = (mud > 0.5).astype(float)
c = c * (1 - fm[..., None]) + filmc * (1 + 0.08 * dent[..., None]) * fm[..., None]
c = c * (1 - rm[..., None]) + rustc * rm[..., None]; c = c * (1 - mm[..., None]) + mudc * mm[..., None]
metal = (1 - fm) * (1 - rm) * (1 - mm)
r_ = (0.34 + 0.08 * dent) * metal + (0.72 + 0.06 * dent) * fm * (1 - mm) + 1.0 * rm * (1 - mm) + 0.95 * mm
BC[0:160, 320:448] = c; ORM[0:160, 320:448, 1] = np.clip(r_, 0, 1); ORM[0:160, 320:448, 2] = metal
ORM[0:160, 320:448, 0] = 1 - 0.25 * rust * smooth(50, 72, fy_); HG[0:160, 320:448] = 0.8 * dent - 0.6 * rust
# gutters (unused texels): dilate neighbour colours a few px so mips don't bleed black
for _ in range(6):
    empty = BC.max(-1) < 1e-4
    if not empty.any(): break
    full = (~empty).astype(float)[..., None]; cnt = sum(np.roll(full, s, a) for s, a in ((1, 0), (-1, 0), (1, 1), (-1, 1)))
    grow = empty & (cnt[..., 0] > 0)
    for arr in (BC, ORM):                                       # average only filled neighbours (no dark rim)
        nb = sum(np.roll(arr * full, s, a) for s, a in ((1, 0), (-1, 0), (1, 1), (-1, 1))) / np.maximum(cnt, 1)
        arr[grow] = nb[grow]
still = BC.max(-1) < 1e-4; BC[still] = wood; ORM[still] = (1, 0.65, 0)
save_png(os.path.join(STAFF, 'textures', 'T_MedicStaff_BC.png'), to_srgb(BC))
save_png(os.path.join(STAFF, 'textures', 'T_MedicStaff_ORM.png'), ORM)
dxn, gl = normal_from_height(HG, 1.6, wrap=False)
save_png(os.path.join(STAFF, 'textures', 'T_MedicStaff_N.png'), dxn, 16); save_png(os.path.join(STAFF, 'textures', 'T_MedicStaff_N_GL.png'), gl, 16)

# ---------------------------------------------------------------- 5. export
for o in bpy.context.scene.objects: o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=os.path.join(STAFF, 'SM_MedicStaff.fbx'), use_selection=True, object_types={'MESH'},
                         mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, bake_anim=False, apply_scale_options='FBX_SCALE_UNITS')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(STAFF, 'medic502_staff.blend'))
print('BUILD502 OK', flush=True)
