# Wall-section breach collapse (#327 for #316, TGA). blender -b --factory-startup -P build_breach.py  -> breach.blend (env WORK)
# SK_WallBreach: a 6 m wide x 7 m high x 2.4 m thick castle wall section (pivot bottom centre, OUTER face toward +X): ashlar
# facing courses (outer + inner) over a rubble core. An irregular hole (stepped along the courses, like real masonry
# failing) collapses: its ashlar blocks, some split half-blocks, core lumps and mortar crumbs (~36 chunks) are blasted inward
# (-X) by a kinematic kick, simulated with Blender rigid bodies (high damping + sleeping so everything settles and stays),
# baked, and converted to ONE skinned mesh with one bone per chunk + bone 'Frame' for the standing wall.
# Materials: M_WallStone = the castle's world-aligned wall stone on the dressed faces, M_WallFracture = fresh broken stone on
# the core and every fracture face. SM_Rubble_Masonry_01..06: static piles of cut blocks / half-blocks for dressing.
import bpy, bmesh, numpy as np, math, os, random
from mathutils import Vector, Matrix, Euler
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(327); FPS, FRAMES = 30, 75                     # 2.5 s
W, H, T, FACE = 6.0, 7.0, 2.4, 0.6                                  # section size, facing depth
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, FRAMES
def mat(n): return bpy.data.materials.get(n) or bpy.data.materials.new(n)
STONE, FRAC = mat('M_WallStone'), mat('M_WallFracture')
def act(o):
    for x in list(sc.objects):
        if x is not None: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
