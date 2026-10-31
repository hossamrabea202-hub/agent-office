# Tiny toast + skill-point reminder (adjustedfilm, 2026-10-31; owner W: #314, and the toast #313 uses).
#   "<blender python>" -I gen_toast.py -> BPC_Toast_graph.txt, NoticeHUD_ToastHook_graph.txt, manifest_noticehud_toast.json,
#                                         VARIABLES_BPVar.txt
# BPC_Toast (hero component "Toast"):
#   Toast(Text)        anyone calls it (GetPlayerPawn -> GetComponentByClass BPC_Toast -> Toast): a tiny line low on the
#                      screen, fade in 0.35 s, hold, fade out 0.6 s (ToastDur 3 s), faint dark backing. Real time, so it
#                      also shows while paused (e.g. in the barracks menu, #313).
#   RemindPoll (1 s)   unspent skill points = max(hero.Level - 1 - MPC_SkillTree.St.A, 0) (the skill tree's own formula).
#                      While > 0: 10 min of game time after they appear, and every 10 min after that, the toast says
#                      "Unspent skill points  ·  press T". Spending them all resets the clock. Game time = no reminders
#                      while paused or in a menu.
#   DrawToast(Hud, SizeX, SizeY)  called every frame by BP_NoticeHUD (the hook paste), draws over everything else.
# No self-calls to own events (the #254 lesson): RemindPoll sets the toast variables itself; timers call events by name.
import os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

COMP, HUDC, FONTC = CLS('ActorComponent'), CLS('HUD'), CLS('Font')
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC_SKILL = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
LEVEL_REF = 'VariableReference=(MemberParent=%s,MemberName="Level",MemberGuid=B91A6A184C00C166883230BED5E416AD)' % HERO
SELF = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Toast', 'BPC_Toast')
REMIND = 'Unspent skill points  -  press T'
P_CANNON, P_SOLDIER = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannon', '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
CANNON, SOLDIER = BPC(P_CANNON, 'BP_Cannon'), BPC(P_SOLDIER, 'BP_SoldierSword')
FULL_MSG = 'All cannons are mounted'
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)


class T(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def div(s, a, c, x, y, db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def loc(s, actor, x, y):
        return (s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'), 'ReturnValue')
    def count(s, node, x, y):
        n = s.name('Count')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.G.link(node, 'OutActors', n, 'TargetArray'); return (n, 'ReturnValue')
    def realnow(s, x, y): return (s.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], x, y, pure=True, tag='RealNow'), 'ReturnValue')
    def colr(s, r, g, b_, a, x, y, dr='1.0', dg='1.0', db_='1.0', da='1.0'):
        return s.math('MakeColor', [(fl('R', default=dr), r), (fl('G', default=dg), g), (fl('B', default=db_), b_), (fl('A', default=da), a)], st('ReturnValue', LC, out=True), x, y)
    def text(s, hud, txt, c, X, Y, scale, x, y):
        n = s.call(HUDC, 'DrawText', [S('Text'), st('TextColor', LC, default=col(1, 1, 1)), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT),
                   F('Scale', '1.0'), bo('bScalePosition', default='false')], x, y, target=hud, tag='Txt')
        for p, v in (('Text', txt), ('TextColor', c), ('ScreenX', X), ('ScreenY', Y), ('Scale', scale)): s.wire(v, n, p)
        return n
    def rect(s, hud, c, X, Y, W, H, x, y):
        n = s.call(HUDC, 'DrawRect', [st('RectColor', LC, default=col(0, 0, 0, 0.5)), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], x, y, target=hud, tag='Rect')
        for p, v in (('RectColor', c), ('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n


def write(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    names = [n[0] for n in G.nodes]
    if bad or len(names) != len(set(names)): raise SystemExit('%s: bad links %s / dup names' % (name, bad[:10]))
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (name, len(G.nodes), len(G.links)))


# ================================================================================================= BPC_Toast
G = Graph(); b = T(G, 'ts')
g = b.get
G.node('tsBeginPlay', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
tm = b.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default='RemindPoll'), fl('Time', default='1.0'), bo('bLooping', default='true'),
                                fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                st('ReturnValue', TIMERH, out=True)], 300, 0, tag='TimerRemind')
