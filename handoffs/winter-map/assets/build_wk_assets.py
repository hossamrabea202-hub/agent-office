"""WinterKeep #390: real winter assets for UE, built procedurally in Blender 4.5 (meshes + calibrated textures).

blender -b --factory-startup -P build_wk_assets.py -- [--tex 1024] [--only tex|mesh] [--no-fbx]
Writes (all under assets/out/):
  tex/T_WK_<Name>_BC.png (sRGB 8-bit), _ORM.png (AO, roughness, metallic=0; linear 8-bit), _N.png (OpenGL, 16-bit:
      UE import sets flip_green_channel) -> run pbr_check on every BC/ORM pair
  fbx/SM_WK_*.fbx       metres -> cm, axis_forward -Y, up Z (Blender X = UE X, Blender Y = -UE Y), pivot at the base
  wk_assets.blend       the same meshes + Cycles lookdev materials (render_winterkeep.py appends from it)
  props.json            UE transforms for the bridge, the frozen falls and the 3 farmsteads, computed from the heightmap
Values (linear albedo): snow 0.80-0.86, needles ~0.05, spruce bark ~0.10, birch bark ~0.48, granite ashlar ~0.20,
weathered logs ~0.13, scoured rock ~0.07, frozen-falls ice 0.10-0.60 (clear vs bubbly). Never 1.0 white.
"""
import bpy, bmesh, json, math, os, struct, sys, zlib
import numpy as np
from mathutils import Vector, geometry

A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d): return A[A.index(k) + 1] if k in A else d
TEX, ONLY = int(arg('--tex', '1024')), arg('--only', 'all')
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out'); TER = os.path.join(HERE, '..', 'terrain', 'out')
for d in ('tex', 'fbx'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
TAU = 2 * math.pi

# ================================================================== texture helpers (tileable, numpy)
def vnoise(n, cx, cy, seed, octv=5, gain=0.5):
    r = np.random.default_rng(seed); tot = np.zeros((n, n), np.float32); amp, nm = 1.0, 0.0
    for o in range(octv):
        kx, ky = cx * 2 ** o, cy * 2 ** o; lat = r.uniform(-1, 1, (ky, kx)).astype(np.float32)
        u = np.arange(n) * kx / n; i = u.astype(int); fx = u - i; fx = fx * fx * (3 - 2 * fx)
        v = np.arange(n) * ky / n; j = v.astype(int); fy = v - j; fy = fy * fy * (3 - 2 * fy)
        i1, j1 = (i + 1) % kx, (j + 1) % ky; fx, fy = fx[None, :], fy[:, None]
        a, b, c, d = lat[np.ix_(j, i)], lat[np.ix_(j, i1)], lat[np.ix_(j1, i)], lat[np.ix_(j1, i1)]
        tot += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy); nm += amp; amp *= gain
    t = tot / nm; return (t - t.mean()) / (t.std() + 1e-6)          # zero mean, unit std
