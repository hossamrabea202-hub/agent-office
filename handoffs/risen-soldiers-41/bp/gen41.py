# #41 Fallen soldiers rise as zombies: generates the Blueprint pastes (laptop2, 2026-10-29). Run with any Python 3:
#   python gen41.py   ->  BP_RisenDirector_graph.txt   (EventGraph of the NEW actor BP_RisenDirector: fallen list, wave rise)
#                         BP_ZombieRisen_graph.txt     (EventGraph of the NEW BP_ZombieRisen, child of BP_Zombie)
#                         Soldier_FallenHook_graph.txt (7 nodes for BP_SoldierSword's death branch: FallIn .. FallOut)
# Uses the Master's node kit (tools/master/t81/kit.py) the same way #96's gen96.py does. Node/pin layouts that the kit
# does not have were copied from the 2026-10-28 exports (handoffs/exports/laptop2/gameplay + checkking).
import os, re, sys
sys.dont_write_bytecode = True      # keep the kit folder clean
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'master', 't81'))
from kit import *

# ---------------------------------------------------------------- classes / assets
OBJ = '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"'
ACT, PAWN, CHARC, CMC, CTRL, PCON = CLS('Actor'), CLS('Pawn'), CLS('Character'), CLS('CharacterMovementComponent'), CLS('Controller'), CLS('PlayerController')
GS, KSL, KML, KSTR, KTXT, KARR = CLS('GameplayStatics'), CLS('KismetSystemLibrary'), CLS('KismetMathLibrary'), CLS('KismetStringLibrary'), CLS('KismetTextLibrary'), CLS('KismetArrayLibrary')
SCENE, PRIM, MESHC, SKIN, SKEL = CLS('SceneComponent'), CLS('PrimitiveComponent'), CLS('MeshComponent'), CLS('SkinnedMeshComponent'), CLS('SkeletalMeshComponent')
MATI, MID, CURVE, PSYS, PSC = CLS('MaterialInterface'), CLS('MaterialInstanceDynamic'), CLS('CurveFloat'), CLS('ParticleSystem'), CLS('ParticleSystemComponent')
UMG = lambda c: '"/Script/CoreUObject.Class\'/Script/UMG.%s\'"' % c
TEXTB, USERW, WIDGET = UMG('TextBlock'), UMG('UserWidget'), UMG('Widget')
NAVSYS = '"/Script/CoreUObject.Class\'/Script/NavigationSystem.NavigationSystemV1\'"'
NAVDATA = '"/Script/CoreUObject.Class\'/Script/NavigationSystem.NavigationData\'"'
NAVFILT = '"/Script/CoreUObject.Class\'/Script/NavigationSystem.NavigationQueryFilter\'"'
ENUM = lambda e: '"/Script/CoreUObject.Enum\'/Script/Engine.%s\'"' % e
VEC, ROT, XFORM, LC = STRUCT('Vector'), STRUCT('Rotator'), STRUCT('Transform'), STRUCT('LinearColor')
TIMERH = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.TimerHandle\'"'
HITRES = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.HitResult\'"'

P_ZOMBIE = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
P_RISEN = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_ZombieRisen'
P_DIR = '/Game/CastleDefender/Gameplay/Castle/BP_RisenDirector'
P_WM = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager'
P_SOLDIER = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
P_CMDR = '/Game/CastleDefender/Characters/Knight/BP_SoldierCommander'
P_WBP = '/Game/CastleDefender/Gameplay/Castle/WBP_WaveBanner'
cpath = lambda p: '%s.%s_C' % (p, p.split('/')[-1])      # class default-object path for class pins
ZOMBIE, RISEN, DIRECTOR = BPC(P_ZOMBIE, 'BP_Zombie'), BPC(P_RISEN, 'BP_ZombieRisen'), BPC(P_DIR, 'BP_RisenDirector')
WM, SOLDIER = BPC(P_WM, 'BP_ZombieWaveManager'), BPC(P_SOLDIER, 'BP_SoldierSword')
WBP = '"/Script/UMG.WidgetBlueprintGeneratedClass\'%s\'"' % cpath(P_WBP)
C_HP, C_DMG = '/Game/CastleDefender/Gameplay/Waves/C_Wave_HPMult.C_Wave_HPMult', '/Game/CastleDefender/Gameplay/Waves/C_Wave_DmgMult.C_Wave_DmgMult'
P_SMOKE = '/Game/CastleDefender/VFX/Smoke/P_Smoke_Burst.P_Smoke_Burst'
FOREACH = "MacroGraph=\"/Script/Engine.EdGraph'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop'\",GraphBlueprint=\"/Script/Engine.Blueprint'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros'\",GraphGuid=99DBFD5540A796041F72A5A9DA655026"
FORLOOP = "MacroGraph=\"/Script/Engine.EdGraph'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForLoop'\",GraphBlueprint=\"/Script/Engine.Blueprint'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros'\",GraphGuid=55C904AF4B45FE1761FB55A8DB9FB801"

def D(name, out=False, default=None): return fl(name, out=out, default=default, sub='double')
def S(name, out=False, default=None): return {'name': name, 'cat': 'string', 'out': out, 'default': default}
def N(name, default=None): return {'name': name, 'cat': 'name', 'default': default}
def CLSPIN(name, base, dpath): return {'name': name, 'cat': 'class', 'obj': base, 'dobj': dpath}
def V(name, out=False, default='0, 0, 0'): return st(name, VEC, out=out, default=default)
def arr(p): return dict(p, container='Array')
WC = lambda: dict(ob('WorldContextObject', OBJ), hidden=True)

# variable pin types (used for get/set nodes; the names are replaced by the variable name)
INT, DBL, BOOL, STR = it('v', default='0'), D('v', default='0.0'), bo('v', default='false'), S('v')
VECT = V('v')
MATV = ob('v', MATI)


