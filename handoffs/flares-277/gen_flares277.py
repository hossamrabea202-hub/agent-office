# #277 Crossbow flares (adjustedfilm, 2026-10-31; owner idea): a barracks upgrade; at night crossbowmen fire illumination
# flares at threats they spot - never constantly, only at a spotted danger, so the player sees what comes in the dark.
#   "<blender python>" -I gen_flares277.py -> BP_Flare_graph.txt, BPC_Flares_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
#
# BPC_Flares (hero component "Flares"):
#   shop  - near the barracks NPC (4.5 m) while not owned: notice "[F] Crossbow flares: 400 gold ..."; F buys (BP_ZombieHUD
#           Gold), saved in slot CastleSaveFlares (Data = [Owned]) like the weapon kit.
#   fire  - FlarePoll every 1 s, only when owned + night (BP_DayNight.IsNight) + FlareGap since the last flare + fewer
#           than MaxFlares burning: one random crossbowman looks for the best zombie between SightRange (14 m, he sees it
#           anyway) and SpotRange (60 m): nearest first, a colossus wall-breaker (#138) counts 40 m nearer. If no burning
#           flare already lights that spot (LitRadius 25 m), he fires one. No threat = no flare.
# BP_Flare: flies 1.4 s on an arc to 22 m over the target, ignites (pop + hiss loop), hangs and drifts down 0.55 m/s with a
#   slow sway, light flickers like burning magnesium (4500 K, 3500 cd, shadows), fades over the last 2.5 s of a 26 s burn.
import math, os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP = CLS('ActorComponent')
P_FLARE = '/Game/CastleDefender/Gameplay/Flares/BP_Flare'
P_DN = '/Game/CastleDefender/Environment/DayNight/BP_DayNight'
P_NPC = '/Game/CastleDefender/Gameplay/Castle/BP_NPC_Barracks'
P_XBOW = '/Game/CastleDefender/Characters/Knight/BP_SoldierXbow'
P_WB = '/Game/CastleDefender/Gameplay/Siege/BP_ZombieWallBreaker'
P_ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
FX = '/Game/CastleDefender/Gameplay/Flares/'
FLAREC, DNC, NPCC, XBOWC = BPC(P_FLARE, 'BP_Flare'), BPC(P_DN, 'BP_DayNight'), BPC(P_NPC, 'BP_NPC_Barracks'), BPC(P_XBOW, 'BP_SoldierXbow')
ZHUDC, NOTC = BPC(P_ZHUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD')
SAVEC = BPC('/Game/CastleDefender/Gameplay/Save/BP_CastleSave', 'BP_CastleSave')
SAVEG, HUDCLS, SOUND, AUDC = CLS('SaveGame'), CLS('HUD'), CLS('SoundBase'), CLS('AudioComponent')
PLC, CLSC = CLS('PointLightComponent'), '"/Script/CoreUObject.Class\'/Script/CoreUObject.Class\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
SLOT = 'CastleSaveFlares'
OBJV = lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
SHOP_TEXT = '[F] Crossbow flares: 400 gold. At night your crossbowmen light up the threats they spot.'


class B7(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def div(s, a, c, x, y, db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def sin(s, a, x, y): return s.math('Sin', [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
    def lerpv(s, a, c, t, x, y):
        return s.math('VLerp', [(V('A'), a), (V('B'), c), (fl('Alpha', default='0.0'), t)], V('ReturnValue', out=True), x, y)
    def getall(s, path, cls, x, y):
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def count(s, node, x, y):
        n = s.name('Count')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.G.link(node, 'OutActors', n, 'TargetArray'); return (n, 'ReturnValue')
    def item(s, arrsrc, pin, idx, x, y):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def actor_of_(s, path, cls, x, y):
        return s.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], x, y, tag='Find' + path.split('/')[-1][3:])
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
    def myloc(s, x, y):
        n = s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'); return (n, 'ReturnValue')
    def dist2d(s, a, c, x, y): return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hud_cast(s, cls, label, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x - 150, y + 300, target=s.pc(x - 350, y + 300), pure=True, const=True, tag='HUD')
        nc = s.name('As' + label); cast(s.G, nc, cls, 'As' + label, x, y); s.wire((hud, 'ReturnValue'), nc, 'Object'); return nc, (nc, 'As' + label)
    def notice(s, text, x, y):
        nc, nh = s.hud_cast(NOTC, 'BP Notice HUD', x, y)
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x + 300, y, target=nh, tag='Notice')
        s.G.link(nc, 'then', pn, 'execute'); return nc, pn
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def sound_at(s, name, loc, x, y, vol='1.000000'):
        n = s.lib(GS, 'PlaySoundAtLocation', [WC(), dict(ob('Sound', SOUND), dobj=FX + '%s.%s' % (name, name)), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
                  fl('VolumeMultiplier', default=vol), fl('PitchMultiplier', default='1.000000'), fl('StartTime', default='0.000000')], x, y, tag=name[10:])
        s.wire(loc, n, 'Location'); return n


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


# ================================================================================================= BP_Flare
G = Graph(); b = B7(G, 'fl')
g = b.get
event_override(G, 'BP', ACT, 'ReceiveBeginPlay', [], 0, 0)
fl_ = b.call_self('GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.PointLightComponent'), NAME_('Tag', 'FlareLight'),
                  arr(ob('ReturnValue', PLC, out=True))], 200, 300, ACT, pure=True, const=True, tag='FindLight')
