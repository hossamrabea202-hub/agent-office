# #561 Noble crossbow rebuilt as a real object (checkking (Claude), 2026-11-07). Our own model, not the licensed one.
# Late-15th-century German steel-prod hunting crossbow: oiled walnut stock with an engraved staghorn inlay, forged steel
# prod, waxed hemp string (3 twisted strands), cord bridle, antler nut, iron trigger + stirrup, brass rivets.
#   blender -b --factory-startup -P build_xbow561.py -- <out_dir> [bake_size=2048] [--nobake]
# Writes <out_dir>/xbow561.blend, SM_Crossbow561.fbx (cm, X forward, Z up, origin at the nut), and with baking
# T_Crossbow561M_BaseColor.png / _ORM.png / _Normal.png (OpenGL; UE import flips green).
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]; SIZE = int(args[1]) if len(args) > 1 and args[1].isdigit() else 2048; BAKE = '--nobake' not in args
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'laptop2', 'retex_lib'))
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------------------------------------------------------- helpers
def rrect(w, h, r, seg=5):
    """rounded rectangle in the (u, v) plane, centred, counter-clockwise"""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4); pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts
def catmull(pts, n):
    """Catmull-Rom through a list of tuples (any length), n sub-steps per span"""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        for s in range(n):
            t = s / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * P[i][k]) + (-P[i - 1][k] + P[i + 1][k]) * t + (2 * P[i - 1][k] - 5 * P[i][k] + 4 * P[i + 1][k] - P[i + 2][k]) * t2
                                    + (-P[i - 1][k] + 3 * P[i][k] - 3 * P[i + 1][k] + P[i + 2][k]) * t3) for k in range(len(P[i]))))
    out.append(pts[-1]); return out
def loft(name, frames, mat, cap=True):
    """frames: list of (origin Vector, u Vector, v Vector, [(a,b)...] section). Bridges rings, fills the caps."""
    bm = bmesh.new(); rings = []
    for o, u, v, sec in frames:
        rings.append([bm.verts.new(o + u * a + v * b) for a, b in sec])
    for r0, r1 in zip(rings, rings[1:]):
        n = len(r0)
        for i in range(n):
            bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
    if cap:
        for ring, flip in ((rings[0], True), (rings[-1], False)):
            c = bm.verts.new(sum((v.co for v in ring), Vector()) / len(ring)); n = len(ring)
            for i in range(n):
                f = (ring[i], ring[(i + 1) % n], c); bm.faces.new(f[::-1] if flip else f)
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    ob.data.shade_smooth() if hasattr(ob.data, 'shade_smooth') else None
    return ob
def tube(name, pts, radius, mat, sides=8, closed=False, radius_fn=None):
    """sweep a circle along a point list (parallel-transport frames)"""
    pts = [Vector(p) for p in pts]; frames = []
    t0 = (pts[1] - pts[0]).normalized(); up = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    u = t0.cross(up).normalized()
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = (u - t * u.dot(t)).normalized(); v = t.cross(u)
        rr = radius_fn(i / (len(pts) - 1)) if radius_fn else radius
        frames.append((p, u, v, [(rr * math.cos(2 * math.pi * k / sides), rr * math.sin(2 * math.pi * k / sides)) for k in range(sides)]))
    return loft(name, frames, mat, cap=not closed)
def rounded_box(name, size, loc, mat, bevel=0.0015, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); ob = bpy.context.object; ob.name = name
    ob.scale = size; bpy.ops.object.transform_apply(scale=True)
    m = ob.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 3; m.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier='bev'); ob.data.materials.append(mat)
    bpy.ops.object.shade_smooth(); return ob
def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=24, bevel=0.0008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot); ob = bpy.context.object; ob.name = name
    m = ob.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 2; m.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier='bev'); ob.data.materials.append(mat); bpy.ops.object.shade_smooth(); return ob

