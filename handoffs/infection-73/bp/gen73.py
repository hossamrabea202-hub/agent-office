# #73 Infection: generates the Blueprint pastes (laptop2, 2026-10-29). Run with any Python 3:
#   python gen73.py  ->  BPC_Infection_graph.txt     (EventGraph of the new component BPC_Infection, on the hero as "Infection")
#                        Hero_Infection_graph.txt    (BP_ThirdPersonCharacter: damage x DefMul after #121's ObsDmg, regen gate)
#                        NoticeHUD_Infection_graph.txt (BP_NoticeHUD DrawHUD: green bar, "YOU HAVE BEEN INFECTED", 3 explainer cards)
# Built with the Master's node kit (tools/master/t81/kit.py) the same way as #96's gen96.py, against the 10-28 exports
# in exports/laptop2/gameplay (hero, BP_ZombieHUD) and exports/laptop2/prompt68 (BP_NoticeHUD, BP_SkillTreeHUD).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'master', 't81'))
from kit import *

OBJ = '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"'
ACT, COMP, HUDC, PCC = CLS('Actor'), CLS('ActorComponent'), CLS('HUD'), CLS('PlayerController')
GS, MATL, SYS, MATH = CLS('GameplayStatics'), CLS('KismetMaterialLibrary'), CLS('KismetSystemLibrary'), CLS('KismetMathLibrary')
MIDC, MPCC, MATI = CLS('MaterialInstanceDynamic'), CLS('MaterialParameterCollection'), CLS('MaterialInterface')
LC, V2 = STRUCT('LinearColor'), STRUCT('Vector2D')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
BLEND = '"/Script/CoreUObject.Enum\'/Script/Engine.EBlendMode\'"'
INFC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Infection', 'BPC_Infection')
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')
NOTICE = BPC('/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD', 'BP_NoticeHUD')
SAVE = BPC('/Game/CastleDefender/Gameplay/Save/BP_CastleSave', 'BP_CastleSave')
SAVE_CLS = '/Game/CastleDefender/Gameplay/Save/BP_CastleSave.BP_CastleSave_C'
MPC_CTRL = '/Game/CastleDefender/UI/Controls/MPC_Controls.MPC_Controls'
HINT = '/Game/CastleDefender/UI/Hints/M_HintCard.M_HintCard'
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
T_FILL, T_FRAME = '/Game/CastleDefender/UI/T_HP_Fill.T_HP_Fill', '/Game/CastleDefender/UI/T_HP_Frame.T_HP_Frame'
SLOT = 'CastleSaveInfection'
TWO_PI = '6.2831853'

def D(name, out=False, default=None): return fl(name, out=out, default=default, sub='double')
def S(name, out=False, default=None): return {'name': name, 'cat': 'string', 'out': out, 'default': default}
def E(name, enum, default): return {'name': name, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'%s\'"' % enum, 'default': default}
WC = lambda: ob('WorldContextObject', OBJ, hidden=True)
DBL, BOOL, INT = D('v', default='0.0'), bo('v', default='false'), it('v', default='0')

