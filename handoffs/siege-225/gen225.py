# #225 Siege engines gameplay (TGA, 2026-10-31; owner assignment): Blueprint-only, paste-ready.
#   BP_SiegeEngine   (new Character, parent of BP_SiegeRam / BP_SiegeTower, which only set defaults)
#     BeginPlay: Body mesh = IntactMesh (yaw MeshYaw so the engine's front is +X), tower: Bridge snapped to the Body's
#                Bridge_Hinge socket and raised; spawns 4 big zombies (scale PusherScale) attached at Push_0..3.
#     Think (0.5 s): living pushers -> speed BaseSpeed * n / 4 (none -> it stops); burning -> BurnDPS;
#       ram:   walks the NavMesh to BP_CastleGateControl; within 7 m: every GatePeriod adds RamHit / (1 + 0.5 ForgeGate)
#              to the wave manager's GateDamage (the same 0..100 gauge zombies fill; 100 = breach), min 100.
#       tower: walks to its WallPoint (a TargetPoint tagged SiegeWall, on the wall walk); within 7 m it stops, lowers the
#              bridge over 2 s, then spills SpillLeft zombies onto the wall walk (at WallPoint) every SpillPeriod.
#     AnyDamage: HP; a cannonball hit counts CannonMult times and sets it burning (wood) for 6 s.
#     Break (HP 0): wreck mesh, bridge hidden, stops, pushers let go (they fight on), smoke; the wreck stays (debris).
#   BP_SiegeDirector (new Actor, placed outside the walls where engines should appear)
#     Poll (2 s): on each new wave at night: wave >= RamFromWave -> a ram; wave >= TowerFromWave -> a tower too
#     (towers take the nearest SiegeWall point).
#   python gen225.py   (Blender's python works: U:\5.2\python\bin\python.exe gen225.py)
import os, sys, json
sys.dont_write_bytecode = True
HERE225 = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE225, '..', 'farm-223', 'gen223.py'), encoding='utf-8').read()
_g = _src[:_src.index('# ================================================================ BP_FarmPlot')].replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = HERE225')
__file__ = os.path.join(HERE225, '..', 'farm-223', 'gen223.py'); exec(_g); __file__ = os.path.join(HERE225, 'gen225.py')
HERE = HERE225

