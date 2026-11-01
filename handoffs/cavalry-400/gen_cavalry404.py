# #404 Heavy cavalry (checkking (Claude), 2026-11-01): mounted knights on barded destriers that charge with the lance.
#   "<blender python>" -I gen_cavalry404.py -> BP_Cavalry_graph.txt, BPC_Cavalry_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# Design and numbers: GAMEPLAY.md. Pattern: the #185 medics (adjustedfilm): a plain Character unit + a hero component that
# recruits it with a key, built with bpkit (tools/laptop2/bpgen).
# BP_Cavalry (Character): Mesh = SK_Destrier; components Tack / Lance / RiderLegs (leader pose on Mesh) and Rider (the
#   soldier's own body, attached to bone RiderSocket, legs hidden). Think every 0.2 s: follow -> charge -> impact ->
#   ride through -> wheel -> rest. Bogged in a crowd = attrition. ReceiveAnyDamage + Die.
# BPC_Cavalry (hero component "Cavalry"): at the stables (tag Stables) or the barracks NPC, notice
#   "[L] Raise a knight on a barded destrier: 400 gold (n/4)"; L buys (BP_ZombieHUD.Gold) -> a BP_Cavalry rides out.
import math, os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))     # bpkit has its own HERE

COMP = CLS('ActorComponent')
P_CC = '/Game/CastleDefender/Gameplay/Cavalry/BPC_Cavalry'
P_CAV = '/Game/CastleDefender/Gameplay/Cavalry/BP_Cavalry'
P_NPC = '/Game/CastleDefender/Gameplay/Castle/BP_NPC_Barracks'
P_ZHUD, P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
CCC, CAVC, NPCC = BPC(P_CC, 'BPC_Cavalry'), BPC(P_CAV, 'BP_Cavalry'), BPC(P_NPC, 'BP_NPC_Barracks')
ZHUDC, NOTC = BPC(P_ZHUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
ANIMA, SOUND, DMGT = CLS('AnimationAsset'), CLS('SoundBase'), CLS('DamageType')
CAPS = CLS('CapsuleComponent')
CAVA = '/Game/CastleDefender/Characters/Cavalry'
def asset(n, root=CAVA): return '%s/%s.%s' % (root, n, n)
SND_HIT = '/Game/Audio/Kenney/SFX_impactMetal_heavy_003.SFX_impactMetal_heavy_003'
OBJV = lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
RULE = lambda n, d='SnapToTarget': {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', 'default': d}
FLV = fl('v', default='0.0')                                 # float (single) property pin
REAL = lambda n, d: fl('v', default=d, sub='double')


class BC(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def item(s, arrsrc, pin, idx, x, y):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def getall(s, path, cls, x, y):
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def arrlen(s, src, x, y):
        n = s.name('Len')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.wire(src, n, 'TargetArray'); return (n, 'ReturnValue')
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
    def myloc(s, x, y):
        n = s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'); return (n, 'ReturnValue')
    def actvec(s, member, actor, x, y):
        if actor is None: n = s.call_self(member, [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag=member[8:])
        else: n = s.call(ACT, member, [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag=member[8:])
        return (n, 'ReturnValue')
    def dist2d(s, a, c, x, y): return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def vmul(s, v, f, x, y, df='1.0'): return s.math('Multiply_VectorFloat', [(V('A'), v), (D('B', default=df), f)], V('ReturnValue', out=True), x, y)
    def vadd(s, a, c, x, y, db='0, 0, 0'): return s.v2('Add_VectorVector', a, c, x, y, db=db)
    def vsub(s, a, c, x, y): return s.v2('Subtract_VectorVector', a, c, x, y)
    def norm2d(s, v, x, y): return s.math('Normal2D', [(V('A'), v), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), x, y)
    def dot(s, a, c, x, y): return s.math('Dot_VectorVector', [(V('A'), a), (V('B'), c)], D('ReturnValue', out=True), x, y)
    def speed(s, x, y):
        v = s.call_self('GetVelocity', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='Vel')
        return s.math('VSizeXY', [(V('A'), (v, 'ReturnValue'))], D('ReturnValue', out=True), x + 200, y)
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hero(s, x, y):
        return (s.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], x, y, pure=True, tag='Hero'), 'ReturnValue')
    def hud_cast(s, cls, label, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', CLS('HUD'), out=True)], x - 150, y + 300, target=s.pc(x - 350, y + 300), pure=True, const=True, tag='GetHUD')
        nc = s.name('As' + label.replace(' ', '')); cast(s.G, nc, cls, 'As' + label, x, y); s.wire((hud, 'ReturnValue'), nc, 'Object'); return nc, (nc, 'As' + label)
    def notice(s, text, x, y, text_src=None):
        nc, nh = s.hud_cast(NOTC, 'BP Notice HUD', x, y)
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x + 300, y, target=nh, tag='Notice')
        s.wire(text_src, pn, 'Text'); s.G.link(nc, 'then', pn, 'execute'); return nc, pn
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.200000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def istr(s, src, x, y):
        n = s.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], x, y, pure=True, tag='IntStr'); s.wire(src, n, 'InInt'); return (n, 'ReturnValue')
    def ctl(s, x, y):
        return (s.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], x, y, PAWN, pure=True, const=True, tag='Ctl'), 'ReturnValue')
    def move_to(s, goal, x, y):
        mv = s.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], x + 250, y, tag='Move')
        s.wire(s.ctl(x, y + 250), mv, 'Controller'); s.wire(goal, mv, 'Goal'); return mv
    def comp(s, name, x, y): return s.get(name, OBJV(SKEL), x, y)
    def mesh(s, x, y): return s.getm('Mesh', CHARC, OBJV(SKEL), s.self_node(x - 150, y), x, y)
    def cmc(s, x, y): return s.getm('CharacterMovement', CHARC, OBJV(CMC), s.self_node(x - 150, y), x, y)
    def setspeed(s, src, x, y, d='450.0'):
        n = s.setm('MaxWalkSpeed', CMC, FLV, src, s.cmc(x - 200, y + 200), x, y)
        if src is None:
            for nm, c, props, pins, *_ in s.G.nodes:
                if nm == n:
                    for p in pins:
                        if p['name'] == 'MaxWalkSpeed': p['default'] = d
        return n
    def play(s, anim, loop, x, y):
        return s.call(SKEL, 'PlayAnimation', [dict(ob('NewAnimToPlay', ANIMA), dobj=asset(anim)), bo('bLooping', default='true' if loop else 'false')], x, y,
                      target=s.mesh(x - 200, y + 200), tag='Play' + anim[11:])
    def apply_damage(s, victim, dmg, x, y, ddmg='0.0'):
        n = s.lib(GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage', default=ddmg), ob('EventInstigator', CTRL), ob('DamageCauser', ACT),
                                      {'name': 'DamageTypeClass', 'cat': 'class', 'obj': DMGT}, fl('ReturnValue', out=True, default='0.0')], x, y, tag='Damage')
        s.wire(victim, n, 'DamagedActor'); s.wire(dmg, n, 'BaseDamage'); s.wire(s.self_node(x - 200, y + 300), n, 'DamageCauser'); return n
    def launch(s, victim, vel, x, y):
        n = s.call(CHARC, 'LaunchCharacter', [V('LaunchVelocity'), bo('bXYOverride', default='true'), bo('bZOverride', default='true')], x, y, target=victim, tag='Launch')
        s.wire(vel, n, 'LaunchVelocity'); return n
    def acontains(s, arrsrc, item, x, y):
        n = s.name('Has')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'bIsConstFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Contains")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'object', 'obj': ZOMBIE, 'container': 'Array', 'ref': True},
                  {'name': 'ItemToFind', 'cat': 'object', 'obj': ZOMBIE, 'ref': True}, bo('ReturnValue', out=True, default='false')], x, y)
        s.wire(arrsrc, n, 'TargetArray'); s.wire(item, n, 'ItemToFind'); return (n, 'ReturnValue')
    def aclear(s, arrvar, pin, x, y):
        a = s.get(arrvar, arr(pin), x, y + 150); n = s.name('Clear' + arrvar)
        s.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
                 [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], x, y)
        s.wire(a, n, 'TargetArray'); return n
    def setvis(s, comp, on, x, y):
        return s.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='true' if on else 'false'), bo('bPropagateToChildren', default='false')], x, y,
                      target=comp, tag='Vis' + ('On' if on else 'Off'))


