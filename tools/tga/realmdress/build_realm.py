# Realm dressing (#202 item 10, TGA). blender -b --factory-startup -P build_realm.py   -> realm.blend
# SM_Realm_SpitSac: a tentacle-burrow spit sac - earth mound broken open by a fleshy root, a ribbed stalk and a swollen,
# glowing sac on top (ties to the #155/#169 realm creatures). SM_Realm_SporeVent: a fleshy chimney with a ridged rim and
# a glowing pink mouth, spore nodules round its foot. Built like the zombies: lofts + blobs fused by a voxel remesh,
# smoothed, decimated. One shared 2K atlas; bake_realm.py finds the regions (earth / flesh / sac / glow) from landmarks.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(210)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    up = np.array([0, 0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0, 0])
    N = np.cross(up, T); N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9; return T, N, np.cross(T, N)
def loft(P, r, seg=20, rib=0.0, nrib=0):
    P = np.asarray(P, float); T, N, B = frames(P); ang = np.linspace(0, 2 * np.pi, seg, endpoint=False); V, F = [], []
    for i in range(len(P)):
        rr = r[i] * (1 + rib * np.cos(ang * nrib))
        for k, a in enumerate(ang): V.append(P[i] + rr[k] * (math.cos(a) * N[i] + math.sin(a) * B[i]))
    for i in range(len(P) - 1):
        for k in range(seg): F.append([i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k])
    F.append(list(range(seg))[::-1]); F.append([(len(P) - 1) * seg + k for k in range(seg)]); return V, F
def blob(c, r, n=16):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=n * 2, v_segments=n, radius=1.0)
    for v in bm.verts: v.co = Vector((c[0] + v.co.x * r[0], c[1] + v.co.y * r[1], c[2] + v.co.z * r[2]))
    V = [tuple(v.co) for v in bm.verts]; F = [[v.index for v in f.verts] for f in bm.faces]; bm.free(); return V, F
def build(name, parts, ox, tris):
    V, F = [], []
    for v, f in parts:
        off = len(V); V += [tuple(x) for x in v]; F += [[i + off for i in face] for face in f]
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); bpy.context.view_layer.objects.active = o
    for typ, kw in (('REMESH', dict(mode='VOXEL', voxel_size=0.012)), ('LAPLACIANSMOOTH', dict(lambda_factor=0.5, iterations=5, use_volume_preserve=True))):
        m = o.modifiers.new(typ, typ)
        for k, v in kw.items(): setattr(m, k, v)
        bpy.ops.object.modifier_apply(modifier=m.name)
    co = np.array([v.co for v in me.vertices]); d = co.copy()                  # organic surface noise after the fuse
    n = np.array([v.normal for v in me.vertices])
    noise = np.sin(co[:, 0] * 37 + np.sin(co[:, 2] * 23) * 2) * np.sin(co[:, 1] * 31 + np.sin(co[:, 0] * 19) * 2)
    for v, p, nn, s in zip(me.vertices, co, n, noise): v.co = Vector(p + nn * 0.006 * s)
    m = o.modifiers.new('D', 'DECIMATE'); m.ratio = min(1.0, tris / max(len(me.polygons) * 2, 1)); bpy.ops.object.modifier_apply(modifier='D')
    o.location.x = ox; print('BUILT', name, sum(len(p.vertices) - 2 for p in me.polygons), flush=True); return o
# ---- spit sac ------------------------------------------------------------------------------------------------------
parts = [blob((0, 0, -0.05), (0.75, 0.65, 0.22))]                                 # earth mound
for k in range(5):                                                               # heaved clods round the hole
    a = 2 * math.pi * k / 5 + rng.normal(0, 0.2); parts.append(blob((0.42 * math.cos(a), 0.36 * math.sin(a), 0.1), (0.16, 0.12, 0.1), 10))
t = np.linspace(0, 1, 30); P = np.stack([0.06 * np.sin(t * 5), 0.04 * np.cos(t * 4), -0.1 + 0.95 * t], 1)
parts.append(loft(P, 0.16 - 0.06 * t + 0.012 * np.sin(t * 22), 20, rib=0.1, nrib=6))   # ribbed stalk
parts.append(blob((0.05, 0.03, 1.02), (0.3, 0.28, 0.36), 20))                    # the sac
for k in range(3):                                                               # roots breaking out of the mound
    a = 2 * math.pi * k / 3 + 0.5; t = np.linspace(0, 1, 16)
    P = np.stack([(0.1 + 0.6 * t) * math.cos(a), (0.1 + 0.6 * t) * math.sin(a), 0.12 * np.sin(t * math.pi) - 0.02], 1)
    parts.append(loft(P, 0.07 * (1 - 0.8 * t), 14))
sac = build('SM_Realm_SpitSac', parts, 0.0, 9000)
# ---- spore vent ----------------------------------------------------------------------------------------------------
t = np.linspace(0, 1, 30); P = np.stack([0 * t, 0 * t, -0.1 + 0.85 * t], 1)
r = 0.5 - 0.28 * t + 0.1 * np.exp(-((t - 0.95) / 0.06) ** 2)                      # chimney, flared lip
parts = [loft(P, r, 28, rib=0.12, nrib=7)]
for k in range(8):                                                               # spore nodules round the foot
    a = 2 * math.pi * k / 8 + rng.normal(0, 0.2); rr = 0.5 + rng.uniform(0, 0.25)
    s = rng.uniform(0.06, 0.12); parts.append(blob((rr * math.cos(a), rr * math.sin(a), 0.02), (s, s, s * 0.9), 10))
vent = build('SM_Realm_SporeVent', parts, 2.5, 7000)
# hollow the mouth: push the top cap down into a throat
me = vent.data; co = np.array([v.co for v in me.vertices]); rad = np.hypot(co[:, 0], co[:, 1])
mouth = (co[:, 2] > 0.68) & (rad < 0.17)
for v, m_, rr in zip(me.vertices, mouth, rad):
    if m_: v.co.z -= 0.35 * (1 - rr / 0.17) ** 0.5
me.update()
for o in (sac, vent): o.select_set(True)
bpy.context.view_layer.objects.active = sac
bpy.ops.object.duplicate(); dup = bpy.context.selected_objects; bpy.context.view_layer.objects.active = dup[0]
bpy.ops.object.transform_apply(location=True); bpy.ops.object.join(); at = bpy.context.active_object; at.name = 'SM_RealmAtlas'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_smooth()
# split back by x (sac < 1.25 m < vent) so both carry the atlas UVs; origin back to each piece's foot
for name, keep, ox in (('SM_Realm_SpitSac', lambda x: x < 1.25, 0.0), ('SM_Realm_SporeVent', lambda x: x >= 1.25, 2.5)):
    old = bpy.data.objects[name]; bpy.data.objects.remove(old)
    c = at.copy(); c.data = at.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co.x)], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-ox, 0, 0)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
    print('SEG', name, len(c.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'realm.blend'))
