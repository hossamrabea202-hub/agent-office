# #539 Tentacle spore base (adjustedfilm, 2026-11-06). The ground where the arm tore out: heaved crust plates, rock slabs thrust outward, roots gripping the rubble,
# spore pods growing from the fractures. Nominal size in metres: trunk radius 30, outer radius 95; the placement script scales it to each tentacle. Nanite mesh, no UVs baked:
# vertex colour = albedo (RGB) and roughness (A), UV0 = box projection for the tiling detail textures.
#   blender -b --factory-startup -P gen_sporebase.py -- <out.fbx> <seed> [preview.blend]
# Layers in physical order (knowledge base rule 3): base rock and soil -> strata -> fresh fractures -> cavities -> up-facing dust -> wet ooze near the wound -> spore stain.
import bpy, sys, math, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; OUT, SEED = a[0], int(a[1]); BLEND = a[2] if len(a) > 2 else None
rng = np.random.default_rng(SEED); R0, ROUT = 30.0, 95.0
def s2l(c): c = np.asarray(c, float) / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
PERM = rng.permutation(4096); GRAD = rng.random(4096)
def vnoise(x, y, z=0.0):
    x, y = np.asarray(x, float), np.asarray(y, float); z = np.broadcast_to(z, x.shape).astype(float)
    i, j, k = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int); u, v, w = x - i, y - j, z - k
    u, v, w = u * u * (3 - 2 * u), v * v * (3 - 2 * v), w * w * (3 - 2 * w)
    h = lambda a_, b_, c_: GRAD[PERM[(PERM[(PERM[a_ & 4095] + b_) & 4095] + c_) & 4095]]
    return ((h(i, j, k) * (1 - u) + h(i + 1, j, k) * u) * (1 - v) + (h(i, j + 1, k) * (1 - u) + h(i + 1, j + 1, k) * u) * v) * (1 - w) + ((h(i, j, k + 1) * (1 - u) + h(i + 1, j, k + 1) * u) * (1 - v) + (h(i, j + 1, k + 1) * (1 - u) + h(i + 1, j + 1, k + 1) * u) * v) * w
def fbm(x, y, z=0.0, oct_=5, lac=2.03, gain=0.5):
    t, amp, tot = 0.0, 1.0, 0.0
    for o in range(oct_):
        t = t + amp * (vnoise(x, y, z) - 0.5); tot += amp; x, y, z = x * lac + 17.3, y * lac + 9.1, np.asarray(z) * lac + 3.7; amp *= gain
    return t / tot * 2.0
sstep = lambda a_, b_, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a_) / (b_ - a_), 0, 1))
PARTS = []     # (verts, faces, rgb linear, roughness)
def add(v, f, c, r): PARTS.append((v, f, c, r))
# ---------- 1 the heaved crust: a polar height field, cut into plates that tilt away from the wound
NR, NA = 300, 1180
rr = R0 - 8.0 + (ROUT - R0 + 8.0) * (np.linspace(0, 1, NR) ** 1.25); th = np.linspace(0, 2 * math.pi, NA, endpoint=False)
TH, RR = np.meshgrid(th, rr); X, Y = RR * np.cos(TH), RR * np.sin(TH); U = np.clip((RR - R0) / (ROUT - R0), 0, 1)
sites = []
while len(sites) < 420:
    r_ = R0 + (ROUT - R0) * rng.random() ** 1.5; t_ = rng.random() * 2 * math.pi; sites.append((r_ * math.cos(t_), r_ * math.sin(t_)))
sites = np.array(sites); wx, wy = X + 3.0 * fbm(X * 0.07, Y * 0.07, 1.0, 3), Y + 3.0 * fbm(X * 0.07, Y * 0.07, 5.0, 3)
F1, F2, IDX = np.full(X.shape, 1e9), np.full(X.shape, 1e9), np.zeros(X.shape, int)
sa = np.arctan2(sites[:, 1], sites[:, 0]); WR = np.hypot(wx, wy); WA = np.arctan2(wy, wx); SRr = np.hypot(sites[:, 0], sites[:, 1])
for n_, (sx, sy) in enumerate(sites):
    da = (WA - sa[n_] + math.pi) % (2 * math.pi) - math.pi; stretch = 1.0 + 2.6 * np.clip((WR - R0) / 40.0, 0, 1)         # radial shards, longer further out
    d = np.hypot((WR - SRr[n_]) / stretch, da * WR); nearer = d < F1
    F2 = np.where(nearer, F1, np.minimum(F2, d)); IDX = np.where(nearer, n_, IDX); F1 = np.minimum(F1, d)
