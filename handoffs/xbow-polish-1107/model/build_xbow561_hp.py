# #561 pass 3: the same crossbow as a ~2M-tri HIGH poly (real carved, hammered, grained detail) baked onto a ~10k-tri LOW
# poly game mesh, the AAA way. checkking (Claude), 2026-11-07. Materials + helpers come from build_xbow561.py (pass 2).
#   blender -b --factory-startup -P build_xbow561_hp.py -- <out_dir> --stage high            -> xbow561_high.blend
#   blender -b --factory-startup -P build_xbow561_hp.py -- <out_dir> --stage bake [2048]     -> xbow561_low.blend, SM_Crossbow561.fbx,
#                                                                                               T_Crossbow561M_BaseColor/ORM/Normal.png
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]; STAGE = args[args.index('--stage') + 1]
SIZE = next((int(a) for a in args[1:] if a.isdigit()), 2048)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'laptop2', 'retex_lib'))
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange
if STAGE == 'bake': bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'xbow561_high.blend'))
else: bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
SRC = open(os.path.join(HERE, 'build_xbow561.py'), encoding='utf-8').read()
A, B = '# ---------------------------------------------------------------- helpers', '# ---------------------------------------------------------------- materials'
C = '# ---------------------------------------------------------------- geometry'
exec(SRC[SRC.index(A):SRC.index(B)], globals())                       # rrect, catmull, loft, tube, rounded_box, cyl
if STAGE == 'high': exec(SRC[SRC.index(B):SRC.index(C)], globals())    # M_WOOD, M_BONE, M_STEEL, M_BRASS, M_CORD, M_NUT
log = lambda *a: print('XBOW561HP', *a, flush=True)

def densify(pts, n):
    """resample a closed polygon to exactly n points, evenly by arc length (same count on every ring of a loft)"""
    if not n: return pts
    P = np.array(pts + [pts[0]], float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, cum[-1], n, endpoint=False); x = np.interp(t, cum, P[:, 0]); y = np.interp(t, cum, P[:, 1])
    return list(zip(x.tolist(), y.tolist()))
def to_coll(objs, name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    for o in objs:
        for u in list(o.users_collection): u.objects.unlink(o)
        c.objects.link(o)
def displace(ob, kind, size, strength, stretch=None, rot=None, mid=0.5):
    t = bpy.data.textures.new(ob.name + kind, kind)
    if kind == 'WOOD': t.wood_type = 'RINGNOISE'; t.noise_basis_2 = 'SIN'; t.turbulence = 4.0; t.noise_scale = size
    elif kind == 'VORONOI': t.noise_scale = size; t.distance_metric = 'DISTANCE'
    else: t.noise_scale = size; t.noise_depth = 2
    m = ob.modifiers.new(kind, 'DISPLACE'); m.texture = t; m.strength = strength; m.mid_level = mid
    if stretch:
        e = bpy.data.objects.new(ob.name + '_tx', None); sc.collection.objects.link(e); e.scale = stretch
        if rot: e.rotation_euler = rot
        m.texture_coords = 'OBJECT'; m.texture_coords_object = e
    else:
        m.texture_coords = 'LOCAL'
def subdiv(ob, lv):
    if lv: m = ob.modifiers.new('sub', 'SUBSURF'); m.levels = lv; m.render_levels = lv; m.subdivision_type = 'CATMULL_CLARK'
def apply_all(ob):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)

# ------------------------------------------------------------ shared design (metres; X forward, Z up; origin = nut)
ST = [(-0.430, 0.032, 0.088, -0.044, 0.012), (-0.424, 0.038, 0.104, -0.045, 0.015), (-0.385, 0.043, 0.110, -0.043, 0.018),
      (-0.310, 0.042, 0.090, -0.032, 0.017), (-0.210, 0.038, 0.064, -0.016, 0.015), (-0.120, 0.034, 0.047, -0.006, 0.013),
      (-0.050, 0.037, 0.048, -0.005, 0.010), (0.000, 0.044, 0.054, -0.004, 0.010), (0.050, 0.041, 0.047, -0.004, 0.009),
      (0.150, 0.032, 0.036, -0.002, 0.010), (0.230, 0.036, 0.042, -0.001, 0.010), (0.285, 0.042, 0.048, -0.002, 0.009),
      (0.315, 0.040, 0.044, -0.003, 0.010), (0.322, 0.032, 0.036, -0.003, 0.010)]
