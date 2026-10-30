# Obsidian set v2 (checkking, 2026-10-30): generates the full EventGraph of BPC_ObsidianSet.
#   python gen_set_v2.py  ->  BPC_ObsidianSet_v2_graph.txt   (replaces the #96 graph: Ctrl+A, BackSpace, Ctrl+V)
# Built on the live export handoffs/exports/master/2026-10-30/BPC_ObsidianSet.t3d: same 13 variables and the same events
# (BuyPiece, SetPieceWorn, BuyShield, LoadState, Refresh, OnOwnerHit, PushZombies), so nothing that calls them breaks.
# New: ToggleWear, DebugGiveAll, a 0.5 s Refresh timer, tiered bonus, piece meshes on the hero, knight slots hidden.
# Uses laptop2's bpkit (tools/laptop2/bpgen), which sits on the Master's node kit (tools/master/t81/kit.py).
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

COMP = CLS('ActorComponent')
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
SETC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet', 'BPC_ObsidianSet')
SMC, STATICMESHC = CLS('StaticMeshComponent'), CLS('StaticMeshComponent')
ZOMBIE = BPC('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', 'BP_Zombie')
NAME_ = lambda n, out=False, default=None: {'name': n, 'cat': 'name', 'out': out, 'default': default}
RULE = lambda n: {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', 'default': 'KeepRelative'}
INT, DBL, BOOL = it('v', default='0'), D('v', default='0.0'), bo('v', default='false')
XF = st('v', XFORM)
SMCV, SKV, MATV2 = ob('v', SMC), ob('v', SKEL), ob('v', MATI)


class B2(bpkit.B):
    def seli(s, a, b_, pick, x, y, da='0', db='0'):
        return s.math('SelectInt', [(it('A', default=da), a), (it('B', default=db), b_), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)
    def inot(s, a, x, y): return s.math('Not_Int', [(it('A', default='0'), a)], it('ReturnValue', out=True), x, y)
    def b2i(s, a, x, y): return s.math('Conv_BoolToInt', [(bo('InBool', default='false'), a)], it('ReturnValue', out=True), x, y)
    def b2d(s, a, x, y): return s.math('Conv_BoolToDouble', [(bo('InBool', default='false'), a)], D('ReturnValue', out=True), x, y)
    def round_(s, a, x, y): return s.math('Round', [(D('A', default='0.0'), a)], it('ReturnValue', out=True), x, y)
    def pow(s, base, e, x, y, db='2.0'):
        return s.math('MultiplyMultiply_FloatFloat', [(D('Base', default=db), base), (D('Exp', default='0.0'), e)], D('ReturnValue', out=True), x, y)
    def bit(s, idsrc, x, y):
        """Bit(Id) = round(2 ^ (Id - 10))"""
        e = s.i2('Subtract_IntInt', idsrc, None, x, y, db='10')
        return s.round_(s.pow(None, s.i2d(e, x + 200, y), x + 400, y), x + 600, y)
    def has(s, mask, bit, x, y):
        return s.icmp('Greater_IntInt', s.i2('And_IntInt', mask, bit, x, y), None, x + 200, y)
    def item(s, arrsrc, pin, idx, x, y):
        """GetArrayItem on an array that comes from a pin (not a variable)."""
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
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
    def me(s, member, x, y, pins=()):
        """call one of this component's own events (bSelfContext: MemberParent self-calls are dropped on paste, gotcha 1)."""
        return s.call_self(member, list(pins), x, y, SETC, tag='Call' + member)


G = Graph(); b = B2(G, 'o')

# =====================================================================================================================
# BeginPlay: bind the owner's damage, find KnightMesh (tag ObsKnight), keep its 5 original materials, re-attach every
# piece component (tag ObsK<k>) to its bone with the ref-pose offset from setup_set_v2_ue.py, then a 0.5 s Refresh timer.
# =====================================================================================================================
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
own = b.owner(0, 250)
G.node('Bind', 'K2Node_AddDelegate', ['DelegateReference=(MemberParent=%s,MemberName="OnTakeAnyDamage")' % ACT],
       [ex(), ex('then', True), selfpin(ACT), {'name': 'Delegate', 'cat': 'delegate', 'mref': '()'}], 300, 0)
G.link('BP', 'then', 'Bind', 'execute'); b.wire(own, 'Bind', 'self')

kn = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.SkeletalMeshComponent'), NAME_('Tag', default='ObsKnight'),
            arr(ob('ReturnValue', SKEL, out=True))], 600, 250, target=own, const=True, pure=True, tag='FindKnight')
