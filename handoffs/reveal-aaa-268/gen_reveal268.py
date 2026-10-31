# #268 AAA pickup reveal (adjustedfilm, 2026-10-31): new EventGraph for the hero component BPC_MotionFX (replaces the v1
# flipbook graph of #231, which the owner rejected). Same component, same DrawReveal(Hud, SizeX, SizeY) event, so the
# BP_ArmoryHUD hook, the I-key / T-key auto-open pastes (BagOpenNow / BookOpenNow) and the #141 add-on (RevealSeq.then_2)
# all keep working unchanged.
#   "<blender python>" -I gen_reveal268.py  ->  BPC_MotionFX_v2_graph.txt, VARIABLES_BPVar.txt
#
# BeginPlay: spawns BP_RevealStage far above the map (only the scene capture sees it), finds its Pivot / Capture / book /
#   satchel by tag, centres each mesh on the pivot, limits the capture to the stage, makes the 3 dynamic materials.
# DrawReveal, every HUD frame (also while paused: real time, the capture is triggered by hand):
#   trigger  BookAge / BagAge (MPC_SkillTree) between 0.05 and 2 s, item not seen yet -> pending; starts when nothing plays
#   timeline tl (s), with a 70 ms hit-stop at the peak (0.47):
#     0.00-0.12  anticipation: background starts to blur, the item pulls back (scale 0.50 -> 0.44)
#     0.12-0.47  reveal: ease-out expo to full size, spins in from -160 deg, ~6 % overshoot that settles by 0.9 s  (whoosh)
#     0.47       peak: light burst + anamorphic streak + ring, 3 deg camera push, 70 ms hit-stop                      (low hit)
#     0.55-1.25  title: per-letter slide-in, 35 ms stagger, gold shine sweep 1.0-1.6 s; how-to line with a key cap  (shimmer)
#     1.85-2.25  exit: the item flies on an arc into the dock bottom-right, the blur and the title fade
#     2.25       BookOpenNow / BagOpenNow true for one frame -> the skill tree / pack opens (T / I path); dock ring pulse
#     3.10       done
#   skip: mouse click, Space, Enter, E, Esc (after 0.35 s) jumps to the exit
import math, os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP, HUDC = CLS('ActorComponent'), CLS('HUD')
MATL, MPC_CLS, MIDC = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection'), CLS('MaterialInstanceDynamic')
CAPC, SCENEC, PRIMC = CLS('SceneCaptureComponent2D'), CLS('SceneCaptureComponent'), CLS('PrimitiveComponent')
PCON_, SOUND = CLS('PlayerController'), CLS('SoundBase')
MPC_SKILL = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
UI = '/Game/CastleDefender/UI/Reveal/'
MPC_REV = UI + 'MPC_Reveal.MPC_Reveal'
STAGE = '/Game/CastleDefender/UI/Reveal/BP_RevealStage'
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
FONTC = '"/Script/CoreUObject.Class\'/Script/Engine.Font\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
V2D = '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector2D\'"'
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
INT, DBL, BOOL = it('v', default='0'), D('v', default='0.0'), bo('v', default='false')
OBJV = lambda c: ob('v', c)
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)

GOLD, SHINE, INK = (1.0, 0.72, 0.30), (1.0, 0.95, 0.80), (0.92, 0.86, 0.74)
T_PEAK, T_HOLD, T_EXIT, T_OPEN, T_END = 0.47, 0.07, 1.85, 2.25, 3.10
BOOK_TITLE, BAG_TITLE = 'BOOK OF SKILLS', 'SATCHEL OF HOLDING'
BOOK_LINE, BAG_LINE = 'Open the skill tree', 'Open your pack'


