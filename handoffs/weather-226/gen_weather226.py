# #226 Weather (adjustedfilm, 2026-10-31): EventGraph of the hero component BPC_Weather ("Weather" on the hero).
#   "<blender python>" -I gen_weather226.py  ->  BPC_Weather_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# Weather kinds: 0 clear, 1 rain, 2 fog, 3 storm (rain + wind + lightning). Day 1 is clear; every dawn (BP_DayNight.IsNight
# true -> false) Today = Tomorrow and a new Tomorrow is rolled (clear 50 %, rain 20 %, fog 15 %, storm 15 %). Notices:
# dawn "Weather today: Rain", dusk "Tomorrow: Storm" (the forecast line).
# WxTick (0.1 s): Rain / Fog / Storm ease toward today's target over BlendSec (20 s), then
#   MPC_Weather  Rain, Fog, Storm, Wind (0.15 + 0.85 storm), Wet (wets in 60 s of rain, dries in 120 s), Flash (lightning)
#   BP_DayNight  FogDay = FogBase x (1 + 1.5 rain + 5 fog + 1.5 storm)   (its own fog code does the rest, day and night)
#   rain curtain follows the camera, hidden when dry; rain loop volume follows Rain
#   wind source (cloth banners / capes): strength 0.1 -> 1.0, speed 0.2 -> 1.0 with the storm (one wind field, rule 10)
#   lightning: storm > 0.6 -> a bolt every 6-18 s: double flicker in MPC Flash, thunder 0.8-3 s later (A close / B far)
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP = CLS('ActorComponent')
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
P_DN = '/Game/CastleDefender/Environment/DayNight/BP_DayNight'
P_RC = '/Game/CastleDefender/Environment/Weather/BP_RainCurtain'
P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
WX = '/Game/CastleDefender/Environment/Weather/'
MPC = WX + 'MPC_Weather.MPC_Weather'
DNC, RCC, NOTC = BPC(P_DN, 'BP_DayNight'), BPC(P_RC, 'BP_RainCurtain'), BPC(P_NOTICE, 'BP_NoticeHUD')
WINDA, WINDC = CLS('WindDirectionalSource'), CLS('WindDirectionalSourceComponent')
AUDC, SOUND, PCM, HUDCLS = CLS('AudioComponent'), CLS('SoundBase'), CLS('PlayerCameraManager'), CLS('HUD')
OBJV = lambda c: ob('v', c)
NAMES = ['Clear', 'Rain', 'Fog', 'Storm']


