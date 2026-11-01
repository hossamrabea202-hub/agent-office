# Quick clay preview (Workbench) for shape checks: blender -b <file.blend> -P preview.py -- <out.png> <view> [action] [frame]
# views: side | 34 | front | head | back
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out, view = a[0], a[1]
sc = bpy.context.scene
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if arm and len(a) > 2:
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[a[2]]
    if hasattr(arm.animation_data, 'action_slot') and arm.animation_data.action.slots: arm.animation_data.action_slot = arm.animation_data.action.slots[0]
    sc.frame_set(int(a[3]) if len(a) > 3 else 0)
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL' if '--mat' in sys.argv else 'SINGLE'; sh.single_color = (0.6, 0.55, 0.5)
sh.show_cavity = True; sh.show_shadows = True
cams = {'side': ((4.8, -0.2, 1.2), (0, -0.2, 1.0), 35), '34': ((3.4, -4.0, 2.0), (0, -0.3, 1.0), 35), 'front': ((0.0, -5.0, 1.5), (0, -0.5, 1.1), 40),
        'head': ((1.4, -2.3, 1.9), (0, -1.25, 1.65), 40), 'back': ((-2.6, 3.6, 1.8), (0, 0.3, 1.0), 35), 'left': ((-4.8, -0.2, 1.2), (0, -0.2, 1.0), 35)}
cl, tg, lens = cams[view]
cd = bpy.data.cameras.new('PC'); cam = bpy.data.objects.new('PC', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = Vector(cl); cd.lens = lens; cam.rotation_euler = (Vector(tg) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y = 1000, 700; sc.render.filepath = out
bpy.ops.render.render(write_still=True); print('PREVIEW', out)