STF = catmull(ST, 32)
def stock_at(x):
    for a, b in zip(STF, STF[1:]):
        if a[0] <= x <= b[0]:
            t = (x - a[0]) / max(b[0] - a[0], 1e-9); return tuple(a[k] + (b[k] - a[k]) * t for k in range(5))
    return STF[0] if x < STF[0][0] else STF[-1]
PX, PZ, SPAN = 0.272, 0.010, 0.335
NUTZ = stock_at(0.0)[3] + stock_at(0.0)[2] / 2 - 0.004
CATCH = Vector((0.009, 0, NUTZ + 0.019))
TIP = [Vector((PX - 0.055 - 0.004, s * (SPAN - 0.006), PZ)) for s in (1, -1)]
def scroll(xs, zs):           # the engraving, same formula as the Staghorn shader (coords / 0.022 m)
    fx = xs - np.floor(xs) - 0.5; fz = (zs + 0.5) - np.floor(zs + 0.5) - 0.5
    r2 = np.sqrt(fx * fx + fz * fz); ang = np.arctan2(fz, fx); jit = 7.0 + 1.5 * np.sin(xs * 1.7) * np.cos(zs * 2.3)
    sp = (r2 * jit + ang * 0.159) % 1.0
    ss = lambda e0, e1, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - e0) / (e1 - e0), 0, 1))
    return ss(0.38, 0.45, np.abs(sp - 0.5)) * ss(0.48, 0.40, r2)

