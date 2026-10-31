# #185 Medics (adjustedfilm, 2026-10-31): a recruitable unit that heals wounded soldiers and the hero, never fights.
#   "<blender python>" -I gen_medics185.py -> BPC_Medics_graph.txt, BP_Medic_graph.txt, MotionFX_Medics_graph.txt +
#        manifest_motionfx_medics.json, VARIABLES_BPVar.txt, VARIABLES.md
# Numbers (card: "spec the numbers first"): Price 150 gold, MaxMedics 4, heal 8 HP/s within 2.5 m, looks for patients within
#   25 m, retreats when a zombie is within 6 m, otherwise follows the hero 4 m behind. Walk 380 (soldier-like).
# BPC_Medics (hero component "Medics"): at the barracks NPC (4.5 m) a notice "[M] Recruit a medic: 150 gold (n/4)"; M buys
#   (BP_ZombieHUD.Gold) -> a BP_Medic walks out of the barracks. DrawMedics(Hud, SizeX, SizeY): "MEDICS n/4" under the
#   top-left HUD block, green-white, only while you have medics (via the BPC_MotionFX hook, after the #283 map).
# BP_Medic (Character, stand-in soldier body + TGA's satchel and armband #248, attached at BeginPlay to spine_03 / Spine2
#   and upperarm_l / LeftArm, whichever exists). Think every 0.5 s:
#   danger (zombie within 6 m) -> run toward the hero;
#   else the most wounded patient within 25 m: soldiers (State.X = HP, alive while State.Z < 0.5; their max is the highest
#   HP the medic has seen on them) or the hero (BP_ThirdPersonCharacter.DamageTaken > 0) -> walk to him; within 2.5 m heal
#   4 HP per tick (8 HP/s): soldier State.X += 4 (capped at his max), hero DamageTaken -= 4 (floored at 0); "+ HEAL"
#   floats over the medic (TextRender, green) while healing;
#   nobody to heal -> follow the hero.
import math, os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP, HUDC = CLS('ActorComponent'), CLS('HUD')
P_MC = '/Game/CastleDefender/Gameplay/Medics/BPC_Medics'
P_MED = '/Game/CastleDefender/Gameplay/Medics/BP_Medic'
P_NPC = '/Game/CastleDefender/Gameplay/Castle/BP_NPC_Barracks'
P_ZHUD, P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
MCC, MEDC, NPCC = BPC(P_MC, 'BPC_Medics'), BPC(P_MED, 'BP_Medic'), BPC(P_NPC, 'BP_NPC_Barracks')
ZHUDC, NOTC, HEROC = BPC(P_ZHUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD'), BPC(P_HERO, 'BP_ThirdPersonCharacter')
TEXTR, SMC = CLS('TextRenderComponent'), CLS('StaticMeshComponent')
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
FONTC = '"/Script/CoreUObject.Class\'/Script/Engine.Font\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
OBJV = lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
RULE = lambda n: {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', 'default': 'SnapToTarget'}
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)


class BM(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def item(s, arrsrc, pin, idx, x, y):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def getall(s, path, cls, x, y):
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def count(s, node, x, y):
        n = s.name('Count')
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.G.link(node, 'OutActors', n, 'TargetArray'); return (n, 'ReturnValue')
    def actor_of_(s, path, cls, x, y):
        return s.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], x, y, tag='Find' + path.split('/')[-1][3:])
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
    def myloc(s, x, y):
        n = s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'); return (n, 'ReturnValue')
    def dist2d(s, a, c, x, y): return s.math('Vector_Distance2D', [(V('V1'), a), (V('V2'), c)], D('ReturnValue', out=True), x, y)
    def owner(s, x, y):
        n = s.name('Owner'); callfn(s.G, n, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hero(s, x, y):
        return (s.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], x, y, pure=True, tag='Hero'), 'ReturnValue')
    def hud_cast(s, cls, label, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', CLS('HUD'), out=True)], x - 150, y + 300, target=s.pc(x - 350, y + 300), pure=True, const=True, tag='GetHUD')
        nc = s.name('As' + label.replace(' ', '')); cast(s.G, nc, cls, 'As' + label, x, y); s.wire((hud, 'ReturnValue'), nc, 'Object'); return nc, (nc, 'As' + label)
    def notice(s, text, x, y, text_src=None):
        nc, nh = s.hud_cast(NOTC, 'BP Notice HUD', x, y)
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x + 300, y, target=nh, tag='Notice')
        s.wire(text_src, pn, 'Text'); s.G.link(nc, 'then', pn, 'execute'); return nc, pn
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.200000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def istr(s, src, x, y):
        n = s.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], x, y, pure=True, tag='IntStr'); s.wire(src, n, 'InInt'); return (n, 'ReturnValue')
    def move_to(s, goal, x, y):
        ctl = s.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], x, y + 250, PAWN, pure=True, const=True, tag='Ctl')
        mv = s.lib(NAVSYS, 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], x + 250, y, tag='Move')
        s.wire((ctl, 'ReturnValue'), mv, 'Controller'); s.wire(goal, mv, 'Goal'); return mv


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


