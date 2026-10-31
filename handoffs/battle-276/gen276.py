# #276 Day/night battle plan (TGA, 2026-10-31; owner idea, priority). Blueprint-only, paste-ready. Replaces #274's
# BP_SiegeDirector (place this one instead).
#   BP_BattleDirector (new Actor, placed outside the walls on the zombies' road, arrow toward the castle)
#   Poll (2 s):
#     dusk -> a new night: Plan = random 0..2 (0 Feint, 1 Pincer, 2 Hold & rush), warning notice with the compass side.
#     each new wave:
#       DAY   from wave ColossusFromWave, every ColossusEvery waves: a BP_ZombieWallBreaker (#138) spawns outside a random
#             unbroken BP_WallBreachSpot (Target set) with ColossusHorde zombies around it + a notice.
#       NIGHT from wave SiegeFromWave the night's plan runs with the #274 engines (BP_SiegeRam / BP_SiegeTower):
#         Feint:  FeintSize zombies storm from flank A at once; FeintDelay s later the ram + escorts come from flank B.
#         Pincer: ram from flank A and (from TowerFromWave) a tower from flank B at the same time, each with escorts.
#         Hold:   engines + a bigger escort group; the escorts hold out of crossbow range (movement off) until an engine
#                 is within RushDist of its target or breaks, then everyone charges.
#     escorts march at the engine's pace (MaxWalkSpeed = EscortMarch) and charge (EscortRun) when the engine is near its
#     target, broken, or a soldier / the hero comes within 15 m of the engine.
#   python gen276.py
import os, sys, json
sys.dont_write_bytecode = True
HERE276 = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE276, '..', 'farm-223', 'gen223.py'), encoding='utf-8').read()
_g = _src[:_src.index('# ================================================================ BP_FarmPlot')].replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = HERE276')
__file__ = os.path.join(HERE276, '..', 'farm-223', 'gen223.py'); exec(_g); __file__ = os.path.join(HERE276, 'gen276.py')
HERE = HERE276

P_SIEGE = '/Game/CastleDefender/Gameplay/Siege/'
P_ENG, P_RAM, P_TOWER = P_SIEGE + 'BP_SiegeEngine', P_SIEGE + 'BP_SiegeRam', P_SIEGE + 'BP_SiegeTower'
P_BRK, P_SPOT = P_SIEGE + 'BP_ZombieWallBreaker', P_SIEGE + 'BP_WallBreachSpot'
ENGC, RAMC, TOWERC = BPC(P_ENG, 'BP_SiegeEngine'), BPC(P_RAM, 'BP_SiegeRam'), BPC(P_TOWER, 'BP_SiegeTower')
BRKC, SPOTC = BPC(P_BRK, 'BP_ZombieWallBreaker'), BPC(P_SPOT, 'BP_WallBreachSpot')
P_GATE = P_CASTLE + 'BP_CastleGateControl'; GATEC = BPC(P_GATE, 'BP_CastleGateControl')
ACTV = ob('v', ACT); FLT = fl('v', default='0.0')
BDC = BPC(P_SIEGE + 'BP_BattleDirector', 'BP_BattleDirector')

