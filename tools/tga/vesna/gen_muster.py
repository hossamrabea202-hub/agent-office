# The Muster (#359): the barracks screen, same kit as Vesna's Trade (#361). EventGraph of the NEW hero component BPC_Muster.
#   python gen_muster.py  ->  handoffs/barracks-hud-359/build/BPC_Muster_graph.txt  (+ the add-on events, hooks and manifests)
# DrawMuster(Hud, SizeX, SizeY) is called every frame from BP_ArmoryHUD (MusterSeq, before the #66 reveal):
#   Near  = the hero is within NearDist of BP_NPC_Barracks and Vesna's shop is closed. BP_BarracksHUD skips its old recruit
#           screen while Near (hook below), so E at the barracks opens this screen only.
#   E at the barracks opens it (game paused, cursor on); Esc closes it. Tabs RECRUIT / ARTILLERY / FORTIFY / SUPPLIES.
#   Every item's price / ore / state is refreshed each frame from the real systems, and a buy calls them (nothing copied):
#     swordsman / crossbowman / commander -> pays like the old screen, then BP_BarracksHUD.Enqueue(Kind) (#188 queue)
#     medic -> BPC_Medics.HudBuy   cannon -> BP_CannonOrder.HudOrder   walls / towers -> BPC_CastleUpgrades.HudBuyWalls/Towers
#     flares -> BPC_Flares.HudBuy      (the HudBuy events are 1-node add-ons that enter each system right after its key check)
# Helpers (Flow, X/Y/SZ geometry, sprite/cell/text) are gen_trade.py's, run here from its source so both screens stay one kit.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, 'gen_trade.py'), encoding='utf-8').read().split('\n')
def chunk(a, b_): return '\n'.join(SRC[a - 1:b_])
def find(prefix, start=1):
    for i, l in enumerate(SRC[start - 1:], start):
        if l.startswith(prefix): return i
    raise SystemExit('gen_trade.py changed: ' + prefix)
L_EV, L_GEO, L_DRAW, L_STATE = find('# ---------------------------------------------------------------- event + scale'), find('# geometry:'), \
    find('# ---------------------------------------------------------------- draw helpers'), find('# ---------------------------------------------------------------- shared state reads')
exec(chunk(1, L_EV - 1))                                   # imports, constants, value helpers, Flow
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'handoffs', 'barracks-hud-359', 'build'); os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(HERE, 'layout_mu.json'))); SC0, A = L['S'], L['atlas']
MUC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Muster', 'BPC_Muster')
BHUD = BPC('/Game/CastleDefender/Gameplay/Castle/BP_BarracksHUD', 'BP_BarracksHUD')
UPGC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_CastleUpgrades', 'BPC_CastleUpgrades')
FLAC = BPC('/Game/CastleDefender/Gameplay/Flares/BPC_Flares', 'BPC_Flares')
MEDC = BPC('/Game/CastleDefender/Gameplay/Medics/BPC_Medics', 'BPC_Medics')
YARDC = BPC('/Game/CastleDefender/Gameplay/Castle/BP_CannonOrder', 'BP_CannonOrder')
P_NPC = '/Game/CastleDefender/Characters/NPC/Barracks/BP_NPC_Barracks'
NPCC = BPC(P_NPC, 'BP_NPC_Barracks')
MPC_B = '/Game/CastleDefender/UI/Barracks/MPC_Barracks.MPC_Barracks'
STRV = S('v')

# ---------------------------------------------------------------- event, shop check, geometry, mouse (gen_trade's, renamed)
b.event('DrawMuster', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, 0)
hud = ('DrawMuster', 'Hud')
fl0 = Flow(('DrawMuster', 'then'))
mpcg = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', 'Shop'), st('ReturnValue', LC, out=True)], *P(), tag='GetShop')
fl0.go(mpcg)
brk = b.math('BreakColor', [(st('InColor', LC), (mpcg, 'ReturnValue'))], fl('R', out=True, default='0.0'), *P()); brkn = brk[0]
for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
SHOPOPEN = dcmp('Greater_DoubleDouble', (brkn, 'R'), 0.5)
exec(chunk(L_GEO, L_DRAW - 1).replace("'DrawTrade'", "'DrawMuster'"))
exec(chunk(L_DRAW, L_STATE - 1).replace("cls=TRADEC", "cls=MUC"))

def mpcb(param):
    n = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC_B), NAME_('ParameterName', param), st('ReturnValue', LC, out=True)], *P(), pure=True, tag='MPCB' + param)
    k_ = b.math('BreakColor', [(st('InColor', LC), (n, 'ReturnValue'))], fl('R', out=True, default='0.0'), *P())
    for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
    return {c_: (k_[0], c_) for c_ in 'RGBA'}
def rint(v): return rnd(v)
def d2i(v): return rnd(v)
def objv(cls): return ob('v', cls)

# ---------------------------------------------------------------- cached lookups (in the exec chain, once)
ownn = b.name('Owner'); callfn(G, ownn, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=P()[0], y=P()[1], self_hidden=True); OWNER = (ownn, 'ReturnValue')
def cache(fl_, var, cls, make):
    f1, f2 = fl_.iff(NOT(b.valid(get(var, objv(cls)), *P())), 'IfNo' + var)
    src = make(f1); setvar(f1, var, objv(cls), src)
    return f1.join(f2)
