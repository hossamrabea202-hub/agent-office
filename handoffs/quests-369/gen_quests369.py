# #369 Quests + daily rewards, v1 system (adjustedfilm, 2026-10-31). Owner W: "daily rewards. quests map : use inventory,
# recruit soldier, commander, kill zombie, mount canon, find object, etc." TGA makes the quest-map look later; this is the
# working logic with a plain screen (the game's own notice board + toasts). Core of #364 (Day Ledger).
#   "<blender python>" -I gen_quests369.py -> BPC_Quests_graph.txt + VARIABLES_BPVar.txt
# BPC_Quests (ActorComponent on the hero, added by the setup script; touches no other Blueprint):
#   BeginPlay  load slot CastleSaveQuests (BP_CastleSave.Data: [Done0..9, Kills, Earned, LastDay, Streak]), remember the
#              soldier count, then the DAILY REWARD: a new calendar day -> streak +1 if it was yesterday, else 1;
#              reward 100 x streak gold (cap 7 = 700), toast; saved. Starts QPoll every 0.5 s (a timer by name).
#   QPoll      watches what the game already shows (no hooks in other Blueprints):
#                0 Open your pack (inventory)      HUD StatV > 0.5          100 gold
#                1 Visit Vesna's shop              HUD ShopV > 0.5          100
#                2 Recruit a soldier               more soldiers than at start   150
#                3 Recruit a commander             a BP_SoldierCommander exists  300
#                4 Mount a cannon                  hero MountedCannon is set     150
#                5 Slay 10 zombies                 hero XP went up 10 times      200
#                6 Slay 50 zombies                 ... 50 times                  500
#                7 Find the old chest              a BP_TreasureChest is Opened  300
#                8 Survive a night                 BP_DayNight night -> day      400
#                9 Earn 1000 gold                  gold gained since the start   300
#              each one once: done -> gold to the HUD, toast "Quest done: <name>  +N gold", saved.
#   J          the quest list on the notice board: "[x] Recruit a soldier", "[ ] Slay 50 zombies (12/50)", ...
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
P_ZHUD, P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
P_TOAST, P_DN = '/Game/CastleDefender/Gameplay/Castle/BPC_Toast', '/Game/CastleDefender/Environment/DayNight/BP_DayNight'
P_CHEST, P_SAVE = '/Game/CastleDefender/Gameplay/Chest/BP_TreasureChest', '/Game/CastleDefender/Gameplay/Save/BP_CastleSave'
HERO, ZHUD, NOTC = BPC(P_HERO, 'BP_ThirdPersonCharacter'), BPC(P_ZHUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD')
TOAST, DNC, CHEST, SAVE = BPC(P_TOAST, 'BPC_Toast'), BPC(P_DN, 'BP_DayNight'), BPC(P_CHEST, 'BP_TreasureChest'), BPC(P_SAVE, 'BP_CastleSave')
SAVEG, ACOMP = CLS('SaveGame'), CLS('ActorComponent')
SLOT = 'CastleSaveQuests'
Q = [('Open your pack (inventory)', 100), ("Visit Vesna's shop", 100), ('Recruit a soldier', 150), ('Recruit a commander', 300),
     ('Mount a cannon', 150), ('Slay 10 zombies', 200), ('Slay 50 zombies', 500), ('Find the old chest', 300),
     ('Survive a night', 400), ('Earn 1000 gold', 300)]
NQ, I_KILLS, I_EARN, I_DAY, I_STREAK = len(Q), 10, 11, 12, 13
DATA = arr(D('v', default='0.0'))

G = Graph(); b = bpkit.B(G, 'q'); g = b.get
dget = lambda i, x, y: b.aget('Data', D('v', default='0.0'), b.math('Conv_IntToInteger', [], it('ReturnValue', out=True), 0, 0) if False else None, x, y) if False else _dget(i, x, y)


def _dget(i, x, y):
    a = b.get('Data', DATA, x, y)
    n = b.name('DataGet')
    G.node(n, 'K2Node_GetArrayItem', [], [arr(D('Array')), it('Dimension 1', default=str(i)), D('Output', out=True)], x + 220, y)
    b.wire(a, n, 'Array'); return (n, 'Output')


def dset(i, val, x, y, dval='1.0'):
    return b.aset('Data', D('v', default='0.0'), None, val, x, y, ditem=dval) if False else _dset(i, val, x, y, dval)


def _dset(i, val, x, y, dval):
    a = b.get('Data', DATA, x, y + 150)
    n = b.name('DataSet')
    G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Set")' % KARR],
           [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
            it('Index', default=str(i)), {'name': 'Item', 'cat': 'wildcard', 'ref': True, 'default': dval}, bo('bSizeToFit', default='true')], x, y)
    b.wire(a, n, 'TargetArray'); b.wire(val, n, 'Item'); return n


