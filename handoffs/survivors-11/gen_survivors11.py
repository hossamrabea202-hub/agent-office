# #11 Survivors (adjustedfilm, 2026-10-31): tired, injured soldiers sometimes arrive at the castle and ask to join the army;
# taken in, they heal at the barracks and then fight as normal soldiers. System only: the body is a stand-in (the soldier's
# skeletal mesh + anim class, copied by setup_survivors11_ue.py); the owner swaps in MetaHumans later.
#   "<blender python>" -I gen_survivors11.py  ->  BPC_Survivors_graph.txt, BP_Survivor_graph.txt, VARIABLES_BPVar.txt
#
# BPC_Survivors (hero component "Survivors"), SurvPoll every 3 s:
#   calm (no BP_Zombie alive) + fewer than MaxWaiting survivors around + MinGap s since the last one + game time > FirstDelay
#   + a Chance roll -> one BP_Survivor spawns ArriveDist outside the gate (navmesh point, random +-7 m along the wall),
#   and a notice "A wounded soldier is at the gate ...". "Outside" = away from the castle centre (CastleCentre, the
#   #41 castle box 0..4600 x 0..3450 -> 2300, 1725).
# BP_Survivor (Character), Think every 0.25 s, State:
#   0 limps to just inside the gate (walk 130, anim 0.7x)          label "Wounded soldier"
#   1 waits there; hero within 4 m + E -> taken in (if the army < MaxArmy), else "Army full"   label "[E] Take him into your army"
#   2 walks to the barracks NPC                                    label "Going to the barracks to heal"
#   3 rests HealSeconds (60), anim speeds back up                   label "Healing 63%"
#   -> a normal BP_SoldierSword spawns on his spot (exactly what the barracks recruit does), the survivor is removed.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP = CLS('ActorComponent')
P_SURV = '/Game/CastleDefender/Gameplay/Survivors/BP_Survivor'
P_ZOMBIE_ = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
P_GATE = '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl'
P_NPC = '/Game/CastleDefender/Gameplay/Castle/BP_NPC_Barracks'
P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
SURVC, ZOMBC = BPC(P_SURV, 'BP_Survivor'), BPC(P_ZOMBIE_, 'BP_Zombie')
GATEC, NPCC, NOTC = BPC(P_GATE, 'BP_CastleGateControl'), BPC(P_NPC, 'BP_NPC_Barracks'), BPC(P_NOTICE, 'BP_NoticeHUD')
TEXTR, PCM, HUDCLS = CLS('TextRenderComponent'), CLS('PlayerCameraManager'), CLS('HUD')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
OBJV = lambda c: ob('v', c)
TXT = lambda n, out=False: {'name': n, 'cat': 'text', 'out': out}