edge = F2 - F1
sr = np.hypot(sites[:, 0], sites[:, 1]); su = np.clip((sr - R0) / (ROUT - R0), 0, 1); force = (1 - su) ** 1.6
off, tilt = (0.3 + 3.2 * rng.random(len(sites))) * force, (0.05 + 0.30 * rng.random(len(sites))) * force
nx, ny = sites[:, 0] / sr, sites[:, 1] / sr
along = (X - sites[IDX, 0]) * nx[IDX] + (Y - sites[IDX, 1]) * ny[IDX]            # the outer edge of each plate rides high
mound = 7.5 * np.exp(-((RR - R0 - 6.0) / 13.0) ** 2) + 3.5 * (1 - U) ** 2
H = mound + off[IDX] + along * tilt[IDX] * 0.9
crackw = 0.22 + 1.5 * (1 - U) ** 2; crack = 1 - sstep(0.0, crackw, edge + 0.5 * fbm(X * 0.6, Y * 0.6, 12.0, 3))
H = H - crack * (0.5 + 5.0 * (1 - U) ** 1.5)
H = H + 2.0 * fbm(X * 0.07, Y * 0.07, 2.0, 5) + 0.7 * fbm(X * 0.35, Y * 0.35, 3.0, 5) * (1 - 0.5 * U) + 0.16 * fbm(X * 1.6, Y * 1.6, 4.0, 3)
EDGE = 0.62 + 0.26 * (0.5 + fbm(np.cos(TH) * 2.2, np.sin(TH) * 2.2, 21.0, 4))                                 # a wandering line, so no circle shows
fade = sstep(EDGE - 0.28, EDGE, U); H = H * (1 - fade) - 2.6 * sstep(EDGE - 0.06, EDGE + 0.1, U)     # dives under the terrain
H = np.where(RR < R0 + 3, H - (R0 + 3 - RR) * 1.5, H)                          # the throat falls away under the arm
V = np.stack([X, Y, H], -1).reshape(-1, 3); ii = np.arange(NR * NA).reshape(NR, NA); F = []
a0, b0, c0, d0 = ii[:-1, :].ravel(), ii[:-1, np.r_[1:NA, 0]].ravel(), ii[1:, np.r_[1:NA, 0]].ravel(), ii[1:, :].ravel()
F = np.stack([a0, b0, c0, d0], 1)
# albedo: soil, strata in the cracks' walls, dust on the plates, wet at the wound
n1, n2 = fbm(X * 0.11, Y * 0.11, 7.0, 5), fbm(X * 0.9, Y * 0.9, 8.0, 3)
soil = s2l([72, 60, 47]) * (1 + 0.35 * n1 + 0.2 * n2)[..., None]; rockc = s2l([104, 96, 86]) * (1 + 0.4 * n1 + 0.22 * n2)[..., None]
plate_rock = (rng.random(len(sites)) < 0.62)[IDX] * (1 - sstep(0.12, 0.42, U + 0.25 * n1)); streak = sstep(0.1, 0.45, fbm(np.cos(TH) * 26, np.sin(TH) * 26, RR * 0.012, 3)) * (1 - sstep(0.2, 0.8, U)); m_rock = np.clip(plate_rock + crack * 0.7 * (1 - U) + 0.4 * streak, 0, 1)[..., None]
C = soil * (1 - m_rock) + rockc * m_rock
strata = 0.5 + 0.5 * np.sin(H * 3.4 + 2.5 * n1); C = C * (1 + (0.22 * strata - 0.11)[..., None] * m_rock)
C = C * (1 - 0.32 * crack)[..., None]                                          # cavities, restrained
wound = np.exp(-np.clip(RR - R0, 0, None) / 7.0) * (0.7 + 0.5 * n1); wetc = s2l([58, 32, 34]); wm = np.clip(wound, 0, 0.9)[..., None]
stain = sstep(0.05, 0.55, fbm(X * 0.04, Y * 0.04, 11.0, 4) + 0.55 * (1 - U) - 0.25)[..., None] * 0.55; stainc = s2l([142, 112, 70])
C = C * (1 - stain) + (C * 0.45 + stainc * 0.55) * stain; C = C * (1 - wm) + wetc * wm
RO = np.clip(0.92 - 0.65 * wm[..., 0] - 0.12 * m_rock[..., 0] + 0.08 * n2, 0.22, 1.0)
add(V, F, C.reshape(-1, 3), RO.ravel())
def height(x, y):       # sample the crust
    r_ = np.hypot(x, y); i_ = np.clip(np.searchsorted(rr, r_), 0, NR - 1); j_ = int((math.atan2(y, x) % (2 * math.pi)) / (2 * math.pi) * NA) % NA
    return float(H[i_, j_])
