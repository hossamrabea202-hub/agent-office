# Potion polish (i9, 2026-11-02): full EventGraph of BPC_PotionBelt, replacing #74's. Same drink/heal rules and shop row;
# new slot, feedback and the Q hint.   python gen_potion_polish.py  -> build/BPC_PotionBelt_polish_graph.txt
# (the BP_ZombieHUD hook from #74 stays: it calls DrawPotion(Hud) every frame.)
#   - SLOT: round M_UI_PotionBadge (via BadgeMID, created once) in line with the Dash/Berserk badges, left of the HP bar;
#     gold Q key cap on its top-left, "xN" count bottom-right. Cooldown = clockwise sweep in the badge.
#   - REFUSE: Q when it can't drink (full HP, cooldown, none left, dead): fail sound, red ring flash + a short shake.
#   - HEALING: the badge halo turns green and a soft green glow sits on the HP bar until the heal is done.
#   - LOW HP: below 30 % with a potion ready, the badge halo pulses gold.
#   - Q HINT (motion graphic): the first time HP drops below 50 % with a potion, an ornate plate rises out of the badge:
#     an animated Q key cap (presses itself) + "Drink a Healing Potion / Restores 35% health over 3 s"; holds ~4 s, fades.
#     Once more at 30 % if no potion was drunk yet (10 s after the first). Drinking ends hints for good (fades in 0.6 s).
# Positions are in 1080p units (U = viewport height / 1080), bottom centre: badge centre (-177, -73) from (centre, bottom).
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(_here, '..', 'castle-scroll-411', 'gen_scroll411.py'), encoding='utf-8').read()
_src = _src[:_src.index('# ---------------------------------------------------------------- event, viewport, unit')]
__file__ = os.path.join(_here, '..', 'castle-scroll-411', 'gen_scroll411.py')
exec(compile(_src, 'gen_scroll411-preamble', 'exec'))
HERE = _here; OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
G = Graph(); b = B(G, 'pp'); XY[0], XY[1] = 0, 300

HUDC = CLS('HUD')
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
SND_BUY, SND_FAIL = '/Game/CastleDefender/UI/Trade/SFX_TradeBuy.SFX_TradeBuy', '/Game/CastleDefender/UI/Trade/SFX_TradeFail.SFX_TradeFail'
DBLV, INTV = D('v', default='0.0'), it('v', default='0')
BLENDP = {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': 'BLEND_Translucent'}
MIDC = CLS('MaterialInstanceDynamic')
MIDV, MATV_, TEXV = ob('v', MIDC), ob('v', CLS('MaterialInterface')), ob('v', TEX2D)
TAU = 6.2831853


def sound(fl_, path, vol='0.8'):
    n = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', CLS('SoundBase')), dobj=path), fl('VolumeMultiplier', default=vol, advanced=True),
              fl('PitchMultiplier', default='1.000000', advanced=True), fl('StartTime', default='0.000000', advanced=True),
              dict(ob('ConcurrencySettings', CLS('SoundConcurrency')), advanced=True), dict(ob('OwningActor', ACT), advanced=True),
              dict(bo('bIsUISound', default='true'), advanced=True)], *P(), tag='Snd')
    fl_.go(n)
def iget(var): return get(var, INTV)
def dget(var): return get(var, DBLV)
def icmp(m, a, c): return b.icmp(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(a) if isnum(a) else '0', db=str(c) if isnum(c) else '0')
def iop(m, a, c): return b.i2(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(a) if isnum(a) else '0', db=str(c) if isnum(c) else '0')
def dmax(a, c): return b.math('FMax', [(D('A', default='0.0'), None if isnum(a) else a), (D('B', default=str(float(c)) if isnum(c) else '0.0'), None if isnum(c) else c)], D('ReturnValue', out=True), *P())
def dmin(a, c): return b.math('FMin', [(D('A', default=str(float(a)) if isnum(a) else '0.0'), None if isnum(a) else a), (D('B', default=str(float(c)) if isnum(c) else '0.0'), None if isnum(c) else c)], D('ReturnValue', out=True), *P())
def selc(a, c, pick): return b.math('SelectColor', [(st('A', LC, default=a), None), (st('B', LC, default=c), None), (bo('bPickA', default='false'), pick)], st('ReturnValue', LC, out=True), *P())
def dsin(v): return b.math('Sin', [(D('A', default='0.0'), v)], D('ReturnValue', out=True), *P())
def mul(a, c): return dop('Multiply_DoubleDouble', a, c)
def add(a, c): return dop('Add_DoubleDouble', a, c)
def sub(a, c): return dop('Subtract_DoubleDouble', a, c)
def smooth(t):   # t*t*(3-2t), t already 0..1
    return mul(mul(t, t), sub(3.0, mul(t, 2.0))) if not isnum(t) else t