def hud_cast(x, y, cls=ZHUD, nm=None):
    pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x - 400, y + 250, pure=True, tag='PC')
    hd = b.call(PCON, 'GetHUD', [ob('ReturnValue', CLS('HUD'), out=True)], x - 200, y + 250, target=(pc, 'ReturnValue'), pure=True, const=True, tag='HUD')
    c = nm or b.name('CastHUD'); cast(G, c, cls, 'AsHUD', x, y); b.wire((hd, 'ReturnValue'), c, 'Object'); return c


def hero_cast(x, y):
    h = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], x - 250, y + 250, pure=True, tag='Hero')
    c = b.name('CastHero'); cast(G, c, HERO, 'AsHero', x, y); b.wire((h, 'ReturnValue'), c, 'Object'); return c


def toast(text_src, x, y):
    """hero.Toast.Toast(Text): one cast per consumer"""
    hc = hero_cast(x, y)
    tc = b.getm('Toast', HERO, ob('v', TOAST), (hc, 'AsHero'), x + 250, y + 250)
    t = b.call(TOAST, 'Toast', [S('Text')], x + 450, y, target=tc, tag='ShowToast'); b.wire(text_src, t, 'Text')
    G.link(hc, 'then', t, 'execute'); return hc, t


def add_gold(amount_src, x, y):
    """HUD.Gold += amount (int), returns (first, last) exec"""
    hc = hud_cast(x, y)
    gold = b.getm('Gold', ZHUD, INT, (hc, 'AsHUD'), x + 250, y + 300)
    s = b.setm('Gold', ZHUD, INT, b.i2('Add_IntInt', gold, amount_src, x + 450, y + 300), (hc, 'AsHUD'), x + 600, y)
    G.link(hc, 'then', s, 'execute'); return hc, s


# ============================================================ BeginPlay: load, daily reward, start the poll
b.G.node('qBegin', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACOMP, 'bOverrideFunction=True'],
         [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACOMP}, ex('then', True)], 0, 0)
