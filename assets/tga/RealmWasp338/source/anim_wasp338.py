# Realm wasp v2 animations + FBX (#338, TGA PC). blender -b wasp338_rig.blend -P anim_wasp338.py -> wasp338_anim.blend, out/SK_RealmWasp.fbx
# Film motion method (research_notes/creature_studio_method.md section 3): the wingbeat is the DRIVER; body bob, gaster,
# legs, antennae and head are FOLLOWERS = damped springs on the driver curves, simulated over 3 loops and the last loop kept
# (seamless, with overlap and follow-through). Hover has staccato head snaps + holds; the sting has anticipation, a 3-frame
# strike, a hold on the hit and a slow recovery. Wingbeat 7.5 Hz: a 1.9 m insect must beat slowly, the blur cards
# (wingblur_L/R, scale-keyed shimmer) carry the speed.
# Clips, 30 fps, same names as v1 so BP_RealmWasp keeps working:
#   A_RealmWasp_Hover 48 loop | _Fly 32 loop | _Dive 24 loop | _Sting 30 one-shot, HIT FRAME 13 (BP waits 0.43 s) | _Death 45 one-shot
# Death drop is 0.40 m (v1: 1.05 m): BP_RealmWasp turns gravity back on, the capsule (half height 60) lands, and with the mesh at
# -130 cm the body then rests on the ground instead of sinking 45 cm under it.
import bpy, math, os
import numpy as np
from mathutils import Matrix, Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
sc = bpy.context.scene; sc.render.fps = 30
arm = bpy.data.objects['SK_RealmWasp_Rig']; Z0 = 1.30
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
def R(ax, deg): return Matrix.Rotation(math.radians(deg), 3, ax)
def flap(sd, up): return R('Y', -up if sd == 'L' else up)
def sweep(sd, back): return R('Z', back if sd == 'L' else -back)
def fold(sd, inward): return R('Y', inward if sd == 'L' else -inward)
def pitch(down): return R('X', down)
def yaw(left): return R('Z', left)
def roll(r): return R('Y', r)
SIDES = ('L', 'R'); LEGS = ('F', 'M', 'H')

def spring(target, k=0.25, c=0.45, loops=3):
    """damped follower of a periodic target (per frame); simulated over 3 loops, the last loop returned (seamless)."""
    n = len(target); x, v = target[0], 0.0; out = np.zeros(n)
    for L in range(loops):
        for i in range(n):
            a = k * (target[i] - x) - c * v; v += a; x += v
            if L == loops - 1: out[i] = x
    return out
def once(target, k=0.25, c=0.45):
    x, v = target[0], 0.0; out = np.zeros(len(target))
    for i, t in enumerate(target): a = k * (t - x) - c * v; v += a; x += v; out[i] = x
    return out
def loop_noise(n, amp, harmonics=(1, 2, 3), seed=0):
    r = np.random.default_rng(seed); f = np.arange(n); s = np.zeros(n)
    for h in harmonics: s += amp / h * np.sin(2 * np.pi * h * f / n + r.uniform(0, 6.28))
    return s
def env(f, keys):
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f0 <= f <= f1: t = (f - f0) / max(f1 - f0, 1e-6); t = t * t * (3 - 2 * t); return v0 + (v1 - v0) * t
    return keys[-1][1] if f > keys[-1][0] else keys[0][1]

def key(f, rot, loc=None, scl=None):
    for pb in arm.pose.bones:
        B = pb.bone.matrix_local.to_3x3(); Rm = rot.get(pb.name, Matrix.Identity(3))
        pb.rotation_quaternion = (B.inverted() @ Rm @ B).to_quaternion(); pb.keyframe_insert('rotation_quaternion', frame=f)
        pb.location = B.inverted() @ Vector((loc or {}).get(pb.name, (0, 0, 0))); pb.keyframe_insert('location', frame=f)
        if pb.name.startswith('wingblur'):
            s = (scl or {}).get(pb.name, 1.0); pb.scale = (s, s, s); pb.keyframe_insert('scale', frame=f)

def wing_angle(f, up, down, period=4.0, lag=0.0):
    ph = ((f / period) + lag) % 1.0 * 2 * math.pi; a = math.cos(ph)
    a = math.copysign(abs(a) ** 0.8, a)                     # a touch of dwell at the stroke ends (real strokes are not pure sines)
    return (up + down) / 2 + (up - down) / 2 * a, math.sin(ph)
