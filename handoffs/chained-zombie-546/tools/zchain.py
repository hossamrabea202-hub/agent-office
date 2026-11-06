# zchain.py - #546 the chained zombie: chain-limited body + key poses. Run:
#   blender -b -P zchain.py -- <clip_rig.fbx> <out_dir> [clip names...]
# Metres, Blender space: the zombie faces -Y, +X is its LEFT, the wall is behind him at y = WALL. Wrists and ankles are ALWAYS placed by IK, and a chained
# one is projected back inside its chain's length around its wall anchor, so a yank stops dead where the chain goes taut. Free arm = same IK, no limit.
import bpy, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
import zrig, zpose as P, zperform as F

WALL = 0.50
AW = {'L': Vector((1.02, 0.47, 1.76)), 'R': Vector((-1.02, 0.47, 1.76))}        # wrist anchors on the wall
AF = {'L': Vector((0.56, 0.47, 0.24)), 'R': Vector((-0.56, 0.47, 0.24))}        # ankle anchors
LW, LF = 0.72, 0.52                                                             # chain lengths
LAYOUT = dict(wall_y=WALL, wrist_anchor_L=list(AW['L']), ankle_anchor_L=list(AF['L']), chain_wrist=LW, chain_ankle=LF)

B = dict(F.BASE)
B.update({'pel_y': 0.04, 'pel_z': -0.07, 'spine': 8.0, 'spine1': 6.0, 'spine2': 4.0, 'neck': -2.0, 'head': 4.0, 'claw_L': 30.0, 'claw_R': 30.0, 'hand_L': 0.0, 'hand_R': 0.0,
          'wL_x': 0.73, 'wL_y': 0.06, 'wL_z': 1.44, 'wR_x': -0.73, 'wR_y': 0.06, 'wR_z': 1.44, 'pole_L': 0.0, 'pole_R': 0.0,    # wrist targets (world), elbow pole lift
          'chain_L': 1.0, 'chain_R': 1.0, 'jerk': 0.0,
          'foot_L_x': 0.217, 'foot_L_y': 0.0, 'foot_L_z': 0.0, 'foot_R_x': -0.217, 'foot_R_y': 0.0, 'foot_R_z': 0.0, 'tremble': 0.0, 'foot_free': 0.0})
F.BASE.clear(); F.BASE.update(B)
F.GROUP_LAG.update({'wL': 0.05, 'wR': 0.05, 'pole': 0.05, 'chain': 0.0, 'jerk': 0.0})

def pole_twist(arm, t1, s1, ft, pole):
    """turn the arm about the shoulder-wrist axis until the elbow points at the pole (signed angle: never the 180 degree ambiguity of a rotation_difference)."""
    H = P.wpos(arm, t1); K = P.wpos(arm, s1); A = P.wpos(arm, ft); ax = (A - H).normalized()
    kv = (K - H) - ax*((K - H).dot(ax)); want = pole - ax*pole.dot(ax)
    if kv.length < 1e-5 or want.length < 1e-5: return
    a = math.atan2(ax.dot(kv.cross(want)), kv.dot(want))
    P.rot(arm, t1, ax, math.degrees(a), H)

