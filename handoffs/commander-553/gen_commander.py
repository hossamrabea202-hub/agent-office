# Commander card (#553): the EventGraph of the NEW hero component BPC_CommanderCard.
#   python gen_commander.py -> handoffs/commander-553/build/BPC_CommanderCard_graph.txt + card_data.json
# Same kit as The Muster (tools/tga/vesna/gen_trade.py helpers, run from its source). DrawCommander(Hud, SizeX, SizeY) is called
# every frame from the HUD (one line in C++, see CPP_SPEC.md) and does three jobs:
#   1. COMMANDER WINDOW: E near a commander opens it (game paused, cursor on). Motion-graphics stroke (M_CC_Stroke), name, age,
#      stats, aura, troops + ranks, squad size, gather mix page, orders, attack-confirm page.
#   2. GATE KEEPER: guards open the closed gate when the hero comes back from outside, and close it behind him. Otherwise a
#      closed gate fades in "Use your keys to open the gate - press E", and E opens it (BP_CastleGateControl.SetGateOpen).
#   3. TENTACLE ATTACK: 1 Hz strikes while a squad is ordered onto a tentacle (soldiers only ever target BP_Zombie by themselves).
# Soldier channels are the same ones the old wheel writes: Order.X = code, Goal = world point, State.X = HP, Rank.X/Y = XP/level.
#   Codes: 0 post, 1 follow, 3 crew cannon, 4 wall, 5 hold at Goal, 6 attack outside, 7 defend gate.
# "Defend the castle" here is the plain Blueprint version (crossbows to the wall, swords inside the gate, gate shuts after 10 s) and
# tags the commander CD_DefendCastle; the C++ brain in CPP_SPEC.md takes over from that tag.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
VESNA = os.path.join(REPO, 'tools', 'tga', 'vesna')
SRC = open(os.path.join(VESNA, 'gen_trade.py'), encoding='utf-8').read().split('\n')
def chunk(a, b_): return '\n'.join(SRC[a - 1:b_])
def find(prefix, start=1):
    for i, l in enumerate(SRC[start - 1:], start):
        if l.startswith(prefix): return i
    raise SystemExit('gen_trade.py changed: ' + prefix)
L_EV, L_GEO, L_DRAW, L_STATE = find('# ---------------------------------------------------------------- event + scale'), find('# geometry:'), \
    find('# ---------------------------------------------------------------- draw helpers'), find('# ---------------------------------------------------------------- shared state reads')
_here = HERE
HERE = VESNA                                                 # gen_trade reads layout.json next to itself
__file__ = os.path.join(VESNA, 'gen_trade.py')
exec(chunk(1, L_EV - 1))                                     # imports, constants, value helpers, Flow
HERE = _here
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
SC0 = 1.0                                                    # target px = 1920 x 1080 space
CARD = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_CommanderCard', 'BPC_CommanderCard')
P_GATE = '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl'
GATEC = BPC(P_GATE, 'BP_CastleGateControl')
P_VIT = '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals'
VITC = BPC(P_VIT, 'BP_TentacleVitals')
CMDC = BPC(P_CMDR, 'BP_SoldierCommander')
STRV, ACTV, NAMEV = S('v'), ob('v', ACT), N('v')
GATE_X, GATE_Y = -110.0, 1750.0                              # BP_CastleGateControl P_Vis / R_Branch use this point; outside is X < gate
OPEN_RANGE, NOTICE_RANGE, TALK_RANGE, SOLDIER_E = 1500.0, 450.0, 300.0, 200.0
PANEL, PANEL2, HOVER, LINE, LINEHOT = col(.05, .045, .04, .55), col(.04, .035, .03, .96), col(.30, .22, .10, .85), col(.62, .50, .28, .55), col(.97, .82, .50, 1)
DIMSCR = col(0, 0, 0, .62)

b.event('DrawCommander', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, 0)
hud = ('DrawCommander', 'Hud')
exec(chunk(L_GEO, L_DRAW - 1).replace("'DrawTrade'", "'DrawCommander'"))
exec(chunk(L_DRAW, L_STATE - 1).replace("cls=TRADEC", "cls=CARD"))
fl0 = Flow(('DrawCommander', 'then'))
PRESS = AND(key('LeftMouseButton', down=True), NOT(get('PrevDown', BOOL)))
ownn = b.name('Owner'); callfn(G, ownn, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=P()[0], y=P()[1], self_hidden=True); OWNER = (ownn, 'ReturnValue')

# ---------------------------------------------------------------- small value helpers
def alen(src):
    n = b.name('Len'); G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                              [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], *P())
    b.wire(src, n, 'TargetArray'); return (n, 'ReturnValue')
def array_call(fl_, member, arrsrc, itempin, item, extra=()):
    n = b.name(member)
    G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="%s")' % (KARR, member)],
           [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
            dict({'name': itempin, 'cat': 'wildcard', 'ref': True}, default=item if isinstance(item, str) else None)] + list(extra), *P())
    b.wire(arrsrc, n, 'TargetArray')
    if not isinstance(item, str): b.wire(item, n, itempin)
    fl_.go(n); return n
def add_to(fl_, arrvar, item): return array_call(fl_, 'Array_Add', get(arrvar, arr(ACTV)), 'NewItem', item, [it('ReturnValue', out=True, default='0')])
def remove_from(fl_, arrvar, item): return array_call(fl_, 'Array_RemoveItem', get(arrvar, arr(ACTV)), 'Item', item, [bo('ReturnValue', out=True, default='false')])
def clear(fl_, arrvar):
    n = b.name('Clear' + arrvar)
    G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
           [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], *P())
    b.wire(get(arrvar, arr(ACTV)), n, 'TargetArray'); fl_.go(n); return n
def tags_of(actor): return b.getm('Tags', ACT, arr(NAMEV), actor, *P())
def add_tag(fl_, actor, tag): return array_call(fl_, 'Array_AddUnique', tags_of(actor), 'NewItem', tag, [it('ReturnValue', out=True, default='0')])
def del_tag(fl_, actor, tag): return array_call(fl_, 'Array_RemoveItem', tags_of(actor), 'Item', tag, [bo('ReturnValue', out=True, default='false')])
def hastag(actor, tag):
    n = b.call(ACT, 'ActorHasTag', [N('Tag', default=tag if isinstance(tag, str) else None), bo('ReturnValue', out=True, default='false')], *P(), target=actor, pure=True, const=True, tag='HasTag')
    if not isinstance(tag, str): b.wire(tag, n, 'Tag')
    return (n, 'ReturnValue')
def asold(actor):
    n = b.name('AsSold'); cast(G, n, SOLDIER, 'AsBP Soldier Sword', *P(), pure=True); b.wire(actor, n, 'Object'); return (n, 'AsBP Soldier Sword')
def comp(sold, name): return b.getm(name, SOLDIER, ob('v', SCENE), sold, *P())
def chan(sold, name): return b.brk(b.relloc(comp(sold, name), *P()), *P())
def write_chan(fl_, sold, name, vec_):
    n = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
               *P(), target=comp(sold, name), tag='Set' + name)
    b.wire(vec_, n, 'NewLocation'); fl_.go(n); return n
def vecf(x_, y_, z_):
    return b.vec(None if isnum(x_) else x_, None if isnum(y_) else y_, None if isnum(z_) else z_, *P(), dx=str(float(x_)) if isnum(x_) else '0.0',
                 dy=str(float(y_)) if isnum(y_) else '0.0', dz=str(float(z_)) if isnum(z_) else '0.0')
def actor_loc(actor):
    n = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], *P(), target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
