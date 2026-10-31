# Siege engine atlases (#225, TGA): blender -b siege.blend -P bake_siege.py   env ATLAS (SM_RamAtlas | SM_TowerAtlas), B (T_SiegeRam | T_SiegeTower), RES, AO_SAMPLES
# Same data-bake + numpy pipeline as the zombies/horse; wood grain follows each timber's baked long axis.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects[os.environ['ATLAS']]
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False); o.hide_render = o.name != os.environ['ATLAS']
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
at.attribute_name = 'mat'; HIDE = (bake('EMIT', margin=0)[used][:, 0] > 0.4).astype(np.float32)
at.attribute_name = 'burn'; BURN = bake('EMIT', margin=0)[used][:, 0]
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
# wood grain: stretch the noise ~25x along each timber's long axis (G), offset per timber (PID) so no two boards match
S = 1.0 + 24.0 * (1 - np.abs(G)); Q = P * S + PID[:, None] * 37.0
ring = np.sin(fbm(Q, 6, 5, 1) * 34.0 + 3.0 * fbm(Q, 30, 3, 14)) * 0.5 + 0.5
grain = 0.6 * ring + 0.4 * fbm(Q, 60, 4, 2); fine = fbm(Q, 220, 3, 3)
knot = ss(0.80, 0.86, fbm(P + PID[:, None] * 11.0, 6, 2, 4)) * (1 - HIDE)
weather = np.clip(0.3 + 0.45 * up + 0.2 * (fbm(P, 2, 2, 5) - 0.5), 0, 1)                    # sun-greyed tops
damp = ss(0.6, 0.0, z) * (1 - up * 0.5)                                                      # mud splash at the base
mud = damp * ss(0.45, 0.6, fbm(P, 6, 3, 21))
nail = ss(0.985, 0.995, vn(P, 90, 7)) * (1 - IRON) * (1 - up) * (1 - HIDE)
# hides: wet rawhide panels, darker stitched seams every ~0.9 m, hair-side mottling
hm = fbm(P, 4, 4, 30); hw_ = fbm(P, 25, 3, 31)
wp = P + 0.6 * np.stack([fbm(P, 0.8, 2, 35), fbm(P, 0.8, 2, 36), fbm(P, 0.8, 2, 37)], 1)                         # warped: hides are uneven skins, not a grid
seam = np.maximum(ss(0.975, 0.997, np.abs(np.sin(wp[:, 0] * 2.1 + 2.0 * fbm(P, 1.5, 3, 32)))), ss(0.975, 0.997, np.abs(np.sin((wp[:, 1] + wp[:, 2]) * 1.7 + 2.0 * fbm(P, 1.5, 3, 33)))))
seam = seam * ss(0.3, 0.5, fbm(P, 2, 2, 38))                                                  # seams come and go
stitch = seam * ss(0.4, 0.6, np.sin((P[:, 0] + P[:, 1] + P[:, 2]) * 160) * 0.5 + 0.5)
char = BURN * ss(0.35, 0.55, fbm(P, 1.6, 3, 90) + 0.25 * fbm(P, 12, 2, 91) + 0.15 * up)          # wrecks: fire-blackened
char = np.maximum(char, BURN * ss(1.2, 0.2, z) * 0.6)
ash = ss(0.6, 0.8, fbm(P, 6, 3, 93)) * char * up
# ---- height -> normal
h = (0.0008 * (grain - 0.5) + 0.0003 * (fine - 0.5) - 0.0012 * knot) * (1 - HIDE) * (1 - IRON)
h += HIDE * (0.0012 * (hw_ - 0.5) + 0.0005 * (hm - 0.5) - 0.0008 * seam + 0.0004 * stitch)
h += 0.0004 * (fbm(P, 30, 3, 10) - 0.5) * IRON + 0.0006 * char * (fbm(P, 70, 2, 94) - 0.5)        # alligatored char
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = os.environ['B']
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
fresh, grey, dark = lin(132, 96, 64), lin(138, 132, 122), lin(70, 50, 36)
col = mix(fresh, dark, 0.7 * grain + 0.3 * (PID - 0.5)) * (0.72 + 0.56 * PID)[:, None]
col = mix(col, grey * (0.85 + 0.3 * grain)[:, None], weather * 0.8)
col = col * (0.72 + 0.56 * grain)[:, None] * (0.92 + 0.16 * fine)[:, None]
col = mix(col, lin(56, 40, 30), knot * 0.8)
hide = mix(lin(124, 88, 60), lin(78, 54, 38), ss(0.35, 0.7, hm)) * (0.85 + 0.3 * hw_)[:, None]
hide = mix(hide, lin(128, 108, 88), ss(0.6, 0.85, fbm(P, 5, 3, 34)) * 0.35)                      # pale scraped patches
hide = mix(hide, lin(70, 50, 36), np.clip(seam * 0.35 + stitch * 0.15, 0, 1))
col = mix(col, hide, HIDE)
col = mix(col, lin(72, 60, 46), mud * 0.7)
col = mix(col, lin(50, 44, 40), cav * 0.4)
rg = 0.68 + 0.12 * weather + 0.10 * (grain - 0.5) + 0.06 * (fine - 0.5) + 0.26 * (fbm(P, 7, 2, 15) - 0.5) - 0.1 * damp
rg = np.where(HIDE > 0.5, 0.52 + 0.14 * hm + 0.12 * (hw_ - 0.5) + 0.15 * seam, rg)              # wet rawhide sheen
me_ = np.zeros_like(rg)
col = mix(col, lin(34, 30, 28) * (0.85 + 0.3 * fbm(P, 60, 2, 92))[:, None], char * 0.92); rg = rg + (0.9 - rg) * char * 0.8
col = mix(col, lin(120, 116, 110), ash * 0.45)
rust = ss(0.4, 0.6, fbm(P, 50, 3, 13)); rust = np.maximum(rust, char * 0.5)                          # burnt iron rusts through
bare = rust < 0.5; icol = np.where(bare[:, None], lin(192, 188, 182), lin(104, 60, 40))
col = mix(col, icol, np.clip(IRON + nail, 0, 1)); me_ = np.where((IRON + nail > 0.5) & bare, 1.0, me_)
rg = np.where(IRON + nail > 0.5, 0.45 + 0.4 * rust, rg)
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(B + '_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = np.clip(rg, 0.08, 0.95); orm[used, 2] = me_; save(B + '_ORM', orm)
print('TEX OK', B, flush=True)