class B6(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def exp(s, a, x, y): return s.math('Exp', [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
    def b2d(s, a, x, y): return s.math('Conv_BoolToDouble', [(bo('InBool', default='false'), a)], D('ReturnValue', out=True), x, y)
    def eqi(s, a, v, x, y): return s.icmp('EqualEqual_IntInt', a, None, x, y, db=str(v))
    def seli(s, a, c, pick, x, y, da='0', db='0'):
        return s.math('SelectInt', [(it('A', default=da), a), (it('B', default=db), c), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)
    def roll(s, x, y):
        """weighted weather roll: 0 clear 50 %, 1 rain 20 %, 2 fog 15 %, 3 storm 15 % (thresholds are variables)."""
        r = s.rnd('0.0', '1.0', x, y)
        lt = lambda var, yy: s.dcmp('Less_DoubleDouble', r, s.get(var, DBL, x + 200, yy), x + 400, yy)
        return s.seli(None, s.seli(None, s.seli(None, None, lt('PFog', y + 300), x + 600, y + 300, da='2', db='3'),
                                   lt('PRain', y + 200), x + 800, y + 200, da='1'), lt('PClear', y + 100), x + 1000, y + 100, da='0')
    def name_of(s, kind, x, y):
        sel = None
        for i in range(3, 0, -1):
            sel = s.selstr(None, sel, s.eqi(kind, i, x, y + 100 * i), x + 200 + 200 * (3 - i), y + 100 * i, da=NAMES[i], db=NAMES[0] if sel is None else '')
        return sel
    def mpc_set(s, param, val, x, y):
        n = s.name('Set' + param)
        callfn(s.G, n, MATL, 'SetScalarParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), {'name': 'ParameterName', 'cat': 'name', 'default': param},
               fl('ParameterValue', default='0.0')], x=x, y=y, self_hidden=True)
        s.wire(val, n, 'ParameterValue'); return n
    def notice(s, text_src, x, y):
        pcn = s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x - 300, y + 300, pure=True, tag='PC')
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x - 100, y + 300, target=(pcn, 'ReturnValue'), pure=True, const=True, tag='HUD')
        nc = s.name('AsNoticeHUD'); cast(s.G, nc, NOTC, 'AsBP Notice HUD', x, y); s.wire((hud, 'ReturnValue'), nc, 'Object')
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=''), it('Tier', default='1')], x + 300, y, target=(nc, 'AsBP Notice HUD'), tag='Notice')
        s.wire(text_src, pn, 'Text'); s.G.link(nc, 'then', pn, 'execute')
        return nc, pn
    def ease(s, var, target, x, y):
        """var += (target - var) * min(1, 0.1 / BlendSec) -> set node"""
        cur = s.get(var, DBL, x, y + 200)
        k = s.math('FMin', [(D('A', default='1.0'), None), (D('B', default='0.0'), s.d2('Divide_DoubleDouble', None, s.get('BlendSec', DBL, x, y + 400), x + 200, y + 400, da='0.1'))],
                   D('ReturnValue', out=True), x + 400, y + 400)
        nv = s.add(cur, s.mul(s.sub(target, cur, x + 200, y + 250), k, x + 600, y + 300), x + 800, y + 250)
        return s.set(var, DBL, nv, x + 200, y)


G = Graph(); b = B6(G, 'wx')
g = b.get
dn = lambda x, y: g('DN', OBJV(DNC), x, y)

# ================================================================================================= BeginPlay
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
fd = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_DN)), ob('ReturnValue', DNC, out=True)], 300, 0, tag='FindDayNight')
G.link('BP', 'then', fd, 'execute')
sdn = b.set('DN', OBJV(DNC), (fd, 'ReturnValue'), 600, 0); G.link(fd, 'then', sdn, 'execute')
vd = b.branch(b.valid(dn(700, 250), 850, 250), 900, 0, tag='IfDN'); G.link(sdn, 'then', vd, 'execute')
sfb = b.set('FogBase', DBL, b.getm('FogDay', DNC, DBL, dn(1000, 300), 1150, 300), 1200, -200); G.link(vd, 'then', sfb, 'execute')
swn = b.set('WasNight', BOOL, b.getm('IsNight', DNC, BOOL, dn(1250, 450), 1400, 450), 1450, -200); G.link(sfb, 'then', swn, 'execute')
mg = b.seq('AfterDN', 1, 1750, 0); G.link(vd, 'else', mg, 'execute'); G.link(swn, 'then', mg, 'execute')
xf0 = transform(b, None, 2000, 300)
sc = spawn(b, P_RC, RCC, xf0, 2000, 0); G.link(mg, 'then_0', sc, 'execute')
scu = b.set('Curtain', OBJV(ACT), (sc, 'ReturnValue'), 2350, 0); G.link(sc, 'then', scu, 'execute')
hid = b.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='true')], 2650, 0, target=g('Curtain', OBJV(ACT), 2500, 250), tag='HideCurtain')
G.link(scu, 'then', hid, 'execute')
# wind source (native class)
sw = b.name('SpawnWind')
G.node(sw, 'K2Node_SpawnActorFromClass', ['AdvancedPinDisplay=Hidden'],
       [ex(), ex('then', True), CLSPIN('Class', ACT, '/Script/Engine.WindDirectionalSource'), ob('ReturnValue', WINDA, out=True), st('SpawnTransform', XFORM),
        {'name': 'CollisionHandlingOverride', 'cat': 'byte', 'obj': ENUM('ESpawnActorCollisionHandlingMethod'), 'default': 'AlwaysSpawn'},
        {'name': 'TransformScaleMethod', 'cat': 'byte', 'obj': ENUM('ESpawnActorScaleMethod'), 'default': 'SelectDefaultAtRuntime', 'advanced': True},
        dict(ob('Owner', ACT), advanced=True), ob('Instigator', PAWN)], 2950, 0)