def nearest(origin, arrsrc):
    n = b.lib(GS, 'FindNearestActor', [V('Origin'), arr(ob('ActorsToCheck', ACT)), D('Distance', out=True, default='0.0'), ob('ReturnValue', ACT, out=True)], *P(), pure=True, tag='Nearest')
    b.wire(origin, n, 'Origin'); b.wire(arrsrc, n, 'ActorsToCheck'); return (n, 'ReturnValue'), (n, 'Distance')
def dist2d(a, x_, y_):
    n = b.math('Vector_Distance2D', [(V('V1'), a), (V('V2', default='%f,%f,0.0' % (x_, y_)), None)], D('ReturnValue', out=True), *P()); return n
def lifespan_ok(actor):
    n = b.call(ACT, 'GetLifeSpan', [D('ReturnValue', out=True)], *P(), target=actor, pure=True, const=True, tag='Life'); return dcmp('Less_DoubleDouble', (n, 'ReturnValue'), 0.01)
def findall(fl_, path, tag):
    n = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', ACT, out=True))], *P(), tag='Find' + tag); fl_.go(n); return (n, 'OutActors')
def rgba(r, g_, b_, a):
    return b.math('MakeColor', [(fl('R', default=repr(float(r))), None), (fl('G', default=repr(float(g_))), None), (fl('B', default=repr(float(b_))), None), (fl('A', default='1.0'), a)], st('ReturnValue', LC, out=True), *P())
def msg(fl_, s):
    setvar(fl_, 'Msg', STRV, None if isinstance(s, str) else s, lit=s if isinstance(s, str) else None); setvar(fl_, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 5.0))
def call(fl_, ev, pins=()): return selfcall(fl_, ev, pins, cls=CARD)
def call_with(fl_, ev, pins, wires=()):
    n = call(fl_, ev, pins)
    for pin, src in wires: b.wire(src, n, pin)
    return n
def set_gate(fl_, want):
    v, _ = (get('Gate', ob('v', GATEC)), None)
    f1, f2 = fl_.iff(b.valid(v, *P()), 'IfGate')
    n = b.call(GATEC, 'CmdGateOpen' if want else 'CmdGateClose', [], *P(), target=get('Gate', ob('v', GATEC)), tag='SetGate'); f1.go(n)
    return f1.join(f2)
GATEV = lambda: get('Gate', ob('v', GATEC))
CMD = lambda: get('Cmd', ACTV)

# ---------------------------------------------------------------- once: gate + wave manager; 2x a second: commanders + nearest soldier
f1, f2 = fl0.iff(NOT(b.valid(GATEV(), *P())), 'IfNoGate')
gfind = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_GATE)), ob('ReturnValue', GATEC, out=True)], *P(), tag='FindGate'); f1.go(gfind)
setvar(f1, 'Gate', ob('v', GATEC), (gfind, 'ReturnValue'))
wfind = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_WM)), ob('ReturnValue', WM, out=True)], *P(), tag='FindWM'); f1.go(wfind)
setvar(f1, 'WMgr', ob('v', WM), (wfind, 'ReturnValue'))
fl0 = f1.join(f2)
HEROLOC = actor_loc(OWNER)
f1, f2 = fl0.iff(dcmp('Greater_DoubleDouble', NOW, get('NextScan', DBL)), 'IfScan')
setvar(f1, 'NextScan', DBL, dop('Add_DoubleDouble', NOW, 0.5))
cs = b.lib(GS, 'GetAllActorsWithTag', [WC(), N('Tag', default='Commander'), arr(ob('OutActors', ACT, out=True))], *P(), tag='FindCmds'); f1.go(cs)
setvar(f1, 'Cmds', arr(ACTV), (cs, 'OutActors'))
ss = findall(f1, P_SOLDIER, 'Soldiers')
setvar(f1, 'AllSold', arr(ACTV), ss)
sn, sd = nearest(HEROLOC, get('AllSold', arr(ACTV)))
setvar(f1, 'SoldNear', BOOL, dcmp('Less_DoubleDouble', sd, SOLDIER_E))
setvar(f1, 'AnyGuard', BOOL, icmp('Greater_IntInt', alen(get('AllSold', arr(ACTV))), 0))
cn, cd = nearest(HEROLOC, get('Cmds', arr(ACTV)))
setvar(f1, 'NearCmd', ACTV, cn)
setvar(f1, 'NearCmdDist', DBL, cd)
fl0 = f1.join(f2)
TALKABLE = AND(AND(b.valid(get('NearCmd', ACTV), *P()), dcmp('Less_DoubleDouble', get('NearCmdDist', DBL), TALK_RANGE)), AND(icmp('Greater_IntInt', alen(get('Cmds', arr(ACTV))), 0), lifespan_ok(get('NearCmd', ACTV))))
setvar(fl0, 'NearCommander', BOOL, TALKABLE)

# ---------------------------------------------------------------- jobs that run with or without the window
fl0 = Flow(*fl0.c)
# tentacle strikes 1 Hz, delayed gate close after Defend
f1, f2 = fl0.iff(AND(b.valid(get('AttackV', ACTV), *P()), dcmp('Greater_DoubleDouble', NOW, get('NextStrike', DBL))), 'IfStrike')
setvar(f1, 'NextStrike', DBL, dop('Add_DoubleDouble', NOW, 1.0)); call(f1, 'TentacleTick')
fl0 = f1.join(f2)
f1, f2 = fl0.iff(AND(dcmp('Greater_DoubleDouble', get('DefendCloseAt', DBL), 0.0), dcmp('Greater_DoubleDouble', NOW, get('DefendCloseAt', DBL))), 'IfDefClose')
setvar(f1, 'DefendCloseAt', DBL, None, lit='0.0'); f1 = set_gate(f1, False)
fl0 = f1.join(f2)

fopen, fclosed = fl0.iff(get('Open', BOOL), 'IfOpen')

