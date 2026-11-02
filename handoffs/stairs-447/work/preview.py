import bpy, math, sys
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=out + '/SM_Stair447_Courtyard34.blend')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (0.62, 0.58, 0.52)
sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
for o in sc.objects: o.hide_render = not o.name.endswith('_high')
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, pos, tgt, lens=35):
    cam.location = Vector(pos); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + '/preview_' + name + '.png'; bpy.ops.render.render(write_still=True)
shot('wide', (3.0, 5.5, 3.0), (5.5, -1.2, 3.0), 24)     # from the courtyard side (parapet side, Blender -y is courtyard? both shown)
shot('nosing', (4.4, -1.15, 3.4), (5.3, -1.15, 3.0), 40)
shot('under', (5.0, 3.0, 0.8), (5.0, -1.2, 2.8), 24)
for o in sc.objects: o.hide_render = not o.name.endswith('_low')
shot('low_wide', (3.0, 5.5, 3.0), (5.5, -1.2, 3.0), 24)
