# Round trip of the delivered FBX (#485): tris, bounds, UV overlap + use, loose normals, and the frame against a piece already in the game.
#   blender -b --factory-startup -P verify_fbx.py -- <helm.fbx> <Boots_L.fbx> [BaseColor.png]
import sys, bpy
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    o = [x for x in bpy.data.objects if x.type == 'MESH']
    assert len(o) == 1, [x.name for x in o]
    return o[0]
o = load(a[0]); me = o.data; M = np.array(o.matrix_world)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = (M[:3, :3] @ co.reshape(-1, 3).T).T + M[:3, 3]
print('VERIFY name', o.name, 'polys', len(me.polygons), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'material slots', len(me.materials), 'uv layers', len(me.uv_layers))
print('VERIFY bounds cm blender min', np.round(co.min(0) * 100, 2).tolist(), 'max', np.round(co.max(0) * 100, 2).tolist())
print('VERIFY UE bounds cm: x', np.round([co[:, 0].min() * 100, co[:, 0].max() * 100], 1).tolist(), 'y', np.round([-co[:, 1].max() * 100, -co[:, 1].min() * 100], 1).tolist(), 'z', np.round([co[:, 2].min() * 100, co[:, 2].max() * 100], 1).tolist())
print('VERIFY origin', np.round(M[:3, 3], 4).tolist(), 'smooth', sum(p.use_smooth for p in me.polygons))
N = 2048
uv = me.uv_layers.active.data
grid = np.zeros((N, N), np.int16); degenerate = 0
for p in me.polygons:
    if len(p.loop_indices) != 3: continue
    t = np.array([uv[i].uv for i in p.loop_indices]) * N
    area = (t[1, 0] - t[0, 0]) * (t[2, 1] - t[0, 1]) - (t[2, 0] - t[0, 0]) * (t[1, 1] - t[0, 1])
    if abs(area) < 1e-6: degenerate += 1; continue
    x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N), min(y1, N)
    if x1 <= x0 or y1 <= y0: continue
    X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    d = lambda A, B: (B[0] - A[0]) * (Y - A[1]) - (B[1] - A[1]) * (X - A[0])
    s = np.sign(area); w = (d(t[0], t[1]) * s >= 0) & (d(t[1], t[2]) * s >= 0) & (d(t[2], t[0]) * s >= 0)
    grid[y0:y1, x0:x1] += w
u = np.array([v.uv for v in uv])
print('VERIFY UV range', np.round(u.min(0), 4).tolist(), np.round(u.max(0), 4).tolist(), 'used %.1f%%' % ((grid > 0).mean() * 100), 'texels covered twice or more %d' % (grid > 1).sum(), 'degenerate UV tris', degenerate)
if len(a) > 2:      # bake misses show as pure black inside the UV islands
    im = bpy.data.images.load(a[2]); im.colorspace_settings.name = 'Non-Color'; w, h = im.size
    x = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(x); x = x.reshape(h, w, 4)
    miss = (x[..., :3].max(-1) < 0.002) & (grid > 0)
    print('VERIFY bake misses: %d black texels inside the islands of %d (%.2f%%)' % (miss.sum(), (grid > 0).sum(), 100 * miss.sum() / (grid > 0).sum()))
b = load(a[1]); B = np.array(b.matrix_world); c = np.empty(len(b.data.vertices) * 3); b.data.vertices.foreach_get('co', c); c = (B[:3, :3] @ c.reshape(-1, 3).T).T + B[:3, 3]
print('VERIFY frame check Boots_L FBX cm: x', np.round([c[:, 0].min() * 100, c[:, 0].max() * 100], 1).tolist(), 'y', np.round([c[:, 1].min() * 100, c[:, 1].max() * 100], 1).tolist(), 'z', np.round([c[:, 2].min() * 100, c[:, 2].max() * 100], 1).tolist(), '(UE asset measured: x 6.8..20.2, y -10.4..27.7, z 0..24.4)')
