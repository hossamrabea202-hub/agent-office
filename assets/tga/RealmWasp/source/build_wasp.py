# Realm wasp (#156, TGA, 2026-10-30): a human-sized stinging insect for the tentacle realm. Original, procedural.
#   blender -b --factory-startup -P build_wasp.py          ->  wasp_rig.blend (mesh + UVs + rig + skin weights)
# Body faces -Y (Blender front), so it imports facing +Y in UE like the mannequin. Metres, Z up, root on the ground
# under the body; the body hovers at Z0. Every part is a loft (rings along a path), so UVs come straight from the
# topology: U around the ring, V along the length, both in metres (even texel density), seam on the underside.
import bpy, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
Z0 = 1.30
rng = np.random.default_rng(156)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)      # factory scene: drop the default cube, light, camera

def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    ref = np.array([0, 0, 1.0]) if abs(T[0] @ [0, 0, 1]) < 0.9 else np.array([1.0, 0, 0])
    N = np.zeros_like(P); n = ref - (ref @ T[0]) * T[0]; n /= np.linalg.norm(n)
    for i in range(len(P)):                       # parallel transport, no flips along the path
        n = n - (n @ T[i]) * T[i]; n /= np.linalg.norm(n) + 1e-9; N[i] = n
    return T, N, np.cross(T, N)

def loft(P, rx, ry, seg=20, up=None, prof=None):
    """rings along path P (n,3), radii rx (along N) and ry (along B). An end whose radius is ~0 becomes a pole.
    prof(i, a) -> radial scale (for ridges). Returns verts, faces (lists of vertex ids) and per-face-corner UVs (m)."""
    P = np.asarray(P, float); n = len(P); T, N, B = frames(P)
    if up is not None:                             # roll the frame so N points along 'up' at the start (seam on -N side)
        u0 = np.asarray(up, float)
        for i in range(n):
            nn = u0 - (u0 @ T[i]) * T[i]
            if np.linalg.norm(nn) > 1e-3: nn /= np.linalg.norm(nn); N[i] = nn; B[i] = np.cross(T[i], nn)
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False) + np.pi    # angle 0 = +N; seam at angle pi = -N (underside)
    verts, rows = [], []
    for i in range(n):
        if (i == 0 or i == n - 1) and max(rx[i], ry[i]) < 1e-4:
            rows.append([len(verts)]); verts.append(P[i]); continue
        row = []
        for a in ang:
            s = prof(i, a) if prof else 1.0
            row.append(len(verts)); verts.append(P[i] + s * (rx[i] * math.cos(a) * N[i] + ry[i] * math.sin(a) * B[i]))
        rows.append(row)
    # V = arc length along the path, U = arc length around the ring at the widest point
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    circ = np.pi * (np.max(rx) + np.max(ry))
    faces, uvs = [], []
    for i in range(n - 1):
        a, b = rows[i], rows[i + 1]
        for j in range(seg):
            j1 = j + 1; u0, u1 = j / seg * circ, j1 / seg * circ
            if len(a) == 1:
                faces.append([a[0], b[j1 % seg], b[j]]); uvs.append([((u0 + u1) / 2, L[i]), (u1, L[i + 1]), (u0, L[i + 1])])
            elif len(b) == 1:
                faces.append([a[j], a[j1 % seg], b[0]]); uvs.append([(u0, L[i]), (u1, L[i]), ((u0 + u1) / 2, L[i + 1])])
            else:
                faces.append([a[j], a[j1 % seg], b[j1 % seg], b[j]]); uvs.append([(u0, L[i]), (u1, L[i]), (u1, L[i + 1]), (u0, L[i + 1])])
    return np.array(verts), faces, uvs, L / max(L[-1], 1e-9), rows

PARTS = {'head': 0, 'thorax': 1, 'petiole': 2, 'abdomen': 3, 'stinger': 4, 'leg': 5, 'eye': 6, 'mandible': 7, 'antenna': 8}
pieces = []          # (name, verts, faces, uvs, part id, per-vertex u (0..1 along), per-vertex bone weights {bone: w array})

def add(name, part, P, rx, ry, seg, weights, up=(0, 0, 1), prof=None):
    v, f, uv, t, rows = loft(P, np.asarray(rx, float), np.asarray(ry, float), seg, up, prof)
    uvert = np.zeros(len(v))
    for i, r in enumerate(rows): uvert[r] = t[i]
    W = weights(v, uvert) if callable(weights) else {weights: np.ones(len(v))}
    pieces.append((name, v, f, uv, PARTS[part], uvert, W))

def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def path(pts, n):
    """smooth path through control points (Catmull-Rom), n samples."""
    pts = np.asarray(pts, float); out = []
    for k in range(n):
        s = k / (n - 1) * (len(pts) - 1); i = min(int(s), len(pts) - 2); t = s - i
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)

