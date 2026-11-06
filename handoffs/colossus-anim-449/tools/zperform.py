# zperform.py - pose-to-pose performance authoring for the SK_Zombie rig (zombies / colossus; adjustedfilm).
# Same design as the brute's bl_perform: key poses at key times, per-channel curves, eases, per-group overlap lags,
# a tremble channel. Angles in degrees, positions in metres (at scale 1; the colossus is scaled x3.9-5.8 in game).
import math, bpy
from mathutils import Vector, Quaternion
import zpose as P, zrig

BASE = {   # the base stance: a hulking, slightly crouched zombie (arms hang out from the body, elbows bent)
    'pel_x': 0.0, 'pel_y': 0.0, 'pel_z': -0.10, 'pel_yaw': 0.0, 'pel_pitch': 0.0, 'pel_roll': 0.0,
    'spine': 13.0, 'spine1': 11.0, 'spine2': 8.0, 'twist': 0.0, 'side': 0.0,
    'neck': -2.0, 'neck_yaw': 0.0, 'head': 2.0, 'head_yaw': 0.0, 'head_roll': 0.0,
    'shoulder_L': 0.0, 'shoulder_R': 0.0,
    'arm_in_L': 70.0, 'arm_in_R': 70.0, 'arm_sw_L': 22.0, 'arm_sw_R': 22.0, 'arm_tw_L': 0.0, 'arm_tw_R': 0.0,
    'elbow_L': 34.0, 'elbow_R': 34.0, 'hand_L': 0.0, 'hand_R': 0.0, 'claw_L': 20.0, 'claw_R': 20.0,
    'foot_L_x': 0.04, 'foot_L_y': 0.0, 'foot_L_z': 0.0, 'foot_R_x': -0.04, 'foot_R_y': 0.0, 'foot_R_z': 0.0,
    'tremble': 0.0, 'foot_free': 0.0,
}
GROUP_LAG = {'pel': 0.0, 'spine': 0.0, 'spine1': 0.02, 'spine2': 0.04, 'twist': 0.03, 'side': 0.03, 'neck': 0.07, 'head': 0.11,
             'shoulder': 0.05, 'arm': 0.07, 'elbow': 0.12, 'hand': 0.16, 'claw': 0.20, 'foot': 0.0, 'tremble': 0.0}
LAG_SCALE = 1.0   # the colossus: longer lags (set by the author script)

def group(ch):
    for g in sorted(GROUP_LAG, key=len, reverse=True):
        if ch.startswith(g): return g
    return 'pel'

EASES = {
    'smooth': lambda x: x*x*(3-2*x),
    'in': lambda x: x**3,
    'in2': lambda x: x**2,
    'out': lambda x: 1-(1-x)**3,
    'inout': lambda x: 4*x**3 if x < 0.5 else 1-(-2*x+2)**3/2,
    'snap': lambda x: 1-(1-x)**5,
    'linear': lambda x: x,
}

class Performance:
    def __init__(self, keys, length):
        self.length = length; self.curves = {ch: [] for ch in BASE}
        ks = sorted(keys, key=lambda k: k[0])
        for i, (t, ease, ch) in enumerate(ks):
            for c in BASE:
                if i == 0: self.curves[c].append((t, ease, ch.get(c, BASE[c])))
                elif c in ch: self.curves[c].append((t, ease, ch[c]))
    def value(self, ch, t):
        t = t - GROUP_LAG[group(ch)]*LAG_SCALE
        ks = self.curves[ch]
        if t <= ks[0][0]: return ks[0][2]
        for (t0, _, a), (t1, ease, b) in zip(ks, ks[1:]):
            if t <= t1:
                x = (t - t0)/max(1e-6, t1 - t0); return a + (b - a)*EASES[ease](x)
        return ks[-1][2]
    def params(self, t): return {ch: self.value(ch, t) for ch in BASE}