# ================================================================================================= BPC_Medics
G = Graph(); b = BM(G, 'md')
g = b.get
event_override(G, 'BP', COMP, 'ReceiveBeginPlay', [], 0, 0)
t1 = b.timer_ev('MedPoll', '1.0', 300, 0); t2 = b.timer_ev('MedKeys', '0.05', 600, 0)
G.link('BP', 'then', t1, 'execute'); G.link(t1, 'then', t2, 'execute')
# MedPoll: count medics, barracks prompt
Y = 800
b.event('MedPoll', [], 0, Y)
gm = b.getall(P_MED, MEDC, 300, Y); G.link('MedPoll', 'then', gm, 'execute')
scnt = b.set('Count', INT, b.count(gm, 500, Y + 300), 650, Y); G.link(gm, 'then', scnt, 'execute')
fn = b.actor_of_(P_NPC, NPCC, 900, Y); G.link(scnt, 'then', fn, 'execute')
npc = (fn, 'ReturnValue')
near = b.b2('BooleanAND', b.valid(npc, 1100, Y + 300),
            b.dcmp('Less_DoubleDouble', b.dist2d(b.loc(b.owner(1100, Y + 450), 1300, Y + 450), b.loc(npc, 1300, Y + 550), 1500, Y + 500), None, 1700, Y + 500, db='450.0'), 1900, Y + 400)
bf = b.branch(b.b2('BooleanAND', near, b.bnot(g('NearShop', BOOL, 1900, Y + 550), 2100, Y + 550), 2300, Y + 500), 1200, Y, tag='IfOffer')
G.link(fn, 'then', bf, 'execute')
offer = b.concat(b.concat(b.concat(None, b.istr(g('Count', INT, 1300, Y - 500), 1500, Y - 500), 1700, Y - 550,
                                   da='[M] Recruit a medic: 150 gold. Medics heal your soldiers and you, and never fight.  ('), None, 1900, Y - 550, db='/'),
                 b.istr(g('MaxMedics', it('v', default='4'), 1900, Y - 400), 2100, Y - 400), 2300, Y - 500)
