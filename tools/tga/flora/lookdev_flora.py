# Owner renders of the meadow flora kit (#352, TGA): blender -b flora.blend -P lookdev_flora.py   (env WORK, SAMPLES)
#   out/flora_lineup.jpg (all 17 meshes, LOD0), out/flora_meadow.jpg (clumps by ecology rule: flowers in species patches, never an even
#   spray; bushes at the edge, bracken in the bush shade), out/flora_lods.jpg (LOD0..3 of Daisy_C and Hawthorn_B).
import bpy, os, math, numpy as np
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); OUT = os.path.join(D, 'out')
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '96')); sc.cycles.device = 'CPU'
sc.render.film_transparent = False; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.cycles.max_bounces = 6
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.color_mode = 'RGB'
src = {o.name: o for o in sc.objects if o.type == 'MESH'}
for m in bpy.data.materials:                                                 # a bit more leaf transmission for the stills
    if m.use_nodes and 'LIT' in m.node_tree.nodes: m.node_tree.nodes['LIT'].inputs[0].default_value = 0.45
for o in src.values(): o.hide_render = True
for o in [o for o in sc.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)
wd = bpy.data.worlds.new('Sky'); sc.world = wd; wd.use_nodes = True; bg = wd.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.68, 0.9, 1); bg.inputs[1].default_value = 1.4
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(35))); sun = bpy.context.active_object; sun.data.energy = 4.0; sun.data.angle = math.radians(1.5); sun.data.color = (1, 0.95, 0.86)
gm = bpy.data.materials.new('Ground'); gm.use_nodes = True; gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.09, 0.075, 0.05, 1); gb.inputs['Roughness'].default_value = 0.95
bpy.ops.mesh.primitive_plane_add(size=60); gp = bpy.context.active_object; gp.data.materials.append(gm)
gr = bpy.data.materials.new('Grass'); gr.use_nodes = True; nt = gr.node_tree; b = nt.nodes['Principled BSDF']
va = nt.nodes.new('ShaderNodeVertexColor'); va.layer_name = 'Col'; nt.links.new(va.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.6
tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); nt.links.new(va.outputs[0], tr.inputs['Color']); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.3
nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
def grass(x0, x1, y0, y1, n, seed, hmax=0.35):
    """stand-in meadow grass (lookdev only, adjustedfilm's scatter uses the project grass): tapered 2-tri blades, clumped heights and tints"""
    r = np.random.default_rng(seed); V, F, C = [], [], []
    for i in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1); clump = 0.5 + 0.5 * math.sin(x * 1.7 + 2 * math.sin(y * 1.3)) * math.cos(y * 2.1)
        h = hmax * (0.35 + 0.65 * clump) * r.uniform(0.6, 1.1); a = r.uniform(0, 6.28); lean = r.normal(0, 0.25, 2); w = 0.004
        dx, dy = math.cos(a) * w, math.sin(a) * w; k = len(V)
        V += [(x - dx, y - dy, 0), (x + dx, y + dy, 0), (x + lean[0] * h * 0.5 + dx * 0.5, y + lean[1] * h * 0.5 + dy * 0.5, h * 0.55), (x + lean[0] * h, y + lean[1] * h, h)]
        F += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
        g = (0.05 + 0.03 * clump * r.random(), 0.09 + 0.05 * r.random(), 0.02 + 0.012 * r.random(), 1); dry = r.random() < 0.12
        if dry: g = (0.2, 0.17, 0.08, 1)
        C += [g] * 4
    me = bpy.data.meshes.new('G'); me.from_pydata(V, [], F); ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', np.array(C, np.float32).ravel())
    me.materials.append(gr); o = bpy.data.objects.new('Grass', me); sc.collection.objects.link(o); return o
placed = []
def put(name, loc, rz=0.0, s=1.0):
    o = src[name].copy(); sc.collection.objects.link(o); o.hide_render = False; o.location = loc; o.rotation_euler = (0, 0, rz); o.scale = (s, s, s); placed.append(o); return o
def clear():
    for o in placed: bpy.data.objects.remove(o)
    placed.clear()
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
def shoot(path, loc, look, lens, rx=1600, ry=900):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry; cam.location = loc; cam.data.lens = lens
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.render.filepath = os.path.join(OUT, path)
    bpy.ops.render.render(write_still=True); print('RENDERED', path, flush=True)
# 1. lineup
names = [n for n in src if '_LOD' not in n]; x = 0.0
row1 = [n for n in names if n.startswith('SM_Flower')]; row2 = [n for n in names if not n.startswith('SM_Flower')]
for i, n in enumerate(row1): put(n, (-2.75 + i * 0.5, 0.6, 0), 0.4)
xs = {'SM_Bush_Hawthorn_A': -2.6, 'SM_Bush_Hawthorn_B': -0.9, 'SM_Bush_Hazel_A': 0.9, 'SM_Bush_Hazel_B': 2.8, 'SM_Fern_Bracken_A': 4.4}
for n in row2: put(n, (xs.get(n, 0), 3.2, 0), 0.3)
shoot('flora_lineup.jpg', (0.6, -4.6, 1.5), (0.6, 1.6, 0.55), 30)
clear()
# 2. meadow vignette
g = grass(-4, 4, -2, 5, 26000, 1)
r = np.random.default_rng(7)
def patch(sp, cx, cy, n, rad):
    for i in range(n):
        a, d = r.uniform(0, 6.28), rad * math.sqrt(r.random()); put('SM_Flower_%s_%s' % (sp, 'ABC'[r.integers(3)]), (cx + d * math.cos(a), cy + d * math.sin(a), 0), r.uniform(0, 6.28), r.uniform(0.85, 1.15))
patch('Daisy', -1.2, 0.6, 9, 0.6); patch('Poppy', 0.7, 0.3, 7, 0.5); patch('Yarrow', 1.6, 1.6, 5, 0.45); patch('Cornflower', -0.2, 1.4, 6, 0.5)
patch('Daisy', 1.9, 0.0, 4, 0.35); patch('Poppy', -2.2, 1.9, 4, 0.4)
put('SM_Bush_Hawthorn_B', (-2.3, 3.6, 0), 0.5); put('SM_Bush_Hazel_B', (0.6, 4.2, 0), 1.2); put('SM_Bush_Hawthorn_A', (2.6, 3.4, 0), 2.0)
put('SM_Fern_Bracken_A', (-0.8, 3.2, 0), 0.0); put('SM_Fern_Bracken_A', (1.8, 3.0, 0), 2.1, 0.85)
shoot('flora_meadow.jpg', (0.1, -2.6, 0.75), (0.1, 2.0, 0.35), 32)
clear(); bpy.data.objects.remove(g)
# 3. LOD strip
for lod in range(4):
    sfx = '' if lod == 0 else '_LOD%d' % lod
    put('SM_Flower_Daisy_C' + sfx, (-1.05 + lod * 0.5, -0.3, 0)); put('SM_Bush_Hawthorn_B' + sfx, (-1.7 + lod * 1.9, 2.2, 0))
shoot('flora_lods.jpg', (1.1, -4.2, 1.3), (1.1, 1.5, 0.6), 30)
