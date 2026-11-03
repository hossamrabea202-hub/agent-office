# i5 2026-11-02, card #447: one watertight game-ready stone stair per flight, low poly baked from a high poly.
#   blender -b --factory-startup -P build_stair.py -- build  <spec.json> <outdir>
#   blender -b --factory-startup -P build_stair.py -- bake   <spec.json> <outdir> [size=4096] [gpu=1]
# build: low poly (closed manifold, 2 slots: Tread / Body, hard edges = UV seams, UV0 unique) + high poly (voxel remesh of
#        the low, then real masonry by displacement: 1.5 cm mortar joints, per-stone bulge, worn nosings with a foot path).
#        Writes <name>_low.fbx, <name>.blend, a manifold report.
# bake:  normal (16-bit, MikkTSpace, cage), AO, masks (R joint, G foot-wear, B stone tone) -> <name>_N.png, <name>_M.png
#        (M: R=AO G=joint B=wear A=stone tone). Raw float buffers are not kept (bake hygiene, KNOWLEDGE_LOG 10-30).
# Space: cm in the spec, metres in Blender. UE +Y = Blender -Y, so the stair is built at Blender y in [-width, 0].
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
STAGE, SPEC, OUT = argv[0], json.load(open(argv[1])), argv[2]
NAME = SPEC['name']
os.makedirs(OUT, exist_ok=True)
CM = 0.01


def profile(s):
    """Side profile of the flight in XZ (cm): sawtooth treads on top, sloped soffit underneath, solid pier at the top."""
    n, run, rise = s['steps'], s['run'], s['rise']
    pts = [(0.0, 0.0)]
    for k in range(n):
        pts += [(k * run, (k + 1) * rise), ((k + 1) * run, (k + 1) * rise)]
    L = n * run
    if s.get('solid'):                                   # #301 kit flights: filled to the ground, no soffit
        return pts + [(L, 0.0)]
    pier = s['pier_x']
    t = s['soffit_t']
    sb = lambda x: rise / run * x - t
    pts += [(L, 0.0), (pier, 0.0), (pier, sb(pier))]
    x0 = t * run / rise
    pts += [(x0, 0.0)]
    return pts


