# #74 health potions (i5 core, 2026-11-01): graph of the NEW component BPC_PotionBelt (on BP_ZombieHUD) + its 3-node hook.
#   python gen_potion74.py  (on i5: UE's Engine/Binaries/ThirdParty/Python3/Win64/python.exe -I)
#   -> build/BPC_PotionBelt_graph.txt, build/ZombieHUD_PotionHook_graph.txt
# Rules (vice master's decision on #74): key Q drinks one potion: heals HealPct (35 %) of MaxHP over HealDur (3 s), then an
# 8 s cooldown; Vesna sells it for 60 gold. Hero HP = MaxHP (100) - DamageTaken on BP_ThirdPersonCharacter (#73), so the
# heal lowers DamageTaken a little every frame (game time: nothing happens while paused, never below 0, not when dead).
# DrawPotion(Hud), every frame from BP_ZombieHUD's DrawHUD:
#   - the potion slot left of the HP bar: icon (dim when empty), count, a Q key cap, a dark cooldown curtain that drops;
#   - while Vesna's shop is open (MPC_SkillTree Shop.R > 0.5 and paused): an APOTHECARY row "Health Potion  60 G  BUY [B]"
#     at PanelX/PanelY (1080p units, tune on the Class Defaults); click it or press B: Gold -= Price, Potions += 1.
# The builder helpers (bpkit, Flow, dop, ...) are the #411 generator's, loaded from its preamble.
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(_here, '..', 'castle-scroll-411', 'gen_scroll411.py'), encoding='utf-8').read()
_src = _src[:_src.index('# ---------------------------------------------------------------- event, viewport, unit')]
__file__ = os.path.join(_here, '..', 'castle-scroll-411', 'gen_scroll411.py')   # the preamble resolves REPO from its own folder
exec(compile(_src, 'gen_scroll411-preamble', 'exec'))
HERE = _here; OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
G = Graph(); b = B(G, 'pt'); XY[0], XY[1] = 0, 300

HUDC = CLS('HUD')
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
BELT = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_PotionBelt', 'BPC_PotionBelt')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
SND_BUY, SND_FAIL = '/Game/CastleDefender/UI/Trade/SFX_TradeBuy.SFX_TradeBuy', '/Game/CastleDefender/UI/Trade/SFX_TradeFail.SFX_TradeFail'
DBLV, INTV = D('v', default='0.0'), it('v', default='0')
BLENDP = {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': 'BLEND_Translucent'}


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
def dmin(a, c): return b.math('FMin', [(D('A', default='0.0'), a), (D('B', default='0.0'), c)], D('ReturnValue', out=True), *P())
def selc(a, c, pick): return b.math('SelectColor', [(st('A', LC, default=a), None), (st('B', LC, default=c), None), (bo('bPickA', default='false'), pick)], st('ReturnValue', LC, out=True), *P())

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
dt = b.math('FClamp', [(D('Value', default='0.0'), dop('Subtract_DoubleDouble', NOW, dget('LastT'))), (D('Min', default='0.0'), None), (D('Max', default='0.1'), None)],
            D('ReturnValue', out=True), *P())
setvar(fl0, 'LastT', DBLV, NOW)

# ---------------------------------------------------------------- drink (Q) + heal over time
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], *P(), pure=True, tag='Pawn')
cast(G, 'ptAsHero', HERO, 'AsBP Third Person Character', *P(), pure=True); b.wire((pp, 'ReturnValue'), 'ptAsHero', 'Object')
HEROH = ('ptAsHero', 'AsBP Third Person Character')
fh, fnoh = fl0.iff(b.valid(HEROH, *P()), 'IfHero')
DT = b.getm('DamageTaken', HERO, DBLV, HEROH, *P())
DEAD = b.getm('IsDead', HERO, bo('v', default='false'), HEROH, *P())
drink = AND(AND(key('Q'), icmp('Greater_IntInt', iget('Potions'), 0)),
            AND(dcmp('GreaterEqual_DoubleDouble', NOW, dget('CoolUntil')), AND(NOT(DEAD), dcmp('Greater_DoubleDouble', DT, 0.5))))