wrot = b.math('MakeTransform', [(V('Location'), None), (st('Rotation', ROT, default='0.000000,35.000000,0.000000'), None), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
              st('ReturnValue', XFORM, out=True), 2800, 300)
b.wire(wrot, sw, 'SpawnTransform'); G.link(hid, 'then', sw, 'execute')
sws = b.set('Wind', OBJV(WINDA), (sw, 'ReturnValue'), 3300, 0); G.link(sw, 'then', sws, 'execute')
au = b.lib(GS, 'SpawnSound2D', [WC(), dict(ob('Sound', SOUND), dobj=WX + 'SFX_Rain_Loop.SFX_Rain_Loop'), fl('VolumeMultiplier', default='0.010000'),
           fl('PitchMultiplier', default='1.000000'), fl('StartTime', default='0.000000'), bo('bPersistAcrossLevelTransition', default='false'),
           bo('bAutoDestroy', default='false'), ob('ReturnValue', AUDC, out=True)], 3600, 0, tag='RainLoop')
G.link(sws, 'then', au, 'execute')
sau = b.set('RainAudio', OBJV(AUDC), (au, 'ReturnValue'), 3950, 0); G.link(au, 'then', sau, 'execute')
st0 = b.set('Tomorrow', INT, b.roll(4000, 300), 4250, 0); G.link(sau, 'then', st0, 'execute')
tm = b.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default='WxTick'), fl('Time', default='0.1'), bo('bLooping', default='true'),
                                fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                st('ReturnValue', TIMERH, out=True)], 4550, 0, tag='TimerWx')
b.wire(b.self_node(4400, 200), tm, 'Object'); G.link(st0, 'then', tm, 'execute')

# ================================================================================================= WxTick
Y = 1400
b.event('WxTick', [], 0, Y)
seq = b.seq('WxSeq', 5, 200, Y); G.link('WxTick', 'then', seq, 'execute')
now = b.now(200, Y + 2400)

# ---- then_0: dawn / dusk
X = 500
vdn = b.branch(b.valid(dn(X, Y + 250), X + 150, Y + 250), X + 200, Y, tag='IfDN2'); G.link(seq, 'then_0', vdn, 'execute')
night = b.getm('IsNight', DNC, BOOL, dn(X + 300, Y + 400), X + 450, Y + 400)
was = g('WasNight', BOOL, X + 450, Y + 500)
dawn = b.b2('BooleanAND', was, b.bnot(night, X + 650, Y + 450), X + 850, Y + 450)
dusk = b.b2('BooleanAND', b.bnot(was, X + 650, Y + 550), night, X + 850, Y + 550)
bdw = b.branch(dawn, X + 500, Y, tag='IfDawn'); G.link(vdn, 'then', bdw, 'execute')
stoday = b.set('Today', INT, g('Tomorrow', INT, X + 700, Y - 250), X + 800, Y - 200); G.link(bdw, 'then', stoday, 'execute')
stom = b.set('Tomorrow', INT, b.roll(X + 900, Y - 450), X + 1100, Y - 200); G.link(stoday, 'then', stom, 'execute')
nc1, _ = b.notice(b.concat(None, b.name_of(g('Today', INT, X + 1300, Y - 500), X + 1400, Y - 600), X + 2200, Y - 500, da='Weather today: '), X + 1700, Y - 200)
G.link(stom, 'then', nc1, 'execute')
bdk = b.branch(dusk, X + 2400, Y, tag='IfDusk'); G.link(bdw, 'else', bdk, 'execute')
nc2, _ = b.notice(b.concat(None, b.name_of(g('Tomorrow', INT, X + 2600, Y - 500), X + 2700, Y - 600), X + 3500, Y - 500, da='Forecast for tomorrow: '), X + 2900, Y - 200)
G.link(bdk, 'then', nc2, 'execute')
swn2 = b.set('WasNight', BOOL, night, X + 3800, Y + 200)
G.link(bdk, 'else', swn2, 'execute'); G.link(nc1, 'CastFailed', swn2, 'execute'); G.link(nc2, 'CastFailed', swn2, 'execute')
G.link(nc1 + '' if False else [n for n in G.nodes if n[0].startswith('wxNotice')][0][0], 'then', swn2, 'execute')
G.link([n for n in G.nodes if n[0].startswith('wxNotice')][1][0], 'then', swn2, 'execute')