# ================================================================ closed: open on E; gate keeper + notice
SHOP = None
EKEY = anykey('E', 'Gamepad_FaceButton_Left')
fe, fne = fclosed.iff(AND(get('NearCommander', BOOL), EKEY), 'IfTalk')
setvar(fe, 'Open', BOOL, None, 'true'); setvar(fe, 'OpenAt', DBL, NOW); setvar(fe, 'Page', INT, None, '0'); setvar(fe, 'Cmd', ACTV, get('NearCmd', ACTV)); setvar(fe, 'PrevDown', BOOL, None, 'true')
pz = b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='true'), bo('ReturnValue', out=True, default='false')], *P(), tag='Pause'); fe.go(pz)
call(fe, 'CardOpened'); snd(fe, 'Swipe')
# gate keeper
GOK = AND(b.valid(GATEV(), *P()), b.valid(get('WMgr', ob('v', WM)), *P()))
GOPEN = b.getm('bGateOpen', GATEC, BOOL, GATEV(), *P())
GBROKEN = b.getm('GateBroken', WM, BOOL, get('WMgr', ob('v', WM)), *P())
DG = dist2d(HEROLOC, GATE_X, GATE_Y)
HX = b.brk(HEROLOC, *P())['X']
OUTSIDE = dcmp('Less_DoubleDouble', HX, GATE_X - 150.0)
INSIDE = dcmp('Greater_DoubleDouble', HX, GATE_X + 350.0)
fk, fnk = fne.iff(GOK, 'IfGateOk')
# guards open for the hero coming back (2x a second, on the commander scan clock, so "coming closer" compares 0.25 s apart)
fg, fng = fk.iff(dcmp('Greater_DoubleDouble', NOW, get('NextKeeper', DBL)), 'IfKeeper')
setvar(fg, 'NextKeeper', DBL, dop('Add_DoubleDouble', NOW, 0.25))
comeback = AND(AND(OUTSIDE, dcmp('Less_DoubleDouble', DG, OPEN_RANGE)), AND(dcmp('Less_DoubleDouble', DG, get('PrevDG', DBL)), AND(AND(NOT(GOPEN), NOT(GBROKEN)), get('AnyGuard', BOOL))))
fo, fno = fg.iff(comeback, 'IfComeBack')
setvar(fo, 'OpenedForHero', BOOL, None, 'true'); fo = set_gate(fo, True); msg(fo, 'The guards open the gate for you')
fg = fo.join(fno)
done_in = AND(get('OpenedForHero', BOOL), OR(INSIDE, dcmp('Greater_DoubleDouble', DG, 2500.0)))
fc, fnc = fg.iff(done_in, 'IfBehindHero')
setvar(fc, 'OpenedForHero', BOOL, None, 'false'); fc = set_gate(fc, False)
fg = fc.join(fnc)
setvar(fg, 'PrevDG', DBL, DG)
fk = fg.join(fng)
# notice + keys. E near the lever stays the lever's (the gate's own PressE), E next to a soldier stays his wheel.
NEARL = AND(dcmp('Less_DoubleDouble', DG, NOTICE_RANGE), AND(NOT(get('NearCommander', BOOL)), NOT(get('SoldNear', BOOL))))
WANT = AND(AND(NOT(GOPEN), NOT(GBROKEN)), AND(NEARL, NOT(get('OpenedForHero', BOOL))))
dt = dop('Subtract_DoubleDouble', NOW, get('LastT', DBL))
fade = b.math('FInterpConstantTo'.replace('FInterpConstantTo', 'FInterpTo_Constant'), [(D('Current', default='0.0'), get('NoticeA', DBL)), (D('Target', default='0.0'), seld(1.0, 0.0, WANT)), (D('DeltaTime', default='0.0'), dt), (D('InterpSpeed', default='2.5'), None)], D('ReturnValue', out=True), *P())
setvar(fk, 'NoticeA', DBL, fade)
fn1, fn2 = fk.iff(dcmp('Greater_DoubleDouble', get('NoticeA', DBL), 0.01), 'IfNotice')
rect(fn1, 660, 880, 600, 56, rgba(.04, .035, .03, dop('Multiply_DoubleDouble', get('NoticeA', DBL), 0.72)), tag='NoticeBg')
rect(fn1, 660, 880, 600, 2, rgba(.97, .82, .50, get('NoticeA', DBL)), tag='NoticeLine')
text(fn1, 'Use your keys to open the gate  -  press E', 960, 908, 26, rgba(.97, .92, .80, get('NoticeA', DBL)), anchor='c', tag='NoticeTxt')
fk = fn1.join(fn2)
fke, fnke = fk.iff(AND(EKEY, WANT), 'IfKeys')
fke = set_gate(fke, True)
fk = fke.join(fnke)
fclosed_end = fk.join(fnk).join(Flow(*fe.c))
# short messages while walking around
fm1, fm2 = fclosed_end.iff(dcmp('Greater_DoubleDouble', get('MsgUntil', DBL), NOW), 'IfMsgOut')
text(fm1, get('Msg', STRV), 960, 840, 24, GOLD, anchor='c', tag='MsgOut')
fclosed_end = fm1.join(fm2)

# ================================================================ open
WX, WY, WW, WH = 350, 130, 1220, 820
# refresh + close keys
fr, fnr = fopen.iff(dcmp('Greater_DoubleDouble', NOW, get('NextTroops', DBL)), 'IfTroops')
setvar(fr, 'NextTroops', DBL, dop('Add_DoubleDouble', NOW, 0.4)); call(fr, 'RefreshTroops')
fw = fr.join(fnr)
pcs_ = b.setm('bShowMouseCursor', PCON, bo('v', default='true'), None, pc, *P()); fw.go(pcs_)
OPENT = dop('Subtract_DoubleDouble', NOW, get('OpenAt', DBL))
PROG = b.math('FClamp', [(D('Value', default='0.0'), dop('Divide_DoubleDouble', OPENT, 0.7)), (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), *P())
# the stroke + panel: one material, T drives the motion because the game is paused while the window is up
for pname, val in (('T', NOW), ('Open', PROG)):
    n = b.call(MID, 'SetScalarParameterValue', [NAME_('ParameterName', pname), F('Value')], *P(), target=get('StrokeMid', ob('v', MID)), tag='Par' + pname)
    b.wire(val, n, 'Value'); fw.go(n)
dm = b.call(HUDC, 'DrawMaterial', [ob('Material', MATI), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
            F('MaterialUWidth', default='1.0'), F('MaterialVHeight', default='1.0'), F('Scale', default='1.0'), bo('bScalePosition', default='false'),
            F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='DrawStroke')
b.wire(get('StrokeMid', ob('v', MID)), dm, 'Material')
b.wire(X(WX - 40), dm, 'ScreenX'); b.wire(Y(WY - 40), dm, 'ScreenY'); b.wire(SZ(WW + 80), dm, 'ScreenW'); b.wire(SZ(WH + 80), dm, 'ScreenH')
fw.go(dm)
# the contents wait for the stroke to start closing
fshow, fhide = fw.iff(dcmp('Greater_DoubleDouble', OPENT, 0.18), 'IfShow')
fd = fshow

CMDS = asold(CMD())
CR, CSt = chan(CMDS, 'Rank'), chan(CMDS, 'State')
CLV = CR['Y']
LVF = lambda lv: dop('Add_DoubleDouble', 1.0, dop('Multiply_DoubleDouble', dop('Subtract_DoubleDouble', lv, 1.0), 0.15))
def maxhp(sold_actor, lv): return dop('Multiply_DoubleDouble', seld(90.0, 120.0, hastag(sold_actor, 'Xbow')), LVF(lv))
def rankname(lv):
    idx = b.math('Clamp', [(it('Value', default='0'), iop('Subtract_IntInt', rnd(lv), 1)), (it('Min', default='0'), None), (it('Max', default='4'), None)], it('ReturnValue', out=True), *P())
    return getarr('RankNames', STRV, idx)
def bar(fl_, x, y, w, h, frac, colr, tag):
    rect(fl_, x, y, w, h, col(.12, .10, .08, .9), tag='BarBg');
    fr_ = b.math('FClamp', [(D('Value', default='0.0'), frac), (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), *P())
    rect(fl_, x, y, dop('Multiply_DoubleDouble', fr_, float(w)), h, colr, tag=tag)
def button(fl_, x, y, w, h, label, page=0, enabled=None, sub=None, lh=24, tag='Btn', hot=False):
    """draws the button; returns (clicked flow, rest flow). A disabled button draws dim and never fires."""
    on = icmp('EqualEqual_IntInt', get('Page', INT), page)
    if enabled is not None: on = AND(on, enabled)
    over = AND(inside(x, y, w, h), on)
    rect(fl_, x, y, w, h, selc(HOVER, col(.20, .15, .08, .85) if hot else PANEL, over), tag='Bg' + tag)
    lc_ = selc(LINEHOT, LINE, over)
    for rx, ry, rw, rh in ((x, y, w, 2), (x, y + h - 2, w, 2), (x, y, 2, h), (x + w - 2, y, 2, h)): rect(fl_, rx, ry, rw, rh, lc_, tag='Line' + tag)
    tc = selc(CREAM, DIM, enabled) if enabled is not None else CREAM
    text(fl_, label, x + w / 2.0, y + (h / 2.0 if sub is None else h * .36), lh, tc, anchor='c', tag='Txt' + tag)
    if sub is not None: text(fl_, sub, x + w / 2.0, y + h * .72, 18, DIM, anchor='c', tag='Sub' + tag)
    t, f = fl_.iff(AND(PRESS, over), 'If' + tag); snd(t, 'Swipe')
    return t, f

# ---- header
text(fd, 'COMMANDER', WX + 40, WY + 36, 22, GOLD, tag='Head')
tc_, fc_ = button(fd, WX + WW - 170, WY + 16, 130, 40, 'CLOSE', lh=20, tag='Close')
ex_key = OR(anykey('E', 'Escape', 'Gamepad_FaceButton_Right', 'BackSpace'), NOT(b.valid(CMD(), *P())))
fesc, fnesc = fc_.iff(ex_key, 'IfEsc')
fx = tc_.join(fesc)
setvar(fx, 'Open', BOOL, None, 'false')
upz = b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='false'), bo('ReturnValue', out=True, default='false')], *P(), tag='Unpause'); fx.go(upz)
fx.go(b.setm('bShowMouseCursor', PCON, BOOL, None, pc, *P()))
imo = b.lib(UMG('WidgetBlueprintLibrary'), 'SetInputMode_GameOnly', [ob('PlayerController', PCON), dict(bo('bFlushInput', default='false'), advanced=True)], *P(), tag='InputGame')
b.wire(pc, imo, 'PlayerController'); fx.go(imo)
fd = fnesc

