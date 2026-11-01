# #402 Destrier: living war horse, 15 hands (1.52 m at the withers). checkking (Claude), 2026-11-01. Original, procedural.
# Built on TGA's #155 horse pipeline (assets/tga/HalfHorseZombie/source/build_horse.py: anatomical lofts -> voxel remesh
# -> Laplacian smooth -> decimate -> smart UV -> rig), extended to a whole, healthy horse: full neck with a stallion's
# crest, head (jowls, eyes, nostrils, ears), tail dock, plus mane / forelock / tail hair as alpha cards (slot 2).
#   blender -b --factory-startup -P build_destrier.py -- <workdir>        ->  destrier_rig.blend
# Faces -Y (UE +Y like the mannequin), metres, Z up, hooves on z = 0. Research: handoffs/cavalry-400/RESEARCH.md §2.
import bpy, bmesh, numpy as np, math, os, sys
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
D = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
os.makedirs(D, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
TRIS = int(os.environ.get('TRIS', '36000'))
rng = np.random.default_rng(402)

def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    ref = np.array([0, 0, 1.0]) if abs(T[0] @ [0, 0, 1]) < 0.9 else np.array([0, -1.0, 0])
    N = np.zeros_like(P); n = ref - (ref @ T[0]) * T[0]; n /= np.linalg.norm(n)
    for i in range(len(P)):
        n = n - (n @ T[i]) * T[i]; n /= np.linalg.norm(n) + 1e-9; N[i] = n
    return T, N, np.cross(T, N)
def loft(P, rx, ry, seg=24, prof=None):
    P = np.asarray(P, float); T, N, B = frames(P); ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    V, F, rows = [], [], []
    for i in range(len(P)):
        if (i == 0 or i == len(P) - 1) and max(rx[i], ry[i]) < 1e-4: rows.append([len(V)]); V.append(P[i]); continue
        row = []
        for a in ang:
            s = prof(i, a) if prof else 1.0
            row.append(len(V)); V.append(P[i] + s * (rx[i] * math.cos(a) * N[i] + ry[i] * math.sin(a) * B[i]))
        rows.append(row)
    for i in range(len(P) - 1):
        a, b = rows[i], rows[i + 1]
        for j in range(seg):
            j1 = (j + 1) % seg
            if len(a) == 1: F.append([a[0], b[j1], b[j]])
            elif len(b) == 1: F.append([a[j], a[j1], b[0]])
            else: F.append([a[j], a[j1], b[j1], b[j]])
    if len(rows[0]) > 1: F.append(rows[0][::-1])
    if len(rows[-1]) > 1: F.append(rows[-1])
    return V, F
def path(pts, n):
    pts = np.asarray(pts, float); out = []
    for k in range(n):
        s = k / (n - 1) * (len(pts) - 1); i = min(int(s), len(pts) - 2); t = s - i
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def interp(t, keys, smooth=0):
    ks = np.array(keys); v = np.interp(t, ks[:, 0], ks[:, 1])
    if smooth:
        k = np.ones(smooth) / smooth; e0, e1 = v[0], v[-1]
        v = np.convolve(np.pad(v, smooth, mode='edge'), k, mode='same')[smooth:-smooth]; v[0], v[-1] = e0, e1
    return v
parts = []
def add(V, F): parts.append((V, F))
def blob(c, r, n=24, seg=32):
    t = np.linspace(0, 1, n); P = np.stack([np.full(n, c[0]), c[1] - r[1] + 2 * r[1] * t, np.full(n, c[2])], 1)
    s = np.sqrt(np.clip(np.sin(np.pi * t), 0, 1)); s[0] = s[-1] = 0
    add(*loft(P, r[2] * s, r[0] * s, seg))
def blob_axis(c, axis, half, r1, r2, n=16, seg=20):
    """ellipsoid along an arbitrary axis (half length `half`), cross radii r1 (frame N) / r2 (frame B)."""
    c = np.asarray(c, float); a = np.asarray(axis, float); a /= np.linalg.norm(a)
    t = np.linspace(0, 1, n); P = c[None] + (t[:, None] * 2 - 1) * half * a[None]
    s = np.sqrt(np.clip(np.sin(np.pi * t), 0, 1)); s[0] = s[-1] = 0
    add(*loft(P, r1 * s, r2 * s, seg))

# ---- barrel: a fit, muscled horse (fuller than the #155 carcass), the back dips behind the withers ---------------------
n = 100; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), -1.00 + 2.02 * t, 1.12 + interp(t, [(0, 0.10), (0.25, 0.06), (0.5, 0.0), (0.8, 0.07), (1, 0.06)], 25)], 1)
rx = interp(t, [(0, 0.0), (0.04, 0.22), (0.15, 0.30), (0.45, 0.335), (0.7, 0.32), (0.88, 0.29), (0.97, 0.19), (1, 0.0)], 9)
ry = interp(t, [(0, 0.0), (0.04, 0.26), (0.15, 0.37), (0.45, 0.385), (0.7, 0.355), (0.88, 0.34), (0.97, 0.22), (1, 0.0)], 9)
add(*loft(P, ry, rx, 64))
for sg in (1, -1):
    blob((0.18 * sg, -0.60, 1.10), (0.14, 0.27, 0.31))          # shoulder + triceps
    blob((0.17 * sg, 0.62, 1.12), (0.16, 0.33, 0.31))           # hindquarter (gluteals + thigh)
    blob((0.19 * sg, 0.40, 1.32), (0.07, 0.10, 0.07), 12, 16)   # point of hip, rounded on a fit horse
