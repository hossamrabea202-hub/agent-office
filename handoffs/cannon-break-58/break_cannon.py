# #58 (checkking, 2026-10-30 night): three "break stage" meshes from any field-cannon FBX, automatically (Blender 4.5).
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
    wheels.sort(key=lambda w: w.location.x + w.location.y)
    mn, mx = ext(src); centre = (mn + mx) / 2
    if k == 1:
        if barrel: rot_about(barrel, 'Y', 4, barrel.location)
        if wheels: rot_about(wheels[0], 'X', 14, Vector((wheels[0].location.x, wheels[0].location.y, 0)))
        small = sorted(carriage, key=lambda p: (ext(p)[1] - ext(p)[0]).length)[:max(1, len(carriage) // 6)]
        for p in small: p.location += Vector((0.03, -0.02, -0.05)); rot_about(p, 'Z', random.uniform(-20, 20), p.location)
    if k == 2:
        if wheels:
            w = wheels[0]; w.location += Vector((0, -0.35 if w.location.y < centre.y else 0.35, 0)); rot_about(w, 'X', 88, w.location)
        lost_side = -1 if (wheels and wheels[0].location.y < centre.y) else 1
        for p in carriage + ([barrel] if barrel else []): rot_about(p, 'X', -9 * lost_side, Vector((centre.x, centre.y, 0)))
        if barrel: rot_about(barrel, 'Y', 12, barrel.location)
    if k == 3:
        for w in wheels:
            rot_about(w, 'X', 90, w.location); w.location += Vector((random.uniform(-0.3, 0.3), random.uniform(-0.6, 0.6), 0))
        if barrel:
            rot_about(barrel, 'Y', 6, barrel.location); rot_about(barrel, 'Z', 22, barrel.location)
        for p in carriage:
            p.location += Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), 0))
            rot_about(p, 'Z', random.uniform(-35, 35), p.location); rot_about(p, 'X', random.uniform(-25, 25), p.location)
    if k >= 2: ground(parts)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    o = bpy.context.object; o.name = '%s_Break%d' % (NAME, k)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')        # keep the source origin (cursor at world 0)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                             axis_forward='-Y', axis_up='Z', mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
    print('STAGE', k, o.name, 'wheels', len(wheels), 'barrel', bool(barrel), 'carriage parts', len(carriage))
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