sl = b.set('Light', OBJV(PLC), b.item((fl_, 'ReturnValue'), ob('v', PLC), None, 450, 300), 300, 0); G.link('BP', 'then', sl, 'execute')
ss = b.set('Start', V('v'), b.myloc(500, 250), 600, 0); G.link(sl, 'then', ss, 'execute')
st0 = b.set('T0', DBL, b.now(800, 250), 850, 0); G.link(ss, 'then', st0, 'execute')
ln = b.sound_at('SFX_Flare_Launch', b.myloc(1000, 250), 1150, 0); G.link(st0, 'then', ln, 'execute')

Y = 900
event_override(G, 'Tick', ACT, 'ReceiveTick', [fl('DeltaSeconds')], 0, Y)
t = b.sub(b.now(200, Y + 300), g('T0', DBL, 200, Y + 400), 400, Y + 350)
tgt = g('Target', V('v'), 200, Y + 600)
apex = b.v2('Add_VectorVector', tgt, b.vec(None, None, g('FlareHeight', DBL, 200, Y + 700), 400, Y + 700), 600, Y + 650)
fly = b.branch(b.dcmp('Less_DoubleDouble', t, None, 600, Y + 300, db='1.4'), 300, Y, tag='IfFlying'); G.link('Tick', 'then', fly, 'execute')
p = b.sat(b.div(t, None, 800, Y + 450, db='1.4'), 1000, Y + 450)
om = b.sub(None, p, 1200, Y + 450, da='1.0')
e = b.sub(None, b.mul(om, om, 1400, Y + 450), 1600, Y + 450, da='1.0')
arc = b.vec(None, None, b.mul(b.sin(b.mul(p, None, 1400, Y + 600, db=repr(math.pi)), 1600, Y + 600), None, 1800, Y + 600, db='500.0'), 2000, Y + 600)
fpos = b.v2('Add_VectorVector', b.lerpv(g('Start', V('v'), 1600, Y + 750), apex, e, 1800, Y + 700), arc, 2200, Y + 650)
mv1 = b.call_self('K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true'),
                  bo('ReturnValue', out=True, default='false')], 900, Y - 200, ACT, tag='Fly')
b.wire(fpos, mv1, 'NewLocation'); G.link(fly, 'then', mv1, 'execute')
# burning
lit = g('Lit', BOOL, 700, Y + 900)
bi = b.branch(b.bnot(lit, 900, Y + 900), 700, Y + 100, tag='IfIgnite'); G.link(fly, 'else', bi, 'execute')
sli = b.set('Lit', bo('v', default='true'), None, 1000, Y + 100); G.link(bi, 'then', sli, 'execute')
ig = b.sound_at('SFX_Flare_Ignite', b.myloc(1100, Y + 300), 1250, Y + 100); G.link(sli, 'then', ig, 'execute')
root = b.call_self('K2_GetRootComponent', [ob('ReturnValue', SCENE, out=True)], 1400, Y + 400, ACT, pure=True, const=True, tag='Root')
sa = b.lib(GS, 'SpawnSoundAttached', [dict(ob('Sound', SOUND), dobj=FX + 'SFX_Flare_Burn.SFX_Flare_Burn'), ob('AttachToComponent', SCENE), NAME_('AttachPointName', 'None'),
           V('Location'), st('Rotation', ROT, default='0, 0, 0'), {'name': 'LocationType', 'cat': 'byte', 'obj': ENUM('EAttachLocation'), 'default': 'KeepRelativeOffset'},
           bo('bStopWhenAttachedToDestroyed', default='true'), fl('VolumeMultiplier', default='0.700000'), fl('PitchMultiplier', default='1.000000'),
           ob('ReturnValue', AUDC, out=True)], 1550, Y + 100, tag='BurnLoop')
