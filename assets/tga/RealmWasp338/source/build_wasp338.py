# Realm wasp v2 (#338, TGA PC, 2026-11-06): the zombie hornet rebuilt to the film creature method
# (handoffs/knowledge/research_notes/creature_studio_method.md). Original procedural work.
#   blender -b --factory-startup -P build_wasp338.py      ->  <WORK>/wasp338_rig.blend
# Same 32 bone names as v1 SK_RealmWasp (+ wingblur_L/R), same axes: faces -Y in Blender (+Y in UE), metres, Z up, root on
# the ground under the body, body at Z0. Anatomy in true order: head (emarginate eyes, ocelli, toothed mandibles, elbowed
# 13-segment antennae), pronotum collar, mesoscutum, scutellum, propodeum, petiole, 6 nested gaster shells over wet tissue,
# sting + sheath; legs = coxa, trochanter, femur, tibia + spurs, 5 tarsomeres, 2 claws. Zombie story (rot breaks the soft
# parts first): the gaster gapes at joint 3/4 over tissue, a hole is broken through tergite 4 (right side), Ophiocordyceps-style
# fungal stalks grow out of the joints, setae (real strands) on head/thorax/legs. Wings: veined, corrugated membranes plus
# blur cards (5 strobe copies over the stroke arc) so the wingbeat reads in Play.
# Mesh objects (joined at export, material order = UE slot order): body 0, wings 1, hair 2, wing blur 3.
import bpy, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
Z0 = 1.30
rng = np.random.default_rng(338)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)

def ss(e0, e1, x): t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def path(pts, n):
    pts = np.asarray(pts, float); out = []
    for k in range(n):
        s = k / (n - 1) * (len(pts) - 1); i = min(int(s), len(pts) - 2); t = s - i
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)

def frames(P, up=None):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    N = np.zeros_like(P)
    ref = np.asarray(up, float) if up is not None else (np.array([0, 0, 1.0]) if abs(T[0] @ [0, 0, 1]) < 0.9 else np.array([1.0, 0, 0]))
    n = ref - (ref @ T[0]) * T[0]; n /= np.linalg.norm(n) + 1e-9
    for i in range(len(P)):
        if up is not None:
            nn = ref - (ref @ T[i]) * T[i]
            if np.linalg.norm(nn) > 1e-3: n = nn
        n = n - (n @ T[i]) * T[i]; n /= np.linalg.norm(n) + 1e-9; N[i] = n
    return T, N, np.cross(T, N)

def loft(P, rx, ry, seg=20, up=(0, 0, 1), prof=None, cap0=True, cap1=True, fr=None):
    """rings along P; rx along N (up), ry along B. prof(i, a) -> radial scale. Ends with radius ~0 become poles.
    Returns verts, faces, per-corner UVs in metres, per-ring t (0..1 by arc length), rows."""
    P = np.asarray(P, float); n = len(P); rx = np.asarray(rx, float); ry = np.asarray(ry, float)
    T, N, B = fr if fr is not None else frames(P, up)
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False) + np.pi          # seam on the underside (-N)
    verts, rows = [], []
    for i in range(n):
        if (i == 0 or i == n - 1) and max(rx[i], ry[i]) < 1e-4:
            rows.append([len(verts)]); verts.append(P[i]); continue
        row = []
        for a in ang:
            s = prof(i, a) if prof else 1.0
            row.append(len(verts)); verts.append(P[i] + s * (rx[i] * math.cos(a) * N[i] + ry[i] * math.sin(a) * B[i]))
        rows.append(row)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1) + np.abs(np.diff(np.maximum(rx, ry))))])
    circ = np.pi * (np.max(rx) + np.max(ry))
    faces, uvs = [], []
    for i in range(n - 1):
        a, b = rows[i], rows[i + 1]
        for j in range(seg):
            j1 = j + 1; u0, u1 = j / seg * circ, j1 / seg * circ
            if len(a) == 1: faces.append([a[0], b[j1 % seg], b[j]]); uvs.append([((u0 + u1) / 2, L[i]), (u1, L[i + 1]), (u0, L[i + 1])])
            elif len(b) == 1: faces.append([a[j], a[j1 % seg], b[0]]); uvs.append([(u0, L[i]), (u1, L[i]), ((u0 + u1) / 2, L[i + 1])])
            else: faces.append([a[j], a[j1 % seg], b[j1 % seg], b[j]]); uvs.append([(u0, L[i]), (u1, L[i]), (u1, L[i + 1]), (u0, L[i + 1])])
    return np.array(verts), faces, uvs, L / max(L[-1], 1e-9), rows

PARTS = {'head': 0, 'thorax': 1, 'petiole': 2, 'abdomen': 3, 'stinger': 4, 'leg': 5, 'eye': 6, 'mandible': 7, 'antenna': 8,
         'tissue': 9, 'fungus': 10, 'ocellus': 11, 'tegula': 12}
