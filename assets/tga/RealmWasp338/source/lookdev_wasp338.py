# Calibrated lookdev of the realm wasp v2 (#338, TGA PC): physical sky, sun 35 deg, 0.18 grey ball + chrome ball, exposure
# metered on the grey ball in Standard (118 sRGB), then AgX at that locked exposure (or EXPOSURE=<ev> to reuse a metered value).
#   blender -b wasp338_anim.blend -P lookdev_wasp338.py   env SKIN Ember|Blight, VIEW 34|side|front|close|low|far, POSE <action>, FRAME n,
#   LD_NAME, LD_SAMPLES, EXPOSURE, RES_X, RES_Y
# Materials mirror the UE ones: body = BC / ORM / N + SSE (R subsurface, G spore glow, B wet), wings translucent, blur cards faint.
import bpy, bpy_extras, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); T = os.path.join(D, 'out', 'tex')
SKIN = os.environ.get('SKIN', 'Ember'); VIEW = os.environ.get('VIEW', '34'); sc = bpy.context.scene
def teximg(nt, name, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, name + '.png'), check_existing=True); n.image.colorspace_settings.name = cs; return n
def body_mat():
    m = bpy.data.materials.new('M_Body_' + SKIN); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; L = nt.links.new
    bc = teximg(nt, f'T_RealmWasp_Body_{SKIN}_BC', 'sRGB'); orm = teximg(nt, f'T_RealmWasp_Body_{SKIN}_ORM', 'Non-Color')
    nm = teximg(nt, 'T_RealmWasp_Body_N_GL', 'Non-Color'); sse = teximg(nt, 'T_RealmWasp_Body_SSE', 'Non-Color')
    L(bc.outputs[0], b.inputs['Base Color']); sp = nt.nodes.new('ShaderNodeSeparateColor'); L(orm.outputs[0], sp.inputs[0]); L(sp.outputs[1], b.inputs['Roughness'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); L(nm.outputs[0], nmap.inputs['Color']); L(nmap.outputs[0], b.inputs['Normal'])
    s2 = nt.nodes.new('ShaderNodeSeparateColor'); L(sse.outputs[0], s2.inputs[0])
    w = nt.nodes.new('ShaderNodeMath'); w.operation = 'MULTIPLY'; w.inputs[1].default_value = 0.6; L(s2.outputs[0], w.inputs[0]); L(w.outputs[0], b.inputs['Subsurface Weight'])
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.55, 0.3); b.inputs['Subsurface Scale'].default_value = 0.006   # thin chitin / tissue: a few mm
    e = nt.nodes.new('ShaderNodeMath'); e.operation = 'MULTIPLY'; e.inputs[1].default_value = 6.0; L(s2.outputs[1], e.inputs[0])
    b.inputs['Emission Color'].default_value = (1.0, 0.62, 0.25, 1) if SKIN == 'Ember' else (0.55, 1.0, 0.45, 1); L(e.outputs[0], b.inputs['Emission Strength'])
    return m
