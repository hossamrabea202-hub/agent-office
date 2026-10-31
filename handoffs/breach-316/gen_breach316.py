# #316 breach made dramatic (adjustedfilm, 2026-10-31; owner W:). Part A: trigger + VFX + no floating stones.
# (Part B = TGA #327: the baked masonry collapse SK_WallBreach, spawned here through CollapseClass once it exists.)
#   "<blender python>" -I gen_breach316.py -> BP_BreachFX_graph.txt, VARIABLES_BPVar.txt
# BP_BreachFX (one per level). No edit to BP_WallBreachSpot: it watches every spot's parts by name (the Master's notes on
# #316: components Rubble*, Brk0..Brk20).
#   FxPoll (0.2 s) per spot: the natural-boulder Rubble* parts are hidden (HideRubble). A spot counts as broken the moment any
#   of its Brk* parts is visible. On that edge: collapse sound, 5 dust bursts (P_Smoke_Burst) staggered over 0.6 s around
#   the hole, a camera shake (BP_CannonShake_Impact, 15-60 m), and then
#     - with CollapseClass set (TGA's baked collapse): spawn it at the spot, facing the spot's forward, and hide every Brk*;
#     - without it: every Brk* part becomes movable + simulates physics, so it falls and settles instead of hanging in the air.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

P_SPOT = '/Game/CastleDefender/Gameplay/Siege/BP_WallBreachSpot'
SPOT = BPC(P_SPOT, 'BP_WallBreachSpot')
SMC_ = CLS('StaticMeshComponent'); SOUND = CLS('SoundBase')
SFX = '/Game/CastleDefender/Gameplay/Siege/Breach/SFX_WallBreach.SFX_WallBreach'
SHAKE = '/Game/CastleDefender/Gameplay/Cannon/BP_CannonShake_Impact.BP_CannonShake_Impact_C'
OBJV = lambda c: ob('v', c)
CLSV = lambda: {'name': 'v', 'cat': 'class', 'obj': ACT}


class B(bpkit.B):
    def timer_ev(s, fn, interval, loop, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default=loop),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def starts(s, strv, prefix, x, y):
        return s.math('StartsWith', [(S('SourceString'), strv), (S('InPrefix', default=prefix), None),
                                     ({'name': 'SearchCase', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/CoreUObject.ESearchCase\'"', 'default': 'IgnoreCase'}, None)],
                      bo('ReturnValue', out=True), x, y) if False else s._starts(strv, prefix, x, y)
    def _starts(s, strv, prefix, x, y):
        n = s.lib(KSTR, 'StartsWith', [S('SourceString'), S('InPrefix', default=prefix),
                  {'name': 'SearchCase', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/CoreUObject.ESearchCase\'"', 'default': 'IgnoreCase'},
                  bo('ReturnValue', out=True, default='false')], x, y, pure=True, tag='Starts' + prefix)
        s.wire(strv, n, 'SourceString'); return (n, 'ReturnValue')
    def objname(s, obj, x, y):
        n = s.lib(KSL, 'GetObjectName', [ob('Object', OBJ), S('ReturnValue', out=True)], x, y, pure=True, tag='Name'); s.wire(obj, n, 'Object'); return (n, 'ReturnValue')
    def comps_of(s, actor, x, y):
        n = s.call(ACT, 'K2_GetComponentsByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Script/Engine.StaticMeshComponent'), arr(ob('ReturnValue', SMC_, out=True))],
                   x, y, target=actor, pure=True, const=True, tag='Parts')
        return (n, 'ReturnValue')


G = Graph(); b = B(G, 'bx')
g = b.get
G.node('bxBeginPlay', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT}, ex('then', True)], 0, 0)
ga = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SPOT)), arr(ob('OutActors', SPOT, out=True))], 300, 0, tag='AllSpots')
G.link('bxBeginPlay', 'then', ga, 'execute')
ss = b.set('Spots', arr(OBJV(ACT)), (ga, 'OutActors'), 600, 0); G.link(ga, 'then', ss, 'execute')
fe = b.foreach(ACT, 900, 0); b.wire(g('Spots', arr(OBJV(ACT)), 800, 200), fe, 'Array'); G.link(ss, 'then', fe, 'Exec')
G.link(fe, 'LoopBody', b.aadd('WasBroken', BOOL, None, 1200, 0), 'execute')
G.link(fe, 'Completed', b.timer_ev('FxPoll', '0.2', 'true', 1300, 400), 'execute')

