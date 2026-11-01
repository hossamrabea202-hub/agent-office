# #402 Destrier coat textures (body) + hair card textures. checkking (Claude), 2026-11-01.
#   blender -b <work>/destrier_anim.blend -P bake_destrier.py -- <work>        env RES (2048), AO_SAMPLES
# TGA's #155 method: Cycles bakes data only (world position, normal, AO); numpy paints every layer by its physical cause
# (knowledge base): coat + dapples + paler belly + black points, the muzzle's bare dark skin, wet glossy eyes, horn hooves,
# sweat (darker + glossier) where tack and muscles rub (neck under the crest, behind the elbow, between the hind legs),
# mud splashed up the legs from the ground, dust settled on the back. No light in the BaseColor.
# Out (out/tex): T_Destrier_<Skin>_BC / _ORM, T_Destrier_N (DirectX) + _N_GL; T_DestrierHair_<Skin>_BCA (alpha cards).
# Skins: Bay, Grey, Black. Values: non-metal 30-240 sRGB (natural >= 40 for the black coat), metallic 0.
import bpy, numpy as np, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cavlib import save_png, lin, to_srgb, ss, mix
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
D = argv[0] if argv else os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '2048'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SK_Destrier']
for o in sc.objects:
    if o.type == 'MESH' and o != body: o.hide_render = True        # tack/hair don't occlude the coat AO
arm = bpy.data.objects['SK_Destrier_Rig']; arm.animation_data.action = None
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
keep_mats = list(body.data.materials)
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active = body
geo = nt.nodes.new('ShaderNodeNewGeometry'); one = nt.nodes.new('ShaderNodeRGB'); one.outputs[0].default_value = (1, 1, 1, 1)
def bake(kind, margin=16, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = margin; sc.render.bake.margin_type = 'EXTEND'; sc.render.bake.target = 'IMAGE_TEXTURES'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
nt.links.new(one.outputs[0], em.inputs['Color']); used = bake('EMIT')[..., 0] > 0.5
nt.links.new(geo.outputs['Position'], em.inputs['Color']); P = bake('EMIT')[used]
nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
mat2 = bpy.data.materials.new('M_AO'); mat2.use_nodes = True; t2 = mat2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; mat2.node_tree.nodes.active = t2
body.data.materials.clear(); body.data.materials.append(mat2)
if sc.world is None: sc.world = bpy.data.worlds.new('W')
sc.world.light_settings.distance = 0.6
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '96')))[..., 0][used]
body.data.materials.clear()
for m in keep_mats: body.data.materials.append(m)
M = int(used.sum())
me = body.data; uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
d3 = np.linalg.norm(co[lv[ls + 1]] - co[lv[ls]], axis=1); d2 = np.linalg.norm(uv[ls + 1] - uv[ls], axis=1)
ok = d3 > 1e-4; TPM = float(np.median(d2[ok] / d3[ok])) * RES; print('TEXEL DENSITY %.0f px/m' % TPM, flush=True)

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

x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]
POLL = np.array([0, -1.13, 1.90]); MUZ = np.array([0, -1.47, 1.33]); TH = (MUZ - POLL) / np.linalg.norm(MUZ - POLL)
th = (P - POLL) @ TH                                                # distance down the head
onhead = ss(-0.05, 0.02, th) * (np.linalg.norm((P - POLL) - th[:, None] * TH, axis=1) < 0.22)
mott = fbm(P, 4, 3, 1); mid = fbm(P, 22, 3, 2); micro = vn(P, 260, 3)
cav = 1 - ss(0.45, 0.95, AO)
leg = ss(0.86, 0.74, z) * (np.abs(y + 0.0) > 0.0) * (1 - ss(0.95, 1.05, z)) * 1.0
lowleg = ss(0.60, 0.48, z) * 1.0                                    # points: knee / hock down
hoof = ss(0.095, 0.08, z) * 1.0
belly = ss(-0.3, -0.75, nz) * (1 - leg) * ss(0.95, 1.0, z)
muzzle = ss(0.42, 0.52, th) * onhead
EYEc = [POLL + TH * 0.13 + np.array([0, 0, 0]) for _ in range(2)]
Nf = np.array([0, 0, 1.0]) - (np.array([0, 0, 1.0]) @ TH) * TH; Nf /= np.linalg.norm(Nf)
eye = np.zeros(M, np.float32)
for sg in (1, -1):
    e = POLL + TH * 0.13 + Nf * 0.035 + np.array([0.115 * sg, 0, 0])
    eye = np.maximum(eye, ss(0.026, 0.018, np.linalg.norm(P - e, axis=1)))
