# Blender: before/after of one clip on the REAL brute mesh (local preview only; the licensed mesh never leaves ckw/).
# blender -b -P render_mesh.py -- <SK.fbx> <before.fbx> <after.fbx> <out_dir> <clip> <frames "a,b,c" | "mp4"> [view: front|side|threeq]
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--')+1:]
SK, BEFORE, AFTER, OUT, CLIP, FR = a[:6]; VIEW = a[6] if len(a) > 6 else 'threeq'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def bl_fcurves(act):
    try: return list(act.fcurves)
    except Exception: return [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]

def load(anim, x, label):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=SK, automatic_bone_orientation=False, ignore_leaf_bones=False)
    new = [o for o in bpy.data.objects if o not in before]; arm = [o for o in new if o.type == 'ARMATURE'][0]
    b2 = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=anim, automatic_bone_orientation=False, ignore_leaf_bones=False)
    new2 = [o for o in bpy.data.objects if o not in b2]; src = [o for o in new2 if o.type == 'ARMATURE'][0]
    act = src.animation_data.action
    def strip(fcs):
        for fc in [fc for fc in fcs if fc.data_path in ('location', 'rotation_euler', 'rotation_quaternion', 'scale')]:
            fcs.remove(fc)
    try:
        strip(act.fcurves)
    except Exception:
        for layer in act.layers:
            for strip_ in layer.strips:
                for cb in strip_.channelbags: strip(cb.fcurves)
    arm.animation_data_create(); arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and src.animation_data.action_slot:
        arm.animation_data.action_slot = src.animation_data.action_slot
    for o in new2: bpy.data.objects.remove(o, do_unlink=True)
    e = bpy.data.objects.new('off_' + label, None); sc.collection.objects.link(e); e.location.x = x
    for o in new:
        if o.parent is None: o.parent = e
        if o.type == 'MESH':
            for s in o.material_slots:
                if s.material: s.material.diffuse_color = (0.58, 0.43, 0.38, 1)
    return arm, act

ab, act = load(BEFORE, 0.0, 'before'); aa, act2 = load(AFTER, 2.2, 'after')
f0 = int(act.frame_range[0]); f1 = max(int(act.frame_range[1]), int(act2.frame_range[1]))
for ob, ac in ((ab, act), (aa, act2)):
    ob.animation_data.action.use_cyclic = True if hasattr(ob.animation_data.action, 'use_cyclic') else None
    try:
        for fc in bl_fcurves(ac):
            if not any(m.type == 'CYCLES' for m in fc.modifiers): fc.modifiers.new('CYCLES')
    except Exception as e: print('cyc', e)
sc.frame_start, sc.frame_end = f0, f1; sc.render.fps = 30
SOUTH = VIEW.endswith('S'); ty = 0.6 if SOUTH else -0.6; rz = 0 if SOUTH else math.radians(180); dx = -0.6 if SOUTH else 0.6
for txt, x in ((os.environ.get('LABEL_BEFORE', 'BEFORE'), 0.0), (os.environ.get('LABEL_AFTER', 'AFTER  #449 creature layer'), 2.2)):
    bpy.ops.object.text_add(location=(x+dx*(-1 if SOUTH else 1)-0.0, ty, 2.45)); t = bpy.context.object; t.data.body = txt; t.data.size = 0.15
    t.rotation_euler = (math.radians(90), 0, rz)
bpy.ops.object.text_add(location=(-0.6 if SOUTH else 0.6, ty, 2.65)); t = bpy.context.object; t.data.body = CLIP; t.data.size = 0.11; t.rotation_euler = (math.radians(90), 0, rz)
bpy.ops.mesh.primitive_plane_add(size=14, location=(1.1, 0, 0))
# camera: the brute faces -Y in this import; frame both
sc.frame_set(f0)
c = Vector((1.1, 0, 1.75 if VIEW.startswith('face') else 1.2))
off = {'front': Vector((0, 6.2, 0.35)), 'side': Vector((6.5, 0.0, 0.3)), 'threeq': Vector((-2.2, 5.8, 0.5)), 'face': Vector((-1.6, 4.4, 0.25)), 'faceS': Vector((0.0, -4.8, 0.15)), 'sideq': Vector((5.0, -4.2, 0.3)), 'frontS': Vector((0.4, -6.6, 0.35))}[VIEW]
bpy.ops.object.camera_add(location=c+off); cam = bpy.context.object; sc.camera = cam
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50 if VIEW.startswith('face') else 35
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_shadows = True; sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
if FR == 'mp4':
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    sc.render.filepath = os.path.join(OUT, CLIP + '_before_after.mp4'); bpy.ops.render.render(animation=True)
else:
    for f in [int(x) for x in FR.split(',')]:
        sc.frame_set(f0+f); sc.render.filepath = os.path.join(OUT, '%s_%s_%03d.png' % (CLIP, VIEW, f))
        sc.render.image_settings.file_format = 'PNG'; bpy.ops.render.render(write_still=True)
print('RENDER OK', CLIP, f0, f1)
