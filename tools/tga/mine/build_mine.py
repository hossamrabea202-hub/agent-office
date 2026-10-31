# Underground mine dungeon kit (#309 for #297, TGA). blender -b --factory-startup -P build_mine.py  -> mine.blend (env WORK)
# Tunnels are carved: a rock block minus a swept tunnel void (exact boolean, so every piece is a closed watertight solid),
# voxel-remeshed, hewn-rock displacement (pick facets, calmer floor) that fades to zero at the module faces so pieces join
# seamlessly on a 4 m grid, then decimated. Vertex colour R = wetness (floor band + gravity drip streaks) drives the
# material's damp darkening. UV0 = metric box projection (2 m per tile) for the tileable baked rock set.
# Grid: a module occupies x 0..4, y -2..2 (chamber 0..14, -6..6); tunnels run along the cell centre lines, floor z = 0.
# Profile 3 m wide, 2.8 m high. Props are modelled at real size with metric UVs on tiling oak / iron / ore / rock sets.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
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
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
MATS = ('M_MineRock', 'M_MineOak', 'M_MineIron', 'M_MineOre', 'M_MineGlow')
def mat(n): return bpy.data.materials.get(n) or bpy.data.materials.new(n)
def link(name, me):
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o
def act(o):
    for x in bpy.context.scene.objects: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
def apply_mod(o, typ, **kw):
    act(o); m = o.modifiers.new('m', typ)
    for k, v in kw.items(): setattr(m, k, v)
    bpy.ops.object.modifier_apply(modifier=m.name)

# ---------------- tunnel profile + void sweep ----------------
def profile():
    pts = [(-1.5 + 3.0 * i / 6, 0.0) for i in range(7)]                     # floor, left to right
    pts += [(1.5 + 0.03 * k, 0.4 * k) for k in (1, 2, 3)]                   # right wall, bowing out
    for k in range(1, 9):                                                   # superellipse arch 1.2 -> 2.8
        a = math.pi / 2 * k / 8; pts.append((1.59 * math.cos(a) ** 0.5, 1.2 + 1.6 * math.sin(a) ** 0.5))
    pts = pts + [(-y, z) for (y, z) in reversed(pts[7:-1])]
    return pts
PRO = profile()
def sweep(path, name='void'):
    """path: list of (pos Vector, tangent Vector). Closed tube (capped) for the boolean."""
    bm = bmesh.new(); rings = []
    for p, t in path:
        t = t.normalized(); side = Vector((-t.y, t.x, 0)).normalized()
        rings.append([bm.verts.new(p + side * y + Vector((0, 0, z))) for (y, z) in PRO])
    n = len(PRO)
    for a, b in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return link(name, me)
def line(a, b, n=8):
    a, b = Vector(a), Vector(b); return [(a.lerp(b, i / n), b - a) for i in range(n + 1)]
def arc(c, r, a0, a1, n=16, z=0.0):
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; p = Vector((c[0] + r * math.cos(a), c[1] + r * math.sin(a), z))
        out.append((p, Vector((-math.sin(a), math.cos(a), 0)) * (1 if a1 > a0 else -1)))
    return out