def voronoi(n, cx, cy, seed):
    r = np.random.default_rng(seed); pts = r.uniform(0, 1, (cy, cx, 2)).astype(np.float32)
    v, u = np.mgrid[0:n, 0:n].astype(np.float32); gu, gv = u * cx / n, v * cy / n; iu, iv = gu.astype(int), gv.astype(int)
    f1 = np.full((n, n), 9.0, np.float32); f2 = f1.copy(); cid = np.zeros((n, n), np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ju, jv = iu + dx, iv + dy; p = pts[jv % cy, ju % cx]
            dd = np.hypot(ju + p[..., 0] - gu, jv + p[..., 1] - gv); idx = (jv % cy) * cx + (ju % cx)
            c = dd < f1; f2 = np.where(c, f1, np.minimum(f2, dd)); cid = np.where(c, idx, cid); f1 = np.where(c, dd, f1)
    return f1, f2, cid
def gblur(a, s):
    n = a.shape[0]; k = np.fft.fftfreq(n); K = k[:, None] ** 2 + k[None, :] ** 2
    return np.real(np.fft.ifft2(np.fft.fft2(a) * np.exp(-2 * (math.pi * s) ** 2 * K))).astype(np.float32)
def sstep(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)
def png(path, arr, bits=8):
    arr = np.clip(np.asarray(arr, np.float64), 0, 1); hh, ww = arr.shape[:2]; ch = 1 if arr.ndim == 2 else arr.shape[2]
    data = (arr * 65535 + 0.5).astype('>u2') if bits == 16 else (arr * 255 + 0.5).astype(np.uint8)
    data = data.reshape(hh, -1); raw = b''.join(b'\x00' + data[y].tobytes() for y in range(hh))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', ww, hh, bits, {1: 0, 3: 2, 4: 6}[ch], 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
def cavity_ao(h, s, k):
    return np.clip(1 - np.clip((gblur(h, s) - h) * k, 0, 0.65), 0.35, 1)
def save_set(name, bc, rough, h, nstr, ao_k=4.0, ao_s=None):
    """bc linear RGB, rough 0..1, h height (texture-tile units, any scale) -> BC/ORM/N pngs. Image row 0 = top."""
    n = h.shape[0]; ao = cavity_ao(h, ao_s or n / 256, ao_k)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * nstr; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * nstr
    nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
    nrm = np.dstack([-gx * nz * 0.5 + 0.5, gy * nz * 0.5 + 0.5, nz * 0.5 + 0.5])     # OpenGL (+G up in UV space)
    base = os.path.join(OUT, 'tex', 'T_WK_' + name)
    png(base + '_BC.png', srgb(bc * ao[..., None] ** 0.0)); png(base + '_N.png', nrm, 16)  # no AO baked into BC (rule 1)
    png(base + '_ORM.png', np.dstack([ao, np.clip(rough, 0.03, 1), np.zeros_like(ao)]))
    print('tex', name, 'albedo mean %.3f' % float(bc.mean()), 'rough mean %.2f' % float(rough.mean()))
def mix(a, b, t): t = np.asarray(t)[..., None] if np.ndim(t) == 2 else t; return a * (1 - t) + b * t
def col(rgb, n): return np.broadcast_to(np.array(rgb, np.float32), (n, n, 3)).copy()

def textures(n):
    # --- spruce bark: thin round scales, grey-brown, a few lichen flecks (1 m x 1 m tile, u around the trunk)
    f1, f2, cid = voronoi(n, 14, 9, 11); tone = np.random.default_rng(1).uniform(0, 1, 14 * 9)[cid]
    edge = sstep(0.0, 0.16, f2 - f1); fine = vnoise(n, 32, 32, 2, 4)
    h = edge ** 0.6 * (0.7 + 0.3 * tone) + 0.05 * fine
    bc = mix(col((0.115, 0.085, 0.065), n), col((0.12, 0.112, 0.10), n), sstep(0.55, 0.9, tone)) * (0.8 + 0.1 * fine[..., None])
    bc *= (0.55 + 0.45 * edge)[..., None]
    lich = sstep(1.6, 2.2, vnoise(n, 10, 10, 3, 5)); bc = mix(bc, col((0.30, 0.31, 0.25), n), lich * 0.85)
    save_set('SpruceBark', bc, 0.84 + 0.06 * fine - 0.1 * lich, h, n / 60)
    # --- spruce needles on a frond (u across the frond 0..1, centre twig at 0.5; v along the branch, 0.6 m per tile)
    v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n; d = np.abs(u - 0.5) * 2
    jit = vnoise(n, 4, 24, 4, 3) * 0.08; nd = np.zeros((n, n), np.float32)
    for k, off in enumerate((0.0, 0.33, 0.66)):
        ph = (v * 26 + d * 9 + off + jit * (k + 1)) % 1.0
        nd = np.maximum(nd, sstep(0.14, 0.06, np.abs(ph - 0.5)) * sstep(1.0, 0.75, d + 0.08 * k))
    twig = sstep(0.05, 0.02, d); nz_ = vnoise(n, 8, 8, 5, 4)
    bc = mix(col((0.020, 0.030, 0.022), n), col((0.036, 0.062, 0.036), n) * (1 + 0.15 * nz_[..., None]), nd)
    bc = mix(bc, col((0.09, 0.06, 0.045), n), twig)
    frost = sstep(1.3, 1.8, vnoise(n, 16, 16, 6, 4)) * sstep(0.55, 0.9, d) * nd          # hoar frost on needle tips
    bc = mix(bc, col((0.42, 0.45, 0.50), n), frost * 0.8)
    save_set('Needles', bc, 0.62 + 0.22 * (1 - nd) - 0.1 * frost, nd * 0.6 + twig * 0.5, n / 90)
    # --- birch bark (white, horizontal lenticels, peeling bands)
    band = vnoise(n, 2, 40, 7, 4); f1, f2, cid = voronoi(n, 5, 70, 8)
    lent = sstep(0.11, 0.05, f1) * (np.random.default_rng(2).uniform(0, 1, 5 * 70)[cid] > 0.35)
    knot = sstep(1.9, 2.4, vnoise(n, 6, 4, 9, 5))
    bc = col((0.50, 0.49, 0.45), n) * (1 + 0.06 * band[..., None])
    bc = mix(bc, col((0.56, 0.48, 0.44), n), sstep(1.0, 1.6, band) * 0.6)              # fresh pinkish layer under peel
    bc = mix(bc, col((0.05, 0.045, 0.045), n), np.maximum(lent * 0.9, knot))
    save_set('BirchBark', bc, 0.62 + 0.08 * band + 0.2 * knot, -lent * 0.4 - knot * 0.5 + 0.05 * band, n / 120)
    # --- birch dark: fissured base bark and the fine twigs
    f1, f2, cid = voronoi(n, 5, 2, 10); fis = sstep(0.0, 0.22, f2 - f1); nz_ = vnoise(n, 24, 24, 11, 4)
    bc = mix(col((0.035, 0.03, 0.028), n), col((0.085, 0.068, 0.06), n), fis) * (1 + 0.1 * nz_[..., None])
    bc = mix(bc, col((0.40, 0.39, 0.36), n), sstep(1.4, 2.0, nz_) * fis)                 # white bark left on the ridges
    save_set('BirchDark', bc, 0.86 + 0.05 * nz_, fis + 0.05 * nz_, n / 50)
    # --- snow (2 m tile): pillows + grain; albedo 0.80-0.86 (never 1.0)
    big = vnoise(n, 4, 4, 12, 4); grain = vnoise(n, 96, 96, 13, 2)
    bc = col((0.80, 0.82, 0.86), n) * (0.965 + 0.025 * np.tanh(big)[..., None] + 0.008 * grain[..., None])
    save_set('Snow', bc, 0.66 + 0.05 * big + 0.04 * grain, big * 1.0 + grain * 0.06, n / 900, ao_k=1.5)
    # --- frozen-falls ice (2 m tile, v = down the flow): clear blue-black streaks vs white bubbly ice
    st = vnoise(n, 6, 1, 14, 4); drips = vnoise(n, 12, 4, 15, 4); lump = vnoise(n, 8, 5, 18, 3)   # broad flow lanes, bulbous lumps
    clear = sstep(0.55, 1.1, st + 0.35 * drips - 0.3 * lump)                                    # few clear lanes, not pinstripes
    frost = sstep(-0.4, 0.8, lump + 0.3 * drips)                                                  # rime + hoar on the bulges
    bc = mix(col((0.50, 0.59, 0.64), n), col((0.66, 0.72, 0.75), n), frost)                         # milky bubbly ice, frosted bulges
    bc = mix(bc, col((0.18, 0.30, 0.37), n), clear * 0.85)                                         # clear blue-black lanes
    save_set('Ice', bc, 0.12 + 0.38 * frost * (1 - clear) + 0.02 * drips, lump * 0.8 + st * 0.25 + drips * 0.2, n / 120, ao_k=1.0)
    # --- bridge ashlar (2 m tile, 5 courses of 0.4 m; blocks 0.6-1.2 m; lime mortar)
    r = np.random.default_rng(16); v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n
    row = np.minimum((v * 5).astype(int), 4); ly = v * 5 - row
    edgedist = np.zeros((n, n), np.float32); bid = np.zeros((n, n), np.int32); tone = r.uniform(0.82, 1.18, 200)
    for k in range(5):
        cuts = [0.0]
        while cuts[-1] < 0.85: cuts.append(cuts[-1] + r.uniform(0.3, 0.6))
        cuts = np.array(cuts[:-1] + [1.0]) + r.uniform(0, 1); m = row == k; uu = u[m]
        pos = (uu - cuts[0]) % 1.0 + cuts[0]; j = np.searchsorted(cuts, pos, side='right') - 1
        dx = np.minimum(pos - cuts[j], cuts[j + 1] - pos) * 2.0; dy = np.minimum(ly[m], 1 - ly[m]) * 0.4
        edgedist[m] = np.minimum(dx, dy); bid[m] = k * 40 + j
    mort = sstep(0.014, 0.008, edgedist); grain = vnoise(n, 64, 64, 17, 3); face = vnoise(n, 16, 16, 18, 5)
    streak = sstep(0.8, 1.6, vnoise(n, 30, 2, 19, 4))
    h = sstep(0.0, 0.05, edgedist) * (1 + 0.04 * face) + 0.02 * grain
    bc = col((0.20, 0.195, 0.185), n) * tone[bid][..., None] * (0.92 + 0.06 * grain[..., None]) * (1 - 0.12 * streak[..., None])
    bc = mix(bc, col((0.36, 0.34, 0.31), n), mort)
    save_set('Stone', bc, 0.80 + 0.05 * face + 0.1 * mort + 0.35 * (tone[bid] - 1.0) * (1 - mort) - 0.06 * streak, h, n / 40)   # each block its own wear
    # --- weathered logs (2 m tile, u along the log, 8 logs of 0.25 m across v) with clay-moss chinking
    v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n; ly = (v * 8) % 1.0; lid = (v * 8).astype(int)
    prof = np.sqrt(np.clip(1 - (2 * ly - 1) ** 2, 0, 1)); gap = sstep(0.32, 0.18, prof)
    grain = vnoise(n, 3, 120, 20, 5); checks = sstep(2.2, 2.8, np.abs(vnoise(n, 2, 90, 21, 4)))
    ltone = np.random.default_rng(3).uniform(0.85, 1.15, 8)[lid]
    bc = col((0.14, 0.13, 0.12), n) * ltone[..., None] * (1 + 0.08 * grain[..., None]) * (0.9 + 0.1 * prof[..., None])
    bc *= (1 - 0.6 * checks)[..., None]; bc = mix(bc, col((0.06, 0.058, 0.045), n), gap)
    save_set('Wood', bc, 0.82 + 0.05 * grain + 0.08 * gap, prof * 0.8 - checks * 0.15 + 0.03 * grain, n / 40)
    # --- scoured granite/gneiss (4 m tile): dark, mineral speckle, foliation, cracks, a little crustose lichen
    v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n; warp = vnoise(n, 4, 4, 22, 4)
    fol = np.sin((u * 1.0 + v * 0.35) * TAU * 9 + warp * 2.2); spk = vnoise(n, 128, 128, 23, 3)
    f1, f2, cid = voronoi(n, 6, 6, 24); crack = sstep(0.035, 0.0, f2 - f1); fr = vnoise(n, 8, 8, 25, 6)
    bc = col((0.068, 0.068, 0.072), n) * (1 + 0.12 * fol[..., None] + 0.08 * fr[..., None])
    bc = mix(bc, col((0.15, 0.145, 0.14), n), sstep(1.2, 1.8, spk) * 0.8); bc = mix(bc, col((0.035, 0.035, 0.038), n), crack)
    lich = sstep(1.5, 2.1, vnoise(n, 12, 12, 26, 5)); bc = mix(bc, col((0.27, 0.29, 0.24), n), lich * 0.8)
    save_set('Rock', bc, 0.78 + 0.06 * fr + 0.1 * crack - 0.05 * lich, fr * 0.5 - crack * 0.6 + 0.05 * spk, n / 70)

# ================================================================== mesh builder
MATS = ['WK_SpruceBark', 'WK_Needles', 'WK_Snow', 'WK_BirchBark', 'WK_BirchDark', 'WK_Ice', 'WK_Stone', 'WK_Wood', 'WK_Rock']
class MB:
    def __init__(s): s.V, s.F, s.UV, s.M, s.nv = [], [], [], [], 0
    def raw(s, V, F, UV, mat):                                    # F: list of index lists (local), UV: per-face corner uvs
        s.V.append(np.asarray(V, np.float32).reshape(-1, 3))
        for f, uv in zip(F, UV): s.F.append([i + s.nv for i in f]); s.UV.append(uv); s.M.append(MATS.index(mat))
        s.nv += len(s.V[-1])
    def grid(s, P, U, mat, want=None, closed_rows=False):
        r, c = P.shape[:2]; idx = np.arange(r * c).reshape(r, c)
        F = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
        if want is not None:                                      # orient so the middle quad faces 'want'
            q = F[len(F) // 2]; p = P.reshape(-1, 3); nrm = np.cross(p[q[1]] - p[q[0]], p[q[3]] - p[q[0]])
            if np.dot(nrm, want) < 0: F = F[:, ::-1]
        uv = U.reshape(-1, 2)[F]; s.raw(P.reshape(-1, 3), F.tolist(), uv.tolist(), mat)
    def box(s, c, size, mat, tile=2.0, rotz=0.0):
        hx, hy, hz = np.array(size) / 2; cs = np.array([[x, y, z] for z in (-hz, hz) for y in (-hy, hy) for x in (-hx, hx)])
        ca, sa = math.cos(rotz), math.sin(rotz); cs = cs @ np.array([[ca, sa, 0], [-sa, ca, 0], [0, 0, 1]]) + c
        s.solid(cs, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)], mat, tile)
    def solid(s, V, F, mat, tile=2.0, convex=True):              # box-projected uvs (world metres / tile)
        V = np.asarray(V, np.float64); UV = []; cen = V.mean(0); F = [list(f) for f in F]
        for i, f in enumerate(F):
            p = V[f]; nrm = np.cross(p[1] - p[0], p[-1] - p[0])
            if convex and np.dot(nrm, p.mean(0) - cen) < 0: F[i] = f = f[::-1]; p = V[f]
            ax = int(np.argmax(np.abs(nrm)))
            a, b = [(1, 2), (0, 2), (0, 1)][ax]; UV.append([(q[a] / tile, q[b] / tile) for q in p])
        s.raw(V, [list(f) for f in F], UV, mat)
    def obj(s, name, smooth=True, sharp_deg=None):
        V = np.concatenate(s.V); me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], s.F)
        uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.array([q for f in s.UV for q in f], np.float32).ravel())
        me.polygons.foreach_set('material_index', np.array(s.M, np.int32)); me.polygons.foreach_set('use_smooth', np.full(len(s.F), smooth))
        used = sorted(set(s.M)); remap = {m: i for i, m in enumerate(used)}
        me.polygons.foreach_set('material_index', np.array([remap[m] for m in s.M], np.int32))
        for m in used: me.materials.append(MAT[MATS[m]])
        if sharp_deg: me.set_sharp_from_angle(angle=math.radians(sharp_deg))
        me.update(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        print('mesh', name, 'tris', sum(len(f) - 2 for f in s.F), 'slots', [MATS[m] for m in used]); return ob

def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None] + 1e-9
    a = np.array([0, 0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0, 0]); n = np.cross(T[0], a); n /= np.linalg.norm(n); N = [n]
    for t in T[1:]:
        n = N[-1] - t * np.dot(N[-1], t); N.append(n / (np.linalg.norm(n) + 1e-9))
    N = np.array(N); return T, N, np.cross(T, N)