def prism(bm, pts, y0, y1):
    """Extrude a closed XZ polygon between Blender y0 and y1 into a closed prism."""
    a = [bm.verts.new((x * CM, y0 * CM, z * CM)) for x, z in pts]
    b = [bm.verts.new((x * CM, y1 * CM, z * CM)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    m = len(pts)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((a[i], a[j], b[j], b[i]))


def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_low(s):
    W = s['width']
    bm = bmesh.new()
    prism(bm, profile(s), 0.0, -W)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    low = new_obj(NAME + '_low', bm)
    pp = s.get('parapet')
    if pp:
        bm2 = bmesh.new()
        top = lambda x: s['rise'] / s['run'] * x + s['rise'] + pp['above']
        poly = [(pp['x0'], 0.0), (pp['x0'], top(pp['x0'])), (s['steps'] * s['run'], top(s['steps'] * s['run'])), (s['steps'] * s['run'], 0.0)]
        prism(bm2, poly, -(W - 2.0), -(W + pp['thick']))
        bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
        par = new_obj(NAME + '_parapet', bm2)
        mod = low.modifiers.new('union', 'BOOLEAN')
        mod.operation, mod.solver, mod.object = 'UNION', 'EXACT', par
        bpy.context.view_layer.objects.active = low
        bpy.ops.object.modifier_apply(modifier='union')
        bpy.data.objects.remove(par)
    bm = bmesh.new(); bm.from_mesh(low.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(low.data); bm.free()
    return low


def finish_low(low, s):
    me = low.data
    # two material slots: tread / landing tops of the flight, everything else
    for nm in ('MI_StairBaked_Tread', 'MI_StairBaked_Body'):
        me.materials.append(bpy.data.materials.get(nm) or bpy.data.materials.new(nm))
    W = s['width']
    for p in me.polygons:
        c = p.center
        p.material_index = 0 if (p.normal.z > 0.9 and c.y > -W * CM - 0.001) else 1
    # triangulate now: the baked tangent space must be the exported one
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free()
    # every edge sharper than 30 deg is hard; UV seams on the same edges
    bm = bmesh.new(); bm.from_mesh(me)
    for e in bm.edges:
        hard = len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(30)
        e.smooth = not hard
        e.seam = hard
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    bpy.context.view_layer.objects.active = low
    for o in bpy.context.selected_objects:
        o.select_set(False)
    low.select_set(True)
    me.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.004)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')


def manifold_report(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bad = [e for e in bm.edges if not e.is_manifold]
    r = {'verts': len(bm.verts), 'tris': sum(len(f.verts) - 2 for f in bm.faces), 'non_manifold_edges': len(bad),
         'watertight': len(bad) == 0, 'volume_m3': round(bm.calc_volume(signed=True), 3)}
    bm.free()
    return r


# ---------- high poly ----------
def stone_rng(*key):
    return random.Random(hash(key) & 0xffffffff)


def splits(length, lo, hi, *key):
    """Random stone joints along a length (cm), seeded, running-bond friendly."""
    r = stone_rng(*key)
    out, x = [], r.uniform(0, lo)
    while x < length:
        out.append(x)
        x += r.uniform(lo, hi)
    return out


def joint_d(u, js):
    return min((abs(u - j) for j in js), default=1e9)


def vnoise(x, y, z, seed=0):
    """Smooth value noise in [-1, 1] (trilinear over hashed lattice)."""
    xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - xi, y - yi, z - zi
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    def h(a, b, c):
        n = (a * 73856093) ^ (b * 19349663) ^ (c * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177 & 0xffffffff
        return (n / 0xffffffff) * 2 - 1
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                acc += w * h(xi + dx, yi + dy, zi + dz)
    return acc


def courses(length, key):
    """Course boundaries (cm) with varied heights, like real coursed ashlar (28-46 cm)."""
    r = stone_rng('courses', *key)
    out, z = [0.0], 0.0
    while z < length:
        z += r.uniform(28, 46)
        out.append(z)
    return out


def build_high(low, s):
    hi = low.copy(); hi.data = low.data.copy(); hi.name = NAME + '_high'
    bpy.context.scene.collection.objects.link(hi)
    hi.data.materials.clear()
    vox = s.get('voxel_cm', 1.5) * CM
    m = hi.modifiers.new('remesh', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = vox; m.adaptivity = 0.0
    bpy.context.view_layer.objects.active = hi
    bpy.ops.object.modifier_apply(modifier='remesh')
    # nearest low face gives the surface frame for the masonry pattern
    lbm = bmesh.new(); lbm.from_mesh(low.data); lbm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(lbm)
    run, rise, n, W = s['run'], s['rise'], s['steps'], s['width']
    tread_js = {k: splits(W, 55, 105, 'tread', k) for k in range(n + 1)}
    # sharp edges of each low triangle (for chips and edge rounding)
    sharp = {}
    for f in lbm.faces:
        sharp[f.index] = [(e.verts[0].co / CM, e.verts[1].co / CM) for e in f.edges
                          if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(30)]
    cz = courses(2000, ('side',))
    cy = courses(400, ('soffit',))
    import bisect

    def seg_d(p, a, b):
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        return (p - (a + ab * t)).length
    me = hi.data
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    disp = []
    for v in me.vertices:
        p = v.co / CM
        loc, nrm, fi, dist = bvh.find_nearest(v.co)
        nx, ny, nz = abs(nrm.x), abs(nrm.y), abs(nrm.z)
        x, y, z = p.x, -p.y, p.z          # UE-style local: y across the width (0..W), x up the flight
        k = max(0, min(n - 1, int(x // run)))
        wear = 0.0
        if nz > 0.9 and nrm.z > 0 and y <= W + 0.5:          # tread top: joints across the width, worn nosing path
            js = tread_js[k]; ju = joint_d(y, js)
            sid = (k, sum(1 for j in js if j < y))
            front = x - k * run                               # 0 at the nosing
            path = math.exp(-((y - W * 0.5) / (W * 0.22)) ** 2)
            wear = path * max(0.0, 1.0 - front / (run * 0.8))
        elif nx > 0.9 and z > rise / run * x - 2:             # risers: the tread stones continue down
            kk = max(0, min(n - 1, int(round(z / rise)) - 1))
            js = tread_js[kk]; ju = joint_d(y, js); sid = (kk, sum(1 for j in js if j < y))
        else:                                                 # sides, pier ends, soffit, parapet: coursed ashlar
            if ny > 0.5:
                u, vv, cc, tag = x, z, cz, 'side'
            elif nx > 0.9:
                u, vv, cc, tag = y, z, cz, 'end'
            else:
                a = math.atan2(rise, run)
                u, vv, cc, tag = x * math.cos(a) + z * math.sin(a), y, cy, 'soffit'
            c = max(0, bisect.bisect_right(cc, vv) - 1)
            js = splits(n * run + 400, 40, 110, 'course', c, tag)
            ju = min(abs(vv - cc[c]), abs(vv - cc[min(c + 1, len(cc) - 1)]), joint_d(u, js))
            sid = (c, sum(1 for j in js if j < u), tag)
        r = stone_rng(*sid)
        joint = max(0.0, 1.0 - ju / 1.1)                      # 1.5 cm joint, rounded shoulders
        joint = joint * joint * (3 - 2 * joint)
        # hand-dressed face: per-stone tilt/bulge + tooling noise (wavelengths >= 4 cm: under Nyquist for the bake)
        seed = r.randint(0, 9999)
        bulge = r.uniform(-0.35, 0.35) + 0.15 * vnoise(p.x / 9, p.y / 9, p.z / 9, seed) + 0.06 * vnoise(p.x / 4, p.y / 4, p.z / 4, seed + 1)
        # chips along stone edges and the low's hard edges
        ed = min((seg_d(p, a, b) for a, b in sharp.get(fi, [])), default=99.0)
        edge = max(0.0, 1.0 - ed / 3.0)
        near = max(edge, max(0.0, 1.0 - ju / 3.5) * (1 - joint))
        chip = 0.0
        if near > 0:
            cn = vnoise(p.x / 2.5, p.y / 2.5, p.z / 2.5, 7)
            chip = max(0.0, cn - 0.35) * 2.2 * near            # sparse dents up to ~1.4 cm
        round_off = 0.9 * edge * edge                          # extra rounding on the outer arrises
        d = -1.1 * joint + (0 if joint > 0.5 else bulge) - 1.4 * wear - chip - round_off
        disp.append(d)
        col.data[v.index].color = (joint, wear, r.random(), 1.0)
    for v, d in zip(me.vertices, disp):
        loc, nrm, fi, dist = bvh.find_nearest(v.co)
        v.co = v.co + nrm * (d * CM)
    lbm.free()
    hi.modifiers.new('smooth', 'CORRECTIVE_SMOOTH').iterations = 2
    bpy.ops.object.modifier_apply(modifier='smooth')
    # smooth shading: a flat-shaded high bakes its voxel facets into the normal map
    me.shade_smooth()
    return hi


if STAGE == 'build':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    low = build_low(SPEC)
    finish_low(low, SPEC)
    rep = manifold_report(low)
    high = build_high(low, SPEC)
    rep['high_tris'] = sum(len(p.vertices) - 2 for p in high.data.polygons)
    json.dump(rep, open(os.path.join(OUT, NAME + '_report.json'), 'w'), indent=1)
    print('REPORT', json.dumps(rep))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + '.blend'))
    for o in bpy.context.selected_objects:
        o.select_set(False)
    low.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, NAME + '_low.fbx'), use_selection=True, mesh_smooth_type='OFF',
                             use_tspace=True, add_leaf_bones=False, bake_space_transform=False, apply_unit_scale=True,
                             object_types={'MESH'}, use_mesh_modifiers=True)
    print('BUILD OK', NAME)

if STAGE == 'bake':
    size = int(argv[3]) if len(argv) > 3 else 4096
    gpu = (argv[4] != '0') if len(argv) > 4 else True
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, NAME + '.blend'))
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    if gpu:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for t in ('OPTIX', 'CUDA'):
            try:
                prefs.compute_device_type = t; prefs.get_devices()
                if any(d.type == t for d in prefs.devices):
                    for d in prefs.devices: d.use = d.type == t
                    sc.cycles.device = 'GPU'; break
            except Exception:
                pass
    low, high = bpy.data.objects[NAME + '_low'], bpy.data.objects[NAME + '_high']
    # emission material on the high reads the mask colours
    hm = bpy.data.materials.new('HighMask'); hm.use_nodes = True
    nt = hm.node_tree; nt.nodes.clear()
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'Col'
    e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs[0], o.inputs[0])
    high.data.materials.clear(); high.data.materials.append(hm)
    imgs = {}
    for key, float_buf in (('N', True), ('AO', False), ('MK', False)):
        imgs[key] = bpy.data.images.new(NAME + '_' + key, size, size, alpha=False, float_buffer=float_buf)
        imgs[key].colorspace_settings.name = 'Non-Color'
    for mat in low.data.materials:
        mat.use_nodes = True
        tn = mat.node_tree.nodes.get('BakeTarget') or mat.node_tree.nodes.new('ShaderNodeTexImage')
        tn.name = 'BakeTarget'; mat.node_tree.nodes.active = tn
    def bake(kind, img, samples):
        for mat in low.data.materials:
            mat.node_tree.nodes['BakeTarget'].image = img
        sc.cycles.samples = samples
        for ob in sc.objects: ob.select_set(False)
        high.select_set(True); low.select_set(True); bpy.context.view_layer.objects.active = low
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=0.025, max_ray_distance=0.06,
                            normal_space='TANGENT', margin=16, margin_type='EXTEND')
        print('baked', kind)
    bake('NORMAL', imgs['N'], 8)
    bake('AO', imgs['AO'], 64)
    bake('EMIT', imgs['MK'], 4)
    # save: normal 16-bit PNG (OpenGL green, UE flips on import with flip_green), packed masks RGBA 8-bit
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.render.image_settings.color_mode = 'RGB'
    imgs['N'].save_render(os.path.join(OUT, NAME + '_N.png'), scene=sc)
    import numpy as np
    ao = np.array(imgs['AO'].pixels[:]).reshape(size, size, 4)
    mk = np.array(imgs['MK'].pixels[:]).reshape(size, size, 4)
    packed = np.stack([ao[..., 0], mk[..., 0], mk[..., 1], mk[..., 2]], axis=-1)
    pm = bpy.data.images.new(NAME + '_M', size, size, alpha=True)
    pm.colorspace_settings.name = 'Non-Color'
    pm.pixels[:] = packed.ravel()
    sc.render.image_settings.color_depth = '8'; sc.render.image_settings.color_mode = 'RGBA'
    pm.save_render(os.path.join(OUT, NAME + '_M.png'), scene=sc)
    print('BAKE OK', NAME, size)
