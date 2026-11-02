# Vesna's Trade v3 = #418 v2 + #424 BUNDLES (i9 helper, 2026-11-02). Fork of tools/tga/vesna/gen_trade.py (TGA).
#   python gen_trade_bd.py  ->  ../BPC_VesnaTrade_bd_graph.txt + ../trade_bd_data.json   (layout: tools/tga/vesna/layout_bd.py)
# The BP_ArmoryHUD hook is unchanged (DrawTrade(Hud, SizeX, SizeY, Pass), Covering), so only BPC_VesnaTrade's EventGraph
# is replaced. #424 changes:
#   - ARMOUR list = 4 Obsidian bundles (row id 0..3 = BPC_ObsidianSet bundle index) + the 3 shields (27..29). A bundle
#     row reads BundleAvail / BundleOwned / BundleWorn / BundleCost[id] from BPC_ObsidianSet; E buys it (gold -BundleCost,
#     BuyBundle) or puts it on / takes it off (ToggleBundle). Piece ids 10..20 are no longer listed.
#   - Set count and bonus lines count bundles worn (BundleCount, n / 4; tiers 2 / 3 / 4), SET PROGRESS shows 4 tiers.
#   - EQUIPMENT doll = the inventory's 6 slots (Head / Torso / Hands | Weapon / Shield / Boots): the bundle icon when
#     worn, a faint outline glyph when empty (T_VT_Frame_424 has the 6 boxes).
#   - NEW: the same 6-slot look on the I-key inventory doll (BP_ZombieHUD's panel, reported in MPC InvP / InvQ):
#     pass 1 with the shop closed draws the worn bundle icons / faint outlines over the 4 armour slots and the empty
#     weapon / shield slots. Display only: the old inventory's clicks are untouched.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..'))                     # handoffs/obsidian-bundles-424
KIT = os.path.join(REPO, 'tools', 'tga', 'vesna')
L = json.load(open(os.path.join(KIT, 'layout_bd.json')))
SC0, A = L['S'], L['atlas']
ATW = 2048.0                                  # atlas texture size (px)

COMP = CLS('ActorComponent')
HUDC, TEXC, MATL, MPC_CLS = CLS('HUD'), CLS('Texture'), CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
TEX2D = CLS('Texture2D')
CAPC = CLS('SceneCaptureComponent2D')
SETC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet', 'BPC_ObsidianSet')
TRADEC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_VesnaTrade', 'BPC_VesnaTrade')
KITC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit', 'BPC_ShieldKit')   # #418 shields
ZHUD = BPC('/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', 'BP_ZombieHUD')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
FONTC = '"/Script/CoreUObject.Class\'/Script/Engine.Font\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
V2D = '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector2D\'"'
BLEND = '"/Script/CoreUObject.Enum\'/Script/Engine.EBlendMode\'"'
SND = '/Game/CastleDefender/UI/Trade/SFX_Trade%s.SFX_Trade%s'
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
INT, DBL, BOOL = it('v', default='0'), D('v', default='0.0'), bo('v', default='false')
LCV = st('v', LC)
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)
CREAM, DIM, GOLD, GREEN, RED, WHITE = col(.93, .89, .81), col(.62, .58, .52), col(.94, .80, .52), col(.62, .86, .36), col(.88, .36, .28), col(1, 1, 1)

G = Graph()
XY = [0, 0]
def P():
    XY[0] += 280
    if XY[0] > 14000: XY[0] = 0; XY[1] += 220
    return XY[0], XY[1]

class B3(bpkit.B):
    def item(s, arrsrc, pin, idx, x, y):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
b = B3(G, 'v')

def isnum(v): return isinstance(v, (int, float))
def _zero_b(m, a, c):
    """#424 paste trap: a literal 0 on B of Add/Subtract/Multiply/Divide pastes as the C++ default 1. x+0 / x-0 = x,
    x*0 = (x - x). Returns a handle, or None when the node is safe to build as is."""
    if not (isnum(c) and c == 0) or isnum(a): return None
    if m.startswith(('Add_', 'Subtract_')): return a
    if m.startswith('Multiply_'): return b.d2('Subtract_DoubleDouble', a, a, *P()) if 'Double' in m else b.i2('Subtract_IntInt', a, a, *P())
    return None
def dop(m, a, c):
    z = _zero_b(m, a, c)
    if z is not None: return z
    return b.d2(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(float(a)) if isnum(a) else '0.0', db=str(float(c)) if isnum(c) else '0.0')
def iop(m, a, c):
    z = _zero_b(m, a, c)
    if z is not None: return z
    return b.i2(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(int(a)) if isnum(a) else '0', db=str(int(c)) if isnum(c) else '0')
def dcmp(m, a, c):
    return b.dcmp(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(float(a)) if isnum(a) else '0.0', db=str(float(c)) if isnum(c) else '0.0')
def icmp(m, a, c):
    return b.icmp(m, None if isnum(a) else a, None if isnum(c) else c, *P(), da=str(int(a)) if isnum(a) else '0', db=str(int(c)) if isnum(c) else '0')
AND = lambda a, c: b.b2('BooleanAND', a, c, *P())
OR = lambda a, c: b.b2('BooleanOR', a, c, *P())
NOT = lambda a: b.bnot(a, *P())
i2d = lambda a: b.i2d(a, *P())
def seld(a, c, pick): return b.self_(None if isnum(a) else a, None if isnum(c) else c, pick, *P(), da=str(float(a)) if isnum(a) else '0.0', db=str(float(c)) if isnum(c) else '0.0')
def seli(a, c, pick):
    return b.math('SelectInt', [(it('A', default=str(a) if isnum(a) else '0'), None if isnum(a) else a), (it('B', default=str(c) if isnum(c) else '0'), None if isnum(c) else c),
                                (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), *P())
def selc(a, c, pick):   # colours: literal strings or handles
    lit = lambda v: isinstance(v, str)
    return b.math('SelectColor', [(st('A', LC, default=a if lit(a) else col(0, 0, 0)), None if lit(a) else a), (st('B', LC, default=c if lit(c) else col(0, 0, 0)), None if lit(c) else c),
                                  (bo('bPickA', default='false'), pick)], st('ReturnValue', LC, out=True), *P())
def sels(a, c, pick): return b.selstr(None if isinstance(a, str) else a, None if isinstance(c, str) else c, pick, *P(), da=a if isinstance(a, str) else '', db=c if isinstance(c, str) else '')
def istr(src):
    n = b.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], *P(), pure=True); b.wire(src, n, 'InInt'); return (n, 'ReturnValue')
def cat(*parts):
    h = None
    for p in parts:
        if h is None: h = p if not isinstance(p, str) else None; first = p;
        else:
            h = b.concat(h if h is not None else None, None if isinstance(p, str) else p, *P(), da=first if (h is None and isinstance(first, str)) else '', db=p if isinstance(p, str) else '')
        if h is None and isinstance(p, str) and p is not parts[0]: pass
    return h
def cat2(a, c):
    return b.concat(None if isinstance(a, str) else a, None if isinstance(c, str) else c, *P(), da=a if isinstance(a, str) else '', db=c if isinstance(c, str) else '')
def catn(*parts):
    h = parts[0]
    for p in parts[1:]: h = cat2(h, p)
    return h
def group(n):   # 3120 -> "3,120" (numbers below a million)
    th = iop('Divide_IntInt', n, 1000)
    rest = b.lib(KSTR, 'RightChop', [S('SourceString'), it('Count', default='1'), S('ReturnValue', out=True)], *P(), pure=True)
    b.wire(istr(iop('Add_IntInt', iop('Percent_IntInt', n, 1000), 1000)), rest, 'SourceString')
    return sels(catn(istr(th), ',', (rest, 'ReturnValue')), istr(n), icmp('GreaterEqual_IntInt', n, 1000))
def get(var, pin): return b.get(var, pin, *P())
def getarr(var, pin, idx): return b.aget(var, pin, idx, *P())
def bit(idsrc):   # 2 ^ (Id - 10)
    e = iop('Subtract_IntInt', idsrc, 10)
    return b.round_(b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), i2d(e))], D('ReturnValue', out=True), *P()), *P()) \
        if hasattr(b, 'round_') else None
def rnd(v): return b.math('Round', [(D('A', default='0.0'), v)], it('ReturnValue', out=True), *P())
def bit(idsrc):
    e = iop('Subtract_IntInt', idsrc, 10)
    return rnd(b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), i2d(e))], D('ReturnValue', out=True), *P()))
def has(mask, bt): return icmp('Greater_IntInt', iop('And_IntInt', mask, bt), 0)

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

# ---------------------------------------------------------------- event + scale
b.event('DrawTrade', [ob('Hud', HUDC), it('SizeX'), it('SizeY'), it('Pass')], 0, 0)
hud = ('DrawTrade', 'Hud')
fl0 = Flow(('DrawTrade', 'then'))
mpcg = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', 'Shop'), st('ReturnValue', LC, out=True)], *P(), tag='GetShop')
fl0.go(mpcg)
brk = b.math('BreakColor', [(st('InColor', LC), (mpcg, 'ReturnValue'))] , fl('R', out=True, default='0.0'), *P())
brkn = brk[0]
for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
shopR = (brkn, 'R')
paused = b.lib(GS, 'IsGamePaused', [WC(), bo('ReturnValue', out=True, default='false')], *P(), pure=True, tag='Paused')
isopen = AND(dcmp('Greater_DoubleDouble', shopR, 0.5), (paused, 'ReturnValue'))
fopen, fclosed = fl0.iff(isopen, 'IfShopOpen')
sWas = b.set('WasOpen', BOOL, None, *P()); fclosed.go(sWas)
fclosed.go(b.set('Covering', BOOL, None, *P()))

# pass 1 = only the tab bar over the classic shop
fp1, fp0 = fopen.iff(icmp('EqualEqual_IntInt', ('DrawTrade', 'Pass'), 1), 'IfPass1')