def tube(mb, P, R, sides, mat, utile=1.0, vtile=1.0, caps=False):
    P = np.asarray(P, np.float64); R = np.asarray(R, np.float64); T, N, B = frames(P); th = np.linspace(0, TAU, sides + 1)
    ring = P[:, None] + R[:, None, None] * (np.cos(th)[None, :, None] * N[:, None] + np.sin(th)[None, :, None] * B[:, None])
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    circ = max(1, round(TAU * R.max() / utile)); U = np.stack(np.broadcast_arrays((th / TAU * circ)[None, :], (L / vtile)[:, None]), -1)
    mb.grid(ring, U, mat)
    if caps:
        for e, sgn in ((0, -1), (-1, 1)):
            c = ring[e, :-1]; V = np.vstack([P[e], c]); F = [[0, 1 + (i + 1) % sides, 1 + i] if sgn < 0 else [0, 1 + i, 1 + (i + 1) % sides] for i in range(sides)]
            mb.raw(V, F, [[(0.5, 0.5), (0.5 + 0.4 * math.cos(th[f[1] - 1]), 0.5 + 0.4 * math.sin(th[f[1] - 1])),
                           (0.5 + 0.4 * math.cos(th[f[2] - 1]), 0.5 + 0.4 * math.sin(th[f[2] - 1]))] for f in F], mat)
