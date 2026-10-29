# #96 Obsidian set: generates the two Blueprint pastes (laptop2, 2026-10-29). Run with any Python 3:
#   python gen96.py      ->  BPC_ObsidianSet_graph.txt (EventGraph of the new component)
#                            Hero_ObsidianDamage_graph.txt (nodes for BP_ThirdPersonCharacter's ReceiveAnyDamage)
# Uses the Master's node kit (tools/master/t81/kit.py), the same one #81 was built with.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'master', 't81'))
from kit import *

ACT, COMP, CHAR, OBJ = CLS('Actor'), CLS('ActorComponent'), CLS('Character'), '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"'
GS, MATL = CLS('GameplayStatics'), CLS('KismetMaterialLibrary')
MPC_CLS = CLS('MaterialParameterCollection')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
ZOMBIE = BPC('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', 'BP_Zombie')
SETC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet', 'BPC_ObsidianSet')
LC, VEC = STRUCT('LinearColor'), STRUCT('Vector')

def D(name, out=False, default=None): return fl(name, out=out, default=default, sub='double')
WC = lambda: ob('WorldContextObject', OBJ, hidden=True)

class B:
    """small builder on top of kit.Graph: math nodes return (node, 'ReturnValue') handles."""
    def __init__(s, G, prefix): s.G, s.p, s.n = G, prefix, 0
    def name(s, tag): s.n += 1; return '%s%s%d' % (s.p, tag, s.n)
    def wire(s, src, node, pin):
        if src is None: return
        if isinstance(src, tuple): s.G.link(src[0], src[1], node, pin)
    def math(s, member, ins, outpin, x, y):
        """ins: list of (pin dict, source handle or None)."""
        n = s.name(member[:6]); mathfn(s.G, n, member, [p for p, _ in ins] + [outpin], x, y)
        for p, src in ins: s.wire(src, n, p['name'])
        return (n, outpin['name'])
    # ints
    def i2(s, member, a, b, x, y, da='0', db='0'):
        return s.math(member, [(it('A', default=da), a), (it('B', default=db), b)], it('ReturnValue', out=True), x, y)
    def icmp(s, member, a, b, x, y, da='0', db='0'):
        return s.math(member, [(it('A', default=da), a), (it('B', default=db), b)], bo('ReturnValue', out=True), x, y)
    def d2(s, member, a, b, x, y, da='0.0', db='0.0'):
        return s.math(member, [(D('A', default=da), a), (D('B', default=db), b)], D('ReturnValue', out=True), x, y)
    def dcmp(s, member, a, b, x, y, da='0.0', db='0.0'):
        return s.math(member, [(D('A', default=da), a), (D('B', default=db), b)], bo('ReturnValue', out=True), x, y)
    def b2(s, member, a, b, x, y):
        return s.math(member, [(bo('A', default='false'), a), (bo('B', default='false'), b)], bo('ReturnValue', out=True), x, y)
    def bnot(s, a, x, y): return s.math('Not_PreBool', [(bo('A', default='false'), a)], bo('ReturnValue', out=True), x, y)
    def inot(s, a, x, y): return s.math('Not_Int', [(it('A', default='0'), a)], it('ReturnValue', out=True), x, y)
    def i2d(s, a, x, y): return s.math('Conv_IntToDouble', [(it('InInt', default='0'), a)], D('ReturnValue', out=True), x, y)
    def b2i(s, a, x, y): return s.math('Conv_BoolToInt', [(bo('InBool', default='false'), a)], it('ReturnValue', out=True), x, y)
    def b2d(s, a, x, y): return s.math('Conv_BoolToDouble', [(bo('InBool', default='false'), a)], D('ReturnValue', out=True), x, y)
    def rnd(s, a, x, y): return s.math('Round', [(D('A', default='0.0'), a)], it('ReturnValue', out=True), x, y)
    def pow(s, base, e, x, y, db='2.0'):
        return s.math('MultiplyMultiply_FloatFloat', [(D('Base', default=db), base), (D('Exp', default='0.0'), e)], D('ReturnValue', out=True), x, y)
    def seli(s, a, b, pick, x, y, da='0', db='0'):
        return s.math('SelectInt', [(it('A', default=da), a), (it('B', default=db), b), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)
    def self_(s, a, b, pick, x, y, da='0.0', db='0.0'):
        return s.math('SelectFloat', [(D('A', default=da), a), (D('B', default=db), b), (bo('bPickA', default='false'), pick)], D('ReturnValue', out=True), x, y)
    def get(s, var, pin, x, y):
        n = s.name('Get' + var); varget(s.G, n, None, var, None, dict(pin, name=var), x, y, self_ctx=True); return (n, var)
    def set(s, var, pin, src, x, y):
        n = s.name('Set' + var); varset(s.G, n, None, var, None, dict(pin, name=var), x, y, self_ctx=True); s.wire(src, n, var); return n
    def now(s, x, y):
        n = s.name('Now'); callfn(s.G, n, GS, 'GetTimeSeconds', [WC(), D('ReturnValue', out=True)], pure=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def mpc_get(s, param, x, y):
        n = s.name('Get' + param)
        callfn(s.G, n, MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC),
               {'name': 'ParameterName', 'cat': 'name', 'default': param}, st('ReturnValue', LC, out=True)], x=x, y=y, self_hidden=True)
        k = s.name('Break' + param)
        mathfn(s.G, k, 'BreakColor', [st('InColor', LC)] + [fl(c, out=True, default='0.0') for c in 'RGBA'], x + 300, y + 150)
        s.G.link(n, 'ReturnValue', k, 'InColor')
        return n, {c: (k, c) for c in 'RGBA'}
    def mpc_set(s, param, rgba, x, y):
        k = s.name('Make' + param)
        mathfn(s.G, k, 'MakeColor', [fl(c, default='0.0') for c in 'RGBA'] + [st('ReturnValue', LC, out=True)], x - 250, y + 200)
        for c, src in zip('RGBA', rgba): s.wire(src, k, c)
        n = s.name('Set' + param)
        callfn(s.G, n, MATL, 'SetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC),
               {'name': 'ParameterName', 'cat': 'name', 'default': param}, st('ParameterValue', LC)], x=x, y=y, self_hidden=True)
        s.G.link(k, 'ReturnValue', n, 'ParameterValue')
        return n
    def call_self(s, event, x, y, pins=(), cls=None):
        n = s.name('Call' + event)
        ref = 'FunctionReference=(MemberName="%s",bSelfContext=True)' % event if cls is None else \
              'FunctionReference=(MemberParent=%s,MemberName="%s")' % (cls, event)
        s.G.node(n, 'K2Node_CallFunction', [ref], [ex(), ex('then', True), selfpin(cls or SETC, hidden=cls is None)] + list(pins), x, y)
        return n
    def event(s, name, params, x, y):
        """custom event with typed inputs: params = list of pin dicts (shown as outputs on the event)."""
        props = ['CustomFunctionName="%s"' % name]
        for p in params:
            t = 'PinCategory="%s"' % p['cat'] + (',PinSubCategory="%s"' % p['sub'] if p.get('sub') else '') + \
                (',PinSubCategoryObject=%s' % p['obj'] if p.get('obj') and p['obj'] != 'None' else '')
            props.append('CustomProperties UserDefinedPin (PinName="%s",PinType=(%s),DesiredPinDirection=EGPD_Output)' % (p['name'], t))
        s.G.node(name, 'K2Node_CustomEvent', props, [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '()'}, ex('then', True)]
                 + [dict(p, out=True) for p in params], x, y)
        return name
    def chain(s, *nodes):
        for a, b in zip(nodes, nodes[1:]):
            s.G.link(a[0] if isinstance(a, tuple) else a, a[1] if isinstance(a, tuple) else 'then', b, 'execute')