def event_override(G, nm, parent, member, params, x, y):
    G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (parent, member), 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (parent, member)}, ex('then', True)]
           + [dict(p, out=True) for p in params], x, y)
    return nm


def write(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    if bad: raise SystemExit('%s bad links: %s' % (name, bad[:10]))
    names = [n[0] for n in G.nodes]; dup = {n for n in names if names.count(n) > 1}
    if dup: raise SystemExit('%s duplicate names: %s' % (name, sorted(dup)[:10]))
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (name, len(G.nodes), len(G.links)))


# ================================================================================================= BP_Cavalry
G = Graph(); b = BC(G, 'cv')
g = b.get
INTV = lambda d: it('v', default=d)
# ---- BeginPlay: leader pose, rider on the saddle, mane hidden, slot, idle, Think timer
event_override(G, 'BP', ACT, 'ReceiveBeginPlay', [], 0, 0)
last = 'BP'; X = 300
for cname in ('Tack', 'Lance', 'RiderLegs'):
    n = b.call(SKIN, 'SetLeaderPoseComponent', [ob('NewLeaderBoneComponent', SKIN), bo('bForceUpdate', default='false'), bo('bFollowerShouldTickPose', default='false')],
               X, 0, target=b.comp(cname, X - 200, 200), tag='Leader' + cname)
    b.wire(b.mesh(X - 200, 320), n, 'NewLeaderBoneComponent'); G.link(last, 'then', n, 'execute'); last = n; X += 350
at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), NAME_('SocketName', 'RiderSocket'), RULE('LocationRule'), RULE('RotationRule', 'KeepWorld'),
            RULE('ScaleRule', 'KeepWorld'), bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], X, 0, target=b.comp('Rider', X - 200, 200), tag='AttachRider')