class B5(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def div(s, a, c, x, y, db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, db=db)
    def eqi(s, a, v, x, y): return s.icmp('EqualEqual_IntInt', a, None, x, y, db=str(v))
    def all_(s, vals, x, y):
        acc = vals[0]
        for i, v in enumerate(vals[1:]): acc = s.b2('BooleanAND', acc, v, x + 200 * i, y)
        return acc
    def getall(s, path, cls, x, y):
        """GetAllActorsOfClass (impure in 5.3: on the exec chain) -> node; length via count()."""
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def count(s, node, x, y):
        n = s.name('Count')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.G.link(node, 'OutActors', n, 'TargetArray'); return (n, 'ReturnValue')
    def actor_of_(s, path, cls, x, y):
        return s.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], x, y, tag='Find' + path.split('/')[-1][3:])
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc')
        return (n, 'ReturnValue')
    def myloc(s, x, y):
        n = s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc')
        return (n, 'ReturnValue')
    def vscale(s, v, f, x, y, df='1.0'):
        return s.math('Multiply_VectorFloat', [(V('A'), v), (D('B', default=df), f)], V('ReturnValue', out=True), x, y)
    def dist2d(s, a, c, x, y):
        return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def outward(s, gate, centre, x, y):
        """unit 2D vector from the castle centre to the gate (points outside)."""
        d = s.v2('Subtract_VectorVector', gate, centre, x, y)
        bv = s.brk(d, x + 220, y)
        flat = s.vec(bv['X'], bv['Y'], None, x + 440, y)
        n = s.math('Normal', [(V('A'), flat), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), x + 660, y)
        return n
    def notice(s, text, x, y):
        """the player's HUD -> cast BP_NoticeHUD -> PushNotice(text, tier 1); returns (cast node, notice node)."""
        pcn = s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x - 300, y + 300, pure=True, tag='PC')
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x - 100, y + 300, target=(pcn, 'ReturnValue'), pure=True, const=True, tag='HUD')
        nc = s.name('AsNoticeHUD'); cast(s.G, nc, NOTC, 'AsBP Notice HUD', x, y); s.wire((hud, 'ReturnValue'), nc, 'Object')
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x + 300, y, target=(nc, 'AsBP Notice HUD'), tag='Notice')
        s.G.link(nc, 'then', pn, 'execute')
        return nc, pn
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.300000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def setd(s, var, val, x, y, dv='0.0'):
        n = s.set(var, D('v', default=dv), val, x, y); return n
    def seti(s, var, v, x, y):
        n = s.set(var, it('v', default=str(v)), None, x, y); return n


def begin_play(G, cls, x=0, y=0):
    G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % cls, 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % cls}, ex('then', True)], x, y)
    return 'BP'


def check_and_write(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    if bad: raise SystemExit('%s bad links: %s' % (name, bad[:10]))
    names = [n[0] for n in G.nodes]
    dup = {n for n in names if names.count(n) > 1}
    if dup: raise SystemExit('%s duplicate names: %s' % (name, sorted(dup)[:10]))
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render())
    print('%s: nodes %d, links %d' % (name, len(G.nodes), len(G.links)))


# ================================================================================================= BPC_Survivors
G = Graph(); b = B5(G, 'sv')
g = b.get
begin_play(G, COMP)
t = b.timer_ev('SurvPoll', '3.0', 300, 0); G.link('BP', 'then', t, 'execute')

Y = 600
b.event('SurvPoll', [], 0, Y)
now = b.now(200, Y + 900)
gz = b.getall(P_ZOMBIE_, ZOMBC, 300, Y); G.link('SurvPoll', 'then', gz, 'execute')
gs_ = b.getall(P_SURV, SURVC, 650, Y); G.link(gz, 'then', gs_, 'execute')
cond = b.all_([b.eqi(b.count(gz, 500, Y + 300), 0, 700, Y + 300),
               b.icmp('Less_IntInt', b.count(gs_, 850, Y + 400), g('MaxWaiting', it('v', default='2'), 850, Y + 500), 1050, Y + 400),
               b.dcmp('Greater_DoubleDouble', b.sub(now, g('LastArrival', DBL, 450, Y + 650), 650, Y + 650), g('MinGap', DBL, 650, Y + 750), 850, Y + 650),
               b.dcmp('Greater_DoubleDouble', now, g('FirstDelay', DBL, 450, Y + 850), 850, Y + 850),
               b.dcmp('Less_DoubleDouble', b.rnd('0.0', '1.0', 650, Y + 950), g('Chance', DBL, 650, Y + 1050), 850, Y + 950)], 1150, Y + 600)
