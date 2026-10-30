# Day / night system (owner 2026-10-30). BP_DayNight: one actor in the level, Blueprint-only, drives what is already there:
#   the Directional Light (sun by day, the same light swung round as a cool moon by night), the Sky Light, the
#   Exponential Height Fog, and a material parameter collection MPC_DayNight (scalar Night 0..1) any material can read.
#   Clock: Hour 0..24, a full day in DayLengthMin real minutes (10). Sun rises 6:00, overhead 12:00, sets 18:00.
#   Night = 18:00-6:00. At the two transitions the notice banner says NIGHT FALLS / DAWN and IsNight flips (for waves,
#   carts, torches: read BP_DayNight.IsNight or Hour).
#   python gen_daynight.py -> BP_DayNight_graph.txt
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
NOTC, HUDCLS = BPC(P_NOTICE, 'BP_NoticeHUD'), CLS('HUD')
DLA, SLA, FOGA = CLS('DirectionalLight'), CLS('SkyLight'), CLS('ExponentialHeightFog')
LIGHTA, LIGHTC, SKYC, FOGC = CLS('Light'), CLS('LightComponent'), CLS('SkyLightComponent'), CLS('ExponentialHeightFogComponent')
KMAT, MPC = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC_PATH = '/Game/CastleDefender/Environment/DayNight/MPC_DayNight.MPC_DayNight'
P_DIRL, P_SKYL, P_FOG = '/Script/Engine.DirectionalLight', '/Script/Engine.SkyLight', '/Script/Engine.ExponentialHeightFog'

G = Graph(); b = B(G, 'dn')


def find(cls_path, cls, x, y, tag):
    return b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cls_path), ob('ReturnValue', cls, out=True)], x, y, tag=tag)


def lerp(a, b_, t, x, y): return b.math('Lerp', [(D('A'), a), (D('B'), b_), (D('Alpha'), t)], D('ReturnValue', out=True), x, y)


def clerp(ca, cb, t, x, y):
    return b.math('LinearColorLerp', [(st('A', LC, default=ca), None), (st('B', LC, default=cb), None), (fl('Alpha'), t)], st('ReturnValue', LC, out=True), x, y)


# ---------------- BeginPlay: find the sky, start the clock ----------------
bp = b.override('DNBeginPlay', 'ReceiveBeginPlay', 0, 0)
s0 = b.set('Hour', DBL, b.get('StartHour', D('v', default='9.0'), 150, 250), 300, 0); G.link(bp, 'then', s0, 'execute')
s1 = b.set('Sun', ob('v', DLA), (find(P_DIRL, DLA, 450, 250, 'FindSun'), 'ReturnValue'), 700, 0); G.link(s0, 'then', s1, 'execute')
s2 = b.set('Sky', ob('v', SLA), (find(P_SKYL, SLA, 850, 250, 'FindSky'), 'ReturnValue'), 1100, 0); G.link(s1, 'then', s2, 'execute')
s3 = b.set('Fog', ob('v', FOGA), (find(P_FOG, FOGA, 1250, 250, 'FindFog'), 'ReturnValue'), 1500, 0); G.link(s2, 'then', s3, 'execute')
tm = b.timer('Clock', 1900, 0, dtime='0.1', loop=True); G.link(s3, 'then', tm, 'execute')

