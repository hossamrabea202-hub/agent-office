# Author CR_Walk_Heavy: an in-place heavy lumber for the Flesh Brute, made for ITS body (#449 stage 2, adjustedfilm).
# blender -b -P author_walk.py -- <SK.fbx> <out.fbx> [preview.blend]
# Design (RESEARCH.md): matched to the game speed so the feet don't skate; long crouched stance; a fast drop then a
# slow rise on every footfall (catch the weight); wide sway; chest counter-turn; heavy arms swinging late (overlap);
# a stabilised hunting head. Every number is in the PARAMS block.
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_rig, bl_pose as P
from mathutils import Vector, Quaternion

a = sys.argv[sys.argv.index('--')+1:]
SK, OUT = a[0], a[1]; BLEND = a[2] if len(a) > 2 else None

# ---------------- PARAMS ----------------
SPEED = 71.5          # cm/s, BP_FleshBrute MaxWalkSpeed
N = 46                # frames per cycle at 30 fps (1.53 s, two steps)
STANCE = 0.65         # fraction of the cycle each foot is planted (heavy = long stance)
LIFT = 0.12           # m, foot clearance (heavy creatures shuffle low)
WIDTH = 0.03          # m, wider stance than rest
CROUCH = 0.09         # m, pelvis lowered (bent knees)
DIP = 0.055           # m, impact compression on each footfall
RISE = 0.018          # m, mid-stance rise
SWAY = 0.055          # m, lateral pelvis shift toward the stance foot
YAW, ROLL = 6.0, 4.0  # deg, pelvis
LEAN = (11.0, 10.0, 8.0)  # deg forward on spine_02/03/04 (hunched predator)
COUNTER = 0.55        # chest counter-yaw against the pelvis
NOD = 3.0             # deg spine/head nod on impact, delayed
ARM_IN = 22.0         # deg, arms brought in from the A-pose toward the body
ELBOW = 14.0          # deg, elbows bent
ARM_SWING, ARM_LAG = 13.0, 0.10      # deg, cycle fraction
FORE_SWING, FORE_LAG = 9.0, 0.16
HEAD_STAB = 0.8       # head cancels this much of the body's yaw/roll
HEAD_UP = 0.0         # deg extra head lift (0 = the maw looks ahead and a little down)
TOE_OFF = 22.0        # deg heel lift at push-off

D = SPEED*N/30.0*STANCE/100.0       # m the foot travels back while planted
arm = bl_rig.load_rig(SK, keep_mesh=bool(BLEND))
P.rest_all(arm)
home = {s: P.wpos(arm, P.LEGS[s][4]) for s in 'LR'}
toe_rest = {s: P.wpos(arm, P.LEGS[s][5]) for s in 'LR'}
REST_HEAD = P.wpos(arm, 'head'); REST_PEL = P.wpos(arm, 'spine_01')
frot = {s: (arm.matrix_world @ arm.pose.bones[P.LEGS[s][4]].matrix).to_quaternion() for s in 'LR'}
OFF = {'L': 0.0, 'R': 0.5}
SIDE = {'L': 1.0, 'R': -1.0}

def impact(u):
    """compression after a contact at u=0: fast drop (3 frames), slow heavy recovery."""
    t = u*N/30.0
    if t < 0: return 0.0
    if t < 0.10: return P.ease(t/0.10)
    return math.exp(-(t-0.10)/0.22)

def foot(side, p):
    u = P.wrap(p - OFF[side]); h = home[side]
    x = h.x + SIDE[side]*WIDTH
    if u < STANCE:
        s = u/STANCE; fwd = D*(0.5 - s); z = h.z; lift = 0.0
        heel = TOE_OFF*P.ease((s-0.72)/0.28) if s > 0.72 else 0.0
    else:
        s = (u-STANCE)/(1-STANCE)
        fwd = D*(-0.5 + P.ease(s)); lift = LIFT*math.sin(math.pi*min(1.0, s**0.85)); z = h.z + lift
        heel = TOE_OFF*(1-P.ease(s/0.45)) - 6.0*math.sin(math.pi*s)    # toe swings through, slight toe-up before the slap
    return Vector((x, h.y - fwd, z)), heel      # forward is -Y