# ---------- 2 rock slabs thrust up and outward
def slab(L, W, T, seed, S=22):
    g = np.linspace(-0.5, 0.5, S); vs, fs, off_ = [], [], 0
    for ax, sg in ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)):
        A_, B_ = np.meshgrid(g, g); P = np.zeros((S * S, 3)); o_ = [q for q in range(3) if q != ax]; P[:, ax] = 0.5 * sg; P[:, o_[0]] = A_.ravel(); P[:, o_[1]] = B_.ravel()
        q = np.arange(S * S).reshape(S, S) + off_; ff = np.stack([q[:-1, :-1].ravel(), q[:-1, 1:].ravel(), q[1:, 1:].ravel(), q[1:, :-1].ravel()], 1)
        if (sg > 0) == (ax == 1): ff = ff[:, ::-1]
        vs.append(P); fs.append(ff); off_ += S * S
    P = np.concatenate(vs); Fq = np.concatenate(fs); P = P / np.maximum(np.abs(P).max(1, keepdims=True), 1e-6) * 0.5     # stays a box
    P = P * np.array([L, W, T])
    for _ in range(7):                                                          # fractures: random planes shear the block into a broken shard
        nrm = rng.normal(size=3); nrm /= np.linalg.norm(nrm); dist = rng.random() * 0.22 * L + 0.16 * min(L, W)
        over = P @ nrm - dist; P = P - np.where(over > 0, over, 0)[:, None] * nrm
    z_ = seed * 13.1; P = P + 0.045 * L * np.stack([fbm(P[:, 1] * 0.12, P[:, 2] * 0.12, z_, 4), fbm(P[:, 0] * 0.12, P[:, 2] * 0.12, z_ + 1, 4), fbm(P[:, 0] * 0.12, P[:, 1] * 0.12, z_ + 2, 4)], 1)
    P = P + 0.5 * np.stack([fbm(P[:, 1] * 0.7, P[:, 2] * 0.7, z_ + 3, 4), fbm(P[:, 0] * 0.7, P[:, 2] * 0.7, z_ + 4, 4), fbm(P[:, 0] * 0.7, P[:, 1] * 0.7, z_ + 5, 4)], 1)
    return P, Fq
def rot(ax, an):
    c_, s_ = math.cos(an), math.sin(an); x, y, z = ax
    return np.array([[c_ + x * x * (1 - c_), x * y * (1 - c_) - z * s_, x * z * (1 - c_) + y * s_], [y * x * (1 - c_) + z * s_, c_ + y * y * (1 - c_), y * z * (1 - c_) - x * s_], [z * x * (1 - c_) - y * s_, z * y * (1 - c_) + x * s_, c_ + z * z * (1 - c_)]])
