# Rasterise LP UV triangles at 512 and report overlapping pixels (and which material-region / object part they belong to).
import bpy, numpy as np
ob = next(o for o in bpy.data.objects if o.name.startswith('SM_ObsidianSovereign_Shoulders_L'))
me = ob.data; me.calc_loop_triangles()
uv = me.uv_layers.active.data
N = 512; cnt = np.zeros((N, N), np.int32); owner = np.full((N, N), -1, np.int64); clash = set()
for t in me.loop_triangles:
    p = np.array([uv[i].uv for i in t.loops]) * N
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)) + 0.5, np.arange(max(y0, 0), min(y1, N)) + 0.5)
    if xs.size == 0: continue
    a, b, c = p
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-12: continue
    l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
    l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
    ins = (l1 >= 0) & (l2 >= 0) & (1 - l1 - l2 >= 0)
    yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
    cnt[yy, xx] += 1
    hit = owner[yy, xx]
    for o in set(hit[hit >= 0].tolist()): clash.add((o, t.index))
    owner[yy, xx] = t.index
print('UVOVERLAP covered', int((cnt > 0).sum()), 'overlap px', int((cnt > 1).sum()), 'of', N * N)
import sys, collections
sys.path.insert(0, r'C:\Users\hossam.rabea\checkking-work\shoulders')
from shoulderlib import O, D
tris = me.loop_triangles
def desc(i):
    c = np.mean([me.vertices[v].co for v in tris[i].vertices], 0); q = c - O; h = -(q @ D); r = np.linalg.norm(q + h * D)
    n = np.array(tris[i].normal); rad = (q + h * D) / (r + 1e-9)
    return f'h{h:+.3f} r{r:.3f} {"in" if n @ rad < -0.25 else "out" if n @ rad > 0.25 else "side"}'
c = collections.Counter()
for a, b in clash: c[(desc(a)[:5], desc(a)[-4:], desc(b)[:5], desc(b)[-4:])] += 1
for k, v in c.most_common(15): print('CLASH', v, k)
