# #301/#447 masonry stairs (i5, 2026-11-03). Blender 4.5 headless:
#   blender -b --factory-startup -P gen_stair_mason451.py -- <out dir> [N ...]        (default N = 13 20 31)
# Owner: build the stairs like the keep (real modelled stones, not a stone texture on boxes), the AAA way.
# Same footprint and pivot as the kit flight SM_Stair_W200_Solid_N<N> (UE: x 0..200, y 0..-30N, z 0..18N, rising to -Y),
# so it swaps in place on every placed flight (their per-actor scale stays).
#  - TREADS (slot 0 "Tread"): every step is 1-3 dressed blocks across the width (joint 0.6 cm, recessed), 18 cm high,
#    30 cm deep + 2.5 cm nosing over the step below; bevel 1.2 cm, front-top arris worn round (3.5 cm) and the tread top
#    dished up to 0.6 cm in the walking line; +-0.25 cm random set, so no two steps are machine-identical.
#  - SIDE WALLS + BACK (slot 1 "Wall"): coursed ashlar 36 cm courses, 40-95 cm stones, cut to the stair profile, long
#    and short quoins at the front corners; a 1 cm recessed core fills the inside.
#  - Vertex colour (i9's M_TunnelAshlarB contract): R = stone tone (random per stone), G = damp (high near the ground,
#    in the joints), B = cavity (bevels / joint edges).
#  - UV0: box projection per stone, 1 UV = 120 cm, random offset per stone (scan texture never repeats in step).
#  - UCX collision: one simple box per step (walk + NavMesh stay smooth, AAA practice), not per stone.
import bpy, bmesh, math, os, random, sys
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
OUT = A[0]; NS = [int(x) for x in A[1:]] or [13, 20, 31]
W, RUN, RISE, JOINT, NOSE = 200.0, 30.0, 18.0, 0.8, 2.5      # 0.8 cm joint; the 3 cm overlap behind keeps it closed
OVL = 3.0                                                    # each stone runs 3 cm into the stone behind / below it
UVS = 120.0


def mat(name):
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)


def add_block(bm, layers, x0, x1, y0, y1, z0, z1, slot, tone, worn=0.0, dish=0.0, damp_z=60.0):
    """one dressed stone (UE cm, y negative = up the stair), built + bevelled in its own bmesh, then appended to bm.
    Blender coords = (x, -y, z)."""
    j = JOINT / 2
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    sx, sy, sz = (x1 - x0) - JOINT, (y1 - y0) - JOINT, (z1 - z0) - JOINT
    for vt in b.verts:
        vt.co = Vector((cx + vt.co.x * sx, -cy + vt.co.y * sy, cz + vt.co.z * sz))      # translate + positive scale: no mirror, faces stay outward
    bmesh.ops.bevel(b, geom=list(b.edges), offset=min(1.8, 0.3 * min(sx, sy, sz)), segments=2, profile=0.5, affect='EDGES')
    bmesh.ops.recalc_face_normals(b, faces=list(b.faces))     # the (x, -y, z) mirror flips winding: point every face outward
    if worn or dish:
        for vt in b.verts:
            p = vt.co; uy = -p.y
            if worn and p.z > z1 - j - worn and uy > y1 - j - worn:          # front-top arris (front = y1 side, toward the bottom)
                d = min(1.0, (p.z - (z1 - j - worn)) / worn) * min(1.0, (uy - (y1 - j - worn)) / worn)
                vt.co.z -= d * worn * 0.30; vt.co.y += d * worn * 0.30   # pull back + down = worn round nosing
            if dish and p.z > z1 - j - 0.05:
                wx = math.exp(-((p.x - W * 0.5) / (W * 0.28)) ** 2); wy = math.exp(-((uy - (y0 + y1) / 2) / (RUN * 0.6)) ** 2)
                vt.co.z -= dish * wx * wy
    uvl = b.loops.layers.uv.new('UVMap'); cl = b.loops.layers.color.new('Col')
    ox, oy = random.random() * 5, random.random() * 5
    b.normal_update()
    for f in b.faces:
        f.material_index = slot
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i])); a, c = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            p = l.vert.co
            l[uvl].uv = (p[a] / UVS + ox, p[c] / UVS + oy)
            l[cl] = (tone, max(0.0, 1.0 - p.z / damp_z) * 0.8, 0.55 if abs(n[ax]) < 0.97 else 0.08, 1.0)
    tm = bpy.data.meshes.new('tmp'); b.to_mesh(tm); b.free()
    bm.from_mesh(tm); bpy.data.meshes.remove(tm)