b.wire((root, 'ReturnValue'), sa, 'AttachToComponent'); G.link(ig, 'then', sa, 'execute')
mg = b.seq('Burning', 1, 1900, Y + 100); G.link(bi, 'else', mg, 'execute'); G.link(sa, 'then', mg, 'execute')
h = b.sub(t, None, 400, Y + 1200, db='1.4')
sway = b.vec(b.mul(b.sin(b.mul(h, None, 600, Y + 1300, db='0.9'), 800, Y + 1300), None, 1000, Y + 1300, db='60.0'),
             b.mul(b.sin(b.add(b.mul(h, None, 600, Y + 1400, db='0.7'), None, 800, Y + 1400, db='1.0'), 1000, Y + 1400), None, 1200, Y + 1400, db='45.0'),
             b.mul(h, None, 1000, Y + 1500, db='-55.0'), 1400, Y + 1400)
hpos = b.v2('Add_VectorVector', apex, sway, 1600, Y + 1350)
mv2 = b.call_self('K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true'),
                  bo('ReturnValue', out=True, default='false')], 2200, Y + 100, ACT, tag='Hang')
b.wire(hpos, mv2, 'NewLocation'); G.link(mg, 'then_0', mv2, 'execute')
life = g('Life', DBL, 1600, Y + 1700)
ramp = b.sat(b.div(h, None, 1800, Y + 1600, db='0.3'), 2000, Y + 1600)
fade = b.sat(b.div(b.sub(life, h, 1800, Y + 1750), None, 2000, Y + 1750, db='2.5'), 2200, Y + 1750)
flick = b.add(b.add(b.mul(b.sin(b.mul(h, None, 1800, Y + 1900, db='23.0'), 2000, Y + 1900), None, 2200, Y + 1900, db='0.08'),
                    b.mul(b.sin(b.mul(h, None, 1800, Y + 2000, db='61.3'), 2000, Y + 2000), None, 2200, Y + 2000, db='0.06'), 2400, Y + 1950), None, 2600, Y + 1950, db='0.86')
inten = b.mul(b.mul(b.mul(g('FlareCd', DBL, 2400, Y + 1600), ramp, 2600, Y + 1600), fade, 2800, Y + 1650), flick, 3000, Y + 1750)
lv = b.branch(b.valid(g('Light', OBJV(PLC), 2400, Y + 300), 2550, Y + 300), 2500, Y + 100, tag='IfLight'); G.link(mv2, 'then', lv, 'execute')
si = b.call(CLS('LightComponent'), 'SetIntensity', [fl('NewIntensity', default='0.0')], 2800, Y + 100, target=g('Light', OBJV(PLC), 2650, Y + 400), tag='Flicker')
b.wire(inten, si, 'NewIntensity'); G.link(lv, 'then', si, 'execute')
mg2 = b.seq('AfterLight', 1, 3100, Y + 100); G.link(lv, 'else', mg2, 'execute'); G.link(si, 'then', mg2, 'execute')
be = b.branch(b.dcmp('GreaterEqual_DoubleDouble', h, life, 3300, Y + 300), 3300, Y + 100, tag='IfBurntOut'); G.link(mg2, 'then_0', be, 'execute')
ds = b.call_self('K2_DestroyActor', [], 3600, Y + 100, ACT, tag='Destroy'); G.link(be, 'then', ds, 'execute')
write(G, 'BP_Flare_graph.txt')
VARS_F = [('Target', 'vector', '0,0,0', 'set by BPC_Flares right after the spawn: the spotted threat'), ('Start', 'vector', '0,0,0', 'launch point'),
          ('T0', 'real', '0.0', 'game time of the launch'), ('Lit', 'bool', 'false', 'ignited'), ('Life', 'real', '26.0', 'seconds it burns'),
          ('FlareHeight', 'real', '2200.0', 'cm over the target where it ignites'), ('FlareCd', 'real', '3500.0', 'light candela at full burn'),
          ('Light', 'obj:PointLightComponent', '', 'its light (tag FlareLight)')]

