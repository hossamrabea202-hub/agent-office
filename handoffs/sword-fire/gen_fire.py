# Sword fire: the hero's blade lights when zombies come close (owner 2026-10-30). Paste for BP_ThirdPersonCharacter.
#   FireInit (inserted at the top of BeginPlay): a dynamic instance of MI_SwordFire becomes the Sword's Overlay Material;
#     a point light (warm, 0 intensity) is added and attached to the Sword; a 0.15 s looping timer starts FireThink.
#   FireThink: Near = any BP_Zombie within FireRange (600 cm). FireHeat eases toward (FireOn && Near ? 1 : 0) at speed 4;
#     Heat goes to the overlay material and the light (0..4000 intensity).
#   Variables (VARIABLES.md): FireMID, FireLight, FireHeat, FireOn (true), FireRange (600), FireNear.
#   python gen_fire.py -> Hero_SwordFire_graph.txt + manifest.json (rewire: K2Node_Event_1.then -> FireInit -> K2Node_DynamicCast_0)
import os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
MI_PATH = '/Game/CastleDefender/VFX/SwordFire/MI_SwordFire.MI_SwordFire'
ZOMBIE = BPC(P_ZOMBIE, 'BP_Zombie')
PLC, ACOMP, SMC, KMAT = CLS('PointLightComponent'), CLS('ActorComponent'), CLS('StaticMeshComponent'), CLS('KismetMaterialLibrary')
ATT = lambda n: {'name': n, 'cat': 'byte', 'obj': ENUM('EAttachmentRule'), 'default': 'KeepRelative'}

G = Graph(); b = B(G, 'sf')
# ---------------- FireInit ----------------
sword = b.get('Sword', ob('v', SMC), 0, 400)
mid = b.lib(KMAT, 'CreateDynamicMaterialInstance', [WC(), dict(ob('Parent', MATI), dobj=MI_PATH), N('OptionalName', default='None'),
                                                     {'name': 'OptionalMIDCreationFlags', 'cat': 'byte', 'obj': ENUM('EMIDCreationFlags'), 'default': 'None'},
                                                     ob('ReturnValue', MID, out=True)], 0, 0, tag='MakeFireMID')
s_mid = b.set('FireMID', ob('v', MID), (mid, 'ReturnValue'), 400, 0)
ov = b.call(MESHC, 'SetOverlayMaterial', [ob('NewOverlayMaterial', MATI)], 700, 0, target=sword, tag='SetOverlay')
b.wire(b.get('FireMID', ob('v', MID), 500, 300), ov, 'NewOverlayMaterial')
addc = b.call_self('AddComponentByClass', [CLSPIN('Class', ACOMP, '/Script/Engine.PointLightComponent'), bo('bManualAttachment', default='false'),
                                           st('RelativeTransform', XFORM, default='0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,1.000000,0.000000,0.000000,0.000000,1.000000,1.000000,1.000000'),
                                           bo('bDeferredFinish', default='false'), ob('ReturnValue', ACOMP, out=True)], 1050, 0, ACT, tag='AddLight')
cs = b.name('AsLight'); cast(G, cs, PLC, 'AsPoint Light Component', 1450, 0); b.wire((addc, 'ReturnValue'), cs, 'Object')
s_l = b.set('FireLight', ob('v', PLC), (cs, 'AsPoint Light Component'), 1800, 0)
light = b.get('FireLight', ob('v', PLC), 1800, 350)
att = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName', default='None'), ATT('LocationRule'), ATT('RotationRule'), ATT('ScaleRule'), bo('bWeldSimulatedBodies', default='false')], 2100, 0, target=light, tag='AttachLight')
b.wire(sword, att, 'Parent')
LIGHT = CLS('LightComponent')
colr = b.call(LIGHT, 'SetLightColor', [st('NewLightColor', LC, default='(R=1.000000,G=0.450000,B=0.120000,A=1.000000)'), bo('bSRGB', default='true')], 2500, 0, target=light, tag='LightColor')
rad = b.call(PLC, 'SetAttenuationRadius', [fl('NewRadius', default='600.000000')], 2850, 0, target=light, tag='LightRadius')
sh = b.call(LIGHT, 'SetCastShadows', [bo('bNewValue', default='false')], 3200, 0, target=light, tag='LightShadows')
it0 = b.call(LIGHT, 'SetIntensity', [fl('NewIntensity', default='0.000000')], 3550, 0, target=light, tag='LightOff')
tm = b.timer('FireThink', 3900, 0, dtime='0.15', loop=True)
b.chain(mid, s_mid, ov, addc, cs, s_l, att, colr, rad, sh, it0, tm)