class B4(bpkit.B):
    # ---- double math
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def div(s, a, c, x, y, da='0.0', db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, da=da, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def lin(s, t, t0, dur, x, y):
        """saturate((t - t0) / dur)"""
        return s.sat(s.div(s.sub(t, None, x, y, db=repr(t0)), None, x + 180, y, db=repr(dur)), x + 360, y)
    def one_minus(s, v, x, y): return s.sub(None, v, x, y, da='1.0')
    def fn1(s, m, a, x, y): return s.math(m, [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
    def sin(s, a, x, y): return s.fn1('Sin', a, x, y)
    def exp(s, a, x, y): return s.fn1('Exp', a, x, y)
    def fmax(s, a, c, x, y, db='0.0'): return s.d2('FMax', a, c, x, y, db=db)
    def fmin(s, a, c, x, y, db='0.0'): return s.d2('FMin', a, c, x, y, db=db)
    def lerp(s, a, c, t, x, y, da='0.0', db='0.0'):
        return s.math('Lerp', [(D('A', default=da), a), (D('B', default=db), c), (D('Alpha', default='0.0'), t)], D('ReturnValue', out=True), x, y)
    def pow2(s, e, x, y):
        return s.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), e)], D('ReturnValue', out=True), x, y)
    def smooth(s, v, x, y):
        """v*v*(3-2v) on a saturated v (ease in-out)"""
        return s.mul(s.mul(v, v, x, y), s.sub(None, s.mul(v, None, x, y + 120, db='2.0'), x + 180, y + 120, da='3.0'), x + 360, y)
    def cmp(s, m, a, c, x, y, db='0.0'): return s.dcmp(m, a, c, x, y, db=db)
    def colr(s, r, g, b_, a, x, y, dr='1.0', dg='1.0', db_='1.0'):
        return s.math('MakeColor', [(fl('R', default=dr), r), (fl('G', default=dg), g), (fl('B', default=db_), b_), (fl('A', default='1.0'), a)], st('ReturnValue', LC, out=True), x, y)
    # ---- objects / calls
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def item0(s, arrsrc, pin, x, y):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); return (n, 'Output')
    def by_tag(s, actor, cls, tag, x, y):
        n = s.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.' + cls.split('.')[-1].strip('\'"')), NAME_('Tag', tag),
                   arr(ob('ReturnValue', cls, out=True))], x, y, target=actor, pure=True, const=True, tag='Find' + tag)
        return s.item0((n, 'ReturnValue'), ob('v', cls), x + 260, y)
    def mpc_scalar(s, mpc, param, x, y):
        n = s.name('Get' + param)
        callfn(s.G, n, MATL, 'GetScalarParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=mpc), NAME_('ParameterName', param),
               fl('ReturnValue', out=True, default='0.0')], x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def mpc_set(s, mpc, param, val, x, y, dv='0.0'):
        n = s.name('Set' + param)
        callfn(s.G, n, MATL, 'SetScalarParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=mpc), NAME_('ParameterName', param),
               fl('ParameterValue', default=dv)], x=x, y=y, self_hidden=True)
        s.wire(val, n, 'ParameterValue'); return n
    def mid_scalar(s, mid, param, val, x, y, dv='0.0'):
        n = s.call(MIDC, 'SetScalarParameterValue', [NAME_('ParameterName', param), fl('Value', default=dv)], x, y, target=mid, tag='S' + param)
        s.wire(val, n, 'Value'); return n
    def mid_vector(s, mid, param, colsrc, x, y):
        n = s.call(MIDC, 'SetVectorParameterValue', [NAME_('ParameterName', param), st('Value', LC, default=col(0, 0, 0, 0))], x, y, target=mid, tag='V' + param)
        s.wire(colsrc, n, 'Value'); return n
    def make_mid(s, path, x, y, tag):
        return s.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), dict(ob('Parent', MATI), dobj=path), NAME_('OptionalName', 'None'),
                     {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None'},
                     ob('ReturnValue', MIDC, out=True)], x, y, tag=tag)
    def drawmat(s, hud, mid, X, Y, W, H, x, y, tag):
        n = s.call(HUDC, 'DrawMaterial', [ob('Material', MATI), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
                   F('MaterialUWidth', '1.0'), F('MaterialVHeight', '1.0'), F('Scale', '1.0'), bo('bScalePosition', default='false'), F('Rotation'),
                   st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], x, y, target=hud, tag=tag)
        for p, v in (('Material', mid), ('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n
    def rect(s, hud, colsrc, X, Y, W, H, x, y, tag='Rect'):
        n = s.call(HUDC, 'DrawRect', [st('RectColor', LC, default=col(0, 0, 0, 0)), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], x, y, target=hud, tag=tag)
        for p, v in (('RectColor', colsrc), ('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n
    def text(s, hud, txt, colsrc, X, Y, scale, x, y, tag='Txt', dtxt=''):
        n = s.call(HUDC, 'DrawText', [S('Text', default=dtxt), st('TextColor', LC, default=col(1, 1, 1)), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT),
                   F('Scale', '1.0'), bo('bScalePosition', default='false')], x, y, target=hud, tag=tag)
        for p, v in (('Text', txt), ('TextColor', colsrc), ('ScreenX', X), ('ScreenY', Y), ('Scale', scale)): s.wire(v, n, p)
        return n
    def tsize(s, hud, txt, scale, x, y, dtxt=''):
        n = s.call(HUDC, 'GetTextSize', [S('Text', default=dtxt), fl('OutWidth', out=True, default='0.0'), fl('OutHeight', out=True, default='0.0'),
                   dict(ob('Font', FONTC), dobj=FONT), fl('Scale', default='1.0')], x, y, target=hud, pure=True, const=True, tag='Size')
        s.wire(txt, n, 'Text'); s.wire(scale, n, 'Scale')
        return (n, 'OutWidth'), (n, 'OutHeight')
    def substr(s, src, start, length, x, y, dstart='0', dlen='1'):
        n = s.lib(KSTR, 'GetSubstring', [S('SourceString'), it('StartIndex', default=dstart), it('Length', default=dlen), S('ReturnValue', out=True)], x, y, pure=True, tag='Sub')
        s.wire(src, n, 'SourceString'); s.wire(start, n, 'StartIndex'); s.wire(length, n, 'Length'); return (n, 'ReturnValue')
    def strlen(s, src, x, y):
        n = s.lib(KSTR, 'Len', [S('S'), it('ReturnValue', out=True, default='0')], x, y, pure=True, tag='Len')
        s.wire(src, n, 'S'); return (n, 'ReturnValue')
    def setloc(s, member, comp, vec, x, y, tag):
        n = s.call(SCENE, member, [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], x, y, target=comp, tag=tag)
        s.wire(vec, n, 'NewLocation'); return n
    def worldloc(s, comp, x, y):
        n = s.call(SCENE, 'K2_GetComponentLocation', [V('ReturnValue', out=True)], x, y, target=comp, pure=True, const=True, tag='Loc')
        return (n, 'ReturnValue')
    def bounds(s, comp, x, y):
        n = s.lib(KSL, 'GetComponentBounds', [ob('Component', SCENE), V('Origin', out=True), V('BoxExtent', out=True), fl('SphereRadius', out=True, default='0.0')], x, y, pure=True, tag='Bounds')
        s.wire(comp, n, 'Component'); return (n, 'Origin'), (n, 'BoxExtent')
    def visible(s, comp, on, x, y, tag):
        n = s.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], x, y, target=comp, tag=tag)
        s.wire(on, n, 'bNewVisibility'); return n
    def sound(s, name, vol, x, y):
        return s.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', SOUND), dobj=UI + '%s.%s' % (name, name)), fl('VolumeMultiplier', default=vol),
                     fl('PitchMultiplier', default='1.000000'), fl('StartTime', default='0.000000')], x, y, tag=name[10:])
    def key(s, pc, k, x, y):
        n = s.call(PCON_, 'WasInputKeyJustPressed', [st('Key', KEY, default=k), bo('ReturnValue', out=True, default='false')], x, y, target=pc, pure=True, const=True, tag='Key' + k[:6])
        return (n, 'ReturnValue')
    def any_(s, vals, x, y):
        acc = vals[0]
        for i, v in enumerate(vals[1:]): acc = s.b2('BooleanOR', acc, v, x + 200 * i, y)
        return acc
    def all_(s, vals, x, y):
        acc = vals[0]
        for i, v in enumerate(vals[1:]): acc = s.b2('BooleanAND', acc, v, x + 200 * i, y)
        return acc


