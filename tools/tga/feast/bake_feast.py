# Feast atlas (#227, TGA): blender -b feast.blend -P bake_feast.py   env RES (4096), AO_SAMPLES. Same data bake as the siege set.
# Same data-bake + numpy pipeline as the zombies/horse; wood grain follows each timber's baked long axis.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SM_FeastAtlas']
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False); o.hide_render = o.name != 'SM_FeastAtlas'
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
at.attribute_name = 'mat'; CLS = np.rint(bake('EMIT', margin=0)[used][:, 0] * 4).astype(np.int32)   # 0 wood 1 iron 3 wax 4 flame 5 bread 6 meat 7 cheese 8 apple 9 pewter 10 cloth 11 pitch
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
cav = 1 - ss(0.45, 0.95, AO); up = ss(0.5, 0.9, nz)
K = lambda k: (CLS == k).astype(np.float32)
WOOD, WAX, FLAME, BREAD, MEAT, CHEESE, APPLE, PEW, CLOTH, PITCH = K(0), K(3), K(4), K(5), K(6), K(7), K(8), K(9), K(10), K(11)
S = 1.0 + 24.0 * (1 - np.abs(G)); Q = P * S + PID[:, None] * 37.0
ring = np.sin(fbm(Q, 6, 5, 1) * 34.0 + 3.0 * fbm(Q, 30, 3, 14)) * 0.5 + 0.5
grain = 0.6 * ring + 0.4 * fbm(Q, 60, 4, 2); fine = fbm(Q, 220, 3, 3)
knot = ss(0.80, 0.86, fbm(P + PID[:, None] * 11.0, 6, 2, 4)) * WOOD
n1 = fbm(P, 20, 4, 40); n2 = fbm(P, 80, 3, 41); big = fbm(P, 4, 3, 42)
wine = ss(0.72, 0.8, fbm(P, 9, 3, 43)) * up * ss(0.7, 0.76, z) * WOOD                       # spilt wine / grease rings on the top
weave = (np.sin(P[:, 0] * 900) * np.sin(P[:, 1] * 900)) * 0.5 + 0.5
# ---- height -> normal
h = (0.0008 * (grain - 0.5) + 0.0003 * (fine - 0.5) - 0.0012 * knot) * WOOD
h += BREAD * (0.0015 * (n1 - 0.5) - 0.002 * ss(0.94, 0.99, np.abs(np.sin(P[:, 0] * 60 + P[:, 1] * 30))) * up)      # crust + scoring
h += MEAT * (0.003 * (n1 - 0.5) + 0.0015 * (n2 - 0.5)) + CHEESE * 0.0006 * (n2 - 0.5) + APPLE * 0.0002 * (n2 - 0.5)
h += PEW * 0.0004 * (fbm(P, 12, 2, 44) - 0.5) + CLOTH * 0.00015 * weave + PITCH * 0.002 * (n1 - 0.5) + WAX * 0.0006 * ss(0.6, 0.8, fbm(P * [1, 1, 0.2], 60, 2, 45))
h += 0.0004 * (fbm(P, 30, 3, 10) - 0.5) * IRON
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = 'T_Feast'
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
# wood: oiled, hand-worn table oak
col = mix(lin(124, 88, 58), lin(72, 50, 34), 0.7 * grain + 0.3 * (PID - 0.5)) * (0.75 + 0.5 * PID)[:, None]
col = col * (0.75 + 0.5 * grain)[:, None] * (0.92 + 0.16 * fine)[:, None]; col = mix(col, lin(56, 40, 30), knot * 0.8)
col = mix(col, lin(70, 34, 32), wine * 0.6)
rg = 0.62 + 0.1 * (grain - 0.5) + 0.06 * (fine - 0.5) + 0.2 * (fbm(P, 7, 2, 15) - 0.5) - 0.15 * up * WOOD - 0.15 * wine
me_ = np.zeros_like(rg)
def put(mask, c, r, m_=0.0):
    global col, rg, me_
    col = mix(col, c, mask); rg = rg + (r - rg) * mask; me_ = me_ + (m_ - me_) * mask
put(BREAD, mix(lin(184, 128, 70), lin(122, 74, 40), np.clip(up * 0.8 + 0.4 * (n1 - 0.5), 0, 1)) * (0.9 + 0.2 * n2)[:, None], 0.72 + 0.1 * n2)
put(BREAD * ss(0.72, 0.8, fbm(P, 90, 2, 46)) * up * 0.7, lin(200, 186, 160), 0.85)                        # flour dust
put(MEAT, mix(lin(108, 56, 32), lin(50, 28, 18), np.clip(ss(0.4, 0.65, n1) + 0.5 * up, 0, 1)) * (0.85 + 0.3 * n2)[:, None], 0.36 + 0.3 * n2)   # crisp dark top                # roasted, glossy fat
put(CHEESE, mix(lin(206, 164, 84), lin(230, 204, 130), up), 0.55 + 0.1 * n2)
put(APPLE, mix(lin(152, 34, 30), lin(176, 160, 70), ss(0.5, 0.75, fbm(P * [1, 1, 4], 30, 3, 47))), 0.32 + 0.1 * n2)
put(PEW, lin(186, 184, 180) * (0.97 + 0.06 * n2)[:, None], 0.35 + 0.25 * fbm(P, 12, 2, 48), 1.0)
put(CLOTH, mix(lin(206, 196, 172), lin(150, 130, 104), ss(0.68, 0.8, big) * 0.6) * (0.95 + 0.05 * weave)[:, None], 0.85)
put(WAX, lin(222, 212, 184) * (0.95 + 0.05 * n2)[:, None], 0.4)
put(PITCH, lin(44, 36, 30) * (0.85 + 0.3 * n1)[:, None], 0.55 + 0.2 * n2)
put(FLAME, lin(236, 196, 130), 0.6)
rust = ss(0.4, 0.6, fbm(P, 50, 3, 13)); bare = rust < 0.5; icol = np.where(bare[:, None], lin(192, 188, 182), lin(104, 60, 40))
col = mix(col, icol, IRON); me_ = np.where((IRON > 0.5) & bare, 1.0, me_); rg = np.where(IRON > 0.5, 0.45 + 0.4 * rust, rg)
col = mix(col, col * 0.75, cav * 0.4 * (1 - FLAME) * (1 - me_))                                  # metal albedo stays >= 180 sRGB
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(B + '_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = np.where(FLAME > 0.5, 1.0, AO); orm[used, 1] = np.clip(rg, 0.08, 0.95); orm[used, 2] = me_; save(B + '_ORM', orm)
em = np.zeros((RES, RES, 3), np.float32); hot = ss(0.3, 0.9, fbm(P, 30, 2, 49))
em[used] = to_srgb(FLAME[:, None] * mix(lin(255, 140, 50), lin(255, 226, 160), hot)); save(B + '_E', em)
print('TEX OK feast', flush=True)
