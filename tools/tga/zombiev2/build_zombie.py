# Zombie variations v2 (#199, TGA, 2026-10-30): an ORIGINAL procedural humanoid base (no licensed mesh), then variants.
#   blender -b --factory-startup -P build_zombie.py       env VARIANT = Base | Bloated | Burnt | Hollow | Infected | Soldier | Crawler
# Anatomy lofts (torso, ribcage, pelvis, neck, skull + face masses, arms, hands with fingers, legs, feet) are fused by a
# voxel remesh, smoothed like muscle, then variant damage is carved, decimated to ~22k tris, smart-UV'd and auto-weighted
# to a UE-mannequin bone hierarchy (root/pelvis/spine_01-03/neck_01/head, clavicle/upperarm/lowerarm/hand, thigh/calf/
# foot/ball). Faces -Y (UE +Y like the mannequin), metres, feet on z = 0, A-pose.
import bpy, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Base'); TRIS = int(os.environ.get('TRIS', '22000'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
rng = np.random.default_rng({'Base': 1, 'Bloated': 2, 'Burnt': 3, 'Hollow': 4, 'Infected': 5, 'Soldier': 6, 'Crawler': 7}[VAR] + 199)

def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    ref = np.array([0, -1.0, 0]) if abs(T[0] @ [0, -1, 0]) < 0.9 else np.array([0, 0, 1.0])
    N = np.zeros_like(P); n = ref - (ref @ T[0]) * T[0]; n /= np.linalg.norm(n)
    for i in range(len(P)):
        n = n - (n @ T[i]) * T[i]; n /= np.linalg.norm(n) + 1e-9; N[i] = n
    return T, N, np.cross(T, N)
def loft(P, rx, ry, seg=24):
    """rings along P; rx along N (front, -Y for vertical parts), ry along B; zero radius at an end makes a pole."""
    P = np.asarray(P, float); T, N, B = frames(P); ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    V, F, rows = [], [], []
    for i in range(len(P)):
        if (i == 0 or i == len(P) - 1) and max(rx[i], ry[i]) < 1e-4: rows.append([len(V)]); V.append(P[i]); continue
        row = []
        for a in ang: row.append(len(V)); V.append(P[i] + rx[i] * math.cos(a) * N[i] + ry[i] * math.sin(a) * B[i])
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
def prof(t, keys, smooth=5):
    ks = np.array(keys); v = np.interp(t, ks[:, 0], ks[:, 1])
    if smooth:
        k = np.ones(smooth) / smooth; e0, e1 = v[0], v[-1]; v = np.convolve(np.pad(v, smooth, mode='edge'), k, mode='same')[smooth:-smooth]; v[0], v[-1] = e0, e1
    return v
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
parts = []
def add(V, F): parts.append((V, F))
def blob(c, r, n=18, seg=24, axis=2):
    t = np.linspace(0, 1, n); c = np.asarray(c, float); P = np.tile(c, (n, 1)); P[:, axis] = c[axis] - r[axis] + 2 * r[axis] * t
    s = np.sqrt(np.clip(np.sin(np.pi * t), 0, 1)); s[0] = s[-1] = 0
    o = [i for i in range(3) if i != axis]
    add(*loft(P, r[o[1]] * s if axis != 1 else r[0] * s, r[o[0]] * s if axis != 1 else r[2] * s, seg))
def limb(pts, rkeys, n=40, seg=20, flat=1.0, cap=True):
    P = path(pts, n); L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); t = L / L[-1]
    r = prof(t, rkeys, 3)
    if cap: r[0] = r[-1] = 0
    add(*loft(P, r, r * flat, seg)); return P

THIN = {'Bloated': 1.25}.get(VAR, 1.0)            # bloated swells the soft tissue
# ---- torso: pelvis -> waist -> chest, hunched forward ------------------------------------------------------------------
n = 50; t = np.linspace(0, 1, n)
P = path([(0, 0.00, 0.90), (0, -0.01, 1.08), (0, 0.01, 1.25), (0, -0.02, 1.40), (0, -0.04, 1.47)], n)
W = prof(t, [(0, 0.0), (0.03, 0.15), (0.15, 0.17), (0.4, 0.135), (0.7, 0.16), (0.9, 0.15), (1.0, 0.0)], 5)
Dp = prof(t, [(0, 0.0), (0.03, 0.10), (0.15, 0.11), (0.4, 0.085 * THIN), (0.7, 0.11), (0.9, 0.09), (1.0, 0.0)], 5)
add(*loft(P, Dp, W, 40))
blob((0, -0.02, 1.27), (0.15, 0.115, 0.15))                       # ribcage
for s in (1, -1):
    blob((0.07 * s, 0.05, 0.93), (0.075, 0.07, 0.08))              # gluteals
    blob((0.12 * s, 0.0, 1.44), (0.07, 0.05, 0.035), axis=0)       # trapezius
    blob((0.195 * s, -0.005, 1.385), (0.04, 0.045, 0.055))          # deltoid (wasted)
