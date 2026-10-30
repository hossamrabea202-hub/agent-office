# BP_RealmGate (#169 stage 1 gameplay). TGA, 2026-10-30. Pure Tick logic on the level's Realm_Gate_* actors:
# within UseRange the 'E  Open' prompt shows (turned to the player); E opens: the leaves swing OpenAngle (95 deg) over
# 1/OpenRate s with smoothstep easing and the bar lifts 1.5 m; once the player is out of range for 3 s the gate closes.
# Only the player's key opens it (zombies never do). Nodes are cloned from the Master's / laptop2's exports (bpkit).
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpkit
from bpkit import Export, Graph, bpvar, var_get, var_set, fl, it, bo, ob, vec, CLS
OUT = sys.argv[1] if len(sys.argv) > 1 else r'T:\bp\out'
Z = Export(r'R:\handoffs\exports\master\2026-10-30\BP_Zombie.t3d'); GC = Export(r'R:\handoffs\exports\laptop2\prompt68\BP_CastleGateControl.t3d')
G = Graph('RGT')
def T(ex, cls, member=None, extra=None): return ex.find(cls, member, extra)
def C(ex, cls, member=None, x=0, y=0, extra=None): return G.clone(ex, T(ex, cls, member, extra), x, y)
def call(member, x, y, ex=Z): return C(ex, 'K2Node_CallFunction', member, x, y)
def br(x, y): return C(Z, 'K2Node_IfThenElse', None, x, y)
def getv(name, pin, x, y): return var_get(G, name, pin, x, y)
def setv(name, pin, x, y, value=None):
    n = var_set(G, name, pin, x, y)
    if value is not None: n.set_default(name, value)
    return n
def chain(*nodes):
    for a, b in zip(nodes, nodes[1:]): G.link(a, 'then', b, 'execute')
    return nodes[-1]
def math2(member, a, apin, b, bpin, x, y, ex=Z):
    n = call(member, x, y, ex)
    if isinstance(a, (int, float, str)): n.set_default('A', str(a))
    else: G.link(a, apin, n, 'A')
    if isinstance(b, (int, float, str)): n.set_default('B', str(b))
    else: G.link(b, bpin, n, 'B')
    return n
ACT = lambda n: ob(n, CLS('Actor'))
SCENE = '/Script/Engine.SceneComponent'
def prompt_get(x, y):
    n = C(Z, 'K2Node_VariableGet', 'Mesh', x, y); n.sub_prop('MemberName="Mesh"', 'MemberName="Prompt"')
    p = n.pin('Mesh'); p['name'] = 'Prompt'; p['line'] = p['line'].replace('PinName="Mesh"', 'PinName="Prompt"').replace('/Script/Engine.SkeletalMeshComponent', '/Script/Engine.TextRenderComponent')
    return n
def set_actor_loc(x, y):        # K2_SetActorLocation on another actor, built on K2_SetRelativeLocation's shell (as in #174)
    sl = call('K2_SetRelativeLocation', x, y)
    sl.props = [l for l in sl.props if not l.startswith('FunctionReference')] + ['FunctionReference=(MemberName="K2_SetActorLocation",bSelfContext=True)']
    rot_t = G.clone(Z, T(Z, 'K2Node_CallFunction', 'K2_SetActorRotation'), 0, 0); del G.nodes[rot_t.name]
    sl.pins = [p if p['name'] != 'self' else dict(rot_t.pin('self'), id=bpkit.g()) for p in sl.pins]; sl.pins.append(dict(rot_t.pin('ReturnValue'), id=bpkit.g()))
    sl.set_default('bTeleport', 'true'); return sl