G = Graph(); b = B4(G, 'rv')
g = lambda var, pin, x, y: b.get(var, pin, x, y)
STAGEC = BPC(STAGE, 'BP_RevealStage')

# ================================================================================================= BeginPlay
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
sp = spawn(b, STAGE, STAGEC, transform(b, b.vec(None, None, None, 200, 300, dz='200000.0'), 450, 300), 400, 0)
G.link('BP', 'then', sp, 'execute')
ss = b.set('RvStage', OBJV(ACT), (sp, 'ReturnValue'), 800, 0); G.link(sp, 'then', ss, 'execute')
stage = lambda x, y: g('RvStage', OBJV(ACT), x, y)
sc_ = b.set('RvCap', OBJV(CAPC), b.by_tag(stage(800, 300), CAPC, 'RevealCapture', 950, 300), 1100, 0)
spv = b.set('RvPivot', OBJV(SCENE), b.by_tag(stage(1100, 450), SCENE, 'RevealPivot', 1250, 450), 1400, 0)
sbk = b.set('RvBook', OBJV(PRIMC), b.by_tag(stage(1400, 600), PRIMC, 'RevealBook', 1550, 600), 1700, 0)
sbg = b.set('RvBag', OBJV(PRIMC), b.by_tag(stage(1700, 750), PRIMC, 'RevealBag', 1850, 750), 2000, 0)
b.chain(ss, sc_, spv, sbk, sbg)
cap = lambda x, y: g('RvCap', OBJV(CAPC), x, y)
piv = lambda x, y: g('RvPivot', OBJV(SCENE), x, y)
vc = b.branch(b.valid(cap(2100, 300), 2250, 300), 2300, 0, tag='IfCap'); G.link(sbg, 'then', vc, 'execute')
so = b.call(SCENEC, 'ShowOnlyActorComponents', [ob('InActor', ACT), bo('bIncludeFromChildActors', default='false')], 2600, 0, target=cap(2450, 250), tag='ShowOnly')
b.wire(stage(2450, 400), so, 'InActor'); G.link(vc, 'then', so, 'execute')
last = so
X = 2900
for var in ('RvBook', 'RvBag'):         # centre each mesh on the pivot, so the spin turns about its middle
    it_ = lambda x, y, v=var: g(v, OBJV(PRIMC), x, y)
    vb = b.branch(b.valid(it_(X, 300), X + 150, 300), X + 200, 0, tag='If' + var); b.chain(last, vb)
    org, _ext = b.bounds(it_(X + 200, 450), X + 400, 450)
    delta = b.v2('Subtract_VectorVector', b.worldloc(piv(X + 400, 650), X + 600, 650), None, X + 850, 600)
    b.wire(org, delta[0], 'B')
    nl = b.v2('Add_VectorVector', b.worldloc(it_(X + 850, 800), X + 1050, 800), delta, X + 1250, 700)
    sw = b.setloc('K2_SetWorldLocation', it_(X + 1200, 300), nl, X + 1450, 0, 'Centre' + var[2:])
    G.link(vb, 'then', sw, 'execute')
    mg = b.seq(b.name('After' + var), 1, X + 1750, 0); G.link(sw, 'then', mg, 'execute'); G.link(vb, 'else', mg, 'execute')
    last, X = (mg, 'then_0'), X + 2000
mk = []
for i, (var, path) in enumerate((('RvItemMID', UI + 'M_RevealItem.M_RevealItem'), ('RvBackMID', UI + 'M_RevealScreen.M_RevealScreen'),
                                 ('RvFrontMID', UI + 'M_RevealScreen.M_RevealScreen'))):
    m_ = b.make_mid(path, X + i * 600, 0, 'Make' + var[2:])
    s_ = b.set(var, OBJV(MIDC), (m_, 'ReturnValue'), X + i * 600 + 300, 0)
    mk += [m_, s_]
G.link(last[0], last[1], mk[0], 'execute')
b.chain(*mk)
lay = b.mid_scalar(g('RvFrontMID', OBJV(MIDC), X + 1800, 300), 'Layer', None, X + 1900, 0, dv='1.0')
G.link(mk[-1], 'then', lay, 'execute')
blur0 = b.mpc_set(MPC_REV, 'Blur', None, X + 2200, 0); G.link(lay, 'then', blur0, 'execute')

# ================================================================================================= DrawReveal
Y0 = 1600
b.event('DrawReveal', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, Y0)
hud = ('DrawReveal', 'Hud')
top = b.seq('RevealSeq', 3, 200, Y0)          # then_0 trigger/start, then_1 the running reveal, then_2 free for #141
G.link('DrawReveal', 'then', top, 'execute')
W, H = b.i2d(('DrawReveal', 'SizeX'), 200, Y0 + 300), b.i2d(('DrawReveal', 'SizeY'), 200, Y0 + 400)
rn = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], 200, Y0 + 550, pure=True, tag='RealNow')
now = (rn, 'ReturnValue')
kind = lambda x, y: g('RvKind', INT, x, y)

# ---- then_0: clear the one-frame open pulses, mark pending items, start the next one when idle
Y = Y0
c1 = b.set('BookOpenNow', BOOL, None, 500, Y); c2 = b.set('BagOpenNow', BOOL, None, 750, Y)
G.link(top, 'then_0', c1, 'execute'); G.link(c1, 'then', c2, 'execute')
last = c2; X = 1000
for nm, age, opened in (('Book', 'BookAge', 'BookOpened'), ('Bag', 'BagAge', 'BagOpened')):
    a = b.mpc_scalar(MPC_SKILL, age, X, Y)            # impure in 5.3 (the live SkillTreeHUD export has it on the exec chain)
    b.chain(last, a[0])
    cond = b.all_([b.cmp('Greater_DoubleDouble', a, None, X + 250, Y + 300, db='0.05'), b.cmp('Less_DoubleDouble', a, None, X + 250, Y + 400, db='2.0'),
                   b.bnot(g(opened, BOOL, X + 250, Y + 500), X + 450, Y + 500)], X + 650, Y + 400)
    br = b.branch(cond, X + 300, Y, tag='If%sNew' % nm); b.chain(a[0], br)
    sp_ = b.set('Rv%sPend' % nm, bo('v', default='true'), None, X + 600, Y - 150); G.link(br, 'then', sp_, 'execute')
    mg = b.seq(b.name('Pend' + nm), 1, X + 900, Y); G.link(br, 'else', mg, 'execute'); G.link(sp_, 'then', mg, 'execute')
    last, X = (mg, 'then_0'), X + 1300
