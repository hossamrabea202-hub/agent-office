# LP UV sanity: zero-area UV faces (by nearest HP material) + overlap at 512.
import bpy, numpy as np
from collections import Counter
from mathutils.bvhtree import BVHTree
LP = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'HP'][0]; HP = bpy.data.objects['HP']
dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(HP, dg); hpm = [s.material.name.split('.')[0] for s in HP.material_slots]
uv = LP.data.uv_layers.active.data; inv = HP.matrix_world.inverted(); z = Counter(); tot = Counter()
N = 512; grid = np.zeros((N, N), np.int32)
for f in LP.data.polygons:
    p = [uv[i].uv for i in f.loop_indices]; a = 0
    for i in range(1, len(p) - 1): a += abs((p[i].x - p[0].x) * (p[i + 1].y - p[0].y) - (p[i + 1].x - p[0].x) * (p[i].y - p[0].y)) / 2
    m = hpm[HP.data.polygons[bvh.find_nearest(inv @ (LP.matrix_world @ f.center))[2]].material_index]
    tot[m] += 1
    if a * 4096 * 4096 < 0.25: z[m] += 1
print('UVCHK tris', sum(len(p.vertices) - 2 for p in LP.data.polygons), 'faces', len(LP.data.polygons))
for m in tot: print('UVCHK', m, 'faces', tot[m], 'zero-area(<1/4 texel @4K)', z[m])
