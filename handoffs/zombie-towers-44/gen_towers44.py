# #44 Zombie towers: zombies stack to climb the wall (adjustedfilm, 2026-10-31; owner pick, card #44).
#   "<blender python>" -I gen_towers44.py -> BP_ZombieTower_graph.txt, BP_TowerDirector_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# BP_TowerDirector (one per level): every 2 s from wave FromWave (4): if fewer than MaxTowers (2) towers stand and the
#   cooldown (40 s) is over, the first BP_WallBreachSpot with >= GatherMin (6) live zombies within 7 m gets a BP_ZombieTower.
# BP_ZombieTower (15 hidden skeletal "tiers" made by the setup script, 5 layers 5/4/3/2/1):
#   Init       finds the wall: inward = toward CastleCenter; the ground (trace down 2.6 m outside the spot), the wall top (trace
#              down 1.5 m inside) and the wall-walk point; layer spacing = (wall top - ground) / 5 (0.9-2.6 m); stands outside the
#              wall facing out; each tier leans a little more onto the wall per layer.
#   TowerPoll  (0.1 s) absorbs the nearest live zombie within 12 m every GrowEvery (1.8 s): it is hidden, frozen and kept alive
#              (wave counts stay right) and its look (mesh, anim class, materials) goes onto the next tier. The tower sways more
#              the higher it gets. Full (15) = breach: every ClimbEvery (2 s) one absorbed zombie climbs out onto the wall-walk;
#              new zombies keep joining and climbing.
#   AnyDamage  the base box takes damage (hero, bolts, cannon); at 0 HP it topples (1.1 s, falling like a tree): pushed from
#              outside (the hero on the ground) it falls INTO the wall, otherwise (from the wall) outward onto the horde. The
#              landing does 400 radial damage in 3.5 m; 30 % of the tower's zombies get up there, the rest die.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

P_TOWER, P_SPOT = '/Game/CastleDefender/Gameplay/Siege/BP_ZombieTower', '/Game/CastleDefender/Gameplay/Siege/BP_WallBreachSpot'
TOWER, SPOT = BPC(P_TOWER, 'BP_ZombieTower'), BPC(P_SPOT, 'BP_WallBreachSpot')
NOTC = BPC('/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD', 'BP_NoticeHUD')
HUDCLS, SKM, SKMESH = CLS('HUD'), CLS('SkeletalMeshComponent'), CLS('SkeletalMesh')
ANIMI, MATI = CLS('AnimInstance'), CLS('MaterialInterface')
HITRES_ = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.HitResult\'"'
OBJV = lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}


class B(bpkit.B):
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def div(s, a, c, x, y, db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def vmul(s, v, f, x, y, df='0.0'): return s.math('Multiply_VectorFloat', [(V('A'), v), (D('B', default=df), f)], V('ReturnValue', out=True), x, y)
    def loc(s, actor, x, y):
        return (s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'), 'ReturnValue')
    def myloc(s, x, y):
        return (s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'), 'ReturnValue')
    def count(s, node, x, y):
        n = s.name('Count')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.G.link(node, 'OutActors', n, 'TargetArray'); return (n, 'ReturnValue')
    def d2d(s, a, c, x, y): return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def getall(s, path, cls, x, y):
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def trace_z(s, start, x, y, tag):
        """line trace straight down 60 m from start; returns (trace node, impact Location handle)"""
        end = s.v2('Subtract_VectorVector', start, None, x - 200, y + 150, db='0.000000, 0.000000, 6000.000000')
        n = s.lib(KSL, 'LineTraceSingle', [WC(), V('Start'), V('End'),
                  {'name': 'TraceChannel', 'cat': 'byte', 'obj': ENUM('ETraceTypeQuery'), 'default': 'TraceTypeQuery1'}, bo('bTraceComplex', default='false'),
                  arr(ob('ActorsToIgnore', ACT)), {'name': 'DrawDebugType', 'cat': 'byte', 'obj': ENUM('EDrawDebugTrace'), 'default': 'None'},
                  st('OutHit', HITRES_, out=True), bo('bIgnoreSelf', default='true'), st('TraceColor', LC, default='(R=1.000000,G=0.000000,B=0.000000,A=1.000000)'),
                  st('TraceHitColor', LC, default='(R=0.000000,G=1.000000,B=0.000000,A=1.000000)'), fl('DrawTime', default='5.000000'),
                  bo('ReturnValue', out=True, default='false')], x, y, tag=tag)
        s.wire(start, n, 'Start'); s.wire(end, n, 'End')
        bk = s.name('Hit' + tag)
        callfn(s.G, bk, GS, 'BreakHitResult', [st('Hit', HITRES_), bo('bBlockingHit', out=True), bo('bInitialOverlap', out=True), fl('Time', out=True), fl('Distance', out=True),
               V('Location', out=True), V('ImpactPoint', out=True), V('Normal', out=True), V('ImpactNormal', out=True), ob('PhysMat', '"/Script/CoreUObject.Class\'/Script/PhysicsCore.PhysicalMaterial\'"', out=True),
               ob('HitActor', ACT, out=True), ob('HitComponent', PRIM, out=True), NAME_('HitBoneName') | {'out': True}, NAME_('BoneName') | {'out': True},
               it('HitItem', out=True), it('ElementIndex', out=True), it('FaceIndex', out=True), V('TraceStart', out=True), V('TraceEnd', out=True)],
               pure=True, x=x + 300, y=y + 250, self_hidden=True)
        s.G.link(n, 'OutHit', bk, 'Hit')
        return n, (bk, 'Location'), (n, 'ReturnValue')
    def notice(s, text, tier, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x - 150, y + 300,
                     target=(s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x - 350, y + 300, pure=True, tag='PC'), 'ReturnValue'),
                     pure=True, const=True, tag='HUD')
        nc = s.name('AsNotice'); cast(s.G, nc, NOTC, 'AsBP Notice HUD', x, y); s.wire((hud, 'ReturnValue'), nc, 'Object')
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default=str(tier))], x + 300, y, target=(nc, 'AsBP Notice HUD'), tag='Notice')
        s.G.link(nc, 'then', pn, 'execute')
        out = s.seq(s.name('AfterNotice'), 1, x + 600, y); s.G.link(pn, 'then', out, 'execute'); s.G.link(nc, 'CastFailed', out, 'execute')
        return nc, (out, 'then_0')
    def set_hidden(s, actor, hide, x, y):
        a = s.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='true' if hide else 'false')], x, y, target=actor, tag='Hide' if hide else 'Show')
        c = s.call(ACT, 'SetActorEnableCollision', [bo('bNewActorEnableCollision', default='false' if hide else 'true')], x + 250, y, target=actor, tag='Coll')
        s.G.link(a, 'then', c, 'execute'); return a, c