mudh = 0.32 + 0.10 * (fbm(P, 6, 3, 8) - 0.5)
mud = np.clip(ss(mudh, mudh - 0.14, z) + ss(0.82, 0.86, vn(P, 70, 9)) * ss(0.70, 0.3, z), 0, 1)
up = ss(0.55, 0.9, nz)
neck_side = ss(0.4, 0.8, np.abs(N[:, 0])) * ss(-0.62, -0.80, y) * ss(1.2, 1.35, z) * (1 - onhead)
elbow = np.exp(-(((y + 0.55) / 0.18) ** 2 + ((z - 1.0) / 0.15) ** 2))
inner = np.exp(-((y - 0.62) / 0.25) ** 2) * ss(0.12, 0.05, np.abs(x)) * ss(0.8, 1.0, z)
sweat = np.clip(ss(0.48, 0.62, fbm(P, 5, 3, 30)) * (neck_side + elbow + inner), 0, 1)

hairdir = np.where(leg > 0.5, 0, 1)
hair = np.where(hairdir == 1, vn(P * np.array([1, 0.12, 1], np.float32), 700, 10), vn(P * np.array([1, 1, 0.12], np.float32), 700, 11))
h = 0.00022 * (hair - 0.5) * (1 - muzzle * 0.7) * (1 - hoof)
h += 0.0012 * (fbm(P, 45, 3, 14) - 0.5) * mud
h += 0.0003 * np.sin(np.arctan2(x - np.sign(x) * 0.185, np.where(y < 0, y + 0.82, y - 0.71)) * 60) * hoof
h += 0.0002 * (fbm(P, 120, 2, 15) - 0.5) * muzzle
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
g = nrm * 0.5 + 0.5; save('T_Destrier_N_GL', g); g[..., 1] = 1 - g[..., 1]; save('T_Destrier_N', g); del g, nrm, H, gx, gy

SK = {'Bay': dict(coat=lin(98, 62, 44), belly=lin(118, 84, 60), points=lin(48, 40, 36), muzzle=lin(58, 48, 44), r_coat=0.62),
      'Grey': dict(coat=lin(158, 156, 150), dapple=lin(116, 114, 110), belly=lin(170, 166, 158), points=lin(86, 84, 80), muzzle=lin(70, 64, 62), r_coat=0.60),
      'Black': dict(coat=lin(46, 42, 40), belly=lin(54, 48, 44), points=lin(42, 38, 36), muzzle=lin(48, 42, 40), r_coat=0.56)}