# ================================================================================================= BPC_Flares
G = Graph(); b = B7(G, 'fx')
g = b.get
event_override(G, 'BP', COMP, 'ReceiveBeginPlay', [], 0, 0)
fd = b.actor_of_(P_DN, DNC, 300, 0); G.link('BP', 'then', fd, 'execute')
sdn = b.set('DN', OBJV(DNC), (fd, 'ReturnValue'), 600, 0); G.link(fd, 'then', sdn, 'execute')
hs = b.lib(GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 800, 300, pure=True, tag='HasSave')
bl = b.branch((hs, 'ReturnValue'), 900, 0, tag='IfSave'); G.link(sdn, 'then', bl, 'execute')
ld = b.lib(GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', SAVEG, out=True)], 1200, -200, tag='Load')
G.link(bl, 'then', ld, 'execute')
cast(G, 'fxAsLoad', SAVEC, 'AsBP Castle Save', 1500, -200); b.wire((ld, 'ReturnValue'), 'fxAsLoad', 'Object'); G.link(ld, 'then', 'fxAsLoad', 'execute')
dat = b.getm('Data', SAVEC, arr(D('Data')), ('fxAsLoad', 'AsBP Castle Save'), 1700, 100)
dl = 'fxDataLen'
G.node(dl, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 1900, 250)
b.wire(dat, dl, 'TargetArray')
bd = b.branch(b.icmp('Greater_IntInt', (dl, 'ReturnValue'), None, 2100, 250, db='0'), 1800, -200, tag='IfData'); G.link('fxAsLoad', 'then', bd, 'execute')
so = b.set('Owned', BOOL, b.dcmp('Greater_DoubleDouble', b.item(dat, D('v'), None, 2100, 400), None, 2300, 400, db='0.5'), 2100, -200)
G.link(bd, 'then', so, 'execute')
mg = b.seq('AfterLoad', 1, 2500, 0)
for src, pin in ((bl, 'else'), ('fxAsLoad', 'CastFailed'), (bd, 'else'), (so, 'then')): G.link(src, pin, mg, 'execute')
t1 = b.timer_ev('FlarePoll', '1.0', 2800, 0); G.link(mg, 'then_0', t1, 'execute')
t2 = b.timer_ev('FlareKeys', '0.05', 3100, 0); G.link(t1, 'then', t2, 'execute')

# ---- SaveNow: Data = [Owned]
Y = 900
b.event('SaveNow', [], 0, Y)
cs = b.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SAVEG, '/Game/CastleDefender/Gameplay/Save/BP_CastleSave.BP_CastleSave_C'), ob('ReturnValue', SAVEG, out=True)], 300, Y, tag='NewSave')
G.link('SaveNow', 'then', cs, 'execute')
cast(G, 'fxAsSave', SAVEC, 'AsBP Castle Save', 600, Y); b.wire((cs, 'ReturnValue'), 'fxAsSave', 'Object'); G.link(cs, 'then', 'fxAsSave', 'execute')
mk = b.name('MakeData'); G.node(mk, 'K2Node_MakeArray', ['NumInputs=1'], [D('[0]', default='0.0'), arr(D('Array', out=True))], 800, Y + 300)
b.wire(b.math('Conv_BoolToDouble', [(bo('InBool', default='false'), g('Owned', BOOL, 500, Y + 400))], D('ReturnValue', out=True), 650, Y + 400), mk, '[0]')
sd = b.setm('Data', SAVEC, arr(D('Data')), (mk, 'Array'), ('fxAsSave', 'AsBP Castle Save'), 1000, Y); G.link('fxAsSave', 'then', sd, 'execute')
sv = b.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SAVEG), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 1300, Y, tag='Save')
b.wire(('fxAsSave', 'AsBP Castle Save'), sv, 'SaveGameObject'); G.link(sd, 'then', sv, 'execute')

# ---- FlareKeys (0.05 s): F at the barracks buys the upgrade
Y = 1700
b.event('FlareKeys', [], 0, Y)
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='F'), bo('ReturnValue', out=True, default='false')], 200, Y + 300, target=b.pc(0, Y + 300), pure=True, const=True, tag='KeyF')
pr = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('FWas', BOOL, 300, Y + 450), 500, Y + 450), 700, Y + 400),
          b.b2('BooleanAND', g('NearShop', BOOL, 500, Y + 550), b.bnot(g('Owned', BOOL, 500, Y + 650), 700, Y + 650), 900, Y + 600), 1100, Y + 500)