class ChainBody(F.Body):
    """F.Body with the arms replaced by wrist IK and everything chained held inside its chain."""
    prevW = None
    def apply(self, q, t=0.0):
        arm = self.arm; P.rest_all(arm)
        tr = q['tremble']
        n1 = math.sin(2*math.pi*9.1*t) + 0.6*math.sin(2*math.pi*13.7*t+1.3)
        n2 = math.sin(2*math.pi*7.3*t+0.7) + 0.5*math.sin(2*math.pi*11.9*t+2.1)
        n3 = math.sin(2*math.pi*5.3*t+0.3) + 0.4*math.sin(2*math.pi*17.3*t+0.9)
        P.pel_move(arm, (q['pel_x'] + 0.004*tr*n2, -q['pel_y'], q['pel_z'] + 0.004*tr*n3))
        P.pel_rot(arm, P.UP, q['pel_yaw']); P.pel_rot(arm, P.LEFT, q['pel_pitch']); P.pel_rot(arm, P.FWD, q['pel_roll'])
        for b, k, kt in (('Spine', 'spine', 0.25), ('Spine1', 'spine1', 0.35), ('Spine2', 'spine2', 0.40)):
            P.rot(arm, b, P.LEFT, q[k] + 0.7*tr*n1)
            P.rot(arm, b, P.UP, q['twist']*kt); P.rot(arm, b, P.FWD, q['side']*kt + 0.5*tr*n2)
        P.rot(arm, 'Neck', P.LEFT, q['neck']); P.rot(arm, 'Neck', P.UP, q['neck_yaw'])
        P.rot(arm, 'Head', P.LEFT, q['head'] + 1.6*tr*n2); P.rot(arm, 'Head', P.UP, q['head_yaw'] + 1.1*tr*n1); P.rot(arm, 'Head', P.FWD, q['head_roll'] + 0.8*tr*n3)
        for s, sg in (('L', 1.0), ('R', -1.0)):
            sh, ua, fa, hd = P.ARMS[s]
            P.rot(arm, sh, P.FWD, -sg*q['shoulder_' + s])
            P.rot(arm, fa, P.UP, -sg*24.0)                    # bend the elbow the way an elbow bends before the solve
            W = Vector((q['w%s_x' % s], q['w%s_y' % s], q['w%s_z' % s]))
            W += Vector((n3, n1, n2))*0.0035*tr
            Sh = P.wpos(arm, ua); reach = 0.985*((P.wpos(arm, fa) - Sh).length + (P.wpos(arm, hd) - P.wpos(arm, fa)).length)   # never dead straight: the elbow pole needs a bend to hold on to
            for _ in range(6):                        # inside the chain AND inside the arm's reach
                if q['chain_' + s] > 0.5:
                    d = W - AW[s]
                    if d.length > LW: W = AW[s] + d.normalized()*LW
                if (W - Sh).length > reach: W = Sh + (W - Sh).normalized()*reach
            if (W - Sh).length < 0.34: W = Sh + (W - Sh).normalized()*0.34      # hand never into the shoulder: that is where the elbow whips round
            pw = self.prevW.get(s)
            if pw is not None and (W - pw).length > 0.17: W = pw + (W - pw).normalized()*0.17       # wrist top speed 5 m/s
            self.prevW[s] = W.copy()
            pole = Vector((sg*0.5, 0.6, -0.6 + q['pole_' + s]))
            P.chain_ik(arm, (ua, fa, hd), W, None, None, 0.0)
            pole_twist(arm, ua, fa, hd, pole)
            P.rot(arm, hd, P.LEFT, q['hand_' + s] + 3.0*tr*n3)
            for fb in P.FINGERS[s]:
                if fb in arm.pose.bones: P.rot_local(arm, fb, 0, (q['claw_' + s] + 5.0*tr*n1)*(0.6 if 'Thumb' in fb else 1.0))
        R = P.pel_quat(arm) @ self.pel0.inverted()
        for s, sg in (('L', 1.0), ('R', -1.0)):
            tgt = self.home[s] + Vector((q['foot_%s_x' % s], -q['foot_%s_y' % s], q['foot_%s_z' % s]))
            d = tgt - AF[s]
            if d.length > LF: tgt = AF[s] + d.normalized()*LF
            P.leg_ik(arm, s, tgt, knee_dir=R @ (P.FWD + P.LEFT*sg*0.35), n_hint=R @ P.LEFT)
            ff = max(0.0, min(1.0, q['foot_free']))
            if ff < 1.0:
                cur = P.world_rot(arm, P.LEGS[s][2]); P.set_world_rot(arm, P.LEGS[s][2], self.frot[s].slerp(cur, ff))