b.wire(b.mesh(X - 200, 320), at, 'Parent'); G.link(last, 'then', at, 'execute'); last = at; X += 350
off = b.call(SCENE, 'K2_AddWorldOffset', [V('DeltaLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
             X, 0, target=b.comp('Rider', X - 200, 200), tag='RiderDrop')
b.wire(b.vec(None, None, g('RiderDrop', REAL('v', '-92.0'), X - 400, 400), X - 200, 400), off, 'DeltaLocation'); G.link(last, 'then', off, 'execute'); last = off; X += 350
for bone in ('thigh_l', 'thigh_r', 'LeftUpLeg', 'RightUpLeg'):          # mannequin + Mixamo names; a missing name does nothing
    hb = b.call(SKIN, 'HideBoneByName', [NAME_('BoneName', bone), {'name': 'PhysBodyOption', 'cat': 'byte', 'obj': ENUM('EPhysBodyOp'), 'default': 'PBO_None'}],
                X, 0, target=b.comp('Rider', X - 200, 200), tag='Hide' + bone)
    G.link(last, 'then', hb, 'execute'); last = hb; X += 300
mn = b.call(PRIM, 'SetMaterialByName', [NAME_('MaterialSlotName', 'M_DestrierMane'), dict(ob('Material', MATI), dobj=asset('M_CavalryInvisible'))], X, 0,
            target=b.mesh(X - 200, 200), tag='HideMane')
G.link(last, 'then', mn, 'execute'); last = mn; X += 350
pi = b.play('A_Destrier_Idle', True, X, 0); G.link(last, 'then', pi, 'execute'); last = pi; X += 350
ga = b.getall(P_CAV, CAVC, X, 0); G.link(last, 'then', ga, 'execute'); last = ga; X += 350
ss_ = b.set('Slot', INTV('0'), b.i2('Subtract_IntInt', b.arrlen((ga, 'OutActors'), X - 100, 300), None, X + 100, 300, db='1'), X, 0)
G.link(last, 'then', ss_, 'execute'); last = ss_; X += 300
shp = b.set('HP', REAL('v', '600.0'), g('MaxHP', REAL('v', '600.0'), X - 100, 300), X, 0); G.link(last, 'then', shp, 'execute'); last = shp; X += 300
tm = b.timer_ev('Think', '0.2', X, 0); G.link(last, 'then', tm, 'execute')

# ---- Think
Y = 1200
b.event('Think', [], 0, Y)
dead = b.branch(b.icmp('EqualEqual_IntInt', g('State', INTV('0'), 100, Y + 250), None, 300, Y + 250, db='9'), 300, Y, tag='IfDead')
G.link('Think', 'then', dead, 'execute')
seq = b.seq('ThinkSeq', 4, 600, Y); G.link(dead, 'else', seq, 'execute')
now = lambda x, y: b.now(x, y)
STATE = lambda x, y: g('State', INTV('0'), x, y)
heroh = b.hero(400, Y + 6000)
# then_0: scan zombies -> Zs, NearCount, BestZ, Best
X = 900
z1 = b.set('NearCount', INTV('0'), None, X, Y); z2 = b.set('Best', REAL('v', '0.0'), g('Acquire', REAL('v', '3500.0'), X + 150, Y + 250), X + 250, Y)
z3 = b.set('BestZ', OBJV(ZOMBIE), None, X + 500, Y)
G.link(seq, 'then_0', z1, 'execute'); b.chain(z1, z2, z3)
gz = b.getall('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', ZOMBIE, X + 750, Y); G.link(z3, 'then', gz, 'execute')
sz = b.set('Zs', arr(OBJV(ZOMBIE)), (gz, 'OutActors'), X + 1050, Y); G.link(gz, 'then', sz, 'execute')
fe = b.foreach(ZOMBIE, X + 1300, Y); G.link(sz, 'then', fe, 'Exec'); b.wire((gz, 'OutActors'), fe, 'Array')
el = (fe, 'Array Element')
life = b.call(ACT, 'GetLifeSpan', [fl('ReturnValue', out=True, default='0.0')], X + 1300, Y + 500, target=el, pure=True, const=True, tag='Life')
alive = b.dcmp('Less_DoubleDouble', (life, 'ReturnValue'), None, X + 1500, Y + 500, db='0.01')
dz = b.dist2d(b.myloc(X + 1300, Y + 650), b.loc(el, X + 1300, Y + 750), X + 1500, Y + 700)
bal = b.branch(alive, X + 1600, Y, tag='IfAlive'); G.link(fe, 'LoopBody', bal, 'execute')
bnear = b.branch(b.dcmp('Less_DoubleDouble', dz, None, X + 1800, Y + 300, db='300.0'), X + 1850, Y, tag='IfNear'); G.link(bal, 'then', bnear, 'execute')
inc = b.set('NearCount', INTV('0'), b.i2('Add_IntInt', g('NearCount', INTV('0'), X + 1900, Y - 300), None, X + 2100, Y - 300, db='1'), X + 2100, Y - 150)
G.link(bnear, 'then', inc, 'execute')
mgn = b.seq('NearDone', 1, X + 2400, Y); G.link(inc, 'then', mgn, 'execute'); G.link(bnear, 'else', mgn, 'execute')
bbest = b.branch(b.dcmp('Less_DoubleDouble', dz, g('Best', REAL('v', '0.0'), X + 2500, Y + 300), X + 2700, Y + 300), X + 2650, Y, tag='IfBest')
G.link(mgn, 'then_0', bbest, 'execute')
sb1 = b.set('Best', REAL('v', '0.0'), dz, X + 2950, Y - 150); sb2 = b.set('BestZ', OBJV(ZOMBIE), el, X + 3200, Y - 150)
G.link(bbest, 'then', sb1, 'execute'); G.link(sb1, 'then', sb2, 'execute')
# then_1: bogged attrition
X = 900; Y1 = Y + 1300
spd = b.speed(X, Y1 + 400)
bog = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', spd, None, X + 400, Y1 + 400, db='250.0'),
           b.icmp('GreaterEqual_IntInt', g('NearCount', INTV('0'), X + 300, Y1 + 550), None, X + 500, Y1 + 550, db='4'), X + 700, Y1 + 450)
sbog = b.set('Bogged', BOOL, bog, X, Y1); G.link(seq, 'then_1', sbog, 'execute')
bb = b.branch(g('Bogged', BOOL, X + 250, Y1 + 250), X + 300, Y1, tag='IfBogged'); G.link(sbog, 'then', bb, 'execute')
dhp = b.set('HP', REAL('v', '0.0'), b.sub(g('HP', REAL('v', '0.0'), X + 500, Y1 + 250), b.mul(g('BogDPS', REAL('v', '30.0'), X + 500, Y1 + 400), None, X + 700, Y1 + 400, db='0.2'),
            X + 900, Y1 + 300), X + 650, Y1)
G.link(bb, 'then', dhp, 'execute')
bdie = b.branch(b.dcmp('LessEqual_DoubleDouble', g('HP', REAL('v', '0.0'), X + 900, Y1 + 500), None, X + 1100, Y1 + 500, db='0.0'), X + 1000, Y1, tag='IfHPZero')
G.link(dhp, 'then', bdie, 'execute')
cdie = b.call_self('Die', [], X + 1300, Y1 - 100, CAVC, tag='CallDie')
G.link(bdie, 'then', cdie, 'execute')

# rally point: 8 m behind the hero, knights 3 m apart side by side
def rally(x, y):
    back = b.vmul(b.actvec('GetActorForwardVector', heroh, x, y + 100), None, x + 200, y + 100, df='-800.0')
    side = b.vmul(b.actvec('GetActorRightVector', heroh, x, y + 250),
                  b.mul(b.sub(b.i2d(g('Slot', INTV('0'), x - 200, y + 400), x, y + 400), None, x + 200, y + 400, db='1.5'), None, x + 400, y + 400, db='300.0'), x + 600, y + 250)
    return b.vadd(b.vadd(b.loc(heroh, x + 400, y), back, x + 650, y + 50), side, x + 850, y + 150)

# then_2: the state machine
X = 900; Y2 = Y + 2600
b0 = b.branch(b.icmp('EqualEqual_IntInt', STATE(X - 200, Y2 + 250), None, X, Y2 + 250, db='0'), X, Y2, tag='IfFollow'); G.link(seq, 'then_2', b0, 'execute')
# -- 0 Follow: charge when a target is in range and the rest is over, else ride to the rally point
ready = b.b2('BooleanAND', b.valid(g('BestZ', OBJV(ZOMBIE), X + 200, Y2 + 400), X + 400, Y2 + 400),
             b.dcmp('Greater_DoubleDouble', now(X + 200, Y2 + 550), g('NextCharge', REAL('v', '0.0'), X + 200, Y2 + 650), X + 400, Y2 + 600), X + 600, Y2 + 500)
bgo = b.branch(ready, X + 300, Y2 - 400, tag='IfCharge'); G.link(b0, 'then', bgo, 'execute')
cdir = b.norm2d(b.vsub(b.loc(g('BestZ', OBJV(ZOMBIE), X + 500, Y2 - 900), X + 700, Y2 - 900), b.myloc(X + 700, Y2 - 800), X + 900, Y2 - 850), X + 1100, Y2 - 850)
c1 = b.set('Target', OBJV(ZOMBIE), g('BestZ', OBJV(ZOMBIE), X + 600, Y2 - 600), X + 600, Y2 - 500)
c2 = b.set('ChargeDir', VECT, cdir, X + 850, Y2 - 500); c3 = b.set('StateT', REAL('v', '0.0'), now(X + 900, Y2 - 300), X + 1100, Y2 - 500)
c4 = b.aclear('Hit', OBJV(ZOMBIE), X + 1350, Y2 - 500); c5 = b.set('State', INTV('1'), None, X + 1600, Y2 - 500)
for n in (c5,):
    for nm, c, props, pins, *_ in G.nodes:
        if nm == n:
            for p in pins:
                if p['name'] == 'State': p['default'] = '1'
G.link(bgo, 'then', c1, 'execute'); b.chain(c1, c2, c3, c4, c5)
fdist = b.dist2d(b.myloc(X + 600, Y2 + 200), rally(X + 400, Y2 + 900), X + 1300, Y2 + 300)
fspd = b.self_(None, None, b.dcmp('Greater_DoubleDouble', fdist, None, X + 1500, Y2 + 300, db='1500.0'), X + 1700, Y2 + 250, da='800.0', db='450.0')
fs = b.setspeed(fspd, X + 700, Y2 - 100); G.link(bgo, 'else', fs, 'execute')
fm = b.move_to(rally(X + 700, Y2 + 1300), X + 1000, Y2 - 100); G.link(fs, 'then', fm, 'execute')
# -- 1 Charge
X = 3200
b1 = b.branch(b.icmp('EqualEqual_IntInt', STATE(X - 200, Y2 + 250), None, X, Y2 + 250, db='1'), X, Y2, tag='IfChargeSt'); G.link(b0, 'else', b1, 'execute')
tch = b.sub(now(X, Y2 + 600), g('StateT', REAL('v', '0.0'), X, Y2 + 700), X + 200, Y2 + 650)
ramp = b.math('FMin', [(D('A', default='0.0'), b.add(b.mul(tch, None, X + 400, Y2 + 650, db='250.0'), None, X + 600, Y2 + 650, db='450.0')),
                        (D('B', default='0.0'), g('ChargeSpeed', REAL('v', '950.0'), X + 600, Y2 + 800))], D('ReturnValue', out=True), X + 800, Y2 + 700)
cs = b.setspeed(ramp, X + 300, Y2 - 300); G.link(b1, 'then', cs, 'execute')
tval = b.valid(g('Target', OBJV(ZOMBIE), X + 400, Y2 - 700), X + 600, Y2 - 700)
aimT = b.loc(g('Target', OBJV(ZOMBIE), X + 600, Y2 - 900), X + 800, Y2 - 900)
aimS = b.vadd(b.myloc(X + 600, Y2 - 1100), b.vmul(g('ChargeDir', VECT, X + 600, Y2 - 1000), None, X + 800, Y2 - 1000, df='800.0'), X + 1000, Y2 - 1050)
aim = b.selvec(aimT, aimS, tval, X + 1200, Y2 - 900)
goal = b.vadd(aim, b.vmul(g('ChargeDir', VECT, X + 1200, Y2 - 700), None, X + 1400, Y2 - 700, df='400.0'), X + 1600, Y2 - 800)   # aim past the target: never brake
cm = b.move_to(goal, X + 600, Y2 - 300); G.link(cs, 'then', cm, 'execute')
fwd = b.actvec('GetActorForwardVector', None, X + 1200, Y2 + 200)
tob = b.norm2d(b.vsub(b.loc(g('BestZ', OBJV(ZOMBIE), X + 1000, Y2 + 350), X + 1200, Y2 + 350), b.myloc(X + 1200, Y2 + 450), X + 1400, Y2 + 400), X + 1600, Y2 + 400)
hit = b.b2('BooleanAND', b.b2('BooleanAND', b.valid(g('BestZ', OBJV(ZOMBIE), X + 1400, Y2 + 550), X + 1600, Y2 + 550),
                              b.dcmp('Less_DoubleDouble', g('Best', REAL('v', '0.0'), X + 1600, Y2 + 650), None, X + 1800, Y2 + 650, db='280.0'), X + 2000, Y2 + 600),
           b.dcmp('Greater_DoubleDouble', b.dot(fwd, tob, X + 1800, Y2 + 300), None, X + 2000, Y2 + 300, db='0.5'), X + 2200, Y2 + 450)
bimp = b.branch(hit, X + 1300, Y2 - 300, tag='IfImpact'); G.link(cm, 'then', bimp, 'execute')
cimp = b.call_self('Impact', [], X + 1600, Y2 - 500, CAVC, tag='CallImpact'); G.link(bimp, 'then', cimp, 'execute')
bgive = b.branch(b.dcmp('Greater_DoubleDouble', tch, None, X + 1800, Y2 - 100, db='6.0'), X + 1600, Y2 - 250, tag='IfGiveUp'); G.link(bimp, 'else', bgive, 'execute')
gw1 = b.set('State', INTV('3'), None, X + 1900, Y2 - 250); gw2 = b.set('StateT', REAL('v', '0.0'), now(X + 2000, Y2 - 50), X + 2150, Y2 - 250)
G.link(bgive, 'then', gw1, 'execute'); G.link(gw1, 'then', gw2, 'execute')
# -- 2 Ride through
X = 6200
b2_ = b.branch(b.icmp('EqualEqual_IntInt', STATE(X - 200, Y2 + 250), None, X, Y2 + 250, db='2'), X, Y2, tag='IfRide'); G.link(b1, 'else', b2_, 'execute')
rs = b.setspeed(None, X + 300, Y2 - 300, d='800.0'); G.link(b2_, 'then', rs, 'execute')
rm = b.move_to(g('RideEnd', VECT, X + 400, Y2 - 100), X + 600, Y2 - 300); G.link(rs, 'then', rm, 'execute')
fe2 = b.foreach(ZOMBIE, X + 1200, Y2 - 300); G.link(rm, 'then', fe2, 'Exec'); b.wire(g('Zs', arr(OBJV(ZOMBIE)), X + 1000, Y2 - 100), fe2, 'Array')
e2 = (fe2, 'Array Element')
tr = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 1200, Y2 + 100), b.loc(e2, X + 1200, Y2 + 200), X + 1400, Y2 + 150), None, X + 1600, Y2 + 150, db='200.0'),
          b.bnot(b.acontains(g('Hit', arr(OBJV(ZOMBIE)), X + 1400, Y2 + 300), e2, X + 1600, Y2 + 300), X + 1800, Y2 + 300), X + 2000, Y2 + 200)