sK = b.set('Knight', SKV, b.item((kn, 'ReturnValue'), ob('v', SKEL), None, 900, 300), 1100, 0)
G.link('Bind', 'then', sK, 'execute')
lp = b.forloop(None, None, 1400, 0); G.link(sK, 'then', lp, 'execute')
lastK = b.i2('Subtract_IntInt', b.alen('KnightCover', INT, 1100, 450), None, 1400, 450, db='1')
b.wire(lastK, lp, 'LastIndex')
gm = b.call(PRIM, 'GetMaterial', [it('ElementIndex', default='0'), ob('ReturnValue', MATI, out=True)], 1700, 300,
            target=b.get('Knight', SKV, 1500, 350), pure=True, const=True)
b.wire((lp, 'Index'), gm, 'ElementIndex')
addm = b.aadd('KnightMats', MATV2, (gm, 'ReturnValue'), 1900, 0); G.link(lp, 'LoopBody', addm, 'execute')

lp2 = b.forloop(None, None, 2300, 0); G.link(lp, 'Completed', lp2, 'execute')
lastP = b.i2('Subtract_IntInt', b.alen('PieceId', INT, 2000, 500), None, 2300, 500, db='1')
b.wire(lastP, lp2, 'LastIndex')
idxs = b.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], 2400, 400, pure=True)
b.wire((lp2, 'Index'), idxs, 'InInt')
tagn = b.lib(KSTR, 'Conv_StringToName', [S('InString'), NAME_('ReturnValue', out=True)], 2800, 400, pure=True)
b.wire(b.concat(None, (idxs, 'ReturnValue'), 2600, 400, da='ObsK'), tagn, 'InString')
fc = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.StaticMeshComponent'), NAME_('Tag'),
            arr(ob('ReturnValue', SMC, out=True))], 3000, 400, target=b.owner(2800, 550), const=True, pure=True, tag='FindPiece')
b.wire((tagn, 'ReturnValue'), fc, 'Tag')
pc = b.item((fc, 'ReturnValue'), ob('v', SMC), None, 3250, 450)
att = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), NAME_('SocketName'), RULE('LocationRule'), RULE('RotationRule'), RULE('ScaleRule'),
             bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], 3500, 0, target=pc)
b.wire(b.get('Knight', SKV, 3300, 700), att, 'Parent'); b.wire(b.aget('PieceBone', NAME_('v'), (lp2, 'Index'), 3100, 800), att, 'SocketName')
okp = b.branch(b.valid(pc, 3300, 250), 2700, 0, tag='IfPiece'); G.link(lp2, 'LoopBody', okp, 'execute'); G.link(okp, 'then', att, 'execute')
srt = b.call(SCENE, 'K2_SetRelativeTransform', [st('NewTransform', XFORM), bo('bSweep', default='false'), dict(st('SweepHitResult', HITRES, out=True)),
             bo('bTeleport', default='true')], 3900, 0, target=pc)
b.wire(b.aget('PieceOffset', XF, (lp2, 'Index'), 3600, 900), srt, 'NewTransform'); G.link(att, 'then', srt, 'execute')
addc = b.aadd('PieceComps', SMCV, pc, 4300, 0); G.link(srt, 'then', addc, 'execute')
G.link(okp, 'else', addc, 'execute')          # keep indices aligned with the table even if a component is missing
tm = b.timer('Refresh', 2700, -300, dtime='0.5', loop=True); G.link(lp2, 'Completed', tm, 'execute')
G.link(tm, 'then', b.me('Refresh', 3000, -300), 'execute')

