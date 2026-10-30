# #214 (checkking, 2026-10-30 night): the golden crossbow fires like a machine gun.
# BP_Crossbow fires on IA_XbowFire Started: CX_106 (cast hero) -> CX_114 (LoadedBolt visible AND no montage) -> CX_123
# trace -> CX_138 spawn bolt ... A hard fire-rate gate is added whatever retriggers it:
#   CX_106.then -> CoolIf (GameTime >= NextFireAt) -> CX_114          (else: the click is ignored)
#   CX_114.then -> SetNextFire (NextFireAt = GameTime + FireCooldown) -> CX_123
# FireCooldown (default 1.0 s, about the old crossbow's 0.35 + 1.05 s reload) and NextFireAt are new BP_Crossbow
# variables: add_vars_214.py makes them.
#   python gen214.py -> Xbow_FireGate_graph.txt (manifest_crossbow.json)
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
DBL = D('v', default='0.0')

G = Graph(); b = bpkit.B(G, 'xf')
now = b.now(0, 200)
ok = b.dcmp('GreaterEqual_DoubleDouble', now, b.get('NextFireAt', DBL, 0, 350), 250, 250)
branch(G, 'CoolIf', 300, 0); b.wire(ok, 'CoolIf', 'Condition')
nxt = b.d2('Add_DoubleDouble', b.now(500, 500), b.get('FireCooldown', DBL, 500, 650), 750, 550)
varset(G, 'SetNextFire', None, 'NextFireAt', None, dict(DBL, name='NextFireAt'), 900, 300, self_ctx=True)
b.wire(nxt, 'SetNextFire', 'NextFireAt')
open(os.path.join(HERE, 'Xbow_FireGate_graph.txt'), 'w', newline='\r\n').write(G.render())
print('fire gate: nodes', len(G.nodes), 'links', len(G.links))