G = Graph(); b = B(G, 'bd'); b.imp = B(G, 'bdQ')
here = lambda x, y: (b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='Here'), 'ReturnValue')
right = lambda x, y: (b.call_self('GetActorRightVector', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='Right'), 'ReturnValue')
myrot = lambda x, y: (b.call_self('K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], x, y, ACT, pure=True, const=True, tag='Rot'), 'ReturnValue')
now = lambda x, y: b.now(x, y)
def flank(side, x, y):
    """director location + right * side * FlankOffset (side -1 = flank A, +1 = flank B, 0 = centre)."""
    if side == 0: return here(x, y)
    off = b.math('Multiply_VectorFloat', [(V('A'), right(x, y + 150)), (fl('B', default='0.0'), b.d2('Multiply_DoubleDouble', b.get('FlankOffset', D('v', default='1500.0'), x, y + 300), None, x + 200, y + 300, db=str(float(side))))],
                 V('ReturnValue', out=True), x + 400, y + 150)
    return b.v2('Add_VectorVector', here(x + 200, y), off, x + 600, y)
def jitter(loc, r, x, y):
    return b.v2('Add_VectorVector', loc, b.vec(b.rnd(str(-r), str(r), x, y + 100), b.rnd(str(-r), str(r), x, y + 250), None, x + 200, y + 150, dz='100.0'), x + 400, y)
def xform(loc, x, y, rot=None):
    return b.math('MakeTransform', [(V('Location'), loc), (st('Rotation', ROT, default='0, 0, 0'), rot), (V('Scale', default='1.000000,1.000000,1.000000'), None)], st('ReturnValue', XFORM, out=True), x, y)
def notice_text(text_src, x, y):
    """PushNotice(text) on the player's notice HUD; text_src is a string handle. -> (first, last)."""
    hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x, y + 300, target=pc(b, x - 250, y + 300), pure=True, const=True, tag='HUD')
    nc, nh = notice_hud(b, (hud, 'ReturnValue'), x + 250, y)
    n = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='2')], x + 600, y, target=nh, tag='Warn'); b.wire(text_src, n, 'Text')
    G.link(nc, 'then', n, 'execute'); return nc, n
def compass(loc, x, y):
    """'north' / 'east' / 'south' / 'west' of the castle gate for a world location (+X north, +Y east, editor convention)."""
    gl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=(b.imp.actor_of(P_GATE, GATEC, x - 250, y), 'ReturnValue'), pure=True, const=True, tag='GateAt')
    d = b.brk(b.v2('Subtract_VectorVector', loc, (gl, 'ReturnValue'), x + 250, y), x + 450, y)
    absx = b.math('Abs', [(D('A', default='0.0'), d['X'])], D('ReturnValue', out=True), x + 650, y)
    absy = b.math('Abs', [(D('A', default='0.0'), d['Y'])], D('ReturnValue', out=True), x + 650, y + 150)
    ns = b.selstr(None, None, b.dcmp('Greater_DoubleDouble', d['X'], None, x + 850, y + 300), x + 1050, y + 300, da='north', db='south')
    ew = b.selstr(None, None, b.dcmp('Greater_DoubleDouble', d['Y'], None, x + 850, y + 450), x + 1050, y + 450, da='east', db='west')
    return b.selstr(ns, ew, b.dcmp('Greater_DoubleDouble', absx, absy, x + 850, y + 150), x + 1250, y + 150)

def spawn_escorts(count_src, loc, march, x, y):
    """count_src zombies around loc; each is added to Escorts and marches (MaxWalkSpeed = EscortMarch) or holds (movement off).
    Returns (first, last) exec nodes."""
    fl_ = b.name('ForLoop'); G.node(fl_, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FORLOOP],
                                     [ex(), it('FirstIndex', default='1'), it('LastIndex', default='0'), ex('LoopBody', True), it('Index', out=True), ex('Completed', True)], x, y)
    b.wire(count_src, fl_, 'LastIndex')
    sz = spawn(b, P_ZOMBIE, ZOMBIE, xform(jitter(loc, 600, x, y + 400), x + 500, y + 400), x + 400, y)
    G.link(fl_, 'LoopBody', sz, 'execute')
    zc = (sz, 'ReturnValue'); cm = b.getm('CharacterMovement', CHARC, ob('v', CMC), zc, x + 650, y + 300)
    ad = b.aadd('Escorts', ACTV, zc, x + 1500, y)
    if march:
        sp = b.setm('MaxWalkSpeed', CMC, FLT, b.get('EscortMarch', D('v', default='130.0'), x + 750, y + 450), cm, x + 900, y)
        G.link(sz, 'then', sp, 'execute'); G.link(sp, 'then', ad, 'execute')
    else:
        dm = b.call(CMC, 'DisableMovement', [], x + 900, y, target=cm, tag='Hold'); G.link(sz, 'then', dm, 'execute'); G.link(dm, 'then', ad, 'execute')
    return fl_, (fl_, 'Completed')