def build(H, mats):
    """H = True: high poly; False: low poly game mesh. mats = dict of materials (low uses one for everything)."""
    W, BO, ST_, BR, CO, NU = (mats[k] for k in ('wood', 'bone', 'steel', 'brass', 'cord', 'nut'))
    made = []
    def keep(o): made.append(o); return o
    # stock (+ 2.5 mm bolt groove forward of the nut on the high; the low gets it from the normal map)
    fr = []
    for x, w, h, zc, r in (STF if H else catmull(ST, 3)):
        sec = densify(rrect(w, h, r, 12 if H else 3), 176 if H else 0)
        if H and 0.02 < x < 0.31:
            g = min(1.0, (x - 0.02) / 0.01, (0.31 - x) / 0.01)
            sec = [(a, b - 0.0025 * g * max(0.0, 1 - (abs(a) / 0.0045) ** 2) if b > h / 2 - 0.004 else b) for a, b in sec]
        fr.append((Vector((x, 0, zc)), Vector((0, 1, 0)), Vector((0, 0, 1)), sec))
    st = keep(loft('Stock', fr, W))
    if H:
        subdiv(st, 1)
        displace(st, 'WOOD', 0.6, 0.00008, stretch=(0.004, 0.004, 0.06), rot=(0, math.pi / 2, 0))    # growth rings along the stock
        displace(st, 'CLOUDS', 0.5, 0.00018, stretch=(0.10, 0.05, 0.05))                              # hand-shaped, not CNC-perfect
        # staghorn inlay: a carved grid flush on the stock sides (0.5 mm proud, 0.45 mm deep engraving)
        for side in (1, -1):
            nx, nz = 1100, 170; xs = np.linspace(-0.355, -0.065, nx); bm = bmesh.new(); grid = []
            for i, x in enumerate(xs):
                _, w, h, zc, r = stock_at(x); ph = h * 0.52; zz = zc + np.linspace(-ph / 2, ph / 2, nz)
                u = np.minimum(np.minimum(i, nx - 1 - i) / 6.0, 1.0)
                v = np.minimum(np.minimum(np.arange(nz), nz - 1 - np.arange(nz)) / 6.0, 1.0)
                proud = 0.0005 * np.minimum(u, v) ** 0.5
                carve = 0.00045 * scroll(np.full(nz, x / 0.022), zz / 0.022) * np.minimum(u, v)
                yy = side * (w / 2 + proud - carve - 0.0001)
                grid.append([bm.verts.new((x, float(yy[k]), float(zz[k]))) for k in range(nz)])
            for i in range(nx - 1):
                for k in range(nz - 1):
                    f = (grid[i][k], grid[i + 1][k], grid[i + 1][k + 1], grid[i][k + 1]); bm.faces.new(f if side < 0 else f[::-1])
            me = bpy.data.meshes.new('Inlay'); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new('Inlay%+d' % side, me)
            sc.collection.objects.link(ob); me.materials.append(BO)
            for p in me.polygons: p.use_smooth = True
            keep(ob)
            for x in [i * 0.03 - 0.345 for i in range(10)]:        # domed brass rivets, hammered
                _, w, h, zc, r = stock_at(x)
                for dz in (h * 0.30, -h * 0.30):
                    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.0026, location=(x, side * (w / 2 + 0.0005), zc + dz))
                    rv = bpy.context.object; rv.scale = (1, 0.45, 1); bpy.ops.object.transform_apply(scale=True); rv.data.materials.append(BR)
                    bpy.ops.object.shade_smooth(); keep(rv)
    # prod
    pf = []; NP = 321 if H else 41
    for i in range(NP):
        y = -SPAN + 2 * SPAN * i / (NP - 1); t = abs(y) / SPAN
        x = PX - 0.055 * t ** 1.7; dx = -0.055 * 1.7 * t ** 0.7 * (1 if y >= 0 else -1) / SPAN
        tan = Vector((dx, 1, 0)).normalized(); nrm = Vector((tan.y, -tan.x, 0))
        th, hh = 0.0145 - 0.0060 * t, 0.034 - 0.015 * t
        pf.append((Vector((x, y, PZ)), nrm, Vector((0, 0, 1)), densify(rrect(th, hh, 0.0028, 8 if H else 2), 72 if H else 0)))
    pr = keep(loft('Prod', pf, ST_))
    if H: subdiv(pr, 1); displace(pr, 'VORONOI', 0.006, 0.00022)                   # hammer marks from forging
    # nut + side plates (+ pins on the high)
    keep(cyl('Nut', 0.0155, 0.032, (0, 0, NUTZ), NU, rot=(math.pi / 2, 0, 0), verts=64 if H else 14))
    for s in (1, -1):
        keep(rounded_box('NutFinger%+d' % s, (0.008, 0.007, 0.012), (0.004, s * 0.008, NUTZ + 0.016), NU, 0.002 if H else 0.0005))
        keep(rounded_box('NutPlate%+d' % s, (0.050, 0.0016, 0.026), (0.0, s * 0.0228, NUTZ - 0.006), ST_, 0.0006 if H else 0.0003))
        if H: keep(cyl('NutPin%+d' % s, 0.0035, 0.002, (0, s * 0.0238, NUTZ), BR, rot=(math.pi / 2, 0, 0), verts=32))
    # string: high = 3 twisted strands; low = one tube around them
    for k, tip in enumerate(TIP):
        L = (CATCH - tip).length; d = (CATCH - tip).normalized(); u = d.cross(Vector((0, 0, 1))).normalized(); v = d.cross(u)
        if H:
            N = 700
            for strand in range(3):
                pts = [tip.lerp(CATCH, i / N) + (u * math.cos(a) + v * math.sin(a)) * 0.0011
                       for i in range(N + 1) for a in [2 * math.pi * (L * i / N) / 0.009 + strand * 2 * math.pi / 3]]
                keep(tube('String%d_%d' % (k, strand), pts, 0.00115, CO, sides=10))
        else:
            keep(tube('String%d' % k, [tip.lerp(CATCH, i / 6) for i in range(7)], 0.0021, CO, sides=6))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.0085, minor_radius=0.0016 if H else 0.0022, major_segments=48 if H else 10,
                                         minor_segments=12 if H else 4, location=tip, rotation=(0, math.pi / 2, 0))
        lp = bpy.context.object; lp.data.materials.append(CO); bpy.ops.object.shade_smooth(); keep(lp)
    # bridle: 6 wraps + 2 crossed loops; high = 2-strand twisted cord, low = plain tube
    def cord(name, centre_fn, n):
        if H:
            base = [centre_fn(j / n) for j in range(n + 1)]
            for sd in range(2):
                pts = []
                for j, p in enumerate(base):
                    t = (base[min(j + 1, n)] - base[max(j - 1, 0)]).normalized(); a0 = t.cross(Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))).normalized()
                    b0 = t.cross(a0); a = 2 * math.pi * j * (base[1] - base[0]).length / 0.005 + sd * math.pi
                    pts.append(p + (a0 * math.cos(a) + b0 * math.sin(a)) * 0.0009)
                keep(tube(name + 's%d' % sd, pts, 0.0010, CO, sides=8, closed=True))
        else:
            keep(tube(name, [centre_fn(j / 16) for j in range(17)], 0.0019, CO, sides=5, closed=True))
    for i in range(6):
        x = 0.243 + i * 0.0085; _, w, h, zc, r = stock_at(x)
        cord('Bridle%d' % i, lambda f, x=x, w=w, h=h, zc=zc: Vector((x, (w / 2 + 0.0016) * math.cos(2 * math.pi * f), zc + (h / 2 + 0.0016) * math.sin(2 * math.pi * f))), 160)
    for s in (1, -1):
        R = Matrix.Rotation(s * math.radians(38), 3, 'Z')
        cord('BridleX%+d' % s, lambda f, R=R: Vector((PX, 0, PZ)) + R @ Vector((0, 0.034 * math.cos(2 * math.pi * f), 0.030 * math.sin(2 * math.pi * f))), 160)
    # stirrup, straps, front plate
    sp = [(0.300, 0.024, 0.0), (0.335, 0.048, -0.004), (0.380, 0.058, -0.010), (0.425, 0.045, -0.014), (0.445, 0.0, -0.016),
          (0.425, -0.045, -0.014), (0.380, -0.058, -0.010), (0.335, -0.048, -0.004), (0.300, -0.024, 0.0)]
    stp = keep(tube('Stirrup', catmull(sp, 48 if H else 4), 0.0058, ST_, sides=28 if H else 8,
                    radius_fn=lambda t: 0.0058 if 0.15 < t < 0.85 else 0.0048))
    if H: displace(stp, 'VORONOI', 0.006, 0.0002)
    for s in (1, -1):
        keep(rounded_box('StirrupStrap%+d' % s, (0.040, 0.003, 0.014), (0.290, s * 0.0215, -0.002), ST_, 0.0008 if H else 0.0004))
        if H: keep(cyl('StirrupRivet%+d' % s, 0.0032, 0.004, (0.282, s * 0.0235, -0.002), BR, rot=(math.pi / 2, 0, 0), verts=32))
    keep(rounded_box('HeadPlate', (0.004, 0.036, 0.040), (0.322, 0, -0.003), ST_, 0.0012 if H else 0.0006))
    # trigger
    tp = [(0.004, 0, -0.026), (-0.020, 0, -0.040), (-0.080, 0, -0.050), (-0.160, 0, -0.056), (-0.240, 0, -0.058), (-0.262, 0, -0.054)]
    pts = catmull(tp, 40 if H else 4); fr = []
    for i, p in enumerate(pts):
        p = Vector(p); t = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        nz = Vector((0, 1, 0)).cross(t).normalized(); f = i / (len(pts) - 1)
        fr.append((p, Vector((0, 1, 0)), nz, rrect(0.0085 - 0.002 * f, 0.0065, 0.0022, 6 if H else 2)))
    tr = keep(loft('Trigger', fr, ST_))
    if H: displace(tr, 'VORONOI', 0.006, 0.00015)
    keep(cyl('TriggerPin', 0.0028, 0.044, (0.0, 0, -0.024), ST_, rot=(math.pi / 2, 0, 0), verts=32 if H else 8))
    keep(rounded_box('TriggerSlot', (0.030, 0.012, 0.004), (-0.01, 0, -0.030), ST_, 0.001 if H else 0.0004))
    return made

