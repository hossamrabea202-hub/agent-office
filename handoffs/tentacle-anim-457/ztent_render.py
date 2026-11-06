# blender -b --factory-startup -P ztent_render.py -- <clip.fbx with mesh> <out dir> <name> <"s1,s2,..." seconds | mp4> [idle.fbx]
# Renders the tentacle clip (left: the idle clip on the mesh if given, right: the new clip). Workbench, camera 250 m back.
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
CLIP, OUT, NAME, FR = a[:4]; IDLE = a[4] if len(a) > 4 else None
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24

def load(fbx, dx, label):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=fbx, use_anim=True)
    new = [o for o in bpy.data.objects if o not in before]
    e = bpy.data.objects.new(label, None); sc.collection.objects.link(e); e.location.x = dx; e.rotation_euler.z = math.radians(55)
    for o in new:
        if o.parent is None: o.parent = e
        if o.type == 'MESH':
            for s in o.material_slots:
                if s.material: s.material.diffuse_color = (0.42, 0.16, 0.16, 1)
    arm = next((o for o in new if o.type == 'ARMATURE'), None)
    return arm

arms = []
if IDLE:
    # the idle: UE clip export (armature only) -> needs the mesh: use the clip file's mesh by loading the clip, then swap its action
    ai = load(CLIP, -60.0, 'idle'); ai_act = ai.animation_data.action
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=IDLE, use_anim=True)
    src = next(o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE')
    ai.animation_data.action = src.animation_data.action
    for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)
    arms.append(ai)
ar = load(CLIP, 60.0 if IDLE else 0.0, 'react'); arms.append(ar)
act = ar.animation_data.action; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
sc.frame_start, sc.frame_end = f0, f1
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -330, 60); cam.rotation_euler = (math.radians(90), 0, 0); cd.lens = 35
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
for txt, x in ((('IDLE (today: no body reaction to a cannonball)', -60),) if IDLE else ()) + ((NAME, 60 if IDLE else 0),):
    cu = bpy.data.curves.new(txt, 'FONT'); cu.body = txt; cu.size = 5; cu.align_x = 'CENTER'
    t = bpy.data.objects.new(txt, cu); sc.collection.objects.link(t); t.location = (x, -40, -14); t.rotation_euler = (math.radians(90), 0, 0)
if FR == 'mp4':
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.filepath = os.path.join(OUT, NAME + '.mp4'); bpy.ops.render.render(animation=True)
else:
    for s in [float(x) for x in FR.split(',')]:
        sc.frame_set(f0 + int(s * 24)); sc.render.filepath = os.path.join(OUT, '%s_%03.1fs.png' % (NAME, s))
        sc.render.image_settings.file_format = 'PNG'; bpy.ops.render.render(write_still=True)
print('TRENDER OK', NAME, f0, f1)