def wings(r, f, up=55, down=-40, amp=1.0, swp=0.0, period=4.0):
    for sd in SIDES:
        a, fe = wing_angle(f, up, down, period); a2, fe2 = wing_angle(f, up, down, period, lag=0.12)   # hindwing lags
        r[f'wing_fore_{sd}'] = sweep(sd, swp) @ flap(sd, a * amp) @ R('X', 24 * fe * amp)
        r[f'wing_hind_{sd}'] = sweep(sd, swp * 1.1) @ flap(sd, a2 * amp * 0.9) @ R('X', 20 * fe2 * amp)
        r[f'wingblur_{sd}'] = sweep(sd, swp)
    return r
def lift(n, period=4.0, amp=0.012):
    """body bob driven by the downstrokes: lift peaks just after each downstroke"""
    f = np.arange(n); return amp * np.sin(2 * np.pi * (f / period - 0.35))

def build(name, n, fn, loop=True):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    frames = [fn(f) for f in range(n + 1)]
    if loop: frames[n] = frames[0]
    for f, (rot, loc, scl) in enumerate(frames): key(f, rot, loc, scl)
    act.use_fake_user = True; act.frame_range = (0, n); print('ACTION', name, n, flush=True); return act

# ---------------- hover: driver = wingbeat; followers = bob, gaster, legs, antennae; staccato head ------------------
def make_hover(n=48):
    bob = lift(n) + loop_noise(n, 0.035, (1, 2), 1)                       # slow drift + stroke bob
    sway = loop_noise(n, 0.03, (1, 3), 2); rollc = loop_noise(n, 3.0, (1, 2), 3); yawc = loop_noise(n, 4.0, (1,), 4)
    th_p = -12 + loop_noise(n, 2.5, (1, 2), 5) - 200 * np.gradient(bob)  # nose pitches against the vertical accel
    ab1 = spring(th_p * 0.8 - 6, 0.18, 0.40); ab2 = spring(ab1 * 0.9 + 2, 0.16, 0.38)   # gaster lags the thorax and overshoots
    st = spring(ab2 * 0.4, 0.2, 0.45)
    legsw = spring(-600 * np.gradient(np.gradient(bob)) + loop_noise(n, 4, (1, 2), 6), 0.12, 0.35)   # legs dangle, drag behind
    head_y = np.array([env(f, [(0, 0), (13, 0), (15, 14), (27, 14), (29, -6), (40, -6), (42, 0), (48, 0)]) for f in range(n)])   # snap, hold
    head_p = np.array([env(f, [(0, 0), (20, 0), (21.5, -8), (33, -8), (35, 0)]) for f in range(n)])
    ant = spring(head_y * 1.0, 0.10, 0.25); antp = spring(head_p * 1.2, 0.1, 0.25)       # antennae flick late
    mand = np.array([env(f, [(0, 0), (6, 0), (7, 12), (9, 0), (34, 0), (35, 14), (36, 2), (37, 12), (39, 0)]) for f in range(n)])
    blur = 1 + 0.04 * np.sin(np.arange(n) * 2.7)
    def fn(f):
        i = f % n; r = wings({}, f)
        r['thorax'] = yaw(yawc[i]) @ roll(rollc[i]) @ pitch(th_p[i])
        r['head'] = yaw(head_y[i]) @ pitch(head_p[i] + 6)
        r['abdomen_01'] = pitch(ab1[i] - th_p[i] - 10); r['abdomen_02'] = pitch(ab2[i] - ab1[i] - 6); r['stinger'] = pitch(st[i] - 4)
        for sd, sg in (('L', 1), ('R', -1)):
            r[f'antenna_{sd}'] = sweep(sd, -0.6 * (ant[i] - head_y[i]) * sg) @ pitch(-0.8 * (antp[i] - head_p[i]) + 3 * math.sin(2 * math.pi * i / n * 3 + sg))
            r[f'mandible_{sd}'] = R('Z', sg * mand[i])
        for li, lg in enumerate(LEGS):
            for sd in SIDES:
                s = legsw[(i + li * 3) % n]
                r[f'leg_{lg}_{sd}_1'] = pitch(20 + s); r[f'leg_{lg}_{sd}_2'] = fold(sd, 14 + 0.7 * s); r[f'leg_{lg}_{sd}_3'] = fold(sd, 8 + 0.4 * s)
        return r, {'root': (sway[i], 0, bob[i])}, {'wingblur_L': blur[i], 'wingblur_R': blur[(i + 7) % n]}
    return fn

