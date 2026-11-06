# #543 mine lift + find (TGA PC, 2026-11-06). blender -b --factory-startup -P build_mine543.py  -> mine543.blend (env WORK)
# Owner: a real door at the mine entrance, [E] -> into a big bucket that lowers like a medieval lift (the hidden loading
# bar), and down there a floating historic weapon with VFX and an info card.
# Same kit rules as #309 (tools/tga/mine/build_mine.py, whose helpers this imports): metres, Z up, real size, tiling
# oak / iron / rock / ore sets on metric UVs, so the new pieces reuse MI_MineOak / Iron / Rock / Ore in UE.
#   SM_MineGate_Door        hinged oak door for the hut mouth and the winding room. Pivot ON THE HINGE (bottom),
#                           leaf runs +Y from it, front faces +X. BP swings it about Z.
#   SM_MineGate_Bulkhead    plank wall that closes the 3 m kit tunnel profile round SM_Mine_DoorFrame (faces +X)
#   SM_MineShaft_Top        carved rock: dead passage, winding room 5 x 5.2 m, shaft 2.3 m square going 13.2 m down.
#                           Door plane at x = 1.2, shaft centre (3.9, 0), floor z = 0
#   SM_MineShaft_Bottom     carved rock module that REPLACES the dungeon's Tunnel_DeadEnd on the 4 m grid (x = 0 face joins
#                           the T), landing room, shaft centre (3.25, 0) rising to z = 14.6
#   SM_MineShaft_Cribbing   oak shaft lining, 13 m, pivot at its top: frames every 1.3 m + corner posts
#   SM_MineShaft_Collar     collar beams round the hole + plank floor edge + the two windlass trestles
#   SM_MineWindlass_Drum    drum + iron bands + 2 cranks + rope turns. Pivot ON THE AXLE (axis Y). BP spins it
#   SM_MineBucket           kibble: staved oak tub 1.4 m wide, 3 hoops, iron bail. Pivot bottom centre. Sockets (import
#                           script): Rope (bail eye), Stand (where the hero stands), Lamp
#   SM_MineRope_1m          3-strand hemp, pivot at the BOTTOM, z 0..1 m: BP scales Z to the drum (UV is world-locked)
#   SM_Mine_OreVein_Cracked the find: an ore face split open, glowing cleft (slot M_RevealGlow)
#   SM_Ulfberht             Viking-age sword (Petersen type X), point down, pivot at the balance point, own textures
#   SM_Reveal_LightShaft / SM_Reveal_Motes / SM_InfoCard   VFX + the card (own materials, see import_mine543_ue.py)
import bpy, bmesh, numpy as np, math, os, sys
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'ref'))
import build_mine as K                               # #309 helpers: fbm, ss, sweep, line, block, apply_mod, prop, cyl, box, uvbox
D = os.environ.get('WORK') or os.path.join(HERE, 'work'); os.makedirs(D, exist_ok=True)
rng = np.random.default_rng(543)
mat, link, act, apply_mod, uvbox = K.mat, K.link, K.act, K.apply_mod, K.uvbox
cyl, box, fbm, ss = K.cyl, K.box, K.fbm, K.ss

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
def shell(name, voids, ntris, seed, amp=0.07, clip_x0=False, zoff=0.0):
    """The rock skin of a closed cavity, seen from inside. Voxel remesh fills sealed hollows, so instead of carving a
    block (K.carve) the voids are joined, remeshed into their union, displaced, and their normals flipped inward.
    clip_x0: cut the cavity open at x = 0 (a kit module face: displacement fades to 0 there, so it joins the T)."""
    for v in voids: v.select_set(True)
    act(voids[0])
    for v in voids[1:]: v.select_set(True)
    bpy.ops.object.join(); o = bpy.context.active_object; o.name = o.data.name = name
    apply_mod(o, 'REMESH', mode='VOXEL', voxel_size=0.05)
    me = o.data; n = len(me.vertices); P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    N = np.array([v.vector for v in me.vertex_normals])                       # outward from the cavity = into the rock
    fade = ss(0.02, 0.6, np.abs(P[:, 0])) if clip_x0 else np.ones(n)
    calm = 1 - 0.8 * ss(0.6, 0.9, -N[:, 2]) * ss(0.4, 0.0, np.abs(P[:, 2]))    # walkable floors stay calmer
    spall = np.floor(fbm(P, 2.2, 3, seed + 1) * 5) / 5                       # fire-set: rounded walls, shallow spalled flakes
    d = amp * (fbm(P, 0.9, 3, seed) - 0.5) + 0.035 * (spall - 0.5) + 0.006 * (fbm(P, 9, 2, seed + 2) - 0.5)
    P += N * (d * fade * calm)[:, None]; me.vertices.foreach_set('co', P.ravel()); me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    if clip_x0:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    apply_mod(o, 'DECIMATE', ratio=min(1.0, ntris / max(1, 2 * len(me.polygons))))   # remesh makes quads: 2 tris each
    me = o.data; n = len(me.vertices); P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    Nn = np.array([v.vector for v in me.vertex_normals])
    floor = (Nn[:, 2] > 0.8)
    streak = ss(0.62, 0.8, K.vn(P * [1, 1, 0.08], 5.0, seed + 3))
    wet = np.clip(ss(0.5, 0.0, P[:, 2]) * floor * 0.85 + streak * 0.6 + 0.15 * fbm(P, 1.2, 2, seed + 4), 0, 1)
    wet = np.maximum(wet, ss(-2.0, -9.0, P[:, 2] - zoff) * 0.8 * (P[:, 2] - zoff < 0))   # shaft walls wetter going down (seepage); zoff
                                                                             # lines the bottom shaft up with the top one at the swap
    soot = np.clip(ss(2.4, 3.4, P[:, 2]) * (0.55 + 0.6 * (fbm(P, 0.7, 2, seed + 5) - 0.5)), 0, 1)
    puddle = ss(0.04, 0.0, np.abs(P[:, 2])) * floor * ss(0.5, 0.62, fbm(P, 0.8, 2, seed + 6))
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); cols = np.ones((n, 4)); cols[:, 0] = wet; cols[:, 1] = soot; cols[:, 2] = puddle
    ca.data.foreach_set('color', cols.ravel())
    me.materials.clear(); me.materials.append(mat('M_MineRock')); uvbox(o, 2.0); act(o); bpy.ops.object.shade_smooth()
    return o