idle = b.icmp('EqualEqual_IntInt', kind(X, Y + 300), None, X + 200, Y + 300, db='0')
pend = b.b2('BooleanOR', g('RvBookPend', BOOL, X + 200, Y + 450), g('RvBagPend', BOOL, X + 200, Y + 550), X + 400, Y + 500)
bs = b.branch(b.all_([idle, pend, b.valid(cap(X + 200, Y + 650), X + 400, Y + 650)], X + 600, Y + 400), X + 300, Y, tag='IfStart'); G.link(last[0], last[1], bs, 'execute')
isbook = g('RvBookPend', BOOL, X + 500, Y + 700)
k = b.math('SelectInt', [(it('A', default='1'), None), (it('B', default='2'), None), (bo('bPickA', default='false'), isbook)], it('ReturnValue', out=True), X + 700, Y + 700)
sk = b.set('RvKind', INT, k, X + 600, Y); G.link(bs, 'then', sk, 'execute')
st0 = b.set('RvT0', DBL, now, X + 850, Y)
ssn = b.set('RvSnd', INT, None, X + 1100, Y)
isb = b.icmp('EqualEqual_IntInt', kind(X + 1100, Y + 300), None, X + 1300, Y + 300, db='1')
# mark seen + clear pending for the started one (Select keeps the other item's state)
sbo = b.set('BookOpened', BOOL, b.b2('BooleanOR', g('BookOpened', BOOL, X + 1300, Y + 450), isb, X + 1500, Y + 450), X + 1350, Y)
sgo = b.set('BagOpened', BOOL, b.b2('BooleanOR', g('BagOpened', BOOL, X + 1550, Y + 600), b.bnot(isb, X + 1550, Y + 700), X + 1750, Y + 600), X + 1600, Y)
sbp = b.set('RvBookPend', BOOL, b.b2('BooleanAND', g('RvBookPend', BOOL, X + 1800, Y + 450), b.bnot(isb, X + 1800, Y + 550), X + 2000, Y + 450), X + 1850, Y)
sgp = b.set('RvBagPend', BOOL, b.b2('BooleanAND', g('RvBagPend', BOOL, X + 2050, Y + 600), isb, X + 2250, Y + 600), X + 2100, Y)
book = lambda x, y: g('RvBook', OBJV(PRIMC), x, y)
bag = lambda x, y: g('RvBag', OBJV(PRIMC), x, y)
v1 = b.visible(book(X + 2300, Y + 300), isb, X + 2400, Y, 'ShowBook')
v2 = b.visible(bag(X + 2600, Y + 300), b.bnot(isb, X + 2600, Y + 450), X + 2700, Y, 'ShowBag')
# size of the shown item: R = |BoxExtent|, flat = extent Z < half the bigger of X / Y (a book lying on its cover)
_o1, e1 = b.bounds(book(X + 2700, Y + 600), X + 2900, Y + 600)
_o2, e2 = b.bounds(bag(X + 2700, Y + 800), X + 2900, Y + 800)
ext = b.selvec(e1, e2, isb, X + 3100, Y + 700)
rr = b.math('VSize', [(V('A'), ext)], D('ReturnValue', out=True), X + 3300, Y + 600)
sr = b.set('RvR', DBL, b.fmax(rr, None, X + 3500, Y + 600, db='5.0'), X + 3000, Y)
eb = b.brk(ext, X + 3300, Y + 800)
flat = b.cmp('Less_DoubleDouble', eb['Z'], b.mul(b.fmax(eb['X'], eb['Y'], X + 3500, Y + 850), None, X + 3700, Y + 850, db='0.5'), X + 3900, Y + 800)
sf = b.set('RvFlat', BOOL, flat, X + 3300, Y)
# capture distance: fit the item's sphere in a 30 deg FOV with 25 % margin (R / tan 15 deg * 1.25)
dist = b.mul(g('RvR', DBL, X + 3500, Y + 1000), None, X + 3700, Y + 1000, db='%.4f' % (1.25 / math.tan(math.radians(15))))
cl = b.setloc('K2_SetRelativeLocation', cap(X + 3700, Y + 300), b.vec(b.mul(dist, None, X + 3900, Y + 1000, db='-1.0'), None, None, X + 4100, Y + 1000), X + 3600, Y, 'CapDist')
b.chain(sk, st0, ssn, sbo, sgo, sbp, sgp, v1, v2, sr, sf, cl)

# ---- then_1: the running reveal
Y = Y0 + 2600
ba = b.branch(b.icmp('Greater_IntInt', kind(300, Y + 300), None, 500, Y + 300, db='0'), 500, Y, tag='IfPlaying')
G.link(top, 'then_1', ba, 'execute')
# idle: keep the blur off
bi = b.mpc_set(MPC_REV, 'Blur', None, 800, Y - 300); G.link(ba, 'else', bi, 'execute')
t0 = lambda x, y: g('RvT0', DBL, x, y)
raw = b.sub(now, t0(600, Y + 500), 800, Y + 500)
# hit-stop: time stands still for T_HOLD at the peak
tl = b.self_(raw, b.fmax(b.sub(raw, None, 1000, Y + 650, db=repr(T_HOLD)), None, 1200, Y + 650, db=repr(T_PEAK)),
             b.cmp('Less_DoubleDouble', raw, None, 1000, Y + 800, db=repr(T_PEAK)), 1400, Y + 600)
pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON_, out=True)], 800, Y + 1000, pure=True, tag='PC')
pcv = (pc, 'ReturnValue')
keys = [b.key(pcv, kk, 1000, Y + 950 + 100 * i) for i, kk in enumerate(('LeftMouseButton', 'SpaceBar', 'Enter', 'E', 'Escape'))]
skip = b.all_([b.valid(pcv, 1000, Y + 1500), b.any_(keys, 1300, Y + 1100), b.cmp('Greater_DoubleDouble', tl, None, 1300, Y + 1300, db='0.35'),
               b.cmp('Less_DoubleDouble', tl, None, 1300, Y + 1400, db=repr(T_EXIT))], 1700, Y + 1300)
