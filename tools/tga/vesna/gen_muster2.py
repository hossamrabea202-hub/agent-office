# The Muster v2 (#420): the owner rejected v1 in Play (clicks barely respond, too many panels, line glyphs instead of soldier
# portraits, "E NOT NOW" because the army read 0 / 0). Same component (BPC_Muster), same event DrawMuster(Hud, SizeX, SizeY),
# same systems and buys as v1 (gen_muster.py, whose refresh part is run here with the fixes below); new input and draw.
#   python gen_muster2.py -> handoffs/muster-v2-420/build/BPC_Muster_graph.txt + muster_data.json
# Fixes:
#   clicks  : v1 used WasInputKeyJustPressed(LMB) with the input mode left at Game Only, so the viewport captured the mouse
#             on press and many clicks never reached the screen. v2 switches to Game And UI (no lock, cursor kept) while
#             open, and makes its own press edge from IsInputKeyDown (PrevDown), so a click is seen on the frame it lands.
#             Every card, its button, the tabs and CLOSE are hit-tested on exactly the rect that is drawn (same X/Y/SZ).
#   army    : v1 read MPC_Barracks Cnt.A as the cap, but BP_BarracksHUD writes a timestamp there (and only on a recruit).
#             The old screen's rule is: army = BP_SoldierSword actors + Que.R (in training), cap = 2 x hero Level + 4.
#   words   : no "NOT NOW": the button says why (ARMY FULL, QUEUE FULL, NO FREE PAD...) and the card says what to do.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, 'gen_muster.py'), encoding='utf-8').read()
CUT = '# ---------------------------------------------------------------- input (screen open)'
head = SRC[:SRC.index(CUT)]
REPL = [
    ("L = json.load(open(os.path.join(HERE, 'layout_mu.json')))", "L = json.load(open(os.path.join(HERE, 'layout_mu2.json')))"),
    ("OUT = os.path.join(REPO, 'handoffs', 'barracks-hud-359', 'build')", "OUT = os.path.join(REPO, 'handoffs', 'muster-v2-420', 'build')"),
    # open: Game And UI input + no click carried in; close: Game Only again
    ("fe.go(b.setm('bShowMouseCursor', PCON, bo('v', default='true'), None, pc, *P()))",
     "fe.go(b.setm('bShowMouseCursor', PCON, bo('v', default='true'), None, pc, *P())); fe.go(input_mode(True)); setvar(fe, 'PrevDown', BOOL, None, 'true')"),
    ("fx.go(b.setm('bShowMouseCursor', PCON, BOOL, None, pc, *P()))", "fx.go(b.setm('bShowMouseCursor', PCON, BOOL, None, pc, *P())); fx.go(input_mode(False))"),
    ("fx, fnx = fo_.iff(anykey('Escape', 'Gamepad_FaceButton_Right'), 'IfClose')",
     "fx, fnx = fo_.iff(OR(anykey('Escape', 'Gamepad_FaceButton_Right', 'BackSpace'), AND(PRESS, inside(CL['x'], CL['y'], CL['w'], CL['h']))), 'IfClose')"),
    # army and cap: the old screen's rule (BP_BarracksHUD 10-30b: CX_3003..CX_3114)
    ("armyn = b.math('Add_DoubleDouble', [(D('A', default='0.0'), cnt['R']), (D('B', default='0.0'), cnt['G'])], D('ReturnValue', out=True), *P())\nfull = dcmp('GreaterEqual_DoubleDouble', armyn, cnt['A'])",
     "armyp = b.math('Add_DoubleDouble', [(D('A', default='0.0'), cnt['R']), (D('B', default='0.0'), cnt['G'])], D('ReturnValue', out=True), *P())\n"
     "armyn, capn = army_and_cap(fm)\nfull = dcmp('GreaterEqual_DoubleDouble', armyn, capn)"),
    ("(D('Exp', default='0.0'), armyn)", "(D('Exp', default='0.0'), armyp)"),
    ("armytxt = catn('ARMY  ', istr(rint(armyn)), ' / ', istr(rint(cnt['A'])))", "armytxt = catn('ARMY  ', istr(rint(armyn)), ' / ', istr(rint(capn)))"),
    ("recnote = sels('Army full - level up your hero', sels('Training queue is full (3)', '', qfull), full)",
     "recnote = sels('Army full: level up to recruit more', sels('Training queue is full (3 / 3)', '', qfull), full)\nreclbl = sels('ARMY FULL', 'QUEUE FULL', full)"),
    ("def item_set(fl_, i, price, oa=(None, -1, 0), ob_=(None, -1, 0), state=0, note='', sub=''):", "def item_set(fl_, i, price, oa=(None, -1, 0), ob_=(None, -1, 0), state=0, note='', sub='', label='NOT AVAILABLE'):"),
    ("    put('ISub', STRV, sub if not isinstance(sub, str) else None, lit=sub if isinstance(sub, str) else None)",
     "    put('ISub', STRV, sub if not isinstance(sub, str) else None, lit=sub if isinstance(sub, str) else None)\n"
     "    put('IBlock', STRV, label if not isinstance(label, str) else None, lit=label if isinstance(label, str) else None)"),
    ("item_set(fm, 0, pw(40), state=recstate, note=recnote, sub=armytxt)", "item_set(fm, 0, pw(40), state=recstate, note=recnote, sub=armytxt, label=reclbl)"),
    ("item_set(fm, 1, pw(60), state=recstate, note=recnote, sub=armytxt)", "item_set(fm, 1, pw(60), state=recstate, note=recnote, sub=armytxt, label=reclbl)"),
    ("sub=sels('IN SERVICE', 'ONE PER ARMY', hascmd))", "sub=sels('IN SERVICE', 'ONE PER ARMY', hascmd), label='QUEUE FULL')"),
    ("sub=catn('FREE PADS  ', istr(get('FreePads', INT))))", "sub=catn('FREE PADS  ', istr(get('FreePads', INT))), label='NO FREE PAD')"),
]
for a_, b_ in REPL:
    if a_ not in head: raise SystemExit('gen_muster.py changed: ' + a_[:80])
    head = head.replace(a_, b_)

