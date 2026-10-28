# Preview renders of the open gauntlet .blend: blender -b <file>.blend -P render_clay.py -- out_prefix [samples] [res]
import sys, math
import bpy, mathutils
argv = sys.argv[sys.argv.index('--') + 1:]
prefix = argv[0]
samples = int(argv[1]) if len(argv) > 1 else 48
res = int(argv[2]) if len(argv) > 2 else 900
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('W') if not sc.world else sc.world
sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.20, 0.21, 0.23, 1); bg.inputs[1].default_value = 0.35
hide = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.endswith('_R')]
for o in hide: o.hide_render = True                    # frame the left hand only
TGT = mathutils.Vector((0.345, 0.0, 0.748))
def light(name, loc, energy, size, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = TGT + mathutils.Vector(loc)
    o.rotation_euler = (TGT - o.location).to_track_quat('-Z', 'Y').to_euler()
light('Key', (-0.5, -0.7, 0.4), 70, 0.5, (1.0, 0.95, 0.88))
light('Fill', (0.7, -0.3, 0.1), 20, 0.7, (0.8, 0.88, 1.0))
light('Rim', (0.3, 0.7, 0.5), 60, 0.4, (0.85, 0.9, 1.0))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 70
views = {'back': (0, 6, 0.55), 'back34': (-40, 15, 0.55), 'thumb': (-90, 8, 0.55), 'palm': (165, 10, 0.55)}
for name, (az, el, d) in views.items():
    a, e = math.radians(az - 90), math.radians(el)
    cam.location = (TGT.x + d * math.cos(e) * math.cos(a), TGT.y + d * math.cos(e) * math.sin(a), TGT.z + d * math.sin(e))
    cam.rotation_euler = (TGT - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath)