x0, y0 = 0, 0
tk = C(Z, 'K2Node_Event', 'ReceiveTick', x0, y0)
pawn = call('GetPlayerPawn', x0 + 100, y0 + 300, GC)
dist = call('GetDistanceTo', x0 + 300, y0 + 300); G.link(pawn, 'ReturnValue', dist, 'OtherActor')
near = math2('Less_DoubleDouble', dist, 'ReturnValue', getv('UseRange', fl('UseRange'), x0 + 300, y0 + 450), 'UseRange', x0 + 500, y0 + 300)
notop = call('Not_PreBool', x0 + 500, y0 + 450); G.link(getv('Opening', bo('Opening'), x0 + 300, y0 + 550), 'Opening', notop, 'A')
show = math2('BooleanAND', near, 'ReturnValue', notop, 'ReturnValue', x0 + 700, y0 + 350)
vis = G.clone(GC, 'P_Vis', x0 + 900, y0); G.link(prompt_get(x0 + 700, y0 + 150), 'Prompt', vis, 'self'); G.link(show, 'ReturnValue', vis, 'bNewVisibility'); G.link(tk, 'then', vis, 'execute')
# turn the prompt to face the player (yaw only); K2_SetWorldRotation built on K2_SetRelativeLocation's shell
lk = call('FindLookAtRotation', x0 + 900, y0 + 300); G.link(call('K2_GetActorLocation', x0 + 700, y0 + 600), 'ReturnValue', lk, 'Start')
pl = call('K2_GetActorLocation', x0 + 700, y0 + 700); G.link(pawn, 'ReturnValue', pl, 'self'); G.link(pl, 'ReturnValue', lk, 'Target')
bk = call('BreakRotator', x0 + 1100, y0 + 300); G.link(lk, 'ReturnValue', bk, 'InRot'); mr = call('MakeRotator', x0 + 1300, y0 + 300); G.link(bk, 'Yaw', mr, 'Yaw')
wr = call('K2_SetRelativeLocation', x0 + 1200, y0); wr.sub_prop('MemberName="K2_SetRelativeLocation"', 'MemberName="K2_SetWorldRotation"')
np_ = wr.pin('NewLocation'); np_['name'] = 'NewRotation'
np_['line'] = np_['line'].replace('PinName="NewLocation"', 'PinName="NewRotation"').replace("/Script/CoreUObject.Vector'", "/Script/CoreUObject.Rotator'")
np_['line'] = re.sub(r'(?<![A-Za-z])DefaultValue="[^"]*",', '', np_['line'])
G.link(prompt_get(x0 + 1000, y0 + 150), 'Prompt', wr, 'self'); G.link(mr, 'ReturnValue', wr, 'NewRotation'); G.link(vis, 'then', wr, 'execute')
# E pressed near a closed gate -> open
pc = call('GetPlayerController', x0 + 1300, y0 + 500, GC); key = G.clone(GC, 'T_RDown', x0 + 1500, y0 + 500); key.set_default('Key', 'E'); G.link(pc, 'ReturnValue', key, 'self')
go = math2('BooleanAND', show, 'ReturnValue', key, 'ReturnValue', x0 + 1700, y0 + 400)
bo_ = br(x0 + 1500, y0); G.link(go, 'ReturnValue', bo_, 'Condition'); G.link(wr, 'then', bo_, 'execute')
op = setv('Opening', bo('Opening'), x0 + 1800, y0 - 150, 'true'); ca0 = setv('CloseAcc', fl('CloseAcc'), x0 + 2050, y0 - 150, '0.0'); chain(op, ca0); G.link(bo_, 'then', op, 'execute')
# while open: player in range -> hold; out of range for 3 s (after fully open) -> close
bj = br(x0 + 2350, y0); G.link(getv('Opening', bo('Opening'), x0 + 2150, y0 + 150), 'Opening', bj, 'Condition'); G.link(ca0, 'then', bj, 'execute'); G.link(bo_, 'else', bj, 'execute')
bn = br(x0 + 2650, y0 - 150); G.link(near, 'ReturnValue', bn, 'Condition'); G.link(bj, 'then', bn, 'execute')
hold = setv('CloseAcc', fl('CloseAcc'), x0 + 2950, y0 - 300, '0.0'); G.link(bn, 'then', hold, 'execute')
acc = setv('CloseAcc', fl('CloseAcc'), x0 + 2950, y0); G.link(math2('Add_DoubleDouble', getv('CloseAcc', fl('CloseAcc'), x0 + 2750, y0 + 150), 'CloseAcc', None, None, x0 + 2950, y0 + 150) if False else None, None, acc, 'CloseAcc') if False else None
addc = call('Add_DoubleDouble', x0 + 2800, y0 + 150); G.link(getv('CloseAcc', fl('CloseAcc'), x0 + 2600, y0 + 150), 'CloseAcc', addc, 'A'); G.link(tk, 'DeltaSeconds', addc, 'B'); G.link(addc, 'ReturnValue', acc, 'CloseAcc')
G.link(bn, 'else', acc, 'execute')
c3 = math2('Greater_DoubleDouble', acc, 'Output_Get', 3.0, None, x0 + 3150, y0 + 150)
full = math2('GreaterEqual_DoubleDouble', getv('OpenT', fl('OpenT'), x0 + 3000, y0 + 300), 'OpenT', 1.0, None, x0 + 3150, y0 + 300)
cl = br(x0 + 3250, y0); G.link(math2('BooleanAND', c3, 'ReturnValue', full, 'ReturnValue', x0 + 3350, y0 + 200), 'ReturnValue', cl, 'Condition'); G.link(acc, 'then', cl, 'execute')
shut = setv('Opening', bo('Opening'), x0 + 3550, y0 - 100, 'false'); G.link(cl, 'then', shut, 'execute')
# OpenT moves toward 1 (opening) or 0 (closing) at OpenRate per second
x1 = x0 + 3900
step = math2('Multiply_DoubleDouble', tk, 'DeltaSeconds', getv('OpenRate', fl('OpenRate'), x1 - 200, y0 + 450), 'OpenRate', x1, y0 + 400)
up_ = call('FMin', x1 + 400, y0 + 300, GC) if False else G.clone(GC, 'D_Cap', x1 + 400, y0 + 300)
G.link(math2('Add_DoubleDouble', getv('OpenT', fl('OpenT'), x1, y0 + 250), 'OpenT', step, 'ReturnValue', x1 + 200, y0 + 300), 'ReturnValue', up_, 'A'); up_.set_default('B', '1.0')
dn = G.clone(GC, 'R_Max', x1 + 400, y0 + 500); sub = G.clone(GC, 'R_Sub', x1 + 200, y0 + 500)
G.link(getv('OpenT', fl('OpenT'), x1, y0 + 550), 'OpenT', sub, 'A'); G.link(step, 'ReturnValue', sub, 'B'); G.link(sub, 'ReturnValue', dn, 'A'); dn.set_default('B', '0.0')
sel = call('SelectFloat', x1 + 600, y0 + 400); G.link(up_, 'ReturnValue', sel, 'A'); G.link(dn, 'ReturnValue', sel, 'B'); G.link(getv('Opening', bo('Opening'), x1 + 400, y0 + 650), 'Opening', sel, 'bPickA')
so = setv('OpenT', fl('OpenT'), x1 + 300, y0); G.link(sel, 'ReturnValue', so, 'OpenT')
for n_, pin in ((bj, 'else'), (hold, 'then'), (cl, 'else'), (shut, 'then')): G.link(n_, pin, so, 'execute')
# ease = t*t*(3-2t); angle = OpenAngle * ease * SwingSign
t_ = so
tt = math2('Multiply_DoubleDouble', t_, 'Output_Get', t_, 'Output_Get', x1 + 700, y0 + 700)
k = math2('Multiply_DoubleDouble', 2.0, None, t_, 'Output_Get', x1 + 700, y0 + 850)
three = G.clone(GC, 'R_Sub', x1 + 900, y0 + 850); three.set_default('A', '3.0'); G.link(k, 'ReturnValue', three, 'B')
ease = math2('Multiply_DoubleDouble', tt, 'ReturnValue', three, 'ReturnValue', x1 + 1100, y0 + 750)
ang = math2('Multiply_DoubleDouble', ease, 'ReturnValue', getv('OpenAngle', fl('OpenAngle'), x1 + 1100, y0 + 900), 'OpenAngle', x1 + 1300, y0 + 750)
angs = math2('Multiply_DoubleDouble', ang, 'ReturnValue', getv('SwingSign', fl('SwingSign'), x1 + 1300, y0 + 900), 'SwingSign', x1 + 1500, y0 + 750)
def leaf(var, base, sign, x, y):
    yaw = (math2('Add_DoubleDouble', getv(base, fl(base), x - 400, y + 300), base, angs, 'ReturnValue', x - 200, y + 250) if sign > 0
           else G.clone(GC, 'R_Sub', x - 200, y + 250))
    if sign < 0: G.link(getv(base, fl(base), x - 400, y + 300), base, yaw, 'A'); G.link(angs, 'ReturnValue', yaw, 'B')
    mr_ = call('MakeRotator', x, y + 250); G.link(yaw, 'ReturnValue', mr_, 'Yaw')
    sr = call('K2_SetActorRotation', x + 200, y); G.link(getv(var, ACT(var), x, y + 150), var, sr, 'self'); G.link(mr_, 'ReturnValue', sr, 'NewRotation'); return sr
