# #295 preview: numpy port of the M_NoticeBanner HLSL (Roll 1, 0.5; Tier 0 and 1), saved as preview_scroll295.png.
#   "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b --python preview_scroll295.py
import os, numpy as np, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, A = 1520, 128, 11.875


def hsh(ix, iy): return np.modf(np.sin(ix * 127.1 + iy * 311.7) * 43758.5453)[0] % 1.0


def vnoise(px, py, s):
    px, py = px + s, py + s
    ix, iy = np.floor(px), np.floor(py); fx, fy = px - ix, py - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = hsh(ix, iy), hsh(ix + 1, iy), hsh(ix, iy + 1), hsh(ix + 1, iy + 1)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy


def sat(v): return np.clip(v, 0, 1)
def lerp(a, b, t): return a + (b - a) * t


def banner(roll, tier):
    u, v = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
    x, y = u * A, v; cx = A * 0.5; hw = lerp(0.45, cx - 0.5, roll); dx = abs(x - cx); aa = 0.02
    n1, n2 = vnoise(x * 2.5, y * 2.5, 3.1), vnoise(x * 9, y * 9, 17.7)
    nt, nb = vnoise(x * 7, 0 * y, 41.0), vnoise(x * 7, 0 * y, 73.0)
    fb = np.modf(np.sin(np.floor(y * 240) * 91.7 + np.floor(x * 5) * 13.1) * 43758.5453)[0] % 1.0
    yt, yb = 0.11 + 0.022 * (nt - 0.5), 0.89 + 0.022 * (nb - 0.5)
    sheet = sat((hw - dx) / aa) * sat((y - yt) / aa) * sat((yb - y) / aa)
    vel = lerp(np.array([0.19, 0.12, 0.066]), np.array([0.30, 0.20, 0.112]), n1[..., None])
    vel = lerp(vel, np.array([0.25, 0.05, 0.04]) * (0.8 + 0.4 * n1[..., None]), tier)
    vel *= (0.84 + 0.26 * n2)[..., None]; vel *= (0.93 + 0.07 * fb)[..., None]
    vel *= lerp(0.55, 1.0, sat(np.minimum(y - yt, yb - y) / 0.12))[..., None]
    curl = sat(1 - (hw - dx) / 0.6); vel *= (1 - 0.5 * curl * curl)[..., None]
    rule = sat(sat(1 - abs(y - 0.2) / 0.008) + sat(1 - abs(y - 0.8) / 0.008))
    vel = lerp(vel, vel * 0.55, (rule * 0.6)[..., None])
    rodX = abs(dx - hw); rodW = 0.12
    rod = sat((rodW - rodX) / aa) * sat((y - 0.03) / aa) * sat((0.97 - y) / aa)
    shade = np.sqrt(sat(1 - (rodX / rodW) ** 2)); grain = np.modf(y * 14 + 3 * n2)[0]
    wood = np.array([0.11, 0.065, 0.035]) * (0.8 + 0.4 * grain)[..., None]
    fin = sat((abs(y - 0.5) - 0.40) / 0.01)
    rodC = lerp(wood, np.array([0.30, 0.19, 0.07]), fin[..., None]) * (0.3 + 0.9 * shade)[..., None]
    col = lerp(vel, rodC, rod[..., None])
    col *= (1 - 0.4 * sat(1 - (hw - dx) / 0.3) * sheet * (1 - rod))[..., None]
    return col, np.maximum(sheet, rod)


bg = np.array([0.05, 0.07, 0.09])          # a dim night scene behind it
rows = []
for roll, tier in ((1.0, 0.0), (1.0, 1.0), (0.5, 0.0)):
    c, a = banner(roll, tier)
    rows += [np.nan_to_num(c * a[..., None] + bg * (1 - a[..., None])), np.tile(bg, (24, W, 1))]
img = np.concatenate(rows[:-1], 0)
srgb = np.where(img <= 0.0031308, img * 12.92, 1.055 * np.power(np.clip(img, 0, None), 1 / 2.4) - 0.055)
h = img.shape[0]
px = np.concatenate([np.clip(srgb[::-1], 0, 1), np.ones((h, W, 1))], 2).astype(np.float32)
im = bpy.data.images.new('p', W, h, alpha=True); im.pixels.foreach_set(px.ravel())
im.filepath_raw = os.path.join(HERE, 'preview_scroll295.png'); im.file_format = 'PNG'; im.save()
print('saved', im.filepath_raw)
