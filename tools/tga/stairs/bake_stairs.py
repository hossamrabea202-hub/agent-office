# Stair kit textures (#279, TGA). blender -b stairs.blend -P bake_stairs.py   env WORK, RES (2048), AO_SAMPLES (128)
# Cycles selected-to-active bake of the 4 high-poly step modules onto the strip atlas: Normal (tangent, saved DirectX),
# AO, high-poly position (-> height). Curvature comes from the baked normal. The PBR maps are then built in numpy from
# those bakes plus the analytic strip layout (which variant, riser/nose/tread, metres across): sandstone matched to the
# castle walls, grime in cavities, joints and the riser feet, lighter worn noses, polished smoother dished tread centres,
# damp + moss at the riser feet of the bottom-step variant.  -> T_StairKit_BC / _ORM / _N (+ _N_GL, _Curv, _H) .png
import bpy, numpy as np, os, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out', 'tex'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '2048'))
from build_stairs import vn, fbm, ss, R, G, B, WM, L1, L2, LP, SU, VARS
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
highs = [bpy.data.objects['High_%d' % k] for k in range(4)]
lows = [bpy.data.objects['BakeLow_%d' % k] for k in range(4)]
for o in sc.objects: o.hide_render = o not in highs + lows; o.select_set(False)
for o in lows: o.select_set(True)
bpy.context.view_layer.objects.active = lows[0]; bpy.ops.object.join(); low = bpy.context.view_layer.objects.active
img = bpy.data.images.new('bake', RES, RES, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
def target_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.nodes.active = t; return m
low.data.materials.clear(); low.data.materials.append(target_mat('M_Target'))
hm = bpy.data.materials.new('M_HighPos'); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
em = nt.nodes.new('ShaderNodeEmission'); outn = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], outn.inputs[0])
nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Position'], em.inputs['Color'])
for h in highs: h.data.materials.clear(); h.data.materials.append(hm); h.select_set(True)
low.select_set(True); bpy.context.view_layer.objects.active = low
bk = sc.render.bake; bk.use_selected_to_active = True; bk.cage_extrusion = 0.035; bk.max_ray_distance = 0.08
bk.margin = 12; bk.margin_type = 'EXTEND'
def bake(kind, samples=1, **kw):
    sc.cycles.samples = samples; bpy.ops.object.bake(type=kind, **kw)
    px = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(px); print('BAKED', kind, flush=True)
    return px.reshape(RES, RES, 4)[..., :3].copy()
NRM = bake('NORMAL', normal_space='TANGENT')                    # OpenGL (+Y) tangent space, 0..1
PH = bake('EMIT')                                               # high-poly surface position per texel
AO = bake('AO', samples=int(os.environ.get('AO_SAMPLES', '128')))[..., 0]

# ---- analytic layout per texel (row 0 = v 0) ----
vv, uu = np.meshgrid((np.arange(RES) + 0.5) / RES, (np.arange(RES) + 0.5) / RES, indexing='ij')
k = np.clip(np.floor((vv - 0.015) / 0.246), 0, 3).astype(int)
lx = np.clip((uu - 0.01) / SU, 0, WM); s = np.clip((vv - 0.015 - k * 0.246) / SU, 0, LP)
inside = ((uu - 0.01) / SU >= 0) & ((uu - 0.01) / SU <= WM) & ((vv - 0.015 - k * 0.246) / SU >= 0) & ((vv - 0.015 - k * 0.246) / SU <= LP)
riser = s < L1; tread = s > L1 + L2; nose = ~riser & ~tread
ty = np.where(tread, B + (s - L1 - L2), np.where(riser, 0.0, (s - L1) / math.sqrt(2)))      # metres back from the riser
tz = np.where(riser, s, R)                                                                     # height in the step
LOWP = np.stack([lx + k * 3.0, ty, tz], -1)
LN = np.where(riser[..., None], [0, -1, 0], np.where(tread[..., None], [0, 0, 1], [0, -0.7071, 0.7071]))
H = np.where(inside, np.clip(((PH - LOWP) * LN).sum(-1), -0.03, 0.03), 0.0)                  # + = high above low (misses clipped)
P = np.stack([lx, ty, tz], -1).reshape(-1, 3) + (k.reshape(-1, 1) * 17.0)                      # noise space per variant

# ---- micro detail added to the baked normal (grain + tool marks + pits), then curvature ----
TPM = SU * RES
grain = fbm(P, 220, 3, 3).reshape(RES, RES); pits = ss(0.78, 0.86, vn(P, 600, 4)).reshape(RES, RES)
hd = 0.00035 * (grain - 0.5) - 0.0005 * pits
gy, gx = np.gradient(hd); n = NRM * 2 - 1
n[..., 0] -= gx * TPM; n[..., 1] -= gy * TPM; n /= np.linalg.norm(n, axis=-1, keepdims=True); n[~inside] = (0, 0, 1)
def blur(a, r):                                                         # separable box blur (summed area)
    for ax in (0, 1):
        c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge'), axis=ax)
        a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a