# ---- body ------------------------------------------------------------------------------------------------------
n = 40; t = np.linspace(0, 1, n)
# head: a broad wedge, wider than tall, flat face toward -Y
P = np.stack([np.zeros(n), -0.47 - 0.31 * t, Z0 + 0.02 - 0.05 * t ** 2], 1)
sh = np.sin(np.pi * np.clip(t, 0, 1) ** 0.8) ** 0.55; sh[0] = sh[-1] = 0
add('head', 'head', P, 0.165 * sh * (1 - 0.25 * t), 0.15 * sh, 28, 'head')
# compound eyes: big kidney-shaped domes on the sides of the head
for sgn in (1, -1):
    m = 26; te = np.linspace(0, 1, m)
    P = path([(0.088 * sgn, -0.53, Z0 + 0.10), (0.106 * sgn, -0.62, Z0 + 0.03), (0.09 * sgn, -0.70, Z0 - 0.07)], m)
    se = np.sqrt(np.clip(np.sin(np.pi * te), 0, 1)); se[0] = se[-1] = 0
    add('eye_' + ('L' if sgn > 0 else 'R'), 'eye', P, 0.046 * se, 0.06 * se, 20, 'head', up=(sgn, 0, 0))   # set into the head
    # mandibles: curved hooks that close in front of the face
    m = 16; tm = np.linspace(0, 1, m)
    P = path([(0.05 * sgn, -0.74, Z0 - 0.06), (0.085 * sgn, -0.82, Z0 - 0.10), (0.05 * sgn, -0.89, Z0 - 0.12), (0.008 * sgn, -0.90, Z0 - 0.11)], m)
    r = 0.019 * (1 - tm) ** 0.7 + 0.002; r[-1] = 0
    add('mandible_' + ('L' if sgn > 0 else 'R'), 'mandible', P, r, r * 0.7, 10, 'mandible_' + ('L' if sgn > 0 else 'R'), up=(0, 0, 1))
    # antennae: scape up from the face, elbow, a long flagellum arcing forward
    m = 30; ta = np.linspace(0, 1, m)
    P = path([(0.035 * sgn, -0.73, Z0 + 0.07), (0.06 * sgn, -0.78, Z0 + 0.22), (0.16 * sgn, -0.92, Z0 + 0.30), (0.26 * sgn, -1.08, Z0 + 0.24)], m)
    r = 0.012 - 0.005 * ta; r[-1] = 0
    add('antenna_' + ('L' if sgn > 0 else 'R'), 'antenna', P, r, r, 8, 'antenna_' + ('L' if sgn > 0 else 'R'), up=(0, 0, 1))

# thorax: a barrel, highest over the wing roots
n = 36; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), -0.04 - 0.44 * t, Z0 + 0.03 * np.sin(np.pi * t)], 1)
sh = np.sin(np.pi * t) ** 0.45; sh[0] = sh[-1] = 0
add('thorax', 'thorax', P, 0.19 * sh, 0.20 * sh * (1 + 0.06 * np.sin(np.pi * t)), 30, 'thorax')
# petiole: the thin waist
n = 12; t = np.linspace(0, 1, n)
P = np.stack([np.zeros(n), 0.10 - 0.18 * t, Z0 - 0.01 * t], 1)
r = 0.045 + 0.02 * (np.abs(t - 0.5) * 2) ** 2
add('petiole', 'petiole', P, r, r, 14, 'abdomen_01')
# abdomen: six overlapping segments, drooping; each segment's rear rim stands proud of the next one
n = 90; t = np.linspace(0, 1, n)
P = path([(0, 0.08, Z0), (0, 0.32, Z0 - 0.06), (0, 0.58, Z0 - 0.17), (0, 0.78, Z0 - 0.30)], n)
env = np.sin(np.pi * np.clip(t, 0, 1) ** 0.58) ** 0.55 * (1 - 0.25 * t ** 3); env[0] = env[-1] = 0   # wasp gaster: pointed tail
segf = (t * 6.2) % 1.0
rim = 1 - 0.05 * ss(0.0, 0.18, segf) * (1 - ss(0.82, 1.0, segf)) + 0.02 * ss(0.85, 1.0, segf)   # tapers into the next segment
def abd_w(v, u):
    w2 = ss(0.38, 0.52, u); return {'abdomen_01': 1 - w2, 'abdomen_02': w2}
add('abdomen', 'abdomen', P, 0.205 * env * rim, 0.19 * env * rim, 32, abd_w)
# stinger: a long curved lance out of the last segment
m = 20; ts = np.linspace(0, 1, m)
P = path([(0, 0.75, Z0 - 0.28), (0, 0.86, Z0 - 0.37), (0, 0.95, Z0 - 0.47)], m)
r = 0.028 * (1 - ts) ** 1.3; r[-1] = 0
add('stinger', 'stinger', P, r, r, 12, 'stinger')

