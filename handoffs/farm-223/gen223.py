# #223 Farming system (TGA, 2026-10-31; owner assignment): Blueprint-only, paste-ready.
#   BP_FarmPlot     (new Actor)     4x4 m field: 16 crop instances (ISM) that show the stage mesh (TGA FarmCrops #252):
#                                   0 bare, 1 sown, 2 growing, 3 ripe, 4 stubble. A tended crop grows one stage per in-game day;
#                                   DoWork = sow / tend / harvest (yield -> the farmer's basket); zombies walking in trample it.
#   BP_Farmer       (new Character) work loop every 0.5 s: find a plot that needs work -> walk -> work 6 s -> carry the harvest to
#                                   the granary (BP_FarmDirector) -> HUD Food. Flees to the granary at night or when a zombie is
#                                   within 20 m. HP 100, ragdoll on death, body gone after 30 s.
#   BP_FarmDirector (new Actor)     the granary in the yard: store + home, counts days (BP_DayNight dusk -> dawn), spawns the
#                                   farmers, keeps HUD Food / Farmers, save/load (slot CastleSaveFarm).
#   BP_FarmerHire   (new Actor)     a trigger next to the barracks NPC: [H] hire a farmer for Cost gold (max MaxFarmers).
#   BP_ZombieHUD    manifest_hud.json: "FOOD n   FARMERS n" under the ORE line (after #201's DrawOre).
#   BP_Zombie       manifest_zombie.json: after the zombie's soldier search, a living farmer within 25 m that is closer than
#                                   the current target becomes the target (zombies attack their Owner); a dead farmer target
#                                   is dropped back to the player.
#   python gen223.py  (Blender's python is fine: U:\5.2\python\bin\python.exe gen223.py)
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))          # bpkit's own HERE is imported above

P_FARM = '/Game/CastleDefender/Gameplay/Farm/'
P_PLOT, P_FARMER, P_DIRF, P_HIRE = P_FARM + 'BP_FarmPlot', P_FARM + 'BP_Farmer', P_FARM + 'BP_FarmDirector', P_FARM + 'BP_FarmerHire'
P_CASTLE = '/Game/CastleDefender/Gameplay/Castle/'
P_HUD, P_NOTICE = P_CASTLE + 'BP_ZombieHUD', P_CASTLE + 'BP_NoticeHUD'
P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
P_DN = '/Game/CastleDefender/Environment/DayNight/BP_DayNight'
PLOTC, FARMERC, FDIRC = BPC(P_PLOT, 'BP_FarmPlot'), BPC(P_FARMER, 'BP_Farmer'), BPC(P_DIRF, 'BP_FarmDirector')
HUDC, NOTC, HEROC, DNC = BPC(P_HUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD'), BPC(P_HERO, 'BP_ThirdPersonCharacter'), BPC(P_DN, 'BP_DayNight')
SAVEC = BPC('/Game/CastleDefender/Gameplay/Save/BP_CastleSave', 'BP_CastleSave')
SMC, SM, ISMC, HUDCLS, FONT = CLS('StaticMeshComponent'), CLS('StaticMesh'), CLS('InstancedStaticMeshComponent'), CLS('HUD'), CLS('Font')
CAPS, SAVEG = CLS('CapsuleComponent'), CLS('SaveGame')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
SLOT = 'CastleSaveFarm'
HIRE_TEXT = '[H] Hire a farmer: 60 gold. Farmers sow, tend and harvest the fields outside the walls.'


# ---------------------------------------------------------------- shared helpers
def event_override(b, nm, member, params, x, y):
    b.G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ACT, member), 'bOverrideFunction=True'],
             [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (ACT, member)}, ex('then', True)]
             + [dict(p, out=True) for p in params], x, y)
    return nm


def pc(b, x, y): return (b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')


def zhud(b, x, y):
    """exec cast of the player's HUD to BP_ZombieHUD -> (cast node, handle)."""
    hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x, y + 300, target=pc(b, x - 250, y + 300), pure=True, const=True, tag='HUD')
    zc = b.name('AsZombieHUD'); cast(b.G, zc, HUDC, 'AsBP Zombie HUD', x + 250, y); b.wire((hud, 'ReturnValue'), zc, 'Object')
    return zc, (zc, 'AsBP Zombie HUD'), (hud, 'ReturnValue')


def notice_hud(b, hud, x, y):
    nc = b.name('AsNoticeHUD'); cast(b.G, nc, NOTC, 'AsBP Notice HUD', x, y); b.wire(hud, nc, 'Object'); return nc, (nc, 'AsBP Notice HUD')


def notice(b, text, nh, x, y): return b.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x, y, target=nh, tag='Notice')


def is_night(b, x, y):
    dn = b.imp.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_DN)), ob('ReturnValue', DNC, out=True)], x, y, pure=True, tag='FindDayNight')
    return b.b2('BooleanAND', b.valid((dn, 'ReturnValue'), x + 300, y - 50), b.getm('IsNight', DNC, BOOL, (dn, 'ReturnValue'), x + 300, y + 100), x + 600, y)


def all_of(b, path, cls, x, y):
    """GetAllActorsOfClass + ForEachLoop -> (getall node, foreach node, element handle). getall.then -> foreach already linked."""
    ga = b.imp.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    fe = b.foreach(cls, x + 350, y); b.wire((ga, 'OutActors'), fe, 'Array'); b.G.link(ga, 'then', fe, 'Exec')
    return ga, fe, (fe, 'Array Element')


def dist_to(b, other, x, y, tag='Dist'):
    n = b.call_self('GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag=tag)
    b.wire(other, n, 'OtherActor'); return (n, 'ReturnValue')


def move_to(b, goal, x, y):
    ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], x, y + 250, PAWN, pure=True, const=True, tag='Ctl')
    mv = b.lib(NAVSYS, 'SimpleMoveToActor', [ob('Controller', CTRL), ob('Goal', ACT)], x + 250, y, tag='MoveTo')
    b.wire((ctl, 'ReturnValue'), mv, 'Controller'); b.wire(goal, mv, 'Goal'); return mv


def item(b, arrsrc, pin, idx, x, y, didx='0'):
    n = b.name('Item'); b.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default=didx), dict(pin, name='Output', out=True)], x, y)
    b.wire(arrsrc, n, 'Array'); b.wire(idx, n, 'Dimension 1'); return (n, 'Output')


def round_(b, a, x, y): return b.math('Round', [(D('A', default='0.0'), a)], it('ReturnValue', out=True), x, y)
def b2d(b, a, x, y): return b.math('Conv_BoolToDouble', [(bo('InBool', default='false'), a)], D('ReturnValue', out=True), x, y)
def eqi(b, a, v, x, y): return b.icmp('EqualEqual_IntInt', a, None, x, y, db=str(v))


def save_set(b, arrh, idx, val, x, y):
    """Array_Set(arr, idx, val) with bSizeToFit (grows the save array)."""
    n = b.name('SetData')
    b.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Set")' % KARR],
             [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
              it('Index', default='0'), {'name': 'Item', 'cat': 'wildcard', 'ref': True, 'default': '0.0'}, bo('bSizeToFit', default='true')], x, y)
    b.wire(arrh, n, 'TargetArray'); b.wire(idx, n, 'Index'); b.wire(val, n, 'Item'); return n


