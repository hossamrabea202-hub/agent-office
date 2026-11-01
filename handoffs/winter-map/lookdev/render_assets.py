"""WinterKeep #390: asset lineup lookdev (grey ball 0.18, chrome ball, LOCKED exposure, low winter sun).

blender -b --factory-startup -P render_assets.py -- [--res 1600] [--samples 64] [--out <png>] [--shot trees|ice]
Appends the SM_WK_* meshes from ../assets/out/wk_assets.blend (built by build_wk_assets.py).
"""
import bpy, math, os, sys
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d): return A[A.index(k) + 1] if k in A else d
RES, SAMPLES, SHOT = int(arg('--res', '1600')), int(arg('--samples', '64')), arg('--shot', 'trees')
HERE = os.path.dirname(os.path.abspath(__file__)); BLEND = os.path.join(HERE, '..', 'assets', 'out', 'wk_assets.blend')
OUTP = arg('--out', os.path.join(HERE, 'shots', 'assets_%s.png' % SHOT))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
with bpy.data.libraries.load(BLEND) as (src, dst): dst.objects = [n for n in src.objects if n.startswith('SM_WK_')]
P = {o.name: o for o in dst.objects}
def put(name, loc, rz=0.0, s=1.0):
    o = P[name].copy(); sc.collection.objects.link(o); o.location = loc; o.rotation_euler[2] = math.radians(rz); o.scale = (s, s, s); return o
# ground: snow, 2 m texture tile
bpy.ops.mesh.primitive_plane_add(size=240, location=(0, 0, 0)); g = bpy.context.active_object
for l in g.data.uv_layers[0].data: l.uv = l.uv * 120
g.data.materials.append(bpy.data.materials['WK_Snow'])
if SHOT == 'trees':
    put('SM_WK_Spruce_A', (0, 6, -0.3)); put('SM_WK_Spruce_B', (-9, 3, -0.2), 40); put('SM_WK_Birch_A', (9, 5, -0.2), 10)
    put('SM_WK_Rock_A', (-5.5, -5, -0.3), 30); put('SM_WK_Rock_B', (3.5, -6, -0.1), 70)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(6.5, -6, 2.3)); b = bpy.context.active_object; b.scale = (3.4, 0.2, 0.22)
    b.data.materials.append(bpy.data.materials['WK_Wood']); put('SM_WK_Icicles_3m', (5.0, -6.12, 2.19))
    eye, tgt, lens, ball = (0, -27, 3.2), (0, 0, 6.5), 30, (-1.6, -11, 0)
else:   # ice: falls curtain + icicles close
    put('SM_WK_IceFalls', (0, 0, -0.5)); eye, tgt, lens, ball = (-6, -30, 3.0), (0, 0, 7), 30, (-2.0, -16, 0)
for i, (nm, mk) in enumerate((('Grey18', 'grey'), ('Chrome', 'chrome'))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(ball[0] + i * 0.8, ball[1], 0.3 + ball[2])); o = bpy.context.active_object
    bpy.ops.object.shade_smooth(); m = bpy.data.materials.new(nm); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1) if mk == 'grey' else (0.95, 0.95, 0.95, 1)
    p.inputs['Roughness'].default_value = 0.5 if mk == 'grey' else 0.0; p.inputs['Metallic'].default_value = 0.0 if mk == 'grey' else 1.0; o.data.materials.append(m)
# world: Nishita sky, winter sun at 14 deg from the front-left (key 4:1), exposure LOCKED
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; nd, ln = w.node_tree.nodes, w.node_tree.links; nd.clear()
sky = nd.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(14); sky.sun_rotation = math.radians(235)
sky.altitude = 900; sky.dust_density = 1.4; bg = nd.new('ShaderNodeBackground'); out = nd.new('ShaderNodeOutputWorld')
ln.new(sky.outputs['Color'], bg.inputs['Color']); ln.new(bg.outputs['Background'], out.inputs['Surface'])
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Base Contrast'; sc.view_settings.exposure = -3.9
cam = bpy.data.cameras.new('Cam'); cam.lens = lens; co = bpy.data.objects.new('Cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = eye; co.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 8
sc.render.resolution_x = RES; sc.render.resolution_y = int(RES * 9 / 16); sc.render.filepath = OUTP
bpy.ops.render.render(write_still=True); print('wrote', OUTP, 'exposure locked -3.9')
