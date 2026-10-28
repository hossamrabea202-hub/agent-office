# Dump LP UVs as a hash + array: blender -b <file.blend> -P uvcmp.py -- out.npy
import sys, bpy, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
lp = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'HP'][0]
uv = lp.data.uv_layers.active.data; a = np.zeros(len(uv) * 2, dtype=np.float32); uv.foreach_get('uv', a)
np.save(out, a); print('UV', lp.name, len(uv), float(a.sum()))
