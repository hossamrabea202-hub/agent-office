# #472 (i5): turn fix A / B / C's generators into ops files for graph_ops_ue.py (node list, links, removals). Same logic as the paste versions, one source.
#   python build_ops.py          needs the 11-03 exports + fixes*/ merged files only to look up which live pins feed what
import json, os, re, sys
sys.dont_write_bytecode = True
OPSDIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(OPSDIR, '..'))
for d in ('fixes', 'fixes_b', 'fixes_c'): sys.path.insert(0, os.path.join(ROOT, d))
import build_472 as A
import build_472b as B
import build_472c as C
from bpkit import Graph
captured = {}
class G2(Graph):
    def render(self):
        captured[len(captured)] = self; return ''
for m in (A, B, C): m.Graph = G2
def write_null(*a, **k): pass
TMP = os.path.join(OPSDIR, '_tmp'); os.makedirs(TMP, exist_ok=True)
A.HERE = B.HERE = C.HERE = TMP
def real_path(ref):
    m = re.search(r"'([^']+)'", ref); return m.group(1)
def conv_node(n):
    name, cls, props, pins, x, y = n
    pj = ' '.join(props); d = {'id': name, 'x': x, 'y': y}
    fr = re.search(r'FunctionReference=\((?:MemberParent=("[^"]+"),)?MemberName="(\w+)"', pj)
    vr = re.search(r'VariableReference=\((?:MemberParent=("[^"]+"),)?MemberName="(\w+)"', pj)
    if cls in ('K2Node_CallFunction', 'K2Node_CallArrayFunction'):
        if fr.group(1): d.update(kind='call', path='%s:%s' % (real_path(fr.group(1)), fr.group(2)))
        else: d.update(kind='call', path='@self:' + fr.group(2))
    elif cls in ('K2Node_VariableGet', 'K2Node_VariableSet'):
        d.update(kind='get' if cls.endswith('Get') else 'set', var=vr.group(2))
        if vr.group(1): d['cls'] = real_path(vr.group(1))
    elif cls == 'K2Node_IfThenElse': d['kind'] = 'branch'
    elif cls == 'K2Node_CustomEvent': d.update(kind='custom', name=re.search(r'CustomFunctionName="(\w+)"', pj).group(1))
    elif cls == 'K2Node_Event': d.update(kind='override', member=re.search(r'MemberName="(\w+)"', pj).group(1))
    elif cls == 'K2Node_Self': d.update(kind='named', name='Variables|Getareferencetoself')
    else: raise SystemExit('no op for %s %s' % (cls, name))
    defaults = []
    for p in pins:
        if p.get('out') or p.get('cat') == 'exec' or p.get('hidden') or p['name'] == 'self': continue
        if p.get('dobj'): defaults.append((p['name'], p['dobj']))
        elif p.get('default') is not None and d['kind'] == 'call': defaults.append((p['name'], str(p['default'])))
    defaults.sort(key=lambda kv: kv[0] != 'ActorClass')
    d['defaults'] = defaults
    return d
def to_ops(G, manifest, remove, fix, bp, vars_, set_live=(), dx=0, dy=0):
    nodes = [conv_node(n) for n in G.nodes]
    for n in nodes:
        if n.get('path', '').startswith('@self:'): n['path'] = '%s.%s_C:%s' % (bp, bp.split('/')[-1], n['path'][6:])
    links = [['%s.%s' % (a, pa), '%s.%s' % (b, pb), False] for a, pa, b, pb in G.links]
    for r in manifest['rewires']: links.append([r['from'], r['to'], bool(r.get('replace'))])
    return {'fix': fix, 'bp': bp, 'vars': vars_, 'nodes': nodes, 'links': links, 'remove': remove, 'set_live': list(set_live), 'dx': dx, 'dy': dy}
def dump(name, ops):
    json.dump(ops, open(os.path.join(OPSDIR, name), 'w'), indent=0); print(name, len(ops['nodes']), 'nodes', len(ops['links']), 'links', len(ops['remove']), 'removed')
P_Z, P_W = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager'
OZ = {'object': P_Z}; OS = {'object': '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'}; OF = {'object': '/Game/CastleDefender/Gameplay/Farm/BP_Farmer'}
OG = {'object': '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl'}; OW = {'object': P_W}
FA = os.path.join(ROOT, 'fixes'); FB = os.path.join(ROOT, 'fixes_b')
EXP = os.path.join(ROOT, '..', 'exports', 'adjustedfilm', 'faults-1205')
def rd(p): return open(p, encoding='utf-8', errors='replace', newline='').read().replace('\r\n', '\n')
# --- A
A.gen_wm(); g_wm = captured[max(captured)]
dump('ops_A_wm.json', to_ops(g_wm, json.load(open(os.path.join(TMP, 'wm_manifest.json'))), A.WM_STRIP, 'A', P_W,
     [['RegHost', OW], ['ZombieReg', dict(OZ, array=True)], ['SoldierCache', dict(OS, array=True)], ['FarmerCache', dict(OF, array=True)], ['GateCache', OG]], dy=9000))
z = A.to_graph(os.path.join(EXP, 'BP_Zombie.t3d.txt')); A.gen_zombie(rd(z)); g_z = captured[max(captured)]
dump('ops_A_zombie.json', to_ops(g_z, json.load(open(os.path.join(TMP, 'zombie_manifest.json'))), A.Z_STRIP, 'A', P_Z,
     [['WMRef', OW], ['LastMoveGoal', {'object': 'Actor'}], ['LastMoveAt', {'basic': 'real'}]],
     set_live=[['K2Node_CallFunction_ZB6', 'InitialStartDelayVariance', '0.25']], dy=12000))
# --- B and C are built on A's result; their look-ups only touch nodes A leaves alone
B.gen(rd(os.path.join(FB, '..', 'fixes', 'zombie_merged.txt')).replace('\r\n', '\n')); g_b = captured[max(captured)]
dump('ops_B_zombie.json', to_ops(g_b, json.load(open(os.path.join(TMP, 'zombie_b_manifest.json'))), B.DEATHS + ['CX_97'], 'B', P_Z, [], dy=14000))
C.gen(rd(os.path.join(FB, 'zombie_b_merged.txt'))); g_c = captured[max(captured)]
dump('ops_C_zombie.json', to_ops(g_c, json.load(open(os.path.join(TMP, 'zombie_c_manifest.json'))), [], 'C', P_Z,
     [['ThinkTick', {'basic': 'int'}], ['LastFlinchAt', {'basic': 'real'}]], dy=16000))
# the three fixes in one run, one compile: this is what i5 tests and what the Master applies
abc = {'fix': 'ABC', 'bp': P_Z, 'vars': [], 'nodes': [], 'links': [], 'remove': [], 'set_live': [], 'dx': 0, 'dy': 12000}
for f in ('ops_A_zombie.json', 'ops_B_zombie.json', 'ops_C_zombie.json'):
    o = json.load(open(os.path.join(OPSDIR, f)))
    for k in ('vars', 'nodes', 'links', 'remove', 'set_live'): abc[k] += o[k]
    for n in o['nodes']: n['y'] += o['dy'] - 12000
dump('ops_ABC_zombie.json', abc)
for f in os.listdir(TMP): os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