pieces = []
def add(name, part, P, rx, ry, seg, weights, up=(0, 0, 1), prof=None, fr=None, seg_id=0, drop=None):
    v, f, uv, t, rows = loft(P, rx, ry, seg, up, prof, fr=fr)
    uvert = np.zeros(len(v))
    for i, r in enumerate(rows): uvert[r] = t[i]
    if drop is not None:                                    # broken shell: drop faces whose centre is inside the hole
        keep = [k for k, fc in enumerate(f) if not drop(v[fc].mean(0))]
        f = [f[k] for k in keep]; uv = [uv[k] for k in keep]
    W = weights(v, uvert) if callable(weights) else {weights: np.ones(len(v))}
    pieces.append((name, v, f, uv, PARTS[part], uvert, W, np.full(len(v), seg_id, float)))

# =============================== head ===========================================================================
n = 44; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), -0.47 - 0.31 * t, Z0 + 0.03 - 0.07 * t ** 2], 1)
sh = np.sin(np.pi * np.clip(t, 0, 1) ** 0.78) ** 0.5; sh[0] = sh[-1] = 0
def head_prof(i, a):
    ti = t[i]; c = math.cos(a)
    crown = 1 + 0.07 * max(c, 0) ** 2 * math.exp(-((ti - 0.35) / 0.2) ** 2)          # vertex bulge behind the ocelli
    clyp = 1 + 0.10 * max(-c, 0) * math.exp(-((ti - 0.82) / 0.1) ** 2)              # clypeus plate, low on the face
    gena = 1 + 0.05 * abs(math.sin(a)) * math.exp(-((ti - 0.45) / 0.18) ** 2)        # cheeks behind the eyes
    return crown * clyp * gena
add('head', 'head', P, 0.148 * sh * (1 - 0.2 * t), 0.19 * sh * (1 - 0.12 * t), 32, 'head', prof=head_prof)
for sgn in (1, -1):
    sd = 'L' if sgn > 0 else 'R'
    # compound eye: emarginate (kidney notch on the inner edge, a vespid trait), wraps the side of the head
    m = 34; te = np.linspace(0, 1, m)
    P = path([(0.098 * sgn, -0.515, Z0 + 0.105), (0.134 * sgn, -0.585, Z0 + 0.07), (0.142 * sgn, -0.65, Z0 + 0.005),
              (0.134 * sgn, -0.70, Z0 - 0.06), (0.108 * sgn, -0.73, Z0 - 0.095)], m)
    se = np.sqrt(np.clip(np.sin(np.pi * te), 0, 1)); se[0] = se[-1] = 0
    notch = 1 - 0.45 * np.exp(-((te - 0.42) / 0.09) ** 2)
    dent = (lambda i, a: 1.0) if sgn > 0 else (lambda i, a: 1 - 0.25 * max(math.cos(a), 0) * math.exp(-((te[i] - 0.6) / 0.15) ** 2))   # R eye collapsed (decay)
    add('eye_' + sd, 'eye', P, 0.038 * se, 0.06 * se * notch, 20, 'head', up=(sgn, 0, 0), prof=dent)
    # mandible: a broad blade with 4 teeth on the inner edge; the left one is chipped
    m = 22; tm = np.linspace(0, 1, m)
    P = path([(0.06 * sgn, -0.735, Z0 - 0.075), (0.085 * sgn, -0.79, Z0 - 0.11), (0.05 * sgn, -0.835, Z0 - 0.125), (0.008 * sgn, -0.85, Z0 - 0.12)], m)
    w_ = 0.036 * (1 - tm) ** 0.4 + 0.005; w_[-1] = 0
    chip = 0.55 if sgn > 0 else 1.0
    def mand_prof(i, a, tm=tm, sgn=sgn, chip=chip):
        inner = max(-math.cos(a), 0)
        teeth = 0.35 * inner * max(math.sin((tm[i] - 0.35) * np.pi * 7), 0) ** 3 * (tm[i] > 0.35)
        if tm[i] > 0.8: teeth *= chip
        return 1 + teeth
    add('mandible_' + sd, 'mandible', P, w_, w_ * 0.32, 12, 'mandible_' + sd, up=(0, 0, 1), prof=mand_prof)
    # antenna: thick scape, pedicel, 11 flagellomeres, elbowed; the right one is broken off short (decay)
    m = 64; ta = np.linspace(0, 1, m)
    tip = (0.27 * sgn, -1.10, Z0 + 0.22) if sgn > 0 else (0.20 * sgn, -0.98, Z0 + 0.29)
    P = path([(0.035 * sgn, -0.735, Z0 + 0.075), (0.055 * sgn, -0.775, Z0 + 0.235), (0.15 * sgn, -0.905, Z0 + 0.31), tip], m)
    r = np.where(ta < 0.28, 0.0125, 0.0105 - 0.004 * ta)
    r *= 1 - 0.14 * ss(0.25, 0.5, np.abs(np.sin(np.clip(ta - 0.3, 0, 1) / 0.7 * np.pi * 11))) * (ta > 0.3)   # segment joints
    r[-1] = 0
    add('antenna_' + sd, 'antenna', P, r, r, 9, 'antenna_' + sd, up=(0, 0, 1))