br = b.branch(cond, 1000, Y, tag='IfArrive'); G.link(gs_, 'then', br, 'execute')
fg = b.actor_of_(P_GATE, GATEC, 1300, Y); G.link(br, 'then', fg, 'execute')
gate = (fg, 'ReturnValue')
bv = b.branch(b.valid(gate, 1500, Y + 250), 1650, Y, tag='IfGate'); G.link(fg, 'then', bv, 'execute')
gl = b.loc(gate, 1500, Y + 400)
out = b.outward(gl, g('CastleCentre', V('v'), 1500, Y + 550), 1700, Y + 450)
ob_ = b.brk(out, 2500, Y + 450)
perp = b.vec(b.mul(ob_['Y'], None, 2700, Y + 450, db='-1.0'), ob_['X'], None, 2900, Y + 450)
origin = b.v2('Add_VectorVector', b.v2('Add_VectorVector', gl, b.vscale(out, g('ArriveDist', DBL, 2700, Y + 650), 2900, Y + 600), 3100, Y + 550),
              b.vscale(perp, b.rnd('-700.0', '700.0', 2900, Y + 800), 3100, Y + 750), 3300, Y + 650)
nav = b.lib(NAVSYS, 'K2_GetRandomReachablePointInRadius', [WC(), dict(V('Origin'), ref=True), V('RandomLocation', out=True),
            fl('Radius', default='500.000000'), ob('NavData', NAVDATA), {'name': 'FilterClass', 'cat': 'class', 'obj': NAVFILT}, bo('ReturnValue', out=True, default='false')],
            3500, Y + 650, pure=True, tag='NavPoint')
b.wire(origin, nav, 'Origin')
pos = b.selvec(b.v2('Add_VectorVector', (nav, 'RandomLocation'), None, 3800, Y + 600, db='0.000000,0.000000,100.000000'),
               b.v2('Add_VectorVector', origin, None, 3800, Y + 750, db='0.000000,0.000000,100.000000'), (nav, 'ReturnValue'), 4000, Y + 650)
look = b.math('FindLookAtRotation', [(V('Start'), pos), (V('Target'), gl)], st('ReturnValue', ROT, out=True), 4200, Y + 750)
xf = b.math('MakeTransform', [(V('Location'), pos), (st('Rotation', ROT, default='0, 0, 0'), look), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
            st('ReturnValue', XFORM, out=True), 4400, Y + 650)
sp = spawn(b, P_SURV, SURVC, xf, 2000, Y); G.link(bv, 'then', sp, 'execute')
sl = b.setd('LastArrival', now, 2350, Y); G.link(sp, 'then', sl, 'execute')
nc, pn = b.notice('A wounded soldier is at the gate. He asks to join your army.', 2700, Y)
G.link(sl, 'then', nc, 'execute')
check_and_write(G, 'BPC_Survivors_graph.txt')
VARS_C = [('LastArrival', 'real', '-1000.0', 'game time of the last arrival'), ('MinGap', 'real', '150.0', 's between two arrivals'),
          ('Chance', 'real', '0.12', 'chance per 3 s poll once the gap is over (about one every 3-4 min when calm)'),
          ('FirstDelay', 'real', '120.0', 'no survivor in the first 2 minutes of a game'),
          ('MaxWaiting', 'int', '2', 'at most this many survivors around at once'), ('ArriveDist', 'real', '3000.0', 'cm outside the gate'),
          ('CastleCentre', 'vector', '2300.000000,1725.000000,0.000000', 'centre of the #41 castle box; outside = away from it')]

# ================================================================================================= BP_Survivor
G = Graph(); b = B5(G, 'su')
g = b.get
SELFC = SURVC
begin_play(G, ACT)
selfh = lambda x, y: b.self_node(x, y)
mesh = lambda x, y: b.getm('Mesh', CHARC, OBJV(SKEL), selfh(x - 200, y), x, y)
cmc = lambda x, y: b.getm('CharacterMovement', CHARC, OBJV(CMC), selfh(x - 200, y), x, y)
a1 = b.setm('GlobalAnimRateScale', SKEL, fl('v', default='0.7'), None, mesh(200, 300), 300, 0)
a2 = b.setm('MaxWalkSpeed', CMC, fl('v', default='130.0'), None, cmc(500, 300), 600, 0)
G.link('BP', 'then', a1, 'execute'); G.link(a1, 'then', a2, 'execute')
lab = b.call_self('GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.TextRenderComponent'), NAME_('Tag', 'SurvLabel'),
                  arr(ob('ReturnValue', TEXTR, out=True))], 700, 300, ACT, pure=True, const=True, tag='FindLabel')
