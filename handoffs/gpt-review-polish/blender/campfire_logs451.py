# #451 campfire logs (i5, 2026-11-03). Blender 4.5 headless:
#   blender -b --factory-startup -P campfire_logs451.py -- <out.fbx>
# A teepee of 7 hand-split firewood logs (real campfire build: logs lean on each other over the ember bed, butts spread on
# the ground). Each log: 14-sided cylinder 45-62 cm long, 7-11 cm across, slightly oval and bent, bark noise on the side,
# angled saw cuts at both ends. Material slot 0 = bark (side), slot 1 = end grain (caps), to match the project's
# M_AshenGate_FirewoodBark / M_AshenGate_FirewoodEnd. UVs: side = cylindrical (U around, V along, 1 unit = 12 cm), caps =
# planar. Built in cm-sized Blender units, exported with global_scale 0.01 so UE gets real cm. Pivot at the pit centre, on the ground.
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix, noise
out = sys.argv[sys.argv.index('--') + 1]
random.seed(451)
bpy.ops.wm.read_factory_settings(use_empty=True)
bark = bpy.data.materials.new('M_AshenGate_FirewoodBark'); end = bpy.data.materials.new('M_AshenGate_FirewoodEnd')
me = bpy.data.meshes.new('SM_FirePitLogs451'); ob = bpy.data.objects.new('SM_FirePitLogs451', me)
bpy.context.collection.objects.link(ob); me.materials.append(bark); me.materials.append(end)
bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
SEG, RINGS = 14, 8


def log(length, radius, base, tip):
    """one log from base (on the ground) leaning to tip; returns nothing (adds to bm)."""
    axis = (tip - base).normalized(); length = (tip - base).length
    up = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    sx = axis.cross(up).normalized(); sy = axis.cross(sx).normalized()
    ov = random.uniform(0.85, 1.0); bend = random.uniform(-0.04, 0.04) * length; seed = Vector((random.random() * 50, random.random() * 50, 0))
    rings = []
    for i in range(RINGS + 1):
        t = i / RINGS; c = base + axis * (length * t) + sx * (bend * math.sin(math.pi * t))
        ring = []
        for j in range(SEG):
            a = 2 * math.pi * j / SEG
            n = noise.noise(seed + Vector((math.cos(a) * 1.5, math.sin(a) * 1.5, t * 6.0)))
            r = radius * (1 + 0.10 * n) * (1 - 0.06 * t)
            ring.append(bm.verts.new(c + sx * (math.cos(a) * r) + sy * (math.sin(a) * r * ov)))
        rings.append(ring)
    circ = 2 * math.pi * radius
    for i in range(RINGS):
        for j in range(SEG):
            q = [rings[i][j], rings[i][(j + 1) % SEG], rings[i + 1][(j + 1) % SEG], rings[i + 1][j]]
            f = bm.faces.new(q); f.material_index = 0
            us = [j / SEG, (j + 1) / SEG, (j + 1) / SEG, j / SEG]; vs = [i / RINGS, i / RINGS, (i + 1) / RINGS, (i + 1) / RINGS]
            for l, u0, v0 in zip(f.loops, us, vs): l[uv].uv = (u0 * circ / 12.0, v0 * length / 12.0)
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(list(reversed(ring)) if flip else ring); f.material_index = 1
        cen = sum((v.co for v in ring), Vector()) / len(ring)
        for l in f.loops:
            d = l.vert.co - cen; l[uv].uv = (0.5 + d.dot(sx) / (radius * 2.4), 0.5 + d.dot(sy) / (radius * 2.4))


tip = Vector((0, 0, 46))
for k in range(7):
    a = 2 * math.pi * k / 7 + random.uniform(-0.15, 0.15)
    rr = random.uniform(24, 30)
    base = Vector((math.cos(a) * rr, math.sin(a) * rr, random.uniform(2.5, 4.0)))
    t = tip + Vector((random.uniform(-4, 4), random.uniform(-4, 4), random.uniform(-6, 4)))
    t = base + (t - base) * random.uniform(1.05, 1.18)                      # logs cross a little past the apex
    log(None, random.uniform(3.6, 5.4), base, t)
# two short split logs lying in the ember bed
for k in range(2):
    a = random.uniform(0, 2 * math.pi); c = Vector((math.cos(a) * 10, math.sin(a) * 10, 3.0)); d = Vector((math.cos(a + 1.4), math.sin(a + 1.4), 0.05))
    log(None, random.uniform(3.2, 4.2), c - d * 17, c + d * 17)
bm.normal_update(); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = p.material_index == 0
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, global_scale=0.01, apply_unit_scale=True, mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z')
print('CAMPFIRE ok', len(me.polygons), 'faces ->', out)