b.wire(b.self_node(100, 200), tm, 'Object'); G.link('tsBeginPlay', 'then', tm, 'execute')

# ---- Toast(Text): public
Y = 500
b.event('Toast', [S('Text')], 0, Y)
s1 = b.set('ToastText', S('v'), ('Toast', 'Text'), 300, Y); G.link('Toast', 'then', s1, 'execute')
s2 = b.set('ToastT0', D('v', default='0.0'), b.realnow(300, Y + 250), 600, Y); G.link(s1, 'then', s2, 'execute')

# ---- RemindPoll (1 s): unspent skill points reminder
Y = 1100
b.event('RemindPoll', [], 0, Y)
own = b.name('Owner'); callfn(G, own, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=100, y=Y + 300, self_hidden=True)
cast(G, 'tsAsHero', HERO, 'AsBP Third Person Character', 300, Y); b.wire((own, 'ReturnValue'), 'tsAsHero', 'Object'); G.link('RemindPoll', 'then', 'tsAsHero', 'execute')
st_ = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC_SKILL), N('ParameterName', 'St'), st('ReturnValue', LC, out=True)], 600, Y, tag='GetSt')
G.link('tsAsHero', 'then', st_, 'execute')
bk = b.name('BreakSt'); mathfn(G, bk, 'BreakColor', [st('InColor', LC)] + [fl(c, out=True, default='0.0') for c in 'RGBA'], 650, Y + 250); G.link(st_, 'ReturnValue', bk, 'InColor')
lv = b.name('GetLevel'); G.node(lv, 'K2Node_VariableGet', [LEVEL_REF], [it('Level', out=True, default='0'), selfpin(HERO)], 650, Y + 450)
G.link('tsAsHero', 'AsBP Third Person Character', lv, 'self')
pts = b.d2('FMax', b.d2('Subtract_DoubleDouble', b.i2d((lv, 'Level'), 850, Y + 450), (bk, 'A'), 1050, Y + 400, db='0.0'), None, 1250, Y + 400, db='0.0')
pts = b.sub(pts, None, 1450, Y + 400, db='1.0')            # Level - 1 - spent
now = b.now(1300, Y + 600)
nxt = lambda x, y: g('NextRemind', D('v', default='-1.0'), x, y)
b_has = b.branch(b.dcmp('Greater_DoubleDouble', pts, None, 1650, Y + 400, db='0.5'), 900, Y, tag='IfPoints')
G.link(st_, 'then', b_has, 'execute')
# no points: clock off
r0 = b.set('NextRemind', D('v', default='-1.0'), None, 1200, Y - 250); G.link(b_has, 'else', r0, 'execute')
# points: start the clock the first time, remind when due
b_arm = b.branch(b.dcmp('Less_DoubleDouble', nxt(1300, Y + 750), None, 1500, Y + 750, db='0.0'), 1200, Y, tag='IfArm'); G.link(b_has, 'then', b_arm, 'execute')
ra = b.set('NextRemind', D('v', default='-1.0'), b.add(now, g('RemindEvery', D('v', default='600.0'), 1500, Y + 900), 1700, Y + 850), 1500, Y - 150)
G.link(b_arm, 'then', ra, 'execute')
b_due = b.branch(b.dcmp('GreaterEqual_DoubleDouble', now, nxt(1700, Y + 1000), 1900, Y + 1000), 1500, Y + 150, tag='IfDue'); G.link(b_arm, 'else', b_due, 'execute')
t1 = b.set('ToastText', S('v', default=REMIND), None, 1800, Y + 150); G.link(b_due, 'then', t1, 'execute')
t2 = b.set('ToastT0', D('v', default='0.0'), b.realnow(1900, Y + 400), 2100, Y + 150); G.link(t1, 'then', t2, 'execute')
t3 = b.set('NextRemind', D('v', default='-1.0'), b.add(now, g('RemindEvery', D('v', default='600.0'), 2200, Y + 900), 2400, Y + 850), 2400, Y + 150)
G.link(t2, 'then', t3, 'execute')

