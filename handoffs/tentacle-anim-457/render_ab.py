# #457 (i5): before/after video, old clip LEFT vs polished clip RIGHT, same camera, Workbench (light on the 2 GB GPU).
#   blender -b --factory-startup -P render_ab.py -- <old.fbx> <new.fbx> <out.mp4> [seconds=12]
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
OLD, NEW, OUT = argv[:3]
SECS = float(argv[3]) if len(argv) > 3 else 12.0
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for i, f in enumerate((OLD, NEW)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f, use_anim=True)
    new = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in new if o.type == 'ARMATURE')
    objs.append((root, new))
# measure and place side by side
import mathutils
def bbox(objs_):
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs_ if o.type == 'MESH' for c in o.bound_box]
    return mathutils.Vector([min(p[k] for p in pts) for k in range(3)]), mathutils.Vector([max(p[k] for p in pts) for k in range(3)])
lo, hi = bbox(objs[0][1]); size = hi - lo; H = size.z; W = max(size.x, size.y)
for k, ((root, new), dx) in enumerate(zip(objs, (-W * 0.8, W * 0.8))):   # parent each import to an empty and move that
    e = bpy.data.objects.new('off%d' % k, None); bpy.context.scene.collection.objects.link(e); e.location.x = dx
    e.rotation_euler.z = math.radians(float(__import__('os').environ.get('TURN', '55')))   # show the main bend plane
    tops = [o for o in new if o.parent is None]
    for o in tops: o.parent = e
    print('IMPORT', k, [(o.name, o.type) for o in new], 'tops', [o.name for o in tops])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.42, 0.16, 0.16)
sh.show_cavity = True; sh.show_shadows = True; sh.show_specular_highlight = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = int(SECS * 24); sc.frame_step = 1
cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
c = (lo + hi) / 2
cam.location = (c.x, c.y - max(H, W * 3) * 1.9, c.z + H * 0.15)
cam.rotation_euler = (math.radians(88), 0, 0)
cam_d.lens = 40
w = bpy.data.worlds.new('w'); sc.world = w
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'; sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
# labels
for txt, x in (('BEFORE', -W * 0.8), ('AFTER #457', W * 0.8)):
    cu = bpy.data.curves.new(txt, 'FONT'); cu.body = txt; cu.size = H * 0.06; cu.align_x = 'CENTER'
    t = bpy.data.objects.new(txt, cu); sc.collection.objects.link(t)
    t.location = (c.x + x, c.y - W, lo.z - H * 0.05); t.rotation_euler = (math.radians(90), 0, 0)
sc.render.filepath = OUT
if OUT.endswith('.png'):                                 # still check of the framing: one frame at SECS seconds
    sc.render.image_settings.file_format = 'PNG'; sc.frame_set(int(SECS * 24)); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print('VIDEO', OUT, 'H', round(H, 2), 'W', round(W, 2))
