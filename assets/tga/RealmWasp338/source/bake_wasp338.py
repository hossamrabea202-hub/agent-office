# Realm wasp v2 textures (#338, TGA PC). blender -b wasp338_rig.blend -P bake_wasp338.py     env RES (default 4096)
# Cycles (GPU) bakes only data: world position, normal, part / length / gaster segment, AO. Every value after that is numpy,
# layered in the film order (base -> colour variation at 3 scales -> thin-part translucency -> dirt by cause -> wet only where
# fluid is -> dust on top) and calibrated by number: non-metal albedo 30-240 sRGB, metallic 0, roughness varied.
# Out (<WORK>/out/tex):
#   T_RealmWasp_Body_<Skin>_BC (sRGB) / _ORM (R AO, G rough, B metal 0) / T_RealmWasp_Body_N (DirectX, _N_GL for Blender)
#   T_RealmWasp_Body_SSE: R = thin-chitin/tissue subsurface mask, G = spore glow mask, B = wet mask (shared by both skins)
#   T_RealmWasp_Wings_<Skin>_BCA (A = membrane opacity, translucent), T_RealmWasp_WingBlur_<Skin>_BCA (smeared, for the blur cards)
import bpy, numpy as np, os, math
from mathutils.kdtree import KDTree
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096')); WRES = 2048
Z0 = 1.30
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'
pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = True
body = bpy.data.objects['SK_RealmWasp']
for o in sc.objects: o.hide_render = o.type == 'MESH' and o != body        # AO from the body only (hair is too thin to occlude)

mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active = body
geo = nt.nodes.new('ShaderNodeNewGeometry')
def attr3(a0, a1, c2=None):
    c = nt.nodes.new('ShaderNodeCombineXYZ')
    for k, an in enumerate((a0, a1)):
        a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = an; nt.links.new(a.outputs['Fac'], c.inputs[k])
    if c2 is None: c.inputs[2].default_value = 1.0
    else: a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = c2; nt.links.new(a.outputs['Fac'], c.inputs[2])
    nt.links.new(c.outputs[0], em.inputs['Color'])
def bake(kind, margin=16, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = margin; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, margin, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
attr3('part', 'ulen'); cover = bake('EMIT', margin=0)[..., 2] > 0.5
A = bake('EMIT'); used = A[..., 2] > 0.5
part = np.rint(A[..., 0][used]).astype(np.int8); ulen = A[..., 1][used]; del A
attr3('gseg', 'ulen', 'gseg'); gseg = np.rint(bake('EMIT')[..., 0][used]).astype(np.int8)
nt.links.new(geo.outputs['Position'], em.inputs['Color']); P = bake('EMIT')[used]
nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
mat2 = bpy.data.materials.new('M_AO'); mat2.use_nodes = True; t2 = mat2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; mat2.node_tree.nodes.active = t2
body.data.materials.clear(); body.data.materials.append(mat2)
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '192')))[..., 0][used]
M = int(used.sum()); print('TEXELS', M, 'covered', int(cover.sum()), flush=True)

