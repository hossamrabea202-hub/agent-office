# #402 Destrier tack + barding textures. checkking (Claude), 2026-11-01.
#   blender -b <work>/destrier_anim.blend -P bake_tack.py -- <work>       env RES (2048), AO_SAMPLES
# Data bakes (position, normal, AO, part id from the vertex colour), then numpy paints by part and by cause:
#   wool caparison + neck cover: the castle's arms, Or an eagle sable (the Yellow Eagle set), weld-yellow wool with black
#     eagles displayed on both flanks facing the head, a black hem band; twill weave, fuzz-rough (0.8-0.96, INDUSTRY_SECRETS 1.1),
#     mud splashed up the hem by the hooves, dust on top, darker sweat-damp cloth under the saddle edges
#   strap leather: dark brown, edges rubbed lighter, glossier where hands and reins rub; seat: red-brown leather
#   steel (chanfron, bit, stirrups): bare >= 180 sRGB metallic 1, roughness 0.22-0.45 with scratches; oxide spots non-metal
#   saddle bows: leather over wood painted dark red
# Out (out/tex): T_DestrierTack_BC / _ORM / _N (DirectX) / _N_GL.
import bpy, numpy as np, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cavlib import lin, to_srgb, ss, mix
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
D = argv[0] if argv else os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '2048'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
tack = bpy.data.objects['SK_Destrier_Tack']
arm = bpy.data.objects['SK_Destrier_Rig']; arm.animation_data.action = None
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
for o in sc.objects:
    if o.type == 'MESH' and o.name not in ('SK_Destrier_Tack', 'SK_Destrier'): o.hide_render = True
mat = bpy.data.materials.new('M_Bake'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; nt.nodes.active = tex
keep = list(tack.data.materials); tack.data.materials.clear(); tack.data.materials.append(mat)
for o in sc.objects: o.select_set(False)
tack.select_set(True); bpy.context.view_layer.objects.active = tack
geo = nt.nodes.new('ShaderNodeNewGeometry'); one = nt.nodes.new('ShaderNodeRGB'); one.outputs[0].default_value = (1, 1, 1, 1)
attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'Part'
def bake(kind, samples=1):
    sc.cycles.samples = samples; sc.render.bake.margin = 8; sc.render.bake.margin_type = 'EXTEND'; sc.render.bake.target = 'IMAGE_TEXTURES'
    bpy.ops.object.bake(type=kind); px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px)
    print('BAKED', kind, flush=True); return px.reshape(RES, RES, 4)[..., :3].copy()
nt.links.new(one.outputs[0], em.inputs['Color']); used = bake('EMIT')[..., 0] > 0.5
nt.links.new(geo.outputs['Position'], em.inputs['Color']); P = bake('EMIT')[used]
nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bake('EMIT')[used]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-6
nt.links.new(attr.outputs['Color'], em.inputs['Color']); PID = np.round(bake('EMIT')[used][:, 0] * 10).astype(np.int32)
mat2 = bpy.data.materials.new('M_AO'); mat2.use_nodes = True; t2 = mat2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; mat2.node_tree.nodes.active = t2
tack.data.materials.clear(); tack.data.materials.append(mat2)
if sc.world is None: sc.world = bpy.data.worlds.new('W')
sc.world.light_settings.distance = 0.5
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '64')))[..., 0][used]
tack.data.materials.clear()
for m in keep: tack.data.materials.append(m)
M = int(used.sum())
me = tack.data; uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
d3 = np.linalg.norm(co[lv[ls + 1]] - co[lv[ls]], axis=1); d2 = np.linalg.norm(uv[ls + 1] - uv[ls], axis=1)
ok = d3 > 1e-4; TPM = float(np.median(d2[ok] / d3[ok])) * RES; print('TEXEL DENSITY %.0f px/m' % TPM, 'parts', np.bincount(PID), flush=True)

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

# ---- the heraldic eagle (displayed, head to the front), as a 2D signed distance field; units: eagle height = 1
def cap(px, py, ax, ay, bx, by, r):
    vx, vy = bx - ax, by - ay; wx, wy = px - ax, py - ay
    t = np.clip((wx * vx + wy * vy) / (vx * vx + vy * vy + 1e-9), 0, 1)
    return np.hypot(wx - t * vx, wy - t * vy) - r
