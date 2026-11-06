# #543 textures (TGA PC). blender -b work/mine543.blend -P bake_mine543.py   -> work/out/tex/*.png  (env WORK, BAKE_RES, BAKE_SAMPLES)
# 1. T_Ulfberht_BC / _ORM / _N (+ _N_GL for Blender): a procedural shader on the sword, Cycles-baked to its UVs.
#    Blade: bright preserved steel (metal F0 ~0.60), long polishing scratches along the blade, grey patina clouds, a few
#    rust specks (metal 0), and the inlaid +VLFBERH+T in the fuller on the front, a lattice on the back (iron inlay:
#    darker, rougher, a hair proud). Guard + pommel: darker forged iron with more patina. Grip: dark leather with a wrap.
# 2. T_MineRope_BC / _ORM / _N: 3-strand hemp, tiles every 0.36 m along the rope (3 lays of 12 cm), 1 tile round it.
# 3. T_RevealNoise: tileable soft noise (R, G = two octaves) that the light shaft and the cleft glow pan through.
# ORM = R AO, G roughness, B metallic. N = DirectX (green down) for UE, like the #309 kit.
import bpy, numpy as np, math, os
D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath); T = os.path.join(D, 'out', 'tex'); os.makedirs(T, exist_ok=True)
SRC = os.path.join(D, 'src'); RES = int(os.environ.get('BAKE_RES', '2048')); BAL = 0.14
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'
pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = True
sc.cycles.samples = int(os.environ.get('BAKE_SAMPLES', '32'))