# ---------------- Clock (every 0.1 s) ----------------
Y = 800
ev = b.event('Clock', [], 0, Y)
# Hour += 0.1 s * 24 h / (DayLengthMin * 60 s)
step = b.d2('Divide_DoubleDouble', None, b.d2('Multiply_DoubleDouble', b.get('DayLengthMin', D('v', default='10.0'), 0, Y + 400), None, 250, Y + 400, db='60.0'), 500, Y + 300, da='2.4')
h1 = b.d2('Add_DoubleDouble', b.get('Hour', DBL, 500, Y + 150), step, 750, Y + 200)
wrap = b.dcmp('GreaterEqual_DoubleDouble', h1, None, 1000, Y + 350, db='24.0')
h2 = b.self_(b.d2('Subtract_DoubleDouble', h1, None, 1000, Y + 200, db='24.0'), h1, wrap, 1250, Y + 200)
sh = b.set('Hour', DBL, h2, 1500, Y); G.link(ev, 'then', sh, 'execute')
# sun elevation e = sin((Hour - 6) * 15 deg): +1 noon, 0 at 6:00 / 18:00, -1 midnight
hr = b.get('Hour', DBL, 1500, Y + 500)
ang = b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', hr, None, 1750, Y + 500, db='6.0'), None, 2000, Y + 500, db='15.0')
e = b.math('DegSin', [(D('A'), ang)], D('ReturnValue', out=True), 2250, Y + 500)
day = b.clamp(b.d2('Multiply_DoubleDouble', e, None, 2500, Y + 450, db='3.0'), '0.0', '1.0', 2750, Y + 450)
night = b.clamp(b.d2('Multiply_DoubleDouble', e, None, 2500, Y + 650, db='-3.0'), '0.0', '1.0', 2750, Y + 650)
isn = b.dcmp('Less_DoubleDouble', e, None, 2500, Y + 850, db='0.0')
# light direction: pitch = -(Hour-6)*15 by day; the same light swung 180 deg round is the moon by night
pitch_day = b.d2('Multiply_DoubleDouble', ang, None, 2250, Y + 1050, db='-1.0')
pitch = b.self_(b.d2('Subtract_DoubleDouble', pitch_day, None, 2500, Y + 1050, db='180.0'), pitch_day, isn, 2750, Y + 1050)
rot = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch'), pitch), (fl('Yaw'), b.get('SunYaw', D('v', default='35.0'), 2750, Y + 1250))], st('ReturnValue', ROT, out=True), 3000, Y + 1050)
sun = b.get('Sun', ob('v', DLA), 3000, Y + 300)
sr = b.call(ACT, 'K2_SetActorRotation', [st('NewRotation', ROT), bo('bTeleportPhysics', default='false'), bo('ReturnValue', out=True)], 3300, Y, target=sun, tag='SunRot')
b.wire(rot, sr, 'NewRotation'); G.link(sh, 'then', sr, 'execute')
# sun / moon strength and colour
sunc = b.getm('LightComponent', LIGHTA, ob('v', LIGHTC), sun, 3300, Y + 300)
lux_day = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', day, None, 3300, Y + 500, db='9.0'), None, 3550, Y + 500, db='1.0')         # 1..10 lux
lux_moon = b.d2('Multiply_DoubleDouble', night, b.get('MoonLux', D('v', default='0.6'), 3300, Y + 700), 3550, Y + 700)
lux = b.self_(lux_moon, lux_day, isn, 3800, Y + 600)
si = b.call(LIGHTC, 'SetIntensity', [fl('NewIntensity')], 3800, Y, target=sunc, tag='SunLux'); b.wire(lux, si, 'NewIntensity'); G.link(sr, 'then', si, 'execute')
cday = clerp('(R=1.000000,G=0.520000,B=0.250000,A=1.000000)', '(R=1.000000,G=0.960000,B=0.900000,A=1.000000)', day, 3800, Y + 850)       # horizon amber -> noon white
cmoon = b.math('LinearColorLerp', [(st('A', LC, default='(R=0.300000,G=0.400000,B=0.700000,A=1.000000)'), None), (st('B', LC, default='(R=0.550000,G=0.680000,B=1.000000,A=1.000000)'), None), (fl('Alpha'), night)], st('ReturnValue', LC, out=True), 3800, Y + 1000)
col = b.math('SelectColor', [(st('A', LC), cmoon), (st('B', LC), cday), (bo('bPickA', default='false'), isn)], st('ReturnValue', LC, out=True), 4100, Y + 900)
sc = b.call(LIGHTC, 'SetLightColor', [st('NewLightColor', LC), bo('bSRGB', default='true')], 4200, Y, target=sunc, tag='SunColor'); b.wire(col, sc, 'NewLightColor'); G.link(si, 'then', sc, 'execute')
# sky light: ambient follows the day, a little stays at night
sky = b.get('Sky', ob('v', SLA), 4500, Y + 300); skyc = b.getm('LightComponent', SLA, ob('v', SKYC), sky, 4700, Y + 300)
amb = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', day, None, 4500, Y + 550, db='0.85'), None, 4750, Y + 550, db='0.15')
sk = b.call(LIGHTC, 'SetIntensity', [fl('NewIntensity')], 4950, Y, target=skyc, tag='SkyLux'); b.wire(amb, sk, 'NewIntensity'); G.link(sc, 'then', sk, 'execute')
# fog: thicker and bluer at night
fog = b.get('Fog', ob('v', FOGA), 5300, Y + 300); fogc = b.getm('Component', FOGA, ob('v', FOGC), fog, 5500, Y + 300)
dens = b.d2('Add_DoubleDouble', b.get('FogDay', D('v', default='0.02'), 5300, Y + 550), b.d2('Multiply_DoubleDouble', night, b.get('FogNightExtra', D('v', default='0.03'), 5300, Y + 800), 5550, Y + 700), 5800, Y + 600)
fd = b.call(FOGC, 'SetFogDensity', [fl('Value')], 5750, Y, target=fogc, tag='FogDensity'); b.wire(dens, fd, 'Value'); G.link(sk, 'then', fd, 'execute')
fcol = clerp('(R=0.700000,G=0.760000,B=0.850000,A=1.000000)', '(R=0.050000,G=0.070000,B=0.140000,A=1.000000)', night, 5800, Y + 950)
fc = b.call(FOGC, 'SetFogInscatteringColor', [st('Value', LC)], 6150, Y, target=fogc, tag='FogColor'); b.wire(fcol, fc, 'Value'); G.link(fd, 'then', fc, 'execute')
# material parameter collection: Night 0..1 for torches, windows, the realm
mp = b.lib(KMAT, 'SetScalarParameterValue', [WC(), dict(ob('Collection', MPC), dobj=MPC_PATH), N('ParameterName', default='Night'), fl('ParameterValue')], 6550, Y, tag='MPCNight')
b.wire(night, mp, 'ParameterValue'); G.link(fc, 'then', mp, 'execute')
# transition: IsNight changed -> banner
chg = b.math('NotEqual_BoolBool', [(bo('A', default='false'), isn), (bo('B', default='false'), b.get('IsNight', BOOL, 6700, Y + 500))], bo('ReturnValue', out=True), 6950, Y + 450)
brc = b.branch(chg, 7000, Y, 'IfChanged'); G.link(mp, 'then', brc, 'execute')
sn = b.set('IsNight', BOOL, isn, 7300, Y); G.link(brc, 'then', sn, 'execute')
pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], 7300, Y + 400, pure=True, tag='PC')
hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], 7550, Y + 400, target=(pc, 'ReturnValue'), pure=True, const=True, tag='HUD')
nc = b.name('AsNoticeHUD'); cast(G, nc, NOTC, 'AsBP Notice HUD', 7600, Y); b.wire((hud, 'ReturnValue'), nc, 'Object'); G.link(sn, 'then', nc, 'execute')
txt = b.selstr(None, None, b.get('IsNight', BOOL, 7900, Y + 500), 8150, Y + 400, da='NIGHT FALLS', db='DAWN')
pn = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='1')], 8200, Y, target=(nc, 'AsBP Notice HUD'), tag='Notice'); b.wire(txt, pn, 'Text'); G.link(nc, 'then', pn, 'execute')

open(os.path.join(HERE, 'BP_DayNight_graph.txt'), 'w', encoding='utf-8').write(G.render())
print('BP_DayNight', len(G.nodes), 'nodes')
