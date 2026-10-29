# Photoreal retexture of an existing game prop (laptop2, 2026-10-29), to the knowledge-base standard.
#   blender -b --factory-startup -P retex.py -- <mesh.fbx> <BaseColor> [ORM|-] [Normal|-] <out_dir> [size] [grip_axis x|y|z]
# Keeps the prop's own design (its BaseColor layout, its normal map) and rebuilds the surface physically:
#   1. classify every texel by the original BaseColor/metallic into metal, gilded metal, wood, leather/cord, other
#   2. recalibrate the albedo into PBR ranges (non-metal 30..240 sRGB, metal >= 180 sRGB, metallic strictly 0/1)
#   3. layer wear in physical order: edges (ray bevel) brighter or bare, cavities (AO) grimed, up-facing dust,
#      scratches on metal, wood grain detail, hand polish where it is held, 3-scale roughness variation
#   4. bake BaseColor / ORM / Normal (original normal + new micro detail) on the same UVs, then run pbr_check
import bpy, sys, os, math
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
FBX, BC = args[0], args[1]
ORM = None if args[2] == '-' else args[2]; NRM = None if args[3] == '-' else args[3]
OUT = args[4]; SIZE = int(args[5]) if len(args) > 5 else 4096; GAX = args[6] if len(args) > 6 else 'z'
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _mul_col

if FBX.lower().endswith('.fbx'): bpy.ops.import_scene.fbx(filepath=FBX)
else: bpy.ops.wm.append(directory=FBX + '/Object/', filename=args[7] if len(args) > 7 else 'SM')
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
size = max(ob.dimensions); print('RETEX', ob.name, 'size', round(size, 3), 'm, tris', sum(len(p.vertices) - 2 for p in ob.data.polygons))
S = 1.0 / max(size, 1e-3)          # noise scales are written for a ~1 m prop

def img(path, cs):
    im = bpy.data.images.load(path); im.colorspace_settings.name = cs; return im