btr = b.branch(tr, X + 1500, Y2 - 300, tag='IfTrample'); G.link(fe2, 'LoopBody', btr, 'execute')
ah = b.aadd('Hit', OBJV(ZOMBIE), e2, X + 1800, Y2 - 500); G.link(btr, 'then', ah, 'execute')
td = b.apply_damage(e2, b.mul(g('TrampleDmg', REAL('v', '35.0'), X + 1900, Y2 - 200), None, X + 2100, Y2 - 200, db='0.5'), X + 2100, Y2 - 500)
G.link(ah, 'then', td, 'execute')
tl = b.launch(e2, b.vadd(b.vmul(g('ChargeDir', VECT, X + 2200, Y2 - 200), None, X + 2400, Y2 - 200, df='450.0'), None, X + 2600, Y2 - 200, db='0, 0, 250'), X + 2400, Y2 - 500)
G.link(td, 'then', tl, 'execute')
rdone = b.b2('BooleanOR', b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 1200, Y2 + 600), g('RideEnd', VECT, X + 1200, Y2 + 700), X + 1400, Y2 + 650), None, X + 1600, Y2 + 650, db='250.0'),
            b.dcmp('Greater_DoubleDouble', b.sub(now(X + 1200, Y2 + 850), g('StateT', REAL('v', '0.0'), X + 1200, Y2 + 950), X + 1400, Y2 + 900), None, X + 1600, Y2 + 900, db='3.5'),
            X + 1800, Y2 + 750)