# ---- left: who he is
LX = WX + 40
sprite(fd, 'BustTex', LX, WY + 70, 210, 240, (0.0, 0.0, 1.0, 1.0), tag='Bust')
for rx, ry, rw, rh in ((LX, WY + 70, 210, 2), (LX, WY + 308, 210, 2), (LX, WY + 70, 2, 240), (LX + 208, WY + 70, 2, 240)): rect(fd, rx, ry, rw, rh, LINE, tag='BustLine')
TX = LX + 226
text(fd, get('CmdName', STRV), TX, WY + 96, 34, WHITE, tag='Name')
text(fd, catn('Age ', istr(get('CmdAge', INT))), TX, WY + 140, 22, CREAM, tag='Age')
text(fd, catn(rankname(CLV), '  -  level ', istr(rnd(CLV))), TX, WY + 172, 22, GOLD, tag='CmdRank')
text(fd, catn('Leads ', istr(iop('Add_IntInt', get('NS', INT), get('NX', INT))), ' men'), TX, WY + 204, 22, CREAM, tag='Leads')
# stats
SY = WY + 340
text(fd, 'STATS', LX, SY, 20, GOLD, tag='StatH')
MAXC = maxhp(CMD(), CLV)
text(fd, 'Health', LX, SY + 34, 20, DIM, tag='S1'); bar(fd, LX + 110, SY + 26, 200, 16, dop('Divide_DoubleDouble', CSt['X'], MAXC), rgba(.72, .20, .14, 1.0) if False else col(.72, .20, .14, 1), 'HpC')
text(fd, catn(istr(rnd(CSt['X'])), ' / ', istr(rnd(MAXC))), LX + 322, SY + 34, 20, CREAM, tag='S1v')
text(fd, 'Damage', LX, SY + 66, 20, DIM, tag='S2'); text(fd, istr(rnd(dop('Multiply_DoubleDouble', 12.0, LVF(CLV)))), LX + 110, SY + 66, 20, CREAM, tag='S2v')
text(fd, 'Battle XP', LX, SY + 98, 20, DIM, tag='S3'); text(fd, istr(rnd(CR['X'])), LX + 110, SY + 98, 20, CREAM, tag='S3v')
# aura
AY = WY + 480
text(fd, 'AURA OF COMMAND', LX, AY, 20, GOLD, tag='AuraH')
ASC = (lambda: None)
ascn = b.name('AsCmd'); cast(G, ascn, CMDC, 'AsBP Soldier Commander', *P(), pure=True); b.wire(CMD(), ascn, 'Object'); ASCMD = (ascn, 'AsBP Soldier Commander')
AUR = b.getm('AuraRadius', CMDC, DBL, ASCMD, *P()); AUH = b.getm('AuraRegen', CMDC, DBL, ASCMD, *P())
text(fd, catn('Heals nearby men ', istr(rnd(AUH)), ' health each second'), LX, AY + 32, 20, CREAM, tag='Aura1')
text(fd, catn('Reach ', istr(rnd(dop('Divide_DoubleDouble', AUR, 100.0))), ' metres'), LX, AY + 60, 20, CREAM, tag='Aura2')
text(fd, catn(istr(get('InAura', INT)), ' of his men stand in it now'), LX, AY + 88, 20, CREAM, tag='Aura3')
# gate
gatelbl = sels('CLOSE THE GATE', 'OPEN THE GATE', b.getm('bGateOpen', GATEC, BOOL, GATEV(), *P()))
tg, fd = button(fd, LX, WY + WH - 130, 360, 60, gatelbl, lh=22, tag='Gate')
ga = call_with(tg, 'ToggleGateByCommander', [])
fd = tg.join(fd)

# ---- right: troops
RX = WX + 450
text(fd, 'TROOPS', RX, WY + 96, 22, GOLD, tag='TroopH')
text(fd, catn(istr(get('NS', INT)), ' swordsmen   ', istr(get('NX', INT)), ' crossbowmen'), RX + 130, WY + 96, 20, CREAM, tag='TroopSum')
HY = WY + 124
for hx, ht in ((0, 'TYPE'), (190, 'RANK'), (340, 'LV'), (400, 'HEALTH'), (640, 'XP')): text(fd, ht, RX + hx, HY, 16, DIM, tag='ColH')
rect(fd, RX, HY + 14, 720, 1, LINE, tag='ColLine')
ROW0, ROWH, ROWS = HY + 34, 26, 8
nrows = b.math('Min', [(it('A', default='0'), alen(get('Members', arr(ACTV)))), (it('B', default=str(ROWS)), None)], it('ReturnValue', out=True), *P())
lp = b.forloop(None, iop('Subtract_IntInt', nrows, 1), *P()); fd.go(lp, inp='execute', out=None)
fb = Flow((lp, 'LoopBody'))
ry_ = dop('Add_DoubleDouble', float(ROW0), dop('Multiply_DoubleDouble', i2d((lp, 'Index')), float(ROWH)))
m_ = getarr('Members', ACTV, (lp, 'Index')); msold = asold(m_)
mr, ms = chan(msold, 'Rank'), chan(msold, 'State')
text(fb, sels('Crossbowman', 'Swordsman', hastag(m_, 'Xbow')), RX, ry_, 19, CREAM, tag='RowT')
text(fb, rankname(mr['Y']), RX + 190, ry_, 19, GOLD, tag='RowR')
text(fb, istr(rnd(mr['Y'])), RX + 340, ry_, 19, CREAM, tag='RowL')
bar(fb, RX + 400, dop('Subtract_DoubleDouble', ry_, 7.0), 220, 14, dop('Divide_DoubleDouble', ms['X'], maxhp(m_, mr['Y'])), col(.55, .72, .28, 1), 'RowHp')
text(fb, istr(rnd(mr['X'])), RX + 640, ry_, 19, CREAM, tag='RowXp')
fd = Flow((lp, 'Completed'))
# empty squad line
fe0, fne0 = fd.iff(icmp('EqualEqual_IntInt', alen(get('Members', arr(ACTV))), 0), 'IfEmpty')
text(fe0, 'No men yet. Pick a size and gather his squad.', RX, ROW0 + 40, 20, DIM, tag='Empty')
fd = fe0.join(fne0)
frm, fnm = fd.iff(icmp('Greater_IntInt', alen(get('Members', arr(ACTV))), ROWS), 'IfMore')
text(frm, catn('and ', istr(iop('Subtract_IntInt', alen(get('Members', arr(ACTV))), ROWS)), ' more'), RX, ROW0 + ROWS * ROWH, 16, DIM, tag='More')
fd = frm.join(fnm)

