# #230 Deploy cannon (checkking, 2026-10-30 night). Two new Blueprints, UE 5.3, all casts / actor lookups in the exec chain.
#   BP_CannonOrder  (new Actor, the "artillery yard" marker): hero in range + O key -> price check on BP_ZombieHUD.Gold ->
#                   reserve a free pad (an actor tagged CannonPad: its tag is swapped to CannonPadUsed) -> pay ->
#                   spawn BP_CannonConvoy 3 m in front -> StartConvoy(pad location, pad yaw) -> notice.
#   BP_CannonConvoy (new Character, like BP_OreCart): walks the NavMesh to the pad with 2 BP_SoldierSword crew beside it,
#                   wheels WheelL/WheelR roll by distance / 55.4 cm, 400 HP (any damage), every 1 s pulls zombies within
#                   15 m onto itself and re-issues the crew's follow; at the pad: spawns BP_Cannon there (pad yaw) and goes.
# Notices through BP_NoticeHUD.PushNotice(Text, Tier). python gen230.py -> BP_CannonOrder_graph.txt, BP_CannonConvoy_graph.txt,
# VARIABLES_BPVar.txt (BPVar lines to paste on each Blueprint's VARIABLES header, one at a time).
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

P_CASTLE = '/Game/CastleDefender/Gameplay/Castle/'
P_ORDER, P_CONVOY = P_CASTLE + 'BP_CannonOrder', P_CASTLE + 'BP_CannonConvoy'
P_CANNON = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannon'
P_HUD, P_NOTICE = P_CASTLE + 'BP_ZombieHUD', P_CASTLE + 'BP_NoticeHUD'
P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
ORDERC, CONVOYC, CANNONC = BPC(P_ORDER, 'BP_CannonOrder'), BPC(P_CONVOY, 'BP_CannonConvoy'), BPC(P_CANNON, 'BP_Cannon')
HUDC, NOTICEC, HEROC = BPC(P_HUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD'), BPC(P_HERO, 'BP_ThirdPersonCharacter')
SOLDC, ZOMBC = BPC(P_SOLDIER, 'BP_SoldierSword'), BPC(P_ZOMBIE, 'BP_Zombie')
HUDCLS, SMC = CLS('HUD'), CLS('StaticMeshComponent')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
INT, DBL, BOOL, VEC_ = it('v', default='0'), D('v', default='0.0'), bo('v', default='false'), V('v')
NAME_ = lambda n, default=None, out=False: {'name': n, 'cat': 'name', 'default': default, 'out': out}


def ev_over(b, nm, member, params, x, y):
    b.G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ACT, member), 'bOverrideFunction=True'],
             [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (ACT, member)}, ex('then', True)]
             + [dict(p, out=True) for p in params], x, y)
    return nm

def pc0(b, x, y):
    return b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC')

def notice(b, text, tier, x, y):
    """GetHUD -> Cast BP_NoticeHUD (exec) -> PushNotice(text, tier). Returns (first, last) exec nodes."""
    hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x, y + 300, target=(pc0(b, x - 250, y + 300), 'ReturnValue'), pure=True, const=True, tag='HUD')
    cn = b.name('AsNotice'); cast(b.G, cn, NOTICEC, 'AsBP Notice HUD', x + 250, y); b.wire((hud, 'ReturnValue'), cn, 'Object')
    pn = b.call(NOTICEC, 'PushNotice', [S('Text', default=text), it('Tier', default=str(tier))], x + 600, y, target=(cn, 'AsBP Notice HUD'), tag='Notice')
    b.G.link(cn, 'then', pn, 'execute')
    return cn, pn

def chain_join(b, first_exec_src, nodes):
    """link src -> nodes[0].execute and each (first, last) pair in order. first_exec_src: (node, pin)."""
    src = first_exec_src
    for f, l in nodes:
        b.G.link(src[0], src[1], f, 'execute'); src = (l, 'then')
    return src

def destroy(b, x, y): return b.call_self('K2_DestroyActor', [], x, y, ACT, tag='Destroy')

