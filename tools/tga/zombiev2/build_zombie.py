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
blob((0, -0.005, 1.29), (0.135, 0.10, 0.13))                      # ribcage (inside the torso loft, just fills the chest)
for s in (1, -1):
    blob((0.065 * s, 0.035, 0.94), (0.065, 0.05, 0.07))             # gluteals (wasted)
    blob((0.12 * s, 0.0, 1.44), (0.07, 0.05, 0.035), axis=0)       # trapezius
    blob((0.18 * s, -0.005, 1.39), (0.045, 0.045, 0.05))            # deltoid (wasted, overlaps the shoulder)
if VAR == 'Bloated': blob((0, -0.065, 1.12), (0.155, 0.115, 0.19))  # distended belly
for s in (1, -1):
    limb([(0.015 * s, -0.085, 1.43), (0.08 * s, -0.075, 1.445), (0.16 * s, -0.04, 1.43)], [(0, 0.013), (0.5, 0.011), (1, 0.014)], 14, 12)   # collarbones
    if VAR != 'Crawler': blob((0.11 * s, -0.06, 0.51), (0.035, 0.022, 0.035))   # kneecaps
    blob((0.075 * s, 0.07, 1.22), (0.035, 0.03, 0.09))                       # shoulder-blade / lat ridge
rng = np.random.default_rng({'Bloated': 1, 'Burnt': 2, 'Hollow': 3, 'Infected': 4, 'Soldier': 5, 'Crawler': 6}.get(VAR, 0))
if VAR == 'Infected':                                                         # pink realm growths clustered on shoulder, back and thigh
    for c0, n0 in (((-0.21, 0.0, 1.42), 9), ((0.06, 0.14, 1.25), 8), ((-0.15, -0.07, 0.78), 6), ((0.045, -0.03, 1.665), 3)):
        for _ in range(n0):
            r0 = rng.uniform(0.018, 0.038); blob(np.array(c0) + rng.normal(0, 0.02, 3), (r0, r0 * rng.uniform(0.8, 1.2), r0), 12, 14)
if VAR == 'Soldier':                                                          # torn tabard: a thin shell over the torso hanging to mid-thigh, ragged hem
    n = 30; t = np.linspace(0, 1, n); P = np.stack([np.zeros(n), np.linspace(-0.01, 0.0, n), np.linspace(1.44, 0.70, n)], 1)
    add(*loft(P, prof(t, [(0, 0.115), (0.3, 0.125), (0.6, 0.14), (1, 0.15)], 3), prof(t, [(0, 0.19), (0.3, 0.165), (0.5, 0.15), (0.65, 0.17), (1, 0.20)], 3), 40))
    for s in (1, -1): limb([(0.12 * s, -0.02, 1.43), (0.0, -0.02, 1.46), (-0.12 * s, -0.02, 1.43)], [(0, 0.03), (1, 0.03)], 12, 12)   # belt-strap over the shoulders
