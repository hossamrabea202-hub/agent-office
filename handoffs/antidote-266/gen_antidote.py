# #266 Antidote at Vesna (adjustedfilm, 2026-10-31): the missing step 5 of #148, so the infection can be cured.
#   python gen_antidote.py -> NoticeHUD_Antidote_graph.txt + manifest_noticehud_antidote.json
# One paste into BP_NoticeHUD (the top HUD, child of BP_ArmoryHUD, so it draws over Vesna's shop), chained between the
# live #148 infection block and the #31 banner: InfOut.then_0 -> AntIn ... AntOut.then_0 -> NoticeIn.
# While Vesna's shop is open (MPC_SkillTree Shop.R > 0.5 and the game paused) AND the hero is infected it draws an
# APOTHECARY panel under the shop's STATS box: antidote icon, "Antidote", "Cures the infection", price (FREE / n gold,
# red when you can't pay) and a BUY / TAKE button. Click: Gold -= Infection.AntidotePrice, then Infection.BuyAntidote()
# (live since #148: Infected = false, CuredAt = now, CURED notice, price goes up). Hover without the gold: "Not enough
# gold, hunter." No new variables, no self-calls (BuyAntidote is called on the component), casts are in the exec chain.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

HUDC, TEXC, FONTC = CLS('HUD'), CLS('Texture'), CLS('Font')
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC = '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree'
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
ICON = '/Game/CastleDefender/UI/T_Item_Antidote.T_Item_Antidote'
BLEND = '"/Script/CoreUObject.Enum\'/Script/Engine.EBlendMode\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
V2 = STRUCT('Vector2D')
INFC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Infection', 'BPC_Infection')
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
GOLD_REF = 'VariableReference=(MemberName="Gold",MemberGuid=053CEB09405150030911748F9697F7C4,bSelfContext=True)'  # as in the live NoticeHUD
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)


