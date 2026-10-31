# #284 Realm bubble (TGA, 2026-10-31; owner whiteboard task). Blueprint-only, paste-ready.
#   BP_Cannonball (manifest_cannonball.json): a cannonball that hits an actor tagged RealmBubble (the realm dome) bounces
#     off once - mirrored on the hit normal, half speed, forced downward so it lands outside - and the dome ripples; the
#     ball then explodes on the ground as usual. (Projectile movement stops itself after a blocking hit, so the bounce is
#     re-armed 0.02 s later by a timer: SetUpdatedComponent(Ball) + Velocity + Activate.)
#   BP_RealmDirector (new Actor; the setup script places one): Ripple(HitLocation) flash on the dome; Think (1 s):
#     soldiers inside the dome march on the nearest living tentacle (BP_TentacleVitals) and every soldier within HitRange
#     takes SoldierDPS a second off its Health - the only way to hurt the tentacles, since the dome turns cannon fire away;
#     a tentacle at 0 falls (hidden, notice); when TentaclesToKill have fallen the realm collapses: notice, bursts, the dome
#     shrinks away over 4 s, every realm actor (tag laptop2_realm) is hidden + collision off, PPV_Realm (tag RealmPPV) removed.
#   python gen284.py
import os, sys, json
sys.dont_write_bytecode = True
HERE284 = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE284, '..', 'farm-223', 'gen223.py'), encoding='utf-8').read()
_g = _src[:_src.index('# ================================================================ BP_FarmPlot')].replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = HERE284')
__file__ = os.path.join(HERE284, '..', 'farm-223', 'gen223.py'); exec(_g); __file__ = os.path.join(HERE284, 'gen284.py')
HERE = HERE284

P_RDIR = '/Game/CastleDefender/Gameplay/Realm/BP_RealmDirector'; RDIRC = BPC(P_RDIR, 'BP_RealmDirector')
P_VIT = '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals'; VITC = BPC(P_VIT, 'BP_TentacleVitals')
P_BALL = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannonball'; BALLC = BPC(P_BALL, 'BP_Cannonball')
PMC, SPHC = CLS('ProjectileMovementComponent'), CLS('SphereComponent')
ACTV = ob('v', ACT)
def emitter(b, loc, scale, x, y, tag='FX'):
    n = b.lib(GS, 'SpawnEmitterAtLocation', [WC(), dict(ob('EmitterTemplate', PSYS), dobj=P_SMOKE), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
              V('Scale', default=scale), bo('bAutoDestroy', default='true'), {'name': 'PoolingMethod', 'cat': 'byte', 'obj': ENUM('EPSCPoolMethod'), 'default': 'None'},
              bo('bAutoActivateSystem', default='true'), ob('ReturnValue', PSC, out=True)], x, y, tag=tag)
    b.wire(loc, n, 'Location'); return n
def has_tag(b, actor, tag, x, y):
    n = b.call(ACT, 'ActorHasTag', [N('Tag', default=tag), bo('ReturnValue', out=True, default='false')], x, y, target=actor, pure=True, const=True, tag='Has' + tag)
    return (n, 'ReturnValue')

