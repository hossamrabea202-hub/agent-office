# Sword fire textures (laptop2, 2026-10-30): a seamless fire-noise pack + a heat ramp, for the hero's flaming sword overlay.
#   T_SwordFire_Noise.png 512x512 RGB linear, tiles both ways: R soft fbm (flame body), G sharp wisps (ridged), B a second fbm offset (break-up)
#   T_SwordFire_Ramp.png 256x8 sRGB: heat ramp black -> deep red -> orange -> yellow -> white (u = temperature)
import numpy as np, os
import bpy
def save(arr8, path):
    h, w = arr8.shape[:2]; im = bpy.data.images.new('x', w, h, alpha=True); px = np.ones((h, w, 4), np.float32); px[..., :3] = arr8[::-1] / 255.0
    im.pixels.foreach_set(px.ravel()); im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
OUT = r'C:/Users/hossam.rabea/agent-office/assets/laptop2/SwordFire'
N = 512; rng = np.random.default_rng(7)
u, v = np.meshgrid(np.linspace(0, 1, N, endpoint=False), np.linspace(0, 1, N, endpoint=False))
def pnoise(u, v, p, seed):     # periodic value noise with period p (integer lattice), smoothstep interpolation
    r = np.random.default_rng(seed); lat = r.random((p, p))
    x, y = u * p, v * p; x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); fx, fy = x - x0, y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    g = lambda i, j: lat[j % p, i % p]
    return (g(x0, y0) * (1 - fx) + g(x0 + 1, y0) * fx) * (1 - fy) + (g(x0, y0 + 1) * (1 - fx) + g(x0 + 1, y0 + 1) * fx) * fy
def fbm(u, v, p, seed, oct=5, gain=0.5, ridged=False):
    a, s, tot = 1.0, 0.0, 0.0
    for o in range(oct):
        n = pnoise(u, v, p * 2 ** o, seed + o)
        if ridged: n = 1 - abs(2 * n - 1); n = n * n
        s += a * n; tot += a; a *= gain
    return s / tot
R = fbm(u, v * 2 % 1, 4, 11)                                  # stretched along v (flames are tall)
G = fbm(u, v * 2 % 1, 8, 23, oct=4, gain=0.55, ridged=True)
B = fbm((u + 0.37) % 1, (v * 2 + 0.11) % 1, 6, 37)
norm = lambda a: (a - a.min()) / (a.max() - a.min())
img = np.stack([norm(R), norm(G), norm(B)], -1)
save((img * 255 + 0.5).astype(np.uint8), os.path.join(OUT, 'T_SwordFire_Noise.png'))
# ramp: black -> red -> orange -> yellow -> white (sRGB), with the lower 8 % fully black so the flame edge is clean
t = np.linspace(0, 1, 256)
keys = [(0.0, (0, 0, 0)), (0.08, (0, 0, 0)), (0.25, (0.55, 0.02, 0.0)), (0.5, (1.0, 0.25, 0.0)), (0.75, (1.0, 0.72, 0.1)), (1.0, (1.0, 0.97, 0.85))]
ramp = np.zeros((8, 256, 3))
for c in range(3):
    ramp[:, :, c] = np.interp(t, [k for k, _ in keys], [col[c] for _, col in keys])
save((ramp * 255 + 0.5).astype(np.uint8), os.path.join(OUT, 'T_SwordFire_Ramp.png'))
print('wrote', OUT, 'noise R/G/B mean', [round(float(img[..., i].mean()), 3) for i in range(3)])