class B:
    """small builder on top of kit.Graph (same idea as gen96.py): value helpers return (node, pin) handles."""
    def __init__(s, G, prefix): s.G, s.p, s.n = G, prefix, 0
    def name(s, tag): s.n += 1; return '%s%s%d' % (s.p, re.sub(r'\W', '', tag)[:14], s.n)
    def wire(s, src, node, pin):
        if src is not None: s.G.link(src[0], src[1], node, pin)
    def link(s, a, pa, b_, pb): s.G.link(a, pa, b_, pb)
    # ---- pure math (KismetMathLibrary) ----
    def math(s, member, ins, outpin, x, y):
        n = s.name(member); mathfn(s.G, n, member, [p for p, _ in ins] + [outpin], x, y)
        for p, src in ins: s.wire(src, n, p['name'])
        return (n, outpin['name'])
    def d2(s, m, a, b_, x, y, da='0.0', db='0.0'): return s.math(m, [(D('A', default=da), a), (D('B', default=db), b_)], D('ReturnValue', out=True), x, y)
    def dcmp(s, m, a, b_, x, y, da='0.0', db='0.0'): return s.math(m, [(D('A', default=da), a), (D('B', default=db), b_)], bo('ReturnValue', out=True), x, y)
    def i2(s, m, a, b_, x, y, da='0', db='0'): return s.math(m, [(it('A', default=da), a), (it('B', default=db), b_)], it('ReturnValue', out=True), x, y)
    def icmp(s, m, a, b_, x, y, da='0', db='0'): return s.math(m, [(it('A', default=da), a), (it('B', default=db), b_)], bo('ReturnValue', out=True), x, y)
    def b2(s, m, a, b_, x, y): return s.math(m, [(bo('A', default='false'), a), (bo('B', default='false'), b_)], bo('ReturnValue', out=True), x, y)
    def bnot(s, a, x, y): return s.math('Not_PreBool', [(bo('A', default='false'), a)], bo('ReturnValue', out=True), x, y)
    def i2d(s, a, x, y): return s.math('Conv_IntToDouble', [(it('InInt', default='0'), a)], D('ReturnValue', out=True), x, y)
    def clamp(s, v, lo, hi, x, y): return s.math('FClamp', [(D('Value', default='0.0'), v), (D('Min', default=lo), None), (D('Max', default=hi), None)], D('ReturnValue', out=True), x, y)
    def rnd(s, lo, hi, x, y): return s.math('RandomFloatInRange', [(D('Min', default=lo), None), (D('Max', default=hi), None)], D('ReturnValue', out=True), x, y)
    def self_(s, a, b_, pick, x, y, da='0.0', db='0.0'):
        return s.math('SelectFloat', [(D('A', default=da), a), (D('B', default=db), b_), (bo('bPickA', default='false'), pick)], D('ReturnValue', out=True), x, y)
    def selstr(s, a, b_, pick, x, y, da='', db=''):
        return s.math('SelectString', [(S('A', default=da), a), (S('B', default=db), b_), (bo('bPickA', default='false'), pick)], S('ReturnValue', out=True), x, y)
    def selvec(s, a, b_, pick, x, y, da='0, 0, 0', db='0, 0, 0'):
        return s.math('SelectVector', [(V('A', default=da), a), (V('B', default=db), b_), (bo('bPickA', default='false'), pick)], V('ReturnValue', out=True), x, y)
    def vec(s, xx, yy, zz, x, y, dx='0.0', dy='0.0', dz='0.0'):
        return s.math('MakeVector', [(D('X', default=dx), xx), (D('Y', default=dy), yy), (D('Z', default=dz), zz)], V('ReturnValue', out=True), x, y)
    def brk(s, v, x, y):
        n = s.name('BreakVector'); mathfn(s.G, n, 'BreakVector', [V('InVec')] + [D(c, out=True, default='0.0') for c in 'XYZ'], x, y)
        s.wire(v, n, 'InVec'); return {c: (n, c) for c in 'XYZ'}
    def v2(s, m, a, b_, x, y, db='0, 0, 0'): return s.math(m, [(V('A'), a), (V('B', default=db), b_)], V('ReturnValue', out=True), x, y)
    def concat(s, a, b_, x, y, da='', db=''):
        n = s.name('Concat'); callfn(s.G, n, KSTR, 'Concat_StrStr', [S('A', default=da), S('B', default=db), S('ReturnValue', out=True)], pure=True, x=x, y=y, self_hidden=True)
        s.wire(a, n, 'A'); s.wire(b_, n, 'B'); return (n, 'ReturnValue')
    def text(s, src, x, y):
        n = s.name('ToText'); callfn(s.G, n, KTXT, 'Conv_StringToText', [S('InString'), {'name': 'ReturnValue', 'cat': 'text', 'out': True}], pure=True, x=x, y=y, self_hidden=True)
        s.wire(src, n, 'InString'); return (n, 'ReturnValue')
    def now(s, x, y):
        n = s.name('Now'); callfn(s.G, n, GS, 'GetTimeSeconds', [WC(), D('ReturnValue', out=True)], pure=True, x=x, y=y, self_hidden=True)
        return (n, 'ReturnValue')
    def valid(s, obj, x, y):
        n = s.name('IsValid'); callfn(s.G, n, KSL, 'IsValid', [ob('Object', OBJ), bo('ReturnValue', out=True, default='false')], pure=True, x=x, y=y, self_hidden=True)
        s.wire(obj, n, 'Object'); return (n, 'ReturnValue')
    # ---- variables ----
    def get(s, var, pin, x, y):
        n = s.name('Get' + var); varget(s.G, n, None, var, None, dict(pin, name=var), x, y, self_ctx=True); return (n, var)
    def set(s, var, pin, src, x, y):
        n = s.name('Set' + var); varset(s.G, n, None, var, None, dict(pin, name=var, out=False), x, y, self_ctx=True); s.wire(src, n, var); return n
    def getm(s, var, parent, pin, target, x, y):
        """variable of another object (VariableReference with MemberParent), target = handle of the object."""
        n = s.name('Get' + var); varget(s.G, n, parent, var, parent, dict(pin, name=var), x, y); s.wire(target, n, 'self'); return (n, var)
    def setm(s, var, parent, pin, src, target, x, y):
        n = s.name('Set' + var); varset(s.G, n, parent, var, parent, dict(pin, name=var, out=False), x, y); s.wire(src, n, var); s.wire(target, n, 'self'); return n
    def relloc(s, comp, x, y):
        return s.getm('RelativeLocation', SCENE, VECT, comp, x, y)
    # ---- arrays ----
    def aget(s, arrvar, pin, idx, x, y):
        a = s.get(arrvar, arr(pin), x, y)
        n = s.name('Item' + arrvar)
        s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x + 220, y)
        s.wire(a, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def alen(s, arrvar, pin, x, y):
        a = s.get(arrvar, arr(pin), x, y)
        n = s.name('Len' + arrvar)
        s.G.node(n, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
                 [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], x + 220, y)
        s.wire(a, n, 'TargetArray'); return (n, 'ReturnValue')
    def aadd(s, arrvar, pin, item, x, y):
        a = s.get(arrvar, arr(pin), x, y + 150)
        n = s.name('Add' + arrvar)
        s.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Add")' % KARR],
                 [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
                  {'name': 'NewItem', 'cat': 'wildcard', 'ref': True}, it('ReturnValue', out=True, default='0')], x, y)
        s.wire(a, n, 'TargetArray'); s.wire(item, n, 'NewItem'); return n
    def aset(s, arrvar, pin, idx, item, x, y, ditem=None):
        a = s.get(arrvar, arr(pin), x, y + 150)
        n = s.name('Set' + arrvar)
        s.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Set")' % KARR],
                 [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
                  it('Index', default='0'), {'name': 'Item', 'cat': 'wildcard', 'ref': True, 'default': ditem}, bo('bSizeToFit', default='false')], x, y)
        s.wire(a, n, 'TargetArray'); s.wire(idx, n, 'Index'); s.wire(item, n, 'Item'); return n
    # ---- exec nodes ----
    def event(s, name, params, x, y):
        props = ['CustomFunctionName="%s"' % name]
        for p in params:
            t = 'PinCategory="%s"' % p['cat'] + (',PinSubCategory="%s"' % p['sub'] if p.get('sub') else '') + \
                (',PinSubCategoryObject=%s' % p['obj'] if p.get('obj') and p['obj'] != 'None' else '')
            props.append('CustomProperties UserDefinedPin (PinName="%s",PinType=(%s),DesiredPinDirection=EGPD_Output)' % (p['name'], t))
        s.G.node(name, 'K2Node_CustomEvent', props, [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '()'}, ex('then', True)]
                 + [dict(p, out=True, default=None) for p in params], x, y)
        return name
    def override(s, nm, member, x, y):
        s.G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ACT, member), 'bOverrideFunction=True'],
                 [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (ACT, member)}, ex('then', True)], x, y)
        return nm
    def branch(s, cond, x, y, tag='If'):
        n = s.name(tag); branch(s.G, n, x, y); s.wire(cond, n, 'Condition'); return n
    def seq(s, nm, k, x, y): sequence(s.G, nm, k, x, y); return nm
    def call(s, parent, member, pins, x, y, target=None, pure=False, const=False, tag=None):
        """call on another object (self pin visible, linked to target)."""
        n = s.name(tag or member); callfn(s.G, n, parent, member, pins, pure=pure, const=const, x=x, y=y)
        s.wire(target, n, 'self'); return n
    def lib(s, parent, member, pins, x, y, pure=False, tag=None):
        """static library call (hidden self)."""
        n = s.name(tag or member); callfn(s.G, n, parent, member, pins, pure=pure, x=x, y=y, self_hidden=True); return n
    def call_self(s, member, pins, x, y, cls, pure=False, const=False, tag=None):
        n = s.name(tag or member)
        props = (['bIsPureFunc=True'] if pure else []) + (['bIsConstFunc=True'] if const else []) + ['FunctionReference=(MemberName="%s",bSelfContext=True)' % member]
        s.G.node(n, 'K2Node_CallFunction', props, ([] if pure else [ex(), ex('then', True)]) + [selfpin(cls, hidden=True)] + list(pins), x, y)
        return n
    def timer(s, fn, x, y, time=None, dtime='0.5', loop=False):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=dtime), bo('bLooping', default='true' if loop else 'false'),
                                      fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                      st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(time, n, 'Time'); return n
    def timer_fn(s, member, fn, x, y):     # K2_ClearTimer / K2_PauseTimer / K2_UnPauseTimer (Object defaults to self)
        return s.lib(KSL, member, [ob('Object', OBJ), S('FunctionName', default=fn)], x, y, tag=member[3:] + fn)
    def actor_of(s, path, cls, x, y):
        n = s.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], x, y, tag='Find' + path.split('/')[-1][3:])
        return n
    def self_node(s, x, y):
        n = s.name('Self'); s.G.node(n, 'K2Node_Self', [], [{'name': 'self', 'cat': 'object', 'sub': 'self', 'out': True}], x, y); return (n, 'self')
    def foreach(s, elem_cls, x, y):
        n = s.name('ForEach')
        s.G.node(n, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FOREACH, 'ResolvedWildcardType=(PinCategory="object",PinSubCategoryObject=%s)' % elem_cls],
                 [ex('Exec'), arr(ob('Array', elem_cls)), ex('LoopBody', True), ob('Array Element', elem_cls, out=True), it('Array Index', out=True), ex('Completed', True)], x, y)
        return n
    def forloop(s, first, last, x, y):
        n = s.name('ForLoop')
        s.G.node(n, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FORLOOP],
                 [ex(), it('FirstIndex', default='0'), it('LastIndex', default='0'), ex('LoopBody', True), it('Index', out=True), ex('Completed', True)], x, y)
        s.wire(first, n, 'FirstIndex'); s.wire(last, n, 'LastIndex'); return n
    def chain(s, *nodes):
        for a, b_ in zip(nodes, nodes[1:]):
            s.G.link(a[0] if isinstance(a, tuple) else a, a[1] if isinstance(a, tuple) else 'then', b_[0] if isinstance(b_, tuple) else b_, b_[1] if isinstance(b_, tuple) else 'execute')