itn = b.name('Item'); G.node(itn, 'K2Node_GetArrayItem', [], [arr(ob('Array', TEXTR)), it('Dimension 1', default='0'), ob('Output', TEXTR, out=True)], 950, 300)
G.link(lab, 'ReturnValue', itn, 'Array')
s_lab = b.set('Label', OBJV(TEXTR), (itn, 'Output'), 900, 0); G.link(a2, 'then', s_lab, 'execute')
fg = b.actor_of_(P_GATE, GATEC, 1200, 0); G.link(s_lab, 'then', fg, 'execute')
gate = (fg, 'ReturnValue')
bg_ = b.branch(b.valid(gate, 1400, 300), 1500, 0, tag='IfGate'); G.link(fg, 'then', bg_, 'execute')
gl = b.loc(gate, 1400, 450)
out = b.outward(gl, g('CastleCentre', V('v'), 1400, 600), 1600, 500)
inside = b.v2('Subtract_VectorVector', gl, b.vscale(out, None, 2400, 500, df='700.0'), 2600, 450)
s_in = b.set('Inside', V('v'), inside, 1800, 0); G.link(bg_, 'then', s_in, 'execute')
mg = b.seq('AfterGate', 1, 2100, 0); G.link(bg_, 'else', mg, 'execute'); G.link(s_in, 'then', mg, 'execute')
fn = b.actor_of_(P_NPC, NPCC, 2400, 0); G.link(mg, 'then_0', fn, 'execute')
npc = (fn, 'ReturnValue')
bn = b.branch(b.valid(npc, 2600, 300), 2700, 0, tag='IfNPC'); G.link(fn, 'then', bn, 'execute')
heal = b.v2('Add_VectorVector', b.loc(npc, 2600, 450), b.vec(b.rnd('-220.0', '220.0', 2600, 600), b.rnd('-220.0', '220.0', 2600, 700), None, 2800, 600), 3000, 500)
s_h = b.set('HealSpot', V('v'), heal, 3000, 0); G.link(bn, 'then', s_h, 'execute')
mg2 = b.seq('AfterNPC', 1, 3300, 0); G.link(bn, 'else', mg2, 'execute'); G.link(s_h, 'then', mg2, 'execute')
st0 = b.seti('State', 0, 3600, 0); G.link(mg2, 'then_0', st0, 'execute')
tt = b.timer_ev('Think', '0.25', 3900, 0); G.link(st0, 'then', tt, 'execute')

# ---- Think
Y = 1200
b.event('Think', [], 0, Y)
seq = b.seq('ThinkSeq', 3, 200, Y); G.link('Think', 'then', seq, 'execute')
now = b.now(200, Y + 1600)
state = lambda x, y: g('State', it('v', default='0'), x, y)
label = lambda x, y: g('Label', OBJV(TEXTR), x, y)
hero = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 200, Y + 1800, pure=True, tag='Hero')
heroh = (hero, 'ReturnValue')
near = b.b2('BooleanAND', b.valid(heroh, 400, Y + 1900),
            b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(400, Y + 2000), b.loc(heroh, 400, Y + 2100), 600, Y + 2000), None, 800, Y + 2000, db='400.0'), 1000, Y + 1950)
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 200, Y + 2300, PAWN, pure=True, const=True, tag='Ctl')
ctlh = (ctl, 'ReturnValue')
def move(goal, x, y):
    mv = b.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], x, y, tag='Move')
    b.wire(ctlh, mv, 'Controller'); b.wire(goal, mv, 'Goal'); return mv
