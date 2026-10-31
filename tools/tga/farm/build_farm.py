# Farm crops for #223 (TGA). blender -b --factory-startup -P build_farm.py   -> farm.blend + out/*.fbx
# SM_Field_Plot: 4 x 4 m tilled plot, 8 ridges along X every 0.5 m (ridge tops at y = -1.75 + 0.5 k), edges fall to the
# ground; UV = world / 2 m on the tiling soil texture (T_FieldSoil). Crop patches are 1 x 1 m, two rows at y = +-0.25,
# roots at z 0.10 (the ridge top): place them at plot x/y in {-1.5, -0.5, 0.5, 1.5} -> 16 per plot, rows sit on the ridges.
# Wheat: Sown / Growing / Ripe / Harvested (stubble + a sheaf); Cabbage: Young / Ripe. Geometry crops (no alpha cards,
# Nanite-friendly), UVs into one trim sheet T_Crops (regions below). Vertex colour R = wind weight (0 at the root).
import bpy, numpy as np, math, os
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, 'out'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(223)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
# trim sheet regions (u0, u1, v0, v1) - paint_farm.py paints the same layout
R = {'stalk_g': (0.0, 0.125, 0, 1), 'stalk_y': (0.125, 0.25, 0, 1), 'head_g': (0.25, 0.375, 0, 1), 'head_y': (0.375, 0.5, 0, 1),
     'leaf_g': (0.5, 0.625, 0, 1), 'leaf_y': (0.625, 0.75, 0, 1), 'cab_out': (0.75, 1.0, 0, 0.5), 'cab_in': (0.75, 1.0, 0.5, 1.0)}
UP = np.array([0, 0, 1.0]); Z0 = 0.10
class Mesh:
    def __init__(s): s.V, s.F, s.UV = [], [], []
    def grid(s, P, A, Vv, reg, closed_tip=False):
        """P (n, m, 3) points, A/Vv (n, m) local trim coords 0..1; quads between rows i and i+1."""
        u0, u1, v0, v1 = R[reg]; n, m = P.shape[:2]; off = len(s.V); s.V += [tuple(p) for p in P.reshape(-1, 3)]
        uv = lambda i, j: (u0 + (0.03 + 0.94 * A[i, j]) * (u1 - u0), v0 + (0.03 + 0.94 * Vv[i, j]) * (v1 - v0))
        for i in range(n - 1):
            for j in range(m - 1):
                s.F.append([off + i * m + j, off + i * m + j + 1, off + (i + 1) * m + j + 1, off + (i + 1) * m + j])
                s.UV.append([uv(i, j), uv(i, j + 1), uv(i + 1, j + 1), uv(i + 1, j)])
    def build(s, name, wind=True):
        me = bpy.data.meshes.new(name); me.from_pydata(s.V, [], s.F); me.update()
        uvl = me.uv_layers.new(name='UV0'); flat = [c for f in s.UV for c in f]
        uvl.data.foreach_set('uv', np.array(flat, np.float32).ravel())
        co = np.array(s.V); w = np.clip((co[:, 2] - Z0) / 1.0, 0, 1) ** 1.3 if wind else np.zeros(len(co))
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', np.stack([w, w, w, np.ones_like(w)], 1).astype(np.float32).ravel())
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
        print('BUILT', name, sum(len(p.vertices) - 2 for p in me.polygons), flush=True); return o
def frame(d):
    d = d / np.linalg.norm(d); a = np.cross(d, UP if abs(d[2]) < 0.95 else np.array([1.0, 0, 0])); a /= np.linalg.norm(a); return a, np.cross(d, a)
def tube(m, path, rad, reg, sides=3, vrange=(0, 1)):
    n = len(path); T = np.gradient(path, axis=0); P = np.zeros((n, sides + 1, 3)); A = np.zeros((n, sides + 1)); Vv = np.zeros((n, sides + 1))
    for i in range(n):
        a, b = frame(T[i])
        for k in range(sides + 1):
            ang = 2 * math.pi * k / sides; P[i, k] = path[i] + rad[i] * (math.cos(ang) * a + math.sin(ang) * b); A[i, k] = k / sides
            Vv[i, k] = vrange[0] + (vrange[1] - vrange[0]) * i / (n - 1)
    m.grid(P, A, Vv, reg)
def stalk(m, base, H, lean, reg, segs=4, r=0.0025):
    t = np.linspace(0, 1, segs + 1)[:, None]; path = base + UP * H * t + lean * H * t ** 2
    tube(m, path, r * (1 - 0.35 * t[:, 0]), reg); return path[-1], path[-1] - path[-2]