def one_minus(v): return sub(1.0, v)
def mcol(r, g_, b_, a):
    """MakeColor; each channel a number or a wire. Alpha is always wired or a non-zero literal (zero-default gotcha)."""
    pins = []
    for nm, v in (('R', r), ('G', g_), ('B', b_), ('A', a)):
        lit = '%f' % v if isnum(v) else ('1.000000' if nm == 'A' else '0.000000')
        pins.append((fl(nm, default=lit), None if isnum(v) else v))
    return b.math('MakeColor', pins, st('ReturnValue', LC, out=True), *P())

# ---------------------------------------------------------------- event, viewport, time
b.event('DrawPotion', [ob('Hud', HUDC)], 0, 0)
hud = ('DrawPotion', 'Hud')
fl0 = Flow(('DrawPotion', 'then'))
pcn = b.call(HUDC, 'GetOwningPlayerController', [ob('ReturnValue', PCON, out=True)], *P(), target=hud, pure=True, const=True, tag='PC')
PC = (pcn, 'ReturnValue')
vs = b.call(PCON, 'GetViewportSize', [it('SizeX', out=True, default='0'), it('SizeY', out=True, default='0')], *P(), target=PC, pure=True, const=True, tag='ViewSize')
SXd, SYd = i2d((vs, 'SizeX')), i2d((vs, 'SizeY'))
U = dop('Divide_DoubleDouble', SYd, 1080.0)
def px(v): return dop('Multiply_DoubleDouble', U, float(v) if isnum(v) else v)
mp = b.call(PCON, 'GetMousePosition', [F('LocationX', out=True), F('LocationY', out=True), bo('ReturnValue', out=True, default='false')], *P(), target=PC, pure=True, const=True, tag='Mouse')
MX, MY = (mp, 'LocationX'), (mp, 'LocationY')
def key(name):
    n = b.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default=name), bo('ReturnValue', out=True, default='false')], *P(), target=PC, pure=True, const=True, tag='Key' + name[:10])
    return (n, 'ReturnValue')
now = b.lib(GS, 'GetTimeSeconds', [WC(), D('ReturnValue', out=True)], *P(), pure=True, tag='GameNow'); NOW = (now, 'ReturnValue')
dt = b.math('FClamp', [(D('Value', default='0.0'), sub(NOW, dget('LastT'))), (D('Min', default='0.0'), None), (D('Max', default='0.1'), None)],
            D('ReturnValue', out=True), *P())
# LastT is written AFTER the heal (see fl2 below): dt is a pure node, read when the heal runs, so writing LastT first made dt 0
# and the #74 heal never moved (the bug this pass fixes).

# ---------------------------------------------------------------- the badge material instance (created once)
fm, fhas = fl0.iff(NOT(b.valid(get('BadgeMID', MIDV), *P())), 'IfNoMID')
cm = b.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), ob('Parent', CLS('MaterialInterface')), NAME_('OptionalName', 'None'),
           {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None'},
           ob('ReturnValue', MIDC, out=True)], *P(), tag='MakeMID')
b.wire(get('BadgeMat', MATV_), cm, 'Parent')
fm.go(cm)
setvar(fm, 'BadgeMID', MIDV, (cm, 'ReturnValue'))
fl0 = fm.join(fhas)

