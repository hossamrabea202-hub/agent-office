# Motion graphics #66 / #139 / #140 / #86 (checkking, 2026-10-30): generates the EventGraph of the new hero component
# BPC_MotionFX (named MotionFX on the hero, made by setup_motionfx_ue.py).
#   python gen_motionfx.py  ->  BPC_MotionFX_graph.txt
# DrawReveal(Hud, SizeX, SizeY) is called every frame from BP_ArmoryHUD's DrawHUD (the checkking hook, then_2), after the
# shop, the inventory and the skill tree have drawn, so the reveal and its hint card sit on top of everything.
# Clock: real time from the first frame BookAge / BagAge (MPC_SkillTree, written by the game when the item is picked up)
# is between 0.05 and 2 s, so it keeps running while the game is paused. A load (BookAge = 100) never starts it.
# Per item, t = seconds since that frame:
#   0.0-3.6  dimmed screen, gold ray burst + sparkles (additive, counter-rotating), the pre-rendered 3D flipbook
#            (64 frames, 24 fps, T_Reveal_<Book|Bag>_Atlas) spinning in at 78 % of the screen height and opening;
#            a flash at 2.75 s as the light pours out, then it shrinks and fades 3.0-3.6 s "into" the HUD
#   3.0      BookOpenNow / BagOpenNow is true for one frame: BP_SkillTreeHUD / BP_QueueHUD OR it into the T / I key,
#            so the skill tree / pack opens by itself (manifest_skilltreehud.json, manifest_queuehud.json)
#   3.2-13   the how-to card (M_HintCard: gold frame draws on, shimmer) at the bottom centre, lines fade in one by one;
#            the book card carries #86 (double-click a skill or press UP to rank it up)
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP, HUDC = CLS('ActorComponent'), CLS('HUD')
MATL, MPC_CLS, MIDC = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection'), CLS('MaterialInstanceDynamic')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
SELF = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX', 'BPC_MotionFX')
UI = '/Game/CastleDefender/UI/Reveal/'
HINT = '/Game/CastleDefender/UI/Hints/M_HintCard.M_HintCard'
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
FONTC = '"/Script/CoreUObject.Class\'/Script/Engine.Font\'"'
TEXC = '"/Script/CoreUObject.Class\'/Script/Engine.Texture\'"'
BLEND = '"/Script/CoreUObject.Enum\'/Script/Engine.EBlendMode\'"'
V2D = '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector2D\'"'
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
DBL, BOOL = D('v', default='0.0'), bo('v', default='false')
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)