# ---------------- FireThink ----------------
Y = 900
ev = b.event('FireThink', [], 0, Y)
s_n0 = b.set('FireNear', BOOL, None, 300, Y); G.link(ev, 'then', s_n0, 'execute')
ga = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_ZOMBIE)), arr(ob('OutActors', ACT, out=True))], 600, Y, tag='Zombies')
G.link(s_n0, 'then', ga, 'execute')
fe = b.foreach(ACT, 1000, Y); G.link(ga, 'then', fe, 'Exec'); b.wire((ga, 'OutActors'), fe, 'Array')
dist = b.call_self('GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 1300, Y + 350, ACT, pure=True, const=True, tag='DistZ'); b.wire((fe, 'Array Element'), dist, 'OtherActor')
close = b.dcmp('Less_DoubleDouble', (dist, 'ReturnValue'), b.get('FireRange', D('v', default='600.0'), 1300, Y + 500), 1600, Y + 350)
br = b.branch(close, 1900, Y + 200, 'IfClose'); G.link(fe, 'LoopBody', br, 'execute')
s_n1 = b.set('FireNear', bo('v', default='true'), None, 2200, Y + 200); G.link(br, 'then', s_n1, 'execute')
# target heat, ease, apply
want = b.b2('BooleanAND', b.get('FireOn', BOOL, 1300, Y + 750), b.get('FireNear', BOOL, 1300, Y + 900), 1600, Y + 800)
tgt0 = b.self_(None, None, want, 1900, Y + 800, da='1.0', db='0.0')
# night: the blade idles warm (a torch) while BP_DayNight says it is night
DNC = BPC('/Game/CastleDefender/Environment/DayNight/BP_DayNight', 'BP_DayNight')
dn = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, '/Game/CastleDefender/Environment/DayNight/BP_DayNight.BP_DayNight_C'), ob('ReturnValue', DNC, out=True)], 1300, Y + 1200, pure=True, tag='FindDayNight')
isn = b.b2('BooleanAND', b.valid((dn, 'ReturnValue'), 1600, Y + 1150), b.getm('IsNight', DNC, BOOL, (dn, 'ReturnValue'), 1600, Y + 1300), 1900, Y + 1200)
idle = b.self_(b.get('NightIdle', D('v', default='0.25'), 1900, Y + 1400), None, isn, 2150, Y + 1250, db='0.0')
tgt = b.math('FMax', [(D('A'), tgt0), (D('B'), idle)], D('ReturnValue', out=True), 2150, Y + 950)
ease = b.math('FInterpTo', [(D('Current'), b.get('FireHeat', DBL, 1900, Y + 1000)), (D('Target'), tgt), (D('DeltaTime', default='0.15'), None), (D('InterpSpeed', default='4.0'), None)], D('ReturnValue', out=True), 2300, Y + 850)
s_h = b.set('FireHeat', DBL, ease, 2600, Y + 600); G.link(fe, 'Completed', s_h, 'execute')
heat = b.get('FireHeat', DBL, 2600, Y + 1000)
sp = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', default='Heat'), fl('Value')], 2950, Y + 600, target=b.get('FireMID', ob('v', MID), 2700, Y + 850), tag='SetHeat')
b.wire(heat, sp, 'Value'); G.link(s_h, 'then', sp, 'execute')
li = b.call(LIGHT, 'SetIntensity', [fl('NewIntensity')], 3350, Y + 600, target=b.get('FireLight', ob('v', PLC), 3100, Y + 850), tag='LightHeat')
b.wire(b.d2('Multiply_DoubleDouble', heat, None, 3100, Y + 1000, db='4000.0'), li, 'NewIntensity'); G.link(sp, 'then', li, 'execute')

tm2 = b.timer('BurnThink', 4250, 0, dtime='0.25', loop=True); G.link(tm, 'then', tm2, 'execute')

