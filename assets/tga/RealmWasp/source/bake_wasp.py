# Realm wasp textures (#156, TGA). blender -b wasp_rig.blend -P bake_wasp.py      env RES (default 4096)
# Cycles bakes only the data: world position, object normal, part id + length along the part, AO. Everything else is
# numpy, so every value is calibrated by number (handoffs/knowledge): non-metal albedo 30-240 sRGB, metallic 0,
# roughness varied at 3 scales, wear by physical cause (cavity grime, abraded rims, one shared up-facing dust pass),
# no lighting in BaseColor. The normal map comes from a height field in UV space (tangent frame = UV axes).
# Out (out/tex): T_RealmWasp_Body_<Skin>_BC / _ORM (R AO, G rough, B metal 0), T_RealmWasp_Body_N (DirectX),
# _N_GL (OpenGL, for Blender), T_RealmWasp_Wings_<Skin>_BCA (RGBA, A = opacity). Skins: Ember, Blight.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096')); WRES = RES // 2
Z0 = 1.30
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SK_RealmWasp']

# ---- bakes --------------------------------------------------------------------------------------------------------
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active = body
geo = nt.nodes.new('ShaderNodeNewGeometry')
def src_position(): nt.links.new(geo.outputs['Position'], em.inputs['Color'])
def src_normal(): nt.links.new(geo.outputs['Normal'], em.inputs['Color'])       # raw -1..1 into a float image
def src_attr():
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'part'; b = nt.nodes.new('ShaderNodeAttribute'); b.attribute_name = 'ulen'
    c = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(a.outputs['Fac'], c.inputs[0]); nt.links.new(b.outputs['Fac'], c.inputs[1]); c.inputs[2].default_value = 1.0
    nt.links.new(c.outputs[0], em.inputs['Color'])
def bake(kind, margin=16, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = margin; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, margin, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
src_attr(); cover = bake('EMIT', margin=0)[..., 2] > 0.5
A = bake('EMIT'); used = A[..., 2] > 0.5                      # padded texels: compute colour there too (no seams)
part = np.rint(A[..., 0][used]).astype(np.int8); ulen = A[..., 1][used]; del A
src_position(); P = bake('EMIT')[used]
src_normal(); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
for l in list(nt.links):
    if l.to_node == em: nt.links.remove(l)
mat2 = bpy.data.materials.new('M_AO'); mat2.use_nodes = True; t2 = mat2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; mat2.node_tree.nodes.active = t2
body.data.materials.clear(); body.data.materials.append(mat2)
sc.render.bake.use_pass_direct = sc.render.bake.use_pass_indirect = True
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '160')))[..., 0][used]
M = int(used.sum()); print('TEXELS', M, 'covered', int(cover.sum()), flush=True)

# texel density (px per metre) from the mesh, to turn height slopes into normals
me = body.data; uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers['UVMap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
d3 = np.linalg.norm(co[lv[ls + 1]] - co[lv[ls]], axis=1); d2 = np.linalg.norm(uv[ls + 1] - uv[ls], axis=1)
ok = d3 > 1e-4; TPM = float(np.median(d2[ok] / d3[ok])) * RES; print('TEXEL DENSITY %.0f px/m' % TPM, flush=True)

# ---- noise ----------------------------------------------------------------------------------------------------------
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
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lin(*srgb): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in srgb], np.float32)
def mix(a, b, t): t = np.asarray(t, np.float32); return a + (b - a) * (t[:, None] if t.ndim else t)

x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]; ny = N[:, 1]
pm = {k: part == v for k, v in dict(head=0, thorax=1, petiole=2, abdomen=3, stinger=4, leg=5, eye=6, mandible=7, antenna=8).items()}
sf = (ulen * 6.2) % 1.0; seg = np.floor(ulen * 6.2)
mott = fbm(P, 5, 3, 1); mid = fbm(P, 28, 3, 2); micro = vn(P, 240, 3)
cav = 1 - ss(0.45, 0.95, AO)                                  # 0 open .. 1 deep cavity