me = body.data; uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers['UVMap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
d3 = np.linalg.norm(co[lv[ls + 1]] - co[lv[ls]], axis=1); d2 = np.linalg.norm(uv[ls + 1] - uv[ls], axis=1)
ok = d3 > 1e-4; TPM = float(np.median(d2[ok] / d3[ok])) * RES; print('TEXEL DENSITY %.0f px/m' % TPM, flush=True)
# distance from every texel to the nearest fungus foot (mycelium spreads around it) and to the gaster wound
pa = np.empty(len(me.vertices), np.float32); me.attributes['part'].data.foreach_get('value', pa)
ul = np.empty(len(me.vertices), np.float32); me.attributes['ulen'].data.foreach_get('value', ul)
feet = co[(np.rint(pa) == 10) & (ul < 0.06)]
kd = KDTree(len(feet))
for i, p in enumerate(feet): kd.insert(p, i)
kd.balance()
step = 7; sub = P[::step]; dsub = np.array([kd.find(p)[2] for p in sub], np.float32)
dfoot = np.repeat(dsub, step)[:M]
tis = co[np.rint(pa) == 9]; kt = KDTree(len(tis))
for i, p in enumerate(tis): kt.insert(p, i)
kt.balance(); dts = np.array([kt.find(p)[2] for p in sub], np.float32); dtis = np.repeat(dts, step)[:M]
print('DISTANCES OK', flush=True)

# ---- noise ----
def vn(p, f, seed=0):
    q = p * f; i = np.floor(q).astype(np.int64); t = q - i; t = t * t * (3 - 2 * t)
    def h(dx, dy, dz):
        n = ((i[:, 0] + dx) * 73856093) ^ ((i[:, 1] + dy) * 19349663) ^ ((i[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float32) / 65535.0
    x0 = h(0, 0, 0) + (h(1, 0, 0) - h(0, 0, 0)) * t[:, 0]; x1 = h(0, 1, 0) + (h(1, 1, 0) - h(0, 1, 0)) * t[:, 0]
    x2 = h(0, 0, 1) + (h(1, 0, 1) - h(0, 0, 1)) * t[:, 0]; x3 = h(0, 1, 1) + (h(1, 1, 1) - h(0, 1, 1)) * t[:, 0]
    y0 = x0 + (x1 - x0) * t[:, 1]; y1 = x2 + (x3 - x2) * t[:, 1]; return y0 + (y1 - y0) * t[:, 2]
def fbm(p, f, oct=4, seed=0):
    s, a, tot = 0.0, 1.0, 0.0
    for k in range(oct): s = s + a * vn(p, f * 2 ** k, seed + k); tot += a; a *= 0.5
    return s / tot
def cell(p, f, seed=0):                                   # cheap cellular-ish: ridged noise (wrinkled tissue, cracked crust)
    return 1 - np.abs(2 * fbm(p, f, 3, seed) - 1)
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lin(*srgb): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in srgb], np.float32)
def mix(a, b, t): t = np.asarray(t, np.float32); return a + (b - a) * (t[:, None] if t.ndim else t)

x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]; ny = N[:, 1]
PN = dict(head=0, thorax=1, petiole=2, abdomen=3, stinger=4, leg=5, eye=6, mandible=7, antenna=8, tissue=9, fungus=10, ocellus=11, tegula=12)
pm = {k: part == v for k, v in PN.items()}
chit = ~(pm['eye'] | pm['tissue'] | pm['fungus'] | pm['ocellus'])
sf = np.where(pm['abdomen'], ulen, (ulen * 6.2) % 1.0)          # position inside a gaster shell: 0 tucked front .. 1 rim
mott = fbm(P, 5, 3, 1); mid = fbm(P, 28, 3, 2); micro = vn(P, 240, 3)
cav = 1 - ss(0.45, 0.95, AO)
right = x < 0                                                    # the right side is the more decayed side (asymmetry, one cause)
myc = ss(0.07, 0.0, dfoot) * (0.6 + 0.4 * fbm(P, 40, 3, 21)) * chit      # white mycelium felt around the fungus feet
necro = ss(0.09, 0.0, dtis) * chit                                        # chitin next to exposed tissue darkens (necrosis)
hole_c = np.array([-0.10, 0.0, 0.0]); wound = pm['abdomen'] & (gseg >= 3) & (gseg <= 5)
# ooze run-off: fluid from the gape and the hole runs down the shell (gravity), in tongues, not stripes
ooze = ss(0.06, 0.0, dtis) + ss(0.25, 0.0, dtis) * ss(-0.1, -0.6, nz * 0 - 0.5) * 0
lane = fbm(np.stack([x * 30, y * 30, np.zeros_like(x)], 1), 1, 3, 22)
ooze = np.clip(ooze + ss(0.20, 0.0, dtis) * ss(0.55, 0.75, lane) * (nz < 0.6) * pm['abdomen'], 0, 1)

