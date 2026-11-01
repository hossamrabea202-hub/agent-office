# #58 i5 copy (2026-11-01): wheels are grouped per side and laid flat about the axis perpendicular to the AXLE (the
# axle is detected, it runs along X on SM_FieldCannon_HD; the original assumed Y, so its wheels only spun in their plane).
# Original: #58 (checkking, 2026-10-30 night): three "break stage" meshes from any field-cannon FBX, automatically (Blender 4.5).
#   blender -b --factory-startup -P break_cannon.py -- <cannon.fbx> <out_dir> [Name=SM_FieldCannon_HD]
# Writes <out_dir>/<Name>_Break1.fbx, _Break2.fbx, _Break3.fbx (same material slots and UVs as the source, so the cannon's
# materials just work) + renders/break_stages.png (source and the 3 stages side by side).
# Method (no Fracture Mode needed): the mesh is split into loose parts and the parts are classified by shape:
#   wheels  = flat-ish parts whose two largest extents are similar and much bigger than the third (discs),
#   barrel  = the longest part,
#   carriage = everything else. Then each stage moves / tilts / drops parts like a hit from above and in front:
#   Break1  dented barrel (slight bend), one wheel cracked and leaning 14 deg, carriage edge chipped (a corner part dropped)
#   Break2  one wheel off and lying flat beside it, carriage tilted 9 deg toward the lost wheel, barrel tilted down 12 deg
#   Break3  barrel on the ground, both wheels flat, carriage parts spread 20-40 cm and rotated, everything grounded
# All stages keep z >= 0 (sit on the ground plane) and the source origin, so the BP swaps meshes in place.
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = os.path.abspath(a[0]), os.path.abspath(a[1])
NAME = a[2] if len(a) > 2 else os.path.splitext(os.path.basename(SRC))[0]
os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)
random.seed(58)

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
src = bpy.context.object
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
src.name = NAME

def ext(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    return mn, mx

def split(obj):
    """duplicate obj and separate it into loose parts; returns the part objects"""
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate(); d = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    parts = [o for o in bpy.context.selected_objects]
    for p in parts:
        bpy.context.view_layer.objects.active = p; bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    return parts

def classify(parts):
    info = []
    for p in parts:
        mn, mx = ext(p); e = sorted([mx.x - mn.x, mx.y - mn.y, mx.z - mn.z])
        info.append((p, e, (mx - mn).length))
    big = max(info, key=lambda t: t[2])[2]
    wheels = [p for p, e, d in info if d > 0.15 * big and e[1] > 0.7 * e[2] and e[0] < 0.45 * e[2]]
    rest = [t for t in info if t[0] not in wheels]
    barrel = max(rest, key=lambda t: t[1][2])[0] if rest else None
    carriage = [p for p, e, d in info if p not in wheels and p is not barrel]
    return wheels, barrel, carriage

def rot_about(p, axis, deg, pivot):
    m = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-pivot)
    p.matrix_world = m @ p.matrix_world

def ground(parts):
    """drop every part so its lowest point rests on z = 0 (never below)"""
    for p in parts:
        mn, mx = ext(p)
        if mn.z < 0 or True: p.location.z -= mn.z

