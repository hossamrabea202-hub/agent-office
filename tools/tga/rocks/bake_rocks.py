# Rock set textures (#202 item 4, TGA): one atlas for SM_Rock_S/M/L, skins Dry + Mossy, shared normal.
# blender -b rocks.blend -P bake_rocks.py   env RES (2048), AO_SAMPLES. Data bake + numpy like the zombies/shed.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SM_RockAtlas']
for o in sc.objects: o.hide_render = o is not body
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


def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]
cav = 1 - ss(0.45, 0.95, AO); up = ss(0.35, 0.85, nz); edge = ss(0.15, 0.6, AO) * (1 - cav)
speck = vn(P, 900, 1); grains = fbm(P, 160, 3, 2); big = fbm(P, 2.0, 3, 3); mid = fbm(P, 14, 3, 4)
strata = 0.5 + 0.5 * np.sin(z * 38 + 3 * fbm(P, 2, 2, 40))
crack = ss(0.485, 0.5, fbm(P, 6, 4, 5)) * ss(0.515, 0.5, fbm(P, 6, 4, 5)) * ss(0.4, 0.6, fbm(P, 3, 2, 41))   # thinner, broken up             # thin fbm iso-band cracks
base = ss(0.25, 0.0, z)                                                               # soil wicked up the foot
# ---- height -> normal
h = 0.0012 * (grains - 0.5) + 0.0004 * (speck - 0.5) - 0.0025 * crack + 0.0008 * (mid - 0.5) + 0.0006 * (strata - 0.5)
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = 'T_Rock'
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
def skin(mossy):
    col = mix(lin(118, 114, 106), lin(150, 146, 138), big) * (0.88 + 0.24 * mid)[:, None]          # weathered granite-grey
    col = mix(col, lin(70, 68, 66), ss(0.75, 0.9, speck) * 0.7); col = mix(col, lin(196, 192, 182), ss(0.88, 0.96, speck) * 0.5)   # mica / dark grains
    col = col * (0.93 + 0.1 * strata)[:, None]
    col = mix(col, lin(166, 160, 150), edge * 0.35)                                                 # worn edges lighter
    col = mix(col, lin(62, 58, 54), np.clip(crack * 0.3 + cav * 0.45, 0, 1))          # cracks live mostly in the normal
    col = mix(col, lin(92, 78, 62), base * 0.6)
    rg = 0.72 + 0.12 * (grains - 0.5) + 0.30 * (mid - 0.5) + 0.32 * (big - 0.5) - 0.16 * edge + 0.1 * cav
    if mossy:
        moss = ss(0.55, 0.68, up * 0.55 + 0.55 * fbm(P, 5, 4, 6) + 0.2 * fbm(P, 25, 2, 61) + 0.25 * cav - 0.2 * edge)   # patchy cushions, not a cap * (1 - base * 0.5)
        mc = mix(lin(64, 82, 40), lin(98, 112, 54), fbm(P, 30, 3, 7)) * (0.85 + 0.3 * vn(P, 400, 8))[:, None]
        col = mix(col, mc, moss); rg = rg + (0.9 - rg) * moss
    else:                                                                                           # dry: lichen rosettes + dust
        lich = ss(0.70, 0.76, fbm(P, 9, 3, 9)) * (0.4 + 0.6 * up)
        col = mix(col, lin(176, 170, 128), lich * 0.75); col = mix(col, lin(160, 148, 124), up * 0.25)
        rg = rg + 0.05 * up + (0.88 - rg) * lich * 0.8
    return col, np.clip(rg, 0.3, 0.95)
for name, mossy in (('Dry', False), ('Mossy', True)):
    col, rg = skin(mossy)
    bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(f'{B}_{name}_BC', bc); del bc
    orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; save(f'{B}_{name}_ORM', orm); del orm
print('TEX OK rocks', flush=True)