# ---- height (metres) -> normal map ----
h = 0.00025 * (fbm(P, 220, 3, 4) - 0.5) * chit
pits = ss(0.74, 0.86, vn(P, 460, 5)) * (pm['thorax'] | pm['head'] | (pm['abdomen'] & (sf < 0.5)))
h -= 0.00028 * pits
h += pm['abdomen'] * (-0.0015 * (1 - ss(0.0, 0.12, sf)) + 0.0009 * ss(0.86, 0.98, sf))          # shell front groove + rim lip
h += 0.0005 * (fbm(P, 160, 2, 7) - 0.5) * pm['leg'] + 0.0004 * ss(0.8, 0.9, vn(P, 520, 34)) * pm['leg']   # cuticle grain + fine spines
d3_ = np.array([[0, 1, 0], [0, -0.5, 0.866], [0, -0.5, -0.866]], np.float32); k = 2 * np.pi / 0.0035
fac = sum(np.cos(P @ d * k) for d in d3_) / 3
h += 0.00022 * fac * pm['eye'] * (1 - 0.6 * right)                                               # facets (collapsed eye: softened)
h += 0.0022 * (cell(P, 26, 23) - 0.5) * pm['tissue'] + 0.0007 * (fbm(P, 90, 3, 24) - 0.5) * pm['tissue']   # wrinkled wet tissue
h += 0.0006 * (vn(P, 400, 25) - 0.5) * pm['fungus'] + 0.0012 * myc * (vn(P, 300, 26) - 0.5)       # fungal pores + felt
h -= 0.0008 * ss(0.6, 0.9, cell(P, 14, 27)) * necro                                               # crazed, cracked rot crust
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
def save(name, rgb, alpha=None, res=RES):
    im = bpy.data.images.new(name, res, res, alpha=alpha is not None); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((res, res, 4), np.float32); a[..., :3] = rgb
    if alpha is not None: a[..., 3] = alpha
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
gl = nrm * 0.5 + 0.5; save('T_RealmWasp_Body_N_GL', gl)
gl[..., 1] = 1 - gl[..., 1]; save('T_RealmWasp_Body_N', gl); del gl, nrm, H, gx, gy

# ---- shared masks: subsurface, spore glow, wet ----
thin = (pm['leg'] & (ulen > 0.55)) | pm['antenna'] | (pm['abdomen'] & (sf > 0.88)) | pm['mandible'] * (ulen > 0.6) | pm['tegula']
sss = np.clip(0.55 * thin + 1.0 * pm['tissue'] + 0.6 * pm['fungus'] + 0.4 * pm['ocellus'], 0, 1)
fert = pm['fungus'] & (ulen > 0.72)
spore = fert * ss(0.6, 0.85, vn(P, 260, 28)) * ss(0.4, 0.7, fbm(P, 30, 2, 29))                    # perithecia openings glow faintly
wetm = np.clip(pm['tissue'] * (0.7 + 0.3 * fbm(P, 20, 2, 30)) + 0.8 * ooze * chit + 0.6 * pm['eye'] * (~right), 0, 1)
sse = np.zeros((RES, RES, 3), np.float32); sse[used, 0] = sss; sse[used, 1] = spore; sse[used, 2] = wetm; save('T_RealmWasp_Body_SSE', sse); del sse