# ---------------------------------------------------------------- materials (calibrated, KB §1.1 + INDUSTRY_SECRETS)
def edge_mask(nt, radius):
    bev = _n(nt, 'ShaderNodeBevel', samples=8); bev.inputs['Radius'].default_value = radius
    geo = _n(nt, 'ShaderNodeNewGeometry'); d = _n(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    nt.links.new(bev.outputs[0], d.inputs[0]); nt.links.new(geo.outputs['Normal'], d.inputs[1])
    return _maprange(nt, d.outputs['Value'], 0.995, 0.93), bev
def cav_mask(nt, dist):
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', samples=16, only_local=True); ao.inputs['Distance'].default_value = dist
    return _maprange(nt, ao.outputs['AO'], 0.95, 0.55), ao.outputs['AO']
def noise(nt, co, scale, detail=5, rough=0.55, dist=0.0):
    t = _n(nt, 'ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough, in_Distortion=dist)
    nt.links.new(co, t.inputs['Vector']); return t.outputs['Fac']
def stretched(nt, co, sx, sy, sz):
    m = _n(nt, 'ShaderNodeMapping'); m.inputs['Scale'].default_value = (sx, sy, sz); nt.links.new(co, m.inputs['Vector']); return m.outputs[0]
def finish(m, col, rg, mt, ao, bump_h=None, bump_s=0.0004, bevel_bump=False):
    nt = m.node_tree
    for key, sock in (('BC', col), ('RG', rg), ('MT', mt), ('AO', ao)):
        rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_' + key
        if isinstance(sock, (int, float)):
            v = _n(nt, 'ShaderNodeValue'); v.outputs[0].default_value = sock; sock = v.outputs[0]
        nt.links.new(sock, rr.inputs[0])
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled'); bsdf.name = 'BSDF'
    for k, inp in (('BC', 'Base Color'), ('RG', 'Roughness'), ('MT', 'Metallic')):
        nt.links.new(nt.nodes['OUT_' + k].outputs[0], bsdf.inputs[inp])
    if bump_h is not None:
        b = _n(nt, 'ShaderNodeBump'); b.inputs['Distance'].default_value = bump_s; b.inputs['Strength'].default_value = 1.0
        nt.links.new(bump_h, b.inputs['Height']); nt.links.new(b.outputs[0], bsdf.inputs['Normal'])
        for nd in nt.nodes:                       # bevel node follows the bumped normal (metal only)
            if bevel_bump and nd.bl_idname == 'ShaderNodeBevel': nt.links.new(b.outputs[0], nd.inputs['Normal'])
    em = _n(nt, 'ShaderNodeEmission'); em.name = 'EMIT'
    out = _n(nt, 'ShaderNodeOutputMaterial'); out.name = 'OUT'; nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
def newmat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    co = _n(m.node_tree, 'ShaderNodeTexCoord').outputs['Object']; return m, m.node_tree, co

# WALNUT stock: oiled, ~68 sRGB, grain along X, pores rougher, finish rubbed lighter on edges, hand polish on the grip
M_WOOD, nt, co = newmat('Walnut')
edge, _ = edge_mask(nt, 0.0025); cav, ao = cav_mask(nt, 0.01)
gw = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', in_Scale=14.0, in_Distortion=5.0, in_Detail=6.0, in_Detail_Scale=2.0)
nt.links.new(stretched(nt, co, 0.08, 1.0, 1.0), gw.inputs['Vector'])
gw2 = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=14.0, in_Distortion=5.0, in_Detail=6.0, in_Detail_Scale=2.0)
nt.links.new(stretched(nt, co, 0.08, 1.0, 1.0), gw2.inputs['Vector'])
nrm_ = _n(nt, 'ShaderNodeNewGeometry'); sz = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(nrm_.outputs['Normal'], sz.inputs[0])
side_w = _maprange(nt, _math(nt, 'ABSOLUTE', sz.outputs[1]), 0.3, 0.7)
ring = _maprange(nt, _mix_f(nt, side_w, gw2.outputs['Fac'], gw.outputs['Fac']), 0.35, 0.85)
pore = _maprange(nt, noise(nt, stretched(nt, co, 60, 420, 420), 1.0, 2, 0.5), 0.60, 0.74)
fig = noise(nt, stretched(nt, co, 3, 14, 14), 1.0, 4, 0.6)
col = _mix_col(nt, ring, (0.118, 0.068, 0.040), (0.062, 0.034, 0.020))
col = _mix_col(nt, _math(nt, 'MULTIPLY', fig, 0.30), col, (0.135, 0.078, 0.044))
col = _mix_col(nt, _math(nt, 'MULTIPLY', pore, 0.45), col, (0.045, 0.025, 0.015))
sepx = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(co, sepx.inputs[0]); X = sepx.outputs[0]
grip = _math(nt, 'MULTIPLY', _maprange(nt, X, -0.20, -0.14), _maprange(nt, X, -0.01, -0.06))
col = _mix_col(nt, _math(nt, 'MULTIPLY', edge, _maprange(nt, noise(nt, co, 60), 0.35, 0.6, 0.3, 1.0)), col, (0.20, 0.115, 0.062))
col = _mix_col(nt, _math(nt, 'MULTIPLY', grip, 0.35), col, (0.075, 0.040, 0.022))
col = _mix_col(nt, _math(nt, 'MULTIPLY', cav, 0.7), col, (0.040, 0.024, 0.014))
rg = _mix_f(nt, ring, 0.46, 0.56); rg = _mix_f(nt, pore, rg, 0.72); rg = _mix_f(nt, edge, rg, 0.40)
rg = _mix_f(nt, grip, rg, 0.34); rg = _mix_f(nt, cav, rg, 0.80)
finish(M_WOOD, col, rg, 0.0, ao, _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', pore, 0.5)), 0.00008)

# STAGHORN inlay: aged bone ~(0.55,0.48,0.36) linear, engraved scroll lines filled with dark (black wax), satin
M_BONE, nt, co = newmat('Staghorn')
edge, _ = edge_mask(nt, 0.0015); cav, ao = cav_mask(nt, 0.004)
# scrollwork: rings centred on a row of points along X (fract of x), distorted a little, cut to thin lines
mp = _n(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0 / 0.022, 1.0 / 0.022, 1.0 / 0.022); nt.links.new(co, mp.inputs['Vector'])
spx = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(mp.outputs[0], spx.inputs[0])
fx = _math(nt, 'SUBTRACT', _math(nt, 'FRACT', spx.outputs[0]), 0.5)
fz = _math(nt, 'SUBTRACT', _math(nt, 'FRACT', _math(nt, 'ADD', spx.outputs[2], 0.5)), 0.5)
r2 = _math(nt, 'SQRT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', fx, fx), _math(nt, 'MULTIPLY', fz, fz)))
ang = _math(nt, 'ARCTAN2', fz, fx)
jit = _math(nt, 'ADD', 7.0, _math(nt, 'MULTIPLY', 1.5, _math(nt, 'MULTIPLY', _math(nt, 'SINE', _math(nt, 'MULTIPLY', spx.outputs[0], 1.7)), _math(nt, 'COSINE', _math(nt, 'MULTIPLY', spx.outputs[2], 2.3)))))   # same formula as the carved high poly
spiral = _math(nt, 'FRACT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', r2, jit), _math(nt, 'MULTIPLY', ang, 0.159)))
line = _math(nt, 'MULTIPLY', _maprange(nt, _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', spiral, 0.5)), 0.38, 0.45), _maprange(nt, r2, 0.48, 0.40))

col = _mix_col(nt, noise(nt, co, 90, 4), (0.44, 0.36, 0.24), (0.55, 0.46, 0.32))
col = _mix_col(nt, _maprange(nt, noise(nt, co, 8, 3), 0.5, 0.8, 0, 0.5), col, (0.42, 0.33, 0.21))     # age yellowing
col = _mix_col(nt, line, col, (0.030, 0.024, 0.018))
col = _mix_col(nt, _math(nt, 'MULTIPLY', cav, 0.6), col, (0.12, 0.09, 0.06))
rg = _mix_f(nt, noise(nt, co, 40, 3), 0.40, 0.52); rg = _mix_f(nt, line, rg, 0.75); rg = _mix_f(nt, edge, rg, 0.34)
finish(M_BONE, col, rg, 0.0, ao, _math(nt, 'SUBTRACT', 1.0, line), 0.0006)

# STEEL (prod, stirrup, trigger, plates): bare forged steel ~190 sRGB metallic 1 under a patchy dark oxide film
# (non-metal), rubbed bare on edges; a little rust only deep in corners. Hammer marks + draw-filing streaks.
def steel(name, oxide_amt=0.55):
    m, nt, co = newmat(name)
    edge, _ = edge_mask(nt, 0.0015); cav, ao = cav_mask(nt, 0.006)
    ham = _n(nt, 'ShaderNodeTexVoronoi', feature='SMOOTH_F1', in_Scale=220.0); nt.links.new(co, ham.inputs['Vector'])
    hm = _maprange(nt, ham.outputs['Distance'], 0.0, 0.7)
    fil = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=400.0, in_Distortion=6.0, in_Detail=3.0)
    nt.links.new(co, fil.inputs['Vector']); fl = _maprange(nt, fil.outputs['Fac'], 0.6, 1.0)
    patch = _maprange(nt, _math(nt, 'ADD', noise(nt, co, 34, 6, 0.6), _math(nt, 'MULTIPLY', noise(nt, co, 120, 4), 0.25)), 0.62, 0.80)
    wipe = _maprange(nt, noise(nt, stretched(nt, co, 1.0, 0.12, 6.0), 6, 4, 0.6), 0.55, 0.75)    # long wipe marks along the span
    ox = _math(nt, 'SUBTRACT', _math(nt, 'MAXIMUM', patch, _maprange(nt, cav, 0.1, 0.5)), _math(nt, 'ADD', _math(nt, 'MULTIPLY', edge, 2.2), _math(nt, 'MULTIPLY', wipe, 0.45)), True)
    ox = _maprange(nt, ox, 0.30, 0.40)
    rust = _math(nt, 'MULTIPLY', _maprange(nt, cav, 0.55, 0.95), _maprange(nt, noise(nt, co, 40, 4), 0.55, 0.7))
    bare = _mix_col(nt, noise(nt, co, 30, 3), (0.48, 0.49, 0.50), (0.56, 0.565, 0.57))
    bare = _mix_col(nt, _math(nt, 'MULTIPLY', hm, 0.15), bare, (0.44, 0.445, 0.45))
    film = _mix_col(nt, _math(nt, 'ADD', _math(nt, 'MULTIPLY', noise(nt, co, 260, 3), 0.6), _math(nt, 'MULTIPLY', noise(nt, co, 25, 3), 0.4)), (0.038, 0.036, 0.035), (0.075, 0.069, 0.062))
    col = _mix_col(nt, ox, bare, film); col = _mix_col(nt, rust, col, (0.18, 0.057, 0.017))
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', fl, 0.5), 0.34, 0.26); rg = _mix_f(nt, _math(nt, 'MULTIPLY', hm, 0.5), rg, 0.36); rg = _mix_f(nt, edge, rg, 0.18)
    rg = _mix_f(nt, ox, rg, 0.62); rg = _mix_f(nt, rust, rg, 1.0)
    mt = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MAXIMUM', ox, rust), True)
    finish(m, col, rg, mt, ao, _math(nt, 'ADD', _math(nt, 'MULTIPLY', hm, 0.6), _math(nt, 'MULTIPLY', fl, 0.1)), 0.00015, True)
    return m
M_STEEL = steel('Steel')

# BRASS rivets/caps: aged brass, metallic 1, brown tarnish in the recess (non-metal), rubbed bright on top
M_BRASS, nt, co = newmat('Brass')
edge, _ = edge_mask(nt, 0.0008); cav, ao = cav_mask(nt, 0.003)
col = _mix_col(nt, noise(nt, co, 60, 3), (0.66, 0.49, 0.24), (0.76, 0.58, 0.29))
tarn = _maprange(nt, cav, 0.2, 0.6)
col = _mix_col(nt, tarn, col, (0.075, 0.055, 0.032)); col = _mix_col(nt, edge, col, (0.82, 0.65, 0.36))
rg = _mix_f(nt, noise(nt, co, 40, 3), 0.30, 0.42); rg = _mix_f(nt, tarn, rg, 0.75); rg = _mix_f(nt, edge, rg, 0.22)
finish(M_BRASS, col, rg, _math(nt, 'SUBTRACT', 1.0, tarn, True), ao)

# WAXED HEMP (string, bridle cord): tan, darker with wax and handling, rough
M_CORD, nt, co = newmat('Hemp')
cav, ao = cav_mask(nt, 0.002)
fib = noise(nt, stretched(nt, co, 300, 300, 300), 1.0, 3, 0.6)
col = _mix_col(nt, fib, (0.13, 0.10, 0.06), (0.20, 0.155, 0.095))
col = _mix_col(nt, _math(nt, 'MULTIPLY', cav, 0.7), col, (0.07, 0.055, 0.035))
rg = _mix_f(nt, fib, 0.66, 0.80); finish(M_CORD, col, rg, 0.0, ao, fib, 0.0001)

# ANTLER nut: like the inlay but plain, darker, polished where the string rubs
M_NUT, nt, co = newmat('Antler')
edge, _ = edge_mask(nt, 0.001); cav, ao = cav_mask(nt, 0.003)
col = _mix_col(nt, _math(nt, 'ADD', _math(nt, 'MULTIPLY', noise(nt, co, 160, 5), 0.6), _math(nt, 'MULTIPLY', noise(nt, co, 12, 3), 0.4)), (0.22, 0.17, 0.11), (0.40, 0.33, 0.23))
col = _mix_col(nt, _math(nt, 'MULTIPLY', cav, 0.6), col, (0.10, 0.08, 0.05))
rg = _mix_f(nt, noise(nt, co, 50), 0.38, 0.5); rg = _mix_f(nt, edge, rg, 0.28)
finish(M_NUT, col, rg, 0.0, ao, noise(nt, co, 300, 3), 0.00015)

# ---------------------------------------------------------------- geometry (metres; X forward, Z up; origin = nut)
# stock stations: x, width, height, z-centre, corner radius
ST = [(-0.430, 0.032, 0.088, -0.044, 0.012), (-0.424, 0.038, 0.104, -0.045, 0.015), (-0.385, 0.043, 0.110, -0.043, 0.018),
      (-0.310, 0.042, 0.090, -0.032, 0.017), (-0.210, 0.038, 0.064, -0.016, 0.015), (-0.120, 0.034, 0.047, -0.006, 0.013),
      (-0.050, 0.037, 0.048, -0.005, 0.010), (0.000, 0.044, 0.054, -0.004, 0.010), (0.050, 0.041, 0.047, -0.004, 0.009),
      (0.150, 0.032, 0.036, -0.002, 0.010), (0.230, 0.036, 0.042, -0.001, 0.010), (0.285, 0.042, 0.048, -0.002, 0.009),
      (0.315, 0.040, 0.044, -0.003, 0.010), (0.322, 0.032, 0.036, -0.003, 0.010)]
STS = catmull(ST, 4)
frames = []
for x, w, h, zc, r in STS:
    sec = rrect(w, h, r, 6)
    # bolt groove: a shallow 4 mm channel on the top, forward of the nut (vertices near the top centre pulled down)
    if 0.02 < x < 0.31:
        sec = [(a, b - 0.0035 * max(0.0, 1 - abs(a) / 0.0045) if b > h / 2 - 1e-4 else b) for a, b in sec]
    frames.append((Vector((x, 0, zc)), Vector((0, 1, 0)), Vector((0, 0, 1)), sec))
stock = loft('Stock', frames, M_WOOD)
TOP = lambda x: next(zc + h / 2 for xx, w, h, zc, r in STS if xx >= x)

# staghorn inlay panels on both sides of the butt (raised 1 mm, rounded): a thin loft that follows the stock side
for side in (1, -1):
    fr = []
    for x, w, h, zc, r in catmull([s for s in ST if -0.36 <= s[0] <= -0.06], 4):
        ph = h * 0.52; fr.append((Vector((x, side * (w / 2 + 0.0004), zc)), Vector((0, side, 0)), Vector((0, 0, 1)),
                                  [(a * 0.0012, b) for a, b in rrect(2.0, ph, ph * 0.15, 3)]))
    loft('Inlay%+d' % side, fr, M_BONE)
    for x in [i * 0.03 - 0.345 for i in range(10)]:           # brass rivets along the inlay borders
        s = next(s for s in STS if s[0] >= x); zc, h, w = s[3], s[2], s[1]
        for dz in (h * 0.30, -h * 0.30):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.0026, location=(x, side * (w / 2 + 0.0012), zc + dz))
            rv = bpy.context.object; rv.scale = (1, 0.45, 1); bpy.ops.object.transform_apply(scale=True); rv.data.materials.append(M_BRASS)
            bpy.ops.object.shade_smooth()