# ocelli: three small lenses on the crown
for (ox, oy) in ((0.0, -0.585), (0.028, -0.555), (-0.028, -0.555)):
    m = 8; to = np.linspace(0, 1, m)
    P = np.stack([np.full(m, ox), np.full(m, oy), Z0 + 0.155 + 0.012 * to], 1)
    r = 0.011 * np.sqrt(np.clip(1 - to ** 2, 0, 1)); r[-1] = 0; r[0] = 0.011
    add('ocellus', 'ocellus', P, r, r, 10, 'head', up=(0, 1, 0))
# neck membrane (soft, rotting): tissue between head and pronotum
n = 8; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), -0.43 - 0.08 * t, Z0 + 0.02 + 0.005 * t], 1)
add('neck', 'tissue', P, np.full(n, 0.075), np.full(n, 0.07), 16, lambda v, u: {'thorax': 1 - ss(0.3, 0.7, u), 'head': ss(0.3, 0.7, u)})

# =============================== mesosoma (thorax) ===============================================================
n = 52; t = np.linspace(0, 1, n)       # t 0 = front (pronotum), 1 = rear (propodeum)
P = np.stack([np.zeros(n), -0.475 + 0.445 * t, Z0 + 0.035 * np.sin(np.pi * t) - 0.03 * ss(0.75, 1.0, t)], 1)
sh = np.sin(np.pi * np.clip(t, 0, 1)) ** 0.42; sh[0] = sh[-1] = 0
def thx_prof(i, a):
    ti = t[i]; c = math.cos(a); top = max(c, 0)
    collar = 1 + 0.06 * math.exp(-((ti - 0.12) / 0.035) ** 2)                     # pronotum collar ridge
    scut = 1 + 0.07 * top ** 2 * math.exp(-((ti - 0.70) / 0.06) ** 2)              # scutellum hump
    meta = 1 + 0.03 * top ** 2 * math.exp(-((ti - 0.80) / 0.03) ** 2)
    groove = 1 - 0.035 * math.exp(-((ti - 0.62) / 0.012) ** 2) - 0.03 * math.exp(-((ti - 0.76) / 0.01) ** 2)   # sutures
    side = 1 - 0.04 * abs(math.sin(a)) * math.exp(-((ti - 0.45) / 0.15) ** 2) * (c < 0.3)                     # mesopleuron
    return collar * scut * meta * groove * side
add('thorax', 'thorax', P, 0.205 * sh * (1 - 0.18 * ss(0.78, 1.0, t)), 0.205 * sh * (1 + 0.05 * np.sin(np.pi * t)), 36, 'thorax', prof=thx_prof)
for sgn in (1, -1):                     # tegulae: plates over the wing roots
    m = 8; tg = np.linspace(0, 1, m)
    P = path([(0.15 * sgn, -0.385, Z0 + 0.135), (0.17 * sgn, -0.335, Z0 + 0.14), (0.16 * sgn, -0.29, Z0 + 0.125)], m)
    r = 0.022 * np.sin(np.pi * tg) ** 0.6; r[0] = r[-1] = 0
    add('tegula', 'tegula', P, r * 0.45, r, 10, 'thorax', up=(sgn, 0, 1))

# =============================== petiole + gaster ================================================================
n = 14; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), -0.04 + 0.17 * t, Z0 - 0.025 - 0.012 * t], 1)
r = 0.036 + 0.03 * ss(0.55, 1.0, t) + 0.025 * ss(0.25, 0.0, t)
add('petiole', 'petiole', P, r, r, 16, 'abdomen_01')
GN = 110; tg = np.linspace(0, 1, GN)
GP = path([(0, 0.11, Z0 - 0.035), (0, 0.33, Z0 - 0.08), (0, 0.58, Z0 - 0.19), (0, 0.80, Z0 - 0.33)], GN)
GF = frames(GP, up=(0, 0, 1))
env = np.sin(np.pi * np.clip(tg, 0, 1) ** 0.55) ** 0.5 * (1 - 0.3 * tg ** 3); env[-1] = 0.0
def gw(v, u):
    w2 = ss(0.40, 0.55, u); return {'abdomen_01': 1 - w2, 'abdomen_02': w2}
def gw_t(t0, t1):
    def f(v, u): uu = t0 + (t1 - t0) * u; return gw(v, uu)
    return f