offer = b.concat(offer, None, 2500, Y - 500, db=')')
nc, pn = b.notice('', 1500, Y - 200, text_src=offer); G.link(bf, 'then', nc, 'execute')
sns = b.set('NearShop', BOOL, near, 2000, Y)
for src, pin in ((bf, 'else'), (pn, 'then'), (nc, 'CastFailed')): G.link(src, pin, sns, 'execute')
# MedKeys: M at the barracks
Y = 1800
b.event('MedKeys', [], 0, Y)
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='M'), bo('ReturnValue', out=True, default='false')], 200, Y + 300, target=b.pc(0, Y + 300), pure=True, const=True, tag='KeyM')
press = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('MWas', BOOL, 300, Y + 450), 500, Y + 450), 700, Y + 400), g('NearShop', BOOL, 700, Y + 550), 900, Y + 450)
smw = b.set('MWas', BOOL, (down, 'ReturnValue'), 300, Y); G.link('MedKeys', 'then', smw, 'execute')
bp_ = b.branch(press, 600, Y, tag='IfM'); G.link(smw, 'then', bp_, 'execute')
bfull = b.branch(b.icmp('GreaterEqual_IntInt', g('Count', INT, 700, Y + 300), g('MaxMedics', it('v', default='4'), 700, Y + 400), 900, Y + 350), 800, Y, tag='IfFull')
G.link(bp_, 'then', bfull, 'execute')
nfu, _ = b.notice('You already have all the medics the barracks can train.', 1100, Y - 300); G.link(bfull, 'then', nfu, 'execute')
zc, zh = b.hud_cast(ZHUDC, 'BP Zombie HUD', 1100, Y); G.link(bfull, 'else', zc, 'execute')
gold = lambda x, y: b.getm('Gold', ZHUDC, INT, zh, x, y)
price = lambda x, y: g('Price', it('v', default='150'), x, y)
bg = b.branch(b.icmp('GreaterEqual_IntInt', gold(1300, Y + 300), price(1300, Y + 400), 1500, Y + 350), 1400, Y, tag='IfGold'); G.link(zc, 'then', bg, 'execute')
nng, _ = b.notice('Not enough gold: a medic costs 150.', 1700, Y + 300); G.link(bg, 'else', nng, 'execute')
pay = b.setm('Gold', ZHUDC, INT, b.i2('Subtract_IntInt', gold(1600, Y - 100), price(1600, Y), 1800, Y - 50), zh, 1700, Y - 300); G.link(bg, 'then', pay, 'execute')
fn2 = b.actor_of_(P_NPC, NPCC, 2000, Y - 300); G.link(pay, 'then', fn2, 'execute')
spos = b.v2('Add_VectorVector', b.loc((fn2, 'ReturnValue'), 2100, Y), None, 2300, Y, db='150.000000,150.000000,100.000000')
sp = spawn(b, P_MED, MEDC, transform(b, spos, 2500, Y), 2300, Y - 300); G.link(fn2, 'then', sp, 'execute')
nok, _ = b.notice('A medic joins your army (-150 gold).', 2700, Y - 300); G.link(sp, 'then', nok, 'execute')
# DrawMedics(Hud, SizeX, SizeY)
Y = 2800
b.event('DrawMedics', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, Y)
bh = b.branch(b.icmp('Greater_IntInt', g('Count', INT, 200, Y + 300), None, 400, Y + 300, db='0'), 400, Y, tag='IfMedics'); G.link('DrawMedics', 'then', bh, 'execute')
sc = b.d2('Divide_DoubleDouble', b.i2d(('DrawMedics', 'SizeY'), 300, Y + 500), None, 500, Y + 500, db='1080.0')
txt = b.concat(b.concat(b.concat(None, b.istr(g('Count', INT, 500, Y + 600), 700, Y + 600), 900, Y + 600, da='MEDICS   '), None, 1100, Y + 600, db=' / '),
               b.istr(g('MaxMedics', it('v', default='4'), 1100, Y + 700), 1300, Y + 700), 1500, Y + 650)
dt = b.call(HUDC, 'DrawText', [S('Text'), st('TextColor', LC, default=col(0.78, 0.95, 0.80, 1.0)), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT),
            F('Scale', '1.0'), bo('bScalePosition', default='false')], 900, Y, target=('DrawMedics', 'Hud'), tag='DrawMedicsLine')
b.wire(txt, dt, 'Text'); b.wire(b.d2('Multiply_DoubleDouble', b.i2d(('DrawMedics', 'SizeX'), 600, Y + 800), None, 800, Y + 800, db='0.015'), dt, 'ScreenX')
b.wire(b.d2('Multiply_DoubleDouble', b.i2d(('DrawMedics', 'SizeY'), 600, Y + 900), None, 800, Y + 900, db='0.205'), dt, 'ScreenY')
b.wire(b.d2('Multiply_DoubleDouble', sc, None, 800, Y + 1000, db='0.30'), dt, 'Scale')
G.link(bh, 'then', dt, 'execute')
write(G, 'BPC_Medics_graph.txt')
VARS_C = [('Count', 'int', '0', 'medics alive (counted every second)'), ('MaxMedics', 'int', '4', 'barracks limit'), ('Price', 'int', '150', 'gold per medic'),
          ('NearShop', 'bool', 'false', 'hero at the barracks (offer shown)'), ('MWas', 'bool', 'false', 'M held last check')]

