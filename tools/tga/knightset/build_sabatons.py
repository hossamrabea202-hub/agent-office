# Yellow Eagle Knight set (#367, TGA): articulated sabatons after Codex sheet 12 (c. 1300-1340 transitional).
#   blender -b --factory-startup -P build_sabatons.py      (env WORK) -> WORK/sabatons.blend
# Built in cm in a canonical LEFT-foot frame (bottom of the sole under the ankle at the origin, up +Z, toe toward -Y,
# outer side toward +X), then scaled to metres; the fit script moves it onto foot_l / foot_r (#368 ref pose).
# Sheet numbers: 28 cm long (11 toe / 17 mid + heel), ball 10.5 cm, heel 7 cm, ankle 8.5 cm high, toe angle ~22 deg,
# 6-8 plates, 0.8-1.2 mm, leather sole 4-6 mm, strap 2.5-3 cm, buckle ~3 cm. Parts: Steel (pointed toe plate, 5 lames,
# vamp, ankle cuff, heel plate), Brass (pivot rivets, rim rivets, buckle), Leather (sole, ankle strap, lining at the cuff).
import bpy, numpy as np, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build_gauntlets.py'), encoding='utf-8').read()
exec(src[src.index('D = os.environ'):src.index('steel, brass, leather = Mesh()')])
steel, brass, leather = Mesh(), Mesh(), Mesh()