brd = b.branch(rdone, X + 1700, Y2 + 400, tag='IfRideDone'); G.link(fe2, 'Completed', brd, 'execute')
rw1 = b.set('State', INTV('3'), None, X + 2000, Y2 + 400); rw2 = b.set('StateT', REAL('v', '0.0'), now(X + 2100, Y2 + 600), X + 2250, Y2 + 400)
G.link(brd, 'then', rw1, 'execute'); G.link(rw1, 'then', rw2, 'execute')
# -- 3 Wheel and re-form
X = 9200
b3 = b.branch(b.icmp('EqualEqual_IntInt', STATE(X - 200, Y2 + 250), None, X, Y2 + 250, db='3'), X, Y2, tag='IfWheel'); G.link(b2_, 'else', b3, 'execute')
ws = b.setspeed(None, X + 300, Y2 - 300, d='650.0'); G.link(b3, 'then', ws, 'execute')
wm = b.move_to(rally(X + 300, Y2 + 900), X + 600, Y2 - 300); G.link(ws, 'then', wm, 'execute')
there = b.b2('BooleanOR', b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 900, Y2 + 300), rally(X + 600, Y2 + 1400), X + 1500, Y2 + 350), None, X + 1700, Y2 + 350, db='400.0'),
             b.dcmp('Greater_DoubleDouble', b.sub(now(X + 1500, Y2 + 500), g('StateT', REAL('v', '0.0'), X + 1500, Y2 + 600), X + 1700, Y2 + 550), None, X + 1900, Y2 + 550, db='7.0'),
             X + 2100, Y2 + 450)
bth = b.branch(there, X + 1200, Y2 - 300, tag='IfReformed'); G.link(wm, 'then', bth, 'execute')
w1 = b.set('State', INTV('0'), None, X + 1500, Y2 - 500)
w2 = b.set('NextCharge', REAL('v', '0.0'), b.add(now(X + 1600, Y2 - 300), None, X + 1800, Y2 - 300, db='3.0'), X + 1750, Y2 - 500)
w3 = b.set('LanceBroken', BOOL, None, X + 2000, Y2 - 500)
w4 = b.setvis(b.comp('Lance', X + 2100, Y2 - 300), True, X + 2250, Y2 - 500)
G.link(bth, 'then', w1, 'execute'); b.chain(w1, w2, w3, w4)

# then_3: animation from speed (Idle / Walk / Trot / Gallop), play rate within 0.8 - 1.2
X = 900; Y3 = Y + 4600
sp3 = b.speed(X, Y3 + 500)
idx = b.math('FTrunc', [(D('A', default='0.0'), b.add(b.add(b.self_(None, None, b.dcmp('Greater_DoubleDouble', sp3, None, X + 400, Y3 + 500, db='40.0'), X + 600, Y3 + 450, da='1.0'),
                                                                  b.self_(None, None, b.dcmp('Greater_DoubleDouble', sp3, None, X + 400, Y3 + 650, db='260.0'), X + 600, Y3 + 600, da='1.0'), X + 800, Y3 + 500),
                                                            b.self_(None, None, b.dcmp('Greater_DoubleDouble', sp3, None, X + 400, Y3 + 800, db='520.0'), X + 600, Y3 + 750, da='1.0'), X + 1000, Y3 + 600))],
             it('ReturnValue', out=True, default='0'), X + 1200, Y3 + 600)
bch = b.branch(b.icmp('NotEqual_IntInt', idx, g('Anim', INTV('-1'), X + 1200, Y3 + 750), X + 1400, Y3 + 700), X + 300, Y3, tag='IfNewAnim')
G.link(seq, 'then_3', bch, 'execute')
sa = b.set('Anim', INTV('-1'), idx, X + 600, Y3 - 200); G.link(bch, 'then', sa, 'execute')
prev = sa; XA = X + 900
mrg = b.seq('AnimPicked', 1, X + 3200, Y3)
for k, anim in enumerate(('A_Destrier_Idle', 'A_Destrier_Walk', 'A_Destrier_Trot', 'A_Destrier_Gallop')):
    bk = b.branch(b.icmp('EqualEqual_IntInt', g('Anim', INTV('-1'), XA - 100, Y3 + 200 + 150 * k), None, XA + 100, Y3 + 200 + 150 * k, db=str(k)), XA, Y3 - 200, tag='IfAnim%d' % k)
    G.link(prev, 'then' if k == 0 else 'else', bk, 'execute')
    pl = b.play(anim, True, XA + 300, Y3 - 500 - 150 * k); G.link(bk, 'then', pl, 'execute'); G.link(pl, 'then', mrg, 'execute')
    prev = bk; XA += 550
G.link(prev, 'else', mrg, 'execute'); G.link(bch, 'else', mrg, 'execute')
ref = b.self_(b.self_(None, None, b.icmp('EqualEqual_IntInt', g('Anim', INTV('-1'), X + 3300, Y3 + 400), None, X + 3500, Y3 + 400, db='1'), X + 3700, Y3 + 350, da='170.0', db='350.0'),
              None, b.icmp('LessEqual_IntInt', g('Anim', INTV('-1'), X + 3700, Y3 + 550), None, X + 3900, Y3 + 550, db='2'), X + 4100, Y3 + 450, db='750.0')