# ---------------- FireSlash: the slash trail turns to fire while the blade is hot ----------------
# inserted after CX_737 (SetScalarParameterValue Intensity on the slash MID CX_721) and before CX_728 (SetLifeSpan)
Y = 2400
hot = b.dcmp('Greater_DoubleDouble', b.get('FireHeat', DBL, 0, Y + 300), None, 300, Y + 300, db='0.5')
brs = b.branch(hot, 600, Y, 'IfHotSlash')
sc = b.call(MID, 'SetVectorParameterValue', [N('ParameterName', default='Color'), st('Value', LC, default='(R=1.000000,G=0.320000,B=0.040000,A=1.000000)')], 900, Y, tag='SlashEmber')   # self <- CX_721.ReturnValue
si = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', default='Intensity'), fl('Value')], 1300, Y, tag='SlashHot')                                                        # self <- CX_721.ReturnValue
sm = b.d2('Multiply_DoubleDouble', None, None, 1050, Y + 300, da='1.0', db='3.0'); b.wire(sm, si, 'Value')                                                                          # A <- CX_735.ReturnValue
G.link(brs, 'then', sc, 'execute'); G.link(sc, 'then', si, 'execute')
SLASH_MULT = sm[0]

# ---------------- BurnStart: a zombie hit by the hot blade keeps burning ----------------
# hung off CH7.then (ApplyDamage of the sword hit; it had no continuation); OtherActor comes from CH0
Y = 3200
hot2 = b.dcmp('Greater_DoubleDouble', b.get('FireHeat', DBL, 0, Y + 300), None, 300, Y + 300, db='0.5')
brb = b.branch(hot2, 600, Y, 'IfHotHit')
zc = b.name('AsZombieHit'); cast(G, zc, ZOMBIE, 'AsBP Zombie', 900, Y)                                          # Object <- CH0.OtherActor
G.link(brb, 'then', zc, 'execute')
ZH = (zc, 'AsBP Zombie')
burning = b.get('Burning', arr(ob('v', ACT)), 1200, Y + 400)
has = b.name('BurnHas'); G.node(has, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Contains")' % KARR],
                              [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, {'name': 'ItemToFind', 'cat': 'wildcard', 'ref': True}, bo('ReturnValue', out=True)], 1450, Y + 400)
b.wire(burning, has, 'TargetArray'); b.wire(ZH, has, 'ItemToFind')
brn = b.branch(b.bnot((has, 'ReturnValue'), 1750, Y + 400), 1950, Y, 'IfNew'); G.link(zc, 'then', brn, 'execute')
a1 = b.aadd('Burning', ob('v', ACT), ZH, 2250, Y); G.link(brn, 'then', a1, 'execute')
endt = b.d2('Add_DoubleDouble', b.now(2250, Y + 500), b.get('BurnTime', D('v', default='3.0'), 2250, Y + 650), 2550, Y + 500)
a2 = b.aadd('BurnEnd', DBL, endt, 2750, Y); G.link(a1, 'then', a2, 'execute')
zmesh = b.getm('Mesh', CHARC, ob('v', SKEL), ZH, 2900, Y + 400)
bov = b.call(MESHC, 'SetOverlayMaterial', [dict(ob('NewOverlayMaterial', MATI), dobj='/Game/CastleDefender/VFX/SwordFire/MI_Burning.MI_Burning')], 3250, Y, target=zmesh, tag='BurnOverlay')
G.link(a2, 'then', bov, 'execute')