def report(arm, n, name, free=''):
    """the numbers the card asks for: chain stretch, arm spread, knee range."""
    sc = bpy.context.scene; over = {}; spread = {'L': [], 'R': []}; kn = []; prev = None; pops = []; root = []
    for f in range(1, n+1):
        sc.frame_set(f)
        for s in 'LR':
            W = P.wpos(arm, P.ARMS[s][3]); S = P.wpos(arm, P.ARMS[s][1])
            if s not in free: over['w' + s] = max(over.get('w' + s, 0), (W - AW[s]).length - LW)
            over['f' + s] = max(over.get('f' + s, 0), (P.wpos(arm, P.LEGS[s][2]) - AF[s]).length - LF)
            v = W - S; spread[s].append(math.degrees(math.atan2(math.hypot(v.x, v.y), -v.z))); kn.append(P.knee_angle(arm, s))
        cur = {pb.name: pb.matrix_basis.to_quaternion() for pb in arm.pose.bones}
        if prev: pops.append(max(((lambda a_: min(a_, 360-a_))(math.degrees(cur[b].rotation_difference(prev[b]).angle)), b, f) for b in cur))
        prev = cur; root.append(tuple(P.pel_pos(arm)))
    avg = lambda a: sum(a)/len(a)
    print('CHAIN %s | stretch past chain cm: %s | arm from hanging deg L %.0f..%.0f avg %.0f R %.0f..%.0f avg %.0f (T-pose 90, 80%% = 72) | knee %.0f..%.0f | worst %.1f deg/f %s @%d | hips y %.2f..%.2f' % (
        name, {k: round(v*100, 1) for k, v in over.items()}, min(spread['L']), max(spread['L']), avg(spread['L']), min(spread['R']), max(spread['R']), avg(spread['R']),
        min(kn), max(kn), *max(pops), min(r[1] for r in root), max(r[1] for r in root)))

def author(arm, spec, out):
    body = ChainBody(arm); body.prevW = {}; perf = F.Performance(spec['keys'], spec['length']); fps = 30; n = int(round(spec['length']*fps)) + 1
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions.new(spec['name'])
    for f in range(n):
        t = f/float(fps)
        if spec.get('loop') and n > 1:              # a loop's overlap lags wrap round, so frame 0 and the last frame are the same pose
            q = {ch: perf.value(ch, t) if t >= F.GROUP_LAG[F.group(ch)] else perf.value(ch, t + spec['length']) for ch in F.BASE}
        else: q = perf.params(t)
        body.apply(q, t if not spec.get('loop') else t); zrig.key(arm, frame=f+1)
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, n; sc.render.fps = fps
    report(arm, n, spec['name'], spec.get('free', ''))
    zrig.export_anim(arm, os.path.join(out, spec['name'] + '.fbx'), 1, n)
    print('AUTHOR OK', spec['name'], n, 'frames')

# ---------------------------------------- key poses --------------------------------------------------
def K(**k): return dict(k)
REST = dict(B)
LUNGE = K(pel_y=0.20, pel_z=-0.13, pel_pitch=5, spine=20, spine1=15, spine2=12, neck=-14, head=-12, shoulder_L=-8, shoulder_R=-8,
          wL_x=0.68, wL_y=-0.06, wL_z=1.27, wR_x=-0.68, wR_y=-0.06, wR_z=1.27, claw_L=48, claw_R=48, hand_L=-18, hand_R=-18, foot_L_y=0.05, foot_R_y=0.05, tremble=1.0)
SLAM = K(pel_y=-0.05, pel_z=-0.09, pel_pitch=-5, spine=-4, spine1=-7, spine2=-8, neck=-16, head=-20, shoulder_L=8, shoulder_R=8,
         wL_x=0.76, wL_y=0.16, wL_z=1.44, wR_x=-0.76, wR_y=0.16, wR_z=1.44, claw_L=14, claw_R=14, hand_L=10, hand_R=10, foot_L_y=-0.02, foot_R_y=-0.02, tremble=0.5)