def write(name, G):
    open(os.path.join(HERE, name), 'w', encoding='utf-8').write(G.render()); print(name, len(G.nodes), 'nodes')


# ================================================================ BP_FarmPlot
G = Graph(); b = B(G, 'fp'); b.imp = B(G, 'fpQ')   # Q* = nodes fix_impure must splice
bp = b.override('PlotBeginPlay', 'ReceiveBeginPlay', 0, 0)
fl_ = b.name('ForLoop')                                                    # 16 crop instances: 0..15
G.node(fl_, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FORLOOP],
       [ex(), it('FirstIndex', default='0'), it('LastIndex', default='15'), ex('LoopBody', True), it('Index', out=True), ex('Completed', True)], 300, 0)
G.link(bp, 'then', fl_, 'execute')
idx = (fl_, 'Index')
col = b.i2('Percent_IntInt', idx, None, 300, 400, db='4'); row = b.i2('Divide_IntInt', idx, None, 300, 550, db='4')
lx = b.d2('Subtract_DoubleDouble', b.d2('Multiply_DoubleDouble', b.i2d(col, 550, 400), None, 800, 400, db='100.0'), None, 1050, 400, db='150.0')
ly = b.d2('Subtract_DoubleDouble', b.d2('Multiply_DoubleDouble', b.i2d(row, 550, 550), None, 800, 550, db='100.0'), None, 1050, 550, db='150.0')
yaw = b.d2('Multiply_DoubleDouble', b.i2d(b.i2('Percent_IntInt', idx, None, 550, 700, db='2'), 800, 700), None, 1050, 700, db='180.0')   # rows stay on the ridges
rot = b.math('MakeRotator', [(D('Roll', default='0.0'), None), (D('Pitch', default='0.0'), None), (D('Yaw', default='0.0'), yaw)], st('ReturnValue', ROT, out=True), 1300, 700)
xf = b.math('MakeTransform', [(V('Location'), b.vec(lx, ly, None, 1300, 450)), (st('Rotation', ROT, default='0, 0, 0'), rot), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
            st('ReturnValue', XFORM, out=True), 1550, 450)
ai = b.call(ISMC, 'AddInstance', [st('InstanceTransform', XFORM), bo('bWorldSpace', default='false'), it('ReturnValue', out=True)], 1800, 0,
            target=b.get('Crops', ob('v', ISMC), 1600, 250), tag='AddCrop')
b.wire(xf, ai, 'InstanceTransform'); G.link(fl_, 'LoopBody', ai, 'execute')
G.link(fl_, 'Completed', b.call_self('ApplyStage', [], 2100, 300, PLOTC, tag='CallApply'), 'execute')
# ---- ApplyStage: Crops shows StageMeshes[Kind*5 + Stage], hidden when that slot is empty (bare / cleared cabbage)
Y = 1200
b.event('ApplyStage', [], 0, Y)
si = b.i2('Add_IntInt', b.i2('Multiply_IntInt', b.get('Kind', INT, 0, Y + 300), None, 250, Y + 300, db='5'), b.get('Stage', INT, 250, Y + 450), 500, Y + 350)
mesh = b.aget('StageMeshes', ob('v', SM), si, 700, Y + 350)
ss_ = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SM), bo('ReturnValue', out=True, default='false')], 1100, Y, target=b.get('Crops', ob('v', ISMC), 900, Y + 200), tag='StageMesh')
b.wire(mesh, ss_, 'NewMesh'); G.link('ApplyStage', 'then', ss_, 'execute')
vis = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='true'), bo('bPropagateToChildren', default='false')], 1400, Y, target=b.get('Crops', ob('v', ISMC), 1200, Y + 200), tag='StageVis')
b.wire(b.b2('BooleanAND', b.valid(mesh, 1150, Y + 400), b.icmp('Greater_IntInt', b.get('Stage', INT, 1150, Y + 550), None, 1350, Y + 550, db='0'), 1550, Y + 450), vis, 'bNewVisibility')
G.link(ss_, 'then', vis, 'execute')
# ---- NewDay: a tended sown/growing crop moves up one stage
Y = 2000
b.event('NewDay', [], 0, Y)
st_ = b.get('Stage', INT, 0, Y + 300)
growing = b.b2('BooleanOR', eqi(b, st_, 1, 250, Y + 300), eqi(b, st_, 2, 250, Y + 450), 500, Y + 350)
bg = b.branch(b.b2('BooleanAND', growing, b.get('Tended', BOOL, 500, Y + 500), 750, Y + 400), 300, Y, 'IfGrow'); G.link('NewDay', 'then', bg, 'execute')
s1 = b.set('Stage', INT, b.i2('Add_IntInt', b.get('Stage', INT, 600, Y + 650), None, 850, Y + 650, db='1'), 1000, Y); G.link(bg, 'then', s1, 'execute')
s2 = b.set('Tended', BOOL, None, 1300, Y); G.link(s1, 'then', s2, 'execute')
G.link(s2, 'then', b.call_self('ApplyStage', [], 1600, Y, PLOTC, tag='CallApply'), 'execute')
# ---- DoWork: harvest a ripe crop (LastYield = Yield, stubble), tend a growing one, or sow a bare / stubble plot
Y = 2800
b.event('DoWork', [], 0, Y)
s0 = b.set('LastYield', INT, None, 250, Y); G.link('DoWork', 'then', s0, 'execute')
br = b.branch(eqi(b, b.get('Stage', INT, 250, Y + 300), 3, 450, Y + 300), 550, Y, 'IfRipe'); G.link(s0, 'then', br, 'execute')
h1 = b.set('LastYield', INT, b.get('Yield', INT, 700, Y + 300), 850, Y); G.link(br, 'then', h1, 'execute')
h2 = b.set('Stage', it('v', default='4'), None, 1100, Y); G.link(h1, 'then', h2, 'execute')
st2 = b.get('Stage', INT, 700, Y + 650)
bt = b.branch(b.b2('BooleanOR', eqi(b, st2, 1, 900, Y + 650), eqi(b, st2, 2, 900, Y + 800), 1100, Y + 700), 850, Y + 400, 'IfGrowing'); G.link(br, 'else', bt, 'execute')
t1 = b.set('Tended', bo('v', default='true'), None, 1100, Y + 400); G.link(bt, 'then', t1, 'execute')
w1 = b.set('Stage', it('v', default='1'), None, 1100, Y + 600); G.link(bt, 'else', w1, 'execute')
w2 = b.set('Tended', BOOL, None, 1350, Y + 600); G.link(w1, 'then', w2, 'execute')
rc = b.set('Claimed', BOOL, None, 1650, Y); G.link(h2, 'then', rc, 'execute'); G.link(t1, 'then', rc, 'execute'); G.link(w2, 'then', rc, 'execute')
G.link(rc, 'then', b.call_self('ApplyStage', [], 1950, Y, PLOTC, tag='CallApply'), 'execute')
# ---- trample: a zombie walking into the field ruins a sown / growing / ripe crop (stubble, no yield)
Y = 3800
ov = event_override(b, 'PlotOverlap', 'ReceiveActorBeginOverlap', [ob('OtherActor', ACT)], 0, Y)
cz = b.name('AsZombie'); cast(G, cz, ZOMBIE, 'AsBP Zombie', 300, Y); b.wire((ov, 'OtherActor'), cz, 'Object'); G.link(ov, 'then', cz, 'execute')
st3 = b.get('Stage', INT, 500, Y + 300)
bz = b.branch(b.b2('BooleanAND', b.icmp('GreaterEqual_IntInt', st3, None, 700, Y + 300, db='1'), b.icmp('LessEqual_IntInt', st3, None, 700, Y + 450, db='3'), 900, Y + 350), 700, Y, 'IfCrop')
G.link(cz, 'then', bz, 'execute')
z1 = b.set('Stage', it('v', default='4'), None, 1000, Y); G.link(bz, 'then', z1, 'execute')
z2 = b.set('Tended', BOOL, None, 1250, Y); G.link(z1, 'then', z2, 'execute')
z3 = b.call_self('ApplyStage', [], 1500, Y, PLOTC, tag='CallApply'); G.link(z2, 'then', z3, 'execute')
fd = b.imp.actor_of(P_DIRF, FDIRC, 1500, Y + 300)
z4 = b.call(FDIRC, 'SaveNow', [], 1800, Y, target=(fd, 'ReturnValue'), tag='DirSave'); G.link(z3, 'then', z4, 'execute')
write('BP_FarmPlot_graph.txt', G)