def spawn(b, cls_path, cls_ref, xform, x, y):
    n = b.name('Spawn' + cls_path.split('/')[-1][3:])
    b.G.node(n, 'K2Node_SpawnActorFromClass', ['AdvancedPinDisplay=Hidden'],
             [ex(), ex('then', True), CLSPIN('Class', ACT, cpath(cls_path)), ob('ReturnValue', cls_ref, out=True), st('SpawnTransform', XFORM),
              {'name': 'CollisionHandlingOverride', 'cat': 'byte', 'obj': ENUM('ESpawnActorCollisionHandlingMethod'), 'default': 'AdjustIfPossibleButAlwaysSpawn'},
              {'name': 'TransformScaleMethod', 'cat': 'byte', 'obj': ENUM('ESpawnActorScaleMethod'), 'default': 'SelectDefaultAtRuntime', 'advanced': True},
              dict(ob('Owner', ACT), advanced=True), ob('Instigator', PAWN)], x, y)
    b.wire(xform, n, 'SpawnTransform'); return n

def transform(b, loc, x, y):
    return b.math('MakeTransform', [(V('Location'), loc), (st('Rotation', ROT, default='0, 0, 0'), None), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
                  st('ReturnValue', XFORM, out=True), x, y)


# =====================================================================================================================
# 1) BP_RisenDirector (new Actor, one per game; the first soldier death spawns it).
#    ReportFallen(Soldier)  <- the soldier hook. Outside the castle box -> append to the Fallen list.
#    Poll (0.5 s timer)     -> new wave: RiseLeft = MaxPerWave (12), start RiseNext. Also: commander rescue (10 s, 3 m).
#    RiseNext (1.0-1.5 s)   -> oldest eligible entry rises as BP_ZombieRisen at his spot (navmesh within 2 m).
#    ShowRestNotice(Title)  <- called by a risen soldier when he dies ("A FALLEN VETERAN IS AT REST").
#    Fallen list = parallel arrays FallenLoc/FallenRank/FallenKind/FallenWave/FallenTime/FallenCloth, read cursor NextIdx.
#    Kind: 0 sword, 1 crossbow, 2 commander, -1 carried home (never rises).
# =====================================================================================================================
G = Graph(); b = B(G, 'd')

# ---- BeginPlay: Poll timer; LastWave = the current wave (so spawning mid-wave does not count as a wave start) ----
b.override('DirBeginPlay', 'ReceiveBeginPlay', 0, 0)
t = b.timer('Poll', 300, 0, dtime='0.5', loop=True)
f = b.actor_of(P_WM, WM, 650, 0)
ok = b.branch(b.valid((f, 'ReturnValue'), 650, 250), 950, 0, 'IfWM')
s1 = b.set('LastWave', INT, b.getm('Wave', WM, INT, (f, 'ReturnValue'), 950, 350), 1250, 0)
b.chain('DirBeginPlay', t, f, ok)
G.link(ok, 'then', s1, 'execute')

# ---- ReportFallen(Soldier) ----
Y = 900
b.event('ReportFallen', [ob('Soldier', ACT)], 0, Y)
SOL = ('ReportFallen', 'Soldier')
cs = b.name('AsSoldier'); cast(G, cs, SOLDIER, 'AsBP Soldier Sword', 300, Y); G.link('ReportFallen', 'then', cs, 'execute'); b.wire(SOL, cs, 'Object')
AS = (cs, 'AsBP Soldier Sword')
locn = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 300, Y + 300, target=SOL, pure=True, const=True, tag='SoldierLoc')
LOC = (locn, 'ReturnValue')
p = b.brk(LOC, 500, Y + 300)
c1 = b.dcmp('GreaterEqual_DoubleDouble', p['X'], b.get('InsideMinX', DBL, 650, Y + 450), 850, Y + 300)
c2 = b.dcmp('LessEqual_DoubleDouble', p['X'], b.get('InsideMaxX', DBL, 650, Y + 550), 850, Y + 400)
c3 = b.dcmp('GreaterEqual_DoubleDouble', p['Y'], b.get('InsideMinY', DBL, 650, Y + 650), 850, Y + 500)
c4 = b.dcmp('LessEqual_DoubleDouble', p['Y'], b.get('InsideMaxY', DBL, 650, Y + 750), 850, Y + 600)
inside = b.b2('BooleanAND', b.b2('BooleanAND', c1, c2, 1050, Y + 350), b.b2('BooleanAND', c3, c4, 1050, Y + 550), 1250, Y + 450)
br = b.branch(inside, 600, Y, 'IfInside')
G.link(cs, 'then', br, 'execute')                     # inside -> nothing (he never rises)
wmf = b.actor_of(P_WM, WM, 900, Y)
G.link(br, 'else', wmf, 'execute')
# Kind: commander 2 / crossbow 1 / sword 0
cls_ = b.lib(GS, 'GetObjectClass', [dict(ob('Object', OBJ)), {'name': 'ReturnValue', 'cat': 'class', 'obj': ACT, 'out': True}], 1300, Y + 700, pure=True)
b.wire(SOL, cls_, 'Object')
iscmd = b.lib(KML, 'ClassIsChildOf', [{'name': 'TestClass', 'cat': 'class', 'obj': OBJ}, CLSPIN('ParentClass', OBJ, cpath(P_CMDR)), bo('ReturnValue', out=True, default='false')], 1550, Y + 700, pure=True)
G.link(cls_, 'ReturnValue', iscmd, 'TestClass')
xb = b.call(ACT, 'ActorHasTag', [N('Tag', 'Xbow'), bo('ReturnValue', out=True, default='false')], 1550, Y + 850, target=SOL, pure=True, const=True)
k1 = b.math('SelectInt', [(it('A', default='1'), None), (it('B', default='0'), None), (bo('bPickA', default='false'), (xb, 'ReturnValue'))], it('ReturnValue', out=True), 1800, Y + 850)
kind = b.math('SelectInt', [(it('A', default='2'), None), (it('B', default='0'), k1), (bo('bPickA', default='false'), (iscmd, 'ReturnValue'))], it('ReturnValue', out=True), 2000, Y + 750)
# Rank = Soldier.Rank.RelativeLocation.Y ; Cloth = Soldier.KnightMesh material 2 (rank + cape colours live on it)
rk = b.getm('Rank', SOLDIER, ob('v', SCENE), AS, 1300, Y + 1000)
rank = b.brk(b.relloc(rk, 1500, Y + 1000), 1750, Y + 1000)['Y']
km = b.getm('KnightMesh', SOLDIER, ob('v', SKEL), AS, 1300, Y + 1200)
gm = b.call(PRIM, 'GetMaterial', [it('ElementIndex', default='2'), ob('ReturnValue', MATI, out=True)], 1550, Y + 1200, target=km, pure=True, const=True)
wave = b.getm('Wave', WM, INT, (wmf, 'ReturnValue'), 1300, Y + 1350)
a1 = b.aadd('FallenLoc', VECT, LOC, 1200, Y)
a2 = b.aadd('FallenRank', DBL, rank, 1500, Y)
a3 = b.aadd('FallenKind', INT, kind, 1800, Y)
a4 = b.aadd('FallenWave', INT, wave, 2100, Y)
a5 = b.aadd('FallenTime', DBL, b.now(2300, Y + 300), 2400, Y)
a6 = b.aadd('FallenCloth', MATV, (gm, 'ReturnValue'), 2700, Y)
b.chain(wmf, a1, a2, a3, a4, a5, a6)