def YANK(side):            # one arm hauls forward at the chain with the whole trunk behind it. side 1 = his left arm pulls
    a, o = ('L', 'R') if side > 0 else ('R', 'L')
    return dict({'pel_x': -0.05*side, 'pel_y': 0.12, 'pel_z': -0.12, 'pel_yaw': -14*side, 'pel_roll': 5*side, 'twist': -30*side, 'side': -10*side, 'spine': 14, 'spine1': 12, 'spine2': 10,
                 'neck': -8, 'neck_yaw': 10*side, 'head': -6, 'head_yaw': 18*side, 'head_roll': 6*side, 'shoulder_' + a: 14, 'shoulder_' + o: -4, 'claw_' + a: 55, 'claw_' + o: 20, 'hand_' + a: -25,
                 'w%s_x' % a: 0.62*side, 'w%s_y' % a: -0.32, 'w%s_z' % a: 1.24, 'w%s_x' % o: -0.74*side, 'w%s_y' % o: 0.12, 'w%s_z' % o: 1.34,
                 'foot_%s_y' % a: 0.04, 'tremble': 1.2})
WHIP = K(pel_x=0.06, pel_y=0.08, pel_z=-0.10, pel_roll=-6, side=14, twist=8, neck=-6, neck_yaw=-16, head=-4, head_yaw=-30, head_roll=-14, tremble=0.8,
         wL_x=0.72, wL_y=0.0, wL_z=1.34, wR_x=-0.74, wR_y=0.04, wR_z=1.30, claw_L=40, claw_R=40, spine=12, spine1=8, spine2=6)
WHIP2 = K(pel_x=-0.06, pel_y=0.10, pel_roll=6, side=-14, twist=-8, neck_yaw=16, head_yaw=30, head_roll=14, head=-8)
SAG = K(pel_y=0.10, pel_z=-0.17, pel_pitch=3, spine=24, spine1=16, spine2=10, neck=6, head=14, shoulder_L=4, shoulder_R=4,
        wL_x=0.72, wL_y=0.02, wL_z=1.26, wR_x=-0.72, wR_y=0.02, wR_z=1.26, claw_L=20, claw_R=20, hand_L=10, hand_R=10, tremble=0.25, foot_L_y=0.0, foot_R_y=0.0)

