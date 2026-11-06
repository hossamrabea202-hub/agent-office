# #530 previews: blender -b --factory-startup -P style_render.py -- <mesh.fbx> <out.mp4> <left clip|-> <left label> <right clip> <right label> [strike]
# Real mesh (licensed: local only, never committed), Workbench. With "strike" both sides also run a Python copy of the game's FABRIK, driven by the
# BPC_TentacleStrike state timing and targets. It is a SIMULATION for judging only, not the engine. Env: STILLS="3.7,4.0" renders PNGs; MAXSEC limits the mp4.
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MESH, OUT, LC, LL, RC, RL = a[:6]; STRIKE = 'strike' in a[6:]; THROW = 'catapult' if 'catapult' in a[6:] else 'spit' if 'spit' in a[6:] else None
STILLS = [float(x) for x in os.environ.get('STILLS', '').split(',') if x]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24
def action_of(fbx):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=fbx, use_anim=True)
    new = [o for o in bpy.data.objects if o not in before]
    ac = next(o for o in new if o.type == 'ARMATURE').animation_data.action; ac.use_fake_user = True
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    return ac
def side(clip, dx, label):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=MESH, use_anim=False)
    new = [o for o in bpy.data.objects if o not in before]; ar = next(o for o in new if o.type == 'ARMATURE')
    e = bpy.data.objects.new(label + '_root', None); sc.collection.objects.link(e); e.location.x = dx; e.rotation_euler.z = math.radians(55)
    for o in new:
        if o.parent is None: o.scale = (1, 1, 1); o.parent = e      # the mesh FBX: empty x0.01 > armature x100; the clip keys the armature's scale to 1
        if o.type == 'ARMATURE': o.scale = (1, 1, 1)
        if o.type == 'MESH':
            for s in o.material_slots:
                if s.material: s.material.diffuse_color = (0.42, 0.16, 0.16, 1)
    ar.animation_data_create(); ac = action_of(clip); ar.animation_data.action = ac
    if ac.slots: ar.animation_data.action_slot = ac.slots[0]        # Blender 4.4+: without the slot the action does not play on another armature
    for b in ar.pose.bones: b.rotation_mode = 'QUATERNION'          # FBX clips key the bones in quaternions
    cu = bpy.data.curves.new(label, 'FONT'); cu.body = label; cu.size = 5; cu.align_x = 'CENTER'
    t = bpy.data.objects.new(label, cu); sc.collection.objects.link(t); t.location = (dx, -40, -14); t.rotation_euler = (math.radians(90), 0, 0)
    return ar
sides = []
dxs = (-70.0, 70.0) if LC != '-' else (0.0,)
if LC != '-': sides.append((side(LC, dxs[0], LL), True))
sides.append((side(RC, dxs[-1], RL), False))
act = sides[-1][0].animation_data.action; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
sc.frame_start, sc.frame_end = f0, f1
if 'catapult' in a[6:] or 'spit' in a[6:]: sc.frame_end = f0 + int(float(os.environ.get('HOLDSEC', '9')) * 24)
if os.environ.get('MAXSEC'): sc.frame_end = min(f1, f0 + int(float(os.environ['MAXSEC']) * 24))
SEG = ['seg_%02d' % i for i in range(14)]
def fabrik(pts, target, lens):
    root = pts[0].copy(); p = [v.copy() for v in pts]
    if (target - root).length >= sum(lens):
        d = (target - root).normalized()
        for i in range(len(lens)): p[i + 1] = p[i] + d * lens[i]
        return p
    for _ in range(20):
        p[-1] = target.copy()
        for i in range(len(p) - 2, -1, -1): p[i] = p[i + 1] + (p[i] - p[i + 1]).normalized() * lens[i]
        p[0] = root.copy()
        for i in range(len(p) - 1): p[i + 1] = p[i] + (p[i + 1] - p[i]).normalized() * lens[i]
        if (p[-1] - target).length < 0.01: break
    return p
def state(t, old):          # alpha, aim in the armature's space (metres): the game's formulas, from the BPC_TentacleStrike export
    W, U, S, R = (2.4, 1.3, 0.3, 2.0) if old else (2.4, 1.39, 0.21, 3.0)
    Reach = 90.0; Base = Vector((-7.5, 3.1, -0.8)); D = Vector((0, -1, 0)); Z = Vector((0, 0, 1)); Sd = Vector((1, 0, 0))
    Hover = Base + Z * Reach * 0.7 + D * Reach * 0.35; Wind = Base + Z * Reach * 0.95 + D * Reach * -0.4; Tgt = Base + D * 55.0 + Z * 6.0
    if t < W: u = t / W; return 0.6 * u * (2 - u), Hover + Sd * math.sin(t * 9.0) * 9.0
    if t < W + U: u = (t - W) / U; v = u * (2 - u); return 0.6 + 0.4 * v, Hover + (Wind - Hover) * v
    if t < W + U + S: u = (t - W - U) / S; return 1.0, Wind + (Tgt - Wind) * 2 ** (10 * u - 10)
    u = min(1.0, (t - W - U - S) / R); return 1.0 - (1 - math.cos(u * math.pi)) / 2, Tgt
