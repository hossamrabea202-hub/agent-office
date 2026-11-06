# #539 lookdev: blender -b --factory-startup -P lookdev.py -- <sporebase.blend|-> <tentacle mesh.fbx> <idle clip.fbx> <out dir> <name> <far|near|top>
# Cycles, one low sun (key) plus a dim overcast sky, locked exposure, grey ball (albedo 0.18) in shot. Without the blend: the tentacle alone (the "before").
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; BL, MESH, CLIP, OUT, NAME, VIEW = a[:6]; os.makedirs(OUT, exist_ok=True)
if BL != '-': bpy.ops.wm.open_mainfile(filepath=BL)
else: bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
base = next((o for o in bpy.data.objects if o.type == 'MESH'), None)
if base:
    base.scale = (0.01, 0.01, 0.01); m = bpy.data.materials.new('base'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'Col'; nt.links.new(at.outputs['Color'], b.inputs['Base Color']); nt.links.new(at.outputs['Alpha'], b.inputs['Roughness']); base.data.materials.append(m)
before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=MESH, use_anim=False)
new = [o for o in bpy.data.objects if o not in before]; ar = next(o for o in new if o.type == 'ARMATURE'); tm = next(o for o in new if o.type == 'MESH')
S, SINK = 2.7, 15.0     # placed scale; rig metres below the ground. Trunk radius there is about 10 rig m = 27 m; the base is nominal 30 m
for o in new:
    if o.parent is None: o.scale = (S * 0.01, S * 0.01, S * 0.01); o.location = (1.5, -1.0, -SINK * S)
for s in tm.material_slots:
    if s.material: s.material.use_nodes = True; s.material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (0.13, 0.035, 0.04, 1); s.material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.42
if not tm.material_slots:
    m2 = bpy.data.materials.new('t'); m2.use_nodes = True; m2.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.13, 0.035, 0.04, 1); tm.data.materials.append(m2)
# ground out to the horizon, soil albedo
bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, -0.35)); g = bpy.context.object; gm = bpy.data.materials.new('g'); gm.use_nodes = True; gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.075, 0.062, 0.045, 1); gb.inputs['Roughness'].default_value = 0.95; g.data.materials.append(gm)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(-60, -86, 1.2)); ball = bpy.context.object; bm = bpy.data.materials.new('b'); bm.use_nodes = True; bm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1); bm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6; ball.data.materials.append(bm); bpy.ops.object.shade_smooth()
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.2; sd.angle = math.radians(2); so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so); so.rotation_euler = (math.radians(68), 0, math.radians(38))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.52, 0.56, 0.62, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.42
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
VW = {'far': ((-120, -230, 42), (0, 0, 60), 35), 'near': ((-55, -82, 4.0), (-8, -34, 9), 28), 'top': ((-70, -160, 120), (0, 0, 2), 38)}[VIEW]
cam.location = VW[0]; cam.rotation_euler = (Vector(VW[1]) - Vector(VW[0])).to_track_quat('-Z', 'Y').to_euler(); cd.lens = VW[2]
if VIEW == 'near': ball.location = (-46, -70, 1.0)
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SPP', '48')); sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0
sc.render.filepath = os.path.join(OUT, NAME + '.png'); sc.render.image_settings.file_format = 'PNG'; bpy.ops.render.render(write_still=True); print('LOOK OK', sc.render.filepath)