def tcap(px, py, ax, ay, bx, by, r0, r1):
    """tapered capsule: radius r0 at a -> r1 at b (pointed heraldic feathers)."""
    vx, vy = bx - ax, by - ay; wx, wy = px - ax, py - ay
    t = np.clip((wx * vx + wy * vy) / (vx * vx + vy * vy + 1e-9), 0, 1)
    return np.hypot(wx - t * vx, wy - t * vy) - (r0 + (r1 - r0) * t)
def ell(px, py, cx, cy, rx, ry): return (np.hypot((px - cx) / rx, (py - cy) / ry) - 1) * min(rx, ry)
def eagle(u, v):
    d = ell(u, v, 0, 0, 0.10, 0.21)                                          # body
    d = np.minimum(d, cap(u, v, 0.0, 0.16, 0.07, 0.27, 0.05))                 # neck
    d = np.minimum(d, ell(u, v, 0.09, 0.30, 0.075, 0.065))                    # head
    beak = np.minimum(tcap(u, v, 0.13, 0.32, 0.22, 0.30, 0.03, 0.008), tcap(u, v, 0.21, 0.305, 0.215, 0.255, 0.012, 0.004))   # hooked
    d = np.minimum(d, beak)
    for s in (1, -1):                                                          # wings: arm + 5 primaries
        d = np.minimum(d, cap(u, v, 0.05 * s, 0.12, 0.27 * s, 0.30, 0.055))
        for k in range(6):                                                     # primaries fan out and up from the wrist
            th_ = math.radians(-8 + 22 * k); L = 0.34 - 0.025 * k; ax_, ay_ = 0.22 * s, 0.27
            d = np.minimum(d, tcap(u, v, ax_, ay_, ax_ + s * L * math.cos(th_), ay_ + L * math.sin(th_), 0.042 - 0.003 * k, 0.006))
        for k in range(4):                                                     # secondaries hang below the arm
            ax_ = (0.08 + 0.05 * k) * s; ay_ = 0.15 + 0.04 * k
            d = np.minimum(d, tcap(u, v, ax_, ay_, ax_ + 0.05 * s, ay_ - 0.20 + 0.02 * k, 0.035, 0.005))
        d = np.minimum(d, cap(u, v, 0.06 * s, -0.12, 0.17 * s, -0.30, 0.03))  # legs
        for k in range(3): d = np.minimum(d, tcap(u, v, 0.17 * s, -0.30, (0.17 + 0.06 * (k - 1)) * s, -0.38, 0.016, 0.003))   # talons
    for k in range(5): d = np.minimum(d, tcap(u, v, 0.0, -0.15, 0.06 * (k - 2), -0.47 + 0.02 * abs(k - 2), 0.045, 0.006))   # tail
    return d, beak

x, y, z = P[:, 0], P[:, 1], P[:, 2]; nz = N[:, 2]
mott = fbm(P, 4, 3, 1); mid = fbm(P, 24, 3, 2); micro = vn(P, 300, 3)
cav = 1 - ss(0.5, 0.95, AO); up = ss(0.5, 0.9, nz)
wool = (PID == 1) | (PID == 2); leather = PID == 3; seat = PID == 4; steel = PID == 5; bowp = PID == 6

YELLOW = lin(180, 146, 64); BLACK = lin(46, 42, 40); RED = lin(128, 44, 34)
col = np.zeros((M, 3), np.float32); rg = np.zeros(M, np.float32); mt = np.zeros(M, np.float32); h = np.zeros(M, np.float32)
# -- wool: twill weave (diagonal ribs) + fuzz; arms on the flanks
weave = 0.5 + 0.5 * np.sin((y * 1.0 + z * 1.0 + x * 0.3) * 2 * np.pi * 280)
col[wool] = YELLOW * (0.90 + 0.18 * mott[wool])[:, None] * (0.96 + 0.06 * weave[wool])[:, None]
side = (np.abs(N[:, 0]) > 0.35) & (PID == 1)
ed = np.full(M, 9.0, np.float32); bk = np.full(M, 9.0, np.float32)
for yc, zc, sz in ((-0.78, 1.00, 0.62), (0.56, 1.04, 0.66)):              # shoulder + hindquarter, clear of the saddle flaps
    e_, b_ = eagle(-(y - yc) / sz, (z - zc) / sz)                          # faces the head (-Y) on both flanks
    ed = np.minimum(ed, e_ * sz); bk = np.minimum(bk, b_ * sz)