def hair_mat():
    m = bpy.data.materials.new('M_Hair'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    uv = nt.nodes.new('ShaderNodeUVMap'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs[0], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs[1], ramp.inputs[0])
    root, tip = ((0.045, 0.032, 0.022, 1), (0.42, 0.30, 0.14, 1)) if SKIN == 'Ember' else ((0.04, 0.033, 0.04, 1), (0.36, 0.34, 0.24, 1))
    ramp.color_ramp.elements[0].color = root; ramp.color_ramp.elements[1].color = tip; ramp.color_ramp.elements[1].position = 0.35
    nt.links.new(ramp.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.62
    b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Scale'].default_value = 0.002
    return m
def wing_mat(tex, mult):
    m = bpy.data.materials.new(tex); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = teximg(nt, tex, 'sRGB'); t.image.alpha_mode = 'STRAIGHT'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.inputs[1].default_value = mult
    nt.links.new(t.outputs['Alpha'], k.inputs[0]); nt.links.new(k.outputs[0], b.inputs['Alpha']); b.inputs['Roughness'].default_value = 0.25
    b.inputs['Transmission Weight'].default_value = 0.3; b.inputs['Thin Film Thickness'].default_value = 260.0 if mult >= 1 else 0.0   # faint sheen, membranes only
    return m
MATS = {'SK_RealmWasp': body_mat(), 'SK_RealmWasp_Hair': hair_mat(), 'SK_RealmWasp_Wings': wing_mat(f'T_RealmWasp_Wings_{SKIN}_BCA', 1.0),
        'SK_RealmWasp_WingBlur': wing_mat(f'T_RealmWasp_WingBlur_{SKIN}_BCA', float(os.environ.get('BLUR', '0.55')))}
for o in sc.objects:
    if o.name in MATS: o.data.materials.clear(); o.data.materials.append(MATS[o.name])
    if o.name == 'SK_RealmWasp_WingBlur' and os.environ.get('NOBLUR') == '1': o.hide_render = True
arm = bpy.data.objects.get('SK_RealmWasp_Rig')
if arm and os.environ.get('POSE'):
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[os.environ['POSE']]
    if hasattr(arm.animation_data, 'action_slot') and arm.animation_data.action.slots: arm.animation_data.action_slot = arm.animation_data.action.slots[0]
    sc.frame_set(int(os.environ.get('FRAME', '1')))
bpy.ops.mesh.primitive_plane_add(size=80)
g = bpy.context.active_object; gm = bpy.data.materials.new('Ground'); gm.use_nodes = True
gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.06, 0.05, 0.04, 1); gb.inputs['Roughness'].default_value = 0.9; g.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
sky = w.node_tree.nodes.new('ShaderNodeTexSky')
if 'NISHITA' in [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items]: sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(215); w.node_tree.links.new(sky.outputs[0], bg.inputs['Color'])
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0.05, 1.15))
cams = {'34': ((-2.5, -3.3, 1.9), 40), 'side': ((3.9, 0.1, 1.35), 45), 'front': ((0.4, -3.6, 1.45), 50), 'low': ((-1.6, -2.4, 0.6), 30),
        'close': ((-0.95, -1.5, 1.6), 50), 'far': ((-14.0, -20.0, 3.5), 50), 'back': ((1.6, 2.8, 1.9), 40)}
cam.location, cd.lens = cams[VIEW]
if VIEW == 'close': tgt = Vector((0, -0.45, 1.3))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
balls = []
for k, (col, met, rgh) in enumerate([((0.18, 0.18, 0.18, 1), 0.0, 0.5), ((0.95, 0.95, 0.95, 1), 1.0, 0.02)]):
    loc = (1.05 + k * 0.4, -0.9, 0.16) if VIEW != 'far' else (2.2 + k * 0.9, -1.5, 0.36)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16 if VIEW != 'far' else 0.36, segments=48, ring_count=24, location=loc); bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new('Ball%d' % k); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = met; p.inputs['Roughness'].default_value = rgh
    bpy.context.active_object.data.materials.append(m); balls.append(bpy.context.active_object)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'
pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = True
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get('RES_X', '1600')), int(os.environ.get('RES_Y', '1100')); sc.render.image_settings.file_format = 'PNG'
os.makedirs(os.path.join(D, 'out', 'renders'), exist_ok=True)
out = os.path.join(D, 'out', 'renders', os.environ.get('LD_NAME', f'lookdev_{SKIN}_{VIEW}') + '.png')
bpy.context.view_layer.update()
if os.environ.get('EXPOSURE'):
    sc.view_settings.exposure = float(os.environ['EXPOSURE'])
else:
    uvp = bpy_extras.object_utils.world_to_camera_view(sc, cam, balls[0].location)
    tmp = os.path.join(D, 'out', '_meter.png'); sc.render.filepath = tmp; sc.cycles.samples = 16
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -5.9
    for it in range(5):
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
        px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H, W, 4)
        cx, cy = int(uvp.x * W), int(uvp.y * H); v = float(px[cy - 3:cy + 4, cx - 3:cx + 4, :3].mean()) * 255
        print('METER grey ball %.0f sRGB at exposure %.2f' % (v, sc.view_settings.exposure), flush=True)
        if abs(v - 118) < 4: break
        Lf = lambda s: ((s / 255 + 0.055) / 1.055) ** 2.4
        sc.view_settings.exposure += math.log2(Lf(118) / max(Lf(min(v, 254)), 1e-4)) * (1.0 if v < 250 else 1.6)
sc.view_settings.view_transform = 'AgX'; sc.cycles.samples = int(os.environ.get('LD_SAMPLES', '96'))
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('LOOKDEV OK', out, 'exposure %.2f' % sc.view_settings.exposure, flush=True)