# =====================================================================================================================
# BPC_ObsidianSet: one ActorComponent on the hero. All #96 set/shield state lives here; the HUD only calls 4 events.
#   BuyPiece(Id 10..20)  SetPieceWorn(Id, Worn)  BuyShield()  LoadState(Owned, Worn, Bought, ShieldLvl)
# Refresh writes NextPrice / NextShieldPrice / WornCount and the MPC vectors ObsSet and Shield.
# OnOwnerHit (bound to the hero's OnTakeAnyDamage): the ember shockwave, PushZombies(Radius, Damage, Push).
# =====================================================================================================================
G = Graph(); b = B(G, 's')
INT, DBL, BOOL = it('v', default='0'), D('v', default='0.0'), bo('v', default='false')

# ---- BeginPlay: bind the owner's OnTakeAnyDamage, then Refresh ----
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
callfn(G, 'Owner1', COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=200, self_hidden=True)
G.node('Bind', 'K2Node_AddDelegate', ['DelegateReference=(MemberParent=%s,MemberName="OnTakeAnyDamage")' % ACT],
       [ex(), ex('then', True), selfpin(ACT), {'name': 'Delegate', 'cat': 'delegate', 'mref': '()'}], 300, 0)
G.link('BP', 'then', 'Bind', 'execute'); G.link('Owner1', 'ReturnValue', 'Bind', 'self')
c = b.call_self('Refresh', 600, 0); G.link('Bind', 'then', c, 'execute')

