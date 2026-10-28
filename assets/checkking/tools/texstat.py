import sys, bpy, numpy as np
for p in sys.argv[sys.argv.index('--') + 1:]:
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'Non-Color'; im.scale(512, 512)
    a = np.array(im.pixels[:], np.float32).reshape(-1, 4)[:, :3]; m = a.sum(1) > 0.02
    q = np.percentile(a[m], [10, 50, 90], axis=0)
    print('STAT', p.split('/')[-2], p.split('_')[-1], 'p10', q[0].round(3), 'p50', q[1].round(3), 'p90', q[2].round(3))