# ================================================================ BP_Cannonball insert
G = Graph(); b = B(G, 'rb'); b.imp = B(G, 'rbQ')
EV = 'CX_1'                                   # the cannonball's Event Hit (Other, HitLocation, HitNormal) in the 10-30b export
pm = lambda x, y: b.get('ProjectileMovement', ob('v', PMC), x, y)
ht = has_tag(b, None, 'RealmBubble', 0, 300)                      # CX_1.Other is wired in by the manifest
bb = b.branch(b.b2('BooleanAND', ht, b.bnot(b.get('Bounced', BOOL, 0, 450), 200, 450), 400, 350), 300, 0, 'IfBubble')
sbd = b.set('Bounced', bo('v', default='true'), None, 600, -300); G.link(bb, 'then', sbd, 'execute')
vel = b.getm('Velocity', PMC, VECT, pm(450, 100), 650, 100)
mir = b.math('MirrorVectorByNormal', [(V('InVect'), vel), (V('InNormal'), None)], V('ReturnValue', out=True), 850, 100)   # InNormal <- CX_1.HitNormal (manifest)
hv = b.brk(b.math('Multiply_VectorFloat', [(V('A'), mir), (fl('B', default='0.5'), None)], V('ReturnValue', out=True), 1050, 100), 1250, 100)
down = b.d2('Subtract_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), hv['Z'])], D('ReturnValue', out=True), 1450, 250), None, 1650, 250, db='200.0', )
newv = b.vec(hv['X'], hv['Y'], b.d2('Multiply_DoubleDouble', down, None, 1850, 250, db='-1.0'), 2050, 150)
sbv = b.set('BounceVel', VECT, newv, 900, -300); G.link(sbd, 'then', sbv, 'execute')
rd = (b.imp.actor_of(P_RDIR, RDIRC, 1100, -50), 'ReturnValue')
rp = b.call(RDIRC, 'Ripple', [V('At')], 1300, -300, target=rd, tag='Ripple')   # At <- CX_1.HitLocation (manifest)
G.link(sbv, 'then', rp, 'execute')
G.link(rp, 'then', b.timer('RealmRebound', 1600, -300, dtime='0.02'), 'execute')
Y = 900
b.event('RealmRebound', [], 0, Y)
su = b.call(CLS('MovementComponent'), 'SetUpdatedComponent', [ob('NewUpdatedComponent', SCENE)], 300, Y, target=pm(150, Y + 200), tag='Rearm')
b.wire(b.get('Ball', ob('v', SPHC), 150, Y + 350), su, 'NewUpdatedComponent'); G.link('RealmRebound', 'then', su, 'execute')
sv = b.setm('Velocity', PMC, VECT, b.get('BounceVel', VECT, 450, Y + 350), pm(450, Y + 200), 600, Y); G.link(su, 'then', sv, 'execute')
G.link(sv, 'then', b.call(CLS('ActorComponent'), 'Activate', [bo('bReset', default='false')], 900, Y, target=pm(750, Y + 200), tag='Fly'), 'execute')
write('Cannonball_RealmBounce_graph.txt', G)
json.dump({'blueprint': 'BP_Cannonball', 'pastes': ['Cannonball_RealmBounce_graph.txt'], 'rewires': [
    {'from': 'CX_1.then', 'to': bb + '.execute', 'replace': True, 'note': 'Event Hit first asks: did we hit the realm dome? (was -> CX_255)'},
    {'from': bb + '.else', 'to': 'CX_255.execute', 'note': 'no -> the ball explodes as before'},
    {'from': 'CX_1.Other', 'to': ht[0] + '.self', 'note': 'what the ball hit'},
    {'from': 'CX_1.HitNormal', 'to': mir[0] + '.InNormal', 'note': 'bounce off the dome surface'},
    {'from': 'CX_1.HitLocation', 'to': rp + '.At', 'note': 'ripple where it hit'}]},
    open(os.path.join(HERE, 'manifest_cannonball.json'), 'w'), indent=1)

# ================================================================ BP_RealmDirector
G = Graph(); b = B(G, 'rd'); b.imp = B(G, 'rdQ')
bp = b.override('RealmBeginPlay', 'ReceiveBeginPlay', 0, 0)
G.link(bp, 'then', b.timer('Think', 300, 0, dtime='1.0', loop=True), 'execute')
# ---- Ripple(At): flash where the ball hit the dome
Y = 500
b.event('Ripple', [V('At')], 0, Y)
G.link('Ripple', 'then', emitter(b, ('Ripple', 'At'), '4.000000,4.000000,4.000000', 300, Y, 'RippleFX'), 'execute')
# ---- Think
Y = 1200
b.event('Think', [], 0, Y)
bc = b.branch(b.get('Collapsed', BOOL, 0, Y + 250), 250, Y, 'IfGone'); G.link('Think', 'then', bc, 'execute')
dm = b.imp.lib(GS, 'GetAllActorsWithTag', [WC(), N('Tag', default='RealmBubble'), arr(ob('OutActors', ACT, out=True))], 500, Y, tag='Dome')
G.link(bc, 'else', dm, 'execute')
dome = item(b, (dm, 'OutActors'), ACTV, None, 750, Y + 300)
bdv = b.branch(b.valid(dome, 900, Y + 300), 900, Y, 'IfDome'); G.link(dm, 'then', bdv, 'execute')
sdome = b.set('Dome', ACTV, dome, 1150, Y); G.link(bdv, 'then', sdome, 'execute')
bnd = b.call(ACT, 'GetActorBounds', [bo('bOnlyCollidingComponents', default='false'), V('Origin', out=True), V('BoxExtent', out=True), bo('bIncludeFromChildActors', default='false')],
             1150, Y + 400, target=b.get('Dome', ACTV, 1000, Y + 450), const=True, tag='DomeBox')
G.link(sdome, 'then', bnd, 'execute')
so = b.set('DomeOrigin', VECT, (bnd, 'Origin'), 1450, Y); G.link(bnd, 'then', so, 'execute')
se = b.set('DomeExtent', VECT, (bnd, 'BoxExtent'), 1700, Y); G.link(so, 'then', se, 'execute')
sol = b.imp.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SOLDIER)), arr(ob('OutActors', SOLDIER, out=True))], 1950, Y, tag='Soldiers')
G.link(se, 'then', sol, 'execute')
ssol = b.set('Soldiers', arr(ACTV), (sol, 'OutActors'), 2250, Y); G.link(sol, 'then', ssol, 'execute')
vit = b.imp.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_VIT)), arr(ob('OutActors', VITC, out=True))], 2500, Y, tag='Tentacles')
G.link(ssol, 'then', vit, 'execute')
fv = b.foreach(VITC, 2850, Y); b.wire((vit, 'OutActors'), fv, 'Array'); G.link(vit, 'then', fv, 'Exec')
v = (fv, 'Array Element')
alive = b.b2('BooleanAND', b.bnot(has_tag(b, v, 'RealmTentacleDead', 3000, Y + 300), 3200, Y + 300),
             b.dcmp('Greater_DoubleDouble', b.getm('Health', VITC, DBL, v, 3000, Y + 450), None, 3200, Y + 450), 3400, Y + 350)
