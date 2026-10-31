# #292 Muddy footprints (adjustedfilm, 2026-10-31): walking through a wet mud puddle leaves muddy boot prints for a few steps.
#   "<blender python>" -I gen_mud292.py -> BPC_MudPrints_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# BPC_MudPrints (hero component "MudPrints"):
#   BeginPlay: remembers the owner's CharacterMovement, collects the BP_MudPad actors (tag MudPad), MudTick every 0.05 s.
#   MudTick:   InMud = the hero stands inside a pad (2D distance < 140 cm x the pad's scale). In mud -> MudLeft = Prints (6).
#              MudLeft > 0, on the ground, moved >= Stride (80 cm) since the last print -> one boot print:
#              alternating left / right (11 cm beside the centre line), at the feet (FootDrop 92 cm under the actor),
#              facing the walk direction, as a decal of MI_MudPrint: Strength = MudLeft / Prints (each step fainter and
#              drier), Side = +-1; fades out after 8 s over 6 s. MudLeft - 1. Inside the puddle it stays at 6.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP, NAVMV, DECALC = CLS('ActorComponent'), CLS('NavMovementComponent'), CLS('DecalComponent')
MI_PRINT = '/Game/CastleDefender/Environment/Mud/MI_MudPrint.MI_MudPrint'


class BM(bpkit.B):
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
    def dist2d(s, a, c, x, y): return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n


def event_override(G, nm, parent, member, x, y):
    G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (parent, member), 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (parent, member)}, ex('then', True)], x, y)
    return nm


G = Graph(); b = BM(G, 'mp')
g = b.get
# ---------------------------------------------------------------- BeginPlay
event_override(G, 'MudBeginPlay', COMP, 'ReceiveBeginPlay', 0, 0)
nc = b.name('AsCharacter'); cast(G, nc, CHARC, 'AsCharacter', 250, 0); b.wire(b.owner(50, 200), nc, 'Object')
G.link('MudBeginPlay', 'then', nc, 'execute')
cm = b.call(CHARC, 'GetCharacterMovement', [ob('ReturnValue', CMC, out=True)], 450, 250, target=(nc, 'AsCharacter'), pure=True, const=True, tag='GetMove')
sm = b.set('Move', ob('v', CMC), (cm, 'ReturnValue'), 650, 0); G.link(nc, 'then', sm, 'execute')
ga = b.lib(GS, 'GetAllActorsWithTag', [WC(), {'name': 'Tag', 'cat': 'name', 'default': 'MudPad'}, arr(ob('OutActors', ACT, out=True))], 900, 0, tag='FindPads')
G.link(sm, 'then', ga, 'execute'); G.link(nc, 'CastFailed', ga, 'execute')
sp = b.set('Pads', arr(ob('v', ACT)), (ga, 'OutActors'), 1200, 0); G.link(ga, 'then', sp, 'execute')
sl = b.set('LastLoc', VECT, b.loc(b.owner(1250, 350), 1400, 300), 1450, 0); G.link(sp, 'then', sl, 'execute')
tm = b.timer_ev('MudTick', '0.05', 1750, 0); G.link(sl, 'then', tm, 'execute')

# ---------------------------------------------------------------- MudTick
Y = 900
b.event('MudTick', [], 0, Y)
me = lambda x, y: b.loc(b.owner(x - 200, y + 100), x, y)
s0 = b.set('InMud', BOOL, None, 250, Y); G.link('MudTick', 'then', s0, 'execute')
fe = b.foreach(ACT, 500, Y); G.link(s0, 'then', fe, 'Exec'); b.wire(g('Pads', arr(ob('v', ACT)), 300, Y + 250), fe, 'Array')
sc = b.call(ACT, 'GetActorScale3D', [V('ReturnValue', out=True)], 700, Y + 450, target=(fe, 'Array Element'), pure=True, const=True, tag='PadScale')
sx = b.brk((sc, 'ReturnValue'), 900, Y + 450)
rad = b.d2('Multiply_DoubleDouble', sx['X'], None, 1100, Y + 450, db='140.0')
near = b.dcmp('Less_DoubleDouble', b.dist2d(me(900, Y + 300), b.loc((fe, 'Array Element'), 900, Y + 600), 1100, Y + 300), rad, 1300, Y + 350)
inpad = b.b2('BooleanAND', b.valid((fe, 'Array Element'), 1300, Y + 200), near, 1500, Y + 250)
bp_ = b.branch(inpad, 1000, Y, tag='IfInPad'); G.link(fe, 'LoopBody', bp_, 'execute')
s1 = b.set('InMud', dict(BOOL, default='true'), None, 1300, Y)
G.link(bp_, 'then', s1, 'execute')