# ================================================================ BP_Farmer
G = Graph(); b = B(G, 'fm'); b.imp = B(G, 'fmQ')   # Q* = nodes fix_impure must splice
bp = b.override('FarmerBeginPlay', 'ReceiveBeginPlay', 0, 0)
G.link(bp, 'then', b.timer('Think', 300, 0, dtime='0.5', loop=True), 'execute')
plot = lambda x, y: b.get('Plot', ob('v', PLOTC), x, y)
state = lambda x, y: b.get('State', INT, x, y)
def granary(x, y): return (b.imp.actor_of(P_DIRF, FDIRC, x, y), 'ReturnValue')
def set_state(v, x, y): return b.set('State', it('v', default=str(v)), None, x, y)
# ---- Think (0.5 s): dead -> nothing; zombie near or night -> flee home; else the work loop by State
Y = 600
b.event('Think', [], 0, Y)
bd = b.branch(b.get('Dead', BOOL, 0, Y + 250), 250, Y, 'IfDead'); G.link('Think', 'then', bd, 'execute')
sd0 = b.set('Danger', BOOL, None, 500, Y); G.link(bd, 'else', sd0, 'execute')
ga, fe, z = all_of(b, P_ZOMBIE, ZOMBIE, 750, Y); G.link(sd0, 'then', ga, 'execute')
near = b.b2('BooleanAND', b.bnot(b.getm('Dead', ZOMBIE, BOOL, z, 1100, Y + 350), 1300, Y + 350),
            b.dcmp('Less_DoubleDouble', dist_to(b, z, 1100, Y + 500), b.get('FleeRadius', D('v', default='2000.0'), 1100, Y + 650), 1300, Y + 550), 1500, Y + 400)
bn = b.branch(near, 1500, Y + 150, 'IfZombieNear'); G.link(fe, 'LoopBody', bn, 'execute')
G.link(bn, 'then', b.set('Danger', bo('v', default='true'), None, 1750, Y + 150), 'execute')
flee = b.b2('BooleanOR', b.get('Danger', BOOL, 1500, Y + 800), is_night(b, 1200, Y + 950), 1900, Y + 850)
bf = b.branch(flee, 1800, Y, 'IfFlee'); G.link(fe, 'Completed', bf, 'execute')
# flee: once (State < 4): release the plot, State 4, run to the granary; State 4 at the granary -> 5 (home)
bfo = b.branch(b.icmp('Less_IntInt', state(1900, Y - 300), None, 2100, Y - 300, db='4'), 2100, Y - 150, 'IfNotFleeing'); G.link(bf, 'then', bfo, 'execute')
rl = b.call_self('ReleasePlot', [], 2400, Y - 150, FARMERC, tag='CallRelease'); G.link(bfo, 'then', rl, 'execute')
s4 = set_state(4, 2650, Y - 150); G.link(rl, 'then', s4, 'execute')
G.link(s4, 'then', move_to(b, granary(2650, Y + 100), 2900, Y - 150), 'execute')
bh = b.branch(b.b2('BooleanAND', eqi(b, state(2100, Y - 600), 4, 2300, Y - 600),
                   b.dcmp('Less_DoubleDouble', dist_to(b, granary(2100, Y - 450), 2300, Y - 450), None, 2500, Y - 450, db='600.0'), 2700, Y - 500), 2400, Y - 400, 'IfHome')
G.link(bfo, 'else', bh, 'execute'); G.link(bh, 'then', set_state(5, 2700, Y - 400), 'execute')
# safe: State 1 walking / 2 working / 3 carrying / else (0 idle, 4-5 back from fleeing) -> pick the next job
X = 2100; Y2 = Y + 1400
b1 = b.branch(eqi(b, state(X, Y2 + 250), 1, X + 200, Y2 + 250), X + 200, Y2, 'IfWalking'); G.link(bf, 'else', b1, 'execute')
b2_ = b.branch(eqi(b, state(X, Y2 + 650), 2, X + 200, Y2 + 650), X + 200, Y2 + 400, 'IfWorking'); G.link(b1, 'else', b2_, 'execute')
b3 = b.branch(eqi(b, state(X, Y2 + 1050), 3, X + 200, Y2 + 1050), X + 200, Y2 + 800, 'IfCarrying'); G.link(b2_, 'else', b3, 'execute')
G.link(b3, 'else', b.call_self('NextJob', [], X + 500, Y2 + 1200, FARMERC, tag='CallNextJob'), 'execute')
# 1: at the plot (3.5 m) -> stop, work for WorkSeconds; plot gone -> idle
bv = b.branch(b.valid(plot(X + 400, Y2 + 250), X + 600, Y2 + 250), X + 500, Y2, 'IfPlot'); G.link(b1, 'then', bv, 'execute')
G.link(bv, 'else', set_state(0, X + 800, Y2 + 150), 'execute')
ba = b.branch(b.dcmp('Less_DoubleDouble', dist_to(b, plot(X + 700, Y2 + 300), X + 900, Y2 + 300), None, X + 1100, Y2 + 300, db='350.0'), X + 800, Y2 - 150, 'IfAtPlot')
G.link(bv, 'then', ba, 'execute')
sw = set_state(2, X + 1100, Y2 - 150); G.link(ba, 'then', sw, 'execute')
stop = b.call(CMC, 'StopMovementImmediately', [], X + 1350, Y2 - 150, target=b.get('CharacterMovement', ob('v', CMC), X + 1200, Y2 + 50), tag='Stop')
G.link(sw, 'then', stop, 'execute')
wu = b.set('WorkUntil', DBL, b.d2('Add_DoubleDouble', b.now(X + 1350, Y2 + 150), b.get('WorkSeconds', D('v', default='6.0'), X + 1350, Y2 + 300), X + 1600, Y2 + 200), X + 1650, Y2 - 150)
G.link(stop, 'then', wu, 'execute')
# 2: work done -> Plot.DoWork, harvest into the basket, idle
bw = b.branch(b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', b.now(X + 400, Y2 + 650), b.get('WorkUntil', DBL, X + 400, Y2 + 800), X + 650, Y2 + 700),
                   b.valid(plot(X + 650, Y2 + 900), X + 850, Y2 + 900), X + 1050, Y2 + 750), X + 500, Y2 + 400, 'IfWorkDone')