bal = b.branch(alive, 3200, Y, 'IfAlive'); G.link(fv, 'LoopBody', bal, 'execute')
# soldiers inside the dome: march on this tentacle, hack at it within HitRange
fs = b.foreach(ACT, 3500, Y); b.wire(b.get('Soldiers', arr(ACTV), 3350, Y + 300), fs, 'Array'); G.link(bal, 'then', fs, 'Exec')
s = (fs, 'Array Element')
sl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 3700, Y + 400, target=s, pure=True, const=True, tag='SolAt')
d = b.brk(b.v2('Subtract_VectorVector', (sl, 'ReturnValue'), b.get('DomeOrigin', VECT, 3700, Y + 550), 3900, Y + 450), 4100, Y + 450)
ext = b.brk(b.get('DomeExtent', VECT, 3900, Y + 700), 4100, Y + 700)
rx = b.d2('Divide_DoubleDouble', d['X'], ext['X'], 4300, Y + 450); ry = b.d2('Divide_DoubleDouble', d['Y'], ext['Y'], 4300, Y + 600)
inside = b.dcmp('Less_DoubleDouble', b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', rx, rx, 4500, Y + 450), b.d2('Multiply_DoubleDouble', ry, ry, 4500, Y + 600), 4700, Y + 500),
                None, 4900, Y + 500, db='1.0')