# ---- height (metres) -> normal map ----------------------------------------------------------------------------------
chit = ~pm['eye']
h = 0.00025 * (fbm(P, 220, 3, 4) - 0.5) * chit
pits = ss(0.74, 0.86, vn(P, 460, 5)) * (pm['thorax'] | pm['head'] | (pm['abdomen'] & (sf < 0.45)))
h -= 0.00028 * pits                                           # punctation: fine, shallow pits (v1 read as pale crumbs)
fuzz = (pm['thorax'] | (pm['head'] & (nz > -0.2))) * 1.0
h += 0.0004 * (vn(P, 900, 6) - 0.5) * fuzz                    # short pile on thorax and crown
h += pm['abdomen'] * (-0.0022 * (1 - ss(0.0, 0.07, sf)) + 0.0009 * ss(0.88, 1.0, sf))   # segment groove + rim lip
h += 0.00025 * (fbm(P, 160, 2, 7) - 0.5) * pm['leg']          # leg cuticle grain (round spine bumps read as water drops)
d3_ = np.array([[0, 1, 0], [0, -0.5, 0.866], [0, -0.5, -0.866]], np.float32); k = 2 * np.pi / 0.0035
fac = sum(np.cos(P @ d * k) for d in d3_) / 3
h += 0.00022 * fac * pm['eye']                                # ommatidia facets
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
nrm[~used] = (0, 0, 1)
def save(name, rgb, alpha=None, res=RES):
    im = bpy.data.images.new(name, res, res, alpha=alpha is not None); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((res, res, 4), np.float32); a[..., :3] = rgb
    if alpha is not None: a[..., 3] = alpha
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
gl = nrm * 0.5 + 0.5; save('T_RealmWasp_Body_N_GL', gl)
gl[..., 1] = 1 - gl[..., 1]; save('T_RealmWasp_Body_N', gl); del gl, nrm, H, gx, gy