class B2(bpkit.B):
    def mpc_scalar(s, param, x, y):
        n = s.name('Get' + param)
        callfn(s.G, n, MATL, 'GetScalarParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC),
               {'name': 'ParameterName', 'cat': 'name', 'default': param}, fl('ReturnValue', out=True, default='0.0')], x=x, y=y, self_hidden=True)
        return n
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def lin(s, t, t0, dur, x, y):
        """saturate((t - t0) / dur)"""
        return s.sat(s.d2('Divide_DoubleDouble', s.d2('Subtract_DoubleDouble', t, None, x, y, db=str(t0)), None, x + 200, y, db=str(dur)), x + 400, y)
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def colr(s, r, g, b_, a, x, y, dr='1.0', dg='1.0', db_='1.0'):
        return s.math('MakeColor', [(fl('R', default=dr), r), (fl('G', default=dg), g), (fl('B', default=db_), b_), (fl('A', default='1.0'), a)], st('ReturnValue', LC, out=True), x, y)
    def tex(s, hud, path, X, Y, W, H, tint, x, y, U=None, V=None, UW=None, VH=None, du='0.0', dv='0.0', duw='1.0', dvh='1.0', blend='BLEND_Translucent', rot=None, tag='Tex'):
        n = s.call(HUDC, 'DrawTexture', [dict(ob('Texture', TEXC), dobj=UI + path), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'),
                   F('TextureU', du), F('TextureV', dv), F('TextureUWidth', duw), F('TextureVHeight', dvh), st('TintColor', LC, default=col(1, 1, 1)),
                   {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': blend}, F('Scale', '1.0'), bo('bScalePosition', default='false'),
                   F('Rotation', '0.0'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], x, y, target=hud, tag=tag)
        for p, v in (('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H), ('TintColor', tint), ('TextureU', U), ('TextureV', V),
                     ('TextureUWidth', UW), ('TextureVHeight', VH), ('Rotation', rot)):
            s.wire(v, n, p)
        return n
    def text(s, hud, txt, colr_, X, Y, scale, x, y, tag='Txt'):
        n = s.call(HUDC, 'DrawText', [S('Text', default=txt), st('TextColor', LC, default=col(1, 1, 1)), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT),
                   F('Scale', '1.0'), bo('bScalePosition', default='false')], x, y, target=hud, tag=tag)
        s.wire(colr_, n, 'TextColor'); s.wire(X, n, 'ScreenX'); s.wire(Y, n, 'ScreenY'); s.wire(scale, n, 'Scale')
        return n
    def mid_scalar(s, mid, param, val, x, y):
        n = s.call(MIDC, 'SetScalarParameterValue', [{'name': 'ParameterName', 'cat': 'name', 'default': param}, fl('Value', default='0.0')], x, y, target=mid, tag='Set' + param)
        s.wire(val, n, 'Value'); return n


G = Graph(); b = B2(G, 'm')

# ---- BeginPlay: the hint card's dynamic material ----
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
mk = b.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), dict(ob('Parent', MATI), dobj=HINT), {'name': 'OptionalName', 'cat': 'name', 'default': 'None'},
           {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None'},
           ob('ReturnValue', MIDC, out=True)], 300, 0, tag='MakeCardMID')
G.link('BP', 'then', mk, 'execute')
smid = b.set('CardMID', ob('v', MIDC), (mk, 'ReturnValue'), 650, 0); G.link(mk, 'then', smid, 'execute')

# ---- DrawReveal(Hud, SizeX, SizeY) ----
Y0 = 800
b.event('DrawReveal', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, Y0)
hud = ('DrawReveal', 'Hud')
sxd, syd = b.i2d(('DrawReveal', 'SizeX'), 200, Y0 + 300), b.i2d(('DrawReveal', 'SizeY'), 200, Y0 + 400)
sc = b.d2('Divide_DoubleDouble', syd, None, 400, Y0 + 400, db='1080.0')          # 1080p units
rnow = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], 200, Y0 + 550, pure=True, tag='RealNow')
now = (rnow, 'ReturnValue')

BOOK_LINES = ['[T]   Open the skill tree',
              'Every level grants a skill point. Click a skill to unlock it.',
              'Double-click a skill, or press its UP button, to rank it up.',
              '[1] [2] [3]   Cast your skills']
BAG_LINES = ['[I]   Open your pack',
             'Click an item, then a slot to equip it. Armour goes in the torso slot.',
             "Sell loot and buy gear at Vesna's market."]