SLABS = []
for k_ in range(58):
    t_ = rng.random() * 2 * math.pi; rad = R0 + 2 + (ROUT * 0.62 - R0) * rng.random() ** 1.7; nearw = 1 - (rad - R0) / (ROUT * 0.62 - R0)
    L, W, T = (8 + 34 * nearw * rng.random() + 6 * rng.random()), (5 + 15 * rng.random() * (0.4 + nearw)), (1.6 + 5.5 * rng.random())
    P, Fq = slab(L, W, T, k_); strat = P[:, 2] / T
    out = np.array([math.cos(t_), math.sin(t_), 0.0]); side = np.array([-out[1], out[0], 0.0])
    P = P @ np.array([[0, 0, 1.0], [0, 1.0, 0], [-1.0, 0, 0]]).T if False else P
    lean = math.radians(18 + 58 * nearw * rng.random() + 8 * rng.random())       # long axis lies radial; the inner end is lifted by the eruption
    Rm = rot(side, -lean) @ np.column_stack([out, side, [0, 0, 1.0]]) @ rot((0, 0, 1.0), rng.normal(0, 0.35)); P = P @ Rm.T
    c = np.array([rad * math.cos(t_), rad * math.sin(t_), height(rad * math.cos(t_), rad * math.sin(t_)) + 0.12 * L * math.sin(lean)]); P = P + c
    SLABS.append(c)
    n3 = fbm(P[:, 0] * 0.3, P[:, 1] * 0.3, P[:, 2] * 0.3, 4); band = 0.5 + 0.5 * np.sin(strat * 19 + 2.0 * n3)
    Cc = s2l([112, 104, 93]) * (1 + 0.32 * n3 + (0.25 * band - 0.12))[:, None]
    nz = np.clip((P[:, 2] - P[:, 2].min()) / max(1.0, np.ptp(P[:, 2])), 0, 1)
    under = (1 - nz) ** 3; Cc = Cc * (1 - 0.55 * under[:, None]) + s2l([62, 52, 42]) * 0.55 * under[:, None]    # soil clings low, where it was buried
    add(P, Fq, Cc, np.clip(0.86 + 0.1 * n3 - 0.25 * under * 0.0, 0.5, 1.0))
# ---------- 3 rubble skirt
for k_ in range(240):
    t_ = rng.random() * 2 * math.pi; rad = R0 + 1 + (ROUT * 0.8 - R0) * rng.random() ** 1.6; s_ = 0.5 + 3.4 * rng.random() ** 2.4
    P, Fq = slab(s_ * (1 + rng.random()), s_, s_ * (0.5 + 0.6 * rng.random()), 100 + k_, S=7); keep = None
    # a much lighter block is enough: reuse the same builder, then drop to a coarse stride would break faces, so rubble stays low in number
    Rr = rot(tuple(rng.normal(size=3) / max(1e-6, np.linalg.norm(rng.normal(size=3)))), 0) if False else np.eye(3)
    ang = rng.random() * math.pi; ax = rng.normal(size=3); ax /= np.linalg.norm(ax); P = P @ rot(ax, ang).T
    x_, y_ = rad * math.cos(t_), rad * math.sin(t_); P = P + np.array([x_, y_, height(x_, y_) + 0.15 * s_]); n3 = fbm(P[:, 0] * 0.4, P[:, 1] * 0.4, P[:, 2] * 0.4, 3)
    add(P, Fq, s2l([100, 92, 82]) * (1 + 0.35 * n3)[:, None], np.clip(0.88 + 0.1 * n3, 0.5, 1.0))
# ---------- 4 roots: the arm gripping the rubble
def tube(pts, r0, r1, seg=9):
    pts = np.asarray(pts); n_ = len(pts); tan = np.gradient(pts, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True); up = np.array([0, 0, 1.0])
    sd = np.cross(tan, up); sd /= np.maximum(np.linalg.norm(sd, axis=1, keepdims=True), 1e-6); nr = np.cross(sd, tan); v = []
    for i_ in range(n_):
        rad = r0 + (r1 - r0) * (i_ / (n_ - 1)) ** 0.8; rad = rad * (1 + 0.12 * math.sin(i_ * 1.9))
        for j_ in range(seg):
            an = 2 * math.pi * j_ / seg; v.append(pts[i_] + rad * (math.cos(an) * sd[i_] + math.sin(an) * nr[i_]))
    q = np.arange(n_ * seg).reshape(n_, seg); f = np.stack([q[:-1, :].ravel(), q[:-1, np.r_[1:seg, 0]].ravel(), q[1:, np.r_[1:seg, 0]].ravel(), q[1:, :].ravel()], 1)
    return np.array(v), f