class Body:
    """applies a parameter dict to the rig (feet by IK, planted unless their channels move)."""
    def __init__(self, arm):
        self.arm = arm; P.rest_all(arm)
        self.home = {s: P.wpos(arm, P.LEGS[s][2]) for s in 'LR'}
        self.frot = {s: P.world_rot(arm, P.LEGS[s][2]) for s in 'LR'}
        self.pel0 = P.pel_quat(arm)
    def apply(self, q, t=0.0):
        arm = self.arm; P.rest_all(arm)
        tr = q['tremble']
        n1 = math.sin(2*math.pi*9.1*t) + 0.6*math.sin(2*math.pi*13.7*t+1.3)
        n2 = math.sin(2*math.pi*7.3*t+0.7) + 0.5*math.sin(2*math.pi*11.9*t+2.1)
        P.pel_move(arm, (q['pel_x'], -q['pel_y'], q['pel_z']))
        P.pel_rot(arm, P.UP, q['pel_yaw']); P.pel_rot(arm, P.LEFT, q['pel_pitch']); P.pel_rot(arm, P.FWD, q['pel_roll'])
        for b, k, kt in (('Spine', 'spine', 0.25), ('Spine1', 'spine1', 0.35), ('Spine2', 'spine2', 0.40)):
            P.rot(arm, b, P.LEFT, q[k] + 0.6*tr*n1)
            P.rot(arm, b, P.UP, q['twist']*kt); P.rot(arm, b, P.FWD, q['side']*kt + 0.4*tr*n2)
        P.rot(arm, 'Neck', P.LEFT, q['neck']); P.rot(arm, 'Neck', P.UP, q['neck_yaw'])
        P.rot(arm, 'Head', P.LEFT, q['head'] + 1.2*tr*n2); P.rot(arm, 'Head', P.UP, q['head_yaw'] + 0.8*tr*n1); P.rot(arm, 'Head', P.FWD, q['head_roll'])
        for s, sg in (('L', 1.0), ('R', -1.0)):
            sh, ua, fa, hd = P.ARMS[s]
            P.rot(arm, sh, P.FWD, -sg*q['shoulder_' + s])                      # shrug: shoulder_ > 0 lifts the shoulder
            P.rot(arm, ua, P.FWD, -sg*q['arm_in_' + s])                        # from the T-pose down to the side
            P.rot(arm, ua, P.LEFT, -q['arm_sw_' + s])                          # arm_sw > 0 = forward / up
            P.rot(arm, ua, P.UP, sg*q['arm_tw_' + s])
            P.rot(arm, fa, P.LEFT, -q['elbow_' + s] + 1.5*tr*n1)
            P.rot(arm, hd, P.LEFT, q['hand_' + s])
            for fb in P.FINGERS[s]:
                if fb in arm.pose.bones: P.rot_local(arm, fb, 0, q['claw_' + s]*(0.6 if 'Thumb' in fb else 1.0))
        R = P.pel_quat(arm) @ self.pel0.inverted()
        for s, sg in (('L', 1.0), ('R', -1.0)):
            tgt = self.home[s] + Vector((q['foot_%s_x' % s], -q['foot_%s_y' % s], q['foot_%s_z' % s]))
            P.leg_ik(arm, s, tgt, knee_dir=R @ (P.FWD + P.LEFT*sg*0.15), n_hint=R @ P.LEFT)
            ff = max(0.0, min(1.0, q['foot_free']))
            if ff < 1.0:
                cur = P.world_rot(arm, P.LEGS[s][2]); P.set_world_rot(arm, P.LEGS[s][2], self.frot[s].slerp(cur, ff))

def checks(arm, n, name):
    sc = bpy.context.scene; pops = []; prev = None; kn = []
    for f in range(1, n+1):
        sc.frame_set(f); cur = {pb.name: pb.matrix_basis.to_quaternion() for pb in arm.pose.bones}
        if prev: pops.append(max(((lambda _a: min(_a, 360-_a))(math.degrees(cur[b].rotation_difference(prev[b]).angle)), b, f) for b in cur))
        prev = cur
        for sd in 'LR': kn.append(P.knee_angle(arm, sd))
    print('PERF %s frames %d | worst bone turn %.1f deg/frame (%s @%d) | knee %.0f..%.0f' % ((name, n) + max(pops) + (min(kn), max(kn))))

def author(arm, perf, name, fps=30):
    body = Body(arm); n = int(round(perf.length*fps)) + 1
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions.new(name)
    for f in range(n):
        t = f/float(fps); body.apply(perf.params(t), t); zrig.key(arm, frame=f+1)
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, n; sc.render.fps = fps
    checks(arm, n, name)
    return n
