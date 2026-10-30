# Calibrated lookdev of the rotting horse body (#155) (handoffs/knowledge): physical sky, sun 35 deg, 0.18 grey ball + chrome ball,
# exposure metered on the grey ball in linear Standard (118 sRGB) then rendered with AgX at that locked exposure.
#   blender -b horse_anim.blend -P lookdev_horse.py     env SKIN = Bay | Grey, VIEW = 34 | side | front | low,
#   POSE = <action name> FRAME = n (optional), LD_NAME, LD_SAMPLES
import bpy, bpy_extras, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); T = os.path.join(D, 'out', 'tex')
SKIN = os.environ.get('SKIN', 'Pale'); VAR = os.environ.get('VARIANT', 'Hollow'); VIEW = os.environ.get('VIEW', '34'); sc = bpy.context.scene
def teximg(nt, name, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, name + '.png')); n.image.colorspace_settings.name = cs; return n
def body_mat():
    m = bpy.data.materials.new('M_Body_' + SKIN); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    bc = teximg(nt, f'T_Rock_{SKIN}_BC', 'sRGB'); orm = teximg(nt, f'T_Rock_{SKIN}_ORM', 'Non-Color'); nm = teximg(nt, 'T_Rock_N_GL', 'Non-Color')
    nt.links.new(bc.outputs[0], b.inputs['Base Color']); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(orm.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], b.inputs['Roughness']); nt.links.new(sp.outputs[2], b.inputs['Metallic']); nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs[0], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], b.inputs['Normal'])
    return m
def wing_mat():
    m = bpy.data.materials.new('M_Wings_' + SKIN); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = teximg(nt, f'T_RealmWasp_Wings_{SKIN}_BCA', 'sRGB'); t.image.alpha_mode = 'STRAIGHT'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha']); b.inputs['Roughness'].default_value = 0.3
    return m
for o in sc.objects:
    if o.name == 'SM_RockAtlas': o.data.materials.clear(); o.data.materials.append(body_mat())
    pass
arm = bpy.data.objects.get('SK_ZombieV2_Rig')
if arm and os.environ.get('POSE'):
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[os.environ['POSE']]
    if hasattr(arm.animation_data, 'action_slot') and arm.animation_data.action.slots: arm.animation_data.action_slot = arm.animation_data.action.slots[0]
    sc.frame_set(int(os.environ.get('FRAME', '1')))
bpy.ops.mesh.primitive_plane_add(size=40)
g = bpy.context.active_object; gm = bpy.data.materials.new('Ground'); gm.use_nodes = True
gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.06, 0.05, 0.04, 1); gb.inputs['Roughness'].default_value = 0.9; g.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
sky = w.node_tree.nodes.new('ShaderNodeTexSky')
if 'NISHITA' in [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items]: sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(float(os.environ.get('SUNROT', '215'))); w.node_tree.links.new(sky.outputs[0], bg.inputs['Color'])
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0.0, 0.85))
cams = {'34': ((-3.2, -3.9, 1.9), 38), 'flank': ((4.6, -0.2, 1.2), 40), 'side': ((-4.6, 0.1, 1.2), 40), 'front': ((0.4, -3.6, 1.45), 50), 'low': ((-1.6, -2.4, 0.7), 32),
        'close': ((1.9, -1.3, 1.35), 40), 'zfront': ((0.9, -3.0, 1.2), 45), 'face': ((0.30, -0.95, 1.60), 55), 'shed': ((-6.0, -8.5, 3.0), 38), 'fence': ((6.5, -8.0, 2.2), 30), 'rocks': ((4.0, -7.0, 2.4), 32)}
if VIEW == 'rocks': tgt = Vector((4.0, 0, 0.5))
if VIEW == 'fence': tgt = Vector((7.5, 0, 0.6))
if VIEW == 'shed': tgt = Vector((0, 0, 1.2))
if VIEW == 'zfront': tgt = Vector((0, -0.05, 0.95))
if VIEW == 'face': tgt = Vector((0, -0.14, 1.56))
cam.location, cd.lens = cams[VIEW]
if VIEW == 'close': tgt = Vector((0.2, -0.1, 1.05))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
balls = []
for k, (col, met, rgh) in enumerate([((0.18, 0.18, 0.18, 1), 0.0, 0.5), ((0.95, 0.95, 0.95, 1), 1.0, 0.02)]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=48, ring_count=24, location=(1.25 + k * 0.4, -1.3, 0.16)); bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new('Ball%d' % k); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = met; p.inputs['Roughness'].default_value = rgh
    bpy.context.active_object.data.materials.append(m); balls.append(bpy.context.active_object)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1100; sc.render.image_settings.file_format = 'PNG'
out = os.path.join(D, 'out', os.environ.get('LD_NAME', f'lookdev_rocks_{SKIN}') + '.png')
uvp = bpy_extras.object_utils.world_to_camera_view(sc, cam, balls[0].location)
if 0 <= uvp.x <= 1 and 0 <= uvp.y <= 1:
    tmp = os.path.join(D, 'out', '_meter.png'); sc.render.filepath = tmp; sc.cycles.samples = 16
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -5.9
    for it in range(4):
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
        px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H, W, 4)
        cx, cy = int(uvp.x * W), int(uvp.y * H); v = float(px[cy - 3:cy + 4, cx - 3:cx + 4, :3].mean()) * 255
        print('METER grey ball %.0f sRGB at exposure %.2f' % (v, sc.view_settings.exposure), flush=True)
        if abs(v - 118) < 4: break
        L = lambda s: ((s / 255 + 0.055) / 1.055) ** 2.4
        sc.view_settings.exposure += math.log2(L(118) / max(L(min(v, 254)), 1e-4)) * (1.0 if v < 250 else 1.6)
else:
    sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '-5.9'))
sc.view_settings.view_transform = 'AgX'; sc.cycles.samples = int(os.environ.get('LD_SAMPLES', '64'))
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('LOOKDEV OK', out, 'exposure', sc.view_settings.exposure, flush=True)