# =====================================================================================================================
# BP_CannonOrder
# =====================================================================================================================
G = Graph(); b = bpkit.B(G, 'co')
bp = ev_over(b, 'OrderBeginPlay', 'ReceiveBeginPlay', [], 0, 0)
en = b.call_self('EnableInput', [ob('PlayerController', PCON)], 300, 0, ACT, tag='EnableInput'); b.wire((pc0(b, 100, 200), 'ReturnValue'), en, 'PlayerController')
G.link(bp, 'then', en, 'execute')
# range: overlap with the hero (sphere / box collision on this actor)
Y = 600
ov = ev_over(b, 'OrderOverlap', 'ReceiveActorBeginOverlap', [ob('OtherActor', ACT)], 0, Y)
ch = b.name('AsHeroIn'); cast(G, ch, HEROC, 'AsBP Third Person Character', 300, Y); b.wire((ov, 'OtherActor'), ch, 'Object'); G.link(ov, 'then', ch, 'execute')
si = b.set('InRange', bo('v', default='true'), None, 650, Y); G.link(ch, 'then', si, 'execute')
f, l = notice(b, 'Artillery yard - press O to order a cannon', 0, 1000, Y); G.link(si, 'then', f, 'execute')
Y = 1300
eo = ev_over(b, 'OrderEndOverlap', 'ReceiveActorEndOverlap', [ob('OtherActor', ACT)], 0, Y)
ch2 = b.name('AsHeroOut'); cast(G, ch2, HEROC, 'AsBP Third Person Character', 300, Y); b.wire((eo, 'OtherActor'), ch2, 'Object'); G.link(eo, 'then', ch2, 'execute')
so = b.set('InRange', BOOL, None, 650, Y); G.link(ch2, 'then', so, 'execute')
# key O (the actor has input enabled; O is free: C = commander panel, T tree, I pack, E orders)
Y = 1900
G.node('OrderKey', 'K2Node_InputKey', ['InputKey=O', 'bConsumeInput=False'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '()'}, ex('Pressed', True), ex('Released', True),
        st('Key', KEY, out=True)], 0, Y)
