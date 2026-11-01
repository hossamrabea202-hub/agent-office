# #401 stables: medieval timber stable range (lean-to), 16 x 7 m. checkking (Claude), 2026-11-01. Original, procedural.
#   blender -b --factory-startup -P build_stable.py -- <outdir>        -> stable.blend, SM_Stable.fbx
# Research: handoffs/cavalry-400/RESEARCH.md. Layout (metres, Z up, the open front faces -Y, pivot = front-left corner
# on the ground; the back wall at Y = 7 goes against the curtain wall):
#   - oak frame on pad-stones: 5 front posts (eaves 3.0 m) + 5 back posts (6.4 m), plates, tie beams, knee braces,
#     rafters every 0.6 m, shingle roof at 28 deg with 0.8 m overhang
#   - back and side walls: sill on a rubble plinth, studs + mid rail, limewashed wattle-and-daub panels (>= 12 cm thick)
#   - 6 standing stalls 1.6 x 3.0 m (X 0..9.6) + 2 loose boxes 3.2 x 3.2 m with half doors (X 9.6..16)
#   - manger + slanted hay rack along the back wall, tie rings, straw bedding, cobbled walk with a drain gully
# Materials (slots): Oak, Daub, Shingle, Straw, Cobble, Iron. Tiling textures (tex_stable.py, 2 m tiles). Large-scale
# wear is in the vertex colour 'Wear': R = baked AO, G = wet muck / urine (low on boards, behind the horses),
# B = sun bleach (up/out-facing, unoccluded). Collision: UCX_ boxes.
import bpy, bmesh, numpy as np, math, os, sys
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
rng = np.random.default_rng(401)
MATS = ['Oak', 'Daub', 'Shingle', 'Straw', 'Cobble', 'Iron']
MI = {m: i for i, m in enumerate(MATS)}
BM = bmesh.new(); UVL = BM.loops.layers.uv.new('UVMap')
COLL = []                                                        # collision boxes: (center, size, rotation matrix)

def frame(p0, p1, up=(0, 0, 1)):
    p0 = Vector(p0); p1 = Vector(p1); X = (p1 - p0); L = X.length; X.normalize()
    Z = Vector(up); Z = (Z - Z.dot(X) * X)
    if Z.length < 1e-6: Z = Vector((0, 1, 0)) - Vector((0, 1, 0)).dot(X) * X
    Z.normalize(); Y = Z.cross(X)
    return Matrix(((X.x, Y.x, Z.x), (X.y, Y.y, Z.y), (X.z, Y.z, Z.z))), L

