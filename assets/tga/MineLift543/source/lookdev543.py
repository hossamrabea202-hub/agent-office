# #543 lookdev (TGA PC). blender -b work/mine543.blend -P lookdev543.py   env VIEW reveal|room|ride|door|swordcard, LD_NAME, LD_SAMPLES, EXPOSURE
# Materials mirror the UE ones (#309 M_MineSurface: wet = base^2 + roughness 0.15 on vertex colour R, soot G, puddles B;
# DirectX normals flipped here for Blender). Exposure: metered on a 0.18 grey ball beside the subject in its own lantern
# light to METER (default 96 sRGB: a dark mine, not daylight), then AgX at that locked exposure.
import bpy, bpy_extras, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath); T = os.path.join(D, 'out', 'tex')
HERE = os.path.dirname(os.path.abspath(__file__)); KT = os.path.join(HERE, 'ref', 'kit', 'textures'); KF = os.path.join(HERE, 'ref', 'kit', 'fbx')
VIEW = os.environ.get('VIEW', 'reveal'); sc = bpy.context.scene; O = bpy.data.objects
def img(path, cs):
    i = bpy.data.images.load(path, check_existing=True); i.colorspace_settings.name = cs; return i
def newmat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree, m.node_tree.nodes['Principled BSDF']
def texset(name, bcp, ormp, np_, uvscale=(1, 1), dx=True, vcol=False):
    m, nt, b = newmat(name); L = nt.links.new; N = nt.nodes
    uv = N.new('ShaderNodeUVMap'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (uvscale[0], uvscale[1], 1); L(uv.outputs[0], mp.inputs[0])
    t = {}
    for k, p, cs in (('bc', bcp, 'sRGB'), ('orm', ormp, 'Non-Color'), ('n', np_, 'Non-Color')):
        t[k] = N.new('ShaderNodeTexImage'); t[k].image = img(p, cs); L(mp.outputs[0], t[k].inputs[0])
    orm = N.new('ShaderNodeSeparateColor'); L(t['orm'].outputs[0], orm.inputs[0])
    nn = N.new('ShaderNodeSeparateColor'); L(t['n'].outputs[0], nn.inputs[0]); cmb = N.new('ShaderNodeCombineColor')
    L(nn.outputs[0], cmb.inputs[0]); L(nn.outputs[2], cmb.inputs[2])
    if dx: inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; L(nn.outputs[1], inv.inputs[1]); L(inv.outputs[0], cmb.inputs[1])
    else: L(nn.outputs[1], cmb.inputs[1])
    nm = N.new('ShaderNodeNormalMap'); L(cmb.outputs[0], nm.inputs['Color']); L(nm.outputs[0], b.inputs['Normal'])
    L(orm.outputs[2], b.inputs['Metallic'])
    col, rough = t['bc'].outputs[0], orm.outputs[1]
    if vcol:                                                                  # M_MineSurface: R wet, G soot, B puddle
        va = N.new('ShaderNodeVertexColor'); va.layer_name = 'Col'; vs = N.new('ShaderNodeSeparateColor'); L(va.outputs[0], vs.inputs[0])
        sq = N.new('ShaderNodeMix'); sq.data_type = 'RGBA'; sq.blend_type = 'MULTIPLY'; sq.inputs['Factor'].default_value = 1; L(col, sq.inputs[6]); L(col, sq.inputs[7])
        wet = N.new('ShaderNodeMix'); wet.data_type = 'RGBA'; L(vs.outputs[0], wet.inputs['Factor']); L(col, wet.inputs[6]); L(sq.outputs[2], wet.inputs[7])
        soot = N.new('ShaderNodeMix'); soot.data_type = 'RGBA'; L(vs.outputs[1], soot.inputs['Factor']); L(wet.outputs[2], soot.inputs[6]); soot.inputs[7].default_value = (0.016, 0.015, 0.014, 1)
        r1 = N.new('ShaderNodeMix'); L(vs.outputs[0], r1.inputs['Factor']); L(rough, r1.inputs[2]); r1.inputs[3].default_value = 0.15
        r2 = N.new('ShaderNodeMix'); L(vs.outputs[1], r2.inputs['Factor']); L(r1.outputs[0], r2.inputs[2]); r2.inputs[3].default_value = 0.95
        r3 = N.new('ShaderNodeMix'); L(vs.outputs[2], r3.inputs['Factor']); L(r2.outputs[0], r3.inputs[2]); r3.inputs[3].default_value = 0.06
        col, rough = soot.outputs[2], r3.outputs[0]
    L(col, b.inputs['Base Color']); L(rough, b.inputs['Roughness']); return m
def kit(s, vcol=False): return texset('M_Mine' + s, *(os.path.join(KT, 'T_Mine%s_%s.png' % (s, k)) for k in ('BC', 'ORM', 'N')), vcol=vcol)
def glow(name, col, strength):
    m, nt, b = newmat(name); b.inputs['Base Color'].default_value = col + (1,); b.inputs['Emission Color'].default_value = col + (1,); b.inputs['Emission Strength'].default_value = strength; return m
def beam(name, col, strength, noise_tex):
    """M_RevealShaft: additive, fades at both ends (V) and at grazing angles (soft edges), noise pans up."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links.new
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); add = N.new('ShaderNodeAddShader'); em = N.new('ShaderNodeEmission'); tr = N.new('ShaderNodeBsdfTransparent')
    em.inputs['Color'].default_value = col + (1,); L(em.outputs[0], add.inputs[0]); L(tr.outputs[0], add.inputs[1]); L(add.outputs[0], out.inputs[0])
    uv = N.new('ShaderNodeUVMap'); sep = N.new('ShaderNodeSeparateXYZ'); L(uv.outputs[0], sep.inputs[0])
    def mth(op, a, b=None):
        n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = True
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    v = sep.outputs[1]; ends = mth('MULTIPLY', mth('MULTIPLY', v, 6.0), mth('POWER', mth('SUBTRACT', 1.0, v), 1.6))
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5; facing = mth('POWER', mth('SUBTRACT', 1.0, lw.outputs['Facing']), 2.0)
    tx = N.new('ShaderNodeTexImage'); tx.image = img(noise_tex, 'Non-Color'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (3, 0.7, 1)
    L(uv.outputs[0], mp.inputs[0]); L(mp.outputs[0], tx.inputs[0]); nz = mth('ADD', 0.35, mth('MULTIPLY', tx.outputs[0], 1.1))
    L(mth('MULTIPLY', mth('MULTIPLY', mth('MULTIPLY', ends, facing), nz), strength), em.inputs['Strength'])
    return m
MAT = {'M_MineRock': kit('Rock', True), 'M_MineOak': kit('Oak'), 'M_MineIron': kit('Iron'), 'M_MineOre': kit('Ore'),
       'M_MineGlow': glow('M_MineGlow', (1.0, 0.55, 0.2), 3.0), 'M_RevealGlow': glow('M_RevealGlow', (1.0, 0.72, 0.38), 1.6),
       'M_MineRope': texset('M_MineRope', *(os.path.join(T, 'T_MineRope_%s.png' % k) for k in ('BC', 'ORM', 'N')), uvscale=(1, 1 / 0.36)),
       'M_Ulfberht': texset('M_Ulfberht', *(os.path.join(T, 'T_Ulfberht_%s.png' % k) for k in ('BC', 'ORM', 'N'))),
       'M_RevealShaft': beam('M_RevealShaft', (1.0, 0.8, 0.5), 0.12, os.path.join(T, 'T_RevealNoise.png')),
       'M_RevealMotes': None}
def motes_mat():
    m = bpy.data.materials.new('M_RevealMotes'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links.new
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); mx = N.new('ShaderNodeMixShader'); em = N.new('ShaderNodeEmission'); tr = N.new('ShaderNodeBsdfTransparent')
    em.inputs['Color'].default_value = (1.0, 0.85, 0.55, 1); em.inputs['Strength'].default_value = 25.0
    uv = N.new('ShaderNodeUVMap'); vm = N.new('ShaderNodeVectorMath'); vm.operation = 'DISTANCE'; vm.inputs[1].default_value = (0.5, 0.5, 0); L(uv.outputs[0], vm.inputs[0])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.5; mr.inputs['From Max'].default_value = 0.0; L(vm.outputs['Value'], mr.inputs['Value'])
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.5; L(mr.outputs[0], pw.inputs[0])
    L(pw.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs[0]); return m
MAT['M_RevealMotes'] = motes_mat()
def vein_mat():                                                               # M_RevealVein: the ore set + emissive = vertex colour R^2
    m = kit('Ore'); m.name = 'M_RevealVein'; nt = m.node_tree; N = nt.nodes; L = nt.links.new; b = N['Principled BSDF']
    va = N.new('ShaderNodeVertexColor'); va.layer_name = 'Col'; sp = N.new('ShaderNodeSeparateColor'); L(va.outputs[0], sp.inputs[0])
    sq = N.new('ShaderNodeMath'); sq.operation = 'POWER'; sq.inputs[1].default_value = 2.0; L(sp.outputs[0], sq.inputs[0])
    st = N.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 6.0; L(sq.outputs[0], st.inputs[0])
    b.inputs['Emission Color'].default_value = (1.0, 0.72, 0.38, 1); L(st.outputs[0], b.inputs['Emission Strength']); return m
MAT['M_RevealVein'] = vein_mat()
m, nt, b = newmat('M_InfoCard'); cardtex = os.path.join(T, 'T_InfoCard_Ulfberht.png')
if os.path.exists(cardtex):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(cardtex, 'sRGB'); nt.links.new(t.outputs[0], b.inputs['Base Color']); nt.links.new(t.outputs[0], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 0.35; b.inputs['Roughness'].default_value = 0.8
MAT['M_InfoCard'] = m
def import_fbx(name):
    bpy.ops.import_scene.fbx(filepath=os.path.join(KF, name + '.fbx')); o = bpy.context.selected_objects[0]; o.name = name; return o
def dress(o):
    for i, s in enumerate(o.data.materials):
        key = s.name.split('.')[0] if s else ''
        if key in MAT: o.data.materials[i] = MAT[key]
for o in list(O):
    if o.type == 'MESH': dress(o); o.hide_render = True
def show(*names):
    for n in names: O[n].hide_render = False
def place(name, loc, rz=0.0, s=None):
    o = O[name]; o.location = loc; o.rotation_euler = (0, 0, math.radians(rz)); o.hide_render = False
    if s: o.scale = s
    return o
def dup(name, loc, rz=0.0):
    o = O[name].copy(); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, math.radians(rz)); o.hide_render = False; return o
def lamp(p, watts, col=(1.0, 0.62, 0.3), r=0.03):
    L = bpy.data.objects.new('L', bpy.data.lights.new('L', 'POINT')); L.data.energy = watts; L.data.color = col; L.data.shadow_soft_size = r; L.location = p; sc.collection.objects.link(L); return L
def lantern(p, watts=60):
    o = import_fbx('SM_Mine_Lantern'); dress(o); o.location = p; o.visible_shadow = False;   # the lamp sits inside the glass lamp(Vector(p) + Vector((0, 0, 0.2)), watts); return o
def hero(loc, rz=0.0, crouch=0.0):
    """Stand-in figure, 1.8 m, cloth-grey."""
    mm, _, bb = newmat('hero'); bb.inputs['Base Color'].default_value = (0.16, 0.14, 0.12, 1); bb.inputs['Roughness'].default_value = 0.8
    parts = [((0, 0, 1.62), 0.11, 0.0), ((0, 0, 1.28), 0.19, 0.28), ((0, 0, 0.92), 0.16, 0.18)]
    objs = []
    for (x, yy, zz), r, h in parts:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, yy, zz - crouch)) if h == 0 else bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h * 2, location=(x, yy, zz - crouch))
        objs.append(bpy.context.active_object)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.85, location=(0, s * 0.1, 0.43 - crouch * 0.5)); objs.append(bpy.context.active_object)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.62, location=(0.12, s * 0.27, 1.2 - crouch), rotation=(s * 0.25, 0.6, 0)); objs.append(bpy.context.active_object)
    for o in objs: o.data.materials.append(mm); bpy.ops.object.shade_smooth()
    root = bpy.data.objects.new('hero', None); sc.collection.objects.link(root)
    for o in objs: o.parent = root
    root.location = loc; root.rotation_euler.z = math.radians(rz); return root
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
def look(p, t, lens=35):
    cam.location = p; cd.lens = lens; cam.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
ball_at = None
SHAFT = Vector((3.9, 0, 0)); DRUM_Z = 1.15
def top_set(bucket_drop=0.0):
    show('SM_MineShaft_Top'); place('SM_MineShaft_Cribbing_Top', SHAFT); place('SM_MineShaft_Collar', SHAFT)
    place('SM_MineWindlass_Drum', SHAFT + Vector((0.22, 0, DRUM_Z))).rotation_euler.y = bucket_drop / 0.2
    bz = DRUM_Z - 0.36 - 1.83 - bucket_drop; place('SM_MineBucket', SHAFT + Vector((0, 0, bz)))
    place('SM_MineRope_1m', SHAFT + Vector((0, 0, bz + 1.83)), 0, (1, 1, 0.36 + bucket_drop))
    place('SM_MineGate_Bulkhead', (1.2, 0, 0)); place('SM_MineGate_Door', (1.2, -0.62, 0), 95)
    df = import_fbx('SM_Mine_DoorFrame'); dress(df); df.location = (1.2, 0, 0)
    return SHAFT + Vector((0, 0, bz))
if VIEW == 'reveal':
    ch = import_fbx('SM_Mine_Chamber'); dress(ch)
    v = place('SM_Mine_OreVein_Cracked', (6.5, -4.75, 0), 90)
    sw = place('SM_Ulfberht', (6.5, -3.75, 1.42), 0); sw.rotation_euler = (0, math.radians(-8), math.radians(62))
    place('SM_Reveal_LightShaft', (6.5, -3.75, 0.02)); place('SM_Reveal_Motes', (6.5, -3.75, 0.0))
    for n in ('SM_Reveal_LightShaft', 'SM_Reveal_Motes', 'SM_InfoCard'):          # VFX are camera-only (in UE they don't light the cave)
        O[n].visible_diffuse = O[n].visible_glossy = O[n].visible_shadow = O[n].visible_transmission = False
    place('SM_InfoCard', (7.7, -3.3, 0.75), 143, (1, 0.55, 0.55))
    lamp((6.5, -3.45, 1.7), 70, (1.0, 0.8, 0.55), 0.15); lamp((6.5, -4.3, 1.2), 35, (1.0, 0.7, 0.38), 0.3)   # the find's light + cleft bounce
    lantern((3.5, -3.6, 2.6)); lantern((10.5, 3.9, 2.4)); lantern((7.0, 4.2, 2.5))
    ball_at = Vector((5.9, -2.9, 0.9))
    sp = bpy.data.objects.new('K', bpy.data.lights.new('K', 'SPOT')); sp.data.energy = 120; sp.data.spot_size = math.radians(25); sp.data.color = (1.0, 0.9, 0.75)
    sp.location = (5.0, -1.6, 2.4); sp.rotation_euler = (Vector((6.5, -3.75, 1.4)) - sp.location).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(sp)   # key: makes the blade flash
    look((5.0, -1.2, 1.5), (6.75, -3.8, 1.3), 30)
elif VIEW == 'room':
    b0 = top_set(); hero((2.1, 0.5, 0), -20)
    lantern((2.1, -1.5, 2.2)); lantern((5.5, 1.4, 2.2))
    ball_at = Vector((2.5, -1.2, 0.9)); look((1.55, 2.05, 1.8), (3.9, -0.35, 0.3), 20)
elif VIEW == 'ride':
    b0 = top_set(6.5); h = hero(b0 + Vector((0.3, 0, 0.07)), 180)
    L = lantern(b0 + Vector((0.0, 0.42, 1.5)), 40)                          # the bucket's own lamp, hung on the bail
    lantern(SHAFT + Vector((-1.0, 1.0, -3.0)), 25)
    ball_at = b0 + Vector((-0.35, -0.3, 0.6)); look(b0 + Vector((-0.75, -0.55, 3.4)), b0 + Vector((0.1, 0.05, 0.6)), 16)
elif VIEW == 'door':
    for n in ('SM_Mine_Tunnel_Straight',):
        t = import_fbx(n); dress(t); t.location = (-2.0, 0, 0)
        t2 = import_fbx(n); dress(t2); t2.location = (2.0, 0, 0)
    place('SM_MineGate_Bulkhead', (1.2, 0, 0), 180); place('SM_MineGate_Door', (1.2, 0.62, 0), 215)   # strapped front to the player, swinging away
    df = import_fbx('SM_Mine_DoorFrame'); dress(df); df.location = (1.2, 0, 0)
    lantern((0.4, 0.95, 1.75)); lamp((3.2, 0, 1.4), 30, (1.0, 0.6, 0.3), 0.3)
    hero((-0.4, 0.35, 0), 0); ball_at = Vector((0.3, -0.9, 0.9)); look((-3.2, -0.9, 1.65), (1.2, -0.15, 1.15), 26)
elif VIEW == 'swordcard':                                                     # the card's picture: the sword lying flat, transparent
    sw = place('SM_Ulfberht', (-0.235, 0, 0)); sw.rotation_euler = (0, math.radians(-90), 0)   # hilt left, front (+VLFBERH+T) to the camera
    cd.type = 'ORTHO'; cd.ortho_scale = 1.16; look((0, 2, 0.0), (0, 0, 0)); sc.render.film_transparent = True
    for p, e in (((-0.6, -1.5, 1.2), 30), ((0.8, -1.2, -0.6), 12), ((0.2, 1.4, 1.0), 16)):
        a = bpy.data.objects.new('A', bpy.data.lights.new('A', 'AREA')); a.data.energy = e; a.data.size = 1.5; a.location = p; sc.collection.objects.link(a)
        a.rotation_euler = (Vector((0, 0, 0)) - Vector(p)).to_track_quat('-Z', 'Y').to_euler()
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.25
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'; pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = True
sc.cycles.use_denoising = True; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x, sc.render.resolution_y = (2400, 800) if VIEW == 'swordcard' else (int(os.environ.get('RES_X', '1600')), int(os.environ.get('RES_Y', '1000')))
os.makedirs(os.path.join(D, 'out', 'renders'), exist_ok=True)
out = os.path.join(D, 'out', 'renders', os.environ.get('LD_NAME', 'ld_' + VIEW) + '.png')
sc.view_settings.view_transform = 'AgX'
if ball_at is not None:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=48, ring_count=24, location=ball_at); bpy.ops.object.shade_smooth()
    gm, _, gb = newmat('grey18'); gb.inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1); gb.inputs['Roughness'].default_value = 0.5
    ball = bpy.context.active_object; ball.data.materials.append(gm); bpy.context.view_layer.update()
    if os.environ.get('EXPOSURE'): sc.view_settings.exposure = float(os.environ['EXPOSURE'])
    else:
        MODE = os.environ.get('METER_MODE', 'median'); target = float(os.environ.get('METER', '62' if MODE == 'median' else '96')); uvp = bpy_extras.object_utils.world_to_camera_view(sc, cam, ball.location)
        tmp = os.path.join(D, 'out', '_meter.png'); sc.render.filepath = tmp; sc.cycles.samples = 16; sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0.0
        for it in range(6):
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
            px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H, W, 4)
            cx, cy = int(uvp.x * W), int(uvp.y * H); v = float(px[cy - 3:cy + 4, cx - 3:cx + 4, :3].mean()) * 255
            if MODE == 'median': v = float(np.median(px[:, :, :3].mean(-1))) * 255   # tight caves: the ball often sits in a shadow
            print('METER grey ball %.0f sRGB at exposure %.2f' % (v, sc.view_settings.exposure), flush=True)
            if abs(v - target) < 4: break
            Lf = lambda s: ((s / 255 + 0.055) / 1.055) ** 2.4
            sc.view_settings.exposure += math.log2(Lf(target) / max(Lf(min(max(v, 1), 254)), 1e-5)) * (1.0 if v < 250 else 1.6)
        sc.view_settings.view_transform = 'AgX'
if ball_at is not None and os.environ.get('SHOW_BALL') != '1': ball.hide_render = True
sc.cycles.samples = int(os.environ.get('LD_SAMPLES', '128')); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
print('LOOKDEV OK', out, 'exposure %.2f' % sc.view_settings.exposure, flush=True)
