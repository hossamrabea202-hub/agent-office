# #546 forged iron for the chained zombie (adjustedfilm, 2026-11-06). Blender 4.5:
#   blender -b --factory-startup -P gen_chain.py -- <out_dir>
# Writes FBX: SM_ChainLink, SM_ChainCuff, SM_ChainAnchor, SM_MeltPool. All procedural, original.
# Vertex colour = physical masks, read by M_CD_ForgedIron:
#   R rust     where water sits: inside bends, under the plate rim, rivet roots, seams. Never on a rubbed face.
#   G bright   metal rubbed clean: where link touches link, the staple's inner bend, the cuff's hasp pin. The only true metal.
#   B dirt     one shared soot/grease pass, up-facing and cavity
# Bevels: everything is smooth-shaded round stock, cross-sections 8-10 sides; the edge of the cuff band has a real 2.5 mm chamfer.
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, noise
OUT = sys.argv[sys.argv.index('--') + 1]; os.makedirs(OUT, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def sweep(bm, path, radius, sides=8, closed=True, flat=1.0, rough=0.0, seed=0.0):
    """round bar along a path; flat < 1 squashes it (forge-flattened), rough = hammer dents in metres."""
    n = len(path); rings = []
    for i, p in enumerate(path):
        a, b = path[(i - 1) % n] if (closed or i > 0) else p, path[(i + 1) % n] if (closed or i < n - 1) else p
        t = (b - a).normalized(); u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-3: u = t.cross(Vector((0, 1, 0)))
        u.normalize(); v = u.cross(t).normalized(); ring = []
        for k in range(sides):
            th = 2 * math.pi * k / sides; d = u * math.cos(th) * radius + v * math.sin(th) * radius * flat
            q = p + d
            if rough: q += d.normalized() * rough * noise.noise(q * 45.0 + Vector((seed, 0, 0)))
            ring.append(bm.verts.new(q))
        rings.append(ring)
    for i in range(n if closed else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for k in range(sides):
            bm.faces.new((r0[k], r0[(k + 1) % sides], r1[(k + 1) % sides], r1[k]))
    if not closed:
        for r in (rings[0], rings[-1][::-1]): bm.faces.new(r[::-1])
    return rings

def stadium(L, W, n=26):
    """link centre-line in XY, length L along X, width W: a forged oval, not a perfect one."""
    r = W / 2.0; s = L / 2.0 - r; pts = []
    for i in range(n):
        u = i / float(n); per = 2 * (2 * s) + 2 * math.pi * r; d = u * per
        if d < 2 * s: p = Vector((-s + d, -r, 0))
        elif d < 2 * s + math.pi * r: a = (d - 2 * s) / r - math.pi / 2; p = Vector((s + r * math.cos(a), r * math.sin(a), 0))
        elif d < 4 * s + math.pi * r: p = Vector((s - (d - 2 * s - math.pi * r), r, 0))
        else: a = (d - 4 * s - math.pi * r) / r + math.pi / 2; p = Vector((-s + r * math.cos(a), r * math.sin(a), 0))
        pts.append(p)
    return pts

def finish(name, bm, masks):
    me = bpy.data.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.update()
    uvl = me.uv_layers.new(name='UV0')
    for lp in me.loops:                 # a cheap skewed planar UV: detail and roughness only, nothing lines up on a seam at this size
        c = me.vertices[lp.vertex_index].co; uvl.data[lp.index].uv = ((c.x + c.y * 0.6) * 9.0, (c.z + c.y * 0.45) * 9.0)
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for lp in me.loops:
        v = me.vertices[lp.vertex_index]; r, g, b = masks(v.co, v.normal); ca.data[lp.index].color = (min(1, max(0, r)), min(1, max(0, g)), min(1, max(0, b)), 1.0)
    return ob

def export(ob, name):
    for o in bpy.data.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + '.fbx'), use_selection=True, object_types={'MESH'}, apply_unit_scale=True, global_scale=100.0,
                             bake_space_transform=False, mesh_smooth_type='FACE', use_tspace=True, colors_type='LINEAR', axis_forward='X', axis_up='Z', add_leaf_bones=False, bake_anim=False)
    print('GEN', name, len(ob.data.vertices), 'verts', len(ob.data.polygons), 'quads')

def nz(p, s, o=0.0): return noise.noise(p * s + Vector((o, o * 0.7, o * 0.3)))