fd, fnd = fh.iff(drink, 'IfDrink')
setvar(fd, 'Potions', INTV, iop('Subtract_IntInt', iget('Potions'), 1))
setvar(fd, 'HealLeft', DBLV, dop('Add_DoubleDouble', dget('HealLeft'), dop('Multiply_DoubleDouble', dget('HealPct'), dget('MaxHP'))))
setvar(fd, 'CoolUntil', DBLV, dop('Add_DoubleDouble', NOW, dget('Cooldown')))
sound(fd, SND_BUY, '0.6')
f1 = fd.join(fnd)
fhl, fno = f1.iff(dcmp('Greater_DoubleDouble', dget('HealLeft'), 0.0), 'IfHealing')
rate = dop('Divide_DoubleDouble', dop('Multiply_DoubleDouble', dget('HealPct'), dget('MaxHP')), dmax(dget('HealDur'), 0.1))
amt = dmin(dget('HealLeft'), dop('Multiply_DoubleDouble', rate, dt))
fhl.go(b.setm('DamageTaken', HERO, DBLV, dmax(dop('Subtract_DoubleDouble', DT, amt), 0.0), HEROH, *P()))
setvar(fhl, 'HealLeft', DBLV, dop('Subtract_DoubleDouble', dget('HealLeft'), amt))
fl2 = fhl.join(fno, fnoh)

# ---------------------------------------------------------------- drawing helpers
def rect(fl_, x, y, w, h, color):
    n = b.call(HUDC, 'DrawRect', [st('RectColor', LC, default=color if isinstance(color, str) else WHITE), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], *P(), target=hud, tag='Rect')
    for pin, v in (('ScreenX', x), ('ScreenY', y), ('ScreenW', w), ('ScreenH', h)): b.wire(v, n, pin)
    if not isinstance(color, str): b.wire(color, n, 'RectColor')
    fl_.go(n)