def apply_ik(ar, alpha, aim):
    if alpha <= 0.001: return
    ch = [ar.pose.bones[n] for n in SEG]
    pts = [b.head.copy() for b in ch]; lens = [(pts[i + 1] - pts[i]).length for i in range(13)]
    sol = fabrik(pts, aim, lens); sol = [pts[i].lerp(sol[i], alpha) for i in range(14)]
    for i in range(13):                 # swing each bone onto its solved segment, from the root out
        b = ch[i]; cur = ch[i + 1].head - b.head; want = sol[i + 1] - sol[i]
        q = cur.rotation_difference(want); h = b.head.copy(); m = b.matrix.copy(); m.translation = (0, 0, 0)
        nm = q.to_matrix().to_4x4() @ m; nm.translation = h; b.matrix = nm; bpy.context.view_layer.update()
# #533: the IK easing of wire_spit_ue.py, in rig metres (the tentacle's placed scale is about 2.7). The target is at -Y.
_B = Vector((-7.5, 3.1, -0.8)); _Dr = Vector((0, -1, 0)); _Zv = Vector((0, 0, 1)); _R = 98.0
_ik = {'t': -1.0, 'a': 0.0, 'p': None}
def throw_state(t, ar):
    if THROW == 'catapult':
        plan = [(0.1, _B + _Zv * _R * 0.85 + _Dr * _R * -0.5, 0.85, 1.5), (2.4, _B + _Zv * _R * 0.55 + _Dr * _R * 0.75, 1.0, 16.0), (3.2, None, 0.0, 1.2)]
    else:
        plan = [(0.0, ar.pose.bones['seg_13'].head + _Dr * 9.0, 0.45, 5.0), (1.4, None, 0.0, 2.5)]
    goal, ag, sp = None, 0.0, 1.0
    for ts, g, al, spd in plan:
        if t >= ts: goal = g if g is not None else goal; ag, sp = al, spd
    if goal is None: return 0.0, Vector((0, 0, 0))
    if _ik['p'] is None: _ik['p'] = ar.pose.bones['seg_13'].head.copy()
    k = min(1.0, sp / 24.0); _ik['a'] += (ag - _ik['a']) * k; _ik['p'] = _ik['p'].lerp(goal, k)
    return _ik['a'], _ik['p'].copy()
