# #519 stage 4 (adjustedfilm, 2026-11-06): paste + manifest for BP_Zombie (export #518, 11-06 09:24): the 11 death picks
# that play blob-rise montages (AM_ZDeath_ZA_Burst_A-K, AM_ZDeath_ZA_Laying_Idle_B) play the 4 new death montages instead
# (made by zw_deaths_ue.py): Back x3, Side x3, Crumple x3, Collapse x2 (+ AM_ZDeath_A_Death, which already holds the
# collapse since #521). Each old Montage_Play node is bypassed by a pasted one with the new montage; nothing else moves.
#   python gen_zd519.py   (Blender's python is fine)
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
ANIMI, MONT = CLS('AnimInstance'), CLS('AnimMontage')
RET = '"/Script/CoreUObject.Enum\'/Script/Engine.EMontagePlayReturnType\'"'
DP = '/Game/CastleDefender/Characters/Enemies/Zombie/Anim/Death/'
asset = lambda n: '%s%s.%s' % (DP, n, n)
# old node -> (its exec source pin, new montage key). From the #518 export: every old node's then -> K2Node_CallFunction_ZB76,
# self <- PsAnimInst.ReturnValue; the exec source is CX_1xx.then, except _21 which hangs on CX_165.else.
OLD = {
    'K2Node_CallFunction_12': ('CX_133.then', 'Back'), 'K2Node_CallFunction_15': ('CX_145.then', 'Back'), 'K2Node_CallFunction_18': ('CX_157.then', 'Back'),
    'K2Node_CallFunction_13': ('CX_137.then', 'Side'), 'K2Node_CallFunction_16': ('CX_149.then', 'Side'), 'K2Node_CallFunction_19': ('CX_161.then', 'Side'),
    'K2Node_CallFunction_14': ('CX_141.then', 'Crumple'), 'K2Node_CallFunction_17': ('CX_153.then', 'Crumple'), 'K2Node_CallFunction_20': ('CX_165.then', 'Crumple'),
    'K2Node_CallFunction_21': ('CX_165.else', 'Collapse'), 'K2Node_CallFunction_10': ('CX_123.then', 'Collapse'),
}
G = Graph(); b = B(G, 'zd')
rew = []
for i, (old, (src, key)) in enumerate(OLD.items()):
    n = b.call(ANIMI, 'Montage_Play', [dict(ob('MontageToPlay', MONT), dobj=asset('AM_ZDeath_ZW_' + key)), fl('InPlayRate', default='1.000000'),
                                       {'name': 'ReturnValueType', 'cat': 'byte', 'obj': RET, 'default': 'MontageLength'},
                                       fl('InTimeToStartMontageAt', default='0.000000'), bo('bStopAllMontages', default='true'), fl('ReturnValue', out=True, default='0.0')],
               0, i*260, tag='Death' + key)
    rew.append({'from': src, 'to': n + '.execute', 'replace': True, 'note': 'death pick %s: was %s' % (key, old)})
    rew.append({'from': n + '.then', 'to': 'K2Node_CallFunction_ZB76.execute', 'note': 'then as before'})
    rew.append({'from': 'PsAnimInst.ReturnValue', 'to': n + '.self', 'note': 'the anim instance'})
name = 'BP_Zombie_ZD519_graph.txt'
open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print(name, len(G.nodes), 'nodes')
json.dump({'blueprint': 'BP_Zombie', 'pastes': [name], 'rewires': rew}, open(os.path.join(HERE, 'manifest_zd519.json'), 'w'), indent=1)
print('manifest_zd519.json', len(rew), 'rewires')