# steel prod, spanned: tips pulled back 6 cm, tapering, rounded-rect section
PX, PZ, SPAN = 0.272, 0.010, 0.335
pf = []
for i in range(81):
    y = -SPAN + 2 * SPAN * i / 80; t = abs(y) / SPAN
    x = PX - 0.055 * t ** 1.7; dx = -0.055 * 1.7 * t ** 0.7 * (1 if y >= 0 else -1) / SPAN
    tan = Vector((dx, 1, 0)).normalized(); nrm = Vector((tan.y, -tan.x, 0))
    th, hh = 0.0145 - 0.0060 * t, 0.034 - 0.015 * t
    pf.append((Vector((x, y, PZ)), nrm, Vector((0, 0, 1)), rrect(th, hh, 0.0028, 4)))
loft('Prod', pf, M_STEEL)
TIP = [Vector((PX - 0.055 - 0.004, s * (SPAN - 0.006), PZ)) for s in (1, -1)]

# nut (antler) sunk in the stock top with two fingers that hold the string, iron pin plates on the sides
NUTZ = TOP(0.0) - 0.004
cyl('Nut', 0.0155, 0.032, (0, 0, NUTZ), M_NUT, rot=(math.pi / 2, 0, 0), verts=28)
for s in (1, -1):
    rounded_box('NutFinger%+d' % s, (0.008, 0.007, 0.012), (0.004, s * 0.008, NUTZ + 0.016), M_NUT, 0.002)
    rounded_box('NutPlate%+d' % s, (0.050, 0.0016, 0.026), (0.0, s * 0.0228, NUTZ - 0.006), M_STEEL, 0.0006)
    cyl('NutPin%+d' % s, 0.0035, 0.002, (0, s * 0.0238, NUTZ), M_BRASS, rot=(math.pi / 2, 0, 0), verts=16)