G.link(b2_, 'then', bw, 'execute')
dw = b.call(PLOTC, 'DoWork', [], X + 800, Y2 + 400, target=plot(X + 650, Y2 + 550), tag='PlotWork'); G.link(bw, 'then', dw, 'execute')
sc = b.set('Carry', INT, b.i2('Add_IntInt', b.get('Carry', INT, X + 900, Y2 + 600), b.getm('LastYield', PLOTC, INT, plot(X + 900, Y2 + 750), X + 1100, Y2 + 750), X + 1300, Y2 + 650),
           X + 1100, Y2 + 400); G.link(dw, 'then', sc, 'execute')
G.link(sc, 'then', set_state(0, X + 1400, Y2 + 400), 'execute')
# 3: at the granary (5 m) -> HUD Food += Carry, basket empty, save
bg_ = b.branch(b.dcmp('Less_DoubleDouble', dist_to(b, granary(X + 300, Y2 + 1050), X + 550, Y2 + 1050), None, X + 750, Y2 + 1050, db='500.0'), X + 500, Y2 + 800, 'IfAtGranary')
G.link(b3, 'then', bg_, 'execute')
zc, zh, _ = zhud(b, X + 900, Y2 + 800); G.link(bg_, 'then', zc, 'execute')
fd_ = b.setm('Food', HUDC, INT, b.i2('Add_IntInt', b.getm('Food', HUDC, INT, zh, X + 1200, Y2 + 1100), b.get('Carry', INT, X + 1200, Y2 + 1250), X + 1450, Y2 + 1150), zh, X + 1500, Y2 + 800)
G.link(zc, 'then', fd_, 'execute')
c0 = b.set('Carry', INT, None, X + 1800, Y2 + 800); G.link(fd_, 'then', c0, 'execute')
s0 = set_state(0, X + 2050, Y2 + 800); G.link(c0, 'then', s0, 'execute')
G.link(s0, 'then', b.call(FDIRC, 'SaveNow', [], X + 2300, Y2 + 800, target=granary(X + 2100, Y2 + 1050), tag='DirSave'), 'execute')
# ---- NextJob: carry the basket home first; else the first plot that needs work and is free
Y = 4200
b.event('NextJob', [], 0, Y)
i0 = set_state(0, 250, Y); G.link('NextJob', 'then', i0, 'execute')
bc = b.branch(b.icmp('Greater_IntInt', b.get('Carry', INT, 300, Y + 250), None, 500, Y + 250, db='0'), 550, Y, 'IfBasket'); G.link(i0, 'then', bc, 'execute')
s3 = set_state(3, 800, Y); G.link(bc, 'then', s3, 'execute'); G.link(s3, 'then', move_to(b, granary(800, Y + 250), 1050, Y), 'execute')
ga, fe, p = all_of(b, P_PLOT, PLOTC, 800, Y + 500); G.link(bc, 'else', ga, 'execute')
pst = b.getm('Stage', PLOTC, INT, p, 1200, Y + 900)
growing = b.b2('BooleanOR', eqi(b, pst, 1, 1400, Y + 900), eqi(b, pst, 2, 1400, Y + 1050), 1600, Y + 950)
done = b.b2('BooleanAND', growing, b.getm('Tended', PLOTC, BOOL, p, 1600, Y + 1100), 1800, Y + 1000)            # tended and growing: nothing to do today
needs = b.b2('BooleanAND', b.bnot(done, 2000, Y + 1000), b.bnot(b.getm('Claimed', PLOTC, BOOL, p, 1800, Y + 1200), 2000, Y + 1200), 2200, Y + 1100)
free = b.b2('BooleanAND', needs, eqi(b, state(2000, Y + 1350), 0, 2200, Y + 1350), 2400, Y + 1200)
bp_ = b.branch(free, 1500, Y + 500, 'IfJob'); G.link(fe, 'LoopBody', bp_, 'execute')
sp = b.set('Plot', ob('v', PLOTC), p, 1800, Y + 500); G.link(bp_, 'then', sp, 'execute')
cl = b.setm('Claimed', PLOTC, bo('v', default='true'), None, p, 2050, Y + 500); G.link(sp, 'then', cl, 'execute')
s1_ = set_state(1, 2300, Y + 500); G.link(cl, 'then', s1_, 'execute')
G.link(s1_, 'then', move_to(b, p, 2550, Y + 500), 'execute')
# ---- ReleasePlot: free the claimed plot
Y = 6000
b.event('ReleasePlot', [], 0, Y)
br_ = b.branch(b.valid(plot(0, Y + 250), 200, Y + 250), 250, Y, 'IfPlot'); G.link('ReleasePlot', 'then', br_, 'execute')
rc = b.setm('Claimed', PLOTC, BOOL, None, plot(400, Y + 250), 550, Y); G.link(br_, 'then', rc, 'execute')
G.link(rc, 'then', b.set('Plot', ob('v', PLOTC), None, 850, Y), 'execute')
# ---- AnyDamage: HP; at 0 -> ragdoll, tell the granary, gone after 30 s
Y = 6600
dm = event_override(b, 'FarmerAnyDamage', 'ReceiveAnyDamage', [fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CTRL), ob('DamageCauser', ACT)], 0, Y)
hp = b.set('HP', DBL, b.d2('Subtract_DoubleDouble', b.get('HP', DBL, 250, Y + 300), (dm, 'Damage'), 450, Y + 300), 600, Y); G.link(dm, 'then', hp, 'execute')
bk = b.branch(b.b2('BooleanAND', b.dcmp('LessEqual_DoubleDouble', b.get('HP', DBL, 700, Y + 300), None, 900, Y + 300, db='0.0'), b.bnot(b.get('Dead', BOOL, 700, Y + 450), 900, Y + 450), 1100, Y + 350),
              900, Y, 'IfKilled'); G.link(hp, 'then', bk, 'execute')
