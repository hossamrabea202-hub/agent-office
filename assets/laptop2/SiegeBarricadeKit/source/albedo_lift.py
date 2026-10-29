# Calibrated-lookdev fix (handoffs/knowledge): the v2 bark read darker than the 0.18 grey ball (median ~60 sRGB, weathered
# wood should sit ~90-115). Scales the albedo in linear light, with a soft shoulder so the brightest texels stay < ~200 sRGB.
#   blender -b --factory-startup -P albedo_lift.py -- <gain> <BaseColor.png> [...]
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; K = float(a[0])
def to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
for p in a[1:]:
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'Non-Color'; w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(-1, 4)
    used = px[:, :3].max(-1) > 0.002                       # outside the UV islands stays black (padding)
    lin = to_lin(px[used, :3]) * K
    S = 0.55; lin = np.where(lin > S * 0.7, S * 0.7 + (lin - S * 0.7) / (1 + (lin - S * 0.7) / (S * 0.3)), lin)   # shoulder
    px[used, :3] = to_srgb(lin); im.pixels.foreach_set(px.ravel()); im.filepath_raw = p; im.file_format = 'PNG'; im.save()
    s = px[used, :3].mean(-1) * 255
    print('LIFT', p.split('\\')[-1], 'p5/p50/p95 sRGB = %.0f/%.0f/%.0f' % tuple(np.percentile(s, [5, 50, 95])), flush=True)
    bpy.data.images.remove(im)