THRASH = dict(name='CH_Thrash', length=10.0, loop=True, keys=[
    (0.00, 'smooth', dict(SAG)),
    (0.45, 'inout', K(pel_y=-0.02, pel_z=-0.08, spine=4, spine1=2, spine2=0, neck=-4, head=-4, tremble=0.3)),     # gathers: back against the wall
    (0.72, 'snap', dict(LUNGE)),                                                                                   # goes for you. The chains stop him dead
    (1.40, 'linear', K(pel_y=0.215, spine=21, tremble=1.3)),                                                       # straining, shaking
    (1.75, 'inout', dict(WHIP)),
    (1.95, 'snap', dict(WHIP2)),
    (2.15, 'snap', K(pel_x=0.05, pel_roll=-5, side=12, neck_yaw=-14, head_yaw=-26, head_roll=-12)),
    (2.35, 'snap', K(pel_x=-0.03, pel_roll=2, side=-6, neck_yaw=8, head_yaw=14, head_roll=4)),
    (2.60, 'inout', dict(SLAM)),                                                                                   # thrown back, the wall stops him
    (2.95, 'out', K(tremble=0.4, neck=-10, head=-14)),
    (3.25, 'in2', K(pel_y=0.06, spine=10, spine1=6, spine2=4, neck=-6, head=-2, wL_y=0.10, wR_y=0.0)),
    (3.55, 'inout', YANK(1)),                                                                                       # hauls at the left chain
    (4.05, 'linear', K(pel_y=0.14, twist=-33, tremble=1.5)),
    (4.30, 'inout', K(pel_y=0.05, twist=-10, pel_yaw=-4, pel_x=-0.01, pel_roll=1, side=-3, wL_x=0.72, wL_y=-0.1, wL_z=1.32, head_yaw=4, neck_yaw=2, tremble=0.6, claw_L=30, shoulder_L=6)),
    (4.56, 'inout', dict(YANK(1), tremble=1.3)),                                                                    # and again, harder
    (4.95, 'inout', dict(SAG)),
    (5.35, 'inout', K(pel_y=0.0, spine=6, spine1=4, spine2=2, neck=-6, head=-8, tremble=0.4)),
    (5.66, 'inout', YANK(-1)),                                                                                      # now the right
    (6.15, 'linear', K(pel_y=0.14, twist=33, tremble=1.5)),
    (6.45, 'inout', dict(SLAM)),
    (6.85, 'in2', K(pel_y=0.02, pel_z=-0.10, spine=8, spine1=4, spine2=2, tremble=0.5, wL_y=0.04, wR_y=0.04)),
    (7.10, 'snap', dict(LUNGE, pel_y=0.22, spine=24, neck=-20, head=-16)),                                         # both: the big one, up on the toes
    (7.80, 'linear', K(pel_y=0.235, tremble=1.6, foot_L_z=0.015, foot_R_z=0.015)),
    (8.05, 'inout', dict(WHIP2)),
    (8.25, 'snap', dict(WHIP)),
    (8.45, 'snap', K(pel_x=-0.04, pel_roll=4, side=-10, neck_yaw=12, head_yaw=22, head_roll=10, foot_L_z=0.0, foot_R_z=0.0)),
    (8.75, 'inout', K(pel_x=0.0, pel_roll=0, side=0, neck_yaw=0, head_yaw=4, head_roll=3, pel_y=0.14, pel_z=-0.15, spine=20, spine1=14, spine2=9, neck=2, head=8, tremble=0.5)),
    (10.0, 'inout', dict(SAG)),                                                                                    # panting, head down, watching
])

def free_pose(side):       # the arm 'side' is loose: weight thrown forward against the other three chains
    a, o = ('L', 'R') if side > 0 else ('R', 'L')
    return dict({'pel_x': 0.03*side, 'pel_y': 0.17, 'pel_z': -0.13, 'pel_yaw': -10*side, 'pel_roll': -3*side, 'twist': -14*side, 'side': 4*side, 'spine': 18, 'spine1': 13, 'spine2': 10,
                 'neck': -12, 'neck_yaw': 4*side, 'head': -10, 'head_yaw': 6*side, 'claw_' + a: 52, 'claw_' + o: 34, 'shoulder_' + a: 10, 'shoulder_' + o: -8, 'hand_' + a: -12, 'hand_' + o: -14,
                 'w%s_x' % a: 0.46*side, 'w%s_y' % a: -0.44, 'w%s_z' % a: 1.34, 'w%s_x' % o: -0.70*side, 'w%s_y' % o: -0.06, 'w%s_z' % o: 1.30, 'chain_' + a: 0.0, 'foot_L_y': 0.03, 'foot_R_y': 0.03, 'tremble': 0.7})

