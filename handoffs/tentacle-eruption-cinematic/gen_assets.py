# #545 assets (adjustedfilm, 2026-11-06). blender -b --factory-startup -P gen_assets.py -- <out dir>
# fbx/SM_EruptDome.fbx: 70 m ground disc, vertex alpha = bulge weight, rises through the terrain by WPO.
# fbx/SM_EruptSlab_S|M|L.fbx: thrown rock slabs, closed solids for Fracture Mode, vertex colour + UV0 like the spore base.
# tex/T_EruptCrack_BC|N|ORM|Mask.png: 2048 crack decal. Mask R = crack opacity, G = reveal order from the centre (0 opens first).
import bpy, bmesh, sys, os, math, numpy as np
OUT = sys.argv[sys.argv.index('--') + 1]; os.makedirs(os.path.join(OUT, 'fbx'), exist_ok=True); os.makedirs(os.path.join(OUT, 'tex'), exist_ok=True); rng = np.random.default_rng(545)
P_ = rng.permutation(4096); G_ = rng.random(4096)
def vn(x, y, z=0.0):
    x, y = np.asarray(x, float), np.asarray(y, float); z = np.broadcast_to(z, x.shape).astype(float); i, j, k = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int); u, v, w = x - i, y - j, z - k; u, v, w = u * u * (3 - 2 * u), v * v * (3 - 2 * v), w * w * (3 - 2 * w)
    h = lambda a, b, c: G_[P_[(P_[(P_[a & 4095] + b) & 4095] + c) & 4095]]
    return ((h(i, j, k) * (1 - u) + h(i + 1, j, k) * u) * (1 - v) + (h(i, j + 1, k) * (1 - u) + h(i + 1, j + 1, k) * u) * v) * (1 - w) + ((h(i, j, k + 1) * (1 - u) + h(i + 1, j, k + 1) * u) * (1 - v) + (h(i, j + 1, k + 1) * (1 - u) + h(i + 1, j + 1, k + 1) * u) * v) * w
def fbm(x, y, z=0.0, o=5):
    t, a, tot = 0.0, 1.0, 0.0
    for _ in range(o): t = t + a * (vn(x, y, z) - 0.5); tot += a; x, y, z = x * 2.03 + 17.3, y * 2.03 + 9.1, np.asarray(z) * 2.03 + 3.7; a *= 0.5
    return t / tot * 2