lL = leaf('LeafL', 'BaseYawL', +1, x1 + 900, y0); lR = leaf('LeafR', 'BaseYawR', -1, x1 + 1400, y0)
bz = math2('Multiply_DoubleDouble', ease, 'ReturnValue', 150.0, None, x1 + 1700, y0 + 600)
mv = call('MakeVector', x1 + 1900, y0 + 550); mv.set_default('X', '0.0').set_default('Y', '0.0'); G.link(bz, 'ReturnValue', mv, 'Z')
av = call('Add_VectorVector', x1 + 2100, y0 + 450); G.link(getv('BarBase', vec('BarBase'), x1 + 1900, y0 + 400), 'BarBase', av, 'A'); G.link(mv, 'ReturnValue', av, 'B')
sb = set_actor_loc(x1 + 2300, y0); G.link(getv('Bar', ACT('Bar'), x1 + 2100, y0 + 250), 'Bar', sb, 'self'); G.link(av, 'ReturnValue', sb, 'NewLocation')
chain(so, lL, lR, sb)

open(os.path.join(OUT, 'BP_RealmGate_EventGraph.txt'), 'w', encoding='utf-8').write(G.render())
V = [bpvar('LeafL', 'object', '', obj="/Script/CoreUObject.Class'/Script/Engine.Actor'"), bpvar('LeafR', 'object', '', obj="/Script/CoreUObject.Class'/Script/Engine.Actor'"),
     bpvar('Bar', 'object', '', obj="/Script/CoreUObject.Class'/Script/Engine.Actor'"),
     bpvar('BaseYawL', 'real', '0.0', sub='double'), bpvar('BaseYawR', 'real', '0.0', sub='double'),
     bpvar('BarBase', 'struct', '0.000000,0.000000,0.000000', obj="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),
     bpvar('OpenT', 'real', '0.0', sub='double'), bpvar('CloseAcc', 'real', '0.0', sub='double'), bpvar('Opening', 'bool', 'False'),
     bpvar('OpenAngle', 'real', '95.0', sub='double'), bpvar('OpenRate', 'real', '0.833', sub='double'), bpvar('UseRange', 'real', '300.0', sub='double'),
     bpvar('SwingSign', 'real', '1.0', sub='double')]
open(os.path.join(OUT, 'BP_RealmGate_vars.txt'), 'w', encoding='utf-8').write('\n'.join(V) + '\n')
print('GATE nodes', len(G.nodes), 'links', len(G.links))
