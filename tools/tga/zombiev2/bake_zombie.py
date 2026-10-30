# v2 zombie textures (#199, TGA). blender -b zombie_<VARIANT>.blend -P bake_zombie.py    env VARIANT, RES (4096), AO_SAMPLES
# Horse/wasp pipeline: Cycles bakes the data (position, normal, AO), numpy paints to the knowledge-base numbers. Wounds are
# texture + the geometry cuts from build_zombie.py (same masks, evaluated in un-hunched space). No decals (owner rule).
# Out (out/tex): T_ZombieV2_<Var>_<Skin>_BC/_ORM(/_E emissive mask), T_ZombieV2_<Var>_N (DirectX), _N_GL. Skins Pale/Dark/Realm.
import bpy, numpy as np, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '4096'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
VAR = os.environ.get('VARIANT', 'Hollow'); body = bpy.data.objects['SK_ZombieV2_' + VAR]
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
# ---- un-hunch the baked positions so the masks use the same coordinates as build_zombie.py's cuts ------------------
def unhunch(p):
    q = p.copy()
    for _ in range(4):                                                     # fixed point: the bend angle depends on the original z
        a = np.radians(14) * ss(1.05, 1.50, q[:, 2]); dy, dz = p[:, 1], p[:, 2] - 1.05
        q[:, 1] = dy * np.cos(a) + dz * np.sin(a); q[:, 2] = 1.05 - dy * np.sin(a) + dz * np.cos(a)
    return q
U = unhunch(P); x, y, z = U[:, 0], U[:, 1], U[:, 2]; nz = N[:, 2]
mott = fbm(P, 4, 3, 1); mid = fbm(P, 22, 3, 2); micro = vn(P, 260, 3)
cav = 1 - ss(0.45, 0.95, AO); up = ss(0.55, 0.9, nz)
HC = np.array([0, -0.055, 1.603])                                             # measured: smoothing settles the face ~2 cm below HEADC
# face: dark orbits, rotted nasal hole, mouth/teeth line
FR = ss(-0.03, -0.06, y - HC[1])                                              # front of the face only (masks ignore depth: orbits are sunk)
orb = FR * sum(np.exp(-(((x - 0.033 * s) / 0.024) ** 2 + ((z - HC[2] - 0.016) / 0.019) ** 2)) for s in (1, -1))
eye = FR * sum(np.exp(-(((x - 0.034 * s) / 0.008) ** 2 + ((z - HC[2] - 0.014) / 0.007) ** 2)) for s in (1, -1))
nose = np.exp(-np.sum(((U - HC - [0, -0.10, -0.012]) / [0.009, 0.03, 0.011]) ** 2, 1))
mouth = np.exp(-np.sum(((U - HC - [0, -0.09, -0.05]) / [0.028, 0.03, 0.010]) ** 2, 1))
teeth = ss(0.5, 0.7, np.exp(-np.sum(((U - HC - [0, -0.093, -0.038]) / [0.022, 0.03, 0.004]) ** 2, 1))) * (np.sin(x * 900) > -0.6)
# bites / tears scattered on every variant (each has its own seed-shifted set), plus the variant's own wound
bite = ss(0.80, 0.86, fbm(P, 3.5, 3, 30 + len(VAR)))
flesh = np.clip(bite + 0.9 * nose + 0.8 * mouth * (1 - teeth), 0, 1); bone = np.zeros_like(x); ember = np.zeros_like(x)
cloth = np.zeros_like(x); growth = np.zeros_like(x); char = np.zeros_like(x); wet = np.zeros_like(x)
if VAR == 'Bloated':
    tear = np.exp(-((x + 0.01 * np.sin(z * 90)) / 0.02) ** 2 - ((z - 1.08) / 0.08) ** 4) * (y < -0.12); flesh = np.maximum(flesh, ss(0.3, 0.6, tear))
    wet = np.ones_like(x)                                                   # drowned: waterlogged, slick, bluish
if VAR == 'Burnt':
    char = ss(0.35, 0.55, fbm(P, 3, 3, 40) + 0.25 * ss(0.6, 1.2, z))       # worst on the upper body (fire rises)
    q = np.sin(x * 61 + np.sin(z * 37) * 2) * np.sin(z * 53 + np.sin(y * 41) * 2) * np.sin(y * 47 + x * 29)
    ember = ss(0.10, 0.03, np.abs(q)) * char