# ---------------------------------------------------------------- drink (Q) + heal over time + refuse + hint triggers
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], *P(), pure=True, tag='Pawn')
cast(G, 'ppAsHero', HERO, 'AsBP Third Person Character', *P(), pure=True); b.wire((pp, 'ReturnValue'), 'ppAsHero', 'Object')
HEROH = ('ppAsHero', 'AsBP Third Person Character')
fh, fnoh = fl0.iff(b.valid(HEROH, *P()), 'IfHero')
DT = b.getm('DamageTaken', HERO, DBLV, HEROH, *P())
DEAD = b.getm('IsDead', HERO, bo('v', default='false'), HEROH, *P())
QK = key('Q')
can = AND(icmp('Greater_IntInt', iget('Potions'), 0), AND(dcmp('GreaterEqual_DoubleDouble', NOW, dget('CoolUntil')), AND(NOT(DEAD), dcmp('Greater_DoubleDouble', DT, 0.5))))
fq, fnq = fh.iff(QK, 'IfQ')
fd, frf = fq.iff(can, 'IfDrink')
setvar(fd, 'Potions', INTV, iop('Subtract_IntInt', iget('Potions'), 1))
setvar(fd, 'HealLeft', DBLV, add(dget('HealLeft'), mul(dget('HealPct'), dget('MaxHP'))))
setvar(fd, 'CoolUntil', DBLV, add(NOW, dget('Cooldown')))
setvar(fd, 'HintStage', INTV, None, lit='3')
setvar(fd, 'HintAt', DBLV, dmin(dget('HintAt'), sub(NOW, 4.0)))
sound(fd, SND_BUY, '0.6')
setvar(frf, 'RefuseAt', DBLV, NOW)
sound(frf, SND_FAIL, '0.5')
f1 = fd.join(frf, fnq)
fhl, fno = f1.iff(dcmp('Greater_DoubleDouble', dget('HealLeft'), 0.0), 'IfHealing')
rate = dop('Divide_DoubleDouble', mul(dget('HealPct'), dget('MaxHP')), dmax(dget('HealDur'), 0.1))
amt = dmin(dget('HealLeft'), mul(rate, dt))
fhl.go(b.setm('DamageTaken', HERO, DBLV, dmax(sub(DT, amt), 0.0), HEROH, *P()))
setvar(fhl, 'HealLeft', DBLV, sub(dget('HealLeft'), amt))
f2 = fhl.join(fno)
setvar(f2, 'HPFrac', DBLV, clamp01(one_minus(dop('Divide_DoubleDouble', DT, dmax(dget('MaxHP'), 1.0)))))
HAS = icmp('Greater_IntInt', iget('Potions'), 0)
h1 = AND(AND(icmp('EqualEqual_IntInt', iget('HintStage'), 0), dcmp('Less_DoubleDouble', dget('HPFrac'), 0.5)), AND(HAS, NOT(DEAD)))
fh1, fnh1 = f2.iff(h1, 'IfHint1')
setvar(fh1, 'HintAt', DBLV, NOW)
setvar(fh1, 'HintStage', INTV, None, lit='1')
f3 = fh1.join(fnh1)
h2 = AND(AND(icmp('EqualEqual_IntInt', iget('HintStage'), 1), dcmp('Less_DoubleDouble', dget('HPFrac'), 0.3)),
         AND(AND(HAS, NOT(DEAD)), dcmp('Greater_DoubleDouble', sub(NOW, dget('HintAt')), 10.0)))
fh2, fnh2 = f3.iff(h2, 'IfHint2')
setvar(fh2, 'HintAt', DBLV, NOW)
setvar(fh2, 'HintStage', INTV, None, lit='2')
fl2 = fh2.join(fnh2, fnoh)
setvar(fl2, 'LastT', DBLV, NOW)

# ---------------------------------------------------------------- drawing helpers
def rect(fl_, x, y, w, h, color):
    n = b.call(HUDC, 'DrawRect', [st('RectColor', LC, default=color if isinstance(color, str) else WHITE), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], *P(), target=hud, tag='Rect')
    for pin, v in (('ScreenX', x), ('ScreenY', y), ('ScreenW', w), ('ScreenH', h)): b.wire(v, n, pin)
    if not isinstance(color, str): b.wire(color, n, 'RectColor')
    fl_.go(n)
