# Medieval heater shield (laptop2, 2026-10-29): painted lime-wood board, iron rim, leather enarmes (ARROW=1 adds a broken arrow, off by default).
#   blender -b --factory-startup -P build_heater.py      (env RES = low | high)
# low  = game mesh (~7k tris, real-world-scale UVs)                    -> Heater_low.blend
# high = bake source (1 mm grids, paint chips, sword gashes, rivets)   -> Heater_high.blend + masks/*.png
# Units: metres, Z up, the painted face looks toward -Y, the bottom point at z 0. The pivot (hand grip centre) is
# written to heater_meta.json and applied when the FBX is exported.
import os, math, json
import bpy, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('RES', 'low'); HIGH = RES == 'high'
PI = math.pi
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}
def mat(name):
    if name not in MATS: MATS[name] = bpy.data.materials.new(name)
    return MATS[name]

# ---------------- value noise (numpy, deterministic) ----------------
def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def vnoise(u, v, s=0):
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = _hash(iu, iv, s), _hash(iu + 1, iv, s), _hash(iu, iv + 1, s), _hash(iu + 1, iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def fbm(u, v, s, oct=5):
    t, amp, f, tot = 0, 1.0, 1.0, 0
    for o in range(oct):
        t = t + amp * vnoise(u * f, v * f, s + o * 17); tot += amp; amp *= 0.5; f *= 2.03
    return t / tot
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

# ---------------- fast mesh from numpy ----------------
def mesh(name, V, blocks, mname, uv=None, attrs=None, group=None):
    V = np.asarray(V, np.float32).reshape(-1, 3)
    blocks = [np.asarray(b, np.int64) for b in blocks if len(b)]
    idx = np.concatenate([b.ravel() for b in blocks]).astype(np.int32)
    sizes = np.concatenate([np.full(len(b), b.shape[1]) for b in blocks])
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(len(idx)); me.loops.foreach_set('vertex_index', idx)
    me.polygons.add(len(sizes)); me.polygons.foreach_set('loop_start', starts)
    me.update(calc_edges=True)
    me.materials.append(mat(mname))
    if uv is not None:
        lay = me.uv_layers.new(name='UV'); lay.data.foreach_set('uv', np.asarray(uv, np.float32)[idx].ravel())
    for k, a in (attrs or {}).items():
        me.attributes.new(k, 'FLOAT', 'POINT').data.foreach_set('value', np.asarray(a, np.float32))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if group: ob.vertex_groups.new(name=group).add(list(range(len(V))), 1.0, 'REPLACE')
    return ob

def grid_quads(nr, nc, wrap=False):
    i = np.arange(nr - 1)[:, None]; j = np.arange(nc if wrap else nc - 1)[None, :]
    a = i * nc + j; b = i * nc + (j + 1) % nc
    return np.stack([a, b, b + nc, a + nc], -1).reshape(-1, 4)
def orient(V, Q, want):
    """flip the winding of Q so the summed face normal points along `want`."""
    V = np.asarray(V); q = Q[:: max(1, len(Q) // 400)]
    n = np.cross(V[q[:, 1]] - V[q[:, 0]], V[q[:, 2]] - V[q[:, 0]]).sum(0)
    return Q if np.dot(n, want) > 0 else Q[:, ::-1]
def unit(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)

# ---------------- the heater shape ----------------
W, H, ZS = 0.62, 0.84, 0.54          # width, height, where the straight sides turn into the arcs
HW = W / 2; CX = (ZS ** 2 - HW ** 2) / (2 * HW); RA = HW + CX; RCN = 0.025
T = 0.014                             # board thickness (lime planks)
RC, KV, ZC = 0.90, 0.010, 0.46        # cross curvature radius, slight vertical dish
def sdf(x, z):
    ax = np.abs(x)
    d = np.where(z >= ZS, ax - HW, np.hypot(-ax - CX, z - ZS) - RA)
    d = np.maximum(d, z - H)
    cm = (ax > HW - RCN) & (z > H - RCN)
    return np.where(cm, np.hypot(ax - (HW - RCN), z - (H - RCN)) - RCN, d)
def yf(x, z): return RC - np.sqrt(RC * RC - x * x) + KV * ((z - ZC) / ZC) ** 2
def yb(x, z): return yf(x, z) + T
def nfront(x, z):
    e = 1e-4; gx = (yf(x + e, z) - yf(x - e, z)) / (2 * e); gz = (yf(x, z + e) - yf(x, z - e)) / (2 * e)
    return unit(np.stack([gx, -np.ones_like(gx), gz], -1))
def outline(N):
    pts = []
    a0 = math.atan2(-ZS, CX)
    pts += [(-CX + RA * math.cos(a), ZS + RA * math.sin(a)) for a in np.linspace(a0, 0, 600)]
    pts += [(HW, z) for z in np.linspace(ZS, H - RCN, 200)]
    pts += [(HW - RCN + RCN * math.cos(a), H - RCN + RCN * math.sin(a)) for a in np.linspace(0, PI / 2, 60)]
    pts += [(x, H) for x in np.linspace(HW - RCN, -HW + RCN, 400)]
    pts += [(-HW + RCN + RCN * math.cos(a), H - RCN + RCN * math.sin(a)) for a in np.linspace(PI / 2, PI, 60)]
    pts += [(-HW, z) for z in np.linspace(H - RCN, ZS, 200)]
    a1 = math.atan2(-ZS, -CX) + 2 * PI
    pts += [(CX + RA * math.cos(a), ZS + RA * math.sin(a)) for a in np.linspace(PI, a1, 600)]
    P = np.array(pts); keep = np.r_[True, np.linalg.norm(np.diff(P, axis=0), axis=1) > 1e-7]; P = P[keep][:-1]
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1); L = seg.sum(); cs = np.r_[0, np.cumsum(seg)]
    s = np.arange(N) * L / N
    Pc = np.vstack([P, P[:1]])
    O = np.stack([np.interp(s, cs, Pc[:, 0]), np.interp(s, cs, Pc[:, 1])], -1)
    t = unit(np.roll(O, -1, 0) - np.roll(O, 1, 0))
    n = np.stack([t[:, 1], -t[:, 0]], -1)
    return O, n, s, L

# ---------------- heraldry + damage (the same functions drive the 1 mm mesh and the 0.3 mm masks) ----------------
# Azure, a tower Or masoned sable, on a chief gules three bezants. Painted on gesso over the planks, then fought with.
GASH = [(-0.215, 0.705, -0.045, 0.615, 0.0028, 0.0045), (0.045, 0.795, 0.205, 0.700, 0.0022, 0.0038),
        (0.150, 0.480, 0.268, 0.395, 0.0032, 0.0050), (-0.205, 0.345, -0.118, 0.175, 0.0022, 0.0034),
        (-0.030, 0.585, 0.095, 0.552, 0.0016, 0.0030), (0.060, 0.120, 0.140, 0.205, 0.0018, 0.0032)]
DENT = [(0.185, 0.615, 0.034, 0.0018), (-0.160, 0.480, 0.030, 0.0015), (0.020, 0.250, 0.040, 0.0020),
        (-0.085, 0.760, 0.024, 0.0012), (0.240, 0.300, 0.026, 0.0014), (-0.255, 0.600, 0.022, 0.0013)]
AX, AZ = 0.135, 0.300                               # broken arrow (only with ARROW=1)
ARROW = os.environ.get("ARROW", "0") == "1"; AK = 1.0 if ARROW else 0.0
ADIR = unit(np.array([-0.26, -1.0, 0.32]))          # out of the face, back toward the archer
SEAMS = [-0.186, -0.062, 0.062, 0.186]              # five lime planks
GX, GZ = 0.110, 0.490                               # hand grip centre on the back
STRAP_RIV = [(-0.112, 0.395), (-0.088, 0.395), (-0.112, 0.585), (-0.088, 0.585),
             (-0.215, 0.696), (-0.215, 0.714), (0.215, 0.696), (0.215, 0.714)]
GRIP_RIV = [(GX, 0.415), (GX, 0.565)]
def rim_rivets():
    O, n, s, L = outline(4000)
    k = np.round(np.arange(0, L - 0.03, 0.065) / L * 4000).astype(int) % 4000
    return O[k] + n[k] * -0.0095, n[k]
RIM_RIV, _ = rim_rivets()

def box_sdf(x, z, x0, x1, z0, z1): return np.maximum(np.maximum(x0 - x, x - x1), np.maximum(z0 - z, z - z1))
def soft(d, w=0.00035): return np.clip(0.5 - d / w, 0, 1)
def masks(xs, zs):
    X, Z = np.meshgrid(xs, zs)
    out = {}
    wx = X + 0.0018 * (fbm(X * 45 + 3, Z * 45, 21, 3) - 0.5)
    wz = Z + 0.0018 * (fbm(X * 45, Z * 45 + 7, 22, 3) - 0.5)
    body = box_sdf(wx, wz, -0.115, 0.115, 0.170, 0.470)
    tw = np.minimum(body, box_sdf(wx, wz, -0.128, 0.128, 0.150, 0.172))
    tw = np.minimum(tw, box_sdf(wx, wz, -0.123, 0.123, 0.458, 0.477))
    mw = 0.042; g = (0.23 - 4 * mw) / 3
    for k in range(4):
        x0 = -0.115 + k * (mw + g); tw = np.minimum(tw, box_sdf(wx, wz, x0, x0 + mw, 0.470, 0.536))
    gate = np.minimum(box_sdf(wx, wz, -0.036, 0.036, 0.140, 0.215), np.where(wz >= 0.215, np.hypot(wx, wz - 0.215) - 0.036, 1))
    slits = np.minimum(np.minimum(box_sdf(wx, wz, -0.062, -0.050, 0.330, 0.392), box_sdf(wx, wz, 0.050, 0.062, 0.330, 0.392)),
                       box_sdf(wx, wz, -0.006, 0.006, 0.375, 0.432))
    opn = np.minimum(gate, slits)
    mas = np.zeros_like(X)
    for k in range(1, 9):
        mas = np.maximum(mas, soft(np.abs(wz - (0.170 + k * 0.0335)) - 0.0011))
    course = np.floor((wz - 0.170) / 0.0335)
    u = np.mod(wx + 0.115 + np.mod(course, 2) * 0.024, 0.048)
    mas = np.maximum(mas, soft(np.minimum(u, 0.048 - u) - 0.0011))
    mas = mas * soft(body + 0.004) * soft(-(opn - 0.005))
    bez = np.full_like(X, 1.0)
    for bx in (-0.160, 0.0, 0.160): bez = np.minimum(bez, np.hypot(wx - bx, wz - 0.752) - 0.031)
    SW = 0.0015
    sable = np.maximum.reduce([soft(np.abs(tw) - SW), soft(tw) * soft(opn - SW), mas, soft(np.abs(bez) - 0.0012)])
    gold = np.maximum(soft(tw + SW) * soft(-(opn - SW)), soft(bez + 0.0012))
    chief = soft(-(wz - 0.665 - 0.0012 * (fbm(X * 30, Z, 23, 3) - 0.5)))      # 1 in the chief (top band)
    red = chief * soft(-(bez - 0.0012))
    out['gold'], out['red'], out['sable'] = gold * (1 - sable), red * (1 - sable), sable
    # ---- damage ----
    d = sdf(X, Z)
    w = 0.06 + 0.80 * sstep(-0.034, -0.017, d) + 0.22 * sstep(-0.08, -0.03, d)
    disp = np.zeros_like(X); gm = np.zeros_like(X)
    for cx, cz, r, dep in DENT:
        rr2 = ((X - cx) ** 2 + (Z - cz) ** 2) / (r * r)
        disp += dep * np.exp(-2 * rr2); w += 0.85 * np.exp(-rr2 / 1.7)
    for x0, z0, x1, z1, dep, wd in GASH:
        vx, vz = x1 - x0, z1 - z0; L2 = vx * vx + vz * vz
        s = ((X - x0) * vx + (Z - z0) * vz) / L2
        px, pz = x0 + np.clip(s, 0, 1) * vx, z0 + np.clip(s, 0, 1) * vz
        dist = np.hypot(X - px, Z - pz)
        dist = dist * (1 + 0.35 * (fbm(X * 300, Z * 300, 24, 3) - 0.5))      # splintered, not ruler-straight
        tap = np.sin(PI * np.clip(s, 0, 1)) ** 0.55
        gg = np.clip(1 - dist / (wd / 2), 0, 1) * tap
        disp += dep * gg - dep * 0.18 * np.exp(-((dist - wd * 0.62) / (wd * 0.28)) ** 2) * tap
        gm = np.maximum(gm, sstep(0.05, 0.25, gg))
        w += 0.9 * np.exp(-(dist / (wd * 2.6)) ** 2) * np.sin(PI * np.clip(s * 0.9 + 0.05, 0, 1)) ** 0.3
    ra = np.hypot(X - AX, Z - AZ)
    ang = np.arctan2(Z - AZ, X - AX)
    spl = 0.5 + 0.5 * np.sin(ang * 9 + 3 * fbm(np.cos(ang) * 3, np.sin(ang) * 3, 25, 3))
    disp += AK * 0.0045 * np.exp(-(ra / 0.0075) ** 2) + AK * 0.0012 * np.exp(-(ra / 0.016) ** 2) * spl
    w += AK * 1.1 * np.exp(-(ra / (0.018 + 0.010 * spl)) ** 2)
    crack = np.zeros_like(X)
    for xs_ in SEAMS:
        ds = np.abs(X - xs_ - 0.0008 * (fbm(Z * 40, X, 26, 3) - 0.5))
        on = sstep(0.40, 0.48, fbm(Z * 30 + xs_ * 9, X * 0 + xs_, 27, 3))
        crack = np.maximum(crack, soft(ds - 0.00035, 0.0003) * on)
        disp += 0.00035 * np.exp(-(ds / 0.0007) ** 2) * on
        w += 0.30 * np.exp(-(ds / 0.006) ** 2) * on
    n1 = fbm(X * 115, Z * 115, 31, 4); n2 = fbm(X * 30, Z * 30, 32, 3)
    s = 0.62 * n1 + 0.38 * n2
    thr = 0.71 - 0.27 * np.clip(w, 0, 1.2)
    chip = sstep(thr, thr + 0.010, s)
    deep = sstep(thr + 0.13, thr + 0.14, s) * sstep(0.55, 0.85, w)
    deep = np.maximum(deep, AK * sstep(0.0125, 0.009, ra))
    chip = np.maximum(chip, np.maximum(gm, deep))
    out['chip'], out['deep'], out['gash'] = chip, deep * (1 - gm), gm
    disp += -0.00028 * (1 - chip) + 0.0005 * deep * (1 - gm) + 0.00005 * (fbm(X * 420, Z * 22, 33, 3) - 0.5)
    out['disp'] = disp
    # rust bleeding down from every iron head, grime along the rim and the lower half, seam cracks
    rust = np.zeros_like(X)
    for rx, rz in list(map(tuple, RIM_RIV)) + STRAP_RIV + GRIP_RIV:
        if rx < xs[0] - 0.03 or rx > xs[-1] + 0.03 or rz < zs[0] - 0.005 or rz > zs[-1] + 0.10: continue
        dz = rz - Z; dx = np.abs(X - rx)
        L = 0.03 + 0.05 * _hash(int(rx * 1e4) & 0xFFFF, int(rz * 1e4) & 0xFFFF, 3)
        st = np.exp(-(dx / (0.0025 + 0.10 * np.clip(dz, 0, None))) ** 2) * np.exp(-np.clip(dz, 0, None) / L) * (dz > -0.004)
        rust = np.maximum(rust, st * sstep(0.3, 0.6, fbm(X * 220, Z * 25, 34, 3)))
    out['rust'] = np.clip(rust * 1.2, 0, 1)
    grime = 0.75 * sstep(-0.05, -0.016, d) + 0.35 * sstep(0.40, 0.02, Z)
    out['grime'] = np.clip(grime * (0.45 + 0.8 * fbm(X * 12, Z * 12, 35, 4)), 0, 1)
    out['crack'] = crack
    out['sdf'] = d
    return out

def arrow_entry():
    return np.array([AX, float(yf(np.array(AX), np.array(AZ))), AZ])
def arrow_exit():
    return arrow_entry() - ADIR * ((T + 0.0005) / abs(ADIR[1]))
def back_disp(X, Z):
    pid = np.clip(np.floor((X + 0.31) / 0.124), 0, 4).astype(int)
    ds = np.min([np.abs(X - s) for s in SEAMS], axis=0)
    off = (np.array([_hash(k, 1, 51) for k in range(5)])[pid] - 0.5) * 0.0009
    grain = 0.00024 * (fbm(X * 380, Z * 9, 52, 4) - 0.5) * 2
    ph = np.array([_hash(k, 2, 53) for k in range(5)])[pid]
    scal = 0.00022 * np.sin(2 * PI * (Z / 0.042 + ph) + 3 * fbm(X * 20, Z * 6, 54, 3))
    groove = -0.0010 * np.exp(-(ds / 0.0010) ** 2)
    e = arrow_exit()        # exit splinters of the arrow push out of the back
    ra = np.hypot(X - e[0], Z - e[2]); ang = np.arctan2(Z - e[2], X - e[0])
    spl = (0.5 + 0.5 * np.sin(ang * 7 + 2.5 * fbm(np.cos(ang) * 2, np.sin(ang) * 2, 55, 3))) ** 2
    return off + grain + scal + groove + AK * 0.004 * np.exp(-(ra / (0.008 + 0.010 * spl)) ** 2) * spl, pid

# ---------------- generic sweeps ----------------
def sweep(path, up, prof, closed=False, caps=True):
    """prof: (M,2) closed profile in (side, up). Returns V, quads, tris, uv.
    The profile's first column is repeated at the end (and a closed path's first row), so every UV island has a real
    seam instead of a face that wraps back across the whole island (that overlap baked black)."""
    path = np.asarray(path, float)
    t = unit(np.roll(path, -1, 0) - np.roll(path, 1, 0)) if closed else unit(np.gradient(path, axis=0))
    up = unit(up - (up * t).sum(-1, keepdims=True) * t); side = unit(np.cross(t, up))
    if closed:
        path, up, side = np.vstack([path, path[:1]]), np.vstack([up, up[:1]]), np.vstack([side, side[:1]])
    N = len(path); prof = np.vstack([prof, prof[:1]]); M = len(prof)
    V = (path[:, None, :] + prof[None, :, 0, None] * side[:, None, :] + prof[None, :, 1, None] * up[:, None, :]).reshape(-1, 3)
    Q = grid_quads(N, M, False)
    pl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]
    sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    uv = np.stack(np.broadcast_arrays(pl[None, :], sl[:, None]), -1).reshape(-1, 2)
    Tr = np.zeros((0, 3), int)
    if caps and not closed:
        # each end cap gets its own vertices and its own little UV island (the profile shape), so its fan never
        # paints across the side strip's island
        K = M - 1; r0 = V[:K]; r1 = V[(N - 1) * M:(N - 1) * M + K]; pu = prof[:K] - prof[:K].min(0)
        c0 = len(V); V = np.vstack([V, r0, r1, path[0], path[-1]])
        uv = np.vstack([uv, pu, pu, pu.mean(0, keepdims=True), pu.mean(0, keepdims=True)])
        j = np.arange(K); jn = (j + 1) % K; a0, a1, ce0, ce1 = c0, c0 + K, c0 + 2 * K, c0 + 2 * K + 1
        Tr = np.vstack([np.stack([np.full(K, ce0), a0 + jn, a0 + j], -1), np.stack([np.full(K, ce1), a1 + j, a1 + jn], -1)])
    return V, Q, Tr, uv
def rrect(w, h, n, p=6.0):
    a = np.linspace(0, 2 * PI, n, endpoint=False); c, s = np.cos(a), np.sin(a)
    return np.stack([w / 2 * np.sign(c) * np.abs(c) ** (2 / p), h / 2 * np.sign(s) * np.abs(s) ** (2 / p)], -1)
def circ(r, n):
    a = np.linspace(0, 2 * PI, n, endpoint=False); return np.stack([r * np.cos(a), r * np.sin(a)], -1)
def add(parts, V, Q, Tr, uv):
    parts.append((V, Q, Tr, uv))
def emit(name, parts, mname, group=None):
    Vs, Qs, Ts, Us, off = [], [], [], [], 0
    for V, Q, Tr, uv in parts:
        Vs.append(V); Us.append(uv); Qs.append(np.asarray(Q).reshape(-1, 4) + off); Ts.append(np.asarray(Tr).reshape(-1, 3) + off); off += len(V)
    return mesh(name, np.vstack(Vs), [np.vstack(Qs), np.vstack(Ts)], mname, uv=np.vstack(Us), group=group)

def frame_of(n):
    n = unit(np.asarray(n, float)); a = unit(np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0])); return n, a, np.cross(n, a)