blob((0, -0.88, 1.10), (0.17, 0.10, 0.14))                     # chest / pectorals
blob((0, -0.48, 1.47), (0.07, 0.20, 0.07), 14, 16)             # withers ridge

# ---- neck: withers -> poll, a stallion's crested neck -------------------------------------------------------------------
n = 40; t = np.linspace(0, 1, n)
NECK = [(0, -0.50, 1.24), (0, -0.78, 1.46), (0, -0.98, 1.68), (0, -1.10, 1.84), (0, -1.15, 1.90)]
P = path(NECK, n)
rv = interp(t, [(0, 0.34), (0.25, 0.27), (0.6, 0.18), (0.88, 0.13), (1.0, 0.115)], 5)    # depth (crest -> throat)
rl = interp(t, [(0, 0.24), (0.25, 0.19), (0.6, 0.125), (0.88, 0.095), (1.0, 0.09)], 5)   # width, narrow at the throatlatch
crest = lambda i, a: (1 + 0.16 * max(math.cos(a), 0) ** 2 * math.sin(math.pi * min(1.0, i / (n - 1) * 1.1)) - 0.06 * max(-math.cos(a), 0))
add(*loft(P, rv, rl, 36, prof=crest))

# ---- head: poll -> muzzle, about 50 deg below the horizontal (collected) --------------------------------------------------
POLL = np.array([0, -1.13, 1.90]); MUZ = np.array([0, -1.47, 1.33])
n = 36; t = np.linspace(0, 1, n)
P = path([POLL + (POLL - MUZ) * 0.06, POLL, POLL + (MUZ - POLL) * 0.5, MUZ], n)
depth = interp(t, [(0, 0.0), (0.04, 0.13), (0.14, 0.18), (0.34, 0.165), (0.62, 0.125), (0.86, 0.10), (0.95, 0.09), (1.0, 0.0)], 3)
width = interp(t, [(0, 0.0), (0.04, 0.115), (0.14, 0.14), (0.34, 0.125), (0.62, 0.095), (0.86, 0.085), (0.95, 0.08), (1.0, 0.0)], 3)
# frame N = the front of the face (forehead / nasal bone), -N = the jaw. The jaw side is deep at the back (cheeks).
# section: flat broad forehead / nasal bone on top (superellipse), rounder underneath
jaw = lambda i, a: (abs(math.cos(a)) ** 3 + abs(math.sin(a)) ** 3) ** (-1 / 3) * (0.92 if math.cos(a) > 0 else 1.0)
add(*loft(P, depth, width, 32, prof=jaw))
T_head = (MUZ - POLL) / np.linalg.norm(MUZ - POLL)
Nf = np.array([0, 0, 1.0]) - (np.array([0, 0, 1.0]) @ T_head) * T_head; Nf /= np.linalg.norm(Nf)      # face front
for sg in (1, -1):
    blob_axis(POLL + T_head * 0.17 - Nf * 0.15 + np.array([0.055 * sg, 0, 0]), T_head, 0.15, 0.16, 0.075)   # mandible + masseter: the deep round cheek
    blob_axis(POLL + T_head * 0.13 + Nf * 0.035 + np.array([0.10 * sg, 0, 0]), T_head, 0.024, 0.02, 0.016, 10, 14)  # orbit / eye bulge
    # ears: from the poll, up and a little forward and out
    eb = POLL + np.array([0.055 * sg, 0, 0.02]) + Nf * 0.01
    et = eb + np.array([0.04 * sg, -0.05, 0.15])
    EP = path([eb, eb + (et - eb) * 0.5, et], 12); te = np.linspace(0, 1, 12)
    add(*loft(EP, interp(te, [(0, 0.03), (0.35, 0.042), (0.8, 0.022), (1, 0.0)]), interp(te, [(0, 0.025), (0.35, 0.022), (1, 0.0)]), 12))
