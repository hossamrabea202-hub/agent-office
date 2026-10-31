# Zombie siege engines (#225, TGA). blender -b --factory-startup -P build_siege.py   -> siege.blend
# SM_Siege_Ram: covered battering ram on 4 wheels, hide-covered pitched roof, iron-capped ram log slung on chains,
# push bars at the back for big zombies. SM_Siege_Tower: ~11.7 m tapering tower on 4 wheels, 4 floors, plank cladding
# with wet hides on the front, open back with a ladder, crenellated top. SM_Siege_TowerBridge: the drop bridge as its own
# mesh, pivot on the hinge, modelled DOWN (deployed). SM_Siege_RamWreck / SM_Siege_TowerWreck: burnt, collapsed versions.
# Two atlases: SM_RamAtlas (ram + ram wreck), SM_TowerAtlas (tower + bridge + tower wreck). Metres, Z up, front = -Y
# for the tower (faces the wall), -X for the ram (head). Pivots on the ground at each piece's centre.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(225)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
pieces = []; PSEG = []
SEG = [0]; BURN = [0.0]
KIND = {'wood': 0.0, 'iron': 1.0, 'leather': 2.0, 'wax': 3.0, 'flame': 4.0}
def tag(me, kind, grain=(0.0, 0.0, 1.0)):
    n = len(me.vertices)
    me.attributes.new('grain', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', np.tile(np.abs(np.array(grain, float)), n))
    me.attributes.new('pid', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, rng.random()))
    me.attributes.new('iron', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, 1.0 if kind == 'iron' else 0.0))
    me.attributes.new('mat', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, KIND[kind] / 4.0))
    me.attributes.new('burn', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, BURN[0]))
    me.attributes.new('seg', 'INT', 'POINT').data.foreach_set('value', np.full(n, SEG[0], np.int32))
def add_mesh(bm, kind, grain=(0.0, 0.0, 1.0)):
    me = bpy.data.meshes.new('m'); bm.to_mesh(me); bm.free(); tag(me, kind, grain)
    o = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(o); pieces.append(o); PSEG.append(SEG[0]); return o
def timber(a, b, w, h, sag=0.0, tilt=0.0, kind='wood', taper=1.0):
    """box from point a to b, cross-section w x h, bevelled; long axis = grain."""
    a, b = Vector(a), Vector(b); L = (b - a).length; ax = (b - a).normalized()
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * L, v.co.y * w, v.co.z * h))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(w, h) * 0.12, segments=1, affect='EDGES')
    if L > 0.8: bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().x) > 0.9], cuts=3)
    for v in bm.verts:                                                     # sag in the middle, tiny twist
        t = v.co.x / L; v.co.z -= sag * (1 - (2 * t) ** 2); v.co.y += tilt * t * v.co.z
        k_ = 1.0 + (taper - 1.0) * (t + 0.5); v.co.y *= k_; v.co.z *= k_                # taper towards b
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0)); yb = up.cross(ax).normalized(); zb = ax.cross(yb)
    M = Matrix((ax, yb, zb)).transposed().to_4x4(); M.translation = (a + b) / 2; bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return add_mesh(bm, kind, tuple(ax))
j = lambda s=0.01: rng.normal(0, s)
def log(a, b, r, tip=0.0, kind='wood', seg=10):
    """round log a -> b (radius r), optional sharpened tip of length tip at b; grain along the axis."""
    a, b = Vector(a), Vector(b); ax = (b - a).normalized(); L = (b - a).length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L - tip)
    for v in bm.verts: v.co.z += (L - tip) / 2; v.co.x += 0.06 * r * math.sin(v.co.z * 7); v.co.y += 0.06 * r * math.cos(v.co.z * 5)
    if tip > 0:
        top = [v for v in bm.verts if v.co.z > L - tip - 1e-4]; c = bm.verts.new(Vector((0, 0, L)))
        ring = sorted(top, key=lambda v: math.atan2(v.co.y, v.co.x))
        for f in [f for f in bm.faces if len(f.verts) == len(ring) and all(v in ring for v in f.verts)]: bm.faces.remove(f)
        for k in range(len(ring)): bm.faces.new((ring[k], ring[(k + 1) % len(ring)], c))
    M = ax.to_track_quat('Z', 'Y').to_matrix().to_4x4(); M.translation = a; bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return add_mesh(bm, kind, tuple(ax))