rate = b.self_(b.clamp(b.d2('Divide_DoubleDouble', sp3, ref, X + 4300, Y3 + 450), '0.8', '1.2', X + 4500, Y3 + 450), None,
               b.icmp('Greater_IntInt', g('Anim', INTV('-1'), X + 4300, Y3 + 650), None, X + 4500, Y3 + 650, db='0'), X + 4700, Y3 + 500, db='1.0')
pr = b.call(SKEL, 'SetPlayRate', [fl('Rate', default='1.0')], X + 3500, Y3, target=b.mesh(X + 3300, Y3 + 200), tag='PlayRate')
b.wire(rate, pr, 'Rate'); G.link(mrg, 'then_0', pr, 'execute')

# ---- Impact: lance hit on BestZ, trample cone, lance may break, ride through
Y = 7400
b.event('Impact', [], 0, Y)
spI = b.speed(100, Y + 600)
fac = b.clamp(b.d2('Divide_DoubleDouble', spI, g('ChargeSpeed', REAL('v', '950.0'), 200, Y + 750), 400, Y + 650), '0.35', '1.2', 600, Y + 650)
base = b.self_(b.mul(g('TrampleDmg', REAL('v', '35.0'), 400, Y + 850), None, 600, Y + 850, db='2.0'), g('LanceDmg', REAL('v', '140.0'), 600, Y + 950),
               g('LanceBroken', BOOL, 600, Y + 1050), 800, Y + 900)
dmg = b.mul(base, fac, 1000, Y + 750)
best = lambda x, y: g('BestZ', OBJV(ZOMBIE), x, y)
dI = b.apply_damage(best(400, Y + 300), dmg, 600, Y); G.link('Impact', 'then', dI, 'execute')
kv = b.vadd(b.vmul(g('ChargeDir', VECT, 800, Y + 400), None, 1000, Y + 400, df='900.0'), None, 1200, Y + 400, db='0, 0, 350')
lI = b.launch(best(1000, Y + 250), kv, 1000, Y); G.link(dI, 'then', lI, 'execute')
snd = b.lib(GS, 'PlaySoundAtLocation', [WC(), dict(ob('Sound', SOUND), dobj=SND_HIT), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
                                        fl('VolumeMultiplier', default='1.0'), fl('PitchMultiplier', default='0.8')], 1400, Y, tag='HitSound')
b.wire(b.myloc(1200, Y + 250), snd, 'Location'); G.link(lI, 'then', snd, 'execute')
ah0 = b.aadd('Hit', OBJV(ZOMBIE), best(1500, Y + 400), 1700, Y); G.link(snd, 'then', ah0, 'execute')
brk = b.b2('BooleanAND', b.bnot(g('LanceBroken', BOOL, 1700, Y + 450), 1900, Y + 450),
           b.math('RandomBoolWithWeight', [(fl('Weight', default='0.3'), None)], bo('ReturnValue', out=True, default='false'), 1900, Y + 550), 2100, Y + 500)
bbr = b.branch(brk, 2000, Y, tag='IfLanceBreaks'); G.link(ah0, 'then', bbr, 'execute')
lb1 = b.set('LanceBroken', bo('v', default='true'), None, 2300, Y - 200)
for nm, c, props, pins, *_ in G.nodes:
    if nm == lb1:
        for p in pins:
            if p['name'] == 'LanceBroken': p['default'] = 'true'
lb2 = b.setvis(b.comp('Lance', 2400, Y), False, 2550, Y - 200)
G.link(bbr, 'then', lb1, 'execute'); G.link(lb1, 'then', lb2, 'execute')
mbr = b.seq('BreakDone', 1, 2850, Y); G.link(lb2, 'then', mbr, 'execute'); G.link(bbr, 'else', mbr, 'execute')
fe3 = b.foreach(ZOMBIE, 3100, Y); G.link(mbr, 'then_0', fe3, 'Exec'); b.wire(g('Zs', arr(OBJV(ZOMBIE)), 2900, Y + 200), fe3, 'Array')
e3 = (fe3, 'Array Element')
fwdI = b.actvec('GetActorForwardVector', None, 3100, Y + 500)
toE = b.norm2d(b.vsub(b.loc(e3, 3100, Y + 650), b.myloc(3100, Y + 750), 3300, Y + 700), 3500, Y + 700)
cone = b.b2('BooleanAND', b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(3300, Y + 900), b.loc(e3, 3300, Y + 1000), 3500, Y + 950), None, 3700, Y + 950, db='250.0'),
                               b.dcmp('Greater_DoubleDouble', b.dot(fwdI, toE, 3700, Y + 600), None, 3900, Y + 600, db='0.3'), 4100, Y + 750),
            b.bnot(b.acontains(g('Hit', arr(OBJV(ZOMBIE)), 3700, Y + 1100), e3, 3900, Y + 1100), 4100, Y + 1100), 4300, Y + 900)
bco = b.branch(cone, 3400, Y, tag='IfInCone'); G.link(fe3, 'LoopBody', bco, 'execute')
ah3 = b.aadd('Hit', OBJV(ZOMBIE), e3, 3700, Y - 200); G.link(bco, 'then', ah3, 'execute')
d3 = b.apply_damage(e3, g('TrampleDmg', REAL('v', '35.0'), 3900, Y + 100), 4000, Y - 200); G.link(ah3, 'then', d3, 'execute')
l3 = b.launch(e3, b.vadd(b.vmul(g('ChargeDir', VECT, 4100, Y + 100), None, 4300, Y + 100, df='600.0'), None, 4500, Y + 100, db='0, 0, 300'), 4400, Y - 200)
G.link(d3, 'then', l3, 'execute')
r1 = b.set('State', INTV('2'), None, 3500, Y + 1400); G.link(fe3, 'Completed', r1, 'execute')
r2 = b.set('StateT', REAL('v', '0.0'), now(3600, Y + 1600), 3750, Y + 1400)
r3 = b.set('RideEnd', VECT, b.vadd(b.myloc(3800, Y + 1600), b.vmul(g('ChargeDir', VECT, 3800, Y + 1700), None, 4000, Y + 1700, df='1400.0'), 4200, Y + 1650), 4000, Y + 1400)
b.chain(r1, r2, r3)