bk = b.branch(b.get('InRange', BOOL, 0, Y + 300), 300, Y, tag='IfInRange'); G.link('OrderKey', 'Pressed', bk, 'execute')
hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], 500, Y + 300, target=(pc0(b, 300, Y + 400), 'ReturnValue'), pure=True, const=True, tag='HUD')
cz = b.name('AsZHud'); cast(G, cz, HUDC, 'AsBP Zombie HUD', 600, Y); b.wire((hud, 'ReturnValue'), cz, 'Object'); G.link(bk, 'then', cz, 'execute')
zh = (cz, 'AsBP Zombie HUD')
gold = b.getm('Gold', HUDC, INT, zh, 900, Y + 300)
bg = b.branch(b.icmp('GreaterEqual_IntInt', gold, b.get('Price', it('v', default='800'), 900, Y + 450), 1100, Y + 350), 1000, Y, tag='IfGold')
G.link(cz, 'then', bg, 'execute')
nf, nl = notice(b, 'Not enough gold for a cannon', 1, 1300, Y + 700); G.link(bg, 'else', nf, 'execute')
pads = b.lib(GS, 'GetAllActorsWithTag', [WC(), NAME_('Tag', 'CannonPad'), arr(ob('OutActors', ACT, out=True))], 1300, Y, tag='FindPads')
G.link(bg, 'then', pads, 'execute')
plen = b.name('PadCount')
G.node(plen, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'object', 'obj': ACT, 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 1600, Y + 300)
b.wire((pads, 'OutActors'), plen, 'TargetArray')
bp_ = b.branch(b.icmp('Greater_IntInt', (plen, 'ReturnValue'), None, 1800, Y + 300, db='0'), 1700, Y, tag='IfPad')
G.link(pads, 'then', bp_, 'execute')
nf2, nl2 = notice(b, 'No free cannon pad on the walls', 1, 1900, Y + 900); G.link(bp_, 'else', nf2, 'execute')
pad = b.name('Pad'); G.node(pad, 'K2Node_GetArrayItem', [], [arr(ob('Array', ACT)), it('Dimension 1', default='0'), ob('Output', ACT, out=True)], 1900, Y + 300)
b.wire((pads, 'OutActors'), pad, 'Array')
# reserve the pad: Tags = [CannonPadUsed]
mk = b.name('UsedTags'); G.node(mk, 'K2Node_MakeArray', ['NumInputs=1'], [NAME_('[0]', 'CannonPadUsed'), arr(NAME_('Array', out=True))], 2100, Y + 450)
st_ = b.setm('Tags', ACT, arr(NAME_('v')), (mk, 'Array'), (pad, 'Output'), 2300, Y)
G.link(bp_, 'then', st_, 'execute')
pay = b.setm('Gold', HUDC, INT, b.i2('Subtract_IntInt', gold, b.get('Price', it('v', default='800'), 2400, Y + 650), 2600, Y + 600), zh, 2700, Y)
G.link(st_, 'then', pay, 'execute')
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 2800, Y + 500, ACT, pure=True, const=True, tag='YardLoc')
fw = b.call_self('GetActorForwardVector', [V('ReturnValue', out=True)], 2800, Y + 650, ACT, pure=True, const=True, tag='YardFwd')
loc = b.v2('Add_VectorVector', (me, 'ReturnValue'), b.math('Multiply_VectorFloat', [(V('A'), (fw, 'ReturnValue')), (D('B', default='300.0'), None)], V('ReturnValue', out=True), 3000, Y + 650), 3200, Y + 550)
sp = spawn(b, P_CONVOY, CONVOYC, transform(b, loc, 3400, Y + 550), 3100, Y); G.link(pay, 'then', sp, 'execute')
pl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 3300, Y + 800, target=(pad, 'Output'), pure=True, const=True, tag='PadLoc')
pr = b.call(ACT, 'K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], 3300, Y + 950, target=(pad, 'Output'), pure=True, const=True, tag='PadRot')
mathfn(G, 'PadYaw', 'BreakRotator', [st('InRot', ROT), D('Roll', out=True, default='0.0'), D('Pitch', out=True, default='0.0'), D('Yaw', out=True, default='0.0')], 3550, Y + 950)
G.link(pr, 'ReturnValue', 'PadYaw', 'InRot')
sc = b.call(CONVOYC, 'StartConvoy', [V('Target'), D('Yaw', default='0.0')], 3700, Y, target=(sp, 'ReturnValue'), tag='StartConvoy')
b.wire((pl, 'ReturnValue'), sc, 'Target'); G.link('PadYaw', 'Yaw', sc, 'Yaw'); G.link(sp, 'then', sc, 'execute')
nf3, nl3 = notice(b, 'Cannon ordered - the crew is on the way', 0, 4000, Y); G.link(sc, 'then', nf3, 'execute')
open(os.path.join(HERE, 'BP_CannonOrder_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_CannonOrder', len(G.nodes), 'nodes', len(G.links), 'links')

# =====================================================================================================================
# BP_CannonConvoy
# =====================================================================================================================
G = Graph(); b = bpkit.B(G, 'cv')
ev = b.event('StartConvoy', [V('Target'), D('Yaw')], 0, 0)
s1 = b.set('Target', VEC_, (ev, 'Target'), 300, 0); G.link(ev, 'then', s1, 'execute')
s2 = b.set('TargetYaw', DBL, (ev, 'Yaw'), 550, 0); G.link(s1, 'then', s2, 'execute')
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 600, 300, ACT, pure=True, const=True, tag='CartLoc')
s3 = b.set('LastLoc', VEC_, (me, 'ReturnValue'), 800, 0); G.link(s2, 'then', s3, 'execute')
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 900, 300, PAWN, pure=True, const=True, tag='Ctl')
mv = b.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], 1100, 0, tag='GoToPad')
b.wire((ctl, 'ReturnValue'), mv, 'Controller'); b.wire((ev, 'Target'), mv, 'Goal'); G.link(s3, 'then', mv, 'execute')
rv = b.call_self('GetActorRightVector', [V('ReturnValue', out=True)], 1200, 500, ACT, pure=True, const=True, tag='CartRight')
last = mv
for k, side in enumerate(('220.0', '-220.0')):
    x = 1400 + k * 800
    off = b.math('Multiply_VectorFloat', [(V('A'), (rv, 'ReturnValue')), (D('B', default=side), None)], V('ReturnValue', out=True), x, 500)
    sp = spawn(b, P_SOLDIER, SOLDC, transform(b, b.v2('Add_VectorVector', (me, 'ReturnValue'), off, x + 200, 500), x + 400, 500), x, 0)
    G.link(last, 'then', sp, 'execute')
    ad = b.aadd('Crew', ob('v', ACT), (sp, 'ReturnValue'), x + 400, 0); G.link(sp, 'then', ad, 'execute'); last = ad
t1 = b.timer('Step', 3100, 0, dtime='0.1', loop=True); G.link(last, 'then', t1, 'execute')
t2 = b.timer('Lure', 3400, 0, dtime='1.0', loop=True); G.link(t1, 'then', t2, 'execute')
nf, nl = notice(b, 'Cannon cart on the way - guard it', 0, 3700, 0); G.link(t2, 'then', nf, 'execute')