# =====================================================================================================================
# BuyPiece(Id): only a piece that has art and isn't owned yet. Owned + worn (a bought piece goes straight on), count +1.
# =====================================================================================================================
Y = 1400
b.event('BuyPiece', [it('Id')], 0, Y)
bit = b.bit(('BuyPiece', 'Id'), 0, Y + 250)
ok = b.b2('BooleanAND', b.has(b.get('AvailMask', INT, 600, Y + 400), bit, 800, Y + 400),
          b.bnot(b.has(b.get('ObsOwned', INT, 600, Y + 550), bit, 800, Y + 550), 1050, Y + 550), 1250, Y + 450)
br = b.branch(ok, 300, Y, tag='IfCanBuy'); G.link('BuyPiece', 'then', br, 'execute')
s1 = b.set('ObsOwned', INT, b.i2('Or_IntInt', b.get('ObsOwned', INT, 1300, Y + 700), bit, 1500, Y + 700), 1500, Y)
s2 = b.set('ObsWorn', INT, b.i2('Or_IntInt', b.get('ObsWorn', INT, 1500, Y + 850), bit, 1700, Y + 850), 1750, Y)
s3 = b.set('ObsBought', INT, b.i2('Add_IntInt', b.get('ObsBought', INT, 1800, Y + 1000), None, 2000, Y + 1000, db='1'), 2000, Y)
G.link(br, 'then', s1, 'execute'); b.chain(s1, s2, s3, b.me('Refresh', 2300, Y))

# =====================================================================================================================
# SetPieceWorn(Id, Worn): on only if owned. ToggleWear(Id): flips it (for the HUD set panel).
# =====================================================================================================================
Y = 2700
b.event('SetPieceWorn', [it('Id'), bo('Worn')], 0, Y)
bit = b.bit(('SetPieceWorn', 'Id'), 0, Y + 250)
w = b.get('ObsWorn', INT, 600, Y + 450)
on = b.i2('Or_IntInt', w, b.i2('And_IntInt', bit, b.get('ObsOwned', INT, 700, Y + 650), 900, Y + 600), 1100, Y + 450)
off = b.i2('And_IntInt', w, b.inot(bit, 900, Y + 800), 1100, Y + 750)
s1 = b.set('ObsWorn', INT, b.seli(on, off, ('SetPieceWorn', 'Worn'), 1300, Y + 500), 1400, Y)
b.chain('SetPieceWorn', s1, b.me('Refresh', 1700, Y))

Y = 3700
b.event('ToggleWear', [it('Id')], 0, Y)
bit = b.bit(('ToggleWear', 'Id'), 0, Y + 250)
cw = b.me('SetPieceWorn', 900, Y, pins=[it('Id', default='0'), bo('Worn', default='false')])
b.wire(('ToggleWear', 'Id'), cw, 'Id'); b.wire(b.bnot(b.has(b.get('ObsWorn', INT, 600, Y + 450), bit, 700, Y + 450), 900, Y + 450), cw, 'Worn')
b.chain('ToggleWear', cw)

# ---- DebugGiveAll(): every piece with art owned and worn (test without the HUD) ----
Y = 4300
b.event('DebugGiveAll', [], 0, Y)
s1 = b.set('ObsOwned', INT, b.get('AvailMask', INT, 200, Y + 200), 350, Y)
s2 = b.set('ObsWorn', INT, b.get('AvailMask', INT, 450, Y + 200), 600, Y)
b.chain('DebugGiveAll', s1, s2, b.me('Refresh', 900, Y))