k1 = b.set('Dead', bo('v', default='true'), None, 1150, Y); G.link(bk, 'then', k1, 'execute')
k2 = b.call_self('ReleasePlot', [], 1400, Y, FARMERC, tag='CallRelease'); G.link(k1, 'then', k2, 'execute')
mesh = lambda x, y: b.get('Mesh', ob('v', SKEL), x, y)
k3 = b.call(PRIM, 'SetCollisionProfileName', [N('InProfileName', default='Ragdoll'), bo('bUpdateOverlaps', default='true')], 1650, Y, target=mesh(1500, Y + 250), tag='Ragdoll')
G.link(k2, 'then', k3, 'execute')
k4 = b.call(PRIM, 'SetSimulatePhysics', [bo('bSimulate', default='true')], 1950, Y, target=mesh(1800, Y + 250), tag='Physics'); G.link(k3, 'then', k4, 'execute')
k5 = b.call(PRIM, 'SetCollisionEnabled', [{'name': 'NewType', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.ECollisionEnabled\'"', 'default': 'NoCollision'}],
            2250, Y, target=b.get('CapsuleComponent', ob('v', CAPS), 2100, Y + 250), tag='CapsuleOff'); G.link(k4, 'then', k5, 'execute')
k6 = b.call(CMC, 'DisableMovement', [], 2550, Y, target=b.get('CharacterMovement', ob('v', CMC), 2400, Y + 250), tag='NoMove'); G.link(k5, 'then', k6, 'execute')
k7 = b.call(FDIRC, 'FarmerDied', [], 2850, Y, target=granary(2650, Y + 250), tag='DirDied'); G.link(k6, 'then', k7, 'execute')
G.link(k7, 'then', b.call_self('SetLifeSpan', [fl('InLifespan', default='30.0')], 3150, Y, ACT, tag='BodyLife'), 'execute')
write('BP_Farmer_graph.txt', G)


# ================================================================ BP_FarmDirector (the granary: store, home, days, farmers, save)
G = Graph(); b = B(G, 'fd'); b.imp = B(G, 'fdQ')   # Q* = nodes fix_impure must splice
bp = b.override('DirBeginPlay', 'ReceiveBeginPlay', 0, 0)
t1 = b.timer('LoadSaved', 300, 0, dtime='0.3'); G.link(bp, 'then', t1, 'execute')     # after the HUD exists
G.link(t1, 'then', b.timer('Poll', 600, 0, dtime='1.0', loop=True), 'execute')
dat_t = arr(D('v'))
def plots(x, y): return all_of(b, P_PLOT, PLOTC, x, y)
def pidx(p, extra, x, y):
    return b.i2('Add_IntInt', b.i2('Multiply_IntInt', b.getm('PlotId', PLOTC, INT, p, x, y), None, x + 200, y, db='2'), None, x + 400, y, db=str(3 + extra))