def slice_clip(side):      # the blade cuts the chain: recoil from the blow, the arm flies loose, he surges out against what is left
    a, o = ('L', 'R') if side > 0 else ('R', 'L'); s = side
    return dict(name='CH_Slice_' + a, length=1.8, free=a, keys=[
        (0.00, 'smooth', dict(SAG, tremble=0.4)),
        (0.13, 'out', {'pel_x': -0.07*s, 'pel_y': -0.02, 'pel_z': -0.09, 'pel_roll': 8*s, 'pel_yaw': 12*s, 'twist': 20*s, 'side': -12*s, 'spine': 0, 'spine1': -6, 'spine2': -8, 'neck': -18, 'head': -14, 'head_yaw': -22*s, 'head_roll': -10*s, 'claw_' + a: -6,
                        'w%s_x' % a: 0.80*s, 'w%s_y' % a: 0.18, 'w%s_z' % a: 1.50, 'tremble': 0.6}),      # thrown back from the blow
        (0.20, 'out', {'chain_' + a: 0.0, 'w%s_x' % a: 0.92*s, 'w%s_y' % a: 0.02, 'w%s_z' % a: 1.34, 'hand_' + a: 20}),   # chain gone: the arm drops away, it surprises him
        (0.50, 'inout', {'pel_x': 0.02*s, 'pel_y': 0.09, 'pel_roll': 0, 'pel_yaw': 0, 'twist': 0, 'side': 0, 'spine': 10, 'spine1': 8, 'spine2': 4, 'neck': -6, 'head': -4, 'head_yaw': 10*s, 'head_roll': 0, 'w%s_x' % a: 0.86*s, 'w%s_y' % a: -0.14, 'w%s_z' % a: 1.00, 'claw_' + a: 30}),
        (0.80, 'inout', dict(free_pose(s), pel_y=0.235, spine=24, neck=-20, tremble=1.6, **{'w%s_x' % a: 0.30*s, 'w%s_y' % a: -0.70, 'w%s_z' % a: 1.62})),     # realises it: lunges, the free hand goes for you
        (1.30, 'linear', {'pel_y': 0.24, 'tremble': 1.7, 'w%s_x' % a: 0.36*s, 'w%s_y' % a: -0.66, 'w%s_z' % a: 1.56}),
        (1.80, 'inout', dict(free_pose(s))),
    ])