def piece(mat, p0, p1, w, h, up=(0, 0, 1), bevel=0.012, seg=0.3, uv='timber', top=None, jitter=0.0, taper=0.0, coll=False, wob=0.0, cutw=0.0):
    """box from p0 to p1 (long axis), cross-section w (local Y) x h (local Z), bevelled, cut every `seg` metres.
    uv: 'timber' = U along the length (grain), 'world' = box projection in world metres, 'roof' = top face downslope.
    top: material for the local +Z face (roof). wob: noise displacement amplitude (stones, daub)."""
    R, L = frame(p0, p1, up)
    if jitter:                                                    # carpentry is never exact
        R = R @ Matrix.Rotation(rng.normal(0, jitter), 3, 'Y') @ Matrix.Rotation(rng.normal(0, jitter), 3, 'Z')
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.scale(b, vec=(L, w, h), verts=b.verts); bmesh.ops.translate(b, vec=(L / 2, 0, 0), verts=b.verts)
    n = max(1, int(L / seg))
    for k in range(1, n):
        g = b.verts[:] + b.edges[:] + b.faces[:]
        bmesh.ops.bisect_plane(b, geom=g, plane_co=(L * k / n, 0, 0), plane_no=(1, 0, 0))
    if cutw:                                                      # wide slabs (roof): cut across the width too
        m = max(1, int(w / cutw))
        for k in range(1, m):
            g = b.verts[:] + b.edges[:] + b.faces[:]
            bmesh.ops.bisect_plane(b, geom=g, plane_co=(0, -w / 2 + w * k / m, 0), plane_no=(0, 1, 0))
    if wob > 0 and uv == 'world':                                # big flat faces (daub, stones): cut a grid too
        for ax, size in ((1, w), (2, h)):
            m = max(1, int(size / 0.25))
            for k in range(1, m):
                g = b.verts[:] + b.edges[:] + b.faces[:]
                co = [0, 0, 0]; co[ax] = -size / 2 + size * k / m; no = [0, 0, 0]; no[ax] = 1
                bmesh.ops.bisect_plane(b, geom=g, plane_co=co, plane_no=no)
    if bevel > 0:
        edges = [e for e in b.edges if abs((e.verts[0].co - e.verts[1].co).normalized().x) > 0.99 or
                 (abs(e.verts[0].co.x - e.verts[1].co.x) < 1e-5 and (e.verts[0].co.x < 1e-4 or e.verts[0].co.x > L - 1e-4))]
        # only the 4 long edges and the 8 end-cap edges are real corners: keep those that lie on the box outline
        edges = [e for e in edges if all(abs(abs(v.co.y) - w / 2) < 1e-5 or abs(abs(v.co.z) - h / 2) < 1e-5 for v in e.verts)
                 and sum(1 for v in e.verts if abs(abs(v.co.y) - w / 2) < 1e-5 and abs(abs(v.co.z) - h / 2) < 1e-5) == 2
                 or (abs(e.verts[0].co.x - e.verts[1].co.x) < 1e-5 and (e.verts[0].co.x < 1e-4 or e.verts[0].co.x > L - 1e-4))]
        try: bmesh.ops.bevel(b, geom=list(set(edges)), offset=min(bevel, w * 0.3, h * 0.3), segments=2, profile=0.5, affect='EDGES')
        except Exception: pass
    if taper:                                                     # hewn timbers: slightly irregular section along the length
        for v in b.verts:
            s = 1 + taper * math.sin(v.co.x * 2.3 + rng.uniform(0, 6)) * 0.5
            v.co.y *= s; v.co.z *= (2 - s)
    off = (rng.uniform(0, 1), rng.uniform(0, 1))
    b.normal_update()
    # move into the world, then UVs (timber: local frame; world: world coordinates) and material per face
    M4 = Matrix.Translation(Vector(p0)) @ R.to_4x4()
    loc_co = {v: v.co.copy() for v in b.verts}
    bmesh.ops.transform(b, matrix=M4, verts=b.verts)
    if wob > 0:
        for v in b.verts:
            c = v.co; d = math.sin(c.x * 7.1 + c.y * 3.3) * math.sin(c.y * 6.7 - c.z * 5.1) * math.sin(c.z * 8.3 + c.x * 2.9)
            nrm = v.normal
            v.co = c + nrm * wob * d
    luv = b.loops.layers.uv.new('UVMap')
    for f in b.faces:
        fn_l = R.inverted() @ f.normal                            # local normal
        fm = mat
        if top and fn_l.z > 0.7: fm = top
        f.material_index = MI[fm]
        a = max(range(3), key=lambda i: abs(f.normal[i]))
        for lp in f.loops:
            lc = loc_co[lp.vert]; wc = lp.vert.co
            if uv == 'timber' or (uv == 'roof' and fm != top):
                if abs(fn_l.x) > 0.7: u, vv = lc.y, lc.z               # end grain
                elif abs(fn_l.y) > 0.7: u, vv = lc.x, lc.z
                else: u, vv = lc.x, lc.y
                lp[luv].uv = (u / 2 + off[0], vv / 2 + off[1])
            elif uv == 'roof':
                lp[luv].uv = (lc.y / 2, -lc.x / 2)                    # shingle rows run along X, V downslope
            else:
                if a == 0: u, vv = wc.y, wc.z
                elif a == 1: u, vv = wc.x, wc.z
                else: u, vv = wc.x, wc.y
                lp[luv].uv = (u / 2 + off[0] * (mat in ('Cobble',)), vv / 2)
    # append into the main bmesh
    vm = {}
    for v in b.verts: vm[v] = BM.verts.new(v.co)
    for f in b.faces:
        try: nf = BM.faces.new([vm[v] for v in f.verts])
        except ValueError: continue
        nf.material_index = f.material_index; nf.smooth = False
        for la, lb in zip(f.loops, nf.loops): lb[UVL].uv = la[luv].uv
    b.free()
    if coll:
        c = Vector(p0) + R @ Vector((L / 2, 0, 0)); COLL.append((c, (L, w, h), R))