# ---- LoadSaved: Data = [Food, Farmers, Day, (Stage, Tended) x PlotId]; no save -> StartFarmers
Y = 600
b.event('LoadSaved', [], 0, Y)
hs = b.imp.lib(GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 0, Y + 250, pure=True, tag='HasSave')
bl = b.branch((hs, 'ReturnValue'), 300, Y, 'IfSave'); G.link('LoadSaved', 'then', bl, 'execute')
ns = b.set('SpawnLeft', INT, b.get('StartFarmers', it('v', default='3'), 400, Y + 500), 600, Y + 400); G.link(bl, 'else', ns, 'execute')
G.link(ns, 'then', b.call_self('SpawnSome', [], 900, Y + 400, FDIRC, tag='CallSpawnSome'), 'execute')
ld = b.imp.lib(GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', SAVEG, out=True)], 600, Y, tag='Load'); G.link(bl, 'then', ld, 'execute')
cast(G, 'fdQAsLoad', SAVEC, 'AsBP Castle Save', 600, Y - 300, pure=True); b.wire((ld, 'ReturnValue'), 'fdQAsLoad', 'Object')
sdat = b.set('SaveData', dat_t, b.getm('Data', SAVEC, arr(D('Data')), ('fdQAsLoad', 'AsBP Castle Save'), 850, Y - 300), 900, Y); G.link(ld, 'then', sdat, 'execute')
dat = lambda x, y: b.get('SaveData', dat_t, x, y)
zc, zh, _ = zhud(b, 1200, Y); G.link(sdat, 'then', zc, 'execute')
sf = b.setm('Food', HUDC, INT, round_(b, item(b, dat(1300, Y + 600), D('v'), None, 1500, Y + 600, didx='0'), 1700, Y + 600), zh, 1700, Y); G.link(zc, 'then', sf, 'execute')
G.link(zc, 'CastFailed', sf, 'execute')    # never: the HUD exists by now; keeps the chain going if not
s_n = b.set('SpawnLeft', INT, round_(b, item(b, dat(1900, Y + 600), D('v'), None, 2100, Y + 600, didx='1'), 2300, Y + 600), 2000, Y); G.link(sf, 'then', s_n, 'execute')
s_d = b.set('Day', INT, round_(b, item(b, dat(2300, Y + 800), D('v'), None, 2500, Y + 800, didx='2'), 2700, Y + 800), 2300, Y); G.link(s_n, 'then', s_d, 'execute')
ga, fe, p = plots(2600, Y); G.link(s_d, 'then', ga, 'execute')
ln = b.name('LenData'); G.node(ln, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                              [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 3100, Y + 600)
b.wire(dat(2900, Y + 600), ln, 'TargetArray')
i1 = pidx(p, 1, 2900, Y + 800)
bin_ = b.branch(b.icmp('Greater_IntInt', (ln, 'ReturnValue'), i1, 3400, Y + 700), 3100, Y, 'IfInSave'); G.link(fe, 'LoopBody', bin_, 'execute')
ps = b.setm('Stage', PLOTC, INT, round_(b, item(b, dat(3300, Y + 1000), D('v'), pidx(p, 0, 3100, Y + 1100), 3600, Y + 1000), 3800, Y + 1000), p, 3400, Y)
G.link(bin_, 'then', ps, 'execute')
pt = b.setm('Tended', PLOTC, BOOL, b.dcmp('Greater_DoubleDouble', item(b, dat(3600, Y + 1300), D('v'), i1, 3800, Y + 1300), None, 4000, Y + 1300, db='0.5'), p, 3700, Y)
G.link(ps, 'then', pt, 'execute')
G.link(pt, 'then', b.call(PLOTC, 'ApplyStage', [], 4000, Y, target=p, tag='PlotApply'), 'execute')
G.link(fe, 'Completed', b.call_self('SpawnSome', [], 3400, Y - 300, FDIRC, tag='CallSpawnSome'), 'execute')
# ---- SpawnSome: SpawnLeft farmers
Y = 2400
b.event('SpawnSome', [], 0, Y)
fl2 = b.name('ForLoop')                                                   # 1..SpawnLeft
G.node(fl2, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FORLOOP],
       [ex(), it('FirstIndex', default='1'), it('LastIndex', default='0'), ex('LoopBody', True), it('Index', out=True), ex('Completed', True)], 300, Y)
b.wire(b.get('SpawnLeft', INT, 0, Y + 300), fl2, 'LastIndex'); G.link('SpawnSome', 'then', fl2, 'execute')
G.link(fl2, 'LoopBody', b.call_self('SpawnFarmer', [], 650, Y, FDIRC, tag='CallSpawnFarmer'), 'execute')
# ---- SpawnFarmer: one farmer near the granary, Alive + 1
Y = 3000
b.event('SpawnFarmer', [], 0, Y)
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 0, Y + 300, ACT, pure=True, const=True, tag='Here')
off = b.vec(b.rnd('-300.0', '300.0', 0, Y + 450), b.rnd('-300.0', '300.0', 0, Y + 600), None, 250, Y + 500, dz='120.0')
sp = spawn(b, P_FARMER, FARMERC, transform(b, b.v2('Add_VectorVector', (me, 'ReturnValue'), off, 500, Y + 350), 750, Y + 350), 300, Y)
G.link('SpawnFarmer', 'then', sp, 'execute')
al = b.set('Alive', INT, b.i2('Add_IntInt', b.get('Alive', INT, 600, Y + 600), None, 800, Y + 600, db='1'), 1000, Y); G.link(sp, 'then', al, 'execute')
G.link(al, 'then', b.call_self('UpdateHUD', [], 1300, Y, FDIRC, tag='CallUpdateHUD'), 'execute')
# ---- UpdateHUD / FarmerDied
Y = 3700
b.event('UpdateHUD', [], 0, Y)
zc, zh, _ = zhud(b, 300, Y); G.link('UpdateHUD', 'then', zc, 'execute')
G.link(zc, 'then', b.setm('Farmers', HUDC, INT, b.get('Alive', INT, 700, Y + 300), zh, 900, Y), 'execute')
Y = 4300
b.event('FarmerDied', [], 0, Y)
ad = b.set('Alive', INT, b.i2('Subtract_IntInt', b.get('Alive', INT, 0, Y + 300), None, 200, Y + 300, db='1'), 300, Y); G.link('FarmerDied', 'then', ad, 'execute')
b.chain(ad, b.call_self('UpdateHUD', [], 600, Y, FDIRC, tag='CallUpdateHUD'), b.call_self('SaveNow', [], 900, Y, FDIRC, tag='CallSaveNow'))
# ---- Poll (1 s): dusk -> dawn = a new day: every plot grows, save
Y = 5000
b.event('Poll', [], 0, Y)
night = is_night(b, 0, Y + 400)
bday = b.branch(b.b2('BooleanAND', b.get('WasNight', BOOL, 700, Y + 250), b.bnot(night, 900, Y + 400), 1100, Y + 300), 700, Y, 'IfDawn'); G.link('Poll', 'then', bday, 'execute')
dd = b.set('Day', INT, b.i2('Add_IntInt', b.get('Day', INT, 950, Y + 600), None, 1150, Y + 600, db='1'), 1000, Y); G.link(bday, 'then', dd, 'execute')
ga, fe, p = plots(1300, Y); G.link(dd, 'then', ga, 'execute')
G.link(fe, 'LoopBody', b.call(PLOTC, 'NewDay', [], 1900, Y + 200, target=p, tag='PlotNewDay'), 'execute')
sv = b.call_self('SaveNow', [], 1900, Y - 200, FDIRC, tag='CallSaveNow'); G.link(fe, 'Completed', sv, 'execute')
wn = b.set('WasNight', BOOL, night, 2200, Y - 200); G.link(sv, 'then', wn, 'execute'); G.link(bday, 'else', wn, 'execute')
# ---- SaveNow: Data = [Food, Alive, Day, (Stage, Tended) x PlotId] -> slot CastleSaveFarm
Y = 6000
b.event('SaveNow', [], 0, Y)
zc, zh, _ = zhud(b, 300, Y); G.link('SaveNow', 'then', zc, 'execute')
mk = b.name('MakeData'); G.node(mk, 'K2Node_MakeArray', ['NumInputs=3'], [D('[0]', default='0.0'), D('[1]', default='0.0'), D('[2]', default='0.0'), arr(D('Array', out=True))], 700, Y + 300)
b.wire(b.i2d(b.getm('Food', HUDC, INT, zh, 450, Y + 300), 600, Y + 300), mk, '[0]'); b.wire(b.i2d(b.get('Alive', INT, 450, Y + 450), 600, Y + 450), mk, '[1]')
b.wire(b.i2d(b.get('Day', INT, 450, Y + 600), 600, Y + 600), mk, '[2]')
s0 = b.set('SaveData', dat_t, (mk, 'Array'), 900, Y); G.link(zc, 'then', s0, 'execute')
ga, fe, p = plots(1200, Y); G.link(s0, 'then', ga, 'execute')
a1 = save_set(b, dat(1600, Y + 500), pidx(p, 0, 1500, Y + 650), b.i2d(b.getm('Stage', PLOTC, INT, p, 1500, Y + 800), 1700, Y + 800), 1900, Y + 300)
a2 = save_set(b, dat(2000, Y + 500), pidx(p, 1, 1900, Y + 650), b2d(b, b.getm('Tended', PLOTC, BOOL, p, 1900, Y + 800), 2100, Y + 800), 2300, Y + 300)
G.link(fe, 'LoopBody', a1, 'execute'); G.link(a1, 'then', a2, 'execute')
cs = b.imp.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SAVEG, '/Game/CastleDefender/Gameplay/Save/BP_CastleSave.BP_CastleSave_C'), ob('ReturnValue', SAVEC, out=True)], 1700, Y - 300, tag='NewSave')
G.link(fe, 'Completed', cs, 'execute')
cast(G, 'fdQAsSave', SAVEC, 'AsBP Castle Save', 1700, Y - 600, pure=True); b.wire((cs, 'ReturnValue'), 'fdQAsSave', 'Object')
sd = b.setm('Data', SAVEC, arr(D('Data')), dat(2000, Y - 450), ('fdQAsSave', 'AsBP Castle Save'), 2100, Y - 300); G.link(cs, 'then', sd, 'execute')
svg = b.imp.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SAVEG), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 2400, Y - 300, tag='Save')
b.wire(('fdQAsSave', 'AsBP Castle Save'), svg, 'SaveGameObject'); G.link(sd, 'then', svg, 'execute')
write('BP_FarmDirector_graph.txt', G)