bk_ = b.branch(skip, 800, Y, tag='IfSkip'); G.link(ba, 'then', bk_, 'execute')
sks = b.set('RvT0', DBL, b.sub(now, None, 1100, Y - 250, db=repr(T_EXIT + T_HOLD)), 1100, Y - 150); G.link(bk_, 'then', sks, 'execute')
mg = b.seq('AfterSkip', 1, 1400, Y); G.link(bk_, 'else', mg, 'execute'); G.link(sks, 'then', mg, 'execute')
last = (mg, 'then_0')

# ---- sounds on the beats, one each; a late beat (after a skip) is skipped but still counted
snd = lambda x, y: g('RvSnd', INT, x, y)
X = 1700
for i, (name, at, until, vol) in enumerate((('SFX_Reveal_Whoosh', 0.12, 0.47, '0.800000'), ('SFX_Reveal_Hit', T_PEAK, 1.0, '0.550000'),
                                            ('SFX_Reveal_Shimmer', 0.95, T_EXIT, '0.700000'))):
    due = b.b2('BooleanAND', b.icmp('EqualEqual_IntInt', snd(X, Y + 300), None, X + 200, Y + 300, db=str(i)),
               b.cmp('GreaterEqual_DoubleDouble', tl, None, X + 200, Y + 400, db=repr(at)), X + 400, Y + 350)
    bd = b.branch(due, X + 200, Y, tag='IfBeat%d' % i); G.link(last[0], last[1], bd, 'execute')
    bl = b.branch(b.cmp('Less_DoubleDouble', tl, None, X + 400, Y + 550, db=repr(until)), X + 450, Y, tag='IfOnTime%d' % i); G.link(bd, 'then', bl, 'execute')
    ps = b.sound(name, vol, X + 700, Y - 200); G.link(bl, 'then', ps, 'execute')
    sn = b.set('RvSnd', INT, None, X + 1000, Y); G.node  # value set below
    G.nodes[-1][3][2]['default'] = str(i + 1)
    G.link(ps, 'then', sn, 'execute'); G.link(bl, 'else', sn, 'execute')
    mg = b.seq(b.name('Beat%d' % i), 1, X + 1250, Y); G.link(bd, 'else', mg, 'execute'); G.link(sn, 'then', mg, 'execute')
    last, X = (mg, 'then_0'), X + 1500

# ---- one-frame open pulse at T_OPEN (RvSnd 4 = opened)
isb = b.icmp('EqualEqual_IntInt', kind(X, Y + 500), None, X + 200, Y + 500, db='1')
op = b.b2('BooleanAND', b.icmp('Less_IntInt', snd(X, Y + 300), None, X + 200, Y + 300, db='4'),
          b.cmp('GreaterEqual_DoubleDouble', tl, None, X + 200, Y + 400, db=repr(T_OPEN)), X + 400, Y + 350)
bo_ = b.branch(op, X + 200, Y, tag='IfOpen'); G.link(last[0], last[1], bo_, 'execute')
o1 = b.set('BookOpenNow', BOOL, isb, X + 500, Y - 200); o2 = b.set('BagOpenNow', BOOL, b.bnot(isb, X + 700, Y - 50), X + 750, Y - 200)
o3 = b.set('RvSnd', INT, None, X + 1000, Y - 200); G.nodes[-1][3][2]['default'] = '4'
b.chain(o1, o2, o3); G.link(bo_, 'then', o1, 'execute')
mg = b.seq('AfterOpen', 1, X + 1250, Y); G.link(bo_, 'else', mg, 'execute'); G.link(o3, 'then', mg, 'execute')
last = (mg, 'then_0'); X += 1500

# ---- curves (pure)
CY = Y + 2000
pa = b.lin(tl, 0.0, 0.12, 300, CY)                                  # anticipation progress
p = b.lin(tl, 0.12, 0.35, 300, CY + 150)                            # reveal progress
e = b.one_minus(b.pow2(b.mul(p, None, 900, CY + 150, db='-10.0'), 1100, CY + 150), 1300, CY + 150)     # ease-out expo
q = b.lin(tl, 0.30, 0.60, 300, CY + 300)
over = b.mul(b.mul(b.sin(b.mul(q, None, 900, CY + 300, db=repr(math.pi)), 1100, CY + 300), b.one_minus(q, 1100, CY + 400), 1300, CY + 350), None, 1500, CY + 350, db='0.104')
s_in = b.self_(b.sub(None, b.mul(pa, None, 1500, CY, db='0.06'), 1700, CY, da='0.5'),
               b.add(b.add(b.mul(e, None, 1500, CY + 150, db='0.56'), None, 1700, CY + 150, db='0.44'), over, 1900, CY + 250),
               b.cmp('Less_DoubleDouble', tl, None, 1900, CY + 400, db='0.12'), 2100, CY + 100)
xo = b.lin(tl, T_EXIT, T_OPEN - T_EXIT, 300, CY + 600)               # exit progress
ein = b.smooth(xo, 900, CY + 600)
SCL = b.mul(s_in, b.sub(None, b.mul(ein, None, 2100, CY + 600, db='0.9'), 2300, CY + 600, da='1.0'), 2500, CY + 300)
itemA = b.mul(b.lin(tl, 0.0, 0.06, 300, CY + 850), b.one_minus(b.lin(tl, 2.15, 0.10, 900, CY + 950), 1500, CY + 950), 1700, CY + 900)
burst = b.self_(b.lin(tl, 0.40, 0.07, 300, CY + 1100),
                b.exp(b.mul(b.sub(tl, None, 900, CY + 1250, db=repr(T_PEAK)), None, 1100, CY + 1250, db='-6.0'), 1300, CY + 1250),
                b.cmp('Less_DoubleDouble', tl, None, 1300, CY + 1400, db=repr(T_PEAK)), 1500, CY + 1150)