m = bpy.data.materials.new('RETEX'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
ob.data.materials.clear(); ob.data.materials.append(m)
uvn = _n(nt, 'ShaderNodeUVMap'); uvn.uv_map = ob.data.uv_layers.active.name
def tex(path, cs):
    t = _n(nt, 'ShaderNodeTexImage', interpolation='Linear'); t.image = img(path, cs); nt.links.new(uvn.outputs[0], t.inputs['Vector']); return t
tb = tex(BC, 'sRGB')
orig = tb.outputs['Color']
if ORM:
    to = tex(ORM, 'Non-Color'); so = _sep(nt, to.outputs['Color']); met0, rg0 = so[2], so[1]
else:
    met0, rg0 = None, None
co = _co(nt); co = _scale(nt, co, S, S, S)
edge = _edge(nt, 0.0025 * size); cav, ao = _cav(nt, 0.03 * size)
g = _n(nt, 'ShaderNodeNewGeometry'); nz = _sep(nt, g.outputs['Normal'])[2]
hsv = _n(nt, 'ShaderNodeSeparateColor', mode='HSV'); nt.links.new(orig, hsv.inputs[0]); H, Sat, Val = hsv.outputs[0], hsv.outputs[1], hsv.outputs[2]
# --- classes (soft masks) ---
if met0 is not None:
    metal = _maprange(nt, met0, 0.35, 0.65)
else:   # no metallic map: bright desaturated or yellow-saturated-bright texels are metal
    metal = _math(nt, 'MAXIMUM', _math(nt, 'MULTIPLY', _maprange(nt, Val, 0.35, 0.55), _maprange(nt, Sat, 0.35, 0.15)),
                  _math(nt, 'MULTIPLY', _maprange(nt, Val, 0.45, 0.65), _maprange(nt, Sat, 0.35, 0.55)))
gold = _math(nt, 'MULTIPLY', metal, _math(nt, 'MULTIPLY', _maprange(nt, H, 0.06, 0.10), _maprange(nt, H, 0.17, 0.13)))
gold = _math(nt, 'MULTIPLY', gold, _maprange(nt, Sat, 0.25, 0.45))
nonm = _math(nt, 'SUBTRACT', 1.0, metal, True)
woodm = _math(nt, 'MULTIPLY', nonm, _math(nt, 'MULTIPLY', _maprange(nt, H, 0.02, 0.05), _maprange(nt, H, 0.14, 0.10)))
woodm = _math(nt, 'MULTIPLY', woodm, _math(nt, 'MULTIPLY', _maprange(nt, Sat, 0.18, 0.35), _maprange(nt, Val, 0.06, 0.15)))
# --- recalibrated base: keep the hue/pattern, put values into PBR range ---
lum = _n(nt, 'ShaderNodeRGBToBW'); nt.links.new(orig, lum.inputs[0])
# non-metal: lift the floor to >= ~0.02 linear (30 sRGB), cap at 0.85, desaturate a touch (CG colour is over-saturated)
desat = _mix_col(nt, 0.12, orig, lum.outputs[0])
nm_col = _mix_col(nt, _maprange(nt, lum.outputs[0], 0.02, 0.0), desat, (0.035, 0.030, 0.026))
# metal: reflectance from the original hue, value pushed to 0.5..0.75 linear (180..225 sRGB)
steel = _mix_col(nt, _noise(nt, co, 20, 4, 0.6), (0.50, 0.50, 0.50), (0.62, 0.61, 0.59))
goldc = _mix_col(nt, _noise(nt, co, 25, 4, 0.6), (0.80, 0.58, 0.28), (0.95, 0.72, 0.38))
mt_col = _mix_col(nt, gold, steel, goldc)          # bare metal = calibrated reflectance; the design's darkness becomes the oxide layer
col = _mix_col(nt, metal, nm_col, mt_col)
# where the original metal was painted dark (old iron, blackened steel), real life has bright metal under a dark oxide /
# mill-scale film: a NON-metal layer. Keep the designer's dark look that way; edges get rubbed back to bare metal below.
oxide = _math(nt, 'MULTIPLY', metal, _maprange(nt, Val, 0.42, 0.14))
oxide = _math(nt, 'MULTIPLY', oxide, _maprange(nt, _noise(nt, co, 14, 5, 0.6), 0.38, 0.58, 0.0, 1.0))   # patchy: bare metal shows through
oxide = _math(nt, 'MULTIPLY', oxide, _math(nt, 'SUBTRACT', 1.0, gold, True))
ox_col = _mix_col(nt, _noise(nt, co, 30, 4, 0.6), (0.040, 0.037, 0.034), (0.070, 0.062, 0.055))
# --- detail & wear ---
grain = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction=GAX.upper(), in_Scale=60.0, in_Distortion=8.0, in_Detail=6.0)
nt.links.new(co, grain.inputs['Vector'])
gm = _maprange(nt, grain.outputs['Fac'], 0.2, 0.9)
col = _mix_col(nt, _math(nt, 'MULTIPLY', woodm, _math(nt, 'MULTIPLY', gm, 0.35)), col, _mul_col(nt, col, 0.55))
# edges: metal edges rubbed bright, wood edges lighter and drier, paint/leather edges worn
ew = _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.15), _maprange(nt, _noise(nt, co, 90, 4, 0.6), 0.38, 0.62))
oxv = _math(nt, 'MULTIPLY', oxide, _math(nt, 'SUBTRACT', 1.0, _maprange(nt, ew, 0.2, 0.5), True))   # oxide left where not rubbed
col = _mix_col(nt, oxv, col, ox_col)
col = _mix_col(nt, _math(nt, 'MULTIPLY', ew, _mix_f(nt, metal, 0.35, 0.7)), col, _mix_col(nt, metal, _mul_col(nt, col, 1.35), (0.66, 0.65, 0.62)))
# cavities: grime and old oil
grime = _maprange(nt, cav, 0.12, 0.7, 0, 0.8)
col = _mix_col(nt, _math(nt, 'MULTIPLY', grime, _mix_f(nt, metal, 1.0, 0.35)), col, (0.035, 0.028, 0.020))   # bare metal stays bright unless grime covers it (then it's non-metal)
# metal: patina in hollows, fine scratches everywhere
patina = _math(nt, 'MULTIPLY', metal, _math(nt, 'MULTIPLY', _maprange(nt, cav, 0.05, 0.4), _maprange(nt, _noise(nt, co, 9, 4, 0.6), 0.45, 0.7)))
col = _mix_col(nt, _math(nt, 'MULTIPLY', patina, 0.45), col, _mix_col(nt, gold, (0.30, 0.27, 0.24), (0.40, 0.30, 0.14)))   # light tarnish while still metal; heavy patina flips to non-metal below
scr = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', in_Scale=900.0, in_Distortion=18.0, in_Detail=3.0)
nt.links.new(co, scr.inputs['Vector'])
scm = _math(nt, 'MULTIPLY', metal, _math(nt, 'MULTIPLY', _maprange(nt, scr.outputs['Fac'], 0.93, 1.0), _maprange(nt, _noise(nt, co, 12, 2, 0.5), 0.5, 0.68)))
col = _mix_col(nt, _math(nt, 'MULTIPLY', scm, 0.6), col, (0.85, 0.84, 0.82))
# dust on up-facing surfaces, very light
col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, nz, 0.6, 0.95), 0.18), col, (0.22, 0.20, 0.17))
# --- roughness: 3 scales, physics-driven ---
r_micro = _noise(nt, co, 400, 3, 0.6); r_mid = _noise(nt, co, 40, 4, 0.6); r_mac = _noise(nt, co, 4, 3, 0.5)
rg_nm = _mix_f(nt, r_micro, 0.62, 0.80); rg_nm = _mix_f(nt, _maprange(nt, r_mac, 0.3, 0.7), rg_nm, 0.74)
rg_nm = _mix_f(nt, woodm, rg_nm, _mix_f(nt, gm, 0.70, 0.85))
rg_mt = _mix_f(nt, r_mid, 0.22, 0.38); rg_mt = _mix_f(nt, _math(nt, 'MULTIPLY', r_micro, 0.4), rg_mt, 0.45)
rg_mt = _mix_f(nt, scm, rg_mt, 0.30); rg_mt = _mix_f(nt, patina, rg_mt, 0.55)
rg = _mix_f(nt, metal, rg_nm, rg_mt)
rg = _mix_f(nt, oxv, rg, _mix_f(nt, r_mid, 0.55, 0.72))
rg = _mix_f(nt, _math(nt, 'MULTIPLY', ew, 0.6), rg, _mix_f(nt, metal, 0.88, 0.16))
rg = _mix_f(nt, grime, rg, 0.85)
# metallic strictly 0/1: metal where metal and not covered by oxide, patina or heavy grime
cover = _math(nt, 'MAXIMUM', _math(nt, 'MAXIMUM', _maprange(nt, grime, 0.55, 0.6), _maprange(nt, patina, 0.45, 0.5)), _maprange(nt, oxv, 0.48, 0.52))
mt = _math(nt, 'MULTIPLY', _maprange(nt, metal, 0.49, 0.51), _math(nt, 'SUBTRACT', 1.0, cover, True))
# --- normal: the original normal map + micro detail (grain on wood, hammer and scratches on metal) ---
nrm = None
if NRM:
    tn = tex(NRM, 'Non-Color'); nm_ = _n(nt, 'ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm_.inputs['Color']); nrm = nm_.outputs['Normal']
bump = _n(nt, 'ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.0006 * size
hgt = _math(nt, 'ADD', _math(nt, 'MULTIPLY', woodm, gm), _math(nt, 'MULTIPLY', metal, _math(nt, 'ADD', _math(nt, 'MULTIPLY', r_mid, 0.4), _math(nt, 'MULTIPLY', scm, -0.6))))
nt.links.new(hgt, bump.inputs['Height'])
if nrm is not None: nt.links.new(nrm, bump.inputs['Normal'])
for key, sock in (('BC', col), ('RG', rg), ('MT', mt), ('AO', ao)):
    rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_' + key; nt.links.new(sock, rr.inputs[0])
bsdf = _n(nt, 'ShaderNodeBsdfPrincipled'); bsdf.name = 'BSDF'
nt.links.new(col, bsdf.inputs['Base Color']); nt.links.new(rg, bsdf.inputs['Roughness']); nt.links.new(mt, bsdf.inputs['Metallic'])
nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
em = _n(nt, 'ShaderNodeEmission'); out = _n(nt, 'ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
# --- bake on the prop's own UVs ---
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32
sc.render.bake.margin = 16; sc.render.bake.use_selected_to_active = False
tnode = _n(nt, 'ShaderNodeTexImage'); nt.nodes.active = tnode
res = {}
for ch in ('BC', 'RG', 'MT', 'AO', 'Normal'):
    im = bpy.data.images.new('b_' + ch, SIZE, SIZE, alpha=False, float_buffer=True); im.colorspace_settings.name = 'Non-Color'; tnode.image = im
    if ch == 'Normal':
        nt.links.new(bsdf.outputs[0], out.inputs['Surface']); sc.render.bake.normal_space = 'TANGENT'; bpy.ops.object.bake(type='NORMAL')
    else:
        nt.links.new(nt.nodes['OUT_' + ch].outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface']); bpy.ops.object.bake(type='EMIT')
    a = np.empty(SIZE * SIZE * 4, np.float32); im.pixels.foreach_get(a); res[ch] = a.reshape(SIZE, SIZE, 4); print('baked', ch, flush=True)
def save(arr, name, depth='8'):
    im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=(depth == '16')); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    if depth == '16': im.use_half_precision = False
    im.save()
srgb = lambda l: np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(np.maximum(l, 0), 1 / 2.4) - 0.055)
one = np.ones((SIZE, SIZE), np.float32)
base = os.path.splitext(os.path.basename(FBX))[0]
save(np.stack([srgb(res['BC'][..., k]) for k in range(3)] + [one], -1), base + '_Real_BaseColor')
save(np.stack([res['AO'][..., 0], res['RG'][..., 0], res['MT'][..., 0], one], -1), base + '_Real_ORM')
n = [res['Normal'][..., k] for k in range(3)]; n[1] = 1 - n[1]
save(np.stack(n + [one], -1), base + '_Real_Normal_DirectX', '16')
print('RETEX OK', OUT)