def free_loop(side):       # 6 s: the loose arm rakes, swings wild and hauls on the far chain
    a, o = ('L', 'R') if side > 0 else ('R', 'L'); s = side; FP = free_pose(s); wa = 'w%s_' % a
    return dict(name='CH_Free_' + a, length=6.0, loop=True, free=a, keys=[
        (0.00, 'smooth', dict(FP)),
        (0.35, 'inout', {wa + 'x': 0.86*s, wa + 'y': -0.06, wa + 'z': 1.74, 'twist': 6*s, 'pel_y': 0.10, 'shoulder_' + a: 18, 'head_yaw': -4*s}),               # wind-up, high and wide
        (0.66, 'inout', {wa + 'x': 0.16*s, wa + 'y': -0.74, wa + 'z': 1.30, 'twist': -34*s, 'pel_y': 0.23, 'spine': 24, 'spine1': 16, 'head_yaw': 10*s, 'tremble': 1.3}),     # rakes across
        (0.90, 'inout', {wa + 'x': -0.04*s, wa + 'y': -0.52, wa + 'z': 1.06, 'twist': -22*s, 'pel_y': 0.20}),
        (1.25, 'inout', {wa + 'x': 0.70*s, wa + 'y': -0.30, wa + 'z': 1.12, 'twist': -2*s, 'pel_y': 0.12, 'tremble': 0.8}),
        (1.52, 'inout', {wa + 'x': 0.44*s, wa + 'y': -0.70, wa + 'z': 1.58, 'twist': -22*s, 'pel_y': 0.22, 'tremble': 1.2}),                                     # snatch at the air
        (1.72, 'inout', {wa + 'x': 0.54*s, wa + 'y': -0.56, wa + 'z': 1.36, 'twist': -16*s, 'pel_y': 0.17}),
        (1.92, 'inout', {wa + 'x': 0.34*s, wa + 'y': -0.74, wa + 'z': 1.50, 'twist': -26*s, 'pel_y': 0.23, 'tremble': 1.4}),
        (2.30, 'inout', {wa + 'x': 0.40*s, wa + 'y': -0.30, wa + 'z': 1.50, 'twist': -4*s, 'pel_y': 0.06, 'pel_yaw': 4*s, 'spine': 8, 'neck': -6, 'tremble': 0.5}),       # gather
        (2.68, 'inout', {'w%s_x' % o: -0.62*s, 'w%s_y' % o: -0.28, 'w%s_z' % o: 1.24, 'pel_yaw': 16*s, 'twist': 30*s, 'pel_x': 0.05*s, 'pel_y': 0.14, 'spine': 16, 'neck_yaw': -12*s, 'head_yaw': -22*s, 'claw_' + o: 55, 'shoulder_' + o: 14, 'tremble': 1.5,
                        wa + 'x': 0.72*s, wa + 'y': -0.12, wa + 'z': 1.18}),      # hauls at the last arm chain; the free arm helps by bracing out
        (3.20, 'linear', {'pel_y': 0.15, 'twist': 33*s, 'tremble': 1.7}),
        (3.45, 'inout', {'w%s_x' % o: -0.72*s, 'w%s_y' % o: -0.02, 'w%s_z' % o: 1.34, 'pel_yaw': 2*s, 'twist': 4*s, 'pel_x': 0.0, 'pel_y': 0.06, 'neck_yaw': 0, 'head_yaw': 0, 'claw_' + o: 34, 'shoulder_' + o: 0, 'tremble': 0.6}),
        (3.72, 'inout', {'w%s_x' % o: -0.62*s, 'w%s_y' % o: -0.28, 'w%s_z' % o: 1.24, 'pel_yaw': 14*s, 'twist': 28*s, 'pel_x': 0.04*s, 'pel_y': 0.14, 'neck_yaw': -10*s, 'head_yaw': -20*s, 'claw_' + o: 55, 'shoulder_' + o: 14, 'tremble': 1.6}),      # again
        (4.15, 'inout', {'w%s_x' % o: -0.70*s, 'w%s_y' % o: -0.06, 'w%s_z' % o: 1.30, 'pel_yaw': -10*s, 'twist': -14*s, 'pel_x': 0.03*s, 'pel_y': 0.12, 'neck_yaw': 4*s, 'head_yaw': 6*s, 'claw_' + o: 34, 'shoulder_' + o: -8, 'tremble': 0.7,
                         wa + 'x': 0.82*s, wa + 'y': -0.02, wa + 'z': 1.66}),
        (4.46, 'inout', {wa + 'x': 0.08*s, wa + 'y': -0.76, wa + 'z': 1.22, 'twist': -36*s, 'pel_y': 0.235, 'spine': 25, 'tremble': 1.4}),                     # rakes again
        (4.75, 'inout', {wa + 'x': -0.02*s, wa + 'y': -0.44, wa + 'z': 1.00, 'twist': -20*s, 'pel_y': 0.17, 'spine': 18}),
        (5.20, 'inout', {wa + 'x': 0.62*s, wa + 'y': -0.42, wa + 'z': 1.30, 'twist': -8*s, 'pel_y': 0.14, 'tremble': 0.6}),
        (6.00, 'inout', dict(FP)),
    ])

def claw(side):            # 1.3 s: the hit that can hurt. Blow on frame 17 (0.57 s), hand 1.0 m out from the hips
    a, o = ('L', 'R') if side > 0 else ('R', 'L'); s = side; FP = free_pose(s); wa = 'w%s_' % a
    return dict(name='CH_Claw_' + a, length=1.3, free=a, keys=[
        (0.00, 'smooth', dict(FP)),
        (0.36, 'inout', {wa + 'x': 0.74*s, wa + 'y': -0.06, wa + 'z': 1.86, 'twist': 12*s, 'pel_y': 0.06, 'spine': 6, 'spine1': 4, 'neck': -10, 'shoulder_' + a: 22, 'claw_' + a: 20, 'head_yaw': -6*s}),
        (0.57, 'in2', {wa + 'x': 0.10*s, wa + 'y': -0.80, wa + 'z': 1.28, 'twist': -38*s, 'pel_y': 0.24, 'pel_z': -0.15, 'spine': 26, 'spine1': 18, 'spine2': 12, 'neck': -22, 'claw_' + a: 58, 'hand_' + a: -18, 'head_yaw': 10*s, 'tremble': 1.0}),
        (0.82, 'out', {wa + 'x': -0.06*s, wa + 'y': -0.50, wa + 'z': 0.98, 'twist': -26*s, 'pel_y': 0.21}),
        (1.30, 'inout', dict(FP)),
    ])