sfw = b.set('FWas', BOOL, (down, 'ReturnValue'), 300, Y); G.link('FlareKeys', 'then', sfw, 'execute')
bp_ = b.branch(pr, 600, Y, tag='IfBuy'); G.link(sfw, 'then', bp_, 'execute')
zc, zh = b.hud_cast(ZHUDC, 'BP Zombie HUD', 900, Y); G.link(bp_, 'then', zc, 'execute')
price = lambda x, y: g('Price', it('v', default='400'), x, y)
gold = lambda x, y: b.getm('Gold', ZHUDC, INT, zh, x, y)
bg = b.branch(b.icmp('GreaterEqual_IntInt', gold(1200, Y + 300), price(1200, Y + 400), 1400, Y + 350), 1250, Y, tag='IfGold'); G.link(zc, 'then', bg, 'execute')
pay = b.setm('Gold', ZHUDC, INT, b.i2('Subtract_IntInt', gold(1500, Y + 450), price(1500, Y + 550), 1700, Y + 500), zh, 1550, Y - 200)
G.link(bg, 'then', pay, 'execute')
own = b.set('Owned', bo('v', default='true'), None, 1850, Y - 200); G.link(pay, 'then', own, 'execute')
save = b.call_self('SaveNow', [], 2100, Y - 200, CLS('ActorComponent'), tag='CallSave'); G.link(own, 'then', save, 'execute')
n1c, _ = b.notice('Your crossbowmen now carry flares (-400 gold). At night they light up the threats they spot.', 2500, Y - 200); G.link(save, 'then', n1c, 'execute')
n2c, _ = b.notice('Not enough gold: crossbow flares cost 400.', 1700, Y + 200); G.link(bg, 'else', n2c, 'execute')

# ---- FlarePoll (1 s)
Y = 2700
b.event('FlarePoll', [], 0, Y)
seq = b.seq('PollSeq', 2, 200, Y); G.link('FlarePoll', 'then', seq, 'execute')
now = b.now(200, Y + 2000)
# then_0: barracks prompt
fn = b.actor_of_(P_NPC, NPCC, 500, Y); G.link(seq, 'then_0', fn, 'execute')
npc = (fn, 'ReturnValue')
near = b.b2('BooleanAND', b.b2('BooleanAND', b.valid(npc, 700, Y + 300), b.bnot(g('Owned', BOOL, 700, Y + 400), 900, Y + 400), 1100, Y + 350),
            b.dcmp('Less_DoubleDouble', b.dist2d(b.loc(b.owner(700, Y + 550), 900, Y + 550), b.loc(npc, 900, Y + 650), 1100, Y + 600), None, 1300, Y + 600, db='450.0'), 1500, Y + 450)
first = b.b2('BooleanAND', near, b.bnot(g('NearShop', BOOL, 1500, Y + 600), 1700, Y + 600), 1900, Y + 550)
bf = b.branch(first, 800, Y, tag='IfShopPrompt'); G.link(fn, 'then', bf, 'execute')
n3c, n3 = b.notice(SHOP_TEXT, 1100, Y - 200); G.link(bf, 'then', n3c, 'execute')
sns = b.set('NearShop', BOOL, near, 1700, Y)
for src, pin in ((bf, 'else'), (n3, 'then'), (n3c, 'CastFailed')): G.link(src, pin, sns, 'execute')

# then_1: fire at a spotted threat
X = 400; Y1 = Y + 1200
dn = g('DN', OBJV(DNC), X, Y1 + 300)
ready = b.b2('BooleanAND', b.b2('BooleanAND', g('Owned', BOOL, X, Y1 + 200), b.valid(dn, X + 150, Y1 + 300), X + 350, Y1 + 250),
             b.b2('BooleanAND', b.getm('IsNight', DNC, BOOL, g('DN', OBJV(DNC), X, Y1 + 450), X + 150, Y1 + 450),
                  b.dcmp('GreaterEqual_DoubleDouble', now, g('NextFlare', DBL, X, Y1 + 550), X + 150, Y1 + 550), X + 350, Y1 + 500), X + 550, Y1 + 400)