# ================================================================================================= BP_Medic
G = Graph(); b = BM(G, 'me')
g = b.get
event_override(G, 'BP', ACT, 'ReceiveBeginPlay', [], 0, 0)
mesh = b.getm('Mesh', CHARC, OBJV(SKEL), b.self_node(100, 300), 300, 300)
last = ('BP', 'then'); X = 300
for tag, socks in (('MedicSatchel', ('spine_03', 'Spine2')), ('MedicArmband', ('upperarm_l', 'LeftArm'))):
    fc = b.call_self('GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.StaticMeshComponent'), NAME_('Tag', tag), arr(ob('ReturnValue', SMC, out=True))],
                     X, 500, ACT, pure=True, const=True, tag='Find' + tag)
    part = b.item((fc, 'ReturnValue'), ob('v', SMC), None, X + 250, 500)
    ex_ = b.call(SCENE, 'DoesSocketExist', [NAME_('InSocketName', socks[0]), bo('ReturnValue', out=True, default='false')], X + 250, 700, target=mesh, pure=True, const=True, tag='HasSocket')
    sock = b.math('SelectName', [(NAME_('A', socks[0]), None), (NAME_('B', socks[1]), None), (bo('bPickA', default='false'), (ex_, 'ReturnValue'))],
                  {'name': 'ReturnValue', 'cat': 'name', 'out': True}, X + 450, 700)
    bv = b.branch(b.valid(part, X + 450, 500), X + 300, 0, tag='If' + tag)
    at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), NAME_('SocketName', 'None'), RULE('LocationRule'), RULE('RotationRule'), RULE('ScaleRule'),
                bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], X + 600, -200, target=part, tag='Attach' + tag)
    b.wire(mesh, at, 'Parent'); b.wire(sock, at, 'SocketName')
    G.link(last[0], last[1], bv, 'execute'); G.link(bv, 'then', at, 'execute')
    mg = b.seq(b.name('After' + tag), 1, X + 900, 0); G.link(bv, 'else', mg, 'execute'); G.link(at, 'then', mg, 'execute')
    last = (mg, 'then_0'); X += 1300
fl_ = b.call_self('GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.TextRenderComponent'), NAME_('Tag', 'HealFX'), arr(ob('ReturnValue', TEXTR, out=True))],
                  X, 500, ACT, pure=True, const=True, tag='FindHealFX')
sfx = b.set('HealFX', OBJV(TEXTR), b.item((fl_, 'ReturnValue'), ob('v', TEXTR), None, X + 250, 500), X + 200, 0)
G.link(last[0], last[1], sfx, 'execute')
tm = b.timer_ev('Think', '0.5', X + 500, 0); G.link(sfx, 'then', tm, 'execute')

# ---- Think
Y = 1200
b.event('Think', [], 0, Y)
seq = b.seq('ThinkSeq', 3, 200, Y); G.link('Think', 'then', seq, 'execute')
heroh = b.hero(200, Y + 2400)
# then_0: danger -> run to the hero
gz = b.getall('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', ZOMBIE, 500, Y); G.link(seq, 'then_0', gz, 'execute')
sd = b.set('Danger', BOOL, None, 850, Y); G.link(gz, 'then', sd, 'execute')
fe = b.foreach(ZOMBIE, 1100, Y); G.link(sd, 'then', fe, 'Exec'); b.wire((gz, 'OutActors'), fe, 'Array')
cl = b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(1100, Y + 400), b.loc((fe, 'Array Element'), 1100, Y + 500), 1300, Y + 450), None, 1500, Y + 450, db='600.0')
bc = b.branch(cl, 1400, Y, tag='IfClose'); G.link(fe, 'LoopBody', bc, 'execute')
sdt = b.set('Danger', bo('v', default='true'), None, 1700, Y - 200); G.link(bc, 'then', sdt, 'execute')
# then_1: pick the most wounded patient in range (soldiers + the hero)
X = 500; Y1 = Y + 1200
s1 = b.set('Patient', OBJV(ACT), None, X, Y1); s2 = b.set('Worst', DBL, None, X + 250, Y1); s3 = b.set('PatientIsHero', BOOL, None, X + 500, Y1)
G.link(seq, 'then_1', s1, 'execute'); b.chain(s1, s2, s3)
gs = b.getall(P_SOLDIER, SOLDIER, X + 750, Y1); G.link(s3, 'then', gs, 'execute')
fs = b.foreach(SOLDIER, X + 1100, Y1); G.link(gs, 'then', fs, 'Exec'); b.wire((gs, 'OutActors'), fs, 'Array')
el = (fs, 'Array Element')
stv = b.brk(b.relloc(b.getm('State', SOLDIER, OBJV(SCENE), el, X + 1100, Y1 + 400), X + 1300, Y1 + 400), X + 1500, Y1 + 400)
hp, alive = stv['X'], b.dcmp('Less_DoubleDouble', stv['Z'], None, X + 1700, Y1 + 500, db='0.5')
# remembered max per soldier (parallel arrays Known / KnownMax); the highest HP seen is his max
fi = b.name('FindKnown')
G.node(fi, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'bIsConstFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Find")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'object', 'obj': ACT, 'container': 'Array', 'ref': True},
        {'name': 'ItemToFind', 'cat': 'object', 'obj': ACT, 'ref': True}, it('ReturnValue', out=True, default='0')], X + 1700, Y1 + 700)