def input_mode(gameui):
    if gameui:
        n = b.lib(UMG('WidgetBlueprintLibrary'), 'SetInputMode_GameAndUIEx', [ob('PlayerController', PCON), ob('InWidgetToFocus', UMG('Widget')),
                  {'name': 'InMouseLockMode', 'cat': 'byte', 'obj': ENUM('EMouseLockMode'), 'default': 'DoNotLock'},
                  bo('bHideCursorDuringCapture', default='false'), dict(bo('bFlushInput', default='false'), advanced=True)], *P(), tag='InputGameUI')
    else:
        n = b.lib(UMG('WidgetBlueprintLibrary'), 'SetInputMode_GameOnly', [ob('PlayerController', PCON), dict(bo('bFlushInput', default='false'), advanced=True)], *P(), tag='InputGame')
    b.wire(pc, n, 'PlayerController'); return n

def army_and_cap(fl_):
    sold = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SOLDIER)), arr(ob('OutActors', ACT, out=True))], *P(), tag='FindSoldiers'); fl_.go(sold)
    sl = b.name('SoldLen'); G.node(sl, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                                  [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], *P())
    G.link(sold, 'OutActors', sl, 'TargetArray')
    que = mpcb('Que')
    army = dop('Add_DoubleDouble', i2d((sl, 'ReturnValue')), que['R'])
    cast(G, 'AsHero', HEROC, 'AsBP Third Person Character', *P(), pure=True); b.wire(OWNER, 'AsHero', 'Object')
    lvl = b.getm('Level', HEROC, INT, ('AsHero', 'AsBP Third Person Character'), *P())
    cap = dop('Add_DoubleDouble', dop('Multiply_DoubleDouble', i2d(lvl), 2.0), 4.0)
    return army, cap

HEROC = None
_pre = head.index('# ---------------------------------------------------------------- event, shop check')
exec(head[:_pre])
HEROC = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
CL, CA = L['close'], L['card']
# the press edge has to exist before the close / open branches use it: built lazily on first use
_press = {}
def _mk_press():
    if not _press:
        _press['down'] = key('LeftMouseButton', down=True)
        _press['p'] = AND(_press['down'], NOT(get('PrevDown', BOOL)))
    return _press['p']
