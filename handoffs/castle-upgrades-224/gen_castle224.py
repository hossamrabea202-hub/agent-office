# #224 Castle upgrades v1 (adjustedfilm, 2026-10-31): walls + towers, paid with gold + mine ore (#201), saved.
# (The gate track already exists: the forge's gate bands #208, ForgeGate, up to +150 % gate life.)
#   "<blender python>" -I gen_castle224.py -> BPC_CastleUpgrades_graph.txt, BP_TowerBallista_graph.txt,
#        WallBreaker_Walls_graph.txt + manifest_wallbreaker.json, VARIABLES_BPVar.txt, VARIABLES.md
# BPC_CastleUpgrades (hero component "CastleUpgrades"): at the barracks NPC a notice offers the next level of each track;
#   J buys walls, K buys towers (gold + Ore[5] on BP_ZombieHUD: 0 Fe, 1 Cu, 2 Ag, 3 Au, 4 Star). Slot CastleSaveCastle.
#   Walls 1 "Reinforced masonry" 300 gold + 6 Fe; 2 "Iron-banded walls" 700 gold + 8 Fe + 3 Ag.
#   Towers 1 "Ballista nests" 400 gold + 6 Fe + 2 Cu; 2 "Fire ballistas" 900 gold + 6 Fe + 2 Au.
# Walls effect (WallBreaker manifest): the colossus's smash damage on a breach spot 500 / (1 + 0.75 Walls) -> the wall lasts
#   x1.75 / x2.5. Towers effect: every placed BP_TowerBallista shows and fires once Towers >= 1 (nearest zombie within 50 m,
#   a colossus first; 120 dmg / 4 s; level 2: 180 dmg / 2.5 s), the spear flies 0.35 s, coals glow with a flicker.
import math, os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP = CLS('ActorComponent')
P_CU = '/Game/CastleDefender/Gameplay/Castle/BPC_CastleUpgrades'
P_TB = '/Game/CastleDefender/Gameplay/Castle/BP_TowerBallista'
P_NPC = '/Game/CastleDefender/Gameplay/Castle/BP_NPC_Barracks'
P_ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
P_WB = '/Game/CastleDefender/Gameplay/Siege/BP_ZombieWallBreaker'
CUC, TBC, NPCC = BPC(P_CU, 'BPC_CastleUpgrades'), BPC(P_TB, 'BP_TowerBallista'), BPC(P_NPC, 'BP_NPC_Barracks')
ZHUDC, NOTC = BPC(P_ZHUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD')
SAVEC = BPC('/Game/CastleDefender/Gameplay/Save/BP_CastleSave', 'BP_CastleSave')
SAVEG, HUDCLS, SOUND, SMC, PLC = CLS('SaveGame'), CLS('HUD'), CLS('SoundBase'), CLS('StaticMeshComponent'), CLS('PointLightComponent')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
SLOT = 'CastleSaveCastle'
OBJV = lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
WALLS = [('Reinforced masonry', 300, {0: 6}), ('Iron-banded walls', 700, {0: 8, 2: 3})]
TOWERS = [('Ballista nests', 400, {0: 6, 1: 2}), ('Fire ballistas', 900, {0: 6, 3: 2})]
ORE = ['iron', 'copper', 'silver', 'gold ore', 'starmetal']


def cost_text(lv):
    name, gold, ores = lv
    return '%s: %d gold%s' % (name, gold, ''.join(', %d %s' % (n, ORE[i]) for i, n in sorted(ores.items())))


class B8(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def div(s, a, c, x, y, da='0.0', db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, da=da, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def sin(s, a, x, y): return s.math('Sin', [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
    def eqi(s, a, v, x, y): return s.icmp('EqualEqual_IntInt', a, None, x, y, db=str(v))
    def seli(s, a, c, pick, x, y, da='0', db='0'):
        return s.math('SelectInt', [(it('A', default=da), a), (it('B', default=db), c), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)
    def item(s, arrsrc, pin, idx, x, y, didx='0'):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default=didx), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def aset(s, arrsrc, idx, val, x, y, didx='0'):
        n = s.name('SetOre')
        s.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Set")' % KARR],
                 [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
                  it('Index', default=didx), {'name': 'Item', 'cat': 'wildcard', 'ref': True, 'default': '0'}, bo('bSizeToFit', default='false')], x, y)
        s.wire(arrsrc, n, 'TargetArray'); s.wire(idx, n, 'Index'); s.wire(val, n, 'Item'); return n
    def actor_of_(s, path, cls, x, y):
        return s.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], x, y, tag='Find' + path.split('/')[-1][3:])
    def getall(s, path, cls, x, y):
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
    def dist2d(s, a, c, x, y): return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hud_cast(s, cls, label, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x - 150, y + 300, target=s.pc(x - 350, y + 300), pure=True, const=True, tag='HUD')
        nc = s.name('As' + label.replace(' ', '')); cast(s.G, nc, cls, 'As' + label, x, y); s.wire((hud, 'ReturnValue'), nc, 'Object'); return nc, (nc, 'As' + label)
    def notice(s, text, x, y, text_src=None):
        nc, nh = s.hud_cast(NOTC, 'BP Notice HUD', x, y)
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x + 300, y, target=nh, tag='Notice')
        s.wire(text_src, pn, 'Text'); s.G.link(nc, 'then', pn, 'execute'); return nc, pn
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def upgrades_of_player(s, x, y):
        """GetPlayerPawn -> GetComponentByClass(BPC_CastleUpgrades) -> handle (may be invalid)."""
        pp = s.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], x, y, pure=True, tag='Hero')
        n = s.call(ACT, 'GetComponentByClass', [{'name': 'ComponentClass', 'cat': 'class', 'obj': CLS('ActorComponent'), 'dobj': cpath(P_CU)}, ob('ReturnValue', CUC, out=True)],
                   x + 200, y, target=(pp, 'ReturnValue'), pure=True, const=True, tag='FindUpgrades')
        return (n, 'ReturnValue')