def dome(c, n, r, h, nu=14, nv=5):
    """rivet head: a low dome on the surface point c with normal n."""
    n, a, b = frame_of(n)
    th = np.linspace(0, 2 * PI, nu, endpoint=False); ph = np.linspace(0, PI / 2, nv + 1)[:-1]
    R = r * np.cos(ph)[:, None]; Hh = h * np.sin(ph)[:, None] - 0.0004
    V = c + R[..., None] * (np.cos(th)[None, :, None] * a + np.sin(th)[None, :, None] * b) + Hh[..., None] * n
    V = np.vstack([V.reshape(-1, 3), c + n * (h - 0.0004)])
    Q = grid_quads(nv, nu, True); top = len(V) - 1; j = np.arange(nu)
    Tr = np.stack([(nv - 1) * nu + j, (nv - 1) * nu + (j + 1) % nu, np.full(nu, top)], -1)
    return V, Q, Tr, np.zeros((len(V), 2))
def superellipsoid(nlon, nlat, e=0.18):
    th = np.linspace(-PI / 2, PI / 2, nlat + 2)[1:-1]; ph = np.linspace(-PI, PI, nlon, endpoint=False)
    sg = lambda v, m: np.sign(v) * np.abs(v) ** m
    T_, P_ = np.meshgrid(th, ph, indexing='ij')
    V = np.stack([sg(np.cos(T_), e) * sg(np.cos(P_), e), sg(np.cos(T_), e) * sg(np.sin(P_), e), sg(np.sin(T_), e)], -1).reshape(-1, 3)
    V = np.vstack([V, [0, 0, -1], [0, 0, 1]])
    Q = grid_quads(nlat, nlon, True); j = np.arange(nlon); bot, top = len(V) - 2, len(V) - 1
    Tr = np.vstack([np.stack([np.full(nlon, bot), (j + 1) % nlon, j], -1), np.stack([(nlat - 1) * nlon + j, (nlat - 1) * nlon + (j + 1) % nlon, np.full(nlon, top)], -1)])
    return V, Q, Tr
