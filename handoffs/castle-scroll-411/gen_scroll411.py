# #411 castle scroll (i5 core, 2026-11-01): generates the graph of the NEW component BPC_CastleScroll and the 3-node hook
# for BP_ZombieHUD.   python gen_scroll411.py   (any Python 3; on i5 use UE's: Engine/Binaries/ThirdParty/Python3/Win64/python.exe -I)
#   -> build/BPC_CastleScroll_graph.txt   (paste into BPC_CastleScroll's EventGraph)
#   -> build/ZombieHUD_ScrollHook_graph.txt (paste into BP_ZombieHUD's EventGraph; rewire_hook411_ue.py wires it)
# DrawScroll(Hud) runs inside BP_ZombieHUD's DrawHUD, where the ORE / FOOD text lines were (UX_CallFunction_23 -> here
# -> K2Node_IfThenElse_H296). Each frame:
#   - the castle medallion T_HUD_CastleKey at (16, 150) U, 84 U square (U = viewport height / 1080), brighter on hover / open;
#   - click on it or key C toggles Open (+ the trade swipe sound);
#   - T eases 0 -> 1 in 0.4 s (1 -> 0 in 0.36 s); e = 1 - (1 - T)^3;
#   - the #295 vellum scroll (M_NoticeBanner via a MID, Roll 1) unrolls to the RIGHT from the medallion: its left roller
#     stays put under the icon and the sheet grows from 300 U (rollers together) to 900 U wide (Aspect = width / 300);
#   - the text fades in as the right roller passes it: column 1 (Iron, Copper, Silver, Gold ore), the title, column 2
#     (Starmetal, Food, Farmers); gold ink with a soft shadow, Font_Cinzel, sized from the font's measured line height.
# Data: BP_ZombieHUD Ore[0..4] (Fe, Cu, Ag, Au, Star), Food, Farmers (the same variables the old text lines read).
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))           # (bpkit's * import overwrites HERE)
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)

COMP, HUDC, TEXC, TEX2D, MATL = CLS('ActorComponent'), CLS('HUD'), CLS('Texture'), CLS('Texture2D'), CLS('KismetMaterialLibrary')
SCROLLC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll', 'BPC_CastleScroll')
ZHUD = BPC('/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', 'BP_ZombieHUD')
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
FONTC = '"/Script/CoreUObject.Class\'/Script/Engine.Font\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
V2D = '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector2D\'"'
BLEND = '"/Script/CoreUObject.Enum\'/Script/Engine.EBlendMode\'"'
SND = '/Game/CastleDefender/UI/Trade/SFX_TradeSwipe.SFX_TradeSwipe'
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
def col(r, g_, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g_, b_, a)
WHITE = col(1, 1, 1)

G = Graph(); b = B(G, 'cs')
XY = [0, 300]
def P():
    XY[0] += 280
    if XY[0] > 12000: XY[0] = 0; XY[1] += 220
    return XY[0], XY[1]
def isnum(v): return isinstance(v, (int, float))
def dop(m, a, c): return b.d2(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(float(a)) if isnum(a) else '0.0', db=str(float(c)) if isnum(c) else '0.0')
def dcmp(m, a, c): return b.dcmp(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(float(a)) if isnum(a) else '0.0', db=str(float(c)) if isnum(c) else '0.0')
AND = lambda a, c: b.b2('BooleanAND', a, c, *P())
OR = lambda a, c: b.b2('BooleanOR', a, c, *P())
NOT = lambda a: b.bnot(a, *P())
i2d = lambda a: b.i2d(a, *P())
def clamp01(v): return b.math('FClamp', [(D('Value', default='0.0'), v), (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), *P())
def ramp(v, a0, w):   # clamp((v - a0) / w, 0, 1)
    return clamp01(dop('Divide_DoubleDouble', dop('Subtract_DoubleDouble', v, float(a0)), float(w)))
def istr(src):
    n = b.lib(CLS('KismetStringLibrary'), 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], *P(), pure=True); b.wire(src, n, 'InInt'); return (n, 'ReturnValue')
def get(var, pin): return b.get(var, pin, *P())

class Flow:
    def __init__(s, *srcs): s.c = list(srcs)
    def go(s, node, inp='execute', out='then'):
        for a, p in s.c: G.link(a, p, node, inp)
        s.c = [(node, out)] if out else []; return node
    def iff(s, cond, tag='If'):
        n = b.branch(cond, *P(), tag=tag); s.go(n, out=None); return Flow((n, 'then')), Flow((n, 'else'))
    def join(s, *others):
        for o in others: s.c += o.c
        return s