def make_fly(n=32):
    bob = lift(n, amp=0.010) + loop_noise(n, 0.02, (1,), 11); bank = loop_noise(n, 5.0, (1,), 12)
    th_p = 18 + loop_noise(n, 2.0, (1, 2), 13)
    ab1 = spring(th_p * 0.3 + 2, 0.16, 0.4); ab2 = spring(ab1 * 0.8, 0.14, 0.38)
    legsw = spring(loop_noise(n, 5, (1, 2), 14), 0.12, 0.35)
    blur = 1 + 0.04 * np.sin(np.arange(n) * 2.7)
    def fn(f):
        i = f % n; r = wings({}, f, 62, -46)
        r['thorax'] = roll(bank[i]) @ pitch(th_p[i]); r['head'] = pitch(-12)
        r['abdomen_01'] = pitch(ab1[i] - th_p[i] + 8); r['abdomen_02'] = pitch(ab2[i] - ab1[i] + 3); r['stinger'] = pitch(2)
        for sd, sg in (('L', 1), ('R', -1)):
            r[f'antenna_{sd}'] = pitch(10 + 4 * math.sin(2 * math.pi * i / n * 2 + sg)) @ sweep(sd, 10)   # swept back by the airflow
        for li, lg in enumerate(LEGS):
            for sd in SIDES:
                s = legsw[(i + li * 4) % n]
                r[f'leg_{lg}_{sd}_1'] = pitch(50 + s); r[f'leg_{lg}_{sd}_2'] = fold(sd, 36 + 0.5 * s); r[f'leg_{lg}_{sd}_3'] = fold(sd, 14)
        return r, {'root': (0, 0, bob[i])}, {'wingblur_L': blur[i], 'wingblur_R': blur[(i + 5) % n]}
    return fn

def make_dive(n=24):
    jit = loop_noise(n, 2.0, (2, 3), 21)
    def fn(f):
        i = f % n; r = wings({}, f, 20, -14, 1.0, 38)
        r['thorax'] = roll(jit[i]) @ pitch(50); r['head'] = pitch(-24 + 0.5 * jit[i])
        r['abdomen_01'] = pitch(-32); r['abdomen_02'] = pitch(-30); r['stinger'] = pitch(-20)          # sting cocked forward
        for sd, sg in (('L', 1), ('R', -1)):
            r[f'antenna_{sd}'] = pitch(18) @ sweep(sd, 22); r[f'mandible_{sd}'] = R('Z', sg * 14)       # jaws open
        for lg in LEGS:
            for sd in SIDES: r[f'leg_{lg}_{sd}_1'] = pitch(-36 + jit[i]); r[f'leg_{lg}_{sd}_2'] = fold(sd, -8); r[f'leg_{lg}_{sd}_3'] = fold(sd, -4)  # reaching
        return r, {}, {'wingblur_L': 0.75, 'wingblur_R': 0.75}
    return fn

def make_sting(n=30):
    hov = make_hover(48)
    a1 = [(0, -10), (8, 16), (10, 6), (12, -55), (13, -64), (17, -60), (22, -30), (30, -10)]     # cock back, strike, hold, recover
    a2 = [(0, -6), (8, 12), (10, 4), (12, -42), (13, -50), (17, -46), (22, -24), (30, -6)]
    sg = [(0, -4), (8, 8), (10, 2), (12, -24), (13, -30), (17, -26), (23, -8), (30, -4)]
    th = [(0, -12), (8, -22), (11, -8), (13, -26), (18, -22), (30, -12)]
    lunge = [(0, 0), (8, 0.08), (11, -0.10), (13, -0.30), (17, -0.26), (30, 0)]
    rise = [(0, 0), (8, 0.06), (13, -0.05), (30, 0)]
    def fn(f):
        r, loc, scl = hov(f % 48)
        r['abdomen_01'] = pitch(env(f, a1)); r['abdomen_02'] = pitch(env(f, a2)); r['stinger'] = pitch(env(f, sg))
        r['thorax'] = pitch(env(f, th)); r['head'] = pitch(-8)
        for sd, s2 in (('L', 1), ('R', -1)): r[f'mandible_{sd}'] = R('Z', s2 * env(f, [(0, 0), (8, 16), (13, 18), (18, 0)]))
        return r, {'root': (0, env(f, lunge), loc['root'][2] + env(f, rise))}, scl
    return fn