P_SIEGE = '/Game/CastleDefender/Gameplay/Siege/'
P_ENG, P_RAM, P_TOWER, P_SDIR = P_SIEGE + 'BP_SiegeEngine', P_SIEGE + 'BP_SiegeRam', P_SIEGE + 'BP_SiegeTower', P_SIEGE + 'BP_SiegeDirector'
ENGC, RAMC, TOWERC = BPC(P_ENG, 'BP_SiegeEngine'), BPC(P_RAM, 'BP_SiegeRam'), BPC(P_TOWER, 'BP_SiegeTower')
P_GATE = P_CASTLE + 'BP_CastleGateControl'; GATEC = BPC(P_GATE, 'BP_CastleGateControl')
P_BALL = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannonball'
BALLC = BPC(P_BALL, 'BP_Cannonball')
RULE = lambda n, d='SnapToTarget': {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', 'default': d}
DRULE = lambda n: {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EDetachmentRule\'"', 'default': 'KeepWorld'}
SMV = ob('v', SMC); ACTV = ob('v', ACT)


def gate_hit(b, amount, x, y):
    """WM.GateDamage = min(GateDamage + amount / (1 + 0.5 HUD.ForgeGate), 100). Returns (first, last) exec."""
    wm = (b.imp.actor_of(P_WM, WM, x, y + 300), 'ReturnValue')
    zc, zh, _ = zhud(b, x, y)
    fg = b.i2d(b.getm('ForgeGate', HUDC, INT, zh, x + 300, y + 600), x + 500, y + 600)
    div = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', fg, None, x + 700, y + 600, db='0.5'), None, x + 900, y + 600, db='1.0')
    hit = b.d2('Divide_DoubleDouble', amount, div, x + 1100, y + 500)
    new = b.math('FMin', [(D('A', default='0.0'), b.d2('Add_DoubleDouble', b.getm('GateDamage', WM, DBL, wm, x + 1100, y + 300), hit, x + 1300, y + 350)),
                          (D('B', default='100.0'), None)], D('ReturnValue', out=True), x + 1500, y + 350)
    s = b.setm('GateDamage', WM, DBL, new, wm, x + 1700, y)
    b.G.link(zc, 'then', s, 'execute')
    return zc, s


def spawn_zombie(b, loc, scale, x, y):
    xf = b.math('MakeTransform', [(V('Location'), loc), (st('Rotation', ROT, default='0, 0, 0'), None), (V('Scale', default='1.000000,1.000000,1.000000'), scale)], st('ReturnValue', XFORM, out=True), x, y + 300)
    return spawn(b, P_ZOMBIE, ZOMBIE, xf, x + 250, y)


# ================================================================ BP_SiegeEngine
G = Graph(); b = B(G, 'se'); b.imp = B(G, 'seQ')
body = lambda x, y: b.get('Body', SMV, x, y)
bridge = lambda x, y: b.get('Bridge', SMV, x, y)
kind = lambda x, y: b.get('Kind', INT, x, y)
dead = lambda x, y: b.get('Dead', BOOL, x, y)
cmc = lambda x, y: b.get('CharacterMovement', ob('v', CMC), x, y)
bp = b.override('EngineBeginPlay', 'ReceiveBeginPlay', 0, 0)
s_hp = b.set('HP', DBL, b.get('MaxHP', D('v', default='900.0'), 100, 250), 300, 0); G.link(bp, 'then', s_hp, 'execute')
sm = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SM), bo('ReturnValue', out=True, default='false')], 600, 0, target=body(450, 250), tag='Intact')
b.wire(b.get('IntactMesh', ob('v', SM), 450, 400), sm, 'NewMesh'); G.link(s_hp, 'then', sm, 'execute')
rot = b.math('MakeRotator', [(D('Roll', default='0.0'), None), (D('Pitch', default='0.0'), None), (D('Yaw', default='0.0'), b.get('MeshYaw', DBL, 700, 550))], st('ReturnValue', ROT, out=True), 900, 550)
sr = b.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], 900, 0, target=body(800, 250), tag='MeshYaw')
b.wire(rot, sr, 'NewRotation'); G.link(sm, 'then', sr, 'execute')
btw = b.branch(eqi(b, kind(1000, 300), 1, 1200, 300), 1200, 0, 'IfTower'); G.link(sr, 'then', btw, 'execute')
bm = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SM), bo('ReturnValue', out=True, default='false')], 1500, -300, target=bridge(1350, -100), tag='BridgeMesh')
b.wire(b.get('BridgeMesh', ob('v', SM), 1350, 50), bm, 'NewMesh'); G.link(btw, 'then', bm, 'execute')
at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName', default='Bridge_Hinge'), RULE('LocationRule'), RULE('RotationRule'), RULE('ScaleRule', 'KeepWorld'),
            bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], 1800, -300, target=bridge(1650, -100), tag='BridgeHinge')
b.wire(body(1650, 0), at, 'Parent'); G.link(bm, 'then', at, 'execute')
up = b.call_self('ApplyBridge', [], 2100, -300, ENGC, tag='CallApplyBridge'); G.link(at, 'then', up, 'execute')
hb = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 1500, 200, target=bridge(1350, 400), tag='NoBridge')
G.link(btw, 'else', hb, 'execute')
# pushers: 4 big zombies at Push_0..3 (sockets on the art, behind the engine), movement off, attached
floop = b.name('ForLoop'); G.node(floop, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FORLOOP],
                               [ex(), it('FirstIndex', default='0'), it('LastIndex', default='3'), ex('LoopBody', True), it('Index', out=True), ex('Completed', True)], 2400, 0)
G.link(up, 'then', floop, 'execute'); G.link(hb, 'then', floop, 'execute')
sock = b.math('Conv_StringToName', [(S('InString'), b.concat(None, b.math('Conv_IntToString', [(it('InInt', default='0'), (floop, 'Index'))], S('ReturnValue', out=True), 2400, 500), 2600, 450, da='Push_'))],
              {'name': 'ReturnValue', 'cat': 'name', 'out': True}, 2800, 450)
sl = b.call(SCENE, 'GetSocketLocation', [N('InSocketName'), V('ReturnValue', out=True)], 3000, 400, target=body(2850, 300), pure=True, const=True, tag='PushAt')
b.wire(sock, sl, 'InSocketName')
ps = b.get('PusherScale', D('v', default='1.25'), 3000, 650)
scl = b.vec(ps, ps, ps, 3200, 650)
sz = spawn_zombie(b, (sl, 'ReturnValue'), scl, 3300, 0); G.link(floop, 'LoopBody', sz, 'execute')
zp = (sz, 'ReturnValue')
dm = b.call(CMC, 'DisableMovement', [], 3700, 0, target=b.getm('CharacterMovement', CHARC, ob('v', CMC), zp, 3550, 250), tag='PusherStill')
G.link(sz, 'then', dm, 'execute')
ap = b.call(ACT, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName'), RULE('LocationRule', 'KeepWorld'), RULE('RotationRule', 'KeepWorld'), RULE('ScaleRule', 'KeepWorld'),
            bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], 4000, 0, target=zp, tag='PusherAttach')
