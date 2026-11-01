# Weapon Mastery (#416): the skill tree in the same kit as Vesna's Trade (#361) and the Muster (#359). EventGraph of the NEW
# hero component BPC_SkillTome.   python gen_skill.py -> handoffs/skilltree-416/build/BPC_SkillTome_graph.txt (+ skill_data.json)
# DrawTome(Hud, SizeX, SizeY) is called every frame from BP_ArmoryHUD (hook: TomeSeq). While the skill tree is open
# (MPC_SkillTree St.R > 0.5, opened and closed by BP_SkillTreeHUD as today: T / Esc, pause) it draws the whole screen and
# handles the clicks and keys; BP_SkillTreeHUD skips its old draw + clicks while Covering is true (gate hook).
# Game rules are BP_SkillTreeHUD's (10-30 export, CX_4791..4843), re-implemented with the same MPC writes:
#   ranks RkA.R blast, RkA.G charge, RkB.G whirl, RkB.B quake, RkB.A fissure; max 3; next rank costs mult x (rank + 1)
#   (x1 x5 x1 x5 x10); prerequisite: the previous skill of the chain has a rank (charge <- blast, quake <- whirl, fissure <- quake);
#   free points = hero Level - St.A. Learning writes Rk* channel + 1, St = (1, St.G, skill, St.A + cost), Fx = (skill, now, Fx.B, Fx.A)
#   (Fx starts the BP_SkillUnlockFX book, as the old up arrow did).
# Learn = E / gamepad A / the gold button / a double-click on a row or on the big glyph (#119).
# Auras (tab 3): ranks and the buy go through BP_HeroAuras; that part is wired when the live 5.8 export lands (AURA_HOOK below).
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
OUT = os.path.join(REPO, 'handoffs', 'skilltree-416', 'build'); os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(HERE, 'layout_sk.json'))); SC0, A = L['S'], L['atlas']
TOMEC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_SkillTome', 'BPC_SkillTome')
HEROC = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
STRV = S('v')
SND = '/Game/CastleDefender/UI/Trade/SFX_Trade%s.SFX_Trade%s'     # the kit's sounds (Swipe, Buy, Fail)
AURA_HOOK = None                                                  # filled from the BP_HeroAuras export (ranks, costs, buy call)

# ---------------------------------------------------------------- event, MPC reads, geometry, mouse (gen_trade's, renamed)
b.event('DrawTome', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, 0)
hud = ('DrawTome', 'Hud')
fl0 = Flow(('DrawTome', 'then'))
def mpcv(param):
    n = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', param), st('ReturnValue', LC, out=True)], *P(), pure=True, tag='MPC' + param)
    k_ = b.math('BreakColor', [(st('InColor', LC), (n, 'ReturnValue'))], fl('R', out=True, default='0.0'), *P())
    for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
    return {c_: (k_[0], c_) for c_ in 'RGBA'}
ST, RKA, RKB, FX = mpcv('St'), mpcv('RkA'), mpcv('RkB'), mpcv('Fx')
exec(chunk(L_GEO, L_DRAW - 1).replace("'DrawTrade'", "'DrawTome'"))
exec(chunk(L_DRAW, L_STATE - 1).replace("cls=TRADEC", "cls=TOMEC"))
def rint(v): return rnd(v)
def geti(var, pin, i):     # array item at a literal index
    n = b.item(get(var, arr(pin)), pin, None, *P()); G.nodes[-1][3][1]['default'] = str(i); return n
def fclamp(v, lo=0.0, hi=1.0):
    return b.math('FClamp', [(D('Value', default='0.0'), v), (D('Min', default=str(lo)), None), (D('Max', default=str(hi)), None)], D('ReturnValue', out=True), *P())
def mkcol(r, g, b_, a):
    pins = []
    for n_, v in zip('RGBA', (r, g, b_, a)): pins.append((fl(n_, default=str(float(v)) if isnum(v) else '0.0'), None if isnum(v) else v))
    return b.math('MakeColor', pins, st('ReturnValue', LC, out=True), *P())
def mpcset(fl_, param, colsrc):
    n = b.lib(MATL, 'SetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', param), st('ParameterValue', LC)], *P(), tag='Set' + param)
    b.wire(colsrc, n, 'ParameterValue'); fl_.go(n); return n