def slab(c, ax, ay, L, W, th, kind='leather', sag=0.0, n=4, cuts=8):
    """thin draped panel (hides): length L along ax, width W along ay, droops by sag between n supports, wrinkled."""
    c, ax, ay = Vector(c), Vector(ax).normalized(), Vector(ay); ay = (ay - ax * ay.dot(ax)).normalized(); az = ax.cross(ay)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * L, v.co.y * W, v.co.z * th))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        s, t = v.co.x / L, v.co.y / W
        v.co.z -= sag * abs(math.sin(math.pi * n * (s + 0.5))) * (1 - 0.5 * (2 * t) ** 2)
        v.co.z += 0.01 * math.sin(v.co.x * 9 + v.co.y * 5) * math.sin(v.co.y * 11 - v.co.x * 3)
    M = Matrix((ax, ay, az)).transposed().to_4x4(); M.translation = c; bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return add_mesh(bm, kind, tuple(ax))
def splinters(p, d, n=6, L=0.18):
    p, d = Vector(p), Vector(d).normalized()
    for k in range(n):
        q = d + Vector((j(0.25), j(0.25), j(0.25))); q.normalize()
        timber(p + Vector((j(0.02), j(0.02), j(0.02))), p + q * (L * (0.4 + rng.random())), 0.012 + abs(j(0.006)), 0.008, taper=0.2)
def wheel(c, normal_axis, r=0.45, spokes=8, broken=-1):
    c = Vector(c)
    u, v = {'Z': (Vector((1, 0, 0)), Vector((0, 1, 0))), 'Y': (Vector((1, 0, 0)), Vector((0, 0, 1))),
            'X': (Vector((0, 1, 0)), Vector((0, 0, 1)))}[normal_axis]
    for k in range(12):                                                # felloe segments
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        timber(c + r * (math.cos(a0) * u + math.sin(a0) * v), c + r * (math.cos(a1) * u + math.sin(a1) * v), 0.09, 0.09)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes + 0.2
        timber(c, c + (r * (0.55 if k == broken else 0.95)) * (math.cos(a) * u + math.sin(a) * v), 0.05, 0.05)
    for k in range(12):                                                # iron tyre
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        timber(c + (r + 0.045) * (math.cos(a0) * u + math.sin(a0) * v), c + (r + 0.045) * (math.cos(a1) * u + math.sin(a1) * v), 0.095, 0.016, kind='iron')
    w = u.cross(v); log(c - 0.11 * w, c + 0.11 * w, 0.1)                 # hub
    log(c - 0.13 * w, c - 0.11 * w, 0.11, kind='iron'); log(c + 0.11 * w, c + 0.13 * w, 0.11, kind='iron')
NAMES = ['SM_Siege_Ram', 'SM_Siege_RamWreck', 'SM_Siege_Tower', 'SM_Siege_TowerBridge', 'SM_Siege_TowerWreck']
OFF = [0.0, 9.0, 20.0, 20.0, 30.0]
# ---- battering ram (head at -X) ------------------------------------------------------------------------------------
SEG[0] = 0; BURN[0] = 0.0; WR = 0.45; WZ = WR + 0.06
def ram_head(a, b, r):
    log(a, b, r * 0.95)                                               # the ram log
    hd = Vector(a) + (Vector(a) - Vector(b)).normalized() * 0.5
    log(a, hd, r * 1.15, tip=0.22, kind='iron', seg=12)               # iron cap
    for k in (0.12, 0.3, 0.7, 0.88):                                  # iron bands
        p = Vector(a) + (Vector(b) - Vector(a)) * k; d = (Vector(b) - Vector(a)).normalized() * 0.05
        log(p - d, p + d, r * 1.03, kind='iron', seg=12)
for sy in (-0.8, 0.8):
    timber((-2.6, sy, WZ + 0.05), (2.6, sy, WZ + 0.05), 0.22, 0.26)    # base beams over the axles
    for sx in (-1.6, 1.6): wheel((sx, sy * 1.22, WZ), 'Y', WR)
