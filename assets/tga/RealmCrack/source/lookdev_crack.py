# Lookdev of the realm mountain crack: blender -b crack.blend -P lookdev_crack.py    env TIME = day | night, LD_NAME
# Day: physical sky, sun 35 deg, exposure metered on a 0.18 grey ball (118 sRGB, linear Standard) then locked, AgX.
# Night: sky at moonlight level, the same locked exposure + EV_NIGHT stops, so the glow is judged against a dark scene.
import bpy, bpy_extras, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); T = os.path.join(D, 'out', 'tex')
TIME = os.environ.get('TIME', 'day'); sc = bpy.context.scene
def ti(nt, n, cs):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(T, n + '.png')); t.image.colorspace_settings.name = cs; return t
ob = bpy.data.objects['SM_RealmCrack']; m = bpy.data.materials.new('M_Look'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
bc = ti(nt, 'T_RealmCrack_BC', 'sRGB'); orm = ti(nt, 'T_RealmCrack_ORM', 'Non-Color'); nm = ti(nt, 'T_RealmCrack_N_GL', 'Non-Color'); e = ti(nt, 'T_RealmCrack_E', 'Non-Color')
nt.links.new(bc.outputs[0], b.inputs['Base Color']); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(orm.outputs[0], sp.inputs[0]); nt.links.new(sp.outputs[1], b.inputs['Roughness'])
nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs[0], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], b.inputs['Normal'])
nt.links.new(e.outputs[0], b.inputs['Emission Strength']); b.inputs['Emission Color'].default_value = (1.0, 0.32, 0.05, 1)
GLOW = float(os.environ.get('GLOW', '40'))
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = GLOW
nt.links.new(e.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], b.inputs['Emission Strength'])
ob.data.materials.clear(); ob.data.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, -15, -0.2)); g = bpy.context.active_object
gm = bpy.data.materials.new('G'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.05, 0.045, 0.04, 1); g.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; sky = w.node_tree.nodes.new('ShaderNodeTexSky')
if 'NISHITA' in [x.identifier for x in sky.bl_rna.properties['sky_type'].enum_items]: sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(200); w.node_tree.links.new(sky.outputs[0], bg.inputs['Color'])
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (6.5, -20.0, 3.5); cd.lens = 40; tgt = Vector((0, 0, 4.2)); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(-4.5, -6.0, 0.3)); bpy.ops.object.shade_smooth(); ball = bpy.context.active_object
bm = bpy.data.materials.new('Ball'); bm.use_nodes = True; bm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1); ball.data.materials.append(bm)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True; sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
uvp = bpy_extras.object_utils.world_to_camera_view(sc, cam, ball.location)
tmp = os.path.join(D, 'out', '_meter.png'); sc.render.filepath = tmp; sc.cycles.samples = 16; sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -5.9
b.inputs['Emission Strength'].default_value = 0; nt.links.remove(mul.outputs[0].links[0])        # meter without the glow
L = lambda s: ((s / 255 + 0.055) / 1.055) ** 2.4
for it in range(4):
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W_, H_ = im.size
    px = np.empty(W_ * H_ * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H_, W_, 4)
    cx, cy = int(uvp.x * W_), int(uvp.y * H_); v = float(px[cy - 3:cy + 4, cx - 3:cx + 4, :3].mean()) * 255
    print('METER %.0f at %.2f' % (v, sc.view_settings.exposure), flush=True)
    if abs(v - 118) < 4: break
    sc.view_settings.exposure += math.log2(L(118) / max(L(min(v, 254)), 1e-4)) * (1.0 if v < 250 else 1.6)
nt.links.new(mul.outputs[0], b.inputs['Emission Strength'])
if TIME == 'night':
    bg.inputs['Strength'].default_value = 0.004; sky.sun_elevation = math.radians(-8)
    sc.view_settings.exposure += float(os.environ.get('EV_NIGHT', '5.5'))
sc.view_settings.view_transform = 'AgX'; sc.cycles.samples = int(os.environ.get('LD_SAMPLES', '64'))
sc.render.filepath = os.path.join(D, 'out', os.environ.get('LD_NAME', 'crack_' + TIME) + '.png'); bpy.ops.render.render(write_still=True)
print('LOOKDEV OK', sc.render.filepath, sc.view_settings.exposure, flush=True)