if VAR == 'Bloated': blob((0, -0.10, 1.10), (0.16, 0.13, 0.16))  # distended belly
# ---- neck + head --------------------------------------------------------------------------------------------------
limb([(0, -0.02, 1.40), (0, -0.04, 1.50), (0, -0.05, 1.60)], [(0, 0.062), (1, 0.052)], 12, 20, 1.1, cap=False)
blob((0, -0.035, 1.715), (0.074, 0.098, 0.088), n=24, seg=32, axis=1)   # cranium (long front-back)
blob((0, -0.085, 1.635), (0.06, 0.05, 0.065), n=20, seg=28)          # face / maxilla
blob((0, -0.115, 1.705), (0.055, 0.02, 0.015), axis=0)             # brow ridge
blob((0, -0.135, 1.66), (0.012, 0.02, 0.028))                     # nose
blob((0, -0.10, 1.585), (0.045, 0.035, 0.03), axis=0)             # jaw / chin (slack)
for s in (1, -1):
    blob((0.045 * s, -0.11, 1.645), (0.02, 0.02, 0.016))           # cheekbones
    blob((0.075 * s, -0.045, 1.67), (0.008, 0.018, 0.03))          # ears
# ---- arms (A-pose ~25 deg) and hands with fingers --------------------------------------------------------------------
ARM = {}
for s, sd in ((1, 'l'), (-1, 'r')):
    if VAR == 'Hollow' and sd == 'r': ARM[sd] = None; limb([(0.19 * s, 0, 1.40), (0.24 * s, 0.01, 1.30)], [(0, 0.05), (0.7, 0.045), (1, 0.03)], 10, 18); continue
    sh, el, wr = np.array([0.20 * s, 0.0, 1.40]), np.array([0.30 * s, 0.03, 1.15]), np.array([0.37 * s, -0.01, 0.92])
    limb([sh, (sh + el) / 2 + [0, 0.01, 0], el, (el + wr) / 2, wr], [(0, 0.05), (0.2, 0.045), (0.45, 0.034), (0.5, 0.036), (0.75, 0.03), (1, 0.024)], 40, 20)
    hd = wr + np.array([0.025 * s, -0.01, -0.09])
    limb([wr, hd], [(0, 0.026), (0.5, 0.032), (1, 0.03)], 12, 16, 0.45)          # palm (flat)
    for f in range(4):                                                                # curled zombie fingers
        base = hd + np.array([0.0, -0.022 + f * 0.015, 0.0])
        limb([base, base + [0.01 * s, -0.012, -0.035], base + [0.015 * s, -0.03, -0.06]], [(0, 0.009), (1, 0.006)], 10, 10)
    limb([wr + [0, -0.03, -0.02], wr + [0.01 * s, -0.06, -0.06], wr + [0.02 * s, -0.07, -0.08]], [(0, 0.011), (1, 0.007)], 10, 10)   # thumb
    ARM[sd] = (sh, el, wr, hd)
# ---- legs and feet ------------------------------------------------------------------------------------------------
LEG = {}
for s, sd in ((1, 'l'), (-1, 'r')):
    hp, kn, an = np.array([0.085 * s, 0.0, 1.00]), np.array([0.11 * s, -0.025, 0.50]), np.array([0.11 * s, 0.015, 0.085])
    if VAR == 'Crawler':                                                                # legs gone at mid-thigh: ragged stumps
        limb([hp, hp + [0.01 * s, -0.01, -0.22]], [(0, 0.085), (0.8, 0.07), (1, 0.05)], 16, 22); LEG[sd] = None; continue
    limb([hp, (hp + kn) / 2, kn, kn + (an - kn) * 0.3, an], [(0, 0.085), (0.4, 0.065), (0.48, 0.05), (0.55, 0.05), (0.7, 0.048), (1, 0.034)], 40, 22)
    blob((0.11 * s, 0.035, 0.36), (0.04, 0.035, 0.09))                               # calf
    ft = np.array([0.115 * s, -0.16, 0.025])
    limb([an + [0, 0.03, 0.03], an + [0, 0.0, -0.05], ft], [(0, 0.03), (0.3, 0.04), (1, 0.03)], 20, 16, 0.6)
    LEG[sd] = (hp, kn, an, ft)

V, F = [], []
for v, f in parts:
    off = len(V); V += [tuple(x) for x in v]; F += [[i + off for i in face] for face in f]