if THROW: STRIKE = True; state = None
if STRIKE:                              # bake clip + simulated IK into keys, so the render needs no handlers
    baked = []
    def clip_pose(ar, curves, f):       # sample the clip directly: frame_set does not restore channels whose keyed value did not change, so IK edits would stick
        for b in ar.pose.bones: b.location = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.scale = (1, 1, 1)
        for (name, prop, idx), fc in curves.items():
            if len(fc.keyframe_points): getattr(ar.pose.bones[name], prop)[idx] = fc.evaluate(f)   # the UE clips hold empty curves: they would evaluate to 0
        ar.update_tag(); bpy.context.view_layer.update()
    for ar, old in sides:
        fr = {}; cl = ar.animation_data.action; curves = {}; f_own = int(cl.frame_range[0])
        for fc in cl.layers[0].strips[0].channelbags[0].fcurves:
            if fc.data_path.startswith('pose.bones["'):
                curves[(fc.data_path.split('"')[1], fc.data_path.rsplit('.', 1)[1], fc.array_index)] = fc
        ar.animation_data.action = None
        for f in range(f0, sc.frame_end + 1):
            clip_pose(ar, curves, f_own + (f - f0)); apply_ik(ar, *(throw_state((f - f0) / 24.0, ar) if THROW else state((f - f0) / 24.0, old)))
            if THROW: fr.setdefault('head', {})[f] = ar.pose.bones['seg_13'].head.copy()
            fr[f] = {b.name: b.matrix_basis.copy() for b in ar.pose.bones}
        baked.append(fr)
    for (ar, old), fr in zip(sides, baked):
        ar.animation_data.action = None; ac = bpy.data.actions.new(ar.name + '_baked'); ar.animation_data.action = ac
        for b in ar.pose.bones: b.rotation_mode = 'QUATERNION'
        for f, pose in fr.items():
            if f == 'head': continue
            for b in ar.pose.bones:
                b.matrix_basis = pose[b.name]; b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
    print('BAKED', [len(fr) for fr in baked])
    if THROW:                           # 3 blobs on the same ballistics as the game (2.2 m wide, gravity and scale in rig units), staggered 0.16 and 0.24 s
        G_ = 9.8 / 2.7; T0 = 2.6 if THROW == 'catapult' else 0.5; ar = sides[-1][0]; hd = baked[-1]['head']; root = ar.parent
        mat = bpy.data.materials.new('blob'); mat.diffuse_color = (0.75, 0.32, 0.2, 1)
        for n, (dt, off) in enumerate(((0.0, (-5, -2)), (0.16, (6, 3)), (0.40, (1, -6)))):
            f_s = f0 + int(round((T0 + dt) * 24)); P0 = hd.get(f_s, hd[max(k for k in hd)]).copy()
            Tg = _B + _Dr * (75.0 if THROW == 'catapult' else 40.0) + Vector((off[0], off[1], 0.8)); fl = 1.6 * math.sqrt(max(1.0, (P0 - Tg).length) / G_) * 0.62
            vx = (Tg - P0 + Vector((0, 0, 0.5 * G_ * fl * fl))) / fl
            def flying(radius, mt, scl=(1, 1, 1)):
                bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=10, ring_count=6); q = bpy.context.object; q.parent = root; q.data.materials.append(mt); q.scale = scl; return q
            def key(q, f, loc, sc_):
                q.location = loc; q.scale = sc_; q.keyframe_insert('location', frame=f); q.keyframe_insert('scale', frame=f)
            o = flying(0.31, mat)                       # true size: 1.65 m at the placed scale of 2.7
            for f in range(f0, sc.frame_end + 1):
                t_ = (f - f_s) / 24.0; key(o, f, P0 if t_ < 0 else (Tg if t_ >= fl else P0 + vx * t_ + Vector((0, 0, -0.5 * G_ * t_ * t_))), (0.001,) * 3 if t_ < 0 or t_ > fl + 0.4 else (1, 1, 1))
            # the trail: a streak every 0.1 s, falling and shrinking for 0.8 s
            wet = bpy.data.materials.get('wet') or bpy.data.materials.new('wet'); wet.diffuse_color = (0.14, 0.02, 0.015, 1)
            for j in range(int(fl / 0.1)):
                t0_ = j * 0.1; Q0 = P0 + vx * t0_ + Vector((0, 0, -0.5 * G_ * t0_ * t0_)); q = flying(0.14, wet); q.rotation_euler = (0, 0.3, 0)
                for f in range(f_s + int(t0_ * 24) - 1, f_s + int((t0_ + 0.85) * 24) + 1):
                    u = (f - f_s) / 24.0 - t0_
                    if u < 0 or u > 0.8: key(q, f, Q0, (0.001,) * 3)
                    else: k_ = 1 - u / 0.9; key(q, f, Q0 + Vector((0, 0, -0.5 * G_ * u * u)), (0.55 * k_, 0.55 * k_, 1.4 * k_))
            # the landing: a 5.2 m splat and the burst's chunks
            f_l = f_s + int(fl * 24); bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.96, fill_type='NGON'); d_ = bpy.context.object; d_.parent = root; d_.data.materials.append(wet)
            key(d_, f_l - 1, Tg + Vector((0, 0, -0.75)), (0.001,) * 3); key(d_, f_l + 2, Tg + Vector((0, 0, -0.75)), (1, 1, 1))
            for c_ in range(14):
                an = c_ * 2.4; vc = Vector((math.cos(an) * (1.0 + c_ % 3), math.sin(an) * (1.0 + c_ % 3), 3.0 + c_ % 4)); q = flying(0.07, wet)
                for f in range(f_l - 1, f_l + 22):
                    u = (f - f_l) / 24.0
                    pz = Tg + vc * max(0, u) + Vector((0, 0, -0.5 * G_ * max(0, u) ** 2))
                    key(q, f, pz, (1, 1, 1) if 0 <= u < 0.8 and pz.z > Tg.z - 0.8 else (0.001,) * 3)
            print('BLOB', n, 'flight %.1f s, leaves at %.2f s' % (fl, T0 + dt))
        act_fix = sc.frame_end
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -270, 48); cam.rotation_euler = (math.radians(90), 0, 0); cd.lens = 35
if os.environ.get('NEAR'):                  # the close-up of the landing: a low camera near the target
    from mathutils import Euler
    tw = sides[-1][0].parent.matrix_world @ (_B + _Dr * (75.0 if THROW == 'catapult' else 40.0)); cam.location = tw + Vector((-3, -24, 4)); cam.rotation_euler = (Vector((tw.x, tw.y, tw.z + 3)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = 35
    bpy.ops.mesh.primitive_plane_add(size=600, location=(tw.x, tw.y, tw.z - 0.01)); gr_ = bpy.data.materials.new('ground'); gr_.diffuse_color = (0.20, 0.19, 0.15, 1); bpy.context.object.data.materials.append(gr_)
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
if STILLS:
    for s in STILLS:
        sc.frame_set(f0 + int(round(s * 24))); bpy.context.view_layer.update()
        sc.render.filepath = OUT.replace('.mp4', '_%04.2fs.png' % s); sc.render.image_settings.file_format = 'PNG'; bpy.ops.render.render(write_still=True)
else:
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.filepath = OUT; bpy.ops.render.render(animation=True)
print('RENDER OK', OUT, f0, sc.frame_end)