def event_override(G, nm, parent, member, params, x, y):
    G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (parent, member), 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (parent, member)}, ex('then', True)]
           + [dict(p, out=True) for p in params], x, y)
    return nm


def write(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    if bad: raise SystemExit('%s bad links: %s' % (name, bad[:10]))
    names = [n[0] for n in G.nodes]; dup = {n for n in names if names.count(n) > 1}
    if dup: raise SystemExit('%s duplicate names: %s' % (name, sorted(dup)[:10]))
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (name, len(G.nodes), len(G.links)))


# ================================================================================================= BPC_CastleUpgrades
G = Graph(); b = B8(G, 'cu')
g = b.get
event_override(G, 'BP', COMP, 'ReceiveBeginPlay', [], 0, 0)
hs = b.lib(GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 200, 300, pure=True, tag='HasSave')
bl = b.branch((hs, 'ReturnValue'), 300, 0, tag='IfSave'); G.link('BP', 'then', bl, 'execute')
ld = b.lib(GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', SAVEG, out=True)], 600, -200, tag='Load'); G.link(bl, 'then', ld, 'execute')
cast(G, 'cuAsLoad', SAVEC, 'AsBP Castle Save', 900, -200); b.wire((ld, 'ReturnValue'), 'cuAsLoad', 'Object'); G.link(ld, 'then', 'cuAsLoad', 'execute')
dat = b.getm('Data', SAVEC, arr(D('Data')), ('cuAsLoad', 'AsBP Castle Save'), 1100, 100)
dl = 'cuDataLen'
G.node(dl, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 1300, 250)
b.wire(dat, dl, 'TargetArray')
bd = b.branch(b.icmp('Greater_IntInt', (dl, 'ReturnValue'), None, 1500, 250, db='1'), 1200, -200, tag='IfData'); G.link('cuAsLoad', 'then', bd, 'execute')
rnd = lambda src, x, y: b.math('Round', [(D('A', default='0.0'), src)], it('ReturnValue', out=True), x, y)
s1 = b.set('Walls', INT, rnd(b.item(dat, D('v'), None, 1500, 400), 1700, 400), 1500, -200)
s2 = b.set('Towers', INT, rnd(b.item(dat, D('v'), None, 1700, 550, didx='1'), 1900, 550), 1750, -200)
G.link(bd, 'then', s1, 'execute'); G.link(s1, 'then', s2, 'execute')
mg = b.seq('AfterLoad', 1, 2000, 0)
for src, pin in ((bl, 'else'), ('cuAsLoad', 'CastFailed'), (bd, 'else'), (s2, 'then')): G.link(src, pin, mg, 'execute')
t1 = b.timer_ev('UpgPoll', '1.0', 2300, 0); G.link(mg, 'then_0', t1, 'execute')
t2 = b.timer_ev('UpgKeys', '0.05', 2600, 0); G.link(t1, 'then', t2, 'execute')

# ---- SaveNow
Y = 900
b.event('SaveNow', [], 0, Y)
cs = b.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SAVEG, '/Game/CastleDefender/Gameplay/Save/BP_CastleSave.BP_CastleSave_C'), ob('ReturnValue', SAVEG, out=True)], 300, Y, tag='NewSave')
G.link('SaveNow', 'then', cs, 'execute')
cast(G, 'cuAsSave', SAVEC, 'AsBP Castle Save', 600, Y); b.wire((cs, 'ReturnValue'), 'cuAsSave', 'Object'); G.link(cs, 'then', 'cuAsSave', 'execute')
mk = b.name('MakeData'); G.node(mk, 'K2Node_MakeArray', ['NumInputs=2'], [D('[0]', default='0.0'), D('[1]', default='0.0'), arr(D('Array', out=True))], 800, Y + 300)
b.wire(b.i2d(g('Walls', INT, 500, Y + 400), 650, Y + 400), mk, '[0]'); b.wire(b.i2d(g('Towers', INT, 500, Y + 500), 650, Y + 500), mk, '[1]')
sd = b.setm('Data', SAVEC, arr(D('Data')), (mk, 'Array'), ('cuAsSave', 'AsBP Castle Save'), 1000, Y); G.link('cuAsSave', 'then', sd, 'execute')
sv = b.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SAVEG), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 1300, Y, tag='Save')
b.wire(('cuAsSave', 'AsBP Castle Save'), sv, 'SaveGameObject'); G.link(sd, 'then', sv, 'execute')