# geometry: k = min(SizeX/1920, SizeY/1080); T = S * k; origin centred
sx, sy = i2d(('DrawTrade', 'SizeX')), i2d(('DrawTrade', 'SizeY'))
k = b.math('FMin', [(D('A', default='0.0'), dop('Divide_DoubleDouble', sx, 1920.0)), (D('B', default='0.0'), dop('Divide_DoubleDouble', sy, 1080.0))], D('ReturnValue', out=True), *P())
T = dop('Multiply_DoubleDouble', k, SC0)
OX = dop('Multiply_DoubleDouble', dop('Subtract_DoubleDouble', sx, dop('Multiply_DoubleDouble', k, 1920.0)), 0.5)
OY = dop('Multiply_DoubleDouble', dop('Subtract_DoubleDouble', sy, dop('Multiply_DoubleDouble', k, 1080.0)), 0.5)
_cx, _cy, _cs = {}, {}, {}
def X(v):
    if isnum(v):
        if v not in _cx: _cx[v] = dop('Add_DoubleDouble', OX, dop('Multiply_DoubleDouble', T, float(v)))
        return _cx[v]
    return dop('Add_DoubleDouble', OX, dop('Multiply_DoubleDouble', T, v))
def Y(v):
    if isnum(v):
        if v not in _cy: _cy[v] = dop('Add_DoubleDouble', OY, dop('Multiply_DoubleDouble', T, float(v)))
        return _cy[v]
    return dop('Add_DoubleDouble', OY, dop('Multiply_DoubleDouble', T, v))
def SZ(v):
    if isnum(v):
        if v not in _cs: _cs[v] = dop('Multiply_DoubleDouble', T, float(v))
        return _cs[v]
    return dop('Multiply_DoubleDouble', T, v)

# mouse + keys (one set of nodes, used by both passes)
pcn = b.call(HUDC, 'GetOwningPlayerController', [ob('ReturnValue', PCON, out=True)], *P(), target=hud, pure=True, const=True, tag='PC')
pc = (pcn, 'ReturnValue')
mp = b.call(PCON, 'GetMousePosition', [F('LocationX', out=True), F('LocationY', out=True), bo('ReturnValue', out=True, default='false')], *P(), target=pc, pure=True, const=True, tag='Mouse')
MX, MY = (mp, 'LocationX'), (mp, 'LocationY')
def key(name, down=False):
    n = b.call(PCON, 'IsInputKeyDown' if down else 'WasInputKeyJustPressed', [st('Key', KEY, default=name), bo('ReturnValue', out=True, default='false')], *P(),
               target=pc, pure=True, const=True, tag='Key' + name[:10]); return (n, 'ReturnValue')
def anykey(*names):
    h = key(names[0])
    for n_ in names[1:]: h = OR(h, key(n_))
    return h
CLICK = key('LeftMouseButton')
def inside(x0, y0, w, h):   # target-px rect (numbers or handles for y0)
    xa, ya = X(x0), Y(y0)
    return AND(AND(dcmp('GreaterEqual_DoubleDouble', MX, xa), dcmp('Less_DoubleDouble', MX, dop('Add_DoubleDouble', xa, SZ(w)))),
               AND(dcmp('GreaterEqual_DoubleDouble', MY, ya), dcmp('Less_DoubleDouble', MY, dop('Add_DoubleDouble', ya, SZ(h)))))
now = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], *P(), pure=True, tag='RealNow'); NOW = (now, 'ReturnValue')

# ---------------------------------------------------------------- draw helpers
def sprite(fl_, tex, x, y, w, h, uv, tint=WHITE, tag='Spr', raw=False):
    """tex = Texture variable name; x, y, w, h in target px (numbers or handles); uv = (u, v, uw, vh) numbers in 0..1 or a LinearColor handle.
    raw = True (#424 inventory overlay): x, y, w, h are handles already in screen px."""
    n = b.call(HUDC, 'DrawTexture', [ob('Texture', TEXC), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('TextureU'), F('TextureV'),
               F('TextureUWidth', default='1.0'), F('TextureVHeight', default='1.0'), st('TintColor', LC, default=tint if isinstance(tint, str) else WHITE),
               {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': 'BLEND_Translucent'}, F('Scale', default='1.0'), bo('bScalePosition', default='false'),
               F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag=tag)
    b.wire(get(tex, ob('v', TEX2D)) if isinstance(tex, str) else tex, n, 'Texture')
    if raw:
        b.wire(x, n, 'ScreenX'); b.wire(y, n, 'ScreenY'); b.wire(w, n, 'ScreenW'); b.wire(h, n, 'ScreenH')
    else:
        b.wire(X(x), n, 'ScreenX'); b.wire(Y(y), n, 'ScreenY'); b.wire(SZ(w), n, 'ScreenW'); b.wire(SZ(h), n, 'ScreenH')
    if not isinstance(tint, str): b.wire(tint, n, 'TintColor')
    if isinstance(uv, tuple) and len(uv) == 4 and all(isnum(q) for q in uv):
        for pin, v in zip(('TextureU', 'TextureV', 'TextureUWidth', 'TextureVHeight'), uv): G.nodes[[q[0] for q in G.nodes].index(n)][3][[p['name'] for p in G.nodes[[q[0] for q in G.nodes].index(n)][3]].index(pin)]['default'] = '%f' % v
    else:
        bc = b.math('BreakColor', [(st('InColor', LC), uv)], fl('R', out=True, default='0.0'), *P())
        for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
        for pin, c_ in zip(('TextureU', 'TextureV', 'TextureUWidth', 'TextureVHeight'), 'RGBA'): G.link(bc[0], c_, n, pin)
    fl_.go(n); return n
def cell_uv(k_):
    r = A[k_]; return (r['x'] * SC0 / ATW, r['y'] * SC0 / ATW, r['w'] * SC0 / ATW, r['h'] * SC0 / ATW)
def cell(fl_, k_, x, y, tint=WHITE, anchor='l', tag=None):
    """draw atlas cell k_ with its own size; x = left / centre / right per anchor, y = vertical centre (target px)."""
    r = A[k_]
    xx = x if anchor == 'l' else (x - r['w'] / 2 if (anchor == 'c' and isnum(x)) else (x - r['w'] if isnum(x) else x))
    if anchor == 'c' and not isnum(x): xx = dop('Subtract_DoubleDouble', x, r['w'] / 2.0)
    if anchor == 'r' and not isnum(x): xx = dop('Subtract_DoubleDouble', x, float(r['w']))
    yy = y - r['h'] / 2 if isnum(y) else dop('Subtract_DoubleDouble', y, r['h'] / 2.0)
    return sprite(fl_, 'AtlasTex', xx, yy, r['w'], r['h'], cell_uv(k_), tint, tag=tag or ('C' + k_))
def rect(fl_, x, y, w, h, color, tag='Rect'):
    n = b.call(HUDC, 'DrawRect', [st('RectColor', LC, default=color if isinstance(color, str) else WHITE), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], *P(), target=hud, tag=tag)
    b.wire(X(x) if not isinstance(x, tuple) or True else x, n, 'ScreenX'); b.wire(Y(y), n, 'ScreenY'); b.wire(SZ(w), n, 'ScreenW'); b.wire(SZ(h), n, 'ScreenH')
    if not isinstance(color, str): b.wire(color, n, 'RectColor')
    fl_.go(n); return n
# Cinzel text: the font's line height at Scale 1 is measured once per frame (GetTextSize "0"), so a line of LH target
# px gets Scale = LH * T / H0 whatever the font asset's import size is.
h0n = b.call(HUDC, 'GetTextSize', [S('Text', default='0'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')],
             *P(), target=hud, pure=True, const=True, tag='FontH0')
H0 = (h0n, 'OutHeight')
_sc = {}
def tscale(lh):
    if lh not in _sc: _sc[lh] = dop('Divide_DoubleDouble', SZ(float(lh)), H0)
    return _sc[lh]
def text(fl_, s, x, y, lh, color, anchor='l', tag='Txt'):
    """s = string handle or literal; x in target px (number or handle in target px), y = vertical centre."""
    sc = tscale(lh)
    n = b.call(HUDC, 'DrawText', [S('Text', default=s if isinstance(s, str) else ''), st('TextColor', LC, default=color if isinstance(color, str) else WHITE), F('ScreenX'), F('ScreenY'),
               dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0'), bo('bScalePosition', default='false')], *P(), target=hud, tag=tag)
    if not isinstance(s, str): b.wire(s, n, 'Text')
    if not isinstance(color, str): b.wire(color, n, 'TextColor')
    b.wire(sc, n, 'Scale')
    xs = X(x)
    if anchor != 'l':
        ts = b.call(HUDC, 'GetTextSize', [S('Text', default=s if isinstance(s, str) else ''), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT),
                    F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='Measure')
        if not isinstance(s, str): b.wire(s, ts, 'Text')
        b.wire(sc, ts, 'Scale')
        wdt = (ts, 'OutWidth') if anchor == 'r' else dop('Multiply_DoubleDouble', (ts, 'OutWidth'), 0.5)
        xs = dop('Subtract_DoubleDouble', xs, wdt)
    b.wire(xs, n, 'ScreenX')
    b.wire(dop('Subtract_DoubleDouble', Y(y), dop('Multiply_DoubleDouble', dop('Multiply_DoubleDouble', sc, H0), 0.5)), n, 'ScreenY')
    fl_.go(n); return n
def snd(fl_, which):
    n = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', CLS('SoundBase')), dobj=SND % (which, which)), fl('VolumeMultiplier', default='1.000000', advanced=True),
              fl('PitchMultiplier', default='1.000000', advanced=True), fl('StartTime', default='0.000000', advanced=True),
              dict(ob('ConcurrencySettings', CLS('SoundConcurrency')), advanced=True), dict(ob('OwningActor', ACT), advanced=True),
              bo('bIsUISound', default='true')], *P(), tag='Snd' + which)
    G.nodes[-1][3][-1]['advanced'] = True
    fl_.go(n); return n
def setv(fl_, var, pin, src): n = b.set(var, pin, src if not isnum(src) else None, *P());
def setvar(fl_, var, pin, src, lit=None):
    n = b.set(var, pin, None if lit is not None else src, *P())
    if lit is not None: G.nodes[-1][3][2]['default'] = lit
    fl_.go(n); return n
def selfcall(fl_, member, pins=(), cls=TRADEC):
    n = b.call_self(member, list(pins), *P(), cls, tag='Call' + member); fl_.go(n); return n

# ---------------------------------------------------------------- shared state reads
SETV = ob('v', SETC)
setc = get('Set', SETV)
def sv(var, pin=INT): return b.getm(var, SETC, pin, setc, *P())
OWNED, WORN, AVAIL = sv('ObsOwned'), sv('WornEff'), sv('AvailMask')
PRICE, WCOUNT, TIER, SHIELD = sv('NextPrice'), sv('WornCount'), sv('Tier'), sv('ShieldLevel')
zh = cast(G, 'AsZHud', ZHUD, 'AsBP Zombie HUD', *P(), pure=True); b.wire(hud, 'AsZHud', 'Object')
ZH = ('AsZHud', 'AsBP Zombie HUD')
GOLD_ = b.getm('Gold', ZHUD, INT, ZH, *P())
TAB, RTAB, SEL, SCROLL = get('Tab', INT), get('RTab', INT), get('Sel', INT), get('Scroll', INT)
SELID = getarr('PieceIds', INT, SEL)
SBIT = bit(SELID)
S_OWN = has(b.i2('Or_IntInt', OWNED, WORN, *P()), SBIT)
S_WORN, S_AV = has(WORN, SBIT), has(AVAIL, SBIT)
S_CUIRASS = icmp('EqualEqual_IntInt', SELID, 10)
# #418 shields: list rows 27-29 are BPC_ShieldKit[id - 27]; their set bits (17-19) are never in the set's masks, so every
# set test above is false for them and the kit terms below decide instead
KITV = get('Kit', ob('v', KITC)); KIT_OK = b.valid(KITV, *P())
K_OWNED, K_WORN = b.getm('Owned', KITC, INT, KITV, *P()), b.getm('Worn', KITC, INT, KITV, *P())
K_PRICES = b.getm('Prices', KITC, arr(INT), KITV, *P())
def iskit(idv): return AND(icmp('GreaterEqual_IntInt', idv, 27), icmp('LessEqual_IntInt', idv, 29))
def kk(idv): return iop('Subtract_IntInt', idv, 27)
def k_own(idv): return has(K_OWNED, rnd(b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), i2d(kk(idv)))], D('ReturnValue', out=True), *P())))
def k_worn(idv): return icmp('EqualEqual_IntInt', K_WORN, kk(idv))
def k_price(idv): return b.item(K_PRICES, INT, b.math('Max', [(it('A', default='0'), kk(idv)), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
S_SH = AND(iskit(SELID), KIT_OK)
S_OWN = OR(S_OWN, AND(S_SH, k_own(SELID))); S_WORN = OR(S_WORN, AND(S_SH, k_worn(SELID))); S_AV = OR(S_AV, S_SH)
PRICE_SET = PRICE
PRICE = seli(k_price(SELID), PRICE_SET, S_SH)          # the selected row's price (the set's next price, or the shield's)
# #424 bundles: list rows 0..3 are BPC_ObsidianSet bundles (bit k of BundleAvail / BundleOwned / BundleWorn). Their piece
# bits round(2 ^ (id - 10)) are 0, so every piece test above is false for them and these terms decide instead.
B_OWNED, B_WORN, B_AVAIL, B_COUNT = sv('BundleOwned'), sv('BundleWorn'), sv('BundleAvail'), sv('BundleCount')
B_COST = b.getm('BundleCost', SETC, arr(INT), setc, *P())
def cl03(v): return b.math('Clamp', [(it('Value', default='0'), v), (it('Min', default='0'), None), (it('Max', default='3'), None)], it('ReturnValue', out=True), *P())
def isb(idv): return AND(icmp('GreaterEqual_IntInt', idv, 0), icmp('LessEqual_IntInt', idv, 3))
def bb(idv): return rnd(b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), i2d(cl03(idv)))], D('ReturnValue', out=True), *P()))
def b_av(idv): return AND(isb(idv), has(B_AVAIL, bb(idv)))
def b_own(idv): return AND(isb(idv), has(B_OWNED, bb(idv)))
def b_worn(idv): return AND(isb(idv), has(B_WORN, bb(idv)))
def b_price(idv): return b.item(B_COST, INT, cl03(idv), *P())
S_BD = isb(SELID)
S_OWN = OR(S_OWN, b_own(SELID)); S_WORN = OR(S_WORN, b_worn(SELID)); S_AV = OR(S_AV, b_av(SELID))
PRICE = seli(b_price(SELID), PRICE, S_BD)
AFFORD = icmp('GreaterEqual_IntInt', GOLD_, PRICE)
# clicks (#420 lesson): own press edge from IsInputKeyDown, PrevDown is written at the end of the input below
LDOWN = key('LeftMouseButton', down=True)
CLICK = AND(LDOWN, NOT(get('PrevDown', BOOL)))