# ---- skins ----
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
up = ss(0.55, 0.9, nz)
def skin(S):
    n = M; col = np.tile(S['chitin'], (n, 1)) * (0.82 + 0.36 * mott)[:, None] * (0.94 + 0.12 * mid)[:, None]
    rg = np.full(n, S['r_chitin'], np.float32)
    face = pm['head'] & (ny < -0.35) & (z < Z0 + 0.05)                         # pale face plate (clypeus, frons)
    col = mix(col, S['band'] * (0.8 + 0.4 * mott)[:, None] * (0.9 + 0.2 * mid)[:, None], ss(0.0, 0.25, -ny - 0.35) * face)
    fmark = face * ss(0.03, 0.012, np.abs(x)) * ss(Z0 - 0.09, Z0 - 0.02, z)                     # dark frons mark (hornet face pattern)
    col = mix(col, S['mtip'], 0.75 * fmark)
    th = pm['thorax'] & (nz > 0.25)
    stripe = ss(0.012, 0.004, np.abs(np.abs(x) - 0.075 - 0.01 * (vn(P, 14, 10) - 0.5))) * ss(0.12, 0.25, ulen) * ss(0.85, 0.7, ulen)
    col = mix(col, S['band'], np.clip(stripe, 0, 1) * th)
    ab = pm['abdomen']
    edge = 0.5 + 0.06 * (vn(P, 18, 11) - 0.5) + 0.04 * np.cos(np.arctan2(x, z - Z0) * 2)        # warning band at the rear of each shell
    band = ss(edge, edge + 0.05, sf) * (gseg >= 1)
    spots = ss(0.035, 0.02, np.hypot(np.abs(x) - 0.07, (sf - 0.75) * 0.12)) * (gseg >= 2) * (gseg <= 5) * (nz > 0)
    bcol = S['band'] * (0.86 + 0.28 * mott)[:, None]; bcol = mix(bcol, S['band_edge'], ss(0.1, 0.0, sf - edge))
    col = mix(col, bcol, band * (1 - spots) * ab); rg = np.where(ab & (band > 0.5), S['r_band'], rg)
    col = mix(col, S['band_edge'], 0.35 * (ab & (nz < -0.4)))
    col = mix(col, S['band'], pm['tegula'] * 0.8 + pm['petiole'] * 0.0)
    lg = pm['leg']; col = mix(col, S['leg'] * (0.9 + 0.2 * mid)[:, None], ss(0.56, 0.66, ulen) * lg)
    md = pm['mandible']; col = mix(col, S['band'], (1 - ss(0.45, 0.7, ulen)) * md); col = mix(col, S['mtip'], ss(0.6, 0.85, ulen) * md)
    rg = np.where(md, 0.24 + 0.1 * ss(0.6, 0.9, ulen), rg)
    an = pm['antenna']; col = mix(col, S['leg'], ss(0.0, -0.5, nz) * an * 0.7)
    st = pm['stinger']; col = np.where(st[:, None], mix(S['stinger'], S['stinger_tip'], ss(0.5, 1.0, ulen)), col); rg = np.where(st, 0.2, rg)
    # eyes: the left still glossy, the right collapsed and milky (Blight: both milky)
    ey = pm['eye']; milky = right | S['both_milky']
    ecol = np.where(milky[:, None], S['eye_milky'] * (0.85 + 0.3 * fbm(P, 60, 3, 12))[:, None], S['eye'] * (0.85 + 0.3 * vn(P, 280, 12))[:, None])
    ecol = ecol * (0.7 + 0.3 * ss(-0.4, 0.4, fac))[:, None]                                        # facet rims stay dark
    col = np.where(ey[:, None], ecol, col); rg = np.where(ey, np.where(milky, 0.24, S['r_eye']), rg)
    oc = pm['ocellus']; col = np.where(oc[:, None], S['ocellus'], col); rg = np.where(oc, 0.12, rg)
    # realm corruption vein net (restraint: patchy, thin)
    veins = (1 - ss(0.0, 0.012, np.abs(fbm(P, 9, 4, 8) - 0.5))) * ss(0.48, 0.70, fbm(P, 2.2, 3, 9))
    vmask = veins * S['vein_amt'] * chit * (band < 0.5)
    col = mix(col, S['vein'], vmask); rg = rg - 0.06 * vmask
    # decay by cause: necrotic crust next to exposed tissue, mycelium felt around the fungus, the right side worse
    col = mix(col, S['necro'], np.clip(necro * (0.7 + 0.3 * right), 0, 1)); rg = rg + 0.12 * necro
    col = mix(col, S['mycel'] * (0.9 + 0.2 * mid)[:, None], myc); rg = rg + 0.3 * myc
    # wear by cause: abraded rims (paler, smoother), cavity grime (darker, rougher); bald rubbed patch on the scutum
    rim = ab * ss(0.9, 1.0, sf) + 0.5 * (1 - cav) * ss(0.8, 1.0, AO) * (lg | md)
    col = col * (1 + 0.14 * rim)[:, None]; rg = rg - 0.07 * rim
    col = mix(col, S['grime'], 0.6 * cav * chit); rg = rg + 0.12 * cav
    rg = rg + 0.08 * lg
    fuzz = (pm['thorax'] | (pm['head'] & (nz > -0.2))) * 1.0; rg = rg + 0.18 * fuzz * (~ey)
    rg = rg + 0.06 * (micro - 0.5) + 0.05 * (mid - 0.5) + 0.06 * (mott - 0.5)
    # tissue: grey-olive rot over pale pink, darker in the folds, wet (the only wet surface)
    ti = pm['tissue']; tcol = mix(S['tissue'], S['tissue_dark'], ss(0.45, 0.2, cell(P, 26, 23)) * 0.8 + 0.3 * cav)
    tcol = mix(tcol, S['tissue_rot'], ss(0.45, 0.75, fbm(P, 9, 3, 31)))
    col = np.where(ti[:, None], tcol, col); rg = np.where(ti, 0.12 + 0.12 * fbm(P, 40, 2, 32), rg)
    # fungus: pale bone stems, ochre fertile heads (Blight: sick green-grey), matte, darker stalk feet
    fu = pm['fungus']; fcol = mix(S['f_stem'] * (0.9 + 0.2 * mid)[:, None], S['f_head'] * (0.85 + 0.3 * mott)[:, None], ss(0.6, 0.8, ulen))
    fcol = mix(fcol, S['necro'], ss(0.08, 0.0, ulen) * 0.6)
    col = np.where(fu[:, None], fcol, col); rg = np.where(fu, 0.62 + 0.15 * fbm(P, 60, 2, 33), rg)
    # ooze: darker, glossy tongues running from the wound
    oz = ooze * chit; col = mix(col, S['ooze'], 0.75 * oz); rg = rg - 0.45 * oz
    # one shared dust pass on dry, up-facing chitin (never on the wet tissue)
    dust = up * ss(0.4, 0.7, fbm(P, 12, 3, 14)) * 0.4 * chit * (1 - oz)
    col = mix(col, S['dust'], dust); rg = rg + 0.15 * dust
    return col, np.clip(rg, 0.06, 0.95)