def ring(center, normal, R=0.045, r=0.007):
    """iron tie ring + staple."""
    b = bmesh.new(); seg, sides = 16, 6
    verts = []
    N = Vector(normal).normalized(); Up = Vector((0, 0, 1)); T = N.cross(Up).normalized() if abs(N.dot(Up)) < 0.9 else Vector((1, 0, 0))
    B2 = N.cross(T)
    for i in range(seg):
        a = 2 * math.pi * i / seg; cpt = Vector(center) + (T * math.cos(a) + (-Up) * (math.sin(a) + 1)) * R
        tang = (-T * math.sin(a) + (-Up) * math.cos(a)).normalized(); rad = (cpt - (Vector(center) - Up * R)).normalized()
        row = []
        for j in range(sides):
            bj = 2 * math.pi * j / sides; row.append(b.verts.new(cpt + (rad * math.cos(bj) + N * math.sin(bj)) * r))
        verts.append(row)
    for i in range(seg):
        for j in range(sides):
            b.faces.new([verts[i][j], verts[(i + 1) % seg][j], verts[(i + 1) % seg][(j + 1) % sides], verts[i][(j + 1) % sides]])
    luv = b.loops.layers.uv.new('UVMap')
    for f in b.faces:
        f.material_index = MI['Iron']
        for lp in f.loops: lp[luv].uv = (lp.vert.co.x * 2, lp.vert.co.z * 2)
    vm = {v: BM.verts.new(v.co) for v in b.verts}
    for f in b.faces:
        nf = BM.faces.new([vm[v] for v in f.verts]); nf.material_index = f.material_index; nf.smooth = True
        for la, lb in zip(f.loops, nf.loops): lb[UVL].uv = la[luv].uv
    b.free()

def blob(mat, c, r, yaw=0.0, wob=0.35):
    """lumpy ellipsoid (hay forkful): icosphere, scaled, noise-displaced, world UVs."""
    b = bmesh.new(); bmesh.ops.create_icosphere(b, subdivisions=2, radius=1.0)
    ph = rng.uniform(0, 6, 3)
    for v in b.verts:
        d = 1 + wob * (math.sin(v.co.x * 5 + ph[0]) * math.sin(v.co.y * 4 + ph[1]) * math.sin(v.co.z * 6 + ph[2]))
        v.co = Vector((v.co.x * r[0] * d, v.co.y * r[1] * d, v.co.z * r[2] * d))
    bmesh.ops.rotate(b, verts=b.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(yaw, 3, 'Z'))
    bmesh.ops.translate(b, verts=b.verts, vec=Vector(c))
    luv = b.loops.layers.uv.new('UVMap'); b.normal_update()
    for f in b.faces:
        f.material_index = MI[mat]; a = max(range(3), key=lambda i: abs(f.normal[i]))
        for lp in f.loops:
            wc = lp.vert.co; u, vv = ((wc.y, wc.z), (wc.x, wc.z), (wc.x, wc.y))[a]; lp[luv].uv = (u / 2, vv / 2)
    vm = {v: BM.verts.new(v.co) for v in b.verts}
    for f in b.faces:
        nf = BM.faces.new([vm[v] for v in f.verts]); nf.material_index = f.material_index; nf.smooth = True
        for la, lb in zip(f.loops, nf.loops): lb[UVL].uv = la[luv].uv
    b.free()

def stone(c, sx, sy, sz):
    piece('Cobble', (c[0] - sx / 2, c[1], c[2] + sz / 2), (c[0] + sx / 2, c[1], c[2] + sz / 2), sy, sz, bevel=0.03, seg=0.1, uv='world', wob=0.012, jitter=0.02)

# ================================================================ layout numbers
LEN, DEP = 16.0, 7.0
YF, YB = 0.3, 6.7                     # front / back post lines
ZF, ZB = 3.0, 6.4                     # eaves plate heights
POST = 0.25
XS = [0.0, 4.0, 8.0, 12.0, 16.0]
SLOPE = (ZB - ZF) / (YB - YF)          # tan 28 deg
def roof_z(y): return ZF + (y - YF) * SLOPE

# ---- pad-stones and plinth
for x in XS:
    stone((x, YF, 0), 0.55, 0.55, 0.22)