b.wire(body(3850, 250), ap, 'Parent'); b.wire(sock, ap, 'SocketName'); G.link(dm, 'then', ap, 'execute')
G.link(ap, 'then', b.aadd('Pushers', ACTV, zp, 4300, 0), 'execute')
G.link(floop, 'Completed', b.timer('Think', 2700, 900, dtime='0.5', loop=True), 'execute')

# ---- ApplyBridge: Bridge relative roll = BridgeUpRoll * (1 - BridgeT)  (0 = down / deployed)
Y = 1400
b.event('ApplyBridge', [], 0, Y)
roll = b.d2('Multiply_DoubleDouble', b.get('BridgeUpRoll', D('v', default='90.0'), 0, Y + 300), b.d2('Subtract_DoubleDouble', None, b.get('BridgeT', DBL, 0, Y + 450), 200, Y + 450, da='1.0'), 400, Y + 350)
br = b.math('MakeRotator', [(D('Roll', default='0.0'), roll), (D('Pitch', default='0.0'), None), (D('Yaw', default='0.0'), None)], st('ReturnValue', ROT, out=True), 600, Y + 350)
sb = b.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], 800, Y, target=bridge(650, Y + 200), tag='BridgeRoll')
b.wire(br, sb, 'NewRotation'); G.link('ApplyBridge', 'then', sb, 'execute')

# ---- Think
Y = 2200
b.event('Think', [], 0, Y)
bd = b.branch(dead(0, Y + 250), 250, Y, 'IfDead'); G.link('Think', 'then', bd, 'execute')
s0 = b.set('Alive', INT, None, 500, Y); G.link(bd, 'else', s0, 'execute')
fe = b.foreach(ACT, 750, Y); b.wire(b.get('Pushers', arr(ACTV), 600, Y + 300), fe, 'Array'); G.link(s0, 'then', fe, 'Exec')
pz = b.name('AsPusher'); cast(G, pz, ZOMBIE, 'AsBP Zombie', 1100, Y); b.wire((fe, 'Array Element'), pz, 'Object'); G.link(fe, 'LoopBody', pz, 'execute')
bpd = b.branch(b.getm('Dead', ZOMBIE, BOOL, (pz, 'AsBP Zombie'), 1300, Y + 300), 1450, Y, 'IfPusherDead'); G.link(pz, 'then', bpd, 'execute')
det = b.call(ACT, 'K2_DetachFromActor', [DRULE('LocationRule'), DRULE('RotationRule'), DRULE('ScaleRule')], 1750, Y - 200, target=(pz, 'AsBP Zombie'), tag='DropDead')
G.link(bpd, 'then', det, 'execute')
G.link(bpd, 'else', b.set('Alive', INT, b.i2('Add_IntInt', b.get('Alive', INT, 1600, Y + 400), None, 1800, Y + 400, db='1'), 1750, Y + 150), 'execute')
spd = b.d2('Multiply_DoubleDouble', b.get('BaseSpeed', D('v', default='120.0'), 1500, Y + 900),
           b.d2('Divide_DoubleDouble', b.i2d(b.get('Alive', INT, 1500, Y + 1050), 1700, Y + 1050), None, 1900, Y + 1050, db='4.0'), 2100, Y + 950)
ms = b.setm('MaxWalkSpeed', CMC, fl('v', default='0.0'), spd, cmc(2150, Y + 700), 2300, Y + 500); G.link(fe, 'Completed', ms, 'execute')
# burning
now = lambda x, y: b.now(x, y)
bburn = b.branch(b.dcmp('Less_DoubleDouble', now(2500, Y + 700), b.get('BurnUntil', DBL, 2500, Y + 850), 2700, Y + 750), 2600, Y + 500, 'IfBurning')
G.link(ms, 'then', bburn, 'execute')
bhp = b.set('HP', DBL, b.d2('Subtract_DoubleDouble', b.get('HP', DBL, 2800, Y + 300), b.d2('Multiply_DoubleDouble', b.get('BurnDPS', D('v', default='15.0'), 2800, Y + 150), None, 3000, Y + 150, db='0.5'), 3000, Y + 300), 2900, Y)
G.link(bburn, 'then', bhp, 'execute')
here = lambda x, y: (b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='Here'), 'ReturnValue')
fx = b.lib(GS, 'SpawnEmitterAtLocation', [WC(), dict(ob('EmitterTemplate', PSYS), dobj=P_SMOKE), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
           V('Scale', default='1.500000,1.500000,1.500000'), bo('bAutoDestroy', default='true'),
           {'name': 'PoolingMethod', 'cat': 'byte', 'obj': ENUM('EPSCPoolMethod'), 'default': 'None'}, bo('bAutoActivateSystem', default='true'), ob('ReturnValue', PSC, out=True)], 3200, Y, tag='BurnSmoke')