b.wire(g('Known', arr(OBJV(ACT)), X + 1500, Y1 + 700), fi, 'TargetArray'); b.wire(el, fi, 'ItemToFind')
known = b.icmp('GreaterEqual_IntInt', (fi, 'ReturnValue'), None, X + 1900, Y1 + 700, db='0')
bk = b.branch(known, X + 1400, Y1, tag='IfKnown'); G.link(fs, 'LoopBody', bk, 'execute')
ak = b.aadd('Known', OBJV(ACT), el, X + 1700, Y1 - 300); am = b.aadd('KnownMax', DBL, hp, X + 2000, Y1 - 300)
G.link(bk, 'else', ak, 'execute'); G.link(ak, 'then', am, 'execute')
kmax = b.aget('KnownMax', DBL, (fi, 'ReturnValue'), X + 1900, Y1 + 900)
upd = b.aset('KnownMax', DBL, (fi, 'ReturnValue'), b.math('FMax', [(D('A', default='0.0'), kmax), (D('B', default='0.0'), hp)], D('ReturnValue', out=True), X + 2100, Y1 + 900),
             X + 1700, Y1 + 100)
G.link(bk, 'then', upd, 'execute')
mg1 = b.seq('Remembered', 1, X + 2400, Y1); G.link(am, 'then', mg1, 'execute'); G.link(upd, 'then', mg1, 'execute')
wound = b.sub(kmax, hp, X + 2300, Y1 + 1000)
inr = b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 2300, Y1 + 1150), b.loc(el, X + 2300, Y1 + 1250), X + 2500, Y1 + 1200), None, X + 2700, Y1 + 1200, db='2500.0')
better = b.b2('BooleanAND', b.b2('BooleanAND', alive, inr, X + 2900, Y1 + 1100),
              b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', wound, None, X + 2700, Y1 + 1000, db='2.0'),
                   b.dcmp('Greater_DoubleDouble', wound, g('Worst', DBL, X + 2700, Y1 + 900), X + 2900, Y1 + 950), X + 3100, Y1 + 1000), X + 3300, Y1 + 1050)
bb = b.branch(better, X + 2700, Y1, tag='IfWorse'); G.link(mg1, 'then_0', bb, 'execute')
p1 = b.set('Patient', OBJV(ACT), el, X + 3000, Y1 - 200); p2 = b.set('Worst', DBL, wound, X + 3250, Y1 - 200); p3 = b.set('PatientMax', DBL, kmax, X + 3500, Y1 - 200)
G.link(bb, 'then', p1, 'execute'); b.chain(p1, p2, p3)
# the hero
hcast = b.name('AsHeroPC'); cast(G, hcast, HEROC, 'AsBP Third Person Character', X + 3800, Y1); b.wire(heroh, hcast, 'Object'); G.link(fs, 'Completed', hcast, 'execute')
hh = (hcast, 'AsBP Third Person Character')
dmg = b.getm('DamageTaken', HEROC, DBL, hh, X + 4000, Y1 + 400)
hin = b.dcmp('Less_DoubleDouble', b.dist2d(b.myloc(X + 4000, Y1 + 550), b.loc(hh, X + 4000, Y1 + 650), X + 4200, Y1 + 600), None, X + 4400, Y1 + 600, db='2500.0')
hb = b.b2('BooleanAND', hin, b.dcmp('Greater_DoubleDouble', dmg, b.math('FMax', [(D('A', default='2.0'), None), (D('B', default='0.0'), g('Worst', DBL, X + 4200, Y1 + 800))],
          D('ReturnValue', out=True), X + 4400, Y1 + 800), X + 4600, Y1 + 700), X + 4800, Y1 + 650)