# ---- FxPoll
Y = 1000
b.event('FxPoll', [], 0, Y)
fs = b.foreach(ACT, 300, Y); b.wire(g('Spots', arr(OBJV(ACT)), 200, Y + 200), fs, 'Array'); G.link('FxPoll', 'then', fs, 'Exec')
spot, si = (fs, 'Array Element'), (fs, 'Array Index')
vs = b.branch(b.valid(spot, 500, Y + 200), 550, Y, tag='IfSpot'); G.link(fs, 'LoopBody', vs, 'execute')
c0 = b.set('Broken', bo('v', default='false'), None, 800, Y); G.link(vs, 'then', c0, 'execute')
fp = b.foreach(SMC_, 1050, Y); b.wire(b.comps_of(spot, 850, Y + 250), fp, 'Array'); G.link(c0, 'then', fp, 'Exec')
part = (fp, 'Array Element')
pname = b.objname(part, 1100, Y + 350)
isrub = b._starts(pname, 'Rubble', 1300, Y + 350); isbrk = b._starts(pname, 'Brk', 1300, Y + 500)
br = b.branch(b.b2('BooleanAND', isrub, g('HideRubble', BOOL, 1300, Y + 650), 1500, Y + 600), 1300, Y, tag='IfRubble'); G.link(fp, 'LoopBody', br, 'execute')
hr = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 1550, Y - 150, target=part, tag='HideRubble')
G.link(br, 'then', hr, 'execute')
hc = b.call(PRIM, 'SetCollisionEnabled', [{'name': 'NewType', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.ECollisionEnabled\'"', 'default': 'NoCollision'}],
            1800, Y - 150, target=part, tag='NoCollRubble')
G.link(hr, 'then', hc, 'execute')
vis = b.call(SCENE, 'IsVisible', [bo('ReturnValue', out=True, default='false')], 1500, Y + 800, target=part, pure=True, const=True, tag='Vis')
bb = b.branch(b.b2('BooleanAND', isbrk, (vis, 'ReturnValue'), 1700, Y + 700), 1600, Y + 150, tag='IfBrkShown'); G.link(br, 'else', bb, 'execute')
G.link(bb, 'then', b.set('Broken', bo('v', default='true'), None, 1850, Y + 150), 'execute')
# edge: just broken
edge = b.b2('BooleanAND', g('Broken', BOOL, 1300, Y + 1200), b.bnot(b.aget('WasBroken', BOOL, si, 1300, Y + 1350), 1500, Y + 1350), 1700, Y + 1250)
be = b.branch(edge, 1300, Y + 1000, tag='IfJustBroken'); G.link(fp, 'Completed', be, 'execute')
sw = b.aset('WasBroken', BOOL, si, None, 1550, Y + 1000, ditem='true'); G.link(be, 'then', sw, 'execute')
sl = b.set('FxAt', VECT, b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1600, Y + 1300, target=spot, pure=True, const=True, tag='SpotLoc') and
           (G.nodes[-1][0], 'ReturnValue'), 1800, Y + 1000)
G.link(sw, 'then', sl, 'execute')
sfx = b.lib(GS, 'PlaySoundAtLocation', [WC(), dict(ob('Sound', SOUND), dobj=SFX), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
            fl('VolumeMultiplier', default='1.500000'), fl('PitchMultiplier', default='1.000000'), fl('StartTime', default='0.000000'),
            ob('AttenuationSettings', CLS('SoundAttenuation')), ob('ConcurrencySettings', CLS('SoundConcurrency')), ob('OwningActor', ACT), ob('InitialParams', CLS('InitialActiveSoundParams'))],
            2050, Y + 1000, tag='Crash')