b.wire(b.v2('Add_VectorVector', here(3000, Y + 500), None, 3200, Y + 500, db='0, 0, 150'), fx, 'Location'); G.link(bhp, 'then', fx, 'execute')
bk = b.branch(b.dcmp('LessEqual_DoubleDouble', b.get('HP', DBL, 3400, Y + 300), None, 3600, Y + 300, db='0.0'), 3500, Y, 'IfBurnt')
G.link(fx, 'then', bk, 'execute'); G.link(bk, 'then', b.call_self('Break', [], 3800, Y - 150, ENGC, tag='CallBreak'), 'execute')
bkind = b.branch(eqi(b, kind(3800, Y + 900), 0, 4000, Y + 900), 3900, Y + 600, 'IfRam')
G.link(bk, 'else', bkind, 'execute'); G.link(bburn, 'else', bkind, 'execute')
G.link(bkind, 'then', b.call_self('RamThink', [], 4200, Y + 450, ENGC, tag='CallRam'), 'execute')
G.link(bkind, 'else', b.call_self('TowerThink', [], 4200, Y + 800, ENGC, tag='CallTower'), 'execute')

# ---- RamThink: walk to the gate; at the gate hit it every GatePeriod
Y = 4000
b.event('RamThink', [], 0, Y)
gate = lambda x, y: (b.imp.actor_of(P_GATE, GATEC, x, y), 'ReturnValue')
bat = b.branch(b.dcmp('Less_DoubleDouble', dist_to(b, gate(0, Y + 300), 300, Y + 300), None, 500, Y + 300, db='700.0'), 300, Y, 'IfAtGate')
G.link('RamThink', 'then', bat, 'execute')
G.link(bat, 'else', move_to(b, gate(600, Y + 650), 800, Y + 450), 'execute')
bnx = b.branch(b.dcmp('GreaterEqual_DoubleDouble', now(700, Y - 250), b.get('NextHit', DBL, 700, Y - 100), 900, Y - 150), 700, Y, 'IfSwing')
G.link(bat, 'then', bnx, 'execute')
nh = b.set('NextHit', DBL, b.d2('Add_DoubleDouble', now(950, Y + 250), b.get('GatePeriod', D('v', default='5.0'), 950, Y + 400), 1150, Y + 300), 1000, Y)
G.link(bnx, 'then', nh, 'execute')
g0, g1 = gate_hit(b, b.get('RamHit', D('v', default='20.0'), 1300, Y + 700), 1300, Y); G.link(nh, 'then', g0, 'execute')
dust = b.lib(GS, 'SpawnEmitterAtLocation', [WC(), dict(ob('EmitterTemplate', PSYS), dobj=P_SMOKE), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
             V('Scale', default='1.000000,1.000000,1.000000'), bo('bAutoDestroy', default='true'),
             {'name': 'PoolingMethod', 'cat': 'byte', 'obj': ENUM('EPSCPoolMethod'), 'default': 'None'}, bo('bAutoActivateSystem', default='true'), ob('ReturnValue', PSC, out=True)],
             3300, Y, tag='RamDust')                                       # dust burst at the gate on each hit
G.link(g1, 'then', dust, 'execute')
gl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 3100, Y + 400, target=gate(2900, Y + 400), pure=True, const=True, tag='GateAt')
b.wire((gl, 'ReturnValue'), dust, 'Location')