EYE = {sg: POLL + T_head * 0.13 + Nf * 0.03 + np.array([0.125 * sg, 0, 0]) for sg in (1, -1)}
NOSTRIL = {sg: MUZ - T_head * 0.06 + Nf * 0.03 + np.array([0.05 * sg, 0, 0]) for sg in (1, -1)}

# ---- legs: TGA's joint order (front: shoulder > elbow > knee > fetlock > hoof; hind: hip > stifle > hock > fetlock > hoof)
LEGS = {}
for sd, sg in (('L', 1), ('R', -1)):
    LEGS['front_' + sd] = [(0.20 * sg, -0.70, 1.22), (0.20 * sg, -0.74, 0.92), (0.18 * sg, -0.76, 0.50), (0.18 * sg, -0.77, 0.19), (0.18 * sg, -0.81, 0.07), (0.18 * sg, -0.83, 0.0)]
    LEGS['hind_' + sd] = [(0.20 * sg, 0.70, 1.22), (0.24 * sg, 0.52, 0.86), (0.21 * sg, 0.80, 0.55), (0.19 * sg, 0.76, 0.19), (0.19 * sg, 0.72, 0.07), (0.19 * sg, 0.70, 0.0)]
for name, J in LEGS.items():
    J = np.array(J); front = name.startswith('front')
    top = J[0] + np.array([-0.12 * np.sign(J[0][0]), 0, 0.16])
    P = path([top, J[0], J[1], J[2], J[3], J[4]], 80)[8:]
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); tl = L / L[-1]
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(J[:5], axis=0), axis=1))]); seg /= seg[-1]
    if front:
        rk = [(0, 0.11), (seg[1], 0.105), (seg[1] + 0.12, 0.09), (seg[2] - 0.03, 0.05), (seg[2], 0.06), (seg[2] + 0.05, 0.043), (seg[3] - 0.02, 0.041), (seg[3], 0.054), (seg[3] + 0.04, 0.043), (1, 0.045)]
    else:
        rk = [(0, 0.14), (seg[1], 0.15), (seg[1] + 0.10, 0.105), (seg[2] - 0.02, 0.064), (seg[2], 0.074), (seg[2] + 0.06, 0.048), (seg[3] - 0.02, 0.043), (seg[3], 0.055), (seg[3] + 0.04, 0.043), (1, 0.046)]
    r = interp(tl, rk); r[0] = 0
    add(*loft(P, r, r * (0.9 if front else 0.8), 28))
    hp = np.array([J[4] + [0, 0, 0.012], J[5] + [0, -0.012, 0]]); ht = np.linspace(0, 1, 6)
    H = hp[0] + (hp[1] - hp[0]) * ht[:, None]
    add(*loft(H, 0.050 + 0.022 * ht, 0.054 + 0.024 * ht, 22))
    if front: add(*loft(path([J[1] + [0, 0.07, 0.06], J[1] + [0, 0.10, -0.02]], 8), np.full(8, 0.05), np.full(8, 0.05), 14))
    else: add(*loft(path([J[2] + [0, 0.02, 0.06], J[2] + [0, 0.07, -0.01]], 8), np.full(8, 0.035), np.full(8, 0.035), 14))