# ================================================================ BP_FarmerHire (trigger beside the barracks NPC)
G = Graph(); b = B(G, 'fh'); b.imp = B(G, 'fhQ')   # Q* = nodes fix_impure must splice
ov = event_override(b, 'HireEnter', 'ReceiveActorBeginOverlap', [ob('OtherActor', ACT)], 0, 0)
cs = b.name('AsHero'); cast(G, cs, HEROC, 'AsBP Third Person Character', 300, 0); b.wire((ov, 'OtherActor'), cs, 'Object'); G.link(ov, 'then', cs, 'execute')
en = b.call_self('EnableInput', [ob('PlayerController', PCON)], 700, 0, ACT, tag='EnableInput'); b.wire(pc(b, 450, 300), en, 'PlayerController'); G.link(cs, 'then', en, 'execute')
zc, zh, hud = zhud(b, 1000, 0); G.link(en, 'then', zc, 'execute')
nc, nh = notice_hud(b, hud, 1500, 0); G.link(zc, 'then', nc, 'execute'); G.link(nc, 'then', notice(b, HIRE_TEXT, nh, 1850, 0), 'execute')
ov2 = event_override(b, 'HireLeave', 'ReceiveActorEndOverlap', [ob('OtherActor', ACT)], 0, 700)
cs2 = b.name('AsHero2'); cast(G, cs2, HEROC, 'AsBP Third Person Character', 300, 700); b.wire((ov2, 'OtherActor'), cs2, 'Object'); G.link(ov2, 'then', cs2, 'execute')
dis = b.call_self('DisableInput', [ob('PlayerController', PCON)], 700, 700, ACT, tag='DisableInput'); b.wire(pc(b, 450, 1000), dis, 'PlayerController'); G.link(cs2, 'then', dis, 'execute')
Y = 1500
G.node('fhKeyH', 'K2Node_InputKey', ['InputKey=H', 'bConsumeInput=True'], [ex('Pressed', True), ex('Released', True), st('Key', KEY, out=True)], 0, Y)
zc, zh, hud = zhud(b, 300, Y); G.link('fhKeyH', 'Pressed', zc, 'execute')
nc, nh = notice_hud(b, hud, 800, Y); G.link(zc, 'then', nc, 'execute')
fd = (b.imp.actor_of(P_DIRF, FDIRC, 900, Y + 300), 'ReturnValue')
bfull = b.branch(b.icmp('GreaterEqual_IntInt', b.getm('Alive', FDIRC, INT, fd, 1150, Y + 300), b.get('MaxFarmers', it('v', default='12'), 1150, Y + 450), 1400, Y + 350), 1150, Y, 'IfFull')
G.link(nc, 'then', bfull, 'execute'); G.link(bfull, 'then', notice(b, 'No room for more farmers.', nh, 1450, Y - 200), 'execute')
cost = lambda x, y: b.get('Cost', it('v', default='60'), x, y)
bgold = b.branch(b.icmp('GreaterEqual_IntInt', b.getm('Gold', HUDC, INT, zh, 1450, Y + 300), cost(1450, Y + 450), 1650, Y + 350), 1450, Y, 'IfGold')
G.link(bfull, 'else', bgold, 'execute'); G.link(bgold, 'else', notice(b, 'Not enough gold: a farmer costs 60.', nh, 1750, Y + 250), 'execute')
pay = b.setm('Gold', HUDC, INT, b.i2('Subtract_IntInt', b.getm('Gold', HUDC, INT, zh, 1700, Y + 500), cost(1700, Y + 650), 1900, Y + 550), zh, 1750, Y)
G.link(bgold, 'then', pay, 'execute')
b.chain(pay, b.call(FDIRC, 'SpawnFarmer', [], 2050, Y, target=fd, tag='DirSpawn'), b.call(FDIRC, 'SaveNow', [], 2350, Y, target=fd, tag='DirSave'),
        notice(b, 'A farmer joins the fields (-60 gold).', nh, 2650, Y))
write('BP_FarmerHire_graph.txt', G)


# ================================================================ BP_ZombieHUD: "FOOD n   FARMERS n" under the ORE line
G = Graph(); b = B(G, 'hf'); b.imp = B(G, 'hfQ')   # Q* = nodes fix_impure must splice
pcn = pc(b, 0, 400)
vs = b.call(PCON, 'GetViewportSize', [it('SizeX', out=True), it('SizeY', out=True)], 250, 400, target=pcn, pure=True, const=True, tag='ViewSize')
sx = b.d2('Multiply_DoubleDouble', b.i2d((vs, 'SizeX'), 500, 400), None, 750, 400, db='0.015')
sy = b.d2('Multiply_DoubleDouble', b.i2d((vs, 'SizeY'), 500, 550), None, 750, 550, db='0.17')
def istr(src, x, y):
    n = b.name('IntStr'); callfn(G, n, KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], pure=True, x=x, y=y, self_hidden=True)
    b.wire(src, n, 'InInt'); return (n, 'ReturnValue')
s = b.concat(None, istr(b.get('Food', INT, 0, 900), 250, 900), 500, 750, da='FOOD   ')
s = b.concat(s, None, 750, 750, db='      FARMERS   ')
s = b.concat(s, istr(b.get('Farmers', INT, 750, 900), 1000, 900), 1250, 750)
dt = b.call_self('DrawText', [S('Text'), st('TextColor', LC, default='(R=0.950000,G=0.880000,B=0.760000,A=1.000000)'), fl('ScreenX'), fl('ScreenY'),
                               ob('Font', FONT), fl('Scale', default='1.400000'), bo('bScalePosition', default='false')], 1600, 0, HUDCLS, tag='DrawFood')
b.wire(s, dt, 'Text'); b.wire(sx, dt, 'ScreenX'); b.wire(sy, dt, 'ScreenY')
write('ZombieHUD_Food_graph.txt', G)
json.dump({'blueprint': 'BP_ZombieHUD', 'pastes': ['ZombieHUD_Food_graph.txt'], 'rewires': [
    {'from': 'orDrawOre32.then', 'to': dt + '.execute', 'replace': True, 'note': 'after #201 ORE line (was -> K2Node_IfThenElse_H296)'},
    {'from': dt + '.then', 'to': 'K2Node_IfThenElse_H296.execute', 'note': 'then the rest of the draw chain'}]},
    open(os.path.join(HERE, 'manifest_hud.json'), 'w'), indent=1)