for sx in (-1.6, 1.6): log((sx, -1.05, WZ), (sx, 1.05, WZ), 0.06)     # axles
for sx in (-2.4, -0.8, 0.8, 2.4): timber((sx, -0.95, WZ + 0.22), (sx, 0.95, WZ + 0.22), 0.16, 0.14)
for sx in (-2.3, -0.8, 0.8, 2.3):
    for sy in (-0.8, 0.8):
        timber((sx, sy, WZ + 0.18), (sx + j(0.01), sy, 1.95), 0.16, 0.16)              # posts
        timber((sx - 0.5 * np.sign(sx + 1e-3), sy, WZ + 0.2), (sx, sy, 1.4), 0.08, 0.08)  # knee braces
for sy in (-0.8, 0.8): timber((-2.55, sy, 1.98), (2.55, sy, 1.98), 0.16, 0.16)   # top plates
timber((-2.6, 0, 2.72), (2.6, 0, 2.72), 0.16, 0.18)                     # ridge
for k in range(11):                                                      # rafters
    sx = -2.5 + 0.5 * k
    for sy in (-1, 1): timber((sx, sy * 1.05, 1.88), (sx, 0, 2.74), 0.07, 0.1)
for sy in (-1, 1):                                                       # wet hides over each roof pitch
    a = Vector((0, sy * 1.07, 1.86)); b = Vector((0, 0, 2.82)); mid = (a + b) / 2 + Vector((0, 0, 0.04))
    slab(mid, (1, 0, 0), b - a, 5.6, (b - a).length + 0.15, 0.025, sag=0.045, n=5)
for sx in (-1.4, 1.2):                                                   # chains: ridge -> ram log
    for sy in (-0.25, 0.25):
        p0, p1 = Vector((sx, 0, 2.62)), Vector((sx + 0.15, sy, 1.18))
        for k in range(7):
            q0, q1 = p0 + (p1 - p0) * (k / 7), p0 + (p1 - p0) * ((k + 0.85) / 7)
            timber(q0, q1, 0.035 if k % 2 else 0.012, 0.012 if k % 2 else 0.035, kind='iron')
ram_head((-2.75, 0, 1.12), (2.3, 0, 1.15), 0.19)
for sx in (2.85,):                                                       # push bars at the back
    for sy in (-0.8, 0.8): timber((2.45, sy, 1.05), (sx, sy, 1.05), 0.12, 0.12)
    timber((sx, -1.35, 1.05), (sx, 1.35, 1.05), 0.12, 0.12, kind='wood')
    for sy in (-1.15, -0.45, 0.45, 1.15): timber((sx - 0.02, sy - 0.12, 1.05), (sx - 0.02, sy + 0.12, 1.05), 0.14, 0.14, kind='leather')  # hide grips
# ---- ram wreck (burnt, roof fallen in) ------------------------------------------------------------------------------
SEG[0] = 1; BURN[0] = 1.0; X = OFF[1]
timber((X - 2.6, -0.8, 0.13), (X + 2.6, -0.85, 0.15), 0.22, 0.26)
timber((X - 2.6, 0.8, 0.13), (X - 0.2, 0.9, 0.35), 0.22, 0.26); splinters((X - 0.2, 0.9, 0.35), (1, 0, 0.3), 8, 0.3)
timber((X + 0.1, 0.95, 0.13), (X + 2.6, 0.75, 0.13), 0.22, 0.26); splinters((X + 0.1, 0.95, 0.13), (-1, 0, 0.2), 6, 0.25)
wheel((X - 1.6, -1.0, WZ), 'Y', WR, broken=3); wheel((X + 1.4, 2.0, 0.06), 'Z', WR, broken=5)
wheel((X + 1.7, -1.05, WZ), 'Y', WR, broken=1)
for sx, sy, hh in ((-2.3, -0.8, 1.2), (-0.8, 0.8, 0.7), (0.8, -0.8, 1.5), (2.3, 0.8, 0.5)):    # snapped posts
    timber((X + sx, sy, 0.25), (X + sx + j(0.04), sy + j(0.04), hh), 0.16, 0.16); splinters((X + sx, sy, hh), (0, 0, 1), 7, 0.22)
for k in range(9):                                                      # fallen rafters and plates
    a = Vector((X + rng.uniform(-2.6, 2.2), rng.uniform(-1.3, 1.3), 0.08 + rng.uniform(0, 0.25)))
    d = Vector((rng.normal(0, 1), rng.normal(0, 1), rng.normal(0, 0.15))).normalized()
    timber(a, a + d * rng.uniform(0.6, 1.3), 0.07, 0.1)
