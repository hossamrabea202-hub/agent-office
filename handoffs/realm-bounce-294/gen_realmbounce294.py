# #294 Cannonballs bounce off the realm bubble, pawns pass (adjustedfilm, 2026-10-31 late): EventGraph of the NEW component
# BPC_RealmBounce, which the setup script adds to BP_Cannonball.
#   "<blender python>" -I gen_realmbounce294.py  ->  BPC_RealmBounce_graph.txt, VARIABLES_BPVar.txt
# Why a component: the owner's reshaped bubble (Realm_Bubble_Owner) is OverlapAllDynamic, so a cannonball never gets an Event Hit
# from it and #284's hit-bounce never fires. Changing the bubble's collision is off limits (owner). Instead the ball checks its own
# path every frame against the REAL bubble mesh (Component Line Trace, complex: works with overlap collision, any shape):
#   BeginPlay: the bubble = first actor tagged RealmBubble -> its first StaticMeshComponent; the ball's ProjectileMovement; Last = here
#   Tick: bubble valid + visible (not collapsed, #284) and not bounced yet -> trace Last -> now. A hit = the ball crossed the membrane:
#         put it 30 cm back out along the normal, velocity = mirror(velocity, normal) x BounceKeep, Z at most -MinDown (it lands
#         outside the realm and explodes there as usual), Bounced = true. Last = now.
# Pawns (soldiers, zombies, wasps, the hero) already pass: the bubble only overlaps them. Nothing on the bubble is changed.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))          # bpkit's import overwrites HERE

COMP, SMC = CLS('ActorComponent'), CLS('StaticMeshComponent')
PMC, MOVC = CLS('ProjectileMovementComponent'), CLS('MovementComponent')
G = Graph(); b = B(G, 'rb')
g = lambda var, pin, x, y: b.get(var, pin, x, y)
BOOLV, DBLV, VECV, OBJV = bo('v', default='false'), D('v', default='0.0'), V('v'), lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}


def event(nm, member, extra, x, y):
    G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (COMP, member), 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (COMP, member)}, ex('then', True)] + extra, x, y)
    return nm


def owner(x, y):
    n = b.name('Owner'); callfn(G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
    return (n, 'ReturnValue')


def first_of(actor, cls, cpath_, x, y, tag):
    gc = b.call(ACT, 'K2_GetComponentsByClass', [CLSPIN('ComponentClass', COMP, cpath_), arr(ob('ReturnValue', cls, out=True))], x, y,
                target=actor, pure=True, const=True, tag=tag)
    n = b.name('First' + tag)
    G.node(n, 'K2Node_GetArrayItem', [], [arr(ob('Array', cls)), it('Dimension 1', default='0'), ob('Output', cls, out=True)], x + 250, y)
    b.wire((gc, 'ReturnValue'), n, 'Array'); return (n, 'Output')


def actor_loc(x, y):
    n = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=owner(x - 200, y), pure=True, const=True, tag='BallLoc')
    return (n, 'ReturnValue')


# ================================================================================================= BeginPlay
event('BP', 'ReceiveBeginPlay', [], 0, 0)
tg = b.lib(GS, 'GetAllActorsWithTag', [WC(), NAME_('Tag', 'RealmBubble'), arr(ob('OutActors', ACT, out=True))], 300, 0, tag='FindBubble')
G.link('BP', 'then', tg, 'execute')
b0 = b.name('Bubble0')
G.node(b0, 'K2Node_GetArrayItem', [], [arr(ob('Array', ACT)), it('Dimension 1', default='0'), ob('Output', ACT, out=True)], 600, 300)
b.wire((tg, 'OutActors'), b0, 'Array')
sbm = b.set('BubbleMesh', OBJV(PRIM), first_of((b0, 'Output'), SMC, '/Script/Engine.StaticMeshComponent', 800, 300, 'BubbleMesh'), 700, 0)
spm = b.set('Move', OBJV(PMC), first_of(owner(800, 600), PMC, '/Script/Engine.ProjectileMovementComponent', 1000, 600, 'Projectile'), 1000, 0)
sl = b.set('Last', VECV, actor_loc(1200, 300), 1300, 0)
b.chain(tg, sbm, spm, sl)

# ================================================================================================= Tick
Y = 1200
event('TK', 'ReceiveTick', [fl('DeltaSeconds', out=True, default='0.0')], 0, Y)
mesh = lambda x, y: g('BubbleMesh', OBJV(PRIM), x, y)
vis = b.call(SCENE, 'IsVisible', [bo('ReturnValue', out=True, default='false')], 300, Y + 400, target=mesh(100, Y + 400), pure=True, const=True, tag='BubbleVis')
ok = b.b2('BooleanAND', b.b2('BooleanAND', b.valid(mesh(100, Y + 300), 300, Y + 300), (vis, 'ReturnValue'), 500, Y + 350),
          b.b2('BooleanAND', b.bnot(g('Bounced', BOOLV, 300, Y + 550), 500, Y + 550), b.valid(g('Move', OBJV(PMC), 300, Y + 650), 500, Y + 650), 700, Y + 600), 900, Y + 450)