def spawn_engine(path, cls, loc, x, y):
    s = spawn(b, path, cls, xform(loc, x + 250, y + 300, myrot(x, y + 450)), x, y)
    a = b.aadd('Engines', ACTV, (s, 'ReturnValue'), x + 400, y); G.link(s, 'then', a, 'execute')
    return s, a

# ---------------------------------------------------------------- BeginPlay + Poll
bp = b.override('BattleBeginPlay', 'ReceiveBeginPlay', 0, 0)
G.link(bp, 'then', b.timer('Poll', 300, 0, dtime='2.0', loop=True), 'execute')
Y = 600
b.event('Poll', [], 0, Y)
night = is_night(b, 0, Y + 900)
bdusk = b.branch(b.b2('BooleanAND', night, b.bnot(b.get('WasNight', BOOL, 300, Y + 750), 500, Y + 750), 700, Y + 800), 300, Y, 'IfDusk')
G.link('Poll', 'then', bdusk, 'execute')
c_night = b.call_self('NewNight', [], 600, Y - 150, BDC, tag='CallNewNight'); G.link(bdusk, 'then', c_night, 'execute')
swn = b.set('WasNight', BOOL, night, 900, Y); G.link(c_night, 'then', swn, 'execute'); G.link(bdusk, 'else', swn, 'execute')
c_esc = b.call_self('EscortThink', [], 1150, Y, BDC, tag='CallEscort'); G.link(swn, 'then', c_esc, 'execute')
wm = (b.imp.actor_of(P_WM, WM, 1150, Y + 400), 'ReturnValue')
bnew = b.branch(b.b2('BooleanAND', b.valid(wm, 1400, Y + 300), b.icmp('NotEqual_IntInt', b.getm('Wave', WM, INT, wm, 1400, Y + 450), b.get('LastWave', INT, 1400, Y + 600), 1600, Y + 500), 1800, Y + 400), 1500, Y, 'IfNewWave')
G.link(c_esc, 'then', bnew, 'execute')
lw = b.set('LastWave', INT, b.getm('Wave', WM, INT, wm, 1700, Y + 250), 1800, Y); G.link(bnew, 'then', lw, 'execute')
bn2 = b.branch(b.get('WasNight', BOOL, 1950, Y + 250), 2100, Y, 'IfNightWave'); G.link(lw, 'then', bn2, 'execute')
G.link(bn2, 'then', b.call_self('NightWave', [], 2400, Y - 150, BDC, tag='CallNightWave'), 'execute')
G.link(bn2, 'else', b.call_self('DayWave', [], 2400, Y + 150, BDC, tag='CallDayWave'), 'execute')

# ---------------------------------------------------------------- NewNight: pick the plan + warn
Y = 2000
b.event('NewNight', [], 0, Y)
clre = b.name('ClearEng'); G.node(clre, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
                                   [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], 100, Y - 300)
b.wire(b.get('Engines', arr(ACTV), 0, Y - 100), clre, 'TargetArray')                  # last night's wrecks no longer count
pl = b.set('Plan', INT, b.math('RandomIntegerInRange', [(it('Min', default='0'), None), (it('Max', default='2'), None)], it('ReturnValue', out=True), 0, Y + 300), 250, Y)
G.link('NewNight', 'then', clre, 'execute'); G.link(clre, 'then', pl, 'execute')
side = compass(flank(-1, 300, Y + 600), 600, Y + 600)
plan = b.get('Plan', INT, 1600, Y + 1100)
inner = b.selstr(None, None, eqi(b, plan, 1, 1800, Y + 1200), 2000, Y + 1150, da='Siege engines on two sides tonight, the first from the ', db='The horde gathers in the dark to the ')
msg = b.selstr(None, inner, eqi(b, plan, 0, 1800, Y + 1350), 2200, Y + 1100, da='Movement to the ')
txt = b.concat(b.concat(msg, side, 2400, Y + 1000), None, 2600, Y + 1000, db=' of the castle... a siege is coming tonight.')
n0, n1 = notice_text(txt, 2800, Y); G.link(pl, 'then', n0, 'execute')