def offer(track, levels, x, y):
    """string: the next level of a track (or 'best' when maxed)."""
    lv = g(track, INT, x, y)
    return b.selstr(None, b.selstr(None, None, b.eqi(lv, 1, x + 200, y + 100), x + 400, y + 50, da=cost_text(levels[1]), db='at their best'),
                    b.eqi(lv, 0, x + 200, y), x + 600, y, da=cost_text(levels[0]))


# ---- UpgPoll (1 s): the barracks offer
Y = 1700
b.event('UpgPoll', [], 0, Y)
fn = b.actor_of_(P_NPC, NPCC, 300, Y); G.link('UpgPoll', 'then', fn, 'execute')
npc = (fn, 'ReturnValue')
near = b.b2('BooleanAND', b.valid(npc, 500, Y + 300),
            b.dcmp('Less_DoubleDouble', b.dist2d(b.loc(b.owner(500, Y + 450), 700, Y + 450), b.loc(npc, 700, Y + 550), 900, Y + 500), None, 1100, Y + 500, db='450.0'), 1300, Y + 400)
bf = b.branch(b.b2('BooleanAND', near, b.bnot(g('NearShop', BOOL, 1300, Y + 550), 1500, Y + 550), 1700, Y + 500), 600, Y, tag='IfOffer')
G.link(fn, 'then', bf, 'execute')
txt = b.concat(b.concat(b.concat(None, offer('Walls', WALLS, 900, Y - 700), 1600, Y - 650, da='Castle works -  [J] Walls: '), None, 1800, Y - 650, db='     [K] Towers: '),
               offer('Towers', TOWERS, 1500, Y - 400), 2000, Y - 550)
nc, pn = b.notice('', 900, Y - 200, text_src=txt); G.link(bf, 'then', nc, 'execute')
sns = b.set('NearShop', BOOL, near, 1400, Y)
for src, pin in ((bf, 'else'), (pn, 'then'), (nc, 'CastFailed')): G.link(src, pin, sns, 'execute')