def idle_then_move(prev, prev_pin, goal, after, x, y, tag):
    """re-issue the move only while he stands still (start, or stuck), so the path is not restarted 4x a second."""
    vel = b.call_self('GetVelocity', [V('ReturnValue', out=True)], x, y + 250, ACT, pure=True, const=True, tag='Vel')
    spd = b.math('VSizeXY', [(V('A'), (vel, 'ReturnValue'))], D('ReturnValue', out=True), x + 200, y + 250)
    bi = b.branch(b.dcmp('Less_DoubleDouble', spd, None, x + 400, y + 250, db='20.0'), x + 200, y, tag=tag)
    G.link(prev, prev_pin, bi, 'execute')
    mv = move(goal, x + 500, y - 150); G.link(bi, 'then', mv, 'execute')
    G.link(mv, 'then', after, 'execute'); G.link(bi, 'else', after, 'execute')
def stop(x, y):
    n = b.call(CTRL, 'StopMovement', [], x, y, target=ctlh, tag='Stop'); return n

# then_0: face the label to the camera
lv = b.branch(b.valid(label(300, Y - 200), 500, Y - 200), 500, Y - 400, tag='IfLabel'); G.link(seq, 'then_0', lv, 'execute')
cm = b.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCM, out=True)], 500, Y - 100, pure=True, tag='Cam')
cl = b.call(PCM, 'GetCameraLocation', [V('ReturnValue', out=True)], 700, Y - 100, target=(cm, 'ReturnValue'), pure=True, const=True, tag='CamLoc')
lw = b.call(SCENE, 'K2_GetComponentLocation', [V('ReturnValue', out=True)], 700, Y - 250, target=label(500, Y - 250), pure=True, const=True, tag='LabelLoc')
la = b.math('FindLookAtRotation', [(V('Start'), (lw, 'ReturnValue')), (V('Target'), (cl, 'ReturnValue'))], st('ReturnValue', ROT, out=True), 950, Y - 200)
lb = b.math('BreakRotator', [(st('InRot', ROT, default='0, 0, 0'), la)] + [], fl('Yaw', out=True, default='0.0'), 1150, Y - 200)
G.nodes[-1][3].insert(1, fl('Roll', out=True, default='0.0')); G.nodes[-1][3].insert(2, fl('Pitch', out=True, default='0.0'))
lr = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='0.0'), None), (fl('Yaw', default='0.0'), lb)], st('ReturnValue', ROT, out=True), 1350, Y - 200)
sr = b.call(SCENE, 'K2_SetWorldRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
            bo('bTeleport', default='true')], 1550, Y - 400, target=label(1350, Y - 350), tag='FaceCam')
b.wire(lr, sr, 'NewRotation'); G.link(lv, 'then', sr, 'execute')

# then_1: the state machine
X = 400
b0 = b.branch(b.eqi(state(X, Y + 200), 0, X + 200, Y + 200), X + 300, Y, tag='IfS0'); G.link(seq, 'then_1', b0, 'execute')
ins = lambda x, y: g('Inside', V('v'), x, y)
arr0 = b.branch(b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 700, Y - 50), ins(X + 700, Y + 50), X + 900, Y - 50), None, X + 1100, Y - 50, db='250.0'),
                X + 1300, Y - 300, tag='IfInside')
idle_then_move(b0, 'then', ins(X + 500, Y - 150), arr0, X + 400, Y - 300, 'IfStill0')
s1 = b.seti('State', 1, X + 1200, Y - 300); G.link(arr0, 'then', s1, 'execute')
X = 1800
b1 = b.branch(b.eqi(state(X, Y + 200), 1, X + 200, Y + 200), X + 300, Y, tag='IfS1'); G.link(b0, 'else', b1, 'execute')
pcn = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], X + 300, Y + 400, pure=True, tag='PC')
ek = b.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default='E'), bo('ReturnValue', out=True, default='false')], X + 500, Y + 400,
            target=(pcn, 'ReturnValue'), pure=True, const=True, tag='KeyE')