def block(name, x0, x1, y0, y1, z0, z1): return K.block(name, x0, x1, y0, y1, z0, z1)
def rblock(name, bx, bev, seg=4):
    o = block(name, *bx); apply_mod(o, 'BEVEL', width=bev, segments=seg); return o
def loglen(bm, a, b, r, seg=8): cyl(bm, a, b, r, seg, 0.07, rng)

# ------------------------------------------------------------------------------------------------ door + bulkhead
def door_planks(bm):
    for i in range(6):                                                       # 6 riven oak planks, hinge at y = 0
        h = 2.2 - rng.uniform(0.0, 0.025); y = 0.1 + i * 0.2
        box(bm, (0.0, y, h / 2), (0.06, 0.192, h), rng.uniform(-0.004, 0.004))
def door_battens(bm):                                                        # Z-brace on the back (-X)
    for zz in (0.35, 1.85): box(bm, (-0.055, 0.6, zz), (0.05, 1.12, 0.14))
    a, b = Vector((-0.055, 0.12, 0.42)), Vector((-0.055, 1.08, 1.78)); m = (a + b) / 2; L = (b - a).length
    box(bm, tuple(m), (0.045, 0.13, L), 0.0); vs = bm.verts[-8:]
    R = Matrix.Rotation(-math.atan2(b.y - a.y, b.z - a.z), 4, 'X')
    for v in vs: v.co = m + R @ (v.co - m)