PL_H = 0.40
piece('Cobble', (-0.15, YB + 0.05, PL_H / 2), (LEN + 0.15, YB + 0.05, PL_H / 2), 0.36, PL_H, bevel=0.02, seg=0.25, uv='world', wob=0.015, coll=True)
for x in (0.0, LEN):
    piece('Cobble', (x, YF + 0.3, PL_H / 2), (x, YB - 0.13, PL_H / 2), 0.36, PL_H, bevel=0.02, seg=0.25, uv='world', wob=0.015, coll=True)

# ---- posts
for x in XS:
    piece('Oak', (x, YF, 0.22), (x, YF, ZF - 0.12), POST, POST, up=(0, -1, 0), jitter=0.006, taper=0.04, coll=True)
    piece('Oak', (x, YB, PL_H), (x, YB, ZB - 0.12), POST, POST, up=(0, -1, 0), jitter=0.004, taper=0.04)
# ---- plates, tie beams, braces
piece('Oak', (-0.25, YF, ZF), (LEN + 0.25, YF, ZF), 0.26, 0.24, jitter=0.002, taper=0.05)
piece('Oak', (-0.25, YB, ZB), (LEN + 0.25, YB, ZB), 0.26, 0.24, jitter=0.002, taper=0.05)
for x in XS:
    piece('Oak', (x, YF - 0.15, ZF + 0.02), (x, YB + 0.15, ZF + 0.02), 0.22, 0.26, jitter=0.003, taper=0.06)   # tie beam
    piece('Oak', (x, YB, ZF + 0.15), (x, YF + 1.6, roof_z(YF + 1.6) - 0.12), 0.18, 0.18, jitter=0.004)       # raking strut
for x in XS:                           # knee braces post -> plate
    for s in (-1, 1):
        if 0 <= x + s * 0.9 <= LEN:
            piece('Oak', (x + s * 0.08, YF, ZF - 0.85), (x + s * 0.85, YF, ZF - 0.1), 0.14, 0.12, up=(0, -1, 0), jitter=0.004)
# ---- rafters + roof
YO = YF - 0.8                          # front overhang
RX = np.arange(-0.2, LEN + 0.21, 0.6)
for x in RX:
    piece('Oak', (x, YB + 0.25, roof_z(YB + 0.25) + 0.12), (x, YO, roof_z(YO) + 0.12), 0.11, 0.15, up=(0, 0, 1), jitter=0.003, seg=0.5)
TH = 0.05
p0 = Vector((-0.35, YB + 0.35, roof_z(YB + 0.35) + 0.22)); p1 = Vector((-0.35, YO - 0.08, roof_z(YO - 0.08) + 0.22))
nslope = Vector((0, -SLOPE, 1)).normalized()
# roof slab built along the slope: long axis = downslope, width = along X (made as several strips so rows can sag)
piece('Oak', Vector((LEN / 2, p0.y, p0.z)), Vector((LEN / 2, p1.y, p1.z)), LEN + 0.7, TH, up=nslope, bevel=0.0, seg=0.25, uv='roof', top='Shingle', cutw=0.5)
# barge boards on the verges
for x in (-0.38, LEN + 0.38):
    piece('Oak', (x, YB + 0.35, roof_z(YB + 0.35) + 0.18), (x, YO - 0.1, roof_z(YO - 0.1) + 0.18), 0.04, 0.24, up=(0, 0, 1), jitter=0.002)

# ---- back wall: sill, studs, mid rail, daub panels
WT = 0.14
piece('Oak', (-0.1, YB, PL_H + 0.09), (LEN + 0.1, YB, PL_H + 0.09), 0.2, 0.18)
piece('Oak', (0, YB, 2.6), (LEN, YB, 2.6), 0.16, 0.16, jitter=0.002)
studs = sorted(set(list(np.arange(0, LEN + 0.01, 0.8))))
for x in studs:
    if min(abs(x - p) for p in XS) < 0.3: continue
    piece('Oak', (x, YB, PL_H + 0.18), (x, YB, ZB - 0.12), 0.14, 0.14, up=(0, -1, 0), jitter=0.004)
