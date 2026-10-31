# #293 preview: the M_RealmBubble3 HLSL on a sphere (numpy), day and night, over a sky-to-ground gradient.
#   "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b --python preview_bubble3.py
import os, numpy as np, bpy
HERE = os.path.dirname(os.path.abspath(__file__)); N = 480
def hsh(ix, iy): return (np.sin(ix * 127.1 + iy * 311.7) * 43758.5453) % 1.0
def vn(px, py, s):
    px, py = px + s, py + s; ix, iy = np.floor(px), np.floor(py); fx, fy = px - ix, py - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = hsh(ix, iy), hsh(ix + 1, iy), hsh(ix, iy + 1), hsh(ix + 1, iy + 1)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy
def panel(night):
    yy, xx = np.mgrid[0:N, 0:N]; x, y = (xx + 0.5) / N * 2 - 1, 1 - (yy + 0.5) / N * 2
    r2 = x * x + y * y; inside = r2 < 0.85 ** 2; z = np.sqrt(np.clip(0.85 ** 2 - r2, 0, None)) / 0.85
    F = (1 - z) ** 3
    u = (np.arctan2(x, z) / np.pi + 1) * 0.5; v = np.clip(y / 0.85 * 0.5 + 0.5, 0, 1); T = 30.0
    px, py = u * 6, v * 3; w1 = vn(px * 0.7 + T * 0.02, py * 0.7 + T * 0.02, 5.3)
    th = vn(px + w1 * 1.5 + T * 0.015, py + w1 * 1.5 + T * 0.015, 11.9); tn = vn(u * 6 + T * 0.01, v * 3 - T * 0.006, 29.4)
    k = th * 2.2 + F * 0.8
    film = 0.5 + 0.5 * np.cos(6.2831853 * (k[..., None] + np.array([0, 0.33, 0.67])))
    film = film.mean(-1, keepdims=True) + (film - film.mean(-1, keepdims=True)) * 0.55
    em = film * F[..., None] * 0.6 * (0.35 if night else 1.0)
    tent = np.clip((tn - 0.55) / 0.2, 0, 1); tent = tent * tent * (3 - 2 * tent); em *= (1 - tent)[..., None]
    op = np.clip(0.03 + (0.35 - 0.03) * F + tent * 0.12, 0, 1)
    sky = np.where((y > -0.3)[..., None], np.array([0.35, 0.45, 0.6]) if not night else np.array([0.02, 0.025, 0.04]),
                   np.array([0.12, 0.1, 0.07]) if not night else np.array([0.01, 0.01, 0.01]))
    out = sky * (1 - op[..., None]) + np.array([0.015, 0.014, 0.016]) * op[..., None] + em
    return np.where(inside[..., None], out, sky)
img = np.concatenate([panel(False), panel(True)], 1)
s = np.where(img <= 0.0031308, img * 12.92, 1.055 * np.power(np.clip(img, 0, None), 1 / 2.4) - 0.055)
px = np.concatenate([np.clip(s[::-1], 0, 1), np.ones(s.shape[:2] + (1,))], 2).astype(np.float32)
im = bpy.data.images.new('p', img.shape[1], img.shape[0], alpha=True); im.pixels.foreach_set(px.ravel())
im.filepath_raw = os.path.join(HERE, 'preview_bubble3.png'); im.file_format = 'PNG'; im.save(); print('saved')
