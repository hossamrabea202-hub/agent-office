# Rock cluster set (#202 item 4, TGA). blender -b --factory-startup -P build_rocks.py   -> rocks.blend
# Three weathered boulders for the road / courtyard: SM_Rock_S (~0.5 m), SM_Rock_M (~1.2 m), SM_Rock_L (~2.4 m), sharing
# one atlas (two skins Dry / Mossy in bake_rocks.py). Each: a noisy ellipsoid cut by random fracture planes (flat broken
# faces with soft edges), shallow bedding strata, sunk 15 % into the ground so it sits, then decimated. Z up, metres,
# pivot at ground level under the centre. Built side by side, split back into 3 objects (UVs kept) like the fence.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(204)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
def vn(p, f, seed=0):
    q = p * f; i = np.floor(q).astype(np.int64); t = q - i; t = t * t * (3 - 2 * t)
    def h(dx, dy, dz):
        n = ((i[:, 0] + dx) * 73856093) ^ ((i[:, 1] + dy) * 19349663) ^ ((i[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float64) / 65535.0
    x0 = h(0, 0, 0) + (h(1, 0, 0) - h(0, 0, 0)) * t[:, 0]; x1 = h(0, 1, 0) + (h(1, 1, 0) - h(0, 1, 0)) * t[:, 0]
    x2 = h(0, 0, 1) + (h(1, 0, 1) - h(0, 0, 1)) * t[:, 0]; x3 = h(0, 1, 1) + (h(1, 1, 1) - h(0, 1, 1)) * t[:, 0]
    y0 = x0 + (x1 - x0) * t[:, 1]; y1 = x2 + (x3 - x2) * t[:, 1]; return y0 + (y1 - y0) * t[:, 2]
def fbm(p, f, oct=4, seed=0):
    s, a, tot = 0.0, 1.0, 0.0
    for k in range(oct): s = s + a * vn(p, f * 2 ** k, seed + k); tot += a; a *= 0.5
    return s / tot
NAMES = [('SM_Rock_S', 0.5, 2200, 0.0), ('SM_Rock_M', 1.2, 4500, 3.0), ('SM_Rock_L', 2.4, 9000, 7.0)]
objs = []
for k, (name, size, tris, ox) in enumerate(NAMES):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
    P = np.array([v.co for v in bm.verts]); d = P / np.linalg.norm(P, axis=1, keepdims=True)
    r = 1.0 + 0.22 * (fbm(d * 1.0 + k * 7, 1.3, 3, 10 + k) - 0.5) + 0.05 * (fbm(d + k, 6, 3, 20 + k) - 0.5)
    P = d * r[:, None] * np.array([1.0, 0.8 + 0.1 * k, 0.62])           # wider than tall
    for c in range(7 + 2 * k):                                          # fracture planes: flatten everything beyond
        n = rng.normal(0, 1, 3); n[2] = abs(n[2]) * 0.6 if c % 3 else -abs(n[2]) * 0.2; n /= np.linalg.norm(n)
        off = rng.uniform(0.5, 0.8); s = P @ n - off
        P -= np.where(s > 0, s, 0)[:, None] * n * 0.8                  # 80 %: faces keep a hint of curvature
        P -= (0.015 * (fbm(P, 9, 3, 30 + c) - 0.5) * (np.abs(s) < 0.04))[:, None] * n   # chipped edge along each cut
    P[:, 2] += 0.012 * np.sin(P[:, 2] * 38 + 3 * fbm(P, 2, 2, 40 + k))  # bedding strata
    P *= size / (P[:, 0].max() - P[:, 0].min())
    P[:, 2] -= P[:, 2].min() + 0.15 * (P[:, 2].max() - P[:, 2].min())   # sink 15 %
    for v, p in zip(bm.verts, P): v.co = Vector(p)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    s_ = me.attributes.new('seg', 'INT', 'POINT'); s_.data.foreach_set('value', np.full(len(me.vertices), k, np.int32))
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location.x = ox
    bpy.context.view_layer.objects.active = o
    dm = o.modifiers.new('D', 'DECIMATE'); dm.ratio = tris / (len(me.polygons)); bpy.ops.object.modifier_apply(modifier='D')
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, -0.08 * size), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(me); bm.free()                                           # cut away what is deep underground
    objs.append(o); print('ROCK', name, len(me.polygons), flush=True)
for o in bpy.context.scene.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.duplicate(); dup = bpy.context.selected_objects
bpy.context.view_layer.objects.active = dup[0]; bpy.ops.object.transform_apply(location=True); bpy.ops.object.join()
at = bpy.context.active_object; at.name = 'SM_RockAtlas'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_smooth()
for o in objs: bpy.data.objects.remove(o)                              # rebuild the 3 from the atlas so they carry its UVs
seg = np.empty(len(at.data.vertices), np.int32); at.data.attributes['seg'].data.foreach_get('value', seg)
for k, (name, size, tris, ox) in enumerate(NAMES):
    c = at.copy(); c.data = at.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-ox, 0, 0)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
print('ATLAS tris', len(at.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'rocks.blend'))