# string: 3 strands twisted (9 mm pitch) from tip to the nut fingers and back
def string_path(a, b, n):
    return [a.lerp(b, i / n) for i in range(n + 1)]
CATCH = Vector((0.009, 0, NUTZ + 0.019))
for k, tip in enumerate(TIP):
    path = string_path(tip, CATCH, 140); L = (CATCH - tip).length; d = (CATCH - tip).normalized()
    u = d.cross(Vector((0, 0, 1))).normalized(); v = d.cross(u)
    for strand in range(3):
        pts = []
        for i, p in enumerate(path):
            a = 2 * math.pi * (L * i / 140) / 0.009 + strand * 2 * math.pi / 3
            pts.append(p + (u * math.cos(a) + v * math.sin(a)) * 0.0011)
        tube('String%d_%d' % (k, strand), pts, 0.00115, M_CORD, sides=5)
    # loop around the prod tip
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0085, minor_radius=0.0016, major_segments=20, minor_segments=6, location=tip, rotation=(0, math.pi / 2, 0))
    lp = bpy.context.object; lp.data.materials.append(M_CORD); bpy.ops.object.shade_smooth()

# bridle: cord lashing the prod into the stock head (6 wraps around the head + 2 crossed loops over the prod)
for i in range(6):
    x = 0.243 + i * 0.0085; s = next(s for s in STS if s[0] >= x)
    pts = [Vector((x, 0, s[3])) + Vector((0, (s[1] / 2 + 0.0022) * math.cos(a), (s[2] / 2 + 0.0022) * math.sin(a)))
           for a in [2 * math.pi * j / 40 for j in range(41)]]
    tube('Bridle%d' % i, pts, 0.0019, M_CORD, sides=6, closed=True)