me = bpy.data.meshes.new('SK_ZombieV2_' + VAR); me.from_pydata(V, [], F); me.update()
body = bpy.data.objects.new('SK_ZombieV2_' + VAR, me); bpy.context.scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
rm = body.modifiers.new('Remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = float(os.environ.get('VOXEL', '0.005')); bpy.ops.object.modifier_apply(modifier='Remesh')
sm = body.modifiers.new('Smooth', 'LAPLACIANSMOOTH'); sm.lambda_factor = 0.5; sm.iterations = 6; sm.use_volume_preserve = True; bpy.ops.object.modifier_apply(modifier='Smooth')
# ---- carve the face and the variant damage (vertex displacement on the fused skin) ---------------------------------------
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
x, y, z = co[:, 0], co[:, 1], co[:, 2]
for s in (1, -1):                                                                      # sunken eye sockets
    d = np.sqrt(((x - 0.033 * s) / 0.022) ** 2 + ((z - 1.675) / 0.016) ** 2) ; front = y < -0.09
    co[:, 1] += 0.016 * np.exp(-d ** 2 * 1.5) * front
d = np.sqrt((x / 0.025) ** 2 + ((z - 1.606) / 0.01) ** 2); co[:, 1] += 0.012 * np.exp(-d ** 2) * (y < -0.1)    # gaping mouth
gaunt = np.exp(-(((x.__abs__() - 0.05) / 0.02) ** 2 + ((z - 1.62) / 0.025) ** 2)) * (y < -0.07); co[:, 0] -= np.sign(x) * 0.008 * gaunt   # hollow cheeks
me.vertices.foreach_set('co', co.ravel()); me.update()
n0 = len(me.polygons) * 2
dm = body.modifiers.new('Decimate', 'DECIMATE'); dm.ratio = min(1.0, TRIS / max(n0, 1)); bpy.ops.object.modifier_apply(modifier='Decimate')
bpy.ops.object.shade_smooth()
print('ZOMBIE', VAR, 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'from', n0, flush=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')
# ---- UE-mannequin rig ---------------------------------------------------------------------------------------------
ad = bpy.data.armatures.new('SK_ZombieV2_Skeleton'); arm = bpy.data.objects.new('SK_ZombieV2_Rig', ad)
bpy.context.scene.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm; body.select_set(False); arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
def bone(name, h, t, parent=None):
    b = ad.edit_bones.new(name); b.head = Vector(h); b.tail = Vector(t)
    if parent: b.parent = ad.edit_bones[parent]
bone('root', (0, 0, 0), (0, 0.25, 0)); bone('pelvis', (0, 0, 0.95), (0, 0, 1.05), 'root')
bone('spine_01', (0, 0, 1.05), (0, -0.005, 1.17), 'pelvis'); bone('spine_02', (0, -0.005, 1.17), (0, 0.0, 1.29), 'spine_01'); bone('spine_03', (0, 0.0, 1.29), (0, -0.02, 1.42), 'spine_02')
bone('neck_01', (0, -0.03, 1.44), (0, -0.055, 1.56), 'spine_03'); bone('head', (0, -0.055, 1.56), (0, -0.055, 1.80), 'neck_01')
for s, sd in ((1, 'l'), (-1, 'r')):
    bone('clavicle_' + sd, (0.03 * s, -0.03, 1.42), (0.18 * s, 0.0, 1.41), 'spine_03')
    if ARM[sd]:
        sh, el, wr, hd = ARM[sd]; bone('upperarm_' + sd, sh, el, 'clavicle_' + sd); bone('lowerarm_' + sd, el, wr, 'upperarm_' + sd); bone('hand_' + sd, wr, hd, 'lowerarm_' + sd)
    else: bone('upperarm_' + sd, (0.19 * s, 0, 1.40), (0.24 * s, 0.01, 1.30), 'clavicle_' + sd)
    if LEG[sd]:
        hp, kn, an, ft = LEG[sd]; bone('thigh_' + sd, hp, kn, 'pelvis'); bone('calf_' + sd, kn, an, 'thigh_' + sd)
        bone('foot_' + sd, an, an + np.array([0, -0.10, -0.06]), 'calf_' + sd); bone('ball_' + sd, an + np.array([0, -0.10, -0.06]), ft, 'foot_' + sd)
    else: bone('thigh_' + sd, (0.095 * s, 0, 0.92), (0.105 * s, -0.01, 0.70), 'pelvis')
    if 'ball_' + sd in ad.edit_bones: t = ad.edit_bones['ball_' + sd].tail; bone('toeend_' + sd, t, t + Vector((0, -0.04, 0)), 'ball_' + sd)
bone('headtop', (0, -0.055, 1.80), (0, -0.055, 1.86), 'head')
# SK_Zombie (#200, zombie_bones.txt) uses Mixamo names with Hips as the root: rename so the existing anims share by name
ad.edit_bones.remove(ad.edit_bones['root'])
SKZ = {'pelvis': 'Hips', 'spine_01': 'Spine', 'spine_02': 'Spine1', 'spine_03': 'Spine2', 'neck_01': 'Neck', 'head': 'Head', 'headtop': 'HeadTop_End'}
for sd, side in (('l', 'Left'), ('r', 'Right')):
    SKZ.update({'clavicle_' + sd: side + 'Shoulder', 'upperarm_' + sd: side + 'Arm', 'lowerarm_' + sd: side + 'ForeArm', 'hand_' + sd: side + 'Hand',
                'thigh_' + sd: side + 'UpLeg', 'calf_' + sd: side + 'Leg', 'foot_' + sd: side + 'Foot', 'ball_' + sd: side + 'ToeBase', 'toeend_' + sd: side + 'Toe_End'})
for k, v in SKZ.items():
    if k in ad.edit_bones: ad.edit_bones[k].name = v
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.scene.objects: o.select_set(False)
body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('BONES', len(ad.bones), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'zombie_%s.blend' % VAR))
print('RIG OK', flush=True)