def save(name, arr):
    h, w = arr.shape[:2]; a = np.ones((h, w, 4), np.float32); a[:, :, :arr.shape[2]] = arr
    im = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(a.ravel()); im.filepath_raw = os.path.join(T, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    print('TEX', name, w, h, flush=True)
def pixels(im):
    a = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(a); return a.reshape(im.size[1], im.size[0], 4)

# ------------------------------------------------------------------------------------------------ 1. the sword
sw = bpy.data.objects['SM_Ulfberht']
for o in sc.objects: o.select_set(o is sw)
bpy.context.view_layer.objects.active = sw
m = bpy.data.materials.new('M_Ulfberht_bake'); m.use_nodes = True; sw.data.materials.clear(); sw.data.materials.append(m)
nt = m.node_tree; N = nt.nodes; L = nt.links.new; bs = N['Principled BSDF']; out = N['Material Output']
def node(t, **kw):
    n = N.new(t)
    for k, v in kw.items(): setattr(n, k, v)
    return n
def math_(op, a, b=None, clamp=False):
    n = node('ShaderNodeMath', operation=op, use_clamp=clamp)
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L(v, n.inputs[i])
    return n.outputs[0]
def mix(fac, a, b):                                                          # colour mix, a -> b by fac
    n = node('ShaderNodeMix', data_type='RGBA'); L(fac, n.inputs['Factor'])
    for sock, v in ((n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(v, tuple): sock.default_value = v + (1,)
        else: L(v, sock)
    return n.outputs[2]
tc = node('ShaderNodeTexCoord'); xyz = node('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], xyz.inputs[0])
nrm = node('ShaderNodeSeparateXYZ'); L(tc.outputs['Normal'], nrm.inputs[0])
x, y, z = xyz.outputs
blade = math_('LESS_THAN', z, BAL + 0.002); grip = math_('MULTIPLY', math_('GREATER_THAN', z, BAL + 0.0165), math_('LESS_THAN', z, BAL + 0.1125))
fit = math_('SUBTRACT', math_('SUBTRACT', 1.0, blade), grip, clamp=True)
def noise(scale_vec, detail=4.0, rough=0.55):
    mp = node('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale_vec; L(tc.outputs['Object'], mp.inputs['Vector'])
    n = node('ShaderNodeTexNoise', noise_dimensions='3D'); n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
    n.inputs['Scale'].default_value = 1.0; L(mp.outputs[0], n.inputs['Vector']); return n.outputs['Fac']
scr = math_('POWER', math_('SUBTRACT', 1.0, math_('MULTIPLY', math_('ABSOLUTE', math_('SUBTRACT', noise((900, 900, 5), 2.0), 0.5)), 26.0), clamp=True), 3.0)  # thin long scratches
pat = math_('MULTIPLY', math_('SUBTRACT', noise((22, 22, 9), 5.0), 0.42), 3.0, clamp=True)                                               # patina clouds
rust = math_('MULTIPLY', math_('SUBTRACT', noise((140, 140, 60), 6.0, 0.7), 0.69), 12.0, clamp=True)                                   # specks
def inlay(path, side):
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
    u = math_('DIVIDE', math_('SUBTRACT', BAL - 0.03, z), 0.25); v = math_('ADD', math_('DIVIDE', x, -0.023 if side > 0 else 0.023), 0.5)
    cv = node('ShaderNodeCombineXYZ'); L(u, cv.inputs[0]); L(v, cv.inputs[1])
    t = node('ShaderNodeTexImage', extension='CLIP', interpolation='Cubic'); t.image = im; L(cv.outputs[0], t.inputs[0])
    face = math_('GREATER_THAN', math_('MULTIPLY', nrm.outputs[1], float(side)), 0.3)
    return math_('MULTIPLY', math_('MULTIPLY', t.outputs['Color'], face), blade)
ins = math_('ADD', inlay(os.path.join(SRC, 'inscription_front.png'), 1), inlay(os.path.join(SRC, 'inscription_back.png'), -1), clamp=True)
ang = math_('ARCTAN2', y, x); wrap = math_('SINE', math_('MULTIPLY', math_('ADD', math_('DIVIDE', z, 0.0105), math_('DIVIDE', ang, 2 * math.pi)), 2 * math.pi))
wrapb = math_('MULTIPLY', math_('POWER', math_('MULTIPLY', math_('ADD', wrap, 1.0), 0.5), 0.35), grip)
leath = noise((260, 260, 260), 6.0, 0.6)
# base colour (linear)
steel = mix(pat, (0.60, 0.60, 0.61), (0.40, 0.40, 0.40)); steel = mix(ins, steel, (0.30, 0.285, 0.27)); steel = mix(math_('MULTIPLY', scr, 0.25), steel, (0.70, 0.70, 0.71))
iron = mix(pat, (0.46, 0.455, 0.45), (0.27, 0.265, 0.26))
leather = mix(leath, (0.06, 0.038, 0.024), (0.095, 0.062, 0.04)); leather = mix(math_('MULTIPLY', wrapb, 0.5), (0.035, 0.022, 0.014), leather)
col = mix(fit, steel, iron); col = mix(grip, col, leather); col = mix(math_('MULTIPLY', rust, math_('SUBTRACT', 1.0, grip)), col, (0.13, 0.066, 0.035))
metal = math_('MULTIPLY', math_('SUBTRACT', 1.0, grip), math_('SUBTRACT', 1.0, rust))
rb = math_('ADD', math_('ADD', 0.26, math_('MULTIPLY', pat, 0.24)), math_('MULTIPLY', scr, 0.08))
rb = math_('ADD', rb, math_('MULTIPLY', ins, 0.2)); rf = math_('ADD', 0.4, math_('MULTIPLY', pat, 0.25))
rough = math_('ADD', math_('MULTIPLY', blade, rb), math_('ADD', math_('MULTIPLY', fit, rf), math_('MULTIPLY', grip, math_('ADD', 0.56, math_('MULTIPLY', leath, 0.12)))))
rough = math_('ADD', math_('MULTIPLY', rough, math_('SUBTRACT', 1.0, rust)), math_('MULTIPLY', rust, 0.85))
height = math_('ADD', math_('ADD', math_('MULTIPLY', scr, -0.25), math_('MULTIPLY', ins, 0.6)), math_('ADD', math_('MULTIPLY', rust, 0.5), math_('MULTIPLY', wrapb, 1.0)))
bump = node('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.0004; L(height, bump.inputs['Height'])
L(col, bs.inputs['Base Color']); L(metal, bs.inputs['Metallic']); L(rough, bs.inputs['Roughness']); L(bump.outputs[0], bs.inputs['Normal'])
em = node('ShaderNodeEmission')
def bake(kind, name, src=None, cs='Non-Color'):
    im = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=(kind == 'NORMAL')); im.colorspace_settings.name = cs
    tn = node('ShaderNodeTexImage'); tn.image = im; N.active = tn
    if src is not None: L(src, em.inputs['Color']); L(em.outputs[0], out.inputs['Surface'])
    else: L(bs.outputs[0], out.inputs['Surface'])
    sc.render.bake.margin = 8; sc.render.bake.use_clear = True
    bpy.ops.object.bake(type=kind, normal_space='TANGENT') if kind == 'NORMAL' else bpy.ops.object.bake(type=kind)
    a = pixels(im); N.remove(tn); bpy.data.images.remove(im); return a
bc = bake('EMIT', 'bc', col); mt = bake('EMIT', 'mt', metal); rg = bake('ROUGHNESS', 'rg'); ao = bake('AO', 'ao'); nm = bake('NORMAL', 'nm')
L(bs.outputs[0], out.inputs['Surface'])
lin2s = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, 1), 1 / 2.4) - 0.055)
save('T_Ulfberht_BC', lin2s(bc[:, :, :3]))
ao1 = 0.35 + 0.65 * ao[:, :, 0]
save('T_Ulfberht_ORM', np.stack([ao1, rg[:, :, 0], mt[:, :, 0]], -1))
save('T_Ulfberht_N_GL', nm[:, :, :3]); dx = nm[:, :, :3].copy(); dx[:, :, 1] = 1 - dx[:, :, 1]; save('T_Ulfberht_N', dx)

# ------------------------------------------------------------------------------------------------ 2. rope (numpy, tileable)
R = 512; u, v = np.meshgrid((np.arange(R) + 0.5) / R, (np.arange(R) + 0.5) / R)   # v = 0.36 m (3 lays), u = once round
ph = 3 * 2 * np.pi * u - 2 * np.pi * v * 3                                   # the strand lay (matches the mesh lobes)
strand = 0.5 + 0.5 * np.cos(ph)
fib_ph = 3 * 2 * np.pi * u * 9 + 2 * np.pi * v * 3 * 9 * 0.6                 # fibres twist the other way inside each strand
rngr = np.random.default_rng(5431)
def tnoise(f, seed):                                                         # tileable value noise (periodic grid)
    g = np.random.default_rng(seed).random((f, f)); xi = u * f; yi = v * f; x0 = np.floor(xi).astype(int); y0 = np.floor(yi).astype(int)
    tx = xi - x0; ty = yi - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
    a = g[y0 % f, x0 % f]; b = g[y0 % f, (x0 + 1) % f]; c = g[(y0 + 1) % f, x0 % f]; d = g[(y0 + 1) % f, (x0 + 1) % f]
    return a + (b - a) * tx + (c - a) * ty + (a - b - c + d) * tx * ty
fuzz = 0.6 * tnoise(64, 1) + 0.4 * tnoise(128, 2); dirt = 0.6 * tnoise(8, 3) + 0.4 * tnoise(16, 4)
h = strand ** 0.6 * (0.85 + 0.15 * (0.5 + 0.5 * np.cos(fib_ph))) + 0.06 * fuzz
alb = np.stack([0.30, 0.235, 0.15], -1)[None, None, :] * (0.55 + 0.45 * h[:, :, None]) * (0.75 + 0.35 * dirt[:, :, None])
alb *= (1 - 0.35 * (dirt[:, :, None] > 0.62))                                 # grime where hands and the drum wear it
save('T_MineRope_BC', lin2s(alb))
gy, gx = np.gradient(h); nx, ny = -gx * 18, -gy * 18; nz = np.ones_like(h); ln = np.sqrt(nx * nx + ny * ny + nz * nz)
ngl = np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5], -1)
dxr = ngl.copy(); dxr[:, :, 1] = 1 - dxr[:, :, 1]; save('T_MineRope_N', dxr); save('T_MineRope_N_GL', ngl)
fz = (fuzz - fuzz.min()) / np.ptp(fuzz)                                     # fuzzy fibre tops rougher, hand-polished grime smoother
save('T_MineRope_ORM', np.stack([0.45 + 0.55 * strand ** 0.5, 0.58 + 0.3 * fz * (0.6 + 0.4 * strand) - 0.12 * (dirt > 0.62), np.zeros_like(h)], -1))

# ------------------------------------------------------------------------------------------------ 3. reveal noise
R = 512; u, v = np.meshgrid((np.arange(R) + 0.5) / R, (np.arange(R) + 0.5) / R)
n1 = 0.5 * tnoise(4, 11) + 0.3 * tnoise(8, 12) + 0.2 * tnoise(16, 13); n2 = 0.5 * tnoise(8, 14) + 0.3 * tnoise(16, 15) + 0.2 * tnoise(32, 16)
save('T_RevealNoise', np.stack([n1, n2, 0.5 * n1 + 0.5 * n2], -1))
print('BAKE OK', flush=True)