# ---- BuyShield(): unchanged from #96 ----
Y = 4800
b.event('BuyShield', [], 0, Y)
lv = b.i2('Min', b.i2('Add_IntInt', b.get('ShieldLevel', INT, 0, Y + 200), None, 250, Y + 200, db='1'), None, 450, Y + 200, db='4')
b.chain('BuyShield', b.set('ShieldLevel', INT, lv, 700, Y), b.me('Refresh', 1000, Y))

# ---- LoadState(Owned, Worn, Bought, ShieldLvl): from the save; a full set loads without replaying the burst ----
Y = 5300
b.event('LoadState', [it('Owned'), it('Worn'), it('Bought'), it('ShieldLvl')], 0, Y)
s1 = b.set('ObsOwned', INT, ('LoadState', 'Owned'), 400, Y)
s2 = b.set('ObsWorn', INT, ('LoadState', 'Worn'), 650, Y)
s3 = b.set('ObsBought', INT, ('LoadState', 'Bought'), 900, Y)
s4 = b.set('ShieldLevel', INT, ('LoadState', 'ShieldLvl'), 1150, Y)
full = b.icmp('EqualEqual_IntInt', b.i2('And_IntInt', ('LoadState', 'Worn'), None, 1200, Y + 300, db='2047'), None, 1400, Y + 300, db='2047')
b.chain('LoadState', s1, s2, s3, s4, b.set('WasComplete', BOOL, full, 1400, Y), b.me('Refresh', 1700, Y))

# =====================================================================================================================
# Refresh (events + every 0.5 s):
#   WornEff = (ObsWorn without bit 0 | cuirass worn via Armor.R) & AvailMask
#   WornCount, Tier (pieces >= TierAt[i]), ObsSet = (TierDR / 0.15, completion time, last shock, WornCount)
#   prices; then, only when WornEff changed: piece visibility + covered knight slots hidden
# =====================================================================================================================
Y = 6200
b.event('Refresh', [], 0, Y)
ga, cha = b.mpc_get('Armor', 250, Y)
G.link('Refresh', 'then', ga, 'execute')
chest = b.b2i(b.dcmp('GreaterEqual_DoubleDouble', cha['R'], None, 700, Y + 400, db='0.5'), 900, Y + 400)
we = b.i2('And_IntInt', b.i2('Or_IntInt', b.i2('And_IntInt', b.get('ObsWorn', INT, 700, Y + 550), None, 900, Y + 550, db='2046'), chest, 1100, Y + 450),
          b.get('AvailMask', INT, 1100, Y + 650), 1300, Y + 500)
sWe = b.set('WornEff', INT, we, 900, Y); G.link(ga, 'then', sWe, 'execute')
wv = b.get('WornEff', INT, 1200, Y + 900)
cnt = None
for i in range(11):
    x = 1300 + i * 220
    one = b.b2i(b.icmp('Greater_IntInt', b.i2('And_IntInt', wv, None, x, Y + 1000, db=str(1 << i)), None, x, Y + 1150), x, Y + 1300)
    cnt = one if cnt is None else b.i2('Add_IntInt', cnt, one, x + 100, Y + 1450)
sCnt = b.set('WornCount', INT, cnt, 1500, Y); G.link(sWe, 'then', sCnt, 'execute')
nc = b.get('WornCount', INT, 1600, Y + 1700)
tier = None
for i in range(5):
    x = 1700 + i * 260
    one = b.b2i(b.icmp('GreaterEqual_IntInt', nc, b.aget('TierAt', INT, b.i2('Add_IntInt', None, None, x - 200, Y + 1900, da=str(i)), x, Y + 1850), x + 220, Y + 1800), x + 220, Y + 2000)
    tier = one if tier is None else b.i2('Add_IntInt', tier, one, x + 240, Y + 2150)
sTier = b.set('Tier', INT, tier, 1900, Y); G.link(sCnt, 'then', sTier, 'execute')
tv = b.get('Tier', INT, 2100, Y + 2400)
dr = b.d2('Multiply_DoubleDouble', b.aget('TierDR', DBL, b.i2('Max', b.i2('Subtract_IntInt', tv, None, 2300, Y + 2500, db='1'), None, 2500, Y + 2500, db='0'), 2700, Y + 2450),
          b.b2d(b.icmp('Greater_IntInt', tv, None, 2700, Y + 2650, db='0'), 2900, Y + 2650), 3100, Y + 2500)
