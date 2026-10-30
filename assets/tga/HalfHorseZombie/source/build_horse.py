# Rotting horse body for the half-horse zombie (#155, TGA, 2026-10-30). Original, procedural.
#   blender -b --factory-startup -P build_horse.py        ->  horse_rig.blend
# A zombie torso replaces the neck: the body ends in a torn neck stump with a 'TorsoSocket' bone where the licensed
# SK_Zombie attaches in UE (its legs hidden). Faces -Y (UE +Y like the mannequin), metres, Z up, hooves on z = 0.
# Build: anatomical lofts (barrel, stump, 4 legs with real joint order, tail, exposed ribs) are fused by a voxel
# remesh into one watertight skin, decimated to a game budget, smart-UV'd at even texel density, auto-weighted.
import bpy, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
TRIS = int(os.environ.get('TRIS', '30000'))

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
    if len(rows[0]) > 1: F.append(rows[0][::-1])            # flat caps where the ends are open
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
    """profile from (t, value) keys; smooth > 0 runs a moving average (in samples) so the curve has no kinks."""
    ks = np.array(keys); v = np.interp(t, ks[:, 0], ks[:, 1])
    if smooth:
        k = np.ones(smooth) / smooth; e0, e1 = v[0], v[-1]
        v = np.convolve(np.pad(v, smooth, mode='edge'), k, mode='same')[smooth:-smooth]; v[0], v[-1] = e0, e1
    return v
parts = []
def add(V, F): parts.append((V, F))

# ---- barrel: chest -> belly -> croup, the back dips behind the withers ---------------------------------------------
n = 100; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), -1.00 + 2.02 * t, 1.12 + interp(t, [(0, 0.10), (0.25, 0.06), (0.5, 0.0), (0.8, 0.08), (1, 0.06)], 25)], 1)
rx = interp(t, [(0, 0.0), (0.04, 0.20), (0.15, 0.28), (0.45, 0.31), (0.7, 0.30), (0.88, 0.27), (0.97, 0.18), (1, 0.0)], 9)
ry = interp(t, [(0, 0.0), (0.04, 0.24), (0.15, 0.36), (0.45, 0.37), (0.7, 0.34), (0.88, 0.33), (0.97, 0.22), (1, 0.0)], 9)
add(*loft(P, ry, rx, 64))      # N is up (z) at the start, so the first radius is the height
def blob(c, r, n=24, seg=32):
    """ellipsoid mass (muscle group), poles at both ends along Y."""
    t = np.linspace(0, 1, n); P = np.stack([np.full(n, c[0]), c[1] - r[1] + 2 * r[1] * t, np.full(n, c[2])], 1)
    s = np.sqrt(np.clip(np.sin(np.pi * t), 0, 1)); s[0] = s[-1] = 0
    add(*loft(P, r[2] * s, r[0] * s, seg))
for sg in (1, -1):
    blob((0.17 * sg, -0.60, 1.10), (0.13, 0.26, 0.30))          # shoulder + upper arm (triceps)
    blob((0.16 * sg, 0.62, 1.12), (0.15, 0.32, 0.30))           # hindquarter (gluteals + thigh)
    blob((0.20 * sg, 0.42, 1.34), (0.06, 0.07, 0.06), 12, 16)   # point of hip, sharp on a starved carcass
blob((0, -0.84, 1.04), (0.19, 0.12, 0.17))                     # chest / pectorals
# ---- neck stump: rises forward from the withers, torn off where the zombie torso sits (domed, ragged rim) ------------
n = 24; t = np.linspace(0, 1, n)
P = path([(0, -0.60, 1.30), (0, -0.80, 1.45), (0, -0.92, 1.55), (0, -0.95, 1.60)], n)
r = interp(t, [(0, 0.24), (0.45, 0.20), (0.8, 0.18), (0.9, 0.15), (1.0, 0.0)], 3)
add(*loft(P, r * 1.1, r * 0.85, 32, prof=lambda i, a: 1 + 0.10 * ss(0.75, 0.9, i / (n - 1)) * math.sin(5 * a + 1) * math.cos(3 * a)))

