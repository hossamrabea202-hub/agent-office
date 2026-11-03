# #440 (i5): albedo of the grass scans where the blade is opaque (sRGB 0-255), for tint calibration.
import bpy, os, sys, numpy as np
D = sys.argv[sys.argv.index('--') + 1]
for n in ('T_vczndjqja_4K_B', 'T_vlkhcbxia_8K_B'):
    im = bpy.data.images.load(os.path.join(D, n + '.png')); w, h = im.size
    a = np.array(im.pixels[:], np.float32).reshape(h, w, 4)
    op = a[:, :, 3] > 0.5; s = a[:, :, :3][op] * 255
    print('ALB', n, w, h, 'opaque %.0f%%' % (100 * op.mean()), 'p10', np.percentile(s, 10, 0).round(), 'p50', np.median(s, 0).round(), 'p90', np.percentile(s, 90, 0).round())