# =====================================================================================================================
# PASS 0. On open (first frame): reset the screen and find the set + the capture. Then input, then draw.
# =====================================================================================================================
fnew, fold = fp0.iff(get('WasOpen', BOOL), 'IfWasOpen')     # then = already open
fo = fold
setvar(fo, 'WasOpen', BOOL, None, 'true'); setvar(fo, 'Tab', INT, None, '1'); setvar(fo, 'RTab', INT, None, '0')
setvar(fo, 'Yaw', DBL, None, '0.0'); setvar(fo, 'Zoom', DBL, None, '1.0'); setvar(fo, 'Spin', BOOL, None, 'true'); setvar(fo, 'HeroYaw', DBL, None, '0.0')
setvar(fo, 'LastT', DBL, NOW)
own_ = b.math('GetOwner', [], ob('ReturnValue', ACT, out=True), *P()) if False else None
ownn = b.name('Owner'); callfn(G, ownn, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=P()[0], y=P()[1], self_hidden=True); OWNER = (ownn, 'ReturnValue')
gs = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet.BPC_ObsidianSet_C'), ob('ReturnValue', SETC, out=True)],
            *P(), target=OWNER, pure=True, const=True, tag='FindSet')
setvar(fo, 'Set', SETV, (gs, 'ReturnValue'))
gk = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit.BPC_ShieldKit_C'), ob('ReturnValue', KITC, out=True)],
            *P(), target=OWNER, pure=True, const=True, tag='FindKit')
setvar(fo, 'Kit', ob('v', KITC), (gk, 'ReturnValue'))
def input_mode(gameui):
    if gameui:
        n = b.lib(UMG('WidgetBlueprintLibrary'), 'SetInputMode_GameAndUIEx', [ob('PlayerController', PCON), ob('InWidgetToFocus', UMG('Widget')),
                  {'name': 'InMouseLockMode', 'cat': 'byte', 'obj': ENUM('EMouseLockMode'), 'default': 'DoNotLock'},
                  bo('bHideCursorDuringCapture', default='false'), dict(bo('bFlushInput', default='false'), advanced=True)], *P(), tag='InputGameUI')
    else:
        n = b.lib(UMG('WidgetBlueprintLibrary'), 'SetInputMode_GameOnly', [ob('PlayerController', PCON), dict(bo('bFlushInput', default='false'), advanced=True)], *P(), tag='InputGame')
    b.wire(pc, n, 'PlayerController'); return n
fo.go(input_mode(True)); setvar(fo, 'ModeUI', BOOL, None, 'true'); setvar(fo, 'PrevDown', BOOL, None, 'true')
# closed again (whoever closed it): back to Game Only once
fmo, _nmo = fclosed.iff(get('ModeUI', BOOL), 'IfModeUI'); fmo.go(input_mode(False)); setvar(fmo, 'ModeUI', BOOL, None, 'false')
gc = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.SceneCaptureComponent2D'), NAME_('Tag', 'VTCapture'), arr(ob('ReturnValue', COMP, out=True))],
            *P(), target=OWNER, const=True, pure=True, tag='FindCap')
capc = cast(G, 'AsCap', CAPC, 'AsScene Capture Component 2D', *P(), pure=True)
b.wire(b.item((gc, 'ReturnValue'), ob('v', COMP), None, *P()), 'AsCap', 'Object')
setvar(fo, 'Cap', ob('v', CAPC), ('AsCap', 'AsScene Capture Component 2D'))
fcap, fnocap = fo.iff(b.valid(get('Cap', ob('v', CAPC)), *P()), 'IfCap')
so = b.call(CLS('SceneCaptureComponent'), 'ShowOnlyActorComponents', [ob('InActor', ACT), bo('bIncludeFromChildActors', default='true')], *P(), target=get('Cap', ob('v', CAPC)), tag='CapShowOnly')
b.wire(OWNER, so, 'InActor'); fcap.go(so)
cmc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Script/Engine.CharacterMovementComponent'), ob('ReturnValue', CMC, out=True)],
             *P(), target=OWNER, pure=True, const=True, tag='FindCMC')
MWS = b.getm('MaxWalkSpeed', CMC, fl('v', default='0.0'), (cmc, 'ReturnValue'), *P())
fo = fcap.join(fnocap)
fb, fnb = fo.iff(dcmp('Less_DoubleDouble', get('BaseSpeed', DBL), 1.0), 'IfBaseSpeed')
setvar(fb, 'BaseSpeed', DBL, MWS)
fo = fb.join(fnb)
snd(fo, 'Swipe')
fl1 = fo.join(fnew)