bhb = b.branch(hb, X + 4200, Y1, tag='IfHeroWorse'); G.link(hcast, 'then', bhb, 'execute')
h1 = b.set('Patient', OBJV(ACT), hh, X + 4500, Y1 - 200); h2 = b.set('PatientIsHero', bo('v', default='true'), None, X + 4750, Y1 - 200)
G.link(bhb, 'then', h1, 'execute'); G.link(h1, 'then', h2, 'execute')
# then_2: act
X = 500; Y2 = Y + 3200
heal_on = lambda on, x, y: b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='true' if on else 'false'), bo('bPropagateToChildren', default='false')], x, y,
                                  target=g('HealFX', OBJV(TEXTR), x - 150, y + 200), tag='HealFX' + ('On' if on else 'Off'))
off0 = heal_on(False, X, Y2); G.link(seq, 'then_2', off0, 'execute')
bd = b.branch(g('Danger', BOOL, X + 200, Y2 + 300), X + 300, Y2, tag='IfDanger'); G.link(off0, 'then', bd, 'execute')
run = b.move_to(b.loc(heroh, X + 400, Y2 - 300), X + 600, Y2 - 400); G.link(bd, 'then', run, 'execute')
pat = lambda x, y: g('Patient', OBJV(ACT), x, y)
bpv = b.branch(b.valid(pat(X + 600, Y2 + 300), X + 750, Y2 + 300), X + 700, Y2, tag='IfPatient'); G.link(bd, 'else', bpv, 'execute')
follow = b.move_to(b.v2('Subtract_VectorVector', b.loc(heroh, X + 800, Y2 + 600),
                        b.math('Multiply_VectorFloat', [(V('A'), (b.call(ACT, 'GetActorForwardVector', [V('ReturnValue', out=True)], X + 800, Y2 + 750, target=heroh, pure=True, const=True,
                                                                     tag='HeroFwd'), 'ReturnValue')), (D('B', default='400.0'), None)], V('ReturnValue', out=True), X + 1000, Y2 + 750), X + 1200, Y2 + 650),
                   X + 1000, Y2 + 300)
G.link(bpv, 'else', follow, 'execute')
dp = b.dist2d(b.myloc(X + 900, Y2 - 100), b.loc(pat(X + 900, Y2), X + 1100, Y2), X + 1300, Y2 - 50)
bn = b.branch(b.dcmp('Less_DoubleDouble', dp, None, X + 1500, Y2 - 50, db='250.0'), X + 1100, Y2 - 300, tag='IfAtPatient'); G.link(bpv, 'then', bn, 'execute')
go = b.move_to(b.loc(pat(X + 1300, Y2 + 100), X + 1500, Y2 + 100), X + 1500, Y2 - 100); G.link(bn, 'else', go, 'execute')
stp = b.call(CTRL, 'StopMovement', [], X + 1500, Y2 - 500, target=(b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], X + 1300, Y2 - 400, PAWN, pure=True,
                                                                              const=True, tag='Ctl'), 'ReturnValue'), tag='Stop')
G.link(bn, 'then', stp, 'execute')
on1 = heal_on(True, X + 1800, Y2 - 500); G.link(stp, 'then', on1, 'execute')
bwho = b.branch(g('PatientIsHero', BOOL, X + 2000, Y2 - 300), X + 2100, Y2 - 500, tag='IfHero'); G.link(on1, 'then', bwho, 'execute')
hcast2 = b.name('AsHeroHeal'); cast(G, hcast2, HEROC, 'AsBP Third Person Character', X + 2400, Y2 - 700); b.wire(pat(X + 2250, Y2 - 600), hcast2, 'Object')
G.link(bwho, 'then', hcast2, 'execute')
hh2 = (hcast2, 'AsBP Third Person Character')
hset = b.setm('DamageTaken', HEROC, DBL, b.math('FMax', [(D('A', default='0.0'), b.sub(b.getm('DamageTaken', HEROC, DBL, hh2, X + 2600, Y2 - 500), g('HealPerTick', DBL, X + 2600, Y2 - 400),
              X + 2800, Y2 - 450)), (D('B', default='0.0'), None)], D('ReturnValue', out=True), X + 3000, Y2 - 450), hh2, X + 2800, Y2 - 700)
G.link(hcast2, 'then', hset, 'execute')
scast = b.name('AsSoldierHeal'); cast(G, scast, SOLDIER, 'AsBP Soldier Sword', X + 2400, Y2 - 300); b.wire(pat(X + 2250, Y2 - 200), scast, 'Object')
G.link(bwho, 'else', scast, 'execute')
stc = b.getm('State', SOLDIER, OBJV(SCENE), (scast, 'AsBP Soldier Sword'), X + 2600, Y2 - 100)
sv = b.brk(b.relloc(stc, X + 2800, Y2 - 100), X + 3000, Y2 - 100)
nhp = b.math('FMin', [(D('A', default='0.0'), b.add(sv['X'], g('HealPerTick', DBL, X + 3000, Y2), X + 3200, Y2 - 50)), (D('B', default='0.0'), g('PatientMax', DBL, X + 3200, Y2 + 100))],
             D('ReturnValue', out=True), X + 3400, Y2)