bin_ = b.branch(inside, 3850, Y, 'IfInside'); G.link(fs, 'LoopBody', bin_, 'execute')
dvs = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 4100, Y - 300, target=s, pure=True, const=True, tag='DistTentacle'); b.wire(v, dvs, 'OtherActor')
bhit = b.branch(b.dcmp('Less_DoubleDouble', (dvs, 'ReturnValue'), b.get('HitRange', D('v', default='450.0'), 4100, Y - 150), 4300, Y - 250), 4100, Y, 'IfInReach')
G.link(bin_, 'then', bhit, 'execute')
hp = b.setm('Health', VITC, DBL, b.d2('Subtract_DoubleDouble', b.getm('Health', VITC, DBL, v, 4350, Y - 450), b.get('SoldierDPS', D('v', default='25.0'), 4350, Y - 600), 4550, Y - 500), v, 4400, Y - 200)
G.link(bhit, 'then', hp, 'execute')
sctl = b.call(PAWN, 'GetController', [ob('ReturnValue', CTRL, out=True)], 4350, Y + 300, target=s, pure=True, const=True, tag='SolCtl')
mv = b.lib(NAVSYS, 'SimpleMoveToActor', [ob('Controller', CTRL), ob('Goal', ACT)], 4500, Y + 100, tag='MarchOn')
b.wire((sctl, 'ReturnValue'), mv, 'Controller'); b.wire(v, mv, 'Goal'); G.link(bhit, 'else', mv, 'execute')
# after the soldiers: did it fall?
bfall = b.branch(b.dcmp('LessEqual_DoubleDouble', b.getm('Health', VITC, DBL, v, 3600, Y + 1100), None, 3800, Y + 1100, db='0.0'), 3800, Y + 900, 'IfFell')
G.link(fs, 'Completed', bfall, 'execute')
tags = b.getm('Tags', ACT, arr(N('v')), v, 4000, Y + 1150)
tad = b.name('TagDead'); G.node(tad, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Add")' % KARR],
                                [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
                                 {'name': 'NewItem', 'cat': 'wildcard', 'ref': True, 'default': 'RealmTentacleDead'}, it('ReturnValue', out=True, default='0')], 4200, Y + 900)
b.wire(tags, tad, 'TargetArray'); G.link(bfall, 'then', tad, 'execute')
dk = b.set('DeadCount', INT, b.i2('Add_IntInt', b.get('DeadCount', INT, 4450, Y + 1150), None, 4650, Y + 1150, db='1'), 4500, Y + 900); G.link(tad, 'then', dk, 'execute')
par = b.call(ACT, 'GetAttachParentActor', [ob('ReturnValue', ACT, out=True)], 4700, Y + 1300, target=v, pure=True, const=True, tag='TentacleActor')
hid = b.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='true')], 4800, Y + 900, target=(par, 'ReturnValue'), tag='HideTentacle'); G.link(dk, 'then', hid, 'execute')
ncol = b.call(ACT, 'SetActorEnableCollision', [bo('bNewActorEnableCollision', default='false')], 5100, Y + 900, target=(par, 'ReturnValue'), tag='NoCollide'); G.link(hid, 'then', ncol, 'execute')
fx = emitter(b, (b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 5200, Y + 1300, target=v, pure=True, const=True, tag='TentAt'), 'ReturnValue'), '5.000000,5.000000,5.000000', 5400, Y + 900, 'FallFX')
G.link(ncol, 'then', fx, 'execute')
istr = lambda src, x, y: b.math('Conv_IntToString', [(it('InInt', default='0'), src)], S('ReturnValue', out=True), x, y)
txt = b.concat(b.concat(b.concat(None, istr(b.get('DeadCount', INT, 5500, Y + 1600), 5700, Y + 1600), 5900, Y + 1600, da='A TENTACLE FALLS  ('), None, 6100, Y + 1600, db=' / '),
               istr(b.get('TentaclesToKill', it('v', default='2'), 6100, Y + 1750), 6300, Y + 1750), 6500, Y + 1650)