# ---- input: tabs (LB/RB, click), list (A/D/W/S/arrows/pad, wheel, click), preview (R, drag, wheel), F, E, Esc
def tabhit(i): t = L['tabs'][i]; return AND(CLICK, inside(t['x0'], L['tabbar']['y'], t['x1'] - t['x0'], L['tabbar']['h']))
def apply_tabs(fl_):
    nt = iop('Percent_IntInt', iop('Add_IntInt', TAB, 3), 4)              # LB = previous
    f1, f2 = fl_.iff(anykey('Gamepad_LeftShoulder'), 'IfLB'); setvar(f1, 'Tab', INT, nt); fl_ = f1.join(f2)
    nt2 = iop('Percent_IntInt', iop('Add_IntInt', TAB, 1), 4)
    f1, f2 = fl_.iff(anykey('Gamepad_RightShoulder', 'Tab'), 'IfRB'); setvar(f1, 'Tab', INT, nt2); fl_ = f1.join(f2)
    for i in range(4):
        f1, f2 = fl_.iff(tabhit(i), 'IfTab%d' % i); setvar(f1, 'Tab', INT, None, str(i)); snd(f1, 'Swipe'); fl_ = f1.join(f2)
    return fl_
fl1 = apply_tabs(fl1)
COVER = OR(icmp('EqualEqual_IntInt', get('Tab', INT), 1), icmp('EqualEqual_IntInt', get('Tab', INT), 2))
setvar(fl1, 'Covering', BOOL, COVER)
fcv, fnc = fl1.iff(get('Covering', BOOL), 'IfCovering')
fl2 = fcv          # everything below draws the new screen; fnc = classic tabs: nothing more in pass 0

# list navigation
R = L['rows']; NP = len(L['pieces'])
prev_ = anykey('A', 'W', 'Up', 'Left', 'Gamepad_DPad_Up')
next_ = anykey('D', 'S', 'Down', 'Right', 'Gamepad_DPad_Down')
ar = L['arrows']
prev_ = OR(prev_, AND(CLICK, inside(ar['l'] - 22, ar['cy'] - 26, 44, 52)))
next_ = OR(next_, AND(CLICK, inside(ar['r'] - 22, ar['cy'] - 26, 44, 52)))
clampsel = lambda v: b.math('Clamp', [(it('Value', default='0'), v), (it('Min', default='0'), None), (it('Max', default=str(NP - 1)), None)], it('ReturnValue', out=True), *P())
f1, f2 = fl2.iff(prev_, 'IfPrev'); setvar(f1, 'Sel', INT, clampsel(iop('Subtract_IntInt', get('Sel', INT), 1))); snd(f1, 'Swipe'); fl2 = f1.join(f2)
f1, f2 = fl2.iff(next_, 'IfNext'); setvar(f1, 'Sel', INT, clampsel(iop('Add_IntInt', get('Sel', INT), 1))); snd(f1, 'Swipe'); fl2 = f1.join(f2)
for i in range(R['n']):   # click a visible row
    f1, f2 = fl2.iff(AND(CLICK, inside(R['x'], R['y0'] + i * R['step'], R['w'], R['h'])), 'IfRow%d' % i)
    setvar(f1, 'Sel', INT, clampsel(iop('Add_IntInt', get('Scroll', INT), i))); fl2 = f1.join(f2)
# wheel: over the list scrolls, over the preview zooms
wup, wdn = key('MouseScrollUp'), key('MouseScrollDown')
LP = L['left']; overlist = inside(LP['x'], LP['y'], LP['w'], LP['h']); TN = L['turn']
overturn = inside(TN['cx'] - TN['w'] / 2, TN['cy'] - TN['h'] / 2, TN['w'], TN['h'])
maxscroll = NP - R['n']
clampscr = lambda v: b.math('Clamp', [(it('Value', default='0'), v), (it('Min', default='0'), None), (it('Max', default=str(maxscroll)), None)], it('ReturnValue', out=True), *P())
f1, f2 = fl2.iff(AND(wup, overlist), 'IfWheelUpL'); setvar(f1, 'Scroll', INT, clampscr(iop('Subtract_IntInt', get('Scroll', INT), 1))); fl2 = f1.join(f2)
f1, f2 = fl2.iff(AND(wdn, overlist), 'IfWheelDnL'); setvar(f1, 'Scroll', INT, clampscr(iop('Add_IntInt', get('Scroll', INT), 1))); fl2 = f1.join(f2)
clampz = lambda v: b.math('FClamp', [(D('Value', default='0.0'), v), (D('Min', default='0.8'), None), (D('Max', default='1.3'), None)], D('ReturnValue', out=True), *P())
f1, f2 = fl2.iff(AND(wup, overturn), 'IfZoomIn'); setvar(f1, 'Zoom', DBL, clampz(dop('Add_DoubleDouble', get('Zoom', DBL), 0.06))); fl2 = f1.join(f2)
f1, f2 = fl2.iff(AND(wdn, overturn), 'IfZoomOut'); setvar(f1, 'Zoom', DBL, clampz(dop('Subtract_DoubleDouble', get('Zoom', DBL), 0.06))); fl2 = f1.join(f2)
# keep the selection on screen
sel_, scr_ = get('Sel', INT), get('Scroll', INT)
f1, f2 = fl2.iff(icmp('Less_IntInt', sel_, scr_), 'IfSelAbove'); setvar(f1, 'Scroll', INT, get('Sel', INT)); fl2 = f1.join(f2)
f1, f2 = fl2.iff(icmp('Greater_IntInt', get('Sel', INT), iop('Add_IntInt', get('Scroll', INT), R['n'] - 1)), 'IfSelBelow')
setvar(f1, 'Scroll', INT, iop('Subtract_IntInt', get('Sel', INT), R['n'] - 1)); fl2 = f1.join(f2)
# F compare, R spin, right tabs
f1, f2 = fl2.iff(key('F'), 'IfF'); setvar(f1, 'Compare', BOOL, NOT(get('Compare', BOOL))); fl2 = f1.join(f2)
f1, f2 = fl2.iff(key('R'), 'IfR'); setvar(f1, 'Spin', BOOL, NOT(get('Spin', BOOL))); fl2 = f1.join(f2)
RT = L['rtabs']
f1, f2 = fl2.iff(AND(CLICK, inside(RT['eq'][0], RT['y'], RT['eq'][1] - RT['eq'][0], RT['h'])), 'IfRTab0'); setvar(f1, 'RTab', INT, None, '0'); fl2 = f1.join(f2)
f1, f2 = fl2.iff(AND(CLICK, inside(RT['sp'][0], RT['y'], RT['sp'][1] - RT['sp'][0], RT['h'])), 'IfRTab1'); setvar(f1, 'RTab', INT, None, '1'); fl2 = f1.join(f2)
# preview turn: drag (LMB held over the preview) or spin 30 deg/s; the hero turns with a drag over the figure
dt = dop('Subtract_DoubleDouble', NOW, get('LastT', DBL))
lmb = key('LeftMouseButton', down=True)
HR = L['hero']; overhero = inside(HR['x'], HR['y'], HR['w'], HR['h'])
dx = dop('Subtract_DoubleDouble', MX, get('DragX', DBL))
f1, f2 = fl2.iff(AND(AND(lmb, overturn), get('Dragging', BOOL)), 'IfDragItem')
setvar(f1, 'Yaw', DBL, dop('Add_DoubleDouble', get('Yaw', DBL), dop('Multiply_DoubleDouble', dx, 0.5)))
f3, f4 = f2.iff(get('Spin', BOOL), 'IfSpin')
setvar(f3, 'Yaw', DBL, dop('Add_DoubleDouble', get('Yaw', DBL), dop('Multiply_DoubleDouble', dt, 30.0)))
fl2 = f1.join(f3, f4)
f1, f2 = fl2.iff(AND(AND(lmb, overhero), get('Dragging', BOOL)), 'IfDragHero')
setvar(f1, 'HeroYaw', DBL, dop('Add_DoubleDouble', get('HeroYaw', DBL), dop('Multiply_DoubleDouble', dx, 0.5))); fl2 = f1.join(f2)
setvar(fl2, 'Dragging', BOOL, lmb); setvar(fl2, 'DragX', DBL, MX); setvar(fl2, 'LastT', DBL, NOW)
wrap = dop('Subtract_DoubleDouble', get('Yaw', DBL), dop('Multiply_DoubleDouble', i2d(b.math('FFloor', [(D('A', default='0.0'), dop('Divide_DoubleDouble', get('Yaw', DBL), 360.0))], it('ReturnValue', out=True), *P())), 360.0))
setvar(fl2, 'Yaw', DBL, wrap)

