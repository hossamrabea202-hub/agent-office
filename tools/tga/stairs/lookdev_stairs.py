# Lookdev render of the stair kit (#279, TGA): blender -b stairs.blend -P lookdev_stairs.py  -> out/stairs_lookdev.jpg
# Two flights (W200 Solid N10 against a wall, W120 Solid N06 free-standing) with the baked T_StairKit maps on slot 0 and
# a plain sandstone stand-in for the castle wall MI on slot 1. Cycles, sun + sky.
import bpy, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); TEX = os.path.join(D, 'out', 'tex')
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '96')); sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
keep = {'SM_Stair_W200_Solid_N10': (0, 0, 0), 'SM_Stair_W120_Solid_N06': (2.8, 0.6, 0)}
for o in list(sc.objects):
    if o.name not in keep: bpy.data.objects.remove(o)
def img(n, cs):
    i = bpy.data.images.load(os.path.join(TEX, n + '.png')); i.colorspace_settings.name = cs; return i
m = bpy.data.materials.new('Look'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
bc = nt.nodes.new('ShaderNodeTexImage'); bc.image = img('T_StairKit_BC', 'sRGB'); nt.links.new(bc.outputs[0], bs.inputs['Base Color'])
orm = nt.nodes.new('ShaderNodeTexImage'); orm.image = img('T_StairKit_ORM', 'Non-Color'); sp = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(orm.outputs[0], sp.inputs[0]); nt.links.new(sp.outputs[1], bs.inputs['Roughness'])
nm = nt.nodes.new('ShaderNodeTexImage'); nm.image = img('T_StairKit_N_GL', 'Non-Color'); nn = nt.nodes.new('ShaderNodeNormalMap')
nn.uv_map = 'UV0'; nt.links.new(nm.outputs[0], nn.inputs['Color']); nt.links.new(nn.outputs[0], bs.inputs['Normal'])
w = bpy.data.materials.new('Wall'); w.use_nodes = True; wb = w.node_tree.nodes['Principled BSDF']
wb.inputs['Base Color'].default_value = (0.2, 0.15, 0.1, 1); wb.inputs['Roughness'].default_value = 0.85
for n, loc in keep.items():
    o = sc.objects[n]; o.location = loc; o.data.materials[0] = m; o.data.materials[1] = w
    o.data.uv_layers.active = o.data.uv_layers['UV0']
bpy.ops.mesh.primitive_plane_add(size=30, location=(1, 3, 0)); g = bpy.context.active_object
gm = bpy.data.materials.new('Ground'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.08, 0.06, 1)
g.data.materials.append(gm)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.3, 1.6, 1.4)); wall = bpy.context.active_object; wall.scale = (0.6, 5, 2.8); wall.data.materials.append(w)
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-35))); bpy.context.active_object.data.energy = 4.0
wd = bpy.data.worlds.new('W'); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.5, 0.6, 1)
wd.node_tree.nodes['Background'].inputs[1].default_value = 0.6
bpy.ops.object.camera_add(location=(5.2, -3.6, 2.6)); cam = bpy.context.active_object; sc.camera = cam
tgt = bpy.data.objects.new('t', None); tgt.location = (1.5, 1.2, 0.8); sc.collection.objects.link(tgt)
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'; cam.data.lens = 35
sc.render.image_settings.file_format = 'JPEG'; sc.render.filepath = os.path.join(D, 'out', 'stairs_lookdev.jpg')
bpy.ops.render.render(write_still=True); print('RENDERED', sc.render.filepath, flush=True)