exec(head[_pre:].replace("exec(chunk(L_DRAW, L_STATE - 1).replace(\"cls=TRADEC\", \"cls=MUC\"))",
                         "exec(chunk(L_DRAW, L_STATE - 1).replace(\"cls=TRADEC\", \"cls=MUC\"))\nPRESS = _mk_press(); LDOWN = _press['down']"))
assert 'PRESS' in globals()

# ---------------------------------------------------------------- input (screen open)
TS, TCN = [0, 5, 6, 9], [5, 1, 3, 1]                   # first item and item count per tab
X0 = [round(L['TW'] / 2 - (n * CA['w'] + (n - 1) * (CA['step'] - CA['w'])) / 2) for n in TCN]   # first card x per tab
setvar(fm, 'WantAct', BOOL, None, 'false')
def settab(fl_, v): (setvar(fl_, 'Tab', INT, None, str(v)) if isnum(v) else setvar(fl_, 'Tab', INT, v)); setvar(fl_, 'Sel', INT, None, '0'); snd(fl_, 'Swipe')
f1, f2 = fm.iff(anykey('Gamepad_LeftShoulder'), 'IfLB'); settab(f1, iop('Percent_IntInt', iop('Add_IntInt', get('Tab', INT), 3), 4)); fm = f1.join(f2)
f1, f2 = fm.iff(anykey('Gamepad_RightShoulder', 'Tab'), 'IfRB'); settab(f1, iop('Percent_IntInt', iop('Add_IntInt', get('Tab', INT), 1), 4)); fm = f1.join(f2)
TB = L['tabs']
def tabover(i): return inside(TB[i]['x'], TB[i]['y'], TB[i]['w'], TB[i]['h'])
for i, kn in enumerate(('One', 'Two', 'Three', 'Four')):
    f1, f2 = fm.iff(AND(OR(key(kn), AND(PRESS, tabover(i))), icmp('NotEqual_IntInt', get('Tab', INT), i)), 'IfTab%d' % i); settab(f1, i); fm = f1.join(f2)