# ---- Step (0.1 s): wheels + arrival
Y = 1300
b.event('Step', [], 0, Y)
me2 = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 0, Y + 300, ACT, pure=True, const=True, tag='CartLoc')
moved = b.math('VSizeXY', [(V('A'), b.v2('Subtract_VectorVector', (me2, 'ReturnValue'), b.get('LastLoc', VEC_, 0, Y + 450), 250, Y + 400))], D('ReturnValue', out=True), 450, Y + 400)
ang = b.d2('Add_DoubleDouble', b.get('WheelAngle', DBL, 450, Y + 550), b.d2('Multiply_DoubleDouble', moved, None, 650, Y + 450, db='1.034'), 850, Y + 500)   # deg per cm = 57.2958 / 55.4
sa = b.set('WheelAngle', DBL, ang, 300, Y); G.link('Step', 'then', sa, 'execute')
sl = b.set('LastLoc', VEC_, (me2, 'ReturnValue'), 550, Y); G.link(sa, 'then', sl, 'execute')
rot = b.math('MakeRotator', [(D('Roll', default='0.0'), None), (D('Pitch', default='0.0'), b.d2('Multiply_DoubleDouble', b.get('WheelAngle', DBL, 700, Y + 650), None, 900, Y + 650, db='-1.0')),
                             (D('Yaw', default='0.0'), None)], st('ReturnValue', ROT, out=True), 1100, Y + 650)
last = sl
for k, w in enumerate(('WheelL', 'WheelR')):
    n = b.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
               bo('bTeleport', default='true')], 900 + k * 300, Y, target=b.get(w, ob('v', SMC), 800 + k * 300, Y + 250), tag='Roll' + w)
    b.wire(rot, n, 'NewRotation'); G.link(last, 'then', n, 'execute'); last = n
arrive = b.dcmp('Less_DoubleDouble', b.math('VSizeXY', [(V('A'), b.v2('Subtract_VectorVector', b.get('Target', VEC_, 1300, Y + 500), (me2, 'ReturnValue'), 1500, Y + 500))],
                D('ReturnValue', out=True), 1700, Y + 500), None, 1900, Y + 500, db='220.0')
ba = b.branch(arrive, 1600, Y, tag='IfAtPad'); G.link(last, 'then', ba, 'execute')
c1 = b.timer_fn('K2_ClearTimer', 'Step', 1900, Y); G.link(ba, 'then', c1, 'execute')
c2 = b.timer_fn('K2_ClearTimer', 'Lure', 2150, Y); G.link(c1, 'then', c2, 'execute')
mr = b.math('MakeRotator', [(D('Roll', default='0.0'), None), (D('Pitch', default='0.0'), None), (D('Yaw', default='0.0'), b.get('TargetYaw', DBL, 2200, Y + 600))], st('ReturnValue', ROT, out=True), 2400, Y + 600)
xf = b.math('MakeTransform', [(V('Location'), b.get('Target', VEC_, 2200, Y + 450)), (st('Rotation', ROT, default='0, 0, 0'), mr), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
            st('ReturnValue', XFORM, out=True), 2600, Y + 500)
spc = spawn(b, P_CANNON, CANNONC, xf, 2400, Y); G.link(c2, 'then', spc, 'execute')
nf, nl = notice(b, 'Cannon deployed on the wall', 0, 2800, Y); G.link(spc, 'then', nf, 'execute')
ds = destroy(b, 3500, Y); G.link(nl, 'then', ds, 'execute')

# ---- Lure (1 s): crew walk beside the cart; zombies within 15 m go for the cart (ShouldTargetConvoy)
Y = 2600
b.event('Lure', [], 0, Y)
me3 = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 0, Y + 400, ACT, pure=True, const=True, tag='CartLoc')
lc = b.name('ForCrew'); G.node(lc, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FOREACH, 'ResolvedWildcardType=(PinCategory="object",PinSubCategoryObject=%s)' % ACT],
      [ex('Exec'), arr(ob('Array', ACT)), ex('LoopBody', True), ob('Array Element', ACT, out=True), it('Array Index', out=True), ex('Completed', True)], 300, Y)
