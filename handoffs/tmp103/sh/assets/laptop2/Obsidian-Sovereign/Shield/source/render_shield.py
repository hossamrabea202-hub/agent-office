# Quick look at a shield build or final: blender -b <file.blend> -P render_shield.py -- out_prefix [samples] [res] [mode]
# mode 'clay' = simple per-material preview colours; 'keep' = keep the file's materials (textured final).
import sys, math, bpy, mathutils
argv = sys.argv[sys.argv.index('--') + 1:]
prefix = argv[0]; samples = int(argv[1]) if len(argv) > 1 else 48; res = int(argv[2]) if len(argv) > 2 else 900
mode = argv[3] if len(argv) > 3 else 'clay'
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = t; prefs.get_devices()
            if any(d.type == t for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == t
                sc.cycles.device = 'GPU'; break
        except Exception: pass
except Exception: pass
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = float(__import__('os').environ.get('EXPOSURE', '-1.6'))
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.20, 0.21, 0.23, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.35
if mode == 'clay':
    col = {'Steel': (0.30, 0.31, 0.34, 0.35, 1.0), 'Gold': (0.95, 0.70, 0.30, 0.25, 1.0), 'Leather': (0.12, 0.06, 0.03, 0.6, 0.0),
           'Buckle': (0.6, 0.6, 0.62, 0.3, 1.0), 'Etch': (0.05, 0.05, 0.06, 0.6, 0.6)}
    for m in bpy.data.materials:
        k = m.name.split('.')[0]
        if k in col and m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
            b = m.node_tree.nodes['Principled BSDF']; c = col[k]
            b.inputs['Base Color'].default_value = (*c[:3], 1); b.inputs['Roughness'].default_value = c[3]; b.inputs['Metallic'].default_value = c[4]
TGT = mathutils.Vector((0.0, -0.03, 0.39))
def light(name, loc, energy, size, c=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = c
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = TGT + mathutils.Vector(loc)
    o.rotation_euler = (TGT - o.location).to_track_quat('-Z', 'Y').to_euler()
light("Key", (-1.4, -1.9, 1.5), 260, 1.6, (1.0, 0.95, 0.88)); light("Fill", (1.9, -1.0, 0.6), 70, 2.0, (0.8, 0.88, 1.0))
light("Rim", (0.8, 2.0, 1.5), 220, 1.2, (0.85, 0.9, 1.0)); light("Top", (0, 0, 2.2), 60, 1.6)
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -0.0005)); fl = bpy.context.object
fm = bpy.data.materials.new('Floor'); fm.use_nodes = True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.095, 0.1, 1); fl.data.materials.append(fm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 70
views = {'front34': (-30, 12, 2.6), 'front': (0, 4, 2.6), 'back34': (150, 14, 2.6), 'side': (-90, 6, 2.6)}
for name, (az, el, d) in views.items():
    a, e = math.radians(az - 90), math.radians(el)
    cam.location = (TGT.x + d * math.cos(e) * math.cos(a), TGT.y + d * math.cos(e) * math.sin(a), TGT.z + d * math.sin(e))
    cam.rotation_euler = (TGT - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'; bpy.ops.render.render(write_still=True); print('RENDERED', sc.render.filepath)
