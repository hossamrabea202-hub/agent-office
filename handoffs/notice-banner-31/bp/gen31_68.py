# #31 notice banner + #68 prompt fade: generates the Blueprint pastes (laptop2, 2026-10-29). Run with any Python 3:
#   python gen31_68.py  ->  NoticeHUD_Banner_graph.txt   (BP_NoticeHUD EventGraph: PushNotice + the banner draw)
#                           ZombieHUD_VesnaFade_graph.txt (BP_ZombieHUD: fade + breathing for "[E] Speak with Vesna")
# Built on the Master's node kit (tools/master/t81/kit.py) and the 10-28 exports (laptop2/prompt68, laptop2/set96).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'master', 't81'))
from kit import *

OBJ = '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"'
HUD, GS, STR = CLS('HUD'), CLS('GameplayStatics'), CLS('KismetStringLibrary')
LC = STRUCT('LinearColor')
MIDC = CLS('MaterialInstanceDynamic')
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
BANNER = '/Game/CastleDefender/UI/Notices/M_NoticeBanner.M_NoticeBanner'

def D(name, out=False, default=None): return fl(name, out=out, default=default, sub='double')
def S(name, out=False, default=None): return {'name': name, 'cat': 'string', 'out': out, 'default': default}
def E(name, enum, default): return {'name': name, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'%s\'"' % enum, 'default': default}
WC = lambda: ob('WorldContextObject', OBJ, hidden=True)