# ---- legs: front = shoulder > elbow > knee (carpus) > fetlock > hoof; hind = hip > stifle > hock > fetlock > hoof --------
LEGS = {}
for sd, sg in (('L', 1), ('R', -1)):
    LEGS['front_' + sd] = [(0.20 * sg, -0.70, 1.22), (0.20 * sg, -0.74, 0.92), (0.18 * sg, -0.76, 0.50), (0.18 * sg, -0.77, 0.19), (0.18 * sg, -0.81, 0.07), (0.18 * sg, -0.83, 0.0)]
    LEGS['hind_' + sd] = [(0.20 * sg, 0.70, 1.22), (0.24 * sg, 0.52, 0.86), (0.21 * sg, 0.80, 0.55), (0.19 * sg, 0.76, 0.19), (0.19 * sg, 0.72, 0.07), (0.19 * sg, 0.70, 0.0)]
for name, J in LEGS.items():
    J = np.array(J); front = name.startswith('front')
    top = J[0] + np.array([-0.12 * np.sign(J[0][0]), 0, 0.16])                 # start deep inside the body mass
    P = path([top, J[0], J[1], J[2], J[3], J[4]], 80)[8:]
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); tl = L / L[-1]
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(J[:5], axis=0), axis=1))]); seg /= seg[-1]
    if front:   # forearm muscle, then the bony cannon, fetlock knob, pastern
        rk = [(0, 0.10), (seg[1], 0.10), (seg[1] + 0.12, 0.085), (seg[2] - 0.03, 0.045), (seg[2], 0.056), (seg[2] + 0.05, 0.04), (seg[3] - 0.02, 0.038), (seg[3], 0.05), (seg[3] + 0.04, 0.04), (1, 0.042)]
    else:       # big thigh and gaskin muscle, the hock point, cannon, fetlock, pastern
        rk = [(0, 0.13), (seg[1], 0.14), (seg[1] + 0.10, 0.10), (seg[2] - 0.02, 0.06), (seg[2], 0.07), (seg[2] + 0.06, 0.045), (seg[3] - 0.02, 0.04), (seg[3], 0.052), (seg[3] + 0.04, 0.04), (1, 0.043)]
    r = interp(tl, rk); r[0] = 0                                               # domed top (pole), no flat cap
    add(*loft(P, r, r * (0.9 if front else 0.8), 28))
    # hoof: a truncated cone, wider at the ground
    hp = np.array([J[4] + [0, 0, 0.012], J[5] + [0, -0.012, 0]]); ht = np.linspace(0, 1, 6)
    H = hp[0] + (hp[1] - hp[0]) * ht[:, None]
    add(*loft(H, 0.048 + 0.022 * ht, 0.052 + 0.024 * ht, 22))
    # hock point / elbow point (olecranon) bumps
    if front: add(*loft(path([J[1] + [0, 0.07, 0.06], J[1] + [0, 0.10, -0.02]], 8), np.full(8, 0.05), np.full(8, 0.05), 14))
    else: add(*loft(path([J[2] + [0, 0.02, 0.06], J[2] + [0, 0.07, -0.01]], 8), np.full(8, 0.035), np.full(8, 0.035), 14))

# ---- tail: a rotted, bony dock with a few matted strands -------------------------------------------------------------
n = 26; t = np.linspace(0, 1, n)
P = path([(0, 1.00, 1.34), (0, 1.12, 1.22), (0, 1.17, 0.95), (0, 1.15, 0.70)], n)
add(*loft(P, interp(t, [(0, 0.07), (0.3, 0.05), (1, 0.012)]), interp(t, [(0, 0.06), (0.3, 0.045), (1, 0.010)]), 14))
# ---- exposed ribs on the left flank (the rot wound), they stand out of the sunken flesh ----------------------------------
rng = np.random.default_rng(155)
RIBY = []
for k in range(6):
    y0 = -0.32 + k * 0.115 + rng.uniform(-0.015, 0.015); RIBY.append(y0)
    bulge = 0.315 + rng.uniform(-0.01, 0.012); low = 0.84 + (0.16 if k == 3 else 0) + rng.uniform(-0.02, 0.03)   # rib 4 snapped
    pts = [(0.22, y0 - 0.03, 1.40), (bulge, y0, 1.21), (bulge - 0.008, y0 + 0.025, 1.0), (0.25, y0 + 0.035, low)]
    P = path(pts, 20); r = np.full(20, 0.021) * (1 + 0.15 * rng.standard_normal(20).cumsum() / 8); r[0] = r[-1] = 0
    add(*loft(P, r, r * 0.75, 12))