hp = H - blur(H, 14)                                                    # high-pass of the baked height (~1.4 cm)
hp = np.where(inside, hp, 0.0)
curv = np.clip(blur(hp, 1) / 0.004, -1, 1)                              # + convex (edges, rims), - concave (joints, chips, cracks)
cvx = ss(0.12, 0.6, curv); ccv = ss(0.12, 0.7, -curv)

# ---- material ----
def lin(*c): return np.array([((x / 255 + 0.055) / 1.055) ** 2.4 for x in c], np.float32)
def mix(a, b, t): return a + (b - a) * np.asarray(t, np.float32)[..., None]
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
r2 = lambda a: a.reshape(RES, RES)
big, mid, fine = r2(fbm(P, 1.5, 3, 5)), r2(fbm(P, 9, 3, 6)), r2(fbm(P, 60, 2, 7))
wear = np.array([v['wear'] for v in VARS], np.float32)[k]
centre = np.exp(-((lx - WM / 2) / (0.42 * WM)) ** 2)
polish = tread * wear * centre * ss(0.0, 0.08, ty) * ss(G + 0.02, 0.12, ty) + nose * wear * centre * 0.7
cav = 1 - ss(0.4, 0.95, AO)
foot = riser * (1 - ss(0.0, 0.045, tz))                                  # where the riser meets the tread below
back = tread * ss(G - 0.05, G, ty)                                        # under the next riser
joint = ss(0.35, 0.9, -curv) * (1 - polish)                             # deep, narrow recesses only
col = mix(lin(124, 104, 82), lin(152, 132, 104), big) * (0.9 + 0.2 * mid)[..., None]          # castle sandstone
col = mix(col, lin(108, 92, 76), ss(0.6, 0.75, fine) * 0.5)
col = mix(col, lin(178, 160, 132), cvx * 0.55 * (1 - polish * 0.5))                          # worn, lighter edges
col = mix(col, lin(140, 120, 94) * 0.92, polish * 0.45)                                      # trodden: richer, a touch darker
col = mix(col, lin(56, 46, 36), np.clip(cav * 0.6 + ccv * 0.5 + foot * 0.55 + back * 0.4 + joint * 0.6, 0, 1))   # grime
damp = np.clip(foot * 1.3 + (k == 2) * riser * ss(0.09, 0.0, tz) * 0.6, 0, 1) * (0.6 + 0.8 * (r2(fbm(P, 6, 3, 8)) - 0.5))
damp = np.clip(damp, 0, 1)
col = col * (1 - 0.3 * damp)[..., None]
moss = ss(0.55, 0.7, damp * 0.6 + cav * 0.3 + 0.5 * r2(fbm(P, 14, 3, 9))) * ((k == 2) | (k == 3)) * (1 - polish)
col = mix(col, lin(70, 84, 44) * (0.8 + 0.4 * fine)[..., None], moss * 0.85)
rough = 0.82 + 0.08 * (mid - 0.5) + 0.06 * (fine - 0.5) - 0.38 * polish - 0.1 * cvx * (1 - polish) - 0.25 * damp + 0.08 * cav
rough = np.where(moss > 0.3, 0.9, rough)
ao = np.clip(AO * (1 - 0.5 * foot) * (1 - 0.35 * back), 0, 1)
fill = lambda a, v: np.where(inside[..., None] if a.ndim == 3 else inside, a, v)
def save(name, rgb):
    im = bpy.data.images.new(name, RES, RES, alpha=False); im.colorspace_settings.name = 'Non-Color'
    a = np.ones((RES, RES, 4), np.float32); a[..., :3] = rgb
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
BN = 'T_StairKit'
save(BN + '_BC', fill(to_srgb(col), to_srgb(lin(136, 116, 92))))
save(BN + '_ORM', np.stack([fill(ao, 1.0), fill(np.clip(rough, 0.3, 0.95), 0.82), np.zeros_like(ao)], -1))
g = n * 0.5 + 0.5; save(BN + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(BN + '_N', g)
save(BN + '_Curv', np.repeat((curv * 0.5 + 0.5)[..., None], 3, -1))
save(BN + '_H', np.repeat(np.clip(0.5 + H / 0.04, 0, 1)[..., None], 3, -1))
print('TEX OK stairs inside %.1f%%' % (inside.mean() * 100), flush=True)