class A(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def selc(s, a, c, pick, x, y, da, db):
        return s.math('SelectColor', [(st('A', LC, default=da), a), (st('B', LC, default=db), c), (bo('bPickA', default='false'), pick)], st('ReturnValue', LC, out=True), x, y)
    def hud(s, member, pins, x, y, pure=False):
        n = s.name(member[:10])
        props = (['bIsPureFunc=True'] if pure else []) + ['FunctionReference=(MemberName="%s",bSelfContext=True)' % member]
        s.G.node(n, 'K2Node_CallFunction', props, ([] if pure else [ex(), ex('then', True)]) + [selfpin(HUDC, hidden=True)] + pins, x, y)
        return n
    def rect(s, c, X, Y, W, H, x, y, dc):
        n = s.hud('DrawRect', [st('RectColor', LC, default=dc), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], x, y)
        for p, v in (('RectColor', c), ('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n
    def text(s, txt, c, X, Y, scale, x, y, dtext='', dc=col(1, 1, 1)):
        n = s.hud('DrawText', [S('Text', default=dtext), st('TextColor', LC, default=dc), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT),
                               F('Scale', '1.0'), bo('bScalePosition', default='false')], x, y)
        for p, v in (('Text', txt), ('TextColor', c), ('ScreenX', X), ('ScreenY', Y), ('Scale', scale)): s.wire(v, n, p)
        return n
    def tex(s, path, X, Y, W, H, x, y):
        n = s.hud('DrawTexture', [dict(ob('Texture', TEXC), dobj=path), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('TextureU'), F('TextureV'),
                                  F('TextureUWidth', '1.0'), F('TextureVHeight', '1.0'), st('TintColor', LC, default=col(1, 1, 1)),
                                  {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': 'BLEND_Translucent'}, F('Scale', '1.0'),
                                  bo('bScalePosition', default='false'), F('Rotation', '0.0'), st('RotPivot', V2)], x, y)
        for p, v in (('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n


G = Graph(); b = A(G, 'an')
sequence(G, 'AntIn', 1, 0, 0)
sequence(G, 'AntOut', 1, 9000, 0)
mathfn(G, 'AntSizeX', 'Conv_IntToDouble', [it('InInt', default='0'), D('ReturnValue', out=True)], 0, 300)
mathfn(G, 'AntSizeY', 'Conv_IntToDouble', [it('InInt', default='0'), D('ReturnValue', out=True)], 0, 450)
sx, sy = ('AntSizeX', 'ReturnValue'), ('AntSizeY', 'ReturnValue')

# 1) Vesna's shop open? (same test as the WEAPONSMITH / OBSIDIAN ARMOURY panels)
gsh = b.lib(MATL, 'GetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), N('ParameterName', 'Shop'), st('ReturnValue', LC, out=True)], 250, 0, tag='GetShop')
G.link('AntIn', 'then_0', gsh, 'execute')
bk = b.name('BreakShop'); mathfn(G, bk, 'BreakColor', [st('InColor', LC)] + [fl(c, out=True, default='0.0') for c in 'RGBA'], 250, 250); G.link(gsh, 'ReturnValue', bk, 'InColor')
paused = b.lib(GS, 'IsGamePaused', [WC(), bo('ReturnValue', out=True, default='false')], 250, 400, pure=True, tag='Paused')
ifs = b.branch(b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', (bk, 'R'), None, 450, 300, db='0.5'), (paused, 'ReturnValue'), 650, 350), 600, 0, tag='IfShop')
G.link(gsh, 'then', ifs, 'execute'); G.link(ifs, 'else', 'AntOut', 'execute')

# 2) hero -> Infection, infected?
pch = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], 800, 300, pure=True, tag='Char')
cast(G, 'AntAsHero', HERO, 'AsBP Third Person Character', 900, 0); b.wire((pch, 'ReturnValue'), 'AntAsHero', 'Object')
G.link(ifs, 'then', 'AntAsHero', 'execute'); G.link('AntAsHero', 'CastFailed', 'AntOut', 'execute')
comp = b.getm('Infection', HERO, ob('v', INFC), ('AntAsHero', 'AsBP Third Person Character'), 1100, 300)
ifv = b.branch(b.valid(comp, 1300, 300), 1300, 0, tag='IfComp'); G.link('AntAsHero', 'then', ifv, 'execute'); G.link(ifv, 'else', 'AntOut', 'execute')
ifi = b.branch(b.getm('Infected', INFC, BOOL, comp, 1500, 300), 1550, 0, tag='IfInfected'); G.link(ifv, 'then', ifi, 'execute'); G.link(ifi, 'else', 'AntOut', 'execute')

# 3) layout: 1080p units x S (S = SizeY / 1080), panel 380 x 150, centred at SizeX x 0.44, top at 600 (under the STATS box)
X0 = 1800
S_ = b.d2('Divide_DoubleDouble', sy, None, X0, 600, db='1080.0')
u = lambda v, x, y: b.mul(S_, None, x, y, db=str(float(v)))
PX = b.sub(b.mul(sx, None, X0, 750, db='0.44'), u(190, X0, 900), X0 + 200, 800)
PY, PW, PH = u(600, X0, 1050), u(380, X0, 1150), u(150, X0, 1250)
at = lambda base, v, x, y: b.add(base, u(v, x - 200, y), x, y)
price = b.getm('AntidotePrice', INFC, INT, comp, X0, 1400)
gold = b.name('GetGold'); G.node(gold, 'K2Node_VariableGet', [GOLD_REF], [dict(INT, name='Gold', out=True), selfpin(HUDC, hidden=True)], X0, 1550); gold = (gold, 'Gold')
afford = b.icmp('GreaterEqual_IntInt', gold, price, X0 + 200, 1500)
free = b.icmp('EqualEqual_IntInt', price, None, X0 + 200, 1650, db='0')

bg = b.rect(None, PX, PY, PW, PH, X0 + 400, 0, col(0.02, 0.015, 0.01, 0.80)); G.link(ifi, 'then', bg, 'execute')
ln = b.rect(None, PX, PY, PW, u(2, X0 + 400, 1800), X0 + 700, 0, col(0.25, 0.85, 0.30, 0.90)); G.link(bg, 'then', ln, 'execute')   # infection green edge
ic = b.tex(ICON, at(PX, 10, X0 + 900, 1900), at(PY, 30, X0 + 900, 2000), u(110, X0 + 900, 2100), u(110, X0 + 900, 2200), X0 + 1000, 0)
G.link(ln, 'then', ic, 'execute')
cream = col(0.92, 0.86, 0.74)
t1 = b.text(None, None, at(PX, 14, X0 + 1300, 1900), at(PY, 6, X0 + 1300, 2000), u(0.30, X0 + 1300, 2100), X0 + 1300, 0, dtext='APOTHECARY', dc=col(1.0, 0.72, 0.28))
t2 = b.text(None, None, at(PX, 128, X0 + 1600, 1900), at(PY, 40, X0 + 1600, 2000), u(0.30, X0 + 1600, 2100), X0 + 1600, 0, dtext='Antidote', dc=cream)
t3 = b.text(None, None, at(PX, 128, X0 + 1900, 1900), at(PY, 72, X0 + 1900, 2000), u(0.21, X0 + 1900, 2100), X0 + 1900, 0, dtext='Cures the infection', dc=col(0.55, 0.90, 0.58))
istr = b.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], X0 + 2000, 2300, pure=True, tag='PriceStr'); b.wire(price, istr, 'InInt')
ptxt = b.selstr(None, b.concat((istr, 'ReturnValue'), None, X0 + 2200, 2300, db=' gold'), free, X0 + 2400, 2300, da='FREE')
pcol = b.selc(None, None, afford, X0 + 2400, 2450, cream, col(0.85, 0.32, 0.25))
t4 = b.text(ptxt, pcol, at(PX, 128, X0 + 2200, 1900), at(PY, 106, X0 + 2200, 2000), u(0.24, X0 + 2200, 2100), X0 + 2200, 0)
b.chain(ic, t1, t2, t3, t4)

# 4) button 92 x 34 at (270, 102); hover highlight; click buys
BX, BY, BW, BH = at(PX, 272, X0 + 2600, 1900), at(PY, 100, X0 + 2600, 2000), u(92, X0 + 2600, 2100), u(34, X0 + 2600, 2200)
pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], X0 + 2600, 2400, pure=True, tag='PC')
mp = b.call(PCON, 'GetMousePosition', [F('LocationX', out=True), F('LocationY', out=True), bo('ReturnValue', out=True, default='false')], X0 + 2800, 2400,
            target=(pc, 'ReturnValue'), pure=True, const=True, tag='Mouse')
clk = b.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default='LeftMouseButton'), bo('ReturnValue', out=True, default='false')], X0 + 2800, 2600,
             target=(pc, 'ReturnValue'), pure=True, const=True, tag='Click')