SKINS = {
    'Ember': dict(chitin=lin(64, 50, 40), band=lin(196, 132, 46), band_edge=lin(150, 90, 34), leg=lin(170, 112, 48), mtip=lin(48, 34, 28),
                  stinger=lin(74, 42, 32), stinger_tip=lin(126, 82, 52), eye=lin(80, 42, 32), eye_milky=lin(104, 100, 88), ocellus=lin(120, 70, 36),
                  vein=lin(66, 92, 86), grime=lin(46, 38, 30), dust=lin(136, 122, 104), necro=lin(44, 36, 32), mycel=lin(206, 200, 184),
                  tissue=lin(168, 128, 112), tissue_dark=lin(96, 62, 58), tissue_rot=lin(124, 118, 84), ooze=lin(70, 58, 40),
                  f_stem=lin(200, 186, 152), f_head=lin(176, 108, 46), r_chitin=0.52, r_band=0.50, r_eye=0.08, vein_amt=0.4, both_milky=False),
    'Blight': dict(chitin=lin(58, 46, 64), band=lin(186, 178, 124), band_edge=lin(132, 120, 82), leg=lin(128, 116, 88), mtip=lin(44, 34, 40),
                   stinger=lin(70, 44, 60), stinger_tip=lin(142, 122, 112), eye=lin(124, 134, 112), eye_milky=lin(112, 118, 100), ocellus=lin(110, 120, 96),
                   vein=lin(76, 128, 96), grime=lin(48, 44, 40), dust=lin(126, 122, 110), necro=lin(40, 36, 40), mycel=lin(196, 204, 186),
                   tissue=lin(150, 132, 120), tissue_dark=lin(84, 64, 66), tissue_rot=lin(110, 126, 86), ooze=lin(64, 66, 44),
                   f_stem=lin(190, 192, 164), f_head=lin(124, 140, 84), r_chitin=0.48, r_band=0.46, r_eye=0.07, vein_amt=0.75, both_milky=True),
}
for name, S in SKINS.items():
    col, rg = skin(S)
    bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(f'T_RealmWasp_Body_{name}_BC', bc); del bc
    orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; save(f'T_RealmWasp_Body_{name}_ORM', orm); del orm