def find_actor(fl_, path, cls, tag):
    n = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], *P(), tag=tag); fl_.go(n); return (n, 'ReturnValue')
def find_comp(path, cls, tag):
    n = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, path + '.' + path.split('/')[-1] + '_C'), ob('ReturnValue', cls, out=True)],
               *P(), target=OWNER, pure=True, const=True, tag=tag); return (n, 'ReturnValue')
fl0 = cache(fl0, 'NPC', NPCC, lambda f: find_actor(f, P_NPC, NPCC, 'FindNPC'))
fl0 = cache(fl0, 'Yard', YARDC, lambda f: find_actor(f, '/Game/CastleDefender/Gameplay/Castle/BP_CannonOrder', YARDC, 'FindYard'))
fl0 = cache(fl0, 'Upg', UPGC, lambda f: find_comp('/Game/CastleDefender/Gameplay/Castle/BPC_CastleUpgrades', UPGC, 'FindUpg'))
fl0 = cache(fl0, 'Flares', FLAC, lambda f: find_comp('/Game/CastleDefender/Gameplay/Flares/BPC_Flares', FLAC, 'FindFlares'))
fl0 = cache(fl0, 'Medics', MEDC, lambda f: find_comp('/Game/CastleDefender/Gameplay/Medics/BPC_Medics', MEDC, 'FindMedics'))
# free cannon pads (in the exec chain, every frame the screen is open is cheap: a tag lookup)
NPCV, YARDV, UPGV, FLAV, MEDV = get('NPC', objv(NPCC)), get('Yard', objv(YARDC)), get('Upg', objv(UPGC)), get('Flares', objv(FLAC)), get('Medics', objv(MEDC))

# ---------------------------------------------------------------- near / open / close
dist = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), D('ReturnValue', out=True)], *P(), target=OWNER, pure=True, const=True, tag='DistNPC')
b.wire(get('NPC', objv(NPCC)), dist, 'OtherActor')
near = AND(AND(b.valid(get('NPC', objv(NPCC)), *P()), dcmp('Less_DoubleDouble', (dist, 'ReturnValue'), get('NearDist', DBL))), NOT(SHOPOPEN))
setvar(fl0, 'Near', BOOL, near)
fo_, fc_ = fl0.iff(get('Open', BOOL), 'IfOpen')
# closed: E at the barracks opens
fe, fne = fc_.iff(AND(get('Near', BOOL), anykey('E', 'Gamepad_FaceButton_Left')), 'IfOpenKey')
setvar(fe, 'Open', BOOL, None, 'true'); setvar(fe, 'OpenAt', DBL, NOW); setvar(fe, 'Tab', INT, None, '0'); setvar(fe, 'Sel', INT, None, '0')
fe.go(b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='true'), bo('ReturnValue', out=True, default='false')], *P(), tag='Pause'))
fe.go(b.setm('bShowMouseCursor', PCON, bo('v', default='true'), None, pc, *P()))
snd(fe, 'Swipe')
setvar(fne, 'Covering', BOOL, None, 'false')
# open: Esc (or B) closes
fx, fnx = fo_.iff(anykey('Escape', 'Gamepad_FaceButton_Right'), 'IfClose')
setvar(fx, 'Open', BOOL, None, 'false'); setvar(fx, 'Covering', BOOL, None, 'false')
fx.go(b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='false'), bo('ReturnValue', out=True, default='false')], *P(), tag='Unpause'))
fx.go(b.setm('bShowMouseCursor', PCON, BOOL, None, pc, *P()))
fm = fnx
setvar(fm, 'Covering', BOOL, None, 'true')

# ---------------------------------------------------------------- refresh: price / ores / state / notes of the 10 items
NI = len(L['items'])
cnt = mpcb('Cnt')                          # MPC_Barracks Cnt: R swordsmen, G crossbowmen, B commander, A army limit (BP_BarracksHUD)
armyn = b.math('Add_DoubleDouble', [(D('A', default='0.0'), cnt['R']), (D('B', default='0.0'), cnt['G'])], D('ReturnValue', out=True), *P())
full = dcmp('GreaterEqual_DoubleDouble', armyn, cnt['A'])
asbh = cast(G, 'AsBHud', BHUD, 'AsBP Barracks HUD', *P(), pure=True); b.wire(hud, 'AsBHud', 'Object'); BH = ('AsBHud', 'AsBP Barracks HUD')
rq = b.getm('RQ', BHUD, arr(INT), BH, *P())
rqn = b.math('Array_Length', [], it('ReturnValue', out=True), *P()) if False else None
rql = b.name('RQLen'); G.node(rql, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                             [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], *P())
b.wire(rq, rql, 'TargetArray'); RQN = (rql, 'ReturnValue')
qfull = icmp('GreaterEqual_IntInt', RQN, 3)
zh = cast(G, 'AsZHud', ZHUD, 'AsBP Zombie HUD', *P(), pure=True); b.wire(hud, 'AsZHud', 'Object'); ZH = ('AsZHud', 'AsBP Zombie HUD')
GOLD_ = b.getm('Gold', ZHUD, INT, ZH, *P())
ORE = b.getm('Ore', ZHUD, arr(INT), ZH, *P())
def ore(i):
    n = b.item(ORE, INT, None, *P()); G.nodes[-1][3][1]['default'] = str(i); return n