# ---- squad size + gather icon
QY = WY + 410
text(fd, 'SQUAD SIZE', RX, QY + 24, 20, GOLD, tag='SzH')
t1, fd = button(fd, RX + 170, QY, 48, 48, '-', lh=30, tag='SzMinus')
setvar(t1, 'Size', INT, b.math('Max', [(it('A', default='1'), iop('Subtract_IntInt', get('Size', INT), 1)), (it('B', default='1'), None)], it('ReturnValue', out=True), *P())); fd = t1.join(fd)
text(fd, istr(get('Size', INT)), RX + 250, QY + 24, 30, WHITE, anchor='c', tag='SzV')
t1, fd = button(fd, RX + 282, QY, 48, 48, '+', lh=30, tag='SzPlus')
setvar(t1, 'Size', INT, b.math('Min', [(it('A', default='1'), iop('Add_IntInt', get('Size', INT), 1)), (it('B', default='30'), None)], it('ReturnValue', out=True), *P())); fd = t1.join(fd)
t1, fd = button(fd, RX + 370, QY - 4, 350, 56, 'GATHER SQUAD', lh=24, tag='Gather', hot=True)
setvar(t1, 'Page', INT, None, '1')
mix0 = b.math('Min', [(it('A', default='0'), iop('Divide_IntInt', get('Size', INT), 3)), (it('B', default='0'), get('AvX', INT))], it('ReturnValue', out=True), *P())
setvar(t1, 'MixX', INT, mix0); fd = t1.join(fd)

# ---- orders
OY0 = WY + 490; BW, BH, GAP = 232, 104, 12
text(fd, 'ORDERS', RX, OY0, 20, GOLD, tag='OrdH')
OY1 = OY0 + 22; OY2 = OY1 + BH + GAP
HASMEN = icmp('Greater_IntInt', alen(get('Members', arr(ACTV))), 0)
def order_btn(fl_, col_, row, label, sub, tag):
    return button(fl_, RX + col_ * (BW + GAP), OY1 if row == 0 else OY2, BW, BH, label, sub=sub, lh=18, tag=tag, enabled=HASMEN)
t1, fd = order_btn(fd, 0, 0, 'DEFEND THE CASTLE', 'He takes charge', 'Defend'); call(t1, 'OrderDefend'); fd = t1.join(fd)
t1, fd = order_btn(fd, 1, 0, 'LEAD AN ATTACK', 'Asks you where', 'Attack'); setvar(t1, 'Page', INT, None, '2'); call(t1, 'CountTentacles'); fd = t1.join(fd)
t1, fd = order_btn(fd, 2, 0, 'FOLLOW ME', 'Fights at your side', 'Follow'); call(t1, 'OrderFollow'); fd = t1.join(fd)
t1, fd = order_btn(fd, 0, 1, 'HOLD HERE', 'Stand round him', 'Hold'); call(t1, 'OrderHold'); fd = t1.join(fd)
t1, fd = order_btn(fd, 1, 1, 'DISBAND', 'Back to their posts', 'Disband'); call(t1, 'OrderDisband'); fd = t1.join(fd)
fm1, fm2 = fd.iff(dcmp('Greater_DoubleDouble', get('MsgUntil', DBL), NOW), 'IfMsg')
text(fm1, get('Msg', STRV), RX + 2 * (BW + GAP) + BW / 2.0, OY2 + BH / 2.0, 19, GOLD, anchor='c', tag='MsgIn')
fd = fm1.join(fm2)

# ---- page 1: how many of each
fp1, fnp1 = fd.iff(icmp('EqualEqual_IntInt', get('Page', INT), 1), 'IfPage1')
rect(fp1, WX, WY, WW, WH, DIMSCR, tag='Dim1'); PX, PY, PW, PH = 620, 310, 680, 430
rect(fp1, PX, PY, PW, PH, PANEL2, tag='Pop1')
for rx, ry, rw, rh in ((PX, PY, PW, 2), (PX, PY + PH - 2, PW, 2), (PX, PY, 2, PH), (PX + PW - 2, PY, 2, PH)): rect(fp1, rx, ry, rw, rh, LINEHOT, tag='Pop1L')
text(fp1, catn('GATHER ', istr(get('Size', INT)), ' MEN'), PX + PW / 2.0, PY + 44, 30, WHITE, anchor='c', tag='P1H')
text(fp1, 'Pick how many of each', PX + PW / 2.0, PY + 82, 20, DIM, anchor='c', tag='P1S')
NSW = iop('Subtract_IntInt', get('Size', INT), get('MixX', INT))
def stepper(fl_, y, label, val, free, tminus, tplus):
    text(fl_, label, PX + 40, y + 24, 24, CREAM, tag='MixL')
    text(fl_, catn(istr(free), ' free'), PX + 40, y + 52, 17, DIM, tag='MixF')
    t, fl_ = button(fl_, PX + 330, y, 56, 56, '-', page=1, lh=30, tag='Mn' + tminus); yield_ = [t]
    text(fl_, istr(val), PX + 430, y + 28, 32, WHITE, anchor='c', tag='MixV')
    t2, fl_ = button(fl_, PX + 474, y, 56, 56, '+', page=1, lh=30, tag='Pl' + tplus)
    return t, t2, fl_
def imin(a, c): return b.math('Min', [(it('A', default='0'), a), (it('B', default='0'), c)], it('ReturnValue', out=True), *P())
def imax(a, c): return b.math('Max', [(it('A', default='0'), a), (it('B', default=str(c) if isnum(c) else '0'), None if isnum(c) else c)], it('ReturnValue', out=True), *P())
XMAX = imin(get('Size', INT), get('AvX', INT))
tm, tp, fp1 = stepper(fp1, PY + 110, 'Crossbowmen', get('MixX', INT), get('AvX', INT), 'X', 'X')
setvar(tm, 'MixX', INT, imax(iop('Subtract_IntInt', get('MixX', INT), 1), 0)); setvar(tp, 'MixX', INT, imin(iop('Add_IntInt', get('MixX', INT), 1), XMAX)); fp1 = fp1.join(tm, tp)
tm, tp, fp1 = stepper(fp1, PY + 190, 'Swordsmen', NSW, get('AvS', INT), 'S', 'S')
setvar(tm, 'MixX', INT, imin(iop('Add_IntInt', get('MixX', INT), 1), XMAX)); setvar(tp, 'MixX', INT, imax(iop('Subtract_IntInt', get('MixX', INT), 1), 0)); fp1 = fp1.join(tm, tp)
bar(fp1, PX + 40, PY + 268, PW - 80, 14, dop('Divide_DoubleDouble', i2d(get('MixX', INT)), i2d(get('Size', INT))), GOLD, 'MixBar')
tgo, fp1 = button(fp1, PX + 40, PY + 310, 380, 84, 'SOUND THE HORN', page=1, sub='The nearest free men join him', lh=24, tag='Horn', hot=True)
call_with(tgo, 'DoGather', [it('NumXbow'), it('NumSword')], [('NumXbow', get('MixX', INT)), ('NumSword', imin(NSW, get('AvS', INT)))]); setvar(tgo, 'Page', INT, None, '0'); fp1 = fp1.join(tgo)
tbk, fp1 = button(fp1, PX + 440, PY + 310, 200, 84, 'BACK', page=1, lh=22, tag='Back1'); setvar(tbk, 'Page', INT, None, '0'); fp1 = fp1.join(tbk)
fd = fp1.join(fnp1)