def flight(n):
    me = bpy.data.meshes.new('SM_StairMason451_N%d' % n); ob = bpy.data.objects.new(me.name, me)
    bpy.context.collection.objects.link(ob); me.materials.append(mat('Tread')); me.materials.append(mat('Wall'))
    bm = bmesh.new(); uv = col = None
    random.seed(451 + n)
    # treads: step i spans UE y [-30(i+1), -30i] (+ nosing toward +y), z [18i, 18(i+1)]
    for i in range(n):
        y_lo, y_hi = -RUN * (i + 1), -RUN * i + (NOSE if i > 0 else 0.0)
        cuts = sorted(random.sample([40, 60, 80, 100, 120, 140, 160], random.choice([0, 1, 1, 2])))
        xs = [0.0] + [c + random.uniform(-8, 8) for c in cuts] + [W]
        dz = random.uniform(-0.25, 0.25)
        for a, b in zip(xs, xs[1:]):
            add_block(bm, (uv, col), a - (OVL if a > 0 else 0), b, y_lo - OVL, y_hi, RISE * i + dz - OVL, RISE * (i + 1) + dz, 0, random.uniform(0.25, 0.75),
                      worn=3.5, dish=0.6, damp_z=40.0)
    # side walls: coursed ashlar on both faces (12 cm thick facing), cut to the profile
    H = RISE * n; CH = 36.0
    for side, (sx0, sx1) in (('L', (-0.5, 11.5)), ('R', (W - 11.5, W + 0.5))):
        z = 0.0; k = 0
        while z < H - RISE + 0.1:
            z1 = min(z + CH, H - RISE)
            if z1 - z < 6: break
            # the course may only run where the step top above it is >= z1: step i top = 18(i+1) -> i >= z1/18 - 1
            i0 = max(0, int(math.ceil(z1 / RISE)) - 1)
            y_front = -RUN * i0                                   # front end of this course (toward the bottom of the stair)
            y = -RUN * n                                          # start at the back
            first = True
            while y < y_front - 0.1:
                L = random.uniform(40, 95) if not first else random.uniform(20, 50) if k % 2 else random.uniform(55, 80)
                y1 = min(y + L, y_front)
                if y_front - y1 < 18: y1 = y_front
                add_block(bm, (uv, col), sx0, sx1, y - (OVL if y > -RUN * n + 0.1 else 0), y1, z - (OVL if z > 0 else 0), z1, 1, random.uniform(0.2, 0.8))
                y = y1; first = False
            z = z1; k += 1
    # back face (top end): courses across the width
    z = 0.0; k = 0
    while z < H - RISE + 0.1:
        z1 = min(z + CH, H - RISE)
        if z1 - z < 6: break
        x = 11.5
        while x < W - 11.5 - 0.1:
            L = random.uniform(45, 90); x1 = min(x + L, W - 11.5)
            if W - 11.5 - x1 < 20: x1 = W - 11.5
            add_block(bm, (uv, col), x - (OVL if x > 11.6 else 0), x1, -RUN * n - 0.5, -RUN * n + 11.5, z - (OVL if z > 0 else 0), z1, 1, random.uniform(0.2, 0.8))
            x = x1
        z = z1; k += 1
    # recessed core (hidden filler so there is no see-through between facings): one stepped prism per step, 1 cm in
    for i in range(n - 1):
        add_block(bm, (uv, col), 11.0, W - 11.0, -RUN * n + 11.0, -RUN * i - 1.0, 0.0, RISE * i + 0.5, 1, 0.3)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    # UCX: one box per step (from the ground to the step top) = smooth walking + clean NavMesh
    for i in range(n):
        cm = bpy.data.meshes.new('UCX_%s_%02d' % (me.name, i)); co = bpy.data.objects.new(cm.name, cm)
        bpy.context.collection.objects.link(co)
        b2 = bmesh.new()
        bmesh.ops.create_cube(b2, size=1.0)
        for vt in b2.verts:
            vt.co.x = (vt.co.x + 0.5) * W
            vt.co.y = -(-(RUN * (i + 1)) + (vt.co.y + 0.5) * RUN)
            vt.co.z = (vt.co.z + 0.5) * RISE * (i + 1)
        b2.to_mesh(cm); b2.free(); co.parent = ob
    return ob


os.makedirs(OUT, exist_ok=True)
for n in NS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = flight(n)
    bpy.ops.object.select_all(action='SELECT')
    path = os.path.join(OUT, 'SM_StairMason451_N%d.fbx' % n)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, global_scale=0.01, apply_unit_scale=True, mesh_smooth_type='FACE',
                             axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True)
    print('MASON ok N=%d faces=%d -> %s' % (n, len(ob.data.polygons), path))