# ---- damage and death
Y = 9800
event_override(G, 'AnyDamage', ACT, 'ReceiveAnyDamage', [fl('Damage', default='0.0'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CTRL), ob('DamageCauser', ACT)], 0, Y)
dh = b.set('HP', REAL('v', '0.0'), b.sub(g('HP', REAL('v', '0.0'), 200, Y + 300), ('AnyDamage', 'Damage'), 400, Y + 300), 300, Y); G.link('AnyDamage', 'then', dh, 'execute')
bd2 = b.branch(b.b2('BooleanAND', b.dcmp('LessEqual_DoubleDouble', g('HP', REAL('v', '0.0'), 500, Y + 300), None, 700, Y + 300, db='0.0'),
                    b.icmp('NotEqual_IntInt', STATE(500, Y + 450), None, 700, Y + 450, db='9'), 900, Y + 350), 600, Y, tag='IfKilled')
G.link(dh, 'then', bd2, 'execute')
cd2 = b.call_self('Die', [], 900, Y - 100, CAVC, tag='CallDie2'); G.link(bd2, 'then', cd2, 'execute')
Y = 10600
b.event('Die', [], 0, Y)
bonce = b.branch(b.icmp('NotEqual_IntInt', STATE(100, Y + 250), None, 300, Y + 250, db='9'), 300, Y, tag='IfNotDead'); G.link('Die', 'then', bonce, 'execute')
k1 = b.set('State', INTV('9'), None, 600, Y)
for nm, c, props, pins, *_ in G.nodes:
    if nm == k1:
        for p in pins:
            if p['name'] == 'State': p['default'] = '9'
G.link(bonce, 'then', k1, 'execute')
k2 = b.call(CTRL, 'StopMovement', [], 850, Y, target=b.ctl(650, Y + 200), tag='Stop'); G.link(k1, 'then', k2, 'execute')
k3 = b.play('A_Destrier_Death', False, 1150, Y); G.link(k2, 'then', k3, 'execute')
k4 = b.setvis(b.comp('Lance', 1350, Y + 200), False, 1500, Y); G.link(k3, 'then', k4, 'execute')
caps = b.getm('CapsuleComponent', CHARC, OBJV(CAPS), b.self_node(1600, Y + 300), 1750, Y + 300)
k5 = b.call(PRIM, 'SetCollisionEnabled', [{'name': 'NewType', 'cat': 'byte', 'obj': ENUM('ECollisionEnabled'), 'default': 'NoCollision'}], 1850, Y, target=caps, tag='NoColl')
G.link(k4, 'then', k5, 'execute')
k6 = b.call_self('SetLifeSpan', [fl('InLifespan', default='12.0')], 2150, Y, ACT, tag='Gone'); G.link(k5, 'then', k6, 'execute')
nk, _ = b.notice('A knight has fallen.', 2450, Y); G.link(k6, 'then', nk, 'execute')
write(G, 'BP_Cavalry_graph.txt')
VARS_K = [('State', 'int', '0', '0 follow, 1 charge, 2 ride through, 3 wheel, 9 dead'), ('Slot', 'int', '0', 'place in the line (0..3)'),
          ('HP', 'real', '600.0', 'hit points (horse + rider)'), ('MaxHP', 'real', '600.0', ''), ('Anim', 'int', '-1', 'clip playing: 0 idle, 1 walk, 2 trot, 3 gallop'),
          ('Target', 'zobj', '', 'charge target (BP_Zombie)'), ('BestZ', 'zobj', '', 'scratch: nearest live zombie'), ('Best', 'real', '0.0', 'scratch: its distance'),
          ('NearCount', 'int', '0', 'zombies within 3 m'), ('Zs', 'zarr', '', 'zombies this think (BP_Zombie array)'), ('Hit', 'zarr', '', 'already hit this charge'),
          ('ChargeDir', 'vec', '', 'locked charge line'), ('RideEnd', 'vec', '', 'end of the ride-through'), ('StateT', 'real', '0.0', 'time the state began'),
          ('NextCharge', 'real', '0.0', 'rest until'), ('LanceBroken', 'bool', 'false', ''), ('Bogged', 'bool', 'false', 'slow in a crowd: losing HP'),
          ('RiderDrop', 'real', '-92.0', 'cm: rider pelvis into the saddle (tune by eye)'), ('Acquire', 'real', '3500.0', 'cm: charge range'),
          ('ChargeSpeed', 'real', '950.0', 'cm/s at full gallop'), ('LanceDmg', 'real', '140.0', ''), ('TrampleDmg', 'real', '35.0', ''), ('BogDPS', 'real', '30.0', '')]

# ================================================================================================= BPC_Cavalry
G = Graph(); b = BC(G, 'cc')
g = b.get
event_override(G, 'BP', COMP, 'ReceiveBeginPlay', [], 0, 0)
t1 = b.timer_ev('CavPoll', '1.0', 300, 0); t2 = b.timer_ev('CavKeys', '0.05', 600, 0)
G.link('BP', 'then', t1, 'execute'); G.link(t1, 'then', t2, 'execute')
Y = 800
b.event('CavPoll', [], 0, Y)
gk = b.getall(P_CAV, CAVC, 300, Y); G.link('CavPoll', 'then', gk, 'execute')
sc = b.set('Count', INT, b.arrlen((gk, 'OutActors'), 500, Y + 300), 650, Y); G.link(gk, 'then', sc, 'execute')
# shop = the stables (tag Stables) when placed, else the barracks NPC
gt = b.lib(GS, 'GetAllActorsWithTag', [WC(), NAME_('Tag', 'Stables'), arr(ob('OutActors', ACT, out=True))], 900, Y, tag='AllStables'); G.link(sc, 'then', gt, 'execute')
fn = b.actor_of(P_NPC, NPCC, 1150, Y); G.link(gt, 'then', fn, 'execute')
hasst = b.icmp('Greater_IntInt', b.arrlen((gt, 'OutActors'), 1150, Y + 300), None, 1350, Y + 300, db='0')
shop_st = b.item((gt, 'OutActors'), ob('v', ACT), None, 1350, Y + 450)
ss1 = b.set('Shop', OBJV(ACT), (fn, 'ReturnValue'), 1450, Y); G.link(fn, 'then', ss1, 'execute')
bst = b.branch(hasst, 1700, Y, tag='IfStables'); G.link(ss1, 'then', bst, 'execute')
ss2 = b.set('Shop', OBJV(ACT), shop_st, 1950, Y - 200); G.link(bst, 'then', ss2, 'execute')
mshop = b.seq('ShopPicked', 1, 2200, Y); G.link(ss2, 'then', mshop, 'execute'); G.link(bst, 'else', mshop, 'execute')
shop = lambda x, y: g('Shop', OBJV(ACT), x, y)
near = b.b2('BooleanAND', b.valid(shop(2300, Y + 300), 2500, Y + 300),
            b.dcmp('Less_DoubleDouble', b.dist2d(b.loc(b.owner(2300, Y + 450), 2500, Y + 450), b.loc(shop(2300, Y + 550), 2500, Y + 550), 2700, Y + 500), None, 2900, Y + 500, db='600.0'),
            3100, Y + 400)