complete = b.icmp('EqualEqual_IntInt', tv, None, 3100, Y + 2800, db='5')
# prices (unchanged from #96)
bought = b.get('ObsBought', INT, 2300, Y + 300)
raw = b.d2('Multiply_DoubleDouble', b.pow(b.get('ObsPriceMul', DBL, 2400, Y + 450), b.i2d(bought, 2500, Y + 350), 2700, Y + 400), None, 2900, Y + 400, db='9.0')
price = b.i2('Multiply_IntInt', b.round_(raw, 3100, Y + 400), None, 3300, Y + 400, db='50')
price = b.seli(None, price, b.icmp('GreaterEqual_IntInt', bought, None, 3300, Y + 550, db='11'), 3500, Y + 400)
sPrice = b.set('NextPrice', INT, price, 2300, Y); G.link(sTier, 'then', sPrice, 'execute')
lvl = b.get('ShieldLevel', INT, 2600, Y + 700)
sp = None
for L, p in ((3, 2400), (2, 1400), (1, 800), (0, 600)):
    eq = b.icmp('EqualEqual_IntInt', lvl, None, 2800 + (3 - L) * 220, Y + 750, db=str(L))
    sp = b.seli(None, sp, eq, 2800 + (3 - L) * 220, Y + 850, da=str(p), db='0')
sSp = b.set('NextShieldPrice', INT, sp, 2600, Y); G.link(sPrice, 'then', sSp, 'execute')
go, cho = b.mpc_get('ObsSet', 3700, Y); G.link(sSp, 'then', go, 'execute')
just = b.b2('BooleanAND', complete, b.bnot(b.get('WasComplete', BOOL, 3900, Y + 1200), 4100, Y + 1200), 4300, Y + 1150)
gt = b.self_(b.now(4300, Y + 1350), cho['G'], just, 4500, Y + 1250)
sObs = b.mpc_set('ObsSet', [b.d2('Divide_DoubleDouble', dr, None, 4400, Y + 1000, db='0.15'), gt, cho['B'], b.i2d(nc, 4500, Y + 1450)], 4900, Y)
G.link(go, 'then', sObs, 'execute')
sWas = b.set('WasComplete', BOOL, complete, 5200, Y); G.link(sObs, 'then', sWas, 'execute')
gs, chs = b.mpc_get('Shield', 5400, Y); G.link(sWas, 'then', gs, 'execute')
sSh = b.mpc_set('Shield', [b.i2d(lvl, 5600, Y + 400), chs['G'], None, None], 6000, Y); G.link(gs, 'then', sSh, 'execute')
# visuals only when WornEff changed
chg = b.icmp('NotEqual_IntInt', b.get('WornEff', INT, 6100, Y + 300), b.get('LastWorn', INT, 6100, Y + 450), 6300, Y + 350)
bChg = b.branch(chg, 6300, Y, tag='IfChanged'); G.link(sSh, 'then', bChg, 'execute')
sLast = b.set('LastWorn', INT, b.get('WornEff', INT, 6400, Y + 250), 6600, Y); G.link(bChg, 'then', sLast, 'execute')
lv1 = b.forloop(None, b.i2('Subtract_IntInt', b.alen('PieceComps', SMCV, 6600, Y + 500), None, 6900, Y + 500, db='1'), 6900, Y)
G.link(sLast, 'then', lv1, 'execute')
pcomp = b.aget('PieceComps', SMCV, (lv1, 'Index'), 7100, Y + 400)
vis = b.has(b.get('WornEff', INT, 7100, Y + 700), b.bit(b.aget('PieceId', INT, (lv1, 'Index'), 6900, Y + 850), 7100, Y + 850), 7700, Y + 700)
bV = b.branch(b.valid(pcomp, 7400, Y + 300), 7300, Y, tag='IfComp'); G.link(lv1, 'LoopBody', bV, 'execute')
sv = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 7700, Y, target=pcomp)
b.wire(vis, sv, 'bNewVisibility'); G.link(bV, 'then', sv, 'execute')
# knight slots: hidden only when every piece that covers the slot is worn (no holes while the set is partial)
lv2 = b.forloop(None, b.i2('Subtract_IntInt', b.alen('KnightMats', MATV2, 7000, Y + 1300), None, 7300, Y + 1300, db='1'), 7400, Y + 1100)
G.link(lv1, 'Completed', lv2, 'execute')
cov = b.aget('KnightCover', INT, (lv2, 'Index'), 7400, Y + 1500)
hide = b.b2('BooleanAND', b.icmp('Greater_IntInt', cov, None, 7800, Y + 1500, db='0'),
            b.icmp('EqualEqual_IntInt', b.i2('And_IntInt', b.get('WornEff', INT, 7600, Y + 1700), cov, 7800, Y + 1650), cov, 8000, Y + 1650), 8200, Y + 1550)