for k_ in range(26):
    t_ = 2 * math.pi * k_ / 26 + rng.normal(0, 0.1); leng = 22 + 42 * rng.random(); N_ = 46; pts = []; wob = rng.random() * 9
    for i_ in range(N_):
        u = i_ / (N_ - 1); rad = R0 - 2 + leng * u; an = t_ + 0.28 * math.sin(u * 5 + wob) * u
        x_, y_ = rad * math.cos(an), rad * math.sin(an); pts.append((x_, y_, height(x_, y_) + 1.4 * (1 - u) + 0.5 * math.sin(u * 13 + wob) - 1.2 * u ** 6))
    pts = np.array(pts); kz = np.ones(11) / 11.0; pad = np.r_[np.full(5, pts[0, 2]), pts[:, 2], np.full(5, pts[-1, 2])]; pts[:, 2] = np.convolve(pad, kz, 'valid') + 0.25
    P, Fq = tube(pts, 2.3 * (0.5 + 0.7 * rng.random()), 0.12); n3 = fbm(P[:, 0] * 0.35, P[:, 1] * 0.35, P[:, 2] * 0.35, 4)
    add(P, Fq, s2l([70, 30, 33]) * (1 + 0.45 * n3)[:, None], np.clip(0.5 + 0.25 * n3, 0.25, 1.0))
# ---------- 5 spore pods: clusters in the fractures and on the rim, ripe ones pale at the tip with a dark pore
def pod(hgt, rad, seed, burst):
    SU, SV = 18, 15; u = np.linspace(0, 1, SV)[:, None]; v = np.linspace(0, 2 * math.pi, SU, endpoint=False)[None, :]
    prof = np.sin(np.pi * np.clip(u, 0, 1) ** 0.85) ** 0.62
    if burst: prof = np.where(u > 0.62, prof * (0.72 + 0.5 * (u - 0.62)), prof)
    cx, cy = rad * np.cos(v), rad * np.sin(v); ph = seed * 1.7
    cxx, cyy = np.broadcast_to(cx, (SV, SU)), np.broadcast_to(cy, (SV, SU)); uu = np.broadcast_to(u, (SV, SU))
    lump = 1 + 0.32 * (vnoise(cxx * 1.4 + ph, cyy * 1.4, uu * 3.0) - 0.5) + 0.12 * (vnoise(cxx * 5 + ph, cyy * 5, uu * 11.0) - 0.5)
    x_, y_ = prof * cx * lump, prof * cy * lump; z_ = hgt * u * np.ones_like(v)
    if burst:                                                                   # the top tears open: jagged lips and a sunken hollow
        vv = np.broadcast_to(v, (SV, SU)); tear = 0.82 + 0.16 * vnoise(np.cos(vv) * 3 + ph, np.sin(vv) * 3, 2.0); inner = uu > 0.8; d_ = (uu - 0.8) / 0.2
        z_ = np.where(inner, hgt * (tear - 0.62 * np.clip(d_, 0, 1) ** 1.1), np.minimum(z_, hgt * tear)); shrink = np.where(inner, 1 - 0.92 * d_, 1.0); x_, y_ = x_ * shrink, y_ * shrink
    q = np.arange(SU * SV).reshape(SV, SU); f = np.stack([q[:-1, :].ravel(), q[:-1, np.r_[1:SU, 0]].ravel(), q[1:, np.r_[1:SU, 0]].ravel(), q[1:, :].ravel()], 1)
    return np.stack([x_, y_, z_], -1).reshape(-1, 3), f, uu.ravel()
