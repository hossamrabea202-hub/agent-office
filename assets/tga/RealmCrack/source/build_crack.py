# Realm mountain crack (#169 stage 3, TGA, 2026-10-30): the glowing fissure the wasp swarm pours out of. Original.
#   blender -b --factory-startup -P build_crack.py     env RES (4096), AO_SAMPLES, TRIS
# A 14 x 11 m rock face (basalt strata, edges curling back so it buries into the slope) split by a jagged fissure about
# 3 m wide that runs 4 m deep into the mountain, with rubble at its foot. Faces -Y in Blender (UE +Y), pivot at the
# bottom centre of the opening, metres, Z up. Textures are made like the creatures: Cycles bakes the data, numpy the
# rest, to the knowledge-base numbers. The glow is a separate emissive mask (hotter with depth + hot veins in the lips).
# Out (out/): SM_RealmCrack.fbx, tex/T_RealmCrack_BC / _ORM / _N (DirectX) / _N_GL / _E (emissive mask), crack.blend
import bpy, numpy as np, math, os
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, 'out'); TEXD = os.path.join(OUT, 'tex'); os.makedirs(TEXD, exist_ok=True)
RES = int(os.environ.get('RES', '4096')); TRIS = int(os.environ.get('TRIS', '26000'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
rng = np.random.default_rng(169)

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

# ---- the fissure: a jagged centre line and a half-width profile up the face ----------------------------------------
CZ = np.linspace(-0.5, 10.5, 23)
CX = np.cumsum(rng.uniform(-0.35, 0.35, len(CZ))) * 0.8; CX -= np.interp(0.0, CZ, CX)
def centre(z): return np.interp(z, CZ, CX)
def halfw(z): return np.interp(z, [-0.5, 0.0, 1.5, 4.0, 6.5, 8.5, 9.6, 10.5], [1.3, 1.4, 1.75, 1.6, 1.1, 0.5, 0.12, 0.0])
DEPTH = 4.0

# ---- rock face: a dense grid displaced by rock noise, then carved -----------------------------------------------------
NX, NZ = 300, 240; W, H = 14.0, 11.0
gx, gz = np.meshgrid(np.linspace(-W / 2, W / 2, NX), np.linspace(-0.6, H - 0.6, NZ))
P = np.stack([gx.ravel(), np.zeros(gx.size), gz.ravel()], 1).astype(np.float32)
x, z = P[:, 0], P[:, 2]
strata = 0.12 * np.sin(z * 2.6 + 1.5 * fbm(P, 0.4, 3, 1)) ** 3                      # tilted basalt layers stand proud
y = -(0.75 * (fbm(P, 0.18, 5, 2) - 0.5) + strata + 0.25 * (fbm(P, 1.1, 4, 3) - 0.5))   # front = -Y
edge = np.maximum(np.abs(x) / (W / 2), np.clip((z - (H - 3.0)) / 3.0, 0, 1))
y += 3.2 * ss(0.55, 1.0, edge) ** 1.5                                                 # curls back into the mountain
dx = x - centre(z); hw = halfw(z) * (1 + 0.25 * (fbm(P * np.array([1, 1, 3], np.float32), 0.8, 3, 4) - 0.5))
inside = np.clip((hw - np.abs(dx)) / np.maximum(hw, 1e-3), 0, 1)
lip = ss(0.0, 0.25, -np.abs(dx) + hw + 0.35) * (1 - ss(0.0, 0.05, inside))            # broken lips flare outward
y -= 0.35 * lip * (fbm(P, 2.0, 3, 5) + 0.3)
y += DEPTH * ss(0.0, 0.45, inside) ** 0.7 * (1 + 0.15 * (fbm(P, 1.5, 3, 6) - 0.5))      # steep walls, deep back
P[:, 1] = y
faces = []
for j in range(NZ - 1):
    for i in range(NX - 1):
        a = j * NX + i; faces.append((a, a + 1, a + NX + 1, a + NX))
verts = [tuple(v) for v in P]
# rubble at the foot of the opening: fallen blocks, half buried
for k in range(10):
    c = np.array([centre(0.0) + rng.uniform(-3.2, 3.2), rng.uniform(-1.6, -0.2), rng.uniform(-0.3, 0.1)])
    r = rng.uniform(0.25, 0.75); n = 14
    th, ph = np.meshgrid(np.linspace(0, np.pi, n), np.linspace(0, 2 * np.pi, n * 2, endpoint=False), indexing='ij')
    S = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1).reshape(-1, 3)
    S = S * (r * (0.75 + 0.5 * fbm(S.astype(np.float32) + k, 1.3, 3, 20 + k)))[:, None] * np.array([1.2, 1.0, 0.7]) + c
    off = len(verts); verts += [tuple(v) for v in S]
    for a in range(n - 1):
        for b in range(n * 2):
            b1 = (b + 1) % (n * 2); faces.append((off + a * n * 2 + b, off + a * n * 2 + b1, off + (a + 1) * n * 2 + b1, off + (a + 1) * n * 2 + b))
me = bpy.data.meshes.new('SM_RealmCrack'); me.from_pydata(verts, [], faces); me.update()
ob = bpy.data.objects.new('SM_RealmCrack', me); bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.001); bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
n0 = len(me.polygons) * 2
dm = ob.modifiers.new('Decimate', 'DECIMATE'); dm.ratio = min(1.0, TRIS / n0); bpy.ops.object.modifier_apply(modifier='Decimate')
bpy.ops.object.shade_smooth()
print('CRACK tris', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- data bakes -----------------------------------------------------------------------------------------------------
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
me.materials.append(mat); geo = nt.nodes.new('ShaderNodeNewGeometry'); one = nt.nodes.new('ShaderNodeRGB'); one.outputs[0].default_value = (1, 1, 1, 1)
def bake(kind, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = 16; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
nt.links.new(one.outputs[0], em.inputs['Color']); used = bake('EMIT')[..., 0] > 0.5
nt.links.new(geo.outputs['Position'], em.inputs['Color']); Q = bake('EMIT')[used]
nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
mat2 = bpy.data.materials.new('M_AO'); mat2.use_nodes = True; t2 = mat2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; mat2.node_tree.nodes.active = t2
me.materials.clear(); me.materials.append(mat2)
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '128')))[..., 0][used]
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv); ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
d3 = np.linalg.norm(co[lv[ls + 1]] - co[lv[ls]], axis=1); d2 = np.linalg.norm(uv[ls + 1] - uv[ls], axis=1); ok = d3 > 1e-4
TPM = float(np.median(d2[ok] / d3[ok])) * RES; M = int(used.sum()); print('TEXEL DENSITY %.0f px/m' % TPM, flush=True)