# ---- Poll (0.5 s): wave start + commander rescue ----
Y = 2900
b.event('Poll', [], 0, Y)
ps = b.seq('PollSeq', 2, 250, Y)
G.link('Poll', 'then', ps, 'execute')
wf = b.actor_of(P_WM, WM, 500, Y)
G.link(ps, 'then_0', wf, 'execute')
okw = b.branch(b.valid((wf, 'ReturnValue'), 500, Y + 250), 800, Y, 'IfWM')
G.link(wf, 'then', okw, 'execute')
wv = b.getm('Wave', WM, INT, (wf, 'ReturnValue'), 800, Y + 300)
chg = b.branch(b.icmp('NotEqual_IntInt', wv, b.get('LastWave', INT, 1000, Y + 450), 1200, Y + 300), 1100, Y, 'IfNewWave')
G.link(okw, 'then', chg, 'execute')
s1 = b.set('LastWave', INT, wv, 1400, Y)
s2 = b.set('RiseLeft', INT, b.get('MaxPerWave', INT, 1500, Y + 250), 1700, Y)
t1 = b.timer('RiseNext', 2000, Y, time=b.rnd('0.5', '1.0', 1800, Y + 300))
G.link(chg, 'then', s1, 'execute'); b.chain(s1, s2, t1)
# rescue: for i in NextIdx .. Len-1: Kind[i]==2 and Now-Time[i] < RescueWindow -> any living soldier within RescueRadius -> Kind[i] = -1
Y = 3700
ln = b.alen('FallenKind', INT, 300, Y + 300)
last = b.i2('Subtract_IntInt', ln, None, 650, Y + 300, db='1')
lp = b.forloop(b.get('NextIdx', INT, 500, Y + 200), last, 850, Y)
G.link(ps, 'then_1', lp, 'execute')
I = (lp, 'Index')
kd = b.aget('FallenKind', INT, I, 900, Y + 450)
age = b.d2('Subtract_DoubleDouble', b.now(1100, Y + 650), b.aget('FallenTime', DBL, I, 900, Y + 750), 1350, Y + 650)
fresh = b.dcmp('Less_DoubleDouble', age, b.get('RescueWindow', DBL, 1350, Y + 850), 1550, Y + 700)
isc = b.b2('BooleanAND', b.icmp('EqualEqual_IntInt', kd, None, 1350, Y + 450, db='2'), fresh, 1750, Y + 500)
brc = b.branch(isc, 1150, Y, 'IfCmdBody')
G.link(lp, 'LoopBody', brc, 'execute')
alls = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_SOLDIER)), arr(ob('OutActors', SOLDIER, out=True))], 1450, Y)
G.link(brc, 'then', alls, 'execute')
fe = b.foreach(SOLDIER, 1800, Y)
G.link(alls, 'then', fe, 'Exec'); G.link(alls, 'OutActors', fe, 'Array')
EL = (fe, 'Array Element')
alive = b.dcmp('Less_DoubleDouble', b.brk(b.relloc(b.getm('State', SOLDIER, ob('v', SCENE), EL, 1800, Y + 1050), 2000, Y + 1050), 2250, Y + 1050)['Z'], None, 2500, Y + 1050, db='0.5')
eloc = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1950, Y + 1250, target=EL, pure=True, const=True, tag='SquadLoc')
d2d = b.math('Vector_Distance2D', [(V('V1'), (eloc, 'ReturnValue')), (V('V2'), b.aget('FallenLoc', VECT, I, 1950, Y + 1400))], D('ReturnValue', out=True), 2300, Y + 1250)
near = b.dcmp('Less_DoubleDouble', d2d, b.get('RescueRadius', DBL, 2300, Y + 1450), 2550, Y + 1250)
brs = b.branch(b.b2('BooleanAND', alive, near, 2750, Y + 1100), 2200, Y, 'IfCarried')
G.link(fe, 'LoopBody', brs, 'execute')
mk = b.aset('FallenKind', INT, I, None, 2550, Y, ditem='-1')
G.link(brs, 'then', mk, 'execute')

