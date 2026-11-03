# F11 (Alien's Play test, i9 chat 1205): two log errors x255 each (i5, 2026-11-03). Small pastes + applyall manifests.
#   python gen_f11.py   -> muster_rq3_paste.txt + muster_manifest.json, shield_guard_paste.txt + shield_manifest.json
# BPC_Muster "index 0..2 of array RQ length 0": SetIState / SetINote / SetISub read RQ[0], RQ[1], RQ[2] (vItem210/216/222) behind
#   BooleanAND(RQ.Length > k, RQ[k] == 2). Blueprint's AND does not short-circuit, so RQ[k] is read even when the queue is
#   shorter. Fix: before vSetIState247, copy RQ into RQ3 and Resize RQ3 to max(len, 3) (the padding is 0, never the 2 being
#   compared), and point the three reads at RQ3. Same logic, no out-of-range read.
# BPC_ShieldKit "index -1 of BlockChance": the hit roll vIfBlocked65 reads BlockChance[Worn] with Worn = -1 (no shield).
#   Fix: Branch(Worn >= 0) in front of it; the else path does nothing, exactly like vIfBlocked65's own (empty) else.
import json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
INT = it('v', default='0')
MUSTER = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Muster', 'BPC_Muster')

def out(G, name, label):
    names = {n[0] for n in G.nodes}; pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    if bad: raise SystemExit('bad links %s' % bad)
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print(label, len(G.nodes), 'nodes ->', name)

# ---- BPC_Muster ----
G = Graph(); b = bpkit.B(G, 'f11m')
s1 = b.set('RQ3', arr(INT), b.get('RQ', arr(INT), 0, 200), 300, 0)
n = b.name('ResizeRQ3')
G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Resize")' % KARR],
       [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
        it('Size', default='0')], 700, 0)
b.wire(b.get('RQ3', arr(INT), 400, 250), n, 'TargetArray')
b.wire(b.i2('Max', b.alen('RQ3', INT, 300, 400), None, 600, 400, db='3'), n, 'Size')
G.link(s1, 'then', n, 'execute')
g3 = b.get('RQ3', arr(INT), 700, 550)                       # the getter the three reads switch to
out(G, 'muster_rq3_paste.txt', 'BPC_Muster F11')
setn, getn = s1, g3[0]
json.dump({'blueprint': 'BPC_Muster', 'note': 'F11: pad the recruit queue to 3 before the per-slot reads (needs member variable RQ3: int array)',
           'pastes': ['muster_rq3_paste.txt'],
           'rewires': [{'from': 'vSetIOreBN245.then', 'to': setn + '.execute', 'replace': True, 'note': 'was -> vSetIState247'},
                       {'from': n + '.then', 'to': 'vSetIState247.execute', 'replace': True},
                       {'from': getn + '.RQ3', 'to': 'vItem210.Array', 'replace': True, 'note': 'was vGetRQ136'},
                       {'from': getn + '.RQ3', 'to': 'vItem216.Array', 'replace': True},
                       {'from': getn + '.RQ3', 'to': 'vItem222.Array', 'replace': True}]},
          open(os.path.join(HERE, 'muster_manifest.json'), 'w'), indent=1)

# ---- BPC_ShieldKit ----
G = Graph(); b = bpkit.B(G, 'f11s')
cond = b.icmp('GreaterEqual_IntInt', b.get('Worn', INT, 0, 200), None, 250, 200, db='0')
br = b.branch(cond, 500, 0, tag='IfShieldWorn')
out(G, 'shield_guard_paste.txt', 'BPC_ShieldKit F11')
json.dump({'blueprint': 'BPC_ShieldKit', 'note': 'F11: no block roll without a worn shield (Worn = -1 read BlockChance[-1])',
           'pastes': ['shield_guard_paste.txt'],
           'rewires': [{'from': 'vSetLastMult56.then', 'to': br + '.execute', 'replace': True, 'note': 'was -> vIfBlocked65'},
                       {'from': br + '.then', 'to': 'vIfBlocked65.execute', 'replace': True}]},
          open(os.path.join(HERE, 'shield_manifest.json'), 'w'), indent=1)
