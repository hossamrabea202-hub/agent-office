# Author CR_Idle_Hunt: a living predator idle for the Flesh Brute (#449 stage 2, adjustedfilm).
# blender -b -P author_idle.py -- <SK.fbx> <out.fbx>
# Stranger Things-style beats: heavy slow breath, a weight shift between planted feet, a slow scan, a sudden head-tilt
# twitch (fast in, hold, slow out), a sniff, and arms that sway a beat late with a claw flex. Seamless 4 s loop.
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_rig, bl_pose as P
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--')+1:]; SK, OUT = a[0], a[1]

N = 120                    # 4.0 s
CROUCH = 0.10; WIDTH = 0.05; LEAN = (14.0, 12.0, 9.0)
BREATH_N = 2               # breaths per loop (2 s each: slow and heavy)
SHIFT = 0.035              # m weight shift
SCAN = 11.0                # deg slow head scan
TWITCH = (0.38, 13.0)      # (time as loop fraction, roll deg) the head tilt
SNIFF = (0.70, 4.0)        # (time, nod deg) quick double sniff
CLAW = (0.80, 22.0)        # (time, finger curl deg)
ARM_IN, ELBOW = 22.0, 16.0

arm = bl_rig.load_rig(SK, keep_mesh=False); P.rest_all(arm)
home = {s: P.wpos(arm, P.LEGS[s][4]) for s in 'LR'}
frot = {s: (arm.matrix_world @ arm.pose.bones[P.LEGS[s][4]].matrix).to_quaternion() for s in 'LR'}
SIDE = {'L': 1.0, 'R': -1.0}
FINGERS = [b.name for b in arm.pose.bones if b.name.startswith(('f_', 'thumb'))]

def pulse(p, t0, rise, hold, fall):
    """0..1 event: fast rise, hold, slow fall (seconds), wrapping round the loop."""
    t = P.wrap(p - t0)*N/30.0
    if t < rise: return P.ease(t/rise)
    if t < rise+hold: return 1.0
    if t < rise+hold+fall: return 1.0 - P.ease((t-rise-hold)/fall)
    return 0.0

def pose_frame(f):
    p = f/float(N); P.rest_all(arm)
    br = 0.5 - 0.5*math.cos(2*math.pi*BREATH_N*p)                        # inhale 0..1
    br_sharp = br**1.6                                                    # quick top of the inhale, long sag
    shift = SHIFT*math.sin(2*math.pi*p)
    P.move(arm, 'spine_01', (shift, 0.0, -CROUCH - 0.012*br))
    P.rot(arm, 'spine_01', P.FWD, 2.5*math.sin(2*math.pi*p))             # hips roll with the shift
    P.rot(arm, 'spine_01', P.UP, 2.0*math.sin(2*math.pi*(p-0.15)))
    for b, lean, k in (('spine_02', LEAN[0], 0.3), ('spine_03', LEAN[1], 0.6), ('spine_04', LEAN[2], 1.0)):
        P.rot(arm, b, P.LEFT, lean - 2.2*br_sharp*k)                      # the chest lifts on the inhale
        P.rot(arm, b, P.FWD, -1.2*math.sin(2*math.pi*p)*k)               # counter the hip roll
    for s in 'LR':
        P.rot(arm, 'shoulder_' + s, P.FWD, SIDE[s]*3.0*br_sharp)         # shoulders rise with the breath
    # head: scan, twitch tilt (fast in 0.12 s, hold 0.5 s, slow out 0.9 s), double sniff
    scan = SCAN*math.sin(2*math.pi*(p - 0.1))
    tw = pulse(p, TWITCH[0], 0.12, 0.50, 0.90)
    sn = pulse(p, SNIFF[0], 0.08, 0.0, 0.10) + pulse(p, SNIFF[0] + 0.25*30/N, 0.08, 0.0, 0.14)
    P.rot(arm, 'neck', P.LEFT, -4.0 + 1.5*br)
    P.rot(arm, 'neck', P.UP, scan*0.45)
    P.rot(arm, 'head', P.LEFT, -sum(LEAN)*0.42 - 1.0*br + SNIFF[1]*sn + 2.0*tw)
    P.rot(arm, 'head', P.UP, scan*0.55 + 5.0*tw)
    P.rot(arm, 'head', P.FWD, TWITCH[1]*tw)
    # arms: hang in, sway a beat after the hips, claw flex
    claw = pulse(p, CLAW[0], 0.25, 0.35, 0.6)
    for s in 'LR':
        sg = SIDE[s]; lag = math.sin(2*math.pi*(p - 0.12))
        P.rot(arm, 'upper_arm_01_' + s, P.FWD, -sg*ARM_IN + 2.5*lag)
        P.rot(arm, 'upper_arm_01_' + s, P.LEFT, -3.0*br)
        P.rot(arm, 'forearm_01_' + s, P.LEFT, -ELBOW - 4.0*claw)
        P.rot(arm, 'hand_' + s, P.LEFT, 6.0*claw)
    for fb in FINGERS:   # curl about the hand's own lateral axis
        side = 'L' if fb.endswith('_L') else 'R'
        P.rot(arm, fb, P.LEFT, CLAW[1]*claw*(0.6 if fb.startswith('thumb') else 1.0))
    # feet stay planted
    for s in 'LR':
        tgt = home[s] + Vector((SIDE[s]*WIDTH, 0, 0))
        P.leg_ik(arm, s, tgt, knee_dir=P.FWD + P.LEFT*SIDE[s]*0.2)
        P.set_world_rot(arm, P.LEGS[s][4], frot[s])

sc = bpy.context.scene; arm.animation_data_create()
arm.animation_data.action = bpy.data.actions.new('CR_Idle_Hunt')
for f in range(N+1):
    pose_frame(f % N); P.key(arm, frame=f+1)
sc.frame_start, sc.frame_end = 1, N+1; sc.render.fps = 30
drift = 0.0
for f in (1, 30, 60, 90):
    sc.frame_set(f)
    for s in 'LR': drift = max(drift, (P.wpos(arm, P.LEGS[s][5]) - P.wpos(arm, P.LEGS[s][5])).length)
print('IDLE ok frames', N+1)
bl_rig.export_anim(arm, OUT, 1, N+1)
print('AUTHOR OK', OUT)