# ---- RiseNext: the oldest entry that fell before this wave rises (skips carried-home commanders) ----
Y = 5600
b.event('RiseNext', [], 0, Y)
ix = b.get('NextIdx', INT, 0, Y + 300)
c_len = b.icmp('Less_IntInt', ix, b.alen('FallenKind', INT, 0, Y + 450), 450, Y + 350)
c_left = b.icmp('Greater_IntInt', b.get('RiseLeft', INT, 250, Y + 600), None, 450, Y + 550, db='0')
br1 = b.branch(b.b2('BooleanAND', c_len, c_left, 650, Y + 400), 300, Y, 'IfAny')
G.link('RiseNext', 'then', br1, 'execute')
old = b.icmp('Less_IntInt', b.aget('FallenWave', INT, ix, 600, Y + 750), b.get('LastWave', INT, 800, Y + 900), 1050, Y + 750)
br2 = b.branch(old, 600, Y, 'IfOld')
G.link(br1, 'then', br2, 'execute')
# wait until the rescue window of the oldest body is over (a commander may still be carried home); retry in 1 s
age2 = b.d2('Subtract_DoubleDouble', b.now(600, Y + 1150), b.aget('FallenTime', DBL, ix, 400, Y + 1250), 850, Y + 1150)
br2b = b.branch(b.dcmp('GreaterEqual_DoubleDouble', age2, b.get('RescueWindow', DBL, 850, Y + 1300), 1050, Y + 1150), 750, Y, 'IfSettled')
G.link(br2, 'then', br2b, 'execute')
G.link(br2b, 'else', b.timer('RiseNext', 1000, Y + 300, dtime='1.0'), 'execute')
kd = b.aget('FallenKind', INT, ix, 900, Y + 1000)
br3 = b.branch(b.icmp('Less_IntInt', kd, None, 1300, Y + 1000, db='0'), 900, Y, 'IfCarried')
G.link(br2b, 'then', br3, 'execute')
nx1 = b.set('NextIdx', INT, b.i2('Add_IntInt', ix, None, 1100, Y - 250, db='1'), 1200, Y - 150)
again = b.call_self('RiseNext', [], 1500, Y - 150, DIRECTOR, tag='CallRiseNext')
G.link(br3, 'then', nx1, 'execute'); b.chain(nx1, again)
# position: random navmesh point within RiseRadius (2 m) of the fall spot, +100 like the wave manager; else the spot itself
fl_ = b.aget('FallenLoc', VECT, ix, 1100, Y + 1300)
nav = b.lib(NAVSYS, 'K2_GetRandomReachablePointInRadius', [WC(), dict(V('Origin'), ref=True), V('RandomLocation', out=True),
            fl('Radius', default='200.000000'), ob('NavData', NAVDATA), {'name': 'FilterClass', 'cat': 'class', 'obj': NAVFILT}, bo('ReturnValue', out=True, default='false')],
            1500, Y + 1300, pure=True)