# ---- link: 12 cm long, 6.8 cm wide, 1.7 cm stock (hand-forged chain, pitch 8.6 cm)
reset(); LINK_L, LINK_W, WIRE = 0.12, 0.068, 0.017
bm = bmesh.new(); path = stadium(LINK_L - WIRE, LINK_W - WIRE)
for i, p in enumerate(path): p.z += 0.0012 * math.sin(i * 2 * math.pi / len(path) * 2 + 0.7); p.y *= 1.0 + 0.035 * math.sin(p.x * 40)     # never a perfect oval
sweep(bm, path, WIRE / 2, 10, True, 1.0, 0.0011, 3.0)
def m_link(c, n):
    end = max(0.0, (abs(c.x) - 0.040) / 0.02)                      # the bend, where the next link rides
    inner = max(0.0, -(c.x * n.x / max(abs(c.x), 1e-4))) ; bright = min(1.0, end * inner * 1.8) * (0.6 + 0.8 * nz(c, 60.0, 1.0))
    rust = 0.42 + 0.75 * nz(c, 30.0, 5.0) + 0.5 * nz(c, 95.0, 9.0) + 0.20 * max(0.0, -n.z) - bright * 1.2
    return (max(0.0, rust), bright, 0.25 + 0.5 * max(0.0, n.z) * (0.5 + nz(c, 22.0, 2.0)))
export(finish('SM_ChainLink', bm, m_link), 'SM_ChainLink')

# ---- cuff: hinged iron band, axis X. Inner radius 11.8 cm, 6.5 cm wide, 1 cm plate: measured on his wrist (max 11.8 cm at the narrow point). Lug and hasp at -Z. The ankle uses it at scale 0.72 (shin max 7.7 cm)
reset(); bm = bmesh.new(); R, W, T, N = 0.118, 0.065, 0.010, 52
def add_band():
    rings = []
    prof = [(-W / 2, R), (-W / 2 + 0.0025, R - 0.0005 - 0.0), (W / 2 - 0.0025, R - 0.0005), (W / 2, R), (W / 2, R + T - 0.0025), (W / 2 - 0.0025, R + T), (-W / 2 + 0.0025, R + T), (-W / 2, R + T - 0.0025)]
    for i in range(N):
        a = 2 * math.pi * i / N; ca, sa = math.cos(a), math.sin(a); ring = []
        wob = 1.0 + 0.012 * math.sin(3 * a + 0.8) + 0.006 * math.sin(7 * a)           # bent by hand round a former
        for x, rr in prof: ring.append(bm.verts.new((x + 0.0012 * math.sin(2 * a), rr * wob * ca, rr * wob * sa)))
        rings.append(ring)
    for i in range(N):
        r0, r1 = rings[i], rings[(i + 1) % N]; m = len(prof)
        for k in range(m): bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
add_band()
def circ(c, r, axis, n=14):
    a = Vector(axis).normalized(); u = a.cross(Vector((0, 0, 1)))
    if u.length < 1e-3: u = a.cross(Vector((0, 1, 0)))
    u.normalize(); v = a.cross(u).normalized()
    return [Vector(c) + u * r * math.cos(2 * math.pi * i / n) + v * r * math.sin(2 * math.pi * i / n) for i in range(n)]
# hinge knuckle at +Z: a short bar across the band with 2 ears
sweep(bm, [Vector((-W / 2 - 0.006, 0.0, R + T + 0.008)), Vector((W / 2 + 0.006, 0.0, R + T + 0.008))], 0.0105, 10, False)
# hasp at -Z: two lugs, a pin through them; the lug ring takes the chain
for sx in (-0.017, 0.017):
    bm_path = circ((sx, 0.0, -(R + T + 0.020)), 0.019, (1, 0, 0), 14); sweep(bm, bm_path, 0.0062, 8, True, 1.0, 0.0006, 11.0 + sx)
sweep(bm, [Vector((-0.032, 0.0, -(R + T + 0.020))), Vector((0.032, 0.0, -(R + T + 0.020)))], 0.0066, 8, False)
def m_cuff(c, n):
    rad = math.hypot(c.y, c.z)
    rubbed = max(0.0, 1.0 - abs(rad - R) / 0.0012) * max(0.0, -(c.y * n.y + c.z * n.z) / max(rad, 1e-4)) * (0.5 + 0.8 * nz(c, 70.0, 4.0))    # the bore, worn bright by the wrist
    pin = 1.0 if abs(c.z + (R + T + 0.020)) < 0.006 and abs(c.y) < 0.006 else 0.0
    rust = 0.40 + 0.8 * nz(c, 26.0, 7.0) + 0.45 * nz(c, 90.0, 8.0) + (0.35 if rad > R + T + 0.002 else 0.0) - rubbed * 1.1
    return (max(0.0, rust), min(1.0, rubbed + pin * 0.5), 0.3 + 0.5 * max(0.0, n.z) * (0.5 + nz(c, 22.0, 3.0)))
export(finish('SM_ChainCuff', bm, m_cuff), 'SM_ChainCuff')

# ---- wall anchor: forged plate into the stone (back face at x = 0, the wall), 4 clench rivets, a staple, a ring hanging from it. The chain leaves from the ring's bottom: (0.052, 0, -0.078)
reset(); bm = bmesh.new(); P, TH = 0.085, 0.011; S = 7
verts = {}
for i in range(S * 2 + 1):
    for j in range(S * 2 + 1):
        y = (i - S) / S * P; z = (j - S) / S * P; r = max(abs(y), abs(z)) / P
        edge = max(0.0, (r - 0.82) / 0.18); xf = TH * (1.0 - 0.55 * edge * edge) + 0.0009 * nz(Vector((0, y, z)), 34.0, 4.0)     # hammered rim falling to the wall
        wob = 1.0 + 0.05 * nz(Vector((0, y, z)), 12.0, 6.0) * edge
        verts[(i, j)] = bm.verts.new((xf, y * wob, z * wob))
