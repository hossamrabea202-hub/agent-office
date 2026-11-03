# #301 W2 (i5): scan_B.png is a whole stone WALL with its own painted joints (~25 px wide), which would fight the real
# joints in our geometry + M.G mask. A grey closing failed (blocky squares, grain lost, joints wider than the kernel).
# So: cut a joint-free crop from inside one granite block and mirror-tile it 2x2 (seamless by construction; mirror seams
# don't read on granite speckle). Same pixels as the wall scan = same colour and grain as the keep + walls.
# Grain scale is kept: scan 2048 px = 1.5 m, so the 520 px tile = 0.38 m (bake_color.py tile_m).
#   blender -b --factory-startup -P clean_scan.py -- [row0 col0 size]
import bpy, os, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
R0, C0, S = (int(x) for x in argv) if len(argv) == 3 else (1380, 710, 260)
HERE = os.path.dirname(os.path.abspath(__file__))
im = bpy.data.images.load(os.path.join(HERE, 'scan_B.png'))
w, h = im.size
a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
c = a[R0:R0 + S, C0:C0 + S]
t = np.concatenate([np.concatenate([c, c[:, ::-1]], 1), np.concatenate([c[::-1], c[::-1, ::-1]], 1)], 0)
out = bpy.data.images.new('granite_tile', 2 * S, 2 * S, alpha=False)
out.pixels[:] = t.ravel()
out.filepath_raw = os.path.join(HERE, 'granite_tile.png'); out.file_format = 'PNG'; out.save()
lum = lambda x: float((x[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)).mean())
print('TILE', 2 * S, 'crop rows', R0, 'cols', C0, 'lum scan', lum(a), 'tile', lum(t))