# ---- UpgKeys (0.05 s): J walls, K towers
Y = 3000
b.event('UpgKeys', [], 0, Y)
seq = b.seq('KeySeq', 2, 200, Y); G.link('UpgKeys', 'then', seq, 'execute')
X = 500
for track, key, levels, out_i in (('Walls', 'J', WALLS, 0), ('Towers', 'K', TOWERS, 1)):
    YY = Y + out_i * 2600
    down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default=key), bo('ReturnValue', out=True, default='false')], X, YY + 300, target=b.pc(X - 200, YY + 300), pure=True, const=True, tag='Key' + key)
    was = key + 'Was'
    press = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g(was, BOOL, X, YY + 450), X + 200, YY + 450), X + 400, YY + 400),
                 g('NearShop', BOOL, X + 400, YY + 550), X + 600, YY + 450)
    sw = b.set(was, BOOL, (down, 'ReturnValue'), X + 100, YY); G.link(seq, 'then_%d' % out_i, sw, 'execute')
    bp_ = b.branch(press, X + 400, YY, tag='If' + key); G.link(sw, 'then', bp_, 'execute')
    lv = lambda x, y, t=track: g(t, INT, x, y)
    bmax = b.branch(b.icmp('GreaterEqual_IntInt', lv(X + 600, YY + 300), None, X + 800, YY + 300, db='2'), X + 700, YY, tag='IfMax' + track)
    G.link(bp_, 'then', bmax, 'execute')
    nmx, _ = b.notice('Your %s are already at their best.' % track.lower(), X + 1000, YY - 300); G.link(bmax, 'then', nmx, 'execute')
    zc, zh = b.hud_cast(ZHUDC, 'BP Zombie HUD', X + 1000, YY); G.link(bmax, 'else', zc, 'execute')
    l0 = b.eqi(lv(X + 1100, YY + 500), 0, X + 1300, YY + 500)
    gold_cost = b.seli(None, None, l0, X + 1500, YY + 500, da=str(levels[0][1]), db=str(levels[1][1]))
    ore_ids = sorted(set(levels[0][2]) | set(levels[1][2]))
    costs = {i: b.seli(None, None, l0, X + 1500, YY + 600 + 100 * k, da=str(levels[0][2].get(i, 0)), db=str(levels[1][2].get(i, 0))) for k, i in enumerate(ore_ids)}
    goldv = lambda x, y: b.getm('Gold', ZHUDC, INT, zh, x, y)
    orea = lambda x, y: b.getm('Ore', ZHUDC, arr(INT), zh, x, y)
    conds = [b.icmp('GreaterEqual_IntInt', goldv(X + 1700, YY + 400), gold_cost, X + 1900, YY + 450)]
    for k, i in enumerate(ore_ids):
        conds.append(b.icmp('GreaterEqual_IntInt', b.item(orea(X + 1700, YY + 600 + 100 * k), INT, None, X + 1900, YY + 600 + 100 * k, didx=str(i)), costs[i], X + 2100, YY + 600 + 100 * k))
    can = conds[0]
    for k, c_ in enumerate(conds[1:]): can = b.b2('BooleanAND', can, c_, X + 2300 + 150 * k, YY + 500)
    bc = b.branch(can, X + 1300, YY, tag='IfAfford' + track); G.link(zc, 'then', bc, 'execute')
    nno, _ = b.notice('', X + 1600, YY + 1100, text_src=b.concat(None, offer(track, levels, X + 1300, YY + 1300), X + 2100, YY + 1300, da='Not enough: %s needs ' % track.lower()))
    G.link(bc, 'else', nno, 'execute')
    pay = b.setm('Gold', ZHUDC, INT, b.i2('Subtract_IntInt', goldv(X + 1600, YY - 100), gold_cost, X + 1800, YY - 100), zh, X + 1600, YY - 300)
    G.link(bc, 'then', pay, 'execute'); last = pay; XX = X + 1900
    for k, i in enumerate(ore_ids):
        nv = b.i2('Subtract_IntInt', b.item(orea(XX, YY - 600), INT, None, XX + 150, YY - 600, didx=str(i)), costs[i], XX + 300, YY - 550)
        so = b.aset(orea(XX, YY - 450), None, nv, XX + 100, YY - 300, didx=str(i)); G.link(last, 'then', so, 'execute'); last = so; XX += 400
    up = b.set(track, INT, b.i2('Add_IntInt', lv(XX, YY - 600), None, XX + 150, YY - 550, db='1'), XX, YY - 300); G.link(last, 'then', up, 'execute')
    svc = b.call_self('SaveNow', [], XX + 300, YY - 300, COMP, tag='CallSave' + track); G.link(up, 'then', svc, 'execute')
    msg = b.selstr(None, None, b.eqi(lv(XX + 400, YY - 500), 1, XX + 600, YY - 500), XX + 800, YY - 500,
                   da='%s built: %s.' % (track, levels[0][0]), db='%s built: %s.' % (track, levels[1][0]))
    nok, _ = b.notice('', XX + 700, YY - 300, text_src=msg); G.link(svc, 'then', nok, 'execute')