for i in range(S * 2):
    for j in range(S * 2): bm.faces.new((verts[(i, j)], verts[(i + 1, j)], verts[(i + 1, j + 1)], verts[(i, j + 1)]))
for sy, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    c = Vector((TH + 0.002, sy * 0.058, sz * 0.058))
    rings = []
    for k, (dx, rr) in enumerate([(0.0, 0.0125), (0.0035, 0.0115), (0.0075, 0.0075), (0.0092, 0.0025)]): rings.append([bm.verts.new(p) for p in circ(c + Vector((dx, 0, 0)), rr, (1, 0, 0), 12)])
    for a, b in zip(rings, rings[1:]):
        for k in range(12): bm.faces.new((a[k], a[(k + 1) % 12], b[(k + 1) % 12], b[k]))
    bm.faces.new(rings[-1])
stp = [Vector((TH, -0.024, 0.012)), Vector((TH + 0.024, -0.024, 0.012)), Vector((TH + 0.043, -0.018, 0.012)), Vector((TH + 0.050, 0.0, 0.012)), Vector((TH + 0.043, 0.018, 0.012)), Vector((TH + 0.024, 0.024, 0.012)), Vector((TH, 0.024, 0.012))]
sweep(bm, stp, 0.0095, 10, False, 1.0, 0.0007, 21.0)
ring_c = Vector((0.052, 0.0, -0.033)); sweep(bm, circ(ring_c, 0.045, (0, 1, 0), 30), 0.0085, 10, True, 1.0, 0.0008, 31.0)
def m_anchor(c, n):
    plate = c.x < TH + 0.0005; rim = max(0.0, (max(abs(c.y), abs(c.z)) / P - 0.78) / 0.22) if plate else 0.0
    # rub: top of the ring inside the staple, and the ring's bottom where the chain drags
    rub_top = max(0.0, 1.0 - (c - Vector((0.052, 0.0, 0.012))).length / 0.016); rub_bot = max(0.0, 1.0 - (c - Vector((0.052, 0.0, -0.078))).length / 0.018)
    bright = min(1.0, (rub_top + rub_bot) * 1.6) * (0.6 + 0.8 * nz(c, 60.0, 2.0))
    rust = 0.38 + 0.85 * nz(c, 24.0, 12.0) + 0.45 * nz(c, 85.0, 13.0) + rim * 0.55 + (0.30 if c.z < -0.02 and plate else 0.0) - bright * 1.3     # water runs down and sits under the rim
    return (max(0.0, rust), bright, 0.3 + 0.55 * max(0.0, n.z) * (0.5 + nz(c, 20.0, 5.0)))
export(finish('SM_ChainAnchor', bm, m_anchor), 'SM_ChainAnchor')

# ---- melt pool: radius 1 m at scale 1, centre 3.5 cm thick, lobes and tongues; a raised meniscus at the rim as cooled wax has. R = 0..1 radius, G = rim (hot crust), B = random for the marbling
reset(); bm = bmesh.new(); RN, AN = 22, 96; random.seed(7)
def edge(a):
    x, y = math.cos(a), math.sin(a)
    return 0.70 + 0.16 * math.sin(a * 2 + 0.6) + 0.10 * math.sin(a * 3 + 2.1) + 0.06 * math.sin(a * 7 + 1.0) + 0.045 * math.sin(a * 13 + 0.3) + 0.14 * max(0.0, math.cos(a - 3.14)) ** 6
centre = bm.verts.new((0, 0, 0.034)); rings = []
for r in range(1, RN + 1):
    u = r / float(RN); ring = []
    for i in range(AN):
        a = 2 * math.pi * i / AN; rr = edge(a) * u
        rim = math.exp(-((1 - u) / 0.09) ** 2); z = 0.034 * (1 - u ** 3) * 0.72 + 0.009 * rim * (1 - u * 0.0) + 0.0035 * noise.noise(Vector((math.cos(a) * rr * 7, math.sin(a) * rr * 7, 1.0)))
        if r == RN: z = -0.004
        ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
    rings.append(ring)
for i in range(AN): bm.faces.new((centre, rings[0][i], rings[0][(i + 1) % AN]))
for a_, b_ in zip(rings, rings[1:]):
    for i in range(AN): bm.faces.new((a_[i], b_[i], b_[(i + 1) % AN], a_[(i + 1) % AN]))
def m_pool(c, n):
    a = math.atan2(c.y, c.x); u = min(1.0, math.hypot(c.x, c.y) / edge(a))
    return (u, math.exp(-((1 - u) / 0.14) ** 2), 0.5 + 0.8 * nz(c, 5.0, 3.0) + 0.3 * nz(c, 17.0, 4.0))
export(finish('SM_MeltPool', bm, m_pool), 'SM_MeltPool')
print('GEN DONE')