xs_all = sorted(set(studs + XS))
for xa, xb in zip(xs_all, xs_all[1:]):
    for za, zb in ((PL_H + 0.18, 2.52), (2.68, ZB - 0.12)):
        piece('Daub', (xa + 0.07, YB + 0.01, (za + zb) / 2), (xb - 0.07, YB + 0.01, (za + zb) / 2), WT - 0.02, zb - za, bevel=0.015, seg=0.25, uv='world', wob=0.006)
COLL.append((Vector((LEN / 2, YB, ZB / 2)), (LEN, 0.25, ZB), Matrix.Identity(3)))
# ---- side walls (gable ends follow the roof)
for x in (0.0, LEN):
    piece('Oak', (x, YF + 0.12, PL_H + 0.09), (x, YB - 0.12, PL_H + 0.09), 0.2, 0.18)
    piece('Oak', (x, YF + 0.12, 2.6), (x, YB - 0.12, 2.6), 0.16, 0.16)
    ys = list(np.linspace(YF, YB, 9))
    for y in ys[1:-1]:
        piece('Oak', (x, y, PL_H + 0.18), (x, y, roof_z(y) - 0.1), 0.14, 0.14, up=(1, 0, 0), jitter=0.004)
    # raking top rail under the rafters
    piece('Oak', (x, YF, ZF + 0.12), (x, YB, ZB + 0.0), 0.16, 0.16)
    for ya, yb in zip(ys, ys[1:]):
        ya2, yb2 = ya + (0.2 if ya == YF else 0.07), yb - (0.2 if yb == YB else 0.07)
        for za, zb in ((PL_H + 0.18, 2.52), (2.68, roof_z(ya2) - 0.05)):
            if zb - za < 0.1: continue
            piece('Daub', (x, ya2, (za + zb) / 2), (x, yb2, (za + zb) / 2), WT - 0.02, zb - za, up=(0, 0, 1), bevel=0.015, seg=0.25, uv='world', wob=0.006)
        # triangle above the rail is closed by a tapered panel: stack thin daub strips up to the slope
        z0 = 2.68; z1a = roof_z(ya2) - 0.05; z1b = roof_z(yb2) - 0.05
        if z1b - z1a > 0.08:
            nst = 4
            for k in range(nst):
                y_a = ya2 + (yb2 - ya2) * k / nst; y_b = ya2 + (yb2 - ya2) * (k + 1) / nst; zt = roof_z(y_a) - 0.05; zlo = roof_z(ya2) - 0.05
                if zt - zlo > 0.02:
                    piece('Daub', (x, y_a, (zlo + zt) / 2), (x, y_b, (zlo + zt) / 2), WT - 0.02, zt - zlo, up=(0, 0, 1), bevel=0.0, seg=0.25, uv='world', wob=0.0)
    COLL.append((Vector((x, (YF + YB) / 2, ZB / 2)), (0.25, YB - YF, ZB), Matrix.Identity(3)))

# ---- floor: cobbled walk + gully, straw in the stalls
YS0 = 3.6                              # stall heel line (horses face the back wall, rumps toward the walk)
piece('Cobble', (0.12, (YF + 3.25) / 2 - 0.15, -0.02), (LEN - 0.12, (YF + 3.25) / 2 - 0.15, -0.02), 3.25 - YF + 0.6, 0.06, bevel=0.0, seg=0.25, uv='world', wob=0.0)
piece('Cobble', (0.12, 3.40, -0.06), (LEN - 0.12, 3.40, -0.06), 0.28, 0.06, bevel=0.0, seg=0.25, uv='world')   # gully, 4 cm deep
for x0, x1 in ((0.12, 9.6), (9.6, LEN - 0.12)):
    piece('Straw', (x0, (YS0 - 0.1 + YB) / 2, -0.005), (x1, (YS0 - 0.1 + YB) / 2, -0.005), YB - YS0 + 0.1, 0.07, bevel=0.0, seg=0.2, uv='world', wob=0.018)