# ---------------- BurnThink (0.25 s): damage every burning zombie; the oldest burn ends after BurnTime ----------------
Y = 4200
ev2 = b.event('BurnThink', [], 0, Y)
fe2 = b.foreach(ACT, 300, Y); b.wire(b.get('Burning', arr(ob('v', ACT)), 0, Y + 300), fe2, 'Array'); G.link(ev2, 'then', fe2, 'Exec')
ok = b.branch(b.valid((fe2, 'Array Element'), 650, Y + 350), 900, Y + 200, 'IfAlive'); G.link(fe2, 'LoopBody', ok, 'execute')
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 1100, Y + 600, PAWN, pure=True, const=True, tag='MyCtl')
dmg = b.lib(GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage'), ob('EventInstigator', CTRL), ob('DamageCauser', ACT), CLSPIN('DamageTypeClass', CLS('DamageType'), None), fl('ReturnValue', out=True)], 1200, Y + 200, tag='BurnTick')
b.wire((fe2, 'Array Element'), dmg, 'DamagedActor'); b.wire(b.get('BurnDamage', D('v', default='5.0'), 950, Y + 500), dmg, 'BaseDamage'); b.wire((ctl, 'ReturnValue'), dmg, 'EventInstigator'); b.wire(b.self_node(1000, Y + 750), dmg, 'DamageCauser')
G.link(ok, 'then', dmg, 'execute')
# expiry of the oldest entry
n_ = b.alen('BurnEnd', DBL, 1700, Y + 900)
any_ = b.icmp('Greater_IntInt', n_, None, 2150, Y + 900, db='0')
first = b.aget('BurnEnd', DBL, None, 1700, Y + 1100)
due = b.dcmp('GreaterEqual_DoubleDouble', b.now(1950, Y + 1300), first, 2250, Y + 1100)
bre = b.branch(b.b2('BooleanAND', any_, due, 2500, Y + 1000), 2800, Y, 'IfBurnOver'); G.link(fe2, 'Completed', bre, 'execute')
old = b.aget('Burning', ob('v', ACT), None, 2800, Y + 400)
oc = b.name('AsOldZombie'); cast(G, oc, ZOMBIE, 'AsBP Zombie', 3100, Y); b.wire(old, oc, 'Object'); G.link(bre, 'then', oc, 'execute')
omesh = b.getm('Mesh', CHARC, ob('v', SKEL), (oc, 'AsBP Zombie'), 3400, Y + 400)
off = b.call(MESHC, 'SetOverlayMaterial', [ob('NewOverlayMaterial', MATI)], 3700, Y, target=omesh, tag='BurnOff'); G.link(oc, 'then', off, 'execute')
def remove0(arrvar, pin, x, y):
    a = b.get(arrvar, arr(pin), x, y + 200); n = b.name('Pop' + arrvar)
    G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_RemoveIndex")' % KARR],
           [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('IndexToRemove', default='0'), bo('ReturnValue', out=True)], x, y)
    b.wire(a, n, 'TargetArray'); return n
r1 = remove0('Burning', ob('v', ACT), 4100, Y); r2 = remove0('BurnEnd', DBL, 4450, Y)
G.link(off, 'then', r1, 'execute'); G.link(oc, 'CastFailed', r1, 'execute'); G.link(r1, 'then', r2, 'execute')

open(os.path.join(HERE, 'Hero_SwordFire_graph.txt'), 'w', encoding='utf-8').write(G.render())
json.dump({'blueprint': 'BP_ThirdPersonCharacter', 'pastes': ['Hero_SwordFire_graph.txt'], 'rewires': [
  {'from': 'K2Node_Event_1.then', 'to': mid + '.execute', 'replace': True, 'note': 'BeginPlay -> fire init first (was -> K2Node_DynamicCast_0)'},
  {'from': tm2 + '.then', 'to': 'K2Node_DynamicCast_0.execute', 'note': 'then the original BeginPlay chain'},
  {'from': 'CX_737.then', 'to': brs + '.execute', 'replace': True, 'note': 'slash: after Intensity is set (was -> CX_728 SetLifeSpan)'},
  {'from': brs + '.else', 'to': 'CX_728.execute'}, {'from': si + '.then', 'to': 'CX_728.execute'},
  {'from': 'CX_721.ReturnValue', 'to': sc + '.self'}, {'from': 'CX_721.ReturnValue', 'to': si + '.self', 'note': 'the slash MID'},
  {'from': 'CX_735.ReturnValue', 'to': SLASH_MULT + '.A', 'note': 'the normal slash intensity, x3 when hot'},
  {'from': 'K2Node_CallFunction_CH7.then', 'to': brb + '.execute', 'note': 'after the sword hit damage'},
  {'from': 'K2Node_ComponentBoundEvent_CH0.OtherActor', 'to': zc + '.Object', 'note': 'the actor the sword hit'}]},
  open(os.path.join(HERE, 'manifest.json'), 'w'), indent=1)
print('wrote', len(G.nodes), 'nodes', mid, tm)