txt = b.concat(txt, None, 6700, Y + 1650, db=')')
nh = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], 5700, Y + 1900, target=pc(b, 5500, Y + 1900), pure=True, const=True, tag='HUD')
nc, nhh = notice_hud(b, (nh, 'ReturnValue'), 5800, Y + 900); G.link(fx, 'then', nc, 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='2')], 6200, Y + 900, target=nhh, tag='Fell'); b.wire(txt, pn, 'Text'); G.link(nc, 'then', pn, 'execute')
ball = b.branch(b.icmp('GreaterEqual_IntInt', b.get('DeadCount', INT, 6300, Y + 1200), b.get('TentaclesToKill', it('v', default='2'), 6300, Y + 1350), 6500, Y + 1250), 6500, Y + 900, 'IfAllDead')
G.link(pn, 'then', ball, 'execute'); G.link(ball, 'then', b.call_self('Collapse', [], 6800, Y + 900, RDIRC, tag='CallCollapse'), 'execute')

# ---- Collapse: notice, bursts, the dome shrinks away (FadeStep), then the realm is hidden and PPV_Realm removed
Y = 3800
b.event('Collapse', [], 0, Y)
c1 = b.set('Collapsed', bo('v', default='true'), None, 250, Y); G.link('Collapse', 'then', c1, 'execute')
nh = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], 400, Y + 300, target=pc(b, 200, Y + 300), pure=True, const=True, tag='HUD')
nc, nhh = notice_hud(b, (nh, 'ReturnValue'), 500, Y); G.link(c1, 'then', nc, 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text', default='THE REALM COLLAPSES! The land is free again.'), it('Tier', default='3')], 900, Y, target=nhh, tag='Freed'); G.link(nc, 'then', pn, 'execute')
fx1 = emitter(b, b.get('DomeOrigin', VECT, 1000, Y + 300), '20.000000,20.000000,20.000000', 1200, Y, 'CollapseFX'); G.link(pn, 'then', fx1, 'execute')
ds = b.call(ACT, 'GetActorScale3D', [V('ReturnValue', out=True)], 1300, Y + 300, target=b.get('Dome', ACTV, 1150, Y + 450), pure=True, const=True, tag='DomeScale')
s3 = b.set('DomeScale', VECT, (ds, 'ReturnValue'), 1500, Y); G.link(fx1, 'then', s3, 'execute')
G.link(s3, 'then', b.timer('FadeStep', 1800, Y, dtime='0.05', loop=True), 'execute')
Y = 4600
b.event('FadeStep', [], 0, Y)
ft = b.set('FadeT', DBL, b.d2('Add_DoubleDouble', b.get('FadeT', DBL, 0, Y + 300), None, 200, Y + 300, db='0.0125'), 300, Y)      # 4 s
G.link('FadeStep', 'then', ft, 'execute')
k = b.math('FMax', [(D('A', default='0.0'), b.d2('Subtract_DoubleDouble', None, b.get('FadeT', DBL, 400, Y + 450), 600, Y + 450, da='1.0')), (D('B', default='0.0'), None)], D('ReturnValue', out=True), 800, Y + 450)
ns = b.math('Multiply_VectorFloat', [(V('A'), b.get('DomeScale', VECT, 800, Y + 300)), (fl('B', default='1.0'), k)], V('ReturnValue', out=True), 1000, Y + 350)
sc = b.call(ACT, 'SetActorScale3D', [V('NewScale3D')], 1200, Y, target=b.get('Dome', ACTV, 1050, Y + 200), tag='Shrink'); b.wire(ns, sc, 'NewScale3D'); G.link(ft, 'then', sc, 'execute')
bend = b.branch(b.dcmp('GreaterEqual_DoubleDouble', b.get('FadeT', DBL, 1300, Y + 300), None, 1500, Y + 300, db='1.0'), 1500, Y, 'IfFaded'); G.link(sc, 'then', bend, 'execute')
ct = b.timer_fn('K2_ClearTimer', 'FadeStep', 1800, Y); G.link(bend, 'then', ct, 'execute')
ra = b.imp.lib(GS, 'GetAllActorsWithTag', [WC(), N('Tag', default='laptop2_realm'), arr(ob('OutActors', ACT, out=True))], 2100, Y, tag='RealmActors'); G.link(ct, 'then', ra, 'execute')
fr = b.foreach(ACT, 2400, Y); b.wire((ra, 'OutActors'), fr, 'Array'); G.link(ra, 'then', fr, 'Exec')
h1 = b.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='true')], 2700, Y, target=(fr, 'Array Element'), tag='Hide'); G.link(fr, 'LoopBody', h1, 'execute')
G.link(h1, 'then', b.call(ACT, 'SetActorEnableCollision', [bo('bNewActorEnableCollision', default='false')], 3000, Y, target=(fr, 'Array Element'), tag='NoCollide'), 'execute')
pp = b.imp.lib(GS, 'GetAllActorsWithTag', [WC(), N('Tag', default='RealmPPV'), arr(ob('OutActors', ACT, out=True))], 2700, Y + 400, tag='PPV'); G.link(fr, 'Completed', pp, 'execute')
fp = b.foreach(ACT, 3000, Y + 400); b.wire((pp, 'OutActors'), fp, 'Array'); G.link(pp, 'then', fp, 'Exec')
G.link(fp, 'LoopBody', b.call(ACT, 'K2_DestroyActor', [], 3300, Y + 400, target=(fp, 'Array Element'), tag='NoPPV'), 'execute')
write('BP_RealmDirector_graph.txt', G)

