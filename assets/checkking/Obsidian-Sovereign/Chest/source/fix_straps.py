# #64 strap fix without touching UVs (the fitted SK chest keeps the shipped layout):
# LP strap faces with collapsed (zero-area) UVs sample single texels, which hold whatever the bake left there (grey/white).
# Paint plain leather into exactly those texels, but only where no real (non-degenerate) UV face covers them.
#   blender -b bake_ready.blend -P fix_straps.py [-- dry]
import os, sys, bpy, numpy as np
from mathutils.bvhtree import BVHTree
D = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(D, 'tex'); N = 4096
DRY = 'dry' in sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else False
dg = bpy.context.evaluated_depsgraph_get()
LP = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'HP'][0]; HP = bpy.data.objects['HP']
bvh = BVHTree.FromObject(HP, dg); hpm = [s.material.name.split('.')[0] for s in HP.material_slots]
uv = LP.data.uv_layers.active.data; inv = HP.matrix_world.inverted()

def tri_area(p):
    a = 0
    for i in range(1, len(p) - 1): a += abs((p[i][0] - p[0][0]) * (p[i+1][1] - p[0][1]) - (p[i+1][0] - p[0][0]) * (p[i][1] - p[0][1])) / 2
    return a
cover = np.zeros((N, N), bool); target = np.zeros((N, N), bool)
yy, xx = None, None
for f in LP.data.polygons:
    p = [tuple(uv[i].uv * N) for i in f.loop_indices]
    if tri_area(p) > 0.25:   # real face (> 1/4 texel): mark its texels as covered
        P = np.array(p); x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        inside = np.zeros(gx.shape, bool)
        for i in range(1, len(P) - 1):   # fan triangles, sign test with a small tolerance
            a, b, c = P[0], P[i], P[i + 1]
            d = lambda u, v: (gx - v[0]) * (u[1] - v[1]) - (u[0] - v[0]) * (gy - v[1])
            s1, s2, s3 = d(a, b), d(b, c), d(c, a)
            inside |= ~(((s1 < -1e-3) | (s2 < -1e-3) | (s3 < -1e-3)) & ((s1 > 1e-3) | (s2 > 1e-3) | (s3 > 1e-3)))
        cover[y0:y1 + 1, x0:x1 + 1] |= inside
        continue
    m = hpm[HP.data.polygons[bvh.find_nearest(inv @ (LP.matrix_world @ f.center))[2]].material_index]
    if m != 'Leather': continue
    P = np.array(p)   # collapsed face: mark the texels along its points/line (bilinear: 2x2 around each sample)
    for t in np.linspace(0, 1, 9):
        for i in range(len(P)):
            q = P[i] * (1 - t) + P[(i + 1) % len(P)] * t
            x, y = int(q[0] - 0.5), int(q[1] - 0.5)
            target[max(y, 0):min(y + 2, N), max(x, 0):min(x + 2, N)] = True
paint = target   # incl. texels shared with real faces: those are ~77% side-strap leather already; flat normal is what fixes the broken tangents
print('FIX target', int(target.sum()), 'overlap-with-real', int((target & cover).sum()), 'paint', int(paint.sum()))
if not DRY:
    def srgb(l): return 1.055 * l ** (1 / 2.4) - 0.055 if l > 0.0031308 else 12.92 * l
    vals = {'T_ObsidianSovereign_Chest_BaseColor': [srgb(v) for v in (0.034, 0.017, 0.008)],
            'T_ObsidianSovereign_Chest_ORM': [1.0, 0.6, 0.0],
            'T_ObsidianSovereign_Chest_Normal_DirectX': [0.5, 0.5, 1.0],
            'T_ObsidianSovereign_Chest_Normal_OpenGL': [0.5, 0.5, 1.0]}
    for name, v in vals.items():
        im = bpy.data.images.load(os.path.join(TEX, name + '.png')); im.colorspace_settings.name = 'Non-Color'
        a = np.empty(N * N * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(N, N, 4)   # rows bottom-up = UV v
        a[paint, :3] = v
        im.pixels.foreach_set(a.ravel()); im.filepath_raw = os.path.join(TEX, name + '.png'); im.save()
        print('FIX wrote', name)
if DRY:
    im = bpy.data.images.load(os.path.join(TEX, 'T_ObsidianSovereign_Chest_BaseColor.png')); im.colorspace_settings.name = 'Non-Color'
    a = np.empty(N * N * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(N, N, 4)[..., :3]
    for nm, msk in (('overlap', target & cover), ('paint', paint)):
        v = a[msk]; lum = v.mean(1); brown = (v[:, 0] > v[:, 2] * 1.4) & (lum < 0.35)
        print('FIX', nm, 'mean sRGB', v.mean(0).round(3), 'brown-ish %', round(100 * brown.mean(), 1), 'bright(>0.4) %', round(100 * (lum > 0.4).mean(), 1))