def sqrove(c, n, s, h):
    """square iron washer (rove) with a peened rivet end."""
    n, a, b = frame_of(n)
    V, Q, Tr = superellipsoid(16 if HIGH else 4, 6 if HIGH else 1, 0.25)
    P = c + V[:, 0, None] * a * s / 2 + V[:, 1, None] * b * s / 2 + (V[:, 2, None] * 0.5 + 0.5) * n * h
    return P, Q, Tr, np.stack([P[:, 0], P[:, 2]], -1)

# =====================================================================================================
# 1. board: painted front + bare back
if HIGH:
    STEP = 0.001
    xs = np.arange(-0.316, 0.3161, STEP); zs = np.arange(-0.004, 0.8441, STEP)
    nx, nz = len(xs), len(zs)
    dl, sl_ = [], []
    for c0 in range(0, nz, 128):
        mm = masks(xs, zs[c0:c0 + 128]); dl.append(mm['disp']); sl_.append(mm['sdf'])
    disp = np.vstack(dl); dd = np.vstack(sl_)
    X, Z = np.meshgrid(xs, zs)
    keep = dd < 0.0025
    Q = grid_quads(nz, nx)
    Q = Q[keep.ravel()[Q].all(1)]
    Vf = np.stack([X, yf(X, Z) + disp, Z], -1).reshape(-1, 3)
    mesh('FaceFront', Vf, [orient(Vf, Q, np.array([0, -1.0, 0]))], 'Paint')
    bd, pid = back_disp(X, Z)
    Vb = np.stack([X, yb(X, Z) + bd, Z], -1).reshape(-1, 3)
    mesh('FaceBack', Vb, [orient(Vb, Q, np.array([0, 1.0, 0]))], 'Wood', attrs={'plank': (pid.ravel() + 0.5) / 5.0})
    # the paint masks for the shader, 0.31 mm per pixel
    MX0, MX1, MZ0, MZ1, MNX = -0.32, 0.32, -0.01, 0.85, 2048
    MNZ = int(round((MZ1 - MZ0) / (MX1 - MX0) * MNX))
    mxs = np.linspace(MX0, MX1, MNX); mzs = np.linspace(MZ0, MZ1, MNZ)
    IM = {k: np.zeros((MNZ, MNX), np.float32) for k in ('gold', 'red', 'sable', 'chip', 'deep', 'gash', 'rust', 'grime', 'crack')}
    for c0 in range(0, MNZ, 96):
        mm = masks(mxs, mzs[c0:c0 + 96])
        for k in IM: IM[k][c0:c0 + 96] = mm[k]
    for name, ch in (('herald', ('gold', 'red', 'sable')), ('damage', ('chip', 'deep', 'gash')), ('weather', ('rust', 'grime', 'crack'))):
        im = bpy.data.images.new('M_' + name, MNX, MNZ, alpha=False)
        px = np.stack([IM[ch[0]], IM[ch[1]], IM[ch[2]], np.ones_like(IM[ch[0]])], -1)
        im.pixels.foreach_set(px.ravel()); im.filepath_raw = os.path.join(D, 'masks', name + '.png'); im.file_format = 'PNG'; im.save()
    json.dump({'x0': MX0, 'x1': MX1, 'z0': MZ0, 'z1': MZ1}, open(os.path.join(D, 'masks', 'masks.json'), 'w'))