br = b.branch(ready, X + 300, Y1, tag='IfReady'); G.link(seq, 'then_1', br, 'execute')
gf = b.getall(P_FLARE, FLAREC, X + 600, Y1); G.link(br, 'then', gf, 'execute')
gx = b.getall(P_XBOW, XBOWC, X + 900, Y1); G.link(gf, 'then', gx, 'execute')
nx = b.count(gx, X + 1100, Y1 + 400)
ok = b.b2('BooleanAND', b.icmp('Less_IntInt', b.count(gf, X + 1100, Y1 + 300), g('MaxFlares', it('v', default='3'), X + 1100, Y1 + 500), X + 1300, Y1 + 350),
          b.icmp('Greater_IntInt', nx, None, X + 1300, Y1 + 450, db='0'), X + 1500, Y1 + 400)
bo_ = b.branch(ok, X + 1200, Y1, tag='IfRoom'); G.link(gx, 'then', bo_, 'execute')
ri = b.math('RandomIntegerInRange', [(it('Min', default='0'), None), (it('Max', default='0'), b.i2('Subtract_IntInt', nx, None, X + 1500, Y1 + 600, db='1'))], it('ReturnValue', out=True), X + 1700, Y1 + 600)
ssh = b.set('Shooter', OBJV(ACT), b.item((gx, 'OutActors'), ob('v', XBOWC), ri, X + 1900, Y1 + 550), X + 1500, Y1)
G.link(bo_, 'then', ssh, 'execute')
sbs = b.set('BestScore', D('v', default='-1000000000.0'), None, X + 1800, Y1)
sfo = b.set('Found', BOOL, None, X + 2050, Y1)
b.chain(ssh, sbs, sfo)
gz = b.getall('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', ZOMBIE, X + 2300, Y1); G.link(sfo, 'then', gz, 'execute')
fe = b.foreach(ZOMBIE, X + 2650, Y1); G.link(gz, 'then', fe, 'Exec'); b.wire((gz, 'OutActors'), fe, 'Array')
z = (fe, 'Array Element')
shooter = lambda x, y: g('Shooter', OBJV(ACT), x, y)
d = b.dist2d(b.loc(shooter(X + 2700, Y1 + 400), X + 2900, Y1 + 400), b.loc(z, X + 2900, Y1 + 500), X + 3100, Y1 + 450)
oc = b.lib(GS, 'GetObjectClass', [ob('Object', OBJ), {'name': 'ReturnValue', 'cat': 'class', 'obj': OBJ, 'out': True}], X + 2900, Y1 + 700, pure=True, tag='ZClass')
b.wire(z, oc, 'Object')
iswb = b.math('ClassIsChildOf', [({'name': 'TestClass', 'cat': 'class', 'obj': OBJ}, (oc, 'ReturnValue')),
                                 ({'name': 'ParentClass', 'cat': 'class', 'obj': OBJ, 'dobj': cpath(P_WB)}, None)], bo('ReturnValue', out=True), X + 3100, Y1 + 700)
score = b.add(b.mul(d, None, X + 3300, Y1 + 450, db='-1.0'), b.self_(None, None, iswb, X + 3300, Y1 + 700, da='4000.0', db='0.0'), X + 3500, Y1 + 550)
inr = b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', d, g('SightRange', DBL, X + 3300, Y1 + 850), X + 3500, Y1 + 850),
           b.dcmp('Less_DoubleDouble', d, g('SpotRange', DBL, X + 3300, Y1 + 950), X + 3500, Y1 + 950), X + 3700, Y1 + 900)
better = b.b2('BooleanAND', inr, b.dcmp('Greater_DoubleDouble', score, g('BestScore', DBL, X + 3500, Y1 + 1050), X + 3700, Y1 + 1050), X + 3900, Y1 + 950)
bb = b.branch(better, X + 3000, Y1, tag='IfBetter'); G.link(fe, 'LoopBody', bb, 'execute')
s1 = b.set('BestScore', DBL, score, X + 3300, Y1 - 200); s2 = b.set('BestLoc', V('v'), b.loc(z, X + 3400, Y1 - 400), X + 3550, Y1 - 200)
s3 = b.set('Found', bo('v', default='true'), None, X + 3800, Y1 - 200)
G.link(bb, 'then', s1, 'execute'); b.chain(s1, s2, s3)
# already lit? any burning flare within LitRadius of the spot cancels
fe2 = b.foreach(FLAREC, X + 4200, Y1); G.link(fe, 'Completed', fe2, 'Exec'); b.wire((gf, 'OutActors'), fe2, 'Array')
litc = b.dcmp('Less_DoubleDouble', b.dist2d(b.loc((fe2, 'Array Element'), X + 4300, Y1 + 400), g('BestLoc', V('v'), X + 4300, Y1 + 500), X + 4500, Y1 + 450),
              g('LitRadius', DBL, X + 4500, Y1 + 600), X + 4700, Y1 + 500)