ring = b.mul(b.lin(tl, T_PEAK, 0.6, 300, CY + 1550), b.math('Conv_BoolToDouble', [(bo('InBool', default='false'), b.cmp('Greater_DoubleDouble', tl, None, 900, CY + 1650, db=repr(T_PEAK)))],
             D('ReturnValue', out=True), 1100, CY + 1650), 1300, CY + 1600)
bg = b.mul(b.lin(tl, 0.0, 0.3, 300, CY + 1800), b.one_minus(xo, 900, CY + 1900), 1100, CY + 1850)
glow = b.mul(bg, b.add(b.mul(burst, None, 1300, CY + 1950, db='0.8'), None, 1500, CY + 1950, db='0.6'), 1700, CY + 1900)
ta = b.one_minus(b.lin(tl, T_EXIT, 0.2, 300, CY + 2100), 900, CY + 2100)               # title alpha (fade at exit)
la = b.mul(b.lin(tl, 0.95, 0.25, 300, CY + 2250), ta, 900, CY + 2250)                  # how-to line alpha
dockA = b.mul(b.lin(tl, 2.2, 0.08, 300, CY + 2400), b.one_minus(b.lin(tl, 2.5, 0.6, 900, CY + 2500), 1500, CY + 2500), 1700, CY + 2450)
dockR = b.add(b.mul(b.lin(tl, 2.2, 0.5, 300, CY + 2650), None, 900, CY + 2650, db='0.03'), None, 1100, CY + 2650, db='0.012')
isbk = b.icmp('EqualEqual_IntInt', kind(300, CY + 2800), None, 500, CY + 2800, db='1')
yaw0 = b.self_(g('RvBookYaw0', DBL, 700, CY + 2800), g('RvBagYaw0', DBL, 700, CY + 2900), isbk, 900, CY + 2850)
idle_ = b.mul(b.sin(b.mul(b.sub(tl, None, 900, CY + 3000, db=repr(T_PEAK)), None, 1100, CY + 3000, db='1.3'), 1300, CY + 3000), b.lin(tl, T_PEAK, 0.6, 900, CY + 3100), 1500, CY + 3050)
yaw = b.add(b.add(b.add(yaw0, b.mul(b.one_minus(e, 1100, CY + 3200), None, 1300, CY + 3200, db='-160.0'), 1500, CY + 3200),
                  b.mul(idle_, None, 1700, CY + 3050, db='7.0'), 1900, CY + 3100), b.mul(ein, None, 1700, CY + 3300, db='120.0'), 2100, CY + 3200)
pitch = b.self_(None, None, g('RvFlat', BOOL, 1900, CY + 3400), 2100, CY + 3400, da='70.0', db='10.0')
fov = b.sub(None, b.mul(burst, None, 2100, CY + 1150, db='3.0'), 2300, CY + 1150, da='30.0')
# screen layout
sc = b.div(H, None, 2500, CY + 1500, db='1080.0')
itemH = b.mul(b.mul(H, None, 2500, CY + 1650, db='0.56'), SCL, 2700, CY + 1600)
cx = b.lerp(b.mul(W, None, 2500, CY + 1800, db='0.5'), b.mul(W, None, 2500, CY + 1900, db='0.93'), ein, 2700, CY + 1850)
cy = b.sub(b.lerp(b.mul(H, None, 2500, CY + 2050, db='0.45'), b.mul(H, None, 2500, CY + 2150, db='0.88'), ein, 2700, CY + 2100),
           b.mul(b.mul(H, None, 2500, CY + 2300, db='0.10'), b.sin(b.mul(ein, None, 2500, CY + 2400, db=repr(math.pi)), 2700, CY + 2400), 2900, CY + 2350), 3100, CY + 2200)
half = b.mul(itemH, None, 2900, CY + 1600, db='0.5')
asp = b.div(W, H, 2900, CY + 1500)
cU, cV = b.div(cx, W, 3100, CY + 1850), b.div(cy, H, 3300, CY + 2200)
rad = b.div(half, H, 3100, CY + 1600)
centre = b.colr(cU, cV, None, None, 3500, CY + 2000, db_='0.0')
dock = b.colr(None, None, None, dockA, 3500, CY + 2450, dr='0.93', dg='0.88', db_='0.0')

# ---- stage: pose, push, capture; background blur
X += 0
rot = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='0.0'), pitch), (fl('Yaw', default='0.0'), yaw)], st('ReturnValue', ROT, out=True), X, Y + 400)
sr_ = b.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
             bo('bTeleport', default='true')], X + 300, Y, target=piv(X + 100, Y + 250), tag='Pose')
b.wire(rot, sr_, 'NewRotation'); G.link(last[0], last[1], sr_, 'execute')
sfov = b.setm('FOVAngle', CAPC, fl('v', default='30.0'), fov, cap(X + 450, Y + 300), X + 600, Y)
cs = b.call(CAPC, 'CaptureScene', [], X + 900, Y, target=cap(X + 750, Y + 300), tag='Capture')
sb = b.mpc_set(MPC_REV, 'Blur', bg, X + 1200, Y)
b.chain(sr_, sfov, cs, sb)
X += 1500

# ---- draw: back layer, item, front layer
backm = lambda x, y: g('RvBackMID', OBJV(MIDC), x, y)
frontm = lambda x, y: g('RvFrontMID', OBJV(MIDC), x, y)
itemm = lambda x, y: g('RvItemMID', OBJV(MIDC), x, y)
vm = b.branch(b.all_([b.valid(backm(X, Y + 300), X + 150, Y + 300), b.valid(itemm(X, Y + 400), X + 150, Y + 400), b.valid(frontm(X, Y + 500), X + 150, Y + 500)],
              X + 350, Y + 400), X + 200, Y, tag='IfMIDs')
G.link(sb, 'then', vm, 'execute')
chain = [vm]; XX = X + 500
for prm, val in (('T', tl), ('Aspect', asp), ('Rad', rad), ('Bg', bg), ('Glow', glow), ('Dust', bg), ('ItemA', itemA)):
    chain.append(b.mid_scalar(backm(XX, Y + 300), prm, val, XX + 100, Y)); XX += 300
