# Rotting horse body textures (#155, TGA). blender -b horse_rig.blend -P bake_horse.py     env RES (4096), AO_SAMPLES
# Same pipeline as the realm wasp: Cycles bakes the data (world position, normal, AO), numpy makes everything else to
# the knowledge-base numbers (non-metal 30-240 sRGB, metallic 0, 3-scale roughness, wear by cause, no baked light).
# Every rot layer has a physical cause: mange where the hide dried and split, the rib wound, the torn neck stump,
# dried blood running down from both (gravity), mud splashed up the legs from the ground, dust settled on the back.
# Out (out/tex): T_HorseBody_<Skin>_BC / _ORM, T_HorseBody_N (DirectX), _N_GL. Skins: Bay, Grey.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SK_HorseBody']
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active = body
geo = nt.nodes.new('ShaderNodeNewGeometry'); one = nt.nodes.new('ShaderNodeRGB'); one.outputs[0].default_value = (1, 1, 1, 1)
def bake(kind, margin=16, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = margin; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
nt.links.new(one.outputs[0], em.inputs['Color']); used = bake('EMIT')[..., 0] > 0.5
nt.links.new(geo.outputs['Position'], em.inputs['Color']); P = bake('EMIT')[used]
nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
mat2 = bpy.data.materials.new('M_AO'); mat2.use_nodes = True; t2 = mat2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; mat2.node_tree.nodes.active = t2
body.data.materials.clear(); body.data.materials.append(mat2)
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '160')))[..., 0][used]
M = int(used.sum()); print('TEXELS', M, flush=True)
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
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lin(*srgb): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in srgb], np.float32)
def mix(a, b, t): t = np.asarray(t, np.float32); return a + (b - a) * (t[:, None] if t.ndim else t)
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)

x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]
mott = fbm(P, 4, 3, 1); mid = fbm(P, 22, 3, 2); micro = vn(P, 260, 3)
cav = 1 - ss(0.45, 0.95, AO)
leg = ss(0.80, 0.70, z) * 1.0                                         # below the belly line
lowleg = ss(0.62, 0.50, z) * 1.0                                     # the 'points' (cannon down)
hoof = ss(0.10, 0.085, z) * 1.0
RIBY = [-0.32 + k * 0.115 for k in range(6)]
wound = np.exp(-(((y - 0.0) / 0.40) ** 2 + ((z - 1.10) / 0.26) ** 2)) * ss(0.12, 0.2, x)
ribd = np.min(np.stack([np.abs(y - (r + 0.01 + 0.025 * (1.21 - z))) for r in RIBY], 1), 1)
rib = ss(0.022, 0.010, ribd) * ss(0.26, 0.29, x) * ss(0.82, 0.9, z) * ss(1.42, 1.36, z)
flesh = ss(0.35, 0.6, wound + 0.15 * (fbm(P, 9, 3, 4) - 0.5)) * (1 - rib)
sock = np.linalg.norm(P - np.array([0, -0.95, 1.60]), axis=1)
stump = ss(0.20, 0.14, sock + 0.03 * (fbm(P, 14, 3, 5) - 0.5)) * 1.0      # torn neck: flesh, a vertebra in the middle
vert = ss(0.065, 0.04, sock) * 1.0
# mange: hide dried and split, hair gone in patches, worse around the wounds
mange = ss(0.64, 0.72, fbm(P, 6.0, 4, 6) + 0.25 * ss(0.2, 0.0, np.abs(wound - 0.3)) + 0.2 * ss(0.3, 0.2, sock)) * (1 - 0.85 * lowleg)
# dried blood runs straight down from the wound and the stump (vertical streaks, stretched noise)
st = vn(P * np.array([1, 1, 0.06], np.float32), 60, 7)
below_w = ss(0.0, 0.25, 1.05 - z) * ss(0.0, 0.25, z - 0.55) * ss(0.45, 0.25, np.abs(y)) * (x > 0.1)
below_s = ss(0.0, 0.2, 1.55 - z) * ss(0.0, 0.3, z - 1.0) * ss(0.30, 0.15, np.abs(y + 0.88))
streak = ss(0.62, 0.72, st) * np.clip(below_w + below_s, 0, 1)
# mud splashed up from the ground, thick on the hooves, fading up the leg in droplets
mudh = 0.30 + 0.10 * (fbm(P, 6, 3, 8) - 0.5)
mud = np.clip(ss(mudh, mudh - 0.12, z) + ss(0.80, 0.85, vn(P, 70, 9)) * ss(0.65, 0.3, z), 0, 1)
up = ss(0.55, 0.9, nz)