def write(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    names = [n[0] for n in G.nodes]
    if bad or len(names) != len(set(names)): raise SystemExit('%s: bad %s dup %s' % (name, bad[:8], [n for n in names if names.count(n) > 1][:5]))
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (name, len(G.nodes), len(G.links)))


ZOMB = ZOMBIE
CMCV = lambda: ob('v', CMC)

# ================================================================================================= BP_ZombieTower
G = Graph(); b = B(G, 'zt')
g = b.get
# ---- Init (called by the director right after it sets Spot)
b.event('Init', [], 0, 0)
spot = g('Spot', OBJV(ACT), 0, 300)
sl = b.loc(spot, 200, 300)
cc = g('CastleCenter', VECT, 200, 450)
dif = b.v2('Subtract_VectorVector', cc, sl, 400, 400)
dbk = b.brk(dif, 600, 400)
inw = b.math('Normal', [(V('A'), b.vec(dbk['X'], dbk['Y'], None, 800, 400)), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 1000, 400)
si = b.set('Inward', VECT, inw, 300, 0); G.link('Init', 'then', si, 'execute')
INW = lambda x, y: g('Inward', VECT, x, y)
base = b.v2('Add_VectorVector', b.loc(g('Spot', OBJV(ACT), 400, 650), 600, 650), b.vmul(INW(600, 800), None, 800, 800, df='-260.0'), 1000, 700)
up = lambda v, x, y: b.v2('Add_VectorVector', v, None, x, y, db='0.000000, 0.000000, 3000.000000')
t1, gl_, ok1 = b.trace_z(up(base, 1200, 700), 1400, 0, 'TraceGround')
G.link(si, 'then', t1, 'execute')
gz = b.self_(b.brk(gl_, 1700, 600)['Z'], b.brk(b.loc(g('Spot', OBJV(ACT), 1500, 900), 1700, 900), 1900, 900)['Z'], ok1, 2100, 700)
sgz = b.set('GroundZ', DBL, gz, 1800, 0); G.link(t1, 'then', sgz, 'execute')
inner = b.v2('Add_VectorVector', b.loc(g('Spot', OBJV(ACT), 1900, 1100), 2100, 1100), b.vmul(INW(2100, 1250), None, 2300, 1250, df='150.0'), 2500, 1150)
t2, wl_, ok2 = b.trace_z(up(inner, 2600, 1150), 2200, 0, 'TraceWallTop')
G.link(sgz, 'then', t2, 'execute')
wz = b.self_(b.brk(wl_, 2600, 600)['Z'], b.add(g('GroundZ', DBL, 2600, 800), None, 2800, 800, db='800.0'), ok2, 3000, 650)
swz = b.set('WallTopZ', DBL, wz, 2700, 0); G.link(t2, 'then', swz, 'execute')
ww = b.v2('Add_VectorVector', b.vec(b.brk(inner, 2900, 1300)['X'], b.brk(inner, 2900, 1450)['Y'], g('WallTopZ', DBL, 2900, 1600), 3100, 1400),
          b.v2('Add_VectorVector', b.vmul(INW(3100, 1600), None, 3300, 1600, df='200.0'), None, 3500, 1600, db='0.000000, 0.000000, 110.000000'), 3700, 1450)
sww = b.set('WallWalk', VECT, ww, 3000, 0); G.link(swz, 'then', sww, 'execute')
spc = b.clamp(b.div(b.sub(g('WallTopZ', DBL, 3100, 300), g('GroundZ', DBL, 3100, 450), 3300, 350), None, 3500, 350, db='5.0'), '90.0', '260.0', 3700, 350)
ssp = b.set('Spacing', DBL, spc, 3300, 0); G.link(sww, 'then', ssp, 'execute')
yaw = b.math('MakeRotFromX', [(V('X'), b.vmul(INW(3500, 700), None, 3700, 700, df='-1.0'))], st('ReturnValue', ROT, out=True), 3900, 700)
ybk = b.math('BreakRotator', [(st('InRot', ROT, default='0, 0, 0'), yaw)], fl('Yaw', out=True, default='0.0'), 4100, 700)
G.nodes[-1][3].insert(1, fl('Roll', out=True, default='0.0')); G.nodes[-1][3].insert(2, fl('Pitch', out=True, default='0.0'))
sy = b.set('TowerYaw', DBL, ybk, 3600, 0); G.link(ssp, 'then', sy, 'execute')
bl = b.vec(b.brk(base, 3900, 900)['X'], b.brk(base, 3900, 1050)['Y'], g('GroundZ', DBL, 3900, 1200), 4100, 1000)
mv = b.call_self('K2_SetActorLocationAndRotation', [V('NewLocation'), st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'),
                 st('SweepHitResult', HITRES_, out=True), bo('bTeleport', default='true'), bo('ReturnValue', out=True, default='false')], 3900, 0, ACT, tag='Stand')
b.wire(bl, mv, 'NewLocation'); b.wire(yaw, mv, 'NewRotation'); G.link(sy, 'then', mv, 'execute')
gc = b.call_self('GetComponentsByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Script/Engine.SkeletalMeshComponent'), arr(ob('ReturnValue', SKM, out=True))],
                 4200, 300, ACT, pure=True, const=True, tag='TierComps')