# ---- CannonPoll (1 s, #313): CannonsFull = there is a cannon and every cannon is taken. A cannon is taken when the player
#      rides it (BP_Cannon.bMounted) or a soldier holds order 3 "Man a cannon" (Order.RelativeLocation.X = 3, the barracks
#      HUD's own code) with his Goal within CannonReach (5 m) of it. Nothing in the game stores this, so it is derived here.
Y = 2000
tm2 = b.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default='CannonPoll'), fl('Time', default='1.0'), bo('bLooping', default='true'),
                                 fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                 st('ReturnValue', TIMERH, out=True)], 600, 0, tag='TimerCannon')
b.wire(b.self_node(450, 200), tm2, 'Object'); G.link(tm, 'then', tm2, 'execute')
b.event('CannonPoll', [], 0, Y)
ga = lambda path, cls, x, y: b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
gcn = ga(P_CANNON, CANNON, 300, Y); G.link('CannonPoll', 'then', gcn, 'execute')
gsd = ga(P_SOLDIER, SOLDIER, 600, Y); G.link(gcn, 'then', gsd, 'execute')
sf = b.set('CnFull', bo('v', default='true'), None, 900, Y); G.link(gsd, 'then', sf, 'execute')
fc = b.name('ForCannon')
G.node(fc, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FOREACH, 'ResolvedWildcardType=(PinCategory="object",PinSubCategoryObject=%s)' % CANNON],
       [ex('Exec'), arr(ob('Array', CANNON)), ex('LoopBody', True), ob('Array Element', CANNON, out=True), it('Array Index', out=True), ex('Completed', True)], 1200, Y)
G.link(gcn, 'OutActors', fc, 'Array'); G.link(sf, 'then', fc, 'Exec')
can = (fc, 'Array Element')
st0 = b.set('CnTaken', BOOL, b.getm('bMounted', CANNON, BOOL, can, 1300, Y + 300), 1500, Y); G.link(fc, 'LoopBody', st0, 'execute')
fs = b.name('ForSoldier')
G.node(fs, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FOREACH, 'ResolvedWildcardType=(PinCategory="object",PinSubCategoryObject=%s)' % SOLDIER],
       [ex('Exec'), arr(ob('Array', SOLDIER)), ex('LoopBody', True), ob('Array Element', SOLDIER, out=True), it('Array Index', out=True), ex('Completed', True)], 1800, Y)
