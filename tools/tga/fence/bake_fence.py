# Road fence atlas textures (#202 item 3, TGA): the ore-shed wood baker on SM_FenceAtlas. blender -b fence.blend -P bake_fence.py   env RES (2048), AO_SAMPLES
# Same data-bake + numpy pipeline as the zombies/horse; wood grain follows each timber's baked long axis.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SM_FenceAtlas']
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
body.data.materials.clear(); body.data.materials.append(mat)
for o in sc.objects: o.select_set(False); o.hide_render = o.name != 'SM_FenceAtlas'
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
ring = np.sin(fbm(Q, 6, 5, 1) * 34.0 + 3.0 * fbm(Q, 30, 3, 14)) * 0.5 + 0.5                                       # annual rings / streaks
grain = 0.6 * ring + 0.4 * fbm(Q, 60, 4, 2); fine = fbm(Q, 220, 3, 3)
knot = ss(0.80, 0.86, fbm(P + PID[:, None] * 11.0, 6, 2, 4))
weather = np.clip(0.35 + 0.5 * up + 0.25 * ss(1.6, 2.6, z) + 0.2 * (fbm(P, 2, 2, 5) - 0.5), 0, 1)   # sun-greyed tops
damp = ss(0.45, 0.0, z) * (1 - up * 0.5)                                                   # splash/damp line at the base
roof = ss(2.05, 2.25, z) * up                                                                # roof boards: moss + lichen in the hollows
moss = roof * ss(0.55, 0.70, fbm(P, 8, 3, 6) + 0.35 * cav)
nail = ss(0.985, 0.995, vn(P, 90, 7)) * (1 - IRON) * (1 - up)            # sparse round nail heads on the sides
orerust = ss(0.65, 0.8, fbm(P, 5, 3, 8)) * ss(0.7, 0.1, z) * ss(1.0, 0.8, y)                # ore dust/rust stains in the bays
# ---- height -> normal
h = 0.0008 * (grain - 0.5) * (1 - IRON) + 0.0003 * (fine - 0.5) - 0.0012 * knot + 0.0006 * moss * fbm(P, 90, 2, 9)
h += 0.0004 * (fbm(P, 30, 3, 10) - 0.5) * IRON
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = 'T_Fence'
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
fresh, grey, dark = lin(132, 96, 64), lin(138, 132, 122), lin(70, 50, 36)
col = mix(fresh, dark, 0.7 * grain + 0.3 * (PID - 0.5)) * (0.72 + 0.56 * PID)[:, None]
col = mix(col, grey * (0.85 + 0.3 * grain)[:, None], weather * 0.9)
col = col * (0.72 + 0.56 * grain)[:, None] * (0.92 + 0.16 * fine)[:, None]          # grain survives the weathering
col = mix(col, lin(56, 40, 30), knot * 0.8)
col = mix(col, lin(64, 54, 44), damp * 0.6)
col = mix(col, lin(76, 86, 48) * (0.8 + 0.4 * fbm(P, 40, 2, 11))[:, None], moss * 0.85)
col = mix(col, lin(108, 64, 42), orerust * 0.35)
col = mix(col, lin(52, 48, 46), cav * 0.4)
rg = 0.68 + 0.12 * weather + 0.10 * (grain - 0.5) + 0.06 * (fine - 0.5) + 0.12 * (fbm(P, 2.5, 2, 12) - 0.5) - 0.1 * damp + 0.1 * moss + 0.26 * (fbm(P, 7, 2, 15) - 0.5)   # fence: no roof/moss areas, needs its own variation
me_ = np.zeros_like(rg)
# iron: chains and nails, rusty dark metal (metal where bare, rust is a non-metal crust)
rust = ss(0.4, 0.6, fbm(P, 50, 3, 13))
bare = rust < 0.5; icol = np.where(bare[:, None], lin(192, 188, 182), lin(104, 60, 40))            # bare iron (metal) / rust crust (non-metal)
col = mix(col, icol, np.clip(IRON + nail, 0, 1)); me_ = np.where((IRON + nail > 0.5) & bare, 1.0, me_)
rg = np.where(IRON + nail > 0.5, 0.45 + 0.4 * rust, rg)
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(B + '_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = np.clip(rg, 0.08, 0.95); orm[used, 2] = me_; save(B + '_ORM', orm)
print('TEX OK fence', flush=True)