# ---- tail dock (the hair is cards) ---------------------------------------------------------------------------------------
n = 18; t = np.linspace(0, 1, n)
DOCK = [(0, 0.98, 1.36), (0, 1.10, 1.26), (0, 1.15, 1.08), (0, 1.15, 0.98)]
P = path(DOCK, n)
add(*loft(P, interp(t, [(0, 0.075), (0.4, 0.055), (1, 0.0)]), interp(t, [(0, 0.065), (0.4, 0.048), (1, 0.0)]), 14))

V, F = [], []
for v, f in parts:
    off = len(V); V += [tuple(x) for x in v]; F += [[i + off for i in face] for face in f]
me = bpy.data.meshes.new('SK_Destrier'); me.from_pydata(V, [], F); me.update()
body = bpy.data.objects.new('SK_Destrier', me); bpy.context.scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
rm = body.modifiers.new('Remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = float(os.environ.get('VOXEL', '0.008')); rm.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='Remesh')
sm = body.modifiers.new('Smooth', 'LAPLACIANSMOOTH'); sm.lambda_factor = 0.8; sm.iterations = 10; sm.use_volume_preserve = True
bpy.ops.object.modifier_apply(modifier='Smooth')
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
for sg in (1, -1):                                                 # nostrils: flared hollows; eyes: set a little in
    d = np.linalg.norm(co - NOSTRIL[sg], axis=1); w = np.exp(-(d / 0.022) ** 2)
    co -= (w * 0.018)[:, None] * ((co - (MUZ - T_head * 0.06)) / (np.linalg.norm(co - (MUZ - T_head * 0.06), axis=1, keepdims=True) + 1e-6))
me.vertices.foreach_set('co', co.ravel()); me.update()
nt0 = len(me.polygons) * 2
dm = body.modifiers.new('Decimate', 'DECIMATE'); dm.ratio = min(1.0, TRIS / max(nt0, 1)); bpy.ops.object.modifier_apply(modifier='Decimate')
bpy.ops.object.shade_smooth()
print('DESTRIER tris before', nt0, 'after', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(72), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- hair cards: mane (falls to the right, the off side), forelock, tail ---------------------------------------------------
def card_strip(root, dirs, width, normal_hint, col):
    """a bending ribbon: root point, list of segment vectors, constant width; UV u = column of the hair atlas."""
    pts = [np.asarray(root, float)]
    for d in dirs: pts.append(pts[-1] + d)
    pts = np.array(pts); m = len(pts)
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    side = np.cross(T, np.asarray(normal_hint, float)); side /= np.linalg.norm(side, axis=1, keepdims=True) + 1e-9
    taper = np.linspace(1.0, 0.55, m)
    Vs = []; Fs = []; UVs = []
    for i in range(m):
        Vs.append(pts[i] - side[i] * width * 0.5 * taper[i]); Vs.append(pts[i] + side[i] * width * 0.5 * taper[i])
    for i in range(m - 1): Fs.append([2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2])
    u0, u1 = col / 8.0 + 0.004, (col + 1) / 8.0 - 0.004
    for f in Fs:
        UVs.append([(u0 if k % 2 == 0 else u1, 1 - (k // 2) / (m - 1)) for k in f])
    return Vs, Fs, UVs
hv, hf, huv, hgrp = [], [], [], []
def add_card(V_, F_, UV_, grp):
    off = len(hv); hv.extend(V_); hgrp.extend([grp] * len(V_))
    for f, uvs in zip(F_, UV_): hf.append([i + off for i in f]); huv.append(uvs)
crestP = path(NECK, 60)
for k in range(64):                                                # mane: two layers along the crest
    s = k / 63; i = int(4 + s * 52); p = crestP[i]
    T_ = crestP[min(i + 1, 59)] - crestP[max(i - 1, 0)]; T_ /= np.linalg.norm(T_)
    upv = np.array([0, 0, 1.0]) - (np.array([0, 0, 1.0]) @ T_) * T_; upv /= np.linalg.norm(upv)
    rad = (interp(np.array([s]), [(0, 0.34), (0.25, 0.27), (0.6, 0.19), (0.88, 0.15), (1, 0.14)])[0]) * (1 + 0.16 * math.sin(math.pi * min(1, s * 1.1)))
    root = p + upv * (rad - 0.02) + np.array([rng.uniform(-0.02, 0.005), 0, 0])
    L = rng.uniform(0.22, 0.36) * (0.75 + 0.35 * math.sin(math.pi * s)); nseg = 6
    fall = np.array([-1.0, 0, -0.35]); fall /= np.linalg.norm(fall)  # over to the right side, then down
    dirs = []
    for j in range(nseg):
        w = j / (nseg - 1); d = (upv * max(0.0, 0.35 - w) + fall * (0.65 + w)); d /= np.linalg.norm(d)
        d = d + np.array([0, rng.normal(0, 0.08), 0]); d /= np.linalg.norm(d); dirs.append(d * L / nseg)
    V_, F_, UV_ = card_strip(root, dirs, rng.uniform(0.05, 0.08), T_, int(rng.integers(0, 8)))
    add_card(V_, F_, UV_, 'neck_01' if s < 0.5 else 'neck_02')
for k in range(9):                                                 # forelock between the ears, over the forehead
    root = POLL + Nf * 0.05 + np.array([rng.uniform(-0.04, 0.04), 0, 0.03])
    L = rng.uniform(0.14, 0.22); dirs = [(T_head * 0.85 + Nf * 0.3) / np.linalg.norm(T_head * 0.85 + Nf * 0.3) * L / 4 for _ in range(4)]
    V_, F_, UV_ = card_strip(root, dirs, rng.uniform(0.04, 0.06), Nf, int(rng.integers(0, 8)))      # lies flat on the forehead
    add_card(V_, F_, UV_, 'head')
dockP = path(DOCK, 30)
for k in range(46):                                                # tail: from the dock down to the hocks
    s = rng.uniform(0.05, 0.75); p = dockP[int(s * 29)]
    ang = rng.uniform(0, 2 * np.pi); root = p + np.array([0.04 * math.cos(ang), 0.03 * math.sin(ang) + 0.01, 0])
    bottom = rng.uniform(0.42, 0.58); L = root[2] - bottom; nseg = 7
    dirs = []
    for j in range(nseg):
        w = j / (nseg - 1); d = np.array([rng.normal(0, 0.05), 0.10 * (1 - w) + 0.02, -1.0]); d /= np.linalg.norm(d); dirs.append(d * L / nseg)
    V_, F_, UV_ = card_strip(root, dirs, rng.uniform(0.06, 0.09), np.array([0, 1.0, 0]) if rng.uniform() < 0.5 else np.array([1.0, 0, 0.0]), int(rng.integers(0, 8)))
    add_card(V_, F_, UV_, 'tail')
hm = bpy.data.meshes.new('SK_Destrier_Hair'); hm.from_pydata([tuple(v) for v in hv], [], hf); hm.update()
uvl = hm.uv_layers.new(name='UVMap')
for poly, uvs in zip(hm.polygons, huv):
    for li, uv in zip(poly.loop_indices, uvs): uvl.data[li].uv = uv
hair = bpy.data.objects.new('SK_Destrier_Hair', hm); bpy.context.scene.collection.objects.link(hair)
# slots: 0 = tail, 1 = mane + forelock (the barded horse hides slot 1 under the neck cover / chanfron with M_Invisible)
hm.materials.append(bpy.data.materials.get('M_DestrierTail') or bpy.data.materials.new('M_DestrierTail'))
hm.materials.append(bpy.data.materials.get('M_DestrierMane') or bpy.data.materials.new('M_DestrierMane'))
fgrp = []
for f in hf: fgrp.append(hgrp[f[0]])
for poly, g in zip(hm.polygons, fgrp): poly.material_index = 0 if g == 'tail' else 1
for p in hm.polygons: p.use_smooth = True
print('HAIR cards', len(hf), 'tris', len(hf) * 2, flush=True)

# ---- rig ---------------------------------------------------------------------------------------------------------------
ad = bpy.data.armatures.new('SK_Destrier_Skeleton'); arm = bpy.data.objects.new('SK_Destrier_Rig', ad)
bpy.context.scene.collection.objects.link(arm)
for o in bpy.context.scene.objects: o.select_set(False)
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
def bone(name, h, t, parent=None):
    b = ad.edit_bones.new(name); b.head = Vector(h); b.tail = Vector(t)
    if parent: b.parent = ad.edit_bones[parent]
    return b
bone('root', (0, 0, 0), (0, 0.3, 0))
bone('pelvis', (0, 0.55, 1.20), (0, 0.15, 1.18), 'root')
bone('spine_01', (0, 0.15, 1.18), (0, -0.25, 1.17), 'pelvis')
bone('spine_02', (0, -0.25, 1.17), (0, -0.62, 1.24), 'spine_01')
bone('neck_01', (0, -0.58, 1.32), (0, -0.88, 1.56), 'spine_02')
bone('neck_02', (0, -0.88, 1.56), (0, -1.09, 1.82), 'neck_01')
bone('head', tuple(POLL + np.array([0, 0.02, -0.02])), tuple(MUZ), 'neck_02')
for sg, sd in ((1, 'L'), (-1, 'R')):
    eb = POLL + np.array([0.055 * sg, 0, 0.02]); bone('ear_' + sd, tuple(eb), tuple(eb + np.array([0.04 * sg, -0.05, 0.15])), 'head')
bone('tail_01', (0, 0.98, 1.36), (0, 1.12, 1.22), 'pelvis'); bone('tail_02', (0, 1.12, 1.22), (0, 1.16, 0.90), 'tail_01'); bone('tail_03', (0, 1.16, 0.90), (0, 1.16, 0.50), 'tail_02')
for name, J in LEGS.items():
    front = name.startswith('front'); sd = name[-1]
    segs = ['upperarm', 'forearm', 'cannon_f', 'pastern_f'] if front else ['thigh', 'gaskin', 'cannon_h', 'pastern_h']
    par = 'spine_02' if front else 'pelvis'
    for k in range(4):
        bn = f'{segs[k]}_{sd}'; bone(bn, J[k], J[k + 1] if k < 3 else J[5], par); par = bn
# sockets (no skin weights): the rider sits on the saddle seat; the lance pivots at the rider's right armpit
bone('RiderSocket', (0, -0.22, 1.60), (0, -0.22, 1.85), 'spine_01')
bone('lance', (-0.26, -0.18, 2.12), (-0.26, -0.48, 2.12), 'RiderSocket')
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.scene.objects: o.select_set(False)
body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for b in ('RiderSocket', 'lance'):                                   # sockets carry no weights
    vg = body.vertex_groups.get(b)
    if vg: body.vertex_groups.remove(vg)
# hair: rigid-ish weights by part (mane by neck position, tail graded down the 3 tail bones)
for g in ('neck_01', 'neck_02', 'head', 'tail_01', 'tail_02', 'tail_03'): hair.vertex_groups.new(name=g)
hco = np.array(hv)
for i, (g, p) in enumerate(zip(hgrp, hco)):
    if g == 'tail':
        z = p[2]
        if z > 1.15: hair.vertex_groups['tail_01'].add([i], 1.0, 'REPLACE')
        elif z > 0.88: w = (z - 0.88) / 0.27; hair.vertex_groups['tail_01'].add([i], w, 'REPLACE'); hair.vertex_groups['tail_02'].add([i], 1 - w, 'REPLACE')
        else: w = max(0.0, (z - 0.5) / 0.38); hair.vertex_groups['tail_02'].add([i], w, 'REPLACE'); hair.vertex_groups['tail_03'].add([i], 1 - w, 'REPLACE')
    elif g == 'head': hair.vertex_groups['head'].add([i], 1.0, 'REPLACE')
    else:
        w = float(np.clip((p[1] - (-1.05)) / ((-0.6) - (-1.05)), 0, 1))     # blend neck_02 (top) -> neck_01 (base)
        hair.vertex_groups['neck_01'].add([i], w, 'REPLACE'); hair.vertex_groups['neck_02'].add([i], 1 - w, 'REPLACE')
mo = hair.modifiers.new('Armature', 'ARMATURE'); mo.object = arm; hair.parent = arm
print('BONES', len(ad.bones), 'groups', len(body.vertex_groups), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'destrier_rig.blend'))
print('RIG OK', flush=True)