def leaf(m, s0, d, L, W, reg, rise=0.6, droop=0.9, n=4):
    d = np.array([d[0], d[1], 0.0]); d /= np.linalg.norm(d); side = np.cross(UP, d); t = np.linspace(0, 1, n + 1)
    mid = s0 + d[None] * L * t[:, None] + UP[None] * (L * (rise * t - droop * t ** 2))[:, None]
    w = W * np.sin(np.pi * (0.08 + 0.84 * t)) ** 0.7
    P = np.stack([mid - side * w[:, None], mid + UP * (0.25 * w)[:, None], mid + side * w[:, None]], 1)
    A = np.tile([0.0, 0.5, 1.0], (n + 1, 1)); Vv = np.tile(t[:, None], (1, 3)); m.grid(P, A, Vv, reg)
def ear(m, base, d, Lh, Rh, reg, areg):
    d = d / np.linalg.norm(d); t = np.linspace(0, 1, 6); path = base + d * Lh * t[:, None]
    tube(m, path, Rh * np.sin(np.pi * (0.12 + 0.82 * t)) ** 0.6 + 0.0006, reg, sides=5)
    a, b = frame(d)
    for k in range(3):                                                   # awns: thin bristles off the top half
        p0 = base + d * Lh * (0.55 + 0.2 * k); out = (math.cos(2.1 * k) * a + math.sin(2.1 * k) * b) * 0.5 + d; out /= np.linalg.norm(out)
        p1 = p0 + out * Lh * 0.9; side = np.cross(out, a) * 0.0012
        m.grid(np.array([[p0 - side, p0 + side], [p1 - side, p1 + side]]), np.array([[0.45, 0.55], [0.45, 0.55]]), np.array([[0.9, 0.9], [1.0, 1.0]]), areg)
def cabbage(m, c, Rh, nl, open_):
    c = np.asarray(c, float); el = np.radians(np.linspace(-70, 90, 9)); az = np.linspace(0, 2 * np.pi, 13)       # the head
    P = np.zeros((9, 13, 3)); A = np.zeros((9, 13)); Vv = np.zeros((9, 13))
    for i, e in enumerate(el):
        for k, z_ in enumerate(az):
            r = Rh * (1 + 0.04 * math.sin(3 * z_ + 2 * e))
            P[i, k] = c + [r * math.cos(e) * math.cos(z_), r * math.cos(e) * math.sin(z_), Rh * 0.85 + 0.85 * r * math.sin(e)]; A[i, k] = k / 12; Vv[i, k] = i / 8
    m.grid(P, A, Vv, 'cab_in')
    for k in range(nl):                                                  # wrapper leaves, opening outward
        az0 = 2 * math.pi * k / nl + rng.normal(0, 0.2); Rl = Rh * rng.uniform(1.15, 1.35); op = open_ * rng.uniform(0.8, 1.2)
        s = np.linspace(0, 1, 7); t = np.linspace(-1, 1, 5); P = np.zeros((7, 5, 3)); A = np.zeros((7, 5)); Vv = np.zeros((7, 5))
        for i, si in enumerate(s):
            e = math.radians(-35 + si * (110 - 95 * op)); rr = Rl * (1 + 0.9 * op * si ** 1.5)
            for jj, tj in enumerate(t):
                a_ = az0 + tj * math.radians(42) * math.sin(math.pi * (0.2 + 0.8 * si)) ** 0.5
                cup = -0.25 * Rh * (1 - tj * tj) * si
                P[i, jj] = c + [(rr + cup) * math.cos(e) * math.cos(a_), (rr + cup) * math.cos(e) * math.sin(a_), Rh * 0.6 + rr * math.sin(e) * 0.8]
                A[i, jj] = (tj + 1) / 2; Vv[i, jj] = si
        m.grid(P, A, Vv, 'cab_out')
def rows(n):
    for r_ in (-0.25, 0.25):
        for _ in range(n): yield np.array([rng.uniform(-0.48, 0.48), r_ + np.clip(rng.normal(0, 0.045), -0.09, 0.09), Z0 - 0.01])
def rnd_dir():
    a = rng.uniform(0, 2 * math.pi); return np.array([math.cos(a), math.sin(a), 0.0])
WIND = np.array([1.0, 0.2, 0.0]) / math.hypot(1, 0.2)
objs = []
# ---- plot ------------------------------------------------------------------------------------------------------------
m = Mesh(); N = 81; xs = np.linspace(-2, 2, N); X, Y = np.meshgrid(xs, xs, indexing='ij')
edge = np.clip(np.minimum(2 - np.abs(X), 2 - np.abs(Y)) / 0.22, 0, 1); edge = edge * edge * (3 - 2 * edge)
Zp = (0.06 + 0.06 * np.cos(2 * np.pi * (Y + 1.75) / 0.5)) * edge + 0.012 * np.sin(X * 7.3 + Y * 3.1) * np.sin(Y * 5.7 - X * 2.3) * edge - 0.01
Zp += 0.006 * rng.standard_normal(Zp.shape) * edge
P = np.stack([X, Y, Zp], -1); m.grid(P, (X + 2) / 2, (Y + 2) / 2, 'stalk_g')          # region ignored for the plot: uv fixed below
m.UV = [[((m.V[i][0] + 2) / 2, (m.V[i][1] + 2) / 2) for i in f] for f in m.F]          # 2 m tiling UVs
objs.append(m.build('SM_Field_Plot', wind=False))
# ---- wheat -----------------------------------------------------------------------------------------------------------
m = Mesh()                                                                               # sown: fresh shoots
for b in rows(110):
    d = rnd_dir(); L = rng.uniform(0.04, 0.08)
    leaf(m, b, d, L, 0.0025, 'leaf_g', rise=2.2, droop=1.4, n=3); leaf(m, b, -d + rng.normal(0, 0.3, 3) * [1, 1, 0], L * 0.8, 0.0022, 'leaf_g', rise=2.4, droop=1.5, n=3)
