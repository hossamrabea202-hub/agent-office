# Quick clay + silhouette check of the wasp v2 (#338). blender -b wasp338_rig.blend -P clay338.py   env VIEW, SIL=1, OUT
import bpy, math, os
from mathutils import Vector
sc = bpy.context.scene; D = os.environ['WORK']
VIEW = os.environ.get('VIEW', '34'); SIL = os.environ.get('SIL') == '1'
m = bpy.data.materials.new('clay'); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
p.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1) if SIL else (0.35, 0.33, 0.30, 1); p.inputs['Roughness'].default_value = 0.6
for o in sc.objects:
    if o.type == 'MESH':
        if o.name == 'SK_RealmWasp_WingBlur': o.hide_render = True
        o.data.materials.clear(); o.data.materials.append(m)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1) if SIL else (0.6, 0.65, 0.75, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
if not SIL:
    sd = bpy.data.lights.new('S', 'SUN'); sd.energy = 4; s = bpy.data.objects.new('S', sd); sc.collection.objects.link(s); s.rotation_euler = (math.radians(50), 0, math.radians(30))
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cams = {'34': ((-2.6, -3.2, 2.0), 38), 'side': ((4.2, 0.05, 1.25), 40), 'front': ((0.0, -4.0, 1.3), 40), 'below': ((0.3, -0.6, -2.6), 32),
        'top': ((0.0, 0.0, 5.0), 34), 'close': ((-0.95, -1.5, 1.6), 50)}
cam.location, cd.lens = cams[VIEW]; tgt = Vector((0, 0.05, 1.15)) if VIEW != 'close' else Vector((0, -0.45, 1.3))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y' if VIEW != 'top' else 'Y').to_euler()
if VIEW == 'top': cam.rotation_euler = (0, 0, 0)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'
pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = True
sc.cycles.samples = 24; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 900, 640; sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
sc.render.filepath = os.path.join(D, os.environ.get('OUT', f'clay_{VIEW}{"_sil" if SIL else ""}.png')); bpy.ops.render.render(write_still=True)
print('CLAY OK', sc.render.filepath, flush=True)
