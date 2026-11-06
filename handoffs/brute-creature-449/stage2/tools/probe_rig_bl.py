# Blender probe: analytic IK sanity (no keys).
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_rig, bl_pose as P
from mathutils import Vector
a = sys.argv[sys.argv.index('--')+1:]
arm = bl_rig.load_rig(a[0], keep_mesh=False)
P.rest_all(arm)
home = {s: P.wpos(arm, P.LEGS[s][4]) for s in 'LR'}
frot = {s: (arm.matrix_world @ arm.pose.bones[P.LEGS[s][4]].matrix).to_quaternion() for s in 'LR'}
toe0 = {s: P.wpos(arm, P.LEGS[s][5]) for s in 'LR'}
P.move(arm, 'spine_01', (0, 0, -0.12))
for s in 'LR':
    e = P.leg_ik(arm, s, home[s], knee_dir=P.FWD)
    P.set_world_rot(arm, P.LEGS[s][4], frot[s])
    knee = P.wpos(arm, P.LEGS[s][2]); hip = P.wpos(arm, P.LEGS[s][0]); ank = P.wpos(arm, P.LEGS[s][4])
    print('CROUCH', s, 'ankle err', round(e, 4), 'toe drift', round((P.wpos(arm, P.LEGS[s][5]) - toe0[s]).length, 4),
          'knee fwd', round((knee - (hip+ank)*0.5).dot(P.FWD), 3))
# step forward test: left ankle 30 cm forward, 10 cm up
e = P.leg_ik(arm, 'L', home['L'] + P.FWD*0.30 + P.UP*0.10, knee_dir=P.FWD)
print('STEP L err', round(e, 4))
print('PROBE OK')