# E / click on the button: wear-toggle when owned, buy when affordable, else the "not enough gold" line
BU = L['buy']
act = OR(anykey('E', 'Gamepad_FaceButton_Bottom'), AND(CLICK, inside(BU['x'], BU['y'], BU['w'], BU['h'])))
fa, fna = fl2.iff(act, 'IfAction')
fav, fnav = fa.iff(AND(S_AV, NOT(S_CUIRASS)), 'IfBuyable')
fks, fav = fav.iff(S_SH, 'IfShieldSel')
fko, fkn = fks.iff(S_OWN, 'IfShieldOwned')
kw = b.call(KITC, 'Wear', [it('Index', default='0')], *P(), target=KITV, tag='CallKitWear'); b.wire(kk(SELID), kw, 'Index'); fko.go(kw); snd(fko, 'Swipe')
fkg, fkng = fkn.iff(AFFORD, 'IfShieldAfford')
fkg.go(b.setm('Gold', ZHUD, INT, iop('Subtract_IntInt', GOLD_, PRICE), ZH, *P()))
kb = b.call(KITC, 'Buy', [it('Index', default='0')], *P(), target=KITV, tag='CallKitBuy'); b.wire(kk(SELID), kb, 'Index'); fkg.go(kb)
setvar(fkg, 'FlashUntil', DBL, dop('Add_DoubleDouble', NOW, 0.6)); snd(fkg, 'Buy')
setvar(fkng, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 1.5)); snd(fkng, 'Fail')
fbs, fav = fav.iff(S_BD, 'IfBundleSel')                 # #424: a bundle row
fbo, fbn = fbs.iff(S_OWN, 'IfBundleOwned')
tb_ = b.call(SETC, 'ToggleBundle', [it('B', default='0')], *P(), target=get('Set', SETV), tag='CallToggleBundle'); b.wire(SELID, tb_, 'B'); fbo.go(tb_); snd(fbo, 'Swipe')
fbg, fbng = fbn.iff(AFFORD, 'IfBundleAfford')
fbg.go(b.setm('Gold', ZHUD, INT, iop('Subtract_IntInt', GOLD_, PRICE), ZH, *P()))
bb_ = b.call(SETC, 'BuyBundle', [it('B', default='0')], *P(), target=get('Set', SETV), tag='CallBuyBundle'); b.wire(SELID, bb_, 'B'); fbg.go(bb_)
setvar(fbg, 'FlashUntil', DBL, dop('Add_DoubleDouble', NOW, 0.6)); snd(fbg, 'Buy')
setvar(fbng, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 1.5)); snd(fbng, 'Fail')
fo_, fno = fav.iff(S_OWN, 'IfOwnedSel')
tw = b.call(SETC, 'ToggleWear', [it('Id', default='0')], *P(), target=get('Set', SETV), tag='CallToggleWear'); b.wire(SELID, tw, 'Id'); fo_.go(tw); snd(fo_, 'Swipe')
fg, fng = fno.iff(AFFORD, 'IfAfford')
fg.go(b.setm('Gold', ZHUD, INT, iop('Subtract_IntInt', GOLD_, PRICE), ZH, *P()))
bp_ = b.call(SETC, 'BuyPiece', [it('Id', default='0')], *P(), target=get('Set', SETV), tag='CallBuyPiece'); b.wire(SELID, bp_, 'Id'); fg.go(bp_)
setvar(fg, 'FlashUntil', DBL, dop('Add_DoubleDouble', NOW, 0.6)); snd(fg, 'Buy')
setvar(fng, 'MsgUntil', DBL, dop('Add_DoubleDouble', NOW, 1.5)); snd(fng, 'Fail')
snd(fnav, 'Fail')
fl2 = fo_.join(fg, fng, fnav, fna, fko, fkg, fkng, fbo, fbg, fbng)
setvar(fl2, 'PrevDown', BOOL, LDOWN)              # the press edge for the next frame

# Esc: close the shop (Shop.R = 0, unpause, hide the cursor)
fesc, fne = fl2.iff(key('Escape'), 'IfEsc')
mk = b.math('MakeColor', [(fl('R', default='0.0'), None), (fl('G', default='0.0'), (brkn, 'G')), (fl('B', default='0.0'), (brkn, 'B')), (fl('A', default='1.0'), (brkn, 'A'))],
            st('ReturnValue', LC, out=True), *P())
sp = b.lib(MATL, 'SetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', 'Shop'), st('ParameterValue', LC)], *P(), tag='CloseShop')
b.wire(mk, sp, 'ParameterValue'); fesc.go(sp)
fesc.go(b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='false'), bo('ReturnValue', out=True, default='false')], *P(), tag='Unpause'))
fesc.go(b.setm('bShowMouseCursor', PCON, BOOL, None, pc, *P())); fesc.go(input_mode(False)); setvar(fesc, 'ModeUI', BOOL, None, 'false')
setvar(fesc, 'WasOpen', BOOL, None, 'false'); setvar(fesc, 'Covering', BOOL, None, 'false')
fdraw, _ = fne.iff(True if False else get('Covering', BOOL), 'IfStillOpen')   # Esc ends the frame here

# =====================================================================================================================
# DRAW (pass 0, covering)
# =====================================================================================================================
fd = fdraw
rect(fd, 0, 0, L['TW'], L['TH'], col(0.02, 0.018, 0.016, 1.0), tag='BackFill')
rect(fd, -2000, -2000, 0.0, 0.0, col(0, 0, 0, 0), tag='Noop') if False else None
PO = L['portrait']
sprite(fd, 'PortraitTex', PO['x'], PO['y'], PO['w'], PO['h'], (0.0, 0.0, 1.0, 1.0), tag='Portrait')
sprite(fd, 'FrameTex', 0, 0, L['TW'], L['TH'], (0.0, 0.0, 1.0, 1.0 * 1080 / 1080), tag='Frame')

def draw_tabs(fl_):
    tb = L['tabbar']
    for i in range(4):
        t = L['tabs'][i]; r = A['tab%d' % i]
        f1, f2 = fl_.iff(icmp('EqualEqual_IntInt', get('Tab', INT), i), 'IfTabOn%d' % i)
        sprite(f1, 'AtlasTex', (t['x0'] + t['x1']) / 2 - r['w'] / 2, tb['cy'] - r['h'] / 2, r['w'], r['h'], cell_uv('tab%d' % i), tag='TabOn%d' % i)
        fl_ = f1.join(f2)
    return fl_