else:
    O, n, s, L = outline(112)
    c = np.array([0.0, 0.47])
    rings = np.array([0.16, 0.36, 0.56, 0.74, 0.88, 1.0])
    P = (c + rings[:, None, None] * (O[None] - c)).reshape(-1, 2)
    Q = grid_quads(len(rings), len(O), True)
    j = np.arange(len(O)); ctr = len(P)
    Tr = np.stack([np.full(len(O), ctr), j, (j + 1) % len(O)], -1)
    P = np.vstack([P, c])
    for nm, fn, want, mn in (('FaceFront', yf, -1.0, 'Paint'), ('FaceBack', yb, 1.0, 'Wood')):
        V = np.stack([P[:, 0], fn(P[:, 0], P[:, 1]), P[:, 1]], -1)
        Qo, To = orient(V, Q, np.array([0, want, 0])), orient(V, Tr, np.array([0, want, 0]))
        mesh(nm, V, [Qo, To], mn, uv=np.stack([P[:, 0] * (1 if want < 0 else -1), P[:, 1]], -1))

# 2. iron rim: a U channel wrapping the board edge, split in 4 UV islands
def rim_profile(hi):
    Ro = T / 2 + 0.0022
    front = [(-0.0168, 0.0003), (-0.0166, -0.0014), (-0.0160, -0.0021)]
    k = 24 if hi else 4
    arc = [(-0.0005 + Ro * math.sin(a), T / 2 - Ro * math.cos(a)) for a in np.linspace(0, PI, k + 1)]
    flat_f = [(x, -0.0022) for x in np.linspace(-0.0152, -0.0010, 10 if hi else 1, endpoint=False)]
    flat_b = [(x, T + 0.0022) for x in np.linspace(-0.0010, -0.0152, 10 if hi else 2)[1:]]
    return np.array(front + flat_f + arc + flat_b + [(-0.0160, T + 0.0021), (-0.0166, T + 0.0014), (-0.0168, T - 0.0003)])