COMMON = dict(hoof=lin(66, 60, 54), mud=lin(88, 72, 56), grime=lin(52, 44, 36), dust=lin(134, 122, 104), eye=lin(34, 26, 22))
def skin(S):
    col = np.tile(S['coat'], (M, 1)) * (0.84 + 0.32 * mott)[:, None] * (0.93 + 0.14 * mid)[:, None]
    col = col * (1 - 0.12 * ss(1.35, 1.55, z))[:, None]                 # darker topline (dorsal shading of the coat itself)
    if 'dapple' in S:                                                   # dapples: darker rings round lighter cores
        dp = fbm(P, 9, 2, 20); ring = ss(0.50, 0.56, dp) * ss(0.66, 0.58, dp)
        col = mix(col, S['dapple'], ring * (1 - leg) * 0.85)
    col = mix(col, S['belly'], belly * 0.5)
    col = mix(col, S['points'], lowleg)
    col = mix(col, S['muzzle'] * (0.9 + 0.2 * mid)[:, None], muzzle)
    rg = np.full(M, S['r_coat'], np.float32) + 0.05 * (hair - 0.5)
    rg = rg - 0.10 * muzzle                                             # bare, slightly oily skin round the nostrils
    col = mix(col, col * 0.80, sweat * 0.7); rg = rg - 0.22 * sweat      # sweat: darker and glossier
    col = mix(col, COMMON['hoof'] * (0.9 + 0.2 * mid)[:, None], hoof); rg = np.where(hoof > 0.5, 0.48, rg)
    col = mix(col, COMMON['mud'] * (0.85 + 0.3 * mott)[:, None], mud * 0.85); rg = rg + (0.86 - rg) * mud * 0.85
    col = mix(col, COMMON['grime'], 0.25 * cav); rg = rg + 0.06 * cav
    rg = rg + 0.05 * (micro - 0.5) + 0.06 * (mid - 0.5) + 0.08 * (mott - 0.5)
    dust = up * ss(0.4, 0.7, fbm(P, 10, 3, 23)) * 0.35
    col = mix(col, COMMON['dust'], dust); rg = rg + 0.12 * dust
    col = mix(col, COMMON['eye'], eye); rg = rg * (1 - eye) + 0.06 * eye    # the eye: dark and wet
    return col, np.clip(rg, 0.05, 0.95)
for name, S in SK.items():
    col, rg = skin(S)
    bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(f'T_Destrier_{name}_BC', bc); del bc
    orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; save(f'T_Destrier_{name}_ORM', orm); del orm

# ---- hair cards: 8 clump columns, strands with alpha, root darker, tips thinning --------------------------------------
HW, HH = 1024, 2048
rr = np.random.default_rng(77)
A = np.zeros((HH, HW), np.float32); C = np.zeros((HH, HW), np.float32)
yy = np.arange(HH)
for col in range(8):
    x0 = col * HW // 8; w = HW // 8
    for s in range(70):
        cx = x0 + rr.uniform(0.15, 0.85) * w; amp = rr.uniform(1, 5); fr = rr.uniform(0.5, 2.0); ph = rr.uniform(0, 6)
        L = rr.uniform(0.7, 1.0) * HH; th_ = rr.uniform(1.2, 2.6); tone = rr.uniform(0.75, 1.15)
        xs = cx + amp * np.sin(yy / HH * fr * 2 * np.pi + ph) + (yy / HH) * rr.normal(0, 4)
        for k in range(-3, 4):
            xi = np.clip(np.round(xs + k).astype(np.int64), x0, x0 + w - 1)
            prof = np.exp(-(k / th_) ** 2) * (yy < L) * (1 - ss(0.8 * L, L, yy))
            A[yy, xi] = np.maximum(A[yy, xi], prof)
            C[yy, xi] = np.where(prof > 0.3, tone, C[yy, xi])
grad = np.linspace(0.8, 1.0, HH)[:, None]                           # row 0 = root = top of the image (card v = 1); roots darker
HAIR = {'Bay': lin(46, 38, 34), 'Grey': lin(176, 172, 164), 'Black': lin(42, 38, 36)}
for name, hc in HAIR.items():
    im = bpy.data.images.new('h', HW, HH, alpha=True); im.colorspace_settings.name = 'Non-Color'
    rgb = to_srgb(np.clip(hc[None, None] * (np.where(C > 0, C, 1)[..., None]) * (grad[..., None] * np.ones((1, HW, 1))), 0, 1))
    a = np.ones((HH, HW, 4), np.float32); a[..., :3] = rgb; a[..., 3] = np.clip(A, 0, 1)
    im.pixels.foreach_set(a[::-1].ravel()); im.filepath_raw = os.path.join(OUT, f'T_DestrierHair_{name}_BCA.png'); im.file_format = 'PNG'
    im.alpha_mode = 'STRAIGHT'; im.save(); bpy.data.images.remove(im); print('SAVED hair', name, flush=True)
print('TEX OK', flush=True)