# ---- standing stalls: heel posts + kicking boards + top rail, 1.6 m wide
STALL_X = [0.0 + 1.6 * k for k in range(7)]                       # 0 .. 9.6
for i, x in enumerate(STALL_X):
    if x in (0.0,): continue                                       # the side wall closes the first stall
    piece('Oak', (x, YS0, 0.0), (x, YS0, 1.75), 0.15, 0.15, up=(0, -1, 0), jitter=0.006, taper=0.05, coll=False)
    for k in range(5):                                            # 5 planks, 27 cm, little gaps
        z = 0.06 + 0.275 * k + 0.135
        piece('Oak', (x, YS0 + 0.08, z), (x, YB - 0.1, z), 0.055, 0.265, up=(0, 0, 1), jitter=0.002, bevel=0.008)
    piece('Oak', (x, YS0 + 0.05, 1.48), (x, YB - 0.1, 1.55 + 0.2), 0.11, 0.09, up=(0, 0, 1), jitter=0.002)   # top rail rises to the manger
    COLL.append((Vector((x, (YS0 + YB) / 2, 0.8)), (0.12, YB - YS0, 1.6), Matrix.Identity(3)))
# ---- loose boxes: partitions + front walls with half doors
BX = [9.6, 12.8, LEN]
YBF = 3.5
for x in BX[:-1]:
    if x != 9.6:
        pass
for x in BX:
    if x == LEN: continue
    if x != 9.6:
        piece('Oak', (x, YBF, 0.0), (x, YBF, 1.9), 0.16, 0.16, up=(0, -1, 0), jitter=0.005)
    for k in range(6):
        z = 0.06 + 0.275 * k + 0.135
        piece('Oak', (x + 0.0, YBF + 0.08, z), (x, YB - 0.1, z), 0.055, 0.265, up=(0, 0, 1), jitter=0.002, bevel=0.008)
for xa, xb in ((9.6, 12.8), (12.8, LEN)):
    door0, door1 = xa + 1.0, xa + 2.2
    piece('Oak', (door0, YBF, 0.0), (door0, YBF, 1.9), 0.15, 0.15, up=(0, -1, 0), jitter=0.004)
    piece('Oak', (door1, YBF, 0.0), (door1, YBF, 1.9), 0.15, 0.15, up=(0, -1, 0), jitter=0.004)
    for x0, x1 in ((xa + 0.08, door0 - 0.08), (door1 + 0.08, xb - 0.08)):
        for k in range(6):
            z = 0.06 + 0.275 * k + 0.135
            piece('Oak', (x0, YBF, z), (x1, YBF, z), 0.055, 0.265, up=(0, 0, 1), jitter=0.002, bevel=0.008)
    # half door (lower leaf, 1.3 m), hung open 25 deg on the left post
    hinge = Vector((door0 + 0.08, YBF - 0.04, 0.0)); ang = math.radians(-25)
    dirv = Vector((math.cos(ang), math.sin(ang), 0))
    for k in range(4):
        z = 0.12 + 0.3 * k + 0.14
        a = hinge + Vector((0, 0, z)); bpt = a + dirv * 1.04
        piece('Oak', a, bpt, 0.05, 0.29, up=(0, 0, 1), jitter=0.002, bevel=0.008)
    for zz in (0.35, 1.05):                                        # iron strap hinges
        a = hinge + Vector((0, 0, zz)) - Vector((math.sin(ang), -math.cos(ang), 0)) * 0.03
        piece('Iron', a, a + dirv * 0.55, 0.008, 0.05, up=(0, 0, 1), bevel=0.002, seg=0.2)
    piece('Oak', hinge + Vector((0, 0, 1.25)) + dirv * 0.02, hinge + Vector((0, 0, 1.25)) + dirv * 1.04, 0.07, 0.06, up=(0, 0, 1))
    COLL.append((Vector(((xa + door0) / 2, YBF, 0.95)), (door0 - xa, 0.12, 1.9), Matrix.Identity(3)))
    COLL.append((Vector(((door1 + xb) / 2, YBF, 0.95)), (xb - door1, 0.12, 1.9), Matrix.Identity(3)))

# ---- manger along the back wall + hay rack
MY0, MY1 = YB - 0.62, YB - 0.1
for z, h in ((0.95, 0.06),):
    piece('Oak', (0.1, MY0, 1.0), (LEN - 0.1, MY0, 1.0), 0.07, 0.40, up=(0, 0, 1), jitter=0.001, seg=0.4)   # front board
    piece('Oak', (0.1, (MY0 + MY1) / 2, 0.80), (LEN - 0.1, (MY0 + MY1) / 2, 0.80), MY1 - MY0, 0.06, seg=0.4)  # bottom
    piece('Oak', (0.1, MY0, 1.22), (LEN - 0.1, MY0, 1.22), 0.12, 0.07, seg=0.4)                            # chewed top rail