# ---------------------------------------------------------------- DayWave: colossus breach every ColossusEvery waves
Y = 3200
b.event('DayWave', [], 0, Y)
wv = b.get('LastWave', INT, 0, Y + 300)
due = b.b2('BooleanAND', b.icmp('GreaterEqual_IntInt', wv, b.get('ColossusFromWave', it('v', default='4'), 0, Y + 450), 200, Y + 400),
           eqi(b, b.i2('Percent_IntInt', b.i2('Subtract_IntInt', wv, b.get('ColossusFromWave', it('v', default='4'), 200, Y + 650), 400, Y + 600),
                       b.get('ColossusEvery', it('v', default='3'), 400, Y + 750), 600, Y + 650), 0, 800, Y + 650), 1000, Y + 500)
bdue = b.branch(due, 300, Y, 'IfColossus'); G.link('DayWave', 'then', bdue, 'execute')
ga = b.imp.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SPOT)), arr(ob('OutActors', SPOTC, out=True))], 600, Y, tag='Spots')
G.link(bdue, 'then', ga, 'execute')
clr = b.name('ClearCand'); G.node(clr, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
                                  [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], 900, Y)
b.wire(b.get('Candidates', arr(ACTV), 800, Y + 200), clr, 'TargetArray'); G.link(ga, 'then', clr, 'execute')
fe = b.foreach(SPOTC, 1150, Y); b.wire((ga, 'OutActors'), fe, 'Array'); G.link(clr, 'then', fe, 'Exec')
bok = b.branch(b.bnot(b.getm('Broken', SPOTC, BOOL, (fe, 'Array Element'), 1400, Y + 300), 1600, Y + 300), 1500, Y, 'IfWhole')
G.link(fe, 'LoopBody', bok, 'execute'); G.link(bok, 'then', b.aadd('Candidates', ACTV, (fe, 'Array Element'), 1800, Y), 'execute')
nc_ = b.alen('Candidates', ACTV, 1300, Y + 700)
bany = b.branch(b.icmp('Greater_IntInt', nc_, None, 1700, Y + 700, db='0'), 1700, Y + 500, 'IfAnySpot'); G.link(fe, 'Completed', bany, 'execute')
pick = b.aget('Candidates', ACTV, b.math('RandomIntegerInRange', [(it('Min', default='0'), None), (it('Max', default='0'), b.i2('Subtract_IntInt', b.alen('Candidates', ACTV, 1700, Y + 1100), None, 1950, Y + 1100, db='1'))],
                                      it('ReturnValue', out=True), 2150, Y + 1000), 2000, Y + 900)
