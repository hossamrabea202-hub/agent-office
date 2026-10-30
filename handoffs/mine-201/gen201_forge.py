# #201 part 2: BP_Forge (new Actor) - spends the metals from the approved RECIPES.md (v1: 6 keys).
#   Hero walks up to the forge -> the notice banner shows the menu and keys 1-6 are enabled.
#   1  Mint 60 gold      1 Cu + 1 Ag        4  Iron swords   2 Fe          -> HUD.ForgeSword = 1
#   2  Mint 150 gold     1 Au               5  Silver bolts  1 Ag + 1 Cu   -> HUD.ForgeBolt = 1
#   3  Gate bands (next level: 3 Fe / 2 Ag+2 Fe / 2 Au+1 Ag) -> HUD.ForgeGate 1..3
#                                           6  Steel plate   4 Fe + 1 Cu   -> HUD.ForgePlate = 1
#   The Forge* levels live on BP_ZombieHUD next to Gold/Ore; the gate HP / damage multipliers read them (follow-up manifests).
#   python gen201_forge.py -> BP_Forge_graph.txt
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
P_CASTLE = '/Game/CastleDefender/Gameplay/Castle/'
P_HUD, P_NOTICE = P_CASTLE + 'BP_ZombieHUD', P_CASTLE + 'BP_NoticeHUD'
P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
HUDC, NOTC, HEROC = BPC(P_HUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD'), BPC(P_HERO, 'BP_ThirdPersonCharacter')
HUDCLS, KEY = CLS('HUD'), '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
FE, CU, AG, AU, STAR = range(5)
MENU = 'FORGE   [1] Mint 60 gold: 1 Cu + 1 Ag   [2] Mint 150 gold: 1 Au   [3] Gate bands   [4] Iron swords: 2 Fe   [5] Silver bolts: 1 Ag + 1 Cu   [6] Steel plate: 4 Fe + 1 Cu'

G = Graph(); b = B(G, 'fg')


def event_override(nm, member, params, x, y):
    G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ACT, member), 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (ACT, member)}, ex('then', True)]
           + [dict(p, out=True) for p in params], x, y)
    return nm


def key(nm, k, x, y):
    G.node(nm, 'K2Node_InputKey', ['InputKey=%s' % k, 'bConsumeInput=True'], [ex('Pressed', True), ex('Released', True), st('Key', KEY, out=True)], x, y)
    return nm


def pc(x, y): return (b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')


def huds(x, y):
    """-> (zombie-hud cast node, notice-hud cast node); zcast.then -> ncast.execute; returns handles."""
    p = pc(x, y + 300)
    hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x + 250, y + 300, target=p, pure=True, const=True, tag='HUD')
    zc = b.name('AsZombieHUD'); cast(G, zc, HUDC, 'AsBP Zombie HUD', x + 500, y); b.wire((hud, 'ReturnValue'), zc, 'Object')
    nc = b.name('AsNoticeHUD'); cast(G, nc, NOTC, 'AsBP Notice HUD', x + 800, y); b.wire((hud, 'ReturnValue'), nc, 'Object')
    G.link(zc, 'then', nc, 'execute')
    return zc, (zc, 'AsBP Zombie HUD'), nc, (nc, 'AsBP Notice HUD')


def notice(text, nh, x, y):
    n = b.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x, y, target=nh, tag='Notice'); return n


def ore_item(zh, i, x, y):
    o = b.getm('Ore', HUDC, arr(INT), zh, x, y + 150)
    gi = b.name('Ore%d' % i); G.node(gi, 'K2Node_GetArrayItem', [], [arr(dict(INT, name='Array')), it('Dimension 1', default=str(i)), dict(INT, name='Output', out=True)], x + 250, y + 150)
    b.wire(o, gi, 'Array'); return (gi, 'Output')


def ore_set(zh, i, val, x, y):
    o = b.getm('Ore', HUDC, arr(INT), zh, x, y + 200)
    n = b.name('SetOre%d' % i)
    G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Set")' % KARR],
           [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
            it('Index', default=str(i)), {'name': 'Item', 'cat': 'wildcard', 'ref': True, 'default': '0'}, bo('bSizeToFit', default='false')], x, y)
    b.wire(o, n, 'TargetArray'); b.wire(val, n, 'Item'); return n


def buy(exec_from, cost, done_text, effect, x, y):
    """exec_from=(node,pin). cost={metal: n}. effect(zh, x, y) -> (first, last) exec nodes or None. Returns nothing (chain ends in a notice)."""
    zc, zh, nc, nh = huds(x, y); G.link(exec_from[0], exec_from[1], zc, 'execute')
    cond = None; cx = x + 1100
    for k, (m, n) in enumerate(cost.items()):
        ok = b.icmp('GreaterEqual_IntInt', ore_item(zh, m, cx, y + 300 + 350 * k), None, cx + 500, y + 300 + 350 * k, db=str(n))
        cond = ok if cond is None else b.b2('BooleanAND', cond, ok, cx + 750, y + 300 + 350 * k)
    br = b.branch(cond, cx + 1000, y, 'CanAfford'); G.link(nc, 'then', br, 'execute')
    no = notice('Not enough metal: ' + '  '.join('%d %s' % (n, ['Fe', 'Cu', 'Ag', 'Au', 'Star'][m]) for m, n in cost.items()), nh, cx + 1300, y + 200)
    G.link(br, 'else', no, 'execute')
    prev = (br, 'then'); sx = cx + 1300
    for m, n in cost.items():
        less = b.i2('Subtract_IntInt', ore_item(zh, m, sx, y + 250), None, sx + 500, y + 250, db=str(n))
        s = ore_set(zh, m, less, sx + 750, y); G.link(prev[0], prev[1], s, 'execute'); prev = (s, 'then'); sx += 1100
    if effect:
        f, l = effect(zh, sx, y); G.link(prev[0], prev[1], f, 'execute'); prev = (l, 'then'); sx += 900
    G.link(prev[0], prev[1], notice(done_text, nh, sx, y), 'execute')