has = b.lib(GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 150, 0, tag='HasSave')   # impure in 5.3
bh = b.branch((has, 'ReturnValue'), 350, 0, tag='IfSave'); G.link('qBegin', 'then', has, 'execute'); G.link(has, 'then', bh, 'execute')
ld = b.lib(GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', SAVEG, out=True)], 550, -200, tag='Load')
G.link(bh, 'then', ld, 'execute')
cs = 'qCastSave'; cast(G, cs, SAVE, 'AsSave', 800, -200); b.wire((ld, 'ReturnValue'), cs, 'Object'); G.link(ld, 'then', cs, 'execute')
sd = b.set('Data', DATA, b.getm('Data', SAVE, DATA, (cs, 'AsSave'), 1000, 0), 1100, -200); G.link(cs, 'then', sd, 'execute')
j0 = b.seq('qJoin0', 1, 1400, 0)
G.link(bh, 'else', j0, 'execute'); G.link(sd, 'then', j0, 'execute'); G.link(cs, 'CastFailed', j0, 'execute')
# make sure Data has 14 slots
pad = _dset(I_STREAK, _dget(I_STREAK, 1500, 300), 1600, 0, '0.0')
G.link(j0, 'then_0', pad, 'execute')
# soldiers at start
gs = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SOLDIER)), arr(ob('OutActors', ACT, out=True))], 1900, 0, tag='Soldiers0')
G.link(pad, 'then', gs, 'execute')
n0 = b.name('LenSoldiers0')
G.node(n0, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 2100, 300)
G.link(gs, 'OutActors', n0, 'TargetArray')
s0 = b.set('Soldiers0', INT, (n0, 'ReturnValue'), 2200, 0); G.link(gs, 'then', s0, 'execute')
# daily: today = Year * 1000 + DayOfYear
now = b.lib(KML, 'Now', [st('ReturnValue', '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.DateTime\'"', out=True)], 2200, 500, pure=True)
yr = b.lib(KML, 'GetYear', [st('A', '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.DateTime\'"'), it('ReturnValue', out=True)], 2400, 500, pure=True)
dy = b.lib(KML, 'GetDayOfYear', [st('A', '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.DateTime\'"'), it('ReturnValue', out=True)], 2400, 650, pure=True)
b.wire((now, 'ReturnValue'), yr, 'A'); b.wire((now, 'ReturnValue'), dy, 'A')
today = b.i2d(b.i2('Add_IntInt', b.i2('Multiply_IntInt', (yr, 'ReturnValue'), None, 2600, 500, db='1000'), (dy, 'ReturnValue'), 2800, 550), 3000, 550)
st_today = b.set('Today', DBL, today, 2500, 0); G.link(s0, 'then', st_today, 'execute')
last = _dget(I_DAY, 2600, 800)
bnew = b.branch(b.dcmp('NotEqual_DoubleDouble', g('Today', DBL, 2700, 900), last, 2900, 850), 2800, 0, tag='IfNewDay')
G.link(st_today, 'then', bnew, 'execute')
yday = b.dcmp('EqualEqual_DoubleDouble', last, b.d2('Subtract_DoubleDouble', g('Today', DBL, 2900, 1000), None, 3100, 1000, db='1.0'), 3300, 950)
streak = b.self_(b.d2('Add_DoubleDouble', _dget(I_STREAK, 3100, 1150), None, 3300, 1150, db='1.0'), None, yday, 3500, 1050, db='1.0')
sstr = _dset(I_STREAK, streak, 3100, -100, '1.0'); G.link(bnew, 'then', sstr, 'execute')
sday = _dset(I_DAY, g('Today', DBL, 3300, 200), 3400, -100, '0.0'); G.link(sstr, 'then', sday, 'execute')
rew = b.math('FTrunc', [(D('A'), b.d2('Multiply_DoubleDouble', b.clamp(_dget(I_STREAK, 3500, 400), '1.0', '7.0', 3700, 400), None, 3900, 400, db='100.0'))],
             it('ReturnValue', out=True), 4100, 400)
ga1, gb1 = add_gold(rew, 3700, -100); G.link(sday, 'then', ga1, 'execute')
dtxt = b.concat(b.concat(b.math('Conv_IntToString', [(it('InInt'), b.math('FTrunc', [(D('A'), _dget(I_STREAK, 4300, 500))], it('ReturnValue', out=True), 4500, 500))],
                                S('ReturnValue', out=True), 4700, 500), None, 4900, 500, db=' day streak - daily reward +'),
                b.math('Conv_IntToString', [(it('InInt'), rew)], S('ReturnValue', out=True), 4900, 650), 5100, 550, da='')
dtxt2 = b.concat(None, dtxt, 5300, 550, da='Welcome back! ')
tc1, tt1 = toast(dtxt2, 4400, -100); G.link(gb1, 'then', tc1, 'execute')
sdirty = b.set('Dirty', bo('v', default='false'), None, 5000, -100) if False else b.set('Dirty', dict(BOOL, default='true'), None, 5000, -100)
G.link(tt1, 'then', sdirty, 'execute')
j1 = b.seq('qJoin1', 1, 5300, 0); G.link(bnew, 'else', j1, 'execute'); G.link(sdirty, 'then', j1, 'execute')
fdn = b.actor_of(P_DN, DNC, 5500, 0); G.link(j1, 'then_0', fdn, 'execute')
sdn = b.set('DN', ob('v', DNC), (fdn, 'ReturnValue'), 5750, 0); G.link(fdn, 'then', sdn, 'execute')
tm = b.timer('QPoll', 6000, 0, dtime='0.5', loop=True); b.wire(b.self_node(5850, 200), tm, 'Object'); G.link(sdn, 'then', tm, 'execute')