G.link(gsd, 'OutActors', fs, 'Array'); G.link(st0, 'then', fs, 'Exec')
sol = (fs, 'Array Element')
order = b.getm('Order', SOLDIER, ob('v', SCENE), sol, 1900, Y + 300)
goal = b.getm('Goal', SOLDIER, ob('v', SCENE), sol, 1900, Y + 500)
oloc = b.relloc(order, 2100, Y + 300); gloc = b.relloc(goal, 2100, Y + 500)
ox = b.brk(oloc, 2300, Y + 300)['X']
is3 = b.dcmp('Less_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), b.sub(ox, None, 2500, Y + 300, db='3.0'))], D('ReturnValue', out=True), 2700, Y + 300), None, 2900, Y + 300, db='0.5')
cl = b.loc(can, 2300, Y + 600)
near = b.dcmp('Less_DoubleDouble', b.math('Vector_Distance2D', [(V('V1'), gloc), (V('V2'), cl)], D('ReturnValue', out=True), 2500, Y + 550),
              g('CannonReach', D('v', default='500.0'), 2500, Y + 700), 2700, Y + 600)
tk = b.set('CnTaken', BOOL, b.b2('BooleanOR', g('CnTaken', BOOL, 2900, Y + 450), b.b2('BooleanAND', is3, near, 3100, Y + 500), 3300, Y + 450), 2200, Y)
G.link(fs, 'LoopBody', tk, 'execute')
sf2 = b.set('CnFull', BOOL, b.b2('BooleanAND', g('CnFull', BOOL, 2300, Y - 300), g('CnTaken', BOOL, 2300, Y - 200), 2500, Y - 250), 2200, Y - 450)
G.link(fs, 'Completed', sf2, 'execute')
anyc = b.icmp('Greater_IntInt', b.count(gcn, 3300, Y - 300), None, 3500, Y - 300, db='0')
sfin = b.set('CannonsFull', BOOL, b.b2('BooleanAND', g('CnFull', BOOL, 3300, Y - 150), anyc, 3700, Y - 200), 3400, Y - 450)
G.link(fc, 'Completed', sfin, 'execute')

# ---- DrawToast(Hud, SizeX, SizeY)
Y = 2600
b.event('DrawToast', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, Y)
hud = ('DrawToast', 'Hud')
age = b.sub(b.realnow(100, Y + 300), g('ToastT0', D('v', default='-100.0'), 100, Y + 450), 300, Y + 350)
dur = g('ToastDur', D('v', default='3.0'), 300, Y + 550)
on = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', age, dur, 500, Y + 450), b.dcmp('GreaterEqual_DoubleDouble', age, None, 500, Y + 600, db='0.0'), 700, Y + 500)
bon = b.branch(on, 300, Y, tag='IfToast'); G.link('DrawToast', 'then', bon, 'execute')
a = b.mul(b.sat(b.div(age, None, 700, Y + 700, db='0.35'), 900, Y + 700), b.sat(b.div(b.sub(dur, age, 700, Y + 850), None, 900, Y + 850, db='0.6'), 1100, Y + 850), 1300, Y + 750)
S_ = b.div(b.i2d(('DrawToast', 'SizeY'), 700, Y + 1000), None, 900, Y + 1000, db='1080.0')
u = lambda v, x, y: b.mul(S_, None, x, y, db=str(float(v)))
scale = u(0.26, 1100, Y + 1100)
txt = g('ToastText', S('v'), 1100, Y + 1250)
ts = b.call(HUDC, 'GetTextSize', [S('Text'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', '1.0')],
            1300, Y + 1200, target=hud, pure=True, const=True, tag='TxtSize')
b.wire(txt, ts, 'Text'); b.wire(scale, ts, 'Scale')
tw, th = (ts, 'OutWidth'), (ts, 'OutHeight')
X = b.sub(b.mul(b.i2d(('DrawToast', 'SizeX'), 1300, Y + 1400), None, 1500, Y + 1400, db='0.5'), b.mul(tw, None, 1500, Y + 1500, db='0.5'), 1700, Y + 1450)
Yt = b.mul(b.i2d(('DrawToast', 'SizeY'), 1300, Y + 1650), None, 1500, Y + 1650, db='0.80')
bg = b.rect(hud, b.colr(None, None, None, b.mul(a, None, 1900, Y + 1800, db='0.55'), 2100, Y + 1800, dr='0.02', dg='0.015', db_='0.01'),
            b.sub(X, u(16, 1900, Y + 1900), 2100, Y + 1900), b.sub(Yt, u(6, 1900, Y + 2000), 2100, Y + 2000),
            b.add(tw, u(32, 1900, Y + 2100), 2100, Y + 2100), b.add(th, u(12, 1900, Y + 2200), 2100, Y + 2200), 600, Y)
G.link(bon, 'then', bg, 'execute')
sh = b.text(hud, txt, b.colr(None, None, None, b.mul(a, None, 2300, Y + 2300, db='0.8'), 2500, Y + 2300, dr='0.0', dg='0.0', db_='0.0'),
            b.add(X, S_, 2300, Y + 2400), b.add(Yt, S_, 2300, Y + 2500), scale, 900, Y)
G.link(bg, 'then', sh, 'execute')
tx = b.text(hud, txt, b.colr(None, None, None, a, 2500, Y + 2600, dr='0.95', dg='0.88', db_='0.76'), X, Yt, scale, 1200, Y)
G.link(sh, 'then', tx, 'execute')
write(G, 'BPC_Toast_graph.txt')

# ================================================================================================= BP_NoticeHUD hook
G = Graph(); b = T(G, 'th')
sequence(G, 'ToastIn', 1, 0, 0)
sequence(G, 'ToastOut', 1, 1400, 0)
for p in ('SizeX', 'SizeY'):
    mathfn(G, 'ToastSize' + p[-1], 'Add_IntInt', [it('A', default='0'), it('B', default='0'), it('ReturnValue', out=True)], 600, 500 if p == 'SizeX' else 600)
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 250, pure=True, tag='Pawn')
gc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_Toast.BPC_Toast_C'), ob('ReturnValue', SELF, out=True)],
            250, 250, target=(pp, 'ReturnValue'), pure=True, const=True, tag='ToastComp')
ok = b.branch(b.valid((gc, 'ReturnValue'), 500, 300), 300, 0, tag='IfToastComp'); G.link('ToastIn', 'then_0', ok, 'execute')
dr = b.call(SELF, 'DrawToast', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 800, 0, target=(gc, 'ReturnValue'), tag='DrawToast')
b.wire(b.self_node(600, 350), dr, 'Hud'); G.link('ToastSizeX', 'ReturnValue', dr, 'SizeX'); G.link('ToastSizeY', 'ReturnValue', dr, 'SizeY')
G.link(ok, 'then', dr, 'execute'); G.link(dr, 'then', 'ToastOut', 'execute'); G.link(ok, 'else', 'ToastOut', 'execute')
write(G, 'NoticeHUD_ToastHook_graph.txt')
json.dump({'blueprint': 'BP_NoticeHUD',
           '_apply': 'after #307 (antidote: AntIn..AntOut). The toast draws after the antidote panel and before the #31 banner.',
           'pastes': ['NoticeHUD_ToastHook_graph.txt'],
           'rewires': [{'from': 'AntOut.then_0', 'to': 'ToastIn.execute', 'replace': True, 'note': 'was -> NoticeIn'},
                       {'from': 'ToastOut.then_0', 'to': 'NoticeIn.execute'},
                       {'from': 'CX_1.SizeX', 'to': 'ToastSizeX.A'}, {'from': 'CX_1.SizeY', 'to': 'ToastSizeY.A'}]},
          open(os.path.join(HERE, 'manifest_noticehud_toast.json'), 'w'), indent=1)


# ================================================================================================= BP_BarracksHUD (#313)
# Built on handoffs/exports/master/2026-10-30b/BP_BarracksHUD_EventGraph.txt ("Man a cannon" = order code 3):
#   click gate: CX_548.then (row clicked) -> CnIf: all cannons taken? -> Toast("All cannons are mounted"), no order, on to the
#               next row's test (CX_595) / otherwise the original handler (CX_549).
#   label:      CX_1321 (row colour) -> CnSel: dimmed to 45 % while all cannons are taken -> CX_1333.TextColor.
G = Graph(); b = T(G, 'cn')
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 300, pure=True, tag='Pawn')
gc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_Toast.BPC_Toast_C'), ob('ReturnValue', SELF, out=True)],
            250, 300, target=(pp, 'ReturnValue'), pure=True, const=True, tag='ToastComp')
