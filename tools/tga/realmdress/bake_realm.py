# Realm dressing atlas (#202 item 10, TGA): earth / realm flesh / glowing sac / vent mouth / spores from landmarks.
# blender -b realm.blend -P bake_realm.py   env RES (2048), AO_SAMPLES. Data bake + numpy like the zombies.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
body = bpy.data.objects['SM_RealmAtlas']
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
cav = 1 - ss(0.45, 0.95, AO); up = ss(0.5, 0.9, nz)
VENT = x > 1.25; vx = x - 2.5 * VENT; rad = np.hypot(vx, y)
dsac = np.linalg.norm(P - np.array([0.05, 0.03, 1.02]), axis=1)
SACW = ss(0.40, 0.33, dsac) * (~VENT); SAC = SACW > 0.5                               # soft edge where the sac meets the stalk
EARTH = (~VENT) & (z < 0.2) & (rad > 0.17) & ~SAC
NOD = VENT & (rad > 0.56) & (z < 0.15)
MOUTH = VENT & (rad < 0.2) & (z > 0.4)
vein = ss(0.488, 0.5, fbm(P, 9, 4, 50)) * ss(0.512, 0.5, fbm(P, 9, 4, 50)) * ss(0.35, 0.6, fbm(P, 4, 2, 57))   # thinner, fading in and out
ridge = 0.5 + 0.5 * np.cos(np.arctan2(y, vx) * 7 + 2 * fbm(P, 3, 2, 51))
mott = fbm(P, 6, 3, 52); fine = fbm(P, 80, 3, 53); soil = fbm(P, 30, 3, 54)
# ---- height -> normal
h = 0.0008 * (fine - 0.5) + 0.0006 * vein * (~EARTH) + 0.0012 * (soil - 0.5) * EARTH + 0.0006 * (ridge - 0.5) * VENT
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = 'T_RealmDress'
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
flesh = mix(lin(78, 58, 76), lin(120, 86, 104), mott) * (0.9 + 0.2 * fine)[:, None]                    # dark realm flesh
col = mix(flesh, lin(196, 96, 150), vein * 0.75); rg = 0.42 + 0.12 * (mott - 0.5) + 0.1 * (fine - 0.5)
membrane = mix(lin(176, 140, 160), lin(214, 160, 190), fbm(P, 4, 3, 55))
col = mix(col, mix(membrane, lin(232, 110, 176), vein), SACW); rg = rg + (0.22 + 0.1 * (fine - 0.5) - rg) * SACW
earth = mix(lin(92, 76, 60), lin(62, 52, 44), soil) * (0.9 + 0.2 * fine)[:, None]
col = np.where(EARTH[:, None], earth, col); rg = np.where(EARTH, 0.85 + 0.08 * (soil - 0.5), rg)
col = np.where(NOD[:, None], mix(lin(200, 186, 150), lin(220, 150, 170), mott), col); rg = np.where(NOD, 0.5, rg)
col = np.where(MOUTH[:, None], lin(236, 120, 180), col); rg = np.where(MOUTH, 0.3, rg)
col = mix(col, lin(40, 30, 40), 0.35 * cav)
rg = rg + 0.08 * (fbm(P, 2.5, 2, 56) - 0.5)
em = np.clip(vein * 0.6 * (~EARTH) + SACW * (0.25 + 0.75 * vein) + MOUTH * 1.0 + NOD * 0.35 * mott, 0, 1)
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(B + '_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = np.clip(rg, 0.08, 0.95); save(B + '_ORM', orm); del orm
e = np.zeros((RES, RES, 3), np.float32); e[used] = em[:, None]; save(B + '_E', e)
print('TEX OK realm', flush=True)
