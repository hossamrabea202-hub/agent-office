# look renders: blender -b X.blend -P render_heater.py -- out_prefix [clay|mat|keep]
#   clay = grey, mat = build the procedural shieldmat materials (high poly), keep = materials in the file (baked low)
import bpy, sys, math, mathutils, os
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; mode = args[1] if len(args) > 1 else 'clay'
D = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ['KITDIR']
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '64')); sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get('RW', '1200')), int(os.environ.get('RH', '1200'))
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '0'))
if mode == 'mat':
    sys.path.insert(0, os.environ.get('KITDIR', D)); import shieldmat, swordmat; (swordmat if os.environ.get('SHIELD') == 'Sword' else shieldmat).build_all()
elif mode == 'clay':
    for m in bpy.data.materials:
        m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
        b.inputs['Base Color'].default_value = (0.45, 0.45, 0.45, 1); b.inputs['Roughness'].default_value = 0.6
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.45, 0.5, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.85
if os.environ.get('VIEWSET') == 'sword':   # metal needs something to reflect: a real sky instead of flat grey
    nt_ = w.node_tree; sky = nt_.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(140)
    nt_.links.new(sky.outputs[0], nt_.nodes['Background'].inputs['Color']); nt_.nodes['Background'].inputs['Strength'].default_value = 0.25
    gp = bpy.data.meshes.new('floor'); gp.from_pydata([(-5, -5, -0.3), (5, -5, -0.3), (5, 5, -0.3), (-5, 5, -0.3)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new('floor', gp); sc.collection.objects.link(go); gm = bpy.data.materials.new('floorM'); gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.08, 0.07, 0.06, 1); gp.materials.append(gm)
def light(name, kind, energy, rot, size=None):
    l = bpy.data.lights.new(name, kind); l.energy = energy
    if size: l.size = size
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(v) for v in rot]; return o
k = light('Key', 'SUN', 3.2, tuple(float(v) for v in os.environ.get('KEYROT', '55,0,-40').split(','))); k.data.angle = math.radians(4)
r = light('Rim', 'SUN', 1.6, (-60, 0, 150)); r.data.angle = math.radians(8)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 60
views = {'front': ((0.0, -2.2, 0.44), (0, 0.03, 0.42)), 'front34': ((-1.25, -1.75, 0.95), (0, 0.03, 0.42)),
         'back34': ((1.2, 1.8, 0.85), (0.02, 0.03, 0.45)), 'side': ((2.1, -0.35, 0.55), (0, 0.03, 0.42)),
         'close_paint': ((-0.25, -0.62, 0.62), (0.02, 0.0, 0.42)), 'close_arrow': ((-0.35, -0.42, 0.50), (0.10, -0.03, 0.33)),
         'close_grip': ((0.30, 0.48, 0.60), (0.03, 0.04, 0.49)), 'close_rim': ((-0.55, -0.45, 0.98), (-0.20, 0.02, 0.76))}
if os.environ.get('VIEWSET') == 'sword':
    views = {'full': ((0.95, -1.10, 0.35), (0, 0, 0.20)), 'side': ((1.45, -0.05, 0.20), (0, 0, 0.20)),
             'close_hilt': ((0.16, -0.26, 0.06), (0, 0, -0.04)), 'close_blade': ((0.10, -0.22, 0.30), (0, 0, 0.22)),
             'close_pommel': ((0.05, -0.16, -0.10), (0, 0, -0.118)), 'close_guard': ((0.10, -0.18, 0.05), (0, 0, 0.015))}
for kk, (p, t) in views.items():
    if os.environ.get('VIEWS') and kk not in os.environ['VIEWS'].split(','): continue
    cam.location = p; d = mathutils.Vector(t) - mathutils.Vector(p); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 85 if kk.startswith('close') else 60
    sc.render.filepath = out + '_' + kk + '.png'; bpy.ops.render.render(write_still=True)
print('RENDER OK')