def setvar(fl_, var, pin, src, lit=None):
    n = b.set(var, pin, None if lit is not None else src, *P())
    if lit is not None: G.nodes[-1][3][2]['default'] = lit
    fl_.go(n); return n

# ---------------------------------------------------------------- event, viewport, unit
b.event('DrawScroll', [ob('Hud', HUDC)], 0, 0)
hud = ('DrawScroll', 'Hud')
fl0 = Flow(('DrawScroll', 'then'))
pcn = b.call(HUDC, 'GetOwningPlayerController', [ob('ReturnValue', PCON, out=True)], *P(), target=hud, pure=True, const=True, tag='PC')
PC = (pcn, 'ReturnValue')
vs = b.call(PCON, 'GetViewportSize', [it('SizeX', out=True, default='0'), it('SizeY', out=True, default='0')], *P(), target=PC, pure=True, const=True, tag='ViewSize')
U = dop('Divide_DoubleDouble', i2d((vs, 'SizeY')), 1080.0)
_px = {}
def px(v):   # v in U (number, cached) or a handle in U
    if isnum(v):
        if v not in _px: _px[v] = dop('Multiply_DoubleDouble', U, float(v))
        return _px[v]
    return dop('Multiply_DoubleDouble', U, v)
mp = b.call(PCON, 'GetMousePosition', [F('LocationX', out=True), F('LocationY', out=True), bo('ReturnValue', out=True, default='false')], *P(), target=PC, pure=True, const=True, tag='Mouse')
MX, MY = (mp, 'LocationX'), (mp, 'LocationY')
def key(name):
    n = b.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default=name), bo('ReturnValue', out=True, default='false')], *P(), target=PC, pure=True, const=True, tag='Key' + name[:10])
    return (n, 'ReturnValue')
now = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], *P(), pure=True, tag='RealNow'); NOW = (now, 'ReturnValue')

# ---------------------------------------------------------------- input: click on the medallion or C
IX, IY, IS = 16, 150, 84
hover = AND(AND(dcmp('GreaterEqual_DoubleDouble', MX, px(IX)), dcmp('Less_DoubleDouble', MX, px(IX + IS))),
            AND(dcmp('GreaterEqual_DoubleDouble', MY, px(IY)), dcmp('Less_DoubleDouble', MY, px(IY + IS))))
toggle = OR(AND(key('LeftMouseButton'), hover), key('C'))
ft, fn_ = fl0.iff(toggle, 'IfToggle')
setvar(ft, 'Open', BOOL, NOT(get('Open', BOOL)))
sn = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', CLS('SoundBase')), dobj=SND), fl('VolumeMultiplier', default='0.700000', advanced=True),
           fl('PitchMultiplier', default='1.000000', advanced=True), fl('StartTime', default='0.000000', advanced=True),
           dict(ob('ConcurrencySettings', CLS('SoundConcurrency')), advanced=True), dict(ob('OwningActor', ACT), advanced=True),
           dict(bo('bIsUISound', default='true'), advanced=True)], *P(), tag='SndScroll')
ft.go(sn)
fl1 = ft.join(fn_)

# ---------------------------------------------------------------- animation: T (0..1), e = 1 - (1 - T)^3
dt = b.math('FClamp', [(D('Value', default='0.0'), dop('Subtract_DoubleDouble', NOW, get('LastT', DBL))), (D('Min', default='0.0'), None), (D('Max', default='0.1'), None)],
            D('ReturnValue', out=True), *P())
rate = b.self_(None, None, get('Open', BOOL), *P(), da='2.5', db='-2.8')
setvar(fl1, 'T', DBL, clamp01(dop('Add_DoubleDouble', get('T', DBL), dop('Multiply_DoubleDouble', dt, rate))))
setvar(fl1, 'LastT', DBL, NOW)
Tv = get('T', DBL)
om = dop('Subtract_DoubleDouble', 1.0, Tv)
E = dop('Subtract_DoubleDouble', 1.0, dop('Multiply_DoubleDouble', dop('Multiply_DoubleDouble', om, om), om))