if VAR == 'Hollow':
    d = np.sqrt(((x - 0.05) / 0.07) ** 2 + ((z - 1.28) / 0.095) ** 2); hole = ss(1.1, 0.8, d) * (y < -0.02)
    bars = (np.cos((z - 1.17) * 2 * np.pi / 0.034) > 0.45) * (np.abs(x - 0.05) < 0.05)
    flesh = np.maximum(flesh, hole * (1 - bars)); bone = np.maximum(bone, hole * bars)
    stub = ss(0.26, 0.29, -x) * ss(1.38, 1.30, z) * ss(1.20, 1.26, z); flesh = np.maximum(flesh, stub); bone = np.maximum(bone, stub * ss(0.02, 0.0, np.abs(z - 1.29)))
if VAR == 'Infected':
    for c0 in ((-0.21, 0.0, 1.42), (0.06, 0.14, 1.25), (-0.15, -0.07, 0.78), (0.045, -0.03, 1.665)):
        growth = np.maximum(growth, ss(0.075, 0.035, np.linalg.norm(U - c0, axis=1)))
if VAR == 'Soldier':
    rad = np.hypot(x, y); cloth = ss(0.66, 0.70, z) * ss(1.30, 1.26, z) * ss(0.215, 0.20, np.abs(x)) * (rad > 0.10)
    cloth = np.maximum(cloth, ss(0.035, 0.025, np.abs(z - 1.445 + 0.0 * x)) * ss(0.14, 0.12, np.abs(x)))   # shoulder strap
if VAR == 'Crawler':
    flesh = np.maximum(flesh, ss(0.80, 0.74, z)); bone = np.maximum(bone, ss(0.725, 0.70, z) * ss(0.03, 0.015, np.abs(np.abs(x) - 0.095)))
