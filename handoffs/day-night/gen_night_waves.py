# Night waves: when a new wave is rolled (BP_ZombieWaveManager, WV_105: ToSpawn = ToSpawn + Round(x)), the added count is
# x 1.5 while BP_DayNight says it is night (integer: Round * 3 / 2). Pure data insert between WV_104 (Round) and CX_15.B.
#   python gen_night_waves.py -> WaveManager_Night_graph.txt + manifest_waves.json
import os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
P_DN = '/Game/CastleDefender/Environment/DayNight/BP_DayNight'
DNC = BPC(P_DN, 'BP_DayNight')
G = Graph(); b = B(G, 'nw')
dn = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_DN)), ob('ReturnValue', DNC, out=True)], 0, 300, pure=True, tag='FindDayNight')
isn = b.b2('BooleanAND', b.valid((dn, 'ReturnValue'), 300, 250), b.getm('IsNight', DNC, BOOL, (dn, 'ReturnValue'), 300, 400), 600, 300)
mult = b.math('SelectInt', [(it('A', default='3'), None), (it('B', default='2'), None), (bo('bPickA', default='false'), isn)], it('ReturnValue', out=True), 900, 300)
m1 = b.i2('Multiply_IntInt', None, mult, 1200, 0, da='0')                 # A <- WV_104.ReturnValue (the rolled count)
m2 = b.i2('Divide_IntInt', m1, None, 1500, 0, db='2')                     # -> CX_15.B
open(os.path.join(HERE, 'WaveManager_Night_graph.txt'), 'w', encoding='utf-8').write(G.render())
json.dump({'blueprint': 'BP_ZombieWaveManager', 'pastes': ['WaveManager_Night_graph.txt'], 'rewires': [
  {'from': 'WV_104.ReturnValue', 'to': m1[0] + '.A', 'note': 'the rolled wave count'},
  {'from': m2[0] + '.ReturnValue', 'to': 'CX_15.B', 'replace': True, 'note': 'x1.5 at night into ToSpawn = ToSpawn + count'}]},
  open(os.path.join(HERE, 'manifest_waves.json'), 'w'), indent=1)
print('night waves', len(G.nodes), 'nodes', m1[0], m2[0])
