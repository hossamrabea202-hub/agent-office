# quick look render: blender -b X.blend -P clay.py -- out_prefix [textured]
import bpy, sys, math, mathutils, os
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; textured = len(args) > 1 and args[1] == 'tex'
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '48')); sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get('RW', '1400')), int(os.environ.get('RH', '1000'))
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '0'))
if textured:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if '__file__' in dir() else None
    sys.path.insert(0, os.environ['KITDIR']); import woodmat; woodmat.build_all()
keep = len(args) > 1 and args[1] == 'keep'
if not textured and not keep:
    cols = {'Bark': (0.10, 0.07, 0.05), 'WoodCut': (0.45, 0.33, 0.20), 'Rope': (0.40, 0.32, 0.20)}
    for m in bpy.data.materials:
        m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF') or m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        b.inputs['Base Color'].default_value = (*cols.get(m.name.split('.')[0], (0.5, 0.5, 0.5)), 1); b.inputs['Roughness'].default_value = 0.8
        o = m.node_tree.nodes.get('Material Output') or m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(b.outputs[0], o.inputs[0])
# ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
g = bpy.context.object; gm = bpy.data.materials.new('G'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.06, 0.06, 0.05, 1); g.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(-35)); sun.data.angle = math.radians(3)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 40
views = {'front34': ((-4.6, -6.2, 2.3), (0, 0, 1.4)), 'back34': ((4.8, 6.0, 2.4), (0, 0, 1.3)), 'tips': ((-1.0, -1.9, 3.3), (0.1, 0, 2.95)), 'base': ((-0.9, -2.0, 0.9), (0.2, 0, 0.5)), 'lash': ((1.4, 1.9, 2.4), (0.4, 0.3, 2.1))}
for k, (p, t) in views.items():
    if os.environ.get('VIEWS') and k not in os.environ['VIEWS'].split(','): continue
    cam.location = p; d = mathutils.Vector(t) - mathutils.Vector(p); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + '_' + k + '.png'; bpy.ops.render.render(write_still=True)
print('RENDER OK')