pads = b.lib(GS, 'GetAllActorsWithTag', [WC(), NAME_('Tag', 'CannonPad'), arr(ob('OutActors', ACT, out=True))], *P(), tag='FindPads'); fm.go(pads)
padl = b.name('PadLen'); G.node(padl, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                              [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], *P())
G.link(pads, 'OutActors', padl, 'TargetArray'); FREEPADS = (padl, 'ReturnValue')
setvar(fm, 'FreePads', INT, FREEPADS)
lvW = b.getm('Walls', UPGC, INT, get('Upg', objv(UPGC)), *P()); lvT = b.getm('Towers', UPGC, INT, get('Upg', objv(UPGC)), *P())
upg_ok, fla_ok, med_ok, yard_ok = (b.valid(get(v, objv(c)), *P()) for v, c in (('Upg', UPGC), ('Flares', FLAC), ('Medics', MEDC), ('Yard', YARDC)))
# per item: price, oreA idx/amount, oreB idx/amount, state (0 buy, 1 owned, 2 at best, 3 locked, 4 blocked), note, row line
def item_set(fl_, i, price, oa=(None, -1, 0), ob_=(None, -1, 0), state=0, note='', sub=''):
    def put(var, pin, v, lit=None):
        if isnum(v) or lit is not None:
            n = b.aset(var, pin, None, None, *P(), ditem=str(v) if lit is None else lit)
        else:
            n = b.aset(var, pin, None, v, *P())
        G.nodes[[q[0] for q in G.nodes].index(n)][3][[p['name'] for p in G.nodes[[q[0] for q in G.nodes].index(n)][3]].index('Index')]['default'] = str(i)
        fl_.go(n)
    put('IPrice', INT, price)
    put('IOreA', INT, oa[1] if oa[0] is None else oa[0]); put('IOreAN', INT, oa[2] if not isinstance(oa[2], tuple) else oa[2])
    put('IOreB', INT, ob_[1] if ob_[0] is None else ob_[0]); put('IOreBN', INT, ob_[2] if not isinstance(ob_[2], tuple) else ob_[2])
    put('IState', INT, state)
    put('INote', STRV, note if not isinstance(note, str) else None, lit=note if isinstance(note, str) else None)
    put('ISub', STRV, sub if not isinstance(sub, str) else None, lit=sub if isinstance(sub, str) else None)
pw = lambda base: rint(dop('Multiply_DoubleDouble', float(base), b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='1.25'), None), (D('Exp', default='0.0'), armyn)], D('ReturnValue', out=True), *P())))
armytxt = catn('ARMY  ', istr(rint(armyn)), ' / ', istr(rint(cnt['A'])))
recstate = seli(4, seli(4, 0, qfull), full)
recnote = sels('Army full - level up your hero', sels('Training queue is full (3)', '', qfull), full)
item_set(fm, 0, pw(40), state=recstate, note=recnote, sub=armytxt)
item_set(fm, 1, pw(60), state=recstate, note=recnote, sub=armytxt)
hascmd = dcmp('Greater_DoubleDouble', cnt['B'], 0.5)
item_set(fm, 2, 300, state=seli(1, seli(4, 0, qfull), hascmd), note=sels('You already have a Commander', sels('Training queue is full (3)', '', qfull), hascmd),
         sub=sels('IN SERVICE', 'ONE PER ARMY', hascmd))
mcount = b.getm('Count', MEDC, INT, MEDV, *P()); mmax = b.getm('MaxMedics', MEDC, INT, MEDV, *P())
mfull = icmp('GreaterEqual_IntInt', mcount, mmax)
item_set(fm, 3, b.getm('Price', MEDC, INT, MEDV, *P()), state=seli(seli(2, 0, mfull), 3, med_ok), note=sels(sels('All four medics serve you', '', mfull), 'Medics are not installed (#185)', med_ok),
         sub=catn('MEDICS  ', istr(mcount), ' / ', istr(mmax)))
item_set(fm, 4, 0, state=3, note='The workshop is not built yet (#50)', sub='IN TRAINING')
nopad = icmp('LessEqual_IntInt', get('FreePads', INT), 0)
item_set(fm, 5, b.getm('Price', YARDC, INT, YARDV, *P()), state=seli(seli(4, 0, nopad), 3, yard_ok),
         note=sels(sels('No free cannon pad on the walls', '', nopad), 'No artillery yard in this castle', yard_ok), sub=catn('FREE PADS  ', istr(get('FreePads', INT))))