write(G, 'BPC_CastleUpgrades_graph.txt')
VARS_C = [('Walls', 'int', '0', 'walls level 0..2'), ('Towers', 'int', '0', 'towers level 0..2'), ('NearShop', 'bool', 'false', 'hero at the barracks (offer shown)'),
          ('JWas', 'bool', 'false', 'J held last check'), ('KWas', 'bool', 'false', 'K held last check')]

# ================================================================================================= BP_TowerBallista
G = Graph(); b = B8(G, 'tb')
g = b.get
event_override(G, 'BP', ACT, 'ReceiveBeginPlay', [], 0, 0)
def tagged(cls, tag, x, y):
    n = b.call_self('GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.' + cls.split('.')[-1].strip('\'"')), NAME_('Tag', tag),
                    arr(ob('ReturnValue', cls, out=True))], x, y, ACT, pure=True, const=True, tag='Find' + tag)
    return b.item((n, 'ReturnValue'), ob('v', cls), None, x + 250, y)
sf = b.set('Frame', OBJV(SCENE), tagged(SCENE, 'BallistaFrame', 200, 300), 300, 0)
ssp = b.set('Spear', OBJV(SCENE), tagged(SCENE, 'BallistaSpear', 500, 450), 600, 0)
sco = b.set('Coals', OBJV(PLC), tagged(PLC, 'BallistaCoals', 800, 600), 900, 0)
tm = b.timer_ev('Think', '0.05', 1200, 0)
G.link('BP', 'then', sf, 'execute'); b.chain(sf, ssp, sco, tm)

Y = 900
b.event('Think', [], 0, Y)
now = b.now(200, Y + 2400)
up = b.upgrades_of_player(200, Y + 300)
lvl = b.seli(b.getm('Towers', CUC, INT, up, 600, Y + 300), None, b.valid(up, 600, Y + 450), 800, Y + 350, db='0')
active = b.icmp('GreaterEqual_IntInt', lvl, None, 1000, Y + 350, db='1')
hide = b.call_self('SetActorHiddenInGame', [bo('bNewHidden', default='true')], 300, Y, ACT, tag='ShowIfBuilt')
b.wire(b.bnot(active, 1000, Y + 450), hide, 'bNewHidden'); G.link('Think', 'then', hide, 'execute')
ba = b.branch(active, 600, Y, tag='IfActive'); G.link(hide, 'then', ba, 'execute')
seq = b.seq('ThinkSeq', 3, 900, Y); G.link(ba, 'then', seq, 'execute')
lv2 = b.icmp('GreaterEqual_IntInt', lvl, None, 1200, Y + 450, db='2')
# then_0: coals flicker (real light beside the brazier)
cl = g('Coals', OBJV(PLC), 1100, Y - 300)
vcl = b.branch(b.valid(cl, 1250, Y - 300), 1200, Y - 500, tag='IfCoals'); G.link(seq, 'then_0', vcl, 'execute')
fl_ = b.add(b.mul(b.mul(b.sin(b.mul(now, None, 1300, Y - 700, db='9.0'), 1500, Y - 700), b.sin(b.mul(now, None, 1300, Y - 800, db='2.3'), 1500, Y - 800), 1700, Y - 750),
                  None, 1900, Y - 750, db='0.18'), None, 2100, Y - 750, db='0.82')
sci = b.call(CLS('LightComponent'), 'SetIntensity', [fl('NewIntensity', default='1200.0')], 1500, Y - 500, target=cl, tag='CoalsFlicker')
b.wire(b.mul(fl_, b.self_(None, None, lv2, 2100, Y - 600, da='1600.0', db='1200.0'), 2300, Y - 650), sci, 'NewIntensity'); G.link(vcl, 'then', sci, 'execute')
# then_1: pick a target and shoot
X = 1300; Y1 = Y + 800
can = b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', now, g('NextShot', DBL, X, Y1 + 300), X + 200, Y1 + 300),
           b.dcmp('LessEqual_DoubleDouble', g('ShotT0', DBL, X, Y1 + 400), None, X + 200, Y1 + 400, db='0.0'), X + 400, Y1 + 350)