# ---------------------------------------------------------------- open state (the old HUD opens / closes the tree)
OPEN = dcmp('Greater_DoubleDouble', ST['R'], 0.5)
fo_, fc_ = fl0.iff(OPEN, 'IfTreeOpen')
setvar(fc_, 'Covering', BOOL, None, 'false'); setvar(fc_, 'WasOpen', BOOL, None, 'false')
fj, fnj = fo_.iff(NOT(get('WasOpen', BOOL)), 'IfJustOpened')
setvar(fj, 'WasOpen', BOOL, None, 'true'); setvar(fj, 'OpenAt', DBL, NOW); setvar(fj, 'SelAt', DBL, NOW); snd(fj, 'Swipe')
fm = fj.join(fnj)
setvar(fm, 'Covering', BOOL, None, 'true')

# ---------------------------------------------------------------- refresh: rank / cost / state of the 5 skills (+ 3 auras)
ownn = b.name('Owner'); callfn(G, ownn, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=P()[0], y=P()[1], self_hidden=True)
hc = cast(G, 'AsHero', HEROC, 'AsBP Third Person Character', *P(), pure=True); G.link(ownn, 'ReturnValue', 'AsHero', 'Object')
LEVEL = b.getm('Level', HEROC, INT, ('AsHero', 'AsBP Third Person Character'), *P())
SPENT = ST['A']
FREE = dop('Subtract_DoubleDouble', i2d(LEVEL), SPENT)                  # free points, as the old HUD (CX_71)
ITEMS = L['items']; NI = len(ITEMS); KEYS = [i['key'] for i in ITEMS]
RK = {'blast': RKA['R'], 'charge': RKA['G'], 'whirl': RKB['G'], 'quake': RKB['B'], 'fissure': RKB['A']}
def put(fl_, var, pin, i, v):
    n = b.aset(var, pin, None, None if isnum(v) else v, *P(), ditem=str(v) if isnum(v) else None)
    nd = G.nodes[[q[0] for q in G.nodes].index(n)][3]; nd[[p['name'] for p in nd].index('Index')]['default'] = str(i); fl_.go(n)
for i, k_ in enumerate(KEYS[:5]):
    rk = RK[k_]; mult = float(L['mult'][k_])
    cost = dop('Multiply_DoubleDouble', mult, dop('Add_DoubleDouble', rk, 1.0))
    maxed = dcmp('Greater_DoubleDouble', rk, 2.5)
    pre = L['prereq'].get(k_)
    locked = AND(dcmp('Less_DoubleDouble', rk, 0.5), dcmp('Less_DoubleDouble', RK[pre], 0.5)) if pre else None
    state = seli(2, seli(3, 0, locked) if locked else 0, maxed)           # 0 learnable, 2 mastered, 3 locked (needs the previous skill)
    put(fm, 'IRank', INT, i, rint(rk)); put(fm, 'ICost', INT, i, rint(cost)); put(fm, 'IState', INT, i, state)
# auras: BP_HeroAuras (AURA_HOOK). Until it's wired they show their rank 0 and state 4 ("learned in the old aura panel").
for i in range(5, NI):
    put(fm, 'IState', INT, i, 4)
put(fm, 'TabLearned', INT, 0, rint(dop('Add_DoubleDouble', RK['blast'], RK['charge'])))
put(fm, 'TabLearned', INT, 1, rint(dop('Add_DoubleDouble', dop('Add_DoubleDouble', RK['whirl'], RK['quake']), RK['fissure'])))

# ---------------------------------------------------------------- input
NT = len(L['tabnames']); TS = [0, 2, 5]; TCN = [2, 3, 3]
def tabhit(i): t = L['tabs'][i]; return AND(CLICK, inside(t['x0'], L['tabbar']['y'], t['x1'] - t['x0'], L['tabbar']['h']))
def settab(fl_, v):
    (setvar(fl_, 'Tab', INT, None, str(v)) if isnum(v) else setvar(fl_, 'Tab', INT, v)); setvar(fl_, 'Sel', INT, None, '0'); setvar(fl_, 'SelAt', DBL, NOW); snd(fl_, 'Swipe')
f1, f2 = fm.iff(anykey('Gamepad_LeftShoulder', 'A', 'Left'), 'IfTabPrev'); settab(f1, iop('Percent_IntInt', iop('Add_IntInt', get('Tab', INT), NT - 1), NT)); fm = f1.join(f2)
f1, f2 = fm.iff(anykey('Gamepad_RightShoulder', 'Tab', 'D', 'Right'), 'IfTabNext'); settab(f1, iop('Percent_IntInt', iop('Add_IntInt', get('Tab', INT), 1), NT)); fm = f1.join(f2)
for i in range(NT):
    f1, f2 = fm.iff(tabhit(i), 'IfTab%d' % i); settab(f1, i); fm = f1.join(f2)