for i, lv, costs in ((6, lvW, L['walls']), (7, lvT, L['towers'])):
    l0 = icmp('EqualEqual_IntInt', lv, 0)
    (g0, o0), (g1, o1) = costs
    k0, k1 = sorted(o0.items()), sorted(o1.items())
    oa = (seli(int(k0[0][0]), int(k1[0][0]), l0), 0, seli(k0[0][1], k1[0][1], l0))
    ob_ = (seli(int(k0[1][0]) if len(k0) > 1 else -1, int(k1[1][0]) if len(k1) > 1 else -1, l0), 0,
           seli(k0[1][1] if len(k0) > 1 else 0, k1[1][1] if len(k1) > 1 else 0, l0))
    top = icmp('GreaterEqual_IntInt', lv, 2)
    item_set(fm, i, seli(g0, g1, l0), oa, ob_, state=seli(seli(2, 0, top), 3, upg_ok), note=sels(sels('Already at their best', '', top), 'Castle upgrades are not installed (#224)', upg_ok),
             sub=catn('LEVEL  ', istr(lv), ' / 2'))
item_set(fm, 8, 0, state=3, note='Iron bands are forged by the smith (#208)', sub='AT THE FORGE')
fown = b.getm('Owned', FLAC, BOOL, FLAV, *P())
item_set(fm, 9, b.getm('Price', FLAC, INT, FLAV, *P()), state=seli(seli(1, 0, fown), 3, fla_ok), note=sels(sels('Your crossbowmen carry flares', '', fown), 'Flares are not installed (#277)', fla_ok),
         sub=sels('OWNED', 'ONE-TIME UPGRADE', fown))

# ---------------------------------------------------------------- input (screen open)
TS, TCN = [0, 5, 6, 9], [5, 1, 3, 1]                   # first item and item count per tab
def tabhit(i): t = L['tabs'][i]; return AND(CLICK, inside(t['x0'], L['tabbar']['y'], t['x1'] - t['x0'], L['tabbar']['h']))
def settab(fl_, v): (setvar(fl_, 'Tab', INT, None, str(v)) if isnum(v) else setvar(fl_, 'Tab', INT, v)); setvar(fl_, 'Sel', INT, None, '0'); snd(fl_, 'Swipe')
f1, f2 = fm.iff(anykey('Gamepad_LeftShoulder'), 'IfLB'); settab(f1, iop('Percent_IntInt', iop('Add_IntInt', get('Tab', INT), 3), 4)); fm = f1.join(f2)
f1, f2 = fm.iff(anykey('Gamepad_RightShoulder', 'Tab'), 'IfRB'); settab(f1, iop('Percent_IntInt', iop('Add_IntInt', get('Tab', INT), 1), 4)); fm = f1.join(f2)
for i in range(4):
    f1, f2 = fm.iff(tabhit(i), 'IfTab%d' % i); settab(f1, i); fm = f1.join(f2)
TABV = get('Tab', INT)
tstart = getarr('TabStart', INT, TABV); tcount = getarr('TabCount', INT, TABV)
clampsel = lambda v: b.math('Clamp', [(it('Value', default='0'), v), (it('Min', default='0'), None), (it('Max', default='0'), iop('Subtract_IntInt', getarr('TabCount', INT, get('Tab', INT)), 1))], it('ReturnValue', out=True), *P())
ar = L['arrows']
f1, f2 = fm.iff(OR(anykey('A', 'W', 'Up', 'Left', 'Gamepad_DPad_Up'), AND(CLICK, inside(ar['l'] - 22, ar['cy'] - 26, 44, 52))), 'IfPrev'); setvar(f1, 'Sel', INT, clampsel(iop('Subtract_IntInt', get('Sel', INT), 1))); snd(f1, 'Swipe'); fm = f1.join(f2)
f1, f2 = fm.iff(OR(anykey('D', 'S', 'Down', 'Right', 'Gamepad_DPad_Down'), AND(CLICK, inside(ar['r'] - 22, ar['cy'] - 26, 44, 52))), 'IfNext'); setvar(f1, 'Sel', INT, clampsel(iop('Add_IntInt', get('Sel', INT), 1))); snd(f1, 'Swipe'); fm = f1.join(f2)
R = L['rows']
for i in range(R['n']):
    f1, f2 = fm.iff(AND(AND(CLICK, inside(R['x'], R['y0'] + i * R['step'], R['w'], R['h'])), icmp('Less_IntInt', i, getarr('TabCount', INT, get('Tab', INT)))), 'IfRow%d' % i)
    setvar(f1, 'Sel', INT, None, str(i)); fm = f1.join(f2)