# ---- Bit(Id) = round(2 ^ (Id - 10)) ----
def bit_of(idsrc, x, y):
    e = b.i2('Subtract_IntInt', idsrc, None, x, y, db='10')
    return b.rnd(b.pow(None, b.i2d(e, x + 200, y), x + 400, y), x + 600, y)

# ---- BuyPiece(Id): ObsOwned |= Bit, ObsBought += 1, Refresh ----
Y = 500
b.event('BuyPiece', [it('Id')], 0, Y)
bit = bit_of(('BuyPiece', 'Id'), 0, Y + 200)
s1 = b.set('ObsOwned', INT, b.i2('Or_IntInt', b.get('ObsOwned', INT, 600, Y + 350), bit, 900, Y + 300), 1100, Y)
s2 = b.set('ObsBought', INT, b.i2('Add_IntInt', b.get('ObsBought', INT, 1100, Y + 350), None, 1300, Y + 300, db='1'), 1500, Y)
b.chain('BuyPiece', s1, s2, b.call_self('Refresh', 1800, Y))

# ---- SetPieceWorn(Id, Worn): ObsWorn = Worn ? ObsWorn | Bit : ObsWorn & ~Bit, Refresh ----
Y = 1100
b.event('SetPieceWorn', [it('Id'), bo('Worn')], 0, Y)
bit = bit_of(('SetPieceWorn', 'Id'), 0, Y + 250)
w = b.get('ObsWorn', INT, 600, Y + 450)
on = b.i2('Or_IntInt', w, bit, 900, Y + 350)
off = b.i2('And_IntInt', w, b.inot(bit, 800, Y + 550), 1000, Y + 500)
s1 = b.set('ObsWorn', INT, b.seli(on, off, ('SetPieceWorn', 'Worn'), 1200, Y + 400), 1400, Y)
b.chain('SetPieceWorn', s1, b.call_self('Refresh', 1700, Y))

# ---- BuyShield(): ShieldLevel = min(ShieldLevel + 1, 4), Refresh ----
Y = 1800
b.event('BuyShield', [], 0, Y)
lv = b.i2('Min', b.i2('Add_IntInt', b.get('ShieldLevel', INT, 0, Y + 200), None, 250, Y + 200, db='1'), None, 450, Y + 200, db='4')
s1 = b.set('ShieldLevel', INT, lv, 700, Y)
b.chain('BuyShield', s1, b.call_self('Refresh', 1000, Y))

