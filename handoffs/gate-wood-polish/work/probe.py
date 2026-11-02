import bpy, sys, numpy as np
f, pts = sys.argv[sys.argv.index('--') + 1], sys.argv[sys.argv.index('--') + 2:]
im = bpy.data.images.load(f); w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)
for p in pts:
    x, y = [int(v) for v in p.split(',')]; v = px[h - 1 - y, x, :3]   # image coords: y from top
    lin = float(v @ np.array([0.2126, 0.7152, 0.0722])); s = (1.055 * lin ** (1 / 2.4) - 0.055) * 255 if lin > 0.0031308 else lin * 12.92 * 255
    print('px %s rgb %s lum %.3f (~%d sRGB)' % (p, np.round(v, 3), lin, s))