vein = ss(0.47, 0.50, fbm(P, 12, 4, 50)) * ss(0.53, 0.50, fbm(P, 12, 4, 50))   # thin ridges of an fbm iso-band
st = vn(P * np.array([1, 1, 0.08], np.float32), 220, 7)                        # dried blood running down from mouth + wounds
src = np.clip(flesh + mouth, 0, 1); streak = ss(0.70, 0.78, st) * ss(0.45, 0.75, fbm(P * np.array([1, 1, 0.15], np.float32), 10, 2, 51) + 0.35 * src) * (1 - cloth) * ss(0.85, 1.05, z)
# ---- height -> normal --------------------------------------------------------------------------------------------
h = 0.00018 * (micro - 0.5) + 0.00035 * (fbm(P, 90, 3, 12) - 0.5)            # wrinkled, dried skin
h += 0.0016 * (fbm(P, 160, 3, 13) - 0.5) * flesh - 0.003 * flesh               # torn fibrous flesh below the skin edge
h += 0.0002 * vein - 0.0006 * ember + 0.0008 * (fbm(P, 50, 3, 14) - 0.5) * char
h += 0.00025 * np.sin(z * 2600 + 6 * fbm(P, 20, 2, 15)) * cloth              # coarse weave
h += 0.0010 * (fbm(P, 70, 3, 16) - 0.5) * growth
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
B = 'T_ZombieV2_' + VAR
g = nrm * 0.5 + 0.5; save(B + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(B + '_N', g); del g, nrm, H, gx, gy
def skin(S):
    col = np.tile(S['skin'], (M, 1)) * (0.84 + 0.32 * mott)[:, None] * (0.94 + 0.12 * mid)[:, None]
    col = mix(col, S['bruise'], ss(0.55, 0.75, fbm(P, 11, 3, 60)) * 0.35)                 # lividity / bruising blotches
    col = mix(col, S['vein'], vein * 0.7); rg = np.full(M, S['r'], np.float32)
    col = mix(col, S['socket'], np.clip(orb * 0.9, 0, 1)); col = mix(col, S['eye'], np.clip(eye, 0, 1))
    col = mix(col, S['flesh'] * (0.8 + 0.4 * fbm(P, 30, 3, 21))[:, None], flesh); rg = np.where(flesh > 0.5, 0.30 + 0.1 * micro, rg)
    col = mix(col, S['bone'] * (0.85 + 0.25 * fbm(P, 40, 3, 22))[:, None], np.clip(bone + teeth, 0, 1)); rg = np.where(bone + teeth > 0.5, 0.55, rg)
    col = mix(col, S['blood'], streak * 0.8); rg = rg - 0.1 * streak
    if VAR == 'Bloated': col = mix(col, lin(118, 132, 128), 0.35 * wet); rg = rg - 0.18 * wet
    if VAR == 'Burnt': col = mix(col, lin(38, 34, 32) * (0.85 + 0.3 * mid)[:, None], char); rg = rg + (0.8 - rg) * char; col = mix(col, lin(150, 62, 30), ember)
    if VAR == 'Infected': col = mix(col, lin(196, 104, 140) * (0.85 + 0.3 * fbm(P, 25, 3, 61))[:, None], growth); rg = np.where(growth > 0.5, 0.25, rg); col = mix(col, lin(170, 70, 120), vein * 0.6)
    if VAR == 'Soldier':
        cc = S['cloth'] * (0.8 + 0.35 * fbm(P, 9, 3, 62))[:, None]; col = mix(col, cc, cloth); rg = rg + (0.86 - rg) * cloth
    col = mix(col, S['grime'], 0.45 * cav); rg = rg + 0.1 * cav
    dirt = ss(0.5, 0.2, z) * 0.6 + up * ss(0.4, 0.7, fbm(P, 10, 3, 23)) * 0.35; col = mix(col, S['dirt'], np.clip(dirt, 0, 1) * (1 - flesh)); rg = rg + 0.1 * dirt
    rg = rg + 0.06 * (micro - 0.5) + 0.08 * (mid - 0.5) + 0.16 * (mott - 0.5) + 0.10 * (fbm(P, 2.5, 2, 63) - 0.5)   # 3-scale, std >= 0.05
    em = np.clip(np.maximum(ember * 1.0, (eye * S['eyeglow'] + vein * S['veinglow'] + growth * 0.5 * (VAR == 'Infected'))), 0, 1)
    if VAR == 'Infected': em = np.maximum(em, np.clip(eye * 1.2, 0, 1))
    return col, np.clip(rg, 0.08, 0.95), em
SK = {'Pale': dict(skin=lin(136, 140, 126), bruise=lin(112, 108, 112), vein=lin(96, 100, 112), socket=lin(44, 36, 34), eye=lin(170, 166, 142), flesh=lin(110, 40, 36),
                   bone=lin(186, 172, 142), blood=lin(70, 32, 28), grime=lin(56, 48, 40), dirt=lin(92, 78, 62), cloth=lin(118, 40, 36), r=0.58, eyeglow=0.0, veinglow=0.0),
      'Dark': dict(skin=lin(92, 70, 56), bruise=lin(70, 56, 54), vein=lin(66, 54, 52), socket=lin(34, 28, 26), eye=lin(160, 150, 120), flesh=lin(104, 38, 34),
                   bone=lin(182, 166, 136), blood=lin(64, 30, 26), grime=lin(44, 36, 30), dirt=lin(88, 74, 58), cloth=lin(52, 62, 96), r=0.56, eyeglow=0.0, veinglow=0.0),
      'Realm': dict(skin=lin(120, 108, 124), bruise=lin(96, 80, 108), vein=lin(170, 70, 130), socket=lin(40, 30, 44), eye=lin(230, 120, 190), flesh=lin(112, 44, 70),
                    bone=lin(180, 168, 160), blood=lin(80, 30, 60), grime=lin(50, 40, 52), dirt=lin(84, 74, 70), cloth=lin(84, 52, 96), r=0.52, eyeglow=1.0, veinglow=0.6)}
for name, S in SK.items():
    col, rg, em = skin(S)
    bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save(f'{B}_{name}_BC', bc); del bc
    orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; save(f'{B}_{name}_ORM', orm); del orm
    if em.max() > 0.05:
        e = np.zeros((RES, RES, 3), np.float32); e[used] = em[:, None]; save(f'{B}_{name}_E', e); del e
print('TEX OK', VAR, flush=True)

