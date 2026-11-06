# bl_pose.py - body-space posing + IK legs for authoring Flesh Brute clips in Blender (adjustedfilm, #449 stage 2).
# All positions are WORLD metres (armature object at origin, scale 0.01). The brute faces -Y, Z is up, +X is its LEFT.
import bpy, math
from mathutils import Vector, Matrix, Quaternion

FWD = Vector((0, -1, 0)); UP = Vector((0, 0, 1)); LEFT = Vector((1, 0, 0))
LEGS = {'L': ('thigh_01_L', 'thigh_02_L', 'shin_01_L', 'shin_02_L', 'foot_L', 'toe_L'),
        'R': ('thigh_01_R', 'thigh_02_R', 'shin_01_R', 'shin_02_R', 'foot_R', 'toe_R')}

def upd(): bpy.context.view_layer.update()

def rest_all(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    upd()

def wpos(arm, bone, tail=False):
    pb = arm.pose.bones[bone]; return arm.matrix_world @ (pb.tail if tail else pb.head)

def rot(arm, bone, axis, deg, pivot=None):
    """rotate a pose bone about a WORLD axis through its head (or `pivot`), keeping its children attached."""
    pb = arm.pose.bones[bone]
    aw = arm.matrix_world; ai = aw.inverted()
    ax = (ai.to_3x3() @ Vector(axis)).normalized()
    p = pb.head if pivot is None else ai @ Vector(pivot)
    R = Matrix.Translation(p) @ Quaternion(ax, math.radians(deg)).to_matrix().to_4x4() @ Matrix.Translation(-p)
    pb.matrix = R @ pb.matrix; upd()

def move(arm, bone, delta_world):
    pb = arm.pose.bones[bone]; d = arm.matrix_world.inverted().to_3x3() @ Vector(delta_world)
    m = pb.matrix.copy(); m.translation += d; pb.matrix = m; upd()

def key(arm, bones=None, frame=None):
    for pb in arm.pose.bones:
        if bones and pb.name not in bones: continue
        pb.keyframe_insert('rotation_quaternion', frame=frame); pb.keyframe_insert('location', frame=frame)

# ---------------- analytic leg IK (this rig: hip=thigh_01 head, knee=shin_01 head, ankle=foot head; a dog-leg chain:
# thigh_02 rides rigid on thigh_01 and shin_02 rides rigid on shin_01, so it is a clean two-bone problem) --------------
def _rot_q(arm, bone, q, pivot):
    """apply a world-space rotation quaternion q to bone about a world pivot."""
    ax, ang = q.to_axis_angle()
    if abs(ang) > 1e-7: rot(arm, bone, ax, math.degrees(ang), pivot)

def leg_ik(arm, side, target, knee_dir=None, n_hint=None):
    """move the ankle (foot head) of `side` to world `target`; the knee stays in the leg's own bend plane."""
    t1, t2, s1, s2, ft, toe = LEGS[side]
    H = wpos(arm, t1); K = wpos(arm, s1); A = wpos(arm, ft); T = Vector(target)
    a = (K - H).length; b = (A - K).length
    d = max(abs(a-b)+1e-4, min(a+b-1e-4, (T - H).length))
    n = (K - H).cross(A - K)
    if n_hint is not None and (n.length < 1e-3 or n.dot(Vector(n_hint)) < 0): n = Vector(n_hint)   # never let the knee plane flip
    if n.length < 1e-6: n = LEFT.copy()
    n.normalize()
    # 1) knee angle: rotate the shin about n through K so |A-H| = d
    cur = (A - H).length
    def ang_at_knee(dist):   # interior angle at the knee
        return math.acos(max(-1, min(1, (a*a + b*b - dist*dist)/(2*a*b))))
    delta = ang_at_knee(cur) - ang_at_knee(d)       # opening the knee increases the distance
    sgn = 1 if ((Quaternion(n, delta) @ (A - K)) + K - H).length > cur else -1
    if abs(delta) > 1e-6:
        q = Quaternion(n, abs(delta)*sgn)
        if abs(((q @ (A-K)) + K - H).length - d) > abs(((Quaternion(n, -abs(delta)*sgn) @ (A-K)) + K - H).length - d):
            q = Quaternion(n, -abs(delta)*sgn)
        _rot_q(arm, s1, q, K)
    # 2) swing the whole leg about the hip so the ankle lands on the target
    A = wpos(arm, ft)
    q = (A - H).rotation_difference(T - H)
    _rot_q(arm, t1, q, H)
    # 3) optional: twist about the hip->ankle axis so the knee points toward knee_dir
    if knee_dir is not None:
        H = wpos(arm, t1); K = wpos(arm, s1); A = wpos(arm, ft); ax = (A - H).normalized()
        kv = (K - H) - ax*((K - H).dot(ax)); want = Vector(knee_dir) - ax*Vector(knee_dir).dot(ax)
        if kv.length > 1e-5 and want.length > 1e-5:
            q = kv.rotation_difference(want)
            _rot_q(arm, t1, q, H)
    return (wpos(arm, ft) - T).length

def set_world_rot(arm, bone, qw):
    """make the bone's WORLD rotation equal qw (rotating about its own head)."""
    cur = (arm.matrix_world @ arm.pose.bones[bone].matrix).to_quaternion()
    _rot_q(arm, bone, qw @ cur.inverted(), wpos(arm, bone))

# ---------------- (unused) Blender IK constraints: they need tails that point down the chain; this rig's don't ----------------
def empty(name, loc):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e.location = loc; return e

def setup_leg_ik(arm):
    """IK on shin_02 (chain thigh_01..shin_02, the twist bones locked), a pole in front of the knee, and the foot copying
    its target's world rotation. Returns {side: (target, pole)}."""
    rigs = {}
    for side, (t1, t2, s1, s2, ft, toe) in LEGS.items():
        fp = wpos(arm, ft); kp = wpos(arm, s1)
        tgt = empty('IK_' + side, fp)
        tgt.rotation_mode = 'QUATERNION'
        tgt.rotation_quaternion = (arm.matrix_world @ arm.pose.bones[ft].matrix).to_quaternion()
        pole = empty('POLE_' + side, kp + FWD*0.8)
        c = arm.pose.bones[s2].constraints.new('IK'); c.target = tgt; c.pole_target = pole; c.chain_count = 4
        c.use_tail = False   # shin_02's HEAD is the ankle side? decided below by test
        for b in (t2, s2):
            pb = arm.pose.bones[b]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
        cr = arm.pose.bones[ft].constraints.new('COPY_ROTATION'); cr.target = tgt
        rigs[side] = (tgt, pole, c)
    upd()
    # which end of shin_02 reaches the target: use_tail True means the TAIL (ankle) reaches; choose what keeps the foot attached
    for side, (tgt, pole, c) in rigs.items():
        best = None
        for use_tail in (True, False):
            c.use_tail = use_tail
            for ang in range(-180, 180, 10):
                c.pole_angle = math.radians(ang); upd()
                err = (wpos(arm, LEGS[side][4]) - tgt.location).length
                knee = wpos(arm, LEGS[side][2]); hip = wpos(arm, LEGS[side][0])
                fwdness = (knee - (hip + wpos(arm, LEGS[side][4]))*0.5).dot(FWD)
                score = err*10 - fwdness*0.0   # knees bend forward is checked after moving the target up
                if best is None or score < best[0] - 1e-6: best = (score, use_tail, ang)
        c.use_tail = best[1]; c.pole_angle = math.radians(best[2]); upd()
    return rigs

def tune_poles(arm, rigs):
    """with the feet raised 25 cm (knees must bend), pick the pole angle that bends the knee FORWARD and keeps the foot on target."""
    for side, (tgt, pole, c) in rigs.items():
        home = tgt.location.copy(); tgt.location = home + UP*0.25; best = None
        for ang in range(-180, 180, 5):
            c.pole_angle = math.radians(ang); upd()
            err = (wpos(arm, LEGS[side][4]) - tgt.location).length
            knee = wpos(arm, LEGS[side][2]); hip = wpos(arm, LEGS[side][0]); ank = wpos(arm, LEGS[side][4])
            fwdness = (knee - (hip + ank)*0.5).dot(FWD); side_dev = abs((knee - (hip + ank)*0.5).dot(LEFT))
            score = err*20 - fwdness + side_dev*0.5
            if best is None or score < best[0]: best = (score, ang, err, fwdness)
        c.pole_angle = math.radians(best[1]); tgt.location = home; upd()
        print('POLE', side, 'angle', best[1], 'err', round(best[2], 4), 'knee fwd', round(best[3], 3))

def bake(arm, f0, f1):
    for o in bpy.data.objects: o.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones: pb.bone.select = True
    bpy.ops.nla.bake(frame_start=f0, frame_end=f1, only_selected=False, visual_keying=True, clear_constraints=True,
                     use_current_action=True, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')

# ---------------- curve helpers ----------------
def ease(x): x = max(0.0, min(1.0, x)); return x*x*(3-2*x)
def wrap(x): return x - math.floor(x)
def cyc(phase, *harm):
    """sum of cosine harmonics: harm = (amp, n, phase_offset) ..."""
    return sum(a*math.cos(2*math.pi*(n*phase - off)) for a, n, off in harm)