ba = b.branch(b.b2('BooleanAND', near, (ek, 'ReturnValue'), X + 700, Y + 350), X + 600, Y, tag='IfTakeIn'); G.link(b1, 'then', ba, 'execute')
ga = b.getall(P_SOLDIER, SOLDIER, X + 900, Y); G.link(ba, 'then', ga, 'execute')
room = b.icmp('Less_IntInt', b.count(ga, X + 1100, Y + 300), g('MaxArmy', it('v', default='30'), X + 1100, Y + 400), X + 1300, Y + 350)
bf = b.branch(room, X + 1250, Y, tag='IfRoom'); G.link(ga, 'then', bf, 'execute')
s2 = b.seti('State', 2, X + 1550, Y - 200); G.link(bf, 'then', s2, 'execute')
nc, pn = b.notice('He thanks you and limps to the barracks to heal.', X + 1850, Y - 200); G.link(s2, 'then', nc, 'execute')
sfu = b.setd('FullUntil', b.add(now, None, X + 1500, Y + 250, db='3.0'), X + 1550, Y + 100); G.link(bf, 'else', sfu, 'execute')
X = 4200
b2_ = b.branch(b.eqi(state(X, Y + 200), 2, X + 200, Y + 200), X + 300, Y, tag='IfS2'); G.link(b1, 'else', b2_, 'execute')
hs = lambda x, y: g('HealSpot', V('v'), x, y)
arr2 = b.branch(b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 700, Y - 50), hs(X + 700, Y + 50), X + 900, Y - 50), None, X + 1100, Y - 50, db='200.0'),
                X + 1300, Y - 300, tag='IfAtBarracks')
idle_then_move(b2_, 'then', hs(X + 500, Y - 150), arr2, X + 400, Y - 300, 'IfStill2')
s3 = b.seti('State', 3, X + 1200, Y - 300); sh0 = b.setd('HealT0', now, X + 1450, Y - 300); stp = stop(X + 1700, Y - 300)
G.link(arr2, 'then', s3, 'execute'); b.chain(s3, sh0, stp)
X = 6300
b3 = b.branch(b.eqi(state(X, Y + 200), 3, X + 200, Y + 200), X + 300, Y, tag='IfS3'); G.link(b2_, 'else', b3, 'execute')
pct = b.clamp(b.div(b.sub(now, g('HealT0', DBL, X + 300, Y + 500), X + 500, Y + 450), g('HealSeconds', DBL, X + 500, Y + 600), X + 700, Y + 500), '0.0', '1.0', X + 900, Y + 500)
ar = b.setm('GlobalAnimRateScale', SKEL, fl('v', default='0.7'), b.math('Lerp', [(D('A', default='0.7'), None), (D('B', default='1.0'), None), (D('Alpha', default='0.0'), pct)],
            D('ReturnValue', out=True), X + 1100, Y + 500), mesh(X + 500, Y + 300), X + 600, Y)
G.link(b3, 'then', ar, 'execute')
bd = b.branch(b.dcmp('GreaterEqual_DoubleDouble', pct, None, X + 1100, Y + 650, db='1.0'), X + 900, Y, tag='IfHealed'); G.link(ar, 'then', bd, 'execute')
xf = b.call_self('GetActorTransform', [st('ReturnValue', XFORM, out=True)], X + 1100, Y + 300, ACT, pure=True, const=True, tag='MyXform')
sps = spawn(b, P_SOLDIER, SOLDIER, (xf, 'ReturnValue'), X + 1300, Y); G.link(bd, 'then', sps, 'execute')
nc2, pn2 = b.notice('A survivor has healed and joined your soldiers.', X + 1700, Y); G.link(sps, 'then', nc2, 'execute')
ds = b.call_self('K2_DestroyActor', [], X + 2300, Y, ACT, tag='Destroy'); G.link(pn2, 'then', ds, 'execute')
G.link(nc2, 'CastFailed', ds, 'execute')