def make_death(n=45):
    def ease(f, a, b, f0, f1, p=2.0): u = min(max((f - f0) / (f1 - f0), 0), 1); return a + (b - a) * u ** p
    twitch = lambda f: 18 * (math.exp(-((f - 22) / 1.2) ** 2) + 0.6 * math.exp(-((f - 31) / 1.0) ** 2))   # staccato death spasms
    drop_t = once(np.array([0.0] * 3 + [-0.40] * (n - 2)), 0.08, 0.42)                                     # falls, a small bounce, settles
    def fn(f):
        beat = 1 - ease(f, 0, 1, 0, 12, 1.0)
        r = wings({}, f, 55 * beat - 8 * (1 - beat), -40 * beat - 8 * (1 - beat), 1.0, ease(f, 0, 70, 10, 26, 1.5), 4 + 6 * (1 - beat))
        for lg in LEGS:
            for sd in SIDES:
                c = ease(f, 0, 1, 0, 26, 1.0)
                r[f'leg_{lg}_{sd}_1'] = pitch(20 - 55 * c + twitch(f)) @ flap(sd, 22 * c)
                r[f'leg_{lg}_{sd}_2'] = fold(sd, 14 + 75 * c - 0.6 * twitch(f)); r[f'leg_{lg}_{sd}_3'] = fold(sd, 8 + 40 * c)
        r['thorax'] = R('Y', ease(f, 0, 168, 4, 30, 1.6)) @ pitch(ease(f, -12, 4, 0, 30, 1.0))
        r['abdomen_01'] = pitch(ease(f, -8, -40, 0, 20, 1.0) + 0.5 * twitch(f)); r['abdomen_02'] = pitch(ease(f, -5, -32, 0, 20, 1.0))
        r['stinger'] = pitch(-10 + 0.8 * twitch(f))
        for sd, sg in (('L', 1), ('R', -1)):
            r[f'antenna_{sd}'] = pitch(ease(f, 0, -25, 10, 35, 1.0)); r[f'mandible_{sd}'] = R('Z', sg * (6 + 10 * math.exp(-((f - 22) / 1.5) ** 2)))
        return r, {'root': (0, 0, float(drop_t[min(f, n - 1)]))}, {'wingblur_L': max(beat, 0.001), 'wingblur_R': max(beat, 0.001)}
    return fn

acts = [build('A_RealmWasp_Hover', 48, make_hover()), build('A_RealmWasp_Fly', 32, make_fly()), build('A_RealmWasp_Dive', 24, make_dive()),
        build('A_RealmWasp_Sting', 30, make_sting(), loop=False), build('A_RealmWasp_Death', 45, make_death(), loop=False)]
arm.animation_data.action = acts[0]
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)

# ---- one mesh, material slots in UE order: 0 body, 1 wings, 2 hair, 3 wing blur (BP_RealmWasp sets elements 0 and 1) ----
ORDER = [('SK_RealmWasp', 'M_RealmWasp_Body'), ('SK_RealmWasp_Wings', 'M_RealmWasp_Wings'), ('SK_RealmWasp_Hair', 'M_RealmWasp_Hair'),
         ('SK_RealmWasp_WingBlur', 'M_RealmWasp_WingBlur')]
for on, mn in ORDER:
    o = bpy.data.objects[on]; o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get(mn) or bpy.data.materials.new(mn))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'wasp338_anim.blend'))
for o in sc.objects: o.select_set(o.name in [a for a, _ in ORDER])
body = bpy.data.objects['SK_RealmWasp']; bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
want = [mn for _, mn in ORDER]
for i, mn in enumerate(want):                                    # force the slot order
    j = [s.material.name for s in body.material_slots].index(mn); body.active_material_index = j
    while j > i: bpy.ops.object.material_slot_move(direction='UP'); j -= 1
print('SLOTS', [s.material.name for s in body.material_slots], flush=True)
arm.name = 'Armature'
for o in sc.objects: o.select_set(o.name in ('Armature', 'SK_RealmWasp'))
bpy.context.view_layer.objects.active = arm
os.makedirs(os.path.join(D, 'out'), exist_ok=True); fbx = os.path.join(D, 'out', 'SK_RealmWasp.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL',
                         primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL')
print('FBX OK', fbx, os.path.getsize(fbx), flush=True)