# ---- skins --------------------------------------------------------------------------------------------------------
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
veins_net = 1 - ss(0.0, 0.012, np.abs(fbm(P, 9, 4, 8) - 0.5))       # realm corruption: a fine vein net
veins_patch = ss(0.48, 0.70, fbm(P, 2.2, 3, 9))
up = ss(0.55, 0.9, nz)                                                # up-facing for the shared dust pass
def skin(S):
    n = M; col = np.tile(S['chitin'], (n, 1)) * (0.82 + 0.36 * mott)[:, None] * (0.94 + 0.12 * mid)[:, None]
    rg = np.full(n, S['r_chitin'], np.float32)
    # head: pale face plate under the antennae, dark crown
    face = pm['head'] & (ny < -0.35) & (z < Z0 + 0.04)
    col = mix(col, S['band'] * (0.9 + 0.2 * mid)[:, None], ss(0.0, 0.25, -ny - 0.35) * face)
    # thorax: two dorsal stripes and a spot over the waist
    th = pm['thorax'] & (nz > 0.25)
    stripe = ss(0.012, 0.004, np.abs(np.abs(x) - 0.075 - 0.01 * (vn(P, 14, 10) - 0.5))) * ss(0.12, 0.25, ulen) * ss(0.85, 0.7, ulen)
    spot = ss(0.06, 0.03, np.hypot(x, (ulen - 0.07) * 0.44)) * 1.0
    col = mix(col, S['band'], np.clip(stripe + spot, 0, 1) * th)
    # abdomen: a band at the rear of every segment, wavy front edge, a pair of dark spots in bands 2-5
    edge = 0.45 + 0.06 * (vn(P, 18, 11) - 0.5) + 0.04 * np.cos(np.arctan2(x, z - Z0) * 2)
    band = ss(edge, edge + 0.04, sf) * ss(1.0, 0.95, sf) * (seg >= 1)
    spots = ss(0.035, 0.02, np.hypot(np.abs(x) - 0.07, (sf - 0.7) * 0.12)) * (seg >= 2) * (seg <= 5) * (nz > 0)
    bcol = S['band'] * (0.86 + 0.28 * mott)[:, None]; bcol = mix(bcol, S['band_edge'], ss(0.1, 0.0, sf - edge))
    ab = pm['abdomen']; col = mix(col, bcol, band * (1 - spots) * ab); rg = np.where(ab & (band > 0.5), S['r_band'], rg)
    belly = ab & (nz < -0.4); col = mix(col, S['band_edge'], 0.35 * belly)
    # legs: dark femur, paler tibia/tarsus; mandibles pale with dark tips; antenna pale underside
    lg = pm['leg']; lowleg = ss(0.56, 0.66, ulen)               # dark femur and upper tibia, pale lower tibia + tarsus
    col = mix(col, S['leg'] * (0.9 + 0.2 * mid)[:, None], lowleg * lg)
    md = pm['mandible']; col = mix(col, S['band_edge'], (1 - ss(0.5, 0.75, ulen)) * md); rg = np.where(md, 0.22 + 0.1 * ss(0.6, 0.9, ulen), rg)
    an = pm['antenna']; col = mix(col, S['leg'], ss(0.0, -0.5, nz) * an * 0.7)
    st = pm['stinger']; col = np.where(st[:, None], mix(S['stinger'], S['stinger_tip'], ss(0.5, 1.0, ulen)), col); rg = np.where(st, 0.20, rg)
    # eyes: dark, glossy, faint facet variation
    ey = pm['eye']; col = np.where(ey[:, None], S['eye'] * (0.85 + 0.3 * vn(P, 280, 12))[:, None], col); rg = np.where(ey, S['r_eye'], rg)
    # realm corruption veins on the dark chitin (restraint: patchy and thin)
    vmask = veins_net * veins_patch * S['vein_amt'] * (~ey) * (band < 0.5)
    col = mix(col, S['vein'], vmask); rg = rg - 0.08 * vmask
    if 'lesion' in S:                                           # Blight: weeping lesions on the abdomen bands
        les = ss(0.72, 0.8, fbm(P, 7, 3, 13)) * ab
        col = mix(col, S['lesion'], les); rg = rg - 0.18 * les
    # wear by cause: rims and high points abraded (paler, smoother); cavity grime (darker, rougher); fuzz is matte
    rim = ab * ss(0.9, 1.0, sf) + 0.5 * (1 - cav) * ss(0.8, 1.0, AO) * (lg | md)
    col = col * (1 + 0.14 * rim)[:, None]; rg = rg - 0.07 * rim
    col = mix(col, S['grime'], 0.45 * cav); rg = rg + 0.12 * cav
    rg = rg + 0.22 * fuzz * (~ey)
    # roughness at three scales
    rg = rg * S['wet'] + 0.06 * (micro - 0.5) + 0.05 * (mid - 0.5) + 0.06 * (mott - 0.5)
    # one shared dust pass on up-facing surfaces
    dust = up * ss(0.4, 0.7, fbm(P, 12, 3, 14)) * 0.35
    col = mix(col, S['dust'], dust); rg = rg + 0.15 * dust
    return col, np.clip(rg, 0.06, 0.95)

SKINS = {
    'Ember': dict(chitin=lin(60, 49, 40), band=lin(198, 140, 46), band_edge=lin(150, 90, 34), leg=lin(152, 98, 42),
                  stinger=lin(74, 42, 32), stinger_tip=lin(120, 78, 50), eye=lin(76, 40, 32), vein=lin(66, 92, 86),
                  grime=lin(46, 38, 30), dust=lin(132, 118, 100), r_chitin=0.42, r_band=0.46, r_eye=0.09, vein_amt=0.45, wet=1.0),
    'Blight': dict(chitin=lin(56, 45, 62), band=lin(178, 172, 122), band_edge=lin(128, 118, 80), leg=lin(120, 110, 84),
                   stinger=lin(70, 44, 60), stinger_tip=lin(140, 120, 110), eye=lin(124, 134, 112), vein=lin(76, 128, 96),
                   grime=lin(48, 44, 40), dust=lin(124, 120, 108), lesion=lin(116, 54, 44),
                   r_chitin=0.38, r_band=0.42, r_eye=0.07, vein_amt=0.8, wet=0.85),
}
ORMs = {}
for name, S in SKINS.items():
    col, rg = skin(S)
    bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(f'T_RealmWasp_Body_{name}_BC', bc); del bc
    orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; save(f'T_RealmWasp_Body_{name}_ORM', orm); del orm