# ---- then_1: ease the three channels, wetness
X = 500; Y1 = Y + 1200
today = lambda x, y: g('Today', INT, x, y)
rain_t = b.b2d(b.b2('BooleanOR', b.eqi(today(X, Y1 + 600), 1, X + 200, Y1 + 600), b.eqi(today(X, Y1 + 700), 3, X + 200, Y1 + 700), X + 400, Y1 + 650), X + 600, Y1 + 650)
e1 = b.ease('CurRain', rain_t, X + 800, Y1)
e2 = b.ease('CurFog', b.b2d(b.eqi(today(X + 1600, Y1 + 600), 2, X + 1800, Y1 + 600), X + 2000, Y1 + 600), X + 2200, Y1)
e3 = b.ease('CurStorm', b.b2d(b.eqi(today(X + 3000, Y1 + 600), 3, X + 3200, Y1 + 600), X + 3400, Y1 + 600), X + 3600, Y1)
G.link(seq, 'then_1', e1, 'execute'); b.chain(e1, e2, e3)
rain = lambda x, y: g('CurRain', DBL, x, y)
fog = lambda x, y: g('CurFog', DBL, x, y)
storm = lambda x, y: g('CurStorm', DBL, x, y)
wet = g('Wet', DBL, X + 4400, Y1 + 300)
dw = b.self_(None, None, b.dcmp('Greater_DoubleDouble', rain(X + 4400, Y1 + 450), None, X + 4600, Y1 + 450, db='0.3'), X + 4800, Y1 + 400,
             da='%.6f' % (0.1 / 60.0), db='%.6f' % (-0.1 / 120.0))
swt = b.set('Wet', DBL, b.sat(b.add(wet, dw, X + 5000, Y1 + 350), X + 5200, Y1 + 350), X + 4600, Y1); G.link(e3, 'then', swt, 'execute')

# ---- then_2: lightning + thunder
X = 500; Y2 = Y + 2600
bolt = b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', storm(X, Y2 + 300), None, X + 200, Y2 + 300, db='0.6'),
            b.dcmp('GreaterEqual_DoubleDouble', now, g('NextBolt', DBL, X, Y2 + 450), X + 200, Y2 + 450), X + 400, Y2 + 350)
bb = b.branch(bolt, X + 300, Y2, tag='IfBolt'); G.link(seq, 'then_2', bb, 'execute')
sft = b.set('FlashT0', DBL, now, X + 600, Y2 - 200)
snb = b.set('NextBolt', DBL, b.add(now, b.rnd('6.0', '18.0', X + 700, Y2 - 400), X + 900, Y2 - 350), X + 850, Y2 - 200)
sth = b.set('ThunderAt', DBL, b.add(now, b.rnd('0.8', '3.0', X + 1000, Y2 - 400), X + 1200, Y2 - 350), X + 1100, Y2 - 200)
G.link(bb, 'then', sft, 'execute'); b.chain(sft, snb, sth)
mgb = b.seq('AfterBolt', 1, X + 1400, Y2); G.link(bb, 'else', mgb, 'execute'); G.link(sth, 'then', mgb, 'execute')
tha = g('ThunderAt', DBL, X + 1500, Y2 + 300)
bt = b.branch(b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', tha, None, X + 1700, Y2 + 300, db='0.0'), b.dcmp('GreaterEqual_DoubleDouble', now, tha, X + 1700, Y2 + 400),
              X + 1900, Y2 + 350), X + 1700, Y2, tag='IfThunder')