# ---- neck + head --------------------------------------------------------------------------------------------------
limb([(0, -0.01, 1.38), (0, -0.035, 1.48), (0, -0.045, 1.56)], [(0, 0.075), (0.5, 0.060), (1, 0.058)], 12, 20, 1.1, cap=False)   # short, thick, pushed forward
def head(c, nu=128, nv=96):
    """one star-shaped surface: an egg (cranium + face) whose radius is pushed/pulled by skull landmarks, so the features
    flow into each other instead of reading as stuck-on lumps. Local frame: x right(+ = left side), y front(-), z up."""
    c = np.asarray(c, float); u = np.linspace(0, 2 * np.pi, nu, endpoint=False); v = np.linspace(0, np.pi, nv)
    U, Vv = np.meshgrid(u, v); D = np.stack([np.sin(Vv) * np.cos(U), np.sin(Vv) * np.sin(U), np.cos(Vv)], -1)   # unit dirs
    dx, dy, dz = D[..., 0], D[..., 1], D[..., 2]
    rx = 0.071 - 0.012 * ss(0.0, -0.9, dz)                                    # jaw narrower than the cranium
    ry = np.where(dy < 0, 0.100 - 0.006 * ss(0.3, -0.6, dz), 0.098)           # long front-back skull
    rz = np.where(dz > 0, 0.100, 0.118)                                        # chin hangs lower than the crown rises
    P = D * np.stack([rx, ry, rz], -1)
    def bump(p, w, a, sx=1.0):                                                  # radial push (+) / pull (-) around a landmark
        q = P / np.array([sx, 1.0, 1.0]) - np.asarray(p) / np.array([sx, 1.0, 1.0]); d2 = (q ** 2).sum(-1) / w ** 2
        return a * np.exp(-d2)
    dr = np.zeros(dx.shape)
    dr += bump((0, -0.090, 0.040), 0.030, 0.010, 2.2)                           # brow ridge (wide band)
    dr += bump((0, -0.080, -0.088), 0.022, 0.010)                               # chin
    dr += bump((0, -0.097, 0.012), 0.010, 0.016)                                # nasal bridge
    dr += bump((0, -0.100, -0.012), 0.011, -0.020)                              # rotted nose: open nasal cavity
    dr += bump((0, -0.090, -0.052), 0.016, -0.022, 1.9)                         # gaping mouth (wide slit, slack jaw)
    dr += bump((0, -0.093, -0.036), 0.010, 0.006, 2.4)                          # upper lip / teeth line
    for s in (1, -1):
        dr += bump((0.033 * s, -0.088, 0.018), 0.019, -0.026)                  # deep orbits (sunken eyes)
        dr += bump((0.034 * s, -0.080, 0.014), 0.009, 0.010)                   # shrivelled eyeball at the bottom of the orbit
        dr += bump((0.054 * s, -0.070, -0.006), 0.016, 0.009)                  # zygomatic bone / cheekbone
        dr += bump((0.068 * s, -0.030, -0.004), 0.020, 0.005, 0.6)             # zygomatic arch running back to the ear
        dr += bump((0.046 * s, -0.068, -0.040), 0.018, -0.014)                 # hollow cheek under the cheekbone
        dr += bump((0.062 * s, -0.040, 0.036), 0.020, -0.007)                  # sunken temple
        dr += bump((0.055 * s, 0.000, -0.078), 0.020, 0.008)                   # mandible angle
        dr += bump((0.070 * s, -0.012, -0.014), 0.010, 0.006)                  # ear root (ears added as blobs)
    dr += bump((0, 0.095, -0.020), 0.035, 0.008, 1.6)                           # occipital bulge
    P = P + D * dr[..., None] + c
    V = [tuple(p) for p in P.reshape(-1, 3)]; F = []
    for i in range(nv - 1):
        for j in range(nu):
            j1 = (j + 1) % nu; F.append([i * nu + j, i * nu + j1, (i + 1) * nu + j1, (i + 1) * nu + j])
    add(V, F)                                                                  # pole rings collapse to points: the remesh welds them
HEADC = (0, -0.055, 1.625)
head(HEADC)
for s in (1, -1):
    blob((0.074 * s, -0.060, 1.617), (0.008, 0.017, 0.028))                    # ears (shrivelled)
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
    blob((0.11 * s, 0.02, 0.37), (0.035, 0.025, 0.08))                               # calf
    ft = np.array([0.115 * s, -0.16, 0.025])
    limb([an + [0, 0.02, 0.09], an + [0, 0.0, -0.05], ft], [(0, 0.03), (0.3, 0.04), (1, 0.03)], 20, 16, 0.6)
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
# (face landmarks live in head()) - emaciated ribs on the chest sides, then the hunch
if VAR == 'Bloated':                                                          # split belly: a ragged vertical tear opening into the gut
    tear = np.exp(-((x + 0.01 * np.sin(z * 90)) / 0.012) ** 2 - ((z - 1.08) / 0.07) ** 4) * (y < -0.15); co[:, 1] += 0.035 * tear
if VAR == 'Hollow':                                                           # ribcage torn open on the left of the chest
    d = np.sqrt(((x - 0.05) / 0.06) ** 2 + ((z - 1.28) / 0.08) ** 2); cav = np.exp(-d ** 4) * (y < -0.04)
    bars = (np.cos((z - 1.17) * 2 * np.pi / 0.034) > 0.45) * (np.abs(x - 0.05) < 0.05)              # broken rib bars left across the hole
    co[:, 1] += 0.06 * cav * (1 - 0.85 * bars)
if VAR == 'Burnt':                                                            # charred, cracked skin: shallow Voronoi-like grooves
    q = np.sin(x * 61 + np.sin(z * 37) * 2) * np.sin(z * 53 + np.sin(y * 41) * 2) * np.sin(y * 47 + x * 29); co -= (co - [0, 0, 1.0]) / (np.linalg.norm(co - [0, 0, 1.0], axis=1, keepdims=True) + 1e-6) * (0.004 * (np.abs(q) < 0.08))[:, None]
if VAR == 'Soldier':                                                          # tabard folds + torn, uneven hem
    rad = np.hypot(x, y); a = np.arctan2(x, y); tab = (rad > 0.125) * ss(0.70, 0.76, z) * (1 - ss(1.20, 1.28, z)) * (np.abs(x) < 0.21)
    co[:, :2] += np.stack([np.sin(a), np.cos(a)], 1) * (0.009 * np.sin(a * 13 + z * 6) * tab)[:, None]
    co[:, 2] += 0.07 * (0.5 + 0.5 * np.sin(a * 5 + 1.3)) ** 3 * (z < 0.80) * (z > 0.62) * (rad > 0.125) * (np.abs(x) < 0.21)