mx, my = (mp, 'LocationX'), (mp, 'LocationY')
hov = b.b2('BooleanAND',
           b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', mx, BX, X0 + 3000, 2400), b.dcmp('Less_DoubleDouble', mx, b.add(BX, BW, X0 + 2900, 2550), X0 + 3100, 2550), X0 + 3300, 2450),
           b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', my, BY, X0 + 3000, 2700), b.dcmp('Less_DoubleDouble', my, b.add(BY, BH, X0 + 2900, 2850), X0 + 3100, 2850), X0 + 3300, 2750),
           X0 + 3500, 2600)
bcol = b.selc(None, None, hov, X0 + 3500, 2800, col(0.35, 0.80, 0.38, 0.55), col(0.20, 0.45, 0.22, 0.45))
bt = b.rect(bcol, BX, BY, BW, BH, X0 + 2500, 0, col(0.2, 0.45, 0.22, 0.45)); G.link(t4, 'then', bt, 'execute')
blab = b.selstr(None, None, free, X0 + 3700, 2950, da='TAKE', db='BUY')
bl = b.text(blab, None, at(BX, 18, X0 + 2800, 3100), at(BY, 6, X0 + 2800, 3200), u(0.24, X0 + 2800, 3300), X0 + 2800, 0, dc=cream)
G.link(bt, 'then', bl, 'execute')
# not enough gold (hovering the button)
inm = b.branch(b.b2('BooleanAND', hov, b.bnot(afford, X0 + 3000, 3400), X0 + 3200, 3400), X0 + 3100, 0, tag='IfPoor'); G.link(bl, 'then', inm, 'execute')
nm = b.text(None, None, at(PX, 14, X0 + 3400, 3500), b.add(PY, u(158, X0 + 3200, 3600), X0 + 3400, 3600), u(0.24, X0 + 3400, 3700), X0 + 3400, 0,
            dtext='Not enough gold, hunter.', dc=col(0.85, 0.32, 0.25))
G.link(inm, 'then', nm, 'execute')
ick = b.branch(b.b2('BooleanAND', b.b2('BooleanAND', hov, (clk, 'ReturnValue'), X0 + 3600, 3800), afford, X0 + 3800, 3800), X0 + 3700, 0, tag='IfBuy')
G.link(nm, 'then', ick, 'execute'); G.link(inm, 'else', ick, 'execute'); G.link(ick, 'else', 'AntOut', 'execute')
sg = b.name('SetGold')
G.node(sg, 'K2Node_VariableSet', [GOLD_REF], [ex(), ex('then', True), dict(INT, name='Gold'), dict(INT, name='Output_Get', out=True), selfpin(HUDC, hidden=True)], X0 + 4000, 0)
b.wire(b.i2('Subtract_IntInt', gold, price, X0 + 3900, 300), sg, 'Gold'); G.link(ick, 'then', sg, 'execute')
buy = b.name('CallBuyAntidote')
G.node(buy, 'K2Node_CallFunction', ['FunctionReference=(MemberParent=%s,MemberName="BuyAntidote")' % INFC], [ex(), ex('then', True), selfpin(INFC)], X0 + 4300, 0)
b.wire(comp, buy, 'self'); G.link(sg, 'then', buy, 'execute'); G.link(buy, 'then', 'AntOut', 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
open(os.path.join(HERE, 'NoticeHUD_Antidote_graph.txt'), 'w', newline='\r\n').write(G.render())
print('NoticeHUD antidote', len(G.nodes), 'nodes', len(G.links), 'links')
json.dump({'blueprint': 'BP_NoticeHUD',
           '_apply': 'after #148 (InfIn..InfOut are live). Puts the antidote panel between the infection block and the #31 banner.',
           'pastes': ['NoticeHUD_Antidote_graph.txt'],
           'rewires': [{'from': 'InfOut.then_0', 'to': 'AntIn.execute', 'replace': True, 'note': 'was -> NoticeIn'},
                       {'from': 'AntOut.then_0', 'to': 'NoticeIn.execute'},
                       {'from': 'CX_1.SizeX', 'to': 'AntSizeX.InInt'}, {'from': 'CX_1.SizeY', 'to': 'AntSizeY.InInt'}]},
          open(os.path.join(HERE, 'manifest_noticehud_antidote.json'), 'w'), indent=1)