# ---- TowerThink: walk to the wall point; there: bridge down over 2 s, then spill zombies onto the wall walk
Y = 5600
b.event('TowerThink', [], 0, Y)
wp = lambda x, y: b.get('WallPoint', ACTV, x, y)
bwv = b.branch(b.valid(wp(0, Y + 250), 200, Y + 250), 250, Y, 'IfWallPoint'); G.link('TowerThink', 'then', bwv, 'execute')
d2 = b.call_self('GetHorizontalDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 400, Y + 300, ACT, pure=True, const=True, tag='DistWall')
b.wire(wp(250, Y + 400), d2, 'OtherActor')
bta = b.branch(b.dcmp('Less_DoubleDouble', (d2, 'ReturnValue'), None, 650, Y + 300, db='700.0'), 600, Y, 'IfAtWall'); G.link(bwv, 'then', bta, 'execute')
wl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 750, Y + 650, target=wp(600, Y + 650), pure=True, const=True, tag='WallAt')
wf = b.call(ACT, 'GetActorForwardVector', [V('ReturnValue', out=True)], 750, Y + 800, target=wp(600, Y + 800), pure=True, const=True, tag='WallOut')
goal = b.v2('Add_VectorVector', (wl, 'ReturnValue'), b.math('Multiply_VectorFloat', [(V('A'), (wf, 'ReturnValue')), (fl('B', default='450.0'), None)], V('ReturnValue', out=True), 950, Y + 800), 1150, Y + 700)
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 1150, Y + 550, PAWN, pure=True, const=True, tag='Ctl')
mvl = b.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], 1350, Y + 450, tag='ToWall')
b.wire((ctl, 'ReturnValue'), mvl, 'Controller'); b.wire(goal, mvl, 'Goal'); G.link(bta, 'else', mvl, 'execute')
stp = b.call(CMC, 'StopMovementImmediately', [], 900, Y - 300, target=cmc(750, Y - 150), tag='Stop'); G.link(bta, 'then', stp, 'execute')
bdn = b.branch(b.dcmp('Less_DoubleDouble', b.get('BridgeT', DBL, 1000, Y - 450), None, 1200, Y - 450, db='1.0'), 1200, Y - 300, 'IfBridgeUp')
G.link(stp, 'then', bdn, 'execute')
bt = b.set('BridgeT', DBL, b.math('FMin', [(D('A', default='0.0'), b.d2('Add_DoubleDouble', b.get('BridgeT', DBL, 1300, Y - 650), None, 1500, Y - 650, db='0.25')), (D('B', default='1.0'), None)],
           D('ReturnValue', out=True), 1700, Y - 650), 1500, Y - 450)          # 0.25 per 0.5 s think = 2 s
G.link(bdn, 'then', bt, 'execute'); G.link(bt, 'then', b.call_self('ApplyBridge', [], 1800, Y - 450, ENGC, tag='CallApplyBridge'), 'execute')
bsp = b.branch(b.b2('BooleanAND', b.icmp('Greater_IntInt', b.get('SpillLeft', it('v', default='10'), 1400, Y + 100), None, 1600, Y + 100, db='0'),
                    b.dcmp('GreaterEqual_DoubleDouble', now(1400, Y + 250), b.get('NextSpill', DBL, 1400, Y + 400), 1600, Y + 300), 1800, Y + 200), 1700, Y - 100, 'IfSpill')
G.link(bdn, 'else', bsp, 'execute')
ns = b.set('NextSpill', DBL, b.d2('Add_DoubleDouble', now(1900, Y + 300), b.get('SpillPeriod', D('v', default='2.5'), 1900, Y + 450), 2100, Y + 350), 2000, Y - 100)
G.link(bsp, 'then', ns, 'execute')
sl_ = b.set('SpillLeft', INT, b.i2('Subtract_IntInt', b.get('SpillLeft', INT, 2200, Y + 300), None, 2400, Y + 300, db='1'), 2300, Y - 100); G.link(ns, 'then', sl_, 'execute')
off = b.vec(b.rnd('-120.0', '120.0', 2400, Y + 500), b.rnd('-120.0', '120.0', 2400, Y + 650), None, 2600, Y + 550, dz='100.0')
spl = b.v2('Add_VectorVector', (b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 2600, Y + 300, target=wp(2450, Y + 300), pure=True, const=True, tag='SpillAt'), 'ReturnValue'), off, 2800, Y + 400)
sz2 = spawn_zombie(b, spl, None, 2700, Y - 100); G.link(sl_, 'then', sz2, 'execute')

# ---- AnyDamage: cannonballs count CannonMult times and set the wood burning for 6 s
Y = 7000
dmg = event_override(b, 'EngineAnyDamage', 'ReceiveAnyDamage', [fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CTRL), ob('DamageCauser', ACT)], 0, Y)
bdd = b.branch(dead(200, Y + 250), 250, Y, 'IfDead'); G.link(dmg, 'then', bdd, 'execute')
cb = b.name('AsCannonball'); cast(G, cb, BALLC, 'AsBP Cannonball', 500, Y); b.wire((dmg, 'DamageCauser'), cb, 'Object'); G.link(bdd, 'else', cb, 'execute')
ig = b.set('BurnUntil', DBL, b.d2('Add_DoubleDouble', now(800, Y - 300), None, 1000, Y - 300, db='6.0'), 900, Y - 150); G.link(cb, 'then', ig, 'execute')
h1 = b.set('HP', DBL, b.d2('Subtract_DoubleDouble', b.get('HP', DBL, 1100, Y - 400), b.d2('Multiply_DoubleDouble', (dmg, 'Damage'), b.get('CannonMult', D('v', default='5.0'), 1100, Y - 550), 1300, Y - 500), 1500, Y - 450), 1200, Y - 150)
G.link(ig, 'then', h1, 'execute')
h2 = b.set('HP', DBL, b.d2('Subtract_DoubleDouble', b.get('HP', DBL, 900, Y + 350), (dmg, 'Damage'), 1100, Y + 350), 1200, Y + 150); G.link(cb, 'CastFailed', h2, 'execute')
bz = b.branch(b.dcmp('LessEqual_DoubleDouble', b.get('HP', DBL, 1400, Y + 350), None, 1600, Y + 350, db='0.0'), 1600, Y, 'IfBroken')
G.link(h1, 'then', bz, 'execute'); G.link(h2, 'then', bz, 'execute')
G.link(bz, 'then', b.call_self('Break', [], 1900, Y, ENGC, tag='CallBreak'), 'execute')