st_ = b.set('Tiers', arr(OBJV(SKM)), (gc, 'ReturnValue'), 4200, 0); G.link(mv, 'then', st_, 'execute')
fe = b.foreach(SKM, 4500, 0); b.wire(g('Tiers', arr(OBJV(SKM)), 4300, 200), fe, 'Array'); G.link(st_, 'then', fe, 'Exec')
k = (fe, 'Array Index')
ge = lambda v, x, y: b.math('Conv_BoolToInt', [(bo('InBool', default='false'), b.icmp('GreaterEqual_IntInt', k, None, x, y, db=str(v)))], it('ReturnValue', out=True), x + 200, y)
L = b.i2('Add_IntInt', b.i2('Add_IntInt', ge(5, 4500, 400), ge(9, 4500, 550), 4900, 450), b.i2('Add_IntInt', ge(12, 4500, 700), ge(14, 4500, 850), 4900, 750), 5100, 600)
start = b.i2('Subtract_IntInt', b.i2('Multiply_IntInt', L, None, 5300, 500, db='5'), b.i2('Divide_IntInt', b.i2('Multiply_IntInt', L, b.i2('Subtract_IntInt', L, None, 5300, 700, db='1'), 5500, 650), None, 5700, 650, db='2'), 5900, 550)
slot = b.i2('Subtract_IntInt', k, start, 6100, 500)
nlay = b.i2('Subtract_IntInt', None, L, 6100, 700, da='5')
yv = b.mul(b.sub(b.i2d(slot, 6300, 500), b.mul(b.i2d(b.i2('Subtract_IntInt', nlay, None, 6300, 700, db='1'), 6500, 700), None, 6700, 700, db='0.5'), 6900, 600), None, 7100, 600, db='70.0')
Ld = b.i2d(L, 6300, 900)
xv = b.mul(Ld, g('LeanPerLayer', DBL, 6500, 1000), 6700, 950)
xv = b.mul(xv, None, 6900, 950, db='-1.0')
zv = b.mul(Ld, g('Spacing', DBL, 6500, 1100), 6700, 1100)
rl = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES_, out=True), bo('bTeleport', default='true')],
            4900, 0, target=(fe, 'Array Element'), tag='TierPos')
b.wire(b.vec(xv, yv, zv, 7300, 900), rl, 'NewLocation'); G.link(fe, 'LoopBody', rl, 'execute')
hv = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 5200, 0, target=(fe, 'Array Element'), tag='TierHide')
G.link(rl, 'then', hv, 'execute')
s0 = b.set('NextAbsorb', DBL, b.now(4600, -300), 4800, -300); G.link(fe, 'Completed', s0, 'execute')
G.link(s0, 'then', b.timer_ev('TowerPoll', '0.1', 5100, -300), 'execute')

# ---- AnyDamage: base HP, topple direction
Y = 2200
G.node('ztAnyDamage', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveAnyDamage")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveAnyDamage")' % ACT}, ex('then', True),
        fl('Damage', out=True, default='0.0'), ob('DamageType', CLS('DamageType'), out=True), ob('InstigatedBy', CTRL, out=True), ob('DamageCauser', ACT, out=True)], 0, Y)
bf = b.branch(b.bnot(g('Falling', BOOL, 200, Y + 300), 400, Y + 300), 300, Y, tag='IfStanding'); G.link('ztAnyDamage', 'then', bf, 'execute')
hp = b.set('HP', DBL, b.sub(g('HP', DBL, 400, Y + 450), b.math('Conv_FloatToDouble', [(fl('InFloat', default='0.0'), ('ztAnyDamage', 'Damage'))], D('ReturnValue', out=True), 600, Y + 500), 800, Y + 450), 600, Y)
G.link(bf, 'then', hp, 'execute')
bd = b.branch(b.dcmp('LessEqual_DoubleDouble', g('HP', DBL, 800, Y + 300), None, 1000, Y + 300, db='0.0'), 900, Y, tag='IfTopple'); G.link(hp, 'then', bd, 'execute')
caus = ('ztAnyDamage', 'DamageCauser')
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 1000, Y + 700, pure=True, tag='Pawn')
cl = b.selvec(b.loc(caus, 1200, Y + 500), b.loc((pp, 'ReturnValue'), 1200, Y + 700), b.valid(caus, 1200, Y + 850), 1400, Y + 650)
outside = b.dcmp('Greater_DoubleDouble', b.d2d(cl, g('CastleCenter', VECT, 1400, Y + 850), 1600, Y + 700),
                 b.add(b.d2d(b.myloc(1400, Y + 1000), g('CastleCenter', VECT, 1400, Y + 1100), 1600, Y + 1000), None, 1800, Y + 1000, db='200.0'), 2000, Y + 800)
f1 = b.set('Falling', bo('v', default='true'), None, 1200, Y - 150); G.link(bd, 'then', f1, 'execute')
f2 = b.set('FallT0', DBL, b.now(1300, Y + 200), 1500, Y - 150); G.link(f1, 'then', f2, 'execute')
f3 = b.set('FallDir', DBL, b.self_(None, None, outside, 2200, Y + 800, da='-1.0', db='1.0'), 1800, Y - 150); G.link(f2, 'then', f3, 'execute')
nt, _ = b.notice('The zombie tower topples!', 0, 2100, Y - 150); G.link(f3, 'then', nt, 'execute')