for k_ in range(64):
    t_ = rng.random() * 2 * math.pi; rad = R0 + 2 + (ROUT * 0.56 - R0) * rng.random() ** 1.5; n_p = 9 + int(rng.random() * 22); spread = 2.0 + 3.6 * rng.random(); ripe = rng.random()
    for j_ in range(n_p):
        s_ = 0.45 + 2.3 * rng.random() ** 1.8; dx, dy = rng.normal(0, spread, 2); x_, y_ = rad * math.cos(t_) + dx, rad * math.sin(t_) + dy; burst = rng.random() < 0.18 + 0.3 * ripe
        P, Fq, u = pod(s_ * (1.2 + 1.0 * rng.random()), s_, 300 + k_ * 40 + j_, burst); ax = rng.normal(size=3); ax[2] = 0; ax /= np.linalg.norm(ax); P = P @ rot(ax, rng.normal(0, 0.3)).T + np.array([x_, y_, height(x_, y_) - 0.25 * s_])
        n3 = fbm(P[:, 0] * 0.8, P[:, 1] * 0.8, P[:, 2] * 0.8, 4); spots = sstep(0.2, 0.34, fbm(P[:, 0] * 8.0, P[:, 1] * 8.0, P[:, 2] * 8.0, 2)); veins = 1 - sstep(0.0, 0.1, np.abs(fbm(P[:, 0] * 1.5, P[:, 1] * 1.5, P[:, 2] * 1.5, 3)))
        Cc = s2l([104, 74, 62]) * (1 + 0.35 * n3)[:, None]; Cc = Cc * (1 - 0.8 * spots[:, None]) + s2l([168, 150, 112]) * 0.8 * spots[:, None]; Cc = Cc * (1 - 0.35 * veins)[:, None]
        low_ = (1 - sstep(0.0, 0.3, u))[:, None]; Cc = Cc * (1 - low_) + s2l([66, 54, 42]) * low_; rg_ = 0.55 + 0.2 * n3 + 0.3 * low_[:, 0]
        if burst: hol = sstep(0.8, 0.9, u)[:, None]; Cc = Cc * (1 - hol) + s2l([48, 30, 28]) * hol; rg_ = rg_ * (1 - 0.35 * hol[:, 0])
        add(P, Fq, Cc, np.clip(rg_, 0.2, 1.0))
# ---------- build
vs, fs, cs, ro, ofs = [], [], [], [], 0
for v_, f_, c_, r_ in PARTS:
    vs.append(v_); fs.append(np.asarray(f_) + ofs); cs.append(np.clip(c_, 0, 1)); ro.append(np.broadcast_to(r_, (len(v_),))); ofs += len(v_)
V = np.concatenate(vs); Fq = np.concatenate(fs); C = np.concatenate(cs); RG = np.concatenate(ro)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('SM_TentacleSporeBase'); me.vertices.add(len(V)); me.vertices.foreach_set('co', (V * 100.0).astype(np.float32).ravel())   # centimetres
me.loops.add(len(Fq) * 4); me.polygons.add(len(Fq)); me.loops.foreach_set('vertex_index', Fq.astype(np.int32).ravel()); me.polygons.foreach_set('loop_start', np.arange(len(Fq), dtype=np.int32) * 4)
me.update(); me.validate(verbose=False)
col = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); col.data.foreach_set('color', np.column_stack([C, RG]).astype(np.float32).ravel())   # linear values; Blender stores them as sRGB bytes on export
Lv = np.array(me.loops.foreach_get) if False else None
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv); P_ = V[lv]; uvl = me.uv_layers.new(name='UV0')
fn = np.empty(len(me.polygons) * 3, np.float32); me.polygons.foreach_get('normal', fn); fn = np.abs(fn.reshape(-1, 3)); dom = np.repeat(np.argmax(fn, 1), 4)
uv = np.where(dom[:, None] == 2, P_[:, [0, 1]], np.where(dom[:, None] == 0, P_[:, [1, 2]], P_[:, [0, 2]])) / 5.0                                 # 1 tile = 5 m, nominal
uvl.data.foreach_set('uv', uv.astype(np.float32).ravel())
me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool)); me.set_sharp_from_angle(angle=math.radians(52)) if hasattr(me, 'set_sharp_from_angle') else None; me.update()
ob = bpy.data.objects.new('SM_TentacleSporeBase', me); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', use_tspace=False, bake_anim=False, add_leaf_bones=False, colors_type='SRGB')
if BLEND: bpy.ops.wm.save_as_mainfile(filepath=BLEND)
lum = (C @ np.array([0.2126, 0.7152, 0.0722])); sr_ = np.where(lum <= 0.0031308, 12.92 * lum, 1.055 * lum ** (1 / 2.4) - 0.055) * 255
print('SPORE seed %d | verts %d quads %d | albedo sRGB luminance p1 %.0f p50 %.0f p99 %.0f, below 30: %.2f%%, above 240: %.2f%% | roughness %.2f..%.2f std %.2f | size %.0f m' % (SEED, len(V), len(Fq), np.percentile(sr_, 1), np.percentile(sr_, 50), np.percentile(sr_, 99), (sr_ < 30).mean() * 100, (sr_ > 240).mean() * 100, RG.min(), RG.max(), RG.std(), np.ptp(V[:, 0])))