# ---- Break: wreck mesh, no bridge, stop, pushers fight on, smoke; the wreck stays
Y = 8000
b.event('Break', [], 0, Y)
k1 = b.set('Dead', bo('v', default='true'), None, 250, Y); G.link('Break', 'then', k1, 'execute')
k2 = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SM), bo('ReturnValue', out=True, default='false')], 500, Y, target=body(350, Y + 250), tag='Wreck')
b.wire(b.get('WreckMesh', ob('v', SM), 350, Y + 400), k2, 'NewMesh'); G.link(k1, 'then', k2, 'execute')
k3 = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 800, Y, target=bridge(650, Y + 250), tag='NoBridge')
G.link(k2, 'then', k3, 'execute')
k4 = b.call(CMC, 'StopMovementImmediately', [], 1100, Y, target=cmc(950, Y + 250), tag='Stop'); G.link(k3, 'then', k4, 'execute')
k5 = b.call(CMC, 'DisableMovement', [], 1400, Y, target=cmc(1250, Y + 250), tag='NoMove'); G.link(k4, 'then', k5, 'execute')
fe2 = b.foreach(ACT, 1700, Y); b.wire(b.get('Pushers', arr(ACTV), 1550, Y + 300), fe2, 'Array'); G.link(k5, 'then', fe2, 'Exec')
pz2 = b.name('AsPusher'); cast(G, pz2, ZOMBIE, 'AsBP Zombie', 2050, Y); b.wire((fe2, 'Array Element'), pz2, 'Object'); G.link(fe2, 'LoopBody', pz2, 'execute')
dt2 = b.call(ACT, 'K2_DetachFromActor', [DRULE('LocationRule'), DRULE('RotationRule'), DRULE('ScaleRule')], 2350, Y, target=(pz2, 'AsBP Zombie'), tag='LetGo')
G.link(pz2, 'then', dt2, 'execute')
wk = b.call(CMC, 'SetMovementMode', [{'name': 'NewMovementMode', 'cat': 'byte', 'obj': ENUM('EMovementMode'), 'default': 'MOVE_Walking'}, {'name': 'NewCustomMode', 'cat': 'byte', 'default': '0'}],
            2650, Y, target=b.getm('CharacterMovement', CHARC, ob('v', CMC), (pz2, 'AsBP Zombie'), 2500, Y + 250), tag='PusherWalk')
G.link(dt2, 'then', wk, 'execute')
fx2 = b.lib(GS, 'SpawnEmitterAtLocation', [WC(), dict(ob('EmitterTemplate', PSYS), dobj=P_SMOKE), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
            V('Scale', default='3.000000,3.000000,3.000000'), bo('bAutoDestroy', default='true'),
            {'name': 'PoolingMethod', 'cat': 'byte', 'obj': ENUM('EPSCPoolMethod'), 'default': 'None'}, bo('bAutoActivateSystem', default='true'), ob('ReturnValue', PSC, out=True)], 2100, Y + 500, tag='WreckSmoke')
b.wire(here(1900, Y + 800), fx2, 'Location'); G.link(fe2, 'Completed', fx2, 'execute')
write('BP_SiegeEngine_graph.txt', G)