# ---- legs: coxa under the thorax, femur out and up, tibia down, tarsus with a hooked claw ---------------------------
LEGS = {'F': (-0.40, 0.10, -0.25), 'M': (-0.26, 0.00, 0.0), 'H': (-0.12, -0.06, 0.32)}
legbones = {}
for key, (y0, dy, sweep) in LEGS.items():
    for sgn in (1, -1):
        sd = 'L' if sgn > 0 else 'R'
        hip = np.array([0.07 * sgn, y0, Z0 - 0.13])
        knee = hip + np.array([0.34 * sgn, dy + sweep * 0.5, 0.06])
        ankle = knee + np.array([0.10 * sgn, sweep * 0.6 + 0.05, -0.42])
        toe = ankle + np.array([0.04 * sgn, sweep * 0.35 + 0.04, -0.27])
        claw = toe + np.array([-0.015 * sgn, -0.035, -0.02])
        m = 60; P = path([hip, hip + (knee - hip) * 0.5 + [0, 0, 0.03], knee, knee + (ankle - knee) * 0.5, ankle, ankle + (toe - ankle) * 0.5, toe, claw], m)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); tl = L / L[-1]
        j1 = np.linalg.norm(knee - hip) / L[-1]; j2 = j1 + np.linalg.norm(ankle - knee) / L[-1]
        # radius: chunky femur, thinner tibia with a joint swelling, fine tarsus segments
        r = np.where(tl < j1, 0.027 - 0.005 * tl / j1, np.where(tl < j2, 0.019 - 0.005 * (tl - j1) / (j2 - j1), 0.012 - 0.007 * (tl - j2) / (1 - j2)))
        r *= 1 + 0.18 * np.exp(-((tl - j1) / 0.02) ** 2) + 0.12 * np.exp(-((tl - j2) / 0.02) ** 2)
        r *= 1 - 0.12 * ss(0.3, 0.5, np.abs(np.sin((tl - j2) / (1 - j2) * np.pi * 5))) * (tl > j2)     # tarsal segments
        r[0] = r[0] * 0.9; r[-1] = 0
        names = [f'leg_{key}_{sd}_1', f'leg_{key}_{sd}_2', f'leg_{key}_{sd}_3']
        legbones[(key, sd)] = (hip, knee, ankle, claw, names)
        def lw(v, u, j1=j1, j2=j2, names=names):
            a = ss(j1 - 0.015, j1 + 0.015, u); b = ss(j2 - 0.015, j2 + 0.015, u)
            return {names[0]: 1 - a, names[1]: a - b, names[2]: b}
        add(f'leg_{key}_{sd}', 'leg', P, r, r * 0.92, 12, lw, up=(0, 0, 1))

# ---- build the body mesh ----------------------------------------------------------------------------------------
V, F, UV, PART, UVERT = [], [], [], [], []; groups = {}
for name, v, f, uv, pid, uvert, W in pieces:
    off = len(V)
    for k, w in W.items(): groups.setdefault(k, []).append((off, w))
    V.extend(v.tolist()); F.extend([[i + off for i in face] for face in f]); UV.extend(uv); PART.extend([pid] * len(v)); UVERT.extend(uvert.tolist())
me = bpy.data.meshes.new('SK_RealmWasp'); me.from_pydata(V, [], F); me.update()
uvl = me.uv_layers.new(name='UVMap')
flat = [c for face in UV for c in face]
uvl.data.foreach_set('uv', np.array(flat, np.float32).ravel())
me.attributes.new('part', 'FLOAT', 'POINT').data.foreach_set('value', np.array(PART, np.float32))
me.attributes.new('ulen', 'FLOAT', 'POINT').data.foreach_set('value', np.array(UVERT, np.float32))
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
body = bpy.data.objects.new('SK_RealmWasp', me); bpy.context.scene.collection.objects.link(body)
for k, lst in groups.items():
    vg = body.vertex_groups.new(name=k)
    for off, w in lst:
        for i in np.nonzero(w > 1e-4)[0]: vg.add([int(off + i)], float(w[i]), 'REPLACE')
print('BODY verts', len(V), 'tris', sum(len(f) - 2 for f in F), flush=True)