b.wire(g('FxAt', VECT, 1900, Y + 1300), sfx, 'Location'); G.link(sl, 'then', sfx, 'execute')
shk = b.lib(GS, 'PlayWorldCameraShake', [WC(), CLSPIN('Shake', CLS('CameraShakeBase'), SHAKE), V('Epicenter'), fl('InnerRadius', default='1500.0'),
            fl('OuterRadius', default='6000.0'), fl('Falloff', default='1.0'), bo('bOrientShakeTowardsEpicenter', default='false')], 2350, Y + 1000, tag='Shake')
b.wire(g('FxAt', VECT, 2200, Y + 1300), shk, 'Epicenter'); G.link(sfx, 'then', shk, 'execute')
# 5 dust bursts: one now, the rest from a timer (DustLeft counts down)
sdl = b.set('DustLeft', INT, None, 2650, Y + 1000); [n for n in G.nodes if n[0] == sdl][0][3][2]['default'] = '5'
G.link(shk, 'then', sdl, 'execute')
G.link(sdl, 'then', b.timer_ev('DustPuff', '0.12', 'true', 2900, Y + 1000), 'execute')
# collapse or physics
hasc = b.math('IsValidClass', [({'name': 'Class', 'cat': 'class', 'obj': OBJ}, g('CollapseClass', CLSV(), 3000, Y + 1300))], bo('ReturnValue', out=True), 3200, Y + 1300)
bcl = b.branch(hasc, 3150, Y + 1000, tag='IfCollapse'); G.link([n for n in G.nodes if n[0].startswith('bxTimerDustPuff')][-1][0], 'then', bcl, 'execute')
xf = transform(b, g('FxAt', VECT, 3300, Y + 1500), 3500, Y + 1500)
rot = b.call(ACT, 'K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], 3300, Y + 1700, target=spot, pure=True, const=True, tag='SpotRot')
b.wire((rot, 'ReturnValue'), xf[0], 'Rotation')
spn = b.name('SpawnCollapse')
G.node(spn, 'K2Node_SpawnActorFromClass', ['AdvancedPinDisplay=Hidden'],
       [ex(), ex('then', True), CLSPIN('Class', ACT, None), ob('ReturnValue', ACT, out=True), st('SpawnTransform', XFORM),
        {'name': 'CollisionHandlingOverride', 'cat': 'byte', 'obj': ENUM('ESpawnActorCollisionHandlingMethod'), 'default': 'AlwaysSpawn'},
        {'name': 'TransformScaleMethod', 'cat': 'byte', 'obj': ENUM('ESpawnActorScaleMethod'), 'default': 'SelectDefaultAtRuntime', 'advanced': True},
        dict(ob('Owner', ACT), advanced=True), ob('Instigator', PAWN)], 3450, Y + 900)
b.wire(g('CollapseClass', CLSV(), 3300, Y + 1150), spn, 'Class'); b.wire(xf, spn, 'SpawnTransform'); G.link(bcl, 'then', spn, 'execute')
fb = b.foreach(SMC_, 3700, Y + 1000); b.wire(b.comps_of(spot, 3500, Y + 1250), fb, 'Array')
G.link(spn, 'then', fb, 'Exec'); G.link(bcl, 'else', fb, 'Exec')
bp_ = (fb, 'Array Element')
bbk = b.branch(b._starts(b.objname(bp_, 3700, Y + 1350), 'Brk', 3900, Y + 1350), 3950, Y + 1000, tag='IfBrk'); G.link(fb, 'LoopBody', bbk, 'execute')
bmode = b.branch(hasc, 4200, Y + 1000, tag='IfReplace'); G.link(bbk, 'then', bmode, 'execute')
hb = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 4450, Y + 900, target=bp_, tag='HideBrk')
G.link(bmode, 'then', hb, 'execute')
mob = b.call(SCENE, 'SetMobility', [{'name': 'NewMobility', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EComponentMobility\'"', 'default': 'Movable'}],
             4450, Y + 1150, target=bp_, tag='Movable')
