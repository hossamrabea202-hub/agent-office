# Render 3 views of whatever .blend is open: blender -b chest_build_r1.blend -P render_clay.py -- out_prefix [samples] [res]
import sys, os, math
import bpy, mathutils
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
prefix = argv[0] if argv else os.path.join(os.path.dirname(bpy.data.filepath), 'clay')
samples = int(argv[1]) if len(argv) > 1 else 48
res = int(argv[2]) if len(argv) > 2 else 900
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = samples
sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = t; prefs.get_devices()
            if any(d.type == t for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == t
                sc.cycles.device = 'GPU'; print('GPU', t); break
        except Exception: pass
except Exception as e: print('no gpu', e)
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('W') if not sc.world else sc.world
sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.20, 0.21, 0.23, 1); bg.inputs[1].default_value = 0.35

def light(name, loc, energy, size, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    d = mathutils.Vector((0, 0, 0.26)) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
light('Key', (-0.9, -1.1, 0.9), 220, 0.9, (1.0, 0.95, 0.88))
light('Fill', (1.1, -0.6, 0.4), 60, 1.2, (0.8, 0.88, 1.0))
light('Rim', (0.4, 1.2, 1.0), 180, 0.6, (0.85, 0.9, 1.0))
light('Top', (0, 0, 1.4), 60, 1.0)

# floor
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.03))
fl = bpy.context.object; fm = bpy.data.materials.new('Floor'); fm.use_nodes = True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.095, 0.1, 1)
fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
fl.data.materials.append(fm)

cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 70
views = {'front34': (-30, 8, 1.55, (0, 0, 0.24)), 'side': (-90, 5, 1.55, (0, 0, 0.24)), 'back34': (150, 10, 1.55, (0, 0, 0.24))}
if len(argv) > 3 and argv[3] == 'close':
    views['close'] = (-18, 6, 0.62, (0.02, -0.12, 0.34))
for name, (az, el, d, tgt) in views.items():
    a, e = math.radians(az - 90), math.radians(el)
    tgt = mathutils.Vector(tgt)
    cam.location = (tgt.x + d * math.cos(e) * math.cos(a), tgt.y + d * math.cos(e) * math.sin(a), tgt.z + d * math.sin(e))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath)