# ---- LoadState(Owned, Worn, Bought, ShieldLvl): from the save; WasComplete is set first so the burst doesn't replay ----
Y = 2200
b.event('LoadState', [it('Owned'), it('Worn'), it('Bought'), it('ShieldLvl')], 0, Y)
s1 = b.set('ObsOwned', INT, ('LoadState', 'Owned'), 400, Y)
s2 = b.set('ObsWorn', INT, ('LoadState', 'Worn'), 650, Y)
s3 = b.set('ObsBought', INT, ('LoadState', 'Bought'), 900, Y)
s4 = b.set('ShieldLevel', INT, ('LoadState', 'ShieldLvl'), 1150, Y)
full = b.icmp('EqualEqual_IntInt', b.i2('And_IntInt', ('LoadState', 'Worn'), None, 1200, Y + 300, db='2047'), None, 1400, Y + 300, db='2047')
s5 = b.set('WasComplete', BOOL, full, 1400, Y)
b.chain('LoadState', s1, s2, s3, s4, s5, b.call_self('Refresh', 1700, Y))

# ---- Refresh ----
Y = 3000
b.event('Refresh', [], 0, Y)
wv = b.get('ObsWorn', INT, 0, Y + 300)
cnt = None
for i in range(11):     # WornCount = number of set bits 0..10
    x = 200 + i * 220
    one = b.b2i(b.icmp('Greater_IntInt', b.i2('And_IntInt', wv, None, x, Y + 400, db=str(1 << i)), None, x, Y + 550), x, Y + 700)
    cnt = one if cnt is None else b.i2('Add_IntInt', cnt, one, x + 100, Y + 850)
s_cnt = b.set('WornCount', INT, cnt, 2700, Y)
complete = b.icmp('EqualEqual_IntInt', b.i2('And_IntInt', wv, None, 2600, Y + 1000, db='2047'), None, 2800, Y + 1000, db='2047')
# NextPrice = Bought >= 11 ? 0 : round(450 * Mul^Bought / 50) * 50
bought = b.get('ObsBought', INT, 2900, Y + 400)
raw = b.d2('Multiply_DoubleDouble', b.pow(b.get('ObsPriceMul', DBL, 3000, Y + 600), b.i2d(bought, 3100, Y + 500), 3300, Y + 550), None, 3500, Y + 550, db='9.0')
price = b.i2('Multiply_IntInt', b.rnd(raw, 3700, Y + 550), None, 3900, Y + 550, db='50')   # 450/50 = 9
price = b.seli(None, price, b.icmp('GreaterEqual_IntInt', bought, None, 3900, Y + 700, db='11'), 4100, Y + 550)
s_price = b.set('NextPrice', INT, price, 3000, Y)
# NextShieldPrice by level 0..4: 600, 800, 1400, 2400, 0 (MAX)
lvl = b.get('ShieldLevel', INT, 3300, Y + 900)
sp = None
for L, p in ((3, 2400), (2, 1400), (1, 800), (0, 600)):
    eq = b.icmp('EqualEqual_IntInt', lvl, None, 3500 + (3 - L) * 220, Y + 1000, db=str(L))
    sp = b.seli(None, sp, eq, 3500 + (3 - L) * 220, Y + 1150, da=str(p), db='0')
s_sp = b.set('NextShieldPrice', INT, sp, 3300, Y)
# ObsSet = (complete, G = now on the frame it completes, keep B, WornCount)
gset, ch = b.mpc_get('ObsSet', 3600, Y)
just = b.b2('BooleanAND', complete, b.bnot(b.get('WasComplete', BOOL, 3900, Y + 1300), 4100, Y + 1300), 4300, Y + 1250)
g = b.self_(b.now(4300, Y + 1450), ch['G'], just, 4500, Y + 1300)
s_obs = b.mpc_set('ObsSet', [b.b2d(complete, 4500, Y + 1100), g, ch['B'], b.i2d(cnt, 4500, Y + 1500)], 4800, Y)
s_was = b.set('WasComplete', BOOL, complete, 5100, Y)
# Shield = (level, keep G)
gsh, chs = b.mpc_get('Shield', 5300, Y)
s_sh = b.mpc_set('Shield', [b.i2d(lvl, 5500, Y + 400), chs['G'], None, None], 5900, Y)
b.chain('Refresh', s_cnt, s_price, s_sp, gset, s_obs, s_was, gsh, s_sh)

