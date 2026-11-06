# zidle.py - a living idle for the SK_Zombie walkers (adjustedfilm, #519). blender -b -P zidle.py -- <rig.fbx> <out.fbx>
# Seamless 4 s loop (119 intervals like ZA_Idle_A so the blend space sample keeps its length): a slow sway on planted feet,
# ragged breathing, the head lolling and searching, a sudden twitch (fast in, hold, slow out), a jaw-forward sniff, the
# arms hanging and reaching a beat late, the claws flexing. Feet at GROUND (the ZA clips sit 5 cm under z = 0).
import bpy, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig, zpose as P, zperform
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--')+1:]; RIG, OUT = a[0], a[1]

N = 119; GROUND = -0.05; CROUCH = 0.10; WIDTH = 0.04; LEAN = (14.0, 12.0, 9.0)
BREATH_N = 3; SWAY = 0.03; SHIFT = 0.025; SCAN = 14.0
TWITCH = (0.42, 12.0); SNIFF = (0.72, 5.0); CLAW = (0.80, 22.0)
ARM_IN, ELBOW, ARM_SW = 72.0, 30.0, 18.0
for _k, _v in json.loads(os.environ.get('Z_OVR', '{}')).items(): globals()[_k] = tuple(_v) if isinstance(_v, list) else _v
NAME = os.environ.get('Z_NAME', 'ZW_Idle_Shamble')

arm = zrig.load_rig(RIG); P.rest_all(arm)
home = {s: P.wpos(arm, P.LEGS[s][2]) + Vector((0, 0, GROUND)) for s in 'LR'}
frot = {s: P.world_rot(arm, P.LEGS[s][2]) for s in 'LR'}
SIDE = {'L': 1.0, 'R': -1.0}

def pulse(p, t0, rise, hold, fall):
    t = P.wrap(p - t0)*N/30.0
    if t < rise: return P.ease(t/rise)
    if t < rise+hold: return 1.0
    if t < rise+hold+fall: return 1.0 - P.ease((t-rise-hold)/fall)
    return 0.0

def pose_frame(f):
    p = f/float(N); P.rest_all(arm)
    br = 0.5 - 0.5*math.cos(2*math.pi*BREATH_N*p); br_sharp = br**1.6
    shift = SHIFT*math.sin(2*math.pi*p); sway = SWAY*math.sin(2*math.pi*(p - 0.25))
    P.pel_move(arm, (shift, -sway*0.4, -CROUCH - 0.010*br + GROUND))
    P.pel_rot(arm, P.FWD, 2.5*math.sin(2*math.pi*p)); P.pel_rot(arm, P.UP, 2.0*math.sin(2*math.pi*(p-0.15)))
    P.pel_rot(arm, P.LEFT, 2.0*math.sin(2*math.pi*(p-0.25)))
    for b, lean, k in zip(P.SPINE, LEAN, (0.3, 0.6, 1.0)):
        P.rot(arm, b, P.LEFT, lean - 2.0*br_sharp*k); P.rot(arm, b, P.FWD, -1.2*math.sin(2*math.pi*p)*k)
    for s in 'LR': P.rot(arm, P.ARMS[s][0], P.FWD, SIDE[s]*2.5*br_sharp)
    scan = SCAN*math.sin(2*math.pi*(p - 0.1)); tw = pulse(p, TWITCH[0], 0.10, 0.45, 0.90)
    sn = pulse(p, SNIFF[0], 0.08, 0.0, 0.10) + pulse(p, SNIFF[0] + 0.25*30/N, 0.08, 0.0, 0.14)
    P.rot(arm, 'Neck', P.LEFT, -2.0 + 1.5*br); P.rot(arm, 'Neck', P.UP, scan*0.45)
    P.rot(arm, 'Head', P.LEFT, -sum(LEAN)*0.35 - 1.0*br + SNIFF[1]*sn + 2.0*tw)
    P.rot(arm, 'Head', P.UP, scan*0.55 + 5.0*tw); P.rot(arm, 'Head', P.FWD, TWITCH[1]*tw + 6.0*math.sin(2*math.pi*(p - 0.3)))
    claw = pulse(p, CLAW[0], 0.25, 0.35, 0.6)
    for s in 'LR':
        sg = SIDE[s]; lag = math.sin(2*math.pi*(p - 0.12)); sh, ua, fa, hd = P.ARMS[s]
        P.rot(arm, ua, P.FWD, -sg*ARM_IN + 2.5*lag); P.rot(arm, ua, P.LEFT, -ARM_SW - 3.0*br)
        P.rot(arm, fa, P.LEFT, -ELBOW - 4.0*claw); P.rot(arm, hd, P.LEFT, 6.0*claw)
        for fb in P.FINGERS[s]:
            if fb in arm.pose.bones: P.rot_local(arm, fb, 0, (12.0 + CLAW[1]*claw)*(0.6 if 'Thumb' in fb else 1.0))
    for s in 'LR':
        P.leg_ik(arm, s, home[s] + Vector((SIDE[s]*WIDTH, 0, 0)), knee_dir=P.FWD + P.LEFT*SIDE[s]*0.2, n_hint=P.LEFT)
        P.set_world_rot(arm, P.LEGS[s][2], frot[s])

sc = bpy.context.scene; arm.animation_data_create(); arm.animation_data.action = bpy.data.actions.new(NAME)
for f in range(N+1):
    pose_frame(f % N); zrig.key(arm, frame=f+1)
sc.frame_start, sc.frame_end = 1, N+1; sc.render.fps = 30
zperform.checks(arm, N+1, NAME)
zrig.export_anim(arm, OUT, 1, N+1); print('AUTHOR OK', OUT)
