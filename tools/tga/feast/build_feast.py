# Feast set for #227 (TGA). blender -b --factory-startup -P build_feast.py   -> feast.blend + out/*.fbx
# SM_Feast_Table: 3 m trestle table laid for a feast (linen runner, a roast on a board, bread, a cheese wheel, a bowl of
# apples, pewter plates + tankards, three candles); SM_Feast_TableBare: the same table cleared; SM_Feast_Bench: 3 m bench;
# SM_Feast_Torch: 1.9 m standing torch (iron basket, pitch head, emissive flame). One 4K atlas (bake_feast.py).
# Reuses the timber / log / slab / splinter helpers of tools/tga/siege/build_siege.py (everything above its ram section).
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__))
SIEGE = os.environ.get('SIEGE', os.path.join(D, '..', 'siege', 'build_siege.py'))
src = open(SIEGE, encoding='utf-8').read(); exec(src[:src.index('# ---- battering ram')])
rng = np.random.default_rng(227)
KIND.update({'bread': 5.0, 'meat': 6.0, 'cheese': 7.0, 'apple': 8.0, 'pewter': 9.0, 'cloth': 10.0, 'pitch': 11.0})
def blob(c, r, kind, n=12, bumps=0.0, rot=0.0):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=n * 2, v_segments=n, radius=1.0)
    for v in bm.verts:
        p = v.co.copy(); s = 1 + bumps * math.sin(p.x * 7 + p.y * 5) * math.sin(p.z * 6 + p.x * 3)
        x, y = p.x * r[0] * s, p.y * r[1] * s; v.co = Vector((c[0] + x * math.cos(rot) - y * math.sin(rot), c[1] + x * math.sin(rot) + y * math.cos(rot), c[2] + p.z * r[2] * s))
    return add_mesh(bm, kind)
def disc(c, r, h, kind, seg=20): return log(Vector(c), Vector(c) + Vector((0, 0, h)), r, kind=kind, seg=seg)
NAMES = ['SM_Feast_Table', 'SM_Feast_TableBare', 'SM_Feast_Bench', 'SM_Feast_Torch']; OFF = [0.0, 0.0, 0.0, 0.0]
TOP = 0.78
def table(X):
    for k in range(4): timber((X - 1.5, -0.33 + 0.22 * k, TOP - 0.025 + j(0.002)), (X + 1.5, -0.33 + 0.22 * k + j(0.003), TOP - 0.025), 0.215, 0.05, tilt=0.01)
    for sx in (-1.15, 1.15):                                             # trestles: splayed legs, top bearer, foot
        timber((X + sx, -0.42, TOP - 0.08), (X + sx, 0.42, TOP - 0.08), 0.09, 0.07)
        for sy in (-1, 1): timber((X + sx, sy * 0.12, TOP - 0.1), (X + sx, sy * 0.3, 0.04), 0.07, 0.07)
        timber((X + sx, -0.4, 0.04), (X + sx, 0.4, 0.04), 0.08, 0.06)
    timber((X - 1.15, 0, 0.32), (X + 1.15, 0, 0.32), 0.07, 0.09)           # stretcher
    for sx in (-1.25, 1.25): log((X + sx - 0.06, 0, 0.32), (X + sx + 0.06, 0, 0.32), 0.02)   # wedges through the stretcher
# ---- laid table --------------------------------------------------------------------------------------------------------
SEG[0] = 0; X = OFF[0]; table(X); T = TOP + 0.002
slab((X, 0, T + 0.004), (1, 0, 0), (0, 1, 0), 2.7, 0.42, 0.005, kind='cloth', sag=0.0)          # linen runner
disc((X, 0.02, T + 0.008), 0.24, 0.03, 'wood', 24)                                                # carving board + roast
blob((X, 0.02, T + 0.09), (0.17, 0.11, 0.07), 'meat', 16, bumps=0.06)
for s_ in (-1, 1):
    blob((X + 0.06 * s_, 0.1 * s_, T + 0.075), (0.07, 0.045, 0.04), 'meat', 10, bumps=0.05, rot=0.6 * s_)
    log((X + 0.11 * s_, 0.14 * s_, T + 0.08), (X + 0.16 * s_, 0.19 * s_, T + 0.09), 0.009, kind='bread')            # bone ends
for k, (bx, by) in enumerate(((-0.55, 0.05), (-0.75, -0.06), (0.62, 0.04), (0.82, -0.05))):     # bread loaves
    blob((X + bx, by, T + 0.045), (0.12, 0.075, 0.05), 'bread', 12, bumps=0.04, rot=rng.uniform(-0.5, 0.5))
disc((X - 1.1, 0.0, T + 0.008), 0.13, 0.085, 'cheese', 24)                                      # cheese wheel + a wedge
blob((X - 0.92, 0.07, T + 0.03), (0.05, 0.03, 0.025), 'cheese', 6)
disc((X + 1.1, 0.0, T + 0.008), 0.13, 0.05, 'wood', 20)                                         # bowl of apples
for k in range(7):
    a = 2 * math.pi * k / 6; r_ = 0.0 if k == 6 else 0.07
    blob((X + 1.1 + r_ * math.cos(a), r_ * math.sin(a), T + 0.09 + (0.04 if k == 6 else 0)), (0.036, 0.036, 0.033), 'apple', 10)
