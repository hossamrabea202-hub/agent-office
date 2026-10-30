# #220 (checkking, 2026-10-30 night): redo of #205/#181's soldier unstick for BP_SoldierSword (the commander inherits it).
# #205 used `Goal` as an Actor, but in BP_SoldierSword `Goal` is a SceneComponent whose RelativeLocation is a formation
# offset. The real move target is the vector CX_86 (MakeVector) that the soldier's own order feeds into
# SimpleMoveToLocation (CX_399). This detector reads that same vector (wired in by the manifest through a reroute knot):
#   top of Tick: target > 1.5 m away (XY) and speed < 15 cm/s -> StuckT += dt, else StuckT = 0
#   StuckT > 1.5 s -> nudge 60 cm toward the target (swept, +10 cm up for the door sill), SimpleMoveToLocation(target)
#   again (same controller as CX_399), StuckT = 0.
# StuckT and RVO avoidance (radius 200) are already in (Master, #205).
#   python gen220.py -> SoldierSword_Unstick220_graph.txt (manifest_soldiersword.json)
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
DBL = D('v', default='0.0')

G = Graph(); b = B(G, 'un')
seq = b.seq('Unstick220In', 2, 0, 0)
G.node('UnstickTarget', 'K2Node_Knot', [], [V('InputPin'), V('OutputPin', out=True)], 200, 500)
G.node('UnstickCtl', 'K2Node_Knot', [], [ob('InputPin', CTRL), ob('OutputPin', CTRL, out=True)], 200, 650)
tgt = ('UnstickTarget', 'OutputPin')
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 250, 300, ACT, pure=True, const=True, tag='MyLoc')
d = b.math('VSizeXY', [(V('A'), b.v2('Subtract_VectorVector', tgt, (me, 'ReturnValue'), 500, 400))], D('ReturnValue', out=True), 700, 400)
far = b.dcmp('Greater_DoubleDouble', d, None, 900, 400, db='150.0')
vel = b.call_self('GetVelocity', [V('ReturnValue', out=True)], 500, 600, ACT, pure=True, const=True, tag='Vel')
slow = b.dcmp('Less_DoubleDouble', b.math('VSize', [(V('A'), (vel, 'ReturnValue'))], D('ReturnValue', out=True), 750, 600), None, 1000, 600, db='15.0')
br = b.branch(b.b2('BooleanAND', far, slow, 1200, 450), 1400, 0, 'IfStuck'); G.link(seq, 'then_0', br, 'execute')
dt = b.d2('Multiply_DoubleDouble', None, None, 1400, 300, da='0.016', db='1.0')
s1 = b.set('StuckT', DBL, b.d2('Add_DoubleDouble', b.get('StuckT', DBL, 1400, 450), dt, 1650, 350), 1900, 0)
s0 = b.set('StuckT', DBL, None, 1900, 200)
G.link(br, 'then', s1, 'execute'); G.link(br, 'else', s0, 'execute')
br2 = b.branch(b.dcmp('Greater_DoubleDouble', b.get('StuckT', DBL, 2100, 300), None, 2300, 300, db='1.5'), 2500, 0, 'IfLong')
G.link(s1, 'then', br2, 'execute')
dirv = b.math('Normal', [(V('A'), b.v2('Subtract_VectorVector', tgt, (me, 'ReturnValue'), 2600, 600)), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 2850, 600)
step = b.math('Multiply_VectorFloat', [(V('A'), dirv), (D('B', default='60.0'), None)], V('ReturnValue', out=True), 3050, 600)
dest = b.v2('Add_VectorVector', b.v2('Add_VectorVector', (me, 'ReturnValue'), step, 3250, 600), None, 3450, 600, db='0, 0, 10')
mv = b.call_self('K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='true'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='false'), bo('ReturnValue', out=True)], 2800, 0, ACT, tag='Nudge')
b.wire(dest, mv, 'NewLocation')
rm = b.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], 3100, 0, tag='ReMove')
b.wire(('UnstickCtl', 'OutputPin'), rm, 'Controller'); b.wire(tgt, rm, 'Goal')
s2 = b.set('StuckT', DBL, None, 3400, 0)
G.link(br2, 'then', mv, 'execute'); G.link(mv, 'then', rm, 'execute'); G.link(rm, 'then', s2, 'execute')
open(os.path.join(HERE, 'SoldierSword_Unstick220_graph.txt'), 'w', newline='\r\n').write(G.render())
import json
json.dump({'blueprint': 'BP_SoldierSword', '_built_on': 'handoffs/exports/master/2026-10-30b/BP_SoldierSword.T3D (EventGraph)',
           'pastes': ['SoldierSword_Unstick220_graph.txt'], 'rewires': [
  {'from': 'CX_135.then', 'to': 'Unstick220In.execute', 'replace': True, 'note': 'Tick -> unstick first (was CX_139)'},
  {'from': 'Unstick220In.then_1', 'to': 'CX_139.execute', 'note': 'then the original Tick chain'},
  {'from': 'CX_135.DeltaSeconds', 'to': dt[0] + '.A', 'note': 'dt into the accumulator'},
  {'from': 'CX_86.ReturnValue', 'to': 'UnstickTarget.InputPin', 'note': "the soldier's own move target (what CX_399 moves to)"},
  {'from': 'K2Node_CallFunction_2.ReturnValue', 'to': 'UnstickCtl.InputPin', 'note': 'the controller CX_399 uses'}]},
          open(os.path.join(HERE, 'manifest_soldiersword.json'), 'w'), indent=1)
print('unstick 220: nodes', len(G.nodes), 'links', len(G.links))
