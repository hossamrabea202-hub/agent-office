# #450 preview: LEFT today's hit reaction (0.8 s squash/stretch of the root scale on the idle arm), RIGHT the new hit-react
# clip. Two hits, 3 s apart. Workbench (light on the 2 GB GPU).
#   blender -b -P render_react.py -- <idle.fbx> <react.fbx> <out.mp4|png> [still_second]
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]
IDLE, REACT, OUT = a[:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, 144
groups = []
for k, (f, dx) in enumerate(((IDLE, -60.0), (REACT, 60.0))):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=f, use_anim=True)
    new = [o for o in bpy.data.objects if o not in before]
    e = bpy.data.objects.new('g%d' % k, None); sc.collection.objects.link(e); e.location.x = dx; e.rotation_euler.z = math.radians(55)
    for o in new:
        if o.parent is None: o.parent = e
    groups.append((e, next(o for o in new if o.type == 'ARMATURE')))
# LEFT: the current reaction = root scale squash/stretch for 0.8 s at each hit (t = 0.5 s and 3.5 s)
e0 = groups[0][0]
for hit in (0.5, 3.5):
    for f, sz, sxy in ((0, 1.0, 1.0), (0.1, 0.85, 1.08), (0.3, 1.1, 0.95), (0.55, 0.96, 1.02), (0.8, 1.0, 1.0)):
        fr = int((hit + f) * 24) + 1; e0.scale = (sxy, sxy, sz); e0.keyframe_insert('scale', frame=fr)
# RIGHT: the react clip twice (hits at 0.5 s and 3.5 s); between hits the arm rests
arm = groups[1][1]; act = arm.animation_data.action; arm.animation_data.action = None
tr = arm.animation_data.nla_tracks.new()
for hit in (0.5, 3.5):
    s = tr.strips.new('hit%.1f' % hit, int(hit * 24) + 1, act); s.blend_in = 2
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -330, 60); cam.rotation_euler = (math.radians(90), 0, 0); cd.lens = 35
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
sh.single_color = (0.42, 0.16, 0.16); sh.show_cavity = True; sh.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 960, 540
for txt, x in (('NOW (scale wobble)', -60), ('NEW hit reaction #450', 60)):
    cu = bpy.data.curves.new(txt, 'FONT'); cu.body = txt; cu.size = 6; cu.align_x = 'CENTER'
    t = bpy.data.objects.new(txt, cu); sc.collection.objects.link(t); t.location = (x, -40, -12); t.rotation_euler = (math.radians(90), 0, 0)
sc.render.filepath = OUT
if OUT.endswith('.png'):
    sc.render.image_settings.file_format = 'PNG'; sc.frame_set(int(float(a[3]) * 24) + 1); bpy.ops.render.render(write_still=True)
else:
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    bpy.ops.render.render(animation=True)
print('PREVIEW', OUT)