timber((X - 2.5, -0.3, 0.2), (X + 2.0, 0.6, 1.25), 0.16, 0.18); splinters((X + 2.0, 0.6, 1.25), (1, 0.2, 0.2), 6, 0.25)  # ridge leaning
slab((X - 0.3, 0.2, 0.55), (1, 0.15, 0.18), (0, 1, 0.35), 4.6, 1.9, 0.025, sag=0.12, n=3)      # hide slumped over the wreck
ram_head((X - 2.4, -0.25, 0.22), (X + 2.4, 0.9, 0.24), 0.19)
# ---- siege tower (front = -Y faces the wall) -------------------------------------------------------------------------
SEG[0] = 2; BURN[0] = 0.0; X = OFF[2]; TR = 0.55; TZ = TR + 0.07
H0, HT = 0.75, 10.6; FLOORS = (0.75, 3.95, 7.25, 10.6)
hw = lambda z: 1.6 - 0.25 * (z - H0) / (HT - H0)
for sx in (-1, 1):
    timber((X + sx * 1.6, -1.75, TZ + 0.06), (X + sx * 1.6, 1.75, TZ + 0.06), 0.26, 0.28)
    for sy in (-1.15, 1.15): wheel((X + sx * 1.95, sy, TZ), 'X', TR, spokes=10)
for sy in (-1.15, 1.15): log((X - 2.1, sy, TZ), (X + 2.1, sy, TZ), 0.07)
for sy in (-1.6, 0, 1.6): timber((X - 1.75, sy, TZ + 0.3), (X + 1.75, sy, TZ + 0.3), 0.22, 0.22)
for sx in (-1, 1):                                                       # corner posts (taper)
    for sy in (-1, 1): timber((X + sx * 1.6, sy * 1.6, H0 - 0.15), (X + sx * hw(11.75), sy * hw(11.75), 11.75), 0.26, 0.26)
for z in FLOORS:                                                         # floor frames + decks
    h_ = hw(z)
    for sy in (-1, 1): timber((X - h_, sy * h_, z - 0.12), (X + h_, sy * h_, z - 0.12), 0.18, 0.2)
    for sx in (-1, 1): timber((X + sx * h_, -h_, z - 0.12), (X + sx * h_, h_, z - 0.12), 0.18, 0.2)
    hole = z > 1 and z < 10                                              # ladder hatch at the back right
    yy = -h_ + 0.15
    while yy < h_ - 0.1:
        if hole and yy > h_ - 0.95: timber((X - h_, yy + j(0.005), z), (X + 0.15, yy, z), 0.28, 0.05)
        else: timber((X - h_, yy + j(0.005), z), (X + h_, yy, z + j(0.004)), 0.28, 0.05)
        yy += 0.3
z = H0 + 0.1                                                             # cladding: front (-Y) and both sides
while z < HT - 0.1:
    h_ = hw(z) + 0.07
    timber((X - h_, -h_, z), (X + h_, -h_, z + j(0.006)), 0.05, 0.29, tilt=0.01)
    for sx in (-1, 1): timber((X + sx * h_, -h_, z), (X + sx * h_, h_, z + j(0.006)), 0.05, 0.29, tilt=0.01)
    z += 0.3
for sx in (-1, 1):                                                       # vertical battens over the cladding
    for k in (-0.5, 0.5): timber((X + k * 2.6, -hw(H0) - 0.11, H0 + 0.1), (X + k * 2.2, -hw(HT) - 0.11, HT), 0.06, 0.12)
for z0, z1 in zip(FLOORS[:-1], FLOORS[1:]):                             # X-braces on the open back
    a, b = hw(z0), hw(z1)
    timber((X - a, a + 0.02, z0), (X + b, b + 0.02, z1), 0.12, 0.12); timber((X + a, a + 0.06, z0), (X - b, b + 0.06, z1), 0.12, 0.12)
lx = 1.0                                                                 # ladder (back right, up through the hatches)
for sx in (-0.25, 0.25): timber((X + lx + sx, hw(H0) - 0.5, H0), (X + lx + sx, hw(HT) - 0.5, HT), 0.08, 0.08)
z = H0 + 0.3
while z < HT - 0.1: timber((X + lx - 0.27, hw(z) - 0.5, z), (X + lx + 0.27, hw(z) - 0.5, z), 0.05, 0.05); z += 0.34
for k in (-1, 1):                                                        # wet hides hung on the front against fire
    slab((X + k * 0.72, -hw(5.5) - 0.17, 5.6), (0, -0.025, 1), (1, 0, 0), 8.8, 1.45, 0.025, sag=0.05, n=4)