def blob_along(mb, P, right, up, half_w, height, mat, lift=0.0, cols=9, tile=2.0):
    """Snow cushion along a centre line: semi-ellipse cross-sections over the top (snow lies on top surfaces only)."""
    th = np.linspace(0, math.pi, cols); P = np.asarray(P)
    sec = (-np.cos(th)[None, :, None] * (half_w[:, None, None] * right[:, None]) + np.sin(th)[None, :, None] * (height[:, None, None] * up[:, None]))
    G = P[:, None] + up[:, None] * lift + sec
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    U = np.stack(np.broadcast_arrays((th * half_w.mean() / tile)[None, :], (L / tile)[:, None]), -1)
    mb.grid(G, U, mat, want=up[len(up) // 2])
def lumps(n, rng, amp=0.35, k=3):
    x = np.linspace(0, 1, n); y = np.ones(n)
    for _ in range(k): y += amp / k * 2 * np.sin(x * TAU * rng.uniform(1.5, 5) + rng.uniform(0, TAU))
    return np.clip(y, 0.4, 1.8)

# ================================================================== spruce (snow-loaded, branch tiers, snow on top only)
def spruce(name, H, seed, whorl_gap):
    rng = np.random.default_rng(seed); mb = MB()
    zt = np.linspace(-0.5, H, 24); lean = np.cumsum(rng.normal(0, 0.012, (24, 2)), 0) * (zt[:, None] / H)
    P = np.column_stack([lean, zt]); r0 = H * 0.012
    R = r0 * (1 - np.clip(zt, 0, H) / H) ** 0.9 + 0.012; R *= 1 + 0.6 * np.exp(-np.clip(zt, 0, None) / 0.35)
    tube(mb, P, R, 10, 'WK_SpruceBark')
    z0 = 0.05 * H; Rmax = 0.17 * H; zs = np.arange(z0, H * 0.96, whorl_gap); golden = 2.39996
    for wi, z in enumerate(zs):
        t = (z - z0) / (H - z0); crown = Rmax * (1 - t) ** 0.95 + 0.25; nb = 6 if t < 0.8 else 4
        trunk = np.interp(z, zt, P[:, 0]), np.interp(z, zt, P[:, 1])
        for b in range(nb):
            az = wi * golden + b * TAU / nb + rng.normal(0, 0.25); L = crown * rng.uniform(0.85, 1.12); fwd = np.array([math.cos(az), math.sin(az), 0])
            up = np.array([0, 0, 1.0]); right = np.cross(fwd, up); s = np.linspace(0, 1, 11)
            droop = 0.85 - 0.45 * t; rise = 0.28 + 0.25 * t                         # low branches carry more snow, hang more
            C = np.array([trunk[0], trunk[1], z]) + np.outer(s * L, fwd) + np.outer(L * (rise * s - droop * s * s + 0.09 * s ** 4), up)
            W = max(0.18, min(0.8, 0.26 * L)) * (np.sin(math.pi * np.minimum(1, 0.05 + s * 1.05)) ** 0.7 + 0.08)
            saw = np.where(np.arange(11) % 2 == 0, 1.0, 0.78)
            for layer, (hang, wsc, dz) in enumerate(((0.7, 1.0, 0.0),)):
                w = W * wsc; cols = np.array([-1, -0.5, 0, 0.5, 1.0])
                ef = np.where(np.abs(cols)[None, :] == 1, saw[:, None], 1.0)
                sec = (cols[None, :] * w[:, None] * ef)[..., None] * right - (-(np.abs(cols) ** 1.4)[None, :] * (hang * w)[:, None])[..., None] * -up
                G = C[:, None] + sec + np.array([0, 0, dz]); U = np.stack(np.broadcast_arrays(((cols + 1) / 2)[None, :], (s * L / 0.6)[:, None]), -1)
                mb.grid(G, U, 'WK_Needles', want=up)
            # pendulous branchlets (the Norway spruce 'comb' habit): narrow needle strips hanging under the branch
            for sb in np.linspace(0.12, 0.95, max(2, int(L / 0.3))):
                c0 = np.array([np.interp(sb, s, C[:, q]) for q in range(3)]); wb = np.interp(sb, s, W)
                for sd in (-1, 1):
                    dvec = -up + right * sd * 0.4 + fwd * 0.3; dvec /= np.linalg.norm(dvec)
                    ll = (0.3 + 0.5 * (1 - sb)) * min(1.0, L / 1.5) * (0.8 + 0.4 * (1 - t)) * rng.uniform(0.8, 1.2)
                    rr = np.linspace(0, 1, 4); wd = 0.17 - 0.1 * rr
                    S = c0 + right * sd * wb * 0.35 + np.outer(rr * ll, dvec) + np.outer(rr ** 2 * 0.12 * ll, right * sd)
                    G = S[:, None] + np.array([-0.5, 0.5])[None, :, None] * (wd[:, None, None] * fwd)
                    mb.grid(G, np.stack(np.broadcast_arrays(np.array([0.2, 0.8])[None, :], (rr * ll / 0.6)[:, None]), -1), 'WK_Needles')
            if rng.uniform() < 0.95:                                                # snow cushion on the branch top
                ss = slice(1, 11); env = np.sin(math.pi * np.linspace(0.04, 0.96, 10)) ** 0.3          # a long flat pad, not an egg
                hw = np.minimum(W[ss] * 1.05, 0.75) * env * lumps(10, rng, 0.2) + 0.01                    # covers the frond width
                hh = (0.05 + 0.11 * (1 - t)) * env * lumps(10, rng, 0.45) + 0.005                         # 5-16 cm deep (settled snow load)
                Cs = C[ss]; fw = np.gradient(Cs, axis=0); fw /= np.linalg.norm(fw, axis=1)[:, None]
                rt = np.cross(fw, up); rt /= np.linalg.norm(rt, axis=1)[:, None]; upv = np.cross(rt, fw)
                blob_along(mb, Cs, rt, upv, hw, hh, 'WK_Snow', lift=-0.04)
    # leader + snow cap on the top whorl
    tip = np.array([P[-1, 0], P[-1, 1], H]); tube(mb, np.array([tip - [0, 0, 0.9], tip + [0, 0, 0.5]]), np.array([0.03, 0.004]), 6, 'WK_SpruceBark')
    sp = np.linspace(-0.5, 0.5, 7); Cc = tip + np.outer(sp, [1, 0, 0]) - [0, 0, 0.9]; e = np.cos(sp * math.pi) ** 0.5 + 0.02
    blob_along(mb, Cc, np.tile([0, 1.0, 0], (7, 1)), np.tile([0, 0, 1.0], (7, 1)), 0.35 * e, 0.3 * e, 'WK_Snow')
    return mb.obj(name)

# ================================================================== bare birch (white bark, pendulous fine twigs)
def birch(name, H, seed):
    rng = np.random.default_rng(seed); mb = MB()
    z = np.linspace(-0.4, H, 20); bend = np.column_stack([0.25 * np.sin(z / H * 2.6 + 0.4), 0.15 * np.sin(z / H * 3.3)]) * (z[:, None] / H)
    P = np.column_stack([bend, z]); r0 = 0.17; R = r0 * (1 - np.clip(z, 0, H) / H) ** 1.1 + 0.015; R *= 1 + 0.4 * np.exp(-np.clip(z, 0, None) / 0.3)
    cut = int(np.searchsorted(z, 1.6)); tube(mb, P[:cut + 1], R[:cut + 1], 10, 'WK_BirchDark'); tube(mb, P[cut:], R[cut:], 10, 'WK_BirchBark')
    def branch(p0, d, L, r, depth):
        n = [0, 8, 6, 5, 4][depth]; s = np.linspace(0, 1, n); d = d / np.linalg.norm(d)
        g = np.array([0, 0, -1.0]) * (0.0, 0.05, 0.15, 0.45, 0.9)[depth]                 # birch twigs weep
        C = p0 + np.outer(s * L, d) + np.outer((s ** 2) * L, g) + rng.normal(0, 0.02 * L, (n, 3)) * s[:, None]
        Rr = r * (1 - 0.75 * s) + 0.003
        tube(mb, C, Rr, [0, 6, 5, 4, 3][depth], 'WK_BirchBark' if depth == 1 else 'WK_BirchDark', 0.5, 0.5)
        if depth <= 2:                                                                  # thin snow line on the top of limbs
            tan = np.gradient(C, axis=0); tan /= np.linalg.norm(tan, axis=1)[:, None]
            if abs(tan[n // 2][2]) < 0.75:
                rt = np.cross(tan, [0, 0, 1.0]); rt /= np.linalg.norm(rt, axis=1)[:, None] + 1e-9; upv = np.cross(rt, tan)
                env = np.sin(math.pi * np.linspace(0, 1, n)) ** 0.5 * (1 - np.abs(tan[:, 2]))
                blob_along(mb, C, rt, upv, Rr * 0.9 * env + 0.002, (0.025 + Rr * 0.5) * env * lumps(n, rng) + 0.001, 'WK_Snow', lift=Rr.mean() * 0.6, cols=5)
        if depth >= 4: return
        kids = [0, 6, 5, 5][depth]
        for k in range(kids):
            sk = rng.uniform(0.25, 0.95); i = min(n - 1, int(sk * (n - 1))); a = rng.uniform(0, TAU)
            side = np.cross(d, [math.cos(a), math.sin(a), 0.3]); side /= np.linalg.norm(side) + 1e-9
            nd = d * 0.55 + side * 0.75 + [0, 0, 0.25 if depth < 2 else -0.1]
            branch(C[i], nd, L * rng.uniform(0.45, 0.6), Rr[i] * 0.6, depth + 1)
    for k in range(15):
        t = rng.uniform(0.32, 0.93); zz = H * t; a = k * 2.39996 + rng.normal(0, 0.3)
        p0 = np.array([np.interp(zz, z, P[:, 0]), np.interp(zz, z, P[:, 1]), zz])
        d = np.array([math.cos(a), math.sin(a), 0]) * math.sin(math.radians(45)) + [0, 0, math.cos(math.radians(45 - 20 * (1 - t)))]
        branch(p0, d, H * 0.36 * (1 - t * 0.55) * rng.uniform(0.8, 1.1), np.interp(zz, z, R) * 0.5, 1)
    return mb.obj(name)

# ================================================================== icicles (an eave strip; lengths heavy-tailed, drip lines clustered)
def icicle_strip(mb, x0, x1, z, y, rng, maxlen=0.9, dens=11, along=np.array([1.0, 0, 0])):
    """Icicles hanging from an eave line from x0 to x1 (along 'along'), at height z, offset y. Adds an ice rim on top."""
    Lx = x1 - x0; n = max(3, int(Lx * dens)); xs = np.sort(rng.uniform(0, Lx, n)); drip = 0.5 + 0.5 * np.sin(xs * rng.uniform(1.5, 3) + rng.uniform(0, TAU))
    side = np.cross([0, 0, 1.0], along)
    for i, x in enumerate(xs):
        L = 0.04 + maxlen * (rng.uniform() ** 3) * (0.3 + 0.7 * drip[i])
        seg = max(4, int(L * 28)); s = np.linspace(0, 1, seg); base = along * (x0 + x) + side * y + [0, 0, z]
        C = base + np.outer(s, [0, 0, -L]) + np.outer(s ** 2, rng.normal(0, 0.03, 3) * L)
        r0 = 0.008 + 0.05 * L ** 0.8; R = r0 * (1 - s) ** 0.85 * (1 + 0.12 * np.sin(s * L * 70) * (1 - s)) + 0.0008
        tube(mb, C, R, 7, 'WK_Ice', 0.3, 0.6)
    s = np.linspace(0, 1, max(3, int(Lx * 4))); C = along * (x0 + Lx * s)[:, None] + side * y + [0, 0, z + 0.01]
    blob_along(mb, C, np.tile(side, (len(s), 1)), np.tile([0, 0, -1.0], (len(s), 1)), np.full(len(s), 0.035), np.full(len(s), 0.03) * lumps(len(s), rng), 'WK_Ice', cols=5)

# ================================================================== frozen waterfall ice curtain (front faces local +Y)
def ice_falls(name, W=18.0, Hh=15.5, seed=7, lean=0.0):
    rng = np.random.default_rng(seed); mb = MB(); nx, nz = 91, 79
    x = np.linspace(-W / 2, W / 2, nx); z = np.linspace(-1.5, Hh, nz); X, Z = np.meshgrid(x, z)
    t = 1.4 + 0.3 * np.sin(X * 0.7 + 1.3)
    for _ in range(16):                                                    # organ-pipe columns, thicker toward the bottom
        xc = rng.uniform(-W / 2 + 1, W / 2 - 1); sg = rng.uniform(0.25, 0.9); a = rng.uniform(0.4, 1.4)
        top = rng.uniform(Hh * 0.55, Hh); f = rng.uniform(1.5, 3.0); ph = rng.uniform(0, TAU)
        prof = a * (0.35 + 0.65 * np.clip(1 - Z / top, 0, 1) ** 0.7) * (Z < top + 0.5)
        t += prof * np.exp(-((X - xc) / sg) ** 2) * (1 + 0.15 * np.sin(Z * f + ph))
    t += 1.1 * np.exp(-((Z - (Hh - 1.6)) / 1.3) ** 2) * (1 + 0.3 * np.sin(X * 1.7))      # bulging lip at the top
    t += 3.6 * np.exp(-np.clip(Z, 0, None) / 2.4) * (1 + 0.2 * np.sin(X * 0.9))          # spray cone at the bottom
    u = np.clip(Z / Hh, 0, 1); hw = W / 2 * (0.93 - 0.8 * u * (1 - u) + 0.05 * np.sin(Z * 1.3 + 2.0))   # wide lip, a waist, a flared apron
    hw = hw + 0.7 * np.sin(X * 2.1 + 0.5) * np.sin(X * 0.8)                                      # ragged column edges (vertical, like real curtains)
    lip = Hh - 1.2 - 1.3 * (0.5 + 0.5 * np.sin(X * 0.9 + 0.4)) * (0.5 + 0.5 * np.sin(X * 0.37 + 2.2))
    mask = sstep(hw, hw - 1.6, np.abs(X)) * sstep(lip + 0.6, lip - 0.4, Z) + sstep(1.0, -0.5, Z) * sstep(W / 2, W / 2 - 3, np.abs(X))
    t = t * np.clip(mask, 0, 1)
    m = np.clip(mask, 0, 1); Yb = -lean * np.clip(Z, 0, None)
    Zs = Z - 3.0 * (1 - m) * sstep(Hh - 4.0, Hh, Z)                                                # unmasked parts sink 4 m back AND down: nothing pokes above the lip
    F = np.dstack([X, Yb - 4.0 + t * 1.0 + 2.5 * m, Zs]); U = np.dstack([X / 6.0 + 0.13 * np.sin(Z * 0.7), -Z / 6.0])   # 6 m tile, wobbled: no visible repeat
    mb.grid(F, U, 'WK_Ice', want=np.array([0, 1.0, 0]))
    B = np.dstack([X, Yb - 4.6, Zs]); mb.grid(B, U, 'WK_Ice', want=np.array([0, -1.0, 0]))   # back (Lumen: closed), follows the sunk top
    for e in (0, -1):                                                                                      # sides
        S = np.stack([F[:, e], B[:, e]], 1); mb.grid(S, np.dstack([S[..., 1] / 2, -S[..., 2] / 2]), 'WK_Ice', want=np.array([np.sign(x[e]), 0, 0]))
    Tp = np.stack([F[-1], B[-1]], 0); mb.grid(Tp, np.dstack([Tp[..., 0] / 2, Tp[..., 1] / 2]), 'WK_Ice', want=np.array([0, 0, 1.0]))
    # a fringe of icicles hanging off the lip
    icicle_strip(mb, -W / 4, W / 4, Hh - 2.6, -lean * (Hh - 2.6) + 0.3, rng, maxlen=2.2, dens=3)
    return mb.obj(name)

# ================================================================== stone arch bridge (span axis local X, deck top z=0)
def bridge(name, half=38.0, Wd=6.5, R=23.0, ring=1.6, seed=3):
    rng = np.random.default_rng(seed); mb = MB(); wy = Wd / 2 + 0.5; crown = -1.9; zs = crown - R
    arc = [(R * math.cos(a), zs + R * math.sin(a)) for a in np.linspace(0, math.pi, 61)]
    prof = [(-half, 0), (half, 0), (half, -14), (R + 5, -30), (R + 5, -36), (R, -36)] + arc + [(-R, -36), (-R - 5, -36), (-R - 5, -30), (-half, -14)]   # abutments buried in the banks
    # side walls (spandrels, abutments) = the profile extruded across the deck
    pr = np.array(prof); area = np.sum(pr[:, 0] * np.roll(pr[:, 1], -1) - np.roll(pr[:, 0], -1) * pr[:, 1])
    if area < 0: prof = prof[::-1]                                     # CCW in (x, z): side quads then face outward
    k = len(prof); V = [(px, -wy, pz) for px, pz in prof] + [(px, wy, pz) for px, pz in prof]
    tris = geometry.tessellate_polygon([[Vector((px, pz, 0)) for px, pz in prof]]); F = []
    for a, b, c in tris:                                               # front (y-) triangles CCW in (x, z) -> normal -Y
        (x0, z0), (x1, z1), (x2, z2) = prof[a], prof[b], prof[c]
        if (x1 - x0) * (z2 - z0) - (z1 - z0) * (x2 - x0) < 0: b, c = c, b
        F += [(a, b, c), (k + a, k + c, k + b)]
    F += [(i, k + i, k + (i + 1) % k, (i + 1) % k) for i in range(k)]
    mb.solid(V, F, 'WK_Stone', convex=False)
    # voussoirs: real blocks, radial joints, proud of the face by 6 cm; alternating long/short tails
    nv = 47
    for side in (-1, 1):
        for i in range(nv):
            a0 = math.pi * i / nv + 0.004; a1 = math.pi * (i + 1) / nv - 0.004; ro = R + ring + (0.25 if i % 2 else 0)
            pts = [(R * math.cos(a0), R * math.sin(a0)), (ro * math.cos(a0), ro * math.sin(a0)), (ro * math.cos(a1), ro * math.sin(a1)), (R * math.cos(a1), R * math.sin(a1))]
            y0, y1 = side * (wy - 0.45), side * (wy + 0.06)
            C = [(px, y, zs + pz) for y in (y0, y1) for px, pz in pts]
            mb.solid(C, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], 'WK_Stone', 1.0)
        mb.box(np.array([0, side * (wy + 0.04), -0.3]), (2 * half, 0.24, 0.32), 'WK_Stone')            # string course
        mb.box(np.array([0, side * (wy - 0.25), 0.5]), (2 * half, 0.5, 1.0), 'WK_Stone')               # parapet
        mb.box(np.array([0, side * (wy - 0.25), 1.08]), (2 * half + 0.2, 0.64, 0.16), 'WK_Stone')      # coping
        for ex in (-half, half): mb.box(np.array([ex, side * (wy - 0.25), 0.7]), (0.9, 0.9, 1.4), 'WK_Stone')
        # snow cushion on the coping (lumpy), icicles under the string course over the arch crown
        n = 60; xs = np.linspace(-half + 0.5, half - 0.5, n); env = sstep(-half + 0.4, -half + 1.2, xs) * sstep(half - 0.4, half - 1.2, xs)
        C = np.column_stack([xs, np.full(n, side * (wy - 0.25)), np.full(n, 1.16)])
        blob_along(mb, C, np.tile([0, 1.0, 0], (n, 1)), np.tile([0, 0, 1.0], (n, 1)), (0.33 * env * lumps(n, rng, 0.2) + 0.01), 0.26 * env * lumps(n, rng, 0.5) + 0.005, 'WK_Snow')
        icicle_strip(mb, -9.0, 9.0, -0.46, side * (wy + 0.1), rng, maxlen=1.1, dens=5)
    # deck snow: drifted against the parapets, two trodden ruts in the middle
    xs = np.linspace(-half, half, 153); ys = np.linspace(-Wd / 2, Wd / 2, 27); X, Y = np.meshgrid(xs, ys, indexing='ij')
    dep = 0.07 + 0.36 * np.exp(-(Wd / 2 - np.abs(Y)) / 0.55) - 0.05 * np.exp(-((np.abs(Y) - 0.85) / 0.25) ** 2)
    rr = np.random.default_rng(5); dep += 0.03 * np.sin(X * 1.3 + rr.uniform(0, 6)) * np.sin(Y * 2.1)
    dep *= sstep(half, half - 2.5, np.abs(X)) * 0.85 + 0.15
    D = np.dstack([X, Y, dep]); mb.grid(D, np.dstack([X / 2, Y / 2]), 'WK_Snow', want=np.array([0, 0, 1.0]))
    return mb.obj(name, smooth=True, sharp_deg=35)

# ================================================================== half-buried farmstead (log house; local +Y = lee side, drift)
def farmstead(name, seed=9):
    rng = np.random.default_rng(seed); mb = MB(); Lh, Dh, eave, pitch, ov = 6.0, 3.5, 2.7, math.radians(40), 0.6
    ridge = eave + Dh * math.tan(pitch); r = 0.13
    mb.box(np.array([0, 0, -0.45]), (2 * Lh + 0.5, 2 * Dh + 0.5, 1.5), 'WK_Stone')                    # plinth, 1.2 m below grade
    for c in range(10):                                                                                # log walls, interlocked corners
        zc = 0.3 + r + c * 0.24
        for sy in (-1, 1): tube(mb, [(-Lh - 0.35, sy * Dh, zc), (Lh + 0.35, sy * Dh, zc)], [r * rng.uniform(0.92, 1.08)] * 2, 8, 'WK_Wood', 2.0, 2.0, caps=True)
        for sx in (-1, 1): tube(mb, [(sx * Lh, -Dh - 0.35, zc + 0.12), (sx * Lh, Dh + 0.35, zc + 0.12)], [r * rng.uniform(0.92, 1.08)] * 2, 8, 'WK_Wood', 2.0, 2.0, caps=True)
    zc = eave + 0.12
    while zc < ridge - 0.2:                                                                            # gable logs
        hl = Dh * (1 - (zc - eave) / (ridge - eave)) + 0.05
        for sx in (-1, 1): tube(mb, [(sx * Lh, -hl, zc), (sx * Lh, hl, zc)], [r, r], 8, 'WK_Wood', 2.0, 2.0, caps=True)
        zc += 0.24
    # roof boards (two slabs) and the snow load on them: thin on the windward (-Y) side, deep + cornice on the lee (+Y)
    ye = Dh + ov; ze = eave - ov * math.tan(pitch) + 0.2; zr = ridge + 0.2; th = 0.12
    for sy in (-1, 1):
        C = [(x, y, z) for z_off in (0, th) for x in (-Lh - 0.8, Lh + 0.8) for (y, z) in ((sy * ye, ze + z_off), (0, zr + z_off))]
        mb.solid(C, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)], 'WK_Wood')
    nrm_l = np.array([0, math.sin(pitch), math.cos(pitch)]); nrm_w = np.array([0, -math.sin(pitch), math.cos(pitch)])
    prof = []                                                                                          # closed (y, z) loop over the roof
    for w in np.linspace(-1, 1, 25):
        y = w * ye; zroof = zr + th - abs(w) * (zr - ze)
        tk = (0.35 if w < 0 else 0.8) * (1 - 0.25 * abs(w) ** 4) + 0.05
        n = nrm_w if w < 0 else nrm_l; prof.append((y + n[1] * tk, zroof + n[2] * tk))
    prof += [(ye + 0.45, ze + 0.25), (ye + 0.55, ze - 0.15), (ye + 0.2, ze - 0.25), (ye, ze + th)]   # lee cornice curls down
    prof += [(w * ye, zr + th - abs(w) * (zr - ze) - 0.02) for w in np.linspace(1, -1, 9)]
    prof += [(-ye - 0.08, ze + 0.1)]; prof = np.array(prof + [prof[0]])
    xs = np.linspace(-Lh - 1.0, Lh + 1.0, 40); x0 = Lh + 0.5
    base = np.column_stack([np.zeros(len(prof)), prof[:, 0], np.interp(np.abs(prof[:, 0]), [0, ye], [zr + th, ze + th])])
    G = []
    for x in xs:
        env = math.sqrt(max(0, 1 - ((abs(x) - x0) / 0.5) ** 2)) if abs(x) > x0 else 1.0
        lump = 1 + 0.08 * math.sin(x * 1.7 + 1) + 0.05 * math.sin(x * 4.1)
        P = base + (np.column_stack([np.zeros(len(prof)), prof]) - base) * env * np.array([0, 1, lump])
        P[:, 0] = x; G.append(P)
    G = np.array(G); U = np.dstack([G[..., 0] / 2, np.cumsum(np.r_[0, np.linalg.norm(np.diff(prof, axis=0), axis=1)])[None, :].repeat(len(xs), 0) / 2])
    mb.grid(G, U, 'WK_Snow', want=np.array([0, 0, 1.0]))
    # chimney with a snow cap, door on the east gable (dug out), shutters on the windward wall
    mb.box(np.array([-3.0, 0, (ridge + 1.0 + 3.3) / 2]), (0.85, 0.85, ridge + 1.0 - 3.3), 'WK_Stone')
    sp = np.linspace(-0.45, 0.45, 7); e = np.cos(sp / 0.45 * math.pi / 2) ** 0.5 + 0.02
    blob_along(mb, np.column_stack([sp - 3.0, np.zeros(7), np.full(7, ridge + 1.0)]), np.tile([0, 1.0, 0], (7, 1)), np.tile([0, 0, 1.0], (7, 1)), 0.45 * e, 0.22 * e, 'WK_Snow')
    mb.box(np.array([Lh + 0.2, 0, 1.25]), (0.1, 1.05, 1.9), 'WK_Wood')
    for xx in (-3.0, 2.0): mb.box(np.array([xx, -Dh - 0.16, 1.7]), (0.75, 0.06, 0.6), 'WK_Wood')
    icicle_strip(mb, -Lh - 0.6, Lh + 0.6, ze - 0.05, -ye + 0.05, rng, maxlen=0.8, dens=9)
    # woodpile on the west gable, fence posts poking out of the drift
    for i in range(6):
        for j in range(3): tube(mb, [(-Lh - 0.9, -1.6 + i * 0.27 + j * 0.13, 0.5 + j * 0.24), (-Lh - 0.9 - 1.0, -1.6 + i * 0.27 + j * 0.13, 0.5 + j * 0.24)], [0.12, 0.12], 7, 'WK_Wood', 2, 2, caps=True)
    n = 20; yy = np.linspace(-1.75, -0.05 + 5 * 0.27 - 1.6, n)
    blob_along(mb, np.column_stack([np.full(n, -Lh - 1.4), yy, np.full(n, 1.08)]), np.tile([1.0, 0, 0], (n, 1)), np.tile([0, 0, 1.0], (n, 1)), np.full(n, 0.5), 0.2 * lumps(n, rng), 'WK_Snow')
    for k in range(7):
        px, py = -10.0 + rng.normal(0, 0.1), 7.0 + k * 2.2; mb.box(np.array([px, py, 0.6]), (0.14, 0.14, 2.0), 'WK_Wood', rotz=rng.normal(0, 0.15))
        sp = np.linspace(-0.09, 0.09, 5); blob_along(mb, np.column_stack([np.full(5, px), py + sp, np.full(5, 1.6)]), np.tile([1.0, 0, 0], (5, 1)), np.tile([0, 0, 1.0], (5, 1)), np.full(5, 0.09), 0.12 * (np.cos(sp / 0.09 * 1.4) + 0.05), 'WK_Snow')
    # the drift field: to the eaves on the lee side, long tail downwind, scoured near the windward wall, door trench
    xs = np.linspace(-16, 16, 65); ys = np.linspace(-12, 27, 79); X, Y = np.meshgrid(xs, ys, indexing='ij')
    xf = np.exp(-(np.clip(np.abs(X) - Lh, 0, None) / 3.0) ** 2)
    h = (eave - 0.3) * np.clip(1 - (Y - Dh) / 15.0, 0, 1) ** 1.4 * (Y > Dh - 0.2) * xf
    h += 1.1 * np.exp(-(np.clip(np.abs(X) - Lh, 0, None) / 1.6)) * np.exp(-(np.clip(np.abs(Y) - Dh, 0, None) / 2.5)) * (np.abs(X) > Lh)
    h += 0.12 * np.sin(X * 0.7 + 1.2) * np.sin(Y * 0.5) + 0.06 * np.sin(X * 2.3) * np.cos(Y * 1.9)
    h = np.where((np.abs(X) < Lh + 0.05) & (np.abs(Y) < Dh + 0.05), -0.5, h)
    trench = (X > Lh) & (X < Lh + 7) & (np.abs(Y) < 1.6); h = np.where(trench, np.minimum(h, 0.05 + 0.6 * sstep(0.6, 1.6, np.abs(Y))), h)
    edge = np.minimum.reduce([X - xs[0], xs[-1] - X, Y - ys[0], ys[-1] - Y]); h = h * sstep(0, 4, edge) - 0.3 * (1 - sstep(0, 2, edge))
    D = np.dstack([X, Y, h]); mb.grid(D, np.dstack([X / 2, Y / 2]), 'WK_Snow', want=np.array([0, 0, 1.0]))
    return mb.obj(name, smooth=True, sharp_deg=40)

# ================================================================== glacial boulders (fractured + rounded, modelled snow cap on top only)
def boulder(name, size, seed, flat=0.55):
    rng = np.random.default_rng(seed); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    V = np.array([v.co[:] for v in bm.verts]); F = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
    d = V / np.linalg.norm(V, axis=1)[:, None]; r = np.ones(len(V))
    for o in range(6):                                                                  # fractal radial noise
        k = rng.normal(0, 1, (8, 3)); r += sum(0.5 ** o * 0.12 * np.sin(d @ kk * (2 ** o) * 2.2 + rng.uniform(0, TAU)) for kk in k) / 4
    for _ in range(7):                                                                  # plucked fracture planes (angular faces)
        pn = rng.normal(0, 1, 3); pn /= np.linalg.norm(pn); off = rng.uniform(0.62, 0.85)
        proj = d @ pn; r = np.where(proj * r > off, off / np.maximum(proj, 1e-3) * (1 + 0.01 * rng.normal(0, 1, len(r))), r)
    P = d * r[:, None] * np.array([1.0, 0.8, flat]) * size; P[:, 2] = np.maximum(P[:, 2], -0.25 * size)   # grounded bottom
    P[:, 2] += 0.22 * size
    mb = MB(); UV = []
    for f in F:
        p = P[f]; nrm = np.cross(p[1] - p[0], p[2] - p[0]); ax = int(np.argmax(np.abs(nrm))); a, b = [(1, 2), (0, 2), (0, 1)][ax]
        UV.append([(q[a] / 4, q[b] / 4) for q in p])
    mb.raw(P, F, UV, 'WK_Rock')
    # snow cap: the up-facing part of the rock, pushed up by a depth that fades to 0 at the edge
    vn = np.zeros_like(P)
    for f in F:
        nrm = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]]); vn[f] += nrm
    vn /= np.linalg.norm(vn, axis=1)[:, None] + 1e-9; cover = sstep(0.45, 0.85, vn[:, 2])
    keep = [f for f in F if min(vn[f, 2]) > 0.38]
    if keep:
        ids = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(ids)}
        S = P[ids] + np.outer(cover[ids] * (0.08 + 0.1 * size), [0, 0, 1]) + vn[ids] * 0.01
        mb.raw(S, [[remap[i] for i in f] for f in keep], [[(S[remap[i]][0] / 2, S[remap[i]][1] / 2) for i in f] for f in keep], 'WK_Snow')
    return mb.obj(name)