# ---- TowerPoll (0.1 s)
Y = 4000
b.event('TowerPoll', [], 0, Y)
now = b.now(100, Y + 2600)
bfa = b.branch(g('Falling', BOOL, 200, Y + 200), 300, Y, tag='IfFalling'); G.link('TowerPoll', 'then', bfa, 'execute')
# -- standing: sway, absorb, climb
sway = b.mul(b.mul(b.math('Sin', [(D('A', default='0.0'), b.mul(now, None, 300, Y + 900, db='1.3'))], D('ReturnValue', out=True), 500, Y + 900),
                   g('SwayDeg', DBL, 500, Y + 1050), 700, Y + 950), b.div(b.i2d(g('Count', INT, 500, Y + 1200), 700, Y + 1200), None, 900, Y + 1200, db='15.0'), 1100, Y + 1000)
srot = b.call_self('K2_SetActorRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bTeleportPhysics', default='false'), bo('ReturnValue', out=True, default='false')],
                   600, Y + 300, ACT, tag='Sway')
b.wire(b.math('MakeRotator', [(fl('Roll', default='0.0'), sway), (fl('Pitch', default='0.0'), None), (fl('Yaw', default='0.0'), g('TowerYaw', DBL, 1100, Y + 1300))],
              st('ReturnValue', ROT, out=True), 1300, Y + 1100), srot, 'NewRotation')
G.link(bfa, 'else', srot, 'execute')
full = b.icmp('GreaterEqual_IntInt', g('Count', INT, 700, Y + 1500), None, 900, Y + 1500, db='15')
canabs = b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', now, g('NextAbsorb', DBL, 900, Y + 1650), 1100, Y + 1600),
              b.b2('BooleanOR', b.bnot(full, 1100, Y + 1500), g('Breached', BOOL, 1100, Y + 1750), 1300, Y + 1550), 1500, Y + 1600)
ba = b.branch(canabs, 900, Y + 300, tag='IfAbsorbTime'); G.link(srot, 'then', ba, 'execute')
az = b.getall(P_ZOMBIE, ZOMB, 1200, Y + 300); G.link(ba, 'then', az, 'execute')
sbest = b.set('Best', OBJV(ZOMB), None, 1500, Y + 300); G.link(az, 'then', sbest, 'execute')
sbd = b.set('BestD', DBL, g('AbsorbRadius', DBL, 1600, Y + 600), 1750, Y + 300); G.link(sbest, 'then', sbd, 'execute')
fz = b.foreach(ZOMB, 2000, Y + 300); G.link(az, 'OutActors', fz, 'Array'); G.link(sbd, 'then', fz, 'Exec')
z = (fz, 'Array Element')
dz = b.d2d(b.loc(z, 2100, Y + 700), b.myloc(2100, Y + 850), 2300, Y + 750)
inarr = b.name('InTower')
G.node(inarr, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Contains")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, {'name': 'ItemToFind', 'cat': 'wildcard', 'ref': True},
        bo('ReturnValue', out=True, default='false')], 2300, Y + 950)
b.wire(g('Absorbed', arr(OBJV(ACT)), 2100, Y + 950), inarr, 'TargetArray'); G.link(fz, 'Array Element', inarr, 'ItemToFind')
okz = b.b2('BooleanAND', b.b2('BooleanAND', b.bnot(b.getm('Dead', ZOMB, BOOL, z, 2300, Y + 1100), 2500, Y + 1100), b.bnot((inarr, 'ReturnValue'), 2500, Y + 950), 2700, Y + 1000),
           b.dcmp('Less_DoubleDouble', dz, g('BestD', DBL, 2500, Y + 800), 2700, Y + 800), 2900, Y + 900)
bz = b.branch(okz, 2300, Y + 300, tag='IfCloser'); G.link(fz, 'LoopBody', bz, 'execute')
sb1 = b.set('Best', OBJV(ZOMB), z, 2600, Y + 150); G.link(bz, 'then', sb1, 'execute')
sb2 = b.set('BestD', DBL, dz, 2850, Y + 150); G.link(sb1, 'then', sb2, 'execute')
best = lambda x, y: g('Best', OBJV(ZOMB), x, y)
bv = b.branch(b.valid(best(2400, Y - 100), 2600, Y - 100), 2600, Y - 250, tag='IfFound'); G.link(fz, 'Completed', bv, 'execute')
na = b.set('NextAbsorb', DBL, b.add(now, g('GrowEvery', DBL, 2700, Y - 400), 2900, Y - 400), 2850, Y - 250); G.link(bv, 'then', na, 'execute')
aa = b.aadd('Absorbed', OBJV(ACT), best(3000, Y - 100), 3100, Y - 250); G.link(na, 'then', aa, 'execute')
h1, h2 = b.set_hidden(best(3300, Y - 50), True, 3400, Y - 250); G.link(aa, 'then', h1, 'execute')
cmc = b.getm('CharacterMovement', CHARC, CMCV(), best(3600, Y - 50), 3800, Y - 50)
dm = b.call(CMC, 'DisableMovement', [], 3950, Y - 250, target=cmc, tag='Freeze'); G.link(h2, 'then', dm, 'execute')
tp = b.call(ACT, 'K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES_, out=True), bo('bTeleport', default='true'),
            bo('ReturnValue', out=True, default='false')], 4200, Y - 250, target=best(4000, Y - 50), tag='ToBase')