# ============================================================ QPoll
Y = 2000
b.event('QPoll', [], 0, Y)
prev = ('QPoll', 'then')
# --- trackers first: kills (hero XP went up), gold earned, night -> day
hc = hero_cast(300, Y); G.link(prev[0], prev[1], hc, 'execute')
xp = b.getm('XP', HERO, INT, (hc, 'AsHero'), 500, Y + 300)
up = b.icmp('Greater_IntInt', xp, g('LastXP', INT, 500, Y + 400), 700, Y + 350)
bk = b.branch(b.b2('BooleanAND', up, g('XPSeen', BOOL, 700, Y + 450), 900, Y + 400), 600, Y, tag='IfKill'); G.link(hc, 'then', bk, 'execute')
k1 = _dset(I_KILLS, b.d2('Add_DoubleDouble', _dget(I_KILLS, 700, Y - 300), None, 900, Y - 300, db='1.0'), 900, Y - 150, '0.0'); G.link(bk, 'then', k1, 'execute')
jk = b.seq('qJoinK', 1, 1200, Y); G.link(bk, 'else', jk, 'execute'); G.link(k1, 'then', jk, 'execute')
lx = b.set('LastXP', INT, xp, 1400, Y); G.link(jk, 'then_0', lx, 'execute')
xs = b.set('XPSeen', dict(BOOL, default='true'), None, 1600, Y); G.link(lx, 'then', xs, 'execute')
hu = hud_cast(1900, Y, nm='qCastHUDGold'); G.link(xs, 'then', hu, 'execute')
gold = b.getm('Gold', ZHUD, INT, (hu, 'AsHUD'), 2100, Y + 300)
gain = b.i2('Subtract_IntInt', gold, g('LastGold', INT, 2100, Y + 400), 2300, Y + 350)
bg = b.branch(b.b2('BooleanAND', b.icmp('Greater_IntInt', gain, None, 2500, Y + 350), g('GoldSeen', BOOL, 2500, Y + 450), 2700, Y + 400), 2200, Y, tag='IfEarned')
G.link(hu, 'then', bg, 'execute')
e1 = _dset(I_EARN, b.d2('Add_DoubleDouble', _dget(I_EARN, 2300, Y - 300), b.i2d(gain, 2500, Y - 200), 2700, Y - 300), 2700, Y - 150, '0.0'); G.link(bg, 'then', e1, 'execute')
je = b.seq('qJoinE', 1, 3000, Y); G.link(bg, 'else', je, 'execute'); G.link(e1, 'then', je, 'execute')
lg = b.set('LastGold', INT, gold, 3200, Y); G.link(je, 'then_0', lg, 'execute')
gsn = b.set('GoldSeen', dict(BOOL, default='true'), None, 3400, Y); G.link(lg, 'then', gsn, 'execute')
night = b.b2('BooleanAND', b.valid(g('DN', ob('v', DNC), 3400, Y + 300), 3600, Y + 300), b.getm('IsNight', DNC, BOOL, g('DN', ob('v', DNC), 3400, Y + 400), 3600, Y + 400), 3800, Y + 350)
dawn = b.branch(b.b2('BooleanAND', g('WasNight', BOOL, 3800, Y + 500), b.bnot(night, 4000, Y + 450), 4200, Y + 450), 3700, Y, tag='IfDawn')
G.link(gsn, 'then', dawn, 'execute')
sn = b.set('NightsSurvived', INT, b.i2('Add_IntInt', g('NightsSurvived', INT, 3900, Y - 300), None, 4100, Y - 300, db='1'), 4100, Y - 150); G.link(dawn, 'then', sn, 'execute')
jd = b.seq('qJoinD', 1, 4400, Y); G.link(dawn, 'else', jd, 'execute'); G.link(sn, 'then', jd, 'execute')
wn = b.set('WasNight', BOOL, night, 4600, Y); G.link(jd, 'then_0', wn, 'execute')
prev = (wn, 'then')