# ================================================================== Cycles lookdev materials (same textures the UE MIs use)
def tex_node(nd, name, kind, cs):
    t = nd.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(OUT, 'tex', 'T_WK_%s_%s.png' % (name, kind)), check_existing=True)
    t.image.colorspace_settings.name = cs; return t
def lookdev_mat(mname, tname, snow_top=None, **extra):
    m = bpy.data.materials.new(mname); m.use_nodes = True; nt = m.node_tree; nd, ln = nt.nodes, nt.links; nd.clear()
    out = nd.new('ShaderNodeOutputMaterial'); p = nd.new('ShaderNodeBsdfPrincipled')
    bc = tex_node(nd, tname, 'BC', 'sRGB'); orm = tex_node(nd, tname, 'ORM', 'Non-Color'); nm = tex_node(nd, tname, 'N', 'Non-Color')
    sp = nd.new('ShaderNodeSeparateColor'); ln.new(orm.outputs['Color'], sp.inputs['Color']); ln.new(sp.outputs['Green'], p.inputs['Roughness'])
    nmap = nd.new('ShaderNodeNormalMap'); ln.new(nm.outputs['Color'], nmap.inputs['Color']); ln.new(nmap.outputs['Normal'], p.inputs['Normal'])
    ln.new(bc.outputs['Color'], p.inputs['Base Color'])
    for k, v in extra.items():
        if k == 'ssr': p.inputs['Subsurface Radius'].default_value = v
        else: p.inputs[k].default_value = v
    shader = p.outputs['BSDF']
    if mname == 'WK_Snow': shader = snow_glints(nd, ln, p)
    if snow_top is not None:                                                     # top-mask snow (MF_WK_SnowCover in UE)
        geo = nd.new('ShaderNodeNewGeometry'); se = nd.new('ShaderNodeSeparateXYZ')
        ln.new(geo.outputs['Normal'], se.inputs['Vector']); nz = nd.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3
        ad = nd.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ln.new(nz.outputs['Fac'], ad.inputs[0]); ad.inputs[1].default_value = 0.25; ln.new(se.outputs['Z'], ad.inputs[2])
        mr = nd.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1 - snow_top + 0.1; mr.inputs['From Max'].default_value = 1 - snow_top + 0.22; ln.new(ad.outputs['Value'], mr.inputs['Value'])
        sb = nd.new('ShaderNodeBsdfPrincipled'); sb.inputs['Base Color'].default_value = (0.80, 0.82, 0.86, 1); sb.inputs['Roughness'].default_value = 0.66
        sb.inputs['Subsurface Weight'].default_value = 0.2; sb.inputs['Subsurface Scale'].default_value = 0.02
        mx = nd.new('ShaderNodeMixShader'); ln.new(mr.outputs['Result'], mx.inputs['Fac']); ln.new(shader, mx.inputs[1]); ln.new(sb.outputs['BSDF'], mx.inputs[2]); shader = mx.outputs['Shader']
    ln.new(shader, out.inputs['Surface']); return m