def item(kind, age_param, atlas, title, lines, X):
    """one reveal (book or bag); its first node (mGet<Age>) is driven by the top sequence below."""
    T0, OP, ON = kind + 'T0', kind + 'Opened', kind + 'OpenNow'
    Y = Y0 + (0 if kind == 'Book' else 9000)
    ga = b.mpc_scalar(age_param, X, Y)
    age = (ga, 'ReturnValue')
    t0 = b.get(T0, DBL, X, Y + 300)
    start = b.b2('BooleanAND', b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', age, None, X + 200, Y + 400, db='0.05'),
                                     b.dcmp('Less_DoubleDouble', age, None, X + 200, Y + 500, db='2.0'), X + 400, Y + 450),
                 b.dcmp('LessEqual_DoubleDouble', t0, None, X + 200, Y + 600, db='0.0'), X + 600, Y + 500)
    bs = b.branch(start, X + 300, Y, tag='If%sStart' % kind); G.link(ga, 'then', bs, 'execute')
    s0 = b.set(T0, DBL, now, X + 600, Y - 200); G.link(bs, 'then', s0, 'execute')
    t0 = b.get(T0, DBL, X + 700, Y + 700)
    t = b.sub(now, t0, X + 900, Y + 700)
    active = b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', t0, None, X + 900, Y + 850, db='0.0'), b.dcmp('Less_DoubleDouble', t, None, X + 1100, Y + 850, db='13.0'), X + 1300, Y + 800)
    # one-frame open signal at t >= 3
    opn = b.b2('BooleanAND', b.b2('BooleanAND', active, b.dcmp('GreaterEqual_DoubleDouble', t, None, X + 1300, Y + 1000, db='3.0'), X + 1500, Y + 950),
               b.bnot(b.get(OP, BOOL, X + 1300, Y + 1150), X + 1500, Y + 1150), X + 1700, Y + 1050)
    sOn = b.set(ON, BOOL, opn, X + 1000, Y); G.link(bs, 'else', sOn, 'execute'); G.link(s0, 'then', sOn, 'execute')
    bo_ = b.branch(b.get(ON, BOOL, X + 1200, Y + 200), X + 1300, Y, tag='If%sOpen' % kind); G.link(sOn, 'then', bo_, 'execute')
    sOp = b.set(OP, bo('v', default='true'), None, X + 1600, Y - 200); G.link(bo_, 'then', sOp, 'execute')
    seq = b.seq(b.name('Seq' + kind), 2, X + 1900, Y); G.link(bo_, 'else', seq, 'execute'); G.link(sOp, 'then', seq, 'execute')

    # ---------- phase 1: flipbook + burst (t < 3.6)
    XP = X + 2200
    b1 = b.branch(b.b2('BooleanAND', active, b.dcmp('Less_DoubleDouble', t, None, XP, Y + 300, db='3.6'), XP + 200, Y + 250), XP, Y, tag='If%sFlip' % kind)
    G.link(seq, 'then_0', b1, 'execute')
    fin = b.lin(t, 0.0, 0.3, XP, Y + 500)
    fout = b.sat(b.d2('Divide_DoubleDouble', b.sub(None, t, XP, Y + 650, da='3.6'), None, XP + 200, Y + 650, db='0.5'), XP + 400, Y + 650)
    a = b.mul(fin, fout, XP + 600, Y + 550)
    dim = b.call(HUDC, 'DrawRect', [st('RectColor', LC, default=col(0, 0, 0, 0.6)), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], XP + 300, Y, target=hud, tag='Dim')
    b.wire(b.colr(None, None, None, b.mul(a, None, XP + 800, Y + 450, db='0.62'), XP + 1000, Y + 450, dr='0.0', dg='0.0', db_='0.0'), dim, 'RectColor')
    b.wire(sxd, dim, 'ScreenW'); b.wire(syd, dim, 'ScreenH'); G.link(b1, 'then', dim, 'execute')
    cx, cy = b.mul(sxd, None, XP, Y + 800, db='0.5'), b.mul(syd, None, XP, Y + 900, db='0.46')
    # flash at 2.75 s as the light pours out
    flash = b.sat(b.sub(None, b.d2('Divide_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), b.sub(t, None, XP, Y + 1100, db='2.75'))], D('ReturnValue', out=True), XP + 200, Y + 1100),
                                   None, XP + 400, Y + 1100, db='0.25'), XP + 600, Y + 1100, da='1.0'), XP + 800, Y + 1100)
    grow = b.lin(t, 0.0, 0.8, XP, Y + 1250)
    rs = b.mul(b.mul(syd, None, XP + 200, Y + 1400, db='1.25'), b.add(b.mul(grow, None, XP + 400, Y + 1250, db='0.8'), None, XP + 600, Y + 1250, db='0.2'), XP + 800, Y + 1350)
    rs = b.mul(rs, b.add(b.mul(flash, None, XP + 600, Y + 1500, db='0.35'), None, XP + 800, Y + 1500, db='1.0'), XP + 1000, Y + 1400)
    half = lambda v, x, y: b.mul(v, None, x, y, db='0.5')
    rx, ry = b.sub(cx, half(rs, XP + 1000, Y + 1550), XP + 1200, Y + 1550), b.sub(cy, half(rs, XP + 1000, Y + 1650), XP + 1200, Y + 1650)
    ra = b.mul(a, b.add(b.mul(flash, None, XP + 800, Y + 1750, db='1.2'), None, XP + 1000, Y + 1750, db='0.55'), XP + 1200, Y + 1750)
    rays = b.tex(hud, 'T_FX_RevealRays.T_FX_RevealRays', rx, ry, rs, rs, b.colr(None, None, None, ra, XP + 1400, Y + 1750, dr='1.0', dg='0.72', db_='0.32'),
                 XP + 600, Y, blend='BLEND_Additive', rot=b.mul(t, None, XP + 1400, Y + 1900, db='14.0'), tag='Rays')
    G.link(dim, 'then', rays, 'execute')
    sps = b.mul(syd, None, XP + 1400, Y + 2050, db='1.05')
    spx, spy = b.sub(cx, half(sps, XP + 1600, Y + 2050), XP + 1800, Y + 2050), b.sub(cy, half(sps, XP + 1600, Y + 2150), XP + 1800, Y + 2150)
    spk = b.tex(hud, 'T_FX_Sparkles.T_FX_Sparkles', spx, spy, sps, sps, b.colr(None, None, None, b.mul(a, None, XP + 1600, Y + 2250, db='0.85'), XP + 1800, Y + 2250, dr='1.0', dg='0.9', db_='0.6'),
                XP + 900, Y, blend='BLEND_Additive', rot=b.mul(t, None, XP + 1800, Y + 2350, db='-22.0'), tag='Sparkles')
    G.link(rays, 'then', spk, 'execute')
    # flipbook frame = clamp(floor(t * 24), 0, 63); cell (col, row) of the 8x8 atlas, row 0 at the top
    fr = b.math('FFloor', [(D('A', default='0.0'), b.mul(t, None, XP, Y + 2500, db='24.0'))], it('ReturnValue', out=True), XP + 200, Y + 2500)
    fr = b.i2('Min', b.i2('Max', fr, None, XP + 400, Y + 2500, db='0'), None, XP + 600, Y + 2500, db='63')
    cu = b.mul(b.i2d(b.i2('Percent_IntInt', fr, None, XP + 800, Y + 2450, db='8'), XP + 1000, Y + 2450), None, XP + 1200, Y + 2450, db='0.125')
    cv = b.mul(b.i2d(b.i2('Divide_IntInt', fr, None, XP + 800, Y + 2600, db='8'), XP + 1000, Y + 2600), None, XP + 1200, Y + 2600, db='0.125')
    shr = b.lin(t, 3.0, 0.6, XP, Y + 2750)
    fs = b.mul(b.mul(syd, None, XP + 400, Y + 2900, db='0.78'), b.sub(None, b.mul(shr, None, XP + 400, Y + 2750, db='0.35'), XP + 600, Y + 2750, da='1.0'), XP + 800, Y + 2850)
    fx_, fy_ = b.sub(cx, half(fs, XP + 1000, Y + 2850), XP + 1200, Y + 2850), b.sub(cy, half(fs, XP + 1000, Y + 2950), XP + 1200, Y + 2950)
    fa = b.mul(fin, b.sub(None, shr, XP + 1000, Y + 3050, da='1.0'), XP + 1200, Y + 3050)
    flip = b.tex(hud, atlas, fx_, fy_, fs, fs, b.colr(None, None, None, fa, XP + 1400, Y + 3050), XP + 1200, Y, U=cu, V=cv, duw='0.125', dvh='0.125', tag='Flip' + kind)
    G.link(spk, 'then', flip, 'execute')

    # ---------- phase 2: the how-to card (3.2 <= t < 13)
    XH = XP + 2200
    b2_ = b.branch(b.b2('BooleanAND', active, b.dcmp('GreaterEqual_DoubleDouble', t, None, XH, Y + 300, db='3.2'), XH + 200, Y + 250), XH, Y, tag='If%sCard' % kind)
    G.link(seq, 'then_1', b2_, 'execute')
    age2 = b.sub(t, None, XH, Y + 500, db='3.2')
    fade = b.sat(b.d2('Divide_DoubleDouble', b.sub(None, t, XH, Y + 650, da='13.0'), None, XH + 200, Y + 650, db='0.5'), XH + 400, Y + 650)
    cw, ch = b.mul(sc, None, XH, Y + 800, db='760.0'), b.mul(sc, None, XH, Y + 900, db=str(70.0 + 46.0 * len(lines)))
    cxl = b.sub(b.mul(sxd, None, XH + 200, Y + 800, db='0.5'), half(cw, XH + 200, Y + 900), XH + 400, Y + 850)
    cyt = b.sub(b.sub(syd, ch, XH + 200, Y + 1000), b.mul(sc, None, XH + 200, Y + 1100, db='70.0'), XH + 400, Y + 1000)
    mid = b.get('CardMID', ob('v', MIDC), XH, Y + 1200)
    vm = b.branch(b.valid(mid, XH + 200, Y + 1200), XH + 300, Y, tag='IfMID'); G.link(b2_, 'then', vm, 'execute')
    p1 = b.mid_scalar(mid, 'Age', age2, XH + 600, Y)
    p2 = b.mid_scalar(mid, 'Aspect', b.d2('Divide_DoubleDouble', cw, ch, XH + 600, Y + 1300), XH + 900, Y)
    p3 = b.mid_scalar(mid, 'Fade', fade, XH + 1200, Y)
    dm = b.call(HUDC, 'DrawMaterial', [ob('Material', MATI), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
                F('MaterialUWidth', '1.0'), F('MaterialVHeight', '1.0'), F('Scale', '1.0'), bo('bScalePosition', default='false'), F('Rotation'),
                st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], XH + 1500, Y, target=hud, tag='Card' + kind)
    b.wire(mid, dm, 'Material'); b.wire(cxl, dm, 'ScreenX'); b.wire(cyt, dm, 'ScreenY'); b.wire(cw, dm, 'ScreenW'); b.wire(ch, dm, 'ScreenH')
    b.chain(vm, p1, p2, p3, dm)
    tx = b.add(cxl, b.mul(sc, None, XH + 1500, Y + 1400, db='34.0'), XH + 1700, Y + 1400)
    last = dm
    for i, ln in enumerate([title] + lines):
        la = b.mul(b.lin(age2, 0.4 + 0.25 * i, 0.3, XH + 1700, Y + 1600 + i * 260), fade, XH + 2300, Y + 1600 + i * 260)
        cc = b.colr(None, None, None, la, XH + 2500, Y + 1600 + i * 260, *(('1.0', '0.72', '0.28') if i == 0 else ('0.92', '0.86', '0.74')))
        yy = b.add(cyt, b.mul(sc, None, XH + 2500, Y + 1750 + i * 260, db=str(24.0 + (0 if i == 0 else 22.0 + 46.0 * i))), XH + 2700, Y + 1750 + i * 260)
        tn = b.text(hud, ln, cc, tx, yy, b.mul(sc, None, XH + 2700, Y + 1850 + i * 260, db='0.40' if i == 0 else '0.27'), XH + 1800 + i * 300, Y, tag='Line%s%d' % (kind, i))
        G.link(last, 'then', tn, 'execute'); last = tn
    return seq

item('Book', 'BookAge', 'T_Reveal_Book_Atlas.T_Reveal_Book_Atlas', 'THE BOOK OF SKILLS', BOOK_LINES, 300)
item('Bag', 'BagAge', 'T_Reveal_Bag_Atlas.T_Reveal_Bag_Atlas', 'THE SATCHEL', BAG_LINES, 300)
top = b.seq('RevealSeq', 3, 150, Y0 - 300)   # then_2: free for the #141 add-on (manifest_motionfx_141.json)
G.link('DrawReveal', 'then', top, 'execute')
for n in G.nodes:      # first GetScalar of each item: hook its exec input to the top sequence
    if n[0].startswith('mGetBookAge'): G.link(top, 'then_0', n[0], 'execute')
    if n[0].startswith('mGetBagAge'): G.link(top, 'then_1', n[0], 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
open(os.path.join(HERE, 'BPC_MotionFX_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_MotionFX: nodes %d, links %d' % (len(G.nodes), len(G.links)))