bH = b.branch(hide, 7800, Y + 1100, tag='IfHide'); G.link(lv2, 'LoopBody', bH, 'execute')
knt = b.get('Knight', SKV, 8000, Y + 1900)
smH = b.call(PRIM, 'SetMaterial', [it('ElementIndex', default='0'), ob('Material', MATI)], 8300, Y + 1000, target=knt, tag='Hide')
b.wire((lv2, 'Index'), smH, 'ElementIndex'); b.wire(b.get('HiddenMat', MATV2, 8100, Y + 2000), smH, 'Material'); G.link(bH, 'then', smH, 'execute')
smS = b.call(PRIM, 'SetMaterial', [it('ElementIndex', default='0'), ob('Material', MATI)], 8300, Y + 1300, target=knt, tag='Show')
b.wire((lv2, 'Index'), smS, 'ElementIndex'); b.wire(b.aget('KnightMats', MATV2, (lv2, 'Index'), 8000, Y + 2100), smS, 'Material'); G.link(bH, 'else', smS, 'execute')

# =====================================================================================================================
# OnOwnerHit: ember shockwave from tier 3 (6 pieces). Tier 4+ recharges 25 % faster.
# =====================================================================================================================
Y = 9000
b.event('OnOwnerHit', [ob('DamagedActor', ACT), fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CLS('Controller')), ob('DamageCauser', ACT)], 0, Y)
G.link('OnOwnerHit', 'OutputDelegate', 'Bind', 'Delegate')
nw = b.now(200, Y + 450)
ready = b.dcmp('GreaterEqual_DoubleDouble', nw, b.get('ShockReadyAt', DBL, 200, Y + 600), 450, Y + 500)
t3 = b.icmp('GreaterEqual_IntInt', b.get('Tier', INT, 250, Y + 300), None, 450, Y + 300, db='3')
br = b.branch(b.b2('BooleanAND', t3, ready, 650, Y + 400), 400, Y, tag='IfShock'); G.link('OnOwnerHit', 'then', br, 'execute')
fast = b.self_(None, None, b.icmp('GreaterEqual_IntInt', b.get('Tier', INT, 500, Y + 900), None, 700, Y + 900, db='4'), 900, Y + 850, da='0.75', db='1.0')
cd = b.d2('Multiply_DoubleDouble', b.get('ShockCooldown', DBL, 700, Y + 750), fast, 1000, Y + 750)
s1 = b.set('ShockReadyAt', DBL, b.d2('Add_DoubleDouble', nw, cd, 1100, Y + 650), 700, Y); G.link(br, 'then', s1, 'execute')
push = b.me('PushZombies', 1000, Y, pins=[D('Radius', default='400.0'), D('Damage', default='40.0'), D('Push', default='900.0')])
G.link(s1, 'then', push, 'execute')
b.wire(b.get('ShockRadius', DBL, 800, Y + 300), push, 'Radius'); b.wire(b.get('ShockDamage', DBL, 800, Y + 400), push, 'Damage')
gso, cso = b.mpc_get('ObsSet', 1400, Y)
b.chain(push, gso, b.mpc_set('ObsSet', [cso['R'], cso['G'], nw, cso['A']], 2000, Y))

