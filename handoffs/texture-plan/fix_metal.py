# #262 step 2b (TGA, 2026-10-31): after a box downsize, thin metal (nails, bands, rivets) averages with its rust / wood
# neighbours: metallic goes fractional and the metal albedo drops below 180 sRGB. KB rule: metallic is 0 or 1, bare metal
# >= 180 sRGB. This snaps ORM.B to 0/1 (>= 0.5 -> metal) and lifts the BaseColor of metal texels to >= 180 sRGB luminance
# (hue kept). Non-metal texels are untouched.
#   blender -b --factory-startup -P fix_metal.py -- <BC.png> <ORM.png> [more pairs]
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
def load(p):
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
    px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); return im, px.reshape(H, W, 4)
def save(im, px, p):
    W, H = im.size; fmt = im.file_format; alpha = im.channels == 4; bpy.data.images.remove(im)
    o = bpy.data.images.new('fx', W, H, alpha=alpha); o.colorspace_settings.name = 'Non-Color'
    o.pixels.foreach_set(np.clip(px, 0, 1).ravel()); o.filepath_raw = p; o.file_format = fmt
    s = bpy.context.scene.render.image_settings; s.color_mode = 'RGBA' if alpha else 'RGB'; s.compression = 100
    o.save(); bpy.data.images.remove(o)
lum = lambda c: 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]
T = ((180 / 255 + 0.055) / 1.055) ** 2.4                                           # 180 sRGB in linear
for bc_p, orm_p in zip(a[0::2], a[1::2]):
    bi, bc = load(bc_p); oi, orm = load(orm_p)
    if bc.shape != orm.shape: print('SKIP size mismatch', bc_p); bpy.data.images.remove(bi); bpy.data.images.remove(oi); continue
    metal = orm[..., 2] >= 0.5
    orm[..., 2] = metal.astype(np.float32)
    lin = np.where(bc[..., :3] <= 0.04045, bc[..., :3] / 12.92, ((bc[..., :3] + 0.055) / 1.055) ** 2.4)
    l = lum(lin); k = np.where(metal & (l < T), T / np.maximum(l, 1e-4), 1.0)
    lin = np.clip(lin * k[..., None], 0, 1)
    bc[..., :3] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    save(bi, bc, bc_p); save(oi, orm, orm_p)
    print('FIXED', os.path.basename(bc_p), '%d metal texels' % int(metal.sum()), flush=True)