b.wire(b.myloc(4000, Y + 50), tp, 'NewLocation'); G.link(dm, 'then', tp, 'execute')
# its look onto the next tier (while not full)
bt = b.branch(b.bnot(full, 4400, Y + 50), 4450, Y - 250, tag='IfTierFree'); G.link(tp, 'then', bt, 'execute')
tier = lambda x, y: b.aget('Tiers', OBJV(SKM), g('Count', INT, x - 200, y + 150), x, y)
zm = b.getm('Mesh', CHARC, ob('v', SKM), best(4400, Y + 300), 4600, Y + 300)
sm = b.call(SKM, 'SetSkeletalMesh', [ob('NewMesh', SKMESH), bo('bReinitPose', default='true')], 4700, Y - 250, target=tier(4500, Y + 500), tag='TierMesh')
b.wire((b.call(SKM, 'GetSkeletalMeshAsset', [ob('ReturnValue', SKMESH, out=True)], 4800, Y + 300, target=zm, pure=True, const=True, tag='ZMesh'), 'ReturnValue'), sm, 'NewMesh')
G.link(bt, 'then', sm, 'execute')
sa = b.call(SKM, 'SetAnimInstanceClass', [{'name': 'NewClass', 'cat': 'class', 'obj': '"/Script/CoreUObject.Class\'/Script/Engine.Object\'"'}], 5000, Y - 250, target=tier(4800, Y + 700), tag='TierAnim')
b.wire((b.call(SKM, 'GetAnimClass', [{'name': 'ReturnValue', 'cat': 'class', 'obj': '"/Script/CoreUObject.Class\'/Script/Engine.Object\'"', 'out': True}], 5000, Y + 500,
               target=b.getm('Mesh', CHARC, ob('v', SKM), best(4800, Y + 500), 5000, Y + 650), pure=True, const=True, tag='ZAnim'), 'ReturnValue'), sa, 'NewClass')
G.link(sm, 'then', sa, 'execute')
ml = b.forloop(None, b.i2('Subtract_IntInt', b.call(PRIM, 'GetNumMaterials', [it('ReturnValue', out=True)], 5200, Y + 300, target=b.getm('Mesh', CHARC, ob('v', SKM), best(5000, Y + 800), 5200, Y + 800),
                                                    pure=True, const=True, tag='NMat') and (b.G.nodes[-1][0], 'ReturnValue'), None, 5400, Y + 300, db='1'), 5300, Y - 250)
G.link(sa, 'then', ml, 'execute')
smat = b.call(PRIM, 'SetMaterial', [it('ElementIndex', default='0'), ob('Material', MATI)], 5600, Y - 250, target=tier(5400, Y + 900), tag='TierMat')
b.wire((ml, 'Index'), smat, 'ElementIndex')
b.wire((b.call(PRIM, 'GetMaterial', [it('ElementIndex', default='0'), ob('ReturnValue', MATI, out=True)], 5600, Y + 1000,
               target=b.getm('Mesh', CHARC, ob('v', SKM), best(5400, Y + 1100), 5600, Y + 1150), pure=True, const=True, tag='ZMat'), 'ReturnValue'), smat, 'Material')
G.link(ml, 'LoopBody', smat, 'execute')
zmatn = [n for n in G.nodes if n[0].startswith('ztZMat')][-1][0]; G.link(ml, 'Index', zmatn, 'ElementIndex')
sv = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='true'), bo('bPropagateToChildren', default='false')], 5600, Y + 50, target=tier(5400, Y + 1300), tag='TierShow')
G.link(ml, 'Completed', sv, 'execute')
sc = b.set('Count', INT, b.i2('Add_IntInt', g('Count', INT, 5700, Y + 1450), None, 5900, Y + 1450, db='1'), 5900, Y + 50); G.link(sv, 'then', sc, 'execute')
# -- breach: one absorbed zombie climbs out on the wall-walk every ClimbEvery
Y3 = Y + 2200
hasab = b.icmp('Greater_IntInt', b.alen('Absorbed', OBJV(ACT), 600, Y3 + 300), None, 900, Y3 + 300, db='0')
canc = b.b2('BooleanAND', b.b2('BooleanAND', full, hasab, 1100, Y3 + 250), b.dcmp('GreaterEqual_DoubleDouble', now, g('NextClimb', DBL, 900, Y3 + 450), 1100, Y3 + 450), 1300, Y3 + 350)
mga = b.seq('ztAfterAbsorb', 1, 600, Y3)
for src, pin in ((ba, 'else'), (bv, 'else'), (bt, 'else'), (sc, 'then')): G.link(src, pin, mga, 'execute')
bcl = b.branch(canc, 900, Y3, tag='IfClimb'); G.link(mga, 'then_0', bcl, 'execute')
first = b.aget('Absorbed', OBJV(ACT), None, 1100, Y3 + 600)
sfz = b.set('Climber', OBJV(ACT), first, 1200, Y3); G.link(bcl, 'then', sfz, 'execute')
rm = b.name('PopFirst')
G.node(rm, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Remove")' % KARR],
       [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('IndexToRemove', default='0')], 1450, Y3)
b.wire(g('Absorbed', arr(OBJV(ACT)), 1300, Y3 + 200), rm, 'TargetArray'); G.link(sfz, 'then', rm, 'execute')
nc_ = b.set('NextClimb', DBL, b.add(now, g('ClimbEvery', DBL, 1500, Y3 + 350), 1700, Y3 + 350), 1700, Y3); G.link(rm, 'then', nc_, 'execute')
cz = lambda x, y: g('Climber', OBJV(ACT), x, y)
bcv = b.branch(b.valid(cz(1800, Y3 + 300), 2000, Y3 + 300), 1950, Y3, tag='IfClimber'); G.link(nc_, 'then', bcv, 'execute')
tw = b.call(ACT, 'K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES_, out=True), bo('bTeleport', default='true'),
            bo('ReturnValue', out=True, default='false')], 2200, Y3, target=cz(2000, Y3 + 400), tag='OnWall')