# ---- textures -------------------------------------------------------------------------------------------------------
def lin(*s): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in s], np.float32)
def mix(a, b, t): t = np.asarray(t, np.float32); return a + (b - a) * (t[:, None] if t.ndim else t)
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
qx, qy, qz = Q[:, 0], Q[:, 1], Q[:, 2]; nz = N[:, 2]
mott = fbm(Q, 0.5, 4, 30); mid = fbm(Q, 4, 3, 31); micro = vn(Q, 60, 32)
cav = 1 - ss(0.4, 0.95, AO)
depth = np.clip(qy / DEPTH, 0, 1) * ss(1.0, 0.4, np.abs(qx - centre(qz)) / np.maximum(halfw(qz), 0.2))   # how far into the fissure
near = ss(2.6, 0.0, np.abs(qx - centre(qz)) - halfw(qz))                                              # rock around the opening
veins = (1 - ss(0.0, 0.005, np.abs(fbm(Q, 0.7, 4, 33) - 0.5))) * near ** 2 * ss(0.5, 0.75, fbm(Q, 0.6, 3, 34))   # few, thin, close to the lips
strata_c = np.sin(qz * 2.6 + 1.5 * fbm(Q, 0.4, 3, 1))
h = 0.012 * (fbm(Q, 8, 4, 35) - 0.5) + 0.004 * (fbm(Q, 40, 3, 36) - 0.5) + 0.01 * ss(0.7, 0.95, strata_c)   # fracture + grain
h -= 0.008 * veins
Hh = np.zeros((RES, RES), np.float32); Hh[used] = h
g1, g0 = np.gradient(Hh); g0 *= TPM; g1 *= TPM
nrm = np.stack([-g0, -g1, np.ones_like(g0)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb; im.pixels.foreach_set(np.clip(a, 0, 1).ravel())
    im.filepath_raw = os.path.join(TEXD, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
gl = nrm * 0.5 + 0.5; save('T_RealmCrack_N_GL', gl); gl[..., 1] = 1 - gl[..., 1]; save('T_RealmCrack_N', gl); del gl, nrm, Hh, g0, g1
# basalt: grey-brown, strata bands, lichen on ledges, rust-dark mineral streaks running down from the fissure,
# heat-scorched (darker, reddish) round the opening, ash-grey dust on up-facing ledges
col = np.tile(lin(92, 86, 80), (M, 1)) * (0.8 + 0.4 * mott)[:, None] * (0.92 + 0.16 * mid)[:, None]
col = mix(col, lin(108, 100, 92), 0.3 * ss(0.5, 0.9, strata_c))
rg = 0.78 + 0.06 * (micro - 0.5) + 0.06 * (mid - 0.5) + 0.08 * (mott - 0.5)
lichen = ss(0.55, 0.85, nz) * ss(0.55, 0.7, fbm(Q, 3, 3, 37)) * (1 - near)
col = mix(col, lin(118, 122, 96), 0.7 * lichen)
streak = ss(0.6, 0.72, vn(Q * np.array([1, 1, 0.08], np.float32), 6, 38)) * ss(3.5, 0.5, np.abs(qx - centre(qz)) - halfw(qz)) * ss(9, 2, qz)
col = mix(col, lin(70, 54, 44), 0.6 * streak); rg = rg - 0.1 * streak
scorch = near * (1 - depth); col = mix(col, lin(58, 44, 38), 0.65 * scorch); rg = rg + 0.05 * scorch
inner = ss(0.15, 0.6, depth); col = mix(col, lin(64, 46, 36), inner); rg = np.where(inner > 0.5, 0.55 + 0.1 * micro, rg)   # glassy, heat-fused
col = mix(col, lin(52, 46, 42), 0.35 * cav); rg = rg + 0.06 * cav
dust = ss(0.6, 0.9, nz) * ss(0.45, 0.7, fbm(Q, 5, 3, 39)) * 0.4 * (1 - inner)
col = mix(col, lin(140, 132, 120), dust); rg = rg + 0.08 * dust
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save('T_RealmCrack_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = np.clip(rg, 0.1, 0.95); save('T_RealmCrack_ORM', orm); del orm
glow = np.clip(ss(0.25, 0.9, depth) * (0.6 + 0.4 * fbm(Q, 1.2, 3, 40)) + 0.45 * veins * (1 - inner), 0, 1)
e = np.zeros((RES, RES, 3), np.float32); e[used] = glow[:, None]; save('T_RealmCrack_E', e); del e
print('TEX OK', flush=True)

# ---- export ---------------------------------------------------------------------------------------------------------
me.materials.clear(); me.materials.append(bpy.data.materials.get('M_RealmCrack') or bpy.data.materials.new('M_RealmCrack'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'crack.blend'))
for o in sc.objects: o.select_set(o == ob)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_RealmCrack.fbx'), use_selection=True, object_types={'MESH'},
                         mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL', bake_anim=False)
print('FBX OK', flush=True)
