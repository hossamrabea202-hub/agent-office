# #455 fire pit logs, no overlaps (i5, 2026-11-03). Owner (Alien): "No woods over lapping each others (follow real life
# references)". The #451 teepee aimed 7 logs at one apex and extended them 5-18 % past it, so their tops ran THROUGH each other.
# Real campfire teepee (scout / bushcraft builds): the logs lean in and REST on each other near the top; a log may cross in front
# of its neighbour, but wood never passes through wood. The two split logs in the ember bed lie ON the ground, inside the ring.
#   blender -b --factory-startup -P campfire_logs455.py -- <out.fbx> [report.txt]
# Method: same log shape as #451 (14-sided, oval, bent, bark noise, saw-cut ends, bark / end-grain slots, cm units).
# Each log is its own object; a BVH overlap test (+3 mm safety skin) finds every pair that intersects and moves the later log
# (tip outward and up, or the bed log inward) 1 cm at a time until no pair overlaps. Gaps stay small, so the logs touch.
import bpy, bmesh, math, random, sys
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]; REP = argv[1] if len(argv) > 1 else None
random.seed(455)
bpy.ops.wm.read_factory_settings(use_empty=True)
bark = bpy.data.materials.new('M_AshenGate_FirewoodBark'); endm = bpy.data.materials.new('M_AshenGate_FirewoodEnd')
SEG, RINGS = 14, 8


