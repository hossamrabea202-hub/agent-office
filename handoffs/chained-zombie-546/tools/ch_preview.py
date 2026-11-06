# blender -b --factory-startup -P ch_preview.py -- <out_dir> <shots.json|preset> [spp] [res_x]
# #546 lookdev on the REAL zombie mesh + UE re-exported clips: the same chain and melt maths as the Blueprint and the HLSL.
# Locked exposure, 18 % grey ball in shot, one key = the wall torch at 1800 K above him, one dim cold fill from the door.
import bpy, bmesh, sys, os, math, json, importlib.util
from mathutils import Vector, Matrix, Quaternion
Z = os.path.dirname(os.path.abspath(__file__)); a = sys.argv[sys.argv.index('--') + 1:]
OUT = a[0]; PRE = a[1]; SPP = int(a[2]) if len(a) > 2 else 24; RX = int(a[3]) if len(a) > 3 else 960; os.makedirs(OUT, exist_ok=True)
HAND = 'C:/Users/hossam.rabea/agent-office/handoffs/chained-zombie-546/fbx/'
PRESETS = {
 'thrash': [dict(n='thrash_%03d' % f, clip='CH_Thrash', f=f) for f in (1, 24, 42, 80, 110, 136, 225)],
 'beats': [dict(n='a_hold', clip='CH_Thrash', f=1), dict(n='b_lunge', clip='CH_Thrash', f=42), dict(n='c_cut', clip='CH_Slice_L', f=10, cut='L', age=0.3), dict(n='d_free', clip='CH_Free_L', f=20, cut='L', age=2.0), dict(n='e_rake', clip='CH_Claw_L', f=18, cut='L', age=3.0),
           dict(n='f_melt15', clip='CH_Death_L', f=30, cut='L', age=4.0, t=0.15), dict(n='g_melt35', clip='CH_Death_L', f=75, cut='L', age=5.0, t=0.35), dict(n='h_melt55', clip='CH_Death_L', f=130, cut='L', age=6.0, t=0.55), dict(n='i_melt75', clip='CH_Death_L', f=190, cut='L', age=7.0, t=0.75), dict(n='j_melt92', clip='CH_Death_L', f=211, cut='L', age=8.0, t=0.92), dict(n='k_after', clip='CH_Death_L', f=211, cut='L', age=30.0, t=1.0, cool=0.9)],
 'iron': [dict(n='iron_close', clip='CH_Thrash', f=42, cam=((1.15, -0.55, 1.75), (0.95, 0.3, 1.62), 60))],
}
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def mat_pbr(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree, m.node_tree.nodes['Principled BSDF']
# ---- the zombie
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=Z + '/fbx_mesh/SK_Zombie.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
new = [o for o in bpy.data.objects if o not in before]; ARM = next(o for o in new if o.type == 'ARMATURE'); MESHES = [o for o in new if o.type == 'MESH']
mw = ARM.matrix_world.copy(); ARM.parent = None; ARM.matrix_world = mw
for o in new:
    if o.type == 'EMPTY': bpy.data.objects.remove(o, do_unlink=True)
def skin_mat(tex, nameout):
    m, nt, b = mat_pbr(nameout); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexImage'); tc.image = bpy.data.images.load(Z + '/tex_ch/%s.tga' % tex)
    nm = N.new('ShaderNodeTexImage'); nm.image = bpy.data.images.load(Z + '/tex_ch/T_Zombie_N.tga', check_existing=True); nm.image.colorspace_settings.name = 'Non-Color'
    nn = N.new('ShaderNodeNormalMap'); L.new(nm.outputs[0], nn.inputs['Color']); L.new(nn.outputs[0], b.inputs['Normal'])
    mk = N.new('ShaderNodeAttribute'); mk.attribute_name = 'melt'; ht = N.new('ShaderNodeAttribute'); ht.attribute_name = 'glow'
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(mk.outputs['Fac'], mx.inputs[0]); L.new(tc.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.09, 0.05, 0.03, 1); L.new(mx.outputs[2], b.inputs['Base Color'])
    rg = N.new('ShaderNodeMapRange'); L.new(mk.outputs['Fac'], rg.inputs[0]); rg.inputs[3].default_value = 0.62; rg.inputs[4].default_value = 0.16; L.new(rg.outputs[0], b.inputs['Roughness'])
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.02, 0.008, 0.005); b.inputs['Specular IOR Level'].default_value = 0.35
    L.new(ht.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.0
    return m
MS = {'A': skin_mat('T_Zombie_A_BC', 'skinA'), 'B': skin_mat('T_Zombie_B_BC', 'skinB')}
for o in MESHES:
    for s in o.material_slots:
        s.material = MS['A' if '1' in (s.material.name if s.material else '') else 'B']
# ---- iron
def iron_mat():
    m, nt, b = mat_pbr('iron'); N = nt.nodes; L = nt.links; v = N.new('ShaderNodeVertexColor'); v.layer_name = 'Col'; sp = N.new('ShaderNodeSeparateColor'); L.new(v.outputs[0], sp.inputs[0])
    tx = N.new('ShaderNodeTexCoord'); no = N.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 6.0; no.inputs['Detail'].default_value = 7.0; L.new(tx.outputs['UV'], no.inputs['Vector'])
    add = N.new('ShaderNodeMath'); add.operation = 'ADD'; L.new(sp.outputs[0], add.inputs[0]); mp = N.new('ShaderNodeMapRange'); mp.inputs[1].default_value = 0.0; mp.inputs[2].default_value = 1.0; mp.inputs[3].default_value = -0.28; mp.inputs[4].default_value = 0.28; L.new(no.outputs[0], mp.inputs[0]); L.new(mp.outputs[0], add.inputs[1])
    r1 = N.new('ShaderNodeMapRange'); r1.interpolation_type = 'SMOOTHSTEP'; r1.inputs[1].default_value = 0.42; r1.inputs[2].default_value = 0.72; L.new(add.outputs[0], r1.inputs[0])
    b1 = N.new('ShaderNodeMapRange'); b1.interpolation_type = 'SMOOTHSTEP'; b1.inputs[1].default_value = 0.25; b1.inputs[2].default_value = 0.7; L.new(sp.outputs[1], b1.inputs[0])
    c1 = N.new('ShaderNodeMix'); c1.data_type = 'RGBA'; L.new(r1.outputs[0], c1.inputs[0]); c1.inputs[6].default_value = (0.046, 0.041, 0.038, 1); c1.inputs[7].default_value = (0.14, 0.05, 0.018, 1)
    c2 = N.new('ShaderNodeMix'); c2.data_type = 'RGBA'; L.new(b1.outputs[0], c2.inputs[0]); L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (0.56, 0.55, 0.53, 1); L.new(c2.outputs[2], b.inputs['Base Color'])
    r2 = N.new('ShaderNodeMix'); r2.data_type = 'FLOAT'; L.new(r1.outputs[0], r2.inputs[0]); r2.inputs[2].default_value = 0.56; r2.inputs[3].default_value = 0.97
    r3 = N.new('ShaderNodeMix'); r3.data_type = 'FLOAT'; L.new(b1.outputs[0], r3.inputs[0]); L.new(r2.outputs[0], r3.inputs[2]); r3.inputs[3].default_value = 0.3; L.new(r3.outputs[0], b.inputs['Roughness']); L.new(b1.outputs[0], b.inputs['Metallic'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.002; L.new(no.outputs[0], bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal'])
    return m
IRON = iron_mat()
def load_sm(name):
    b4 = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=HAND + name + '.fbx'); o = next(x for x in bpy.data.objects if x not in b4); me = o.data; mw = o.matrix_world.copy(); me.transform(mw); bpy.data.objects.remove(o, do_unlink=True); me.update()
    bb = [v.co for v in me.vertices]; return me
ML, MC, MA, MP = load_sm('SM_ChainLink'), load_sm('SM_ChainCuff'), load_sm('SM_ChainAnchor'), load_sm('SM_MeltPool')
def extent(me): return max(max(v.co[i] for v in me.vertices) - min(v.co[i] for v in me.vertices) for i in range(3))
kl = 0.12 / extent(ML); print('LINK SCALE', kl)
for me in (ML, MC, MA, MP): me.transform(Matrix.Scale(kl, 4)); me.update(); me.materials.append(IRON) if me is not MP else None
print('FBX axes: link extents', [round(max(v.co[i] for v in ML.vertices) - min(v.co[i] for v in ML.vertices), 3) for i in range(3)])
def inst(me, name):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o
# ---- the room: real sizes from the castle scan: wall behind him at y=0.5, floor z=0, torch high on the wall
def stone(name, tile, base):
    m, nt, b = mat_pbr(name); N = nt.nodes; L = nt.links; tx = N.new('ShaderNodeTexCoord'); br = N.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = tile; br.inputs['Mortar Size'].default_value = 0.012; br.offset = 0.5; br.inputs['Brick Width'].default_value = 0.7; br.inputs['Row Height'].default_value = 0.3
    br.inputs['Color1'].default_value = base; br.inputs['Color2'].default_value = tuple(c * 0.72 for c in base[:3]) + (1,); br.inputs['Mortar'].default_value = tuple(c * 0.45 for c in base[:3]) + (1,); mpn = N.new('ShaderNodeMapping'); mpn.inputs['Rotation'].default_value = (math.radians(90), 0, 0) if name == 'wall' else (0, 0, 0); L.new(tx.outputs['Object'], mpn.inputs['Vector']); L.new(mpn.outputs[0], br.inputs['Vector'])
    no = N.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 14.0; no.inputs['Detail'].default_value = 9.0; L.new(tx.outputs['Object'], no.inputs['Vector'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 0.65; L.new(br.outputs['Color'], mx.inputs[6]); L.new(no.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.85
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; bp.inputs['Distance'].default_value = 0.02; L.new(no.outputs[0], bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal']); return m
def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size; bpy.ops.object.transform_apply(scale=True); o.data.materials.append(mat); return o
WM = stone('wall', 3.2, (0.33, 0.31, 0.27, 1)); FM = stone('floor', 2.0, (0.20, 0.185, 0.165, 1))
box('wall', (0, 0.72, 2.25), (5.2, 0.44, 4.5), WM); box('floor', (0, -2.0, -0.05), (5.2, 6, 0.1), FM); box('wallW', (-2.3, -2, 2.25), (0.44, 6, 4.5), WM); box('wallE', (2.3, -2, 2.25), (0.44, 6, 4.5), WM); box('roof', (0, -2, 4.6), (5.2, 6, 0.2), WM)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(-1.45, 0.25, 0.09)); gb = bpy.context.object; gm, _, gp = mat_pbr('grey18'); gp.inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1); gp.inputs['Roughness'].default_value = 0.5; gb.data.materials.append(gm); bpy.ops.object.shade_smooth()
def kelvin(k):
    t = k / 100.0; r = 1.0 if t <= 66 else 1.292936 * (t - 60) ** -0.1332; g = (0.390082 * math.log(t) - 0.631841) if t <= 66 else 1.129891 * (t - 60) ** -0.0755; bl = 0.0 if t <= 19 else 0.543207 * math.log(t - 10) - 1.196254
    return tuple(max(0, min(1, x)) ** 2.2 for x in (r, g, bl))
tl = bpy.data.lights.new('torch', 'POINT'); tl.energy = 240.0; tl.color = kelvin(1800); tl.shadow_soft_size = 0.07; to = bpy.data.objects.new('torch', tl); sc.collection.objects.link(to); to.location = (0.0, 0.40, 3.05)
fl = bpy.data.lights.new('door', 'AREA'); fl.energy = 34.0; fl.color = (0.60, 0.72, 1.0); fl.size = 1.4; fo = bpy.data.objects.new('door', fl); sc.collection.objects.link(fo); fo.location = (0.25, -4.6, 1.3); fo.rotation_euler = (math.radians(90), 0, 0)
hl = bpy.data.lights.new('heat', 'POINT'); hl.energy = 0.0; hl.color = kelvin(1900); hl.shadow_soft_size = 0.12; ho = bpy.data.objects.new('heat', hl); sc.collection.objects.link(ho)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.014, 0.018, 1)
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'; sc.cycles.max_bounces = 4; sc.render.resolution_x = RX; sc.render.resolution_y = int(RX * 9 / 16)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0; sc.render.image_settings.file_format = 'PNG'
# ---- chain maths: the same as the Blueprint (blender metres)
WALLY = 0.5
PLATE = {0: Vector((1.02, WALLY, 1.838)), 1: Vector((-1.02, WALLY, 1.838)), 2: Vector((0.56, WALLY, 0.318)), 3: Vector((-0.56, WALLY, 0.318))}
RING = Vector((0, -0.052, -0.078)); LEN = [0.60, 0.60, 0.43, 0.43]; CNT = [7, 7, 5, 5]; BONES = ['LeftForeArm', 'RightForeArm', 'LeftLeg', 'RightLeg']; ALONG = [0.285, 0.285, 0.43, 0.43]; CS = [1.0, 1.0, 0.72, 0.72]; LUG = [0.167, 0.167, 0.12, 0.12]
ANCH = [PLATE[i] + RING for i in range(4)]
AO = []; CO = []; LO = []
RA = Matrix(((0, 1, 0), (-1, 0, 0), (0, 0, 1)))        # plate: local X out of the wall = world -Y, local Z up; local Y = world +X
for i in range(4):
    o = inst(MA, 'anchor%d' % i); o.matrix_world = Matrix.Translation(PLATE[i]) @ RA.to_4x4(); AO.append(o); c = inst(MC, 'cuff%d' % i); CO.append(c); LO.append([inst(ML, 'l%d_%d' % (i, j)) for j in range(CNT[i])])
for o in AO: o.visible_shadow = True
FWD = Vector((0, -1, 0))
def rot_xz(x, z):
    X = x.normalized(); Y = z.cross(X).normalized(); Zz = X.cross(Y); return Matrix((X, Y, Zz)).transposed().to_4x4()
def seg(links, A, E, L):
    n = len(links); d = (E - A).length; s = math.sqrt(max(0.0, 3.0 * d * max(L - d, 0.0) / 8.0))
    def P(u): return A + (E - A) * u - Vector((0, 0, 1)) * 4.0 * s * u * (1 - u)
    for j, o in enumerate(links):
        p0, p1 = P(j / n), P((j + 1) / n); v = p1 - p0; zc = v.cross(FWD) if j % 2 else FWD
        o.matrix_world = Matrix.Translation((p0 + p1) * 0.5) @ rot_xz(v, zc); o.hide_render = False
def cuff_pose(i):
    pb = ARM.pose.bones[BONES[i]]; R = (ARM.matrix_world @ pb.matrix).to_quaternion() @ (ARM.matrix_world @ pb.bone.matrix_local).to_quaternion().inverted()
    h = ARM.matrix_world @ pb.head; t = ARM.matrix_world @ pb.tail; d = (t - h).normalized(); b = (pb.bone.tail_local - pb.bone.head_local); bw = (ARM.matrix_world.to_3x3() @ (b)).normalized()
    rest_dir = (ARM.matrix_world.to_quaternion() @ b).normalized(); rest = rot_xz(rest_dir, Vector((0, -1, 0))).to_quaternion(); q = R @ rest
    pos = h + d * ALONG[i]; return pos, q
def set_chains(cut, age, t):
    for i in range(4):
        pos, q = cuff_pose(i); up = q @ Vector((0, 0, 1)); lug = pos - up * LUG[i]; rel = (cut == 'L' and i == 0) or (cut == 'R' and i == 1)
        CO[i].matrix_world = Matrix.Translation(pos) @ q.to_matrix().to_4x4() @ Matrix.Scale(CS[i], 4); CO[i].hide_render = False
        wrist_gone = t is not None and t > 0.30; ankle_gone = t is not None and t > 0.82
        if rel:
            k = 4; L5 = LEN[i] * 0.571; end = ANCH[i] + Vector((0, 0, -L5)) + FWD * L5 * 0.26 * math.sin(age * 4.7) * math.exp(-age * 0.62); seg(LO[i][:4], ANCH[i], end, L5); LO[i][4].hide_render = True
            if wrist_gone:
                CO[i].matrix_world = Matrix.Translation(Vector((pos.x * 0.6, -0.1, 0.05))) @ Matrix.Rotation(1.5, 4, 'Y') @ Matrix.Scale(CS[i], 4)
                for o in LO[i][5:]: o.hide_render = True
            else: seg(LO[i][5:], lug, lug - Vector((0, 0, 0.17)) + FWD * 0.03, 0.175)
        elif (i < 2 and wrist_gone) or (i >= 2 and ankle_gone):
            te = t - (0.30 if i < 2 else 0.82); ag = te * 8.5; end = ANCH[i] + Vector((0, 0, -LEN[i])) + FWD * LEN[i] * 0.26 * math.sin(ag * 4.7) * math.exp(-ag * 0.62); seg(LO[i], ANCH[i], end, LEN[i]); CO[i].matrix_world = Matrix.Translation(end - Vector((0, 0, LUG[i]))) @ rot_xz(Vector((1, 0, 0)), Vector((0, 1, 0))) @ Matrix.Scale(CS[i], 4)
        else: seg(LO[i], ANCH[i], lug, LEN[i])
# ---- the melt: the HLSL line for line. Blender metres -> game cm: P = (100 x, -100 y, 100 z), core (0, -18 cm)
def melt_v(x, y, z, tt, G=0.0):
    sat = lambda v: max(min(v, 1.0), 0.0); sst = lambda e0, e1, v: (lambda u: u * u * (3 - 2 * u))(sat((v - e0) / (e1 - e0)))
    dx, dy = x, y - 18.0; r = math.hypot(dx, dy) + 0.001; wr = sat((r - 34.0) / 60.0); wilt = sst(0.02, 0.42, tt); P0 = max(z - G, 0.0); H = max(P0 - wr * wr * wilt * 95.0, 0.0)
    n1 = math.sin(x * 0.031 + y * 0.027) + 0.5 * math.sin(x * 0.067 - y * 0.053 + 1.7); ee = tt * tt * (2.1 - 1.1 * tt); F = 228.0 * (1.0 - ee) + 9.0 * n1 * sat(tt * 6) * sat((1 - tt) * 6)
    k = 16.0; sm = -k * math.log(math.exp(-H / k) + math.exp(-max(F, 0) / k)); exc = max(H - F, 0.0); comp = 0.07 + (0.01 - 0.07) * tt; nh = sm + exc * comp
    band = sat((H - (F - 70.0)) / 70.0) if H < F else 1.0; soft = sat(tt * 9); lob = 0.5 + 0.5 * math.sin(math.atan2(dy, dx) * 5.0 + n1 * 1.5); nh -= lob * lob * band * band * 16.0 * soft; nh = max(nh, 0.6 + 2.0 * (1 - tt))
    f = (34.0 + (r - 34.0) * (1.0 - 0.8 * wilt)) / r if r > 34.0 else 1.0; f *= 1.0 + (0.55 - 1.0) * sat(exc / 60.0); cd_ = (H - F) / 22.0; f *= 1.0 + 0.18 * math.exp(-cd_ * cd_) * soft; f *= 1.0 + 0.85 * sat(1.0 - nh / 22.0) * sst(0.55, 1.0, tt)
    d = H - F; heat = math.exp(-(d * d) / (2 * 9.0 * 9.0)); grain = 0.5 + 0.5 * math.sin(x * 0.35 + z * 0.27) * math.sin(y * 0.41 - z * 0.23); cap = 0.03 if d > 0 else 0.0; below = math.exp(d / 30.0) * 0.06 * grain if d < 0 else 0.0; arm = wr * wilt * (1 - wilt) * 0.45 * grain
    kk = (heat * (0.6 + 0.4 * grain) + cap + below + arm) * sat(tt * 14) * sat((1 - tt) * 5); h2 = sat(heat * heat); col = (1.0, 0.13 + 0.37 * h2, 0.015 + 0.105 * h2)
    return dx * f, dy * f + 18.0, nh + G, max(sat((H - F + 24.0) / 32.0), wr * wilt), tuple(c * kk * 3.2 for c in col)
RENDER_O = {}
def bake_melt(t):
    dg = bpy.context.evaluated_depsgraph_get()
    for o in MESHES:
        o.hide_render = True
        old = RENDER_O.pop(o.name, None)
        if old: me_old = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.meshes.remove(me_old)
        ev = o.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev, depsgraph=dg); me.transform(o.matrix_world); r = bpy.data.objects.new(o.name + '_r', me); sc.collection.objects.link(r); RENDER_O[o.name] = r
        am = me.attributes.new('melt', 'FLOAT', 'POINT'); ag = me.attributes.new('glow', 'FLOAT_COLOR', 'POINT')
        tt = t or 0.0
        for i, v in enumerate(me.vertices):
            x, y, z = v.co.x * 100, -v.co.y * 100, v.co.z * 100
            if tt > 0.0005:
                nx, ny, nz, mk, gl = melt_v(x, y, z, tt); v.co = (nx / 100, -ny / 100, nz / 100); am.data[i].value = mk; ag.data[i].color = (gl[0], gl[1], gl[2], 1)
            else: am.data[i].value = 0.0; ag.data[i].color = (0, 0, 0, 1)
        me.update(); me.shade_smooth() if hasattr(me, 'shade_smooth') else None
pool_o = inst(MP, 'pool'); pm, pn, pb = mat_pbr('pool'); pa = pn.nodes.new('ShaderNodeVertexColor'); pa.layer_name = 'Col'; pm.name = 'pool'; MP.materials.append(pm); ps = pn.nodes.new('ShaderNodeSeparateColor'); pn.links.new(pa.outputs[0], ps.inputs[0]); pr = pn.nodes.new('ShaderNodeMapRange'); pr.inputs[1].default_value = 0.35; pr.inputs[2].default_value = 0.8; pn.links.new(ps.outputs[2], pr.inputs[0]); pmx = pn.nodes.new('ShaderNodeMix'); pmx.data_type = 'RGBA'; pn.links.new(pr.outputs[0], pmx.inputs[0]); pmx.inputs[6].default_value = (0.30, 0.215, 0.115, 1); pmx.inputs[7].default_value = (0.075, 0.03, 0.02, 1); POOLMIX = pmx; pmh = pn.nodes.new('ShaderNodeMix'); pmh.data_type = 'RGBA'; pn.links.new(pmx.outputs[2], pmh.inputs[6]); pmh.inputs[7].default_value = (0.035, 0.018, 0.014, 1); pn.links.new(pmh.outputs[2], pb.inputs['Base Color']); PMH = pmh; pb.inputs['Base Color'].default_value = (0.035, 0.018, 0.014, 1); pb.inputs['Roughness'].default_value = 0.12
def set_pool(t, cool):
    if t is None or t < 0.12: pool_o.hide_render = True; return
    sg = min((t - 0.12) / 0.88, 1); s = 0.02 + 0.95 * sg * sg * (3 - 2 * sg); pool_o.hide_render = False; pool_o.matrix_world = Matrix.Translation((0, -0.18, 0.0)) @ Matrix.Scale(s, 4) @ Matrix.Diagonal((1, 1, 1 / max(s, 1e-3) * 1.0, 1))
    heat = 1.0 - (cool or 0.0); PMH.inputs[0].default_value = min(heat * 1.4, 1); pb.inputs['Roughness'].default_value = 0.42 + (0.12 - 0.42) * min(heat * 2, 1)
    pb.inputs['Emission Color'].default_value = (1.0, 0.13, 0.015, 1); pb.inputs['Emission Strength'].default_value = 0.35 * heat * heat
CL = {}
def put_clip(name, f):
    if name not in CL:
        b4 = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=Z + '/fbx_ch/%s.fbx' % name, automatic_bone_orientation=False, ignore_leaf_bones=False); nn = [x for x in bpy.data.objects if x not in b4]; src = next(x for x in nn if x.type == 'ARMATURE'); CL[name] = (src.animation_data.action, src.animation_data.action_slot if hasattr(src.animation_data, 'action_slot') else None, src.rotation_mode)
        for x in nn: bpy.data.objects.remove(x, do_unlink=True)
    act, slot, rm = CL[name]; ARM.rotation_mode = rm; ARM.animation_data_create(); ARM.animation_data.action = act
    if slot and hasattr(ARM.animation_data, 'action_slot'): ARM.animation_data.action_slot = slot
    sc.frame_set(int(act.frame_range[0]) + f - 1)
shots = PRESETS[PRE] if PRE in PRESETS else json.load(open(PRE))
DEFCAM = ((-1.25, -4.1, 1.15), (0.0, 0.1, 0.98), 30)
for sh in shots:
    put_clip(sh['clip'], sh['f']); bpy.context.view_layer.update(); t = sh.get('t'); set_chains(sh.get('cut'), sh.get('age', 0.0), t)
    for lst in LO:
        for o in lst: o.hide_render = o.hide_render or bool(sh.get('nochain'))
    for o in CO: o.hide_render = bool(sh.get('nochain'))
    for o in AO: o.hide_render = bool(sh.get('nochain'))
    bake_melt(t); set_pool(t, sh.get('cool'))
    if t:
        ee = t * t * (2.1 - 1.1 * t); ho.location = (0, -0.30, 0.12 + 2.05 * (1 - ee)); hl.energy = 16.0 * min(t * 8, 1) * (1.0 - (sh.get('cool') or 0.0))
    else: hl.energy = 0.0
    if t and t >= 1.0:
        for r in RENDER_O.values(): r.hide_render = True
    loc, tgt, lens = sh.get('cam', DEFCAM); cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    sc.render.filepath = os.path.join(OUT, sh['n'] + '.png'); bpy.ops.render.render(write_still=True); print('SHOT', sh['n'])
print('PREVIEW OK')