import subprocess
for gname, pfx in (('Cannonball_RealmBounce', 'rbQ'), ('BP_RealmDirector', 'rdQ')):
    p = os.path.join(HERE, gname + '_graph.txt')
    subprocess.run([sys.executable, os.path.join(HERE, '..', '..', 'tools', 'applyall', 'fix_impure.py'), p, p, pfx], check=True, capture_output=True)
print('fix_impure done')


# ================================================================ VARIABLES.md
T_INT, T_BOOL, T_DBL = '(PinCategory="int")', '(PinCategory="bool")', '(PinCategory="real",PinSubCategory="double")'
T_VEC = '(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'")'
T_ACT = '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'")'
T_ARR = '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",ContainerType=Array)'
VARS = [('BP_Cannonball', 'Bounced', T_BOOL, 'False', 'already bounced off the dome once'), ('BP_Cannonball', 'BounceVel', T_VEC, '', 'velocity after the bounce'),
        ('BP_RealmDirector', 'Collapsed', T_BOOL, 'False', 'the realm is gone'), ('BP_RealmDirector', 'Dome', T_ACT, '', 'the dome actor (tag RealmBubble)'),
        ('BP_RealmDirector', 'DomeOrigin', T_VEC, '', 'dome bounds centre'), ('BP_RealmDirector', 'DomeExtent', T_VEC, '', 'dome bounds half size'),
        ('BP_RealmDirector', 'DomeScale', T_VEC, '', 'dome scale when the collapse starts'), ('BP_RealmDirector', 'Soldiers', T_ARR, '', 'scratch'),
        ('BP_RealmDirector', 'DeadCount', T_INT, '0', 'tentacles fallen'), ('BP_RealmDirector', 'TentaclesToKill', T_INT, '2', 'falls needed for the collapse'),
        ('BP_RealmDirector', 'SoldierDPS', T_DBL, '25.0', 'Health per second each soldier in reach takes off a tentacle'),
        ('BP_RealmDirector', 'HitRange', T_DBL, '450.0', 'cm: soldier reach to a tentacle'), ('BP_RealmDirector', 'FadeT', T_DBL, '0.0', 'collapse progress 0..1')]
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', encoding='utf-8') as fo:
    fo.write('# Variables for #284\n\n| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bpn, n, t, d, m in VARS: fo.write('| %s | %s | %s | %s |\n' % (bpn, n, d or '-', m))
    cur = None
    for k, (bpn, n, t, d, m) in enumerate(VARS):
        if bpn != cur: fo.write('%s\n### %s\n```\n' % ('```\n' if cur else '', bpn)); cur = bpn
        fo.write('BPVar(VarName="%s",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E%03X,VarType=%s,FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5%s)\n'
                 % (n, k, t, n, (',DefaultValue="%s"' % d) if d else ''))
    fo.write('```\n')
print('VARIABLES.md', len(VARS))
