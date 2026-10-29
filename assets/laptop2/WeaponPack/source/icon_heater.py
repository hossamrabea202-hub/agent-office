# Shop icon: blender -b Heater_final.blend -P icon_heater.py -- out.png      (transparent 512 px, 3/4 front, soft key light)
import bpy, sys, math, mathutils
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 128; sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = 1024; sc.render.resolution_percentage = 50
sc.render.film_transparent = True; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
s = sc.render.image_settings; s.file_format = 'PNG'; s.color_mode = 'RGBA'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.52, 0.56, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
def light(name, energy, loc, size):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (mathutils.Vector((0, 0.03, 0.42)) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
light('Key', 120, (-1.2, -1.6, 1.6), 1.2)
light('Fill', 30, (1.4, -1.2, 0.4), 1.5)
light('Rim', 80, (0.6, 1.4, 1.5), 0.8)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 85
import os
if os.environ.get('ICON') == 'sword':      # the sword lies along the icon's diagonal, point up-right
    p = mathutils.Vector((-0.35, -1.75, 0.22)); t = mathutils.Vector((0.0, 0.0, 0.205))
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.rotation_euler.rotate_axis('Z', math.radians(-45))
else:
    p = mathutils.Vector((-0.75, -2.45, 0.70)); t = mathutils.Vector((0.0, 0.03, 0.425))
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.rotation_euler.rotate_axis('Z', math.radians(-12))
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
print('ICON OK')
