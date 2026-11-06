# #539 ejecta skirt decal: blender -b --factory-startup -P gen_skirt.py -- <out tex dir>. Dirt thrown out by the eruption, streaked along the blast, thinning to nothing.
# T_SporeSkirt_BC: soil. T_SporeSkirt_Mask: R opacity, G roughness. The hole at the centre sits under the mound.
import bpy, sys, os, math, numpy as np
OUT = sys.argv[sys.argv.index('--') + 1]; os.makedirs(OUT, exist_ok=True); rng = np.random.default_rng(539); P_ = rng.permutation(4096); G_ = rng.random(4096)
def vn(x, y, z=0.0):
    x, y = np.asarray(x, float), np.asarray(y, float); z = np.broadcast_to(z, x.shape).astype(float); i, j, k = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int); u, v, w = x - i, y - j, z - k; u, v, w = u * u * (3 - 2 * u), v * v * (3 - 2 * v), w * w * (3 - 2 * w)
    h = lambda a, b, c: G_[P_[(P_[(P_[a & 4095] + b) & 4095] + c) & 4095]]
    return ((h(i, j, k) * (1 - u) + h(i + 1, j, k) * u) * (1 - v) + (h(i, j + 1, k) * (1 - u) + h(i + 1, j + 1, k) * u) * v) * (1 - w) + ((h(i, j, k + 1) * (1 - u) + h(i + 1, j, k + 1) * u) * (1 - v) + (h(i, j + 1, k + 1) * (1 - u) + h(i + 1, j + 1, k + 1) * u) * v) * w
def fbm(x, y, z=0.0, o=5):
    t, a, tot = 0.0, 1.0, 0.0
    for _ in range(o): t = t + a * (vn(x, y, z) - 0.5); tot += a; x, y, z = x * 2.03 + 17.3, y * 2.03 + 9.1, np.asarray(z) * 2.03 + 3.7; a *= 0.5
    return t / tot * 2
sstep = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))
N = 1024; yy, xx = np.mgrid[0:N, 0:N]; X, Y = (xx - N / 2 + 0.5) / (N / 2), (yy - N / 2 + 0.5) / (N / 2); R = np.hypot(X, Y); A = np.arctan2(Y, X)
streak = fbm(np.cos(A) * 9, np.sin(A) * 9, R * 1.3, 4); clumps = fbm(X * 14, Y * 14, 2.0, 5); reach = 0.62 + 0.3 * (streak + 0.4)      # how far the dirt was thrown, per direction
op = (1 - sstep(reach * 0.55, reach, R + 0.1 * clumps)) * sstep(-0.32, 0.18, clumps + 0.9 - R * 1.1); op = np.clip(op * 0.9, 0, 1) * (1 - sstep(0.92, 1.0, R))
bc = np.stack([(66 / 255) * (1 + 0.3 * clumps), (54 / 255) * (1 + 0.3 * clumps), (41 / 255) * (1 + 0.3 * clumps)], -1)     # sRGB values, byte images store them directly
rg = np.clip(0.9 + 0.2 * clumps, 0.6, 1.0)
def save(n, rgb):
    im = bpy.data.images.new(n, N, N, alpha=False, float_buffer=False); o = np.ones((N, N, 4), np.float32); o[..., :3] = np.clip(rgb, 0, 1); im.pixels.foreach_set(o.ravel()); im.filepath_raw = os.path.join(OUT, n + '.png'); im.file_format = 'PNG'; im.save(); print('SKIRT', n, np.round(rgb.mean((0, 1)), 3))
bpy.ops.wm.read_factory_settings(use_empty=True); save('T_SporeSkirt_BC', bc); save('T_SporeSkirt_Mask', np.stack([op, rg, np.zeros_like(op)], -1))