def block(name, c, s, bev=0.025, outer_axis=None):
    """bevelled ashlar block centred at c, size s; faces normal to +-X get STONE (dressed), others FRAC if outer_axis=='broken'."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2]))
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, segments=2, affect='EDGES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    me.materials.append(STONE); me.materials.append(FRAC); o.location = c
    rough(o, 0.012); return o
def rough(o, amp, seed=0):
    me = o.data; r = random.Random(hash(o.name) & 0xffff)
    for v in me.vertices: v.co += Vector((r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-amp, amp)))
def split(o, n_axis, frac_mat=1):
    """cut a block in two by a tilted plane; the two halves get FRAC on the cut. returns [a, b]"""
    out = []
    for keep in (0, 1):
        c = o.copy(); c.data = o.data.copy(); sc.collection.objects.link(c); c.name = o.name + ('a' if keep == 0 else 'b')
        bm = bmesh.new(); bm.from_mesh(c.data); nrm = Vector(n_axis).normalized()
        r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=nrm if keep else -nrm, clear_outer=True)
        edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        f = bmesh.ops.edgeloop_fill(bm, edges=edges)['faces'] if edges else []
        for ff in f: ff.material_index = frac_mat
        bmesh.ops.scale(bm, vec=(0.97, 0.97, 0.97), verts=bm.verts)   # a hair of gap: no overlap at rest
        bm.to_mesh(c.data); bm.free(); out.append(c)
    bpy.data.objects.remove(o); return out

# ---------------- courses ----------------
CH = 0.55; rows = int(H / CH); rowh = H / rows
hole = []                                                           # (row, y0, y1): the breach outline, stepped on courses
for r in range(rows):
    z = (r + 0.5) * rowh
    if 0.25 < z < 4.6:
        half = 1.35 * math.sin(math.pi * min(1, (z + 0.6) / 5.8)) ** 0.6 + rnd.uniform(-0.25, 0.25)
        cy = rnd.uniform(-0.15, 0.15); hole.append((r, cy - half, cy + half))
holed = {r: (a, b) for r, a, b in hole}
frame_parts, chunks = [], []
for side, xc in (('O', T / 2 - FACE / 2), ('I', -T / 2 + FACE / 2)):
    for r in range(rows):
        y = -W / 2 + (0.0 if r % 2 == 0 else -0.45); z = (r + 0.5) * rowh
        while y < W / 2:
            L = rnd.uniform(0.75, 1.15); y0, y1 = max(y, -W / 2), min(y + L, W / 2); y = y + L
            if y1 - y0 < 0.12: continue
            c = Vector((xc, (y0 + y1) / 2, z)); s = (FACE - 0.04, y1 - y0 - 0.04, rowh - 0.04)
            ins = r in holed and holed[r][0] < (y0 + y1) / 2 < holed[r][1]
            b = block('%s_%d_%.1f' % (side, r, y0), c, s)
            if ins and side == 'I' and z > 4.2: ins = False         # the inner face holds a little higher: ragged arch
            (chunks if ins else frame_parts).append(b)
# split ~1/4 of the falling blocks into broken halves (fresh fracture faces)
for b in list(chunks):
    if rnd.random() < 0.2:
        chunks.remove(b); chunks += split(b, (rnd.uniform(-0.3, 0.3), rnd.uniform(0.6, 1.0), rnd.uniform(-0.4, 0.4)))
# rubble core: full box minus the hole prism (frame), plus core lumps inside the hole
core = bpy.data.meshes.new('core'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * (T - 2 * FACE), v.co.y * W, (v.co.z + 0.5) * H))
bm.to_mesh(core); bm.free(); co = bpy.data.objects.new('Core', core); sc.collection.objects.link(co); core.materials.append(STONE); core.materials.append(FRAC)
for p in co.data.polygons: p.material_index = 1
cut = bpy.data.meshes.new('cut'); bm = bmesh.new()
for r, a, b_ in hole:                                               # one box per course: stepped prism
    z0, z1 = r * rowh, (r + 1) * rowh
    vs = [bm.verts.new((x, y, z)) for x in (-T, T) for y in (a, b_) for z in (z0 - 0.001, z1 + 0.001)]
    bmesh.ops.convex_hull(bm, input=vs)
bm.to_mesh(cut); bm.free(); cu = bpy.data.objects.new('Cut', cut); sc.collection.objects.link(cu)
act(co); m = co.modifiers.new('b', 'BOOLEAN'); m.object = cu; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; bpy.ops.object.modifier_apply(modifier='b')
for p in co.data.polygons: p.material_index = 1
frame_parts.append(co)
for r, a, b_ in hole[::3]:                                          # core lumps: two per three courses
    for k in range(2):
        y0 = a + (b_ - a) * k / 2; y1 = a + (b_ - a) * (k + 1) / 2; z0 = r * rowh
        lump = block('Core_%d_%d' % (r, k), Vector((0, (y0 + y1) / 2, z0 + rowh / 2)), (T - 2 * FACE - 0.1, y1 - y0 - 0.1, rowh - 0.1), bev=0.06)
        for p in lump.data.polygons: p.material_index = 1
        rough(lump, 0.02); chunks.append(lump)
bpy.data.objects.remove(cu)
for k in range(4):                                                  # mortar crumbs
    r_ = hole[min(len(hole) - 1, 1 + 3 * (k // 2))][0]; a, b_ = holed[r_]; z = (r_ + 0.5) * rowh      # core courses without a lump
    c = block('Crumb_%d' % k, Vector((rnd.uniform(-0.4, 0.4), a + (b_ - a) * (0.3 + 0.4 * (k % 2)), z)), (0.18, 0.22, 0.14), bev=0.03)
    for p in c.data.polygons: p.material_index = 1
    rough(c, 0.025); chunks.append(c)
for o in chunks + frame_parts:
    act(o); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
print('CHUNKS', len(chunks), 'FRAME parts', len(frame_parts), flush=True)

# ---------------- art-directed ballistic collapse (deterministic; replaces a rigid-body sim that kept exploding) ----------------
# Each chunk: launched inward (-X) after a short stagger (inner face + core first, outer face 2 frames later), flies a
# parabola while tumbling, lands on its own non-overlapping spot 2-10 m inside (higher chunks fly farther), makes one small
# bounce + slide, then lies still on its flattest face. Nothing ends in the air; everything is still by 2.5 s.
G_ = 9.81; placed = []; samples = {}
def ease(u): return u * u * (3 - 2 * u)
for o in sorted(chunks, key=lambda c: -c.location.z):
    p0 = o.location.copy(); dims = sorted(o.dimensions); hz = dims[0] / 2            # lie on the flattest face
    reach = 1.5 + 6.5 * min(1.0, p0.z / 5.0) * rnd.uniform(0.7, 1.0)
    for tries in range(200):
        pf = Vector((-T / 2 - reach + rnd.uniform(-0.8, 0.8), p0.y * 1.5 + rnd.uniform(-1.2, 1.2), hz))
        r_ = dims[2] / 2 * 0.9
        if all((pf.xy - q.xy).length > r_ + rq for q, rq in placed): break
        reach += 0.15
    placed.append((pf, r_))
    ax = [0, 1, 2]; d_ = list(o.dimensions); flat = d_.index(min(d_))                  # final: flattest axis up, random yaw
    up = {0: Euler((0, math.pi / 2, 0)), 1: Euler((math.pi / 2, 0, 0)), 2: Euler((0, 0, 0))}[flat]
    qf = (Euler((0, 0, rnd.uniform(0, 6.28))).to_quaternion() @ up.to_quaternion() @ Euler((rnd.uniform(-.06, .06), rnd.uniform(-.06, .06), 0)).to_quaternion())
    outer = o.name.startswith('O_'); t0 = (0.07 if outer else 0.0) + rnd.uniform(0.0, 0.06) + 0.04 * (1 - p0.z / H)
    vz = rnd.uniform(1.0, 3.0); dz = pf.z - p0.z
    tf = (vz + math.sqrt(vz * vz - 2 * G_ * dz)) / G_                                   # time to fall onto the landing height
    spin_ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.3, .3))).normalized(); spin = rnd.uniform(2.5, 7.0)
    hop = Vector((-rnd.uniform(0.2, 0.5), rnd.uniform(-0.2, 0.2), 0)); thop = 0.28; hh = rnd.uniform(0.08, 0.2)
    seq = []
    for f in range(1, FRAMES + 1):
        t = (f - 1) / FPS - t0
        if t <= 0: M = Matrix.Translation(p0)
        elif t < tf:
            u = t / tf; xy = p0.xy.lerp(pf.xy, u); z = p0.z + vz * t - 0.5 * G_ * t * t
            q = qf @ __import__('mathutils').Quaternion(spin_ax, spin * (1 - u))
            M = Matrix.Translation(Vector((xy.x, xy.y, max(z, hz)))) @ q.to_matrix().to_4x4()
        elif t < tf + thop:
            u = (t - tf) / thop; pos = pf + hop * ease(u); pos.z = hz + hh * math.sin(math.pi * u)
            q = qf @ __import__('mathutils').Quaternion(spin_ax, 0.25 * math.sin(math.pi * u))
            M = Matrix.Translation(pos) @ q.to_matrix().to_4x4()
        else: M = Matrix.Translation(pf + hop) @ qf.to_matrix().to_4x4()
        seq.append(M)
    samples[o.name] = seq
moves = [(samples[n][-1].translation - samples[n][-11].translation).length for n in samples]
fin = [samples[n][-1].translation for n in samples]
print('SETTLE max move last 10 frames %.3f m | max final height %.2f m | final x min/max %.1f/%.1f' % (
    max(moves), max(v.z for v in fin), min(v.x for v in fin), max(v.x for v in fin)), flush=True)
for o in chunks: o.matrix_world = samples[o.name][0]                 # rest = frame 1 (the standing wall)
arm_d = bpy.data.armatures.new('SK_WallBreach_Skeleton'); arm = bpy.data.objects.new('SK_WallBreach_Rig', arm_d); sc.collection.objects.link(arm)
act(arm); bpy.ops.object.mode_set(mode='EDIT')
def eb(name, head, parent=None):
    b = arm_d.edit_bones.new(name); b.head = head; b.tail = head + Vector((0, 0, 0.25)); b.parent = parent; return b
root = eb('Root', Vector((0, 0, 0))); eb('Frame', Vector((0, 0, 0.3)), root)
bones = {}
for i, o in enumerate(chunks):
    bones[o.name] = 'Chunk_%02d' % i; eb(bones[o.name], o.matrix_world.translation.copy(), root)
bpy.ops.object.mode_set(mode='OBJECT')
for o in chunks + frame_parts:                                       # vertex groups, then join into one mesh
    vg = o.vertex_groups.new(name=bones.get(o.name, 'Frame')); vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
act(frame_parts[0]); [o.select_set(True) for o in chunks + frame_parts]; bpy.context.view_layer.objects.active = frame_parts[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join()
mesh = bpy.context.active_object; mesh.name = 'SK_WallBreach'; mesh.data.name = 'SK_WallBreach'
mm = mesh.data.materials[:]; mesh.data.materials.clear(); mesh.data.materials.append(STONE); mesh.data.materials.append(FRAC)
mesh.parent = arm; md = mesh.modifiers.new('Armature', 'ARMATURE'); md.object = arm
act(mesh); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cube_project(cube_size=2.0, scale_to_bounds=False, correct_aspect=False); bpy.ops.object.mode_set(mode='OBJECT')
act(arm); arm.animation_data_create(); ac = bpy.data.actions.new('A_WallBreach_Collapse'); arm.animation_data.action = ac
bpy.ops.object.mode_set(mode='POSE')
rest = {n: samples[n][0] for n in samples}
for f in range(1, FRAMES + 1):
    sc.frame_set(f)
    for n, bn in bones.items():
        pb = arm.pose.bones[bn]; M = samples[n][f - 1] @ rest[n].inverted()       # world delta of the chunk
        pb.matrix = M @ arm_d.bones[bn].matrix_local
        pb.keyframe_insert('location', frame=f); pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print('SKELETAL tris %d bones %d frames %d' % (tris, len(arm_d.bones), FRAMES), flush=True)

# ---------------- rubble kit ----------------
for k in range(6):
    parts = []; n = 3 + k
    for j in range(n):
        s = (rnd.uniform(0.45, 0.6), rnd.uniform(0.6, 1.1), rnd.uniform(0.4, 0.55))
        b = block('rb%d_%d' % (k, j), Vector((rnd.uniform(-0.9, 0.9), rnd.uniform(-0.9, 0.9), 0)), s)
        b.rotation_euler = Euler((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6.3)))
        if rnd.random() < 0.4:
            halves = split(b, (rnd.uniform(-0.3, 0.3), 1, rnd.uniform(-0.4, 0.4))); b = halves[0]; bpy.data.objects.remove(halves[1])
        parts.append(b)
    for j, b in enumerate(parts):                                     # stack: drop each onto what is below (bbox heights)
        bpy.context.view_layer.update(); lo = min((b.matrix_world @ Vector(c)).z for c in b.bound_box)
        under = [p for p in parts[:j] if (p.location.xy - b.location.xy).length < 0.7]
        top = max([max((p.matrix_world @ Vector(c)).z for c in p.bound_box) for p in under] + [0.0])
        b.location.z += top - lo - (0.12 if under else 0.05)
    act(parts[0]); [p.select_set(True) for p in parts]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join()
    o = bpy.context.active_object; o.name = o.data.name = 'SM_Rubble_Masonry_%02d' % (k + 1); o.location = (12 + k * 3.5, 0, 0)
    act(o); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=2.0, scale_to_bounds=False, correct_aspect=False); bpy.ops.object.mode_set(mode='OBJECT')
    print('RUBBLE', o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'breach.blend'))