# tissue core (wet, rotting membrane), seen through the gaps and the hole
add('gaster_tissue', 'tissue', GP[::2], 0.205 * env[::2] * 0.86, 0.19 * env[::2] * 0.86, 18, gw, fr=(GF[0][::2], GF[1][::2], GF[2][::2]))
# six nested tergite/sternite shells: each starts tucked under the previous rim and ends in a flared rim
SEG = [(0.0, 0.20), (0.18, 0.37), (0.35, 0.53), (0.555, 0.70), (0.68, 0.84), (0.82, 1.0)]   # joint 3/4 gapes (no overlap)
hole_c = None
for k, (a, b) in enumerate(SEG):
    i0, i1 = int(a * (GN - 1)), int(b * (GN - 1)) + 1
    idx = np.arange(i0, min(i1, GN)); tt = (tg[idx] - a) / (b - a)
    sc = 0.93 + 0.07 * ss(0.0, 0.25, tt) + 0.035 * ss(0.82, 1.0, tt) - 0.02 * ss(0.97, 1.0, tt)   # tucked front, flared rim lip
    if k == 0: sc = sc * (0.6 + 0.4 * ss(0.0, 0.3, tt))                                          # first shell closes onto the petiole
    rx = 0.205 * env[idx] * sc; ry = 0.19 * env[idx] * sc
    fr = (GF[0][idx], GF[1][idx], GF[2][idx])
    drop = None
    if k == 3:                          # broken tergite 4, right dorsal side: a ragged hole over the tissue
        hc = GP[idx[len(idx) // 2]] + np.array([-0.10, 0.0, 0.12]); hole_c = hc
        def drop(c, hc=hc):
            d = np.linalg.norm((c - hc) * [1.0, 0.8, 1.0]); rag = 0.012 * math.sin(c[1] * 260) + 0.01 * math.sin(c[0] * 310 + c[2] * 170)
            return d < 0.075 + rag
    add(f'gaster_{k + 1}', 'abdomen', GP[idx], rx, ry, 32, gw_t(tg[idx[0]], tg[idx[-1]]), fr=fr, seg_id=k + 1, drop=drop)
# sting + sheath
m = 26; ts = np.linspace(0, 1, m)
P = path([(0, 0.775, Z0 - 0.305), (0, 0.875, Z0 - 0.385), (0, 0.97, Z0 - 0.49)], m)
r = 0.026 * (1 - ts) ** 1.25 + 0.0015; r[-1] = 0
add('stinger', 'stinger', P, r, r * 0.8, 12, 'stinger')
for sgn in (1, -1):
    P = path([(0.012 * sgn, 0.77, Z0 - 0.30), (0.016 * sgn, 0.83, Z0 - 0.345), (0.012 * sgn, 0.87, Z0 - 0.375)], 12)
    r = 0.011 * np.sin(np.pi * np.linspace(0, 1, 12)) ** 0.5; r[0] = r[-1] = 0
    add('sheath', 'stinger', P, r, r * 0.6, 8, 'stinger')

# =============================== legs ===========================================================================
LEGS = {'F': (-0.40, 0.10, -0.25, 0.92), 'M': (-0.26, 0.00, 0.0, 1.0), 'H': (-0.13, -0.06, 0.32, 1.12)}
legbones = {}
for key, (y0, dy, sweep, L_) in LEGS.items():
    for sgn in (1, -1):
        sd = 'L' if sgn > 0 else 'R'
        hip = np.array([0.075 * sgn, y0, Z0 - 0.125])
        knee = hip + L_ * np.array([0.33 * sgn, dy + sweep * 0.5, 0.07])
        ankle = knee + L_ * np.array([0.10 * sgn, sweep * 0.6 + 0.05, -0.43])
        toe = ankle + L_ * np.array([0.045 * sgn, sweep * 0.35 + 0.04, -0.27])
        claw = toe + np.array([-0.012 * sgn, -0.03, -0.018])
        broken = (key == 'M' and sd == 'R')          # decay: right mid leg lost its tarsus
        if broken: toe = ankle + (toe - ankle) * 0.35; claw = toe
        m = 66
        ctrl = [hip, hip + (knee - hip) * 0.12 + [0, 0, -0.01], hip + (knee - hip) * 0.5 + [0, 0, 0.035], knee, knee + (ankle - knee) * 0.5, ankle, ankle + (toe - ankle) * 0.5, toe]
        if not broken: ctrl.append(claw)
        P = path(ctrl, m)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); tl = L / L[-1]
        j1 = np.linalg.norm(knee - hip) / L[-1]; j2 = j1 + np.linalg.norm(ankle - knee) / L[-1]
        cox = ss(0.08, 0.0, tl)                                                       # coxa: thick at the body
        r = np.where(tl < j1, 0.040 - 0.008 * tl / j1, np.where(tl < j2, 0.027 - 0.007 * (tl - j1) / (j2 - j1), 0.0165 - 0.008 * (tl - j2) / (1 - j2)))
        r = r * (1 + 0.55 * cox) * (1 - 0.18 * np.exp(-((tl - 0.1) / 0.012) ** 2))    # coxa + trochanter joint
        r *= 1 + 0.2 * np.exp(-((tl - j1) / 0.018) ** 2) + 0.14 * np.exp(-((tl - j2) / 0.018) ** 2)
        ntar = 5; seg_t = np.clip((tl - j2) / (1 - j2), 0, 1)
        r *= 1 - 0.16 * ss(0.3, 0.5, np.abs(np.sin(seg_t * np.pi * ntar))) * (tl > j2)   # 5 tarsomeres
        if broken: r[-1] = r[-2] * 0.8
        else: r[-1] = 0
        names = [f'leg_{key}_{sd}_1', f'leg_{key}_{sd}_2', f'leg_{key}_{sd}_3']
        legbones[(key, sd)] = (hip, knee, ankle, claw, names)
        def lw(v, u, j1=j1, j2=j2, names=names):
            a = ss(j1 - 0.015, j1 + 0.015, u); b = ss(j2 - 0.015, j2 + 0.015, u)
            return {names[0]: 1 - a, names[1]: a - b, names[2]: b}
        flat = lambda i, a, tl=tl, j1=j1: 1 - 0.12 * abs(math.cos(a)) * (tl[i] < j1) * (tl[i] > 0.12)   # femur flattened
        add(f'leg_{key}_{sd}', 'leg', P, r, r * 0.9, 12, lw, up=(0, 0, 1), prof=flat)
        # tibial spurs at the ankle
        tdir = (ankle - knee) / np.linalg.norm(ankle - knee)
        for k_, off in enumerate((np.array([0.0, -0.012, 0]), np.array([0.0, 0.012, 0]))):
            base = ankle - tdir * 0.012 + off * 0.6
            P = path([base, base + tdir * 0.03 + off, base + tdir * 0.05 + off * 1.4], 8)
            rs = 0.0055 * (1 - np.linspace(0, 1, 8)); rs[-1] = 0
            add('spur', 'leg', P, rs, rs, 6, names[1])
        if not broken:                                   # two tarsal claws
            cdir = (claw - toe) / (np.linalg.norm(claw - toe) + 1e-9)
            for s2 in (1, -1):
                side = np.array([0.012 * s2, 0, 0])
                P = path([toe + side * 0.4, toe + cdir * 0.02 + side, toe + cdir * 0.032 + side + [0, 0, -0.022]], 8)
                rc = 0.0045 * (1 - np.linspace(0, 1, 8)) ** 0.8; rc[-1] = 0
                add('claw', 'leg', P, rc, rc, 6, names[2])

# =============================== fungal stalks (Ophiocordyceps-style) ============================================
def stalk(name, base, normal, length, bone, r0=0.011, bend=(0, 0.25, 0.9), knob=True, seed=0):
    nrm = np.asarray(normal, float); nrm /= np.linalg.norm(nrm); bnd = np.asarray(bend, float)
    lr = np.random.default_rng(seed); wob = lr.normal(0, 0.18, 3)
    c = [base - nrm * 0.01, base + nrm * length * 0.3, base + (nrm * 0.45 + bnd * 0.35 + wob * 0.2) * length,
         base + (nrm * 0.35 + bnd * 0.75 + wob * 0.3) * length, base + (nrm * 0.25 + bnd * 1.0 + wob * 0.35) * length]
    m = 34; ts = np.linspace(0, 1, m); P = path(c, m)
    r = r0 * (1 + 1.8 * ss(0.1, 0.0, ts)) * (1 - 0.35 * ts)                         # flared foot (mycelium collar)
    if knob: r = r * (1 + 1.3 * np.exp(-((ts - 0.84) / 0.1) ** 2))                   # swollen fertile head near the tip
    r[-1] = 0
    def bumps(i, a, ts=ts, s=seed):                                                  # perithecia: knobbly fruiting surface
        return 1 + (0.22 * max(math.sin(a * 7 + s) * math.sin(ts[i] * 90 + s), 0) if 0.7 < ts[i] < 0.97 else 0)
    add(name, 'fungus', P, r, r * 0.92, 12, bone, prof=bumps)
def cluster(name, base, normal, lengths, bone, r0, seed, droop=(0, 0.6, -0.2)):
    """a clump of 2-4 stalks out of one joint: thick pale stems that sag under their own weight, knobbly fertile heads"""
    lr = np.random.default_rng(seed); nrm = np.asarray(normal, float); nrm /= np.linalg.norm(nrm)
    for k_, L in enumerate(lengths):
        off = lr.normal(0, 0.012, 3); off -= (off @ nrm) * nrm
        bend = np.asarray(droop, float) + lr.normal(0, 0.35, 3)
        stalk(f'{name}_{k_}', base + off, nrm + lr.normal(0, 0.25, 3), L, bone, r0=r0 * (1 - 0.25 * k_), bend=bend, seed=seed * 10 + k_)
cluster('fungus_neck', np.array([-0.075, -0.455, Z0 + 0.09]), (-0.6, -0.25, 0.75), (0.20, 0.13, 0.08), 'thorax', 0.016, 1, droop=(-0.3, -0.2, -0.1))
cluster('fungus_propodeum', np.array([0.02, -0.075, Z0 + 0.15]), (0.1, 0.45, 0.9), (0.24, 0.17, 0.11, 0.07), 'thorax', 0.018, 2, droop=(0.1, 0.7, -0.15))
jc = GP[int(0.545 * (GN - 1))]
cluster('fungus_gaster34', jc + np.array([-0.08, 0, 0.15]), (-0.45, 0.2, 0.85), (0.22, 0.14, 0.09), 'abdomen_02', 0.016, 4, droop=(-0.4, 0.5, -0.1))
cluster('fungus_hole', hole_c + np.array([0.01, 0, -0.03]), (-0.75, 0.2, 0.6), (0.12, 0.08), 'abdomen_02', 0.012, 6, droop=(-0.5, 0.3, -0.3))
for k_, (pos, nrm_) in enumerate([((0.05, -0.20, Z0 + 0.19), (0.2, 0, 1)), ((0.13, -0.46, Z0 + 0.05), (0.8, -0.2, 0.5))]):
    stalk(f'fungus_small{k_}', np.array(pos), nrm_, 0.05 + 0.02 * k_, 'thorax', r0=0.006, knob=False, seed=10 + k_)

# =============================== body mesh ======================================================================
V, F, UV, PART, UVERT, SEGI = [], [], [], [], [], []; groups = {}
for name, v, f, uv, pid, uvert, W, sg in pieces:
    off = len(V)
    for k, w in W.items(): groups.setdefault(k, []).append((off, w))
    V.extend(v.tolist()); F.extend([[i + off for i in face] for face in f]); UV.extend(uv); PART.extend([pid] * len(v)); UVERT.extend(uvert.tolist()); SEGI.extend(sg.tolist())
me = bpy.data.meshes.new('SK_RealmWasp'); me.from_pydata(V, [], F); me.update()
uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.array([c for face in UV for c in face], np.float32).ravel())
for an, arr in (('part', PART), ('ulen', UVERT), ('gseg', SEGI)): me.attributes.new(an, 'FLOAT', 'POINT').data.foreach_set('value', np.array(arr, np.float32))
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
body = bpy.data.objects.new('SK_RealmWasp', me); bpy.context.scene.collection.objects.link(body)
for k, lst in groups.items():
    vg = body.vertex_groups.new(name=k)
    for off, w in lst:
        for i in np.nonzero(w > 1e-4)[0]: vg.add([int(off + i)], float(w[i]), 'REPLACE')