bs = b.branch(can, X + 200, Y1, tag='IfReload'); G.link(seq, 'then_1', bs, 'execute')
s_b = b.set('BestScore', D('v', default='-1000000000.0'), None, X + 500, Y1); s_t = b.set('Target', OBJV(ACT), None, X + 750, Y1)
G.link(bs, 'then', s_b, 'execute'); G.link(s_b, 'then', s_t, 'execute')
gz = b.getall('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', ZOMBIE, X + 1000, Y1); G.link(s_t, 'then', gz, 'execute')
fe = b.foreach(ZOMBIE, X + 1350, Y1); G.link(gz, 'then', fe, 'Exec'); b.wire((gz, 'OutActors'), fe, 'Array')
z = (fe, 'Array Element')
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], X + 1300, Y1 + 400, ACT, pure=True, const=True, tag='MyLoc')
d = b.math('Vector_Distance', [(V('V1'), (me, 'ReturnValue')), (V('V2'), b.loc(z, X + 1500, Y1 + 500))], D('ReturnValue', out=True), X + 1700, Y1 + 450)
oc = b.lib(GS, 'GetObjectClass', [ob('Object', OBJ), {'name': 'ReturnValue', 'cat': 'class', 'obj': OBJ, 'out': True}], X + 1500, Y1 + 700, pure=True, tag='ZClass')
b.wire(z, oc, 'Object')
iswb = b.math('ClassIsChildOf', [({'name': 'TestClass', 'cat': 'class', 'obj': OBJ}, (oc, 'ReturnValue')),
                                 ({'name': 'ParentClass', 'cat': 'class', 'obj': OBJ, 'dobj': cpath(P_WB)}, None)], bo('ReturnValue', out=True), X + 1700, Y1 + 700)
score = b.add(b.mul(d, None, X + 1900, Y1 + 450, db='-1.0'), b.self_(None, None, iswb, X + 1900, Y1 + 700, da='3000.0', db='0.0'), X + 2100, Y1 + 550)
better = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', d, g('Range', DBL, X + 1900, Y1 + 850), X + 2100, Y1 + 850),
              b.dcmp('Greater_DoubleDouble', score, g('BestScore', DBL, X + 2100, Y1 + 950), X + 2300, Y1 + 950), X + 2500, Y1 + 900)
bb = b.branch(better, X + 1700, Y1, tag='IfBetter'); G.link(fe, 'LoopBody', bb, 'execute')
c1 = b.set('BestScore', DBL, score, X + 2000, Y1 - 200); c2 = b.set('Target', OBJV(ACT), z, X + 2250, Y1 - 200)
G.link(bb, 'then', c1, 'execute'); G.link(c1, 'then', c2, 'execute')
tgt = lambda x, y: g('Target', OBJV(ACT), x, y)
bf = b.branch(b.valid(tgt(X + 2600, Y1 + 300), X + 2750, Y1 + 300), X + 2700, Y1, tag='IfTarget'); G.link(fe, 'Completed', bf, 'execute')
frame = lambda x, y: g('Frame', OBJV(SCENE), x, y)
fpos = b.call(SCENE, 'K2_GetComponentLocation', [V('ReturnValue', out=True)], X + 2900, Y1 + 500, target=frame(X + 2750, Y1 + 500), pure=True, const=True, tag='FrameLoc')
aim = b.math('FindLookAtRotation', [(V('Start'), (fpos, 'ReturnValue')), (V('Target'), b.loc(tgt(X + 2900, Y1 + 650), X + 3050, Y1 + 650))], st('ReturnValue', ROT, out=True), X + 3200, Y1 + 550)
yaw = b.math('BreakRotator', [(st('InRot', ROT, default='0, 0, 0'), aim)], fl('Yaw', out=True, default='0.0'), X + 3400, Y1 + 550)
G.nodes[-1][3].insert(1, fl('Roll', out=True, default='0.0')); G.nodes[-1][3].insert(2, fl('Pitch', out=True, default='0.0'))
rot = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='0.0'), None), (fl('Yaw', default='0.0'), yaw)], st('ReturnValue', ROT, out=True), X + 3600, Y1 + 550)
vf = b.branch(b.valid(frame(X + 2900, Y1 + 300), X + 3050, Y1 + 300), X + 3000, Y1, tag='IfFrame'); G.link(bf, 'then', vf, 'execute')
sr = b.call(SCENE, 'K2_SetWorldRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
            bo('bTeleport', default='true')], X + 3300, Y1 - 200, target=frame(X + 3150, Y1 - 50), tag='Aim')