# ---- OnOwnerHit: ember shockwave when the set is complete and ready ----
Y = 5000
b.event('OnOwnerHit', [ob('DamagedActor', ACT), fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CLS('Controller')), ob('DamageCauser', ACT)], 0, Y)
G.link('OnOwnerHit', 'OutputDelegate', 'Bind', 'Delegate')
nw = b.now(200, Y + 450)
ready = b.dcmp('GreaterEqual_DoubleDouble', nw, b.get('ShockReadyAt', DBL, 200, Y + 600), 450, Y + 500)
cond = b.b2('BooleanAND', b.get('WasComplete', BOOL, 450, Y + 350), ready, 650, Y + 400)
br = b.name('IfShock'); branch(G, br, 400, Y); G.link(cond[0], cond[1], br, 'Condition'); G.link('OnOwnerHit', 'then', br, 'execute')
s1 = b.set('ShockReadyAt', DBL, b.d2('Add_DoubleDouble', nw, b.get('ShockCooldown', DBL, 600, Y + 750), 850, Y + 650), 700, Y)
G.link(br, 'then', s1, 'execute')
push = b.call_self('PushZombies', 1000, Y, pins=[D('Radius', default='400.0'), D('Damage', default='40.0'), D('Push', default='900.0')])
G.link(s1, 'then', push, 'execute')
G.link(*b.get('ShockRadius', DBL, 800, Y + 300), push, 'Radius'); G.link(*b.get('ShockDamage', DBL, 800, Y + 400), push, 'Damage')
gso, cho = b.mpc_get('ObsSet', 1400, Y)
s_obs = b.mpc_set('ObsSet', [cho['R'], cho['G'], nw, cho['A']], 2000, Y)
b.chain(push, gso, s_obs)

# ---- PushZombies(Radius, Damage, Push): every BP_Zombie within Radius takes Damage and is launched away ----
Y = 6200
b.event('PushZombies', [D('Radius'), D('Damage'), D('Push')], 0, Y)
callfn(G, 'Owner2', COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=Y + 400, self_hidden=True)
callfn(G, 'OwnLoc', ACT, 'K2_GetActorLocation', [st('ReturnValue', VEC, out=True)], pure=True, const=True, x=250, y=Y + 400)
G.link('Owner2', 'ReturnValue', 'OwnLoc', 'self')
callfn(G, 'AllZ', GS, 'GetAllActorsOfClass', [WC(), {'name': 'ActorClass', 'cat': 'class', 'obj': ACT, 'dobj': '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C'},
       dict(ob('OutActors', ZOMBIE, out=True), container='Array')], x=300, y=Y, self_hidden=True)
G.link('PushZombies', 'then', 'AllZ', 'execute')
G.node('Loop', 'K2Node_MacroInstance', [
    'MacroGraphReference=(MacroGraph="/Script/Engine.EdGraph\'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop\'",GraphBlueprint="/Script/Engine.Blueprint\'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros\'",GraphGuid=99DBFD5540A796041F72A5A9DA655026)',
    'ResolvedWildcardType=(PinCategory="object",PinSubCategoryObject=%s)' % ZOMBIE],
    [ex('Exec'), dict(ob('Array', ZOMBIE), container='Array'), ex('LoopBody', True), ob('Array Element', ZOMBIE, out=True),
     it('Array Index', out=True), ex('Completed', True)], 650, Y)
G.link('AllZ', 'then', 'Loop', 'Exec'); G.link('AllZ', 'OutActors', 'Loop', 'Array')
callfn(G, 'ZLoc', ACT, 'K2_GetActorLocation', [st('ReturnValue', VEC, out=True)], pure=True, const=True, x=700, y=Y + 400)
G.link('Loop', 'Array Element', 'ZLoc', 'self')
dist = b.math('Vector_Distance', [(st('V1', VEC, default='0, 0, 0'), ('ZLoc', 'ReturnValue')), (st('V2', VEC, default='0, 0, 0'), ('OwnLoc', 'ReturnValue'))],
              D('ReturnValue', out=True), 950, Y + 400)
