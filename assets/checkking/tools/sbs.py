# Side-by-side of two PNGs (scaled to the same height): blender -b -P sbs.py -- left right out height
import sys, bpy, numpy as np
a, b, out, h = sys.argv[sys.argv.index('--') + 1:]; h = int(h)
def load(p):
    im = bpy.data.images.load(p); im.scale(int(im.size[0] * h / im.size[1]), h)
    return np.array(im.pixels[:], dtype=np.float32).reshape(h, im.size[0], 4)
A, B = load(a), load(b); C = np.concatenate([A, B], 1)
o = bpy.data.images.new('sbs', C.shape[1], h); o.pixels = C.ravel(); o.filepath_raw = out; o.file_format = 'PNG'; o.save()
print('SBS', C.shape)