b.wire(rot, sr, 'NewRotation'); G.link(vf, 'then', sr, 'execute')
fwd = b.call(SCENE, 'GetForwardVector', [V('ReturnValue', out=True)], X + 3600, Y1 + 800, target=frame(X + 3450, Y1 + 800), pure=True, const=True, tag='Fwd')
muzzle = b.v2('Add_VectorVector', (fpos, 'ReturnValue'), b.math('Multiply_VectorFloat', [(V('A'), (fwd, 'ReturnValue')), (D('B', default='135.0'), None)], V('ReturnValue', out=True),
              X + 3800, Y1 + 800), X + 4000, Y1 + 750)
sfm = b.set('ShotFrom', V('v'), muzzle, X + 3600, Y1 - 200)
sto = b.set('ShotTo', V('v'), b.v2('Add_VectorVector', b.loc(tgt(X + 3700, Y1 + 1000), X + 3850, Y1 + 1000), None, X + 4000, Y1 + 1000, db='0.000000,0.000000,80.000000'), X + 3850, Y1 - 200)
st0 = b.set('ShotT0', DBL, now, X + 4100, Y1 - 200)
snx = b.set('NextShot', DBL, b.add(now, b.self_(None, None, lv2, X + 4200, Y1 + 400, da='2.5', db='4.0'), X + 4400, Y1 + 350), X + 4350, Y1 - 200)
snd = b.lib(GS, 'PlaySoundAtLocation', [WC(), dict(ob('Sound', SOUND), dobj='/Game/CastleDefender/Gameplay/Castle/SFX_Ballista_Shot.SFX_Ballista_Shot'), V('Location'),
            st('Rotation', ROT, default='0, 0, 0'), fl('VolumeMultiplier', default='1.000000'), fl('PitchMultiplier', default='1.000000'), fl('StartTime', default='0.000000')],
            X + 4600, Y1 - 200, tag='Shot')
b.wire(muzzle, snd, 'Location')
b.chain(sr, sfm, sto, st0, snx, snd)
# then_2: spear flight + hit
X = 1300; Y2 = Y + 2800
t0 = lambda x, y: g('ShotT0', DBL, x, y)
bfl = b.branch(b.dcmp('Greater_DoubleDouble', t0(X, Y2 + 300), None, X + 200, Y2 + 300, db='0.0'), X + 200, Y2, tag='IfFlying'); G.link(seq, 'then_2', bfl, 'execute')
p = b.sat(b.div(b.sub(now, t0(X + 300, Y2 + 500), X + 500, Y2 + 450), None, X + 700, Y2 + 450, db='0.35'), X + 900, Y2 + 450)
pos = b.v2('Add_VectorVector', b.math('VLerp', [(V('A'), g('ShotFrom', V('v'), X + 900, Y2 + 600)), (V('B'), g('ShotTo', V('v'), X + 900, Y2 + 700)), (fl('Alpha', default='0.0'), p)],
           V('ReturnValue', out=True), X + 1100, Y2 + 600), b.vec(None, None, b.mul(b.sin(b.mul(p, None, X + 1100, Y2 + 800, db=repr(math.pi)), X + 1300, Y2 + 800), None, X + 1500, Y2 + 800, db='120.0'),
           X + 1700, Y2 + 800), X + 1900, Y2 + 650)
spear = lambda x, y: g('Spear', OBJV(SCENE), x, y)
vs = b.branch(b.valid(spear(X + 500, Y2 + 200), X + 650, Y2 + 200), X + 500, Y2, tag='IfSpear'); G.link(bfl, 'then', vs, 'execute')
msp = b.call(SCENE, 'K2_SetWorldLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
             X + 800, Y2 - 200, target=spear(X + 650, Y2 - 50), tag='SpearFly')
b.wire(pos, msp, 'NewLocation'); G.link(vs, 'then', msp, 'execute')
mg = b.seq('AfterSpear', 1, X + 1100, Y2); G.link(vs, 'else', mg, 'execute'); G.link(msp, 'then', mg, 'execute')
bh = b.branch(b.dcmp('GreaterEqual_DoubleDouble', p, None, X + 1300, Y2 + 300, db='1.0'), X + 1300, Y2, tag='IfHit'); G.link(mg, 'then_0', bh, 'execute')
vt_ = b.branch(b.valid(tgt(X + 1500, Y2 + 300), X + 1650, Y2 + 300), X + 1600, Y2, tag='IfAlive'); G.link(bh, 'then', vt_, 'execute')
dmg = b.lib(GS, 'ApplyDamage', [ob('DamagedActor', ACT), fl('BaseDamage', default='120.0'), ob('EventInstigator', CTRL), ob('DamageCauser', ACT),
            {'name': 'DamageTypeClass', 'cat': 'class', 'obj': CLS('DamageType')}, fl('ReturnValue', out=True, default='0.0')], X + 1900, Y2 - 200, tag='Hit')