def block(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((x0 + (v.co.x + .5) * (x1 - x0), y0 + (v.co.y + .5) * (y1 - y0), z0 + (v.co.z + .5) * (z1 - z0)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return link(name, me)
def carve(name, box, voids, faces, tris, seed, chamber=False):
    o = block(name, *box)
    for v in voids:
        apply_mod(o, 'BOOLEAN', object=v, operation='DIFFERENCE', solver='EXACT'); bpy.data.objects.remove(v)
    apply_mod(o, 'REMESH', mode='VOXEL', voxel_size=0.045)
    me = o.data; n = len(me.vertices); P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    N = np.array([v.vector for v in me.vertex_normals])
    x0, x1, y0, y1, z0, z1 = box
    dface = np.min(np.stack([np.abs(P[:, 0] - x0), np.abs(P[:, 0] - x1), np.abs(P[:, 1] - y0), np.abs(P[:, 1] - y1), np.abs(P[:, 2] - z0), np.abs(P[:, 2] - z1)]), axis=0)
    fade = ss(0.02, 0.6, dface)                                              # 0 at the module faces: seamless joins
    calm = 1 - 0.8 * ss(0.6, 0.9, N[:, 2]) * ss(0.4, 0.0, P[:, 2])          # the walkable floor stays calmer
    big = 0.4 if chamber else 0.07
    d = big * (fbm(P, 0.9, 3, seed) - 0.5) + (0.12 if chamber else 0.05) * (1 - np.abs(2 * fbm(P, 3.0, 3, seed + 1) - 1)) + 0.015 * (fbm(P, 11, 2, seed + 2) - 0.5)
    P += N * (d * fade * calm)[:, None]; me.vertices.foreach_set('co', P.ravel()); me.update()
    apply_mod(o, 'DECIMATE', ratio=min(1.0, tris / max(1, len(me.polygons))))
    me = o.data; n = len(me.vertices); P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    streak = ss(0.62, 0.8, vn(P * [1, 1, 0.08], 5.0, seed + 3)) * ss(2.9, 1.0, P[:, 2])   # drips run down (stretched in z)
    wet = np.clip(ss(0.7, 0.0, P[:, 2]) * 0.85 + streak * 0.7 + 0.15 * fbm(P, 1.2, 2, seed + 4), 0, 1)
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
    cols = np.ones((n, 4)); cols[:, 0] = wet; cols[:, 1] = 0; cols[:, 2] = 0; ca.data.foreach_set('color', cols.ravel())
    me.materials.clear(); me.materials.append(mat('M_MineRock')); me.polygons.foreach_set('material_index', np.zeros(len(me.polygons), np.int32))
    uvbox(o, 2.0); bpy.ops.object.shade_smooth()
    return o
def uvbox(o, size):
    act(o); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=size, scale_to_bounds=False, correct_aspect=False); bpy.ops.object.mode_set(mode='OBJECT')

# ---------------- props ----------------
def cyl(bm, a, b, r, seg=8, jitter=0.0, rng=None):
    a, b = Vector(a), Vector(b); ax = (b - a).normalized()
    u = ax.orthogonal().normalized(); v = ax.cross(u)
    ra, rb = [], []
    for i in range(seg):
        t = 2 * math.pi * i / seg; rr = r * (1 + (rng.uniform(-jitter, jitter) if rng is not None else 0))
        off = (u * math.cos(t) + v * math.sin(t)) * rr; ra.append(bm.verts.new(a + off)); rb.append(bm.verts.new(b + off))
    for i in range(seg): bm.faces.new((ra[i], ra[(i + 1) % seg], rb[(i + 1) % seg], rb[i]))
    bm.faces.new(ra[::-1]); bm.faces.new(rb)
def box(bm, c, s, rot=0.0):
    r = bmesh.ops.create_cube(bm, size=1.0); vs = r['verts']
    M = Matrix.Translation(Vector(c)) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Diagonal((s[0], s[1], s[2], 1))
    for v in vs: v.co = M @ v.co
    return vs
def prop(name, parts, uv=1.0, bevel=0.0):
    """parts: list of (material name, builder(bm)). One mesh, one material slot per material."""
    me = bpy.data.meshes.new(name); o = link(name, me); bm = bmesh.new(); used = []
    for mn, fn in parts:
        if mn not in used: used.append(mn)
        before = set(bm.faces); fn(bm)
        for f in bm.faces:
            if f not in before: f.material_index = used.index(mn)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for mn in used: me.materials.append(mat(mn))
    if bevel: apply_mod(o, 'BEVEL', width=bevel, segments=1, limit_method='ANGLE')
    uvbox(o, uv); return o
rng = np.random.default_rng(309)

if __name__ == '__main__':
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    Z = (-0.6, 3.6); kit = []
    kit.append(carve('SM_Mine_Tunnel_Straight', (0, 4, -2, 2) + Z, [sweep(line((-0.3, 0, 0), (4.3, 0, 0)))], [(1, -2), (1, 2)], 5000, 1))
    kit.append(carve('SM_Mine_Tunnel_Turn', (0, 4, -2, 2) + Z, [sweep(line((-0.3, 0, 0), (0.02, 0, 0), 1) + arc((0, 2), 2, -math.pi / 2, 0) + line((2, 2.02, 0), (2, 2.3, 0), 1))],
                      [(0, 4), (1, -2)], 5000, 2))
    kit.append(carve('SM_Mine_Tunnel_T', (0, 4, -2, 2) + Z, [sweep(line((-0.3, 0, 0), (4.3, 0, 0))), sweep(line((2, -0.5, 0), (2, 2.3, 0)))], [(1, -2)], 6000, 3))
    kit.append(carve('SM_Mine_Tunnel_DeadEnd', (0, 4, -2, 2) + Z,
                     [sweep(line((-0.3, 0, 0), (2.2, 0, 0)) + [(Vector((2.2 + 0.5 * math.sin(a), 0, 0)), Vector((1, 0, 0))) for a in (0.3, 0.6)])],
                     [(0, 4), (1, -2), (1, 2)], 4500, 4))
    h = 4 * math.tan(math.radians(15))
    kit.append(carve('SM_Mine_Tunnel_Slope15', (0, 4, -2, 2, -0.6, 3.6 + h), [sweep(line((-0.3, 0, -0.3 * h / 4), (4.3, 0, 4.3 * h / 4)))], [(1, -2), (1, 2)], 5000, 5))
    ch = block('cv', 1.4, 12.6, -5.0, 5.0, 0.0, 5.2); apply_mod(ch, 'BEVEL', width=1.6, segments=5)
    kit.append(carve('SM_Mine_Chamber', (0, 14, -6, 6, -0.6, 6.4), [ch, sweep(line((-0.3, 0, 0), (2.4, 0, 0), 2)), sweep(line((11.6, 0, 0), (14.3, 0, 0), 2))],
                     [(1, -6), (1, 6), (2, 6.4)], 16000, 6, chamber=True))
    # timber set: two props + cap beam + wedges + iron spikes, for the 3 m tunnel (props at y +-1.32)
    def tim(bm):
        for s in (-1, 1): cyl(bm, (0, s * 1.32, -0.05), (0.0, s * 1.27, 2.32), 0.13, 8, 0.08, rng)
        cyl(bm, (0, -1.6, 2.45), (0, 1.6, 2.45), 0.15, 8, 0.06, rng)
    def wedge(bm):
        for s in (-1, 1): box(bm, (0.0, s * 1.15, 2.62), (0.22, 0.4, 0.06))
    def spikes(bm):
        for s in (-1, 1):
            cyl(bm, (0.14, s * 1.27, 2.3), (-0.02, s * 1.27, 2.36), 0.012, 4); cyl(bm, (0.15, s * 0.9, 2.45), (-0.02, s * 0.9, 2.45), 0.012, 4)
            box(bm, (0.0, s * 1.29, 1.2), (0.3, 0.03, 0.05))                 # iron band
    kit.append(prop('SM_Mine_TimberSet', [('M_MineOak', tim), ('M_MineOak', wedge), ('M_MineIron', spikes)], 1.0))
    def sleepers(bm):
        for i in range(6): box(bm, (0.33 + i * 0.667, 0, 0.05), (0.18, 1.1, 0.1), rng.uniform(-0.04, 0.04))
    def rails(bm):
        for s in (-1, 1): box(bm, (2.0, s * 0.3, 0.14), (4.0, 0.05, 0.08)); box(bm, (2.0, s * 0.3, 0.11), (4.0, 0.1, 0.02))
    kit.append(prop('SM_Mine_Rail_4m', [('M_MineOak', sleepers), ('M_MineIron', rails)], 1.0))
    def tub(bm):
        box(bm, (0, 0, 0.45), (1.2, 0.8, 0.06))
        for s in (-1, 1): box(bm, (0, s * 0.39, 0.72), (1.2, 0.06, 0.55)); box(bm, (s * 0.61, 0, 0.72), (0.06, 0.8, 0.55))
    def irons(bm):
        for xx in (-0.45, 0.0, 0.45): box(bm, (xx, 0, 0.72), (0.07, 0.86, 0.57))
        for s in (-1, 1): box(bm, (s * 0.35, 0, 0.32), (0.06, 0.72, 0.06))  # axles
        for sx in (-1, 1):
            for sy in (-1, 1): cyl(bm, (sx * 0.35, sy * 0.3, 0.2), (sx * 0.35, sy * 0.36, 0.2), 0.2, 12)
    kit.append(prop('SM_Mine_Cart', [('M_MineOak', tub), ('M_MineIron', irons), ('M_MineOre', lambda bm: box(bm, (0, 0, 0.83), (0.9, 0.6, 0.18)))], 1.0, 0.008))
    def hook(bm): cyl(bm, (-0.18, 0, 0.55), (0, 0, 0.55), 0.012, 4); cyl(bm, (0, 0, 0.55), (0, 0, 0.36), 0.012, 4)
    def frame(bm):
        box(bm, (0, 0, 0.32), (0.16, 0.16, 0.02)); box(bm, (0, 0, 0.08), (0.18, 0.18, 0.03))
        for sx in (-1, 1):
            for sy in (-1, 1): box(bm, (sx * 0.075, sy * 0.075, 0.2), (0.015, 0.015, 0.24))
    def glass(bm): box(bm, (0, 0, 0.2), (0.13, 0.13, 0.22))
    kit.append(prop('SM_Mine_Lantern', [('M_MineIron', hook), ('M_MineIron', frame), ('M_MineGlow', glass)], 0.5))
    def planks(bm):
        for i in range(6): box(bm, (0, -0.5 + i * 0.2, 1.1), (0.06, 0.19, 2.2))
    def straps(bm):
        for zz in (0.35, 1.1, 1.85): box(bm, (0.04, 0, zz), (0.015, 1.18, 0.07))
        for zz in (0.35, 1.1, 1.85):
            for yy in (-0.45, -0.15, 0.15, 0.45): cyl(bm, (0.045, yy, zz), (0.06, yy, zz), 0.018, 6)
        cyl(bm, (0.05, 0.45, 1.0), (0.12, 0.45, 1.0), 0.03, 8)                # ring pull
    kit.append(prop('SM_Mine_Door', [('M_MineOak', planks), ('M_MineIron', straps)], 1.0, 0.006))
    def dframe(bm):
        for s in (-1, 1): cyl(bm, (0, s * 0.72, -0.05), (0, s * 0.71, 2.35), 0.12, 8, 0.07, rng)
        cyl(bm, (0, -0.95, 2.42), (0, 0.95, 2.42), 0.14, 8, 0.06, rng)
    kit.append(prop('SM_Mine_DoorFrame', [('M_MineOak', dframe)], 1.0))
    # ore vein face (slab for the chamber wall, faces +X) and the spoil heap
    vein = bpy.data.meshes.new('v'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=60, y_segments=50, size=1.0)
    for v in bm.verts:
        y, z = v.co.x * 1.6, (v.co.y + 1) * 1.3; v.co = Vector((0, y, z))
    me = vein; bm.to_mesh(me); bm.free(); o = link('SM_Mine_OreVein', me); apply_mod(o, 'SOLIDIFY', thickness=0.5, offset=-1)
    P = np.array([v.co for v in o.data.vertices]); front = P[:, 0] > -0.01
    edge = ss(0.0, 0.5, np.minimum(1.6 - np.abs(P[:, 1]), np.minimum(P[:, 2], 2.6 - P[:, 2])))
    P[:, 0] += np.where(front, (0.35 * fbm(P, 1.4, 3, 9) + 0.12 * (1 - np.abs(2 * fbm(P, 4, 3, 10) - 1))) * edge, 0)
    for v, p in zip(o.data.vertices, P): v.co = Vector(p)
    o.data.materials.append(mat('M_MineOre')); uvbox(o, 1.0); bpy.ops.object.shade_smooth(); kit.append(o)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=2.2, radius2=0.25, depth=1.4)
    me = bpy.data.meshes.new('s'); bm.to_mesh(me); bm.free(); o = link('SM_Mine_SpoilHeap', me); o.data.transform(Matrix.Translation((0, 0, 0.7)))
    apply_mod(o, 'SUBSURF', levels=3, render_levels=3)
    P = np.array([v.co for v in o.data.vertices]); P[:, 2] *= 0.75
    P += (0.12 * (fbm(P, 2.5, 3, 11)[:, None] - 0.5)) * (P[:, 2] > 0.02)[:, None] * np.array([1, 1, 1])
    P[:, 2] = np.maximum(P[:, 2], 0)
    for v, p in zip(o.data.vertices, P): v.co = Vector(p)
    apply_mod(o, 'DECIMATE', ratio=0.25); o.data.materials.append(mat('M_MineRock')); uvbox(o, 2.0); bpy.ops.object.shade_smooth(); kit.append(o)
    rep = []
    for o in kit:
        bm = bmesh.new(); bm.from_mesh(o.data); open_e = sum(1 for e in bm.edges if not e.is_manifold); bm.free()
        rep.append((o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), open_e))
    for r in rep: print('MESH %-28s tris %6d open edges %d' % r, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'mine.blend'))