# --- the 10 quest conditions
X0, YQ = 5000, Y
hud2 = lambda x, y: None
conds = []
# 0 pack, 1 shop: HUD StatV / ShopV (one HUD cast for both)
hq = hud_cast(X0, YQ, nm='qCastHUDQ'); G.link(prev[0], prev[1], hq, 'execute'); prev = (hq, 'then'); prev_fail = (hq, 'CastFailed')
conds.append(b.dcmp('Greater_DoubleDouble', b.getm('StatV', ZHUD, DBL, (hq, 'AsHUD'), X0 + 250, YQ + 300), None, X0 + 450, YQ + 300, db='0.5'))
conds.append(b.dcmp('Greater_DoubleDouble', b.getm('ShopV', ZHUD, DBL, (hq, 'AsHUD'), X0 + 250, YQ + 400), None, X0 + 450, YQ + 400, db='0.5'))
# 2 soldiers, 3 commander, 7 chest: actor queries (impure, in the chain)
gs2 = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SOLDIER)), arr(ob('OutActors', ACT, out=True))], X0 + 300, YQ - 300, tag='SoldiersNow')
n2 = b.name('LenSoldiers')
G.node(n2, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], X0 + 500, YQ - 100)
G.link(gs2, 'OutActors', n2, 'TargetArray')
G.link(hq, 'then', gs2, 'execute'); G.link(hq, 'CastFailed', gs2, 'execute')
cm = b.actor_of(P_CMDR, ACT, X0 + 600, YQ - 300); G.link(gs2, 'then', cm, 'execute')
ch = b.actor_of(P_CHEST, CHEST, X0 + 900, YQ - 300); G.link(cm, 'then', ch, 'execute')
hcq = hero_cast(X0 + 1200, YQ - 300); G.link(ch, 'then', hcq, 'execute')
prev = (hcq, 'then')
conds.append(b.icmp('Greater_IntInt', (n2, 'ReturnValue'), g('Soldiers0', INT, X0 + 500, YQ + 500), X0 + 700, YQ + 500))
conds.append(b.valid((cm, 'ReturnValue'), X0 + 700, YQ + 600))
conds.append(b.valid(b.getm('MountedCannon', HERO, ob('v', ACT), (hcq, 'AsHero'), X0 + 500, YQ + 700), X0 + 700, YQ + 700))
conds.append(b.dcmp('GreaterEqual_DoubleDouble', _dget(I_KILLS, X0 + 500, YQ + 800), None, X0 + 700, YQ + 800, db='10.0'))
conds.append(b.dcmp('GreaterEqual_DoubleDouble', _dget(I_KILLS, X0 + 500, YQ + 900), None, X0 + 700, YQ + 900, db='50.0'))
conds.append(b.b2('BooleanAND', b.valid((ch, 'ReturnValue'), X0 + 500, YQ + 1000), b.getm('Opened', CHEST, BOOL, (ch, 'ReturnValue'), X0 + 500, YQ + 1100), X0 + 700, YQ + 1050))
conds.append(b.icmp('GreaterEqual_IntInt', g('NightsSurvived', INT, X0 + 500, YQ + 1200), None, X0 + 700, YQ + 1200, db='1'))
conds.append(b.dcmp('GreaterEqual_DoubleDouble', _dget(I_EARN, X0 + 500, YQ + 1300), None, X0 + 700, YQ + 1300, db='1000.0'))
x = X0 + 1600
for i, ((name, reward), c) in enumerate(zip(Q, conds)):
    notdone = b.dcmp('Less_DoubleDouble', _dget(i, x, YQ + 400), None, x + 200, YQ + 400, db='0.5')
    bq = b.branch(b.b2('BooleanAND', notdone, c, x + 400, YQ + 350), x, YQ, tag='IfQ%d' % i)
    G.link(prev[0], prev[1], bq, 'execute')
    sdn_ = _dset(i, None, x + 300, YQ - 300, '1.0'); G.link(bq, 'then', sdn_, 'execute')
    ga_, gb_ = add_gold(None, x + 600, YQ - 300); G.link(sdn_, 'then', ga_, 'execute')
    G.nodes[[n[0] for n in G.nodes].index(gb_)][3]  # (gold add reward default)
    # reward amount as the Add's B default
    addn = [l for l in G.links if l[2] == gb_ and l[3] == 'Gold'][0][0]
    for n in G.nodes:
        if n[0] == addn:
            for p in n[3]:
                if p['name'] == 'B': p['default'] = str(reward)
    tc_, tt_ = toast(b.concat(None, None, x + 1300, YQ - 100, da='Quest done: %s  +%d gold' % (name, reward), db=''), x + 1300, YQ - 300)
    G.link(gb_, 'then', tc_, 'execute')
    dd = b.set('Dirty', dict(BOOL, default='true'), None, x + 1900, YQ - 300); G.link(tt_, 'then', dd, 'execute')
    jq = b.seq('qJoinQ%d' % i, 1, x + 2100, YQ); G.link(bq, 'else', jq, 'execute'); G.link(dd, 'then', jq, 'execute')
    prev = (jq, 'then_0'); x += 2400
