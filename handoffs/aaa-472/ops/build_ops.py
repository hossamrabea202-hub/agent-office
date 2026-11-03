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
# --- D: BP_SoldierSword. Built by hand: no live look-ups beyond the node names, the runner checks those
P_S = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'; KM = '/Script/Engine.KismetMathLibrary:'; AC = '/Script/Engine.Actor:'
WMC = P_W + '.BP_ZombieWaveManager_C'
n = lambda i, k, x, y, **kw: dict(id=i, kind=k, x=x, y=y, defaults=kw.pop('defaults', []), **kw)
nodes = [n('sdPlayer', 'call', 0, 0, path='/Script/Engine.GameplayStatics:GetPlayerCharacter'), n('sdDist', 'call', 250, 0, path=AC + 'GetDistanceTo'),
         n('sdNear', 'call', 500, 0, path=KM + 'Less_DoubleDouble', defaults=[['B', '3000.0']]), n('sdSeen', 'call', 500, 150, path=AC + 'WasRecentlyRendered'),
         n('sdFull', 'call', 750, 50, path=KM + 'BooleanOR'), n('sdSel1', 'call', 1000, 0, path=KM + 'SelectFloat', defaults=[['B', '0.2']]),
         n('sdSel2', 'call', 1000, 150, path=KM + 'SelectFloat', defaults=[['B', '0.1']]), n('sdRate', 'call', 1300, 0, path=AC + 'SetActorTickInterval'),
         n('sdCmc', 'get', 1300, 250, var='CharacterMovement', cls='/Script/Engine.Character'), n('sdCmcRate', 'call', 1600, 0, path='/Script/Engine.ActorComponent:SetComponentTickInterval'),
         n('sdAnim', 'call', 0, 1100, path='/Script/Engine.SkeletalMeshComponent:GetAnimInstance'),
         n('sdSlot', 'call', 300, 1100, path='/Script/Engine.AnimInstance:PlaySlotAnimationAsDynamicMontage',
           defaults=[['Asset', '/Game/CastleDefender/Characters/Enemies/Zombie/Anims/A_Attack.A_Attack'], ['SlotNodeName', 'DefaultSlot'], ['BlendInTime', '0.1'], ['BlendOutTime', '0.2']]),
         n('sdFind1', 'call', 0, 500, path='/Script/Engine.GameplayStatics:GetActorOfClass', defaults=[['ActorClass', WMC]]), n('sdReg1', 'get', 300, 600, var='ZombieReg', cls=WMC),
         n('sdFind2', 'call', 0, 800, path='/Script/Engine.GameplayStatics:GetActorOfClass', defaults=[['ActorClass', WMC]]), n('sdReg2', 'get', 300, 900, var='ZombieReg', cls=WMC)]
L_ = [['sdPlayer.ReturnValue', 'sdDist.OtherActor', False], ['sdDist.ReturnValue', 'sdNear.A', False], ['sdNear.ReturnValue', 'sdFull.A', False], ['sdSeen.ReturnValue', 'sdFull.B', False],
      ['sdFull.ReturnValue', 'sdSel1.bPickA', False], ['sdFull.ReturnValue', 'sdSel2.bPickA', False], ['sdSel1.ReturnValue', 'sdRate.TickInterval', False], ['sdSel2.ReturnValue', 'sdCmcRate.TickInterval', False],
      ['sdCmc.CharacterMovement', 'sdCmcRate.self', False], ['CX_135.then', 'sdRate.execute', True], ['sdRate.then', 'sdCmcRate.execute', False], ['sdCmcRate.then', 'Unstick220In.execute', False],
      ['CX_157.Mesh', 'sdAnim.self', False], ['sdAnim.ReturnValue', 'sdSlot.self', False], ['CX_172.then', 'sdSlot.execute', True], ['sdSlot.then', 'CX_178.execute', False],
      ['CX_143.then', 'sdFind1.execute', True], ['sdFind1.then', 'CX_145.Exec', True], ['sdFind1.ReturnValue', 'sdReg1.self', False], ['sdReg1.ZombieReg', 'CX_145.Array', True],
      ['CX_452.then', 'sdFind2.execute', True], ['sdFind2.then', 'CX_454.Exec', True], ['sdFind2.ReturnValue', 'sdReg2.self', False], ['sdReg2.ZombieReg', 'CX_454.Array', True]]
dump('ops_D_soldier.json', {'fix': 'D', 'bp': P_S, 'vars': [], 'nodes': nodes, 'links': L_, 'remove': ['CX_144', 'CX_453', 'CX_173'], 'set_live': [], 'dx': 0, 'dy': 20000})
for f in os.listdir(TMP): os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