class B:
    def __init__(s, G, p): s.G, s.p, s.n = G, p, 0
    def name(s, t): s.n += 1; return '%s%s%d' % (s.p, t, s.n)
    def wire(s, src, node, pin):
        if src is not None: s.G.link(src[0], src[1], node, pin)
    def lib(s, cls, member, ins, outs, x, y, tag=None):
        n = s.name(tag or member[:8])
        callfn(s.G, n, cls, member, [p for p, _ in ins] + outs, pure=True, x=x, y=y, self_hidden=True)
        for p, src in ins: s.wire(src, n, p['name'])
        return n
    def m(s, member, ins, out, x, y):
        n = s.name(member[:8]); mathfn(s.G, n, member, [p for p, _ in ins] + [out], x, y)
        for p, src in ins: s.wire(src, n, p['name'])
        return (n, out['name'])
    def sm(s, member, ins, out, x, y):
        n = s.lib(STR, member, ins, [out], x, y); return (n, out['name'])
    def d2(s, member, a, b, x, y, da='0.0', db='0.0'):
        return s.m(member, [(D('A', default=da), a), (D('B', default=db), b)], D('ReturnValue', out=True), x, y)
    def dc(s, member, a, b, x, y, da='0.0', db='0.0'):
        return s.m(member, [(D('A', default=da), a), (D('B', default=db), b)], bo('ReturnValue', out=True), x, y)
    def b2(s, member, a, b, x, y, da='false', db='false'):
        return s.m(member, [(bo('A', default=da), a), (bo('B', default=db), b)], bo('ReturnValue', out=True), x, y)
    def bnot(s, a, x, y): return s.m('Not_PreBool', [(bo('A', default='false'), a)], bo('ReturnValue', out=True), x, y)
    def sat(s, v, x, y): return s.m('FClamp', [(D('Value', default='0.0'), v), (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), x, y)
    def clamp(s, v, lo, hi, x, y, dlo='0.0', dhi='1.0'):
        return s.m('FClamp', [(D('Value', default='0.0'), v), (D('Min', default=dlo), lo), (D('Max', default=dhi), hi)], D('ReturnValue', out=True), x, y)
    def sel(s, a, b, pick, x, y, da='0.0', db='0.0'):
        return s.m('SelectFloat', [(D('A', default=da), a), (D('B', default=db), b), (bo('bPickA', default='false'), pick)], D('ReturnValue', out=True), x, y)
    def b2d(s, a, x, y): return s.m('Conv_BoolToDouble', [(bo('InBool', default='false'), a)], D('ReturnValue', out=True), x, y)
    def i2d(s, a, x, y, d='0'): return s.m('Conv_IntToDouble', [(it('InInt', default=d), a)], D('ReturnValue', out=True), x, y)
    def get(s, var, pin, x, y):
        n = s.name('Get' + var); varget(s.G, n, None, var, None, dict(pin, name=var), x, y, self_ctx=True); return (n, var)
    def set(s, var, pin, src, x, y):
        n = s.name('Set' + var); varset(s.G, n, None, var, None, dict(pin, name=var), x, y, self_ctx=True); s.wire(src, n, var); return n
    def realnow(s, x, y):
        return (s.lib(GS, 'GetRealTimeSeconds', [(WC(), None)], [D('ReturnValue', out=True)], x, y, 'Now'), 'ReturnValue')
    def color(s, r, g, b_, a, x, y, dr='0.0', dg='0.0', db='0.0'):
        n = s.name('Col'); mathfn(s.G, n, 'MakeColor', [fl('R', default=dr), fl('G', default=dg), fl('B', default=db), fl('A', default='1.0'), st('ReturnValue', LC, out=True)], x, y)
        for c, src in zip('RGBA', (r, g, b_, a)): s.wire(src, n, c)
        return (n, 'ReturnValue')
    def hud(s, member, pins, x, y, pure=False):
        n = s.name(member[:8])
        props = (['bIsPureFunc=True'] if pure else []) + ['FunctionReference=(MemberName="%s",bSelfContext=True)' % member]
        s.G.node(n, 'K2Node_CallFunction', props, ([] if pure else [ex(), ex('then', True)]) + [selfpin(HUD, hidden=True)] + pins, x, y)
        return n
    def textsize(s, text, scale, x, y, dtext=None, dscale='1.0'):
        n = s.hud('GetTextSize', [S('Text', default=dtext), fl('OutWidth', out=True, default='0.0'), fl('OutHeight', out=True, default='0.0'),
                                  dict(ob('Font', CLS('Font')), dobj=FONT), fl('Scale', default=dscale)], x, y, pure=True)
        s.wire(text, n, 'Text'); s.wire(scale, n, 'Scale')
        return (n, 'OutWidth'), (n, 'OutHeight')
    def drawtext(s, text, col, px, py, scale, x, y):
        n = s.hud('DrawText', [S('Text'), st('TextColor', LC), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'),
                               dict(ob('Font', CLS('Font')), dobj=FONT), fl('Scale', default='1.0'), bo('bScalePosition', default='false')], x, y)
        for p, src in (('Text', text), ('TextColor', col), ('ScreenX', px), ('ScreenY', py), ('Scale', scale)): s.wire(src, n, p)
        return n
    def event(s, name, params, x, y):
        props = ['CustomFunctionName="%s"' % name]
        for p in params:
            t = 'PinCategory="%s"' % p['cat'] + (',PinSubCategory="%s"' % p['sub'] if p.get('sub') else '')
            props.append('CustomProperties UserDefinedPin (PinName="%s",PinType=(%s),DesiredPinDirection=EGPD_Output)' % (p['name'], t))
        s.G.node(name, 'K2Node_CustomEvent', props, [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '()'}, ex('then', True)]
                 + [dict(p, out=True, default=None) for p in params], x, y)
        return name
    def chain(s, *ns):
        for a, b in zip(ns, ns[1:]):
            s.G.link(a[0] if isinstance(a, tuple) else a, a[1] if isinstance(a, tuple) else 'then', b, 'execute')
    def br(s, cond, x, y):
        n = s.name('If'); branch(s.G, n, x, y); s.wire(cond, n, 'Condition'); return n
    def entry(s, name, x, y):
        sequence(s.G, name, 1, x, y); return (name, 'then_0')
    # pass-through nodes = named sockets for the Master's rewires
    def pass_b(s, name, x, y):
        mathfn(s.G, name, 'BooleanOR', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True)], x, y); return (name, 'ReturnValue')
    def pass_i(s, name, x, y):
        mathfn(s.G, name, 'Conv_IntToDouble', [it('InInt', default='0'), D('ReturnValue', out=True)], x, y); return (name, 'ReturnValue')
    def pass_d(s, name, src, x, y):
        mathfn(s.G, name, 'Multiply_DoubleDouble', [D('A', default='0.0'), D('B', default='1.0'), D('ReturnValue', out=True)], x, y)
        s.wire(src, name, 'A'); return (name, 'ReturnValue')

DBL, BOOL, INT, STRV = D('v', default='0.0'), bo('v', default='false'), it('v', default='0'), S('v', default='')