emask = ss(0.004, -0.004, ed) * side
col = mix(col, BLACK * (0.9 + 0.15 * mott)[:, None], emask)
col = mix(col, RED, ss(0.004, -0.004, bk) * side)
hem = ss(0.70, 0.68, z) * (PID == 1)                                       # black hem band, 6 cm
neckhem = (PID == 2) * ss(1.30, 1.27, z)
col = mix(col, BLACK * (0.9 + 0.15 * mott)[:, None], np.clip(hem + neckhem, 0, 1))
rg[wool] = 0.88 + 0.05 * (weave[wool] - 0.5) + 0.04 * (micro[wool] - 0.5)
h[wool] = 0.0003 * weave[wool] + 0.0004 * (fbm(P[wool], 60, 2, 5) - 0.5)
splash = ss(0.80, 0.64, z) * ss(0.55, 0.75, fbm(P, 9, 3, 6) + 0.3 * ss(0.75, 0.62, z)) * (PID == 1)   # hooves throw mud at the hem
col = mix(col, lin(86, 70, 54) * (0.85 + 0.3 * mott)[:, None], splash * 0.8); rg = rg + 0.04 * splash
damp = (PID == 1) * np.exp(-(((y + 0.18) / 0.36) ** 2)) * ss(1.25, 1.45, z) * ss(0.48, 0.6, fbm(P, 6, 3, 7))  # sweat under the saddle
col = mix(col, col * 0.78, damp * 0.6); rg = rg - 0.08 * damp
# -- leather straps and flaps
LB = lin(72, 50, 36)
col[leather] = LB * (0.85 + 0.3 * mott[leather])[:, None] * (0.95 + 0.1 * mid[leather])[:, None]
edgew = ss(0.85, 1.0, AO) * ss(0.4, 0.8, fbm(P, 40, 2, 8))
col[leather] = mix(col[leather], lin(104, 76, 54), 0.5 * edgew[leather])
rg[leather] = 0.62 - 0.12 * edgew[leather] + 0.06 * (mid[leather] - 0.5)
h[leather] = 0.00025 * (vn(P[leather], 600, 9) - 0.5)
col[seat] = lin(92, 56, 40) * (0.88 + 0.24 * mott[seat])[:, None]
rg[seat] = 0.55 - 0.1 * up[seat] + 0.05 * (mid[seat] - 0.5); h[seat] = 0.0003 * (vn(P[seat], 500, 10) - 0.5)
col[bowp] = lin(100, 40, 32) * (0.9 + 0.2 * mott[bowp])[:, None]
chip = ss(0.82, 0.9, fbm(P, 30, 3, 11)) * ss(0.8, 1.0, AO)
col[bowp] = mix(col[bowp], lin(84, 64, 48), chip[bowp]); rg[bowp] = 0.45 + 0.25 * chip[bowp]
# -- steel
scr = ss(0.86, 0.95, vn(P * np.array([1, 1, 8], np.float32), 120, 12))
ox = ss(0.68, 0.78, fbm(P, 14, 3, 13)) * (1 - ss(0.9, 1.0, AO) * 0.5)
col[steel] = lin(196, 194, 190) * (0.96 + 0.06 * mid[steel])[:, None]
rg[steel] = 0.30 + 0.10 * (mid[steel] - 0.5) + 0.12 * scr[steel] - 0.05 * up[steel]
mt[steel] = 1.0
oxm = steel & (ox > 0.5)
col[oxm] = lin(92, 70, 56); rg[oxm] = 0.8; mt[oxm] = 0.0
# shared: cavity grime + dust on top (one dirt pass for every part, rule 10)
col = mix(col, col * 0.75, 0.35 * cav * (1 - steel)); rg = rg + 0.05 * cav
dust = up * ss(0.45, 0.7, fbm(P, 10, 3, 23)) * 0.3 * (1 - steel)
col = mix(col, lin(134, 122, 104), dust); rg = rg + 0.08 * dust
col = np.clip(col, lin(30, 30, 30)[None] * 0 + 0.012, 1); rg = np.clip(rg, 0.05, 0.97)

def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
bc = np.zeros((RES, RES, 3), np.float32); bc[used] = to_srgb(col); save('T_DestrierTack_BC', bc); del bc
orm = np.zeros((RES, RES, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; orm[used, 2] = mt; save('T_DestrierTack_ORM', orm); del orm
H = np.zeros((RES, RES), np.float32); H[used] = h
gy, gx = np.gradient(H); gx *= TPM; gy *= TPM
nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
g = nrm * 0.5 + 0.5; save('T_DestrierTack_N_GL', g); g[..., 1] = 1 - g[..., 1]; save('T_DestrierTack_N', g)
print('TACK TEX OK', flush=True)