X = 1800
bm = b.branch(g('InMud', BOOL, X - 100, Y + 1000), X, Y + 800, tag='IfInMud'); G.link(fe, 'Completed', bm, 'execute')
sfull = b.set('MudLeft', INT, g('Prints', INT, X + 150, Y + 1050), X + 300, Y + 700); G.link(bm, 'then', sfull, 'execute')
X = 2400
left = b.icmp('Greater_IntInt', g('MudLeft', INT, X - 300, Y + 1100), None, X - 100, Y + 1100, db='0')
far = b.dcmp('GreaterEqual_DoubleDouble', b.dist2d(me(X - 500, Y + 1250), g('LastLoc', VECT, X - 500, Y + 1450), X - 300, Y + 1300),
             g('Stride', DBL, X - 300, Y + 1450), X - 100, Y + 1300)
fall = b.call(NAVMV, 'IsFalling', [bo('ReturnValue', out=True)], X - 300, Y + 1550, target=g('Move', ob('v', CMC), X - 500, Y + 1600), pure=True, const=True, tag='Falling')
go = b.b2('BooleanAND', b.b2('BooleanAND', left, far, X + 100, Y + 1150), b.bnot((fall, 'ReturnValue'), X - 100, Y + 1550), X + 300, Y + 1250)
bs = b.branch(go, X + 300, Y + 800, tag='IfStep')
G.link(sfull, 'then', bs, 'execute'); G.link(bm, 'else', bs, 'execute')

X = 2900
ss = b.set('Side', DBL, b.d2('Multiply_DoubleDouble', g('Side', DBL, X - 100, Y + 1000), None, X + 50, Y + 1000, db='-1.0'), X + 100, Y + 800)
G.link(bs, 'then', ss, 'execute')
own = b.owner(X + 100, Y + 1300)
rv = b.call(ACT, 'GetActorRightVector', [V('ReturnValue', out=True)], X + 300, Y + 1300, target=own, pure=True, const=True, tag='Right')
side = b.math('Multiply_VectorFloat', [(V('A'), (rv, 'ReturnValue')), (D('B', default='1.0'), b.d2('Multiply_DoubleDouble', g('Side', DBL, X + 300, Y + 1550), None, X + 450, Y + 1500, db='11.0'))],
              V('ReturnValue', out=True), X + 600, Y + 1350)
foot = b.v2('Add_VectorVector', b.loc(own, X + 600, Y + 1200), side, X + 800, Y + 1250)
drop = b.math('Multiply_VectorFloat', [(V('A', default='0.000000,0.000000,-1.000000'), None), (D('B', default='92.0'), g('FootDrop', DBL, X + 800, Y + 1550))],
              V('ReturnValue', out=True), X + 950, Y + 1450)
at = b.v2('Add_VectorVector', foot, drop, X + 1100, Y + 1300)
rot = b.call(ACT, 'K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], X + 600, Y + 1700, target=own, pure=True, const=True, tag='Rot')
br = b.name('BreakRot')
G.node(br, 'K2Node_CallFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="BreakRotator")' % KML],
       [selfpin(KML, hidden=True), st('InRot', ROT), fl('Roll', out=True), fl('Pitch', out=True), fl('Yaw', out=True)], X + 800, Y + 1700)
G.link(rot, 'ReturnValue', br, 'InRot')
mr = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='-90.0'), None), (fl('Yaw', default='0.0'), (br, 'Yaw'))],
            st('ReturnValue', ROT, out=True), X + 1050, Y + 1700)