NR = 3600 if HIGH else 120
O, n, s, L = outline(NR)
prof = rim_profile(HIGH); M_ = len(prof)
NICK = [(0.04, 0.0055, 0.010), (0.18, 0.0045, 0.008), (0.43, 0.006, 0.011), (0.52, 0.004, 0.007), (0.66, 0.005, 0.009), (0.90, 0.0035, 0.007)]
front_side = np.where(prof[:, 1] < T / 2, 1.0, -1.0)
parts = []
for q in range(4):
    i0, i1 = q * NR // 4, (q + 1) * NR // 4 + 1
    ii = np.arange(i0, i1) % NR
    Oq, nq = O[ii], n[ii]
    sq = s[ii].copy()
    if q == 3: sq[-1] = L
    a = np.tile(prof[None, :, 0], (len(ii), 1)); b = np.tile(prof[None, :, 1], (len(ii), 1))
    if HIGH:
        u = sq / L
        for c0, dep, hw in NICK:
            dd_ = np.abs(((u - c0 + 0.5) % 1.0) - 0.5) * L
            lim = 0.0087 - dep * np.clip(1 - dd_ / hw, 0, 1) ** 0.8
            a = np.minimum(a, lim[:, None] - 0.0004 * (fbm(sq[:, None] * 900, b * 900, 61, 2) - 0.5))
            b = b + front_side[None, :] * 0.0009 * np.clip(1 - dd_ / (hw * 2.2), 0, 1)[:, None]   # the blow bent the lips in
        ham = 0.00028 * (fbm(sq[:, None] * 260, a * 900, 62, 3) - 0.5) * 2
        b = b + front_side[None, :] * ham * sstep(-0.016, -0.012, a)
    x = Oq[:, None, 0] + nq[:, None, 0] * a; z = Oq[:, None, 1] + nq[:, None, 1] * a
    y = yf(Oq[:, None, 0], Oq[:, None, 1]) + b
    V = np.stack([x, y, z], -1).reshape(-1, 3)
    Qr = grid_quads(len(ii), M_, False)
    pl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]
    uv = np.stack(np.broadcast_arrays(pl[None, :], (sq - sq[0])[:, None]), -1).reshape(-1, 2)
    # wind so the normals face away from the board's mid-plane (outward of the U)
    mid = len(ii) // 2; k_out = mid * M_ + (len(prof) // 2)
    f = Qr[(mid * (M_ - 1)) + len(prof) // 2]
    nrm = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
    outdir = np.array([nq[mid, 0], 0, nq[mid, 1]])
    if np.dot(nrm, outdir) < 0: Qr = Qr[:, ::-1]
    add(parts, V, Qr, np.zeros((0, 3), int), uv)
emit('Rim', parts, 'Iron')

# 3. rivets (high only: baked into the low poly)
if HIGH:
    parts = []
    for (rx, rz) in RIM_RIV:
        yv = float(yf(np.array(rx), np.array(rz))); nf = nfront(np.array(rx), np.array(rz))
        add(parts, *dome(np.array([rx, yv - 0.0022, rz]), nf, 0.0038, 0.0019))
        add(parts, *dome(np.array([rx, yv + T + 0.0022, rz]), -nf, 0.0030, 0.0009))
    for rx, rz in STRAP_RIV + GRIP_RIV:
        yv = float(yf(np.array(rx), np.array(rz))); r = 0.0070 if (rx, rz) in GRIP_RIV else 0.0055
        add(parts, *dome(np.array([rx, yv - 0.00028, rz]), nfront(np.array(rx), np.array(rz)), r, r * 0.34, 20, 7))
    emit('Rivets', parts, 'Iron')

# 4. leather: arm strap (enarme), guige strap, arm pad
def nback(x, z): return -nfront(x, z)
def on_back(xp, zp, lift):
    xp, zp = np.asarray(xp, float), np.asarray(zp, float)
    return np.stack([xp, yb(xp, zp), zp], -1) + nback(xp, zp) * np.asarray(lift, float).reshape(-1, 1)
def strap(path, up, w, th, stitch=True):
    nprof = 40 if HIGH else 8
    pr = rrect(w, th, nprof, 8.0)
    V, Q, Tr, uv = sweep(path, up, pr)
    if HIGH and stitch:
        N = len(path); M1 = nprof + 1; pe = np.vstack([pr, pr[:1]])
        sl = uv[:N * M1, 1].reshape(N, M1); c = pe[None, :, 0]; e = pe[None, :, 1]
        line = np.abs(np.abs(c) - (w / 2 - 0.0042))
        on = (line < 0.0007) & (np.mod(sl, 0.0045) < 0.0028)
        dz = -(0.00045 * on + 0.00015 * (line < 0.0011)) * np.sign(e)
        t = unit(np.gradient(path, axis=0)); upn = unit(up - (up * t).sum(-1, keepdims=True) * t)
        V[:N * M1] += (dz[..., None] * upn[:, None, :]).reshape(-1, 3)
    return V, Q, Tr, uv
parts = []
STEPL = 0.0012 if HIGH else 0.016
# arm strap: vertical at x -0.10, the forearm passes under its hump
nz_ = int(0.215 / STEPL) + 1; zz = np.linspace(0.383, 0.598, nz_); sp = (zz - 0.383) / 0.215
hump = np.where((sp > 0.11) & (sp < 0.89), 0.050 * np.sin(PI * np.clip((sp - 0.11) / 0.78, 0, 1)) ** 0.75, 0.0) + 0.0022
add(parts, *strap(on_back(np.full(nz_, -0.100), zz, hump), nback(np.full(nz_, -0.100), zz), 0.045, 0.0042))
# guige: lies across the top of the back, sagging a little, lifted over the buckle
nx_ = int(0.45 / STEPL) + 1; xx = np.linspace(-0.225, 0.225, nx_)
zg = 0.705 - 0.032 * np.sin(PI * (xx + 0.225) / 0.45); lg = 0.0020 + 0.0045 * np.exp(-((xx + 0.05) / 0.022) ** 2)
add(parts, *strap(on_back(xx, zg, lg), nback(xx, zg), 0.030, 0.0036))
# loose tail of the guige past the buckle
nt_ = int(0.085 / STEPL) + 1; xt = np.linspace(-0.040, 0.045, nt_)
zt = 0.705 - 0.032 * np.sin(PI * (xt + 0.225) / 0.45) - 0.004 + 0.012 * ((xt + 0.04) / 0.085) ** 2
add(parts, *strap(on_back(xt, zt, np.full(nt_, 0.0058)), nback(xt, zt), 0.026, 0.0034))
# arm pad: a quilted leather cushion between strap and grip
nu, nv = (180, 160) if HIGH else (12, 10)
tu = np.sin(np.linspace(-PI / 2, PI / 2, nu)); tv = np.sin(np.linspace(-PI / 2, PI / 2, nv))
U, Vv = np.meshgrid(tu, tv)
px_ = 0.0025 + U * 0.0725; pz_ = 0.490 + Vv * 0.064
hp = 0.017 * (np.clip(1 - np.abs(U) ** 6, 0, 1) ** 0.35) * (np.clip(1 - np.abs(Vv) ** 6, 0, 1) ** 0.35)
if HIGH:
    l1 = np.abs(np.mod((px_ + pz_) / 0.032, 1) - 0.5) * 0.032; l2 = np.abs(np.mod((px_ - pz_) / 0.032, 1) - 0.5) * 0.032
    inner = (np.abs(U) < 0.88) & (np.abs(Vv) < 0.86)
    hp = hp - 0.0045 * np.exp(-(np.minimum(l1, l2) / 0.0016) ** 2) * inner * (hp / 0.017)
    hp = hp - 0.0004 * ((np.abs(np.abs(U) - 0.93) < 0.012) | (np.abs(np.abs(Vv) - 0.92) < 0.013)) * (np.mod(px_ + pz_, 0.004) < 0.0025)
    hp = hp + 0.0006 * (fbm(px_ * 90, pz_ * 90, 71, 3) - 0.5)
hp = hp - 0.001
pp = on_back(px_.ravel(), pz_.ravel(), hp.ravel())
add(parts, pp, orient(pp, grid_quads(nv, nu), np.array([0, 1.0, 0])), np.zeros((0, 3), int), np.stack([px_.ravel(), pz_.ravel()], -1))
emit('Leather', parts, 'Leather')

# 5. hand grip: wooden bar on two blocks, leather-wrapped between them
yg = float(yb(np.array(GX), np.array(GZ))); GRIP = np.array([GX, yg + 0.040, GZ])
parts_w, parts_l = [], []
for zb in (0.415, 0.565):
    V, Q, Tr = superellipsoid(24 if HIGH else 6, 10 if HIGH else 2, 0.22)
    cc = np.array([GX, float(yb(np.array(GX), np.array(zb))) + 0.028, zb])
    P = cc + V * np.array([0.017, 0.030, 0.015])
    add(parts_w, P, Q, Tr, np.stack([P[:, 0] + P[:, 1] * 0.5, P[:, 2]], -1))
nseg = 40 if HIGH else 12
zr = np.linspace(0.400, 0.580, 180) if HIGH else np.array([0.400, 0.430, 0.433, 0.547, 0.550, 0.580])
path = np.stack([np.full_like(zr, GX), np.full_like(zr, GRIP[1]), zr], -1)
V, Q, Tr, uv = sweep(path, np.tile([0, 1.0, 0], (len(zr), 1)), circ(1.0, nseg))
rad = np.where((zr > 0.431) & (zr < 0.549), 0.0160, 0.0142)
rad2 = np.repeat(rad[:, None], nseg + 1, 1)
if HIGH:
    ang = np.linspace(0, 2 * PI, nseg + 1)
    ph = np.mod(zr[:, None] / 0.013 + ang[None, :] / (2 * PI), 1.0)
    wrap = (zr[:, None] > 0.431) & (zr[:, None] < 0.549)
    rad2 = rad2 + wrap * (0.0007 * np.abs(np.sin(PI * ph)) ** 0.4 - 0.0005 * (ph < 0.06))
Vc = V[:len(zr) * (nseg + 1)].reshape(len(zr), nseg + 1, 3)
V[:len(zr) * (nseg + 1)] = (path[:, None, :] + (Vc - path[:, None, :]) * rad2[..., None]).reshape(-1, 3)
Gr = V[:len(zr) * (nseg + 1)].reshape(len(zr), nseg + 1, 3); c0_ = len(zr) * (nseg + 1)
V[c0_:c0_ + nseg] = Gr[0, :nseg]; V[c0_ + nseg:c0_ + 2 * nseg] = Gr[-1, :nseg]   # the end caps follow the scaled grip
uv[:len(zr) * (nseg + 1), 0] *= 0.015
uv[len(zr) * (nseg + 1):] *= 0.015          # the end caps were drawn from the unit circle: scale them to the real ~15 mm radius
if HIGH:   # the wrap and the wooden ends are different materials on the high poly
    fq = np.repeat((zr[:-1] > 0.431) & (zr[:-1] < 0.549), nseg)
    add(parts_l, V, Q[fq], np.zeros((0, 3), int), uv)
    add(parts_w, V, Q[~fq], Tr, uv)
else:
    add(parts_w, V, Q, Tr, uv)
emit('GripWood', parts_w, 'Wood')
if parts_l: emit('GripWrap', parts_l, 'Leather')

# 6. iron fittings on the back: roves at the strap ends, the guige buckle
parts = []
for rx, rz in STRAP_RIV:
    cc = np.array([rx, float(yb(np.array(rx), np.array(rz))), rz]); nb = nback(np.array(rx), np.array(rz))
    lift = 0.0042 if abs(rx) < 0.15 else 0.0036
    add(parts, *sqrove(cc + nb * (lift + 0.0016), nb, 0.0105, 0.0018))
bx = -0.050; bz = 0.705 - 0.032 * math.sin(PI * (bx + 0.225) / 0.45)
cb = np.array([bx, float(yb(np.array(bx), np.array(bz))), bz]) + np.array([0, 1.0, 0]) * 0.0082
a_ = np.linspace(0, 2 * PI, 96 if HIGH else 12, endpoint=False)
fr = np.stack([0.016 * np.sign(np.cos(a_)) * np.abs(np.cos(a_)) ** 0.35, np.zeros_like(a_), 0.022 * np.sign(np.sin(a_)) * np.abs(np.sin(a_)) ** 0.35], -1)
V, Q, Tr, uv = sweep(cb + fr, np.tile([0, 1.0, 0], (len(a_), 1)), circ(0.0026, 16 if HIGH else 6), closed=True, caps=False)
add(parts, V, Q, Tr, uv)
nt2 = 20 if HIGH else 2
tg = np.stack([np.linspace(bx - 0.016, bx + 0.010, nt2), np.full(nt2, cb[1] + 0.0016), np.full(nt2, bz)], -1)
add(parts, *sweep(tg, np.tile([0, 1.0, 0], (nt2, 1)), circ(0.0016, 12 if HIGH else 5)))
emit('Fittings', parts, 'Iron')

# 7. broken arrow: ash shaft snapped 15 cm out, the bodkin head through the back
if ARROW:
    E = arrow_entry(); Xb = arrow_exit()
    nsh = 120 if HIGH else 3; nsd = 32 if HIGH else 7
    ts = np.linspace(-0.004, 0.150, nsh)
    path = E[None, :] + ts[:, None] * ADIR[None, :]
    upv = np.tile(unit(np.cross(ADIR, [1.0, 0, 0])), (nsh, 1))
    V, Q, Tr, uv = sweep(path, upv, circ(0.0042, nsd), caps=False)
    uv[:, 0] *= 1.0
    brk = np.zeros(len(V))
    if HIGH:   # splintered break: fibre lengths vary around the shaft, the end flares a little
        Vg = V.reshape(nsh, nsd, 3); ang = np.linspace(0, 2 * PI, nsd, endpoint=False)
        jag = 0.016 * fbm(np.cos(ang) * 4 + 2, np.sin(ang) * 4, 81, 4) + 0.006 * (np.mod(np.arange(nsd), 3) == 0)
        span = (0.022 + jag[None, :]) / 0.150
        endz = np.clip((ts[:, None] / 0.150 - (1 - span)) / span, 0, 1)
        Vg = path[:, None, :] + (Vg - path[:, None, :]) * (1 + 0.10 * endz[..., None] ** 2) + ADIR * (jag[None, :, None] * endz[..., None] * 1.0)
        V = Vg.reshape(-1, 3); brk = endz.ravel()
    c0 = len(V); V = np.vstack([V, path[-1] + ADIR * 0.004]); uv = np.vstack([uv, [0, 0]]); brk = np.r_[brk, 1.0]
    j = np.arange(nsd); Tr = np.stack([np.full(nsd, c0), (nsh - 1) * nsd + j, (nsh - 1) * nsd + (j + 1) % nsd], -1)
    mesh('ArrowShaft', V, [Q, Tr], 'Shaft', uv=uv, attrs={'brk': brk}, group='arrow')
    hl = 0.034; th_ = np.linspace(0, 1, 40 if HIGH else 3)
    hp_ = Xb[None, :] + (th_ * hl - 0.012)[:, None] * -ADIR[None, :]
    sq = rrect(0.0074, 0.0074, 32, 3.0) if HIGH else np.array([[0.0037, 0], [0, 0.0037], [-0.0037, 0], [0, -0.0037]])
    V, Q, Tr, uv = sweep(hp_, np.tile(unit(np.cross(ADIR, [1.0, 0, 0])), (len(th_), 1)), sq, caps=False)
    taper = np.clip(1 - np.clip((th_ - 0.25) / 0.75, 0, 1), 0.02, 1) ** 1.1
    Vh = V.reshape(len(th_), len(sq), 3); V = (hp_[:, None, :] + (Vh - hp_[:, None, :]) * taper[:, None, None]).reshape(-1, 3)
    c0 = len(V); V = np.vstack([V, hp_[-1] - ADIR * 0.001]); uv = np.vstack([uv, [0, 0]])
    j = np.arange(len(sq)); Tr = np.stack([np.full(len(sq), c0), (len(th_) - 1) * len(sq) + (j + 1) % len(sq), (len(th_) - 1) * len(sq) + j], -1)
    mesh('ArrowHead', V, [Q, Tr], 'Iron', uv=uv, group='arrow')

json.dump({'grip': GRIP.tolist(), 'grip_axis': [0, 0, 1], 'width': W, 'height': H}, open(os.path.join(D, 'heater_meta.json'), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Heater_%s.blend' % RES))
print('BUILD OK')