# =====================================================================================================================
# #68: Vesna prompt fade. State: PromptVesnaEnv (0..1), PromptVesnaShown (real time it appeared), PromptVesnaVis
# (last frame's visible), PromptLastT (last real time). Real time, so the fade doesn't freeze while paused.
#   Env   = clamp(Env + (Visible ? dt : -dt) / 0.25, 0, 1)
#   Alpha = smoothstep(Env) * (0.875 + 0.125 * sin(2 pi 0.6 (now - Shown)))
# Sockets: VesnaVisIn.A (old condition), FadeIn / FadeOut (exec), VesnaDraw (new Branch condition),
#          VesnaAlpha (-> CX_450.B), VesnaPressIn.A + VesnaPressOK (E only while really visible)
# =====================================================================================================================
G = Graph(); b = B(G, 'p')
fin = b.entry('FadeIn', 0, 0)
vis = b.pass_b('VesnaVisIn', 0, 300)
now = b.realnow(0, 450)
dt = b.clamp(b.d2('Subtract_DoubleDouble', now, b.get('PromptLastT', DBL, 0, 600), 250, 550), None, None, 450, 550, dhi='0.1')
step = b.sel(dt, b.d2('Multiply_DoubleDouble', dt, None, 650, 650, db='-1.0'), vis, 850, 550)
env = b.sat(b.d2('Add_DoubleDouble', b.get('PromptVesnaEnv', DBL, 850, 400), b.d2('Multiply_DoubleDouble', step, None, 1050, 550, db='4.0'), 1250, 450), 1450, 450)
rising = b.b2('BooleanAND', vis, b.bnot(b.get('PromptVesnaVis', BOOL, 850, 800), 1050, 800), 1250, 750)
shown = b.sel(now, b.get('PromptVesnaShown', DBL, 1250, 950), rising, 1450, 800)
s1 = b.set('PromptVesnaEnv', DBL, env, 300, 0)
s2 = b.set('PromptVesnaShown', DBL, shown, 550, 0)
s3 = b.set('PromptVesnaVis', BOOL, vis, 800, 0)
s4 = b.set('PromptLastT', DBL, now, 1050, 0)
fout = b.entry('FadeOut', 1300, 0)
b.chain(fin, s1, s2, s3, s4, 'FadeOut')
# draw-time values, read back from the variables just set
e2 = b.get('PromptVesnaEnv', DBL, 1600, 300)
draw = b.dc('Greater_DoubleDouble', e2, None, 1800, 250, db='0.001')
mathfn(G, 'VesnaDraw', 'BooleanOR', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True)], 2000, 250)
G.link(draw[0], draw[1], 'VesnaDraw', 'A')
ease = b.d2('Multiply_DoubleDouble', b.d2('Multiply_DoubleDouble', e2, e2, 1800, 400),
            b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', e2, None, 1800, 550, db='2.0'), 2000, 550, da='3.0'), 2200, 450)
ph = b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', b.realnow(1800, 700), b.get('PromptVesnaShown', DBL, 1800, 850), 2000, 750), None, 2200, 750, db='3.7699112')
pulse = b.d2('Add_DoubleDouble', None, b.d2('Multiply_DoubleDouble', b.m('Sin', [(D('A', default='0.0'), ph)], D('ReturnValue', out=True), 2400, 750), None, 2600, 750, db='0.125'), 2800, 700, da='0.875')
alpha = b.pass_d('VesnaAlpha', b.d2('Multiply_DoubleDouble', ease, pulse, 3000, 550), 3200, 550)
pin_ = b.pass_b('VesnaPressIn', 1800, 1050)
mathfn(G, 'VesnaPressOK', 'BooleanAND', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True)], 2100, 1050)
G.link(pin_[0], pin_[1], 'VesnaPressOK', 'A'); G.link(vis[0], vis[1], 'VesnaPressOK', 'B')
open(os.path.join(HERE, 'ZombieHUD_VesnaFade_graph.txt'), 'w', newline='\r\n').write(G.render())
print('Vesna fade: nodes', len(G.nodes), 'links', len(G.links))