Y_TOE, Y_HEEL, SOLE = -19.0, 9.0, 0.5
def foot(y):
    """half-width of the sole and height of the instep over the sole at y (toe -19 .. heel +9)"""
    k = [(-19.0, 0.25, 0.35), (-16.0, 2.4, 1.6), (-12.0, 4.4, 3.0), (-8.0, 5.25, 4.4), (-4.0, 4.9, 5.6), (-1.0, 4.3, 6.3),
         (2.0, 4.0, 6.3), (6.0, 3.7, 5.8), (9.0, 2.6, 4.5)]
    y = min(max(y, k[0][0]), k[-1][0])                                      # clamp (the toe plate starts a hair before -19)
    for (y0, w0, h0), (y1, w1, h1) in zip(k, k[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0); t = t * t * (3 - 2 * t); return w0 + (w1 - w0) * t, h0 + (h1 - h0) * t
    return k[-1][1:]
def arch(y, v, grow=1.0, lift=0.0, tilt=0.0):
    """point on the foot cover: v = 0 on top of the instep, +-pi/2 down to the sole edges (outer side +X)"""
    y = y + tilt * (1 - math.cos(v))                                       # lame edges lean back toward the heel down the sides (sheet)
    w, h = foot(y); w *= grow; h = h * grow + lift
    return V3(w * math.sin(v), y, SOLE + h * max(0.0, math.cos(v)) ** 0.85 + 0.05)
# sole: leather slab with the sheet's outline (pointed toe, ball 10.5, heel 7)
ys = [Y_TOE + (Y_HEEL - Y_TOE) * i / 40 for i in range(41)]
outline = [V3(foot(y)[0] * 1.03, y, 0) for y in ys] + [V3(-foot(y)[0] * 1.03, y, 0) for y in reversed(ys)]
n = len(outline); verts = [p for p in outline] + [p + V3(0, 0, SOLE) for p in outline]
faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
faces += [[i, i + 1, n - 2 - i, n - 1 - i][::-1] for i in range(n // 2 - 1)] + [[n + i, n + i + 1, n + n - 2 - i, n + n - 1 - i] for i in range(n // 2 - 1)]
leather.add(verts, faces)
# toe plate + 5 lames + vamp: arched shells along the foot, each a little bigger than the one before so they shingle
SPAN = math.radians(96)
LAMES = [(-19.0, -14.6), (-15.0, -12.5), (-12.9, -10.4), (-10.8, -8.3), (-8.7, -6.2), (-6.6, -4.1), (-4.5, -0.6)]   # toe, 5 lames, vamp
for k, (y0, y1) in enumerate(LAMES):
    nl, na = (10, 18) if k in (0, 6) else (4, 18)
    vs = []
    for i in range(nl):
        t = i / (nl - 1); y = y0 + (y1 - y0) * t
        g = 1.0 + 0.012 * k + 0.035 * t                                   # back edge stands proud of the next lame's front
        for j in range(na):
            vs.append(arch(y, -SPAN + 2 * SPAN * j / (na - 1), g, 0.12 + 0.05 * k, 0.0 if k == 0 else 1.6))
    steel.add(vs, grid(nl, na))
    if 0 < k < 6:                                                          # pivot rivets low on both sides
        for sgn in (-1, 1):
            p = arch((y0 + y1) / 2, sgn * math.radians(70), 1.0 + 0.012 * k + 0.02, 0.2 + 0.05 * k, 1.6)
            rivet(brass, p, V3(sgn, 0, 0.5), r=0.2, sides=8)
    tr = arch((y0 + y1) / 2, 0.0, 1.0 + 0.012 * k + 0.02, 0.2 + 0.05 * k)  # a small rivet on the top line of each plate
    rivet(brass, tr, V3(0, -0.2, 1), r=0.15, sides=6)
# side plates from the vamp back to the heel (low on both sides, under the cuff), then a heel cup round the back
for sgn in (-1, 1):
    vs = []
    for i in range(8):
        y = -1.2 + 8.2 * i / 7
        for j in range(8):
            v = sgn * (math.radians(48) + (SPAN - math.radians(48)) * j / 7)
            vs.append(arch(y, v, 1.1, 0.35))
    steel.add(vs if sgn > 0 else vs, grid(8, 8))
    for y in (1.5, 5.0): rivet(brass, arch(y, sgn * math.radians(75), 1.12, 0.4), V3(sgn, 0, 0.3), r=0.18, sides=8)
# ankle cuff: elliptical collar over the instep and round the sides, open at the back; heel plate behind
def cuff_pt(z, th, rx=4.6, ry=4.3):
    return V3(rx * math.sin(th), 2.0 - ry * math.cos(th), z)
CZ = [5.0 + 6.5 * i / 7 for i in range(8)]; CT = [math.radians(-125 + 250 * j / 23) for j in range(24)]
steel.add([cuff_pt(z, th, 4.6 + 0.08 * (z - 5), 4.3 + 0.06 * (z - 5)) for z in CZ for th in CT], grid(len(CZ), len(CT)))
tube(brass, [cuff_pt(11.5, th, 5.12, 4.69) + V3(0, 0, 0.0) for th in CT], [0.2] * len(CT), 6, cap1=False, ref=V3(0, 0, 1))    # rolled top rim
for th in CT[2::4]: rivet(brass, cuff_pt(10.6, th, 5.08, 4.66), V3(math.sin(th), -math.cos(th), 0), r=0.17, sides=6)
HZ = [SOLE + 0.1 + 5.6 * i / 7 for i in range(8)]; HT = [math.radians(100 + 160 * j / 15) for j in range(16)]
steel.add([V3(4.05 * math.sin(th) * (1 - 0.04 * (z - SOLE)), 5.4 - 3.7 * math.cos(th), z) for z in HZ for th in HT], grid(len(HZ), len(HT)))
# leather: ankle strap with a brass buckle on the outer side, lining showing at the cuff's back opening
SZ = (6.0, 8.6); ST = [math.radians(-180 + 360 * j / 31) for j in range(32)]
leather.add([cuff_pt(z, th, 4.95, 4.62) for z in SZ for th in ST], grid(2, 32, wrap=True))
bt = math.radians(100); p = cuff_pt(7.3, bt, 5.2, 4.85); nn = nz(V3(math.sin(bt), -math.cos(bt), 0)); up = V3(0, 0, 1); side = np.cross(up, nn)
for (u0, v0), (u1, v1) in (((-1.5, -1.5), (1.5, -1.5)), ((1.5, -1.5), (1.5, 1.5)), ((1.5, 1.5), (-1.5, 1.5)), ((-1.5, 1.5), (-1.5, -1.5))):
    tube(brass, [p + side * u0 + up * v0, p + side * u1 + up * v1], [0.17, 0.17], 6, cap1=False, ref=nn)
tube(brass, [p - up * 1.2 + nn * 0.1, p + up * 1.25 + nn * 0.1], [0.1, 0.1], 6, cap1=False, ref=nn)
LZ = [SOLE + 0.2 + 10.6 * i / 6 for i in range(7)]; LT = [math.radians(120 + 120 * j / 9) for j in range(10)]
leather.add([cuff_pt(z, th, 4.3, 4.0) for z in LZ for th in LT], grid(len(LZ), len(LT)))

exec(src[src.index('def make(name, m, thick, bevel):'):src.index("bpy.context.view_layer.objects.active = oS; bpy.ops.object.join()")])
bpy.context.view_layer.objects.active = oS; bpy.ops.object.join(); g = bpy.context.active_object; g.name = 'SM_EagleSabatons_L'
g.data.name = 'SM_EagleSabatons_L'
for p in g.data.polygons: p.use_smooth = True
print('TRIS', sum(len(p.vertices) - 2 for p in g.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'sabatons.blend')); print('SABATONS OK', flush=True)