def pose_frame(f):
    p = f/float(N)
    P.rest_all(arm)
    # pelvis
    dip = sum(impact(P.wrap(p - OFF[s])) + (impact(P.wrap(p - OFF[s]) - 1.0) if False else 0.0) for s in 'LR')
    rise = RISE*math.cos(2*math.pi*(2*p - 0.3*2))
    sway = SWAY*math.cos(2*math.pi*(p - 0.30))
    P.move(arm, 'spine_01', (sway, 0.0, -CROUCH - DIP*dip + rise))
    yaw = -YAW*math.cos(2*math.pi*p); roll = ROLL*math.cos(2*math.pi*(p - 0.30))
    P.rot(arm, 'spine_01', P.UP, yaw); P.rot(arm, 'spine_01', P.FWD, roll)
    # spine: hunch, counter-turn, delayed nod
    nod = sum(impact(P.wrap(p - OFF[s] - 2.0/N)) for s in 'LR')
    for b, lean, k in (('spine_02', LEAN[0], 0.2), ('spine_03', LEAN[1], 0.35), ('spine_04', LEAN[2], 0.45)):
        P.rot(arm, b, P.LEFT, lean + NOD*nod*k)
        P.rot(arm, b, P.UP, -yaw*COUNTER*k*1.4)
        P.rot(arm, b, P.FWD, -roll*0.35)
    # neck/head: look ahead over the hunch, stabilise, heavy head bounce lags 4 frames
    hb = sum(impact(P.wrap(p - OFF[s] - 4.0/N)) for s in 'LR')
    P.rot(arm, 'neck', P.LEFT, -HEAD_UP*0.6 + NOD*0.6*hb)
    P.rot(arm, 'head', P.LEFT, -HEAD_UP*0.4 - sum(LEAN)*0.30 + NOD*0.5*hb)
    P.rot(arm, 'head', P.UP, -yaw*HEAD_STAB*(1-COUNTER)); P.rot(arm, 'head', P.FWD, -roll*HEAD_STAB*0.65)
    # arms: hang in, bent elbows, late heavy swing opposite to the same-side leg
    for s in 'LR':
        sg = SIDE[s]
        sw = -ARM_SWING*math.cos(2*math.pi*(p - OFF[s] - 0.5 - ARM_LAG))
        fs = -FORE_SWING*math.cos(2*math.pi*(p - OFF[s] - 0.5 - FORE_LAG))
        P.rot(arm, 'shoulder_' + s, P.LEFT, 0.3*sw)
        P.rot(arm, 'upper_arm_01_' + s, P.FWD, -sg*ARM_IN)
        P.rot(arm, 'upper_arm_01_' + s, P.LEFT, sw)
        P.rot(arm, 'forearm_01_' + s, P.LEFT, -ELBOW + fs*0.6)
        P.rot(arm, 'hand_' + s, P.LEFT, fs*0.5)
    # legs last (hips moved)
    for s in 'LR':
        tgt, heel = foot(s, p)
        if heel > 0.01:      # heel lift about the toe: keep the toe planted
            toe = Vector((tgt.x, toe_rest[s].y + (tgt.y - home[s].y), toe_rest[s].z + (tgt.z - home[s].z)))
            v = home[s] - toe_rest[s]; v = Quaternion(P.LEFT, -math.radians(heel)) @ v
            tgt = toe + v
        P.leg_ik(arm, s, tgt, knee_dir=P.FWD + P.LEFT*SIDE[s]*0.15)
        P.set_world_rot(arm, P.LEGS[s][4], Quaternion(P.LEFT, -math.radians(heel)) @ frot[s])

sc = bpy.context.scene
arm.animation_data_create()
act = bpy.data.actions.new('CR_Walk_Heavy'); arm.animation_data.action = act
for f in range(N+1):
    pose_frame(f % N)
    P.key(arm, frame=f+1)
sc.frame_start, sc.frame_end = 1, N+1; sc.render.fps = 30
# check: planted toe skate (world toe y speed vs the ground speed) and IK error
sk = []
for f in range(1, N+1):
    sc.frame_set(f); a0 = {s: P.wpos(arm, P.LEGS[s][5]) for s in 'LR'}
    sc.frame_set(f+1); a1 = {s: P.wpos(arm, P.LEGS[s][5]) for s in 'LR'}
    for s in 'LR':
        u = P.wrap((f-1)/N - OFF[s])
        if 0.05 < u < STANCE*0.7: sk.append(abs((a1[s].y - a0[s].y)*30*100 - SPEED))
sc.frame_set(1); hp = P.wpos(arm, 'head'); pp = P.wpos(arm, 'spine_01')
print('WALK lean: head is %.2f m ahead of the pelvis (rest %.2f)' % (-(hp.y-pp.y), -(REST_HEAD.y-REST_PEL.y)))
print('WALK check: planted-toe speed error cm/s max %.2f (0 = no skate); stride D %.2f m' % (max(sk), D))
bl_rig.export_anim(arm, OUT, 1, N+1)
if BLEND: bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('AUTHOR OK', OUT)