bl2 = b.branch(litc, X + 4500, Y1, tag='IfLit'); G.link(fe2, 'LoopBody', bl2, 'execute')
nf = b.set('Found', BOOL, None, X + 4800, Y1 - 200); G.link(bl2, 'then', nf, 'execute')
bfi = b.branch(g('Found', BOOL, X + 4500, Y1 + 800), X + 4700, Y1 + 600, tag='IfFire'); G.link(fe2, 'Completed', bfi, 'execute')
start = b.v2('Add_VectorVector', b.loc(shooter(X + 4800, Y1 + 900), X + 5000, Y1 + 900), None, X + 5200, Y1 + 900, db='0.000000,0.000000,160.000000')
sp = spawn(b, P_FLARE, FLAREC, transform(b, start, X + 5400, Y1 + 900), X + 5000, Y1 + 600); G.link(bfi, 'then', sp, 'execute')
stg = b.setm('Target', FLAREC, V('v'), g('BestLoc', V('v'), X + 5300, Y1 + 1100), (sp, 'ReturnValue'), X + 5400, Y1 + 600); G.link(sp, 'then', stg, 'execute')
snf = b.set('NextFlare', DBL, b.add(now, g('FlareGap', DBL, X + 5500, Y1 + 1000), X + 5700, Y1 + 950), X + 5700, Y1 + 600); G.link(stg, 'then', snf, 'execute')
write(G, 'BPC_Flares_graph.txt')
VARS_C = [('Owned', 'bool', 'false', 'FLARES upgrade bought (saved, slot CastleSaveFlares)'), ('Price', 'int', '400', 'gold'),
          ('NearShop', 'bool', 'false', 'hero is at the barracks and can buy (prompt shown)'), ('FWas', 'bool', 'false', 'F held last check'),
          ('DN', 'obj:BP_DayNight', '', 'BP_DayNight'), ('NextFlare', 'real', '0.0', 'game time the next flare may go up'),
          ('FlareGap', 'real', '6.0', 's between two flares'), ('MaxFlares', 'int', '3', 'flares burning at once'),
          ('SightRange', 'real', '1400.0', 'cm: closer threats are seen anyway (no flare)'), ('SpotRange', 'real', '6000.0', 'cm: how far a crossbowman spots'),
          ('LitRadius', 'real', '2500.0', 'cm: a burning flare this close already lights the spot'),
          ('Shooter', 'obj:Actor', '', 'the crossbowman picked this poll'), ('BestScore', 'real', '0.0', 'scratch'), ('BestLoc', 'vector', '0,0,0', 'scratch'),
          ('Found', 'bool', 'false', 'scratch')]


# ================================================================================================= BPVar lines
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('int', 'bool'): return 'PinCategory="%s"' % kind
    if kind == 'vector': return 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
    if kind == 'obj:BP_DayNight': return 'PinCategory="object",PinSubCategoryObject="/Script/Engine.BlueprintGeneratedClass\'%s.BP_DayNight_C\'"' % P_DN
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda bp, n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'flares277/%s/%s' % (bp, n)).hex.upper(), vt(k), n, d)
out = ['# #277 Crossbow flares - paste one line at a time on the VARIABLES header of My Blueprint, then Compile', '', '# ---- BP_Flare']
out += [bpv('BP_Flare', *v[:3]) for v in VARS_F] + ['', '# ---- BPC_Flares'] + [bpv('BPC_Flares', *v[:3]) for v in VARS_C]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #277 variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bp, vs in (('BP_Flare', VARS_F), ('BPC_Flares', VARS_C)):
        for n, _k, d, m in vs: f.write('| %s | %s | %s | %s |\n' % (bp, n, d or '-', m))
print('BPVar lines: %d + %d' % (len(VARS_F), len(VARS_C)))