def tex(fl_, x, y, w, h, tint_):
    n = b.call(HUDC, 'DrawTexture', [ob('Texture', TEXC), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('TextureU'), F('TextureV'),
               F('TextureUWidth', default='1.0'), F('TextureVHeight', default='1.0'), st('TintColor', LC, default=tint_ if isinstance(tint_, str) else WHITE), BLENDP,
               F('Scale', default='1.0'), bo('bScalePosition', default='false'), F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='Icon')
    b.wire(get('IconTex', ob('v', TEX2D)), n, 'Texture')
    for pin, v in (('ScreenX', x), ('ScreenY', y), ('ScreenW', w), ('ScreenH', h)): b.wire(v, n, pin)
    if not isinstance(tint_, str): b.wire(tint_, n, 'TintColor')
    fl_.go(n)
h0n = b.call(HUDC, 'GetTextSize', [S('Text', default='0'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')],
             *P(), target=hud, pure=True, const=True, tag='FontH0')
H0 = (h0n, 'OutHeight')
def text(fl_, s, x, y, lh, color):
    sc = dop('Divide_DoubleDouble', px(float(lh)), H0)
    for c, d in ((col(0, 0, 0, 0.7), 2.0), (color, 0.0)):
        n = b.call(HUDC, 'DrawText', [S('Text', default=s if isinstance(s, str) else ''), st('TextColor', LC, default=c if isinstance(c, str) else WHITE), F('ScreenX'), F('ScreenY'),
                   dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0'), bo('bScalePosition', default='false')], *P(), target=hud, tag='Txt')
        if not isinstance(s, str): b.wire(s, n, 'Text')
        if not isinstance(c, str): b.wire(c, n, 'TextColor')
        b.wire(sc, n, 'Scale')
        b.wire(dop('Add_DoubleDouble', x, px(d)) if d else x, n, 'ScreenX'); b.wire(dop('Add_DoubleDouble', y, px(d)) if d else y, n, 'ScreenY')
        fl_.go(n)

# ---------------------------------------------------------------- the slot, left of the HP bar (bottom centre)
SXL = dop('Add_DoubleDouble', dop('Multiply_DoubleDouble', SXd, 0.5), px(-232.0))
SYT = dop('Subtract_DoubleDouble', SYd, px(122.0))
def X(dx): return dop('Add_DoubleDouble', SXL, px(float(dx)))
def Y(dy): return dop('Add_DoubleDouble', SYT, px(float(dy)))
SZ_ = 78.0
has = icmp('Greater_IntInt', iget('Potions'), 0)
rect(fl2, X(-4), Y(-4), px(SZ_ + 8), px(SZ_ + 8), col(0.03, 0.02, 0.015, 0.6))
tex(fl2, X(0), Y(0), px(SZ_), px(SZ_), selc(col(1, 1, 1), col(0.38, 0.36, 0.34, 0.75), has))
fc, fnc = fl2.iff(dcmp('Less_DoubleDouble', NOW, dget('CoolUntil')), 'IfCool')
frac = clamp01(dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', dget('CoolUntil'), NOW), dmax(dget('Cooldown'), 0.1)))
rect(fc, X(0), Y(0), px(SZ_), dop('Multiply_DoubleDouble', px(SZ_), frac), col(0.0, 0.0, 0.0, 0.62))
fl3 = fc.join(fnc)
text(fl3, 'Q', X(4), Y(2), 20, col(0.96, 0.84, 0.56))
text(fl3, b.concat(None, istr(iget('Potions')), *P(), da='x'), X(SZ_ - 30), Y(SZ_ - 26), 22, col(0.98, 0.92, 0.80))

# ---------------------------------------------------------------- Vesna's shop: the APOTHECARY row
mpcg = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', CLS('MaterialParameterCollection')), dobj=MPC), NAME_('ParameterName', 'Shop'),
             st('ReturnValue', LC, out=True)], *P(), tag='GetShop')
fl3.go(mpcg)
brk = b.math('BreakColor', [(st('InColor', LC), (mpcg, 'ReturnValue'))], fl('R', out=True, default='0.0'), *P())
for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
paused = b.lib(GS, 'IsGamePaused', [WC(), bo('ReturnValue', out=True, default='false')], *P(), pure=True, tag='Paused')
fs, fns = fl3.iff(AND(dcmp('Greater_DoubleDouble', brk, 0.5), (paused, 'ReturnValue')), 'IfShop')
PX, PY = px(dget('PanelX')), px(dget('PanelY'))
def PXo(dx): return dop('Add_DoubleDouble', PX, px(float(dx)))
def PYo(dy): return dop('Add_DoubleDouble', PY, px(float(dy)))
W_, H_ = 470.0, 88.0
inside = AND(AND(dcmp('GreaterEqual_DoubleDouble', MX, PX), dcmp('Less_DoubleDouble', MX, PXo(W_))),
             AND(dcmp('GreaterEqual_DoubleDouble', MY, PY), dcmp('Less_DoubleDouble', MY, PYo(H_))))
cast(G, 'ptAsZHud', ZHUD, 'AsBP Zombie HUD', *P(), pure=True); b.wire(hud, 'ptAsZHud', 'Object')
ZH = ('ptAsZHud', 'AsBP Zombie HUD')
GOLD = b.getm('Gold', ZHUD, INTV, ZH, *P())
afford = icmp('GreaterEqual_IntInt', GOLD, iget('Price'))
rect(fs, PX, PY, px(W_), px(H_), selc(col(0.10, 0.07, 0.04, 0.92), col(0.04, 0.03, 0.02, 0.88), inside))
rect(fs, PX, PY, px(W_), px(2.0), col(0.80, 0.62, 0.34, 0.9))
rect(fs, PX, PYo(H_ - 2), px(W_), px(2.0), col(0.80, 0.62, 0.34, 0.9))
tex(fs, PXo(8), PYo(6), px(76.0), px(76.0), col(1, 1, 1))
text(fs, 'Health Potion', PXo(92), PYo(10), 26, col(0.98, 0.88, 0.62))
text(fs, 'Q: heals 35% over 3 s', PXo(92), PYo(48), 18, col(0.80, 0.70, 0.55))
text(fs, b.concat(istr(iget('Price')), None, *P(), db=' G'), PXo(330), PYo(14), 26, selc(col(0.96, 0.84, 0.56), col(0.88, 0.36, 0.28), afford))
text(fs, 'BUY  [B]', PXo(330), PYo(50), 20, col(0.98, 0.92, 0.80))
fb, fnb = fs.iff(OR(AND(key('LeftMouseButton'), inside), key('B')), 'IfBuy')
fok, fpoor = fb.iff(afford, 'IfAfford')
fok.go(b.setm('Gold', ZHUD, INTV, iop('Subtract_IntInt', GOLD, iget('Price')), ZH, *P()))
setvar(fok, 'Potions', INTV, iop('Add_IntInt', iget('Potions'), 1))
sound(fok, SND_BUY)
sound(fpoor, SND_FAIL)

open(os.path.join(OUT, 'BPC_PotionBelt_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_PotionBelt: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---------------------------------------------------------------- BP_ZombieHUD hook: Self -> GetComponentByClass -> DrawPotion(Hud = self)
H = Graph(); hb = B(H, 'pthk')
me = hb.self_node(0, 200)
fc_ = hb.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Game/CastleDefender/Gameplay/Castle/BPC_PotionBelt.BPC_PotionBelt_C'),
              ob('ReturnValue', BELT, out=True)], 250, 200, target=me, pure=True, const=True, tag='FindBelt')
callfn(H, 'PtHookDraw', BELT, 'DrawPotion', [ob('Hud', HUDC)], x=520, y=0)
H.link(fc_, 'ReturnValue', 'PtHookDraw', 'self'); H.link(me[0], me[1], 'PtHookDraw', 'Hud')
open(os.path.join(OUT, 'ZombieHUD_PotionHook_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(H.render())
print('ZombieHUD potion hook: nodes %d' % len(H.nodes))