for k in range(8):                                                                               # places: plate + tankard
    px = X - 1.2 + (k // 2) * 0.8; sy = -1 if k % 2 else 1
    disc((px, sy * 0.33, T + 0.002), 0.105, 0.012, 'pewter', 20)
    tx, ty = px + 0.17, sy * 0.25
    disc((tx, ty, T + 0.002), 0.042, 0.13, 'pewter', 16); disc((tx, ty, T + 0.13), 0.046, 0.012, 'pewter', 16)
    timber((tx + 0.045, ty, T + 0.11), (tx + 0.075, ty, T + 0.07), 0.012, 0.02, kind='pewter'); timber((tx + 0.075, ty, T + 0.07), (tx + 0.045, ty, T + 0.03), 0.012, 0.02, kind='pewter')
for cx in (-0.32, 0.32, -1.38):                                                                  # candles
    disc((X + cx, -0.05, T + 0.008), 0.05, 0.015, 'pewter'); disc((X + cx, -0.05, T + 0.02), 0.012, 0.06, 'pewter', 10)
    disc((X + cx, -0.05, T + 0.08), 0.017, 0.14 + j(0.02), 'wax', 12)
    blob((X + cx, -0.05, T + 0.255), (0.008, 0.008, 0.022), 'flame', 8)
# ---- bare table / bench / torch ---------------------------------------------------------------------------------------
SEG[0] = 1; table(OFF[1])
SEG[0] = 2
for k in range(2): timber((-1.5, -0.075 + 0.15 * k, 0.43), (1.5, -0.075 + 0.15 * k + j(0.003), 0.43), 0.15, 0.05, tilt=0.01)
for sx in (-1.2, 1.2):
    timber((sx, -0.14, 0.4), (sx, 0.14, 0.4), 0.07, 0.06)
    for sy in (-1, 1): timber((sx, sy * 0.06, 0.39), (sx, sy * 0.2, 0.03), 0.06, 0.06)
timber((-1.2, 0, 0.2), (1.2, 0, 0.2), 0.05, 0.07)
SEG[0] = 3
log((0, 0, 0.25), (0, 0, 1.62), 0.035)                                                          # pole + tripod
for k in range(3):
    a = 2 * math.pi * k / 3; timber((0.03 * math.cos(a), 0.03 * math.sin(a), 0.42), (0.38 * math.cos(a), 0.38 * math.sin(a), 0.02), 0.05, 0.05)
log((0, 0, 0.36), (0, 0, 0.46), 0.05, kind='iron')                                               # iron collar
for k in range(6):                                                                               # iron basket
    a = 2 * math.pi * k / 6; timber((0.03 * math.cos(a), 0.03 * math.sin(a), 1.58), (0.11 * math.cos(a), 0.11 * math.sin(a), 1.82), 0.012, 0.012, kind='iron')
for z_, r_ in ((1.66, 0.06), (1.8, 0.105)):
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        timber((r_ * math.cos(a0), r_ * math.sin(a0), z_), (r_ * math.cos(a1), r_ * math.sin(a1), z_), 0.012, 0.014, kind='iron')
blob((0, 0, 1.72), (0.08, 0.08, 0.11), 'pitch', 12, bumps=0.12)                                 # pitch-soaked rag head
blob((0, 0, 1.92), (0.075, 0.07, 0.17), 'flame', 12, bumps=0.18)                                 # flame (emissive)
blob((0.02, -0.01, 2.04), (0.035, 0.035, 0.09), 'flame', 8, bumps=0.2)
# ---- atlas -------------------------------------------------------------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = 'SM_FeastAtlas'
seg = np.empty(len(ob.data.vertices), np.int32); ob.data.attributes['seg'].data.foreach_get('value', seg)
SHIFT = {0: (0, 0), 1: (0, 2.0), 2: (0, -1.0), 3: (2.3, -1.0)}                                   # spread out for the AO bake
for v in ob.data.vertices: v.co.x += SHIFT[seg[v.index]][0]; v.co.y += SHIFT[seg[v.index]][1]
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.002)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
for k, name in enumerate(NAMES):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-SHIFT[k][0], -SHIFT[k][1], 0)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
    print('SEG', name, sum(len(p.vertices) - 2 for p in c.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'feast.blend'))
os.makedirs(os.path.join(D, 'out'), exist_ok=True)
for n in NAMES:
    bpy.ops.object.select_all(action='DESELECT'); o = bpy.data.objects[n]; o.select_set(True); bpy.context.view_layer.objects.active = o
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get('M_Feast') or bpy.data.materials.new('M_Feast'))
    bpy.ops.export_scene.fbx(filepath=os.path.join(D, 'out', n + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'feast.blend')); print('EXPORT OK', flush=True)