b.wire(tgt(X + 1750, Y2 - 50), dmg, 'DamagedActor'); b.wire(b.self_node(X + 1750, Y2 + 50), dmg, 'DamageCauser')
b.wire(b.self_(None, None, lv2, X + 1750, Y2 + 150, da='180.0', db='120.0'), dmg, 'BaseDamage'); G.link(vt_, 'then', dmg, 'execute')
rst = b.set('ShotT0', DBL, None, X + 2200, Y2)
G.link(vt_, 'else', rst, 'execute'); G.link(dmg, 'then', rst, 'execute')
back = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation', default='135.000000,0.000000,20.000000'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
              bo('bTeleport', default='true')], X + 2450, Y2, target=spear(X + 2300, Y2 + 200), tag='SpearReload')
G.link(rst, 'then', back, 'execute')
write(G, 'BP_TowerBallista_graph.txt')
VARS_T = [('Frame', 'obj:SceneComponent', '', 'the yawing launcher (tag BallistaFrame)'), ('Spear', 'obj:SceneComponent', '', 'the flying spear (tag BallistaSpear)'),
          ('Coals', 'obj:PointLightComponent', '', 'brazier light (tag BallistaCoals)'), ('Target', 'obj:Actor', '', 'current target'),
          ('BestScore', 'real', '0.0', 'scratch'), ('NextShot', 'real', '0.0', 'game time it may fire again'), ('ShotT0', 'real', '0.0', 'spear launch time (0 = none in flight)'),
          ('ShotFrom', 'vector', '0,0,0', 'muzzle'), ('ShotTo', 'vector', '0,0,0', 'aim point'), ('Range', 'real', '5000.0', 'cm')]

# ================================================================================================= BP_ZombieWallBreaker: walls effect
G = Graph(); b = B8(G, 'wu')
up = b.upgrades_of_player(0, 0)
walls = b.seli(b.getm('Walls', CUC, INT, up, 400, 0), None, b.valid(up, 400, 150), 600, 50, db='0')
dmg = b.div(None, b.add(b.mul(b.i2d(walls, 800, 50), None, 1000, 50, db='0.75'), None, 1200, 50, db='1.0'), 1400, 0, da='500.0')
write(G, 'WallBreaker_Walls_graph.txt')
json.dump({'blueprint': 'BP_ZombieWallBreaker', '_built_on': 'handoffs/exports/master/2026-10-30b/BP_ZombieWallBreaker_EventGraph.txt',
           'pastes': [{'file': 'WallBreaker_Walls_graph.txt', 'offset': [-1200, -900]}],
           'rewires': [{'from': dmg[0] + '.ReturnValue', 'to': 'SM_Dmg.BaseDamage', 'note': 'was the constant 500: smash damage on the breach spot / (1 + 0.75 Walls)'}]},
          open(os.path.join(HERE, 'manifest_wallbreaker.json'), 'w'), indent=1)


# ================================================================================================= BPVar lines
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('int', 'bool'): return 'PinCategory="%s"' % kind
    if kind == 'vector': return 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda bp, n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'castle224/%s/%s' % (bp, n)).hex.upper(), vt(k), n, d)
out = ['# #224 Castle upgrades - paste one line at a time on the VARIABLES header of My Blueprint, then Compile', '', '# ---- BPC_CastleUpgrades']
out += [bpv('BPC_CastleUpgrades', *v[:3]) for v in VARS_C] + ['', '# ---- BP_TowerBallista'] + [bpv('BP_TowerBallista', *v[:3]) for v in VARS_T]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #224 variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bp, vs in (('BPC_CastleUpgrades', VARS_C), ('BP_TowerBallista', VARS_T)):
        for n, _k, d, m in vs: f.write('| %s | %s | %s | %s |\n' % (bp, n, d or '-', m))
print('BPVar lines: %d + %d' % (len(VARS_C), len(VARS_T)))