srl = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
             X + 3000, Y2 - 300, target=stc, tag='HealSoldier')
b.wire(b.vec(nhp, sv['Y'], sv['Z'], X + 3600, Y2), srl, 'NewLocation'); G.link(scast, 'then', srl, 'execute')
write(G, 'BP_Medic_graph.txt')
VARS_M = [('Danger', 'bool', 'false', 'a zombie within 6 m'), ('Patient', 'obj:Actor', '', 'who he heals'), ('PatientIsHero', 'bool', 'false', ''),
          ('Worst', 'real', '0.0', 'scratch: biggest wound found'), ('PatientMax', 'real', '0.0', "the soldier's remembered max HP"),
          ('HealPerTick', 'real', '4.0', 'HP per 0.5 s (8 HP/s)'), ('Known', 'arr:Actor', '', 'soldiers seen'), ('KnownMax', 'arrreal', '', 'their highest HP seen'),
          ('HealFX', 'obj:TextRenderComponent', '', '"+ HEAL" over his head')]

# ================================================================================================= BPC_MotionFX: draw the medics line
G = Graph(); b = BM(G, 'mh')
own = b.name('Owner'); callfn(G, own, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=300, self_hidden=True)
fcm = b.call(ACT, 'GetComponentByClass', [{'name': 'ComponentClass', 'cat': 'class', 'obj': CLS('ActorComponent'), 'dobj': cpath(P_MC)}, ob('ReturnValue', MCC, out=True)],
             200, 300, target=(own, 'ReturnValue'), pure=True, const=True, tag='FindMedics')
bv = b.branch(b.valid((fcm, 'ReturnValue'), 400, 300), 300, 0, tag='MedicsIfValid')
dm = b.call(MCC, 'DrawMedics', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 600, 0, target=(fcm, 'ReturnValue'), tag='MedicsDraw')
G.link(bv, 'then', dm, 'execute')
write(G, 'MotionFX_Medics_graph.txt')
json.dump({'blueprint': 'BPC_MotionFX', '_apply': 'after the #283 map hook (manifest_motionfx_map.json) is in; live = a fresh export of BPC_MotionFX',
           'pastes': [{'file': 'MotionFX_Medics_graph.txt', 'offset': [900, -1200]}],
           'rewires': [{'from': 'mmMapDraw5.then', 'to': bv + '.execute'}, {'from': 'mmMapIfValid4.else', 'to': bv + '.execute'},
                       {'from': 'DrawReveal.Hud', 'to': dm + '.Hud'}, {'from': 'DrawReveal.SizeX', 'to': dm + '.SizeX'}, {'from': 'DrawReveal.SizeY', 'to': dm + '.SizeY'}]},
          open(os.path.join(HERE, 'manifest_motionfx_medics.json'), 'w'), indent=1)


def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind == 'arrreal': return 'PinCategory="real",PinSubCategory="double",ContainerType=Array'
    if kind in ('int', 'bool'): return 'PinCategory="%s"' % kind
    if kind.startswith('arr:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'",ContainerType=Array' % kind[4:]
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda bp, n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'medics185/%s/%s' % (bp, n)).hex.upper(), vt(k), n, d)
out = ['# #185 Medics - paste one line at a time on the VARIABLES header of My Blueprint, then Compile', '', '# ---- BPC_Medics']
out += [bpv('BPC_Medics', *v[:3]) for v in VARS_C] + ['', '# ---- BP_Medic'] + [bpv('BP_Medic', *v[:3]) for v in VARS_M]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('\n'.join(out) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #185 variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Blueprint | Name | Default | Meaning |\n|---|---|---|---|\n')
    for bp, vs in (('BPC_Medics', VARS_C), ('BP_Medic', VARS_M)):
        for n, _k, d, m in vs: f.write('| %s | %s | %s | %s |\n' % (bp, n, d or '-', m))
print('BPVar lines: %d + %d' % (len(VARS_C), len(VARS_M)))