if VAR == 'Crawler':                                                          # ragged stump ends
    stump = ss(0.80, 0.70, z) * (z > 0.6); co[:, 2] += 0.02 * np.sin(x * 140 + y * 90) * stump
rib = np.cos((z - 1.17) * 2 * np.pi / 0.032) * ss(1.10, 1.16, z) * (1 - ss(1.34, 1.40, z)) * ss(0.06, 0.11, np.abs(x)) * (1 - ss(0.13, 0.15, np.abs(x))) * (y < 0.02)
co[:, :2] += (co[:, :2] / (np.linalg.norm(co[:, :2], axis=1, keepdims=True) + 1e-6)) * (0.0025 * rib)[:, None]
co[:, 1] += 0.012 * np.exp(-((x / 0.02) ** 2 + ((z - 1.25) / 0.10) ** 2)) * (y < -0.05)    # sternum groove
def hunch(p):
    # bend the upper body forward about the waist; the same map is applied to the bones so the rig matches
    p = np.atleast_2d(np.asarray(p, float)).copy(); a = np.radians(14) * ss(1.05, 1.50, p[:, 2]); dz = p[:, 2] - 1.05; dy = p[:, 1]
    p[:, 1] = dy * np.cos(a) - dz * np.sin(a); p[:, 2] = 1.05 + dy * np.sin(a) + dz * np.cos(a); return p
co[:] = hunch(co)
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
    b = ad.edit_bones.new(name); b.head = Vector(hunch(h)[0]); b.tail = Vector(hunch(t)[0])
    if parent: b.parent = ad.edit_bones[parent]
bone('root', (0, 0, 0), (0, 0.25, 0)); bone('pelvis', (0, 0, 0.95), (0, 0, 1.05), 'root')
bone('spine_01', (0, 0, 1.05), (0, -0.005, 1.17), 'pelvis'); bone('spine_02', (0, -0.005, 1.17), (0, 0.0, 1.29), 'spine_01'); bone('spine_03', (0, 0.0, 1.29), (0, -0.02, 1.42), 'spine_02')
bone('neck_01', (0, -0.02, 1.42), (0, -0.045, 1.53), 'spine_03'); bone('head', (0, -0.045, 1.53), (0, -0.055, 1.74), 'neck_01')
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
bone('headtop', (0, -0.055, 1.74), (0, -0.055, 1.80), 'head')
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
# bone heat can fail silently (the crawler came out with 0 weighted verts): any vertex left without weights gets
# inverse-distance weights to its 2 nearest bone segments, so no variant ships unrigged
vc = np.array([v.co for v in me.vertices]); bad = np.array([len(v.groups) == 0 for v in me.vertices])
if bad.any():
    bns = [b for b in ad.bones if b.use_deform and not b.name.endswith('_End')]
    Hd = np.array([b.head_local for b in bns]); Tl = np.array([b.tail_local for b in bns]); seg = Tl - Hd
    q = vc[bad][:, None, :] - Hd[None]; t = np.clip((q * seg[None]).sum(-1) / (seg ** 2).sum(-1)[None], 0, 1)
    dist = np.linalg.norm(q - t[..., None] * seg[None], axis=-1)
    Wb = np.zeros((len(vc), len(bns))); nb = np.argsort(dist, 1)[:, :2]; rows = np.nonzero(bad)[0]
    for j in range(2): Wb[rows, nb[:, j]] = 1.0 / (dist[np.arange(len(rows)), nb[:, j]] + 1e-3) ** 4
    Wb[rows] /= Wb[rows].sum(1, keepdims=True)
    ev = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get('vertices', ev); ev = ev.reshape(-1, 2)
    deg = np.bincount(ev.ravel(), minlength=len(vc)).astype(float)[:, None] + 1e-9
    for _ in range(30):                                                         # distance weights tear: diffuse them over the surface
        acc = np.zeros_like(Wb); np.add.at(acc, ev[:, 0], Wb[ev[:, 1]]); np.add.at(acc, ev[:, 1], Wb[ev[:, 0]])
        Wb[rows] = 0.4 * Wb[rows] + 0.6 * (acc / deg)[rows]
    top = np.argsort(-Wb[rows], 1)[:, :4]
    for k, vi in enumerate(rows):
        w = Wb[vi, top[k]]; w = w / max(w.sum(), 1e-9)
        for j, bi in enumerate(top[k]):
            if w[j] < 0.01: continue
            vg = body.vertex_groups.get(bns[bi].name) or body.vertex_groups.new(name=bns[bi].name); vg.add([int(vi)], float(w[j]), 'REPLACE')
print('WEIGHT FALLBACK verts', int(bad.sum()), flush=True)
print('BONES', len(ad.bones), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'zombie_%s.blend' % VAR))
print('RIG OK', flush=True)