V, F = [], []
for v, f in parts:
    off = len(V); V += [tuple(x) for x in v]; F += [[i + off for i in face] for face in f]
me = bpy.data.meshes.new('SK_HorseBody'); me.from_pydata(V, [], F); me.update()
body = bpy.data.objects.new('SK_HorseBody', me); bpy.context.scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
rm = body.modifiers.new('Remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = float(os.environ.get('VOXEL', '0.009')); rm.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='Remesh')
sm = body.modifiers.new('Smooth', 'LAPLACIANSMOOTH'); sm.lambda_factor = 0.8; sm.iterations = 10; sm.use_volume_preserve = True
bpy.ops.object.modifier_apply(modifier='Smooth')                 # fillets the fused joints like muscle, kills voxel steps
# sink the flank between the ribs: pull vertices inward inside the wound ellipse (rot has eaten the flesh)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
wound = np.exp(-(((co[:, 1] - 0.0) / 0.36) ** 2 + ((co[:, 2] - 1.10) / 0.22) ** 2)) * (co[:, 0] > 0.15)
ribd = np.min(np.stack([np.abs(co[:, 1] - (y + 0.01)) for y in RIBY], 1), 1)
co[:, 0] -= 0.035 * wound * ss(0.012, 0.035, ribd)
me.vertices.foreach_set('co', co.ravel()); me.update()
nt0 = len(me.polygons) * 2
dm = body.modifiers.new('Decimate', 'DECIMATE'); dm.ratio = min(1.0, TRIS / max(nt0, 1)); bpy.ops.object.modifier_apply(modifier='Decimate')
bpy.ops.object.shade_smooth()
print('HORSE tris before', nt0, 'after', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
# UVs: smart project, equalise island scale, pack
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(72), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- rig ------------------------------------------------------------------------------------------------------------
ad = bpy.data.armatures.new('SK_HorseBody_Skeleton'); arm = bpy.data.objects.new('SK_HorseBody_Rig', ad)
bpy.context.scene.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm; body.select_set(False); arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
def bone(name, h, t, parent=None):
    b = ad.edit_bones.new(name); b.head = Vector(h); b.tail = Vector(t)
    if parent: b.parent = ad.edit_bones[parent]
    return b
bone('root', (0, 0, 0), (0, 0.3, 0))
bone('pelvis', (0, 0.55, 1.20), (0, 0.15, 1.18), 'root')
bone('spine_01', (0, 0.15, 1.18), (0, -0.25, 1.17), 'pelvis')
bone('spine_02', (0, -0.25, 1.17), (0, -0.62, 1.24), 'spine_01')
bone('neck_stump', (0, -0.62, 1.30), (0, -0.92, 1.56), 'spine_02')
bone('TorsoSocket', (0, -0.98, 1.62), (0, -0.98, 1.92), 'neck_stump')      # zombie torso attaches here (z up)
bone('tail_01', (0, 1.00, 1.34), (0, 1.14, 1.20), 'pelvis'); bone('tail_02', (0, 1.14, 1.20), (0, 1.17, 0.95), 'tail_01'); bone('tail_03', (0, 1.17, 0.95), (0, 1.15, 0.70), 'tail_02')
NAMES = {}
for name, J in LEGS.items():
    front = name.startswith('front'); sd = name[-1]
    segs = ['upperarm', 'forearm', 'cannon_f', 'pastern_f'] if front else ['thigh', 'gaskin', 'cannon_h', 'pastern_h']
    par = 'spine_02' if front else 'pelvis'; nm = []
    for k in range(4):
        bn = f'{segs[k]}_{sd}'; bone(bn, J[k], J[k + 1] if k < 3 else J[5], par); par = bn; nm.append(bn)
    NAMES[name] = nm
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.scene.objects: o.select_set(False)
body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('BONES', len(ad.bones), 'groups', len(body.vertex_groups), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'horse_rig.blend'))
print('RIG OK', flush=True)