RT = L['rtabs']
f1, f2 = fm.iff(OR(key('Q'), AND(CLICK, inside(RT['eq'][0], RT['y'], RT['sp'][1] - RT['eq'][0], RT['h']))), 'IfRTab')
setvar(f1, 'RTab', INT, iop('Subtract_IntInt', 1, get('RTab', INT))); fm = f1.join(f2)
IDX = iop('Add_IntInt', getarr('TabStart', INT, get('Tab', INT)), get('Sel', INT))
ST_ = getarr('IState', INT, IDX); PR_ = getarr('IPrice', INT, IDX)
def orehave(idxsrc, nsrc):   # ore idx -1 = none
    none = icmp('Less_IntInt', idxsrc, 0)
    have = b.item(ORE, INT, b.math('Max', [(it('A', default='0'), idxsrc), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
    return OR(none, icmp('GreaterEqual_IntInt', have, nsrc))
AFF = AND(AND(icmp('GreaterEqual_IntInt', GOLD_, PR_), orehave(getarr('IOreA', INT, IDX), getarr('IOreAN', INT, IDX))),
          orehave(getarr('IOreB', INT, IDX), getarr('IOreBN', INT, IDX)))
BUYABLE = icmp('EqualEqual_IntInt', ST_, 0)
BU = L['buy']
act = AND(OR(anykey('E', 'Gamepad_FaceButton_Bottom'), AND(CLICK, inside(BU['x'], BU['y'], BU['w'], BU['h']))), dcmp('Greater_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('OpenAt', DBL)), 0.25))
fa, fna = fm.iff(act, 'IfAction')
fb_, fnb = fa.iff(BUYABLE, 'IfBuyable')
fg, fng = fb_.iff(AFF, 'IfAfford')
setvar(fng, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 1.5)); snd(fng, 'Fail')
snd(fnb, 'Fail')
# dispatch by item index
IDXV = IDX
def isidx(i): return icmp('EqualEqual_IntInt', IDXV, i)
fr_, frest = fg.iff(icmp('LessEqual_IntInt', IDXV, 2), 'IfRecruit')
fr_.go(b.setm('Gold', ZHUD, INT, iop('Subtract_IntInt', GOLD_, PR_), ZH, *P()))
enq = b.call(BHUD, 'Enqueue', [it('Kind', default='0')], *P(), target=BH, tag='CallEnqueue'); b.wire(IDXV, enq, 'Kind'); fr_.go(enq)
outs = [fr_]
for i, comp, ev in ((3, 'Medics', 'HudBuy'), (5, 'Yard', 'HudOrder'), (6, 'Upg', 'HudBuyWalls'), (7, 'Upg', 'HudBuyTowers'), (9, 'Flares', 'HudBuy')):
    cls = {'Medics': MEDC, 'Yard': YARDC, 'Upg': UPGC, 'Flares': FLAC}[comp]
    f1, frest = frest.iff(isidx(i), 'IfItem%d' % i)
    n = b.call(cls, ev, [], *P(), target=get(comp, objv(cls)), tag='Call' + ev); f1.go(n); outs.append(f1)
fdone = outs[0].join(*outs[1:])
setvar(fdone, 'FlashUntil', DBL, dop('Add_DoubleDouble', NOW, 0.6)); snd(fdone, 'Buy')
fm = fdone.join(frest, fng, fnb, fna)

# =====================================================================================================================
# DRAW
# =====================================================================================================================
fd = fm
rect(fd, 0, 0, L['TW'], L['TH'], col(0.02, 0.018, 0.016, 1.0), tag='BackFill')
PO = L['portrait']
sprite(fd, 'PortraitTex', PO['x'], PO['y'], PO['w'], PO['h'], (0.0, 0.0, 1.0, 1.0), tag='Portrait')
sprite(fd, 'FrameTex', 0, 0, L['TW'], L['TH'], (0.0, 0.0, 1.0, 1.0), tag='Frame')
tb = L['tabbar']
for i in range(4):
    t = L['tabs'][i]; r = A['tab%d' % i]
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', get('Tab', INT), i), 'IfTabOn%d' % i)
    sprite(f1, 'AtlasTex', (t['x0'] + t['x1']) / 2 - r['w'] / 2, tb['cy'] - r['h'] / 2, r['w'], r['h'], cell_uv('tab%d' % i), tag='TabOn%d' % i); fd = f1.join(f2)
PU = L['purse']
text(fd, group(GOLD_), PU['gold'][1], PU['cy'], 30, CREAM, tag='Gold')
text(fd, istr(ore(0)), PU['iron'][1], PU['cy'], 30, CREAM, tag='Iron')
text(fd, istr(ore(2)), PU['silver'][1], PU['cy'], 30, CREAM, tag='Silver')
LH = L['lhead']
text(fd, catn('(', istr(rint(armyn)), ' / ', istr(rint(cnt['A'])), ')'), 318, LH['cy'] + 1, 27, GOLD, tag='ArmyCount')
# rows of the current tab
lp = b.forloop(None, None, *P()); G.nodes[-1][3][2]['default'] = str(R['n'] - 1); fd.go(lp, out='Completed')
fr = Flow((lp, 'LoopBody')); ri = (lp, 'Index')
fin, _z = fr.iff(icmp('Less_IntInt', ri, getarr('TabCount', INT, get('Tab', INT))), 'IfRowUsed')
fr = fin
idx = iop('Add_IntInt', getarr('TabStart', INT, get('Tab', INT)), ri)
ry = dop('Add_DoubleDouble', float(R['y0']), dop('Multiply_DoubleDouble', i2d(ri), float(R['step'])))
rcy = dop('Add_DoubleDouble', ry, R['h'] / 2.0)
rst = getarr('IState', INT, idx)
locked = icmp('EqualEqual_IntInt', rst, 3)
fsel, fns = fr.iff(icmp('EqualEqual_IntInt', ri, get('Sel', INT)), 'IfRowSel')
rs = L['rsel']
sprite(fsel, 'AtlasTex', R['x'] + rs['dx'], dop('Add_DoubleDouble', ry, float(rs['dy'])), rs['w'], rs['h'], cell_uv('rsel'), tag='RowSel'); fr = fsel.join(fns)
ic = R['icon']; isz = 54
sprite(fr, 'AtlasTex', (ic[0] + ic[1]) / 2.0 - isz / 2.0, dop('Subtract_DoubleDouble', rcy, isz / 2.0), isz, isz, getarr('GlyphUV', LCV, idx), selc(col(.55, .52, .48), WHITE, locked), tag='RowGlyph')
nm = A['name_sword']
sprite(fr, 'AtlasTex', R['name'][0], dop('Add_DoubleDouble', ry, R['name'][1] - R['y0'] - nm['h'] / 2.0), nm['w'], nm['h'], getarr('NameUV', LCV, idx), selc(DIM, CREAM, locked), tag='RowName')
text(fr, getarr('ISub', STRV, idx), R['deff'][0], dop('Add_DoubleDouble', ry, R['deff'][1] - R['y0']), 19, DIM, tag='RowSub')
sx_ = R['state'][0]; sy_ = dop('Add_DoubleDouble', ry, R['state'][1] - R['y0'])
f0, fn0 = fr.iff(icmp('EqualEqual_IntInt', rst, 0), 'IfRowBuy')
rpr = catn(group(getarr('IPrice', INT, idx)), ' G')
text(f0, rpr, sx_, sy_, 25, selc(GOLD, RED, icmp('GreaterEqual_IntInt', GOLD_, getarr('IPrice', INT, idx))), anchor='r', tag='RowPrice')
mw = b.call(HUDC, 'GetTextSize', [S('Text'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='PriceW')
b.wire(rpr, mw, 'Text'); b.wire(tscale(25), mw, 'Scale')
sprite(f0, 'AtlasTex', dop('Subtract_DoubleDouble', dop('Subtract_DoubleDouble', float(sx_), dop('Divide_DoubleDouble', (mw, 'OutWidth'), T)), 30.0), dop('Subtract_DoubleDouble', sy_, 11.0), 22, 22, cell_uv('coin'), tag='RowCoin')
f1s, fn1 = fn0.iff(icmp('EqualEqual_IntInt', rst, 1), 'IfRowOwned'); cell(f1s, 'owned', sx_, sy_, anchor='r')
f2s, fn2 = fn1.iff(icmp('EqualEqual_IntInt', rst, 2), 'IfRowBest'); cell(f2s, 'maxed', sx_, sy_, anchor='r')
f3s, fn3 = fn2.iff(locked, 'IfRowLocked'); cell(f3s, 'locked', sx_, sy_, anchor='r')
text(fn3, 'FULL', sx_, sy_, 22, RED, anchor='r', tag='RowFull')

# centre
IT = L['ititle']; tw_ = A['title_sword']
sprite(fd, 'AtlasTex', IT['cx'] - tw_['w'] / 2, IT['y'] - tw_['h'] / 2, tw_['w'], tw_['h'], getarr('TitleUV', LCV, IDX), CREAM, tag='Title')
TG = L['tags']; tg = A['tag_sword']
sprite(fd, 'AtlasTex', TG['slot_cx'] - tg['w'] / 2, TG['y'] - tg['h'] / 2, tg['w'], tg['h'], getarr('TagUV', LCV, IDX), col(.80, .76, .68), tag='Tag')
cell(fd, 'setpiece', TG['piece_cx'], TG['y'], anchor='c')
TN = L['turn']
sprite(fd, 'AtlasTex', TN['cx'] - 100, TN['cy'] - 118, 200, 200, getarr('GlyphUV', LCV, IDX), selc(col(1, 1, 1, .45), WHITE, icmp('EqualEqual_IntInt', ST_, 3)), tag='BigGlyph')
fpp, fnpp = fd.iff(OR(isidx(6), isidx(7)), 'IfPips')
lvsel = seli(b.getm('Walls', UPGC, INT, get('Upg', objv(UPGC)), *P()), b.getm('Towers', UPGC, INT, get('Upg', objv(UPGC)), *P()), isidx(6))
for p_ in range(2):
    f1, f2 = fpp.iff(icmp('Greater_IntInt', lvsel, p_), 'IfPip%d' % p_)
    cell(f1, 'pip_on', TN['cx'] - 14 + p_ * 28, TN['cy'] + 110, anchor='c'); cell(f2, 'pip_off', TN['cx'] - 14 + p_ * 28, TN['cy'] + 110, anchor='c'); fpp = f1.join(f2)
fd = fpp.join(fnpp)
text(fd, getarr('ISub', STRV, IDX), TN['cx'], TN['cy'] + 136, 20, GOLD, anchor='c', tag='CentreSub')
# cost / treasury
CO = L['cost']
fcz, fncz = fd.iff(icmp('Greater_IntInt', PR_, 0), 'IfCost')
text(fcz, catn(group(PR_), ' G'), 616, 637, 32, selc(GREEN, RED, icmp('GreaterEqual_IntInt', GOLD_, PR_)), tag='CostGold')
fd = fcz.join(fncz)
ONAMES = b.get('OreNames', arr(STRV), *P())
def orestr(ia, na):
    nm_ = b.item(ONAMES, STRV, b.math('Max', [(it('A', default='0'), ia), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
    return sels('', catn(istr(na), ' ', nm_), icmp('Less_IntInt', ia, 0))
oline = catn(orestr(getarr('IOreA', INT, IDX), getarr('IOreAN', INT, IDX)), '   ', orestr(getarr('IOreB', INT, IDX), getarr('IOreBN', INT, IDX)))
text(fd, oline, 700, 637, 21, CREAM, tag='CostOre')
text(fd, catn(group(GOLD_), ' G'), 826, 637, 24, CREAM, tag='HaveGold')
def oreheld(ia):
    nm_ = b.item(ONAMES, STRV, b.math('Max', [(it('A', default='0'), ia), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
    have = b.item(ORE, INT, b.math('Max', [(it('A', default='0'), ia), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
    return sels('', catn(istr(have), ' ', nm_), icmp('Less_IntInt', ia, 0))
text(fd, catn(oreheld(getarr('IOreA', INT, IDX)), '   ', oreheld(getarr('IOreB', INT, IDX))), 945, 637, 21, DIM, tag='HaveOre')
# what it does: two description lines + the state note
BN = L['bonus']; dd = A['d1_sword']
sprite(fd, 'AtlasTex', 566, BN['lines'][0] - dd['h'] / 2, dd['w'], dd['h'], getarr('D1UV', LCV, IDX), col(.86, .82, .74), tag='Desc1')
sprite(fd, 'AtlasTex', 566, BN['lines'][1] - dd['h'] / 2, dd['w'], dd['h'], getarr('D2UV', LCV, IDX), col(.86, .82, .74), tag='Desc2')
text(fd, getarr('INote', STRV, IDX), 566, BN['lines'][2] + 2, 19, selc(GREEN, RED, icmp('EqualEqual_IntInt', ST_, 1)), tag='Note')
# button
ON_ = AND(BUYABLE, AFF)
fon, foff = fd.iff(ON_, 'IfBtnOn'); cell(fon, 'btn_on', BU['x'], BU['cy']); cell(foff, 'btn_off', BU['x'], BU['cy']); fd = fon.join(foff)
ffl, fnfl = fd.iff(dcmp('Greater_DoubleDouble', dop('Subtract_DoubleDouble', get('FlashUntil', DBL), NOW), 0.0), 'IfFlash')
rect(ffl, BU['x'], BU['y'], BU['w'], BU['h'], col(1.0, 0.9, 0.6, 0.35), tag='BuyFlash'); fd = ffl.join(fnfl)
cell(fd, 'key_e', BU['key'][0], BU['key'][1], anchor='c')
verb = getarr('IVerb', STRV, IDX)
lbl = catn(verb, ' FOR  ', group(PR_), ' G')
lbl = sels(lbl, sels('OWNED', sels('AT THEIR BEST', sels('LOCKED', 'NOT NOW', icmp('EqualEqual_IntInt', ST_, 3)), icmp('EqualEqual_IntInt', ST_, 2)), icmp('EqualEqual_IntInt', ST_, 1)), BUYABLE)
text(fd, lbl, BU['text'], BU['cy'], 28, selc(col(.10, .07, .03), CREAM, ON_), tag='BuyLabel')
fmsg, fnmsg = fd.iff(dcmp('Less_DoubleDouble', NOW, get('MsgUntil', DBL)), 'IfNoGold')
cell(fmsg, 'nogold', BU['x'] + BU['w'] / 2, BU['y'] - 14, RED, anchor='c'); fd = fmsg.join(fnmsg)

# right: GARRISON / CASTLE
for i, kk in enumerate(('rtab0', 'rtab1')):
    x0 = (RT['eq'] if i == 0 else RT['sp'])[0]; r = A[kk]
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', get('RTab', INT), i), 'IfRTabOn%d' % i)
    sprite(f1, 'AtlasTex', x0, RT['y'], r['w'], r['h'], cell_uv(kk), tag='RTabOn%d' % i); fd = f1.join(f2)
GA = L['garrison']
fg0, fg1 = fd.iff(icmp('EqualEqual_IntInt', get('RTab', INT), 0), 'IfGarrison')
rows_g = [('Swordsmen', istr(rint(cnt['R'])), 'glyph_sword'), ('Crossbowmen', istr(rint(cnt['G'])), 'glyph_xbow'),
          ('Commander', sels('IN SERVICE', '-', hascmd), 'glyph_banner'), ('Medics', catn(istr(mcount), ' / ', istr(mmax)), 'glyph_medic'),
          ('Army', catn(istr(rint(armyn)), ' / ', istr(rint(cnt['A']))), 'glyph_sword')]
for k_, (lab, val, gl) in enumerate(rows_g):
    y_ = GA['y0'] + k_ * GA['step']
    sprite(fg0, 'AtlasTex', GA['icon'] - 14, y_ - 14, 28, 28, cell_uv(gl), col(.85, .72, .45), tag='GIcon')
    text(fg0, lab.upper(), GA['label'], y_, 21, CREAM, tag='GLabel'); text(fg0, val, GA['val'], y_, 24, GOLD, anchor='r', tag='GVal')
QU = L['queue']
text(fg0, 'IN TRAINING', GA['label'], QU['y'] - 30, 20, DIM, tag='QLabel')
for q in range(3):
    x_ = QU['x0'] + q * QU['step']
    cell(fg0, 'qslot', x_, QU['y'] + QU['h'] / 2)
    f1, f2 = fg0.iff(icmp('Greater_IntInt', RQN, q), 'IfQ%d' % q)
    kind = b.item(rq, INT, None, *P()); G.nodes[-1][3][1]['default'] = str(q)
    sprite(f1, 'AtlasTex', x_ + QU['w'] / 2 - 26, QU['y'] + 6, 52, 52, getarr('KindUV', LCV, kind), WHITE, tag='QGlyph')
    if q == 0:
        gt = b.lib(GS, 'GetTimeSeconds', [WC(), D('ReturnValue', out=True)], *P(), pure=True, tag='GameNow')
        prog = b.math('FClamp', [(D('Value', default='0.0'), dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', (gt, 'ReturnValue'), b.getm('RQStart', BHUD, fl('v', default='0.0'), BH, *P())),
                       b.math('FMax', [(D('A', default='0.0'), b.getm('RQDur', BHUD, fl('v', default='0.0'), BH, *P())), (D('B', default='0.1'), None)], D('ReturnValue', out=True), *P()))),
                      (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), *P())
        rect(f1, x_ + 4, QU['y'] + QU['h'] - 7, dop('Multiply_DoubleDouble', prog, float(QU['w'] - 8)), 4, col(.94, .78, .45, .95), tag='QBar')
    fg0 = f1.join(f2)
rows_c = [('Walls', catn('LEVEL ', istr(lvW), ' / 2'), 'glyph_wall'), ('Towers', catn('LEVEL ', istr(lvT), ' / 2'), 'glyph_tower'),
          ('Flares', sels('OWNED', '-', fown), 'glyph_flare'), ('Cannon pads free', istr(get('FreePads', INT)), 'glyph_cannon'), ('Gate', 'AT THE FORGE', 'glyph_gate')]
for k_, (lab, val, gl) in enumerate(rows_c):
    y_ = GA['y0'] + k_ * GA['step']
    sprite(fg1, 'AtlasTex', GA['icon'] - 14, y_ - 14, 28, 28, cell_uv(gl), col(.85, .72, .45), tag='CIcon')
    text(fg1, lab.upper(), GA['label'], y_, 21, CREAM, tag='CLabel'); text(fg1, val, GA['val'], y_, 24, GOLD, anchor='r', tag='CVal')
fd = fg0.join(fg1)
# treasury (stats box): the four ores
STB = L['stats']
for k_ in range(4):
    text(fd, istr(ore(k_)), STB['val'], STB['rows'][k_], 25, CREAM, tag='Ore%d' % k_)

# ---------------------------------------------------------------- self-check + write
names = [n[0] for n in G.nodes]
assert len(names) == len(set(names)), 'duplicate node names'
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
outs_ = {(n[0], p['name']) for n in G.nodes for p in n[3] if p.get('out')}
wrong = [l for l in G.links if (l[0], l[1]) not in outs_ or (l[2], l[3]) in outs_]
if wrong: raise SystemExit('direction: %s' % wrong[:10])
open(os.path.join(OUT, 'BPC_Muster_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_Muster: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---------------------------------------------------------------- variables + defaults (read by setup_muster_ue.py)
items = L['items']
uv = lambda k_: cell_uv(k_)
VARS = dict(Tab=('int', 0), RTab=('int', 0), Sel=('int', 0), Open=('bool', False), Near=('bool', False), Covering=('bool', False),
            OpenAt=('double', 0.0), MsgUntil=('double', 0.0), FlashUntil=('double', 0.0), NearDist=('double', 450.0), FreePads=('int', 0))
DATA = dict(TabStart=TS, TabCount=TCN, IVerb=['RECRUIT', 'RECRUIT', 'RECRUIT', 'RECRUIT', 'TRAIN', 'ORDER', 'BUILD', 'BUILD', 'FORGE', 'BUY'],
            OreNames=L['ores'], IPrice=[0] * NI, IOreA=[-1] * NI, IOreAN=[0] * NI, IOreB=[-1] * NI, IOreBN=[0] * NI, IState=[3] * NI, INote=[''] * NI, ISub=[''] * NI,
            NameUV=[uv('name_' + i['key']) for i in items], TitleUV=[uv('title_' + i['key']) for i in items], TagUV=[uv('tag_' + i['key']) for i in items],
            D1UV=[uv('d1_' + i['key']) for i in items], D2UV=[uv('d2_' + i['key']) for i in items], GlyphUV=[uv('glyph_' + i['glyph']) for i in items],
            KindUV=[uv('glyph_sword'), uv('glyph_xbow'), uv('glyph_banner')])
json.dump(dict(vars=VARS, data=DATA), open(os.path.join(OUT, 'muster_data.json'), 'w'), indent=1)
print('muster_data.json: %d items' % NI)
