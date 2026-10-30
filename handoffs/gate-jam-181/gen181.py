# #181 Soldiers (and the commander) get stuck in the gate opening, spinning and jumping. A stuck detector for
# BP_SoldierSword (BP_SoldierCommander is its child, so it gets it too), inserted at the top of Tick:
#   while a Goal actor is set and still > 1.5 m away but the soldier's speed is < 15 cm/s, StuckT accumulates; after
#   1.5 s the soldier is nudged 60 cm toward the goal (swept, +10 cm up so it steps over the door lip) and its move
#   order is re-issued (SimpleMoveToActor), then StuckT resets. Moving normally resets StuckT every frame.
#   python gen181.py -> SoldierSword_Unstick_graph.txt + manifest.json
# Rewires: CX_135.then -> UnstickIn (was CX_139), UnstickIn.then_1 -> CX_139, CX_135.DeltaSeconds -> the dt Multiply.
# Variable to add: StuckT (float 0). Also tick in the Master's checklist: CharacterMovement > bUseRVOAvoidance on both
# soldier BPs (Avoidance Consideration Radius 200) so they stop shoving each other in the 6 m opening.
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
G = Graph(); b = B(G, 'us')
seq = b.seq('UnstickIn', 2, 0, 0)
goal = b.get('Goal', ob('v', ACT), 250, 300)
valid = b.valid(goal, 500, 300)
dist = b.call_self('GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 500, 450, ACT, pure=True, const=True, tag='DistGoal'); b.wire(goal, dist, 'OtherActor')
far = b.dcmp('Greater_DoubleDouble', (dist, 'ReturnValue'), None, 800, 450, db='150.0')
vel = b.call_self('GetVelocity', [V('ReturnValue', out=True)], 500, 600, ACT, pure=True, const=True, tag='Vel')
speed = b.math('VSize', [(V('A'), (vel, 'ReturnValue'))], D('ReturnValue', out=True), 750, 600)
slow = b.dcmp('Less_DoubleDouble', speed, None, 1000, 600, db='15.0')
stuck = b.b2('BooleanAND', b.b2('BooleanAND', valid, far, 1050, 350), slow, 1250, 400)
br = b.branch(stuck, 1500, 0, 'IfStuck'); G.link(seq, 'then_0', br, 'execute')
# accumulate: StuckT += dt (dt arrives by rewire from CX_135.DeltaSeconds into the Multiply's A)
dt = b.d2('Multiply_DoubleDouble', None, None, 1500, 300, da='0.016', db='1.0'); DT = dt
acc = b.d2('Add_DoubleDouble', b.get('StuckT', DBL, 1500, 450), dt, 1750, 350)
s1 = b.set('StuckT', DBL, acc, 2000, 0)
s0 = b.set('StuckT', DBL, None, 2000, 200)          # else: reset (default 0.0)
G.link(br, 'then', s1, 'execute'); G.link(br, 'else', s0, 'execute')
over = b.dcmp('Greater_DoubleDouble', b.get('StuckT', DBL, 2250, 300), None, 2500, 300, db='1.5')
br2 = b.branch(over, 2750, 0, 'IfLong'); G.link(s1, 'then', br2, 'execute')
# nudge toward the goal
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 2750, 500, ACT, pure=True, const=True, tag='MyLoc')
gl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 2750, 650, target=goal, pure=True, const=True, tag='GoalLoc')
dirv = b.math('Normal', [(V('A'), b.v2('Subtract_VectorVector', (gl, 'ReturnValue'), (me, 'ReturnValue'), 3000, 600)), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 3250, 600)
step = b.math('Multiply_VectorFloat', [(V('A'), dirv), (fl('B', default='60.0'), None)], V('ReturnValue', out=True), 3500, 600)
dest = b.v2('Add_VectorVector', b.v2('Add_VectorVector', (me, 'ReturnValue'), step, 3750, 600), None, 4000, 600, db='0, 0, 10')
mv = b.call_self('K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='true'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='false'), bo('ReturnValue', out=True)], 3250, 0, ACT, tag='Nudge'); b.wire(dest, mv, 'NewLocation')
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 3500, 300, PAWN, pure=True, const=True, tag='Ctl')
remove = b.lib(NAVSYS, 'SimpleMoveToActor', [ob('Controller', CTRL), ob('Goal', ACT)], 3700, 0, tag='ReMove'); b.wire((ctl, 'ReturnValue'), remove, 'Controller'); b.wire(goal, remove, 'Goal')
s2 = b.set('StuckT', DBL, None, 4100, 0)
G.link(br2, 'then', mv, 'execute'); G.link(mv, 'then', remove, 'execute'); G.link(remove, 'then', s2, 'execute')
open(os.path.join(HERE, 'SoldierSword_Unstick_graph.txt'), 'w', encoding='utf-8').write(G.render())
import json
json.dump({'blueprint': 'BP_SoldierSword', 'pastes': ['SoldierSword_Unstick_graph.txt'], 'rewires': [
  {'from': 'CX_135.then', 'to': 'UnstickIn.execute', 'replace': True, 'note': 'Tick -> unstick first (was CX_139)'},
  {'from': 'UnstickIn.then_1', 'to': 'CX_139.execute', 'note': 'then the original Tick chain'},
  {'from': 'CX_135.DeltaSeconds', 'to': DT[0] + '.A', 'note': 'dt into the accumulator'}]}, open(os.path.join(HERE, 'manifest.json'), 'w'), indent=1)
print('wrote', len(G.nodes), 'nodes; dt node', DT[0])