class B:
    """builder on top of kit.Graph (gen96 + gen31_68 helpers): value handles are (node, pin)."""
    def __init__(s, G, p): s.G, s.p, s.n = G, p, 0
    def name(s, t): s.n += 1; return '%s%s%d' % (s.p, t, s.n)
    def wire(s, src, node, pin):
        if src is not None: s.G.link(src[0], src[1], node, pin)
    def m(s, member, ins, out, x, y, tag=None):
        n = s.name(tag or member[:8]); mathfn(s.G, n, member, [p for p, _ in ins] + [out], x, y)
        for p, src in ins: s.wire(src, n, p['name'])
        return (n, out['name'])
    def lib(s, cls, member, ins, outs, x, y, tag=None):
        n = s.name(tag or member[:8])
        callfn(s.G, n, cls, member, [p for p, _ in ins] + outs, pure=True, x=x, y=y, self_hidden=True)
        for p, src in ins: s.wire(src, n, p['name'])
        return n
    # math
    def d2(s, member, a, b, x, y, da='0.0', db='0.0'):
        return s.m(member, [(D('A', default=da), a), (D('B', default=db), b)], D('ReturnValue', out=True), x, y)
    def dc(s, member, a, b, x, y, da='0.0', db='0.0'):
        return s.m(member, [(D('A', default=da), a), (D('B', default=db), b)], bo('ReturnValue', out=True), x, y)
    def i2(s, member, a, b, x, y, da='0', db='0'):
        return s.m(member, [(it('A', default=da), a), (it('B', default=db), b)], it('ReturnValue', out=True), x, y)
    def ic(s, member, a, b, x, y, da='0', db='0'):
        return s.m(member, [(it('A', default=da), a), (it('B', default=db), b)], bo('ReturnValue', out=True), x, y)
    def b2(s, member, a, b, x, y):
        return s.m(member, [(bo('A', default='false'), a), (bo('B', default='false'), b)], bo('ReturnValue', out=True), x, y)
    def bnot(s, a, x, y): return s.m('Not_PreBool', [(bo('A', default='false'), a)], bo('ReturnValue', out=True), x, y)
    def b2d(s, a, x, y): return s.m('Conv_BoolToDouble', [(bo('InBool', default='false'), a)], D('ReturnValue', out=True), x, y)
    def i2d(s, a, x, y): return s.m('Conv_IntToDouble', [(it('InInt', default='0'), a)], D('ReturnValue', out=True), x, y)
    def sat(s, v, x, y): return s.m('FClamp', [(D('Value', default='0.0'), v), (D('Min', default='0.0'), None), (D('Max', default='1.0'), None)], D('ReturnValue', out=True), x, y)
    def sel(s, a, b, pick, x, y, da='0.0', db='0.0'):
        return s.m('SelectFloat', [(D('A', default=da), a), (D('B', default=db), b), (bo('bPickA', default='false'), pick)], D('ReturnValue', out=True), x, y)
    def seli(s, a, b, pick, x, y, da='0', db='0'):
        return s.m('SelectInt', [(it('A', default=da), a), (it('B', default=db), b), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)
    def sels(s, a, b, pick, x, y, da='', db=''):
        return s.m('SelectString', [(S('A', default=da), a), (S('B', default=db), b), (bo('bPickA', default='false'), pick)], S('ReturnValue', out=True), x, y)
    def sin(s, a, x, y): return s.m('Sin', [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
    def color(s, r, g, b_, a, x, y, dr='0.0', dg='0.0', db='0.0', da='1.0'):
        n = s.name('Col'); mathfn(s.G, n, 'MakeColor', [fl('R', default=dr), fl('G', default=dg), fl('B', default=db), fl('A', default=da), st('ReturnValue', LC, out=True)], x, y)
        for c, src in zip('RGBA', (r, g, b_, a)): s.wire(src, n, c)
        return (n, 'ReturnValue')
    # time
    def now(s, x, y): return (s.lib(GS, 'GetTimeSeconds', [(WC(), None)], [D('ReturnValue', out=True)], x, y, 'Now'), 'ReturnValue')
    def realnow(s, x, y): return (s.lib(GS, 'GetRealTimeSeconds', [(WC(), None)], [D('ReturnValue', out=True)], x, y, 'RealNow'), 'ReturnValue')
    # variables on self
    def get(s, var, pin, x, y):
        n = s.name('Get' + var); varget(s.G, n, None, var, None, dict(pin, name=var), x, y, self_ctx=True); return (n, var)
    def set(s, var, pin, src, x, y, default=None):
        n = s.name('Set' + var); varset(s.G, n, None, var, None, dict(pin, name=var, default=default if default is not None else pin.get('default')), x, y, self_ctx=True)
        s.wire(src, n, var); return n
    # variables on another object (target pin wired from `tgt`)
    def oget(s, cls, var, pin, tgt, x, y):
        n = s.name('Get' + var); varget(s.G, n, cls, var, cls, dict(pin, name=var), x, y); s.wire(tgt, n, 'self'); return (n, var)
    def oset(s, cls, var, pin, src, tgt, x, y):
        n = s.name('Set' + var); varset(s.G, n, cls, var, cls, dict(pin, name=var), x, y); s.wire(src, n, var); s.wire(tgt, n, 'self'); return n
    # calls
    def call_self(s, event, x, y, pins=()):
        n = s.name('Call' + event)
        s.G.node(n, 'K2Node_CallFunction', ['FunctionReference=(MemberName="%s",bSelfContext=True)' % event],
                 [ex(), ex('then', True), selfpin(INFC, hidden=True)] + list(pins), x, y)
        return n
    def call_on(s, cls, member, tgt, x, y, pins=()):
        n = s.name('Call' + member)
        s.G.node(n, 'K2Node_CallFunction', ['FunctionReference=(MemberParent=%s,MemberName="%s")' % (cls, member)],
                 [ex(), ex('then', True), selfpin(cls)] + list(pins), x, y)
        s.wire(tgt, n, 'self'); return n
    def hud(s, member, pins, x, y, pure=False):
        n = s.name(member[:8])
        props = (['bIsPureFunc=True'] if pure else []) + ['FunctionReference=(MemberName="%s",bSelfContext=True)' % member]
        s.G.node(n, 'K2Node_CallFunction', props, ([] if pure else [ex(), ex('then', True)]) + [selfpin(HUDC, hidden=True)] + pins, x, y)
        return n
    def paused_set(s, on, x, y):
        n = s.name('Pause')
        callfn(s.G, n, GS, 'SetGamePaused', [WC(), bo('bPaused', default='true' if on else 'false'), bo('ReturnValue', out=True, default='false')], x=x, y=y, self_hidden=True)
        return n
    def mpc_scalar(s, param, x, y):
        n = s.name('Get' + param)
        callfn(s.G, n, MATL, 'GetScalarParameterValue', [WC(), dict(ob('Collection', MPCC), dobj=MPC_CTRL),
               {'name': 'ParameterName', 'cat': 'name', 'default': param}, fl('ReturnValue', out=True, default='0.0')], x=x, y=y, self_hidden=True)
        return n
    def event(s, name, params, x, y):
        props = ['CustomFunctionName="%s"' % name]
        for p in params:
            t = 'PinCategory="%s"' % p['cat'] + (',PinSubCategory="%s"' % p['sub'] if p.get('sub') else '') + \
                (',PinSubCategoryObject=%s' % p['obj'] if p.get('obj') and p['obj'] != 'None' else '')
            props.append('CustomProperties UserDefinedPin (PinName="%s",PinType=(%s),DesiredPinDirection=EGPD_Output)' % (p['name'], t))
        s.G.node(name, 'K2Node_CustomEvent', props, [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '()'}, ex('then', True)]
                 + [dict(p, out=True, default=None) for p in params], x, y)
        return name
    def br(s, cond, x, y, name=None):
        n = name or s.name('If'); branch(s.G, n, x, y); s.wire(cond, n, 'Condition'); return n
    def cast_(s, target, outname, obj, x, y):
        n = s.name('As'); cast(s.G, n, target, outname, x, y); s.wire(obj, n, 'Object'); return n
    def chain(s, *ns):
        for a, b in zip(ns, ns[1:]):
            s.G.link(a[0] if isinstance(a, tuple) else a, a[1] if isinstance(a, tuple) else 'then', b, 'execute')
    def to(s, src, node):
        """exec src (node name -> 'then', or (node, pin)) into node.execute"""
        s.G.link(src[0] if isinstance(src, tuple) else src, src[1] if isinstance(src, tuple) else 'then', node, 'execute')

# =====================================================================================================================
# 1. BPC_Infection: ActorComponent on the hero ("Infection"). All #73 state lives here; the HUD only reads it.
#   Events: Infect()  NextCard()  BuyAntidote()  Refresh()  LoadState(WasInfected, Bought, Seen)
#   OnOwnerHit (bound to the hero's OnTakeAnyDamage): infects below InfectBelow x MaxHP when the causer has tag Infects
#   Tick: save/load (same MPC_Controls SaveT/SaveKind trigger as the armoury save, own slot CastleSaveInfection) + drain
# =====================================================================================================================
G = Graph(); b = B(G, 'i')

# ---- BeginPlay: bind OnTakeAnyDamage, make the hint-card MID, remember SaveT (no save/load at start), Refresh ----
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
callfn(G, 'Owner1', COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=200, self_hidden=True)
G.node('Bind', 'K2Node_AddDelegate', ['DelegateReference=(MemberParent=%s,MemberName="OnTakeAnyDamage")' % ACT],
       [ex(), ex('then', True), selfpin(ACT), {'name': 'Delegate', 'cat': 'delegate', 'mref': '()'}], 300, 0)
G.link('BP', 'then', 'Bind', 'execute'); G.link('Owner1', 'ReturnValue', 'Bind', 'self')
mk = b.name('MakeMID')
callfn(G, mk, MATL, 'CreateDynamicMaterialInstance', [WC(), dict(ob('Parent', MATI), dobj=HINT),
       {'name': 'OptionalName', 'cat': 'name', 'default': 'None'}, E('CreationFlags', '/Script/Engine.EMIDCreationFlags', 'None'), ob('ReturnValue', MIDC, out=True)],
       x=600, y=0, self_hidden=True)
s_mid = b.set('CardMID', ob('v', MIDC), (mk, 'ReturnValue'), 900, 0)
g_t = b.mpc_scalar('SaveT', 1150, 0)
s_t = b.set('LastSaveT', DBL, (g_t, 'ReturnValue'), 1450, 0)
b.chain('Bind', mk, s_mid, g_t, s_t, b.call_self('Refresh', 1700, 0))

# ---- OnOwnerHit: infect when not infected, the causer has tag Infects, HP < InfectBelow x MaxHP, alive, 60 s after a cure ----
Y = 600
b.event('OnOwnerHit', [ob('DamagedActor', ACT), fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CLS('Controller')), ob('DamageCauser', ACT)], 0, Y)
G.link('OnOwnerHit', 'OutputDelegate', 'Bind', 'Delegate')
causer = ('OnOwnerHit', 'DamageCauser')
valid = b.lib(SYS, 'IsValid', [(ob('Object', OBJ), causer)], [bo('ReturnValue', out=True)], 250, Y + 250, 'Valid')
ifv = b.br((valid, 'ReturnValue'), 350, Y); b.to('OnOwnerHit', ifv)
ash = b.cast_(HERO, 'AsHero', ('OnOwnerHit', 'DamagedActor'), 600, Y); b.to((ifv, 'then'), ash)
hero = (ash, 'AsHero')
tag = b.name('HasTag')                   # ActorHasTag's target is a real input: the causer
callfn(G, tag, ACT, 'ActorHasTag', [{'name': 'Tag', 'cat': 'name', 'default': 'Infects'}, bo('ReturnValue', out=True, default='false')], pure=True, x=600, y=Y + 400)
b.wire(causer, tag, 'self')
maxhp = b.get('MaxHP', DBL, 600, Y + 750)
hp = b.d2('Subtract_DoubleDouble', maxhp, b.oget(HERO, 'DamageTaken', DBL, hero, 800, Y + 650), 1000, Y + 700)
low = b.dc('Less_DoubleDouble', hp, b.d2('Multiply_DoubleDouble', maxhp, b.get('InfectBelow', DBL, 800, Y + 900), 1000, Y + 850), 1200, Y + 750)
guard = b.dc('GreaterEqual_DoubleDouble', b.d2('Subtract_DoubleDouble', b.now(800, Y + 1050), b.get('CuredAt', DBL, 800, Y + 1200), 1000, Y + 1100),
             b.get('ReinfectGuard', DBL, 1000, Y + 1250), 1200, Y + 1150)
alive = b.bnot(b.oget(HERO, 'IsDead', BOOL, hero, 1000, Y + 1400), 1200, Y + 1400)
c1 = b.b2('BooleanAND', b.bnot(b.get('Infected', BOOL, 800, Y + 250), 1000, Y + 250), (tag, 'ReturnValue'), 1200, Y + 300)
c2 = b.b2('BooleanAND', low, guard, 1400, Y + 900)
cond = b.b2('BooleanAND', b.b2('BooleanAND', c1, c2, 1600, Y + 600), alive, 1800, Y + 700)
ifc = b.br(cond, 900, Y); b.to((ash, 'then'), ifc)
b.to((ifc, 'then'), b.call_self('Infect', 1200, Y))

def push_notice(text, tier, x, y):
    """Get Player Controller -> Get HUD -> Cast to BP_NoticeHUD -> PushNotice(Text, Tier). Returns (entry node, [exits])."""
    pc = b.lib(GS, 'GetPlayerController', [(WC(), None), (it('PlayerIndex', default='0'), None)], [ob('ReturnValue', PCC, out=True)], x, y + 250, 'PC')
    hud = b.name('GetHUD')
    G.node(hud, 'K2Node_CallFunction', ['bIsPureFunc=True', 'bIsConstFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="GetHUD")' % PCC],
           [selfpin(PCC), ob('ReturnValue', HUDC, out=True)], x + 200, y + 250)
    G.link(pc, 'ReturnValue', hud, 'self')
    cn = b.cast_(NOTICE, 'AsNoticeHUD', (hud, 'ReturnValue'), x + 300, y)
    call = b.call_on(NOTICE, 'PushNotice', (cn, 'AsNoticeHUD'), x + 600, y, pins=[S('Text', default=text), it('Tier', default=str(tier))])
    b.to(cn, call)
    return cn, [(call, 'then'), (cn, 'CastFailed')]

# ---- Infect(): Infected, clock, banner; first time: explainer card 1 + pause ----
Y = 2400
b.event('Infect', [], 0, Y)
s1 = b.set('Infected', BOOL, None, 250, Y, default='true')
s2 = b.set('InfectedAt', DBL, b.now(250, Y + 250), 500, Y)
s3 = b.set('DrainStep', INT, None, 750, Y, default='0')
b.chain('Infect', s1, s2, s3)
pn, exits = push_notice('YOU ARE INFECTED', 1, 1000, Y)
b.to(s3, pn)
ifs = b.br(b.bnot(b.get('InfectSeen', BOOL, 1700, Y + 250), 1900, Y + 250), 1950, Y)
for e in exits: b.to(e, ifs)
e1 = b.set('InfectSeen', BOOL, None, 2200, Y, default='true')
e2 = b.set('ExplainCard', INT, None, 2450, Y, default='1')
e3 = b.set('ExplainT0', DBL, b.realnow(2450, Y + 250), 2700, Y)
e4 = b.paused_set(True, 2950, Y)
ref = b.call_self('Refresh', 3250, Y)
b.chain((ifs, 'then'), e1, e2, e3, e4, ref); b.to((ifs, 'else'), ref)

# ---- NextCard(): called by the HUD on a click. After card 3: close + unpause ----
Y = 3000
b.event('NextCard', [], 0, Y)
card = b.get('ExplainCard', INT, 0, Y + 250)
ifl = b.br(b.ic('GreaterEqual_IntInt', card, None, 200, Y + 250, db='3'), 300, Y); b.to('NextCard', ifl)
n1 = b.set('ExplainCard', INT, None, 600, Y - 150, default='0'); b.to((ifl, 'then'), n1)
b.to(n1, b.paused_set(False, 850, Y - 150))
n2 = b.set('ExplainCard', INT, b.i2('Add_IntInt', card, None, 400, Y + 400, db='1'), 600, Y + 150); b.to((ifl, 'else'), n2)
b.to(n2, b.set('ExplainT0', DBL, b.realnow(650, Y + 400), 850, Y + 150))

# ---- BuyAntidote(): the HUD checks and takes AntidotePrice gold first, then calls this ----
Y = 3700
b.event('BuyAntidote', [], 0, Y)
a1 = b.set('AntidotesBought', INT, b.i2('Add_IntInt', b.get('AntidotesBought', INT, 0, Y + 250), None, 200, Y + 250, db='1'), 300, Y)
a2 = b.set('Infected', BOOL, None, 550, Y, default='false')
a3 = b.set('CuredAt', DBL, b.now(550, Y + 250), 800, Y)
b.chain('BuyAntidote', a1, a2, a3)
pn, exits = push_notice('CURED - the infection is gone', 0, 1050, Y)
b.to(a3, pn)
ref = b.call_self('Refresh', 1800, Y)
for e in exits: b.to(e, ref)

# ---- Refresh(): AntidotePrice = 0 (FREE) for the first, then 1000 + 500 x (bought - 1) ----
Y = 4300
b.event('Refresh', [], 0, Y)
bought = b.get('AntidotesBought', INT, 0, Y + 250)
paid = b.i2('Add_IntInt', b.i2('Multiply_IntInt', b.i2('Subtract_IntInt', bought, None, 200, Y + 350, db='1'), None, 400, Y + 350, db='500'), None, 600, Y + 350, db='1000')
price = b.seli(None, paid, b.ic('EqualEqual_IntInt', bought, None, 400, Y + 200, db='0'), 800, Y + 250, da='0')
b.to('Refresh', b.set('AntidotePrice', INT, price, 300, Y))

# ---- LoadState(WasInfected, Bought, Seen): from the save. The drain clock restarts, the explainer never replays ----
Y = 4800
b.event('LoadState', [bo('WasInfected'), it('Bought'), bo('Seen')], 0, Y)
l1 = b.set('Infected', BOOL, ('LoadState', 'WasInfected'), 350, Y)
l2 = b.set('AntidotesBought', INT, ('LoadState', 'Bought'), 600, Y)
l3 = b.set('InfectSeen', BOOL, ('LoadState', 'Seen'), 850, Y)
l4 = b.set('InfectedAt', DBL, b.now(850, Y + 250), 1100, Y)
l5 = b.set('DrainStep', INT, None, 1350, Y, default='0')
l6 = b.set('CuredAt', DBL, None, 1600, Y, default='-100.0')
b.chain('LoadState', l1, l2, l3, l4, l5, l6, b.call_self('Refresh', 1850, Y))

# ---- Tick: then_0 = save/load watcher, then_1 = drain ----
Y = 5600
G.node('Tick', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveTick")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveTick")' % COMP}, ex('then', True),
        fl('DeltaSeconds', out=True, default='0.0')], 0, Y)