G.link(bmode, 'else', mob, 'execute')
cp = b.call(PRIM, 'SetCollisionProfileName', [NAME_('InCollisionProfileName', 'PhysicsActor') if 'NAME_' in globals() else {'name': 'InCollisionProfileName', 'cat': 'name', 'default': 'PhysicsActor'},
            bo('bUpdateOverlaps', default='true')], 4700, Y + 1150, target=bp_, tag='PhysProfile')
G.link(mob, 'then', cp, 'execute')
sim = b.call(PRIM, 'SetSimulatePhysics', [bo('bSimulate', default='true')], 4950, Y + 1150, target=bp_, tag='Fall')
G.link(cp, 'then', sim, 'execute')

# ---- DustPuff (0.12 s timer, 5 times)
Y2 = 3200
b.event('DustPuff', [], 0, Y2)
off = b.vec(b.rnd('-300.0', '300.0', 200, Y2 + 300), b.rnd('-300.0', '300.0', 200, Y2 + 450), b.rnd('50.0', '350.0', 200, Y2 + 600), 400, Y2 + 450)
loc = b.v2('Add_VectorVector', g('FxAt', VECT, 400, Y2 + 250), off, 600, Y2 + 350)
sc = b.rnd('1.6', '3.0', 600, Y2 + 600)
em = b.lib(GS, 'SpawnEmitterAtLocation', [WC(), dict(ob('EmitterTemplate', CLS('ParticleSystem')), dobj='/Game/CastleDefender/VFX/Smoke/P_Smoke_Burst.P_Smoke_Burst'),
           V('Location'), st('Rotation', ROT, default='0, 0, 0'), V('Scale', default='1.000000,1.000000,1.000000'), bo('bAutoDestroy', default='true'),
           {'name': 'PoolingMethod', 'cat': 'byte', 'obj': ENUM('EPSCPoolMethod'), 'default': 'None'}, bo('bAutoActivateSystem', default='true'),
           ob('ReturnValue', CLS('ParticleSystemComponent'), out=True)], 300, Y2, tag='Dust')
b.wire(loc, em, 'Location'); b.wire(b.vec(sc, sc, sc, 800, Y2 + 600), em, 'Scale'); G.link('DustPuff', 'then', em, 'execute')
dl = b.set('DustLeft', INT, b.i2('Subtract_IntInt', g('DustLeft', INT, 600, Y2 + 800), None, 800, Y2 + 800, db='1'), 650, Y2); G.link(em, 'then', dl, 'execute')
bd = b.branch(b.icmp('LessEqual_IntInt', g('DustLeft', INT, 800, Y2 + 300), None, 1000, Y2 + 300, db='0'), 900, Y2, tag='IfDustDone'); G.link(dl, 'then', bd, 'execute')
ct = b.lib(KSL, 'K2_ClearTimer', [ob('Object', OBJ), S('FunctionName', default='DustPuff')], 1150, Y2, tag='StopDust')
b.wire(b.self_node(1000, Y2 + 200), ct, 'Object'); G.link(bd, 'then', ct, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('bad %s dup %s' % (bad[:8], [n for n in names if names.count(n) > 1][:5]))
open(os.path.join(HERE, 'BP_BreachFX_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_BreachFX_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))
VARS = [('HideRubble', 'PinCategory="bool"', 'true', 'hide the natural-boulder Rubble* parts of every breach spot'),
        ('CollapseClass', 'PinCategory="class",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'"', '', "TGA's baked collapse (#327) once it exists; empty = Brk* pieces fall with physics"),
        ('Spots', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",ContainerType=Array', '', 'state'),
        ('WasBroken', 'PinCategory="bool",ContainerType=Array', '', 'state'), ('Broken', 'PinCategory="bool"', 'false', 'scratch'),
        ('FxAt', 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"', '0,0,0', 'state'),
        ('DustLeft', 'PinCategory="int"', '0', 'state')]
bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'breach316/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# #316 BP_BreachFX - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpv(*v[:3]) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
