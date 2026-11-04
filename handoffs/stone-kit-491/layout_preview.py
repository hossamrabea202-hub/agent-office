# #491 (i5): elevation of one wall from layout/<file>_layout.json, plain boxes coloured by kit length, orthographic.
#   blender -b --factory-startup -P layout_preview.py -- <layout.json> <wall name> <out.png> [face -y|+y]
import bpy, json, math, sys
a = sys.argv[sys.argv.index('--') + 1:]; d = json.load(open(a[0])); w = [x for x in d['walls'] if x['name'] == a[1]][0]; face = a[3] if len(a) > 3 else '-y'
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
cols = {45: (0.55, 0.52, 0.47), 60: (0.62, 0.58, 0.52), 75: (0.70, 0.66, 0.59), 85: (0.78, 0.72, 0.62), 95: (0.85, 0.80, 0.70)}
mats = {}
for k, c in cols.items():
    m = bpy.data.materials.new(str(k)); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*c, 1); mats[k] = m
q = bpy.data.materials.new('quoin'); q.use_nodes = True; q.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.35, 0.25, 1)
for b in w['blocks']:
    if b['face'] != face: continue
    L = int(b['kit'].split('_L')[1].split('_')[0])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(b['c'][0], -b['c'][1], b['c'][2]))
    o = bpy.context.object; o.scale = (b['len_m'], b.get('d_m', 0.38), b['h_m']) if b['face'] in ('-y', '+y') else (b.get('d_m', 0.38), b['len_m'], b['h_m'])
    o.data.materials.append(q if b['role'] == 'quoin' else mats[L])
S = [v / 100 for v in w['size_cm']]
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (S[0] - 0.05, S[1] - 0.05, S[2] - 0.05)
m = bpy.data.materials.new('mortar'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12, 0.11, 0.1, 1); o.data.materials.append(m)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(S[0], S[2]) * 1.05
y = 10 if face == '-y' else -10
cam.location = (0, y, 0); cam.rotation_euler = (math.radians(90), 0, math.radians(180 if face == '-y' else 0))   # UE -y = Blender +y: look back at it
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(70), 0, math.radians(20)); sun.data.energy = 4
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x = 1600; sc.render.resolution_y = int(1600 * S[2] / S[0]) if S[0] > S[2] else 1600
w_ = bpy.data.worlds.new('w'); sc.world = w_; w_.use_nodes = True; w_.node_tree.nodes['Background'].inputs[0].default_value = (0.8, 0.85, 0.9, 1)
sc.render.filepath = a[2]; bpy.ops.render.render(write_still=True); print('PREVIEW', a[2])