def stage(k):
    parts = split(src)
    wheels, barrel, carriage = classify(parts)
    mn, mx = ext(src); centre = (mn + mx) / 2
    # axle axis = the thin axis of the wheel discs; h = the horizontal axis across it (wheels lie flat by turning about h)
    if wheels:
        wmn, wmx = ext(max(wheels, key=lambda p: (ext(p)[1] - ext(p)[0]).length)); d = wmx - wmn
        ax = min(range(2), key=lambda i: d[i])
    else: ax = 1
    AX, H = ('X', 'Y') if ax == 0 else ('Y', 'X')
    out = lambda side: Vector((side, 0, 0)) if ax == 0 else Vector((0, side, 0))
    groups = {}
    for w in wheels: groups.setdefault(1 if w.location[ax] > centre[ax] else -1, []).append(w)
    def gpivot(g):
        mns = [ext(p)[0] for p in g]; mxs = [ext(p)[1] for p in g]
        c = (Vector((min(v.x for v in mns), min(v.y for v in mns), 0)) + Vector((max(v.x for v in mxs), max(v.y for v in mxs), 0))) / 2
        return c
    def turn(g, deg, pivot=None):
        pv = pivot or gpivot(g)
        for p in g: rot_about(p, H, deg, pv)
    def move(g, v):
        for p in g: p.location += v
    # loose spoke/felloe pieces the shape test missed: anything lying inside a wheel's slab (along the axle) joins it
    for sd, g in groups.items():
        lo = min(ext(q)[0][ax] for q in g) - 0.03; hi = max(ext(q)[1][ax] for q in g) + 0.03
        for q in list(carriage):
            qmn, qmx = ext(q)
            if qmn[ax] >= lo and qmx[ax] <= hi: g.append(q); carriage.remove(q)
    sides = sorted(groups)
    lost = sides[0] if sides else -1
    if k == 1:
        if barrel: rot_about(barrel, H, 4, barrel.location)
        if sides: turn(groups[lost], 10 * lost)
        small = sorted(carriage, key=lambda p: (ext(p)[1] - ext(p)[0]).length)[:max(1, len(carriage) // 6)]
        for p in small: p.location += Vector((0.03, -0.02, -0.05)); rot_about(p, 'Z', random.uniform(-20, 20), p.location)
    if k == 2:
        if sides:
            g = groups[lost]; move(g, out(lost) * 0.45); turn(g, 88 * lost)
        for p in carriage + ([barrel] if barrel else []): rot_about(p, H, -9 * lost, Vector((centre.x, centre.y, 0)))
        if barrel: rot_about(barrel, AX, 12, barrel.location)
    if k == 3:
        for sd in sides:
            g = groups[sd]; move(g, out(sd) * random.uniform(0.4, 0.8) + Vector((random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0)) * 0.5)
            turn(g, 90 * sd)
            for p in g: rot_about(p, 'Z', random.uniform(-8, 8), gpivot(g))
        if barrel:
            rot_about(barrel, H, 6, barrel.location); rot_about(barrel, 'Z', 22, barrel.location)
        for p in carriage:
            p.location += Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), 0))
            rot_about(p, 'Z', random.uniform(-35, 35), p.location); rot_about(p, AX, random.uniform(-25, 25), p.location)
    if k >= 2: ground(parts)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    o = bpy.context.object; o.name = '%s_Break%d' % (NAME, k)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')        # keep the source origin (cursor at world 0)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                             axis_forward='-Y', axis_up='Z', mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
    print('STAGE', k, o.name, 'wheel groups', {k_: len(v) for k_, v in groups.items()}, 'axle', AX, 'barrel', bool(barrel), 'carriage parts', len(carriage))
    return o

bpy.context.scene.cursor.location = (0, 0, 0)
stages = [stage(k) for k in (1, 2, 3)]

# preview: source + 3 stages in a row
mn, mx = ext(src); w = (mx.x - mn.x) * 1.4 + 0.5
for i, o in enumerate([src] + stages): o.location.x += i * w
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 600
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 4 * w * 1.05
cam.location = (1.5 * w + (mn.x + mx.x) / 2, -10, (mx.z) / 2 + 2.5); cam.rotation_euler = (math.radians(75), 0, 0)
for nm, loc, en in (('Key', (-3, -6, 6), 1500), ('Rim', (4, 5, 3), 900)):
    l = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'AREA')); l.data.energy = en; l.data.size = 4; l.location = (loc[0] + 1.5 * w, loc[1], loc[2])
    l.rotation_euler = (Vector((1.5 * w, 0, 0)) - l.location).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(l)
bpy.ops.mesh.primitive_plane_add(size=60, location=(1.5 * w, 0, 0))
sc.view_settings.view_transform = 'AgX'
sc.render.filepath = os.path.join(OUT, 'renders', 'break_stages.png'); bpy.ops.render.render(write_still=True)
print('BREAK DONE', NAME)