full = b.b2('BooleanAND', b.valid((gc, 'ReturnValue'), 500, 300), b.getm('CannonsFull', SELF, BOOL, (gc, 'ReturnValue'), 500, 450), 700, 350)
branch(G, 'CnIf', 300, 0); b.wire(full, 'CnIf', 'Condition')
tc = b.call(SELF, 'Toast', [S('Text', default=FULL_MSG)], 700, -150, target=(gc, 'ReturnValue'), tag='ToastFull')
G.link('CnIf', 'then', tc, 'execute')
sequence(G, 'CnToNext', 1, 1000, -150); G.link(tc, 'then', 'CnToNext', 'execute')     # -> CX_595 (manifest)
sequence(G, 'CnToOrder', 1, 700, 150); G.link('CnIf', 'else', 'CnToOrder', 'execute')  # -> CX_549 (manifest)
# dimmed label colour
pp2 = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 700, pure=True, tag='Pawn')
gc2 = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_Toast.BPC_Toast_C'), ob('ReturnValue', SELF, out=True)],
             250, 700, target=(pp2, 'ReturnValue'), pure=True, const=True, tag='ToastComp')
full2 = b.b2('BooleanAND', b.valid((gc2, 'ReturnValue'), 500, 700), b.getm('CannonsFull', SELF, BOOL, (gc2, 'ReturnValue'), 500, 850), 700, 750)
mathfn(G, 'CnColIn', 'Multiply_LinearColorFloat', [st('A', LC, default=col(1, 1, 1)), fl('B', default='1.0'), st('ReturnValue', LC, out=True)], 600, 1000)
mathfn(G, 'CnDim', 'Multiply_LinearColorLinearColor', [st('A', LC, default=col(1, 1, 1)), st('B', LC, default=col(0.45, 0.45, 0.45, 1.0)), st('ReturnValue', LC, out=True)], 850, 1000)
G.link('CnColIn', 'ReturnValue', 'CnDim', 'A')
mathfn(G, 'CnSel', 'SelectColor', [st('A', LC, default=col(1, 1, 1)), st('B', LC, default=col(1, 1, 1)), bo('bPickA', default='false'), st('ReturnValue', LC, out=True)], 1100, 900)
G.link('CnDim', 'ReturnValue', 'CnSel', 'A'); G.link('CnColIn', 'ReturnValue', 'CnSel', 'B'); b.wire(full2, 'CnSel', 'bPickA')
write(G, 'BarracksHUD_CannonFull_graph.txt')
json.dump({'blueprint': 'BP_BarracksHUD',
           '_apply': 'after BPC_Toast exists (#314 setup + BPVars + graph). Built on the 10-30b export; on a fresh export check that the 6 live names still exist.',
           'pastes': ['BarracksHUD_CannonFull_graph.txt'],
           'rewires': [{'from': 'CX_548.then', 'to': 'CnIf.execute', 'replace': True, 'note': 'was -> CX_549 (Man a cannon handler)'},
                       {'from': 'CnToOrder.then_0', 'to': 'CX_549.execute'},
                       {'from': 'CnToNext.then_0', 'to': 'CX_595.execute'},
                       {'from': 'CX_1321.ReturnValue', 'to': 'CnColIn.A'},
                       {'from': 'CnSel.ReturnValue', 'to': 'CX_1333.TextColor', 'replace': True, 'note': 'was <- CX_1321'}]},
          open(os.path.join(HERE, 'manifest_barrackshud_cannonfull.json'), 'w'), indent=1)

# ================================================================================================= BPVar lines
VARS = [('ToastText', 'PinCategory="string"', ''), ('ToastT0', 'PinCategory="real",PinSubCategory="double"', '-100.0'),
        ('ToastDur', 'PinCategory="real",PinSubCategory="double"', '3.0'), ('NextRemind', 'PinCategory="real",PinSubCategory="double"', '-1.0'),
        ('RemindEvery', 'PinCategory="real",PinSubCategory="double"', '600.0'),
        ('CannonsFull', 'PinCategory="bool"', 'false'), ('CnFull', 'PinCategory="bool"', 'false'), ('CnTaken', 'PinCategory="bool"', 'false'),
        ('CannonReach', 'PinCategory="real",PinSubCategory="double"', '500.0')]
bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'toast314/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_Toast - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpv(*v) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