# ---- page 2: attack confirmation
fp2, fnp2 = fd.iff(icmp('EqualEqual_IntInt', get('Page', INT), 2), 'IfPage2')
rect(fp2, WX, WY, WW, WH, DIMSCR, tag='Dim2'); PH2 = 340
rect(fp2, PX, PY, PW, PH2, PANEL2, tag='Pop2')
for rx, ry, rw, rh in ((PX, PY, PW, 2), (PX, PY + PH2 - 2, PW, 2), (PX, PY, 2, PH2), (PX + PW - 2, PY, 2, PH2)): rect(fp2, rx, ry, rw, rh, LINEHOT, tag='Pop2L')
text(fp2, 'LEAD AN ATTACK', PX + PW / 2.0, PY + 44, 30, WHITE, anchor='c', tag='P2H')
text(fp2, 'Where do you send him?  The gate opens for them.', PX + PW / 2.0, PY + 82, 20, DIM, anchor='c', tag='P2S')
HASTENT = icmp('Greater_IntInt', get('TentN', INT), 0)
t1, fp2 = button(fp2, PX + 40, PY + 120, 290, 110, 'ATTACK TENTACLES', page=2, enabled=HASTENT, sub=sels(catn(istr(get('TentN', INT)), ' out there'), 'None up right now', HASTENT), lh=22, tag='AtkT', hot=True)
call(t1, 'OrderTentacles'); setvar(t1, 'Page', INT, None, '0'); fp2 = fp2.join(t1)
t1, fp2 = button(fp2, PX + 350, PY + 120, 290, 110, 'ATTACK OUTSIDE', page=2, sub='Hunt the zombies in the field', lh=22, tag='AtkO', hot=True)
call(t1, 'OrderAttackOutside'); setvar(t1, 'Page', INT, None, '0'); fp2 = fp2.join(t1)
t1, fp2 = button(fp2, PX + 40, PY + 250, 600, 60, 'NOT NOW', page=2, lh=20, tag='AtkNo'); setvar(t1, 'Page', INT, None, '0'); fp2 = fp2.join(t1)
fd = fp2.join(fnp2)

fopen_end = fd.join(fx, fhide)

# ---------------------------------------------------------------- end of every frame
fend = fclosed_end.join(fopen_end)
setvar(fend, 'PrevDown', BOOL, key('LeftMouseButton', down=True))
setvar(fend, 'LastT', DBL, NOW)

# ================================================================ CardOpened: who is he, which squad is his, stroke MID
b.event('CardOpened', [], 0, 20000); XY[0] = 0; XY[1] = 20000
fo = Flow(('CardOpened', 'then'))
fnd = b.name('FindCmd')
G.node(fnd, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Find")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, {'name': 'ItemToFind', 'cat': 'wildcard', 'ref': True}, it('ReturnValue', out=True, default='-1')], *P())
b.wire(get('Known', arr(ACTV)), fnd, 'TargetArray'); b.wire(CMD(), fnd, 'ItemToFind')
fn, fk_ = fo.iff(icmp('Less_IntInt', (fnd, 'ReturnValue'), 0), 'IfNew')
add_to(fn, 'Known', CMD())
fo = fn.join(fk_)
idx_ = (fnd, 'ReturnValue')
setvar(fo, 'CmdIdx', INT, idx_)
NN, NA = iop('Percent_IntInt', get('CmdIdx', INT), 8), iop('Percent_IntInt', get('CmdIdx', INT), 8)
setvar(fo, 'CmdName', STRV, getarr('Names', STRV, NN))
setvar(fo, 'CmdAge', INT, getarr('Ages', INT, NA))
tn = b.lib(KSTR, 'Conv_StringToName', [S('InString'), dict(N('ReturnValue'), out=True)], *P(), pure=True); b.wire(catn('Lead', istr(get('CmdIdx', INT))), tn, 'InString')
setvar(fo, 'LeadTag', NAMEV, (tn, 'ReturnValue'))
setvar(fo, 'NextTroops', DBL, None, lit='0.0')
fm, fh = fo.iff(NOT(b.valid(get('StrokeMid', ob('v', MID)), *P())), 'IfNoMid')
mk = b.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), ob('Parent', MATI), NAME_('OptionalName', 'None'),
           {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None', 'advanced': True}, ob('ReturnValue', MID, out=True)], *P(), tag='MakeMid')
b.wire(get('StrokeMat', ob('v', MATI)), mk, 'Parent'); fm.go(mk); setvar(fm, 'StrokeMid', ob('v', MID), (mk, 'ReturnValue'))
fo = fm.join(fh)
evpc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], *P(), pure=True, tag='EvPC')
imo2 = b.lib(UMG('WidgetBlueprintLibrary'), 'SetInputMode_GameAndUIEx', [ob('PlayerController', PCON), ob('InWidgetToFocus', UMG('Widget')),
             {'name': 'InMouseLockMode', 'cat': 'byte', 'obj': ENUM('EMouseLockMode'), 'default': 'DoNotLock'}, bo('bHideCursorDuringCapture', default='false'), dict(bo('bFlushInput', default='false'), advanced=True)], *P(), tag='InputUI')
b.wire((evpc, 'ReturnValue'), imo2, 'PlayerController'); fo.go(imo2)