sd = b.lib(GS, 'SpawnDecalAtLocation', [WC(), ob('DecalMaterial', MATI), V('DecalSize', default='12.000000,15.000000,15.000000'), V('Location'),
                                         st('Rotation', ROT, default='-90.000000,0.000000,0.000000'), fl('LifeSpan', default='16.0'), ob('ReturnValue', DECALC, out=True)],
           X + 1300, Y + 800, tag='SpawnPrint')
b.wire(g('PrintMat', MATV, X + 1100, Y + 1100), sd, 'DecalMaterial'); b.wire(at, sd, 'Location'); b.wire(mr, sd, 'Rotation')
G.link(ss, 'then', sd, 'execute')
fo = b.call(DECALC, 'SetFadeOut', [fl('StartDelay', default='8.0'), fl('Duration', default='6.0'), bo('DestroyOwnerAfterFade', default='false')],
            X + 1650, Y + 800, target=(sd, 'ReturnValue'), tag='Fade')
G.link(sd, 'then', fo, 'execute')
dm = b.call(DECALC, 'CreateDynamicMaterialInstance', [ob('ReturnValue', MID, out=True)], X + 1950, Y + 800, target=(sd, 'ReturnValue'), tag='PrintMID')
G.link(fo, 'then', dm, 'execute')
strength = b.d2('Divide_DoubleDouble', b.i2d(g('MudLeft', INT, X + 1900, Y + 1150), X + 2050, Y + 1150), b.i2d(g('Prints', INT, X + 1900, Y + 1300), X + 2050, Y + 1300),
                X + 2250, Y + 1200, db='6.0')
p1 = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', 'Strength'), fl('Value', default='1.0')], X + 2300, Y + 800, target=(dm, 'ReturnValue'), tag='SetStrength')
b.wire(strength, p1, 'Value'); G.link(dm, 'then', p1, 'execute')
p2 = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', 'Side'), fl('Value', default='1.0')], X + 2600, Y + 800, target=(dm, 'ReturnValue'), tag='SetSide')
b.wire(g('Side', DBL, X + 2450, Y + 1100), p2, 'Value'); G.link(p1, 'then', p2, 'execute')
sm2 = b.set('MudLeft', INT, b.i2('Subtract_IntInt', g('MudLeft', INT, X + 2750, Y + 1100), None, X + 2900, Y + 1100, db='1'), X + 2900, Y + 800)
G.link(p2, 'then', sm2, 'execute')
sl2 = b.set('LastLoc', VECT, me(X + 3100, Y + 1100), X + 3200, Y + 800); G.link(sm2, 'then', sl2, 'execute')


pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
names = [n[0] for n in G.nodes]; dup = {n for n in names if names.count(n) > 1}
if dup: raise SystemExit('duplicate names: %s' % sorted(dup))
open(os.path.join(HERE, 'BPC_MudPrints_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_MudPrints: nodes %d, links %d' % (len(G.nodes), len(G.links)))

VARS = [('Pads', 'arr:Actor', '', 'the BP_MudPad actors (tag MudPad), found at BeginPlay'),
        ('Move', 'obj:CharacterMovementComponent', '', "the owner's movement (no prints in the air)"),
        ('InMud', 'bool', 'false', 'standing in a puddle this tick'),
        ('MudLeft', 'int', '0', 'muddy prints still to leave'),
        ('Prints', 'int', '6', 'prints after leaving the mud ("a few steps")'),
        ('Side', 'real', '1.0', 'left / right foot (+-1)'),
        ('LastLoc', 'vec', '', 'where the last print was made'),
        ('Stride', 'real', '80.0', 'cm between prints'),
        ('FootDrop', 'real', '92.0', 'cm from the actor centre to the soles (capsule half height)'),
        ('PrintMat', 'obj:MaterialInterface', MI_PRINT, 'the boot print decal (MI_MudPrint)')]


def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('int', 'bool'): return 'PinCategory="%s"' % kind
    if kind == 'vec': return 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
    if kind.startswith('arr:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'",ContainerType=Array' % kind[4:]
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'mud292/%s' % n).hex.upper(), vt(k), n, d)
out = ['# #292 BPC_MudPrints - paste one line at a time on the VARIABLES header of My Blueprint, then Compile'] + [bpv(*v[:3]) for v in VARS]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #292 BPC_MudPrints variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _k, d, m in VARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
print('BPVar lines: %d' % len(VARS))
