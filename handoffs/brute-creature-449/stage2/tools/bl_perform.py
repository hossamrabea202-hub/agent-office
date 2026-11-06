# bl_perform.py - pose-to-pose performance authoring for the Flesh Brute (#449 stage 2, adjustedfilm).
# A clip = key poses (parameter dicts) at key times, each segment with its own easing, plus per-group time lags for
# overlap/follow-through and an optional tremble. This is how hand animators block and spline a creature shot.
import math, bpy
from mathutils import Vector, Quaternion
import bl_pose as P

# every channel the brute's body is posed with (degrees / metres). Missing channels in a key = the previous key's value.
BASE = {  # the idle's base pose (CR_Idle_Hunt frame 0, close enough to blend in 0.2 s)
    'pel_x': 0.0, 'pel_y': 0.0, 'pel_z': -0.10, 'pel_yaw': 0.0, 'pel_pitch': 0.0, 'pel_roll': 0.0,
    's2': 14.0, 's3': 12.0, 's4': 9.0, 'twist': 0.0, 'side': 0.0,
    'neck': -4.0, 'neck_yaw': 0.0, 'head': -14.7, 'head_yaw': 0.0, 'head_roll': 0.0,
    'shoulder_L': 0.0, 'shoulder_R': 0.0,
    'arm_in_L': 22.0, 'arm_in_R': 22.0, 'arm_sw_L': 0.0, 'arm_sw_R': 0.0, 'arm_tw_L': 0.0, 'arm_tw_R': 0.0,
    'elbow_L': 16.0, 'elbow_R': 16.0, 'hand_L': 0.0, 'hand_R': 0.0, 'claw_L': 0.0, 'claw_R': 0.0,
    'foot_L_x': 0.05, 'foot_L_y': 0.0, 'foot_L_z': 0.0, 'foot_R_x': -0.05, 'foot_R_y': 0.0, 'foot_R_z': 0.0,
    'tremble': 0.0, 'foot_free': 0.0,   # foot_free 1 = the feet go limp and follow the legs (falls)
}
GROUP_LAG = {  # seconds each group trails the body (overlap / follow-through)
    'pel': 0.0, 's2': 0.0, 's3': 0.02, 's4': 0.04, 'twist': 0.03, 'side': 0.03, 'neck': 0.06, 'head': 0.09,
    'shoulder': 0.05, 'arm': 0.06, 'elbow': 0.10, 'hand': 0.13, 'claw': 0.16, 'foot': 0.0, 'tremble': 0.0,
}
def group(ch):
    for g in sorted(GROUP_LAG, key=len, reverse=True):
        if ch.startswith(g): return g
    return 'pel'

EASES = {
    'smooth': lambda x: x*x*(3-2*x),
    'in': lambda x: x**3,                         # slow out of the pose, whip into the next
    'in2': lambda x: x**2,                        # strikes: accelerates through 5-6 frames (readable, not a pop)
    'out': lambda x: 1-(1-x)**3,                  # fast off, long settle (recoveries)
    'inout': lambda x: 4*x**3 if x < 0.5 else 1-(-2*x+2)**3/2,
    'snap': lambda x: 1-(1-x)**5,                 # the impact: there almost at once
    'linear': lambda x: x,
}

class Performance:
    def __init__(self, keys, length):
        """keys: list of (time_s, ease_into_this_key, {channel: value}). The first key is usually BASE."""
        # per-channel curves, like an animator's graph editor: a channel only has keys where a pose sets it, so a key
        # for the feet does not freeze the arms (the first key is the base pose for every channel)
        self.length = length; self.curves = {ch: [] for ch in BASE}
        ks = sorted(keys, key=lambda k: k[0])
        for i, (t, ease, ch) in enumerate(ks):
            for c in BASE:
                if i == 0: self.curves[c].append((t, ease, ch.get(c, BASE[c])))
                elif c in ch: self.curves[c].append((t, ease, ch[c]))
    def value(self, ch, t):
        t = t - GROUP_LAG[group(ch)]
        ks = self.curves[ch]
        if t <= ks[0][0]: return ks[0][2]
        for (t0, _, a), (t1, ease, b) in zip(ks, ks[1:]):
            if t <= t1:
                x = (t - t0)/max(1e-6, t1 - t0); return a + (b - a)*EASES[ease](x)
        return ks[-1][2]
    def params(self, t):
        return {ch: self.value(ch, t) for ch in BASE}