G.link(mgb, 'then_0', bt, 'execute')
close = b.math('RandomBool', [], bo('ReturnValue', out=True), X + 1900, Y2 + 600)
# a close strike (A) or a far one (B)
bc = b.branch(close, X + 2000, Y2 - 200, tag='IfClose'); G.link(bt, 'then', bc, 'execute')
pa = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', SOUND), dobj=WX + 'SFX_Thunder_A.SFX_Thunder_A'), fl('VolumeMultiplier', default='0.900000')], X + 2300, Y2 - 400, tag='ThunderA')
pb = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', SOUND), dobj=WX + 'SFX_Thunder_B.SFX_Thunder_B'), fl('VolumeMultiplier', default='0.700000')], X + 2300, Y2 - 100, tag='ThunderB')
G.link(bc, 'then', pa, 'execute'); G.link(bc, 'else', pb, 'execute')
st0b = b.set('ThunderAt', DBL, None, X + 2600, Y2 - 200); G.link(pa, 'then', st0b, 'execute'); G.link(pb, 'then', st0b, 'execute')

# ---- then_3: MPC + fog + curtain + wind + audio
X = 500; Y3 = Y + 4200
t_ = b.sub(now, g('FlashT0', DBL, X, Y3 + 600), X + 200, Y3 + 600)
e_a = b.exp(b.mul(t_, None, X + 400, Y3 + 600, db='-16.0'), X + 600, Y3 + 600)
e_b = b.mul(b.mul(b.exp(b.mul(b.math('FMax', [(D('A', default='0.0'), b.sub(t_, None, X + 400, Y3 + 700, db='0.14')), (D('B', default='0.0'), None)], D('ReturnValue', out=True), X + 600, Y3 + 700),
                              None, X + 800, Y3 + 700, db='-18.0'), X + 1000, Y3 + 700), b.b2d(b.dcmp('Greater_DoubleDouble', t_, None, X + 800, Y3 + 800, db='0.14'), X + 1000, Y3 + 800),
              X + 1200, Y3 + 750), None, X + 1400, Y3 + 750, db='0.6')