sstep = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))
s2l = lambda c: np.where(np.asarray(c, float) / 255 <= 0.04045, np.asarray(c, float) / 255 / 12.92, ((np.asarray(c, float) / 255 + 0.055) / 1.055) ** 2.4)
def build(name, V, F, C, R, path):
    bpy.ops.wm.read_factory_settings(use_empty=True); me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel()); me.loops.add(F.size); me.polygons.add(len(F)); me.loops.foreach_set('vertex_index', F.astype(np.int32).ravel()); me.polygons.foreach_set('loop_start', np.arange(len(F), dtype=np.int32) * F.shape[1]); me.update(); me.validate(verbose=False)
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); col.data.foreach_set('color', np.column_stack([np.clip(C, 0, 1), R]).astype(np.float32).ravel())
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv); P = V[lv] / 100.0; fn = np.empty(len(me.polygons) * 3, np.float32); me.polygons.foreach_get('normal', fn); dom = np.repeat(np.argmax(np.abs(fn.reshape(-1, 3)), 1), F.shape[1]); uv = np.where(dom[:, None] == 2, P[:, [0, 1]], np.where(dom[:, None] == 0, P[:, [1, 2]], P[:, [0, 2]])) / 5.0; me.uv_layers.new(name='UV0').data.foreach_set('uv', uv.astype(np.float32).ravel())
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool)); me.set_sharp_from_angle(angle=math.radians(50)); me.update(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    nz = np.empty(len(me.polygons) * 3, np.float32); me.polygons.foreach_get('normal', nz); ctr = np.empty(len(me.polygons) * 3, np.float32); me.polygons.foreach_get('center', ctr); out = float(((ctr.reshape(-1, 3) - ctr.reshape(-1, 3).mean(0)) * nz.reshape(-1, 3)).sum(1).mean())
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', bake_anim=False, add_leaf_bones=False, colors_type='SRGB'); print('ASSET', name, 'verts', len(V), 'faces', len(F), 'up share %.2f' % float((nz.reshape(-1, 3)[:, 2] > 0).mean()), 'outward %.1f' % out)
# ---- dome: faces up, alpha 1 at the centre, 0 at the rim; the rim stays under the terrain
NR, NA = 90, 256; rr = np.linspace(0.02, 1, NR) * 3500.0; th = np.linspace(0, 2 * math.pi, NA, endpoint=False); T, R_ = np.meshgrid(th, rr); X, Y = R_ * np.cos(T), R_ * np.sin(T); u = R_ / 3500.0; W = (1 - sstep(0.1, 1.0, u)) * (0.75 + 0.5 * fbm(X * 0.002, Y * 0.002, 3.0, 3)); W = np.clip(W, 0, 1) * (u < 0.98)
Z = -30.0 + 22.0 * fbm(X * 0.006, Y * 0.006, 1.0, 4) * (1 - u); V = np.stack([X, Y, Z], -1).reshape(-1, 3); q = np.arange(NR * NA).reshape(NR, NA); F = np.stack([q[1:, :].ravel(), q[1:, np.r_[1:NA, 0]].ravel(), q[:-1, np.r_[1:NA, 0]].ravel(), q[:-1, :].ravel()], 1)
nn = fbm(X * 0.01, Y * 0.01, 2.0, 4); C = s2l([70, 58, 45]) * (1 + 0.4 * nn)[..., None]; build('SM_EruptDome', V, F, C.reshape(-1, 3), W.ravel(), os.path.join(OUT, 'fbx', 'SM_EruptDome.fbx'))
# ---- slabs: broken plates, closed; the top keeps a skin of soil where they were the ground
for nm, L, Wd, Th, sd in (('S', 420.0, 300.0, 90.0, 1), ('M', 900.0, 620.0, 170.0, 2), ('L', 1700.0, 1100.0, 280.0, 3)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=26, use_grid_fill=True); bm.verts.ensure_lookup_table(); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); n = len(bm.verts); P = np.array([v.co[:] for v in bm.verts]) * np.array([L, Wd, Th]); Fq = np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free()
    for _ in range(9):
        d = rng.normal(size=3); d /= np.linalg.norm(d); dist = (0.16 + 0.22 * rng.random()) * L if abs(d[0]) > 0.5 else (0.25 + 0.2 * rng.random()) * max(Wd, Th * 2); o = P @ d - dist; P = P - np.where(o > 0, o, 0)[:, None] * d
    z_ = sd * 11.0; am = 0.035 * L; P = P + am * np.stack([fbm(P[:, 1] * 2 / L, P[:, 2] * 2 / L, z_, 4), fbm(P[:, 0] * 2 / L, P[:, 2] * 2 / L, z_ + 1, 4), fbm(P[:, 0] * 2 / L, P[:, 1] * 2 / L, z_ + 2, 4)], 1) + 14.0 * np.stack([fbm(P[:, 1] * 0.02, P[:, 2] * 0.02, z_ + 3, 3), fbm(P[:, 0] * 0.02, P[:, 2] * 0.02, z_ + 4, 3), fbm(P[:, 0] * 0.02, P[:, 1] * 0.02, z_ + 5, 3)], 1)
    n3 = fbm(P[:, 0] * 0.006, P[:, 1] * 0.006, P[:, 2] * 0.006, 4); band = 0.5 + 0.5 * np.sin(P[:, 2] * 0.09 + 2.0 * n3); C = s2l([112, 104, 93]) * (1 + 0.32 * n3 + 0.24 * band - 0.12)[:, None]; top = sstep(0.1, 0.42, P[:, 2] / Th)[:, None]; C = C * (1 - top) + s2l([74, 60, 46]) * (1 + 0.35 * n3)[:, None] * top
    build('SM_EruptSlab_' + nm, P, Fq, C, np.clip(0.88 + 0.1 * n3, 0.5, 1.0), os.path.join(OUT, 'fbx', 'SM_EruptSlab_%s.fbx' % nm))