b.wire(fl_, nav, 'Origin'); b.wire(b.get('RiseRadius', DBL, 1300, Y + 1500), nav, 'Radius')
up = b.v2('Add_VectorVector', (nav, 'RandomLocation'), None, 1850, Y + 1300, db='0.000000,0.000000,100.000000')
up2 = b.v2('Add_VectorVector', fl_, None, 1850, Y + 1450, db='0.000000,0.000000,10.000000')
pos = b.selvec(up, up2, (nav, 'ReturnValue'), 2050, Y + 1350)
sp = spawn(b, P_RISEN, RISEN, transform(b, pos, 2250, Y + 1350), 1300, Y)
G.link(br3, 'else', sp, 'execute')
R = (sp, 'ReturnValue')
# rank multiplier: commander 2.0, else 1 + 0.25 * clamp(Rank - 1, 0, 3)  (Rank.Y 1 recruit, 2 veteran, 3 elite, 4 = max)
rk = b.aget('FallenRank', DBL, ix, 1500, Y + 1700)
cmd = b.icmp('EqualEqual_IntInt', kd, None, 1750, Y + 1900, db='2')
rmul = b.d2('Add_DoubleDouble', None, b.d2('Multiply_DoubleDouble', b.clamp(b.d2('Subtract_DoubleDouble', rk, None, 1750, Y + 1700, db='1.0'), '0.0', '3.0', 1950, Y + 1700), None, 2150, Y + 1700, db='0.25'), 2350, Y + 1700, da='1.0')
mult = b.self_(None, rmul, cmd, 2550, Y + 1750, da='2.0')
wd = b.i2d(b.get('LastWave', INT, 1900, Y + 2100), 2100, Y + 2100)
hpc = b.lib(CURVE, 'GetFloatValue', [fl('InTime', default='0.0'), fl('ReturnValue', out=True, default='0.0')], 2300, Y + 2100, pure=True, tag='HPMult')
G.nodes[-1][3][0].update({'hidden': False, 'dobj': C_HP})          # curve asset on the (visible) Target pin, as in the export
G.nodes[-1][2].insert(1, 'bIsConstFunc=True')
b.wire(wd, hpc, 'InTime')
dmc = b.lib(CURVE, 'GetFloatValue', [fl('InTime', default='0.0'), fl('ReturnValue', out=True, default='0.0')], 2300, Y + 2250, pure=True, tag='DmgMult')
G.nodes[-1][3][0].update({'hidden': False, 'dobj': C_DMG}); G.nodes[-1][2].insert(1, 'bIsConstFunc=True')
b.wire(wd, dmc, 'InTime')
hp = b.d2('Multiply_DoubleDouble', b.d2('Multiply_DoubleDouble', (hpc, 'ReturnValue'), b.get('BaseHP', DBL, 2300, Y + 2400), 2550, Y + 2100), mult, 2750, Y + 2100)
dmg = b.d2('Multiply_DoubleDouble', b.d2('Multiply_DoubleDouble', (dmc, 'ReturnValue'), b.get('BaseDamage', DBL, 2300, Y + 2550), 2550, Y + 2250), mult, 2750, Y + 2250)
# rest title: "A FALLEN <RANK> IS AT REST"
rn = b.selstr(None, None, b.dcmp('Less_DoubleDouble', rk, None, 1750, Y + 2700, db='3.5'), 1950, Y + 2700, da='ELITE', db='CHAMPION')
rn = b.selstr(None, rn, b.dcmp('Less_DoubleDouble', rk, None, 1750, Y + 2850, db='2.5'), 2150, Y + 2750, da='VETERAN')
rn = b.selstr(None, rn, b.dcmp('Less_DoubleDouble', rk, None, 1750, Y + 3000, db='1.5'), 2350, Y + 2800, da='RECRUIT')
rn = b.selstr(None, rn, cmd, 2550, Y + 2850, da='COMMANDER')
title = b.concat(b.concat(None, rn, 2750, Y + 2850, da='A FALLEN '), None, 2950, Y + 2850, db=' IS AT REST')
# the same init as the wave manager's normal walker (WV_54..WV_65), then the rank multiplier
x0 = 1700
n1 = b.setm('ZType', ZOMBIE, INT, None, R, x0, Y); G.nodes[-1][3][2]['default'] = '5'
n2 = b.setm('Runner', ZOMBIE, BOOL, None, R, x0 + 250, Y)
cm = b.getm('CharacterMovement', CHARC, ob('v', CMC), R, x0 + 250, Y + 250)
n3 = b.setm('MaxWalkSpeed', CMC, fl('v', default='110.0'), b.get('WalkSpeed', DBL, x0 + 450, Y + 400), cm, x0 + 500, Y)
sc = b.selvec(None, None, cmd, x0 + 700, Y + 300, da='1.200000,1.200000,1.200000', db='1.000000,1.000000,1.000000')
n4 = b.call(ACT, 'SetActorScale3D', [V('NewScale3D', default='1.000000,1.000000,1.000000')], x0 + 750, Y, target=R)
b.wire(sc, n4, 'NewScale3D')
n5 = b.setm('MaxHP', ZOMBIE, DBL, hp, R, x0 + 1000, Y)
n6 = b.setm('AttackDamage', ZOMBIE, DBL, dmg, R, x0 + 1250, Y)
n7 = b.setm('XPValue', ZOMBIE, INT, None, R, x0 + 1500, Y); G.nodes[-1][3][2]['default'] = '1'
n8 = b.setm('Rank', RISEN, DBL, rk, R, x0 + 1750, Y)
n9 = b.setm('Kind', RISEN, INT, kd, R, x0 + 2000, Y)
n10 = b.setm('ClothMat', RISEN, MATV, b.aget('FallenCloth', MATV, ix, x0 + 1800, Y + 450), R, x0 + 2250, Y)
n11 = b.setm('RankMult', RISEN, DBL, mult, R, x0 + 2500, Y)
n12 = b.setm('RestTitle', RISEN, STR, title, R, x0 + 2750, Y)
n14 = b.set('NextIdx', INT, b.i2('Add_IntInt', ix, None, x0 + 3000, Y + 300, db='1'), x0 + 3250, Y)
n15 = b.set('RiseLeft', INT, b.i2('Subtract_IntInt', b.get('RiseLeft', INT, x0 + 3250, Y + 450), None, x0 + 3450, Y + 400, db='1'), x0 + 3500, Y)
n16 = b.timer('RiseNext', x0 + 3750, Y, time=b.rnd('1.0', '1.5', x0 + 3600, Y + 300))
b.chain(sp, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n14, n15, n16)

# ---- ShowRestNotice(Title) / HideNotice: one banner at a time, hidden after NoticeTime ----
Y = 9200
b.event('ShowRestNotice', [S('Title')], 0, Y)
nw = b.get('NoticeWidget', ob('v', USERW), 250, Y + 300)
bv = b.branch(b.valid(nw, 450, Y + 300), 300, Y, 'IfOld')
G.link('ShowRestNotice', 'then', bv, 'execute')
rm = b.call(WIDGET, 'RemoveFromParent', [], 600, Y - 150, target=nw)
G.link(bv, 'then', rm, 'execute')
j = b.seq('NoticeJoin', 1, 850, Y)
G.link(rm, 'then', j, 'execute'); G.link(bv, 'else', j, 'execute')
pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], 950, Y + 300, pure=True)
cw = b.name('Banner')
G.node(cw, 'K2Node_CreateWidget', [], [ex(), ex('then', True), dict(CLSPIN('Class', USERW, cpath(P_WBP))), ob('ReturnValue', WBP, out=True), ob('OwningPlayer', PCON)], 1100, Y)
G.link(pc, 'ReturnValue', cw, 'OwningPlayer'); G.link(j, 'then_0', cw, 'execute')
W = (cw, 'ReturnValue')
tt = b.getm('TitleText', WBP, ob('v', TEXTB), W, 1350, Y + 300)
st1 = b.call(TEXTB, 'SetText', [{'name': 'InText', 'cat': 'text'}], 1400, Y, target=tt)
b.wire(b.text(('ShowRestNotice', 'Title'), 1350, Y + 450), st1, 'InText')
ct = b.getm('CountText', WBP, ob('v', TEXTB), W, 1650, Y + 300)
st2 = b.call(TEXTB, 'SetText', [{'name': 'InText', 'cat': 'text'}], 1700, Y, target=ct)
b.wire(b.text(None, 1650, Y + 450), st2, 'InText')
av = b.call(USERW, 'AddToViewport', [dict(it('ZOrder', default='19'), advanced=True)], 1950, Y, target=W)
sn = b.set('NoticeWidget', ob('v', USERW), W, 2200, Y)
th = b.timer('HideNotice', 2450, Y)
b.wire(b.get('NoticeTime', DBL, 2300, Y + 300), th, 'Time')
b.chain(cw, st1, st2, av, sn, th)
Y = 10000
b.event('HideNotice', [], 0, Y)
nw = b.get('NoticeWidget', ob('v', USERW), 250, Y + 300)
bh = b.branch(b.valid(nw, 450, Y + 300), 300, Y, 'IfShown')
G.link('HideNotice', 'then', bh, 'execute')
rm = b.call(WIDGET, 'RemoveFromParent', [], 600, Y, target=nw)
G.link(bh, 'then', rm, 'execute')

GRAPHS = {}
GRAPHS['BP_RisenDirector_graph.txt'] = G