inwin = b.b2d(b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', t_, None, X + 800, Y3 + 900), b.dcmp('Less_DoubleDouble', t_, None, X + 800, Y3 + 1000, db='0.8'), X + 1000, Y3 + 950), X + 1200, Y3 + 950)
flash = b.mul(b.mul(b.add(e_a, e_b, X + 1600, Y3 + 650), inwin, X + 1800, Y3 + 700), storm(X + 1800, Y3 + 850), X + 2000, Y3 + 750)
windv = b.add(b.mul(storm(X, Y3 + 1100), None, X + 200, Y3 + 1100, db='0.85'), None, X + 400, Y3 + 1100, db='0.15')
chain = []
XX = X + 300
for prm, val in (('Rain', rain(XX, Y3 + 300)), ('Fog', fog(XX + 300, Y3 + 300)), ('Storm', storm(XX + 600, Y3 + 300)), ('Wind', windv), ('Wet', g('Wet', DBL, XX + 1200, Y3 + 300)), ('Flash', flash)):
    chain.append(b.mpc_set(prm, val, XX, Y3)); XX += 300
G.link(seq, 'then_3', chain[0], 'execute'); b.chain(*chain)
# fog through BP_DayNight's own variable
vdn3 = b.branch(b.valid(dn(XX, Y3 + 250), XX + 150, Y3 + 250), XX + 100, Y3, tag='IfDN3'); G.link(chain[-1], 'then', vdn3, 'execute')
mult = b.add(b.add(b.add(b.mul(rain(XX, Y3 + 500), None, XX + 200, Y3 + 500, db='1.5'), b.mul(fog(XX, Y3 + 600), None, XX + 200, Y3 + 600, db='5.0'), XX + 400, Y3 + 550),
                   b.mul(storm(XX, Y3 + 700), None, XX + 200, Y3 + 700, db='1.5'), XX + 600, Y3 + 600), None, XX + 800, Y3 + 600, db='1.0')
sfog = b.setm('FogDay', DNC, DBL, b.mul(g('FogBase', DBL, XX + 800, Y3 + 750), mult, XX + 1000, Y3 + 700), dn(XX + 300, Y3 + 300), XX + 400, Y3)
G.link(vdn3, 'then', sfog, 'execute')
mg3 = b.seq('AfterFog', 1, XX + 700, Y3); G.link(vdn3, 'else', mg3, 'execute'); G.link(sfog, 'then', mg3, 'execute')
XX += 1000
cur = lambda x, y: g('Curtain', OBJV(ACT), x, y)
vc = b.branch(b.valid(cur(XX, Y3 + 250), XX + 150, Y3 + 250), XX + 100, Y3, tag='IfCurtain'); G.link(mg3, 'then_0', vc, 'execute')
cm = b.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCM, out=True)], XX, Y3 + 400, pure=True, tag='Cam')
cl = b.call(PCM, 'GetCameraLocation', [V('ReturnValue', out=True)], XX + 200, Y3 + 400, target=(cm, 'ReturnValue'), pure=True, const=True, tag='CamLoc')
ml = b.call(ACT, 'K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true'),
            bo('ReturnValue', out=True, default='false')], XX + 400, Y3, target=cur(XX + 250, Y3 + 250), tag='CurtainToCam')
b.wire((cl, 'ReturnValue'), ml, 'NewLocation'); G.link(vc, 'then', ml, 'execute')
hd = b.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='true')], XX + 700, Y3, target=cur(XX + 550, Y3 + 250), tag='CurtainShow')
b.wire(b.dcmp('Less_DoubleDouble', rain(XX + 550, Y3 + 400), None, XX + 700, Y3 + 400, db='0.01'), hd, 'bNewHidden'); G.link(ml, 'then', hd, 'execute')
mg4 = b.seq('AfterCurtain', 1, XX + 1000, Y3); G.link(vc, 'else', mg4, 'execute'); G.link(hd, 'then', mg4, 'execute')
XX += 1300
wnd = lambda x, y: g('Wind', OBJV(WINDA), x, y)
vw = b.branch(b.valid(wnd(XX, Y3 + 250), XX + 150, Y3 + 250), XX + 100, Y3, tag='IfWind'); G.link(mg4, 'then_0', vw, 'execute')
wc = b.getm('Component', WINDA, OBJV(WINDC), wnd(XX + 200, Y3 + 400), XX + 350, Y3 + 400)
ws = b.call(WINDC, 'SetStrength', [fl('InNewStrength', default='0.1')], XX + 400, Y3, target=wc, tag='WindStrength')
b.wire(b.add(b.mul(storm(XX + 300, Y3 + 550), None, XX + 450, Y3 + 550, db='0.9'), None, XX + 600, Y3 + 550, db='0.1'), ws, 'InNewStrength'); G.link(vw, 'then', ws, 'execute')
wsp = b.call(WINDC, 'SetSpeed', [fl('InNewSpeed', default='0.2')], XX + 700, Y3, target=wc, tag='WindSpeed')
b.wire(b.add(b.mul(storm(XX + 600, Y3 + 650), None, XX + 750, Y3 + 650, db='0.8'), None, XX + 900, Y3 + 650, db='0.2'), wsp, 'InNewSpeed'); G.link(ws, 'then', wsp, 'execute')
mg5 = b.seq('AfterWind', 1, XX + 1000, Y3); G.link(vw, 'else', mg5, 'execute'); G.link(wsp, 'then', mg5, 'execute')
XX += 1300
aud = lambda x, y: g('RainAudio', OBJV(AUDC), x, y)
va = b.branch(b.valid(aud(XX, Y3 + 250), XX + 150, Y3 + 250), XX + 100, Y3, tag='IfAudio'); G.link(mg5, 'then_0', va, 'execute')
sv = b.call(AUDC, 'SetVolumeMultiplier', [fl('NewVolumeMultiplier', default='0.01')], XX + 400, Y3, target=aud(XX + 250, Y3 + 250), tag='RainVolume')
b.wire(b.math('FMax', [(D('A', default='0.0'), b.mul(rain(XX + 300, Y3 + 400), None, XX + 450, Y3 + 400, db='0.6')), (D('B', default='0.01'), None)], D('ReturnValue', out=True),
              XX + 600, Y3 + 400), sv, 'NewVolumeMultiplier')