def snow_glints(nd, ln, p):
    """Snow sparkle: sparse ice-grain facets with random orientations; a sharp lobe only some of them turn to the sun."""
    tc = nd.new('ShaderNodeTexCoord'); vo = nd.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 55
    ln.new(tc.outputs['Object'], vo.inputs['Vector'])
    pts = nd.new('ShaderNodeMapRange'); pts.inputs['From Min'].default_value = 0.10; pts.inputs['From Max'].default_value = 0.06; ln.new(vo.outputs['Distance'], pts.inputs['Value'])
    jit = nd.new('ShaderNodeVectorMath'); jit.operation = 'SUBTRACT'; ln.new(vo.outputs['Color'], jit.inputs[0]); jit.inputs[1].default_value = (0.5, 0.5, 0.5)
    geo = nd.new('ShaderNodeNewGeometry'); sc = nd.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = 1.6; ln.new(jit.outputs['Vector'], sc.inputs[0])
    ad = nd.new('ShaderNodeVectorMath'); ad.operation = 'ADD'; ln.new(geo.outputs['Normal'], ad.inputs[0]); ln.new(sc.outputs['Vector'], ad.inputs[1])
    nr = nd.new('ShaderNodeVectorMath'); nr.operation = 'NORMALIZE'; ln.new(ad.outputs['Vector'], nr.inputs[0])
    g = nd.new('ShaderNodeBsdfGlossy'); g.inputs['Roughness'].default_value = 0.04; g.inputs['Color'].default_value = (1, 1, 1, 1); ln.new(nr.outputs['Vector'], g.inputs['Normal'])
    ad2 = nd.new('ShaderNodeAddShader'); mul = nd.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.35
    ln.new(pts.outputs['Result'], mul.inputs[0]); mx = nd.new('ShaderNodeMixShader'); ln.new(mul.outputs['Value'], mx.inputs['Fac'])
    ln.new(p.outputs['BSDF'], mx.inputs[1]); ln.new(g.outputs['BSDF'], mx.inputs[2]); return mx.outputs['Shader']