for x in np.arange(0.4, LEN, 1.6):
    piece('Oak', (x, MY0 + 0.02, 0.0), (x, MY0 + 0.02, 0.8), 0.12, 0.12, up=(0, -1, 0), jitter=0.006)
for i in range(6):                                                 # tie rings, one per standing stall
    ring((0.8 + 1.6 * i, MY0 - 0.04, 1.12), (0, -1, 0))
for x in (11.2, 14.4):
    ring((x, MY0 - 0.04, 1.12), (0, -1, 0))
# hay rack: rail on the wall at 1.4 m, outer rail 0.55 m out at 2.25 m, round staves every 12 cm
piece('Oak', (0.1, YB - 0.1, 1.42), (LEN - 0.1, YB - 0.1, 1.42), 0.1, 0.1, seg=0.4)
piece('Oak', (0.1, YB - 0.62, 2.25), (LEN - 0.1, YB - 0.62, 2.25), 0.1, 0.1, seg=0.4)
for x in np.arange(0.2, LEN - 0.1, 0.13):
    piece('Oak', (x, YB - 0.12, 1.45), (x, YB - 0.6, 2.24), 0.032, 0.032, up=(0, 0, 1), bevel=0.008, seg=0.3, jitter=0.01)
for x in np.arange(0.4, LEN, 1.6):                                 # brackets
    piece('Oak', (x, YB - 0.08, 1.2), (x, YB - 0.62, 2.2), 0.08, 0.08, up=(0, 0, 1))
# hay in the rack (lumps of straw)
for k in range(70):                                               # loose forkfuls, not loaves: small, tilted, overlapping
    x = rng.uniform(0.5, LEN - 0.5); L = rng.uniform(0.25, 0.55); t = rng.uniform(0, 1)
    yy = YB - 0.15 - 0.4 * t; zz = 1.5 + 0.75 * t + rng.uniform(-0.04, 0.06)
    d = Vector((math.cos(rng.uniform(-0.6, 0.6)), 0, math.sin(rng.uniform(-0.4, 0.4)))) * L / 2
    blob('Straw', (x, yy, zz), (L / 2, rng.uniform(0.09, 0.16), rng.uniform(0.07, 0.13)), rng.uniform(-0.6, 0.6))

# ---- tack pegs on the side wall by the boxes, a few spare oak planks leaning
for k in range(5):
    y = 1.0 + 0.5 * k
    piece('Oak', (LEN - 0.07, y, 1.55), (LEN - 0.42, y, 1.6), 0.05, 0.05, up=(0, 0, 1), bevel=0.01)

BM.normal_update()
me = bpy.data.meshes.new('SM_Stable'); BM.to_mesh(me); BM.free()
ob = bpy.data.objects.new('SM_Stable', me); bpy.context.scene.collection.objects.link(ob)
for m in MATS:
    mat = bpy.data.materials.get('M_Stable' + m) or bpy.data.materials.new('M_Stable' + m); me.materials.append(mat)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0005)
bpy.ops.object.mode_set(mode='OBJECT')
# shading: smooth by angle (keeps bevels soft, corners crisp)
for p in me.polygons: p.use_smooth = True
try:
    bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
except Exception:
    try: me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(35)
    except Exception: pass
ntris = sum(len(p.vertices) - 2 for p in me.polygons)
print('STABLE tris', ntris, 'verts', len(me.vertices), flush=True)