objs.append(m.build('SM_Crop_Wheat_Sown'))
m = Mesh()                                                                               # growing: green stalks + leaves
for b in rows(70):
    H = rng.uniform(0.32, 0.5); lean = WIND * rng.uniform(0.02, 0.1) + rnd_dir() * 0.05
    stalk(m, b, H, lean, 'stalk_g', segs=4, r=0.0022)
    for k in range(3):
        h = H * (0.15 + 0.3 * k); s0 = b + UP * h + lean * h * (h / H)
        leaf(m, s0, rnd_dir(), rng.uniform(0.14, 0.24), 0.006, 'leaf_g', rise=0.9, droop=1.1, n=4)
objs.append(m.build('SM_Crop_Wheat_Growing'))
m = Mesh()                                                                               # ripe: golden stalks, heavy ears
for b in rows(70):
    H = rng.uniform(0.85, 1.08); lean = WIND * rng.uniform(0.04, 0.16) + rnd_dir() * 0.06
    tip, td = stalk(m, b, H, lean, 'stalk_y', segs=5, r=0.0024)
    d = td / np.linalg.norm(td) + WIND * 0.35 - UP * 0.15
    ear(m, tip, d, rng.uniform(0.07, 0.095), 0.0075, 'head_y', 'head_y')
    if rng.random() < 0.6: leaf(m, b + UP * H * 0.25, rnd_dir(), rng.uniform(0.12, 0.2), 0.005, 'leaf_y', rise=0.4, droop=1.2, n=3)
objs.append(m.build('SM_Crop_Wheat_Ripe'))
m = Mesh()                                                                               # harvested: stubble, straw, one sheaf
for b in rows(70): stalk(m, b, rng.uniform(0.07, 0.14), rnd_dir() * 0.15, 'stalk_y', segs=1, r=0.0024)
for _ in range(24):
    p = np.array([rng.uniform(-0.45, 0.45), rng.uniform(-0.45, 0.45), Z0 - 0.04 + 0.05 * rng.random()]); d = rnd_dir() + UP * 0.05
    tube(m, np.stack([p, p + d * 0.12, p + d * 0.25]), np.full(3, 0.002), 'stalk_y')
c = np.array([0.05, 0.0, Z0 - 0.02])
for k in range(50):                                                      # sheaf: stalks gathered at a band 0.45 m up
    a = 2 * math.pi * k / 50 + rng.normal(0, 0.05); r0 = rng.uniform(0.09, 0.15); r1 = 0.045 * math.sqrt(rng.random()); r2 = rng.uniform(0.08, 0.2)
    p0 = c + [r0 * math.cos(a), r0 * math.sin(a), 0]; p1 = c + [r1 * math.cos(a), r1 * math.sin(a), 0.45]; p2 = c + [r2 * math.cos(a), r2 * math.sin(a), rng.uniform(0.85, 1.0)]
    path = np.array([p0 + (p1 - p0) * t if t <= 1 else p1 + (p2 - p1) * (t - 1) for t in np.linspace(0, 2, 7)])
    tube(m, path, np.full(7, 0.0024), 'stalk_y'); ear(m, p2, p2 - p1, rng.uniform(0.07, 0.09), 0.007, 'head_y', 'head_y')
band = np.array([c + [0.05 * math.cos(a), 0.05 * math.sin(a), 0.45] for a in np.linspace(0, 2 * math.pi, 17)])
tube(m, band, np.full(17, 0.012), 'stalk_y', sides=5)
objs.append(m.build('SM_Crop_Wheat_Harvested'))
# ---- cabbage ---------------------------------------------------------------------------------------------------------
for name, Rh, nl, op in (('SM_Crop_Cabbage_Young', 0.045, 5, 0.8), ('SM_Crop_Cabbage_Ripe', 0.105, 7, 0.45)):
    m = Mesh()
    for x in (-0.25, 0.25):
        for y in (-0.25, 0.25): cabbage(m, (x + rng.normal(0, 0.03), y + rng.normal(0, 0.02), Z0 - 0.03), Rh * rng.uniform(0.9, 1.1), nl, op)
    objs.append(m.build(name))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'farm.blend'))
for o in objs:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    o.data.materials.append(bpy.data.materials.new('M_FieldSoil' if o.name == 'SM_Field_Plot' else 'M_Crops'))
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='LINEAR', apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
print('EXPORT OK', flush=True)
