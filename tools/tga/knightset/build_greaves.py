# Yellow Eagle Knight set (#367, TGA): greaves (lower-leg plate) after Codex sheet 11 (c. 1300-1340 transitional).
#   blender -b --factory-startup -P build_greaves.py      (env WORK) -> WORK/greaves.blend
# Built in cm in a canonical LEFT-leg frame (bottom of the ankle flare at the origin, up +Z, shin toward -Y, outer side
# toward +X), then scaled to metres; the fit script moves it onto calf_l / calf_r from the knight ref pose (#368).
# Sheet numbers: 37 cm tall, calf 17 cm (upper) / 14 cm (mid), ankle 10.5 cm, top opening 16.5 cm, bottom 10 cm, plate
# 1.0-1.5 mm, R ~7-8.5 cm, straps 2.5-3 cm, buckle 4 x 3.2 cm. Parts: Steel (front plate wrapping round to an open back,
# centre ridge, knee chevron, flared top and ankle), Brass (rolled rims, domed rivets, buckles), Leather (padded liner
# showing in the open back, 3 straps). Mesh helpers are build_gauntlets.py's (same kit).
import bpy, numpy as np, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build_gauntlets.py'), encoding='utf-8').read()
exec(src[src.index('D = os.environ'):src.index('steel, brass, leather = Mesh()')])     # D, V3, nz, rot, Mesh, grid, frame, tube, rivet, ...
steel, brass, leather = Mesh(), Mesh(), Mesh()

PROF = [(0.0, 5.6, 5.0), (1.5, 5.25, 4.75), (4.0, 5.1, 4.6), (8.0, 5.3, 4.9), (14.0, 6.3, 5.6), (20.0, 7.0, 6.0),
        (26.0, 7.6, 6.4), (31.0, 8.3, 6.6), (35.0, 8.5, 6.7), (37.0, 8.9, 6.9)]          # z, half-width (X), half-depth (Y)
