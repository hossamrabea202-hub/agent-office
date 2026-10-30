# Miner gear atlas (#202 item 7, TGA): wood / iron / leather / wax / flame by the baked 'mat' id. blender -b miner.blend -P bake_miner.py   env RES (2048), AO_SAMPLES
# Same data-bake + numpy pipeline as the zombies/horse; wood grain follows each timber's baked long axis.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SM_MinerAtlas']
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False); o.hide_render = o.name != 'SM_MinerAtlas'
body.select_set(True); bpy.context.view_layer.objects.active = body
geo = nt.nodes.new('ShaderNodeNewGeometry'); one = nt.nodes.new('ShaderNodeRGB'); one.outputs[0].default_value = (1, 1, 1, 1)
def bake(kind, margin=16, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = margin; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
nt.links.new(one.outputs[0], em.inputs['Color']); used = bake('EMIT')[..., 0] > 0.5
nt.links.new(geo.outputs['Position'], em.inputs['Color']); P = bake('EMIT')[used]
nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'grain'; nt.links.new(at.outputs['Vector'], em.inputs['Color']); G = bake('EMIT')[used]
G /= np.linalg.norm(G, axis=1, keepdims=True) + 1e-6
at.attribute_name = 'pid'; nt.links.new(at.outputs['Fac'], em.inputs['Color']); PID = bake('EMIT', margin=0)[used][:, 0]
at.attribute_name = 'iron'; IRON = bake('EMIT', margin=0)[used][:, 0]
at.attribute_name = 'mat'; MAT = np.rint(bake('EMIT', margin=0)[used][:, 0] * 4).astype(int)
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


def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)



x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]
cav = 1 - ss(0.45, 0.95, AO); up = ss(0.5, 0.9, nz); edge = ss(0.2, 0.7, AO) * (1 - cav)
WOOD, IRONM, LEATH, WAX, FLAME = (MAT == k for k in range(5))
S = 1.0 + 24.0 * (1 - np.abs(G)); Q = P * S + PID[:, None] * 37.0
ring = np.sin(fbm(Q, 6, 5, 1) * 34.0 + 3.0 * fbm(Q, 30, 3, 14)) * 0.5 + 0.5; grain = 0.6 * ring + 0.4 * fbm(Q, 60, 4, 2)
pores = vn(P, 1400, 3); crease = ss(0.49, 0.5, fbm(P, 70, 3, 4)) * ss(0.51, 0.5, fbm(P, 70, 3, 4)) * ss(0.45, 0.65, fbm(P, 6, 2, 41))   # fine, broken up
mott = fbm(P, 12, 3, 5)
rust = ss(0.22, 0.42, fbm(P, 50, 3, 13)); bare = (rust < 0.5) & IRONM
drip = ss(0.6, 0.75, vn(P * np.array([1, 1, 0.15]), 120, 6))
# ---- height -> normal
h = np.where(WOOD, 0.0006 * (grain - 0.5), 0.0)
h += np.where(LEATH, 0.00025 * (pores - 0.5) - 0.0008 * crease + 0.0004 * (mott - 0.5), 0.0)
h += np.where(IRONM, 0.0004 * (fbm(P, 60, 3, 10) - 0.5) * rust, 0.0) + np.where(WAX, 0.0006 * drip, 0.0)
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = 'T_MinerGear'
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
col = np.zeros((M, 3), np.float32); rg = np.zeros(M, np.float32); me_ = np.zeros(M, np.float32); em = np.zeros(M, np.float32)
wc = mix(lin(120, 86, 56), lin(66, 46, 32), 0.7 * grain) * (0.85 + 0.3 * PID)[:, None]               # haft: oiled, hand-darkened
col = np.where(WOOD[:, None], wc, col); rg = np.where(WOOD, 0.62 + 0.1 * (grain - 0.5) - 0.12 * edge, rg)
ic = np.where(bare[:, None], lin(186, 182, 176), mix(lin(104, 60, 40), lin(70, 44, 32), fbm(P, 20, 2, 11)))
col = np.where(IRONM[:, None], ic, col); rg = np.where(IRONM, 0.4 + 0.45 * rust, rg); me_ = np.where(bare, 1.0, me_)
lc = mix(lin(92, 66, 48), lin(58, 42, 32), mott) * (0.9 + 0.2 * pores)[:, None]
lc = mix(lc, lin(140, 104, 72), edge * 0.5); lc = mix(lc, lin(48, 34, 26), crease * 0.25 + cav * 0.3)     # worn edges, dark creases
col = np.where(LEATH[:, None], lc, col); rg = np.where(LEATH, 0.58 + 0.15 * (mott - 0.5) - 0.12 * edge + 0.08 * crease, rg)
col = np.where(WAX[:, None], mix(lin(216, 206, 176), lin(190, 176, 140), drip * 0.6), col); rg = np.where(WAX, 0.45, rg)
col = np.where(FLAME[:, None], lin(236, 196, 120), col); rg = np.where(FLAME, 0.5, rg); em = np.where(FLAME, 1.0, em)
col = mix(col, lin(44, 38, 34), 0.35 * cav * (1 - FLAME))                                            # grime + mine dust
col = mix(col, lin(120, 112, 100), 0.18 * up * (1 - FLAME) * (1 - bare))
rg = rg + 0.06 * (fbm(P, 3, 2, 12) - 0.5) + 0.12 * (fbm(P, 8, 2, 15) - 0.5)
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(B + '_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = np.clip(rg, 0.08, 0.95); orm[used, 2] = me_; save(B + '_ORM', orm); del orm
e = np.zeros((RES, RES, 3), np.float32); e[used] = em[:, None]; save(B + '_E', e)
print('TEX OK miner', flush=True)