TCOUNT = getarr('TabCount', INT, get('Tab', INT))
clampsel = lambda v: b.math('Clamp', [(it('Value', default='0'), v), (it('Min', default='0'), None), (it('Max', default='0'), iop('Subtract_IntInt', getarr('TabCount', INT, get('Tab', INT)), 1))], it('ReturnValue', out=True), *P())
def selrow(fl_, v):
    (setvar(fl_, 'Sel', INT, None, str(v)) if isnum(v) else setvar(fl_, 'Sel', INT, v)); setvar(fl_, 'SelAt', DBL, NOW); snd(fl_, 'Swipe')
f1, f2 = fm.iff(anykey('W', 'Up', 'Gamepad_DPad_Up'), 'IfPrev'); selrow(f1, clampsel(iop('Subtract_IntInt', get('Sel', INT), 1))); fm = f1.join(f2)
f1, f2 = fm.iff(anykey('S', 'Down', 'Gamepad_DPad_Down'), 'IfNext'); selrow(f1, clampsel(iop('Add_IntInt', get('Sel', INT), 1))); fm = f1.join(f2)
R = L['rows']; TN = L['turn']
# clicks: a row selects it; a second click on the same row (or on the big glyph) within 0.35 s = double-click = learn
DBLWIN = dcmp('Less_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('ClickAt', DBL)), 0.35)
setvar(fm, 'DoubleHit', BOOL, None, 'false')
for i in range(R['n']):
    hit = AND(AND(CLICK, inside(R['x'], R['y0'] + i * R['step'], R['w'], R['h'])), icmp('Less_IntInt', i, TCOUNT))
    f1, f2 = fm.iff(hit, 'IfRow%d' % i)
    fd1, fd2 = f1.iff(AND(DBLWIN, AND(icmp('EqualEqual_IntInt', get('ClickRow', INT), i), icmp('EqualEqual_IntInt', get('Sel', INT), i))), 'IfDbl%d' % i)
    setvar(fd1, 'DoubleHit', BOOL, None, 'true')
    fs = fd1.join(fd2)
    f3, f4 = fs.iff(icmp('NotEqual_IntInt', get('Sel', INT), i), 'IfNewSel%d' % i); selrow(f3, i); fs = f3.join(f4)
    setvar(fs, 'ClickRow', INT, None, str(i)); setvar(fs, 'ClickAt', DBL, NOW)
    fm = fs.join(f2)
glyphhit = AND(CLICK, inside(TN['cx'] - 120, TN['cy'] - 130, 240, 240))
f1, f2 = fm.iff(glyphhit, 'IfGlyph')
fd1, fd2 = f1.iff(AND(DBLWIN, icmp('EqualEqual_IntInt', get('ClickRow', INT), 9)), 'IfGlyphDbl'); setvar(fd1, 'DoubleHit', BOOL, None, 'true')
fs = fd1.join(fd2); setvar(fs, 'ClickRow', INT, None, '9'); setvar(fs, 'ClickAt', DBL, NOW); fm = fs.join(f2)
RT = L['rtabs']
f1, f2 = fm.iff(OR(key('Q'), AND(CLICK, inside(RT['eq'][0], RT['y'], RT['sp'][1] - RT['eq'][0], RT['h']))), 'IfRTab')
setvar(f1, 'RTab', INT, iop('Subtract_IntInt', 1, get('RTab', INT))); fm = f1.join(f2)
IDX = iop('Add_IntInt', getarr('TabStart', INT, get('Tab', INT)), get('Sel', INT))
ST_ = getarr('IState', INT, IDX); CO_ = getarr('ICost', INT, IDX)
AFF = dcmp('GreaterEqual_DoubleDouble', FREE, i2d(CO_))
LEARNABLE = icmp('EqualEqual_IntInt', ST_, 0)
BU = L['buy']
act = AND(OR(OR(anykey('E', 'Gamepad_FaceButton_Bottom'), AND(CLICK, inside(BU['x'], BU['y'], BU['w'], BU['h']))), get('DoubleHit', BOOL)),
          dcmp('Greater_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('OpenAt', DBL)), 0.25))
fa, fna = fm.iff(act, 'IfLearn')
fb_, fnb = fa.iff(LEARNABLE, 'IfLearnable')
fg, fng = fb_.iff(AFF, 'IfAfford')
fail = fng.join(fnb)
setvar(fail, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 1.5)); setvar(fail, 'ShakeAt', DBL, NOW); snd(fail, 'Fail')
# learn: the old HUD's writes, per skill
outs = []; frest = fg
for i, k_ in enumerate(KEYS[:5]):
    f1, frest = frest.iff(icmp('EqualEqual_IntInt', IDX, i), 'IfLearn%d' % i)
    src = RKA if i < 2 else RKB; ch = {'blast': 'R', 'charge': 'G', 'whirl': 'G', 'quake': 'B', 'fissure': 'A'}[k_]
    vals = [dop('Add_DoubleDouble', src[c_], 1.0) if c_ == ch else src[c_] for c_ in 'RGBA']
    mpcset(f1, 'RkA' if i < 2 else 'RkB', mkcol(*vals))
    cost = dop('Multiply_DoubleDouble', float(L['mult'][k_]), dop('Add_DoubleDouble', RK[k_], 1.0))
    mpcset(f1, 'St', mkcol(1.0, ST['G'], float(i), dop('Add_DoubleDouble', ST['A'], cost)))
    mpcset(f1, 'Fx', mkcol(float(i), NOW, FX['B'], FX['A']))
    outs.append(f1)
fdone = outs[0].join(*outs[1:])
setvar(fdone, 'FlashUntil', DBL, dop('Add_DoubleDouble', NOW, 0.6)); setvar(fdone, 'LearnAt', DBL, NOW); snd(fdone, 'Buy')
fm = fdone.join(frest, fail, fna)

# =====================================================================================================================
# DRAW
# =====================================================================================================================
fd = fm
OT = dop('Subtract_DoubleDouble', NOW, get('OpenAt', DBL))
AL = fclamp(dop('Divide_DoubleDouble', OT, 0.25))                                   # open fade, 250 ms
rect(fd, 0, 0, L['TW'], L['TH'], mkcol(0.02, 0.018, 0.016, AL), tag='BackFill')
sprite(fd, 'FrameTex', 0, 0, L['TW'], L['TH'], (0.0, 0.0, 1.0, 1.0), mkcol(1.0, 1.0, 1.0, AL), tag='Frame')
tb = L['tabbar']
for i in range(NT):
    t = L['tabs'][i]; r = A['tab%d' % i]
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', get('Tab', INT), i), 'IfTabOn%d' % i)
    sprite(f1, 'AtlasTex', (t['x0'] + t['x1']) / 2 - r['w'] / 2, tb['cy'] - r['h'] / 2, r['w'], r['h'], cell_uv('tab%d' % i), tag='TabOn%d' % i); fd = f1.join(f2)
PU = L['purse']
FREEI = rint(FREE)
text(fd, catn(istr(FREEI), sels('  POINT', '  POINTS', icmp('EqualEqual_IntInt', FREEI, 1))), PU['gold'][1], PU['cy'], 26, CREAM, tag='Points')
text(fd, catn('LEVEL ', istr(LEVEL)), PU['iron'][1] + 40, PU['cy'], 24, CREAM, tag='Level')
LH = L['lhead']
text(fd, catn('(', istr(getarr('TabLearned', INT, get('Tab', INT))), ' / ', istr(iop('Multiply_IntInt', TCOUNT, 3)), ')'), 268, LH['cy'] + 1, 27, GOLD, tag='TreeCount')
# rows of the current tab (+ the sealed slots), with the spine through the discs
DX = (R['icon'][0] + R['icon'][1]) / 2.0
NALL = iop('Add_IntInt', TCOUNT, getarr('TabSealed', INT, get('Tab', INT)))
lp = b.forloop(None, None, *P()); G.nodes[-1][3][2]['default'] = str(R['n'] - 1); fd.go(lp, out='Completed')
fr = Flow((lp, 'LoopBody')); ri = (lp, 'Index')
fin, _z = fr.iff(icmp('Less_IntInt', ri, NALL), 'IfRowUsed'); fr = fin
slide = dop('Multiply_DoubleDouble', 40.0, dop('Subtract_DoubleDouble', 1.0, fclamp(dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', OT, dop('Multiply_DoubleDouble', i2d(ri), 0.04)), 0.22))))
ry = dop('Add_DoubleDouble', float(R['y0']), dop('Multiply_DoubleDouble', i2d(ri), float(R['step'])))
rcy = dop('Add_DoubleDouble', ry, R['h'] / 2.0)
rx = lambda x_: dop('Add_DoubleDouble', float(x_), slide)
REAL = icmp('Less_IntInt', ri, TCOUNT)
idx = iop('Add_IntInt', getarr('TabStart', INT, get('Tab', INT)), ri)
rrk = getarr('IRank', INT, idx); rst = getarr('IState', INT, idx)
LIT = AND(REAL, icmp('Greater_IntInt', rrk, 0))
# spine segment up from this disc to the previous one
fsp, fnsp = fr.iff(icmp('Greater_IntInt', ri, 0), 'IfSpine')
rect(fsp, DX - 1.5, dop('Subtract_DoubleDouble', rcy, float(R['step'])), 3, R['step'], selc(col(.94, .78, .45, .95), col(.48, .38, .2, .45), LIT), tag='Spine'); fr = fsp.join(fnsp)
fsel, fns = fr.iff(AND(REAL, icmp('EqualEqual_IntInt', ri, get('Sel', INT))), 'IfRowSel')
rs = L['rsel']
sprite(fsel, 'AtlasTex', R['x'] + rs['dx'], dop('Add_DoubleDouble', ry, float(rs['dy'])), rs['w'], rs['h'], cell_uv('rsel'), tag='RowSel'); fr = fsel.join(fns)
fre, fse = fr.iff(REAL, 'IfRowReal')
# --- a real skill row
fl1, fl2 = fre.iff(LIT, 'IfRingOn')
sprite(fl1, 'AtlasTex', dop('Subtract_DoubleDouble', rx(DX), 30.0), dop('Subtract_DoubleDouble', rcy, 30.0), 60, 60, cell_uv('ring_on'), tag='RingOn')
sprite(fl2, 'AtlasTex', dop('Subtract_DoubleDouble', rx(DX), 30.0), dop('Subtract_DoubleDouble', rcy, 30.0), 60, 60, cell_uv('ring'), tag='Ring')
fre = fl1.join(fl2)
sprite(fre, 'AtlasTex', dop('Subtract_DoubleDouble', rx(DX), 20.0), dop('Subtract_DoubleDouble', rcy, 20.0), 40, 40, getarr('GlyphUV', LCV, idx),
       selc(col(.95, .84, .56), col(.85, .72, .45), LIT), tag='RowGlyph')
nm = A['name_blast']
sprite(fre, 'AtlasTex', rx(R['name'][0]), dop('Add_DoubleDouble', ry, R['name'][1] - R['y0'] - nm['h'] / 2.0), nm['w'], nm['h'], getarr('NameUV', LCV, idx), CREAM, tag='RowName')
sy0 = dop('Add_DoubleDouble', ry, R['deff'][1] - R['y0'])
for p_ in range(3):
    f1, f2 = fre.iff(icmp('Greater_IntInt', rrk, p_), 'IfPip%d' % p_)
    cell(f1, 'pip_on', rx(R['deff'][0] + p_ * 20), sy0); cell(f2, 'pip_off', rx(R['deff'][0] + p_ * 20), sy0); fre = f1.join(f2)
LOCKED = icmp('EqualEqual_IntInt', rst, 3)
text(fre, sels(getarr('INeeds', STRV, idx), catn('RANK ', istr(rrk), ' / 3'), LOCKED), rx(R['deff'][0] + 70), sy0, 17, selc(col(.75, .44, .36), DIM, LOCKED), tag='RowSub')
sx_ = rx(R['state'][0]); syy = dop('Add_DoubleDouble', ry, R['state'][1] - R['y0'])
f0, fn0 = fre.iff(icmp('EqualEqual_IntInt', rst, 0), 'IfRowCost')
rc = istr(getarr('ICost', INT, idx))
text(f0, rc, sx_, syy, 28, selc(GOLD, RED, dcmp('GreaterEqual_DoubleDouble', FREE, i2d(getarr('ICost', INT, idx)))), anchor='r', tag='RowCost')
mw = b.call(HUDC, 'GetTextSize', [S('Text'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='CostW')
b.wire(rc, mw, 'Text'); b.wire(tscale(28), mw, 'Scale')
sprite(f0, 'AtlasTex', dop('Subtract_DoubleDouble', dop('Subtract_DoubleDouble', sx_, dop('Divide_DoubleDouble', (mw, 'OutWidth'), T)), 32.0), dop('Subtract_DoubleDouble', syy, 13.0), 26, 26, cell_uv('spt'), tag='RowStar')
f2s, fn2 = fn0.iff(icmp('EqualEqual_IntInt', rst, 2), 'IfRowMax'); cell(f2s, 'maxed', sx_, syy, anchor='r')
f3s, fn3 = fn2.iff(LOCKED, 'IfRowLocked'); cell(f3s, 'needs', sx_, syy, anchor='r')
text(fn3, 'IN AURA PANEL', sx_, syy, 17, DIM, anchor='r', tag='RowAura')
# --- a sealed slot
sprite(fse, 'AtlasTex', dop('Subtract_DoubleDouble', rx(DX), 30.0), dop('Subtract_DoubleDouble', rcy, 30.0), 60, 60, cell_uv('ring'), tag='SealRing')
sprite(fse, 'AtlasTex', dop('Subtract_DoubleDouble', rx(DX), 16.0), dop('Subtract_DoubleDouble', rcy, 16.0), 32, 32, cell_uv('glyph_lock'), col(.44, .40, .35), tag='SealLock')
sn = A['name_sealed']
sprite(fse, 'AtlasTex', rx(R['name'][0]), dop('Add_DoubleDouble', ry, R['name'][1] - R['y0'] - sn['h'] / 2.0), sn['w'], sn['h'], cell_uv('name_sealed'), DIM, tag='SealName')
text(fse, 'NOT YET REVEALED', rx(R['deff'][0]), sy0, 17, col(.44, .40, .35), tag='SealSub')
cell(fse, 'sealed', sx_, syy, anchor='r')

# centre: the selected skill
IT = L['ititle']; tw_ = A['title_blast']
sprite(fd, 'AtlasTex', IT['cx'] - tw_['w'] / 2, IT['y'] - tw_['h'] / 2, tw_['w'], tw_['h'], getarr('TitleUV', LCV, IDX), CREAM, tag='Title')
TG = L['tags']; tg = A['tag_blast']
sprite(fd, 'AtlasTex', IT['cx'] - tg['w'] / 2, TG['y'] - tg['h'] / 2, tg['w'], tg['h'], getarr('TagUV', LCV, IDX), col(.80, .76, .68), tag='Tag')
pop = dop('Add_DoubleDouble', 0.92, dop('Multiply_DoubleDouble', 0.08, fclamp(dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('SelAt', DBL)), 0.18))))
gcy = TN['cy'] - 10
def centred(fl_, uv, size, tint, tag):
    sz = dop('Multiply_DoubleDouble', pop, float(size))
    half = dop('Multiply_DoubleDouble', sz, 0.5)
    sprite(fl_, 'AtlasTex', dop('Subtract_DoubleDouble', float(TN['cx']), half), dop('Subtract_DoubleDouble', float(gcy), half), sz, sz, uv, tint, tag=tag)
centred(fd, cell_uv('ring_on'), 236, WHITE, 'BigRing')
centred(fd, getarr('GlyphUV', LCV, IDX), 150, selc(col(1, 1, 1, .45), col(.95, .84, .56), icmp('EqualEqual_IntInt', ST_, 3)), 'BigGlyph')
SRK = getarr('IRank', INT, IDX)
RP = L['rankpips']
lpop = fclamp(dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('LearnAt', DBL)), 0.22))
for p_ in range(3):
    cx_ = RP['cx'] + (p_ - 1) * RP['step']
    f1, f2 = fd.iff(icmp('Greater_IntInt', SRK, p_), 'IfBigPip%d' % p_)
    # the newest diamond pops 1.0 -> 1.35 -> 1.0 over 220 ms after a learn
    newest = icmp('EqualEqual_IntInt', SRK, p_ + 1)
    bump = seld(dop('Multiply_DoubleDouble', 0.35, b.math('Sin', [(D('A', default='0.0'), dop('Multiply_DoubleDouble', lpop, 3.14159))], D('ReturnValue', out=True), *P())), 0.0, newest)
    bsz = dop('Multiply_DoubleDouble', 26.0, dop('Add_DoubleDouble', 1.0, bump)); bh = dop('Multiply_DoubleDouble', bsz, 0.5)
    sprite(f1, 'AtlasTex', dop('Subtract_DoubleDouble', float(cx_), bh), dop('Subtract_DoubleDouble', float(RP['y']), bh), bsz, bsz, cell_uv('bigpip_on'), tag='BigPipOn')
    cell(f2, 'bigpip_off', cx_, RP['y'], anchor='c'); fd = f1.join(f2)
# cost box: next rank costs / rank r > r+1 of 3
fcz, fncz = fd.iff(LEARNABLE, 'IfCostShown')
text(fcz, catn(istr(CO_), sels(' POINT', ' POINTS', icmp('EqualEqual_IntInt', CO_, 1))), 616, 637, 30, selc(GREEN, RED, AFF), tag='Cost')
text(fcz, istr(SRK), 826, 637, 28, CREAM, tag='RankNow'); text(fcz, '>', 856, 637, 20, CREAM, tag='RankArrow')
text(fcz, istr(iop('Add_IntInt', SRK, 1)), 884, 637, 28, GREEN, tag='RankNext'); text(fcz, 'OF 3', 922, 637, 20, DIM, tag='RankOf')
text(fncz, sels('MASTERED', sels('LOCKED', '-', icmp('EqualEqual_IntInt', ST_, 3)), icmp('EqualEqual_IntInt', ST_, 2)), 616, 637, 26, GOLD, tag='CostNone')
text(fncz, catn(istr(SRK), ' OF 3'), 826, 637, 28, CREAM, tag='RankOnly')
fd = fcz.join(fncz)
BN = L['bonus']; dd = A['d1_blast']
sprite(fd, 'AtlasTex', 566, BN['lines'][0] - dd['h'] / 2, dd['w'], dd['h'], getarr('D1UV', LCV, IDX), col(.86, .82, .74), tag='Desc1')
fnd, fnn = fd.iff(icmp('EqualEqual_IntInt', ST_, 3), 'IfNeedsLine')
text(fnd, catn('Learn ', getarr('IPrevName', STRV, IDX), ' first.'), 566, BN['lines'][1] + 6, 19, col(.75, .44, .36), tag='NeedsLine')
cell(fnn, 'learnhint', 566, BN['lines'][1] + 6, DIM); fd = fnd.join(fnn)
# button (+ shake on a refused learn, flash on a learn)
ON_ = AND(LEARNABLE, AFF)
shk = dop('Multiply_DoubleDouble', 6.0, b.math('Sin', [(D('A', default='0.0'), dop('Multiply_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('ShakeAt', DBL)), 52.0))], D('ReturnValue', out=True), *P()))
shk = seld(shk, 0.0, dcmp('Less_DoubleDouble', dop('Subtract_DoubleDouble', NOW, get('ShakeAt', DBL)), 0.18))
bx = dop('Add_DoubleDouble', float(BU['x']), shk)
fon, foff = fd.iff(ON_, 'IfBtnOn')
sprite(fon, 'AtlasTex', bx, BU['cy'] - A['btn_on']['h'] / 2, A['btn_on']['w'], A['btn_on']['h'], cell_uv('btn_on'), tag='BtnOn')
sprite(foff, 'AtlasTex', bx, BU['cy'] - A['btn_off']['h'] / 2, A['btn_off']['w'], A['btn_off']['h'], cell_uv('btn_off'), tag='BtnOff'); fd = fon.join(foff)
ffl, fnfl = fd.iff(dcmp('Greater_DoubleDouble', dop('Subtract_DoubleDouble', get('FlashUntil', DBL), NOW), 0.0), 'IfFlash')
rect(ffl, BU['x'], BU['y'], BU['w'], BU['h'], col(1.0, 0.9, 0.6, 0.35), tag='LearnFlash'); fd = ffl.join(fnfl)
cell(fd, 'key_e', dop('Add_DoubleDouble', float(BU['key'][0]), shk), BU['key'][1], anchor='c')
lbl = catn('LEARN RANK ', istr(iop('Add_IntInt', SRK, 1)), '  -  ', istr(CO_), sels(' POINT', ' POINTS', icmp('EqualEqual_IntInt', CO_, 1)))
lbl = sels(lbl, sels('MASTERED', sels('LOCKED', 'IN THE AURA PANEL', icmp('EqualEqual_IntInt', ST_, 3)), icmp('EqualEqual_IntInt', ST_, 2)), LEARNABLE)
text(fd, lbl, dop('Add_DoubleDouble', float(BU['text']), shk), BU['cy'], 26, selc(col(.10, .07, .03), CREAM, ON_), tag='LearnLabel')
fmsg, fnmsg = fd.iff(dcmp('Less_DoubleDouble', NOW, get('MsgUntil', DBL)), 'IfNoPts')
cell(fmsg, 'nopts', BU['x'] + BU['w'] / 2, BU['y'] - 14, RED, anchor='c'); fd = fmsg.join(fnmsg)

# right: MASTERY (all ranks) / RULES
for i, kk in enumerate(('rtab0', 'rtab1')):
    x0 = (RT['eq'] if i == 0 else RT['sp'])[0]; r = A[kk]
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', get('RTab', INT), i), 'IfRTabOn%d' % i)
    sprite(f1, 'AtlasTex', x0, RT['y'], r['w'], r['h'], cell_uv(kk), tag='RTabOn%d' % i); fd = f1.join(f2)
MA = L['mastery']
fm0, fm1 = fd.iff(icmp('EqualEqual_IntInt', get('RTab', INT), 0), 'IfMastery')
y_ = MA['head0']
for h, tb_ in (('CROSSBOW', 0), ('SWORD', 1), ('AURAS', 2)):
    text(fm0, h, MA['x'] + 6, y_, 19, GOLD, tag='MHead'); rect(fm0, MA['x'] + 120, y_, 330, 1, col(.48, .38, .2, .4), tag='MRule'); y_ += 34
    for i in [j for j, it_ in enumerate(ITEMS) if it_['tab'] == tb_]:
        rk_ = geti('IRank', INT, i)
        sprite(fm0, 'AtlasTex', MA['icon'] - 13, y_ - 13, 26, 26, cell_uv('glyph_' + ITEMS[i]['glyph']), selc(col(.95, .84, .56), col(.49, .44, .38), icmp('Greater_IntInt', rk_, 0)), tag='MIcon')
        text(fm0, ITEMS[i]['name'].upper(), MA['label'], y_, 19, selc(CREAM, DIM, icmp('Greater_IntInt', rk_, 0)), tag='MName')
        for p_ in range(3):
            f1, f2 = fm0.iff(icmp('Greater_IntInt', rk_, p_), 'IfMPip')
            cell(f1, 'pip_on', MA['pip0'] + p_ * MA['pipstep'], y_); cell(f2, 'pip_off', MA['pip0'] + p_ * MA['pipstep'], y_); fm0 = f1.join(f2)
        y_ += MA['step'] - 6
    y_ += 10
rect(fm0, 1150, y_ + 4, 485, 1, col(.48, .38, .2, .4), tag='MRule2')
cell(fm0, 'spt', 1173, y_ + 40); text(fm0, 'SKILL POINTS', 1214, y_ + 40, 21, CREAM, tag='MPts')
text(fm0, istr(FREEI), 1610, y_ + 40, 28, GOLD, anchor='r', tag='MPtsN')
text(fm0, catn('One point per hero level. Next at level ', istr(iop('Add_IntInt', LEVEL, 1)), '.'), 1160, y_ + 78, 17, DIM, tag='MNext')
RULES = ['ONE SKILL POINT PER HERO LEVEL.', 'EVERY SKILL HAS 3 RANKS.', 'NEXT RANK COSTS ITS PRICE x (RANK + 1):',
         '   BLAST BOLT, WHIRLWIND  x1', '   CHARGED SHOT, QUAKE SLAM  x5', '   FISSURE  x10',
         'EACH SKILL NEEDS THE ONE BEFORE IT.', 'AURAS: KEYS 4 5 6, 12 S + 2 S PER RANK,', '   THEN THEY RECHARGE.']
for k_, line in enumerate(RULES):
    text(fm1, line, 1160, 270 + k_ * 34, 18, CREAM if not line.startswith('   ') else GOLD, tag='Rule')
fd = fm0.join(fm1)

# ---------------------------------------------------------------- self-check + write
names = [n[0] for n in G.nodes]
assert len(names) == len(set(names)), 'duplicate node names'
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
outs_ = {(n[0], p['name']) for n in G.nodes for p in n[3] if p.get('out')}
wrong = [l for l in G.links if (l[0], l[1]) not in outs_ or (l[2], l[3]) in outs_]
if wrong: raise SystemExit('direction: %s' % wrong[:10])
open(os.path.join(OUT, 'BPC_SkillTome_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_SkillTome: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---------------------------------------------------------------- variables + defaults (read by setup_tome_ue.py)
uv = lambda k_: cell_uv(k_)
name_of = {i['key']: i['name'] for i in ITEMS}
VARS = dict(Tab=('int', 1), RTab=('int', 0), Sel=('int', 0), ClickRow=('int', -1), WasOpen=('bool', False), Covering=('bool', False), DoubleHit=('bool', False),
            OpenAt=('double', 0.0), SelAt=('double', 0.0), ClickAt=('double', -10.0), MsgUntil=('double', 0.0), FlashUntil=('double', 0.0),
            ShakeAt=('double', -10.0), LearnAt=('double', -10.0))
DATA = dict(TabStart=TS, TabCount=TCN, TabSealed=[L['sealed'][str(t)] if str(t) in L['sealed'] else L['sealed'][t] for t in range(NT)], TabLearned=[0, 0, 0],
            IRank=[0] * NI, ICost=[0] * NI, IState=[4] * NI,
            INeeds=['NEEDS ' + name_of[L['prereq'][i['key']]].upper() if i['key'] in L['prereq'] else '' for i in ITEMS],
            IPrevName=[name_of[L['prereq'][i['key']]] if i['key'] in L['prereq'] else '' for i in ITEMS],
            NameUV=[uv('name_' + i['key']) for i in ITEMS], TitleUV=[uv('title_' + i['key']) for i in ITEMS], TagUV=[uv('tag_' + i['key']) for i in ITEMS],
            D1UV=[uv('d1_' + i['key']) for i in ITEMS], GlyphUV=[uv('glyph_' + i['glyph']) for i in ITEMS])
json.dump(dict(vars=VARS, data=DATA), open(os.path.join(OUT, 'skill_data.json'), 'w'), indent=1)
print('skill_data.json: %d items' % NI)