# =====================================================================================================================
# 2) BP_ZombieRisen (new, child of BP_Zombie): all zombie logic is inherited. It hides the zombie mesh, the
#    KnightMesh (ShadowknightUE_SK, child of Mesh) follows it with Leader Pose. BeginPlay hides both meshes, sinks
#    the mesh RiseDepth and pauses the zombie AI; 0.05 s later (after the director has set Rank/Kind/ClothMat on the
#    spawned actor, same frame) Rise() applies the cloth (rank + cape) material, the overlay M_RisenOverlay
#    (commander: MI_RisenOverlay_Boss), shows the knight with a dust burst and starts the 1.2 s rise.
#    RestCheck: when Dead, the director shows the rest notice. (No call from the director into this BP: no cycle.)
# =====================================================================================================================
G = Graph(); b = B(G, 'r')
b.override('RisenBeginPlay', 'ReceiveBeginPlay', 0, 0)
par = b.name('ZombieBeginPlay')
G.node(par, 'K2Node_CallParentFunction', ['FunctionReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ZOMBIE],
       [ex(), ex('then', True), selfpin(ACT, hidden=True)], 250, 0)
mesh = b.get('Mesh', ob('v', SKEL), 450, 250)
hide = b.call(SCENE, 'SetHiddenInGame', [bo('NewHidden', default='true'), bo('bPropagateToChildren', default='false')], 550, 0, target=mesh)
tick = b.setm('VisibilityBasedAnimTickOption', SKIN, {'name': 'v', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EVisibilityBasedAnimTickOption\'"',
              'default': 'AlwaysTickPoseAndRefreshBones'}, None, mesh, 850, 0)
lpb = b.branch(b.get('UseLeaderPose', BOOL, 1050, 250), 1150, 0, 'IfLeader')
knight = b.get('KnightMesh', ob('v', SKEL), 1250, 300)
khide = b.call(SCENE, 'SetHiddenInGame', [bo('NewHidden', default='true'), bo('bPropagateToChildren', default='false')], 1000, -200, target=knight, tag='HideKnight')
lead = b.call(SKIN, 'SetLeaderPoseComponent', [ob('NewLeaderBoneComponent', SKIN), bo('bForceUpdate', default='true'), bo('bInFollowerShouldTickPose', default='false')], 1450, -150, target=knight)
b.wire(mesh, lead, 'NewLeaderBoneComponent')
b.chain('RisenBeginPlay', par, hide, khide, tick, lpb); G.link(lpb, 'then', lead, 'execute')
j0 = b.seq('LeaderJoin', 1, 1750, 0)
G.link(lead, 'then', j0, 'execute'); G.link(lpb, 'else', j0, 'execute')
# sink: remember the mesh offset, move it RiseDepth down, pause the zombie AI (Think timer) and stop the path
s_base = b.set('BaseRel', VECT, b.relloc(mesh, 1850, 350), 2000, 0)
low = b.v2('Subtract_VectorVector', (s_base, 'Output_Get'), b.vec(None, None, b.get('RiseDepth', DBL, 2100, 500), 2250, 450), 2450, 350)
sink = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], 2300, 0, target=mesh)
b.wire(low, sink, 'NewLocation')
pz = b.timer_fn('K2_PauseTimer', 'Think', 2600, 0)
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 2750, 300, PAWN, pure=True, const=True)
stp = b.call(CTRL, 'StopMovement', [], 2850, 0, target=(ctl, 'ReturnValue'))
rz = b.timer('Rise', 3100, 0, dtime='0.05')
b.chain((j0, 'then_0'), s_base, sink, pz, stp, rz)

# ---- Rise(): look, show the knight, dust, start RiseStep ----
Y = 800
b.event('Rise', [], 0, Y)
knight = b.get('KnightMesh', ob('v', SKEL), 200, Y + 300)
cloth = b.get('ClothMat', MATV, 200, Y + 450)
bc = b.branch(b.valid(cloth, 400, Y + 450), 300, Y, 'IfCloth')
G.link('Rise', 'then', bc, 'execute')
sm = b.call(PRIM, 'SetMaterial', [it('ElementIndex', default='2'), ob('Material', MATI)], 600, Y - 200, target=knight)
b.wire(cloth, sm, 'Material'); G.link(bc, 'then', sm, 'execute')
dm = b.call(PRIM, 'CreateDynamicMaterialInstance', [it('ElementIndex', default='2'), ob('SourceMaterial', MATI), N('OptionalName', 'None'), ob('ReturnValue', MID, out=True)], 600, Y + 150, target=knight)
G.link(bc, 'else', dm, 'execute')
sr = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', 'RankLevel'), fl('Value', default='0.0')], 900, Y + 150, target=(dm, 'ReturnValue'))
b.wire(b.get('Rank', DBL, 750, Y + 400), sr, 'Value'); G.link(dm, 'then', sr, 'execute')
j = b.seq('LookJoin', 1, 1200, Y)
G.link(sm, 'then', j, 'execute'); G.link(sr, 'then', j, 'execute')
cmd = b.icmp('EqualEqual_IntInt', b.get('Kind', INT, 1200, Y + 350), None, 1400, Y + 300, db='2')
bb = b.branch(cmd, 1450, Y, 'IfCommander')
G.link(j, 'then_0', bb, 'execute')
ob1 = b.call(MESHC, 'SetOverlayMaterial', [ob('NewOverlayMaterial', MATI)], 1700, Y - 200, target=knight)
b.wire(b.get('OverlayBossMat', MATV, 1550, Y - 300), ob1, 'NewOverlayMaterial'); G.link(bb, 'then', ob1, 'execute')
ob2 = b.call(MESHC, 'SetOverlayMaterial', [ob('NewOverlayMaterial', MATI)], 1700, Y + 150, target=knight)
b.wire(b.get('OverlayMat', MATV, 1550, Y + 300), ob2, 'NewOverlayMaterial'); G.link(bb, 'else', ob2, 'execute')
j2 = b.seq('RiseJoin', 1, 2000, Y)
G.link(ob1, 'then', j2, 'execute'); G.link(ob2, 'then', j2, 'execute')
show = b.call(SCENE, 'SetHiddenInGame', [bo('NewHidden', default='false'), bo('bPropagateToChildren', default='false')], 2200, Y, target=knight, tag='ShowKnight')
s_t0 = b.set('RiseT0', DBL, b.now(2350, Y + 300), 2500, Y)
feet = b.v2('Subtract_VectorVector', (b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 2600, Y + 300, ACT, pure=True, const=True), 'ReturnValue'), None,
            2800, Y + 300, db='0.000000,0.000000,80.000000')
fx = b.lib(GS, 'SpawnEmitterAtLocation', [WC(), dict(ob('EmitterTemplate', PSYS), dobj=P_SMOKE), V('Location'), st('Rotation', ROT, default='0, 0, 0'),
           V('Scale', default='0.800000,0.800000,0.800000'), bo('bAutoDestroy', default='true'),
           {'name': 'PoolingMethod', 'cat': 'byte', 'obj': ENUM('EPSCPoolMethod'), 'default': 'None'}, bo('bAutoActivateSystem', default='true'), ob('ReturnValue', PSC, out=True)], 2800, Y)
b.wire(feet, fx, 'Location')
rt = b.timer('RiseStep', 3100, Y, dtime='0.03', loop=True)
b.chain((j2, 'then_0'), show, s_t0, fx, rt)