class Body:
    """applies a parameter dict to the rig (feet by IK, planted unless their channels move)."""
    def __init__(self, arm):
        self.arm = arm; P.rest_all(arm)
        self.home = {s: P.wpos(arm, P.LEGS[s][4]) for s in 'LR'}
        self.frot = {s: (arm.matrix_world @ arm.pose.bones[P.LEGS[s][4]].matrix).to_quaternion() for s in 'LR'}
        self.pel0 = (arm.matrix_world @ arm.pose.bones['spine_01'].matrix).to_quaternion()
        self.n0 = {}
        for s_ in 'LR':
            H = P.wpos(arm, P.LEGS[s_][0]); K = P.wpos(arm, P.LEGS[s_][2]); A = P.wpos(arm, P.LEGS[s_][4])
            self.n0[s_] = (K - H).cross(A - K).normalized()
        self.fingers = {s: [b.name for b in arm.pose.bones if b.name.startswith(('f_', 'thumb')) and b.name.endswith('_' + s)] for s in 'LR'}
    def apply(self, q, t=0.0):
        arm = self.arm; P.rest_all(arm)
        tr = q['tremble']
        n1 = math.sin(2*math.pi*9.1*t) + 0.6*math.sin(2*math.pi*13.7*t+1.3)     # 9-14 Hz muscular tremble
        n2 = math.sin(2*math.pi*7.3*t+0.7) + 0.5*math.sin(2*math.pi*11.9*t+2.1)
        P.move(arm, 'spine_01', (q['pel_x'], -q['pel_y'], q['pel_z']))          # pel_y > 0 = forward
        P.rot(arm, 'spine_01', P.UP, q['pel_yaw']); P.rot(arm, 'spine_01', P.LEFT, q['pel_pitch']); P.rot(arm, 'spine_01', P.FWD, q['pel_roll'])
        for b, k, kt in (('spine_02', 's2', 0.25), ('spine_03', 's3', 0.35), ('spine_04', 's4', 0.40)):
            P.rot(arm, b, P.LEFT, q[k] + 0.6*tr*n1)
            P.rot(arm, b, P.UP, q['twist']*kt); P.rot(arm, b, P.FWD, q['side']*kt + 0.4*tr*n2)
        P.rot(arm, 'neck', P.LEFT, q['neck']); P.rot(arm, 'neck', P.UP, q['neck_yaw'])
        P.rot(arm, 'head', P.LEFT, q['head'] + 1.2*tr*n2); P.rot(arm, 'head', P.UP, q['head_yaw'] + 0.8*tr*n1); P.rot(arm, 'head', P.FWD, q['head_roll'])
        for s, sg in (('L', 1.0), ('R', -1.0)):
            P.rot(arm, 'shoulder_' + s, P.FWD, sg*q['shoulder_' + s])
            P.rot(arm, 'upper_arm_01_' + s, P.FWD, -sg*q['arm_in_' + s])
            P.rot(arm, 'upper_arm_01_' + s, P.LEFT, -q['arm_sw_' + s])            # arm_sw > 0 = forward / up
            P.rot(arm, 'upper_arm_01_' + s, P.UP, sg*q['arm_tw_' + s])
            P.rot(arm, 'forearm_01_' + s, P.LEFT, -q['elbow_' + s] + 1.5*tr*n1)
            P.rot(arm, 'hand_' + s, P.LEFT, q['hand_' + s])
            for fb in self.fingers[s]:
                P.rot(arm, fb, P.LEFT, q['claw_' + s]*(0.6 if fb.startswith('thumb') else 1.0))
        for s, sg in (('L', 1.0), ('R', -1.0)):
            tgt = self.home[s] + Vector((q['foot_%s_x' % s], -q['foot_%s_y' % s], q['foot_%s_z' % s]))
            R = (arm.matrix_world @ arm.pose.bones['spine_01'].matrix).to_quaternion() @ self.pel0.inverted()   # how the hips turned
            P.leg_ik(arm, s, tgt, knee_dir=R @ (P.FWD + P.LEFT*sg*0.2), n_hint=R @ self.n0[s])
            ff = max(0.0, min(1.0, q['foot_free']))
            if ff < 1.0:
                cur = (arm.matrix_world @ arm.pose.bones[P.LEGS[s][4]].matrix).to_quaternion()
                P.set_world_rot(arm, P.LEGS[s][4], self.frot[s].slerp(cur, ff))

def author(arm, perf, name, fps=30):
    body = Body(arm); n = int(round(perf.length*fps)) + 1
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions.new(name)
    for f in range(n):
        t = f/float(fps); body.apply(perf.params(t), t); P.key(arm, frame=f+1)
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, n; sc.render.fps = fps
    # checks: snap per frame, knees never locked, planted feet drift
    pops = []; prev = None; kn = []
    for f in range(1, n+1):
        sc.frame_set(f); cur = {pb.name: pb.matrix_basis.to_quaternion() for pb in arm.pose.bones}
        if prev: pops.append(max(((lambda _a: min(_a, 360-_a))(math.degrees(cur[b].rotation_difference(prev[b]).angle)), b, f) for b in cur))
        prev = cur
        for sd in 'LR':
            H = P.wpos(arm, 'thigh_01_'+sd); K = P.wpos(arm, 'shin_01_'+sd); A = P.wpos(arm, 'foot_'+sd); kn.append(math.degrees((H-K).angle(A-K)))
    print('PERF %s frames %d | worst bone turn %.1f deg/frame (%s @%d) | knee %.0f..%.0f' % ((name, n) + max(pops) + (min(kn), max(kn))))
    return n