# ---------------------------------------------------------------- the medallion
lit = OR(hover, get('Open', BOOL))
tint = b.math('SelectColor', [(st('A', LC, default=col(1.12, 1.06, 0.96)), None), (st('B', LC, default=col(0.92, 0.90, 0.88)), None), (bo('bPickA', default='false'), lit)],
              st('ReturnValue', LC, out=True), *P())
dtx = b.call(HUDC, 'DrawTexture', [ob('Texture', TEXC), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('TextureU'), F('TextureV'),
             F('TextureUWidth', default='1.0'), F('TextureVHeight', default='1.0'), st('TintColor', LC, default=WHITE),
             {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': 'BLEND_Translucent'}, F('Scale', default='1.0'), bo('bScalePosition', default='false'),
             F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='DrawIcon')
b.wire(get('IconTex', ob('v', TEX2D)), dtx, 'Texture'); b.wire(tint, dtx, 'TintColor')
for pin, v in (('ScreenX', IX), ('ScreenY', IY), ('ScreenW', IS), ('ScreenH', IS)): b.wire(px(v), dtx, pin)
fl1.go(dtx)

# ---------------------------------------------------------------- the scroll (only while T > 0)
fs, fnone = fl1.iff(dcmp('Greater_DoubleDouble', Tv, 0.001), 'IfShown')
SH, SW0, SW1, SY0 = 300.0, 300.0, 900.0, 240.0      # sheet height, closed width, open width, top (U)
QX = IX - 0.38 * SH                                 # quad left: the left roller (0.38..0.62 H) sits under the medallion
WU = dop('Add_DoubleDouble', SW0, dop('Multiply_DoubleDouble', E, SW1 - SW0))     # current width in U
fm, fhave = fs.iff(b.valid(get('Mid', ob('v', MID)), *P()), 'IfMid')            # then = valid
mk = b.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), ob('Parent', MATI), NAME_('OptionalName', 'None'),
           {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None', 'advanced': True},
           ob('ReturnValue', MID, out=True)], *P(), tag='MakeMid')
b.wire(get('ScrollMat', ob('v', MATI)), mk, 'Parent')
fhave.go(mk)
setvar(fhave, 'Mid', ob('v', MID), (mk, 'ReturnValue'))
fd = fm.join(fhave)
for pname, val in (('Roll', 1.0), ('Aspect', dop('Divide_DoubleDouble', WU, SH)), ('Fade', clamp01(dop('Multiply_DoubleDouble', Tv, 5.0))), ('Tier', 0.0)):
    n = b.call(MID, 'SetScalarParameterValue', [NAME_('ParameterName', pname), F('Value', default=str(val) if isnum(val) else '0.0')], *P(),
               target=get('Mid', ob('v', MID)), tag='Par' + pname)
    if not isnum(val): b.wire(val, n, 'Value')
    fd.go(n)