MAT = {}
def materials():
    MAT['WK_Snow'] = lookdev_mat('WK_Snow', 'Snow', **{'Subsurface Weight': 0.3, 'Subsurface Scale': 0.03, 'ssr': (0.9, 1.0, 1.3)})
    MAT['WK_SpruceBark'] = lookdev_mat('WK_SpruceBark', 'SpruceBark', snow_top=0.15)
    MAT['WK_Needles'] = lookdev_mat('WK_Needles', 'Needles', snow_top=0.12, **{'Subsurface Weight': 0.1, 'Subsurface Scale': 0.01})
    MAT['WK_BirchBark'] = lookdev_mat('WK_BirchBark', 'BirchBark', snow_top=0.15)
    MAT['WK_BirchDark'] = lookdev_mat('WK_BirchDark', 'BirchDark', snow_top=0.15)
    MAT['WK_Ice'] = lookdev_mat('WK_Ice', 'Ice', snow_top=0.3, **{'IOR': 1.31, 'Subsurface Weight': 0.6, 'Subsurface Scale': 0.15, 'ssr': (0.5, 0.8, 1.2)})
    MAT['WK_Stone'] = lookdev_mat('WK_Stone', 'Stone', snow_top=0.35)
    MAT['WK_Wood'] = lookdev_mat('WK_Wood', 'Wood', snow_top=0.35)
    MAT['WK_Rock'] = lookdev_mat('WK_Rock', 'Rock', snow_top=0.4)