# =====================================================================================================================
# #31: notice banner in BP_NoticeHUD. Queue = one string, one line per message: "<tier>|<text>^" (no arrays needed; a message can't contain ^).
#   PushNotice(Text, Tier): drop it if it's already queued; if it's the one showing, restart its hold. Important (1)
#   goes to the front, normal (0) to the back.
#   Draw (appended to the end of BP_NoticeHUD's DrawHUD, sockets NoticeIn, NoticeSizeX/Y):
#     start the next message when idle (0.15 s gap), then Roll/Fade/text alpha by the timing table in DESIGN.md.
#     Hidden and its clock paused while the game is paused (skill tree, trade and map all pause it).
# =====================================================================================================================
G = Graph(); b = B(G, 'n')
# ---- PushNotice ----
b.event('PushNotice', [S('Text'), it('Tier')], 0, 0)
txt, tier = ('PushNotice', 'Text'), ('PushNotice', 'Tier')
cat = lambda a, c, x, y, da=None, dc=None: b.sm('Concat_StrStr', [(S('A', default=da), a), (S('B', default=dc), c)], S('ReturnValue', out=True), x, y)
tstr = b.sm('Conv_IntToString', [(it('InInt', default='0'), tier)], S('ReturnValue', out=True), 0, 250)
item = cat(cat(cat(tstr, None, 200, 250, dc='|'), txt, 400, 250), None, 600, 250, dc='^')
q = b.get('NoticeQ', STRV, 400, 450)
key = cat(cat(None, txt, 200, 450, da='|'), None, 400, 600, dc='^')
queued = b.sm('Contains', [(S('SearchIn'), q), (S('Substring'), key), (bo('bUseCase', default='true'), None), (bo('bSearchFromEnd', default='false'), None)],
             bo('ReturnValue', out=True), 650, 450)
showing = b.b2('BooleanAND', b.get('NoticeOn', BOOL, 650, 650),
               b.sm('EqualEqual_StrStr', [(S('A'), b.get('NoticeCur', STRV, 650, 800)), (S('B'), txt)], bo('ReturnValue', out=True), 850, 750), 1050, 650)
dup = b.b2('BooleanOR', queued, showing, 1250, 550)
ifd = b.br(dup, 300, 0)
G.link('PushNotice', 'then', ifd, 'execute')
# duplicate: if it's showing, T0 = now - 0.5 (back to fully open, hold restarts)
t0 = b.sel(b.d2('Subtract_DoubleDouble', b.realnow(1300, 900), None, 1500, 900, db='0.5'), b.get('NoticeT0', DBL, 1500, 1050), showing, 1700, 900)
s = b.set('NoticeT0', DBL, t0, 600, -200); G.link(ifd, 'then', s, 'execute')
# new: important to the front, normal to the back
imp = b.m('EqualEqual_IntInt', [(it('A', default='0'), tier), (it('B', default='1'), None)], bo('ReturnValue', out=True), 1300, 1150)
front = cat(item, q, 1500, 1200); back = cat(q, item, 1500, 1350)
nq = b.m('SelectString', [(S('A'), front), (S('B'), back), (bo('bPickA', default='false'), imp)], S('ReturnValue', out=True), 1700, 1250)
s = b.set('NoticeQ', STRV, nq, 600, 200); G.link(ifd, 'else', s, 'execute')

# ---- draw ----
Y = 2000
nin = b.entry('NoticeIn', 0, Y)
sx = b.pass_i('NoticeSizeX', 0, Y + 300); sy = b.pass_i('NoticeSizeY', 0, Y + 450)
now = b.realnow(0, Y + 600)
paused = b.lib(GS, 'IsGamePaused', [(WC(), None)], [bo('ReturnValue', out=True)], 0, Y + 750, 'Paused'); paused = (paused, 'ReturnValue')
dt = b.clamp(b.d2('Subtract_DoubleDouble', now, b.get('NoticeLastT', DBL, 200, Y + 900), 400, Y + 850), None, None, 600, Y + 850, dhi='0.1')
on = b.get('NoticeOn', BOOL, 200, Y + 1050)
# 1. paused: push T0 forward by dt (the clock stops), 2. remember now
t0g = b.get('NoticeT0', DBL, 600, Y + 1000)
t0p = b.sel(b.d2('Add_DoubleDouble', t0g, dt, 800, Y + 950), t0g, b.b2('BooleanAND', paused, on, 800, Y + 1100), 1000, Y + 1000)
s_t0p = b.set('NoticeT0', DBL, t0p, 300, Y)
s_last = b.set('NoticeLastT', DBL, now, 550, Y)
b.chain(nin, s_t0p, s_last)
# 3. start the next message
q = b.get('NoticeQ', STRV, 800, Y + 1300)
has = b.m('Greater_IntInt', [(it('A', default='0'), b.sm('Len', [(S('S'), q)], it('ReturnValue', out=True), 1000, Y + 1300)), (it('B', default='0'), None)], bo('ReturnValue', out=True), 1200, Y + 1300)
ready = b.dc('GreaterEqual_DoubleDouble', now, b.get('NoticeNext', DBL, 1000, Y + 1450), 1200, Y + 1450)
cond = b.b2('BooleanAND', b.b2('BooleanAND', b.bnot(on, 1200, Y + 1150), has, 1400, Y + 1200), b.b2('BooleanAND', ready, b.bnot(paused, 1200, Y + 1600), 1400, Y + 1500), 1600, Y + 1300)
ifs = b.br(cond, 800, Y); G.link(s_last, 'then', ifs, 'execute')
sp = b.name('Split')
callfn(G, sp, STR, 'Split', [S('SourceString'), S('InStr', default='^'), S('LeftS', out=True), S('RightS', out=True),
       E('SearchCase', '/Script/CoreUObject.ESearchCase', 'IgnoreCase'), E('SearchDir', '/Script/CoreUObject.ESearchDir', 'FromStart'), bo('ReturnValue', out=True)],
       pure=True, x=1000, y=Y + 1700, self_hidden=True)