# ================================================================ RefreshTroops: his men, the free men, counts
b.event('RefreshTroops', [], 0, 22000); XY[0] = 0; XY[1] = 22000
fr = Flow(('RefreshTroops', 'then'))
for v_ in ('Members', 'CandS', 'CandX'): clear(fr, v_)
for v_ in ('NS', 'NX', 'AvS', 'AvX', 'InAura'): setvar(fr, v_, INT, None, lit='0')
all_ = findall(fr, P_SOLDIER, 'All')
lp = b.foreach(ACT, *P()); b.wire(all_, lp, 'Array'); fr.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody')); e_ = (lp, 'Array Element')
fa, fna = fb.iff(AND(lifespan_ok(e_), NOT(hastag(e_, 'Commander'))), 'IfAlive')
fme, fnot = fa.iff(hastag(e_, get('LeadTag', NAMEV)), 'IfMine')
add_to(fme, 'Members', e_)
fxb, fsw = fme.iff(hastag(e_, 'Xbow'), 'IfMineX')
setvar(fxb, 'NX', INT, iop('Add_IntInt', get('NX', INT), 1)); setvar(fsw, 'NS', INT, iop('Add_IntInt', get('NS', INT), 1))
fme = fxb.join(fsw)
gtd = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), D('ReturnValue', out=True)], *P(), target=e_, pure=True, const=True, tag='DistCmd'); b.wire(CMD(), gtd, 'OtherActor')
fia, fnia = fme.iff(dcmp('Less_DoubleDouble', (gtd, 'ReturnValue'), b.getm('AuraRadius', CMDC, DBL, (lambda n_: (cast(G, n_, CMDC, 'AsBP Soldier Commander', *P(), pure=True), b.wire(CMD(), n_, 'Object'), (n_, 'AsBP Soldier Commander'))[2])(b.name('AsCmdR')), *P())), 'IfInAura')
setvar(fia, 'InAura', INT, iop('Add_IntInt', get('InAura', INT), 1))
OC = chan(asold(e_), 'Order')['X']
crew = dcmp('Less_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), dop('Subtract_DoubleDouble', OC, 3.0))], D('ReturnValue', out=True), *P()), 0.5)
ffr, fbs = fnot.iff(AND(NOT(hastag(e_, 'Squad')), NOT(crew)), 'IfFree')
fxb, fsw = ffr.iff(hastag(e_, 'Xbow'), 'IfFreeX')
add_to(fxb, 'CandX', e_); setvar(fxb, 'AvX', INT, iop('Add_IntInt', get('AvX', INT), 1)); add_to(fsw, 'CandS', e_); setvar(fsw, 'AvS', INT, iop('Add_IntInt', get('AvS', INT), 1))

# ================================================================ DoGather: nearest men of each type join him
b.event('DoGather', [it('NumXbow'), it('NumSword')], 0, 24000); XY[0] = 0; XY[1] = 24000
fg = Flow(('DoGather', 'then'))
def gather_type(fl_, arrvar, count, tag):
    lp_ = b.forloop(None, count, *P()); G.nodes[[q[0] for q in G.nodes].index(lp_)][3][[p['name'] for p in G.nodes[[q[0] for q in G.nodes].index(lp_)][3]].index('FirstIndex')]['default'] = '1'
    fl_.go(lp_, inp='execute', out=None)
    fb_ = Flow((lp_, 'LoopBody'))
    fy, fn_ = fb_.iff(icmp('Greater_IntInt', alen(get(arrvar, arr(ACTV))), 0), 'IfCand' + tag)
    pk, _ = nearest(actor_loc(CMD()), get(arrvar, arr(ACTV)))
    setvar(fy, 'Pick', ACTV, pk)
    add_tag(fy, get('Pick', ACTV), 'Squad'); add_tag(fy, get('Pick', ACTV), get('LeadTag', NAMEV))
    so = asold(get('Pick', ACTV))
    write_chan(fy, so, 'Order', vecf(5.0, 0.0, 0.0)); write_chan(fy, so, 'Goal', actor_loc(CMD()))
    remove_from(fy, arrvar, get('Pick', ACTV))
    return Flow((lp_, 'Completed'))
fg = gather_type(fg, 'CandX', ('DoGather', 'NumXbow'), 'X')
fg = gather_type(fg, 'CandS', ('DoGather', 'NumSword'), 'S')
msg(fg, catn(get('CmdName', STRV), ' sounds the horn: ', istr(iop('Add_IntInt', ('DoGather', 'NumXbow'), ('DoGather', 'NumSword'))), ' men come'))
setvar(fg, 'NextTroops', DBL, None, lit='0.0')

# ================================================================ orders
b.event('ApplyOrder', [fl('Code', default=None) if False else D('Code'), V('GoalLoc'), bo('WithCommander')], 0, 26000); XY[0] = 0; XY[1] = 26000
fa_ = Flow(('ApplyOrder', 'then'))
del_tag(fa_, CMD(), 'CD_DefendCastle')
setvar(fa_, 'AttackV', ACTV, None); setvar(fa_, 'DefendCloseAt', DBL, None, lit='0.0')
lp = b.foreach(ACT, *P()); b.wire(get('Members', arr(ACTV)), lp, 'Array'); fa_.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody')); so = asold((lp, 'Array Element'))
write_chan(fb, so, 'Order', vecf(('ApplyOrder', 'Code'), 0.0, 0.0)); write_chan(fb, so, 'Goal', ('ApplyOrder', 'GoalLoc'))
fc_ = Flow((lp, 'Completed'))
fw_, fnw_ = fc_.iff(('ApplyOrder', 'WithCommander'), 'IfWith')
write_chan(fw_, asold(CMD()), 'Order', vecf(('ApplyOrder', 'Code'), 0.0, 0.0)); write_chan(fw_, asold(CMD()), 'Goal', ('ApplyOrder', 'GoalLoc'))

def apply(fl_, code, goal, with_cmd=True):
    pins = [D('Code', default=str(float(code))), V('GoalLoc', default='%f,%f,%f' % goal if isinstance(goal, tuple) and isnum(goal[0]) else '0, 0, 0'), bo('WithCommander', default='true' if with_cmd else 'false')]
    n = call(fl_, 'ApplyOrder', pins)
    if not (isinstance(goal, tuple) and isnum(goal[0])): b.wire(goal, n, 'GoalLoc')
    return n
def order_event(nm):
    b.event(nm, [], 0, XY[1] + 2000); XY[0] = 0; XY[1] += 2000
    return Flow((nm, 'then'))
XY[1] = 28000
f_ = order_event('OrderFollow'); apply(f_, 1, actor_loc(OWNER)); msg(f_, catn(get('CmdName', STRV), ' and his men follow you'))
f_ = order_event('OrderHold'); apply(f_, 5, actor_loc(CMD()), False); msg(f_, 'They hold round him')
f_ = order_event('OrderDisband')
lp = b.foreach(ACT, *P()); b.wire(get('Members', arr(ACTV)), lp, 'Array')
apply(f_, 0, (0.0, 0.0, 0.0)); f_.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody')); del_tag(fb, (lp, 'Array Element'), 'Squad'); del_tag(fb, (lp, 'Array Element'), get('LeadTag', NAMEV))
f2_ = Flow((lp, 'Completed')); setvar(f2_, 'NextTroops', DBL, None, lit='0.0'); msg(f2_, 'The men return to their posts')
f_ = order_event('OrderAttackOutside'); f_ = set_gate(f_, True); apply(f_, 6, (-1000.0, 1750.0, 12.0)); msg(f_, catn(get('CmdName', STRV), ' leads them out'))
# Defend the castle, plain version: crossbows to the wall, swords inside the gate, gate shuts in 10 s. Tag = the C++ brain takes over.
f_ = order_event('OrderDefend'); apply(f_, 5, (150.0, 1750.0, 12.0))
lp = b.foreach(ACT, *P()); b.wire(get('Members', arr(ACTV)), lp, 'Array'); f_.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody')); fx_, fs_ = fb.iff(hastag((lp, 'Array Element'), 'Xbow'), 'IfWall')
so = asold((lp, 'Array Element')); write_chan(fx_, so, 'Order', vecf(4.0, 0.0, 0.0)); write_chan(fx_, so, 'Goal', vecf(-20.0, 1750.0, 990.0))
f2_ = Flow((lp, 'Completed')); add_tag(f2_, CMD(), 'CD_DefendCastle'); setvar(f2_, 'DefendCloseAt', DBL, dop('Add_DoubleDouble', NOW, 10.0))
msg(f2_, catn(get('CmdName', STRV), ' takes the defence'))
f_ = order_event('ToggleGateByCommander')
fo_, fc_ = f_.iff(b.getm('bGateOpen', GATEC, BOOL, GATEV(), *P()), 'IfGO')
fo_ = set_gate(fo_, False); msg(fo_, catn(get('CmdName', STRV), ' shuts the gate')); fc_ = set_gate(fc_, True); msg(fc_, catn(get('CmdName', STRV), ' opens the gate'))

# ---- tentacles
f_ = order_event('CountTentacles')
vs = findall(f_, P_VIT, 'Vitals'); setvar(f_, 'Vit', arr(ACTV), vs); setvar(f_, 'TentN', INT, None, lit='0')
lp = b.foreach(ACT, *P()); b.wire(get('Vit', arr(ACTV)), lp, 'Array'); f_.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody'))
def vit_as(actor):
    n_ = b.name('AsVit'); cast(G, n_, VITC, 'AsBP Tentacle Vitals', *P(), pure=True); b.wire(actor, n_, 'Object'); return (n_, 'AsBP Tentacle Vitals')
fy, _ = fb.iff(dcmp('Greater_DoubleDouble', b.getm('Health', VITC, DBL, vit_as((lp, 'Array Element')), *P()), 0.0), 'IfVitAlive')
setvar(fy, 'TentN', INT, iop('Add_IntInt', get('TentN', INT), 1))
f_ = order_event('OrderTentacles')
tv, _ = nearest(actor_loc(CMD()), get('Vit', arr(ACTV)))
setvar(f_, 'AttackPick', ACTV, tv)
fy, fn_ = f_.iff(b.valid(get('AttackPick', ACTV), *P()), 'IfVit')
fy = set_gate(fy, True)
apply(fy, 5, actor_loc(get('AttackPick', ACTV)))   # clears AttackV, so set it after
setvar(fy, 'AttackV', ACTV, get('AttackPick', ACTV))
lp = b.foreach(ACT, *P()); b.wire(get('Members', arr(ACTV)), lp, 'Array'); fy.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody')); e_ = (lp, 'Array Element'); ix_ = (lp, 'Array Index')
ang = dop('Multiply_DoubleDouble', i2d(ix_), 0.62)
rad = seld(1300.0, 260.0, hastag(e_, 'Xbow'))
VP = b.brk(actor_loc(get('AttackV', ACTV)), *P())
gx = dop('Add_DoubleDouble', VP['X'], dop('Multiply_DoubleDouble', b.math('Cos', [(D('A', default='0.0'), ang)], D('ReturnValue', out=True), *P()), rad))
gy = dop('Add_DoubleDouble', VP['Y'], dop('Multiply_DoubleDouble', b.math('Sin', [(D('A', default='0.0'), ang)], D('ReturnValue', out=True), *P()), rad))
write_chan(fb, asold(e_), 'Goal', vecf(gx, gy, VP['Z']))
f2_ = Flow((lp, 'Completed')); msg(f2_, catn(get('CmdName', STRV), ' leads them at the tentacle'))
# 1 Hz: men in reach strike. Blueprint: soldiers only target zombies by themselves (see #80 notes).
f_ = order_event('TentacleTick')
AV = lambda: vit_as(get('AttackV', ACTV))
fd_, fal = f_.iff(dcmp('LessEqual_DoubleDouble', b.getm('Health', VITC, DBL, AV(), *P()), 0.0), 'IfTentDead')
setvar(fd_, 'AttackV', ACTV, None); apply(fd_, 5, actor_loc(CMD()), False); msg(fd_, 'The tentacle is down')
pa_ = b.call(ACT, 'GetAttachParentActor', [ob('ReturnValue', ACT, out=True)], *P(), target=get('AttackV', ACTV), pure=True, const=True, tag='TentParent')
lp = b.foreach(ACT, *P()); b.wire(get('Members', arr(ACTV)), lp, 'Array'); fal.go(lp, inp='Exec', out=None)
fb = Flow((lp, 'LoopBody')); e_ = (lp, 'Array Element')
gtd = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), D('ReturnValue', out=True)], *P(), target=e_, pure=True, const=True, tag='DistTent'); b.wire((pa_, 'ReturnValue'), gtd, 'OtherActor')
fr_, _ = fb.iff(AND(lifespan_ok(e_), dcmp('Less_DoubleDouble', (gtd, 'ReturnValue'), seld(1500.0, 450.0, hastag(e_, 'Xbow')))), 'IfReach')
dmg = b.lib(GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage', default='0.0'), ob('EventInstigator', CTRL), ob('DamageCauser', ACT), CLSPIN('DamageTypeClass', CLS('DamageType'), None), fl('ReturnValue', out=True, default='0.0')], *P(), tag='HitTent')
b.wire((pa_, 'ReturnValue'), dmg, 'DamagedActor'); b.wire(seld(15.0, 20.0, hastag(e_, 'Xbow')), dmg, 'BaseDamage'); b.wire(e_, dmg, 'DamageCauser'); fr_.go(dmg)
MNT = CLS('AnimMontage')
ch_ = b.name('AsChar'); cast(G, ch_, CHARC, 'AsCharacter', *P(), pure=True); b.wire(e_, ch_, 'Object')
pm = b.call(CHARC, 'PlayAnimMontage', [dict(ob('AnimMontage', MNT), dobj='/Game/CastleDefender/Gameplay/Castle/Combat/AM_Slash1.AM_Slash1'), fl('InPlayRate', default='1.000000'), N('StartSectionName', default='None'), fl('ReturnValue', out=True, default='0.0')], *P(), target=(ch_, 'AsCharacter'), tag='Swing')
fr_.go(pm)

# ---------------------------------------------------------------- self-check + write
names = [n[0] for n in G.nodes]
assert len(names) == len(set(names)), 'duplicate node names'
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
outs = {(n[0], p['name']) for n in G.nodes for p in n[3] if p.get('out')}
wrongdir = [l for l in G.links if (l[0], l[1]) not in outs or (l[2], l[3]) in outs]
if wrongdir: raise SystemExit('direction: %s' % wrongdir[:10])
open(os.path.join(OUT, 'BPC_CommanderCard_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_CommanderCard: nodes %d, links %d' % (len(G.nodes), len(G.links)))
VARS = dict(Open=('bool', False), Page=('int', 0), Size=('int', 6), MixX=('int', 2), PrevDown=('bool', False), LastT=('double', 0.0), OpenAt=('double', 0.0),
            NextScan=('double', 0.0), NextKeeper=('double', 0.0), NextTroops=('double', 0.0), NextStrike=('double', 0.0), DefendCloseAt=('double', 0.0),
            MsgUntil=('double', 0.0), Msg=('string', ''), NoticeA=('double', 0.0), PrevDG=('double', 99999.0), NearCmdDist=('double', 99999.0),
            NearCommander=('bool', False), SoldNear=('bool', False), AnyGuard=('bool', False), OpenedForHero=('bool', False),
            NS=('int', 0), NX=('int', 0), AvS=('int', 0), AvX=('int', 0), InAura=('int', 0), TentN=('int', 0), CmdIdx=('int', 0), CmdAge=('int', 0),
            CmdName=('string', ''), LeadTag=('name', ''),
            Gate=('obj', P_GATE), WMgr=('obj', P_WM), Cmd=('actor', None), NearCmd=('actor', None), Pick=('actor', None), AttackV=('actor', None), AttackPick=('actor', None),
            Cmds=('actors', None), AllSold=('actors', None), Members=('actors', None), CandS=('actors', None), CandX=('actors', None), Known=('actors', None), Vit=('actors', None),
            StrokeMat=('material', None), StrokeMid=('mid', None), BustTex=('tex', None), Names=('strings', None), Ages=('ints', None), RankNames=('strings', None))
DATA = dict(Names=['Aldric Vane', 'Corwin Hale', 'Edmund Ashby', 'Godric Thorne', 'Roland Marsh', 'Tobias Wren', 'Oswin Crane', 'Bertrand Holt'],
            Ages=[41, 38, 52, 46, 34, 57, 44, 49], RankNames=['Recruit', 'Soldier', 'Veteran', 'Sergeant', 'Captain'])
json.dump(dict(vars=VARS, data=DATA), open(os.path.join(OUT, 'card_data.json'), 'w'), indent=1)