# ================================================================ BP_Zombie: raid the farmers
# After the soldier search (ForEach CX_503 -> Completed) and before CX_1: drop a dead-farmer target back to the player, then
# a living farmer within RAID cm that is closer than the current target (Owner) becomes the target. Zombies walk to and
# ApplyDamage their Owner, so nothing else changes.
RAID = '2500.0'
G = Graph(); b = B(G, 'zf'); b.imp = B(G, 'zfQ')   # Q* = nodes fix_impure must splice
own = lambda x, y: (b.call_self('GetOwner', [ob('ReturnValue', ACT, out=True)], x, y, ACT, pure=True, const=True, tag='Owner'), 'ReturnValue')
cf = 'zfAsFarmerTarget'; cast(G, cf, FARMERC, 'AsBP Farmer', 0, 0); b.wire(own(-250, 150), cf, 'Object')
bdead = b.branch(b.getm('Dead', FARMERC, BOOL, (cf, 'AsBP Farmer'), 300, 250), 350, 0, 'IfTargetDead'); G.link(cf, 'then', bdead, 'execute')
pl = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], 600, 250, pure=True, tag='Player')
so = b.call_self('SetOwner', [ob('NewOwner', ACT)], 650, 0, ACT, tag='BackToPlayer'); b.wire((pl, 'ReturnValue'), so, 'NewOwner'); G.link(bdead, 'then', so, 'execute')
ga, fe, f = all_of(b, P_FARMER, FARMERC, 1000, 0)
G.link(so, 'then', ga, 'execute'); G.link(bdead, 'else', ga, 'execute'); G.link(cf, 'CastFailed', ga, 'execute')
d = dist_to(b, f, 1300, 450, tag='DistFarmer')
dcur = b.call_self('GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 1300, 700, ACT, pure=True, const=True, tag='DistTarget')
b.wire(own(1100, 750), dcur, 'OtherActor')
ok = b.b2('BooleanAND', b.b2('BooleanAND', b.bnot(b.getm('Dead', FARMERC, BOOL, f, 1300, 300), 1500, 300), b.dcmp('Less_DoubleDouble', d, None, 1500, 450, db=RAID), 1700, 350),
          b.dcmp('Less_DoubleDouble', d, (dcur, 'ReturnValue'), 1500, 650), 1900, 450)
bf = b.branch(ok, 1700, 100, 'IfRaidFarmer'); G.link(fe, 'LoopBody', bf, 'execute')
st_ = b.call_self('SetOwner', [ob('NewOwner', ACT)], 2000, 100, ACT, tag='TargetFarmer'); b.wire(f, st_, 'NewOwner'); G.link(bf, 'then', st_, 'execute')
write('Zombie_FarmRaid_graph.txt', G)
json.dump({'blueprint': 'BP_Zombie', 'pastes': ['Zombie_FarmRaid_graph.txt'], 'rewires': [
    {'from': 'CX_503.Completed', 'to': cf + '.execute', 'replace': True, 'note': 'after the soldier search (was -> CX_1)'},
    {'from': fe + '.Completed', 'to': 'CX_1.execute', 'note': 'back into the zombie chain'}]},
    open(os.path.join(HERE, 'manifest_zombie.json'), 'w'), indent=1)
print('manifests written')


# ================================================================ VARIABLES.md (BPVar paste lines for My Blueprint)
GC = lambda p: "/Script/Engine.BlueprintGeneratedClass'%s'" % cpath(p)
T_INT, T_BOOL, T_DBL = '(PinCategory="int")', '(PinCategory="bool")', '(PinCategory="real",PinSubCategory="double")'
VARS = [  # (blueprint, name, type, default, meaning)
    ('BP_FarmPlot', 'Kind', T_INT, '0', '0 wheat, 1 cabbage (set per placed plot)'),
    ('BP_FarmPlot', 'Stage', T_INT, '0', '0 bare, 1 sown, 2 growing, 3 ripe, 4 stubble'),
    ('BP_FarmPlot', 'Tended', T_BOOL, 'False', 'tended today (needed to grow)'),
    ('BP_FarmPlot', 'Claimed', T_BOOL, 'False', 'a farmer is on it'),
    ('BP_FarmPlot', 'LastYield', T_INT, '0', 'food from the last harvest (farmer reads it)'),
    ('BP_FarmPlot', 'Yield', T_INT, '16', 'food per harvest: 16 wheat, set 10 on cabbage plots'),
    ('BP_FarmPlot', 'PlotId', T_INT, '0', 'unique per placed plot (0, 1, 2...): the save slot index'),
    ('BP_FarmPlot', 'StageMeshes', '(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.StaticMesh\'",ContainerType=Array)', '', '10 meshes: Kind*5+Stage (setup script fills it)'),
    ('BP_Farmer', 'State', T_INT, '0', '0 idle, 1 to plot, 2 working, 3 to granary, 4 fleeing, 5 home'),
    ('BP_Farmer', 'Plot', '(PinCategory="object",PinSubCategoryObject="%s")' % GC(P_PLOT), '', 'the claimed plot'),
    ('BP_Farmer', 'Carry', T_INT, '0', 'food in the basket'),
    ('BP_Farmer', 'HP', T_DBL, '100.0', 'health'),
    ('BP_Farmer', 'Dead', T_BOOL, 'False', 'dead (zombies drop him as a target)'),
    ('BP_Farmer', 'Danger', T_BOOL, 'False', 'a zombie is within FleeRadius (scratch)'),
    ('BP_Farmer', 'WorkUntil', T_DBL, '0.0', 'game time the current job ends'),
    ('BP_Farmer', 'WorkSeconds', T_DBL, '6.0', 'seconds per job (sow / tend / harvest)'),
    ('BP_Farmer', 'FleeRadius', T_DBL, '2000.0', 'cm: a zombie this close sends him home'),
    ('BP_FarmDirector', 'Day', T_INT, '0', 'days passed (dusk -> dawn)'),
    ('BP_FarmDirector', 'WasNight', T_BOOL, 'False', 'last poll was night'),
    ('BP_FarmDirector', 'StartFarmers', T_INT, '3', 'farmers on a new game'),
    ('BP_FarmDirector', 'SpawnLeft', T_INT, '0', 'scratch: farmers to spawn'),
    ('BP_FarmDirector', 'Alive', T_INT, '0', 'living farmers'),
    ('BP_FarmDirector', 'SaveData', '(PinCategory="real",PinSubCategory="double",ContainerType=Array)', '', 'scratch: the save array'),
    ('BP_FarmerHire', 'Cost', T_INT, '60', 'gold per farmer (also in the banner text)'),
    ('BP_FarmerHire', 'MaxFarmers', T_INT, '12', 'cap'),
    ('BP_ZombieHUD', 'Food', T_INT, '0', 'the food stock (#227 eats it)'),
    ('BP_ZombieHUD', 'Farmers', T_INT, '0', 'living farmers (shown on the HUD)')]
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', encoding='utf-8') as fo:
    fo.write('# Variables for #223\n\nOn BP_FarmPlot make `Kind`, `Yield` and `PlotId` Instance Editable (eye open): they are set per placed plot.\n\n')
    fo.write('| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bpn, n, t, dflt, m in VARS: fo.write('| %s | %s | %s | %s |\n' % (bpn, n, dflt or '-', m))
    cur = None
    for k, (bpn, n, t, dflt, m) in enumerate(VARS):
        if bpn != cur:
            fo.write('%s\n### %s\n```\n' % ('```\n' if cur else '', bpn)); cur = bpn
        fo.write('BPVar(VarName="%s",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E%03X,VarType=%s,FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5%s)\n'
                 % (n, k, t, n, (',DefaultValue="%s"' % dflt) if dflt else ''))
    fo.write('```\n')
print('VARIABLES.md', len(VARS), 'vars')


# ================================================================ fix_impure on every graph (UE 5.3 pastes GetActorOfClass / save calls / casts as impure)
import subprocess
for gname, pfx in (('BP_FarmPlot', 'fpQ'), ('BP_Farmer', 'fmQ'), ('BP_FarmDirector', 'fdQ'), ('BP_FarmerHire', 'fhQ'), ('ZombieHUD_Food', 'hfQ'), ('Zombie_FarmRaid', 'zfQ')):
    p = os.path.join(HERE, gname + '_graph.txt')
    subprocess.run([sys.executable, os.path.join(HERE, '..', '..', 'tools', 'applyall', 'fix_impure.py'), p, p, pfx], check=True, capture_output=True)
print('fix_impure done')