G.link(q[0], q[1], sp, 'SourceString')
cur = b.sm('RightChop', [(S('SourceString'), (sp, 'LeftS')), (it('Count', default='2'), None)], S('ReturnValue', out=True), 1300, Y + 1700)
istier = b.sm('EqualEqual_StrStr', [(S('A'), b.sm('Left', [(S('SourceString'), (sp, 'LeftS')), (it('Count', default='1'), None)], S('ReturnValue', out=True), 1300, Y + 1850)), (S('B', default='1'), None)],
             bo('ReturnValue', out=True), 1500, Y + 1850)
extra = b.d2('Multiply_DoubleDouble', b.m('FMax', [(D('A', default='0.0'), b.d2('Subtract_DoubleDouble', b.i2d(b.sm('Len', [(S('S'), cur)], it('ReturnValue', out=True), 1500, Y + 2000), 1700, Y + 2000), None, 1900, Y + 2000, db='60.0')), (D('B', default='0.0'), None)], D('ReturnValue', out=True), 2100, Y + 2000), None, 2300, Y + 2000, db='0.04')
hold = b.d2('Add_DoubleDouble', b.sel(None, None, istier, 1900, Y + 1850, da='7.0', db='4.0'), extra, 2500, Y + 1900)
c1 = b.set('NoticeCur', STRV, cur, 1100, Y)
c2 = b.set('NoticeTier', DBL, b.b2d(istier, 1700, Y + 1700), 1350, Y)
c3 = b.set('NoticeQ', STRV, (sp, 'RightS'), 1600, Y)
c4 = b.set('NoticeT0', DBL, now, 1850, Y)
c5 = b.set('NoticeHold', DBL, hold, 2100, Y)
c6 = b.set('NoticeOn', BOOL, None, 2350, Y)
b.chain((ifs, 'then'), c1, c2, c3, c4, c5, c6)
# NoticeOn = true on start
for ln in G.nodes:
    if ln[0] == c6:
        for p in ln[3]:
            if p['name'] == 'NoticeOn': p['default'] = 'true'
# 4. make the banner material instance once
mid = b.get('NoticeMID', ob('v', MIDC), 2600, Y + 300)
valid = b.lib(CLS('KismetSystemLibrary'), 'IsValid', [(ob('Object', OBJ), mid)], [bo('ReturnValue', out=True)], 2800, Y + 300, 'Valid')
ifm = b.br(b.bnot((valid, 'ReturnValue'), 3000, Y + 300), 2650, Y)
G.link(ifs, 'else', ifm, 'execute'); G.link(c6, 'then', ifm, 'execute')
mk = b.name('MakeMID')
callfn(G, mk, CLS('KismetMaterialLibrary'), 'CreateDynamicMaterialInstance', [WC(), dict(ob('Parent', CLS('MaterialInterface')), dobj=BANNER),
       {'name': 'OptionalName', 'cat': 'name', 'default': 'None'}, E('CreationFlags', '/Script/Engine.EMIDCreationFlags', 'None'), ob('ReturnValue', MIDC, out=True)],
       x=2900, y=Y - 200, self_hidden=True)
