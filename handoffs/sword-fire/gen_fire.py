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
tgt = b.self_(None, None, want, 1900, Y + 800, da='1.0', db='0.0')
ease = b.math('FInterpTo', [(D('Current'), b.get('FireHeat', DBL, 1900, Y + 1000)), (D('Target'), tgt), (D('DeltaTime', default='0.15'), None), (D('InterpSpeed', default='4.0'), None)], D('ReturnValue', out=True), 2300, Y + 850)
s_h = b.set('FireHeat', DBL, ease, 2600, Y + 600); G.link(fe, 'Completed', s_h, 'execute')
heat = b.get('FireHeat', DBL, 2600, Y + 1000)
sp = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', default='Heat'), fl('Value')], 2950, Y + 600, target=b.get('FireMID', ob('v', MID), 2700, Y + 850), tag='SetHeat')
b.wire(heat, sp, 'Value'); G.link(s_h, 'then', sp, 'execute')
li = b.call(LIGHT, 'SetIntensity', [fl('NewIntensity')], 3350, Y + 600, target=b.get('FireLight', ob('v', PLC), 3100, Y + 850), tag='LightHeat')
b.wire(b.d2('Multiply_DoubleDouble', heat, None, 3100, Y + 1000, db='4000.0'), li, 'NewIntensity'); G.link(sp, 'then', li, 'execute')

open(os.path.join(HERE, 'Hero_SwordFire_graph.txt'), 'w', encoding='utf-8').write(G.render())
json.dump({'blueprint': 'BP_ThirdPersonCharacter', 'pastes': ['Hero_SwordFire_graph.txt'], 'rewires': [
  {'from': 'K2Node_Event_1.then', 'to': mid + '.execute', 'replace': True, 'note': 'BeginPlay -> fire init first (was -> K2Node_DynamicCast_0)'},
  {'from': tm + '.then', 'to': 'K2Node_DynamicCast_0.execute', 'note': 'then the original BeginPlay chain'}]},
  open(os.path.join(HERE, 'manifest.json'), 'w'), indent=1)
print('wrote', len(G.nodes), 'nodes', mid, tm)
