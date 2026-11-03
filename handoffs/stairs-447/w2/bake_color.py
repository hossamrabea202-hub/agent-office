# #301 W2 (i5, 2026-11-03): BakedColor for the baked kit flights, so they can run on i9's M_KeepEntrance_Baked
# (the keep's weathering: lime, moss, grime band, cracks, soil). The colour is the same wall scan Weathered2 uses
# (T_vdbhdju_2K_B -> scan_B.png -> joint-free granite_tile.png, clean_scan.py), box-projected in object space with a
# per-stone offset (M.A) so no two stones show the same patch, then shaped by our own bake masks:
#   tone (M.A) = per-stone brightness, joint (M.G) = darker recessed mortar, wear (M.B) = foot-polished treads a bit lighter.
# AO (M.R) is NOT baked in: the material multiplies BakedAO itself (no double AO).
#   blender -b --factory-startup <build451/NAME.blend> -P bake_color.py -- <build451 dir> <NAME> [size=2048] [tile_m=0.38]
import bpy, os, sys
argv = sys.argv[sys.argv.index('--') + 1:]
BUILD, NAME = argv[0], argv[1]
SIZE = int(argv[2]) if len(argv) > 2 else 2048
TILE = float(argv[3]) if len(argv) > 3 else 0.38
HERE = os.path.dirname(os.path.abspath(__file__))

low = bpy.data.objects[NAME + '_low']
for o in bpy.data.objects:
    o.hide_render = o is not low
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
sc.render.bake.margin = 8

mat = bpy.data.materials.new('W2Bake'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; L = nt.links; N.clear()
def node(t, **kw):
    n = N.new(t)
    for k, v in kw.items(): setattr(n, k, v)
    return n
tc = node('ShaderNodeTexCoord')
mp = node('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / TILE,) * 3
L.new(tc.outputs['Object'], mp.inputs['Vector'])
scan = node('ShaderNodeTexImage', projection='BOX', projection_blend=0.25)
scan.image = bpy.data.images.load(os.path.join(HERE, 'granite_tile.png'))
mimg = node('ShaderNodeTexImage'); mimg.image = bpy.data.images.load(os.path.join(BUILD, NAME + '_M.png'))
mimg.image.colorspace_settings.name = 'Non-Color'; mimg.image.alpha_mode = 'CHANNEL_PACKED'
L.new(tc.outputs['UV'], mimg.inputs['Vector'])
sep = node('ShaderNodeSeparateColor'); L.new(mimg.outputs['Color'], sep.inputs['Color'])
off = node('ShaderNodeCombineXYZ')
for ax, k in zip('XYZ', (3.7, 5.3, 2.9)):
    m = node('ShaderNodeMath', operation='MULTIPLY'); m.inputs[1].default_value = k
    L.new(mimg.outputs['Alpha'], m.inputs[0]); L.new(m.outputs[0], off.inputs[ax])
add = node('ShaderNodeVectorMath', operation='ADD')
L.new(mp.outputs['Vector'], add.inputs[0]); L.new(off.outputs['Vector'], add.inputs[1]); L.new(add.outputs['Vector'], scan.inputs['Vector'])

def math(op, a, b, clamp=False):
    m = node('ShaderNodeMath', operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b)):
        if isinstance(x, float): m.inputs[i].default_value = x
        else: L.new(x, m.inputs[i])
    return m.outputs[0]
# tone: 0.82 .. 1.12 per stone
tone = math('ADD', math('MULTIPLY', mimg.outputs['Alpha'], 0.30), 0.82)
# joint: mortar down to 0.55
joint = math('SUBTRACT', 1.0, math('MULTIPLY', sep.outputs['Green'], 0.45))
# wear: polished foot path up to +8 %
wear = math('ADD', 1.0, math('MULTIPLY', sep.outputs['Blue'], 0.08))
k = math('MULTIPLY', math('MULTIPLY', tone, joint), wear)
mul = node('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mul.inputs['Factor'].default_value = 1.0
L.new(scan.outputs['Color'], mul.inputs[6])
comb = node('ShaderNodeCombineColor')
for ch in ('Red', 'Green', 'Blue'): L.new(k, comb.inputs[ch])
L.new(comb.outputs['Color'], mul.inputs[7])
em = node('ShaderNodeEmission'); L.new(mul.outputs[2], em.inputs['Color'])
out = node('ShaderNodeOutputMaterial'); L.new(em.outputs['Emission'], out.inputs['Surface'])

img = bpy.data.images.new(NAME + '_C', SIZE, SIZE, alpha=False)
tgt = node('ShaderNodeTexImage'); tgt.image = img; N.active = tgt
low.data.materials.clear(); low.data.materials.append(mat)
for p in low.data.polygons: p.material_index = 0
bpy.ops.object.select_all(action='DESELECT'); low.select_set(True); bpy.context.view_layer.objects.active = low
bpy.ops.object.bake(type='EMIT')
img.filepath_raw = os.path.join(BUILD, NAME + '_C.png'); img.file_format = 'PNG'; img.save()
print('BAKED', img.filepath_raw)
