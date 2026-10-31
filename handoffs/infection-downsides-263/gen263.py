# #263 (checkking, 2026-10-31): infection downsides on the hero (owner keeps the +50 % defense below 30 % HP).
#   python gen263.py -> Hero_InfectionDownsides_graph.txt + manifest_hero_263.json   (apply AFTER #255's hero paste)
# While BPC_Infection.Infected (the hero's "Infection" component, already read by the hero's damage code):
#   1. walk speed x0.75: at the top of Tick, CharacterMovement.MaxWalkSpeed = BaseWalkSpeed x (Infected ? 0.75 : 1).
#      BaseWalkSpeed (new hero BPVar, default 0) is captured from MaxWalkSpeed on the first tick.
#   2. 25 % of sword hits miss: the sword damage (WdMulSlash from #255) x (Infected AND Random < 0.25 ? 0 : 1) into ZX8/ZX9.
import os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
INF = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Infection', 'BPC_Infection')
CMC_ = CLS('CharacterMovementComponent')
DBL = D('v', default='0.0')

G = Graph(); b = bpkit.B(G, 'ix')
sequence(G, 'InfTickIn', 2, 0, 0)
inf = b.get('Infection', ob('v', INF), 0, 300)
infected = b.getm('Infected', INF, bo('v', default='false'), inf, 250, 300)
cm = b.getm('CharacterMovement', CHARC, ob('v', CMC_), b.self_node(0, 500), 250, 500)
cur = b.getm('MaxWalkSpeed', CMC_, fl('v', default='0.0'), cm, 500, 500)
need = b.dcmp('LessEqual_DoubleDouble', b.get('BaseWalkSpeed', DBL, 500, 650), None, 750, 650, db='0.0')
bb = b.branch(need, 300, 0, tag='IfNoBase'); G.link('InfTickIn', 'then_1', bb, 'execute')
sb = b.set('BaseWalkSpeed', DBL, cur, 600, -200); G.link(bb, 'then', sb, 'execute')
spd = b.d2('Multiply_DoubleDouble', b.get('BaseWalkSpeed', DBL, 800, 300), b.self_(None, None, infected, 800, 450, da='0.75', db='1.0'), 1000, 350)
ss = b.setm('MaxWalkSpeed', CMC_, fl('v', default='0.0'), spd, cm, 1100, 0)
G.link(sb, 'then', ss, 'execute'); G.link(bb, 'else', ss, 'execute')
roll = b.rnd('0.0', '1.0', 0, 900)
miss = b.b2('BooleanAND', infected, b.dcmp('Less_DoubleDouble', roll, None, 250, 900, db='0.25'), 450, 900)
mathfn(G, 'InfMissMul', 'Multiply_DoubleDouble', [D('A', default='0.0'), D('B', default='1.0'), D('ReturnValue', out=True)], 800, 900)
b.wire(b.self_(None, None, miss, 650, 950, da='0.0', db='1.0'), 'InfMissMul', 'B')
open(os.path.join(HERE, 'Hero_InfectionDownsides_graph.txt'), 'w', newline='\r\n').write(G.render())
json.dump({'blueprint': 'BP_ThirdPersonCharacter', '_apply': 'after #255 (weapon damage): uses its WdMulSlash node',
           'pastes': ['Hero_InfectionDownsides_graph.txt'], 'rewires': [
  {'from': 'K2Node_Event_ZX10.then', 'to': 'InfTickIn.execute', 'replace': True, 'note': 'Tick -> infection slow first'},
  {'from': 'InfTickIn.then_0', 'to': 'K2Node_IfThenElse_ZX12.execute'},
  {'from': 'WdMulSlash.ReturnValue', 'to': 'InfMissMul.A'},
  {'from': 'InfMissMul.ReturnValue', 'to': 'K2Node_CallFunction_ZX8.BaseDamage', 'replace': True},
  {'from': 'InfMissMul.ReturnValue', 'to': 'K2Node_CallFunction_ZX9.BaseDamage', 'replace': True}]},
  open(os.path.join(HERE, 'manifest_hero_263.json'), 'w'), indent=1)
REAL = 'PinCategory="real",PinSubCategory="double"'
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('# BP_ThirdPersonCharacter - paste on the VARIABLES header\nBPVar(VarName="BaseWalkSpeed",VarGuid=%s,VarType=(%s),PropertyFlags=5,DefaultValue="0.0")\n' % (uuid.uuid4().hex.upper(), REAL))
print('infection downsides: nodes', len(G.nodes))
