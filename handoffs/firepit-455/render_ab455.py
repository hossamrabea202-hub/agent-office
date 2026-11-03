# #455: old (#451) vs new (#455) fire pit logs side by side, Workbench, 3/4 view from above (where the overlaps showed).
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for k, (f, dx) in enumerate(((a[0], -0.45), (a[1], 0.45))):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=f)
    for o in set(bpy.data.objects) - before:
        if o.parent is None: o.location.x += dx
    for o in set(bpy.data.objects) - before:
        if o.type == 'MESH':
            for i, m in enumerate(o.data.materials): pass
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'RANDOM'; sh.show_cavity = True; sh.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 640
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -2.1, 1.25); cam.rotation_euler = (math.radians(66), 0, 0); cd.lens = 38
sc.render.filepath = a[2]; bpy.ops.render.render(write_still=True); print('AB', a[2])