for s in (1, -1):
    pts = [Vector((PX, 0, PZ)) + Matrix.Rotation(s * math.radians(38), 3, 'Z') @ Vector((0, 0.034 * math.cos(a), 0.030 * math.sin(a)))
           for a in [2 * math.pi * j / 40 for j in range(41)]]
    tube('BridleX%+d' % s, pts, 0.0019, M_CORD, sides=6, closed=True)

# stirrup: forged iron D-loop in front of the head, legs riveted to the stock sides
sp = [(0.300, 0.024, 0.0), (0.335, 0.048, -0.004), (0.380, 0.058, -0.010), (0.425, 0.045, -0.014), (0.445, 0.0, -0.016),
      (0.425, -0.045, -0.014), (0.380, -0.058, -0.010), (0.335, -0.048, -0.004), (0.300, -0.024, 0.0)]
tube('Stirrup', catmull(sp, 8), 0.0058, M_STEEL, sides=10, radius_fn=lambda t: 0.0058 if 0.15 < t < 0.85 else 0.0048)
for s in (1, -1):
    rounded_box('StirrupStrap%+d' % s, (0.040, 0.003, 0.014), (0.290, s * 0.0215, -0.002), M_STEEL, 0.0008)
    cyl('StirrupRivet%+d' % s, 0.0032, 0.004, (0.282, s * 0.0235, -0.002), M_BRASS, rot=(math.pi / 2, 0, 0), verts=14)
