# Vesna #380 step 2: APPLY (imports 8 textures, makes RT/material/portrait capture, BPC_VesnaTrade + hero components).
import sys, os, unreal
R = r'C:\Users\hossa\Documents\agent-office\handoffs\vesna-trade-361\build'
p = os.path.join(R, 'setup_vesnatrade_ue.py'); sys.argv = ['x']
import re
src = re.sub(r'(?m)^DRY_RUN\s*=\s*True', 'DRY_RUN = False', open(p, encoding='utf-8').read())
assert 'DRY_RUN = False' in src, 'could not flip DRY_RUN'
exec(compile(src, p, 'exec'), {'__name__': '__main__', '__file__': p})
rep = open(os.path.join(R, 'setup_vesnatrade.txt'), encoding='utf-8', errors='replace').read()
unreal.log('VESNA APPLY REPORT (mode line must say DRY_RUN = False)\n' + rep)
unreal.log('VESNA: next = open BPC_VesnaTrade EventGraph, Ctrl+V the contents of BPC_VesnaTrade_graph.txt, Refresh All Nodes, Compile, Save. Then p3_merge.py')
