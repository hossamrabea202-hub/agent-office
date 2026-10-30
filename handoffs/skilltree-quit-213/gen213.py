# #213 (checkking, 2026-10-30 night): clicking UNLOCK in the skill tree quit PIE. Cause (Master's diagnosis): the pause
# menu's invisible Quit row in BP_ZombieHUD (x 0.27-0.73 W, y 0.715-0.80 H) still takes clicks while the skill tree is
# open and covers the same rect. Fix: AND each of the three QuitGame click branches with "skill tree NOT open".
# The skill tree's open flag is MPC_SkillTree.St.R > 0.5 (BP_SkillTreeHUD CX_43 -> CX_48.R -> CX_55, its main draw gate).
# GetVectorParameterValue is an exec node in 5.3 (Master gotcha 3), so each guard is spliced into the exec path:
#   DrawText.then -> StN.execute -> StN.then -> branch.execute;   branch.Condition = old AND  AND  NOT(St.R > 0.5)
#   python gen213.py  ->  ZombieHUD_QuitGuard_graph.txt  (15 nodes) + manifest_zombiehud.json uses it
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'

G = Graph(); b = bpkit.B(G, 'q')
for k in (1, 2, 3):
    y = (k - 1) * 600
    callfn(G, 'QSt%d' % k, MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC),
           {'name': 'ParameterName', 'cat': 'name', 'default': 'St'}, st('ReturnValue', LC, out=True)], x=0, y=y, self_hidden=True)
    mathfn(G, 'QBrk%d' % k, 'BreakColor', [st('InColor', LC)] + [fl(c, out=True, default='0.0') for c in 'RGBA'], 300, y + 150)
    G.link('QSt%d' % k, 'ReturnValue', 'QBrk%d' % k, 'InColor')
    mathfn(G, 'QOpen%d' % k, 'Greater_DoubleDouble', [D('A', default='0.0'), D('B', default='0.5'), bo('ReturnValue', out=True, default='false')], 550, y + 150)
    G.link('QBrk%d' % k, 'R', 'QOpen%d' % k, 'A')
    mathfn(G, 'QNot%d' % k, 'Not_PreBool', [bo('A', default='false'), bo('ReturnValue', out=True, default='false')], 750, y + 150)
    G.link('QOpen%d' % k, 'ReturnValue', 'QNot%d' % k, 'A')
    mathfn(G, 'QAnd%d' % k, 'BooleanAND', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True, default='false')], 950, y + 100)
    G.link('QNot%d' % k, 'ReturnValue', 'QAnd%d' % k, 'B')
open(os.path.join(HERE, 'ZombieHUD_QuitGuard_graph.txt'), 'w', newline='\r\n').write(G.render())
print('quit guard: nodes', len(G.nodes), 'links', len(G.links))
