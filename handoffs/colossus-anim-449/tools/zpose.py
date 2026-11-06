# zpose.py - body-space posing + analytic leg IK for the SK_Zombie rig (adjustedfilm, #449 follow-up: zombies / colossus).
# World metres. The zombie faces -Y, Z is up, +X is its LEFT (same convention as the brute). The pelvis (root bone Hips)
# is the ARMATURE OBJECT, so pelvis moves/rotations act on the object; everything else is a pose bone.
# Bind pose = T-pose (arms along +-X), legs straight, toes on z = 0, ankle 14.5 cm up.
import bpy, math
from mathutils import Vector, Matrix, Quaternion

FWD = Vector((0, -1, 0)); UP = Vector((0, 0, 1)); LEFT = Vector((1, 0, 0))
LEGS = {'L': ('LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'LeftToe_End'),
        'R': ('RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase', 'RightToe_End')}
SPINE = ('Spine', 'Spine1', 'Spine2')
ARMS = {'L': ('LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand'), 'R': ('RightShoulder', 'RightArm', 'RightForeArm', 'RightHand')}
FINGERS = {s: ['%sHand%s%d' % (sd, f, i) for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for i in (1, 2, 3)] for s, sd in (('L', 'Left'), ('R', 'Right'))}
CLOTH = ['BackCloth%d' % i for i in (1, 2, 3, 4)] + ['FrontCloth%d' % i for i in (1, 2, 3, 4)]

def upd(): bpy.context.view_layer.update()

def rest_all(arm, bind_loc=None, bind_rot=None):
    import zrig
    arm.rotation_mode = 'XYZ'; arm.location = (bind_loc or zrig.BIND_LOC).copy(); arm.rotation_euler = bind_rot or zrig.BIND_ROT
    arm.scale = (0.01, 0.01, 0.01)
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    upd()

def wpos(arm, bone, tail=False):
    pb = arm.pose.bones[bone]; return arm.matrix_world @ (pb.tail if tail else pb.head)

def pel_pos(arm): return arm.matrix_world.translation.copy()

def pel_move(arm, delta_world):
    arm.location = arm.location + Vector(delta_world); upd()

def pel_rot(arm, axis, deg, pivot=None):
    """rotate the whole body (the hips object) about a WORLD axis through the hips (or pivot)."""
    p = arm.matrix_world.translation.copy() if pivot is None else Vector(pivot)
    R = Matrix.Translation(p) @ Quaternion(Vector(axis).normalized(), math.radians(deg)).to_matrix().to_4x4() @ Matrix.Translation(-p)
    m = R @ arm.matrix_world
    loc, rot, _ = m.decompose(); arm.location = loc; arm.rotation_euler = rot.to_euler('XYZ'); upd()

def pel_quat(arm): return arm.matrix_world.to_quaternion()

def rot(arm, bone, axis, deg, pivot=None):
    """rotate a pose bone about a WORLD axis through its head (or `pivot`), keeping its children attached."""
    pb = arm.pose.bones[bone]
    aw = arm.matrix_world; ai = aw.inverted()
    ax = (ai.to_3x3() @ Vector(axis)).normalized()
    p = pb.head if pivot is None else ai @ Vector(pivot)
    R = Matrix.Translation(p) @ Quaternion(ax, math.radians(deg)).to_matrix().to_4x4() @ Matrix.Translation(-p)
    pb.matrix = R @ pb.matrix; upd()

def rot_local(arm, bone, axis_local, deg):
    """rotate a pose bone about one of its OWN axes (0=X, 1=Y along the bone, 2=Z)."""
    pb = arm.pose.bones[bone]; ax = Vector((0, 0, 0)); ax[axis_local] = 1.0
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, math.radians(deg)); upd()

def move(arm, bone, delta_world):
    pb = arm.pose.bones[bone]; d = arm.matrix_world.inverted().to_3x3() @ Vector(delta_world)
    m = pb.matrix.copy(); m.translation += d; pb.matrix = m; upd()

def _rot_q(arm, bone, q, pivot):
    ax, ang = q.to_axis_angle()
    if abs(ang) > 1e-7: rot(arm, bone, ax, math.degrees(ang), pivot)

def leg_ik(arm, side, target, knee_dir=None, n_hint=None, prebend=12.0):
    """move the ankle (Foot head) of `side` to world `target`. Two-bone chain UpLeg -> Leg -> Foot. The knee plane normal
    is +X for a forward-bending knee; a straight leg is pre-bent forward first so the solve never flips backwards."""
    t1, s1, ft, toe, toe_end = LEGS[side]
    H = wpos(arm, t1); K = wpos(arm, s1); A = wpos(arm, ft)
    if math.degrees((H - K).angle(A - K)) > 170.0 and prebend:    # straight: bend forward a little first
        rot(arm, s1, LEFT, prebend, K); K = wpos(arm, s1); A = wpos(arm, ft)
    T = Vector(target)
    a = (K - H).length; b = (A - K).length
    d = max(abs(a-b)+1e-4, min(a+b-1e-4, (T - H).length))
    n = (K - H).cross(A - K)
    if n_hint is not None and (n.length < 1e-3 or n.dot(Vector(n_hint)) < 0): n = Vector(n_hint)
    if n.length < 1e-6: n = LEFT.copy()
    n.normalize()
    cur = (A - H).length
    def ang_at_knee(dist): return math.acos(max(-1, min(1, (a*a + b*b - dist*dist)/(2*a*b))))
    delta = ang_at_knee(cur) - ang_at_knee(d)
    if abs(delta) > 1e-6:
        best = None
        for sgn in (1, -1):
            q = Quaternion(n, abs(delta)*sgn); err = abs(((q @ (A-K)) + K - H).length - d)
            if best is None or err < best[0]: best = (err, q)
        _rot_q(arm, s1, best[1], K)
    A = wpos(arm, ft)
    q = (A - H).rotation_difference(T - H)
    _rot_q(arm, t1, q, H)
    if knee_dir is not None:
        H = wpos(arm, t1); K = wpos(arm, s1); A = wpos(arm, ft); ax = (A - H).normalized()
        kv = (K - H) - ax*((K - H).dot(ax)); want = Vector(knee_dir) - ax*Vector(knee_dir).dot(ax)
        if kv.length > 1e-5 and want.length > 1e-5:
            _rot_q(arm, t1, kv.rotation_difference(want), H)
    return (wpos(arm, ft) - T).length

def knee_angle(arm, side):
    t1, s1, ft = LEGS[side][:3]
    H = wpos(arm, t1); K = wpos(arm, s1); A = wpos(arm, ft); return math.degrees((H-K).angle(A-K))

def set_world_rot(arm, bone, qw):
    cur = (arm.matrix_world @ arm.pose.bones[bone].matrix).to_quaternion()
    _rot_q(arm, bone, qw @ cur.inverted(), wpos(arm, bone))

def world_rot(arm, bone): return (arm.matrix_world @ arm.pose.bones[bone].matrix).to_quaternion()

# ---------------- curve helpers ----------------
def ease(x): x = max(0.0, min(1.0, x)); return x*x*(3-2*x)
def wrap(x): return x - math.floor(x)