def set_level(var, val):
    def eff(zh, x, y):
        n = b.setm(var, HUDC, it('v', default=str(val)), None, zh, x, y); return n, n
    return eff


def add_gold(amount):
    def eff(zh, x, y):
        g = b.getm('Gold', HUDC, INT, zh, x, y + 250)
        n = b.setm('Gold', HUDC, INT, b.i2('Add_IntInt', g, None, x + 300, y + 250, db=str(amount)), zh, x + 600, y); return n, n
    return eff


# ---- enter / leave the forge ----
ov = event_override('ForgeEnter', 'ReceiveActorBeginOverlap', [ob('OtherActor', ACT)], 0, 0)
cs = b.name('AsHero'); cast(G, cs, HEROC, 'AsBP Third Person Character', 300, 0); b.wire((ov, 'OtherActor'), cs, 'Object'); G.link(ov, 'then', cs, 'execute')
en = b.call_self('EnableInput', [ob('PlayerController', PCON)], 700, 0, ACT, tag='EnableInput'); b.wire(pc(450, 300), en, 'PlayerController'); G.link(cs, 'then', en, 'execute')
zc, zh, nc, nh = huds(1100, 0); G.link(en, 'then', zc, 'execute')
G.link(nc, 'then', notice(MENU, nh, 2300, 0), 'execute')
ov2 = event_override('ForgeLeave', 'ReceiveActorEndOverlap', [ob('OtherActor', ACT)], 0, 700)
cs2 = b.name('AsHero2'); cast(G, cs2, HEROC, 'AsBP Third Person Character', 300, 700); b.wire((ov2, 'OtherActor'), cs2, 'Object'); G.link(ov2, 'then', cs2, 'execute')
dis = b.call_self('DisableInput', [ob('PlayerController', PCON)], 700, 700, ACT, tag='DisableInput'); b.wire(pc(450, 1000), dis, 'PlayerController'); G.link(cs2, 'then', dis, 'execute')

# ---- the six keys ----
Y = 1500
buy((key('Key1', 'One', 0, Y), 'Pressed'), {CU: 1, AG: 1}, 'Minted 60 gold', add_gold(60), 300, Y); Y += 1500
buy((key('Key2', 'Two', 0, Y), 'Pressed'), {AU: 1}, 'Minted 150 gold', add_gold(150), 300, Y); Y += 1200
k3 = key('Key3', 'Three', 0, Y)
# gate: pick the recipe for the current level
zc3, zh3, nc3, nh3 = huds(300, Y); G.link(k3, 'Pressed', zc3, 'execute')
lv = b.getm('ForgeGate', HUDC, INT, zh3, 1100, Y + 400)
b0 = b.branch(b.icmp('EqualEqual_IntInt', lv, None, 1400, Y + 400, db='0'), 1700, Y, 'Lvl0'); G.link(nc3, 'then', b0, 'execute')
b1 = b.branch(b.icmp('EqualEqual_IntInt', lv, None, 1400, Y + 600, db='1'), 1700, Y + 250, 'Lvl1'); G.link(b0, 'else', b1, 'execute')
b2 = b.branch(b.icmp('EqualEqual_IntInt', lv, None, 1400, Y + 800, db='2'), 1700, Y + 500, 'Lvl2'); G.link(b1, 'else', b2, 'execute')
G.link(b2, 'else', notice('The gate is already gilded', nh3, 2000, Y + 750), 'execute')
buy((b0, 'then'), {FE: 3}, 'Gate: iron bands', set_level('ForgeGate', 1), 2100, Y); Y += 1500
buy((b1, 'then'), {AG: 2, FE: 2}, 'Gate: silver bands', set_level('ForgeGate', 2), 2100, Y); Y += 1500
buy((b2, 'then'), {AU: 2, AG: 1}, 'Gate: gilded', set_level('ForgeGate', 3), 2100, Y); Y += 1500
buy((key('Key4', 'Four', 0, Y), 'Pressed'), {FE: 2}, 'Iron swords: sword damage +20%', set_level('ForgeSword', 1), 300, Y); Y += 1200
buy((key('Key5', 'Five', 0, Y), 'Pressed'), {AG: 1, CU: 1}, 'Silver bolts: crossbow damage +25%, x2 vs risen', set_level('ForgeBolt', 1), 300, Y); Y += 1500
buy((key('Key6', 'Six', 0, Y), 'Pressed'), {FE: 4, CU: 1}, 'Steel plate: soldier HP +30%', set_level('ForgePlate', 1), 300, Y)
open(os.path.join(HERE, 'BP_Forge_graph.txt'), 'w', encoding='utf-8').write(G.render())
print('BP_Forge', len(G.nodes), 'nodes')
