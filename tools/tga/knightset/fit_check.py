# #367 fit check: the fitted Yellow Eagle pieces (knight space) on a stick figure of the knight's ref-pose bones.
#   blender -b --factory-startup -P fit_check.py   (env WORK, REPO) -> WORK/out/fit_check.png
import bpy, os, math, numpy as np, mathutils
D = os.environ['WORK']; REPO = os.environ.get('REPO', 'R:\\')
B = {}
for ln in open(os.path.join(REPO, 'handoffs', 'exports', 'master', 'knight_refpose.txt'), encoding='utf-8'):
    if ln.startswith('#') or not ln.strip(): continue
    f = ln.split('\t'); w = [float(x) for x in f[4].split(',')]; B[f[0]] = mathutils.Vector((w[0], -w[1], w[2])) / 100
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene
chains = [['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head']]
for s in 'lr':
    chains += [['spine_03', 'clavicle_' + s, 'upperarm_' + s, 'lowerarm_' + s, 'hand_' + s], ['pelvis', 'thigh_' + s, 'calf_' + s, 'foot_' + s, 'ball_' + s]]
    for fg in ('index', 'middle', 'ring', 'pinky', 'thumb'): chains.append(['hand_' + s] + ['%s_0%d_%s' % (fg, i, s) for i in (1, 2, 3)])
bm = bpy.data.materials.new('bone'); bm.use_nodes = True; bm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.15, 0.1, 1)
def stick(a, b, r):
    d = b - a; L = d.length
    if L < 1e-4: return
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=L, vertices=8, location=(a + b) / 2)
    o = bpy.context.object; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(bm)
for c in chains:
    for a, b in zip(c, c[1:]): stick(B[a], B[b], 0.004 if ('_0' in b) else 0.012)
for k, v in B.items():
    if k.startswith('ik') or k == 'root': continue
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006 if '_0' in k else 0.016, location=v, segments=10, ring_count=6); bpy.context.object.data.materials.append(bm)
fb = os.path.join(D, 'out', 'fbx_knight')
for f in sorted(os.listdir(fb)):
    if 'LOD' in f: continue
    bpy.ops.import_scene.fbx(filepath=os.path.join(fb, f))
# textures (the FBX carries slot names; rebuild a simple textured material per piece)
for o in [x for x in bpy.data.objects if x.type == 'MESH' and x.name.startswith('SM_Eagle')]:
    pc = o.name.split('_')[1][5:]                        # SM_EagleGauntlets_L -> Gauntlets
    m = bpy.data.materials.new('M_' + pc); m.use_nodes = True; nt = m.node_tree; P = nt.nodes['Principled BSDF']
    tx = os.path.join(D, 'out', 'tex')
    def img(n, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(tx, 'T_Eagle%s_%s.png' % (pc, n)), check_existing=True); t.image.colorspace_settings.name = cs; return t
    bc = img('BC', 'sRGB'); orm = img('ORM', 'Non-Color'); sp = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(bc.outputs[0], P.inputs['Base Color']); nt.links.new(orm.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], P.inputs['Roughness']); nt.links.new(sp.outputs[2], P.inputs['Metallic'])
    o.data.materials.clear(); o.data.materials.append(m)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(30))); bpy.context.object.data.energy = 3
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 700, 1000; sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
views = [('front', (0, -4, 0.9), 1.95, (0, 0, 0.9)), ('side', (4, 0, 0.9), 1.95, (0, 0, 0.9)),
         ('hand_front', (0.5, -3, 1.07), 0.42, (0.5, 0.06, 1.07)), ('hand_top', (0.5, 0.06, 4), 0.42, (0.5, 0.06, 1.07)),
         ('leg_34', (2.2, -2.6, 0.3), 0.75, (0.18, 0.05, 0.25)), ('leg_back', (0.2, 4, 0.3), 0.75, (0.18, 0.05, 0.25))]
paths = []
for n, loc, size, tgt in views:
    cam.location = loc; cam.data.ortho_scale = size
    cam.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    p = os.path.join(D, 'out', 'fitv_%s.png' % n); sc.render.filepath = p; bpy.ops.render.render(write_still=True); paths.append(p)
print('FITCHECK', paths, flush=True)