# ---- wings: two pairs, flat membranes; UV = (span, chord) into one atlas (forewing top half, hindwing bottom) -----
def wing(span, chord, root, sweep_deg, sgn, vrow, name):
    ns, nc = 22, 9; vs, fs, uvs = [], [], []
    for i in range(ns + 1):
        s = i / ns
        c = chord * (0.42 + 0.58 * math.sin(math.pi * min(1.0, s * 1.08) ** 0.55)) * (1 - 0.65 * s ** 6)   # rounded tip
        le = 0.06 * chord * math.sin(math.pi * s)                                                            # leading edge bow
        for j in range(nc + 1):
            q = j / nc
            x, y = s * span, -le + q * c                                                                      # y back from the leading edge
            a = math.radians(sweep_deg); xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)   # tip swept back (+Y)
            vs.append((root[0] + sgn * xr, root[1] + yr, root[2] + 0.02 * math.sin(math.pi * s)))
            uvs.append((s, vrow + 0.5 * (q * c / chord) * 0.96 + 0.01))
    for i in range(ns):
        for j in range(nc):
            a = i * (nc + 1) + j; f = [a, a + nc + 1, a + nc + 2, a + 1]
            fs.append(f if sgn > 0 else f[::-1])
    return vs, fs, uvs
WV, WF, WUV, WG = [], [], [], []
WINGS = {'fore': (1.10, 0.33, (0.09, -0.36, Z0 + 0.15), 12, 0.5), 'hind': (0.74, 0.22, (0.09, -0.20, Z0 + 0.13), 18, 0.0)}
wingroots = {}
for key, (span, chord, root, sweep, vrow) in WINGS.items():
    for sgn in (1, -1):
        sd = 'L' if sgn > 0 else 'R'; rt = (root[0] * sgn, root[1], root[2])
        vs, fs, uvs = wing(span, chord, rt, sweep, sgn, vrow, key)
        off = len(WV); WV += vs; WF += [[i + off for i in f] for f in fs]; WUV += uvs; WG.append((f'wing_{key}_{sd}', off, len(vs)))
        wingroots[(key, sd)] = (np.array(rt), None)
wm = bpy.data.meshes.new('SK_RealmWasp_Wings'); wm.from_pydata(WV, [], WF); wm.update()
wl = wm.uv_layers.new(name='UVMap'); wl.data.foreach_set('uv', np.array([WUV[li.vertex_index] for li in wm.loops], np.float32).ravel())
wings = bpy.data.objects.new('SK_RealmWasp_Wings', wm); bpy.context.scene.collection.objects.link(wings)
for gname, off, cnt in WG: wings.vertex_groups.new(name=gname).add(list(range(off, off + cnt)), 1.0, 'REPLACE')
print('WINGS verts', len(WV), 'tris', 2 * len(WF), flush=True)

# ---- pack body UVs: islands are already in metres, so a uniform-scale pack keeps texel density even --------------
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT'); body.select_set(False)

# ---- armature -----------------------------------------------------------------------------------------------------
ad = bpy.data.armatures.new('SK_RealmWasp_Skeleton'); arm = bpy.data.objects.new('SK_RealmWasp_Rig', ad)
bpy.context.scene.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
def bone(name, h, t, parent=None, roll=0.0):
    b = ad.edit_bones.new(name); b.head = Vector(h); b.tail = Vector(t); b.roll = roll
    if parent: b.parent = ad.edit_bones[parent]; b.use_connect = False
    return b
bone('root', (0, 0, 0), (0, 0.3, 0))
bone('thorax', (0, -0.05, Z0), (0, -0.45, Z0), 'root')
bone('head', (0, -0.47, Z0 + 0.01), (0, -0.76, Z0 - 0.02), 'thorax')
for sd, sgn in (('L', 1), ('R', -1)):
    bone(f'mandible_{sd}', (0.05 * sgn, -0.74, Z0 - 0.06), (0.01 * sgn, -0.90, Z0 - 0.11), 'head')
    bone(f'antenna_{sd}', (0.035 * sgn, -0.73, Z0 + 0.07), (0.26 * sgn, -1.08, Z0 + 0.24), 'head')
bone('abdomen_01', (0, 0.0, Z0), (0, 0.38, Z0 - 0.08), 'thorax')
bone('abdomen_02', (0, 0.38, Z0 - 0.08), (0, 0.76, Z0 - 0.29), 'abdomen_01')
bone('stinger', (0, 0.76, Z0 - 0.29), (0, 0.95, Z0 - 0.47), 'abdomen_02')
for (key, sd), (rt, tip) in wingroots.items():
    span = WINGS[key][0]; sgn = 1 if sd == 'L' else -1; a = math.radians(WINGS[key][3])
    bone(f'wing_{key}_{sd}', tuple(rt), tuple(rt + np.array([sgn * span * math.cos(a), span * math.sin(a), 0])), 'thorax')
for (key, sd), (hip, knee, ankle, claw, names) in legbones.items():
    bone(names[0], tuple(hip), tuple(knee), 'thorax'); bone(names[1], tuple(knee), tuple(ankle), names[0]); bone(names[2], tuple(ankle), tuple(claw), names[1])
bpy.ops.object.mode_set(mode='OBJECT')
for ob in (body, wings):
    ob.parent = arm; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm
print('BONES', len(ad.bones), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'wasp_rig.blend'))
print('RIG OK', flush=True)