def join(objs, name):
    for o in objs: apply_all(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); ob = bpy.context.object; ob.name = name
    for e in [o for o in sc.objects if o.type == 'EMPTY']: bpy.data.objects.remove(e)
    return ob
tris = lambda ob: sum(len(p.vertices) - 2 for p in ob.data.polygons)

if STAGE == 'high':
    hi = join(build(True, dict(wood=M_WOOD, bone=M_BONE, steel=M_STEEL, brass=M_BRASS, cord=M_CORD, nut=M_NUT)), 'SM_Crossbow561')
    log('HIGH tris', tris(hi), 'size', tuple(round(d, 3) for d in hi.dimensions))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'xbow561_high.blend')); log('saved high')

if STAGE == 'bake':
    hi = bpy.data.objects['SM_Crossbow561']; hi.name = 'HIGH'
    M_LOW = bpy.data.materials.new('M_Crossbow561'); M_LOW.use_nodes = True
    lo = join(build(False, {k: M_LOW for k in ('wood', 'bone', 'steel', 'brass', 'cord', 'nut')}), 'SM_Crossbow561')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=1e-6)
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True); bpy.ops.object.mode_set(mode='OBJECT')
    log('LOW tris', tris(lo), '| HIGH tris', tris(hi))
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
    bk = sc.render.bake; bk.use_selected_to_active = True; bk.use_cage = False; bk.cage_extrusion = 0.003; bk.max_ray_distance = 0.009; bk.margin = 8
    imgs = {k: bpy.data.images.new('bake_' + k, SIZE, SIZE, alpha=False, float_buffer=(k == 'N')) for k in ('BC', 'RG', 'MT', 'AO', 'N')}
    imgs['BC'].colorspace_settings.name = 'sRGB'
    for k in ('RG', 'MT', 'AO', 'N'): imgs[k].colorspace_settings.name = 'Non-Color'
    nt = M_LOW.node_tree; tn = nt.nodes.new('ShaderNodeTexImage'); nt.nodes.active = tn
    def route(key):
        for m in hi.data.materials:
            n = m.node_tree; out = n.nodes['OUT']
            if key == 'BSDF': n.links.new(n.nodes['BSDF'].outputs[0], out.inputs['Surface'])
            else: em = n.nodes['EMIT']; n.links.new(n.nodes['OUT_' + key].outputs[0], em.inputs['Color']); n.links.new(em.outputs[0], out.inputs['Surface'])
    bpy.ops.object.select_all(action='DESELECT'); hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    for key in ('BC', 'RG', 'MT', 'AO'):
        route(key); tn.image = imgs[key]; bpy.ops.object.bake(type='EMIT'); log('baked', key)
    route('BSDF'); tn.image = imgs['N']; bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT'); log('baked N')
    def px(im): a = np.empty(SIZE * SIZE * 4, np.float32); im.pixels.foreach_get(a); return a.reshape(SIZE, SIZE, 4)
    def write(arr, name, cs='Non-Color'):
        im = bpy.data.images.new(name, SIZE, SIZE, alpha=False); im.colorspace_settings.name = cs
        im.pixels.foreach_set(np.ascontiguousarray(arr, np.float32).ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'; im.save()
    bc = px(imgs['BC']); orm = np.ones((SIZE, SIZE, 4), np.float32); orm[..., 0] = px(imgs['AO'])[..., 0]; orm[..., 1] = px(imgs['RG'])[..., 0]
    mt = np.clip((px(imgs['MT'])[..., 0] - 0.45) / 0.1, 0.0, 1.0); orm[..., 2] = mt
    lin = np.where(bc[..., :3] <= 0.04045, bc[..., :3] / 12.92, ((bc[..., :3] + 0.055) / 1.055) ** 2.4)
    Y = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32); k = np.where((mt > 0.5) & (Y < 0.456), 0.456 / np.maximum(Y, 1e-4), 1.0)
    lin = np.clip(lin * k[..., None], 0, 1); bc[..., :3] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    write(bc, 'T_Crossbow561M_BaseColor', 'sRGB'); write(orm, 'T_Crossbow561M_ORM'); write(px(imgs['N']), 'T_Crossbow561M_Normal')
    bpy.data.objects.remove(hi); nt.nodes.remove(tn)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'xbow561_low.blend'))
    bpy.ops.object.select_all(action='DESELECT'); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_Crossbow561.fbx'), use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             axis_forward='X', axis_up='Z', mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, bake_space_transform=True)
    log('DONE', OUT)