fd = draw_tabs(fd)
# purse
PU = L['purse']
text(fd, group(GOLD_), PU['gold'][1], PU['cy'], 30, CREAM, tag='Gold')
ORE = b.getm('Ore', ZHUD, arr(INT), ZH, *P())                     # BP_ZombieHUD Ore[0] iron, [1] copper, [2] silver, [3] gold ore (#201)
text(fd, istr(b.item(ORE, INT, None, *P())), PU['iron'][1], PU['cy'], 30, CREAM, tag='Iron')
so_ = b.item(ORE, INT, None, *P()); G.nodes[-1][3][1]['default'] = '2'
text(fd, istr(so_), PU['silver'][1], PU['cy'], 30, CREAM, tag='Silver')
# left header count
LH = L['lhead']
text(fd, catn('(', istr(B_COUNT), ' / 4)'), 322, LH['cy'] + 1, 27, GOLD, tag='SetCount')
# list rows
lp = b.forloop(None, None, *P()); G.nodes[-1][3][2]['default'] = str(R['n'] - 1); fd.go(lp, out='Completed')
fr = Flow((lp, 'LoopBody'))
ri = (lp, 'Index')
idx = iop('Add_IntInt', get('Scroll', INT), ri)
ry = dop('Add_DoubleDouble', float(R['y0']), dop('Multiply_DoubleDouble', i2d(ri), float(R['step'])))     # row top (target px)
rcy = dop('Add_DoubleDouble', ry, R['h'] / 2.0)
rid = getarr('PieceIds', INT, idx); rbit = bit(rid)
r_sh = AND(iskit(rid), KIT_OK)
r_av, r_own, r_worn = OR(has(AVAIL, rbit), r_sh), OR(has(b.i2('Or_IntInt', OWNED, WORN, *P()), rbit), AND(r_sh, k_own(rid))), OR(has(WORN, rbit), AND(r_sh, k_worn(rid)))
r_price = seli(k_price(rid), PRICE_SET, r_sh)
r_av, r_own, r_worn = OR(r_av, b_av(rid)), OR(r_own, b_own(rid)), OR(r_worn, b_worn(rid))      # #424 bundles
r_price = seli(b_price(rid), r_price, isb(rid))
fsel, fns = fr.iff(icmp('EqualEqual_IntInt', idx, get('Sel', INT)), 'IfRowSel')
rs = L['rsel']
sprite(fsel, 'AtlasTex', R['x'] + rs['dx'], dop('Add_DoubleDouble', ry, float(rs['dy'])), rs['w'], rs['h'], cell_uv('rsel'), tag='RowSel')
fr = fsel.join(fns)
# icon: art pieces from T_VT_Icons, the others are atlas glyphs (IconFromAtlas)
ic = R['icon']; isz = 58
icx = (ic[0] + ic[1]) / 2.0 - isz / 2.0
icy = dop('Subtract_DoubleDouble', rcy, isz / 2.0)
tint_ic = selc(WHITE, col(.55, .52, .48), r_av)
fbi, fr = fr.iff(getarr('IconFromBundle', BOOL, idx), 'IfBundleIcon')      # #424: T_VT_Bundles_424 cells
sprite(fbi, 'BundleTex', icx, icy, isz, isz, getarr('IconUV', LCV, idx), selc(WHITE, col(.62, .60, .56), r_av), tag='RowBundle')
fat, fic = fr.iff(getarr('IconFromAtlas', BOOL, idx), 'IfGlyph')
sprite(fat, 'AtlasTex', icx, icy, isz, isz, getarr('IconUV', LCV, idx), tint_ic, tag='RowGlyph')
sprite(fic, 'IconsTex', icx, icy, isz, isz, getarr('IconUV', LCV, idx), WHITE, tag='RowIcon')
fr = fat.join(fic, fbi)
# name + DEF cells (white cells, tinted)
nm_w, nm_h = A['name1']['w'], A['name1']['h']
sprite(fr, 'AtlasTex', R['name'][0], dop('Add_DoubleDouble', ry, R['name'][1] - R['y0'] - nm_h / 2.0), nm_w, nm_h, getarr('NameUV', LCV, idx), selc(CREAM, DIM, r_av), tag='RowName')
df_w, df_h = A['def1']['w'], A['def1']['h']
sprite(fr, 'AtlasTex', R['deff'][0], dop('Add_DoubleDouble', ry, R['deff'][1] - R['y0'] - df_h / 2.0), df_w, df_h, getarr('DefUV', LCV, idx), DIM, tag='RowDef')
# state: WORN / OWNED / FORGING / price
sx_ = R['state'][0]; sy_ = dop('Add_DoubleDouble', ry, R['state'][1] - R['y0'])
fw, fnw = fr.iff(r_worn, 'IfRowWorn'); cell(fw, 'worn', sx_, sy_, anchor='r')
fo2, fno2 = fnw.iff(r_own, 'IfRowOwned'); cell(fo2, 'owned', sx_, sy_, anchor='r')
ff, fnf = fno2.iff(NOT(r_av), 'IfRowForging'); cell(ff, 'forging', sx_, sy_, anchor='r')
fcu, fncu = fnf.iff(icmp('EqualEqual_IntInt', rid, 10), 'IfRowRack')        # the cuirass is sold on the classic rack
text(fcu, 'ON THE RACK', sx_, sy_, 22, DIM, anchor='r', tag='RowRack')
pr = catn(group(r_price), ' G')
tp = text(fncu, pr, sx_, sy_, 25, selc(GOLD, RED, icmp('GreaterEqual_IntInt', GOLD_, r_price)), anchor='r', tag='RowPrice')
mw = b.call(HUDC, 'GetTextSize', [S('Text'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='PriceW')
b.wire(pr, mw, 'Text'); b.wire(tscale(25), mw, 'Scale')
coinx = dop('Subtract_DoubleDouble', dop('Subtract_DoubleDouble', float(sx_), dop('Divide_DoubleDouble', (mw, 'OutWidth'), T)), 30.0)
sprite(fncu, 'AtlasTex', coinx, dop('Subtract_DoubleDouble', sy_, 11.0), 22, 22, cell_uv('coin'), tag='RowCoin')
# (loop body ends: the loop moves on by itself)

# scrollbar thumb
SC = L['scroll']; th = SC['h'] * R['n'] / NP
ty = dop('Add_DoubleDouble', float(SC['y']), dop('Multiply_DoubleDouble', i2d(get('Scroll', INT)), (SC['h'] - th) / max(1, maxscroll)))
rect(fd, SC['x'], ty, SC['w'], th, col(.85, .70, .42, .85), tag='Thumb')

# centre: title, tags
IT = L['ititle']; tw_, th_ = A['title1']['w'], A['title1']['h']
sprite(fd, 'AtlasTex', IT['cx'] - tw_ / 2, IT['y'] - th_ / 2, tw_, th_, getarr('TitleUV', LCV, get('Sel', INT)), col(.93, .89, .81), tag='Title')
TG = L['tags']; gw, gh = A['tag1']['w'], A['tag1']['h']
sprite(fd, 'AtlasTex', TG['slot_cx'] - gw / 2, TG['y'] - gh / 2, gw, gh, getarr('TagUV', LCV, get('Sel', INT)), col(.80, .76, .68), tag='Tag')
cell(fd, 'setpiece', TG['piece_cx'], TG['y'], anchor='c')
# preview: turntable frame (24 frames, 4 x 6 cells of 512 x 340 in a 2048 x 2040 texture), else the glyph + forge line
turn = getarr('TurnTex', ob('v', TEX2D), get('Sel', INT))
fT, fG = fd.iff(b.valid(turn, *P()), 'IfTurn')
fi = b.math('FTrunc', [(D('A', default='0.0'), dop('Divide_DoubleDouble', get('Yaw', DBL), 15.0))], it('ReturnValue', out=True), *P())
fi = iop('Percent_IntInt', fi, 24)
tu = dop('Multiply_DoubleDouble', i2d(iop('Percent_IntInt', fi, 4)), 0.25)
tv = dop('Multiply_DoubleDouble', i2d(iop('Divide_IntInt', fi, 4)), 340.0 / 2040.0)
uvT = b.math('MakeColor', [(fl('R', default='0.0'), tu), (fl('G', default='0.0'), tv), (fl('B', default='0.25'), None), (fl('A', default='%f' % (340.0 / 2040.0)), None)],
             st('ReturnValue', LC, out=True), *P())
zw, zh_ = dop('Multiply_DoubleDouble', get('Zoom', DBL), float(TN['w'] * 1.15)), dop('Multiply_DoubleDouble', get('Zoom', DBL), float(TN['w'] * 1.15 * 340 / 512))
sprite(fT, turn, dop('Subtract_DoubleDouble', float(TN['cx']), dop('Multiply_DoubleDouble', zw, 0.5)), dop('Subtract_DoubleDouble', float(TN['cy'] - 8), dop('Multiply_DoubleDouble', zh_, 0.5)),
       zw, zh_, uvT, tag='Turntable')
sprite(fG, 'AtlasTex', TN['cx'] - 80, TN['cy'] - 100, 160, 160, getarr('IconUV', LCV, get('Sel', INT)), col(1, 1, 1, .55), tag='BigGlyph')
cell(fG, 'forgemsg', TN['cx'], TN['cy'] + 85, col(.75, .70, .62), anchor='c')
fd = fT.join(fG)
# page dots: 5 dots, the lit one follows the selection through the list
DT = L['dots']; lit = b.math('Round', [(D('A', default='0.0'), dop('Multiply_DoubleDouble', i2d(get('Sel', INT)), 4.0 / (NP - 1)))], it('ReturnValue', out=True), *P())
for d in range(5):
    x_ = DT['cx'] + (d - 2) * DT['step']
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', lit, d), 'IfDot%d' % d)
    cell(f1, 'dot_on', x_, DT['y'], anchor='c'); cell(f2, 'dot_off', x_, DT['y'], anchor='c'); fd = f1.join(f2)

# compare box: Defence +N, Current -> After (CurDef = DEF of worn pieces, worked out below)
CM = L['cmp']
cdl = b.forloop(None, None, *P()); G.nodes[-1][3][2]['default'] = str(NP - 1)
setvar(fd, 'CurDef', INT, None, '0'); fd.go(cdl, out='Completed')
fcl = Flow((cdl, 'LoopBody'))
cid = getarr('PieceIds', INT, (cdl, 'Index'))
fwl, _x = fcl.iff(OR(has(WORN, bit(cid)), b_worn(cid)), 'IfDefWorn')
setvar(fwl, 'CurDef', INT, iop('Add_IntInt', get('CurDef', INT), getarr('PieceDef', INT, (cdl, 'Index'))))
SDEF = getarr('PieceDef', INT, get('Sel', INT))
gain = seli(0, SDEF, S_WORN)
after = iop('Add_IntInt', get('CurDef', INT), gain)
K_BLOCK = b.item(b.getm('BlockChance', KITC, arr(DBL), KITV, *P()), DBL, b.math('Max', [(it('A', default='0'), kk(SELID)), (it('B', default='0'), None)], it('ReturnValue', out=True), *P()), *P())
text(fd, sels(catn(istr(rnd(dop('Multiply_DoubleDouble', K_BLOCK, 100.0))), '% BLOCK'), catn('+', istr(SDEF)), S_SH), CM['plus'][0], CM['plus'][1], 36, GREEN, tag='DefPlus')
text(fd, istr(get('CurDef', INT)), CM['cur'][0], CM['cur'][1], 29, CREAM, anchor='c', tag='DefCur')
fcm, fncm = fd.iff(get('Compare', BOOL), 'IfCompare')
text(fcm, istr(after), CM['after'][0], CM['after'][1], 29, GREEN, anchor='c', tag='DefAfter')
fd = fcm.join(fncm)
# set bonus: n / 11 and the three tier lines (green once reached)
BN = L['bonus']
text(fd, catn(istr(B_COUNT), ' / 4'), BN['count_r'], BN['head_y'], 26, CREAM, anchor='r', tag='BonusCount')
for t_, ln in enumerate(L['tiers']):
    reached = icmp('GreaterEqual_IntInt', B_COUNT, ln['n'])
    cell(fd, 'tier%d' % t_, BN['diamond'] - 8, BN['lines'][t_], selc(GREEN, col(.80, .76, .68), reached))
# buy button
fon, foff = fd.iff(AND(AND(S_AV, NOT(S_CUIRASS)), OR(S_OWN, AFFORD)), 'IfBtnOn')
cell(fon, 'btn_on', BU['x'], BU['cy'], anchor='l'); cell(foff, 'btn_off', BU['x'], BU['cy'], anchor='l')
fd = fon.join(foff)
fl_ = dop('Subtract_DoubleDouble', dop('Add_DoubleDouble', get('FlashUntil', DBL), 0.0), NOW)
ffl, fnfl = fd.iff(dcmp('Greater_DoubleDouble', fl_, 0.0), 'IfFlash')
rect(ffl, BU['x'], BU['y'], BU['w'], BU['h'], col(1.0, 0.9, 0.6, 0.35), tag='BuyFlash'); fd = ffl.join(fnfl)
cell(fd, 'key_e', BU['key'][0], BU['key'][1], anchor='c')
lbl = sels('TAKE OFF', 'EQUIP', S_WORN)
lbl = sels(lbl, catn('BUY FOR  ', group(PRICE), ' G'), S_OWN)
lbl = sels('ON THE RACK  —  SEE WEAPONS', lbl, AND(S_CUIRASS, NOT(S_OWN)))
lbl = sels(lbl, 'BEING FORGED', S_AV)
lcol = selc(col(.10, .07, .03), CREAM, AND(AND(S_AV, NOT(S_CUIRASS)), OR(S_OWN, AFFORD)))
text(fd, lbl, BU['text'], BU['cy'], 28, lcol, tag='BuyLabel')
fm, fnm = fd.iff(dcmp('Less_DoubleDouble', NOW, get('MsgUntil', DBL)), 'IfNoGold')
cell(fm, 'nogold', (BU['x'] + BU['x'] + BU['w']) / 2, BU['y'] - 14, RED, anchor='c')
fd = fm.join(fnm)

# right: tabs, hero capture or set progress, slots, stats
for i, kk in enumerate(('rtab0', 'rtab1')):
    x0 = (RT['eq'] if i == 0 else RT['sp'])[0]; r = A[kk]
    f1, f2 = fd.iff(icmp('EqualEqual_IntInt', get('RTab', INT), i), 'IfRTabOn%d' % i)
    sprite(f1, 'AtlasTex', x0, RT['y'], r['w'], r['h'], cell_uv(kk), tag='RTabOn%d' % i); fd = f1.join(f2)
feq, fsp = fd.iff(icmp('EqualEqual_IntInt', get('RTab', INT), 0), 'IfEquipTab')
# live hero: orbit the capture round the hero (HeroYaw), capture, draw M_UI_VTHero (samples RT_VTHero, alpha from the capture)
fcv2, fncv = feq.iff(b.valid(get('Cap', ob('v', CAPC)), *P()), 'IfCapDraw')
hy = get('HeroYaw', DBL)
cosv = b.math('DegCos', [(D('A', default='0.0'), hy)], D('ReturnValue', out=True), *P()); sinv = b.math('DegSin', [(D('A', default='0.0'), hy)], D('ReturnValue', out=True), *P())
dist = get('CapDist', DBL)
locv = b.vec(dop('Multiply_DoubleDouble', cosv, dist), dop('Multiply_DoubleDouble', sinv, dist), get('CapHeight', DBL), *P())
rotv = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='-4.0'), None), (fl('Yaw', default='0.0'), dop('Add_DoubleDouble', hy, 180.0))],
              st('ReturnValue', ROT, out=True), *P())
