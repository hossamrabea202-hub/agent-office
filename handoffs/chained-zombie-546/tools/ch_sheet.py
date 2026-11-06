# blender -b --factory-startup -P ch_sheet.py -- <out.png> <cols> <a.png> <b.png> ...   contact sheet
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; OUT, COLS = a[0], int(a[1]); fs = a[2:]; ims = []
for f in fs:
    i = bpy.data.images.load(f); w, h = i.size; p = np.array(i.pixels[:], dtype=np.float32).reshape(h, w, 4); ims.append(p)
h, w = ims[0].shape[:2]; rows = (len(ims) + COLS - 1) // COLS; S = np.zeros((rows * h, COLS * w, 4), np.float32); S[..., 3] = 1
for k, p in enumerate(ims):
    r = rows - 1 - k // COLS; c = k % COLS; S[r * h:(r + 1) * h, c * w:(c + 1) * w] = p
o = bpy.data.images.new('s', COLS * w, rows * h); o.pixels = S.ravel().tolist(); o.filepath_raw = OUT; o.file_format = 'PNG'; o.save(); print('SHEET', OUT)
