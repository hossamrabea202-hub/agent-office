# Contact sheet of PNGs (for review): blender -b --factory-startup -P sheet.py -- <out.png> <cell px> <cols> <img1> <img2> ...
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
out, cell, cols, files = a[0], int(a[1]), int(a[2]), a[3:]
rows = (len(files) + cols - 1) // cols
S = np.zeros((rows * cell, cols * cell, 4), np.float32); S[..., 3] = 1
for k, f in enumerate(files):
    im = bpy.data.images.load(f); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
    px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(H, W, 4)
    yi = (np.arange(cell) * H // cell); xi = (np.arange(cell) * W // cell)
    r, c = divmod(k, cols); S[(rows - 1 - r) * cell:(rows - r) * cell, c * cell:(c + 1) * cell] = px[yi][:, xi]
    bpy.data.images.remove(im)
im = bpy.data.images.new('sheet', S.shape[1], S.shape[0]); im.colorspace_settings.name = 'Non-Color'
im.pixels.foreach_set(S.ravel()); im.filepath_raw = out; im.file_format = 'PNG'; im.save(); print('SHEET', out)