b.wire(b.v2('Add_VectorVector', g('WallWalk', VECT, 2100, Y3 + 550), b.vec(b.rnd('-150.0', '150.0', 2100, Y3 + 700), b.rnd('-150.0', '150.0', 2100, Y3 + 800), None, 2300, Y3 + 750), 2500, Y3 + 600), tw, 'NewLocation')
G.link(bcv, 'then', tw, 'execute')
u1, u2 = b.set_hidden(cz(2400, Y3 + 300), False, 2450, Y3); G.link(tw, 'then', u1, 'execute')
ccz = cast(G, 'ztAsCharClimb', CHARC, 'AsCharacter', 2950, Y3); b.wire(cz(2800, Y3 + 300), 'ztAsCharClimb', 'Object'); G.link(u2, 'then', 'ztAsCharClimb', 'execute')
wk = b.call(CMC, 'SetMovementMode', [{'name': 'NewMovementMode', 'cat': 'byte', 'obj': ENUM('EMovementMode'), 'default': 'MOVE_Walking'}, {'name': 'NewCustomMode', 'cat': 'byte', 'default': '0'}],
            3250, Y3, target=b.getm('CharacterMovement', CHARC, CMCV(), ('ztAsCharClimb', 'AsCharacter'), 3100, Y3 + 300), tag='Walk')
G.link('ztAsCharClimb', 'then', wk, 'execute')
bbr = b.branch(b.bnot(g('Breached', BOOL, 3400, Y3 + 300), 3600, Y3 + 300), 3550, Y3, tag='IfFirstOver'); G.link(wk, 'then', bbr, 'execute')
sbr = b.set('Breached', bo('v', default='true'), None, 3800, Y3); G.link(bbr, 'then', sbr, 'execute')
nb, _ = b.notice('The zombies are over the wall!', 1, 4100, Y3); G.link(sbr, 'then', nb, 'execute')
# -- falling: like a tree (ease-in), then land
Y4 = Y + 3600
a = b.sat(b.div(b.sub(now, g('FallT0', DBL, 300, Y4 + 400), 500, Y4 + 350), None, 700, Y4 + 350, db='1.1'), 900, Y4 + 350)
pit = b.mul(b.mul(b.mul(a, a, 1100, Y4 + 400), None, 1300, Y4 + 400, db='-90.0'), g('FallDir', DBL, 1300, Y4 + 550), 1500, Y4 + 450)
fr = b.call_self('K2_SetActorRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bTeleportPhysics', default='false'), bo('ReturnValue', out=True, default='false')],
                 600, Y4, ACT, tag='Fall')
b.wire(b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='0.0'), pit), (fl('Yaw', default='0.0'), g('TowerYaw', DBL, 1500, Y4 + 650))],
              st('ReturnValue', ROT, out=True), 1700, Y4 + 550), fr, 'NewRotation')
G.link(bfa, 'then', fr, 'execute')
land = b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', a, None, 1100, Y4 + 700, db='1.0'), b.bnot(g('Landed', BOOL, 1100, Y4 + 850), 1300, Y4 + 850), 1500, Y4 + 750)
bl_ = b.branch(land, 900, Y4, tag='IfLand'); G.link(fr, 'then', bl_, 'execute')
sl_ = b.set('Landed', bo('v', default='true'), None, 1200, Y4); G.link(bl_, 'then', sl_, 'execute')
lp_ = b.v2('Add_VectorVector', b.myloc(1300, Y4 + 1000), b.vmul(b.vmul(INW(1300, 1150 + Y4), None, 1500, Y4 + 1150, df='-1.0'),
                                                             b.mul(b.mul(g('Spacing', DBL, 1500, Y4 + 1300), None, 1700, Y4 + 1300, db='3.0'), g('FallDir', DBL, 1700, Y4 + 1450), 1900, Y4 + 1350), 2100, Y4 + 1200), 2300, Y4 + 1100)
slp = b.set('LandAt', VECT, lp_, 1450, Y4); G.link(sl_, 'then', slp, 'execute')
rd = b.lib(GS, 'ApplyRadialDamage', [WC(), fl('BaseDamage', default='400.0'), V('Origin'), fl('DamageRadius', default='350.0'),
            {'name': 'DamageTypeClass', 'cat': 'class', 'obj': CLS('DamageType')}, arr(ob('IgnoreActors', ACT)), ob('DamageCauser', ACT), ob('InstigatedByController', CTRL),
            bo('bDoFullDamage', default='false'), {'name': 'DamagePreventionChannel', 'cat': 'byte', 'obj': ENUM('ECollisionChannel'), 'default': 'ECC_Visibility'},
            bo('ReturnValue', out=True, default='false')], 1750, Y4, tag='Crush')
b.wire(g('LandAt', VECT, 1600, Y4 + 300), rd, 'Origin'); b.wire(b.self_node(1600, Y4 + 400), rd, 'DamageCauser'); G.link(slp, 'then', rd, 'execute')
fa = b.foreach(ACT, 2100, Y4); b.wire(g('Absorbed', arr(OBJV(ACT)), 2000, Y4 + 300), fa, 'Array'); G.link(rd, 'then', fa, 'Exec')
ea = (fa, 'Array Element')
tl = b.call(ACT, 'K2_SetActorLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES_, out=True), bo('bTeleport', default='true'),
            bo('ReturnValue', out=True, default='false')], 2400, Y4, target=ea, tag='ToLand')
