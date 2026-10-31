# #157 v2 (adjustedfilm, 2026-10-31): BPC_RealmFX, the hero component that fades the realm post process in and out.
#   "<blender python>" -I gen_realmfx157.py -> BPC_RealmFX_graph.txt, VARIABLES_BPVar.txt
# BeginPlay: every actor tagged laptop2_realm (laptop2's #169 placement: walls, dome, dressing) -> Centre = their average
#   position, Radius = 0.9 x the farthest one (the realm wall ring). No actors = nothing happens.
# RealmTick (0.1 s): inside = hero within Radius (2D) of Centre; Inside eases toward it over ~2 s; MPC_Realm.Inside = Inside.
# When #284 removes the realm (actors destroyed), the next BeginPlay finds nothing; while playing, a destroyed realm keeps
# its last centre, so #284 should also set MPC_Realm.Inside to 0 (noted on #284).
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP = CLS('ActorComponent')
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC = '/Game/CastleDefender/Realm/MPC_Realm.MPC_Realm'
G = Graph(); b = bpkit.B(G, 'rf')
g = b.get
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
ga = b.lib(GS, 'GetAllActorsWithTag', [WC(), {'name': 'Tag', 'cat': 'name', 'default': 'laptop2_realm'}, arr(ob('OutActors', ACT, out=True))], 300, 0, tag='FindRealm')
G.link('BP', 'then', ga, 'execute')
s0 = b.set('Sum', V('v'), None, 600, 0); G.link(ga, 'then', s0, 'execute')
fe = b.foreach(ACT, 850, 0); G.link(s0, 'then', fe, 'Exec'); b.wire((ga, 'OutActors'), fe, 'Array')
loc = lambda a, x, y: (b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=a, pure=True, const=True, tag='Loc'), 'ReturnValue')
ss = b.set('Sum', V('v'), b.v2('Add_VectorVector', g('Sum', V('v'), 1000, 300), loc((fe, 'Array Element'), 1000, 400), 1200, 350), 1200, -200)
G.link(fe, 'LoopBody', ss, 'execute')
n = b.name('Count')
G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 1300, 600)
G.link(ga, 'OutActors', n, 'TargetArray')
sc = b.set('Count', INT, (n, 'ReturnValue'), 1500, 0); G.link(fe, 'Completed', sc, 'execute')
bh = b.branch(b.icmp('Greater_IntInt', (n, 'ReturnValue'), None, 1600, 400, db='0'), 1750, 0, tag='IfRealm'); G.link(sc, 'then', bh, 'execute')
cen = b.math('Divide_VectorFloat', [(V('A'), g('Sum', V('v'), 1800, 300)), (D('B', default='1.0'), b.i2d((n, 'ReturnValue'), 1800, 450))], V('ReturnValue', out=True), 2000, 350)
scn = b.set('Centre', V('v'), cen, 2050, 0); G.link(bh, 'then', scn, 'execute')
sr0 = b.set('Radius', DBL, None, 2300, 0); G.link(scn, 'then', sr0, 'execute')
fe2 = b.foreach(ACT, 2550, 0); G.link(sr0, 'then', fe2, 'Exec'); b.wire((ga, 'OutActors'), fe2, 'Array')
d = b.math('Vector_Distance2D', [(V('V1'), loc((fe2, 'Array Element'), 2600, 400)), (V('V2'), g('Centre', V('v'), 2600, 500))], D('ReturnValue', out=True), 2800, 450)
sr = b.set('Radius', DBL, b.math('FMax', [(D('A', default='0.0'), g('Radius', DBL, 2800, 300)), (D('B', default='0.0'), d)], D('ReturnValue', out=True), 3000, 350), 2900, -200)
G.link(fe2, 'LoopBody', sr, 'execute')
srf = b.set('Radius', DBL, b.d2('Multiply_DoubleDouble', g('Radius', DBL, 3100, 300), None, 3300, 300, db='0.9'), 3200, 0); G.link(fe2, 'Completed', srf, 'execute')
tm = b.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default='RealmTick'), fl('Time', default='0.1'), bo('bLooping', default='true'),
                                fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                st('ReturnValue', TIMERH, out=True)], 3500, 0, tag='TimerRealm')
b.wire(b.self_node(3350, 200), tm, 'Object'); G.link(srf, 'then', tm, 'execute')

Y = 1000
b.event('RealmTick', [], 0, Y)
own = b.name('Owner'); callfn(G, own, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=Y + 300, self_hidden=True)
dh = b.math('Vector_Distance2D', [(V('V1'), loc((own, 'ReturnValue'), 200, Y + 300)), (V('V2'), g('Centre', V('v'), 200, Y + 400))], D('ReturnValue', out=True), 400, Y + 350)
tgt = b.math('Conv_BoolToDouble', [(bo('InBool', default='false'), b.dcmp('Less_DoubleDouble', dh, g('Radius', DBL, 400, Y + 500), 600, Y + 450))], D('ReturnValue', out=True), 800, Y + 450)
cur = g('Inside', DBL, 800, Y + 600)
nv = b.d2('Add_DoubleDouble', cur, b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', tgt, cur, 1000, Y + 500), None, 1200, Y + 500, db='0.05'), 1400, Y + 550)
si = b.set('Inside', DBL, nv, 300, Y); G.link('RealmTick', 'then', si, 'execute')
mp = b.name('SetInside')
callfn(G, mp, MATL, 'SetScalarParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), {'name': 'ParameterName', 'cat': 'name', 'default': 'Inside'},
       fl('ParameterValue', default='0.0')], x=600, y=Y, self_hidden=True)
b.wire(g('Inside', DBL, 450, Y + 200), mp, 'ParameterValue'); G.link(si, 'then', mp, 'execute')

pins = {(n_[0], p['name']) for n_ in G.nodes for p in n_[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links %s' % bad)
open(os.path.join(HERE, 'BPC_RealmFX_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_RealmFX: nodes %d, links %d' % (len(G.nodes), len(G.links)))
REAL = 'PinCategory="real",PinSubCategory="double"'
VEC_ = 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
VARS = [('Sum', VEC_, '0,0,0'), ('Count', 'PinCategory="int"', '0'), ('Centre', VEC_, '0,0,0'), ('Radius', REAL, '0.0'), ('Inside', REAL, '0.0')]
bpv = lambda n_, t, d_: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n_, uuid.uuid5(uuid.NAMESPACE_URL, 'realmfx157/' + n_).hex.upper(), t, n_, d_)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('# BPC_RealmFX (#157 v2) - paste one line at a time, then Compile\n' + '\n'.join(bpv(*v) for v in VARS) + '\n')