chain.append(b.mid_vector(backm(XX, Y + 300), 'Center', centre, XX + 100, Y)); XX += 300
chain.append(b.drawmat(hud, backm(XX, Y + 300), None, None, W, H, XX + 100, Y, 'DrawBack')); XX += 400
for prm, val in (('Alpha', itemA), ('Flash', burst)):
    chain.append(b.mid_scalar(itemm(XX, Y + 300), prm, val, XX + 100, Y)); XX += 300
ix, iy = b.sub(cx, half, XX, Y + 500), b.sub(cy, half, XX, Y + 600)
chain.append(b.drawmat(hud, itemm(XX, Y + 300), ix, iy, itemH, itemH, XX + 200, Y, 'DrawItem')); XX += 500
for prm, val in (('T', tl), ('Aspect', asp), ('Rad', rad), ('Burst', burst), ('Ring', ring), ('Dust', bg), ('DockR', dockR)):
    chain.append(b.mid_scalar(frontm(XX, Y + 300), prm, val, XX + 100, Y)); XX += 300
chain.append(b.mid_vector(frontm(XX, Y + 300), 'Center', centre, XX + 100, Y)); XX += 300
chain.append(b.mid_vector(frontm(XX, Y + 300), 'Dock', dock, XX + 100, Y)); XX += 300
chain.append(b.drawmat(hud, frontm(XX, Y + 300), None, None, W, H, XX + 100, Y, 'DrawFront')); XX += 400
b.chain(*chain)

# ---- title: per-letter slide-in with a gold shine sweep
title = b.selstr(None, None, isbk, XX, Y + 600, da=BOOK_TITLE, db=BAG_TITLE)
w1, _h1 = b.tsize(hud, title, None, XX + 200, Y + 700)
ts = b.div(b.mul(W, None, XX + 400, Y + 800, db='0.34'), b.fmax(w1, None, XX + 400, Y + 700, db='1.0'), XX + 600, Y + 750)    # title = 34 % of the width
wT, hT = b.tsize(hud, title, ts, XX + 800, Y + 700)
x0 = b.sub(b.mul(W, None, XX + 1000, Y + 800, db='0.5'), b.mul(wT, None, XX + 1000, Y + 700, db='0.5'), XX + 1200, Y + 750)
ty = b.mul(H, None, XX + 1000, Y + 900, db='0.755')
n_ = b.strlen(title, XX + 200, Y + 1000)
lp = b.forloop(None, b.i2('Subtract_IntInt', n_, None, XX + 400, Y + 1000, db='1'), XX + 300, Y)
G.link(chain[-1], 'then', lp, 'execute')
idx = (lp, 'Index'); fi = b.i2d(idx, XX + 600, Y + 1200)
ch = b.substr(title, idx, None, XX + 600, Y + 1300)
pre = b.substr(title, None, idx, XX + 600, Y + 1400)
xw, _ = b.tsize(hud, pre, ts, XX + 800, Y + 1400)
ai = b.sat(b.div(b.sub(b.sub(tl, None, XX + 800, Y + 1550, db='0.55'), b.mul(fi, None, XX + 800, Y + 1650, db='0.035'), XX + 1000, Y + 1600), None, XX + 1200, Y + 1600, db='0.25'), XX + 1400, Y + 1600)
om = b.one_minus(ai, XX + 1600, Y + 1600)
dy = b.mul(b.mul(b.mul(om, om, XX + 1800, Y + 1650), om, XX + 2000, Y + 1650), b.mul(sc, None, XX + 2000, Y + 1750, db='22.0'), XX + 2200, Y + 1700)
u = b.div(fi, b.fmax(b.i2d(b.i2('Subtract_IntInt', n_, None, XX + 800, Y + 1850, db='1'), XX + 1000, Y + 1850), None, XX + 1200, Y + 1850, db='1.0'), XX + 1400, Y + 1850)
sx = b.div(b.sub(tl, None, XX + 800, Y + 2000, db='1.0'), None, XX + 1000, Y + 2000, db='0.6')
dd = b.mul(b.sub(u, sx, XX + 1600, Y + 1950), None, XX + 1800, Y + 1950, db='5.0')
shine = b.exp(b.mul(b.mul(dd, dd, XX + 2000, Y + 1950), None, XX + 2200, Y + 1950, db='-1.0'), XX + 2400, Y + 1950)
alpha = b.mul(ai, ta, XX + 1800, Y + 1500)
cc = b.colr(b.lerp(None, None, shine, XX + 2600, Y + 1850, da=repr(GOLD[0]), db=repr(SHINE[0])),
            b.lerp(None, None, shine, XX + 2600, Y + 1950, da=repr(GOLD[1]), db=repr(SHINE[1])),
            b.lerp(None, None, shine, XX + 2600, Y + 2050, da=repr(GOLD[2]), db=repr(SHINE[2])), alpha, XX + 2800, Y + 1900)
lx = b.add(x0, xw, XX + 1000, Y + 1400)
ly = b.add(ty, dy, XX + 2400, Y + 1700)
off = b.mul(sc, None, XX + 2400, Y + 2200, db='2.0')
shadow = b.text(hud, ch, b.colr(None, None, None, b.mul(alpha, None, XX + 2600, Y + 2300, db='0.55'), XX + 2800, Y + 2300, dr='0.0', dg='0.0', db_='0.0'),
                b.add(lx, off, XX + 2600, Y + 2400), b.add(ly, off, XX + 2600, Y + 2500), ts, XX + 1100, Y - 300, tag='TitleShadow')
glyph = b.text(hud, ch, cc, lx, ly, ts, XX + 1400, Y - 300, tag='TitleGlyph')
G.link(lp, 'LoopBody', shadow, 'execute'); G.link(shadow, 'then', glyph, 'execute')
XX += 3100