def tex(fl_, texvar, x, y, w, h, tint_, blend='BLEND_Translucent'):
    n = b.call(HUDC, 'DrawTexture', [ob('Texture', TEXC), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('TextureU'), F('TextureV'),
               F('TextureUWidth', default='1.0'), F('TextureVHeight', default='1.0'), st('TintColor', LC, default=tint_ if isinstance(tint_, str) else WHITE),
               dict(BLENDP, default=blend), F('Scale', default='1.0'), bo('bScalePosition', default='false'), F('Rotation'),
               st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='Tex')
    b.wire(get(texvar, TEXV), n, 'Texture')
    for pin, v in (('ScreenX', x), ('ScreenY', y), ('ScreenW', w), ('ScreenH', h)): b.wire(v, n, pin)
    if not isinstance(tint_, str): b.wire(tint_, n, 'TintColor')
    fl_.go(n)
def drawmat(fl_, x, y, w, h):
    n = b.call(HUDC, 'DrawMaterial', [ob('Material', CLS('MaterialInterface')), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
               F('MaterialUWidth', default='1.0'), F('MaterialVHeight', default='1.0'), F('Scale', default='1.0'), bo('bScalePosition', default='false'),
               F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='Badge')
    b.wire(get('BadgeMID', MIDV), n, 'Material')
    for pin, v in (('ScreenX', x), ('ScreenY', y), ('ScreenW', w), ('ScreenH', h)): b.wire(v, n, pin)
    fl_.go(n)
def midvec(fl_, pname, color):
    n = b.call(MIDC, 'SetVectorParameterValue', [NAME_('ParameterName', pname), st('Value', LC, default=WHITE)], *P(), target=get('BadgeMID', MIDV), tag='MidSet')
    b.wire(color, n, 'Value'); fl_.go(n)
h0n = b.call(HUDC, 'GetTextSize', [S('Text', default='0'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')],
             *P(), target=hud, pure=True, const=True, tag='FontH0')
H0 = (h0n, 'OutHeight')
def text(fl_, s, x, y, lh, rgb, alpha=None):
    """text with a soft drop shadow; alpha None = opaque, else a wire 0..1 that fades both."""
    sc = dop('Divide_DoubleDouble', px(float(lh)), H0)
    shadow = col(0, 0, 0, 0.7) if alpha is None else mcol(0, 0, 0, mul(alpha, 0.7))
    main = col(*rgb) if alpha is None else mcol(rgb[0], rgb[1], rgb[2], alpha)
    for c, d in ((shadow, 2.0), (main, 0.0)):
        n = b.call(HUDC, 'DrawText', [S('Text', default=s if isinstance(s, str) else ''), st('TextColor', LC, default=c if isinstance(c, str) else WHITE), F('ScreenX'), F('ScreenY'),
                   dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0'), bo('bScalePosition', default='false')], *P(), target=hud, tag='Txt')
        if not isinstance(s, str): b.wire(s, n, 'Text')
        if not isinstance(c, str): b.wire(c, n, 'TextColor')
        b.wire(sc, n, 'Scale')
        b.wire(add(x, px(d)) if d else x, n, 'ScreenX'); b.wire(add(y, px(d)) if d else y, n, 'ScreenY')
        fl_.go(n)
def keycap(fl_, x, y, sz, lh, alpha=None, press=None):
    """dark key cap with a 2 U gold frame and a gold Q; press (0..1 wire) pushes it down 3 U and lights it."""
    y2 = add(y, mul(press, px(3.0))) if press is not None else y
    fill = col(0.06, 0.04, 0.025, 0.92) if alpha is None and press is None else \
        mcol(add(0.06, mul(press, 0.16)) if press is not None else 0.06, add(0.04, mul(press, 0.10)) if press is not None else 0.04, 0.025, mul(alpha, 0.92) if alpha is not None else 0.92)
    gold = col(0.85, 0.66, 0.34, 0.95) if alpha is None else mcol(0.85, 0.66, 0.34, mul(alpha, 0.95))
    rect(fl_, x, y2, px(sz), px(sz), fill)
    t = 2.0
    rect(fl_, x, y2, px(sz), px(t), gold); rect(fl_, x, add(y2, px(sz - t)), px(sz), px(t), gold)
    rect(fl_, x, y2, px(t), px(sz), gold); rect(fl_, add(x, px(sz - t)), y2, px(t), px(sz), gold)
    text(fl_, 'Q', add(x, px(sz * 0.5 - lh * 0.36)), add(y2, px(sz * 0.5 - lh * 0.55)), lh, (0.98, 0.86, 0.56), alpha)

# ---------------------------------------------------------------- state -> badge parameters
cool = clamp01(dop('Divide_DoubleDouble', sub(dget('CoolUntil'), NOW), dmax(dget('Cooldown'), 0.1)))
empty = one_minus(clamp01(i2d(iget('Potions'))))
refuse = one_minus(ramp(sub(NOW, dget('RefuseAt')), 0.0, 0.4))
healing = dcmp('Greater_DoubleDouble', dget('HealLeft'), 0.0)
healF = b.self_(None, None, healing, *P(), da='1.0', db='0.0')
age = sub(NOW, dget('HintAt'))
hintOn = AND(icmp('GreaterEqual_IntInt', iget('HintStage'), 1), dcmp('Less_DoubleDouble', age, 4.6))
hA = b.self_(dmin(ramp(age, 0.0, 0.3), one_minus(ramp(age, 4.0, 0.6))), None, hintOn, *P(), db='0.0')
low = AND(AND(dcmp('Less_DoubleDouble', dget('HPFrac'), 0.3), icmp('Greater_IntInt', iget('Potions'), 0)),
          AND(dcmp('GreaterEqual_DoubleDouble', NOW, dget('CoolUntil')), NOT(healing)))
lowF = b.self_(None, None, low, *P(), da='0.55', db='0.0')
goldGlow = dmax(hA, lowF)
midvec(fl2, 'Pot', mcol(cool, goldGlow, empty, dmax(refuse, 0.001)))
midvec(fl2, 'Pot2', mcol(healF, 0.0, 0.0, 1.0))

# ---------------------------------------------------------------- the slot: badge left of the HP bar, in the ability row
CX = mul(SXd, 0.5)
shake = mul(dsin(mul(sub(NOW, dget('RefuseAt')), 55.0)), mul(refuse, 6.0))
BXc = add(CX, px(add(-177.0, shake)))
BYc = sub(SYd, px(73.0))
BQ = 84.0
drawmat(fl2, sub(BXc, px(BQ / 2)), sub(BYc, px(BQ / 2)), px(BQ), px(BQ))
keycap(fl2, sub(BXc, px(38.0)), sub(BYc, px(40.0)), 22.0, 16.0)
text(fl2, b.concat(None, istr(iget('Potions')), *P(), da='x'), add(BXc, px(12.0)), add(BYc, px(10.0)), 20, (0.98, 0.92, 0.80))

# heal glow over the HP bar (additive soft glow, pulsing)
fg, fng = fl2.iff(healing, 'IfHealGlow')
pulse = add(0.75, mul(dsin(mul(NOW, 7.0)), 0.25))
tex(fg, 'GlowTex', sub(CX, px(150.0)), sub(SYd, px(97.0)), px(300.0), px(50.0), mcol(0.35, 1.0, 0.45, mul(pulse, 0.22)), 'BLEND_Translucent')
fl3 = fg.join(fng)

# ---------------------------------------------------------------- the Q hint (motion graphic)
fhint, fnhint = fl3.iff(hintOn, 'IfHint')
sIn = smooth(ramp(age, 0.0, 0.35))
PW, PH = 420.0, 80.0
plX = sub(BXc, px(PW / 2))
plY = sub(BYc, px(add(PH + 56.0, mul(one_minus(sIn), -18.0))))
tex(fhint, 'PlateTex', plX, plY, px(PW), px(PH), mcol(1.0, 1.0, 1.0, hA))
rect(fhint, sub(BXc, px(1.5)), add(plY, px(PH - 4.0)), px(3.0), sub(sub(BYc, px(34.0)), add(plY, px(PH - 4.0))), mcol(0.85, 0.66, 0.34, mul(hA, 0.9)))
press = clamp01(sub(mul(dsin(mul(age, TAU * 1.25)), 3.0), 2.0))
keycap(fhint, add(plX, px(26.0)), add(plY, px(19.0)), 40.0, 26.0, hA, press)
text(fhint, 'Drink a Healing Potion', add(plX, px(84.0)), add(plY, px(13.0)), 23, (0.98, 0.86, 0.56), hA)
text(fhint, 'Restores 35% health over 3 s', add(plX, px(84.0)), add(plY, px(45.0)), 16, (0.86, 0.78, 0.64), hA)
fl4 = fhint.join(fnhint)

# ---------------------------------------------------------------- Vesna's shop: the APOTHECARY row (unchanged from #74)
mpcg = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', CLS('MaterialParameterCollection')), dobj=MPC), NAME_('ParameterName', 'Shop'),
             st('ReturnValue', LC, out=True)], *P(), tag='GetShop')
fl4.go(mpcg)
brk = b.math('BreakColor', [(st('InColor', LC), (mpcg, 'ReturnValue'))], fl('R', out=True, default='0.0'), *P())
for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
paused = b.lib(GS, 'IsGamePaused', [WC(), bo('ReturnValue', out=True, default='false')], *P(), pure=True, tag='Paused')
fs, fns = fl4.iff(AND(dcmp('Greater_DoubleDouble', brk, 0.5), (paused, 'ReturnValue')), 'IfShop')
PX, PY = px(dget('PanelX')), px(dget('PanelY'))
def PXo(dx): return add(PX, px(float(dx)))
def PYo(dy): return add(PY, px(float(dy)))
W_, H_ = 470.0, 88.0
inside = AND(AND(dcmp('GreaterEqual_DoubleDouble', MX, PX), dcmp('Less_DoubleDouble', MX, PXo(W_))),
             AND(dcmp('GreaterEqual_DoubleDouble', MY, PY), dcmp('Less_DoubleDouble', MY, PYo(H_))))
cast(G, 'ppAsZHud', ZHUD, 'AsBP Zombie HUD', *P(), pure=True); b.wire(hud, 'ppAsZHud', 'Object')
ZH = ('ppAsZHud', 'AsBP Zombie HUD')
GOLD = b.getm('Gold', ZHUD, INTV, ZH, *P())
afford = icmp('GreaterEqual_IntInt', GOLD, iget('Price'))
rect(fs, PX, PY, px(W_), px(H_), selc(col(0.10, 0.07, 0.04, 0.92), col(0.04, 0.03, 0.02, 0.88), inside))
rect(fs, PX, PY, px(W_), px(2.0), col(0.80, 0.62, 0.34, 0.9))
rect(fs, PX, PYo(H_ - 2), px(W_), px(2.0), col(0.80, 0.62, 0.34, 0.9))
tex(fs, 'IconTex', PXo(8), PYo(6), px(76.0), px(76.0), col(1, 1, 1))
text(fs, 'Health Potion', PXo(92), PYo(10), 26, (0.98, 0.88, 0.62))
text(fs, 'Q: heals 35% over 3 s', PXo(92), PYo(48), 18, (0.80, 0.70, 0.55))
pricec = selc(col(0.96, 0.84, 0.56), col(0.88, 0.36, 0.28), afford)
sc_ = dop('Divide_DoubleDouble', px(26.0), H0)
for c, d in ((col(0, 0, 0, 0.7), 2.0), (pricec, 0.0)):
    n = b.call(HUDC, 'DrawText', [S('Text', default=''), st('TextColor', LC, default=c if isinstance(c, str) else WHITE), F('ScreenX'), F('ScreenY'),
               dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0'), bo('bScalePosition', default='false')], *P(), target=hud, tag='Txt')
    b.wire(b.concat(istr(iget('Price')), None, *P(), db=' G'), n, 'Text')
    if not isinstance(c, str): b.wire(c, n, 'TextColor')
    b.wire(sc_, n, 'Scale'); b.wire(PXo(330 + d), n, 'ScreenX'); b.wire(PYo(14 + d), n, 'ScreenY')
    fs.go(n)
text(fs, 'BUY  [B]', PXo(330), PYo(50), 20, (0.98, 0.92, 0.80))
fb, fnb = fs.iff(OR(AND(key('LeftMouseButton'), inside), key('B')), 'IfBuy')
fok, fpoor = fb.iff(afford, 'IfAfford')
fok.go(b.setm('Gold', ZHUD, INTV, iop('Subtract_IntInt', GOLD, iget('Price')), ZH, *P()))
setvar(fok, 'Potions', INTV, iop('Add_IntInt', iget('Potions'), 1))
sound(fok, SND_BUY)
sound(fpoor, SND_FAIL)

open(os.path.join(OUT, 'BPC_PotionBelt_polish_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_PotionBelt polish: nodes %d, links %d' % (len(G.nodes), len(G.links)))
