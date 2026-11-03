# #440: mean / p50 sRGB of a crop (x0,y0,x1,y1 in image px, origin top-left) of base-colour shots
import bpy, os, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; x0, y0, x1, y1 = [int(v) for v in a[0].split(',')]
for p in a[1:]:
    im = bpy.data.images.load(p); w, h = im.size; px = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1]
    c = px[y0:y1, x0:x1, :3].reshape(-1, 3) * 255
    print('CROP', os.path.basename(p), 'mean', c.mean(0).round(), 'p50', np.median(c, 0).round(), 'p90', np.percentile(c, 90, 0).round())
