# #315 Vesna's shop: A / D also swipe the trade carousel (adjustedfilm, 2026-10-31; owner card).
#   "<blender python>" -I gen_swipe315.py -> SkillTreeHUD_SwipeAD_graph.txt, manifest_skilltreehud_swipe.json
# The carousel (MPC_SkillTree 'Trade') already flips on the Left / Right arrow keys and the on-screen arrows while the
# shop is open (CX_1375 Left -> CX_1376 OR -> CX_1377 -> CX_1382; CX_1379 Right -> CX_1380 OR -> CX_1381 -> CX_1395, in the
# 10-30b BP_SkillTreeHUD export). This adds A next to Left and D next to Right: 4 nodes, 6 links, no re-paste.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
G = Graph(); b = bpkit.B(G, 'sw')
for i, (name, key) in enumerate((('SwipeKeyA', 'A'), ('SwipeKeyD', 'D'))):
    callfn(G, name, PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default=key), bo('ReturnValue', out=True, default='false')], pure=True, const=True, x=0, y=i * 200)
    mathfn(G, 'SwipeOr' + key, 'BooleanOR', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True)], 300, i * 200)
    G.link(name, 'ReturnValue', 'SwipeOr' + key, 'B')
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
assert all((l[0], l[1]) in pins and (l[2], l[3]) in pins for l in G.links)
open(os.path.join(HERE, 'SkillTreeHUD_SwipeAD_graph.txt'), 'w', newline='\r\n').write(G.render())
json.dump({'blueprint': 'BP_SkillTreeHUD', '_built_on': 'handoffs/exports/master/2026-10-30b/BP_SkillTreeHUD_EventGraph.txt',
           'pastes': ['SkillTreeHUD_SwipeAD_graph.txt'],
           'rewires': [{'from': 'CX_14.ReturnValue', 'to': 'SwipeKeyA.self'}, {'from': 'CX_14.ReturnValue', 'to': 'SwipeKeyD.self'},
                       {'from': 'CX_1375.ReturnValue', 'to': 'SwipeOrA.A'},
                       {'from': 'SwipeOrA.ReturnValue', 'to': 'CX_1376.B', 'replace': True, 'note': 'was <- CX_1375 (Left)'},
                       {'from': 'CX_1379.ReturnValue', 'to': 'SwipeOrD.A'},
                       {'from': 'SwipeOrD.ReturnValue', 'to': 'CX_1380.B', 'replace': True, 'note': 'was <- CX_1379 (Right)'}]},
          open(os.path.join(HERE, 'manifest_skilltreehud_swipe.json'), 'w'), indent=1)
print('SkillTreeHUD swipe: nodes %d, links %d' % (len(G.nodes), len(G.links)))