near = b.dcmp('Less_DoubleDouble', dist, ('PushZombies', 'Radius'), 1150, Y + 400)
br = b.name('IfNear'); branch(G, br, 1000, Y); G.link('Loop', 'LoopBody', br, 'execute'); G.link(near[0], near[1], br, 'Condition')
callfn(G, 'Hurt', GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage', default='40.0'), ob('EventInstigator', CLS('Controller')),
       ob('DamageCauser', ACT), {'name': 'DamageTypeClass', 'cat': 'class', 'obj': CLS('DamageType')}, fl('ReturnValue', out=True, default='0.0')], x=1300, y=Y, self_hidden=True)
G.link(br, 'then', 'Hurt', 'execute'); G.link('Loop', 'Array Element', 'Hurt', 'DamagedActor'); G.link('PushZombies', 'Damage', 'Hurt', 'BaseDamage')
G.link('Owner2', 'ReturnValue', 'Hurt', 'DamageCauser')
# launch: normal(zombie - hero) * Push, + 0.35 * Push up
away = b.math('Subtract_VectorVector', [(st('A', VEC, default='0, 0, 0'), ('ZLoc', 'ReturnValue')), (st('B', VEC, default='0, 0, 0'), ('OwnLoc', 'ReturnValue'))], st('ReturnValue', VEC, out=True), 1300, Y + 500)
nrm = b.math('Normal', [(st('A', VEC, default='0, 0, 0'), away), (fl('Tolerance', default='0.000100'), None)], st('ReturnValue', VEC, out=True), 1500, Y + 500)
vel = b.math('Multiply_VectorFloat', [(st('A', VEC, default='0, 0, 0'), nrm), (D('B', default='900.0'), ('PushZombies', 'Push'))], st('ReturnValue', VEC, out=True), 1700, Y + 500)
up = b.math('MakeVector', [(D('X', default='0.0'), None), (D('Y', default='0.0'), None), (D('Z', default='0.0'), b.d2('Multiply_DoubleDouble', ('PushZombies', 'Push'), None, 1700, Y + 750, db='0.35'))],
            st('ReturnValue', VEC, out=True), 1900, Y + 700)
vel = b.math('Add_VectorVector', [(st('A', VEC, default='0, 0, 0'), vel), (st('B', VEC, default='0, 0, 0'), up)], st('ReturnValue', VEC, out=True), 2100, Y + 550)
cast(G, 'AsChar', CHAR, 'AsCharacter', 1600, Y)
G.link('Hurt', 'then', 'AsChar', 'execute'); G.link('Loop', 'Array Element', 'AsChar', 'Object')
callfn(G, 'Launch', CHAR, 'LaunchCharacter', [st('LaunchVelocity', VEC, default='0, 0, 0'), bo('bXYOverride', default='true'), bo('bZOverride', default='true')], x=2300, y=Y)
G.link('AsChar', 'then', 'Launch', 'execute'); G.link('AsChar', 'AsCharacter', 'Launch', 'self'); G.link(vel[0], vel[1], 'Launch', 'LaunchVelocity')