b.wire(b.v2('Add_VectorVector', g('LandAt', VECT, 2300, Y4 + 500), b.vec(b.rnd('-250.0', '250.0', 2300, Y4 + 650), b.rnd('-250.0', '250.0', 2300, Y4 + 750), None, 2500, Y4 + 700, dz='60.0'), 2700, Y4 + 600), tl, 'NewLocation')
G.link(fa, 'LoopBody', tl, 'execute')
v1, v2 = b.set_hidden(ea, False, 2650, Y4); G.link(tl, 'then', v1, 'execute')
cst = cast(G, 'ztAsCharLand', CHARC, 'AsCharacter', 3150, Y4); G.link(fa, 'Array Element', 'ztAsCharLand', 'Object'); G.link(v2, 'then', 'ztAsCharLand', 'execute')
wk2 = b.call(CMC, 'SetMovementMode', [{'name': 'NewMovementMode', 'cat': 'byte', 'obj': ENUM('EMovementMode'), 'default': 'MOVE_Walking'}, {'name': 'NewCustomMode', 'cat': 'byte', 'default': '0'}],
             3450, Y4, target=b.getm('CharacterMovement', CHARC, CMCV(), ('ztAsCharLand', 'AsCharacter'), 3300, Y4 + 300), tag='Walk')
G.link('ztAsCharLand', 'then', wk2, 'execute')
bs = b.branch(b.math('RandomBoolWithWeight', [(fl('Weight', default='0.300000'), None)], bo('ReturnValue', out=True), 3600, Y4 + 300), 3700, Y4, tag='IfSurvives')
G.link(wk2, 'then', bs, 'execute')
kill = b.lib(GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage', default='100000.0'), ob('EventInstigator', CTRL), ob('DamageCauser', ACT),
             {'name': 'DamageTypeClass', 'cat': 'class', 'obj': CLS('DamageType')}, fl('ReturnValue', out=True, default='0.0')], 3950, Y4 + 150, tag='Kill')
b.wire(ea, kill, 'DamagedActor'); b.wire(b.self_node(3800, Y4 + 450), kill, 'DamageCauser'); G.link(bs, 'else', kill, 'execute')
ds = b.call_self('K2_DestroyActor', [], 2400, Y4 - 300, ACT, tag='Gone'); G.link(fa, 'Completed', ds, 'execute')
write(G, 'BP_ZombieTower_graph.txt')

# ================================================================================================= BP_TowerDirector
G = Graph(); b = B(G, 'td')
g = b.get
G.node('tdBeginPlay', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT}, ex('then', True)], 0, 0)
asp = b.getall(P_SPOT, SPOT, 300, 0); G.link('tdBeginPlay', 'then', asp, 'execute')
ss = b.set('Spots', arr(OBJV(ACT)), (asp, 'OutActors'), 600, 0); G.link(asp, 'then', ss, 'execute')
fsp = b.foreach(ACT, 900, 0); b.wire(g('Spots', arr(OBJV(ACT)), 800, 200), fsp, 'Array'); G.link(ss, 'then', fsp, 'Exec')
G.link(fsp, 'LoopBody', b.aadd('SpotTower', OBJV(ACT), None, 1200, 0), 'execute')
G.link(fsp, 'Completed', b.timer_ev('DirPoll', '2.0', 1300, 400), 'execute')
Y = 1000
b.event('DirPoll', [], 0, Y)
now = b.now(100, Y + 1500)
wm = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_WM)), ob('ReturnValue', WM, out=True)], 300, Y, tag='WaveMgr')
G.link('DirPoll', 'then', wm, 'execute')
at = b.getall(P_TOWER, TOWER, 600, Y); G.link(wm, 'then', at, 'execute')
ok = b.b2('BooleanAND', b.b2('BooleanAND', b.valid((wm, 'ReturnValue'), 800, Y + 300),
                              b.icmp('GreaterEqual_IntInt', b.getm('Wave', WM, INT, (wm, 'ReturnValue'), 800, Y + 450), g('FromWave', INT, 800, Y + 600), 1000, Y + 500), 1200, Y + 400),
          b.b2('BooleanAND', b.icmp('Less_IntInt', b.count(at, 1000, Y + 700), g('MaxTowers', INT, 1000, Y + 850), 1200, Y + 750),
               b.dcmp('GreaterEqual_DoubleDouble', now, g('NextTowerAt', DBL, 1000, Y + 950), 1200, Y + 950), 1400, Y + 850), 1600, Y + 600)
bo_ = b.branch(ok, 900, Y, tag='IfMayBuild'); G.link(at, 'then', bo_, 'execute')
az = b.getall(P_ZOMBIE, ZOMB, 1200, Y); G.link(bo_, 'then', az, 'execute')
fs = b.foreach(ACT, 1500, Y); b.wire(g('Spots', arr(OBJV(ACT)), 1400, Y + 200), fs, 'Array'); G.link(az, 'then', fs, 'Exec')
si_ = (fs, 'Array Index'); sp_ = (fs, 'Array Element')
free = b.b2('BooleanAND', b.bnot(b.valid(b.aget('SpotTower', OBJV(ACT), si_, 1500, Y + 400), 1700, Y + 400), 1900, Y + 400),
            b.dcmp('GreaterEqual_DoubleDouble', now, g('NextTowerAt', DBL, 1700, Y + 550), 1900, Y + 550), 2100, Y + 450)
bfree = b.branch(free, 1800, Y, tag='IfSpotFree'); G.link(fs, 'LoopBody', bfree, 'execute')
c0 = b.set('Crowd', INT, None, 2050, Y); G.link(bfree, 'then', c0, 'execute')
fz = b.foreach(ZOMB, 2300, Y); G.link(az, 'OutActors', fz, 'Array'); G.link(c0, 'then', fz, 'Exec')
zz = (fz, 'Array Element')
nearz = b.b2('BooleanAND', b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', b.d2d(b.loc(zz, 2300, Y + 400), b.loc(sp_, 2300, Y + 550), 2500, Y + 450), g('GatherRadius', DBL, 2500, Y + 600), 2700, Y + 500),
                                     b.bnot(b.getm('Dead', ZOMB, BOOL, zz, 2500, Y + 700), 2700, Y + 700), 2900, Y + 600),
             b.bnot(b.call(ACT, 'IsHidden', [bo('ReturnValue', out=True, default='false')], 2700, Y + 850, target=zz, pure=True, const=True, tag='Hid') and (G.nodes[-1][0], 'ReturnValue'), 2900, Y + 850), 3100, Y + 700)