def ab(z):
    for (z0, a0, b0), (z1, a1, b1) in zip(PROF, PROF[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0); t = t * t * (3 - 2 * t); return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t
    return PROF[-1][1:]
OPEN = math.radians(140)                       # plate spans -150..150 deg from the shin; the back 60 deg is open (liner + straps)
def surf(z, th, lift=0.0):
    """point on the plate: th = 0 at the shin (-Y), + toward the outer side (+X); calf bulge at the back"""
    a, b = ab(z)
    calf = 1.0 + 0.14 * max(0.0, -math.cos(th)) * math.exp(-((z - 22) / 7.5) ** 2)
    ridge = 0.7 * math.exp(-(th / 0.13) ** 2) * min(1.0, max(0.0, (z - 3.0) / 3.0))                     # centre ridge down the shin
    chev = 0.0
    if abs(th) < 1.25:
        zc = 31.2 - 3.4 * abs(th)                                                                        # knee chevron, V pointing down
        chev = 0.55 * math.exp(-((z - zc) / 0.55) ** 2)
    r_out = ridge + chev + lift
    a *= 0.84                                                                                            # v1b: slimmer, as the sheet's views
    p = V3(a * math.sin(th) * calf, -b * math.cos(th) * calf, z)
    n = nz(V3(math.sin(th) / a, -math.cos(th) / b, 0))
    return p + n * r_out, n
NZ, NT = 46, 64
def ztop(th): return 37.0 - 3.2 * (abs(th) / OPEN) ** 1.6                                   # top cut slopes down from the knee (sheet)
def zbot(th): return 2.4 * math.exp(-(th / 0.55) ** 2)                                      # arched ankle cut-out at the front
ths = [-OPEN + 2 * OPEN * j / (NT - 1) for j in range(NT)]
zs = [37.0 * (i / (NZ - 1)) for i in range(NZ)]
def zat(u, th): return zbot(th) + (ztop(th) - zbot(th)) * u
steel.add([surf(zat(i / (NZ - 1), th), th)[0] for i in range(NZ) for th in ths], grid(NZ, NT))

def bead_along(pts, rr, sides=6):
    tube(brass, pts, [rr] * len(pts), sides, cap1=False, ref=V3(0, 0, 1))
bead_along([surf(ztop(th), th, 0.05)[0] for th in ths], 0.24)                                 # rolled rims (brass-bound, as the sheet)
bead_along([surf(zbot(th), th, 0.05)[0] for th in ths], 0.22)
for sgn in (-1, 1):
    bead_along([surf(zat(i / (NZ - 1), sgn * OPEN), sgn * OPEN, 0.05)[0] for i in range(NZ)], 0.2)                           # back edges
# rivets: under the top rim, over the ankle rim, down both back edges, the side seams, the chevron apex
def riv(z, th, r=0.2):
    p, n = surf(z, th, 0.12); rivet(brass, p, n, r=r, sides=8)
for k in range(13): th_ = -OPEN + 0.12 + (2 * OPEN - 0.24) * k / 12; riv(ztop(th_) - 1.2, th_)
for k in range(9): th_ = -OPEN + 0.12 + (2 * OPEN - 0.24) * k / 8; riv(zbot(th_) + 1.4, th_, 0.17)
for sgn in (-1, 1):
    for z in (5, 11, 17, 23, 29, 32): riv(z, sgn * (OPEN - 0.13), 0.17)
    for z in (9, 17, 25): riv(z, sgn * math.radians(95), 0.16)
riv(27.6, 0.0, 0.26)

# leather: padded liner seen through the open back, 3 straps round the back, brass buckles on the outer-back side
def liner_pt(z, th, k=0.97):
    a, b = ab(z); a *= 0.84; calf = 1.0 + 0.14 * max(0.0, -math.cos(th)) * math.exp(-((z - 22) / 7.5) ** 2)
    return V3(a * math.sin(th) * calf * k, -b * math.cos(th) * calf * k, z)
lz = [2.0 + 31.0 * i / 20 for i in range(21)]; lt = [OPEN - 0.25 + (2 * math.pi - 2 * OPEN + 0.5) * j / 15 for j in range(16)]
leather.add([liner_pt(z, th) for z in lz for th in lt], grid(len(lz), len(lt)))
for zc in (7.5, 19.0, 30.0):
    st = [OPEN - 0.2 + (2 * math.pi - 2 * OPEN + 0.4) * j / 15 for j in range(16)]
    leather.add([surf(z, th, 0.18)[0] if abs(math.atan2(math.sin(th), math.cos(th))) <= OPEN else liner_pt(z, th, 1.035) for z in (zc - 1.4, zc + 1.4) for th in st], grid(2, 16))
    bt = OPEN + 0.12; p, n = surf(zc, bt, 0.0); p = liner_pt(zc, bt, 1.06); n = nz(V3(math.sin(bt), -math.cos(bt), 0)); up = V3(0, 0, 1); side = np.cross(up, n)
    for (u0, v0), (u1, v1) in (((-1.9, -1.6), (1.9, -1.6)), ((1.9, -1.6), (1.9, 1.6)), ((1.9, 1.6), (-1.9, 1.6)), ((-1.9, 1.6), (-1.9, -1.6))):
        tube(brass, [p + side * u0 * 0.5 + up * v0 * 0.5 + n * 0.12, p + side * u1 * 0.5 + up * v1 * 0.5 + n * 0.12], [0.16, 0.16], 6, cap1=False, ref=n)
    tube(brass, [p + up * -0.8 + n * 0.2, p + up * 0.9 + n * 0.2], [0.1, 0.1], 6, cap1=False, ref=n)     # tongue

# ---------------- objects (build_gauntlets.py's make(): solidify + bevel, cm -> m) ----------------
exec(src[src.index('def make(name, m, thick, bevel):'):src.index("bpy.context.view_layer.objects.active = oS; bpy.ops.object.join()")])
bpy.context.view_layer.objects.active = oS; bpy.ops.object.join(); g = bpy.context.active_object; g.name = 'SM_EagleGreaves_L'
g.data.name = 'SM_EagleGreaves_L'
for p in g.data.polygons: p.use_smooth = True
print('TRIS', sum(len(p.vertices) - 2 for p in g.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'greaves.blend')); print('GREAVES OK', flush=True)