sequence(G, 'TickSeq', 2, 250, Y); b.to('Tick', 'TickSeq')
# save/load: when MPC_Controls.SaveT changes, SaveKind > 1.5 = load, else save (the armoury save's own rule, ASV_1..33)
gT = b.mpc_scalar('SaveT', 500, Y); gK = b.mpc_scalar('SaveKind', 750, Y)
b.to(('TickSeq', 'then_0'), gT); b.to(gT, gK)
moved = b.dc('Greater_DoubleDouble', b.m('Abs', [(D('A', default='0.0'), b.d2('Subtract_DoubleDouble', (gT, 'ReturnValue'), b.get('LastSaveT', DBL, 800, Y + 400), 1000, Y + 350))],
             D('ReturnValue', out=True), 1200, Y + 350), None, 1400, Y + 350, db='0.0005')
ifm = b.br(moved, 1050, Y); b.to(gK, ifm)
st1 = b.set('LastSaveT', DBL, (gT, 'ReturnValue'), 1300, Y); b.to((ifm, 'then'), st1)
ifk = b.br(b.dc('Greater_DoubleDouble', (gK, 'ReturnValue'), None, 1400, Y + 550, db='1.5'), 1550, Y); b.to(st1, ifk)
# load
Y2 = Y - 900
ex_ = b.name('Exists')
callfn(G, ex_, GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], x=1800, y=Y2, self_hidden=True)
b.to((ifk, 'then'), ex_)
ife = b.br((ex_, 'ReturnValue'), 2050, Y2); b.to(ex_, ife)
ld = b.name('Load')
callfn(G, ld, GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', CLS('SaveGame'), out=True)], x=2300, y=Y2, self_hidden=True)
b.to((ife, 'then'), ld)
asl = b.cast_(SAVE, 'AsBP Castle Save', (ld, 'ReturnValue'), 2550, Y2); b.to(ld, asl)
dget = b.oget(SAVE, 'Data', dict(D('v'), container='Array'), (asl, 'AsBP Castle Save'), 2550, Y2 + 300)
items = []
for k in (1, 2, 3):
    n = b.name('Item')
    G.node(n, 'K2Node_GetArrayItem', [], [dict(D('Array'), container='Array'), it('Dimension 1', default=str(k)), dict(D('Output', out=True), ref=True)], 2800, Y2 + 200 + k * 150)
    b.wire(dget, n, 'Array'); items.append((n, 'Output'))
lsv = b.call_self('LoadState', 3200, Y2, pins=[bo('WasInfected', default='false'), it('Bought', default='0'), bo('Seen', default='false')])
b.to(asl, lsv)
b.wire(b.dc('Greater_DoubleDouble', items[0], None, 3000, Y2 + 350, db='0.5'), lsv, 'WasInfected')
b.wire(b.m('Round', [(D('A', default='0.0'), items[1])], it('ReturnValue', out=True), 3000, Y2 + 500), lsv, 'Bought')
b.wire(b.dc('Greater_DoubleDouble', items[2], None, 3000, Y2 + 650, db='0.5'), lsv, 'Seen')
lnew = b.call_self('LoadState', 2300, Y2 + 900, pins=[bo('WasInfected', default='false'), it('Bought', default='0'), bo('Seen', default='false')])
b.to((ife, 'else'), lnew)                  # no save yet = a fresh game
# save: Data = [1.0 (version), Infected, AntidotesBought, InfectSeen]
mko = b.name('NewSave')
callfn(G, mko, GS, 'CreateSaveGameObject', [{'name': 'SaveGameClass', 'cat': 'class', 'obj': CLS('SaveGame'), 'dobj': SAVE_CLS}, ob('ReturnValue', SAVE, out=True)],
       x=1800, y=Y, self_hidden=True)
b.to((ifk, 'else'), mko)
ass = b.cast_(SAVE, 'AsBP Castle Save', (mko, 'ReturnValue'), 2050, Y); b.to(mko, ass)
arr = b.name('Arr')
G.node(arr, 'K2Node_MakeArray', ['NumInputs=4'], [dict(D('Array', out=True), container='Array'), D('[0]', default='1.0'), D('[1]', default='0.0'), D('[2]', default='0.0'), D('[3]', default='0.0')], 2300, Y + 300)
b.wire(b.b2d(b.get('Infected', BOOL, 1900, Y + 400), 2100, Y + 400), arr, '[1]')
b.wire(b.i2d(b.get('AntidotesBought', INT, 1900, Y + 550), 2100, Y + 550), arr, '[2]')
b.wire(b.b2d(b.get('InfectSeen', BOOL, 1900, Y + 700), 2100, Y + 700), arr, '[3]')
sd = b.oset(SAVE, 'Data', dict(D('v'), container='Array'), (arr, 'Array'), (ass, 'AsBP Castle Save'), 2550, Y); b.to(ass, sd)
sv = b.name('Save')
callfn(G, sv, GS, 'SaveGameToSlot', [ob('SaveGameObject', CLS('SaveGame')), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')],
       x=2800, y=Y, self_hidden=True)
b.to(sd, sv); G.link(mko, 'ReturnValue', sv, 'SaveGameObject')
# drain: every DrainEvery s of game time (stops while paused) DamageTaken += DrainPct x MaxHP, never past DrainCap x MaxHP
Y = 7000
ao = b.name('Owner')
callfn(G, ao, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=300, y=Y + 300, self_hidden=True)
ash2 = b.cast_(HERO, 'AsHero', (ao, 'ReturnValue'), 500, Y); b.to(('TickSeq', 'then_1'), ash2)
hero = (ash2, 'AsHero')
step = b.m('FFloor', [(D('A', default='0.0'), b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', b.now(500, Y + 450), b.get('InfectedAt', DBL, 500, Y + 600), 700, Y + 500),
           b.get('DrainEvery', DBL, 700, Y + 650), 900, Y + 550))], it('ReturnValue', out=True), 1100, Y + 550)
due = b.ic('Greater_IntInt', step, b.get('DrainStep', INT, 1100, Y + 700), 1300, Y + 600)
dcond = b.b2('BooleanAND', b.b2('BooleanAND', b.get('Infected', BOOL, 1100, Y + 350), due, 1500, Y + 450),
             b.bnot(b.oget(HERO, 'IsDead', BOOL, hero, 1300, Y + 850), 1500, Y + 850), 1700, Y + 600)
ifd = b.br(dcond, 800, Y); b.to((ash2, 'then'), ifd)
ds = b.set('DrainStep', INT, step, 1100, Y); b.to((ifd, 'then'), ds)
mx = b.get('MaxHP', DBL, 1700, Y + 1000)
dt = b.oget(HERO, 'DamageTaken', DBL, hero, 1700, Y + 1150)
up = b.d2('Add_DoubleDouble', dt, b.d2('Multiply_DoubleDouble', mx, b.get('DrainPct', DBL, 1700, Y + 1300), 1900, Y + 1250), 2100, Y + 1150)
cap = b.d2('Multiply_DoubleDouble', mx, b.get('DrainCap', DBL, 1900, Y + 1450), 2100, Y + 1400)
newdt = b.m('FMax', [(D('A', default='0.0'), dt), (D('B', default='0.0'), b.m('FMin', [(D('A', default='0.0'), up), (D('B', default='0.0'), cap)], D('ReturnValue', out=True), 2300, Y + 1250))],
            D('ReturnValue', out=True), 2500, Y + 1150)
b.to(ds, b.oset(HERO, 'DamageTaken', DBL, newdt, hero, 1400, Y))

open(os.path.join(HERE, 'BPC_Infection_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_Infection: nodes', len(G.nodes), 'links', len(G.links))
COUNTS = {'BPC_Infection_graph.txt': (len(G.nodes), len(G.links))}

# =====================================================================================================================
# 2. Hero paste (BP_ThirdPersonCharacter EventGraph).
#   InfDmg  = ObsDmg.ReturnValue x (Infection.Infected ? Infection.DefMul : 1)     (+50 % DEF = x 1/1.5, after #121's terms)
#   RegenGate = Branch(Infection.Infected): else -> the old regen Set DamageTaken (ZX17); then = no regen (the component drains)
# =====================================================================================================================
G = Graph(); b = B(G, 'h')
comp = b.get('Infection', ob('v', INFC), 0, 0)
inf = b.oget(INFC, 'Infected', BOOL, comp, 250, 0)
dm = b.oget(INFC, 'DefMul', DBL, comp, 250, 150)
mul = b.sel(dm, None, inf, 500, 50, db='1.0')
G.node('InfDmg', 'K2Node_CallFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Multiply_DoubleDouble")' % MATH],
       [selfpin(MATH, hidden=True), D('A', default='0.0'), D('B', default='1.0'), D('ReturnValue', out=True)], 750, 0)
b.wire(mul, 'InfDmg', 'B')
comp2 = b.get('Infection', ob('v', INFC), 0, 500)
inf2 = b.oget(INFC, 'Infected', BOOL, comp2, 250, 500)
b.br(inf2, 500, 450, name='RegenGate')
open(os.path.join(HERE, 'Hero_Infection_graph.txt'), 'w', newline='\r\n').write(G.render())
print('Hero paste: nodes', len(G.nodes), 'links', len(G.links))
COUNTS['Hero_Infection_graph.txt'] = (len(G.nodes), len(G.links))

# =====================================================================================================================
# 3. BP_NoticeHUD paste (end of DrawHUD, before the #31 banner so the banner stays on top).
#   Sockets: InfIn (exec in), InfSizeX / InfSizeY (Conv_IntToDouble, InInt <- CX_1.SizeX / SizeY), InfOut.then_0 (exec out)
#   While Infected: green fill over the hero bar (BP_ZombieHUD H23..H25 geometry), the frame redrawn on top with a 1 Hz green
#   glow (0.5..1.0), "YOU HAVE BEEN INFECTED" (0.25 s fade-in, 0.75..1.0 breathing at 0.6 Hz) + "Antidote: Vesna (castle)".
#   While ExplainCard > 0: dim screen, M_HintCard (#66) card, title/body/[Click to continue]; click/Space/Enter -> NextCard().
# =====================================================================================================================
G = Graph(); b = B(G, 'n')
sequence(G, 'InfIn', 1, 0, 0)
mathfn(G, 'InfSizeX', 'Conv_IntToDouble', [it('InInt', default='0'), D('ReturnValue', out=True)], 0, 300)
mathfn(G, 'InfSizeY', 'Conv_IntToDouble', [it('InInt', default='0'), D('ReturnValue', out=True)], 0, 450)
sx, sy = ('InfSizeX', 'ReturnValue'), ('InfSizeY', 'ReturnValue')
pch = b.lib(GS, 'GetPlayerCharacter', [(WC(), None), (it('PlayerIndex', default='0'), None)], [ob('ReturnValue', CLS('Character'), out=True)], 0, 600, 'Char')
ash = b.cast_(HERO, 'AsHero', (pch, 'ReturnValue'), 250, 0); b.to(('InfIn', 'then_0'), ash)
comp = b.oget(HERO, 'Infection', ob('v', INFC), (ash, 'AsHero'), 250, 300)
cget = lambda var, pin, x, y: b.oget(INFC, var, pin, comp, x, y)
sequence(G, 'InfOut', 1, 9000, 0)
G.link(ash, 'CastFailed', 'InfOut', 'execute')
ifi = b.br(cget('Infected', BOOL, 450, 300), 500, 0); b.to((ash, 'then'), ifi)
sc = b.d2('Divide_DoubleDouble', sy, None, 200, 900, db='1080.0')           # S = SizeY / 1080 for text
# hero bar geometry (BP_ZombieHUD): U = SizeX x 0.1365, frame (SizeX x 0.43175, SizeY x 0.91, U, U x 0.16412),
# fill (frame.x + U x 0.06398, frame.y + U x 0.037553, U x 0.87622 x frac, U x 0.089014), frac = clamp((MaxHP - DamageTaken) / MaxHP)
X = 700
u = b.d2('Multiply_DoubleDouble', sx, None, X, 700, db='0.1365')
fx0 = b.d2('Multiply_DoubleDouble', sx, None, X, 850, db='0.43175'); fy0 = b.d2('Multiply_DoubleDouble', sy, None, X, 1000, db='0.91')
fh0 = b.d2('Multiply_DoubleDouble', u, None, X + 200, 1150, db='0.16412')
bx = b.d2('Add_DoubleDouble', fx0, b.d2('Multiply_DoubleDouble', u, None, X + 200, 700, db='0.06398'), X + 400, 750)
by = b.d2('Add_DoubleDouble', fy0, b.d2('Multiply_DoubleDouble', u, None, X + 200, 1300, db='0.037553'), X + 400, 1250)
bh = b.d2('Multiply_DoubleDouble', u, None, X + 400, 1400, db='0.089014')
mx = cget('MaxHP', DBL, X, 1550)
frac = b.sat(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', mx, b.oget(HERO, 'DamageTaken', DBL, (ash, 'AsHero'), X, 1700), X + 200, 1600), mx, X + 400, 1600), X + 600, 1600)
bw = b.d2('Multiply_DoubleDouble', b.d2('Multiply_DoubleDouble', u, None, X + 400, 850, db='0.87622'), frac, X + 800, 900)
def drawtex(tex, px, py, pw, ph, uw, tint, blend, x, y, dtint):
    n = b.hud('DrawTexture', [dict(ob('Texture', CLS('Texture')), dobj=tex), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'), fl('ScreenW', default='0.0'),
              fl('ScreenH', default='0.0'), fl('TextureU', default='0.0'), fl('TextureV', default='0.0'), fl('TextureUWidth', default='1.0'), fl('TextureVHeight', default='1.0'),
              st('TintColor', LC, default=dtint), {'name': 'BlendMode', 'cat': 'byte', 'obj': BLEND, 'default': blend}, fl('Scale', default='1.000000'),
              bo('bScalePosition', default='false'), fl('Rotation', default='0.000000'), st('RotPivot', V2)], x, y)
    for p, src in (('ScreenX', px), ('ScreenY', py), ('ScreenW', pw), ('ScreenH', ph), ('TextureUWidth', uw), ('TintColor', tint)): b.wire(src, n, p)
    return n
rnow = b.realnow(1700, 1800)
glow = b.d2('Add_DoubleDouble', None, b.d2('Multiply_DoubleDouble', b.sin(b.d2('Multiply_DoubleDouble', rnow, None, 1900, 1800, db=TWO_PI), 2100, 1800), None, 2300, 1800, db='0.25'), 2500, 1800, da='0.75')
gtint = b.color(b.d2('Multiply_DoubleDouble', glow, None, 2700, 1700, db='0.25'), b.d2('Multiply_DoubleDouble', glow, None, 2700, 1850, db='0.85'),
                b.d2('Multiply_DoubleDouble', glow, None, 2700, 2000, db='0.30'), None, 2900, 1800)
d1 = drawtex(T_FILL, bx, by, bw, bh, frac, None, 'BLEND_Translucent', 1700, 0, '(R=0.250000,G=0.850000,B=0.300000,A=0.820000)')
d2 = drawtex(T_FRAME, fx0, fy0, u, fh0, None, None, 'BLEND_Translucent', 2000, 0, '(R=1.000000,G=1.000000,B=1.000000,A=1.000000)')
d3 = drawtex(T_FRAME, fx0, fy0, u, fh0, None, gtint, 'BLEND_Additive', 2300, 0, '(R=0.250000,G=0.850000,B=0.300000,A=1.000000)')
b.chain((ifi, 'then'), d1, d2, d3)
# notice text above the bar. Text heights fixed in px x S by measuring "Ag" (same trick as #31)
def textsize(text, scale, x, y, dtext=None, dscale='1.0'):
    n = b.hud('GetTextSize', [S('Text', default=dtext), fl('OutWidth', out=True, default='0.0'), fl('OutHeight', out=True, default='0.0'),
                              dict(ob('Font', CLS('Font')), dobj=FONT), fl('Scale', default=dscale)], x, y, pure=True)
    b.wire(text, n, 'Text'); b.wire(scale, n, 'Scale')
    return (n, 'OutWidth'), (n, 'OutHeight')
def drawtext(text, col, px, py, scale, x, y, dtext=None):
    n = b.hud('DrawText', [S('Text', default=dtext), st('TextColor', LC), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'),
                           dict(ob('Font', CLS('Font')), dobj=FONT), fl('Scale', default='1.0'), bo('bScalePosition', default='false')], x, y)
    for p, src in (('Text', text), ('TextColor', col), ('ScreenX', px), ('ScreenY', py), ('Scale', scale)): b.wire(src, n, p)
    return n
_, agh = textsize(None, None, 2600, 2300, dtext='Ag')
def tscale(px, x, y): return b.d2('Divide_DoubleDouble', b.d2('Multiply_DoubleDouble', sc, None, x, y, db=px), agh, x + 200, y)
L1, L2 = 'YOU HAVE BEEN INFECTED', 'Antidote: Vesna (castle)'
s1 = tscale('20.0', 2800, 2300); s2 = tscale('14.0', 2800, 2450)
w1, h1 = textsize(None, s1, 3200, 2300, dtext=L1); w2, h2 = textsize(None, s2, 3200, 2500, dtext=L2)
half = b.d2('Multiply_DoubleDouble', sx, None, 3200, 2700, db='0.5')
x1 = b.d2('Subtract_DoubleDouble', half, b.d2('Multiply_DoubleDouble', w1, None, 3400, 2350, db='0.5'), 3600, 2350)
x2 = b.d2('Subtract_DoubleDouble', half, b.d2('Multiply_DoubleDouble', w2, None, 3400, 2550, db='0.5'), 3600, 2550)
y2 = b.d2('Subtract_DoubleDouble', b.d2('Subtract_DoubleDouble', fy0, b.d2('Multiply_DoubleDouble', sc, None, 3400, 2750, db='6.0'), 3600, 2750), h2, 3800, 2700)
y1 = b.d2('Subtract_DoubleDouble', b.d2('Subtract_DoubleDouble', y2, b.d2('Multiply_DoubleDouble', sc, None, 3800, 2900, db='3.0'), 4000, 2850), h1, 4200, 2800)
age = b.d2('Subtract_DoubleDouble', b.now(3400, 3050), cget('InfectedAt', DBL, 3400, 3200), 3600, 3100)
fade = b.sat(b.d2('Divide_DoubleDouble', age, None, 3800, 3100, db='0.25'), 4000, 3100)
breath = b.d2('Add_DoubleDouble', None, b.d2('Multiply_DoubleDouble', b.sin(b.d2('Multiply_DoubleDouble', age, None, 3800, 3250, db='3.7699112'), 4000, 3250), None, 4200, 3250, db='0.125'), 4400, 3200, da='0.875')
al = b.d2('Multiply_DoubleDouble', fade, breath, 4600, 3150)
shc = b.color(None, None, None, b.d2('Multiply_DoubleDouble', al, None, 4800, 3300, db='0.8'), 5000, 3300)
c1 = b.color(None, None, None, al, 5000, 3450, dr='0.35', dg='0.95', db='0.40')
c2 = b.color(None, None, None, b.d2('Multiply_DoubleDouble', al, None, 4800, 3600, db='0.85'), 5000, 3600, dr='0.80', dg='0.92', db='0.78')
t1s = drawtext(None, shc, b.d2('Add_DoubleDouble', x1, sc, 4400, 2350), b.d2('Add_DoubleDouble', y1, sc, 4400, 2800), s1, 2600, 0, dtext=L1)
t1 = drawtext(None, c1, x1, y1, s1, 2900, 0, dtext=L1)
t2s = drawtext(None, shc, b.d2('Add_DoubleDouble', x2, sc, 4400, 2550), b.d2('Add_DoubleDouble', y2, sc, 4400, 2700), s2, 3200, 0, dtext=L2)
t2 = drawtext(None, c2, x2, y2, s2, 3500, 0, dtext=L2)
b.chain(d3, t1s, t1, t2s, t2)
# ---- explainer cards ----
X = 3900
card = cget('ExplainCard', INT, X, 300)
ifx = b.br(b.ic('Greater_IntInt', card, None, X + 200, 300, db='0'), X + 200, 0)
b.to(t2, ifx); b.to((ifi, 'else'), ifx)
G.link(ifx, 'else', 'InfOut', 'execute')
cw = b.d2('Multiply_DoubleDouble', sc, None, X + 200, 4000, db='900.0'); ch = b.d2('Multiply_DoubleDouble', sc, None, X + 200, 4150, db='300.0')
cx = b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', sx, cw, X + 400, 4000), None, X + 600, 4000, db='0.5')
cy = b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', sy, ch, X + 400, 4150), None, X + 600, 4150, db='0.5')
cage = b.d2('Subtract_DoubleDouble', b.realnow(X + 200, 4300), cget('ExplainT0', DBL, X + 200, 4450), X + 400, 4350)
dim = b.hud('DrawRect', [st('RectColor', LC, default='(R=0.000000,G=0.000000,B=0.000000,A=0.550000)'), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'),
                         fl('ScreenW', default='0.0'), fl('ScreenH', default='0.0')], X + 450, 0)
b.wire(sx, dim, 'ScreenW'); b.wire(sy, dim, 'ScreenH'); b.to((ifx, 'then'), dim)
mid = cget('CardMID', ob('v', MIDC), X + 600, 300)
vm = b.lib(SYS, 'IsValid', [(ob('Object', OBJ), mid)], [bo('ReturnValue', out=True)], X + 750, 300, 'Valid')
ifm = b.br((vm, 'ReturnValue'), X + 750, 0); b.to(dim, ifm)
prev = (ifm, 'then')
for k, (pn, src) in enumerate((('Age', cage), ('Aspect', b.d2('Divide_DoubleDouble', cw, ch, X + 800, 4300)), ('Fade', None))):
    n = b.call_on(MIDC, 'SetScalarParameterValue', mid, X + 1000 + k * 250, 0, pins=[{'name': 'ParameterName', 'cat': 'name', 'default': pn}, fl('Value', default='1.0')])
    b.wire(src, n, 'Value'); b.to(prev, n); prev = n
dmat = b.hud('DrawMaterial', [ob('Material', MATI), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'), fl('ScreenW', default='0.0'), fl('ScreenH', default='0.0'),
             fl('MaterialU', default='0.0'), fl('MaterialV', default='0.0'), fl('MaterialUWidth', default='1.0'), fl('MaterialVHeight', default='1.0'),
             fl('Scale', default='1.000000'), bo('bScalePosition', default='false'), fl('Rotation', default='0.000000'), st('RotPivot', V2)], X + 1750, 0)
for p, src in (('Material', mid), ('ScreenX', cx), ('ScreenY', cy), ('ScreenW', cw), ('ScreenH', ch)): b.wire(src, dmat, p)
b.to(prev, dmat)
panel = b.hud('DrawRect', [st('RectColor', LC, default='(R=0.030000,G=0.025000,B=0.030000,A=0.920000)'), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'),
                           fl('ScreenW', default='0.0'), fl('ScreenH', default='0.0')], X + 1000, 400)   # fallback when M_HintCard is missing
for p, src in (('ScreenX', cx), ('ScreenY', cy), ('ScreenW', cw), ('ScreenH', ch)): b.wire(src, panel, p)
b.to((ifm, 'else'), panel)
# copy by card number
is1 = b.ic('EqualEqual_IntInt', card, None, X + 1800, 4500, db='1'); is2 = b.ic('EqualEqual_IntInt', card, None, X + 1800, 4650, db='2')
title = b.sels(None, b.sels(None, None, is2, X + 2000, 4700, da='INFECTED', db='THE CURE'), is1, X + 2200, 4600, da='BITTEN')
body = b.sels(None, b.sels(None, None, is2, X + 2000, 4950, da="Defence +50 %, but your health drains and won't regenerate.",
                           db='Vesna in the castle brews the antidote. Your first one is free.'), is1, X + 2200, 4850, da='Below 30 % health a zombie bite infects you.')
hint = 'Click to continue'
ta = b.sat(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', cage, None, X + 1800, 4350, db='0.35'), None, X + 2000, 4350, db='0.30'), X + 2200, 4350)
st_ = tscale('34.0', X + 2000, 5100); sb = tscale('20.0', X + 2000, 5250); sh_ = tscale('15.0', X + 2000, 5400)
tw, th = textsize(title, st_, X + 2400, 5100); bw_, bh_ = textsize(body, sb, X + 2400, 5250); hw, hh = textsize(None, sh_, X + 2400, 5400, dtext=hint)
ccx = b.d2('Add_DoubleDouble', cx, b.d2('Multiply_DoubleDouble', cw, None, X + 2600, 5550, db='0.5'), X + 2800, 5550)
def centre(w, x, y): return b.d2('Subtract_DoubleDouble', ccx, b.d2('Multiply_DoubleDouble', w, None, x, y, db='0.5'), x + 200, y)
def rowy(f, x, y): return b.d2('Add_DoubleDouble', cy, b.d2('Multiply_DoubleDouble', ch, None, x, y, db=f), x + 200, y)
gold = b.color(None, None, None, ta, X + 3000, 5100, dr='1.0', dg='0.80', db='0.35')
white = b.color(None, None, None, ta, X + 3000, 5250, dr='0.95', dg='0.88', db='0.76')
dimg = b.color(None, None, None, b.d2('Multiply_DoubleDouble', ta, None, X + 2800, 5400, db='0.75'), X + 3000, 5400, dr='0.85', dg='0.72', db='0.40')
tt = drawtext(title, gold, centre(tw, X + 2600, 5100), rowy('0.17', X + 2600, 5700), st_, X + 2000, 0)
tb = drawtext(body, white, centre(bw_, X + 2600, 5250), rowy('0.47', X + 2600, 5850), sb, X + 2250, 0)
th_ = drawtext(None, dimg, centre(hw, X + 2600, 5400), rowy('0.76', X + 2600, 6000), sh_, X + 2500, 0, dtext=hint)
b.to(dmat, tt); b.to(panel, tt); b.chain(tt, tb, th_)
# click / Space / Enter, ignored for the first 0.6 s of each card so one click can't skip two
pc = b.lib(GS, 'GetPlayerController', [(WC(), None), (it('PlayerIndex', default='0'), None)], [ob('ReturnValue', PCC, out=True)], X + 2600, 6200, 'PC')
keys = []
for k, key in enumerate(('LeftMouseButton', 'SpaceBar', 'Enter')):
    n = b.name('Key')
    callfn(G, n, PCC, 'WasInputKeyJustPressed', [{'name': 'Key', 'cat': 'struct', 'obj': KEY, 'default': key}, bo('ReturnValue', out=True, default='false')],
           pure=True, x=X + 2800, y=6200 + k * 150)
    G.link(pc, 'ReturnValue', n, 'self'); keys.append((n, 'ReturnValue'))
anyk = b.b2('BooleanOR', b.b2('BooleanOR', keys[0], keys[1], X + 3050, 6250), keys[2], X + 3250, 6300)
okc = b.b2('BooleanAND', anyk, b.dc('Greater_DoubleDouble', cage, None, X + 3050, 6500, db='0.6'), X + 3450, 6400)
ifk = b.br(okc, X + 2800, 0); b.to(th_, ifk)
nc = b.call_on(INFC, 'NextCard', comp, X + 3050, 0); b.to((ifk, 'then'), nc)
b.to(nc, 'InfOut'); G.link(ifk, 'else', 'InfOut', 'execute')
open(os.path.join(HERE, 'NoticeHUD_Infection_graph.txt'), 'w', newline='\r\n').write(G.render())
print('NoticeHUD paste: nodes', len(G.nodes), 'links', len(G.links))
COUNTS['NoticeHUD_Infection_graph.txt'] = (len(G.nodes), len(G.links))