dm = b.call(HUDC, 'DrawMaterial', [ob('Material', MATI), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
            F('MaterialUWidth', default='1.0'), F('MaterialVHeight', default='1.0'), F('Scale', default='1.0'), bo('bScalePosition', default='false'),
            F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='DrawScroll')
b.wire(get('Mid', ob('v', MID)), dm, 'Material')
b.wire(px(QX), dm, 'ScreenX'); b.wire(px(SY0), dm, 'ScreenY'); b.wire(px(WU), dm, 'ScreenW'); b.wire(px(SH), dm, 'ScreenH')
fd.go(dm)

# ---------------------------------------------------------------- text (Cinzel, gold ink + shadow, fades in behind the roller)
h0n = b.call(HUDC, 'GetTextSize', [S('Text', default='0'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')],
             *P(), target=hud, pure=True, const=True, tag='FontH0')
H0 = (h0n, 'OutHeight')
_sc = {}
def tscale(lh):
    if lh not in _sc: _sc[lh] = dop('Divide_DoubleDouble', px(float(lh)), H0)
    return _sc[lh]
def ink(rgb, alpha, a_mul=1.0):
    a = alpha if a_mul == 1.0 else dop('Multiply_DoubleDouble', alpha, a_mul)
    return b.math('MakeColor', [(fl('R', default=str(rgb[0])), None), (fl('G', default=str(rgb[1])), None), (fl('B', default=str(rgb[2])), None), (fl('A', default='1.0'), a)],
                  st('ReturnValue', LC, out=True), *P())
def text(fl_, s, x, ycen, lh, rgb, alpha, anchor='l'):
    sc = tscale(lh)
    xs = px(x)
    if anchor != 'l':
        ts = b.call(HUDC, 'GetTextSize', [S('Text', default=s if isinstance(s, str) else ''), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT),
                    F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='Measure')
        if not isinstance(s, str): b.wire(s, ts, 'Text')
        b.wire(sc, ts, 'Scale')
        wdt = (ts, 'OutWidth') if anchor == 'r' else dop('Multiply_DoubleDouble', (ts, 'OutWidth'), 0.5)
        xs = dop('Subtract_DoubleDouble', xs, wdt)
    ys = dop('Subtract_DoubleDouble', px(ycen), dop('Multiply_DoubleDouble', dop('Multiply_DoubleDouble', sc, H0), 0.5))
    for k, (c, dx) in enumerate(((ink((0.0, 0.0, 0.0), alpha, 0.55), 2.0), (ink(rgb, alpha), 0.0))):
        n = b.call(HUDC, 'DrawText', [S('Text', default=s if isinstance(s, str) else ''), st('TextColor', LC, default=WHITE), F('ScreenX'), F('ScreenY'),
                   dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0'), bo('bScalePosition', default='false')], *P(), target=hud, tag='Txt')
        if not isinstance(s, str): b.wire(s, n, 'Text')
        b.wire(c, n, 'TextColor'); b.wire(sc, n, 'Scale')
        b.wire(dop('Add_DoubleDouble', xs, px(dx)) if dx else xs, n, 'ScreenX'); b.wire(dop('Add_DoubleDouble', ys, px(dx)) if dx else ys, n, 'ScreenY')
        fl_.go(n)

zh = cast(G, 'csAsZHud', ZHUD, 'AsBP Zombie HUD', *P(), pure=True); b.wire(hud, 'csAsZHud', 'Object')
ZH = ('csAsZHud', 'AsBP Zombie HUD')
oreA = b.getm('Ore', ZHUD, arr(INT), ZH, *P())
def ore(i):
    n = b.name('Ore%d' % i)
    G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(INT, name='Array')), it('Dimension 1', default=str(i)), dict(INT, name='Output', out=True)], *P())
    b.wire(oreA, n, 'Array'); return (n, 'Output')
FOOD, FARM = b.getm('Food', ZHUD, INT, ZH, *P()), b.getm('Farmers', ZHUD, INT, ZH, *P())
LABEL, VALUE, TITLE = (0.80, 0.64, 0.40), (0.96, 0.84, 0.56), (0.98, 0.88, 0.62)
a1, aT, a2 = ramp(E, 0.50, 0.15), ramp(E, 0.62, 0.20), ramp(E, 0.86, 0.12)
text(fd, 'THE KEEP', 352, 47, 24, TITLE, aT, anchor='c')
ROWS = (90, 128, 166, 204)
for (lab, src), y in zip((('Iron', ore(0)), ('Copper', ore(1)), ('Silver', ore(2)), ('Gold ore', ore(3))), ROWS):
    text(fd, lab, 104, y, 24, LABEL, a1); text(fd, istr(src), 330, y, 24, VALUE, a1, anchor='r')
for (lab, src), y in zip((('Starmetal', ore(4)), ('Food', FOOD), ('Farmers', FARM)), ROWS):
    text(fd, lab, 356, y, 24, LABEL, a2); text(fd, istr(src), 600, y, 24, VALUE, a2, anchor='r')

open(os.path.join(OUT, 'BPC_CastleScroll_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_CastleScroll: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---------------------------------------------------------------- BP_ZombieHUD hook: Self -> GetComponentByClass -> DrawScroll(Hud = self)
H = Graph(); hb = B(H, 'cshk')
me = hb.self_node(0, 200)
fc = hb.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll.BPC_CastleScroll_C'),
             ob('ReturnValue', SCROLLC, out=True)], 250, 200, target=me, pure=True, const=True, tag='FindScroll')
callfn(H, 'CsHookDraw', SCROLLC, 'DrawScroll', [ob('Hud', HUDC)], x=520, y=0)
H.link(fc, 'ReturnValue', 'CsHookDraw', 'self'); H.link(me[0], me[1], 'CsHookDraw', 'Hud')
open(os.path.join(OUT, 'ZombieHUD_ScrollHook_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(H.render())
print('ZombieHUD hook: nodes %d (call node CsHookDraw, finder %s)' % (len(H.nodes), fc))