print('BODY verts', len(V), 'tris', sum(len(f) - 2 for f in F), flush=True)
Varr = np.array(V); PARr = np.array(PART); body_groups = groups

# =============================== setae (hair strands) ============================================================
def sample_surface(mask_fn, count, seed):
    tri = []
    for face in F:
        for k in range(1, len(face) - 1): tri.append((face[0], face[k], face[k + 1]))
    tri = np.array(tri); a, b, c = Varr[tri[:, 0]], Varr[tri[:, 1]], Varr[tri[:, 2]]
    cen = (a + b + c) / 3; area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    w = area * mask_fn(cen, PARr[tri[:, 0]]); w = w / w.sum()
    lr = np.random.default_rng(seed); pick = lr.choice(len(tri), count, p=w)
    u = lr.random(count); v = lr.random(count); flip = u + v > 1; u[flip] = 1 - u[flip]; v[flip] = 1 - v[flip]
    p = a[pick] + (b[pick] - a[pick]) * u[:, None] + (c[pick] - a[pick]) * v[:, None]
    nrm = np.cross(b[pick] - a[pick], c[pick] - a[pick]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    return p, nrm, tri[pick, 0]
def hair_mask(c, part):
    x, y, z = c[:, 0], c[:, 1], c[:, 2]
    m = np.zeros(len(c))
    m += (part == 1) * (0.25 + 0.75 * ss(Z0 - 0.05, Z0 + 0.12, z))                  # thorax: dense on top, some on the sides
    m += (part == 0) * (0.4 + 0.6 * ss(Z0 - 0.02, Z0 + 0.1, z)) * (y > -0.76)         # head crown + face
    m += (part == 5) * 0.12 * (z > Z0 - 0.45)                                         # upper legs
    m += (part == 3) * 0.05 * ss(0.4, 0.1, (y - 0.1) / 0.7)                           # a few on the front of the gaster
    m *= 1 - (np.linalg.norm(c - np.array([0.06, -0.33, Z0 + 0.19]), axis=1) < 0.06)  # bald, rubbed patch (wear has a cause)
    return m
NH = int(os.environ.get('HAIRS', '5200'))
hp, hn, hv = sample_surface(hair_mask, NH, 7)
hairbone_v = {}
for bn, lst in body_groups.items():
    for off, w in lst:
        for i in np.nonzero(w > 0.5)[0]: hairbone_v[int(off + i)] = bn
HV, HF, HUV, HG = [], [], [], {}
lr = np.random.default_rng(9)
for k in range(NH):
    # pile: short, fine, laid back toward the tail (like a real hornet's setae), not bristles standing straight out
    p, nrm = hp[k], hn[k]; L = lr.uniform(0.006, 0.016) * (0.6 if PARr[hv[k]] == 5 else 1.0)
    back = np.array([0, 1.0, -0.3]); back -= (back @ nrm) * nrm; back /= np.linalg.norm(back) + 1e-9
    d0 = nrm * 0.55 + back * 0.75 + lr.normal(0, 0.22, 3); d0 /= np.linalg.norm(d0)
    side = np.cross(d0, nrm if abs(d0 @ nrm) < 0.95 else np.array([1.0, 0, 0])); side /= np.linalg.norm(side) + 1e-9
    up2 = np.cross(side, d0); rr = lr.uniform(0.0006, 0.0010)
    base = len(HV); root = p - nrm * 0.0015
    for j in range(3):
        a = 2 * math.pi * j / 3; HV.append(root + rr * (math.cos(a) * side + math.sin(a) * up2))
    HV.append(root + d0 * L + nrm * (-0.15 * L))                   # tip droops a little
    for j in range(3):
        HF.append([base + j, base + (j + 1) % 3, base + 3]); HUV.append([(0.5, 0.0), (0.5, 0.0), (0.5, 1.0)])
    bn = hairbone_v.get(int(hv[k]), 'thorax'); HG.setdefault(bn, []).extend(range(base, base + 4))
hm = bpy.data.meshes.new('SK_RealmWasp_Hair'); hm.from_pydata([tuple(v) for v in HV], [], HF); hm.update()
hl = hm.uv_layers.new(name='UVMap'); hl.data.foreach_set('uv', np.array([c for f in HUV for c in f], np.float32).ravel())
hm.polygons.foreach_set('use_smooth', [True] * len(hm.polygons))
hair = bpy.data.objects.new('SK_RealmWasp_Hair', hm); bpy.context.scene.collection.objects.link(hair)
for bn, ids in HG.items(): hair.vertex_groups.new(name=bn).add(ids, 1.0, 'REPLACE')
print('HAIR strands', NH, 'tris', sum(len(f) - 2 for f in HF), flush=True)

# =============================== wings + blur cards ==============================================================
def chord_frac(s): return (0.42 + 0.58 * math.sin(math.pi * min(1.0, s * 1.08) ** 0.55)) * (1 - 0.65 * s ** 6)
def wing(span, chord, root, sweep_deg, sgn, vrow, ns=28, nc=12, corr=True):
    vs, fs, uvs = [], [], []
    for i in range(ns + 1):
        s = i / ns; c = chord * chord_frac(s); le = 0.06 * chord * math.sin(math.pi * s)
        for j in range(nc + 1):
            q = j / nc; x, y = s * span, -le + q * c
            a = math.radians(sweep_deg); xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
            zc = 0.02 * math.sin(math.pi * s) + 0.012 * math.sin(math.pi * q) * (1 - s)          # camber
            if corr: zc += 0.004 * math.sin(q * math.pi * 5 + s * 2) * (1 - 0.6 * s)               # corrugation along the veins
            vs.append((root[0] + sgn * xr, root[1] + yr, root[2] + zc)); uvs.append((s, vrow + 0.5 * (q * c / chord) * 0.96 + 0.01))
    for i in range(ns):
        for j in range(nc):
            a = i * (nc + 1) + j; f = [a, a + nc + 1, a + nc + 2, a + 1]; fs.append(f if sgn > 0 else f[::-1])
    return vs, fs, uvs
WINGS = {'fore': (1.10, 0.33, (0.10, -0.36, Z0 + 0.16), 12, 0.5), 'hind': (0.74, 0.22, (0.10, -0.20, Z0 + 0.14), 18, 0.0)}
WV, WF, WUV, WG = [], [], [], []
BV, BF, BUV, BG = [], [], [], []
BLUR_ANG = (-45, -19, 7, 33, 60)                 # strobe copies across the stroke (deg up), matches the anim's stroke range
for key, (span, chord, root, sweep, vrow) in WINGS.items():
    for sgn in (1, -1):
        sd = 'L' if sgn > 0 else 'R'; rt = np.array((root[0] * sgn, root[1], root[2]))
        vs, fs, uvs = wing(span, chord, rt, sweep, sgn, vrow)
        off = len(WV); WV += vs; WF += [[i + off for i in f] for f in fs]; WUV += uvs; WG.append((f'wing_{key}_{sd}', off, len(vs)))
        for ang in BLUR_ANG:
            vs, fs, uvs = wing(span, chord, rt, sweep, sgn, vrow, 14, 6, False)
            a = math.radians(ang) * sgn; ca, sa = math.cos(a), math.sin(a)
            vs = [(rt[0] + (v[0] - rt[0]) * ca - (v[2] - rt[2]) * sa, v[1], rt[2] + (v[0] - rt[0]) * sa + (v[2] - rt[2]) * ca) for v in vs]
            off = len(BV); BV += vs; BF += [[i + off for i in f] for f in fs]; BUV += uvs; BG.append((f'wingblur_{sd}', off, len(vs)))
def mk(name, Vs, Fs, UVs, G):
    m = bpy.data.meshes.new(name); m.from_pydata(Vs, [], Fs); m.update()
    l = m.uv_layers.new(name='UVMap'); l.data.foreach_set('uv', np.array([UVs[li.vertex_index] for li in m.loops], np.float32).ravel())
    m.polygons.foreach_set('use_smooth', [True] * len(m.polygons))
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    for gname, off, cnt in G:
        vg = o.vertex_groups.get(gname) or o.vertex_groups.new(name=gname); vg.add(list(range(off, off + cnt)), 1.0, 'REPLACE')
    print(name, 'tris', 2 * len(Fs), flush=True); return o
wings = mk('SK_RealmWasp_Wings', WV, WF, WUV, WG)
blur = mk('SK_RealmWasp_WingBlur', BV, BF, BUV, BG)

# =============================== UV pack (body) ==================================================================
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); body.select_set(False)