G.link('Lure', 'then', lc, 'Exec'); b.wire(b.get('Crew', arr(ob('v', ACT)), 100, Y + 200), lc, 'Array')
cp = b.name('AsCrew'); cast(G, cp, PAWN, 'AsPawn', 600, Y); b.wire((lc, 'Array Element'), cp, 'Object'); G.link(lc, 'LoopBody', cp, 'execute')
cc = b.call(PAWN, 'GetController', [ob('ReturnValue', CTRL, out=True)], 800, Y + 300, target=(cp, 'AsPawn'), pure=True, const=True, tag='CrewCtl')
side = b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', b.i2d((lc, 'Array Index'), 800, Y + 500), None, 1000, Y + 500, db='0.5'), None, 1200, Y + 500, db='440.0')
rv3 = b.call_self('GetActorRightVector', [V('ReturnValue', out=True)], 1000, Y + 650, ACT, pure=True, const=True, tag='CartRight')
goal = b.v2('Add_VectorVector', (me3, 'ReturnValue'), b.math('Multiply_VectorFloat', [(V('A'), (rv3, 'ReturnValue')), (D('B', default='0.0'), side)], V('ReturnValue', out=True), 1300, Y + 650), 1500, Y + 550)
cm = b.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], 1100, Y, tag='CrewFollow')
b.wire((cc, 'ReturnValue'), cm, 'Controller'); b.wire(goal, cm, 'Goal'); G.link(cp, 'then', cm, 'execute')
az = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_ZOMBIE)), arr(ob('OutActors', ZOMBC, out=True))], 600, Y + 900, tag='AllZombies')
G.link(lc, 'Completed', az, 'execute')
lz = b.foreach(ZOMBC, 900, Y + 900); G.link(az, 'then', lz, 'Exec'); G.link(az, 'OutActors', lz, 'Array')
zl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1000, Y + 1250, target=(lz, 'Array Element'), pure=True, const=True, tag='ZLoc')
near = b.dcmp('Less_DoubleDouble', b.math('Vector_Distance', [(V('V1'), (zl, 'ReturnValue')), (V('V2'), (me3, 'ReturnValue'))], D('ReturnValue', out=True), 1250, Y + 1250), None, 1450, Y + 1250, db='1500.0')
bn = b.branch(near, 1300, Y + 900, tag='IfZNear'); G.link(lz, 'LoopBody', bn, 'execute')
zc = b.call(PAWN, 'GetController', [ob('ReturnValue', CTRL, out=True)], 1500, Y + 1100, target=(lz, 'Array Element'), pure=True, const=True, tag='ZCtl')
me4 = b.self_node(1500, Y + 1400)
zm = b.lib(NAVSYS, 'SimpleMoveToActor', [ob('Controller', CTRL), ob('Goal', ACT)], 1700, Y + 900, tag='ZToCart')
b.wire((zc, 'ReturnValue'), zm, 'Controller'); b.wire(me4, zm, 'Goal'); G.link(bn, 'then', zm, 'execute')

# ---- damage
Y = 4400
dm = ev_over(b, 'ConvoyAnyDamage', 'ReceiveAnyDamage', [fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CTRL), ob('DamageCauser', ACT)], 0, Y)
hp = b.set('HP', DBL, b.d2('Subtract_DoubleDouble', b.get('HP', D('v', default='400.0'), 300, Y + 300), (dm, 'Damage'), 550, Y + 300), 800, Y)
G.link(dm, 'then', hp, 'execute')
bd = b.branch(b.dcmp('LessEqual_DoubleDouble', b.get('HP', DBL, 1000, Y + 300), None, 1200, Y + 300, db='0.0'), 1300, Y, tag='IfWrecked')
G.link(hp, 'then', bd, 'execute')
nf, nl = notice(b, 'The cannon cart was destroyed', 1, 1600, Y); G.link(bd, 'then', nf, 'execute')
ds2 = destroy(b, 2300, Y); G.link(nl, 'then', ds2, 'execute')
open(os.path.join(HERE, 'BP_CannonConvoy_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_CannonConvoy', len(G.nodes), 'nodes', len(G.links), 'links')

# ---- BPVar lines (paste on the VARIABLES header, one per paste)
def bpvar(name, vt, default):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),PropertyFlags=5,DefaultValue="%s")' % (name, uuid.uuid4().hex.upper(), vt, default)
REAL = 'PinCategory="real",PinSubCategory="double"'
VECT = 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
lines = ['# BP_CannonOrder', bpvar('InRange', 'PinCategory="bool"', 'false'), bpvar('Price', 'PinCategory="int"', '800'), '',
         '# BP_CannonConvoy', bpvar('HP', REAL, '400.0'), bpvar('Target', VECT, '0,0,0'), bpvar('TargetYaw', REAL, '0.0'),
         bpvar('LastLoc', VECT, '0,0,0'), bpvar('WheelAngle', REAL, '0.0'),
         bpvar('Crew', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",ContainerType=Array', '')]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(lines) + '\n')