# ---- how-to line: key cap + one short line, centred under the title
line = b.selstr(None, None, isbk, XX, Y + 600, da=BOOK_LINE, db=BAG_LINE)
letter = b.selstr(None, None, isbk, XX, Y + 700, da='T', db='I')
ls = b.mul(ts, None, XX, Y + 800, db='0.45')
lw, lh = b.tsize(hud, line, ls, XX + 200, Y + 600)
kw_, kh_ = b.tsize(hud, letter, ls, XX + 200, Y + 900)
kh = b.mul(lh, None, XX + 400, Y + 700, db='1.45')
gap = b.mul(sc, None, XX + 400, Y + 800, db='12.0')
total = b.add(b.add(kh, gap, XX + 600, Y + 750), lw, XX + 800, Y + 700)
kx = b.sub(b.mul(W, None, XX + 800, Y + 900, db='0.5'), b.mul(total, None, XX + 800, Y + 1000, db='0.5'), XX + 1000, Y + 950)
ky = b.add(b.add(ty, hT, XX + 800, Y + 1100), b.mul(sc, None, XX + 800, Y + 1200, db='16.0'), XX + 1000, Y + 1150)
bw = b.mul(sc, None, XX + 1000, Y + 1300, db='2.0')
gc = b.colr(None, None, None, b.mul(la, None, XX + 1200, Y + 1400, db='0.9'), XX + 1400, Y + 1400, dr=repr(GOLD[0]), dg=repr(GOLD[1]), db_=repr(GOLD[2]))
r1 = b.rect(hud, gc, b.sub(kx, bw, XX + 1200, Y + 1500), b.sub(ky, bw, XX + 1200, Y + 1600), b.add(kh, b.mul(bw, None, XX + 1200, Y + 1700, db='2.0'), XX + 1400, Y + 1700),
            b.add(kh, b.mul(bw, None, XX + 1200, Y + 1800, db='2.0'), XX + 1400, Y + 1800), XX + 300, Y, tag='KeyFrame')
r2 = b.rect(hud, b.colr(None, None, None, b.mul(la, None, XX + 1600, Y + 1500, db='0.88'), XX + 1800, Y + 1500, dr='0.07', dg='0.055', db_='0.04'),
            kx, ky, kh, kh, XX + 600, Y, tag='KeyFace')
t1 = b.text(hud, letter, b.colr(None, None, None, la, XX + 1800, Y + 1650, dr=repr(SHINE[0]), dg=repr(SHINE[1]), db_=repr(SHINE[2])),
            b.add(kx, b.mul(b.sub(kh, kw_, XX + 1600, Y + 1800), None, XX + 1800, Y + 1800, db='0.5'), XX + 2000, Y + 1800),
            b.add(ky, b.mul(b.sub(kh, kh_, XX + 1600, Y + 1900), None, XX + 1800, Y + 1900, db='0.5'), XX + 2000, Y + 1900), ls, XX + 900, Y, tag='KeyLetter')
t2 = b.text(hud, line, b.colr(None, None, None, la, XX + 1800, Y + 2050, dr=repr(INK[0]), dg=repr(INK[1]), db_=repr(INK[2])),
            b.add(b.add(kx, kh, XX + 1600, Y + 2150), gap, XX + 1800, Y + 2150),
            b.add(ky, b.mul(b.sub(kh, lh, XX + 1600, Y + 2250), None, XX + 1800, Y + 2250, db='0.5'), XX + 2000, Y + 2250), ls, XX + 1200, Y, tag='HowTo')
G.link(lp, 'Completed', r1, 'execute'); b.chain(r1, r2, t1, t2)
XX += 2300

# ---- done: hide the item, stop
be = b.branch(b.cmp('GreaterEqual_DoubleDouble', tl, None, XX, Y + 300, db=repr(T_END)), XX + 200, Y, tag='IfDone'); G.link(t2, 'then', be, 'execute')
k0 = b.set('RvKind', INT, None, XX + 500, Y); G.link(be, 'then', k0, 'execute')
h1 = b.visible(book(XX + 700, Y + 300), None, XX + 800, Y, 'HideBook')
h2 = b.visible(bag(XX + 1000, Y + 300), None, XX + 1100, Y, 'HideBag')
b0 = b.mpc_set(MPC_REV, 'Blur', None, XX + 1400, Y)
b.chain(k0, h1, h2, b0)

# ================================================================================================= checks + output
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
names = [n[0] for n in G.nodes]
dup = {n for n in names if names.count(n) > 1}
if dup: raise SystemExit('duplicate node names: %s' % sorted(dup)[:10])
open(os.path.join(HERE, 'BPC_MotionFX_v2_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_MotionFX v2: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---- BPVar lines (the v1 variables BookOpened / BagOpened / BookOpenNow / BagOpenNow are already on the component)
def bpvar(name, vt, default):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
        name, uuid.uuid5(uuid.NAMESPACE_URL, 'reveal268/' + name).hex.upper(), vt, name, default)
REAL = 'PinCategory="real",PinSubCategory="double"'
OBJ_ = lambda c: 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % c
VARS = [('RvKind', 'PinCategory="int"', '0'), ('RvT0', REAL, '0.0'), ('RvSnd', 'PinCategory="int"', '0'),
        ('RvBookPend', 'PinCategory="bool"', 'false'), ('RvBagPend', 'PinCategory="bool"', 'false'),
        ('RvR', REAL, '20.0'), ('RvFlat', 'PinCategory="bool"', 'false'), ('RvBookYaw0', REAL, '25.0'), ('RvBagYaw0', REAL, '25.0'),
        ('RvStage', OBJ_('Actor'), ''), ('RvCap', OBJ_('SceneCaptureComponent2D'), ''), ('RvPivot', OBJ_('SceneComponent'), ''),
        ('RvBook', OBJ_('PrimitiveComponent'), ''), ('RvBag', OBJ_('PrimitiveComponent'), ''),
        ('RvItemMID', OBJ_('MaterialInstanceDynamic'), ''), ('RvBackMID', OBJ_('MaterialInstanceDynamic'), ''), ('RvFrontMID', OBJ_('MaterialInstanceDynamic'), '')]
used = {p for n in G.nodes for p in n[2] if 'VariableReference' in p}
for v, _t, _d in VARS:
    if not any('"%s"' % v in u for u in used): raise SystemExit('BPVar %s is never used' % v)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_MotionFX (#268) - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpvar(*v) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