# =============================== armature (v1 names + wingblur_L/R) ==============================================
ad = bpy.data.armatures.new('SK_RealmWasp_Skeleton'); arm = bpy.data.objects.new('SK_RealmWasp_Rig', ad)
bpy.context.scene.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
def bone(name, h, t, parent=None):
    b = ad.edit_bones.new(name); b.head = Vector(h); b.tail = Vector(t)
    if parent: b.parent = ad.edit_bones[parent]; b.use_connect = False
    return b
bone('root', (0, 0, 0), (0, 0.3, 0))
bone('thorax', (0, -0.05, Z0), (0, -0.45, Z0), 'root')
bone('head', (0, -0.47, Z0 + 0.01), (0, -0.76, Z0 - 0.02), 'thorax')
for sd, sgn in (('L', 1), ('R', -1)):
    bone(f'mandible_{sd}', (0.055 * sgn, -0.745, Z0 - 0.065), (0.012 * sgn, -0.905, Z0 - 0.12), 'head')
    bone(f'antenna_{sd}', (0.035 * sgn, -0.735, Z0 + 0.075), (0.27 * sgn, -1.10, Z0 + 0.22), 'head')
bone('abdomen_01', (0, 0.0, Z0 - 0.03), (0, 0.38, Z0 - 0.10), 'thorax')
bone('abdomen_02', (0, 0.38, Z0 - 0.10), (0, 0.77, Z0 - 0.30), 'abdomen_01')
bone('stinger', (0, 0.77, Z0 - 0.30), (0, 0.97, Z0 - 0.49), 'abdomen_02')
for key, (span, chord, root, sweep, vrow) in WINGS.items():
    for sd, sgn in (('L', 1), ('R', -1)):
        rt = np.array((root[0] * sgn, root[1], root[2])); a = math.radians(sweep)
        bone(f'wing_{key}_{sd}', tuple(rt), tuple(rt + np.array([sgn * span * math.cos(a), span * math.sin(a), 0])), 'thorax')
for sd, sgn in (('L', 1), ('R', -1)):
    bone(f'wingblur_{sd}', (0.10 * sgn, -0.30, Z0 + 0.16), (0.10 * sgn, -0.10, Z0 + 0.16), 'thorax')
for (key, sd), (hip, knee, ankle, claw, names) in legbones.items():
    bone(names[0], tuple(hip), tuple(knee), 'thorax'); bone(names[1], tuple(knee), tuple(ankle), names[0])
    bone(names[2], tuple(ankle), tuple(claw if np.linalg.norm(claw - ankle) > 0.02 else ankle + (ankle - knee) * 0.2), names[1])
bpy.ops.object.mode_set(mode='OBJECT')
for ob in (body, wings, hair, blur):
    ob.parent = arm; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm
print('BONES', len(ad.bones), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'wasp338_rig.blend'))
print('RIG OK', flush=True)