ssp = b.set('Spot', ACTV, pick, 2000, Y + 500); G.link(bany, 'then', ssp, 'execute')
spot = lambda x, y: b.get('Spot', ACTV, x, y)
# the colossus comes from the director's side toward the spot: spawn 15 m out from the spot along (director - spot)
sl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 2200, Y + 1300, target=spot(2050, Y + 1300), pure=True, const=True, tag='SpotAt')
outv = b.math('Normal', [(V('A'), b.v2('Subtract_VectorVector', here(2200, Y + 1500), (sl, 'ReturnValue'), 2400, Y + 1450)), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 2600, Y + 1450)
cpos = b.v2('Add_VectorVector', (sl, 'ReturnValue'), b.math('Multiply_VectorFloat', [(V('A'), outv), (fl('B', default='1500.0'), None)], V('ReturnValue', out=True), 2800, Y + 1450), 3000, Y + 1350)
sbrk = spawn(b, P_BRK, BRKC, xform(b.v2('Add_VectorVector', cpos, None, 3200, Y + 1300, db='0, 0, 300'), 3400, Y + 1300), 2300, Y + 500)
G.link(ssp, 'then', sbrk, 'execute')
stg = b.setm('Target', BRKC, ob('v', SPOTC), None, (sbrk, 'ReturnValue'), 2700, Y + 500)
cs = b.name('AsSpot'); cast(G, cs, SPOTC, 'AsBP Wall Breach Spot', 2550, Y + 800, pure=True); b.wire(spot(2400, Y + 900), cs, 'Object'); b.wire((cs, 'AsBP Wall Breach Spot'), stg, 'Target')
G.link(sbrk, 'then', stg, 'execute')
h0, h1 = spawn_escorts(b.get('ColossusHorde', it('v', default='12'), 3000, Y + 700), cpos, False, 3000, Y + 500)
G.link(stg, 'then', h0, 'execute')
rel = b.call_self('ReleaseEscorts', [], 4700, Y + 500, BDC, tag='CallRelease'); G.link(h1[0], h1[1], rel, 'execute')
dtxt = b.concat(b.concat(None, compass(cpos, 4500, Y + 900), 5000, Y + 800, da='A COLOSSUS approaches the '), None, 5200, Y + 800, db=' wall with its horde!')
w0, w1 = notice_text(dtxt, 5000, Y + 500); G.link(rel, 'then', w0, 'execute')

# ---------------------------------------------------------------- NightWave: run tonight's plan
Y = 5600
b.event('NightWave', [], 0, Y)
bsg = b.branch(b.icmp('GreaterEqual_IntInt', b.get('LastWave', INT, 0, Y + 300), b.get('SiegeFromWave', it('v', default='6'), 0, Y + 450), 200, Y + 350), 250, Y, 'IfSiege')
G.link('NightWave', 'then', bsg, 'execute')
sh = b.set('Holding', BOOL, None, 500, Y); G.link(bsg, 'then', sh, 'execute')
plan = lambda x, y: b.get('Plan', INT, x, y)
b0 = b.branch(eqi(b, plan(600, Y + 300), 0, 800, Y + 300), 800, Y, 'IfFeint'); G.link(sh, 'then', b0, 'execute')
b1 = b.branch(eqi(b, plan(900, Y + 600), 1, 1100, Y + 600), 1100, Y + 300, 'IfPincer'); G.link(b0, 'else', b1, 'execute')
towers_ok = lambda x, y: b.icmp('GreaterEqual_IntInt', b.get('LastWave', INT, x, y), b.get('TowerFromWave', it('v', default='9'), x, y + 150), x + 200, y + 50)
# Feint: storm group from flank A now, the ram + escorts from flank B after FeintDelay
f0, f1 = spawn_escorts(b.get('FeintSize', it('v', default='8'), 1100, Y - 300), flank(-1, 1100, Y - 600), False, 1200, Y - 300)
G.link(b0, 'then', f0, 'execute')
fr = b.call_self('ReleaseEscorts', [], 2900, Y - 300, BDC, tag='CallRelease'); G.link(f1[0], f1[1], fr, 'execute')        # the feint charges at once
G.link(fr, 'then', b.timer('FeintMain', 3200, Y - 300, time=b.get('FeintDelay', D('v', default='20.0'), 3000, Y - 100)), 'execute')
# Pincer: ram flank A + tower flank B (or a second ram before TowerFromWave), escorts with both
r0, ra = spawn_engine(P_RAM, RAMC, flank(-1, 1300, Y + 700), 1400, Y + 300); G.link(b1, 'then', r0, 'execute')
e0, e1 = spawn_escorts(b.get('EscortSize', it('v', default='8'), 1900, Y + 600), flank(-1, 1900, Y + 900), True, 2000, Y + 300); G.link(ra, 'then', e0, 'execute')
bt = b.branch(towers_ok(2300, Y + 1300), 3700, Y + 300, 'IfTowers'); G.link(e1[0], e1[1], bt, 'execute')
t0, ta = spawn_engine(P_TOWER, TOWERC, flank(1, 3800, Y + 700), 4000, Y + 100); G.link(bt, 'then', t0, 'execute')
r2, r2a = spawn_engine(P_RAM, RAMC, flank(1, 3800, Y + 1100), 4000, Y + 500); G.link(bt, 'else', r2, 'execute')
e2, e3 = spawn_escorts(b.get('EscortSize', it('v', default='8'), 4500, Y + 600), flank(1, 4500, Y + 900), True, 4600, Y + 300)
G.link(ta, 'then', e2, 'execute'); G.link(r2a, 'then', e2, 'execute')
G.link(e3[0], e3[1], b.call_self('AssignWalls', [], 6200, Y + 300, BDC, tag='CallWalls'), 'execute')
# Hold & rush: ram (+ tower) from the centre, a bigger escort that holds until the engines are close
hr0, hra = spawn_engine(P_RAM, RAMC, flank(0, 1300, Y + 1700), 1400, Y + 1300); G.link(b1, 'else', hr0, 'execute')
bt2 = b.branch(towers_ok(1900, Y + 1700), 1950, Y + 1300, 'IfTowers'); G.link(hra, 'then', bt2, 'execute')
ht0, hta = spawn_engine(P_TOWER, TOWERC, flank(1, 2000, Y + 1900), 2200, Y + 1500); G.link(bt2, 'then', ht0, 'execute')
hsz = b.d2('Multiply_DoubleDouble', b.i2d(b.get('EscortSize', it('v', default='8'), 2600, Y + 1900), 2800, Y + 1900), None, 3000, Y + 1900, db='1.5')
hh = b.set('Holding', bo('v', default='true'), None, 2700, Y + 1300); G.link(hta, 'then', hh, 'execute'); G.link(bt2, 'else', hh, 'execute')
he0, he1 = spawn_escorts(b.math('Round', [(D('A', default='0.0'), hsz)], it('ReturnValue', out=True), 3200, Y + 1900), flank(-1, 3000, Y + 2200), False, 3000, Y + 1300)
G.link(hh, 'then', he0, 'execute')
G.link(he1[0], he1[1], b.call_self('AssignWalls', [], 4600, Y + 1300, BDC, tag='CallWalls'), 'execute')

# ---------------------------------------------------------------- FeintMain (timer): the real attack after the feint
Y = 8400
b.event('FeintMain', [], 0, Y)
fm0, fma = spawn_engine(P_RAM, RAMC, flank(1, 0, Y + 400), 200, Y); G.link('FeintMain', 'then', fm0, 'execute')
fe0, fe1 = spawn_escorts(b.get('EscortSize', it('v', default='8'), 700, Y + 300), flank(1, 700, Y + 600), True, 800, Y); G.link(fma, 'then', fe0, 'execute')

# ---------------------------------------------------------------- AssignWalls: every tower without a WallPoint gets the nearest SiegeWall
Y = 9400
b.event('AssignWalls', [], 0, Y)
tg = b.imp.lib(GS, 'GetAllActorsWithTag', [WC(), N('Tag', default='SiegeWall'), arr(ob('OutActors', ACT, out=True))], 250, Y, tag='Walls')
G.link('AssignWalls', 'then', tg, 'execute')
fe = b.foreach(ACT, 600, Y); b.wire(b.get('Engines', arr(ACTV), 450, Y + 300), fe, 'Array'); G.link(tg, 'then', fe, 'Exec')
ce = b.name('AsEngine'); cast(G, ce, ENGC, 'AsBP Siege Engine', 900, Y); b.wire((fe, 'Array Element'), ce, 'Object'); G.link(fe, 'LoopBody', ce, 'execute')
eng = (ce, 'AsBP Siege Engine')
bneed = b.branch(b.b2('BooleanAND', eqi(b, b.getm('Kind', ENGC, INT, eng, 1050, Y + 300), 1, 1250, Y + 300), b.bnot(b.valid(b.getm('WallPoint', ENGC, ACTV, eng, 1050, Y + 450), 1250, Y + 450), 1450, Y + 450), 1650, Y + 350),
                 1300, Y, 'IfNeedsWall'); G.link(ce, 'then', bneed, 'execute')
sbd = b.set('BestDist', D('v', default='1000000000.0'), None, 1600, Y); G.link(bneed, 'then', sbd, 'execute')
fw = b.foreach(ACT, 1900, Y); b.wire((tg, 'OutActors'), fw, 'Array'); G.link(sbd, 'then', fw, 'Exec')
dd = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 2200, Y + 300, target=eng, pure=True, const=True, tag='DistWall')
b.wire((fw, 'Array Element'), dd, 'OtherActor')
bnr = b.branch(b.dcmp('Less_DoubleDouble', (dd, 'ReturnValue'), b.get('BestDist', DBL, 2200, Y + 450), 2400, Y + 350), 2300, Y, 'IfNearer'); G.link(fw, 'LoopBody', bnr, 'execute')
sb2 = b.set('BestDist', DBL, (dd, 'ReturnValue'), 2600, Y); G.link(bnr, 'then', sb2, 'execute')
G.link(sb2, 'then', b.setm('WallPoint', ENGC, ACTV, (fw, 'Array Element'), eng, 2900, Y), 'execute')