# front cap plate (steel)
rounded_box('HeadPlate', (0.004, 0.036, 0.040), (0.322, 0, -0.003), M_STEEL, 0.0012)

# trigger (tickler): long forged lever under the stock, pivot just behind the nut
tp = [(0.004, 0, -0.026), (-0.020, 0, -0.040), (-0.080, 0, -0.050), (-0.160, 0, -0.056), (-0.240, 0, -0.058), (-0.262, 0, -0.054)]
pts = catmull(tp, 10); fr = []
for i, p in enumerate(pts):
    p = Vector(p); q = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)]); t = q.normalized()
    nz = Vector((0, 1, 0)).cross(t).normalized(); f = i / (len(pts) - 1)
    fr.append((p, Vector((0, 1, 0)), nz, rrect(0.0085 - 0.002 * f, 0.0065, 0.0022, 3)))
loft('Trigger', fr, M_STEEL)
cyl('TriggerPin', 0.0028, 0.044, (0.0, 0, -0.024), M_STEEL, rot=(math.pi / 2, 0, 0), verts=16)
rounded_box('TriggerSlot', (0.030, 0.012, 0.004), (-0.01, 0, -0.030), M_STEEL, 0.001)

# ---------------------------------------------------------------- join, UV, export
objs = [o for o in sc.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = stock; bpy.ops.object.join(); ob = bpy.context.object; ob.name = 'SM_Crossbow561'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=1e-6)
bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.003, rotate=True) if hasattr(bpy.ops.uv, 'pack_islands') else None
bpy.ops.object.mode_set(mode='OBJECT')
tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
print('XBOW561 model', ob.name, 'tris', tris, 'size m', tuple(round(d, 3) for d in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'xbow561.blend'))