open(os.path.join(HERE, 'BPC_ObsidianSet_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_ObsidianSet: nodes', len(G.nodes), 'links', len(G.links))

# =====================================================================================================================
# Hero paste (BP_ThirdPersonCharacter, next to Event AnyDamage). It replaces the single damage factor
#   Damage * (1 - Gear.R * 0.25)
# with
#   Damage * (1 - Gear.R * 0.25) * (1 - Armor.R * 0.35) * (1 - ObsSet.R * 0.15) * Block
# where Block = 0.4 when the shield blocks (chance 0.1 + 0.1 * level, levels 1..4), else 1.
# A block writes Shield.G = now (rune flash + dome) and, at LV4, pushes zombies 1.5 m back.
# Exec in: ObsIn.execute   exec out: ObsOut.then   value in: ObsDmg.A (the old multiply's result)   value out: ObsDmg.ReturnValue
# =====================================================================================================================
G = Graph(); b = B(G, 'h')
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
seq = sequence(G, 'ObsIn', 1, 0, 0)    # one-pin sequence = a named exec entry for the rewire
ga, cha = b.mpc_get('Armor', 250, 0)
go, cho = b.mpc_get('ObsSet', 800, 0)
gs, chs = b.mpc_get('Shield', 1350, 0)
b.chain(('ObsIn', 'then_0'), ga, go, gs)
lv = chs['R']
chance = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', lv, None, 1700, 400, db='0.1'), None, 1900, 400, db='0.1')
roll = b.math('RandomFloat', [], D('ReturnValue', out=True), 1900, 550)
blocked = b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', lv, None, 1900, 250, db='1.0'), b.dcmp('Less_DoubleDouble', roll, chance, 2100, 500), 2300, 350)
br = b.name('IfBlock'); branch(G, br, 1950, 0); G.link(gs, 'then', br, 'execute'); G.link(blocked[0], blocked[1], br, 'Condition')
s_bl = b.set('ObsBlocked', BOOL, blocked, 2250, 0)
G.link(br, 'then', s_bl, 'execute')
s_sh = b.mpc_set('Shield', [chs['R'], b.now(2300, 300), chs['B'], chs['A']], 2700, 0)
G.link(s_bl, 'then', s_sh, 'execute')
br4 = b.name('IfLv4'); branch(G, br4, 2950, 0); G.link(s_sh, 'then', br4, 'execute')
lv4 = b.dcmp('GreaterEqual_DoubleDouble', lv, None, 2950, 250, db='3.5'); G.link(lv4[0], lv4[1], br4, 'Condition')
comp = b.get('ObsidianSet', ob('v', SETC), 3100, 300)
push = b.call_self('PushZombies', 3250, 0, cls=SETC, pins=[D('Radius', default='150.0'), D('Damage', default='0.0'), D('Push', default='700.0')])
G.link(br4, 'then', push, 'execute'); G.link(comp[0], comp[1], push, 'self')
s_nb = b.set('ObsBlocked', BOOL, None, 2250, 700)          # no block this hit
G.link(br, 'else', s_nb, 'execute')
out = sequence(G, 'ObsOut', 1, 3700, 0)
G.link(br4, 'else', 'ObsOut', 'execute'); G.link(push, 'then', 'ObsOut', 'execute'); G.link(s_nb, 'then', 'ObsOut', 'execute')
# value: A * (1 - Armor.R*0.35) * (1 - ObsSet.R*0.15) * (blocked ? 0.4 : 1)
fa = b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', cha['R'], None, 600, 900, db='0.35'), 800, 900, da='1.0')
fo = b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', cho['R'], None, 600, 1050, db='0.15'), 800, 1050, da='1.0')
fb = b.self_(None, None, b.get('ObsBlocked', BOOL, 800, 1250), 1000, 1200, da='0.4', db='1.0')
m1 = b.d2('Multiply_DoubleDouble', fa, fo, 1100, 950)
G.node('ObsDmg', 'K2Node_CallFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Multiply_DoubleDouble")' % CLS('KismetMathLibrary')],
       [selfpin(CLS('KismetMathLibrary'), hidden=True), D('A', default='0.0'), D('B', default='1.0'), D('ReturnValue', out=True)], 1500, 1000)
m2 = b.d2('Multiply_DoubleDouble', m1, fb, 1300, 1100)
G.link(m2[0], m2[1], 'ObsDmg', 'B')
open(os.path.join(HERE, 'Hero_ObsidianDamage_graph.txt'), 'w', newline='\r\n').write(G.render())
print('Hero paste: nodes', len(G.nodes), 'links', len(G.links))