# ---- crack decal: radial fissures that branch outward; the reveal runs from the centre along the cracks
N = 2048; yy, xx = np.mgrid[0:N, 0:N]; X, Y = (xx - N / 2 + 0.5) / (N / 2), (yy - N / 2 + 0.5) / (N / 2); wx, wy = X + 0.06 * fbm(X * 3, Y * 3, 4.0, 3), Y + 0.06 * fbm(X * 3, Y * 3, 7.0, 3); R_ = np.hypot(wx, wy); A_ = np.arctan2(wy, wx); F1 = np.full(X.shape, 9.0); F2 = np.full(X.shape, 9.0)
sr = 0.06 + 1.05 * rng.random(170) ** 0.8; sa = rng.random(170) * 2 * math.pi
for r0, a0 in zip(sr, sa):
    da = (A_ - a0 + math.pi) % (2 * math.pi) - math.pi; d = np.hypot((R_ - r0) / (1.0 + 3.0 * np.clip(R_, 0, 1)), da * np.maximum(R_, 0.05)); near = d < F1; F2 = np.where(near, F1, np.minimum(F2, d)); F1 = np.minimum(F1, d)
edge = F2 - F1; width = 0.0015 + 0.011 * (1 - np.clip(R_, 0, 1)) ** 1.6; crack = 1 - sstep(width * 0.5, width * 1.6, edge + 0.003 * fbm(X * 22, Y * 22, 9.0, 3)); rim = 1 - sstep(0.86, 0.99, R_); opacity = np.clip(crack * rim, 0, 1); halo = (1 - sstep(width, width * 7, edge)) * rim
depth = np.clip(crack, 0, 1); h = -depth + 0.25 * fbm(X * 40, Y * 40, 1.0, 4) + 0.5 * halo * (1 - depth); gx, gy = np.gradient(h); st = 18.0; nx, ny = -gx * st, -gy * st; nz = np.ones_like(nx); ln = np.sqrt(nx * nx + ny * ny + nz * nz); NRM = np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5], -1)
n1 = fbm(X * 9, Y * 9, 5.0, 5); BC = s2l([60, 50, 41]) * (1 + 0.3 * n1)[..., None] * (1 - 0.42 * depth)[..., None]; ROUGH = np.clip(0.88 + 0.14 * n1 - 0.12 * depth, 0.4, 1.0); REVEAL = np.clip(R_ + 0.05 * fbm(X * 7, Y * 7, 8.0, 3), 0, 1)
def save(name, rgb, srgb):
    im = bpy.data.images.new(name, N, N, alpha=False, float_buffer=False); im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'; o = np.ones((N, N, 4), np.float32); o[..., :3] = rgb; im.pixels.foreach_set(o.ravel()); im.filepath_raw = os.path.join(OUT, 'tex', name + '.png'); im.file_format = 'PNG'; im.save(); print('TEX', name, 'mean', np.round(rgb.mean((0, 1)), 3))
bpy.ops.wm.read_factory_settings(use_empty=True); save('T_EruptCrack_BC', np.where(np.clip(BC, 0, 1) <= 0.0031308, 12.92 * np.clip(BC, 0, 1), 1.055 * np.clip(BC, 1e-6, 1) ** (1 / 2.4) - 0.055), True)      # byte images store sRGB values directly; save('T_EruptCrack_N', NRM, False); save('T_EruptCrack_ORM', np.stack([1 - 0.5 * depth, ROUGH, np.zeros_like(ROUGH)], -1), False); save('T_EruptCrack_Mask', np.stack([opacity, REVEAL, np.zeros_like(ROUGH)], -1), False)
print('ASSETS DONE')
