# zwalk.py - in-place gait for the SK_Zombie rig; defaults = the COLOSSUS walk (adjustedfilm, #449 follow-up).
# blender -b -P zwalk.py -- <clip_rig.fbx> <out.fbx>     env Z_OVR = JSON overrides, Z_NAME = clip name
# The colossus is the zombie rig scaled x3.9-5.8 (GiantScale) with MaxWalkSpeed 90. In-place at scale 1 the feet must
# move at 90 / GiantScale cm/s, and a 9 m body steps at about sqrt(5) = 2.2x a human's period. Design (RESEARCH.md):
# ponderous cadence, long double support, a fast impact drop and a slow recovery on each footfall, wide sway, late heavy
# arms, counter-rotating chest, stabilised head. A looping clip: last frame = first.
import bpy, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig, zpose as P
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--')+1:]; RIG, OUT = a[0], a[1]

# ---------------- PARAMS (scale-1 metres / degrees) ----------------
GIANT = 4.85          # design scale (midpoint of 3.9..5.8)
SPEED = 90.0/GIANT    # cm/s at scale 1 = 18.6
N = 78                # frames per cycle (2.6 s: a step every 1.3 s)
STANCE = 0.66
LIFT = 0.07
WIDTH = 0.05
CROUCH = 0.12
FWD_BIAS = 0.06
DIP = 0.045
RISE = 0.02
SWAY = 0.06
YAW, ROLL = 8.0, 6.0
LEAN = (16.0, 13.0, 10.0)
COUNTER = 0.5
NOD = 3.5
ARM_IN = 70.0
ELBOW = 32.0
ARM_SWING, ARM_LAG = 10.0, 0.12
FORE_SWING, FORE_LAG = 8.0, 0.18
HEAD_STAB = 0.7
HEAD_UP = -6.0
TOE_OFF = 10.0
CLAW = 18.0
IMPACT_FAST, IMPACT_SLOW = 0.12, 0.30   # s: the drop, the recovery
for _k, _v in json.loads(os.environ.get('Z_OVR', '{}')).items(): globals()[_k] = tuple(_v) if isinstance(_v, list) else _v
NAME = os.environ.get('Z_NAME', 'CZ_Walk_Colossus')
D = SPEED*N/30.0*STANCE/100.0

arm = zrig.load_rig(RIG); P.rest_all(arm)
home = {s: P.wpos(arm, P.LEGS[s][2]) for s in 'LR'}
toe_rest = {s: P.wpos(arm, P.LEGS[s][3]) for s in 'LR'}
frot = {s: P.world_rot(arm, P.LEGS[s][2]) for s in 'LR'}
REST_HEAD = P.wpos(arm, 'Head'); REST_PEL = P.pel_pos(arm)
OFF = {'L': 0.0, 'R': 0.5}; SIDE = {'L': 1.0, 'R': -1.0}

def impact(u):
    t = u*N/30.0
    if t < 0: return 0.0
    if t < IMPACT_FAST: return P.ease(t/IMPACT_FAST)
    return math.exp(-(t-IMPACT_FAST)/IMPACT_SLOW)

def foot(side, p):
    u = P.wrap(p - OFF[side]); h = home[side]
    x = h.x + SIDE[side]*WIDTH
    if u < STANCE:
        s = u/STANCE; fwd = D*(0.5 - s) + FWD_BIAS; z = h.z
        heel = TOE_OFF*P.ease((s-0.6)/0.4) if s > 0.6 else 0.0
    else:
        s = (u-STANCE)/(1-STANCE)
        fwd = D*(-0.5 + (0.5-0.5*math.cos(math.pi*s))) + FWD_BIAS; z = h.z + LIFT*math.sin(math.pi*s)**1.2
        heel = TOE_OFF*(1-P.ease(s/0.7)) - 4.0*math.sin(math.pi*s)
    return Vector((x, h.y - fwd, z)), heel

