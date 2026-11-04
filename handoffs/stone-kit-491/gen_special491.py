# #491 specials (i9 11-04): walls that get kit blocks lose their old mesh (hidden collider), so their `special[]` parts
# (cap = walk/top, soffit, closer) are rebuilt here as SHARP rbox stones, one mesh per wall: SM_K491S_<wall>, pivot =
# the wall pivot (placed with the old actor's transform). Caps are split along their long axis into 0.6-1.0 m coping
# stones. Fold check per mesh (must be inverted 0). Run: blender -b -P gen_special491.py
import sys, os, json, random, zlib
sys.path.insert(0, 'C:/Users/hossa/sync58/tunnel')
import bpy, bmesh, numpy as np
from mathutils import Vector
import gen_boxmason as GB

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = 'C:/Users/hossa/sync58/tunnel/kit491_special_fbx'; os.makedirs(OUT, exist_ok=True)
J2 = GB.JOINT / 2
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
mats = [bpy.data.materials.new('M_Tun_Ashlar'), bpy.data.materials.new('M_Tun_Mortar')]

def foldcheck(me):   # per loose part: every face normal must point away from its part's centre
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); seen = set(); bad = zero = 0
    for f in bm.faces:
        if f.index in seen: continue
        stack, comp = [f], []
        while stack:
            g = stack.pop()
            if g.index in seen: continue
            seen.add(g.index); comp.append(g)
            stack += [h for e in g.edges for h in e.link_faces if h.index not in seen]
        c = sum((v.co for v in {v for g in comp for v in g.verts}), Vector()) / len({v for g in comp for v in g.verts})
        for g in comp:
            if g.calc_area() < 1e-9: zero += 1
            elif g.normal.dot(g.calc_center_median() - c) < 0: bad += 1
    n = len(bm.faces); bm.free(); return n, bad, zero

RETRY = [0]
def stone(B, c, h):
    """rbox into a scratch buffer, fold-check that stone alone, re-roll (new random draws) until clean, then append.
    Thin caps (0.2 m) get corner chips deeper than the slab, which fold it (re-rolls never fix that), so a thin axis is
    built at 0.19 m half size (like the kit blocks) and squashed back: an axis scale keeps every face pointing out."""
    hs = Vector([max(h[i], 0.19) for i in range(3)]); k = Vector([h[i] / hs[i] for i in range(3)])
    for _ in range(10):
        T = GB.Buf(); GB.rbox(T, Vector((0, 0, 0)), hs, tone=0.5)
        T.v = [Vector((p.x * k.x + c.x, p.y * k.y + c.y, p.z * k.z + c.z)) for p in T.v]
        v = np.array([tuple(p) for p in T.v]); cen = v.mean(axis=0)
        bad = 0
        for f in T.f:
            p = v[list(f)]; n = np.cross(p[1] - p[0], p[2] - p[0])
            if np.linalg.norm(n) > 1e-12 and np.dot(n, p.mean(axis=0) - cen) < 0: bad += 1
        if bad == 0: break
        RETRY[0] += 1
    o = len(B.v)
    B.v += T.v; B.uv += T.uv; B.col += T.col; B.mat += T.mat; B.f += [tuple(i + o for i in f) for f in T.f]

info, lines = [], []
for f in ('curtain', 'keep', 'mason2'):
    for w in json.load(open(os.path.join(HERE, 'layout', f + '_specs_layout.json')))['walls']:
        if not w['blocks'] or not w.get('special'): continue
        random.seed(zlib.crc32(w['name'].encode()))
        B = GB.Buf()
        for s in w['special']:
            c = Vector(s['centre'])
            if 'size_m' in s: sz = Vector(s['size_m'])
            else:   # closer: len along its face, kit depth 0.38 into the wall
                sz = Vector((s['len_m'], 0.38, s['h_m'])) if s['face'][-1] == 'y' else Vector((0.38, s['len_m'], s['h_m']))
            ax = 0 if sz.x >= sz.y else 1
            if s['role'] == 'cap' or sz[ax] > 1.2:   # caps + long soffits: a run of 0.6-1.0 m stones
                for a, b in GB.runs(c[ax] - sz[ax] / 2, c[ax] + sz[ax] / 2, 0.6, 1.0):
                    cc, hh = c.copy(), sz / 2 - Vector((J2, J2, J2))
                    cc[ax] = (a + b) / 2; hh[ax] = (b - a) / 2 - J2
                    stone(B, cc, hh)
            else:
                stone(B, c, sz / 2 - Vector((J2, J2, J2)))
        name = 'SM_K491S_' + w['name'].replace('SM_', '', 1)
        me = bpy.data.meshes.new(name)
        me.from_pydata([(p.x, -p.y, p.z) for p in B.v], [], B.f)
        for m in mats: me.materials.append(m)
        me.polygons.foreach_set('material_index', B.mat)
        lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
        me.uv_layers.new(name='UV0').data.foreach_set('uv', np.asarray(B.uv, dtype=np.float32)[lv].ravel())
        me.attributes.new('Col', 'FLOAT_COLOR', 'CORNER').data.foreach_set('color', np.clip(np.asarray(B.col, dtype=np.float32), 0, 1)[lv].ravel())
        me.flip_normals()
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
        me.shade_smooth()
        n, bad, zero = foldcheck(me)
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath='%s/%s.fbx' % (OUT, name), use_selection=True, mesh_smooth_type='FACE', add_leaf_bones=False,
                                 bake_anim=False, axis_forward='-Z', axis_up='Y', apply_scale_options='FBX_SCALE_NONE', colors_type='LINEAR')
        info.append({'name': name, 'wall': w['name'], 'specs': f, 'faces': n, 'inverted': bad, 'zero_area': zero})
        lines.append('%s faces %d inverted %d zero-area %d' % (name, n, bad, zero))
lines.append('FOLDCHECK special meshes %d inverted %d zero-area %d' % (len(info), sum(i['inverted'] for i in info), sum(i['zero_area'] for i in info)))
print(lines[-1], 'rerolled stones', RETRY[0], flush=True)
open(os.path.join(HERE, 'foldcheck_special491.txt'), 'w').write('\n'.join(lines) + '\n')
json.dump(info, open(OUT + '/special_built.json', 'w'), indent=1)