# ---- vertex colour 'Wear': R = AO (Cycles bake), G = wet muck, B = sun bleach
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('AO_SAMPLES', '48'))
ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
try: me.attributes.active_color = ca
except Exception: pass
sc.render.bake.target = 'VERTEX_COLORS'
if sc.world is None: sc.world = bpy.data.worlds.new('W')
sc.world.light_settings.distance = 1.2                          # AO reach: 1.2 m (corner and contact darkening, not room darkness)
bpy.ops.object.bake(type='AO')
nl = len(me.loops)
ao = np.empty(nl * 4, np.float32); ca.data.foreach_get('color', ao); ao = ao.reshape(-1, 4)[:, 0]
lv = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)[lv]
me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
ln = np.empty(nl * 3, np.float32)
try: me.corner_normals.foreach_get('vector', ln)
except Exception: me.loops.foreach_get('normal', ln)
ln = ln.reshape(-1, 3)
x, y, z = co[:, 0], co[:, 1], co[:, 2]
def vn(p, f, seed):
    q = p * f; i = np.floor(q).astype(np.int64); t = q - i; t = t * t * (3 - 2 * t)
    def h(dx, dy, dz):
        n = ((i[:, 0] + dx) * 73856093) ^ ((i[:, 1] + dy) * 19349663) ^ ((i[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float32) / 65535.0
    x0 = h(0, 0, 0) + (h(1, 0, 0) - h(0, 0, 0)) * t[:, 0]; x1 = h(0, 1, 0) + (h(1, 1, 0) - h(0, 1, 0)) * t[:, 0]
    x2 = h(0, 0, 1) + (h(1, 0, 1) - h(0, 0, 1)) * t[:, 0]; x3 = h(0, 1, 1) + (h(1, 1, 1) - h(0, 1, 1)) * t[:, 0]
    y0 = x0 + (x1 - x0) * t[:, 1]; y1 = x2 + (x3 - x2) * t[:, 1]; return y0 + (y1 - y0) * t[:, 2]
def ssn(e0, e1, v): t = np.clip((v - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
n1 = vn(co, 3.0, 1); n2 = vn(co, 11.0, 2)
inside_stall = (y > YS0 - 0.3) & (y < YB) & (x > 0.1) & (x < LEN - 0.1)
splash_h = 0.28 + 0.18 * n1 + 0.25 * inside_stall                  # muck splashes higher inside the stalls (hooves)
G = ssn(splash_h, splash_h - 0.22, z) * (0.55 + 0.45 * n2)
urine = np.exp(-((y - (YS0 + 0.45)) / 0.55) ** 2) * (x < 9.6) * ssn(0.1, 0.0, z) * (0.6 + 0.4 * n2)   # behind each standing horse
gully = np.exp(-((y - 3.40) / 0.25) ** 2) * ssn(0.05, -0.05, z)
floor = ssn(0.6, 0.85, ln[:, 2])                                  # up-facing floor: muck only in patches, not a full coat
G = G * (1 - floor) + floor * G * 0.35 * ssn(0.55, 0.75, n1)
G = np.clip(np.maximum(G, np.maximum(urine, 0.8 * gully)), 0, 1)
up = np.clip(ln[:, 2], 0, 1); out = np.clip(-ln[:, 1], 0, 1)
front = ssn(2.5, 0.0, y)                                          # the open front gets the sun and rain
B = np.clip((0.55 * up + 0.45 * out) * front * ssn(0.55, 0.9, ao) * (0.6 + 0.4 * n1), 0, 1)
B = np.maximum(B, 0.8 * ssn(0.0, 0.1, z - roof_z(np.clip(y, YO, YB)) - 0.15) * up)   # the roof top: fully weathered
wear = np.stack([ao, G, B, np.ones_like(ao)], 1).astype(np.float32)
cw = me.color_attributes.new('Wear', 'BYTE_COLOR', 'CORNER'); cw.data.foreach_set('color', wear.ravel())
me.color_attributes.remove(me.color_attributes['AO'])
me.color_attributes.active_color = me.color_attributes['Wear']
try: me.color_attributes.render_color_index = me.color_attributes.active_color_index
except Exception: pass
print('WEAR ao mean %.2f muck mean %.2f sun mean %.2f' % (ao.mean(), G.mean(), B.mean()), flush=True)

# ---- collision boxes (UCX_)
for k, (c, s, R) in enumerate(COLL):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=c); cb = bpy.context.active_object
    cb.name = 'UCX_SM_Stable_%02d' % k; cb.scale = s; cb.rotation_euler = R.to_euler()
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'stable.blend'))
for o in bpy.context.scene.objects: o.select_set(o.name == 'SM_Stable' or o.name.startswith('UCX_'))
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_Stable.fbx'), use_selection=True, object_types={'MESH'},
                         mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL', colors_type='LINEAR')
print('STABLE OK', os.path.join(OUT, 'SM_Stable.fbx'), 'collision boxes', len(COLL), flush=True)