def pose_frame(f):
    p = f/float(N); P.rest_all(arm)
    dip = sum(impact(P.wrap(p - OFF[s])) for s in 'LR')
    rise = RISE*math.cos(2*math.pi*(2*p - 0.6))
    sway = SWAY*math.cos(2*math.pi*(p - 0.30))
    P.pel_move(arm, (sway, 0.0, -CROUCH - DIP*dip + rise))
    yaw = -YAW*math.cos(2*math.pi*p); roll = ROLL*math.cos(2*math.pi*(p - 0.30))
    P.pel_rot(arm, P.UP, yaw); P.pel_rot(arm, P.FWD, roll)
    nod = sum(impact(P.wrap(p - OFF[s] - 2.0/N)) for s in 'LR')
    for b, lean, k in zip(P.SPINE, LEAN, (0.2, 0.35, 0.45)):
        P.rot(arm, b, P.LEFT, lean + NOD*nod*k)
        P.rot(arm, b, P.UP, -yaw*COUNTER*k*1.4)
        P.rot(arm, b, P.FWD, -roll*0.35)
    hb = sum(impact(P.wrap(p - OFF[s] - 4.0/N)) for s in 'LR')
    P.rot(arm, 'Neck', P.LEFT, -HEAD_UP*0.6 + NOD*0.6*hb)
    P.rot(arm, 'Head', P.LEFT, -HEAD_UP*0.4 - sum(LEAN)*0.30 + NOD*0.5*hb)
    P.rot(arm, 'Head', P.UP, -yaw*HEAD_STAB*(1-COUNTER)); P.rot(arm, 'Head', P.FWD, -roll*HEAD_STAB*0.65)
    for s in 'LR':
        sg = SIDE[s]; sh, ua, fa, hd = P.ARMS[s]
        sw = -ARM_SWING*math.cos(2*math.pi*(p - OFF[s] - 0.5 - ARM_LAG))
        fs = -FORE_SWING*math.cos(2*math.pi*(p - OFF[s] - 0.5 - FORE_LAG))
        P.rot(arm, sh, P.LEFT, 0.3*sw)
        P.rot(arm, ua, P.FWD, -sg*ARM_IN)
        P.rot(arm, ua, P.LEFT, sw)
        P.rot(arm, fa, P.LEFT, -ELBOW + fs*0.6)
        P.rot(arm, hd, P.LEFT, fs*0.5)
        for fb in P.FINGERS[s]:
            if fb in arm.pose.bones: P.rot_local(arm, fb, 0, CLAW*(0.6 if 'Thumb' in fb else 1.0))
    for s in 'LR':
        tgt, heel = foot(s, p)
        if heel > 0.01:
            toe = Vector((tgt.x, toe_rest[s].y + (tgt.y - home[s].y), toe_rest[s].z + (tgt.z - home[s].z)))
            v = home[s] - toe_rest[s]; v = Quaternion(P.LEFT, -math.radians(heel)) @ v
            tgt = toe + v
        P.leg_ik(arm, s, tgt, knee_dir=P.FWD + P.LEFT*SIDE[s]*0.15, n_hint=P.LEFT)
        P.set_world_rot(arm, P.LEGS[s][2], Quaternion(P.LEFT, -math.radians(heel)) @ frot[s])

sc = bpy.context.scene; arm.animation_data_create()
arm.animation_data.action = bpy.data.actions.new(NAME)
for f in range(N+1):
    pose_frame(f % N); zrig.key(arm, frame=f+1)
sc.frame_start, sc.frame_end = 1, N+1; sc.render.fps = 30
sk = []
for f in range(1, N+1):
    sc.frame_set(f); a0 = {s: P.wpos(arm, P.LEGS[s][3]) for s in 'LR'}
    sc.frame_set(f+1); a1 = {s: P.wpos(arm, P.LEGS[s][3]) for s in 'LR'}
    for s in 'LR':
        u = P.wrap((f-1)/N - OFF[s])
        if 0.05 < u < STANCE*0.7: sk.append(abs((a1[s].y - a0[s].y)*30*100 - SPEED))
sc.frame_set(1); hp = P.wpos(arm, 'Head'); pp = P.pel_pos(arm)
print('WALK lean: head is %.2f m ahead of the pelvis (rest %.2f); hips z %.3f' % (-(hp.y-pp.y), -(REST_HEAD.y-REST_PEL.y), pp.z))
import zperform; zperform.checks(arm, N+1, NAME)
print('WALK check: planted-toe speed error cm/s max %.2f (0 = no skate); stride D %.2f m; speed %.1f cm/s at scale 1 (%.0f at x%.2f); footfalls L frame 1, R frame %d' % (max(sk), D, SPEED, SPEED*GIANT, GIANT, int(N*0.5)+1))
zrig.export_anim(arm, OUT, 1, N+1)
print('AUTHOR OK', OUT)
