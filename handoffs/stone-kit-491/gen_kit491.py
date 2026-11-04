# #491 stone KIT blocks (i9 11-04; TGA_PC had not delivered): one closed SHARP ashlar block per kit name used by
# layout/report.json (SM_Kit_H<cm>_L<cm>_V<n>), size = exactly L x 0.38 x H m (the 12 mm joint is in the layout spacing),
# pivot at the block centre, built with gen_boxmason.rbox (SHARP) -> fold check per block (must be inverted 0) -> FBX
# like gen_boxmason (Y mirrored, colours LINEAR). Vertex colour R (tone) = 0.5: per-stone tone/seed comes from
# PerInstanceRandom on the HISM. Lookdev sheet: Cycles render of all blocks under raking light.
# Run: blender -b -P gen_kit491.py [-- --no-render]   -> sync58/tunnel/kit491_fbx/*.fbx + foldcheck.txt + lookdev_kit491.png
import sys, os, json, math, random, re
sys.path.insert(0, 'C:/Users/hossa/sync58/tunnel')
import bpy, bmesh, numpy as np
from mathutils import Vector
import gen_boxmason as GB

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = 'C:/Users/hossa/sync58/tunnel/kit491_fbx'; os.makedirs(OUT, exist_ok=True)
DEPTH = 0.38
RENDER = '--no-render' not in sys.argv

rep = json.load(open(os.path.join(HERE, 'layout', 'report.json')))
names = sorted({k for r in rep.values() for k in r.get('kit_use', {})})
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
mats = [bpy.data.materials.new('M_Tun_Ashlar'), bpy.data.materials.new('M_Tun_Mortar')]

def foldcheck(me):
    bm = bmesh.new(); bm.from_mesh(me); c = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    bad = zero = 0
    for f in bm.faces:
        if f.calc_area() < 1e-9: zero += 1; continue
        if f.normal.dot(f.calc_center_median() - c) < 0: bad += 1
    n = len(bm.faces); bm.free(); return n, bad, zero

info, lines, objs = [], [], []
for name in names:
    H, L, V = (int(x) for x in re.match(r'SM_Kit_H(\d+)_L(\d+)_V(\d+)$', name).groups())
    random.seed(491000 + H * 1000 + L * 10 + V)
    B = GB.Buf()
    GB.rbox(B, Vector((0, 0, 0)), Vector((L / 200.0, DEPTH / 2.0, H / 200.0)), tone=0.5)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(p.x, -p.y, p.z) for p in B.v], [], B.f)
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', B.mat)
    lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
    me.uv_layers.new(name='UV0').data.foreach_set('uv', np.asarray(B.uv, dtype=np.float32)[lv].ravel())
    me.attributes.new('Col', 'FLOAT_COLOR', 'CORNER').data.foreach_set('color', np.clip(np.asarray(B.col, dtype=np.float32), 0, 1)[lv].ravel())
    me.flip_normals()                              # Y mirror flipped the winding
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
    me.shade_smooth()
    n, bad, zero = foldcheck(me)
    dims = [round(max(v.co[a] for v in me.vertices) - min(v.co[a] for v in me.vertices), 4) for a in range(3)]
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); objs.append(ob)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath='%s/%s.fbx' % (OUT, name), use_selection=True, mesh_smooth_type='FACE', add_leaf_bones=False,
                             bake_anim=False, axis_forward='-Z', axis_up='Y', apply_scale_options='FBX_SCALE_NONE', colors_type='LINEAR')
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    info.append({'name': name, 'tris': tris, 'dims_m': dims, 'faces': n, 'inverted': bad, 'zero_area': zero})
    lines.append('%s tris %d dims %s faces %d inverted %d zero-area %d' % (name, tris, dims, n, bad, zero))
    print('KIT', lines[-1], flush=True)
tot_bad = sum(i['inverted'] for i in info)
lines.append('FOLDCHECK blocks %d inverted %d zero-area %d' % (len(info), tot_bad, sum(i['zero_area'] for i in info)))
print(lines[-1], flush=True)
open(os.path.join(HERE, 'foldcheck_kit491.txt'), 'w').write('\n'.join(lines) + '\n')
json.dump(info, open('%s/kit_built.json' % OUT, 'w'), indent=1)

if RENDER:
    # lookdev sheet: 5 lengths across, 4 heights x 2 variants down, neutral grey stone + raking sun
    sm = bpy.data.materials.new('LD_Stone'); sm.use_nodes = True
    bsdf = sm.node_tree.nodes['Principled BSDF']; bsdf.inputs['Base Color'].default_value = (0.32, 0.31, 0.29, 1); bsdf.inputs['Roughness'].default_value = 0.8
    Ls = sorted({int(re.search(r'_L(\d+)', n).group(1)) for n in names}); Hs = sorted({int(re.search(r'_H(\d+)', n).group(1)) for n in names})
    for ob in objs:
        H, L, V = (int(x) for x in re.match(r'SM_Kit_H(\d+)_L(\d+)_V(\d+)$', ob.name).groups())
        ob.data.materials.clear(); ob.data.materials.append(sm)
        ob.location = (sum(l / 100.0 + 0.15 for l in Ls[:Ls.index(L)]), 0, -(Hs.index(H) * 2 + V - 1) * 0.68)
    W = sum(l / 100.0 + 0.15 for l in Ls); Ht = len(Hs) * 2 * 0.68
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(W, Ht) * 1.08
    cam.location = (W / 2 - 0.3, -10, -(len(Hs) * 2 - 1) * 0.34); cam.rotation_euler = (math.radians(90), 0, 0)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 5.0; sun.rotation_euler = (math.radians(60), 0, math.radians(-80))   # raking from the left (shows arrises/chips)
    sc = bpy.context.scene; sc.camera = cam; sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 2000, int(2000 * Ht / W) if W > Ht else 2000
    sc.world = sc.world or bpy.data.worlds.new('w'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25
    sc.render.filepath = os.path.join(HERE, 'lookdev_kit491.png'); bpy.ops.render.render(write_still=True)
    print('LOOKDEV', sc.render.filepath, flush=True)
print('KIT DONE', len(info), flush=True)