if BAKE:
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
    bake = {}
    for key, cs in (('BC', 'sRGB'), ('RG', 'Non-Color'), ('MT', 'Non-Color'), ('AO', 'Non-Color'), ('N', 'Non-Color')):
        im = bpy.data.images.new('bake_' + key, SIZE, SIZE, alpha=False, float_buffer=(key == 'N')); im.colorspace_settings.name = cs; bake[key] = im
    for m in ob.data.materials:
        nt = m.node_tree; tn = nt.nodes.new('ShaderNodeTexImage'); tn.name = 'BAKE_TARGET'; nt.nodes.active = tn
    def target(key):
        for m in ob.data.materials:
            t = m.node_tree.nodes['BAKE_TARGET']; t.image = bake[key]; m.node_tree.nodes.active = t
    def route(key):
        for m in ob.data.materials:
            nt = m.node_tree; out = nt.nodes['OUT']
            if key == 'BSDF': nt.links.new(nt.nodes['BSDF'].outputs[0], out.inputs['Surface'])
            else: em = nt.nodes['EMIT']; nt.links.new(nt.nodes['OUT_' + key].outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])
    sc.render.bake.margin = 8
    for key in ('BC', 'RG', 'MT', 'AO'):
        route(key); target(key); bpy.ops.object.bake(type='EMIT'); print('XBOW561 baked', key)
    route('BSDF'); target('N'); bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT'); print('XBOW561 baked N')
    import numpy as np
    def px(im): a = np.empty(SIZE * SIZE * 4, np.float32); im.pixels.foreach_get(a); return a.reshape(SIZE, SIZE, 4)
    def write(arr, name, cs='Non-Color'):
        im = bpy.data.images.new(name, SIZE, SIZE, alpha=False); im.colorspace_settings.name = cs
        im.pixels.foreach_set(np.ascontiguousarray(arr, np.float32).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'; im.save()
    bc = px(bake['BC']); orm = np.ones((SIZE, SIZE, 4), np.float32); orm[..., 0] = px(bake['AO'])[..., 0]; orm[..., 1] = px(bake['RG'])[..., 0]
    mt = np.clip((px(bake['MT'])[..., 0] - 0.45) / 0.1, 0.0, 1.0); orm[..., 2] = mt
    lin = np.where(bc[..., :3] <= 0.04045, bc[..., :3] / 12.92, ((bc[..., :3] + 0.055) / 1.055) ** 2.4)
    Y = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32); k = np.where((mt > 0.5) & (Y < 0.456), 0.456 / np.maximum(Y, 1e-4), 1.0)
    lin = np.clip(lin * k[..., None], 0, 1); bc[..., :3] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    write(bc, 'T_Crossbow561M_BaseColor', 'sRGB'); write(orm, 'T_Crossbow561M_ORM')
    write(px(bake['N']), 'T_Crossbow561M_Normal')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'xbow561.blend'))

if BAKE or '--oneslot' in args:   # one UE slot: everything is baked into one texture set
    one = bpy.data.materials.new('M_Crossbow561'); ob.data.materials.clear(); ob.data.materials.append(one)
    for p in ob.data.polygons: p.material_index = 0
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_Crossbow561.fbx'), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                         axis_forward='X', axis_up='Z', mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, bake_space_transform=True)
print('XBOW561 DONE', OUT)
