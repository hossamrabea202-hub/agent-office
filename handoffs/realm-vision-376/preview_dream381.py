# #381 mock of the dream post-process (numpy copy of DREAM_HLSL in setup_realmvision381_ue.py, plus the v2 look's grade).
#   blender -b --factory-startup -P preview_dream381.py -- <in.jpg> <out.png>
# Writes one strip: v1 (dark green, owner rejected) | v2 inside (Amount 1) | v2 crossing (Cross 0.7, swallowed). Not the engine.
import sys, numpy as np, bpy

src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
im = bpy.data.images.load(src); im.scale(800, int(800 * im.size[1] / im.size[0]))
W, H = im.size
img = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1, :, :3]          # top-down, linear
img = np.clip(img, 0, 1)                                                            # byte image: already display space
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
U, Vv = (xx + 0.5) / W, (yy + 0.5) / H
asp = W / H


def samp(u, v):
    x = np.clip(u * W - 0.5, 0, W - 1.001); y = np.clip(v * H - 0.5, 0, H - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    a, b = img[y0, x0], img[y0, x0 + 1]; c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def dream(a, c, T=4.0, Hz=0.2, Dir=1.0, Warp=1, Ghost=1, Glow=1, Lift=1, Haze=1, Lens=1, Chroma=1, Heart=1, HeartHz=0.75):
    dx, dy = U - 0.5, Vv - 0.5
    r = np.sqrt((dx * asp) ** 2 + dy ** 2)
    br = np.sin(T * 6.2831853 * Hz)
    wx = np.sin(Vv * 6 + T * 0.6) + 0.5 * np.sin(Vv * 13 - T * 0.9)
    wy = np.sin(U * 5 - T * 0.5) + 0.5 * np.sin(U * 11 + T * 0.7)
    k = 0.0045 * Warp * a * (0.35 + 1.6 * r)
    ox, oy = wx * k - dx * 0.008 * a * br, wy * k - dy * 0.008 * a * br
    lens = c * Lens * 0.10 * r * r * (1 if Dir >= 0 else -1) * (1 + 0.3 * np.sin(r * 25 - T * 8))
    ox, oy = ox - dx * lens, oy - dy * lens
    sw = 0.05 * a * Warp * r * r * np.sin(T * 0.23)
    ox, oy = ox + (-dy) / asp * sw, oy + dx * asp * sw
    u2, v2 = U + ox, Vv + oy
    cs = (0.002 * a + 0.012 * c) * Chroma
    col = np.stack([samp(u2 + dx * cs, v2 + dy * cs)[..., 0], samp(u2, v2)[..., 1], samp(u2 - dx * cs, v2 - dy * cs)[..., 2]], -1)
    gh = samp(u2 + np.sin(T * 0.37) * 0.014 * Ghost, v2 + np.cos(T * 0.29) * 0.014 * Ghost)
    col = col + (np.maximum(col, gh) - col) * 0.35 * a * Ghost
    rad = 0.006 * a * Glow + 0.02 * c
    bl = np.zeros_like(col)
    for i in range(12):
        an, kk = i * 2.39996323, (i + 0.5) / 12
        bl += samp(u2 + np.cos(an) / asp * np.sqrt(kk) * rad, v2 + np.sin(an) * np.sqrt(kk) * rad)
    bl /= 12
    col = col + (bl - col) * np.clip(0.25 * a * Haze + 0.7 * c, 0, 1)
    col = col + np.maximum(bl - 0.55, 0) * np.array([1.0, 0.62, 0.48]) * 1.0 * Glow * a
    lum = (col * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    g = col * np.array([1.07, 0.94, 0.90]) + np.array([0.05, 0.022, 0.03]) * Lift * (1 - lum)
    g = g + (lum * np.array([1.10, 0.86, 0.80]) - g) * 0.08
    vig = np.clip((r - 0.35) / 0.6, 0, 1); vig = (vig * vig * (3 - 2 * vig))[..., None]
    g = g + (g * np.array([1.0, 0.72, 0.64]) + np.array([0.04, 0.008, 0.015]) - g) * vig * 0.45
    hb = np.clip(np.sin(T * 6.2831853 * HeartHz), 0, 1) ** 12 * Heart
    g = g * (1 - vig * hb * 0.18)
    cl = np.clip((r - (0.75 - 0.5 * c)) / (1.05 - (0.75 - 0.5 * c)), 0, 1); cl = (cl * cl * (3 - 2 * cl) * c)[..., None]
    g = g + (np.array([0.34, 0.09, 0.11]) - g) * cl * 0.8
    m = max(a, c)
    return np.clip(img + (g - img) * m, 0, 1)


def v1_green():   # the rejected v1 look, roughly: exposure -0.35, gain .92/1.04/.94, tint .86/1/.88, saturation .8, vignette .75
    g = img * 2 ** -0.35 * np.array([0.92, 1.04, 0.94]) * np.array([0.86, 1.0, 0.88])
    lum = (g * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    g = lum + (g - lum) * 0.8
    r = np.sqrt(((U - 0.5) * asp) ** 2 + (Vv - 0.5) ** 2)[..., None]
    return np.clip(g * (1 - 0.75 * np.clip(r - 0.2, 0, 1) ** 1.5), 0, 1)


def brighten(x):  # the v2 PP settings on top (exposure +0.25, gain 1.08/.97/.95, offset lift)
    return np.clip(x * 2 ** 0.25 * np.array([1.08, 0.97, 0.95]) + np.array([0.015, 0.004, 0.010]), 0, 1)


panels = [v1_green(), brighten(dream(1.0, 0.0)), brighten(dream(0.4, 0.7, T=4.3))]
strip = np.concatenate([np.pad(p, ((0, 0), (0, 12), (0, 0)), constant_values=1.0) for p in panels], 1)[:, :-12]
h, w = strip.shape[:2]
out = bpy.data.images.new('strip', w, h, alpha=False)
px = np.concatenate([strip[::-1], np.ones((h, w, 1), np.float32)], -1)
out.pixels[:] = px.ravel()
out.filepath_raw = dst; out.file_format = 'PNG'; out.save()
print('wrote', dst, w, h)