# ---------------------------------------------------------------- EscortThink (each poll): release the escorts when it is time
Y = 10600
b.event('EscortThink', [], 0, Y)
sgo = b.set('Go', BOOL, None, 250, Y); G.link('EscortThink', 'then', sgo, 'execute')
fe = b.foreach(ACT, 500, Y); b.wire(b.get('Engines', arr(ACTV), 350, Y + 300), fe, 'Array'); G.link(sgo, 'then', fe, 'Exec')
ce = b.name('AsEngine'); cast(G, ce, ENGC, 'AsBP Siege Engine', 800, Y); b.wire((fe, 'Array Element'), ce, 'Object'); G.link(fe, 'LoopBody', ce, 'execute')
eng = (ce, 'AsBP Siege Engine')
gate = (b.imp.actor_of(P_GATE, GATEC, 800, Y + 500), 'ReturnValue')
dg = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 1050, Y + 500, target=eng, pure=True, const=True, tag='DistGate'); b.wire(gate, dg, 'OtherActor')
wpt = b.getm('WallPoint', ENGC, ACTV, eng, 1050, Y + 700)
dwp = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 1250, Y + 700, target=eng, pure=True, const=True, tag='DistWall'); b.wire(wpt, dwp, 'OtherActor')
istower = eqi(b, b.getm('Kind', ENGC, INT, eng, 1250, Y + 900), 1, 1450, Y + 900)
dtgt = b.self_((dwp, 'ReturnValue'), (dg, 'ReturnValue'), b.b2('BooleanAND', istower, b.valid(wpt, 1450, Y + 1050), 1650, Y + 950), 1850, Y + 700)
pl_ = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], 1250, Y + 1250, pure=True, tag='Player')
dpl = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 1450, Y + 1250, target=eng, pure=True, const=True, tag='DistHero'); b.wire((pl_, 'ReturnValue'), dpl, 'OtherActor')
close = b.b2('BooleanOR', b.b2('BooleanOR', b.dcmp('Less_DoubleDouble', dtgt, b.get('RushDist', D('v', default='2500.0'), 1900, Y + 900), 2100, Y + 800),
                               b.getm('Dead', ENGC, BOOL, eng, 1900, Y + 1050), 2300, Y + 900),
             b.dcmp('Less_DoubleDouble', (dpl, 'ReturnValue'), None, 1900, Y + 1250, db='1500.0'), 2500, Y + 1000)