def door_irons(bm):
    for zz in (0.35, 1.85):                                                  # strap hinges: wide at the knuckle, tapering
        box(bm, (0.04, 0.42, zz), (0.014, 0.84, 0.075)); box(bm, (0.04, 0.93, zz), (0.014, 0.2, 0.05))
        cyl(bm, (0.0, -0.005, zz - 0.06), (0.0, -0.005, zz + 0.06), 0.022, 8)  # knuckle on the hinge line
        for yy in (0.08, 0.3, 0.52, 0.74, 0.96): cyl(bm, (0.046, yy, zz), (0.058, yy, zz), 0.014, 6)
    for zz in (1.1,):
        for yy in (0.1, 0.3, 0.5, 0.7, 0.9, 1.1): cyl(bm, (0.031, yy, zz), (0.043, yy, zz), 0.013, 6)   # clench nails
    cyl(bm, (0.03, 1.06, 1.05), (0.09, 1.06, 1.05), 0.016, 6)                 # ring-pull boss
    t = bmesh.ops.create_circle(bm, segments=14, radius=0.055)['verts']
    for v in t: v.co = Vector((0.1, 1.06 + v.co.x, 0.99 + v.co.y))
    ring = bmesh.ops.extrude_edge_only(bm, edges=list({e for v in t for e in v.link_edges}))
    for v in [e for e in ring['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.x += 0.018
    box(bm, (0.045, 0.9, 1.25), (0.02, 0.45, 0.04)); box(bm, (0.045, 1.15, 1.25), (0.06, 0.04, 0.09))  # latch bar + keeper
def bulk_planks(bm):                                                         # fills the kit profile round a 1.44 x 2.42 opening
    for i in range(16):
        y = -1.5 + 0.1 + i * 0.19
        if abs(y) < 0.86:
            box(bm, (0.0, y, 2.42 + 0.3), (0.05, 0.18, 0.6)); continue
        top = 2.8 if abs(y) < 1.2 else 2.8 - (abs(y) - 1.2) * 1.6
        box(bm, (0.0, y, top / 2), (0.05, 0.18, top), rng.uniform(-0.01, 0.01))
def bulk_rails(bm):
    for zz in (0.5, 1.7): box(bm, (-0.05, -1.17, zz), (0.06, 0.62, 0.12)); box(bm, (-0.05, 1.17, zz), (0.06, 0.62, 0.12))

# ------------------------------------------------------------------------------------------------ shaft timber
def crib(bm, z, hw=1.04, r=0.095):
    for s in (-1, 1):
        loglen(bm, (-hw - 0.15, s * hw, z), (hw + 0.15, s * hw, z), r)
        loglen(bm, (s * hw, -hw - 0.15, z + 0.17), (s * hw, hw + 0.15, z + 0.17), r)
CRIB = 1.3                                                                   # frame pitch: both shafts share it (seamless swap)
def cribbing(frames, post):
    def f(bm):
        for k in range(1, frames + 1): crib(bm, -k * CRIB)
        for sx in (-1, 1):
            for sy in (-1, 1): loglen(bm, (sx * 0.93, sy * 0.93, 0.0), (sx * 0.93, sy * 0.93, -post), 0.075, 7)
    return f
def cribbing_lag(bm):                                                        # a few lagging boards where the rock spalled
    for k in range(9):
        z = -0.65 - k * 1.3 - rng.uniform(0, 0.4); s = rng.choice([-1, 1]); ax = rng.integers(0, 2)
        c = (s * 1.09, rng.uniform(-0.5, 0.5), z) if ax else (rng.uniform(-0.5, 0.5), s * 1.09, z)
        box(bm, c, (0.035, 0.7, 0.9) if ax else (0.7, 0.035, 0.9), rng.uniform(-0.05, 0.05))
def collar(bm):
    for s in (-1, 1):                                                        # collar beams round the 2.3 m hole
        box(bm, (0, s * 1.3, -0.08), (2.9, 0.3, 0.2), rng.uniform(-0.01, 0.01)); box(bm, (s * 1.3, 0, -0.03), (0.3, 2.3, 0.2))
    for s in (-1, 1):                                                        # windlass trestles beside the hole (axle y +-1.45)
        y = s * 1.62
        for dx in (-0.42, 0.42): loglen(bm, (0.22 + dx, y, -0.02), (0.22 + dx * 0.15, y, 1.12), 0.075, 7)
        loglen(bm, (0.22 - 0.4, y, 0.35), (0.22 + 0.4, y, 0.35), 0.06, 6)
        box(bm, (0.22, y, 1.12), (0.22, 0.26, 0.12))                          # bearing block
def collar_iron(bm):
    for s in (-1, 1):
        box(bm, (0.22, s * 1.62, 1.19), (0.18, 0.28, 0.02))                   # bearing straps
        for dx in (-0.06, 0.06): cyl(bm, (0.22 + dx, s * 1.62 - 0.14, 1.2), (0.22 + dx, s * 1.62 - 0.14, 1.1), 0.012, 6)
DRUM_R, DRUM_Z, DRUM_X = 0.2, 1.15, 0.22
def drum(bm):
    cyl(bm, (0, -1.38, 0), (0, 1.38, 0), DRUM_R, 14, 0.03, rng)
    for s in (-1, 1): cyl(bm, (0, s * 1.38, 0), (0, s * 1.75, 0), 0.05, 8)      # axle stubs into the bearings
def drum_iron(bm):
    for yy in (-1.25, -0.5, 0.5, 1.25): cyl(bm, (0, yy - 0.03, 0), (0, yy + 0.03, 0), DRUM_R + 0.012, 14)
    for s in (-1, 1):                                                        # cranks: arm + handle, opposed 180 deg
        a = 0 if s > 0 else math.pi; tip = Vector((0.38 * math.cos(a), s * 1.82, 0.38 * math.sin(a)))
        box(bm, (0.19 * math.cos(a), s * 1.78, 0.19 * math.sin(a)), (0.42 if s else 0, 0.04, 0.05), 0)
        cyl(bm, tuple(tip), tuple(tip + Vector((0, s * 0.06, 0))), 0.018, 6)
def drum_grip(bm):
    for s in (-1, 1):
        a = 0 if s > 0 else math.pi; tip = Vector((0.38 * math.cos(a), s * 1.86, 0.38 * math.sin(a)))
        cyl(bm, tuple(tip), tuple(tip + Vector((0, s * 0.3, 0))), 0.03, 8)
def drum_rope(bm):                                                           # rope turns wound on the drum
    for i in range(16):
        y = -0.4 + i * 0.052; cyl(bm, (0, y - 0.024, 0), (0, y + 0.024, 0), DRUM_R + 0.024, 14)

# ------------------------------------------------------------------------------------------------ the bucket (kibble)
BK_R0, BK_R1, BK_H = 0.62, 0.70, 1.0
def bucket_r(t): return BK_R0 + (BK_R1 - BK_R0) * t + 0.035 * math.sin(math.pi * t)   # slight barrel bulge
def staves(bm):
    n = 22
    for i in range(n):
        a0, a1 = 2 * math.pi * (i + 0.04) / n, 2 * math.pi * (i + 0.96) / n; top = BK_H - rng.uniform(0, 0.03)
        rows = []
        for j in range(7):
            t = j / 6; z = t * top; r = bucket_r(t)
            ring = []
            for a in (a0, a1):
                for rr in (r, r - 0.045): ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
            rows.append(ring)                                                # ring: outer a0, inner a0, outer a1, inner a1
        for r0, r1 in zip(rows, rows[1:]):
            for q in ((0, 2), (3, 1), (1, 0), (2, 3)): bm.faces.new((r0[q[0]], r0[q[1]], r1[q[1]], r1[q[0]]))
        bm.faces.new((rows[0][0], rows[0][1], rows[0][3], rows[0][2])); bm.faces.new((rows[-1][2], rows[-1][3], rows[-1][1], rows[-1][0]))
    cyl(bm, (0, 0, 0.04), (0, 0, 0.09), BK_R0 - 0.03, 22)                    # the floor, let into the croze groove
def hoops(bm):
    for t in (0.1, 0.5, 0.88):
        z = t * BK_H; r = bucket_r(t) + 0.01; hb = 0.05
        rr = [bm.verts.new((r * math.cos(2 * math.pi * k / 32), r * math.sin(2 * math.pi * k / 32), z + dz)) for dz in (-hb, hb) for k in range(32)]
        ro = [bm.verts.new((v.co.x * (1 + 0.012 / r), v.co.y * (1 + 0.012 / r), v.co.z)) for v in rr]
        for k in range(32):
            k1 = (k + 1) % 32
            bm.faces.new((ro[k], ro[k1], ro[32 + k1], ro[32 + k])); bm.faces.new((rr[k], rr[32 + k], rr[32 + k1], rr[k1]))
            bm.faces.new((rr[k], rr[k1], ro[k1], ro[k])); bm.faces.new((rr[32 + k], ro[32 + k], ro[32 + k1], rr[32 + k1]))
    for s in (-1, 1):                                                        # lugs + the bail (a half ring in the x = 0 plane)
        box(bm, (0, s * (BK_R1 + 0.035), BK_H - 0.08), (0.1, 0.05, 0.22))
    pts = [Vector((0, (BK_R1 + 0.05) * math.cos(math.pi * k / 20), BK_H - 0.08 + 0.78 * math.sin(math.pi * k / 20))) for k in range(21)]
    for a, b in zip(pts, pts[1:]): cyl(bm, tuple(a), tuple(b), 0.02, 6)
    t = bmesh.ops.create_circle(bm, segments=10, radius=0.045)['verts']       # bail eye the rope hooks into
    for v in t: v.co = Vector((v.co.x * 0.4, v.co.x, BK_H + 0.74 + 0.045 + v.co.y))
    for v in t: v.co.x = 0.0
    e = bmesh.ops.extrude_edge_only(bm, edges=list({ed for v in t for ed in v.link_edges}))
    for v in [g for g in e['geom'] if isinstance(g, bmesh.types.BMVert)]: v.co.x += 0.02
BUCKET_EYE = BK_H + 0.74 + 0.09                                              # rope attach height above the bucket floor

def rope(bm, L=1.0, r=0.024):
    """3 twisted strands as one 9-sided tube with a lobed section (the hemp lay reads in silhouette); V = metres."""
    rings = []; n = 18; m = 12
    for j in range(m + 1):
        z = L * j / m; tw = z / 0.12 * 2 * math.pi                            # lay: one turn per 12 cm
        rings.append([bm.verts.new((r * (1 + 0.16 * math.cos(3 * (2 * math.pi * k / n) - tw)) * math.cos(2 * math.pi * k / n),
                                    r * (1 + 0.16 * math.cos(3 * (2 * math.pi * k / n) - tw)) * math.sin(2 * math.pi * k / n), z)) for k in range(n)])
    for a, b in zip(rings, rings[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))

# ------------------------------------------------------------------------------------------------ the sword (Ulfberht, Petersen X)
# Real-size: blade 0.90 m, 5.4 cm at the guard, fuller ~45 % wide almost to the point; guard 19 cm straight bar;
# grip 9.5 cm (leather over wood); "tea-cosy" pommel 6.6 cm. Point DOWN, z = 0 at the balance point (~14 cm below the guard).
BAL = 0.14
def blade_ring(t):
    w = 0.054 - 0.017 * t ** 1.4                                              # half-width x2, gentle taper
    if t > 0.86: w *= math.sqrt(max(0.0, 1 - ((t - 0.86) / 0.14) ** 2)) * 0.98 + 0.02 * (1 - t) / 0.14   # rounded spatulate point
    th = 0.0058 - 0.0028 * t                                                  # thickness at the fuller shoulders
    fw = 0.42 * w * (1 if t < 0.82 else max(0.0, 1 - (t - 0.82) / 0.08)); fd = 0.0016 * (1 if t < 0.82 else max(0.0, 1 - (t - 0.82) / 0.08))
    h = w / 2; out = []
    xs = [-h, -0.8 * h, -0.62 * h, -fw / 2 - 0.002, -fw / 4, 0.0, fw / 4, fw / 2 + 0.002, 0.62 * h, 0.8 * h, h]
    for x in xs:                                                             # lenticular edge bevels, flat-ish shoulders, a hollow fuller
        a = abs(x)
        if a >= 0.62 * h: y = th / 2 * (h - a) / (0.38 * h) * (0.9 if a < 0.8 * h else 0.7) + 0.0002
        elif a > fw / 2: y = th / 2
        else: y = th / 2 - fd * math.cos(math.pi * a / max(fw, 1e-4)) ** 1.0 * 0.9
        out.append((x, y))
    top = [(x, y) for x, y in out]; bot = [(x, -y) for x, y in reversed(out[1:-1])]
    return top + bot, w
def blade(bm):
    rings = []; m = 72
    for j in range(m + 1):
        t = j / m; z = 0.008 - 0.908 * t; sec, _ = blade_ring(min(t, 0.999))   # starts inside the guard: no gap at the shoulder
        rings.append([bm.verts.new((x, y, z + BAL)) for x, y in sec])
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for k in range(n): bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))
    bm.faces.new(rings[0][::-1]); tip = bm.verts.new((0, 0, BAL - 0.905))
    for k in range(n): bm.faces.new((rings[-1][k], tip, rings[-1][(k + 1) % n]))