# =====================================================================================================================
# PushZombies(Radius, Damage, Push): unchanged from #96
# =====================================================================================================================
Y = 10200
b.event('PushZombies', [D('Radius'), D('Damage'), D('Push')], 0, Y)
own2 = b.owner(0, Y + 400)
ol = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 250, Y + 400, target=own2, pure=True, const=True, tag='OwnLoc')
allz = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C'),
             arr(ob('OutActors', ZOMBIE, out=True))], 300, Y, tag='AllZ')
G.link('PushZombies', 'then', allz, 'execute')
lz = b.foreach(ZOMBIE, 650, Y); G.link(allz, 'then', lz, 'Exec'); G.link(allz, 'OutActors', lz, 'Array')
zl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 700, Y + 400, target=(lz, 'Array Element'), pure=True, const=True, tag='ZLoc')
dist = b.math('Vector_Distance', [(V('V1'), (zl, 'ReturnValue')), (V('V2'), (ol, 'ReturnValue'))], D('ReturnValue', out=True), 950, Y + 400)
bn = b.branch(b.dcmp('Less_DoubleDouble', dist, ('PushZombies', 'Radius'), 1150, Y + 400), 1000, Y, tag='IfNear'); G.link(lz, 'LoopBody', bn, 'execute')
hurt = b.lib(GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage', default='40.0'), ob('EventInstigator', CLS('Controller')), ob('DamageCauser', ACT),
             {'name': 'DamageTypeClass', 'cat': 'class', 'obj': CLS('DamageType')}, fl('ReturnValue', out=True, default='0.0')], 1300, Y, tag='Hurt')
G.link(bn, 'then', hurt, 'execute'); b.wire((lz, 'Array Element'), hurt, 'DamagedActor'); b.wire(('PushZombies', 'Damage'), hurt, 'BaseDamage'); b.wire(own2, hurt, 'DamageCauser')
away = b.v2('Subtract_VectorVector', (zl, 'ReturnValue'), (ol, 'ReturnValue'), 1300, Y + 500)
nrm = b.math('Normal', [(V('A'), away), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 1500, Y + 500)
vel = b.math('Multiply_VectorFloat', [(V('A'), nrm), (D('B', default='900.0'), ('PushZombies', 'Push'))], V('ReturnValue', out=True), 1700, Y + 500)
up = b.vec(None, None, b.d2('Multiply_DoubleDouble', ('PushZombies', 'Push'), None, 1700, Y + 750, db='0.35'), 1900, Y + 700)
vel = b.v2('Add_VectorVector', vel, up, 2100, Y + 550)
cast(G, 'AsChar', CHARC, 'AsCharacter', 1600, Y)
G.link(hurt, 'then', 'AsChar', 'execute'); b.wire((lz, 'Array Element'), 'AsChar', 'Object')
la = b.call(CHARC, 'LaunchCharacter', [V('LaunchVelocity'), bo('bXYOverride', default='true'), bo('bZOverride', default='true')], 2300, Y, target=('AsChar', 'AsCharacter'), tag='Launch')
G.link('AsChar', 'then', la, 'execute'); b.wire(vel, la, 'LaunchVelocity')

# ---------------------------------------------------------------- self-check + write
names = {n[0] for n in G.nodes}
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
out = os.path.join(HERE, 'BPC_ObsidianSet_v2_graph.txt')
open(out, 'w', newline='\r\n').write(G.render())
print('BPC_ObsidianSet v2: nodes %d, links %d -> %s' % (len(G.nodes), len(G.links), out))