# ---- RiseStep (0.03 s): mesh Z = Base - Depth * (1 - a)^2, a = clamp((now - T0) / RiseTime, 0, 1) ----
Y = 1900
b.event('RiseStep', [], 0, Y)
a = b.clamp(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', b.now(0, Y + 300), b.get('RiseT0', DBL, 0, Y + 450), 200, Y + 300),
                 b.get('RiseTime', DBL, 200, Y + 500), 400, Y + 350, db='1.0'), '0.0', '1.0', 600, Y + 350)
inv = b.d2('Subtract_DoubleDouble', None, a, 800, Y + 350, da='1.0')
off = b.d2('Multiply_DoubleDouble', b.d2('Multiply_DoubleDouble', inv, inv, 1000, Y + 350), b.get('RiseDepth', DBL, 1000, Y + 500), 1200, Y + 400)
nl = b.v2('Subtract_VectorVector', b.get('BaseRel', VECT, 1200, Y + 250), b.vec(None, None, off, 1400, Y + 450), 1600, Y + 300)
mesh = b.get('Mesh', ob('v', SKEL), 1400, Y + 150)
mv = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], 1650, Y, target=mesh)
b.wire(nl, mv, 'NewLocation'); G.link('RiseStep', 'then', mv, 'execute')
bd = b.branch(b.dcmp('GreaterEqual_DoubleDouble', a, None, 1800, Y + 300, db='1.0'), 1950, Y, 'IfRisen')
G.link(mv, 'then', bd, 'execute')
c1 = b.timer_fn('K2_ClearTimer', 'RiseStep', 2200, Y)
c2 = b.timer_fn('K2_UnPauseTimer', 'Think', 2450, Y)
rmv = b.call_self('ResumeMove', [], 2700, Y, ZOMBIE)
rc = b.timer('RestCheck', 2950, Y, dtime='0.25', loop=True)
G.link(bd, 'then', c1, 'execute'); b.chain(c1, c2, rmv, rc)

# ---- RestCheck (0.25 s): Dead -> overlay off, director notice ----
Y = 2700
b.event('RestCheck', [], 0, Y)
bdd = b.branch(b.get('Dead', BOOL, 100, Y + 250), 250, Y, 'IfDead')
G.link('RestCheck', 'then', bdd, 'execute')
c3 = b.timer_fn('K2_ClearTimer', 'RestCheck', 500, Y)
off_ = b.call(MESHC, 'SetOverlayMaterial', [ob('NewOverlayMaterial', MATI)], 750, Y, target=b.get('KnightMesh', ob('v', SKEL), 600, Y + 300))
df = b.actor_of(P_DIR, DIRECTOR, 1000, Y)
bdv = b.branch(b.valid((df, 'ReturnValue'), 1000, Y + 250), 1300, Y, 'IfDirector')
nt = b.call(DIRECTOR, 'ShowRestNotice', [S('Title')], 1550, Y, target=(df, 'ReturnValue'))
b.wire(b.get('RestTitle', STR, 1400, Y + 300), nt, 'Title')
G.link(bdd, 'then', c3, 'execute'); b.chain(c3, off_, df, bdv); G.link(bdv, 'then', nt, 'execute')
GRAPHS['BP_ZombieRisen_graph.txt'] = G

# =====================================================================================================================
# 3) Soldier hook (BP_SoldierSword EventGraph, death branch; Xbow + Commander inherit it).
#    FallIn -> find BP_RisenDirector (spawn it if none) -> ReportFallen(self) -> FallOut
#    Rewire: CX_447.then (Set State = dead) -> FallIn.execute ; FallOut.then_0 -> CX_549.execute (SetVisibility TargetArrow)
# =====================================================================================================================
G = Graph(); b = B(G, 'h')
b.seq('FallIn', 1, 0, 0)
fd = b.actor_of(P_DIR, DIRECTOR, 250, 0)
G.link('FallIn', 'then_0', fd, 'execute')
bh = b.branch(b.valid((fd, 'ReturnValue'), 250, 250), 550, 0, 'IfDirector')
G.link(fd, 'then', bh, 'execute')
me = b.self_node(700, 350)
r1 = b.call(DIRECTOR, 'ReportFallen', [ob('Soldier', ACT)], 850, -150, target=(fd, 'ReturnValue'))
b.wire(me, r1, 'Soldier'); G.link(bh, 'then', r1, 'execute')
sd = spawn(b, P_DIR, DIRECTOR, transform(b, None, 650, 550), 850, 150)
G.link(bh, 'else', sd, 'execute')
r2 = b.call(DIRECTOR, 'ReportFallen', [ob('Soldier', ACT)], 1150, 150, target=(sd, 'ReturnValue'))
b.wire(me, r2, 'Soldier'); G.link(sd, 'then', r2, 'execute')
b.seq('FallOut', 1, 1450, 0)
G.link(r1, 'then', 'FallOut', 'execute'); G.link(r2, 'then', 'FallOut', 'execute')
GRAPHS['Soldier_FallenHook_graph.txt'] = G


# =====================================================================================================================
# write + self-check (LinkedTo symmetry, unique pin ids, link targets exist, chk.py rules)
# =====================================================================================================================
def selfcheck(txt):
    pins, node, errs, ids = {}, None, [], set()
    for ln in txt.splitlines():
        m = re.match(r'Begin Object Class=\S+ Name="([^"]+)"', ln)
        if m: node = m.group(1); continue
        if 'CustomProperties Pin (' in ln:
            pid = re.search(r'PinId=(\w+)', ln).group(1)
            if pid in ids: errs.append('duplicate pin id ' + pid)
            ids.add(pid)
            lk = re.search(r'LinkedTo=\(([^)]*)\)', ln)
            L = [tuple(x.split()) for x in lk.group(1).split(',') if x.strip()] if lk else []
            pins[pid] = dict(node=node, name=re.search(r'PinName="([^"]*)"', ln).group(1), out='EGPD_Output' in ln,
                             cat=re.search(r'PinCategory="(\w*)"', ln).group(1), links=L)
    for pid, p in pins.items():
        for n2, p2 in p['links']:
            q = pins.get(p2)
            if q is None or q['node'] != n2: errs.append('dangling %s.%s -> %s %s' % (p['node'], p['name'], n2, p2)); continue
            if (p['node'], pid) not in [(a, b_) for a, b_ in q['links']]: errs.append('asymmetric %s.%s <-> %s.%s' % (p['node'], p['name'], n2, q['name']))
            if q['out'] == p['out']: errs.append('same-direction link %s.%s - %s.%s' % (p['node'], p['name'], n2, q['name']))
        if not p['out'] and p['cat'] != 'exec' and len(p['links']) > 1: errs.append('multi-source data input %s.%s' % (p['node'], p['name']))
        if p['out'] and p['cat'] == 'exec' and len(p['links']) > 1: errs.append('exec fan-out %s.%s' % (p['node'], p['name']))
    return errs

ok_all = True
for fn, g in GRAPHS.items():
    txt = g.render()
    errs = selfcheck(txt)
    with open(os.path.join(HERE, fn), 'w', newline='\r\n') as fh: fh.write(txt)
    print('%-30s nodes %3d  links %3d  selfcheck %s' % (fn, len(g.nodes), len(g.links), 'OK' if not errs else errs))
    ok_all &= not errs
sys.exit(0 if ok_all else 1)