# then_2: label text
X = 400; YL = Y + 2600
st_ = state(X, YL + 200)
pcti = b.math('Round', [(D('A', default='0.0'), b.mul(pct, None, X + 200, YL + 300, db='100.0'))], it('ReturnValue', out=True), X + 400, YL + 300)
ps = b.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], X + 600, YL + 300, pure=True, tag='PctStr')
b.wire(pcti, ps, 'InInt')
heal_s = b.concat(b.concat(None, (ps, 'ReturnValue'), X + 800, YL + 300, da='Healing  '), None, X + 1000, YL + 300, db='%')
full = b.dcmp('Greater_DoubleDouble', g('FullUntil', DBL, X + 600, YL + 500), now, X + 800, YL + 500)
s1near = b.selstr(None, None, full, X + 1000, YL + 550, da='Your army is full - make room first', db='[E]  Take him into your army')
s1s = b.selstr(s1near, None, near, X + 1200, YL + 600, db='Wounded soldier  -  wants to join your army')
txt = b.selstr(heal_s, b.selstr(None, b.selstr(s1s, None, b.eqi(st_, 1, X + 1200, YL + 800), X + 1400, YL + 750, db='Wounded soldier'),
               b.eqi(st_, 2, X + 1400, YL + 900), X + 1600, YL + 850, da='Going to the barracks to heal'), b.eqi(st_, 3, X + 1600, YL + 1000), X + 1800, YL + 900)
lv2 = b.branch(b.valid(label(X + 1800, YL - 100), X + 2000, YL - 100), X + 1900, YL - 300, tag='IfLabel2'); G.link(seq, 'then_2', lv2, 'execute')
stt = b.call(TEXTR, 'K2_SetText', [TXT('Value')], X + 2300, YL - 300, target=label(X + 2100, YL - 200), tag='SetLabel')
b.wire(b.text(txt, X + 2100, YL + 900), stt, 'Value'); G.link(lv2, 'then', stt, 'execute')
check_and_write(G, 'BP_Survivor_graph.txt')
VARS_S = [('State', 'int', '0', '0 to the gate, 1 waiting, 2 to the barracks, 3 healing'), ('Inside', 'vector', '0,0,0', 'just inside the gate'),
          ('HealSpot', 'vector', '0,0,0', 'next to the barracks NPC'), ('HealT0', 'real', '0.0', 'game time healing started'),
          ('HealSeconds', 'real', '60.0', 'seconds to heal'), ('FullUntil', 'real', '0.0', 'shows "army full" until this time'),
          ('MaxArmy', 'int', '30', 'no take-in when the army (all BP_SoldierSword incl. crossbow / commanders) is this big'),
          ('CastleCentre', 'vector', '2300.000000,1725.000000,0.000000', 'same as BPC_Survivors'),
          ('Label', 'obj:TextRenderComponent', '', 'the floating line over his head')]


# ================================================================================================= BPVar lines
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind == 'int': return 'PinCategory="int"'
    if kind == 'vector': return 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
def bpvar(bp, name, kind, default):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
        name, uuid.uuid5(uuid.NAMESPACE_URL, 'survivors11/%s/%s' % (bp, name)).hex.upper(), vt(kind), name, default)
out = ['# #11 Survivors - paste one line at a time on the VARIABLES header of My Blueprint, then Compile', '', '# ---- BPC_Survivors']
out += [bpvar('BPC_Survivors', n, k, d) for n, k, d, _ in VARS_C]
out += ['', '# ---- BP_Survivor'] + [bpvar('BP_Survivor', n, k, d) for n, k, d, _ in VARS_S]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #11 Survivors: variables (the BPVar lines are in VARIABLES_BPVar.txt)\n\n| Blueprint | Name | Type | Default | Meaning |\n|---|---|---|---|---|\n')
    for bp, vs in (('BPC_Survivors', VARS_C), ('BP_Survivor', VARS_S)):
        for n, k, d, m in vs: f.write('| %s | %s | %s | %s | %s |\n' % (bp, n, k.replace('obj:', ''), d or '-', m))
print('BPVar lines: %d + %d' % (len(VARS_C), len(VARS_S)))