def build(p):
    """bmesh of one log from its parameters (shape randomness is stored in p, so a rebuild is identical apart from base/tip)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    base, tip, radius = p['base'], p['tip'], p['r']
    axis = (tip - base).normalized(); length = (tip - base).length
    up = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    sx = axis.cross(up).normalized(); sy = axis.cross(sx).normalized()
    rings = []
    for i in range(RINGS + 1):
        t = i / RINGS; c = base + axis * (length * t) + sx * (p['bend'] * length * math.sin(math.pi * t))
        ring = []
        for j in range(SEG):
            a = 2 * math.pi * j / SEG
            n = noise.noise(p['seed'] + Vector((math.cos(a) * 1.5, math.sin(a) * 1.5, t * 6.0)))
            r = radius * (1 + 0.10 * n) * (1 - 0.06 * t)
            ring.append(bm.verts.new(c + sx * (math.cos(a) * r) + sy * (math.sin(a) * r * p['ov'])))
        rings.append(ring)
    circ = 2 * math.pi * radius
    for i in range(RINGS):
        for j in range(SEG):
            f = bm.faces.new([rings[i][j], rings[i][(j + 1) % SEG], rings[i + 1][(j + 1) % SEG], rings[i + 1][j]]); f.material_index = 0
            us = [j / SEG, (j + 1) / SEG, (j + 1) / SEG, j / SEG]; vs = [i / RINGS, i / RINGS, (i + 1) / RINGS, (i + 1) / RINGS]
            for l, u0, v0 in zip(f.loops, us, vs): l[uv].uv = (u0 * circ / 12.0, v0 * length / 12.0)
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(list(reversed(ring)) if flip else ring); f.material_index = 1
        cen = sum((v.co for v in ring), Vector()) / len(ring)
        for l in f.loops:
            d = l.vert.co - cen; l[uv].uv = (0.5 + d.dot(sx) / (radius * 2.4), 0.5 + d.dot(sy) / (radius * 2.4))
    bm.normal_update()
    return bm


def bvh(p, skin=0.3):
    bm = build(p)
    for v in bm.verts: v.co += v.normal * skin               # 3 mm safety skin: touching is fine, intersecting is not
    t = BVHTree.FromBMesh(bm); bm.free(); return t


logs = []
APEX = Vector((0, 0, 44))
for k in range(7):                                             # leaning logs: butts on a 24-30 cm ring, tops near the apex
    a = 2 * math.pi * k / 7 + random.uniform(-0.15, 0.15)
    rr = random.uniform(24, 30)
    base = Vector((math.cos(a) * rr, math.sin(a) * rr, random.uniform(2.5, 4.0)))
    tip = APEX + Vector((math.cos(a) * -4.0, math.sin(a) * -4.0, random.uniform(-4, 4)))   # tops lean just past the axis
    logs.append(dict(kind='lean', a=a, base=base, tip=tip, r=random.uniform(3.6, 5.4), ov=random.uniform(0.85, 1.0),
                     bend=random.uniform(-0.04, 0.04), seed=Vector((random.random() * 50, random.random() * 50, 0))))
for k in range(2):                                             # split logs lying in the ember bed, on the ground
    a = random.uniform(0, 2 * math.pi); r = random.uniform(3.2, 4.2)
    c = Vector((math.cos(a) * 9, math.sin(a) * 9, 2.5 + r)); d = Vector((math.cos(a + 1.4), math.sin(a + 1.4), 0.0))
    logs.append(dict(kind='bed', a=a, base=c - d * 15, tip=c + d * 15, r=r, ov=random.uniform(0.85, 1.0),
                     bend=random.uniform(-0.03, 0.03), seed=Vector((random.random() * 50, random.random() * 50, 0))))

moves = 0
for it in range(400):
    trees = [bvh(p) for p in logs]
    pairs = [(i, j) for i in range(len(logs)) for j in range(i + 1, len(logs)) if trees[i].overlap(trees[j])]
    if not pairs: break
    for i, j in pairs:
        q = logs[j]
        if q['kind'] == 'bed':                                 # bed log: away from what it hits, on the ground
            mid = (q['base'] + q['tip']) * 0.5
            if logs[i]['kind'] == 'bed':                       # the other bed log: slide sideways, apart
                o = (logs[i]['base'] + logs[i]['tip']) * 0.5; away = Vector((mid.x - o.x, mid.y - o.y, 0))
                away = away.normalized() if away.length > 1e-3 else Vector((1, 0, 0))
            else:                                              # a leaning log's butt: toward the centre
                away = Vector((-mid.x, -mid.y, 0)).normalized()
            q['base'] += away * 1.0; q['tip'] += away * 1.0
        else:                                                  # leaning log: tip 1 cm outward (its own side) and 0.5 cm up
            q['tip'] += Vector((math.cos(q['a']), math.sin(q['a']), 0)) * 1.0 + Vector((0, 0, 0.5))
        moves += 1
# settle: a leaning log must REST on another (or it would fall). Pull each tip back toward the axis in 2.5 mm steps
# while it stays clear of every other log (3 mm skin), so it ends touching its neighbour.
for i, p in enumerate(logs):
    if p['kind'] != 'lean': continue
    back = Vector((-math.cos(p['a']), -math.sin(p['a']), 0)) * 0.25
    for _ in range(80):
        p['tip'] += back
        ti = bvh(p)
        if any(ti.overlap(bvh(q)) for j, q in enumerate(logs) if j != i):
            p['tip'] -= back; break
trees = [bvh(p, 0.0) for p in logs]
left = [(i, j) for i in range(len(logs)) for j in range(i + 1, len(logs)) if trees[i].overlap(trees[j])]
# contact check: every leaning log should touch (within 1.5 cm) at least one neighbour, so nothing floats
def gap(i, j):
    bi = build(logs[i]); best = 1e9
    tj = trees[j]
    for v in list(bi.verts)[::3]:
        hit = tj.find_nearest(v.co)
        if hit[0] is not None: best = min(best, hit[3])
    bi.free(); return best
touch = []
for i, p in enumerate(logs):
    if p['kind'] != 'lean': continue
    touch.append(min(gap(i, j) for j in range(len(logs)) if j != i))
me = bpy.data.meshes.new('SM_FirePitLogs455'); ob = bpy.data.objects.new('SM_FirePitLogs455', me)
bpy.context.collection.objects.link(ob); me.materials.append(bark); me.materials.append(endm)
bm = bmesh.new()
for p in logs:
    b = build(p); tmp = bpy.data.meshes.new('t'); b.to_mesh(tmp); b.free(); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
bm.to_mesh(me); bm.free()
for poly in me.polygons: poly.use_smooth = poly.material_index == 0
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, global_scale=0.01, apply_unit_scale=True, mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z')
rep = 'CAMPFIRE455 iterations %d moves %d overlapping pairs left %d (%s) | leaning logs nearest-neighbour gap cm: %s | faces %d -> %s' % (
    it, moves, len(left), left, ', '.join('%.1f' % g for g in touch), len(me.polygons), OUT)
print(rep)
if REP: open(REP, 'w').write(rep + '\n')
