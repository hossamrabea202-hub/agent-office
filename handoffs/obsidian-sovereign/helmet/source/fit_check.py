# Measured clearance of the helm against the real head + gorget vertex clouds (#485).
#   blender -b <helm_build_r1.blend | helm_final.blend> -P fit_check.py -- <cloud_dir with head.txt gneck.txt gspine.txt> [out.json]
# The clouds were read from SM_HeroHead / SM_Gorget_* by probes/nomu_helm_probe3_ue.py and are NOT kept in the repo.
# Reported per cloud: points outside the shell, smallest distance from a point to the nearest helm surface (cm), and where.
# Frames: UE knight space -> Blender (x, -y, z) / 100. Head transform derived from HeroHead's relative transform on the head bone.
import sys, json, bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
D = a[0]; OUT = a[1] if len(a) > 1 else None
S = 0.00828
def rot_q(q, v):
    x, y, z, w = q; u = np.array([x, y, z])
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)
head = np.loadtxt(D + '/head.txt')
H = np.stack([head[:, 0] * S, head[:, 1] * S - 4.384, head[:, 2] * S + 8.491], 1)
GN = rot_q((0.770202, 0, 0, -0.637800), np.loadtxt(D + '/gneck.txt')) + np.array([0, -5.9701, 149.3038])
GS = rot_q((-0.664023, 0, 0, 0.747712), np.loadtxt(D + '/gspine.txt')) + np.array([0, -4.4590, 136.6033])
def to_b(P): return P * np.array([1, -1, 1]) * 0.01
dg = bpy.context.evaluated_depsgraph_get()
bm = bmesh.new()
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'HP': continue
    if o.name.startswith(('Inlay', 'Laurel', 'Etch', 'Rivet', 'Breath')): continue
    me = o.evaluated_get(dg).to_mesh(); me2 = me.copy(); me2.transform(o.matrix_world); bm.from_mesh(me2); bpy.data.meshes.remove(me2)
bvh = BVHTree.FromBMesh(bm)
c = np.array([0, 0.036, 1.65])
res = {}
for name, P in (('head', H), ('gorget_neck', GN), ('gorget_spine', GS)):
    Pb = to_b(P); best = 1e9; where = None; out = 0; nout = 0
    ds = []
    for p in Pb:
        v = Vector(p)
        loc, nrm, idx, dist = bvh.find_nearest(v)
        ds.append(dist)
        if dist < best: best, where = dist, tuple(np.round(p * 100, 1))
        # outside test: walking from the centre to the point crosses the shell only if the point is outside
        d = Vector(p) - Vector(c); L = d.length
        hit = bvh.ray_cast(Vector(c), d.normalized(), L)
        if hit[0] is not None: nout += 1
    ds = np.array(ds)
    res[name] = {'points': len(Pb), 'outside_or_beyond_shell': int(nout), 'min_clearance_cm': round(best * 100, 2), 'at_blender_cm': where, 'p1_clearance_cm': round(float(np.percentile(ds, 1)) * 100, 2)}
    print('FIT', name, res[name])
# helm bbox
vs = np.array([v.co for v in bm.verts]); print('FIT bbox_cm blender', np.round(vs.min(0) * 100, 1).tolist(), np.round(vs.max(0) * 100, 1).tolist())
res['bbox_cm_blender'] = [np.round(vs.min(0) * 100, 2).tolist(), np.round(vs.max(0) * 100, 2).tolist()]
if OUT: json.dump(res, open(OUT, 'w'), indent=1)
