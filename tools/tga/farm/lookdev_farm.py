# Calibrated lookdev of the #223 crops (handoffs/knowledge): physical sky, sun 35 deg, grey + chrome ball, exposure metered
# to 118 sRGB on the grey ball (Standard) then AgX.   blender -b farm.blend -P lookdev_farm.py   env VIEW = wide | close, SUNROT
import bpy, bpy_extras, numpy as np, math, os
from mathutils import Vector
D = os.path.dirname(os.path.abspath(bpy.data.filepath)); T = os.path.join(D, 'out', 'tex'); VIEW = os.environ.get('VIEW', 'wide'); sc = bpy.context.scene
def teximg(nt, name, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, name + '.png')); n.image.colorspace_settings.name = cs; return n
def mat(B):
    m = bpy.data.materials.new('M_' + B); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    bc = teximg(nt, B + '_BC', 'sRGB'); orm = teximg(nt, B + '_ORM', 'Non-Color'); nm = teximg(nt, B + '_N_GL', 'Non-Color')
    nt.links.new(bc.outputs[0], b.inputs['Base Color']); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(orm.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], b.inputs['Roughness']); nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs[0], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], b.inputs['Normal'])
    return m
soil, crops = mat('T_FieldSoil'), mat('T_Crops')
src = {o.name: o for o in sc.objects}
for o in src.values(): o.data.materials.clear(); o.data.materials.append(soil if o.name == 'SM_Field_Plot' else crops); o.hide_render = True
def place(name, loc):
    o = src[name].copy(); o.location = loc; o.hide_render = False; sc.collection.objects.link(o)
place('SM_Field_Plot', (0, 0, 0)); place('SM_Field_Plot', (4.6, 0, 0))
for i, st in enumerate(('Sown', 'Growing', 'Ripe', 'Harvested')):
    for y in (-1.5, -0.5, 0.5, 1.5): place('SM_Crop_Wheat_' + st, (-1.5 + i, y, 0))
for x in (-1.5, -0.5, 0.5, 1.5):
    for y in (-1.5, -0.5, 0.5, 1.5): place('SM_Crop_Cabbage_' + ('Young' if x < 0 else 'Ripe'), (4.6 + x, y, 0))
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.005))
g = bpy.context.active_object; gm = bpy.data.materials.new('Ground'); gm.use_nodes = True
gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.06, 0.07, 0.035, 1); gb.inputs['Roughness'].default_value = 0.9; g.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
sky = w.node_tree.nodes.new('ShaderNodeTexSky')
if 'NISHITA' in [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items]: sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(float(os.environ.get('SUNROT', '215'))); w.node_tree.links.new(sky.outputs[0], bg.inputs['Color'])
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cams = {'wide': ((-1.0, -8.5, 3.4), 30, (2.3, 0, 0.3), (1.0, -2.7, 0.16)), 'close': ((-0.2, -3.1, 1.0), 35, (0.4, -0.8, 0.45), (-0.3, -2.3, 0.16))}
(cam.location, cd.lens, tgt, bp) = cams[VIEW]
cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
balls = []
for k, (col, met, rgh) in enumerate([((0.18, 0.18, 0.18, 1), 0.0, 0.5), ((0.95, 0.95, 0.95, 1), 1.0, 0.02)]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=48, ring_count=24, location=(bp[0] + k * 0.3, bp[1], bp[2] - 0.04)); bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new('Ball%d' % k); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = met; p.inputs['Roughness'].default_value = rgh
    bpy.context.active_object.data.materials.append(m); balls.append(bpy.context.active_object)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000; sc.render.image_settings.file_format = 'PNG'
uvp = bpy_extras.object_utils.world_to_camera_view(sc, cam, balls[0].location)
tmp = os.path.join(D, 'out', '_meter.png'); sc.render.filepath = tmp; sc.cycles.samples = 16
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -5.9
for it in range(4):
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
    px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H, W, 4)
    cx, cy = int(uvp.x * W), int(uvp.y * H); v = float(px[cy - 2:cy + 3, cx - 2:cx + 3, :3].mean()) * 255
    print('METER grey ball %.0f sRGB at exposure %.2f' % (v, sc.view_settings.exposure), flush=True)
    if abs(v - 118) < 4: break
    L = lambda s: ((s / 255 + 0.055) / 1.055) ** 2.4
    sc.view_settings.exposure += math.log2(L(118) / max(L(min(v, 254)), 1e-4)) * (1.0 if v < 250 else 1.6)
sc.view_settings.view_transform = 'AgX'; sc.cycles.samples = int(os.environ.get('LD_SAMPLES', '48'))
sc.render.filepath = os.path.join(D, 'out', 'lookdev_farm_' + VIEW + '.png'); bpy.ops.render.render(write_still=True); print('LOOKDEV OK', flush=True)