srl = b.call(SCENE, 'K2_SetRelativeLocationAndRotation', [V('NewLocation'), st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'),
             st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], *P(), target=get('Cap', ob('v', CAPC)), tag='CapOrbit')
b.wire(locv, srl, 'NewLocation'); b.wire(rotv, srl, 'NewRotation'); fcv2.go(srl)
fcv2.go(b.call(CAPC, 'CaptureScene', [], *P(), target=get('Cap', ob('v', CAPC)), tag='CapShot'))
dm = b.call(HUDC, 'DrawMaterial', [ob('Material', MATI), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
            F('MaterialUWidth', default='1.0'), F('MaterialVHeight', default='1.0'), F('Scale', default='1.0'), bo('bScalePosition', default='false'),
            F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='HeroFigure')
b.wire(get('HeroMat', MATV), dm, 'Material'); b.wire(X(HR['x']), dm, 'ScreenX'); b.wire(Y(HR['y']), dm, 'ScreenY'); b.wire(SZ(HR['w']), dm, 'ScreenW'); b.wire(SZ(HR['h']), dm, 'ScreenH')
fcv2.go(dm)
feq = fcv2.join(fncv)
# #424 doll: the inventory's 6 slots (layout_bd: left Head / Torso / Hands, right Weapon / Shield / Boots).
# bundle slot: its bundle icon when worn, else the faint outline glyph; shield slot: the worn kit shield (or the #96
# Obsidian shield glyph), else outline; weapon slot: the sword outline, bright while the inventory's sword is equipped.
SL = L['slot']; slots = L['slotsL'] + L['slotsR']
ssz = 50
OUTLINE_T = col(.85, .71, .42, .38)          # faint gold outline
kitworn = AND(KIT_OK, icmp('GreaterEqual_IntInt', K_WORN, 0))
SWORD_EQ = icmp('EqualEqual_IntInt', b.getm('SwordLoc', ZHUD, INT, ZH, *P()), 0)
def KI(k): return iop('Add_IntInt', 0, k) if k else iop('Subtract_IntInt', 1, 1)     # wired literal index (no 0 on a pin with a C++ default)
def row_icon(fl_, rowidx, x, y, w, h, tint=WHITE, raw=False, tag='Doll'):
    """row rowidx's icon: bundle sheet (IconFromBundle), atlas glyph (IconFromAtlas) or the piece icon sheet."""
    f1, f2 = fl_.iff(getarr('IconFromBundle', BOOL, rowidx), 'If' + tag + 'B')
    sprite(f1, 'BundleTex', x, y, w, h, getarr('IconUV', LCV, rowidx), tint, tag=tag + 'B', raw=raw)
    f3, f4 = f2.iff(getarr('IconFromAtlas', BOOL, rowidx), 'If' + tag + 'A')
    sprite(f3, 'AtlasTex', x, y, w, h, getarr('IconUV', LCV, rowidx), tint, tag=tag + 'A', raw=raw)
    sprite(f4, 'IconsTex', x, y, w, h, getarr('IconUV', LCV, rowidx), tint, tag=tag + 'I', raw=raw)
    return f1.join(f3, f4)
for k, sid in enumerate(slots):
    cx = SL['lx'] if k < 3 else SL['rx']; cy = SL['cy0'] + (k % 3) * SL['step']
    x0, y0 = cx - ssz / 2.0, cy - ssz / 2.0
    if sid >= 0:                                   # bundle sid (= its list row)
        fw, fe = feq.iff(icmp('Greater_IntInt', iop('And_IntInt', B_WORN, 1 << sid), 0), 'IfDollWorn%d' % k)
        fw = row_icon(fw, KI(sid), x0, y0, ssz, ssz, tag='Doll%d' % k)
        sprite(fe, 'AtlasTex', x0, y0, ssz, ssz, cell_uv('out%d' % k), OUTLINE_T, tag='DollOut%d' % k)
        feq = fw.join(fe)
        fs_, fns_ = feq.iff(AND(S_BD, icmp('EqualEqual_IntInt', SELID, sid)), 'IfDollSel%d' % k)
    elif sid == -1:                                # shield
        fw, fe = feq.iff(kitworn, 'IfDollKit')
        fw = row_icon(fw, iop('Add_IntInt', K_WORN, 4), x0, y0, ssz, ssz, tag='DollKit')      # rows 4..6 = kit shields 0..2
        fo, fe2 = fe.iff(icmp('Greater_IntInt', SHIELD, 0), 'IfDollObsShield')
        sprite(fo, 'AtlasTex', x0, y0, ssz, ssz, get('ShieldUV', LCV), WHITE, tag='DollObsShield')
        sprite(fe2, 'AtlasTex', x0, y0, ssz, ssz, cell_uv('out%d' % k), OUTLINE_T, tag='DollOut%d' % k)
        feq = fw.join(fo, fe2)
        fs_, fns_ = feq.iff(S_SH, 'IfDollSel%d' % k)
    else:                                          # weapon
        sprite(feq, 'AtlasTex', x0, y0, ssz, ssz, cell_uv('out%d' % k), selc(col(.94, .80, .52, .9), OUTLINE_T, SWORD_EQ), tag='DollSword')
        continue
    sprite(fs_, 'AtlasTex', cx - 35, cy - 35, 70, 70, cell_uv('slotsel'), tag='DollSel%d' % k)
    feq = fs_.join(fns_)
# SET PROGRESS tab: the five tiers, the current one lit
TIERS4 = [(1, '-3% DAMAGE TAKEN'), (2, '-6% DAMAGE TAKEN'), (3, '-10%  +  EMBER SHOCKWAVE'), (4, "SOVEREIGN'S EMBER  -15%")]   # #424 TierAt / TierDR
for t_, (n_, txt) in enumerate(TIERS4):
    y_ = 300 + t_ * 84
    on = icmp('GreaterEqual_IntInt', B_COUNT, n_)
    cell(fsp, 'tierrow', 1388, y_, selc(col(.94, .80, .52, .9), col(.5, .47, .42, .5), on), anchor='c')
    text(fsp, 'TIER %d  ·  %d / 4 BUNDLES' % (t_ + 1, n_), 1170, y_ - 9, 20, selc(GOLD, DIM, on), tag='TierHead')
    text(fsp, txt, 1170, y_ + 11, 18, selc(CREAM, DIM, on), tag='TierText')
fd = feq.join(fsp)
# stats
ST = L['stats']
text(fd, istr(get('CurDef', INT)), ST['val'], ST['rows'][0], 25, CREAM, tag='StDef')
fsc, fnsc = fd.iff(AND(get('Compare', BOOL), icmp('Greater_IntInt', gain, 0)), 'IfStCompare')
text(fsc, '▸', ST['arr'] - 6, ST['rows'][0], 20, CREAM, tag='StArrow')
text(fsc, catn(istr(after), ' (+', istr(gain), ')'), ST['after'], ST['rows'][0], 25, GREEN, tag='StAfter')
fd = fsc.join(fnsc)
text(fd, istr(get('HeroDamage', INT)), ST['val'], ST['rows'][1], 25, CREAM, tag='StDmg')
spd = rnd(dop('Multiply_DoubleDouble', dop('Divide_DoubleDouble', MWS, b.math('FMax', [(D('A', default='0.0'), get('BaseSpeed', DBL)), (D('B', default='1.0'), None)], D('ReturnValue', out=True), *P())), 100.0))
text(fd, catn(istr(spd), '%'), ST['val'], ST['rows'][2], 25, CREAM, tag='StSpeed')
text(fd, istr(get('HeroMaxHP', INT)), ST['val'], ST['rows'][3], 25, CREAM, tag='StHP')

# =====================================================================================================================
# PASS 1: classic tabs (WEAPONS / SUPPLIES) -> the new tab bar over the classic shop, so the player can come back
# =====================================================================================================================
fq, fnq = fp1.iff(NOT(get('Covering', BOOL)), 'IfClassic')
tb = L['tabbar']
rect(fq, tb['x'], tb['y'], tb['w'], tb['h'], col(0.05, 0.045, 0.04, 0.92), tag='ClassicBar')
for i, t in enumerate(L['tabs']):
    text(fq, L['tabnames'][i], t['lx'] if 'lx' in t else t['cx'], tb['cy'], 22, DIM, anchor='c', tag='ClassicTab')
draw_tabs(fq)

# =====================================================================================================================
# #424 INVENTORY DOLL (the I-key panel drawn by BP_ZombieHUD). Shop closed, pass 1 only (after the parent HUD and the
# ArmoryHUD layer have drawn). The parent reports its panel each frame: MPC InvP = (X, Y, W, H) px, InvQ.R = real time.
# The inventory page is 714 x 892 panel px (W/H = 0.8004; the old trade view reports a 507-wide crop and is skipped).
# Slots (panel px, 91 x 93): Head (271,141) Torso (271,260.5) Hands (271,380) | Weapon (565,141) Shield (565,260.5)
# Boots (565,380). Worn bundle -> its icon; empty slot -> the faint outline. The old HUD's own items, clicks and tooltips
# are untouched (it still draws helm / chest / plate / cuirass / sword / shield items when they are equipped).
# =====================================================================================================================
fcl_ = fmo.join(_nmo)
fi1, _fi0 = fcl_.iff(icmp('EqualEqual_IntInt', ('DrawTrade', 'Pass'), 1), 'IfInvPass1')
def mpcvec(fl_, name):
    n = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', name), st('ReturnValue', LC, out=True)], *P(), tag='Get' + name)
    fl_.go(n)
    k_ = b.math('BreakColor', [(st('InColor', LC), (n, 'ReturnValue'))], fl('R', out=True, default='0.0'), *P())
    for c_ in 'GBA': G.nodes[-1][3].append(fl(c_, out=True, default='0.0'))
    return {c_: (k_[0], c_) for c_ in 'RGBA'}
IQ = mpcvec(fi1, 'InvQ'); IP = mpcvec(fi1, 'InvP'); AR = mpcvec(fi1, 'Armor')
fresh = dcmp('Less_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), dop('Subtract_DoubleDouble', NOW, IQ['R']))], D('ReturnValue', out=True), *P()), 0.05)
ratio = b.math('Abs', [(D('A', default='0.0'), dop('Subtract_DoubleDouble', dop('Divide_DoubleDouble', IP['B'], b.math('FMax', [(D('A', default='0.0'), IP['A']), (D('B', default='1.0'), None)], D('ReturnValue', out=True), *P())), 0.8004))],
                   D('ReturnValue', out=True), *P())
invopen = AND(AND(fresh, dcmp('Less_DoubleDouble', ratio, 0.03)), dcmp('Greater_DoubleDouble', IP['B'], 10.0))
fin, _fnin = fi1.iff(invopen, 'IfInventoryOpen')
# the set / kit are found when the shop first opens; the inventory may come first
fns, fhs = fin.iff(NOT(b.valid(get('Set', SETV), *P())), 'IfInvNoSet'); setvar(fns, 'Set', SETV, (gs, 'ReturnValue')); fin = fns.join(fhs)
fnk, fhk = fin.iff(NOT(b.valid(get('Kit', ob('v', KITC)), *P())), 'IfInvNoKit'); setvar(fnk, 'Kit', ob('v', KITC), (gk, 'ReturnValue')); fin = fnk.join(fhk)
fin_ok, _fnso = fin.iff(b.valid(get('Set', SETV), *P()), 'IfInvSet')
fv = fin_ok
ks = dop('Divide_DoubleDouble', IP['B'], 714.0)                       # panel px -> screen px
def px(vx, vy, sz):
    return (dop('Add_DoubleDouble', IP['R'], dop('Multiply_DoubleDouble', ks, float(vx))), dop('Add_DoubleDouble', IP['G'], dop('Multiply_DoubleDouble', ks, float(vy))),
            dop('Multiply_DoubleDouble', ks, float(sz)))
def zloc(name): return icmp('NotEqual_IntInt', b.getm(name, ZHUD, INT, ZH, *P()), 0)        # the old item is not in its slot
PV = b.getm('PlateV', ZHUD, VECT, ZH, *P())
pvb = b.math('BreakVector', [(V('InVec'), PV)], D('X', out=True), *P())
for c_ in 'YZ': G.nodes[-1][3].append(D(c_, out=True))
plate_worn = AND(dcmp('Greater_DoubleDouble', (pvb[0], 'Y'), 0.5), dcmp('Less_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), (pvb[0], 'X'))], D('ReturnValue', out=True), *P()), 0.5))
cuirass_worn = AND(dcmp('Greater_DoubleDouble', AR['G'], 0.5), dcmp('Less_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), AR['B'])], D('ReturnValue', out=True), *P()), 0.5))
INVS = [  # (slot rect x, y, what): bundle index / 'w' weapon / 's' shield
    (271, 141, 0), (271, 260.5, 1), (271, 380, 2), (565, 141, 'w'), (565, 260.5, 's'), (565, 380, 3)]
EMPTY = {0: zloc('HelmLoc'), 1: AND(AND(zloc('ChestLoc'), NOT(plate_worn)), NOT(cuirass_worn)), 2: zloc('GloveLoc'), 3: zloc('BootLoc'),
         'w': zloc('SwordLoc'), 's': zloc('ShieldLoc')}
OUTK = {0: 0, 1: 1, 2: 2, 'w': 3, 's': 4, 3: 5}                            # out<k> atlas glyphs (layout_bd slot order)
INV_OUT = col(.85, .71, .42, .30)
for vx, vy, what in INVS:
    ix, iy, isz_ = px(vx + 45.5 - 39.0, vy + 46.5 - 39.0, 78.0)              # a 78 px icon centred in the 91 x 93 slot
    if isinstance(what, int):
        fw, fe = fv.iff(icmp('Greater_IntInt', iop('And_IntInt', B_WORN, 1 << what), 0), 'IfInvWorn%d' % what)
        fw = row_icon(fw, KI(what), ix, iy, isz_, isz_, raw=True, tag='Inv%d' % what)
    else:
        fw, fe = fv.iff(AND(kitworn, EMPTY['s']), 'IfInvKit') if what == 's' else (None, fv)
        if fw: fw = row_icon(fw, iop('Add_IntInt', K_WORN, 4), ix, iy, isz_, isz_, raw=True, tag='InvKit')
    fo_, fn_ = fe.iff(EMPTY[what], 'IfInvEmpty%s' % what)
    sprite(fo_, 'AtlasTex', ix, iy, isz_, isz_, cell_uv('out%d' % OUTK[what]), INV_OUT, tag='InvOut%s' % what, raw=True)
    fv = fo_.join(fn_, *([fw] if fw else []))

# ---------------------------------------------------------------- self-check + write
names = [n[0] for n in G.nodes]
assert len(names) == len(set(names)), 'duplicate node names'
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
outs = {(n[0], p['name']) for n in G.nodes for p in n[3] if p.get('out')}
wrongdir = [l for l in G.links if (l[0], l[1]) not in outs or (l[2], l[3]) in outs]
if wrongdir: raise SystemExit('direction: %s' % wrongdir[:10])
open(os.path.join(OUT, 'BPC_VesnaTrade_bd_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_VesnaTrade (#424 bundles): nodes %d, links %d' % (len(G.nodes), len(G.links)))
# (the BP_ArmoryHUD hook is unchanged: handoffs/shop-v2-418/trade/ArmoryHUD_TradeHook_graph.txt stays merged)

# ---------------------------------------------------------------- the variables the setup script creates (and their defaults)
VARS = dict(Tab=('int', 1), RTab=('int', 0), Sel=('int', 1), Scroll=('int', 0), Yaw=('double', 0.0), Zoom=('double', 1.0), Spin=('bool', True),
            Compare=('bool', True), WasOpen=('bool', False), Covering=('bool', False), MsgUntil=('double', 0.0), FlashUntil=('double', 0.0),
            LastT=('double', 0.0), Dragging=('bool', False), DragX=('double', 0.0), HeroYaw=('double', 0.0), BaseSpeed=('double', 0.0),
            HeroDamage=('int', 35), HeroMaxHP=('int', 250), CurDef=('int', 0),
            CapDist=('double', 330.0), CapHeight=('double', 20.0), PrevDown=('bool', False), ModeUI=('bool', False))
ICON_ORDER = ['Chest', 'Shoulders', 'Gauntlets', 'Shins', 'Boots', 'Forearms', 'UpperArms', 'Waist', 'Thighs', 'HeaterShield', 'RoundShield']   # T_VT_Icons, 128 px cells, 8 per row, 1024 x 256
BUNDLE_CELL = {'Torso': 1, 'Gauntlets': 2, 'Legs': 3}                     # T_VT_Bundles_424, 256 px cells, 1024 x 256
TURN = {'Torso': 'T_VT_Turn_Chest', 'Gauntlets': 'T_VT_Turn_Gauntlets', 'Legs': 'T_VT_Turn_Shins', 'RoundShield': 'T_VT_Turn_RoundShield', 'HeaterShield': 'T_VT_Turn_HeaterShield'}
pcs = L['pieces']
def icon_uv(p):
    if p['art'] in BUNDLE_CELL: return (BUNDLE_CELL[p['art']] * 0.25, 0.0, 0.25, 1.0)
    if p['art']: r_, c_ = divmod(ICON_ORDER.index(p['art']), 8); return (c_ * 128 / 1024.0, r_ * 128 / 256.0, 128 / 1024.0, 128 / 256.0)
    return cell_uv('glyph%d' % p['id'])
VARS.update(dict(Sel=('int', 1)))
DATA = dict(
    PieceIds=[p['id'] for p in pcs], PieceDef=[p['deff'] for p in pcs],
    NameUV=[cell_uv('name%d' % p['id']) for p in pcs], DefUV=[cell_uv('def%d' % p['id']) for p in pcs],
    TitleUV=[cell_uv('title%d' % p['id']) for p in pcs], TagUV=[cell_uv('tag%d' % p['id']) for p in pcs],
    IconUV=[icon_uv(p) for p in pcs], IconFromAtlas=[not p['art'] for p in pcs], IconFromBundle=[p['art'] in BUNDLE_CELL for p in pcs],
    TurnTex=[TURN.get(p['art']) for p in pcs], ShieldUV=cell_uv('glyph-1'))
json.dump(dict(vars=VARS, data=DATA), open(os.path.join(OUT, 'trade_bd_data.json'), 'w'), indent=1)
print('trade_bd_data.json: %d rows' % len(pcs))