bgo = b.branch(close, 1100, Y, 'IfCharge'); G.link(ce, 'then', bgo, 'execute')
G.link(bgo, 'then', b.set('Go', bo('v', default='true'), None, 1400, Y), 'execute')
brl = b.branch(b.get('Go', BOOL, 800, Y + 1500), 900, Y + 1300, 'IfGo'); G.link(fe, 'Completed', brl, 'execute')
G.link(brl, 'then', b.call_self('ReleaseEscorts', [], 1200, Y + 1300, BDC, tag='CallRelease'), 'execute')

# ---------------------------------------------------------------- ReleaseEscorts: everyone charges (walk on, run speed), list cleared
Y = 12600
b.event('ReleaseEscorts', [], 0, Y)
fe = b.foreach(ACT, 250, Y); b.wire(b.get('Escorts', arr(ACTV), 100, Y + 300), fe, 'Array'); G.link('ReleaseEscorts', 'then', fe, 'Exec')
cz = b.name('AsZombie'); cast(G, cz, ZOMBIE, 'AsBP Zombie', 550, Y); b.wire((fe, 'Array Element'), cz, 'Object'); G.link(fe, 'LoopBody', cz, 'execute')
cm = b.getm('CharacterMovement', CHARC, ob('v', CMC), (cz, 'AsBP Zombie'), 700, Y + 300)
wk = b.call(CMC, 'SetMovementMode', [{'name': 'NewMovementMode', 'cat': 'byte', 'obj': ENUM('EMovementMode'), 'default': 'MOVE_Walking'}, {'name': 'NewCustomMode', 'cat': 'byte', 'default': '0'}], 850, Y, target=cm, tag='Walk')
G.link(cz, 'then', wk, 'execute')
G.link(wk, 'then', b.setm('MaxWalkSpeed', CMC, FLT, b.get('EscortRun', D('v', default='420.0'), 1000, Y + 450), cm, 1150, Y), 'execute')
clr2 = b.name('ClearEsc'); G.node(clr2, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
                                   [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], 600, Y + 600)