TABV = get('Tab', INT)
CNT_ = getarr('TabCount', INT, TABV)
clampsel = lambda v: b.math('Clamp', [(it('Value', default='0'), v), (it('Min', default='0'), None), (it('Max', default='0'), iop('Subtract_IntInt', getarr('TabCount', INT, get('Tab', INT)), 1))], it('ReturnValue', out=True), *P())
f1, f2 = fm.iff(anykey('A', 'Left', 'Gamepad_DPad_Left'), 'IfPrev'); setvar(f1, 'Sel', INT, clampsel(iop('Subtract_IntInt', get('Sel', INT), 1))); snd(f1, 'Swipe'); fm = f1.join(f2)
f1, f2 = fm.iff(anykey('D', 'Right', 'Gamepad_DPad_Right'), 'IfNext'); setvar(f1, 'Sel', INT, clampsel(iop('Add_IntInt', get('Sel', INT), 1))); snd(f1, 'Swipe'); fm = f1.join(f2)
CX0 = getarr('CardX0', INT, TABV)
def cardx(k): return dop('Add_DoubleDouble', i2d(CX0), float(k * CA['step'])) if isnum(k) else dop('Add_DoubleDouble', i2d(CX0), dop('Multiply_DoubleDouble', i2d(k), float(CA['step'])))
BT = CA['btn']
def cardover(k): return inside(cardx(k), CA['y'], CA['w'], CA['h'])
def btnover(k): return inside(dop('Add_DoubleDouble', cardx(k), float(BT['dx'])), CA['y'] + BT['dy'], BT['w'], BT['h'])
for k in range(5):
    f1, f2 = fm.iff(AND(AND(PRESS, cardover(k)), icmp('Less_IntInt', k, CNT_)), 'IfCard%d' % k)
    # double-click = same card again within 0.35 s; a press on the card's own button buys at once
    dbl = AND(icmp('EqualEqual_IntInt', get('LastCard', INT), k), dcmp('Less_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('LastClickAt', DBL)), 0.35))
    g1, g2 = f1.iff(OR(dbl, btnover(k)), 'IfCardAct%d' % k); setvar(g1, 'WantAct', BOOL, None, 'true'); f1 = g1.join(g2)
    s1, s2 = f1.iff(icmp('NotEqual_IntInt', get('Sel', INT), k), 'IfCardNew%d' % k); snd(s1, 'Swipe'); f1 = s1.join(s2)
    setvar(f1, 'Sel', INT, None, str(k)); setvar(f1, 'LastCard', INT, None, str(k)); setvar(f1, 'LastClickAt', DBL, NOW)
    fm = f1.join(f2)
setvar(fm, 'PrevDown', BOOL, LDOWN)                    # the press edge for the next frame
IDX = iop('Add_IntInt', getarr('TabStart', INT, get('Tab', INT)), get('Sel', INT))
ST_ = getarr('IState', INT, IDX); PR_ = getarr('IPrice', INT, IDX)
def orehave(idxsrc, nsrc):   # ore idx -1 = none
    none = icmp('Less_IntInt', idxsrc, 0)
    have = b.item(ORE, INT, b.math('Max', [(it('A', default='0'), idxsrc), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
    return OR(none, icmp('GreaterEqual_IntInt', have, nsrc))
def afford(ix): return AND(AND(icmp('GreaterEqual_IntInt', GOLD_, getarr('IPrice', INT, ix)), orehave(getarr('IOreA', INT, ix), getarr('IOreAN', INT, ix))),
                           orehave(getarr('IOreB', INT, ix), getarr('IOreBN', INT, ix)))
AFF = afford(IDX)
BUYABLE = icmp('EqualEqual_IntInt', ST_, 0)
act = AND(OR(anykey('E', 'Enter', 'Gamepad_FaceButton_Bottom'), get('WantAct', BOOL)), dcmp('Greater_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('OpenAt', DBL)), 0.25))
fa, fna = fm.iff(act, 'IfAction')
setvar(fa, 'LastCard', INT, None, '-1')                # a third click is a new double-click, not a second buy
fb_, fnb = fa.iff(BUYABLE, 'IfBuyable')
fg, fng = fb_.iff(AFF, 'IfAfford')
setvar(fng, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 1.8)); setvar(fng, 'ShakeAt', DBL, NOW); snd(fng, 'Fail')
setvar(fnb, 'ShakeAt', DBL, NOW); snd(fnb, 'Fail')
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
# DRAW (T_MU2_Frame + T_MU2_Atlas cells + Cinzel numbers; every rect below is the one hit-tested above)
# =====================================================================================================================
fd = fm
rect(fd, 0, 0, L['TW'], L['TH'], col(0.02, 0.018, 0.016, 1.0), tag='BackFill')
sprite(fd, 'FrameTex', 0, 0, L['TW'], L['TH'], (0.0, 0.0, 1.0, 1.0), tag='Frame')
for i in range(4):
    t = TB[i]
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', get('Tab', INT), i), 'IfTabOn%d' % i); cell(f1, 'tab_on', t['x'], t['y'] + t['h'] / 2)
    h1, h2 = f2.iff(tabover(i), 'IfTabHover%d' % i); cell(h1, 'tab_hover', t['x'], t['y'] + t['h'] / 2); fd = f1.join(h1, h2)
fcl, fncl = fd.iff(inside(CL['x'], CL['y'], CL['w'], CL['h']), 'IfCloseHover'); cell(fcl, 'close_hover', CL['x'], CL['y'] + CL['h'] / 2); fd = fcl.join(fncl)
PU = L['purse']; pcy = PU['y'] + PU['h'] / 2
text(fd, group(GOLD_), PU['x'] + 50, pcy, 22, CREAM, tag='Gold')
text(fd, istr(ore(0)), PU['x'] + 188, pcy, 22, CREAM, tag='Iron')
text(fd, istr(ore(2)), PU['x'] + 286, pcy, 22, CREAM, tag='Silver')
# cards of the current tab
lp = b.forloop(None, None, *P()); G.nodes[-1][3][2]['default'] = '4'; fd.go(lp, out='Completed')
fr = Flow((lp, 'LoopBody')); ri = (lp, 'Index')
fin, _z = fr.iff(icmp('Less_IntInt', ri, CNT_), 'IfCardUsed'); fr = fin
idx = iop('Add_IntInt', getarr('TabStart', INT, get('Tab', INT)), ri)
isSel = icmp('EqualEqual_IntInt', ri, get('Sel', INT))
# the selected card's button shakes 0.3 s after a refused buy
shk = dop('Multiply_DoubleDouble', b.math('Sin', [(D('A', default='0.0'), dop('Multiply_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('ShakeAt', DBL)), 70.0))], D('ReturnValue', out=True), *P()),
          seld(6.0, 0.0, AND(isSel, dcmp('Less_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('ShakeAt', DBL)), 0.3))))
cx = cardx(ri); cy0 = CA['y']
ccx = dop('Add_DoubleDouble', cx, CA['w'] / 2.0)
cell(fr, 'card_bg', cx, cy0 + CA['h'] / 2, tag='CardBg')
PO = CA['por']; pox = dop('Add_DoubleDouble', cx, float(PO['dx']))
bust = b.item(b.get('BustTex', arr(ob('v', TEX2D)), *P()), ob('v', TEX2D), idx, *P())
fbu, fnbu = fr.iff(b.valid(bust, *P()), 'IfBust')
sprite(fbu, bust, pox, cy0 + PO['dy'], PO['w'], PO['h'], (0.0, 0.0, 1.0, 1.0), tag='Bust')
sprite(fnbu, 'AtlasTex', dop('Subtract_DoubleDouble', ccx, 100.0), cy0 + PO['dy'] + PO['h'] / 2 - 100, 200, 200, getarr('MedUV', LCV, idx),
       selc(col(.6, .58, .55), WHITE, icmp('EqualEqual_IntInt', getarr('IState', INT, idx), 3)), tag='Medal')
fr = fbu.join(fnbu)
cell(fr, 'vignette', pox, cy0 + PO['dy'] + PO['h'] / 2, tag='Vignette')
rst = getarr('IState', INT, idx); locked = icmp('EqualEqual_IntInt', rst, 3)
nm = A['name_sword']; tg = A['tag_sword']; dd = A['d1_sword']
sprite(fr, 'AtlasTex', dop('Add_DoubleDouble', cx, 10.0), cy0 + CA['name'] - nm['h'] / 2, nm['w'], nm['h'], getarr('NameUV', LCV, idx), selc(DIM, WHITE, locked), tag='CardName')
sprite(fr, 'AtlasTex', dop('Add_DoubleDouble', cx, 10.0), cy0 + CA['tag'] - tg['h'] / 2, tg['w'], tg['h'], getarr('TagUV', LCV, idx), WHITE, tag='CardTag')
sprite(fr, 'AtlasTex', dop('Add_DoubleDouble', cx, 12.0), cy0 + CA['d1'] - dd['h'] / 2, dd['w'], dd['h'], getarr('D1UV', LCV, idx), WHITE, tag='CardD1')
sprite(fr, 'AtlasTex', dop('Add_DoubleDouble', cx, 12.0), cy0 + CA['d2'] - dd['h'] / 2, dd['w'], dd['h'], getarr('D2UV', LCV, idx), WHITE, tag='CardD2')
text(fr, getarr('ISub', STRV, idx), ccx, cy0 + CA['sub'], 16, GOLD, anchor='c', tag='CardSub')
f0, fn0 = fr.iff(icmp('EqualEqual_IntInt', rst, 0), 'IfCardBuy')
aff_k = afford(idx)
rpr = catn(group(getarr('IPrice', INT, idx)), ' G')
text(f0, rpr, dop('Add_DoubleDouble', ccx, 16.0), cy0 + CA['cost'], 23, selc(GREEN, RED, aff_k), anchor='c', tag='CardPrice')
mw = b.call(HUDC, 'GetTextSize', [S('Text'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='PriceW')
b.wire(rpr, mw, 'Text'); b.wire(tscale(23), mw, 'Scale')
sprite(f0, 'AtlasTex', dop('Subtract_DoubleDouble', dop('Subtract_DoubleDouble', dop('Add_DoubleDouble', ccx, 16.0), dop('Multiply_DoubleDouble', dop('Divide_DoubleDouble', (mw, 'OutWidth'), T), 0.5)), 29.0),
       cy0 + CA['cost'] - 11, 22, 22, cell_uv('coin'), tag='CardCoin')
ONAMES = b.get('OreNames', arr(STRV), *P())
def orestr(ia, na):
    nm_ = b.item(ONAMES, STRV, b.math('Max', [(it('A', default='0'), ia), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
    return sels('', catn(' + ', istr(na), ' ', nm_), icmp('Less_IntInt', ia, 0))
text(f0, catn(orestr(getarr('IOreA', INT, idx), getarr('IOreAN', INT, idx)), orestr(getarr('IOreB', INT, idx), getarr('IOreBN', INT, idx))),
     ccx, cy0 + CA['cost'] + 20, 14, DIM, anchor='c', tag='CardOre')
text(fn0, getarr('INote', STRV, idx), ccx, cy0 + CA['cost'], 14, selc(GREEN, RED, icmp('EqualEqual_IntInt', rst, 1)), anchor='c', tag='CardNote')
fr = f0.join(fn0)
# button: on (hover / press) or off, with the shake and the buy flash
bx = dop('Add_DoubleDouble', dop('Add_DoubleDouble', cx, float(BT['dx'])), shk); bcy = cy0 + BT['dy'] + BT['h'] / 2
on_k = AND(icmp('EqualEqual_IntInt', rst, 0), aff_k)
over_b = inside(dop('Add_DoubleDouble', cx, float(BT['dx'])), cy0 + BT['dy'], BT['w'], BT['h'])
fon, foff = fr.iff(on_k, 'IfBtnOn')
fp, fnp = fon.iff(AND(over_b, LDOWN), 'IfBtnPress'); cell(fp, 'btn_press', bx, bcy)
fh, fnh = fnp.iff(over_b, 'IfBtnHover'); cell(fh, 'btn_hover', bx, bcy); cell(fnh, 'btn_on', bx, bcy)
cell(foff, 'btn_off', bx, bcy); fr = fp.join(fh, fnh, foff)
lbl = sels(getarr('IVerb', STRV, idx), sels('OWNED', sels('MAXED', sels('LOCKED', getarr('IBlock', STRV, idx), locked), icmp('EqualEqual_IntInt', rst, 2)), icmp('EqualEqual_IntInt', rst, 1)),
           icmp('EqualEqual_IntInt', rst, 0))
lbl = sels(sels('NOT ENOUGH GOLD', lbl, icmp('EqualEqual_IntInt', rst, 0)), lbl, NOT(aff_k))
text(fr, lbl, dop('Add_DoubleDouble', ccx, shk), bcy + 1, 20, selc(col(.16, .10, .03), col(.81, .77, .69), on_k), anchor='c', tag='BtnLabel')
ffl, fnfl = fr.iff(AND(isSel, dcmp('Greater_DoubleDouble', dop('Subtract_DoubleDouble', get('FlashUntil', DBL), NOW), 0.0)), 'IfFlash')
rect(ffl, dop('Add_DoubleDouble', cx, float(BT['dx'])), cy0 + BT['dy'], BT['w'], BT['h'], col(1.0, 0.95, 0.75, 0.45), tag='BuyFlash'); fr = ffl.join(fnfl)
# selection / hover frame on top
fs, fns = fr.iff(isSel, 'IfCardSel'); cell(fs, 'card_sel', dop('Subtract_DoubleDouble', cx, 6.0), cy0 + CA['h'] / 2)
fhv, fnhv = fns.iff(inside(cx, CA['y'], CA['w'], CA['h']), 'IfCardHover'); cell(fhv, 'card_hover', dop('Subtract_DoubleDouble', cx, 6.0), cy0 + CA['h'] / 2)
# garrison strip
SP = L['strip']; scy = SP['y'] + SP['h'] / 2 + 8
hascmd = dcmp('Greater_DoubleDouble', cnt['B'], 0.5)
cols = [('sword', 'SWORDSMEN  ', istr(rint(cnt['R']))), ('xbow', 'CROSSBOWMEN  ', istr(rint(cnt['G']))), ('banner', 'COMMANDER  ', sels('IN SERVICE', '-', hascmd)),
        ('medic', 'MEDICS  ', catn(istr(mcount), ' / ', istr(mmax))), ('gate', 'ARMY  ', catn(istr(rint(armyn)), ' / ', istr(rint(capn))))]
for k_, (gl, lab, val) in enumerate(cols):
    cell(fd, 'mini_' + gl, SP['cols'][k_] - 24, scy, tag='GIcon')
    text(fd, catn(lab, val), SP['cols'][k_] + 24, scy, 16, selc(RED, CREAM, full) if gl == 'gate' else CREAM, tag='GVal')
for q in range(3):
    x_ = SP['qx0'] + q * SP['qstep']; qy = SP['y'] + (SP['h'] - SP['qh']) / 2
    f1, f2 = fd.iff(icmp('Greater_IntInt', RQN, q), 'IfQ%d' % q)
    kind = b.item(rq, INT, None, *P()); G.nodes[-1][3][1]['default'] = str(q)
    sprite(f1, 'AtlasTex', x_ + SP['qw'] / 2 - 20, qy + SP['qh'] / 2 - 20, 40, 40, getarr('KindUV', LCV, kind), WHITE, tag='QGlyph')
    if q == 0:
        gt = b.lib(GS, 'GetTimeSeconds', [WC(), D('ReturnValue', out=True)], *P(), pure=True, tag='GameNow')
        prog = b.math('FClamp', [(D('Value', default='0.0'), dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', (gt, 'ReturnValue'), b.getm('RQStart', BHUD, fl('v', default='0.0'), BH, *P())),
                       b.math('FMax', [(D('A', default='0.0'), b.getm('RQDur', BHUD, fl('v', default='0.0'), BH, *P())), (D('B', default='0.1'), None)], D('ReturnValue', out=True), *P()))),
                      (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), *P())
        rect(f1, x_ + 4, qy + SP['qh'] - 7, dop('Multiply_DoubleDouble', prog, float(SP['qw'] - 8)), 4, col(.94, .78, .45, .95), tag='QBar')
    fd = f1.join(f2)
fmsg, fnmsg = fd.iff(dcmp('Less_DoubleDouble', NOW, get('MsgUntil', DBL)), 'IfNoGold')
text(fmsg, 'Not enough gold or ore, captain.', L['TW'] / 2, SP['y'] + SP['h'] + 22, 20, RED, anchor='c', tag='NoGold'); fd = fmsg.join(fnmsg)

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
print('BPC_Muster v2: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---------------------------------------------------------------- variables + defaults (read by setup_muster2_ue.py)
items = L['items']
uv = lambda k_: cell_uv(k_)
VARS = dict(Tab=('int', 0), Sel=('int', 0), Open=('bool', False), Near=('bool', False), Covering=('bool', False),
            OpenAt=('double', 0.0), MsgUntil=('double', 0.0), FlashUntil=('double', 0.0), NearDist=('double', 450.0), FreePads=('int', 0),
            PrevDown=('bool', False), WantAct=('bool', False), LastCard=('int', -1), LastClickAt=('double', 0.0), ShakeAt=('double', -10.0))
DATA = dict(TabStart=TS, TabCount=TCN, CardX0=X0, IVerb=[i['verb'] for i in items],
            OreNames=L['ores'], IPrice=[0] * NI, IOreA=[-1] * NI, IOreAN=[0] * NI, IOreB=[-1] * NI, IOreBN=[0] * NI, IState=[3] * NI, INote=[''] * NI, ISub=[''] * NI, IBlock=[''] * NI,
            NameUV=[uv('name_' + i['key']) for i in items], TagUV=[uv('tag_' + i['key']) for i in items],
            D1UV=[uv('d1_' + i['key']) for i in items], D2UV=[uv('d2_' + i['key']) for i in items], MedUV=[uv('med_' + i['glyph']) for i in items],
            KindUV=[uv('mini_sword'), uv('mini_xbow'), uv('mini_banner')], Busts=[i['bust'] for i in items])
json.dump(dict(vars=VARS, data=DATA), open(os.path.join(OUT, 'muster_data.json'), 'w'), indent=1)
print('muster_data.json: %d items' % NI)