# --- save when something changed
bs = b.branch(g('Dirty', BOOL, x, YQ + 300), x, YQ, tag='IfDirty'); G.link(prev[0], prev[1], bs, 'execute')
cso = b.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SAVEG, cpath(P_SAVE)), ob('ReturnValue', SAVEG, out=True)], x + 300, YQ - 200, tag='NewSave')
G.link(bs, 'then', cso, 'execute')
cs2 = 'qCastSave2'; cast(G, cs2, SAVE, 'AsSave', x + 600, YQ - 200); b.wire((cso, 'ReturnValue'), cs2, 'Object'); G.link(cso, 'then', cs2, 'execute')
sdt = b.setm('Data', SAVE, DATA, g('Data', DATA, x + 700, YQ + 100), (cs2, 'AsSave'), x + 900, YQ - 200); G.link(cs2, 'then', sdt, 'execute')
svg = b.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SAVEG), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], x + 1200, YQ - 200, tag='Save')
b.wire((cs2, 'AsSave'), svg, 'SaveGameObject'); G.link(sdt, 'then', svg, 'execute')
clr = b.set('Dirty', dict(BOOL, default='false'), None, x + 1500, YQ - 200); G.link(svg, 'then', clr, 'execute')
jsv = b.seq('qJoinS', 1, x + 1800, YQ); G.link(bs, 'else', jsv, 'execute'); G.link(clr, 'then', jsv, 'execute'); G.link(cs2, 'CastFailed', jsv, 'execute')
# --- J: the quest list on the notice board (edge-detected)
pcj = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x + 1800, YQ + 300, pure=True, tag='PCJ')
kj = b.call(PCON, 'IsInputKeyDown', [st('Key', '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"', default='J'), bo('ReturnValue', out=True, default='false')],
            x + 2000, YQ + 300, target=(pcj, 'ReturnValue'), pure=True, const=True, tag='KeyJ')
press = b.b2('BooleanAND', (kj, 'ReturnValue'), b.bnot(g('JWas', BOOL, x + 2200, YQ + 450), x + 2400, YQ + 450), x + 2600, YQ + 400)
bj = b.branch(press, x + 2100, YQ, tag='IfJ'); G.link(jsv, 'then_0', bj, 'execute')
txt = None
for i, (name, reward) in enumerate(Q):
    mark = b.selstr(None, None, b.dcmp('Greater_DoubleDouble', _dget(i, x + 2300, YQ + 700 + 120 * i), None, x + 2500, YQ + 700 + 120 * i, db='0.5'),
                    x + 2700, YQ + 700 + 120 * i, da='[x] ', db='[ ] ')
    line = b.concat(mark, None, x + 2900, YQ + 700 + 120 * i, db=name + ('    ' if i < NQ - 1 else ''))
    txt = line if txt is None else b.concat(txt, line, x + 3100, YQ + 700 + 120 * i)
head = b.concat(None, txt, x + 3300, YQ + 700, da='QUESTS (J)    ')
hn = hud_cast(x + 2400, YQ - 300, cls=NOTC, nm='qCastNotice'); G.link(bj, 'then', hn, 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='1')], x + 2700, YQ - 300, target=(hn, 'AsHUD'), tag='ShowQuests')
b.wire(head, pn, 'Text'); G.link(hn, 'then', pn, 'execute')
jj = b.seq('qJoinJ', 1, x + 3000, YQ); G.link(bj, 'else', jj, 'execute'); G.link(pn, 'then', jj, 'execute'); G.link(hn, 'CastFailed', jj, 'execute')
sjw = b.set('JWas', BOOL, (kj, 'ReturnValue'), x + 3200, YQ); G.link(jj, 'then_0', sjw, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('bad %s dup %s' % (bad[:6], [n for n in names if names.count(n) > 1][:5]))
open(os.path.join(HERE, 'BPC_Quests_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_Quests_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))
DT = 'PinCategory="real",PinSubCategory="double"'
VARS = [('Data', DT + ',ContainerType=Array', ''), ('Dirty', 'PinCategory="bool"', 'false'), ('Today', DT, '0.0'), ('Soldiers0', 'PinCategory="int"', '0'),
        ('LastXP', 'PinCategory="int"', '0'), ('XPSeen', 'PinCategory="bool"', 'false'), ('LastGold', 'PinCategory="int"', '0'), ('GoldSeen', 'PinCategory="bool"', 'false'),
        ('WasNight', 'PinCategory="bool"', 'false'), ('NightsSurvived', 'PinCategory="int"', '0'), ('JWas', 'PinCategory="bool"', 'false'),
        ('DN', 'PinCategory="object",PinSubCategoryObject="%s"' % DNC.strip('"'), '')]
bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'quests369/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('# #369 BPC_Quests - paste one line at a time on the VARIABLES header, then Compile\n' + '\n'.join(bpv(*v) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