bo_ = b.branch(ok, 300, Y, tag='IfWatch'); G.link('TK', 'then', bo_, 'execute')
now = actor_loc(500, Y + 800)
tr = b.call(PRIM, 'K2_LineTraceComponent', [V('TraceStart'), V('TraceEnd'), bo('bTraceComplex', default='true'), bo('bShowTrace', default='false'),
            bo('bPersistentShowTrace', default='false'), V('HitLocation', out=True), V('HitNormal', out=True), {'name': 'BoneName', 'cat': 'name', 'out': True},
            st('OutHit', HITRES, out=True), bo('ReturnValue', out=True, default='false')], 600, Y, target=mesh(450, Y + 250), tag='CrossCheck')
b.wire(g('Last', VECV, 450, Y + 350), tr, 'TraceStart'); b.wire(now, tr, 'TraceEnd')
G.link(bo_, 'then', tr, 'execute')
bh = b.branch((tr, 'ReturnValue'), 900, Y, tag='IfCrossed'); b.chain(tr, bh)
# bounce: out along the normal (facing the ball's side), mirrored velocity x keep, forced down
vel = b.getm('Velocity', MOVC, VECV, g('Move', OBJV(PMC), 900, Y + 500), 1100, Y + 500)
nrm = (tr, 'HitNormal')
side = b.dcmp('Less_DoubleDouble', b.math('Dot_VectorVector', [(V('A'), vel), (V('B'), nrm)], D('ReturnValue', out=True), 1300, Y + 650), None, 1500, Y + 650, db='0.0')
facing = b.selvec(nrm, b.math('Multiply_VectorFloat', [(V('A'), nrm), (D('B', default='-1.0'), None)], V('ReturnValue', out=True), 1500, Y + 800), side, 1700, Y + 700)
mir = b.math('MirrorVectorByNormal', [(V('InVect'), vel), (V('InNormal'), facing)], V('ReturnValue', out=True), 1900, Y + 600)
kept = b.math('Multiply_VectorFloat', [(V('A'), mir), (D('B', default='0.5'), g('BounceKeep', DBLV, 1900, Y + 750))], V('ReturnValue', out=True), 2100, Y + 650)
kb = b.brk(kept, 2300, Y + 650)
down = b.d2('FMin', kb['Z'], b.d2('Multiply_DoubleDouble', g('MinDown', DBLV, 2300, Y + 850), None, 2500, Y + 850, db='-1.0'), 2700, Y + 750)
newv = b.vec(kb['X'], kb['Y'], down, 2900, Y + 650)
out_ = b.v2('Add_VectorVector', (tr, 'HitLocation'), b.math('Multiply_VectorFloat', [(V('A'), facing), (D('B', default='30.0'), None)], V('ReturnValue', out=True), 1900, Y + 900),
            2100, Y + 900)
mv = b.call(ACT, 'K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true'),
            bo('ReturnValue', out=True, default='false')], 1200, Y - 200, target=owner(1000, Y - 300), tag='PutOutside')
b.wire(out_, mv, 'NewLocation'); G.link(bh, 'then', mv, 'execute')
sv = b.setm('Velocity', MOVC, VECV, newv, g('Move', OBJV(PMC), 1400, Y - 350), 1500, Y - 200)
sb = b.set('Bounced', bo('v', default='true'), None, 1800, Y - 200)
b.chain(mv, sv, sb)
mg = b.seq('AfterBounce', 1, 2100, Y); G.link(bh, 'else', mg, 'execute'); G.link(sb, 'then', mg, 'execute')
mg2 = b.seq('AfterWatch', 1, 2400, Y); G.link(mg, 'then_0', mg2, 'execute'); G.link(bo_, 'else', mg2, 'execute')
sl2 = b.set('Last', VECV, actor_loc(2500, Y + 300), 2700, Y); G.link(mg2, 'then_0', sl2, 'execute')

# ================================================================================================= checks + output
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
names = [n[0] for n in G.nodes]
dup = {n for n in names if names.count(n) > 1}
if dup: raise SystemExit('duplicate node names: %s' % sorted(dup)[:10])
open(os.path.join(HERE, 'BPC_RealmBounce_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_RealmBounce: nodes %d, links %d' % (len(G.nodes), len(G.links)))


def bpvar(name, vt, default, flags):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Realm Bounce"),PropertyFlags=%d,DefaultValue="%s")' % (
        name, uuid.uuid5(uuid.NAMESPACE_URL, 'realmbounce294/' + name).hex.upper(), vt, name, flags, default)
REAL = 'PinCategory="real",PinSubCategory="double"'
OBJ_ = lambda c: 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % c
VEC_ = 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
EDIT, HIDDEN = 5, 4 | 0x10000
VARS = [('BounceKeep', REAL, '0.5', EDIT), ('MinDown', REAL, '200.0', EDIT),
        ('BubbleMesh', OBJ_('PrimitiveComponent'), '', HIDDEN), ('Move', OBJ_('ProjectileMovementComponent'), '', HIDDEN),
        ('Last', VEC_, '0, 0, 0', HIDDEN), ('Bounced', 'PinCategory="bool"', 'false', HIDDEN)]
used = {p for n in G.nodes for p in n[2] if 'VariableReference' in p}
for v, *_ in VARS:
    if not any('"%s"' % v in u for u in used): raise SystemExit('BPVar %s is never used' % v)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_RealmBounce (#294) - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpvar(*v) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