# ================================================================== placements from the heightmap -> props.json (UE cm / deg)
def placements():
    L = json.load(open(os.path.join(TER, 'layout.json'))); H = np.load(os.path.join(TER, 'height_m.npy')); N = H.shape[0]; HALF = (N - 1) / 2
    def hz(x, y): return float(H[int(round(np.clip(y / 100 + HALF, 0, N - 1))), int(round(np.clip(x / 100 + HALF, 0, N - 1)))]) * 100
    def ue_yaw_for(local_dir_b, world_dir_ue):        # rotate a Blender-local direction onto a UE world direction
        wb = (world_dir_ue[0], -world_dir_ue[1]); a_w = math.atan2(wb[1], wb[0]); a_l = math.atan2(local_dir_b[1], local_dir_b[0])
        return round(-math.degrees(a_w - a_l), 2)                  # Blender rotz (CCW) -> UE yaw = -rotz
    out = {'note': 'UE world cm, yaw deg (UE), uniform scale. Computed by build_wk_assets.py from height_m.npy.'}
    b = L['bridge']; rs = np.array(L['road_spline_cm']); k = int(np.argmin(np.hypot(rs[:, 0] - b[0], rs[:, 1] - b[1])))
    d = rs[min(k + 1, len(rs) - 1)] - rs[max(k - 1, 0)]; d = d[:2] / np.linalg.norm(d[:2])
    out['SM_WK_Bridge'] = [{'loc': [b[0], b[1], round(b[2], 1)], 'yaw': ue_yaw_for((1, 0), d), 'scale': 1.0, 'note': 'deck top = graded road height at the bridge (layout.json)'}]
    f = L['frozen_falls']; rv = np.array(L['river_spline_cm']); k = int(np.argmin(np.hypot(rv[:, 0] - f[0], rv[:, 1] - f[1])))
    fd = rv[min(k + 1, len(rv) - 1)] - rv[max(k - 1, 0)]; fd = fd[:2] / np.linalg.norm(fd[:2])
    ts = np.arange(-600, 1600, 50); zz = np.array([hz(f[0] + fd[0] * t, f[1] + fd[1] * t) for t in ts])
    i_top = int(np.argmax(np.diff(zz) < -150)); i_foot = i_top + int(np.argmin(zz[i_top:i_top + 24]))   # the steep step, then the pool
    lean = float((ts[i_foot] - ts[i_top]) / max(100.0, zz[i_top] - zz[i_foot]))
    out['SM_WK_IceFalls'] = [{'loc': [round(f[0] + fd[0] * (ts[i_foot] + 150), 1), round(f[1] + fd[1] * (ts[i_foot] + 150), 1), round(zz[i_foot] - 50, 1)],
                              'yaw': ue_yaw_for((0, 1), fd), 'scale': 1.0, 'lean': round(lean, 3), 'drop_m': round((zz[i_top] - zz[i_foot]) / 100, 1),
                              'note': 'pivot at the foot of the rock step; the curtain leans back up the step; front faces downstream'}]
    out['SM_WK_Farmstead'] = []
    for nm, p in L['farms'].items():                                              # local +Y (lee) points SE, away from the NW wind
        out['SM_WK_Farmstead'].append({'name': nm, 'loc': [p[0], p[1], round(hz(p[0], p[1]) - 15, 1)], 'yaw': ue_yaw_for((0, 1), (0.7071, 0.7071)), 'scale': 1.0})
    json.dump(out, open(os.path.join(OUT, 'props.json'), 'w'), indent=1); print('props', json.dumps(out)[:600]); return out

# ================================================================== main
bpy.ops.wm.read_factory_settings(use_empty=True)
if ONLY in ('all', 'tex'): textures(TEX)
if ONLY in ('all', 'mesh'):
    materials(); PROPS = placements()
    objs = [spruce('SM_WK_Spruce_A', 20.0, 1, 0.45), spruce('SM_WK_Spruce_B', 9.0, 2, 0.34), birch('SM_WK_Birch_A', 13.0, 3),
            boulder('SM_WK_Rock_A', 2.2, 4), boulder('SM_WK_Rock_B', 0.6, 5, 0.7)]
    mb = MB(); icicle_strip(mb, 0, 3.0, 0, 0, np.random.default_rng(6), maxlen=0.9, dens=11); objs.append(mb.obj('SM_WK_Icicles_3m'))
    fl = PROPS['SM_WK_IceFalls'][0]; objs += [ice_falls('SM_WK_IceFalls', Hh=fl['drop_m'] + 2.5, lean=fl['lean']), bridge('SM_WK_Bridge'), farmstead('SM_WK_Farmstead')]
    rep = {}
    for ob in objs:
        rep[ob.name] = {'tris': sum(len(p.vertices) - 2 for p in ob.data.polygons), 'slots': [m.name for m in ob.data.materials],
                        'size_m': [round(v, 2) for v in ob.dimensions]}
        if '--no-fbx' not in A:
            bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
            bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'fbx', ob.name + '.fbx'), use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z',
                                     apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False)
    json.dump(rep, open(os.path.join(OUT, 'assets_report.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'wk_assets.blend'))
    print('REPORT', json.dumps(rep))