# ---- height -> normal --------------------------------------------------------------------------------------------
hairdir = np.where(leg > 0.5, 0, 1)                                    # hair flows along the body, down the legs
hair = np.where(hairdir == 1, vn(P * np.array([1, 0.12, 1], np.float32), 700, 10), vn(P * np.array([1, 1, 0.12], np.float32), 700, 11))
h = 0.00022 * (hair - 0.5) * (1 - mange)                               # coat strokes
h += 0.0004 * (fbm(P, 70, 3, 12) - 0.5) * mange                        # dried split hide
h += 0.0016 * (fbm(P, 160, 3, 13) - 0.5) * np.clip(flesh + stump, 0, 1)   # torn fibrous flesh
h -= 0.004 * flesh                                                     # flesh sits below the hide edge
h += 0.0012 * (fbm(P, 45, 3, 14) - 0.5) * mud
h += 0.0003 * np.sin(np.arctan2(x - np.sign(x) * 0.185, np.where(y < 0, y + 0.82, y - 0.71)) * 60) * hoof   # hoof wall striations
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
g = nrm * 0.5 + 0.5; save('T_HorseBody_N_GL', g); g[..., 1] = 1 - g[..., 1]; save('T_HorseBody_N', g); del g, nrm, H, gx, gy

def skin(S):
    col = np.tile(S['coat'], (M, 1)) * (0.84 + 0.32 * mott)[:, None] * (0.94 + 0.12 * mid)[:, None]
    if 'dapple' in S:                                                  # grey: dapples, lighter rings round darker cores
        dp = fbm(P, 9, 2, 20); col = mix(col, S['dapple'], ss(0.55, 0.7, dp) * (1 - leg) * 0.8)
    col = mix(col, S['belly'], ss(-0.3, -0.7, nz) * (1 - leg) * 0.5)  # paler belly
    col = mix(col, S['points'], lowleg)
    rg = np.full(M, S['r_coat'], np.float32) + 0.04 * (hair - 0.5)
    col = mix(col, S['hide'] * (0.85 + 0.3 * mid)[:, None], mange); rg = rg + (0.52 - S['r_coat']) * mange
    col = mix(col, S['flesh'] * (0.8 + 0.4 * fbm(P, 30, 3, 21))[:, None], np.clip(flesh + stump * (1 - vert), 0, 1))
    rg = np.where((flesh + stump) > 0.5, 0.28 + 0.1 * micro, rg)
    col = mix(col, S['bone'] * (0.85 + 0.25 * fbm(P, 40, 3, 22))[:, None], np.clip(rib + vert, 0, 1)); rg = np.where((rib + vert) > 0.5, 0.55, rg)
    col = mix(col, S['blood'], streak * 0.85); rg = rg - 0.1 * streak
    col = mix(col, S['hoof'] * (0.9 + 0.2 * mid)[:, None], hoof); rg = np.where(hoof > 0.5, 0.48, rg)
    col = mix(col, S['mud'] * (0.85 + 0.3 * mott)[:, None], mud * 0.9); rg = rg + (0.86 - rg) * mud * 0.9
    col = mix(col, S['grime'], 0.4 * cav); rg = rg + 0.1 * cav
    rg = rg + 0.05 * (micro - 0.5) + 0.05 * (mid - 0.5) + 0.06 * (mott - 0.5)
    dust = up * ss(0.4, 0.7, fbm(P, 10, 3, 23)) * 0.4 * (1 - flesh)
    col = mix(col, S['dust'], dust); rg = rg + 0.12 * dust
    return col, np.clip(rg, 0.08, 0.95)
SK = {'Bay': dict(coat=lin(104, 62, 40), belly=lin(122, 84, 58), points=lin(50, 42, 38), hide=lin(84, 66, 58), flesh=lin(104, 40, 34),
                  bone=lin(184, 168, 138), blood=lin(70, 32, 28), hoof=lin(64, 58, 52), mud=lin(88, 72, 56), grime=lin(52, 42, 34), dust=lin(134, 122, 104), r_coat=0.62),
      'Grey': dict(coat=lin(150, 148, 140), dapple=lin(112, 110, 106), belly=lin(166, 162, 152), points=lin(84, 82, 78), hide=lin(112, 104, 100), flesh=lin(100, 42, 36),
                   bone=lin(186, 172, 142), blood=lin(72, 34, 30), hoof=lin(70, 66, 60), mud=lin(90, 74, 58), grime=lin(58, 50, 44), dust=lin(136, 126, 108), r_coat=0.60)}
for name, S in SK.items():
    col, rg = skin(S)
    bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(f'T_HorseBody_{name}_BC', bc); del bc
    orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; save(f'T_HorseBody_{name}_ORM', orm); del orm
print('TEX OK', flush=True)