h_ = hw(HT) + 0.05; top = 11.75                                          # crenellated parapet (front gap = bridge)
for side in range(4):
    for k in range(10):
        t = -h_ + (k + 0.5) * (2 * h_ / 10)
        if side == 0 and abs(t) < 1.2: continue
        hh = 1.15 if k % 2 == 0 else 0.75
        if side == 0: a, b, w, hb = (X + t, -h_, HT), (X + t, -h_, HT + hh), 0.05, 0.27
        elif side == 1: a, b, w, hb = (X + t, h_, HT), (X + t, h_, HT + hh), 0.05, 0.27
        else: s_ = -1 if side == 2 else 1; a, b, w, hb = (X + s_ * h_, t, HT), (X + s_ * h_, t, HT + hh), 0.27, 0.05
        timber(a, b, w, hb)
for sy in (-1, 1): timber((X - h_, sy * h_, HT + 0.65), (X + h_, sy * h_, HT + 0.65), 0.08, 0.1)
for sx in (-1, 1): timber((X + sx * h_, -h_, HT + 0.65), (X + sx * h_, h_, HT + 0.65), 0.1, 0.08)
for sx in (-1.25, 1.25):                                                 # bridge hinge blocks + iron pins
    timber((X + sx, -h_ + 0.05, HT + 0.05), (X + sx, -h_ - 0.15, HT + 0.05), 0.2, 0.18)
    log((X + sx - 0.12, -h_ - 0.1, HT + 0.08), (X + sx + 0.12, -h_ - 0.1, HT + 0.08), 0.04, kind='iron')
for sx in (-1.1, 1.1):                                                   # bridge ropes to the parapet
    timber((X + sx, -h_ + 0.02, HT + 1.1), (X + sx * 0.9, -h_ - 0.35, HT + 1.6), 0.03, 0.03, kind='leather')
HINGE = Vector((X, -h_ - 0.1, HT + 0.08)); print('HINGE', tuple(HINGE - Vector((X, 0, 0))), flush=True)
# ---- drop bridge (own mesh; pivot = hinge; modelled DOWN / deployed along -Y) ---------------------------------------
SEG[0] = 3; BL = 3.3
for sx in (-1.15, 1.15): timber(HINGE + Vector((sx, 0, -0.02)), HINGE + Vector((sx, -BL, -0.02)), 0.16, 0.2)
yy = 0.15
while yy < BL - 0.1: timber(HINGE + Vector((-1.25, -yy, 0.1)), HINGE + Vector((1.25, -yy + j(0.005), 0.1)), 0.24, 0.05); yy += 0.27
for k in (0.2, 0.5, 0.8): timber(HINGE + Vector((-1.2, -BL * k, 0.15)), HINGE + Vector((1.2, -BL * k, 0.15)), 0.05, 0.05)  # cleats
for sx in (-1.2, 1.2):                                                   # iron spikes on the lip to bite the wall walk
    for k in range(3): log(HINGE + Vector((sx * (0.3 + 0.3 * k), -BL + 0.05, 0.0)), HINGE + Vector((sx * (0.3 + 0.3 * k), -BL - 0.12, -0.18)), 0.025, tip=0.08, kind='iron', seg=6)
# ---- tower wreck (burnt stump, cladding collapsed) ------------------------------------------------------------------
SEG[0] = 4; BURN[0] = 1.0; X = OFF[4]
for sx in (-1, 1): timber((X + sx * 1.6, -1.75, TZ + 0.06), (X + sx * 1.6 + j(0.03), 1.75, TZ + 0.06 - 0.25 * (sx > 0)), 0.26, 0.28)
wheel((X - 1.95, -1.15, TZ), 'X', TR, spokes=10, broken=4); wheel((X - 1.95, 1.15, TZ), 'X', TR, spokes=10)
wheel((X + 1.95, -1.15, TZ - 0.2), 'X', TR, spokes=10, broken=2); wheel((X + 2.9, 2.2, 0.06), 'Z', TR, spokes=10, broken=7)
for sy in (-1.6, 0, 1.6): timber((X - 1.75, sy, TZ + 0.3), (X + 1.75, sy, TZ + 0.3 - 0.12 * (sy > 0)), 0.22, 0.22)
for (sx, sy), hh in zip(((-1, -1), (1, -1), (-1, 1), (1, 1)), (4.3, 2.2, 3.4, 1.5)):
    top_ = Vector((X + sx * hw(hh), sy * hw(hh), hh)); timber((X + sx * 1.6, sy * 1.6, H0 - 0.15), top_, 0.26, 0.26)
    splinters(top_, (j(0.3), j(0.3), 1), 9, 0.35)