G.link(va, 'then', sv, 'execute')

# ================================================================================================= checks + output
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
names = [n[0] for n in G.nodes]
dup = {n for n in names if names.count(n) > 1}
if dup: raise SystemExit('duplicate names: %s' % sorted(dup)[:10])
open(os.path.join(HERE, 'BPC_Weather_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_Weather: nodes %d, links %d' % (len(G.nodes), len(G.links)))

REAL = 'PinCategory="real",PinSubCategory="double"'
OBJ_ = lambda path: 'PinCategory="object",PinSubCategoryObject="%s"' % path
VARS = [('DN', OBJ_("/Script/Engine.BlueprintGeneratedClass'%s.BP_DayNight_C'" % P_DN), '', 'BP_DayNight in the level (found at BeginPlay)'),
        ('FogBase', REAL, '0.02', "BP_DayNight's FogDay at Play (the weather multiplies it)"),
        ('Curtain', OBJ_("/Script/CoreUObject.Class'/Script/Engine.Actor'"), '', 'the rain curtain'),
        ('Wind', OBJ_("/Script/CoreUObject.Class'/Script/Engine.WindDirectionalSource'"), '', 'the storm wind source'),
        ('RainAudio', OBJ_("/Script/CoreUObject.Class'/Script/Engine.AudioComponent'"), '', 'rain loop'),
        ('Today', 'PinCategory="int"', '0', '0 clear, 1 rain, 2 fog, 3 storm (day 1 is clear)'), ('Tomorrow', 'PinCategory="int"', '0', 'the forecast'),
        ('WasNight', 'PinCategory="bool"', 'false', 'IsNight last tick (dawn / dusk edge)'),
        ('CurRain', REAL, '0.0', 'current rain 0..1'), ('CurFog', REAL, '0.0', 'current fog 0..1'), ('CurStorm', REAL, '0.0', 'current storm 0..1'),
        ('Wet', REAL, '0.0', 'surface wetness 0..1 (MPC_Weather.Wet)'), ('BlendSec', REAL, '20.0', 'seconds for the weather to change'),
        ('PClear', REAL, '0.5', 'roll below this = clear'), ('PRain', REAL, '0.7', 'below this = rain (20 %)'), ('PFog', REAL, '0.85', 'below this = fog (15 %), else storm'),
        ('NextBolt', REAL, '0.0', 'game time of the next lightning'), ('FlashT0', REAL, '-100.0', 'game time of the last bolt'),
        ('ThunderAt', REAL, '0.0', 'game time the thunder plays (0 = none)')]
used = {p for n in G.nodes for p in n[2] if 'VariableReference' in p}
for v in VARS:
    if not any('"%s"' % v[0] in u for u in used): raise SystemExit('unused BPVar ' + v[0])
bp = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'weather226/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_Weather (#226) - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bp(n, t, d) for n, t, d, _ in VARS) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# BPC_Weather variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _t, d, m in VARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
print('BPVar lines:', len(VARS))