G.link(ifm, 'then', mk, 'execute')
smid = b.set('NoticeMID', ob('v', MIDC), (mk, 'ReturnValue'), 3200, Y - 200); G.link(mk, 'then', smid, 'execute')
# 5. draw while on and not paused
ifd = b.br(b.b2('BooleanAND', b.get('NoticeOn', BOOL, 3300, Y + 300), b.bnot(paused, 3300, Y + 450), 3500, Y + 350), 3500, Y)
G.link(ifm, 'else', ifd, 'execute'); G.link(smid, 'then', ifd, 'execute')
X = 3700
t = b.d2('Subtract_DoubleDouble', now, b.get('NoticeT0', DBL, X, Y + 600), X + 200, Y + 600)
hold = b.get('NoticeHold', DBL, X, Y + 750)
endh = b.d2('Add_DoubleDouble', hold, None, X + 200, Y + 750, db='0.35')                       # hold ends
rin = b.sat(b.d2('Divide_DoubleDouble', t, None, X + 400, Y + 600, db='0.35'), X + 600, Y + 600)
one_m = b.d2('Subtract_DoubleDouble', None, rin, X + 800, Y + 600, da='1.0')
ro = b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', one_m, one_m, X + 1000, Y + 600), X + 1200, Y + 600, da='1.0')   # ease-out
rout = b.sat(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', t, b.d2('Add_DoubleDouble', endh, None, X + 400, Y + 800, db='0.15'), X + 600, Y + 800), None, X + 800, Y + 800, db='0.30'), X + 1000, Y + 800)
roll = b.d2('Multiply_DoubleDouble', ro, b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', rout, rout, X + 1200, Y + 800), X + 1400, Y + 800, da='1.0'), X + 1600, Y + 700)
endall = b.d2('Add_DoubleDouble', endh, None, X + 400, Y + 950, db='0.55')
fade = b.d2('Multiply_DoubleDouble', b.sat(b.d2('Divide_DoubleDouble', t, None, X + 400, Y + 1100, db='0.1'), X + 600, Y + 1100),
            b.sat(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', endall, t, X + 600, Y + 950), None, X + 800, Y + 950, db='0.1'), X + 1000, Y + 950), X + 1200, Y + 1050)
ta = b.d2('Multiply_DoubleDouble', b.sat(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', t, None, X + 400, Y + 1250, db='0.25'), None, X + 600, Y + 1250, db='0.15'), X + 800, Y + 1250),
          b.sat(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', b.d2('Add_DoubleDouble', endh, None, X + 400, Y + 1400, db='0.15'), t, X + 600, Y + 1400), None, X + 800, Y + 1400, db='0.15'), X + 1000, Y + 1400), X + 1200, Y + 1300)
# layout: S = SizeY / 1080; text 24 px * S whatever the font's own size (measure "Ag" at scale 1)
sc = b.d2('Divide_DoubleDouble', sy, None, X, Y + 1600, db='1080.0')
_, agh = b.textsize(None, None, X, Y + 1750, dtext='Ag')
tscale = b.d2('Divide_DoubleDouble', b.d2('Multiply_DoubleDouble', sc, None, X + 200, Y + 1600, db='24.0'), agh, X + 400, Y + 1650)
cur = b.get('NoticeCur', STRV, X + 400, Y + 1850)
tw, th = b.textsize(cur, tscale, X + 600, Y + 1800)
w = b.clamp(b.d2('Add_DoubleDouble', tw, b.d2('Multiply_DoubleDouble', sc, None, X + 800, Y + 1950, db='112.0'), X + 1000, Y + 1850),
            b.d2('Multiply_DoubleDouble', sc, None, X + 1000, Y + 2000, db='420.0'), b.d2('Multiply_DoubleDouble', sc, None, X + 1000, Y + 2150, db='1100.0'), X + 1200, Y + 1900)
h = b.d2('Multiply_DoubleDouble', sc, None, X + 1200, Y + 2100, db='64.0')
bx = b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', sx, w, X + 1400, Y + 1900), None, X + 1600, Y + 1900, db='0.5')
by = b.d2('Multiply_DoubleDouble', sy, None, X + 1400, Y + 2100, db='0.11')
tier = b.get('NoticeTier', DBL, X + 1400, Y + 1500)
mid = b.get('NoticeMID', ob('v', MIDC), X + 1600, Y + 1200)
prev = ifd; first = True
for k, (pn, src) in enumerate((('Roll', roll), ('Aspect', b.d2('Divide_DoubleDouble', w, h, X + 1600, Y + 2000)), ('Fade', fade), ('Tier', tier))):
    n = b.name('MidSet')
    G.node(n, 'K2Node_CallFunction', ['FunctionReference=(MemberParent=%s,MemberName="SetScalarParameterValue")' % MIDC],
           [ex(), ex('then', True), selfpin(MIDC), {'name': 'ParameterName', 'cat': 'name', 'default': pn}, fl('Value', default='0.0')], X + 1800 + k * 250, Y)
    G.link(prev, 'then', n, 'execute') if not first else G.link(ifd, 'then', n, 'execute')
    G.link(mid[0], mid[1], n, 'self'); b.wire(src, n, 'Value'); prev = n; first = False
dm = b.hud('DrawMaterial', [ob('Material', CLS('MaterialInterface')), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'), fl('ScreenW', default='0.0'), fl('ScreenH', default='0.0'),
           fl('MaterialU', default='0.0'), fl('MaterialV', default='0.0'), fl('MaterialUWidth', default='1.0'), fl('MaterialVHeight', default='1.0'),
           fl('Scale', default='1.0'), bo('bScalePosition', default='false'), fl('Rotation', default='0.0'), st('RotPivot', STRUCT('Vector2D'), default='(X=0.500000,Y=0.500000)')], X + 2800, Y)
G.link(prev, 'then', dm, 'execute')
for p, src in (('Material', mid), ('ScreenX', bx), ('ScreenY', by), ('ScreenW', w), ('ScreenH', h)): b.wire(src, dm, p)
# text: centred, 1 px (x S) dark shadow, warm white / gold
tx = b.d2('Subtract_DoubleDouble', b.d2('Multiply_DoubleDouble', sx, None, X + 1800, Y + 2300, db='0.5'), b.d2('Multiply_DoubleDouble', tw, None, X + 1800, Y + 2450, db='0.5'), X + 2000, Y + 2350)
ty = b.d2('Subtract_DoubleDouble', b.d2('Add_DoubleDouble', by, b.d2('Multiply_DoubleDouble', h, None, X + 1800, Y + 2600, db='0.5'), X + 2000, Y + 2550), b.d2('Multiply_DoubleDouble', th, None, X + 2000, Y + 2700, db='0.5'), X + 2200, Y + 2600)
sh = b.d2('Add_DoubleDouble', tx, sc, X + 2400, Y + 2350); shy = b.d2('Add_DoubleDouble', ty, sc, X + 2400, Y + 2600)
shadow = b.color(None, None, None, b.d2('Multiply_DoubleDouble', ta, None, X + 2400, Y + 2800, db='0.8'), X + 2600, Y + 2700)
imp = b.dc('Greater_DoubleDouble', tier, None, X + 2400, Y + 2950, db='0.5')
main = b.color(b.sel(None, None, imp, X + 2600, Y + 2950, da='1.0', db='0.95'), b.sel(None, None, imp, X + 2600, Y + 3100, da='0.80', db='0.88'),
               b.sel(None, None, imp, X + 2600, Y + 3250, da='0.35', db='0.76'), ta, X + 2800, Y + 3000)
d1 = b.drawtext(cur, shadow, sh, shy, tscale, X + 3100, Y); G.link(dm, 'then', d1, 'execute')
d2 = b.drawtext(cur, main, tx, ty, tscale, X + 3350, Y); G.link(d1, 'then', d2, 'execute')
# 6. finished: off, next start after a 0.15 s gap
ife = b.br(b.dc('Greater_DoubleDouble', t, endall, X + 3400, Y + 300), X + 3600, Y)
G.link(d2, 'then', ife, 'execute')
off = b.set('NoticeOn', BOOL, None, X + 3850, Y); G.link(ife, 'then', off, 'execute')
nx = b.set('NoticeNext', DBL, b.d2('Add_DoubleDouble', now, None, X + 3850, Y + 300, db='0.15'), X + 4100, Y); G.link(off, 'then', nx, 'execute')
open(os.path.join(HERE, 'NoticeHUD_Banner_graph.txt'), 'w', newline='\r\n').write(G.render())
print('Notice banner: nodes', len(G.nodes), 'links', len(G.links))