def hilt(bm):
    g = BAL                                                                  # guard bottom sits on the blade shoulder
    r = bmesh.ops.create_cube(bm, size=1.0)['verts']                         # guard: 19 cm bar, slightly narrowing to the ends
    for v in r:
        x = v.co.x * 0.19; v.co = Vector((x, v.co.y * 0.022 * (1 - 0.25 * abs(x) / 0.095), g + 0.008 + v.co.z * 0.016 * (1 - 0.2 * abs(x) / 0.095)))
    rings = []                                                               # grip: oval, swelling a little mid-way (leather over wood)
    for j in range(9):
        t = j / 8; z = g + 0.012 + 0.101 * t; r = 0.0128 + 0.0022 * math.sin(math.pi * t)
        rings.append([bm.verts.new((r * 1.18 * math.cos(2 * math.pi * k / 12), r * 0.86 * math.sin(2 * math.pi * k / 12), z)) for k in range(12)])
    for a, b in zip(rings, rings[1:]):
        for k in range(12): bm.faces.new((a[k], a[(k + 1) % 12], b[(k + 1) % 12], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    p0 = g + 0.111
    r = bmesh.ops.create_cube(bm, size=1.0)['verts']                         # lower pommel bar
    for v in r: v.co = Vector((v.co.x * 0.066, v.co.y * 0.026, p0 + 0.007 + v.co.z * 0.014))
    rings = []                                                               # tea-cosy cap: a half-lens over the bar
    for j in range(9):
        a = math.pi / 2 * j / 8; zz = p0 + 0.014 + 0.026 * math.sin(a); s = math.cos(a)
        rings.append([bm.verts.new((0.031 * s * math.cos(2 * math.pi * k / 20) * 1.0 + 0.0,
                                    0.0115 * max(s, 0.25) * math.sin(2 * math.pi * k / 20), zz)) for k in range(20)])
    for a, b in zip(rings, rings[1:]):
        for k in range(20): bm.faces.new((a[k], a[(k + 1) % 20], b[(k + 1) % 20], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])

# ------------------------------------------------------------------------------------------------ VFX + card meshes
def light_shaft(bm, h=5.5, r0=0.95, r1=0.32, n=28, m=6):
    rings = [[bm.verts.new(((r0 + (r1 - r0) * j / m) * math.cos(2 * math.pi * k / n), (r0 + (r1 - r0) * j / m) * math.sin(2 * math.pi * k / n), h * j / m)) for k in range(n)] for j in range(m + 1)]
    for a, b in zip(rings, rings[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
def motes(bm, count=180):
    for i in range(count):
        a = rng.uniform(0, 2 * math.pi); r = 1.0 * math.sqrt(rng.uniform(0, 1)); c = Vector((r * math.cos(a), r * math.sin(a), rng.uniform(0.2, 2.8)))
        s = rng.uniform(0.006, 0.016); u = Vector(rng.normal(size=3)).normalized(); v = u.orthogonal().normalized(); w = u.cross(v)
        q = [bm.verts.new(c + (v * x + w * y) * s) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        bm.faces.new(q)
def card(bm, w=1.6, h=1.0):
    q = [bm.verts.new((0, y, z)) for y, z in ((-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h))]; bm.faces.new(q)   # faces +X

def mesh_from(name, parts, uvmode=None, bevel=0.0):
    me = bpy.data.meshes.new(name); o = link(name, me); bm = bmesh.new(); used = []
    for mn, fn in parts:
        if mn not in used: used.append(mn)
        before = set(bm.faces); fn(bm)
        for f in bm.faces:
            if f not in before: f.material_index = used.index(mn)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for mn in used: me.materials.append(mat(mn))
    if bevel: apply_mod(o, 'BEVEL', width=bevel, segments=1, limit_method='ANGLE')
    if uvmode is not None: uvbox(o, uvmode)
    return o
def set_uv(o, fn):
    me = o.data; uvl = me.uv_layers[0] if me.uv_layers else me.uv_layers.new()
    for p in me.polygons:
        for li in p.loop_indices: uvl.data[li].uv = fn(me.vertices[me.loops[li].vertex_index].co, p)

if __name__ == '__main__':
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    kit = []
    kit.append(mesh_from('SM_MineGate_Door', [('M_MineOak', door_planks), ('M_MineOak', door_battens), ('M_MineIron', door_irons)], 1.0, 0.004))
    kit.append(mesh_from('SM_MineGate_Bulkhead', [('M_MineOak', bulk_planks), ('M_MineOak', bulk_rails)], 1.0, 0.004))
    # winding room shell: passage (dead, dark) -> door plane x = 1.2 -> room -> shaft
    kit.append(shell('SM_MineShaft_Top',
                     [K.sweep(K.line((-2.9, 0, 0), (1.9, 0, 0), 6)), rblock('room', (1.2, 6.3, -2.6, 2.6, 0.0, 3.7), 1.1),
                      rblock('shaft', (2.75, 5.05, -1.15, 1.15, -13.3, 0.6), 0.15, 2)], 22000, 543))
    # dungeon landing: replaces SM_Mine_Tunnel_DeadEnd at grid x 22 (module x 0..4 and on to 5.6)
    kit.append(shell('SM_MineShaft_Bottom',
                     [K.sweep(K.line((-0.3, 0, 0), (2.6, 0, 0), 4)), rblock('land', (1.7, 4.95, -1.75, 1.75, 0.0, 3.3), 0.8),
                      rblock('shaft', (2.1, 4.4, -1.15, 1.15, 1.5, 14.6), 0.15, 2)], 16000, 544, clip_x0=True, zoff=19.7))
    # top: 10 frames, posts to the shaft floor. bottom (top at z 14.5): 8 frames stop above the landing roof (3.3 m), the
    # corner posts run on down to the landing floor as the bucket's guide posts
    kit.append(mesh_from('SM_MineShaft_Cribbing_Top', [('M_MineOak', cribbing(10, 13.0)), ('M_MineOak', cribbing_lag)], 1.0))
    kit.append(mesh_from('SM_MineShaft_Cribbing_Bottom', [('M_MineOak', cribbing(8, 14.5)), ('M_MineOak', cribbing_lag)], 1.0))
    kit.append(mesh_from('SM_MineShaft_Collar', [('M_MineOak', collar), ('M_MineIron', collar_iron)], 1.0, 0.006))
    kit.append(mesh_from('SM_MineWindlass_Drum', [('M_MineOak', drum), ('M_MineIron', drum_iron), ('M_MineOak', drum_grip), ('M_MineRope', drum_rope)], 1.0))
    kit.append(mesh_from('SM_MineBucket', [('M_MineOak', staves), ('M_MineIron', hoops)], 1.0, 0.004))
    o = mesh_from('SM_MineRope_1m', [('M_MineRope', rope)])
    set_uv(o, lambda co, p: (math.atan2(co.y, co.x) / (2 * math.pi) + 0.5, co.z)); kit.append(o)
    # the find: the kit's ore face, split open with a glowing cleft
    vein = bpy.data.meshes.new('v'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=72, y_segments=60, size=1.0)
    for v in bm.verts: v.co = Vector((0, v.co.x * 1.6, (v.co.y + 1) * 1.3))
    bm.to_mesh(vein); bm.free(); o = link('SM_Mine_OreVein_Cracked', vein); apply_mod(o, 'SOLIDIFY', thickness=0.5, offset=-1)
    P = np.array([v.co for v in o.data.vertices]); front = P[:, 0] > -0.01
    edge = ss(0.0, 0.5, np.minimum(1.6 - np.abs(P[:, 1]), np.minimum(P[:, 2], 2.6 - P[:, 2])))
    cleft = np.exp(-((P[:, 1] - 0.08 * np.sin(P[:, 2] * 3.1)) / 0.16) ** 2) * ss(0.2, 0.6, P[:, 2]) * ss(2.5, 1.9, P[:, 2])
    P[:, 0] += np.where(front, (0.35 * fbm(P, 1.4, 3, 9) + 0.12 * (1 - np.abs(2 * fbm(P, 4, 3, 10) - 1))) * edge - 0.34 * cleft, 0)
    for v, p in zip(o.data.vertices, P): v.co = Vector(p)
    o.data.materials.append(mat('M_RevealVein'))                              # ore set + glow from vertex colour R (smooth, no stair-steps)
    ca = o.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); cols = np.zeros((len(P), 4)); cols[:, 3] = 1
    cols[:, 0] = np.where(front, ss(0.3, 0.85, cleft), 0.0); ca.data.foreach_set('color', cols.ravel())
    uvbox(o, 1.0); act(o); bpy.ops.object.shade_smooth(); kit.append(o)
    sw = mesh_from('SM_Ulfberht', [('M_Ulfberht', blade), ('M_Ulfberht', hilt)])
    act(sw); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))        # crisp edge bevels + caps, smooth flats
    for m in list(sw.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.004)
    bpy.ops.uv.pack_islands(rotate=False, margin=0.004); bpy.ops.object.mode_set(mode='OBJECT')
    uvl = sw.data.uv_layers[0]; uv = np.empty(len(uvl.data) * 2); uvl.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    lo, hi = uv.min(0), uv.max(0); uv = 0.004 + (uv - lo) / (hi - lo) * 0.992   # the 1:17 blade packs into a thin column:
    uvl.data.foreach_set('uv', uv.ravel()); kit.append(sw)                         # stretch to fill (denser across the blade)
    o = mesh_from('SM_Reveal_LightShaft', [('M_RevealShaft', light_shaft)])
    set_uv(o, lambda co, p: (math.atan2(co.y, co.x) / (2 * math.pi) + 0.5, co.z / 5.5)); kit.append(o)
    o = mesh_from('SM_Reveal_Motes', [('M_RevealMotes', motes)])
    me = o.data; me.uv_layers.new(); me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    uvl = me.uv_layers[0]; ca = me.color_attributes['Col']                    # fetch both after adding (adding one moves the other)
    for p in me.polygons:                                                     # per-mote quad UVs + a random phase in R
        ph = rng.uniform(0, 1)
        for k, li in enumerate(p.loop_indices): uvl.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[k % 4]; ca.data[li].color = (ph, rng.uniform(0, 1) if k == 0 else ph, 0, 1)
    kit.append(o)
    o = mesh_from('SM_InfoCard', [('M_InfoCard', card)]); set_uv(o, lambda co, p: (co.y / 1.6 + 0.5, co.z / 1.0)); kit.append(o)
    for o in kit:
        bm = bmesh.new(); bm.from_mesh(o.data); open_e = sum(1 for e in bm.edges if not e.is_manifold); bm.free()
        print('MESH %-26s tris %6d  open edges %5d  size %s' % (o.name, tris(o), open_e, tuple(round(x, 2) for x in o.dimensions)), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'mine543.blend'))
    print('BUILD OK', flush=True)
