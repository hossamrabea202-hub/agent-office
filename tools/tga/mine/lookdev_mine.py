# Layout preview of the mine kit (#309, TGA): blender -b mine.blend -P lookdev_mine.py  -> out/mine_layout.jpg (env WORK, SAMPLES)
# Chamber + tunnels on the 4 m grid, timber every 2 m, rails, cart, ore vein, spoil heap, lanterns each with a real
# point light (KB rule 6), mine door at the far tunnel end. Cycles; rock damp from the vertex colour (wetness).
import bpy, os, math
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); TEX = os.path.join(D, 'out', 'tex')
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '128')); sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 1600, 900; sc.view_settings.look = 'AgX - Medium High Contrast'
def img(n, cs):
    i = bpy.data.images.load(os.path.join(TEX, n + '.png')); i.colorspace_settings.name = cs; return i
def setup(mname, tex, wet=False):
    m = bpy.data.materials[mname]; m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    bc = nt.nodes.new('ShaderNodeTexImage'); bc.image = img(tex + '_BC', 'sRGB')
    orm = nt.nodes.new('ShaderNodeTexImage'); orm.image = img(tex + '_ORM', 'Non-Color'); sp = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(orm.outputs[0], sp.inputs[0]); nt.links.new(sp.outputs[2], bs.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeTexImage'); nm.image = img(tex + '_N', 'Non-Color'); nn = nt.nodes.new('ShaderNodeNormalMap')
    fl = nt.nodes.new('ShaderNodeRGBCurve'); fl.mapping.curves[1].points[0].location = (0, 1); fl.mapping.curves[1].points[1].location = (1, 0)
    nt.links.new(nm.outputs[0], fl.inputs['Color']); nt.links.new(fl.outputs[0], nn.inputs['Color']); nt.links.new(nn.outputs[0], bs.inputs['Normal'])  # DX -> GL
    col, rough = bc.outputs[0], sp.outputs[1]
    if wet:
        va = nt.nodes.new('ShaderNodeVertexColor'); va.layer_name = 'Col'; s2 = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(va.outputs[0], s2.inputs[0])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['B'].default_value = (0, 0, 0, 1)
        mf = nt.nodes.new('ShaderNodeMath'); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = 0.45; nt.links.new(s2.outputs[0], mf.inputs[0])
        nt.links.new(mf.outputs[0], mx.inputs['Factor']); nt.links.new(col, mx.inputs['A']); col = mx.outputs['Result']
        mr = nt.nodes.new('ShaderNodeMix'); mr.inputs['B'].default_value = 0.15; nt.links.new(s2.outputs[0], mr.inputs['Factor'])
        nt.links.new(rough, mr.inputs['A']); rough = mr.outputs['Result']
    nt.links.new(col, bs.inputs['Base Color']); nt.links.new(rough, bs.inputs['Roughness'])
setup('M_MineRock', 'T_MineRock', True); setup('M_MineOak', 'T_MineOak'); setup('M_MineIron', 'T_MineIron'); setup('M_MineOre', 'T_MineOre')
g = bpy.data.materials['M_MineGlow']; g.use_nodes = True; bs = g.node_tree.nodes['Principled BSDF']
bs.inputs['Emission Color'].default_value = (1.0, 0.55, 0.2, 1); bs.inputs['Emission Strength'].default_value = 8.0
src = {o.name: o for o in sc.objects}
def put(name, loc, rz=0.0):
    o = src[name].copy(); sc.collection.objects.link(o); o.hide_render = False; o.location = loc; o.rotation_euler = (0, 0, math.radians(rz)); return o
for o in list(src.values()): o.hide_render = True
put('SM_Mine_Chamber', (0, 0, 0)); put('SM_Mine_Tunnel_Straight', (14, 0, 0)); put('SM_Mine_Tunnel_T', (18, 0, 0))
put('SM_Mine_Tunnel_DeadEnd', (22, 0, 0)); put('SM_Mine_Tunnel_Straight', (-4, 0, 0)); put('SM_Mine_Tunnel_Turn', (-4, 0, 0), 180)
for x in (15, 17, 19.0, 21, -1.5, -3.5): put('SM_Mine_TimberSet', (x, 0, 0))
for x in (-2, 2, 6, 10, 14, 18): put('SM_Mine_Rail_4m', (x, 0, 0))
put('SM_Mine_Cart', (8.5, 0, 0)); put('SM_Mine_OreVein', (6.5, -4.75, 0), 90); put('SM_Mine_OreVein', (3.6, -4.7, 0.2), 80)
put('SM_Mine_SpoilHeap', (10.5, 3.2, 0)); put('SM_Mine_DoorFrame', (24.4, 0, 0)); put('SM_Mine_Door', (24.4, 0, 0))
def lantern(loc, rz):
    put('SM_Mine_Lantern', loc, rz)
    bpy.ops.object.light_add(type='POINT', location=(loc[0], loc[1], loc[2] + 0.2)); L = bpy.context.active_object
    L.data.energy = 300; L.data.color = (1.0, 0.62, 0.3); L.data.shadow_soft_size = 0.05
for loc, rz in (((3.5, -3.6, 2.6), 90), ((10.5, 3.9, 2.4), -90), ((15.0, -1.25, 1.9), 90), ((20.9, 1.25, 1.9), -90), ((7.0, 4.2, 2.5), -90)):
    lantern(loc, rz)
bpy.ops.object.light_add(type='AREA', location=(7, 0, 4.6)); A = bpy.context.active_object; A.data.energy = 500; A.data.size = 6; A.data.color = (0.6, 0.7, 0.9)
wd = bpy.data.worlds.new('W'); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes['Background'].inputs[1].default_value = 0.0
bpy.ops.object.camera_add(location=(1.8, 2.6, 1.75)); cam = bpy.context.active_object; sc.camera = cam; cam.data.lens = 20
cam.rotation_euler = (math.radians(86), 0, math.radians(-104))
sc.render.image_settings.file_format = 'JPEG'; sc.render.filepath = os.path.join(D, 'out', 'mine_layout.jpg')
bpy.ops.render.render(write_still=True); print('RENDERED', sc.render.filepath, flush=True)