b.wire(b.get('Escorts', arr(ACTV), 450, Y + 800), clr2, 'TargetArray'); G.link(fe, 'Completed', clr2, 'execute')
G.link(clr2, 'then', b.set('Holding', BOOL, None, 900, Y + 600), 'execute')
write('BP_BattleDirector_graph.txt', G)

import subprocess
p = os.path.join(HERE, 'BP_BattleDirector_graph.txt')
subprocess.run([sys.executable, os.path.join(HERE, '..', '..', 'tools', 'applyall', 'fix_impure.py'), p, p, 'bdQ'], check=True, capture_output=True)
print('fix_impure done')


# ================================================================ VARIABLES.md
T_INT, T_BOOL, T_DBL = '(PinCategory="int")', '(PinCategory="bool")', '(PinCategory="real",PinSubCategory="double")'
T_ACT = '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'")'
T_ARR = '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",ContainerType=Array)'
VARS = [('LastWave', T_INT, '0', 'last wave seen'), ('WasNight', T_BOOL, 'False', 'last poll was night'), ('Plan', T_INT, '0', "tonight's plan: 0 feint, 1 pincer, 2 hold & rush"),
        ('Holding', T_BOOL, 'False', 'escorts are holding (hold & rush)'), ('Go', T_BOOL, 'False', 'scratch'), ('BestDist', T_DBL, '0.0', 'scratch'),
        ('Spot', T_ACT, '', 'scratch: chosen breach spot'), ('Candidates', T_ARR, '', 'scratch: unbroken breach spots'), ('Escorts', T_ARR, '', 'escort zombies not yet released'),
        ('Engines', T_ARR, '', "tonight's siege engines"),
        ('FlankOffset', T_DBL, '1500.0', 'cm left / right of the director for flank A / B'), ('ColossusFromWave', T_INT, '4', 'first day wave with a colossus'),
        ('ColossusEvery', T_INT, '3', 'then every Nth day wave'), ('ColossusHorde', T_INT, '12', 'zombies with each colossus'),
        ('SiegeFromWave', T_INT, '6', 'first night wave with siege engines'), ('TowerFromWave', T_INT, '9', 'towers from this night wave'),
        ('FeintSize', T_INT, '8', 'zombies in the feint'), ('FeintDelay', T_DBL, '20.0', 's between the feint and the real attack'),
        ('EscortSize', T_INT, '8', 'escorts per engine (x1.5 when holding)'), ('EscortMarch', T_DBL, '130.0', 'escort walk speed while marching with an engine'),
        ('EscortRun', T_DBL, '420.0', 'escort speed when they charge'), ('RushDist', T_DBL, '2500.0', 'engine this close to its target -> charge')]
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', encoding='utf-8') as fo:
    fo.write('# Variables for #276 (BP_BattleDirector)\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, t, d, m in VARS: fo.write('| %s | %s | %s |\n' % (n, d or '-', m))
    fo.write('\n```\n')
    for k, (n, t, d, m) in enumerate(VARS):
        fo.write('BPVar(VarName="%s",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E%03X,VarType=%s,FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5%s)\n'
                 % (n, k, t, n, (',DefaultValue="%s"' % d) if d else ''))
    fo.write('```\n')
print('VARIABLES.md', len(VARS))