# ---- wings: analytic in (span, chord) space; translucent membrane, veins, wrinkles, decay tears ----
def chord_frac(s): return (0.42 + 0.58 * np.sin(np.pi * np.minimum(1.0, s * 1.08) ** 0.55)) * (1 - 0.65 * s ** 6)
u = (np.arange(WRES) + 0.5) / WRES; U, V = np.meshgrid(u, u)
WINGS = {'fore': (1.10, 0.33, 0.5), 'hind': (0.74, 0.22, 0.0)}
def wings(S, seed):
    rgb = np.zeros((WRES, WRES, 3), np.float32); A = np.zeros((WRES, WRES), np.float32)
    for key, (span, chord, vrow) in WINGS.items():
        reg = (V >= vrow) & (V < vrow + 0.5); s = U[reg]; yabs = (V[reg] - vrow - 0.01) / 0.48 * chord
        c = chord * chord_frac(s); q = yabs / np.maximum(c, 1e-4)
        p3 = np.stack([s * span, yabs, np.full_like(s, seed)], 1).astype(np.float32)
        vl = [(0.015, 0.0, 0.0034, 1.0), (0.09, 0.02, 0.0022, 0.75), (0.20, 0.10, 0.0019, 0.9), (0.36, 0.10, 0.0017, 0.95),
              (0.55, 0.12, 0.0016, 0.9), (0.78, 0.05, 0.0014, 0.45)]
        d = np.full_like(s, 1.0)
        for q0, dq, w, smax in vl:
            dist = np.abs(q - (q0 + dq * s)) * c / w; dist = np.where(s <= smax, dist, 9.0); d = np.minimum(d, dist)
        for s0, qa, qb in [(0.30, 0.09, 0.55), (0.46, 0.20, 0.78), (0.58, 0.09, 0.36), (0.66, 0.36, 0.64), (0.72, 0.2, 0.36)]:
            dist = np.abs(s - s0 - 0.03 * (q - qa)) * span / 0.0014; dist = np.where((q > qa) & (q < qb), dist, 9.0); d = np.minimum(d, dist)
        vein = 1 - ss(0.6, 1.2, d)
        stig = ss(0.012, 0.0, np.maximum(np.abs(s - 0.66) * span - 0.035, 0)) * ss(0.13, 0.08, q) * (key == 'fore')
        wrink = fbm(p3, 55, 3, seed + 3)
        memb = S['memb'] * (0.85 + 0.3 * fbm(p3, 30, 3, seed + 1))[:, None] * (0.92 + 0.16 * wrink)[:, None]
        memb = mix(memb, S['memb_base'], ss(0.3, 0.0, s) + 0.5 * ss(0.25, 0.0, q))
        memb = mix(memb, S['grime'], 0.5 * ss(0.55, 0.8, fbm(p3, 8, 3, seed + 5)))                        # dried fluid / dirt blotches
        col = mix(memb, S['vein'], np.clip(vein + stig, 0, 1))
        a = S['a_memb'] + 0.15 * ss(0.3, 0.0, q) + 0.12 * ss(0.3, 0.0, s) + 0.1 * (wrink - 0.5)
        a = np.maximum(a, np.clip(vein + stig, 0, 1)); a = a * ss(1.0, 0.985, q)
        tear = ss(0.64, 0.69, fbm(p3, 9, 4, seed + 7)) * ss(0.35, 0.8, q) * (vein < 0.5)                      # torn: rot breaks soft parts
        tear = np.maximum(tear, ss(0.93, 0.9, q + 0.25 * fbm(p3, 6, 3, seed + 8)) * ss(0.55, 0.75, s) * S['ragged'])  # ragged trailing edge
        a = a * (1 - tear)
        rgb[reg] = to_srgb(col); A[reg] = np.where(q <= 1.0, a, 0)
    return rgb, A
WS = {'Ember': dict(memb=lin(170, 136, 90), memb_base=lin(118, 84, 52), vein=lin(66, 46, 32), grime=lin(110, 90, 62), a_memb=0.42, ragged=0.6),
      'Blight': dict(memb=lin(156, 166, 146), memb_base=lin(100, 104, 94), vein=lin(56, 44, 60), grime=lin(96, 100, 80), a_memb=0.36, ragged=1.0)}
def blur2d(img, r):
    out = img.copy()
    for ax in (0, 1):
        acc = np.zeros_like(out)
        for k in range(-r, r + 1): acc += np.roll(out, k, axis=ax)
        out = acc / (2 * r + 1)
    return out
for i, (name, S) in enumerate(WS.items()):
    rgb, A = wings(S, 40 + i); save(f'T_RealmWasp_Wings_{name}_BCA', rgb, A, WRES)
    # blur card: smeared along the span (the stroke direction), soft, faint; veins survive as streaks
    sm = blur2d(np.concatenate([rgb, A[..., None]], -1), 10)
    save(f'T_RealmWasp_WingBlur_{name}_BCA', sm[..., :3], np.clip(sm[..., 3] * 0.55, 0, 1), WRES)
print('TEX OK', flush=True)