yy = -1.45
while yy < 1.45:                                                         # first deck, planks missing / burnt through
    if rng.random() > 0.25:
        x1 = 1.6 if rng.random() > 0.3 else rng.uniform(-0.6, 0.9)
        timber((X - 1.6, yy, H0), (X + x1, yy, H0 + j(0.01)), 0.28, 0.05)
        if x1 < 1.5: splinters((X + x1, yy, H0), (1, 0, 0), 4, 0.15)
    yy += 0.3
z = H0 + 0.1                                                             # cladding stubs, jagged at the top
while z < 2.8:
    h_ = hw(z) + 0.07
    for face in range(3):
        if rng.random() < (z - H0) * 0.35: continue
        L0 = rng.uniform(-h_, -h_ + 0.6); L1 = rng.uniform(h_ - 1.4, h_)
        if face == 0: a, b, w = (X + L0, -h_, z), (X + L1, -h_, z), (0.05, 0.29)
        else: s_ = -1 if face == 1 else 1; a, b, w = (X + s_ * h_, L0, z), (X + s_ * h_, L1, z), (0.05, 0.29)
        timber(a, b, *w, tilt=0.02)
        if L1 < h_ - 0.1: splinters(b, Vector(b) - Vector(a), 3, 0.12)
    z += 0.3
for k in range(16):                                                      # boards and beams thrown round the wreck
    ang = rng.uniform(0, 2 * math.pi); rr = rng.uniform(1.9, 3.6)
    a = Vector((X + rr * math.cos(ang), rr * math.sin(ang), rng.uniform(0.03, 0.15)))
    d = Vector((rng.normal(0, 1), rng.normal(0, 1), rng.normal(0, 0.1))).normalized()
    if k < 12: timber(a, a + d * rng.uniform(1.0, 2.6), 0.29, 0.05)
    else: timber(a, a + d * rng.uniform(2.0, 3.0), 0.18, 0.2); splinters(a, -d, 4, 0.2)
timber((X - 3.4, -0.6, 0.12), (X - 1.45, -0.5, 4.0), 0.26, 0.26); splinters((X - 3.4, -0.6, 0.12), (-1, 0, -0.2), 5, 0.3)   # leaning post
slab((X + 0.3, -hw(1.5) - 0.6, 0.18), (1, 0.1, 0.02), (0.1, -1, 0.4), 2.8, 1.4, 0.025, sag=0.06, n=2)   # charred hide on the ground
# ---- join into two atlases, UV, split back by seg -------------------------------------------------------------------
def atlas(name, segs):
    bpy.ops.object.select_all(action='DESELECT')
    own = [o for o, s_ in zip(pieces, PSEG) if s_ in segs]
    for o in own: o.select_set(True)
    bpy.context.view_layer.objects.active = own[0]; bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
    seg = np.empty(len(ob.data.vertices), np.int32); ob.data.attributes['seg'].data.foreach_get('value', seg)
    for k in segs:
        c = ob.copy(); c.data = ob.data.copy(); c.name = NAMES[k]; c.data.name = NAMES[k]; bpy.context.scene.collection.objects.link(c)
        bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
        off = Vector((-OFF[k], 0, 0)) - (HINGE - Vector((OFF[k], 0, 0)) if k == 3 else Vector())
        bmesh.ops.translate(bm, vec=off, verts=bm.verts); bm.to_mesh(c.data); bm.free()
        print('SEG', NAMES[k], len(c.data.polygons), sum(len(p.vertices) - 2 for p in c.data.polygons), flush=True)
atlas('SM_RamAtlas', (0, 1)); atlas('SM_TowerAtlas', (2, 3, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'siege.blend'))