def death(side):           # 7 s, held on its last frame: the second cut. Heat seizure, then he hangs dead in what is left of the chains while the melt takes him
    a, o = ('L', 'R') if side > 0 else ('R', 'L'); s = side; FP = free_pose(s); wa = 'w%s_' % a; wo = 'w%s_' % o
    return dict(name='CH_Death_' + a, length=7.0, free=a, keys=[
        (0.00, 'smooth', dict(FP)),
        (0.20, 'inout', {'pel_y': 0.0, 'pel_z': -0.05, 'pel_pitch': -7, 'pel_yaw': 0, 'pel_roll': 0, 'twist': 0, 'side': 0, 'spine': -8, 'spine1': -12, 'spine2': -12, 'neck': -24, 'head': -22, 'head_yaw': 0, 'neck_yaw': 0, 'claw_' + a: 70, 'claw_' + o: 70, 'hand_' + a: 24, 'hand_' + o: 24,
                        wa + 'x': 0.74*s, wa + 'y': 0.10, wa + 'z': 1.66, wo + 'x': -0.76*s, wo + 'y': 0.12, wo + 'z': 1.46, 'shoulder_L': 12, 'shoulder_R': 12, 'tremble': 2.2}),    # every muscle locks
        (1.10, 'linear', {'pel_z': -0.06, 'spine': -9, 'tremble': 2.6}),
        (1.70, 'inout', {'pel_y': 0.10, 'pel_z': -0.22, 'pel_pitch': 4, 'spine': 18, 'spine1': 12, 'spine2': 6, 'neck': 2, 'head': 4, 'claw_' + a: 30, 'claw_' + o: 30, 'hand_' + a: 4, 'hand_' + o: 4, wa + 'x': 0.60*s, wa + 'y': -0.14, wa + 'z': 1.00, wo + 'y': 0.04, wo + 'z': 1.22, 'shoulder_L': 0, 'shoulder_R': 0, 'tremble': 0.9}),   # goes
        (2.40, 'out', {'pel_y': 0.14, 'pel_z': -0.40, 'pel_roll': 6*s, 'side': 8*s, 'spine': 30, 'spine1': 22, 'spine2': 14, 'neck': 18, 'head': 26, 'head_roll': 14*s, 'claw_' + a: 18, 'claw_' + o: 18, 'hand_' + a: 34, 'hand_' + o: 34, wa + 'x': 0.40*s, wa + 'y': -0.12, wa + 'z': 0.72, wo + 'x': -0.70*s, wo + 'y': 0.06, wo + 'z': 1.06, 'tremble': 0.25}),   # hangs by the last arm chain
        (7.00, 'linear', {'pel_z': -0.46, 'pel_y': 0.15, 'tremble': 0.0}),
    ])

def mirror(sp):            # not used for authored L/R, kept for checks
    return sp

CLIPS = [THRASH]
for s_ in (1, -1):
    CLIPS += [slice_clip(s_), free_loop(s_), claw(s_), death(s_)]

if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--')+1:]; RIG, OUT = a[:2]; WANT = a[2:]
    os.makedirs(OUT, exist_ok=True)
    for sp in CLIPS:
        if WANT and sp['name'] not in WANT: continue
        arm = zrig.load_rig(RIG)
        author(arm, sp, OUT)
    json.dump(LAYOUT, open(os.path.join(OUT, 'layout.json'), 'w'), indent=1)