bf = b.branch(b.b2('BooleanAND', near, b.bnot(g('NearShop', BOOL, 3100, Y + 550), 3300, Y + 550), 3500, Y + 500), 2500, Y, tag='IfOffer')
G.link(mshop, 'then_0', bf, 'execute')
offer = b.concat(b.concat(b.concat(None, b.istr(g('Count', INT, 2600, Y - 500), 2800, Y - 500), 3000, Y - 550,
                                   da='[L] Raise a knight on a barded destrier: 400 gold. Heavy cavalry charges zombies with the lance.  ('), None, 3200, Y - 550, db='/'),
                 b.istr(g('MaxKnights', it('v', default='4'), 3200, Y - 400), 3400, Y - 400), 3600, Y - 500)
offer = b.concat(offer, None, 3800, Y - 500, db=')')
nc, pn = b.notice('', 2800, Y - 200, text_src=offer); G.link(bf, 'then', nc, 'execute')
sns = b.set('NearShop', BOOL, near, 3300, Y)
for src, pin in ((bf, 'else'), (pn, 'then'), (nc, 'CastFailed')): G.link(src, pin, sns, 'execute')
Y = 1900
b.event('CavKeys', [], 0, Y)
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='L'), bo('ReturnValue', out=True, default='false')], 200, Y + 300, target=b.pc(0, Y + 300), pure=True, const=True, tag='KeyL')
press = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('LWas', BOOL, 300, Y + 450), 500, Y + 450), 700, Y + 400), g('NearShop', BOOL, 700, Y + 550), 900, Y + 450)
slw = b.set('LWas', BOOL, (down, 'ReturnValue'), 300, Y); G.link('CavKeys', 'then', slw, 'execute')
bp_ = b.branch(press, 600, Y, tag='IfL'); G.link(slw, 'then', bp_, 'execute')
bfull = b.branch(b.icmp('GreaterEqual_IntInt', g('Count', INT, 700, Y + 300), g('MaxKnights', it('v', default='4'), 700, Y + 400), 900, Y + 350), 800, Y, tag='IfFull')
G.link(bp_, 'then', bfull, 'execute')
nfu, _ = b.notice('All four knights of your lance are already mounted.', 1100, Y - 300); G.link(bfull, 'then', nfu, 'execute')
zc, zh = b.hud_cast(ZHUDC, 'BP Zombie HUD', 1100, Y); G.link(bfull, 'else', zc, 'execute')
szh = b.set('ZHud', OBJV(ZHUDC), zh, 1250, Y - 150); G.link(zc, 'then', szh, 'execute')      # one consumer per cast (fix_impure)
zhv = lambda x, y: g('ZHud', OBJV(ZHUDC), x, y)
gold = lambda x, y: b.getm('Gold', ZHUDC, INT, zhv(x - 150, y), x, y)
price = lambda x, y: g('Price', it('v', default='400'), x, y)
bg = b.branch(b.icmp('GreaterEqual_IntInt', gold(1300, Y + 300), price(1300, Y + 400), 1500, Y + 350), 1400, Y, tag='IfGold'); G.link(szh, 'then', bg, 'execute')
nng, _ = b.notice('Not enough gold: a knight and his destrier cost 400.', 1700, Y + 300); G.link(bg, 'else', nng, 'execute')
pay = b.setm('Gold', ZHUDC, INT, b.i2('Subtract_IntInt', gold(1600, Y - 100), price(1600, Y), 1800, Y - 50), zhv(1550, Y - 200), 1700, Y - 300); G.link(bg, 'then', pay, 'execute')
spos = b.v2('Add_VectorVector', b.loc(g('Shop', OBJV(ACT), 1900, Y), 2100, Y), None, 2300, Y, db='300.000000,300.000000,120.000000')
sp = spawn(b, P_CAV, CAVC, transform(b, spos, 2500, Y), 2300, Y - 300); G.link(pay, 'then', sp, 'execute')
nok, _ = b.notice('A knight rides out to join you (-400 gold).', 2700, Y - 300); G.link(sp, 'then', nok, 'execute')
write(G, 'BPC_Cavalry_graph.txt')
VARS_C = [('Count', 'int', '0', 'knights alive (counted every second)'), ('MaxKnights', 'int', '4', 'limit'), ('Price', 'int', '400', 'gold per knight'),
          ('NearShop', 'bool', 'false', 'hero at the stables / barracks (offer shown)'), ('LWas', 'bool', 'false', 'L held last check'),
          ('Shop', 'obj:Actor', '', 'the stables (tag Stables) or the barracks NPC'), ('ZHud', 'hudobj', '', 'BP_ZombieHUD (gold)')]


HUDPATH = "/Script/Engine.BlueprintGeneratedClass'/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD.BP_ZombieHUD_C'"
ZPATH = "/Script/Engine.BlueprintGeneratedClass'/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C'"
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('int', 'bool'): return 'PinCategory="%s"' % kind
    if kind == 'vec': return 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
    if kind == 'hudobj': return 'PinCategory="object",PinSubCategoryObject="%s"' % HUDPATH
    if kind == 'zobj': return 'PinCategory="object",PinSubCategoryObject="%s"' % ZPATH
    if kind == 'zarr': return 'PinCategory="object",PinSubCategoryObject="%s",ContainerType=Array' % ZPATH
    if kind.startswith('arr:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'",ContainerType=Array' % kind[4:]
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda bp, n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'cavalry404/%s/%s' % (bp, n)).hex.upper(), vt(k), n, d)
out = ['# #404 Heavy cavalry - paste one line at a time on the VARIABLES header of My Blueprint, then Compile', '', '# ---- BP_Cavalry']
out += [bpv('BP_Cavalry', *v[:3]) for v in VARS_K] + ['', '# ---- BPC_Cavalry'] + [bpv('BPC_Cavalry', *v[:3]) for v in VARS_C]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #404 variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bp, vs in (('BP_Cavalry', VARS_K), ('BPC_Cavalry', VARS_C)):
        for n, _k, d, m in vs: f.write('| %s | %s | %s | %s |\n' % (bp, n, d or '-', m))
print('BPVar lines: %d + %d' % (len(VARS_K), len(VARS_C)))
