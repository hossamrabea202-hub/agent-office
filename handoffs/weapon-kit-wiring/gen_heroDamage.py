# Weapon kit part 2 (checkking, 2026-10-31): the equipped weapon changes the hero's hit damage.
# BP_ThirdPersonCharacter (10-30b export): K2Node_CallFunction_XL20 (Add_DoubleDouble, base 35 + bonuses) feeds the two sword
# ApplyRadialDamage calls (ZX8, ZX9); K2Node_CallFunction_CH7 (ApplyDamage) has a fixed 35.
# WeaponMul = Equipped >= 0 ? Damage[Equipped] / 40 : 1      (Arming Sword 40 = x1.0, Zweihander 80 = x2.0, Rondel 28 = x0.7)
#   XL20 -> x WeaponMul -> ZX8 / ZX9 BaseDamage;  35 x WeaponMul -> CH7 BaseDamage.  All pure, no casts.
#   python gen_heroDamage.py -> Hero_WeaponDamage_graph.txt + manifest_hero_damage.json
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit', 'BPC_WeaponKit')
INT = it('v', default='0')

G = Graph(); b = bpkit.B(G, 'wd')
me = b.self_node(0, 0)
kit = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit.BPC_WeaponKit_C'),
             ob('ReturnValue', KIT, out=True)], 200, 0, target=me, pure=True, const=True, tag='Kit')
eq = b.getm('Equipped', KIT, INT, (kit, 'ReturnValue'), 450, 0)
dmg = b.getm('Damage', KIT, arr(INT), (kit, 'ReturnValue'), 450, 150)
gi = 'WdItem'; G.node(gi, 'K2Node_GetArrayItem', [], [arr(dict(INT, name='Array')), it('Dimension 1', default='0'), dict(INT, name='Output', out=True)], 700, 150)
b.wire(dmg, gi, 'Array'); b.wire(b.i2('Max', eq, None, 650, 300, db='0'), gi, 'Dimension 1')
per = b.d2('Divide_DoubleDouble', b.i2d((gi, 'Output'), 900, 150), None, 1100, 150, db='40.0')
mul = b.self_(per, None, b.icmp('GreaterEqual_IntInt', eq, None, 1100, 300, db='0'), 1300, 200, db='1.0')
mathfn(G, 'WdMulSlash', 'Multiply_DoubleDouble', [D('A', default='0.0'), D('B', default='1.0'), D('ReturnValue', out=True)], 1500, 100); b.wire(mul, 'WdMulSlash', 'B')
mathfn(G, 'WdMulHit', 'Multiply_DoubleDouble', [D('A', default='35.0'), D('B', default='1.0'), D('ReturnValue', out=True)], 1500, 300); b.wire(mul, 'WdMulHit', 'B')
open(os.path.join(HERE, 'Hero_WeaponDamage_graph.txt'), 'w', newline='\r\n').write(G.render())
json.dump({'blueprint': 'BP_ThirdPersonCharacter', '_built_on': 'handoffs/exports/master/2026-10-30b/BP_ThirdPersonCharacter_EventGraph.txt',
           'pastes': ['Hero_WeaponDamage_graph.txt'], 'rewires': [
  {'from': 'K2Node_CallFunction_XL20.ReturnValue', 'to': 'WdMulSlash.A'},
  {'from': 'WdMulSlash.ReturnValue', 'to': 'K2Node_CallFunction_ZX8.BaseDamage', 'replace': True},
  {'from': 'WdMulSlash.ReturnValue', 'to': 'K2Node_CallFunction_ZX9.BaseDamage', 'replace': True},
  {'from': 'WdMulHit.ReturnValue', 'to': 'K2Node_CallFunction_CH7.BaseDamage', 'replace': True}]},
  open(os.path.join(HERE, 'manifest_hero_damage.json'), 'w'), indent=1)
print('hero weapon damage: nodes', len(G.nodes))
