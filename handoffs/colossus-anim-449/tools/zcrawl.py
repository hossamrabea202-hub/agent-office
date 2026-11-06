# zcrawl.py - belly-crawl loops for the SK_Zombie walkers (adjustedfilm, #519 stage 5).
# blender -b -P zcrawl.py -- <rig.fbx> <out.fbx>   env Z_OVR JSON, Z_NAME
# BP_Zombie crawls at MaxWalkSpeed 45 (CX_320) and loops ZA_Belly_Crawling_A or _B (50/50). In place: the planted hand
# must move back at exactly 45 cm/s. Hands by IK (arm_ik), the body prone, the legs trailing and kicking a little.
import bpy, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig, zpose as P, zperform
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--')+1:]; RIG, OUT = a[0], a[1]

SPEED = 45.0          # cm/s
N = 60                # frames per full cycle (both arms), 2.0 s
STANCE = 0.52         # fraction of the cycle a hand is planted
GROUND = -0.05
HIPS_Z = 0.17         # m, hips above the ground (prone)
REACH = 0.95          # m, how far ahead of the hips the hand lands
HAND_X = 0.32         # m, hands out to the sides
LIFT = 0.16           # m, hand clearance on the reach
PITCH = 78.0          # deg, body pitched forward (prone)
ROLL = 7.0            # deg, the body rolls toward the pulling arm
SPINE = (6.0, -4.0, -10.0)   # curl: the chest lifts off the ground
NECK, HEAD = -30.0, -28.0    # look ahead while prone
LEG_BACK = 0.82       # m, feet behind the hips
LEG_X = 0.14
KICK = 0.10           # m, the trailing leg lifts a little in counter-phase
FOOT_FREE = 0.9
DRAG = 0.0            # 1 = one-arm drag variant: the right arm barely pulls, the left does the work
HEAD_SWAY = 6.0
IMPACT = 0.03         # m, the chest drops when a hand lands
for _k, _v in json.loads(os.environ.get('Z_OVR', '{}')).items(): globals()[_k] = tuple(_v) if isinstance(_v, list) else _v
NAME = os.environ.get('Z_NAME', 'ZW_Crawl_A')
D = SPEED*N/30.0*STANCE/100.0     # m the hand travels back while planted

arm = zrig.load_rig(RIG); P.rest_all(arm)
frot = {s: P.world_rot(arm, P.LEGS[s][2]) for s in 'LR'}
OFF = {'L': 0.0, 'R': 0.5}; SIDE = {'L': 1.0, 'R': -1.0}
PULL = {'L': 1.0, 'R': 1.0 - 0.7*DRAG}

def hand(side, p):
    u = P.wrap(p - OFF[side]); d = D*PULL[side]
    x = SIDE[side]*HAND_X
    if u < STANCE:
        s = u/STANCE; fwd = REACH - d*s; z = GROUND + 0.02
    else:
        s = (u-STANCE)/(1-STANCE); fwd = REACH - d + d*(0.5-0.5*math.cos(math.pi*s)); z = GROUND + 0.02 + LIFT*math.sin(math.pi*s)**1.3
    return Vector((x, -fwd, z))

def pose_frame(f):
    p = f/float(N); P.rest_all(arm)
    land = sum(max(0.0, 1.0 - P.wrap(p - OFF[s])*N/9.0) for s in 'LR')     # a hand just landed: the chest dips
    roll = ROLL*math.sin(2*math.pi*p)
    P.pel_move(arm, (0.0, 0.0, -(1.167377 - HIPS_Z) - IMPACT*land*0.5))
    P.pel_rot(arm, P.LEFT, PITCH); P.pel_rot(arm, P.FWD, roll); P.pel_rot(arm, P.UP, -4.0*math.sin(2*math.pi*p))
    for b, k, w in zip(P.SPINE, SPINE, (0.3, 0.5, 0.7)):
        P.rot(arm, b, P.LEFT, k + 3.0*land*w); P.rot(arm, b, P.FWD, -roll*0.4*w); P.rot(arm, b, P.UP, 6.0*math.sin(2*math.pi*p)*w)
    P.rot(arm, 'Neck', P.LEFT, NECK); P.rot(arm, 'Head', P.LEFT, HEAD + 2.0*land); P.rot(arm, 'Head', P.FWD, HEAD_SWAY*math.sin(2*math.pi*(p-0.1)))
    for s in 'LR':
        sg = SIDE[s]; sh, ua, fa, hd = P.ARMS[s]
        P.rot(arm, sh, P.FWD, -sg*8.0)
        tgt = hand(s, p)
        P.arm_ik(arm, s, tgt, elbow_dir=Vector((sg*0.6, 0.0, 1.0)), n_hint=Vector((0.0, -1.0, sg*0.3)))
        P.set_world_rot(arm, hd, Quaternion(P.LEFT, math.radians(-70)) @ Quaternion(P.UP, math.radians(sg*20)) @ P.world_rot(arm, hd).slerp(P.world_rot(arm, hd), 0))
        for fb in P.FINGERS[s]:
            if fb in arm.pose.bones: P.rot_local(arm, fb, 0, 22.0*(0.6 if 'Thumb' in fb else 1.0))
    for s in 'LR':
        sg = SIDE[s]; u = P.wrap(p - OFF[s] + 0.5)
        kick = KICK*max(0.0, math.sin(2*math.pi*u))**1.5
        tgt = Vector((sg*LEG_X, LEG_BACK - 0.04*math.sin(2*math.pi*u), GROUND + 0.03 + kick))
        P.leg_ik(arm, s, tgt, knee_dir=Vector((sg*0.3, 0, 1)), n_hint=P.LEFT)
        cur = P.world_rot(arm, P.LEGS[s][2]); P.set_world_rot(arm, P.LEGS[s][2], frot[s].slerp(cur, FOOT_FREE))

sc = bpy.context.scene; arm.animation_data_create(); arm.animation_data.action = bpy.data.actions.new(NAME)
for f in range(N+1):
    pose_frame(f % N); zrig.key(arm, frame=f+1)
sc.frame_start, sc.frame_end = 1, N+1; sc.render.fps = 30
sk = []
for f in range(1, N+1):
    sc.frame_set(f); a0 = {s: P.wpos(arm, P.ARMS[s][3]) for s in 'LR'}
    sc.frame_set(f+1); a1 = {s: P.wpos(arm, P.ARMS[s][3]) for s in 'LR'}
    for s in 'LR':
        u = P.wrap((f-1)/N - OFF[s])
        if 0.05 < u < STANCE*0.9: sk.append(abs((a1[s].y - a0[s].y)*30*100 - SPEED*PULL[s]))
zperform.checks(arm, N+1, NAME)
sc.frame_set(1); print('CRAWL check: planted-hand speed error cm/s max %.2f; hand travel %.2f m; hips z %.2f; head z %.2f' % (max(sk), D, P.pel_pos(arm).z, P.wpos(arm, 'Head').z))
zrig.export_anim(arm, OUT, 1, N+1); print('AUTHOR OK', OUT)
