# #217 (checkking, 2026-10-30 night): crossbow bolts float in the air.
# BP_CrossbowBolt on hit: StopMovement -> Deactivate -> SetCollisionEnabled (CX_14) -> SetLifeSpan 8 (CX_16) -> ... ->
# attach to what it hit (CX_51 / CX_81 / CX_91). When that zombie despawns, the bolt is detached and hangs where it was.
# Fix (paste, spliced after CX_14 instead of CX_16): SetLifeSpan 5 -> looping 0.2 s timer "BoltCheckParent" -> CX_21.
# BoltCheckParent: no attach parent any more (the target is gone, or it never attached) -> destroy the bolt.
#   python gen217.py -> Bolt_ParentCheck_graph.txt (manifest_crossbowbolt.json)
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

G = Graph(); b = bpkit.B(G, 'bt')
G.node('BoltLife5', 'K2Node_CallFunction', ['FunctionReference=(MemberParent=%s,MemberName="SetLifeSpan")' % ACT],
       [ex(), ex('then', True), selfpin(ACT, hidden=False), fl('InLifespan', default='5.0')], 0, 0)
tm = b.timer('BoltCheckParent', 300, 0, dtime='0.2', loop=True)
G.nodes[-1] = ('BoltTimer',) + G.nodes[-1][1:]
G.links = [(('BoltTimer' if a == tm else a), pa, ('BoltTimer' if c == tm else c), pc) for a, pa, c, pc in G.links]
G.link('BoltLife5', 'then', 'BoltTimer', 'execute')
seq = b.seq('BoltOut', 1, 650, 0); G.link('BoltTimer', 'then', seq, 'execute')

b.event('BoltCheckParent', [], 0, 400)
par = b.call(ACT, 'GetAttachParentActor', [ob('ReturnValue', ACT, out=True)], 0, 600, pure=True, const=True, tag='Parent')
gone = b.bnot(b.valid((par, 'ReturnValue'), 250, 600), 450, 600)
br = b.branch(gone, 300, 400, tag='IfGone'); G.link('BoltCheckParent', 'then', br, 'execute')
G.node('BoltDestroy', 'K2Node_CallFunction', ['FunctionReference=(MemberParent=%s,MemberName="K2_DestroyActor")' % ACT],
       [ex(), ex('then', True), selfpin(ACT, hidden=False)], 600, 400)
G.link(br, 'then', 'BoltDestroy', 'execute')

open(os.path.join(HERE, 'Bolt_ParentCheck_graph.txt'), 'w', newline='\r\n').write(G.render())
print('bolt fix: nodes', len(G.nodes), 'links', len(G.links))
