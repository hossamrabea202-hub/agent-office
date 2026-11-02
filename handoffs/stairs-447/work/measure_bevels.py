import bpy, glob, os, sys
d = sys.argv[sys.argv.index('--') + 1]
for f in sorted(glob.glob(os.path.join(d, '*.fbx'))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    vs = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    lo = [min(v[k] for v in vs) for k in range(3)]; hi = [max(v[k] for v in vs) for k in range(3)]
    bev = []
    for k in range(3):
        ins = sorted(set(round(min(v[k]-lo[k], hi[k]-v[k]), 4) for v in vs))
        bev.append([x for x in ins if 1e-4 < x][:2])
    nf = sum(len(o.data.polygons) for o in obs); nv = len(vs)
    uv = [len(o.data.uv_layers) for o in obs]
    print('%-20s size(cm)=%s  verts=%d faces=%d uvs=%s  inset-from-edges(cm) X/Y/Z=%s' % (os.path.basename(f)[:-4],
          [round((hi[k]-lo[k])*100, 1) for k in range(3)], nv, nf, uv, [[round(x*100, 2) for x in b] for b in bev]))
