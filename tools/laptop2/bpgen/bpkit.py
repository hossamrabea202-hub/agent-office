# bpkit: the shared Blueprint-paste builder (B class + constants) lifted from gen41.py (laptop2, 2026-10-30).
#   python gen41.py   ->  BP_RisenDirector_graph.txt   (EventGraph of the NEW actor BP_RisenDirector: fallen list, wave rise)
#                         BP_ZombieRisen_graph.txt     (EventGraph of the NEW BP_ZombieRisen, child of BP_Zombie)
#                         Soldier_FallenHook_graph.txt (7 nodes for BP_SoldierSword's death branch: FallIn .. FallOut)
# Uses the Master's node kit (tools/master/t81/kit.py) the same way #96's gen96.py does. Node/pin layouts that the kit
# does not have were copied from the 2026-10-28 exports (handoffs/exports/laptop2/gameplay + checkking).
import os, re, sys
sys.dont_write_bytecode = True      # keep the kit folder clean
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "master", "t81"))
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