# ---- wings: analytic in (span, chord) space ------------------------------------------------------------------------
def chord_frac(s): return (0.42 + 0.58 * np.sin(np.pi * np.minimum(1.0, s * 1.08) ** 0.55)) * (1 - 0.65 * s ** 6)
u = (np.arange(WRES) + 0.5) / WRES; U, V = np.meshgrid(u, u)
WINGS = {'fore': (1.10, 0.33, 0.5), 'hind': (0.74, 0.22, 0.0)}
def wings(S, seed):
    rgb = np.zeros((WRES, WRES, 3), np.float32); A = np.zeros((WRES, WRES), np.float32)
    for key, (span, chord, vrow) in WINGS.items():
        reg = (V >= vrow) & (V < vrow + 0.5); s = U[reg]; yabs = (V[reg] - vrow - 0.01) / 0.48 * chord
        c = chord * chord_frac(s); q = yabs / np.maximum(c, 1e-4)
        p3 = np.stack([s * span, yabs, np.full_like(s, seed)], 1).astype(np.float32)
        # veins (metres from the vein line): costa on the leading edge, then longitudinals fanning out, cross-veins
        vl = [(0.015, 0.0, 0.0030, 1.0), (0.09, 0.02, 0.0018, 0.75), (0.20, 0.10, 0.0016, 0.9), (0.36, 0.10, 0.0014, 0.95),
              (0.55, 0.12, 0.0013, 0.9), (0.78, 0.05, 0.0012, 0.45)]
        d = np.full_like(s, 1.0)
        for q0, dq, w, smax in vl:
            dist = np.abs(q - (q0 + dq * s)) * c / w; dist = np.where(s <= smax, dist, 9.0); d = np.minimum(d, dist)
        for s0, qa, qb in [(0.30, 0.09, 0.55), (0.46, 0.20, 0.78), (0.58, 0.09, 0.36), (0.66, 0.36, 0.64), (0.72, 0.2, 0.36)]:
            dist = np.abs(s - s0 - 0.03 * (q - qa)) * span / 0.0012; dist = np.where((q > qa) & (q < qb), dist, 9.0); d = np.minimum(d, dist)
        vein = 1 - ss(0.6, 1.2, d)
        stig = ss(0.012, 0.0, np.maximum(np.abs(s - 0.66) * span - 0.035, 0)) * ss(0.13, 0.08, q) * (key == 'fore')
        memb = S['memb'] * (0.9 + 0.2 * fbm(p3, 30, 3, seed + 1))[:, None]
        memb = mix(memb, S['memb_base'], ss(0.3, 0.0, s) + 0.5 * ss(0.25, 0.0, q))      # darker towards root and costa
        col = mix(memb, S['vein'], np.clip(vein + stig, 0, 1))
        a = S['a_memb'] + 0.2 * ss(0.3, 0.0, q) + 0.15 * ss(0.3, 0.0, s)
        a = np.maximum(a, np.clip(vein + stig, 0, 1)); a = a * ss(1.0, 0.985, q)            # soft trailing edge
        if 'tears' in S:
            tear = ss(0.66, 0.70, fbm(p3, 9, 4, seed + 7)) * ss(0.45, 0.85, q) * (vein < 0.5)
            a = a * (1 - tear)
        rgb[reg] = to_srgb(col); A[reg] = np.where(q <= 1.0, a, 0)
    return rgb, A
WS = {'Ember': dict(memb=lin(160, 128, 86), memb_base=lin(112, 80, 50), vein=lin(62, 44, 32), a_memb=0.34),
      'Blight': dict(memb=lin(150, 160, 142), memb_base=lin(96, 100, 92), vein=lin(54, 42, 58), a_memb=0.28, tears=1)}
for i, (name, S) in enumerate(WS.items()):
    rgb, A = wings(S, 40 + i); save(f'T_RealmWasp_Wings_{name}_BCA', rgb, A, WRES)
print('TEX OK', flush=True)