bn_ = b.branch(nearz, 2600, Y, tag='IfNear'); G.link(fz, 'LoopBody', bn_, 'execute')
G.link(bn_, 'then', b.set('Crowd', INT, b.i2('Add_IntInt', g('Crowd', INT, 2800, Y + 300), None, 3000, Y + 300, db='1'), 2850, Y), 'execute')
bg = b.branch(b.icmp('GreaterEqual_IntInt', g('Crowd', INT, 2500, Y - 300), g('GatherMin', INT, 2500, Y - 200), 2700, Y - 250), 2600, Y - 400, tag='IfCrowd')
G.link(fz, 'Completed', bg, 'execute')
spn = spawn(b, P_TOWER, TOWER, transform(b, b.loc(sp_, 2800, Y - 600), 3000, Y - 600), 2900, Y - 400)
G.link(bg, 'then', spn, 'execute')
tw_ = (spn, 'ReturnValue')
st1 = b.setm('Spot', TOWER, OBJV(ACT), sp_, tw_, 3200, Y - 400); G.link(spn, 'then', st1, 'execute')
ini = b.call(TOWER, 'Init', [], 3450, Y - 400, target=tw_, tag='Init'); G.link(st1, 'then', ini, 'execute')
st2 = b.aset('SpotTower', OBJV(ACT), si_, tw_, 3700, Y - 400); G.link(ini, 'then', st2, 'execute')
st3 = b.set('NextTowerAt', DBL, b.add(now, g('Cooldown', DBL, 3800, Y - 150), 4000, Y - 150), 3950, Y - 400); G.link(st2, 'then', st3, 'execute')
nn, _ = b.notice('Zombies are piling up against the wall!', 1, 4250, Y - 400); G.link(st3, 'then', nn, 'execute')
write(G, 'BP_TowerDirector_graph.txt')

# ================================================================================================= BPVar lines
R, I_, Bo, Vv = 'PinCategory="real",PinSubCategory="double"', 'PinCategory="int"', 'PinCategory="bool"', 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
O = lambda c, a=False: 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"%s' % (c, ',ContainerType=Array' if a else '')
OB = lambda p, n: 'PinCategory="object",PinSubCategoryObject="/Script/Engine.BlueprintGeneratedClass\'%s.%s_C\'"' % (p, n)
TV = [('Spot', O('Actor'), '', 'set by the director'), ('CastleCenter', Vv, '964,1750,0', 'a point inside the castle (the player start): sets which side is "in"'),
      ('HP', R, '600.0', 'base HP: at 0 the tower topples'), ('GrowEvery', R, '1.8', 's per absorbed zombie'), ('ClimbEvery', R, '2.0', 's per zombie over the wall'),
      ('AbsorbRadius', R, '1200.0', 'cm'), ('LeanPerLayer', R, '25.0', 'cm each layer leans onto the wall'), ('SwayDeg', R, '4.0', 'sway at full height'),
      ('Inward', Vv, '0,0,0', 'state'), ('GroundZ', R, '0.0', 'state'), ('WallTopZ', R, '0.0', 'state'), ('WallWalk', Vv, '0,0,0', 'state'), ('Spacing', R, '180.0', 'state'),
      ('TowerYaw', R, '0.0', 'state'), ('Tiers', O('SkeletalMeshComponent', True), '', 'state'), ('Absorbed', O('Actor', True), '', 'state'), ('Count', I_, '0', 'state'),
      ('NextAbsorb', R, '0.0', 'state'), ('NextClimb', R, '0.0', 'state'), ('Breached', Bo, 'false', 'state'), ('Falling', Bo, 'false', 'state'), ('FallT0', R, '0.0', 'state'),
      ('FallDir', R, '1.0', 'state'), ('Landed', Bo, 'false', 'state'), ('LandAt', Vv, '0,0,0', 'state'), ('Best', OB(P_ZOMBIE, 'BP_Zombie'), '', 'scratch'),
      ('BestD', R, '0.0', 'scratch'), ('Climber', O('Actor'), '', 'scratch')]
DV = [('FromWave', I_, '4', 'first wave with towers'), ('MaxTowers', I_, '2', 'towers standing at once'), ('GatherMin', I_, '6', 'zombies at a breach spot to start one'),
      ('GatherRadius', R, '700.0', 'cm'), ('Cooldown', R, '40.0', 's between new towers'), ('NextTowerAt', R, '0.0', 'state'), ('Crowd', I_, '0', 'scratch'),
      ('Spots', O('Actor', True), '', 'state'), ('SpotTower', O('Actor', True), '', 'state')]
bpv = lambda bp, n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'towers44/%s/%s' % (bp, n)).hex.upper(), t, n, d)
out = ['# #44 zombie towers - paste one line at a time on the VARIABLES header of My Blueprint, then Compile', '', '# ---- BP_ZombieTower']
out += [bpv('T', *v[:3]) for v in TV] + ['', '# ---- BP_TowerDirector'] + [bpv('D', *v[:3]) for v in DV]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #44 variables\n\n| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bp, vs in (('BP_ZombieTower', TV), ('BP_TowerDirector', DV)):
        for n, _t, d, m in vs: f.write('| %s | %s | %s | %s |\n' % (bp, n, d or '-', m))
print('BPVar lines: %d + %d' % (len(TV), len(DV)))