# ================================================================ BP_SiegeDirector
G = Graph(); b = B(G, 'sd'); b.imp = B(G, 'sdQ')
bp = b.override('DirBeginPlay', 'ReceiveBeginPlay', 0, 0)
G.link(bp, 'then', b.timer('Poll', 300, 0, dtime='2.0', loop=True), 'execute')
Y = 600
b.event('Poll', [], 0, Y)
wm = (b.imp.actor_of(P_WM, WM, 0, Y + 300), 'ReturnValue')
wave = b.getm('Wave', WM, INT, wm, 250, Y + 300)
bnew = b.branch(b.b2('BooleanAND', b.valid(wm, 250, Y + 150), b.icmp('NotEqual_IntInt', wave, b.get('LastWave', INT, 250, Y + 450), 450, Y + 400), 650, Y + 300), 500, Y, 'IfNewWave')
G.link('Poll', 'then', bnew, 'execute')
lw = b.set('LastWave', INT, b.getm('Wave', WM, INT, wm, 700, Y + 300), 800, Y); G.link(bnew, 'then', lw, 'execute')
night = is_night(b, 700, Y + 600)
bram = b.branch(b.b2('BooleanAND', night, b.icmp('GreaterEqual_IntInt', b.get('LastWave', INT, 1000, Y + 800), b.get('RamFromWave', it('v', default='6'), 1000, Y + 950), 1200, Y + 850), 1400, Y + 700), 1100, Y, 'IfRam')
G.link(lw, 'then', bram, 'execute')
me = (b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 1300, Y + 400, ACT, pure=True, const=True, tag='Here'), 'ReturnValue')
fwd = (b.call_self('GetActorForwardVector', [V('ReturnValue', out=True)], 1300, Y + 550, ACT, pure=True, const=True, tag='Fwd'), 'ReturnValue')
rotd = (b.call_self('K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], 1300, Y + 700, ACT, pure=True, const=True, tag='Rot'), 'ReturnValue')
def xf_at(dy, x, y):
    side = b.math('Multiply_VectorFloat', [(V('A'), (b.call_self('GetActorRightVector', [V('ReturnValue', out=True)], x, y + 150, ACT, pure=True, const=True, tag='Right'), 'ReturnValue')),
                                           (fl('B', default=str(dy)), None)], V('ReturnValue', out=True), x + 200, y + 150)
    return b.math('MakeTransform', [(V('Location'), b.v2('Add_VectorVector', me, side, x + 400, y)), (st('Rotation', ROT, default='0, 0, 0'), rotd), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
                  st('ReturnValue', XFORM, out=True), x + 600, y)
sr_ = spawn(b, P_RAM, RAMC, xf_at(-500.0, 1400, Y + 1100), 1600, Y - 200); G.link(bram, 'then', sr_, 'execute')
btwr = b.branch(b.b2('BooleanAND', night, b.icmp('GreaterEqual_IntInt', b.get('LastWave', INT, 1900, Y + 800), b.get('TowerFromWave', it('v', default='9'), 1900, Y + 950), 2100, Y + 850), 2300, Y + 700), 2000, Y, 'IfTower')
G.link(sr_, 'then', btwr, 'execute'); G.link(bram, 'else', btwr, 'execute')
st_ = spawn(b, P_TOWER, TOWERC, xf_at(500.0, 2200, Y + 1100), 2400, Y - 200); G.link(btwr, 'then', st_, 'execute')
# nearest SiegeWall point -> the tower's WallPoint
tg = b.imp.lib(GS, 'GetAllActorsWithTag', [WC(), N('Tag', default='SiegeWall'), arr(ob('OutActors', ACT, out=True))], 2800, Y - 200, tag='Walls')
G.link(st_, 'then', tg, 'execute')
s_best = b.set('BestDist', D('v', default='1000000000.0'), None, 3100, Y - 200); G.link(tg, 'then', s_best, 'execute')   # starts huge
fe = b.foreach(ACT, 3400, Y - 200); b.wire((tg, 'OutActors'), fe, 'Array'); G.link(s_best, 'then', fe, 'Exec')
dd = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 3700, Y + 100, target=(st_, 'ReturnValue'), pure=True, const=True, tag='DistWall')
b.wire((fe, 'Array Element'), dd, 'OtherActor')
bb = b.branch(b.dcmp('Less_DoubleDouble', (dd, 'ReturnValue'), b.get('BestDist', DBL, 3700, Y + 250), 3900, Y + 150), 3800, Y - 200, 'IfNearer')
G.link(fe, 'LoopBody', bb, 'execute')
sb_ = b.set('BestDist', DBL, (dd, 'ReturnValue'), 4100, Y - 200); G.link(bb, 'then', sb_, 'execute')
G.link(sb_, 'then', b.setm('WallPoint', ENGC, ACTV, (fe, 'Array Element'), (st_, 'ReturnValue'), 4400, Y - 200), 'execute')
write('BP_SiegeDirector_graph.txt', G)

# ---- fix_impure (only the Q-prefixed GetActorOfClass / GetAllActors* nodes)
import subprocess
for gname, pfx in (('BP_SiegeEngine', 'seQ'), ('BP_SiegeDirector', 'sdQ')):
    p = os.path.join(HERE, gname + '_graph.txt')
    subprocess.run([sys.executable, os.path.join(HERE, '..', '..', 'tools', 'applyall', 'fix_impure.py'), p, p, pfx], check=True, capture_output=True)
print('fix_impure done')


# ================================================================ VARIABLES.md
GC = lambda p: "/Script/Engine.BlueprintGeneratedClass'%s'" % cpath(p)
T_INT, T_BOOL, T_DBL = '(PinCategory="int")', '(PinCategory="bool")', '(PinCategory="real",PinSubCategory="double")'
T_ACT = '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'")'
T_SM = '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.StaticMesh\'")'
VARS = [
    ('BP_SiegeEngine', 'Kind', T_INT, '0', '0 ram, 1 tower (children set it)'), ('BP_SiegeEngine', 'MaxHP', T_DBL, '900.0', 'HP at spawn'),
    ('BP_SiegeEngine', 'HP', T_DBL, '0.0', 'current HP'), ('BP_SiegeEngine', 'BaseSpeed', T_DBL, '120.0', 'cm/s with all 4 pushers'),
    ('BP_SiegeEngine', 'Dead', T_BOOL, 'False', 'broken (wreck)'), ('BP_SiegeEngine', 'Pushers', '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",ContainerType=Array)', '', 'the 4 pusher zombies'),
    ('BP_SiegeEngine', 'Alive', T_INT, '0', 'scratch: living pushers'), ('BP_SiegeEngine', 'NextHit', T_DBL, '0.0', 'ram: next gate hit time'),
    ('BP_SiegeEngine', 'GatePeriod', T_DBL, '5.0', 'ram: seconds between gate hits'), ('BP_SiegeEngine', 'RamHit', T_DBL, '20.0', 'ram: GateDamage % per hit (before forge bands)'),
    ('BP_SiegeEngine', 'BridgeT', T_DBL, '0.0', 'tower: 0 bridge up .. 1 down'), ('BP_SiegeEngine', 'BridgeUpRoll', T_DBL, '90.0', 'tower: bridge roll when raised (flip to -90 if it raises downward)'),
    ('BP_SiegeEngine', 'SpillLeft', T_INT, '10', 'tower: zombies still to spill'), ('BP_SiegeEngine', 'SpillPeriod', T_DBL, '2.5', 'tower: seconds between spills'),
    ('BP_SiegeEngine', 'NextSpill', T_DBL, '0.0', 'tower: next spill time'), ('BP_SiegeEngine', 'WallPoint', T_ACT, '', 'tower: SiegeWall target (set by the director)'),
    ('BP_SiegeEngine', 'BurnUntil', T_DBL, '0.0', 'burning until this game time'), ('BP_SiegeEngine', 'BurnDPS', T_DBL, '15.0', 'fire damage per second'),
    ('BP_SiegeEngine', 'CannonMult', T_DBL, '5.0', 'cannonball damage multiplier (and ignites)'), ('BP_SiegeEngine', 'IntactMesh', T_SM, '', 'SM_Siege_Ram / _Tower'),
    ('BP_SiegeEngine', 'WreckMesh', T_SM, '', 'SM_Siege_RamWreck / _TowerWreck'), ('BP_SiegeEngine', 'BridgeMesh', T_SM, '', 'SM_Siege_TowerBridge'),
    ('BP_SiegeEngine', 'MeshYaw', T_DBL, '0.0', 'Body yaw so the front is +X: ram 180, tower -90'), ('BP_SiegeEngine', 'PusherScale', T_DBL, '1.25', 'size of the pusher zombies'),
    ('BP_SiegeDirector', 'LastWave', T_INT, '0', 'last wave seen'), ('BP_SiegeDirector', 'RamFromWave', T_INT, '6', 'night waves from this one bring a ram'),
    ('BP_SiegeDirector', 'TowerFromWave', T_INT, '9', 'night waves from this one bring a tower too'), ('BP_SiegeDirector', 'BestDist', T_DBL, '0.0', 'scratch')]
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', encoding='utf-8') as fo:
    fo.write('# Variables for #225 gameplay\n\nAdd them to BP_SiegeEngine (the parent; BP_SiegeRam / BP_SiegeTower inherit them) and BP_SiegeDirector.\n\n')
    fo.write('| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bpn, n, t, d, m in VARS: fo.write('| %s | %s | %s | %s |\n' % (bpn, n, d or '-', m))
    cur = None
    for k, (bpn, n, t, d, m) in enumerate(VARS):
        if bpn != cur: fo.write('%s\n### %s\n```\n' % ('```\n' if cur else '', bpn)); cur = bpn
        fo.write('BPVar(VarName="%s",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E%03X,VarType=%s,FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5%s)\n'
                 % (n, k, t, n, (',DefaultValue="%s"' % d) if d else ''))
    fo.write('```\n')
print('VARIABLES.md', len(VARS))
