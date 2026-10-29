# #80 Army split (laptop2, 2026-10-29): generates the EventGraph paste of the new actor BP_ArmySplit.
#   python -I gen80.py     ->  BP_ArmySplit_graph.txt  (paste into the empty EventGraph of BP_ArmySplit)
# Built with the Master's node kit (tools/master/t81/kit.py) the same way #96's gen96.py is. Node/pin layouts the kit
# lacks are copied from the 10-28 exports (handoffs/exports/laptop2/gameplay) and the working commander-kit v2 paste.
#
# Events in the paste (rows top to bottom):
#   BeginPlay   bind OnTakeAnyDamage of every TentacleHit part of every tentacle (the same parts BP_TentacleVitals binds)
#   OnTentHit   the hero hit a part: remember it, and (re)engage when it's a new tentacle or no split is active
#   Engage      find the tentacle's vitals, save HoldPoint, Pick swords then crossbows, order 5 for all, guard ring
#   Pick        followers (Order.X 1 or 2, alive, not a commander) of one role, alternating guard / strike
#   Restore     give everyone still on our order 5 their old Order and Goal back, clear the teams
#   Tick (0.5s) end checks (vitals gone / dead, no hero hit for EndNoHitTime, hero > EndDistance) or StrikeStep
#   StrikeStep  strike goals (sword ring, step back during the slam, crossbow stand-off fan) + the strike attacks
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'master', 't81'))
from kit import *   # Graph, g, TAIL, CLS, BPC, STRUCT, TARGET, ex, branch, sequence, ...

# ---------------------------------------------------------------------------------------------------------------
# types and assets
# ---------------------------------------------------------------------------------------------------------------
ACT, SCN, CHAR, CTRL = CLS('Actor'), CLS('SceneComponent'), CLS('Character'), CLS('Controller')
OBJ = '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"'
KML, GS, KSL, KAL = CLS('KismetMathLibrary'), CLS('GameplayStatics'), CLS('KismetSystemLibrary'), CLS('KismetArrayLibrary')
VEC, ROT, XFORM = STRUCT('Vector'), STRUCT('Rotator'), STRUCT('Transform')
HIT = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.HitResult\'"'
SOLD = BPC('/Game/CastleDefender/Characters/Knight/BP_SoldierSword', 'BP_SoldierSword')
VITALS = BPC('/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals', 'BP_TentacleVitals')
TSTRIKE = BPC('/Game/CastleDefender/Gameplay/Tentacle/BPC_TentacleStrike', 'BPC_TentacleStrike')
BOLTC = BPC('/Game/CastleDefender/Characters/Knight/BP_SoldierBolt', 'BP_SoldierBolt')
ME = BPC('/Game/CastleDefender/Gameplay/Army/BP_ArmySplit', 'BP_ArmySplit')
SOLD_P = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword.BP_SoldierSword_C'
VITALS_P = '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals.BP_TentacleVitals_C'
TSTRIKE_P = '/Game/CastleDefender/Gameplay/Tentacle/BPC_TentacleStrike.BPC_TentacleStrike_C'
BOLT_P = '/Game/CastleDefender/Characters/Knight/BP_SoldierBolt.BP_SoldierBolt_C'
AM_SLASH1 = '/Game/CastleDefender/Gameplay/Castle/Combat/AM_Slash1.AM_Slash1'
AM_SLASH2 = '/Game/CastleDefender/Gameplay/Castle/Combat/AM_Slash2.AM_Slash2'
AM_XBOW = '/Game/CastleDefender/Gameplay/Crossbow/Anims/AM_Xbow_Aim.AM_Xbow_Aim'
SND_SWORD = '/Game/Audio/Kenney/SC_SwordHit.SC_SwordHit'
SND_XBOW = '/Game/CastleDefender/Gameplay/Crossbow/Audio/SFX_XbowFire.SFX_XbowFire'
MACRO_FOREACH = ('MacroGraphReference=(MacroGraph="/Script/Engine.EdGraph\'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop\'",'
                 'GraphBlueprint="/Script/Engine.Blueprint\'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros\'",GraphGuid=99DBFD5540A796041F72A5A9DA655026)')
XBOW_SPREAD_DEG = '6.6'      # angle between crossbow stand-off spots: 1300 cm * tan(6.6 deg) = 150 cm apart

# ---------------------------------------------------------------------------------------------------------------
# kit.Graph with the extra pin flags the real exports use (bIsConst, bIsUObjectWrapper, bDefaultValueIsIgnored)
# and self-checks (unique pin ids, every link end exists, output->input, matching exec-ness)
# ---------------------------------------------------------------------------------------------------------------
class G2(Graph):
    def check(self):
        pins = {}
        for n, c, props, ps, x, y in self.nodes:
            for p in ps:
                assert (n, p['name']) not in pins, 'duplicate pin %s.%s' % (n, p['name'])
                pins[(n, p['name'])] = p
        assert len({n for n, *_ in self.nodes}) == len(self.nodes), 'duplicate node name'
        for a, pa, b, pb in self.links:
            A, Bp = pins.get((a, pa)), pins.get((b, pb))
            assert A is not None, 'missing pin %s.%s' % (a, pa)
            assert Bp is not None, 'missing pin %s.%s' % (b, pb)
            assert bool(A.get('out')) != bool(Bp.get('out')), 'same direction %s.%s -> %s.%s' % (a, pa, b, pb)
            assert (A['cat'] == 'exec') == (Bp['cat'] == 'exec'), 'exec/data mix %s.%s -> %s.%s' % (a, pa, b, pb)
        return pins

    def render(self):
        self.check()
        ids = {}
        for n, c, props, pins, x, y in self.nodes:
            for p in pins: ids[(n, p['name'])] = g()
        assert len(set(ids.values())) == len(ids)
        linked = {}
        for a, pa, b, pb in self.links:
            linked.setdefault((a, pa), []).append((b, ids[(b, pb)])); linked.setdefault((b, pb), []).append((a, ids[(a, pa)]))
        out = []
        for n, c, props, pins, x, y in self.nodes:
            out.append('Begin Object Class=/Script/BlueprintGraph.%s Name="%s"' % (c, n))
            for p in props:
                if not p.startswith('CustomProperties UserDefinedPin'): out.append('   ' + p)
            out.append('   NodePosX=%d' % x); out.append('   NodePosY=%d' % y); out.append('   NodeGuid=%s' % g())
            for p in pins:
                s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (ids[(n, p['name'])], p['name'])
                if p.get('friendly'): s += 'PinFriendlyName=%s,' % p['friendly']
                if p.get('out'): s += 'Direction="EGPD_Output",'
                s += ('PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,PinType.PinSubCategoryMemberReference=%s,'
                      'PinType.PinValueType=(),PinType.ContainerType=%s,PinType.bIsReference=%s,PinType.bIsConst=%s,PinType.bIsWeakPointer=False,'
                      'PinType.bIsUObjectWrapper=%s,PinType.bSerializeAsSinglePrecisionFloat=False,') % (
                    p['cat'], p.get('sub', ''), p.get('obj') or 'None', p.get('mref', '()'), p.get('container', 'None'),
                    'True' if p.get('ref') else 'False', 'True' if p.get('const') else 'False', 'True' if p.get('wrapper') else 'False')
                if p.get('default') is not None: s += 'DefaultValue="%s",' % p['default']
                if p.get('dobj'): s += 'DefaultObject="%s",' % p['dobj']
                L = linked.get((n, p['name']))
                if L: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in L)
                t = TAIL
                if p.get('hidden'): t = t.replace('bHidden=False', 'bHidden=True')
                if p.get('advanced'): t = t.replace('bAdvancedView=False', 'bAdvancedView=True')
                if p.get('ignored'): t = t.replace('bDefaultValueIsIgnored=False', 'bDefaultValueIsIgnored=True')
                out.append('   ' + s + t)
            for p in props:
                if p.startswith('CustomProperties UserDefinedPin'): out.append('   ' + p)
            out.append('End Object')
        return '\n'.join(out) + '\n'

# pin constructors (kwargs pass straight into the pin dict: out, default, dobj, friendly, hidden, advanced, ref, const, wrapper, container)
def P(name, cat, **k): d = {'name': name, 'cat': cat}; d.update(k); return d
def EX(name='execute', out=False): return P(name, 'exec', out=out)
def D(name, **k): return P(name, 'real', sub='double', **dict({'default': None if k.get('out') else '0.0'}, **k))
def F(name, **k): return P(name, 'real', sub='float', **dict({'default': None if k.get('out') else '0.0'}, **k))
def I(name, **k): return P(name, 'int', **dict({'default': None if k.get('out') else '0'}, **k))
def BO(name, **k): return P(name, 'bool', **dict({'default': None if k.get('out') else 'false'}, **k))
def O(name, cls, **k): return P(name, 'object', obj=cls, **k)
def V(name, **k): return P(name, 'struct', obj=VEC, **dict({'default': None if k.get('out') else '0, 0, 0'}, **k))
def R(name, **k): return P(name, 'struct', obj=ROT, **dict({'default': None if k.get('out') else '0, 0, 0'}, **k))
def NM(name, default): return P(name, 'name', default=default)
def CL(name, cls, dobj): return P(name, 'class', obj=cls, dobj=dobj)
DEFOBJ = lambda lib: '/Script/Engine.Default__%s' % lib
WC = lambda: O('WorldContextObject', OBJ, const=True, hidden=True)


class B:
    """builder on kit.Graph (pattern of gen96.B): pure nodes return (node, pin) handles, exec nodes return names."""
    def __init__(s, G, prefix=''): s.G, s.p, s.n = G, prefix, 0
    def name(s, tag): s.n += 1; return '%s%s_%d' % (s.p, tag, s.n)
    def wire(s, src, node, pin):
        if src is not None: s.G.link(src[0], src[1], node, pin)
    def ex(s, a, b, apin='then', bpin='execute'): s.G.link(a, apin, b, bpin)
    def chain(s, *nodes):
        for a, b in zip(nodes, nodes[1:]):
            s.G.link(a[0] if isinstance(a, tuple) else a, a[1] if isinstance(a, tuple) else 'then',
                     b[0] if isinstance(b, tuple) else b, b[1] if isinstance(b, tuple) else 'execute')

    # ---- generic call: ins = [(pin, src)], outs = [pin] ----
    def call(s, parent, member, ins, outs, x, y, pure=False, const=False, lib=None, selfsrc=None, selfctx=False, props=(), tag=None):
        n = s.name(tag or member[:12])
        pr = (['bIsPureFunc=True'] if pure else []) + (['bIsConstFunc=True'] if const else [])
        pr.append('FunctionReference=(MemberName="%s",bSelfContext=True)' % member if selfctx else
                  'FunctionReference=(MemberParent=%s,MemberName="%s")' % (parent, member))
        pr += list(props)
        sp = O('self', parent if not selfctx else ME, friendly=TARGET)
        if lib: sp.update(dobj=DEFOBJ(lib), hidden=True)
        elif selfctx: sp.update(hidden=True)
        pins = ([] if pure else [EX(), EX('then', True)]) + [sp] + [p for p, _ in ins] + [dict(o, out=True) for o in outs]
        s.G.node(n, 'K2Node_CallFunction', pr, pins, x, y)
        for p, src in ins: s.wire(src, n, p['name'])
        s.wire(selfsrc, n, 'self')
        return n
    def m(s, member, ins, out, x, y):           # KismetMathLibrary pure node -> (node, out pin)
        n = s.call(KML, member, ins, [out], x, y, pure=True, lib='KismetMathLibrary'); return (n, out['name'])

    # ---- math shorthands ----
    def d2(s, member, a, b, x, y, da='0.0', db='0.0'): return s.m(member, [(D('A', default=da), a), (D('B', default=db), b)], D('ReturnValue', out=True), x, y)
    def dcmp(s, member, a, b, x, y, da='0.0', db='0.0'): return s.m(member, [(D('A', default=da), a), (D('B', default=db), b)], BO('ReturnValue', out=True), x, y)
    def i2(s, member, a, b, x, y, da='0', db='0'): return s.m(member, [(I('A', default=da), a), (I('B', default=db), b)], I('ReturnValue', out=True), x, y)
    def icmp(s, member, a, b, x, y, da='0', db='0'): return s.m(member, [(I('A', default=da), a), (I('B', default=db), b)], BO('ReturnValue', out=True), x, y)
    def b2(s, member, a, b, x, y): return s.m(member, [(BO('A'), a), (BO('B'), b)], BO('ReturnValue', out=True), x, y)
    def bnot(s, a, x, y): return s.m('Not_PreBool', [(BO('A'), a)], BO('ReturnValue', out=True), x, y)
    def i2d(s, a, x, y): return s.m('Conv_IntToDouble', [(I('InInt'), a)], D('ReturnValue', out=True), x, y)
    def absd(s, a, x, y): return s.m('Abs', [(D('A'), a)], D('ReturnValue', out=True), x, y)
    def seld(s, a, b, pick, x, y, da='0.0', db='0.0'):
        return s.m('SelectFloat', [(D('A', default=da), a), (D('B', default=db), b), (BO('bPickA'), pick)], D('ReturnValue', out=True), x, y)
    def v2(s, member, a, b, x, y, db='0, 0, 0'): return s.m(member, [(V('A'), a), (V('B', default=db), b)], V('ReturnValue', out=True), x, y)
    def makev(s, X, Y, Z, x, y, dx='0.0', dz='0.0'):
        return s.m('MakeVector', [(D('X', default=dx), X), (D('Y'), Y), (D('Z', default=dz), Z)], V('ReturnValue', out=True), x, y)
    def breakv(s, v, x, y):
        n = s.call(KML, 'BreakVector', [(V('InVec'), v)], [D('X'), D('Y'), D('Z')], x, y, pure=True, lib='KismetMathLibrary')
        return {c: (n, c) for c in 'XYZ'}
    def dist2d(s, a, b, x, y): return s.m('Vector_Distance2D', [(V('V1'), a), (V('V2'), b)], D('ReturnValue', out=True), x, y)
    def lookat(s, a, b, x, y):
        return s.m('FindLookAtRotation', [(V('Start', ref=True, const=True, ignored=True), a), (V('Target', ref=True, const=True, ignored=True), b)],
                   R('ReturnValue', out=True), x, y)
    def yaw(s, rot, x, y):
        n = s.call(KML, 'BreakRotator', [(R('InRot', friendly='"Rotation"'), rot)],
                   [F('Roll', friendly='"X (Roll)"'), F('Pitch', friendly='"Y (Pitch)"'), F('Yaw', friendly='"Z (Yaw)"')], x, y, pure=True, lib='KismetMathLibrary')
        return (n, 'Yaw')
    def yawrot(s, yawsrc, x, y):
        return s.m('MakeRotator', [(F('Roll', friendly='"X (Roll)"'), None), (F('Pitch', friendly='"Y (Pitch)"'), None), (F('Yaw', friendly='"Z (Yaw)"'), yawsrc)],
                   R('ReturnValue', out=True), x, y)
    def rand(s, x, y): return s.m('RandomFloat', [], D('ReturnValue', out=True), x, y)
    def randbool(s, x, y): return s.m('RandomBool', [], BO('ReturnValue', out=True), x, y)
    def objeq(s, a, b, x, y): return s.m('EqualEqual_ObjectObject', [(O('A', OBJ), a), (O('B', OBJ), b)], BO('ReturnValue', out=True), x, y)
    def near(s, a, val, x, y, tol='0.5'):
        """|a - val| < tol"""
        return s.dcmp('Less_DoubleDouble', s.absd(s.d2('Subtract_DoubleDouble', a, None, x, y, db=val), x + 180, y), None, x + 330, y, db=tol)
    def polar(s, center, ang, r, x, y):
        """center + (cos ang * r, sin ang * r, 0)"""
        cx = s.d2('Multiply_DoubleDouble', s.m('DegCos', [(D('A'), ang)], D('ReturnValue', out=True), x, y), r, x + 180, y)
        sy = s.d2('Multiply_DoubleDouble', s.m('DegSin', [(D('A'), ang)], D('ReturnValue', out=True), x, y + 110), r, x + 180, y + 110)
        return s.v2('Add_VectorVector', center, s.makev(cx, sy, None, x + 360, y), x + 540, y)

    # ---- actors / library ----
    def hero(s, x, y):
        n = s.call(GS, 'GetPlayerCharacter', [(WC(), None), (I('PlayerIndex'), None)], [O('ReturnValue', CHAR)], x, y, pure=True, lib='GameplayStatics')
        return (n, 'ReturnValue')
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [], [V('ReturnValue')], x, y, pure=True, const=True, selfsrc=actor); return (n, 'ReturnValue')
    def parent(s, actor, x, y):
        n = s.call(ACT, 'GetAttachParentActor', [], [O('ReturnValue', ACT)], x, y, pure=True, const=True, selfsrc=actor); return (n, 'ReturnValue')
    def tag(s, actor, tagname, x, y):
        n = s.call(ACT, 'ActorHasTag', [(NM('Tag', tagname), None)], [BO('ReturnValue')], x, y, pure=True, const=True, selfsrc=actor); return (n, 'ReturnValue')
    def valid(s, obj, x, y):
        n = s.call(KSL, 'IsValid', [(O('Object', OBJ, const=True), obj)], [BO('ReturnValue')], x, y, pure=True, lib='KismetSystemLibrary'); return (n, 'ReturnValue')
    def now(s, x, y):
        n = s.call(GS, 'GetTimeSeconds', [(WC(), None)], [D('ReturnValue')], x, y, pure=True, lib='GameplayStatics'); return (n, 'ReturnValue')
    def allof(s, cls_handle, cls_path, x, y):
        return s.call(GS, 'GetAllActorsOfClass', [(WC(), None), (CL('ActorClass', ACT, cls_path), None)],
                      [O('OutActors', cls_handle, container='Array')], x, y, lib='GameplayStatics', tag='GetAll')
    def foreach(s, arr, elem_cls, x, y):
        n = s.name('ForEach')
        s.G.node(n, 'K2Node_MacroInstance', [MACRO_FOREACH, 'ResolvedWildcardType=(PinCategory="object",PinSubCategoryObject=%s)' % elem_cls],
                 [EX('Exec'), O('Array', elem_cls, container='Array'), EX('LoopBody', True), O('Array Element', elem_cls, out=True),
                  I('Array Index', out=True, default=None), EX('Completed', True)], x, y)
        s.wire(arr, n, 'Array')
        return n
    def branch(s, cond, x, y):
        n = s.name('Branch'); branch(s.G, n, x, y); s.wire(cond, n, 'Condition'); return n

    # ---- variables ----
    def get(s, var, pin, x, y):
        n = s.name('Get' + var)
        s.G.node(n, 'K2Node_VariableGet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % var],
                 [dict(pin, name=var, out=True, default=None), O('self', ME, friendly=TARGET, hidden=True)], x, y)
        return (n, var)
    def set(s, var, pin, src, x, y, default=None):
        n = s.name('Set' + var)
        vp = dict(pin, name=var)
        if default is not None: vp['default'] = default
        s.G.node(n, 'K2Node_VariableSet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % var],
                 [EX(), EX('then', True), vp, dict(pin, name='Output_Get', out=True, default=None), O('self', ME, friendly=TARGET, hidden=True)], x, y)
        s.wire(src, n, var)
        return n
    def oget(s, parent, member, pin, obj, x, y):
        """member variable of another object (soldier Order/Goal/State, SceneComponent RelativeLocation, vitals Health, strike State)"""
        n = s.name('Get' + member)
        s.G.node(n, 'K2Node_VariableGet', ['VariableReference=(MemberParent=%s,MemberName="%s")' % (parent, member)],
                 [dict(pin, name=member, out=True, default=None), O('self', parent, friendly=TARGET)], x, y)
        s.wire(obj, n, 'self')
        return (n, member)
    def comp(s, soldier, cname, x, y): return s.oget(SOLD, cname, O('c', SCN), soldier, x, y)
    def relloc(s, compsrc, x, y): return s.oget(SCN, 'RelativeLocation', V('v'), compsrc, x, y)
    def setrel(s, compsrc, vec, x, y):
        n = s.call(SCN, 'K2_SetRelativeLocation', [(V('NewLocation'), vec), (BO('bSweep'), None)], [], x, y, selfsrc=compsrc, tag='SetRelLoc')
        # pins in export order: ... bSweep, SweepHitResult (out), bTeleport
        nd = s.G.nodes[-1]; nd[3].extend([P('SweepHitResult', 'struct', obj=HIT, out=True), BO('bTeleport', default='true')])
        return n

    # ---- arrays (K2Node_CallArrayFunction / K2Node_GetArrayItem, layout of the commander-kit v2 paste) ----
    def _arr(s, member, var, elem, extra_ins, outs, x, y, pure=False):
        n = s.name(member)
        arrp = dict(elem, name='TargetArray', container='Array', ref=True, default=None)
        if pure: arrp['const'] = True
        pins = ([] if pure else [EX(), EX('then', True)]) + [O('self', KAL, dobj=DEFOBJ('KismetArrayLibrary'), hidden=True), arrp] + \
               [p for p, _ in extra_ins] + [dict(o, out=True) for o in outs]
        s.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="%s")' % (KAL, member)], pins, x, y)
        s.wire(s.get(var, dict(elem, container='Array'), x - 200, y + 140), n, 'TargetArray')
        for p, src in extra_ins: s.wire(src, n, p['name'])
        return n
    def add(s, var, elem, item, x, y):
        return s._arr('Array_Add', var, elem, [(dict(elem, name='NewItem', ref=True, const=True, default=None), item)], [I('ReturnValue', default=None)], x, y)
    def clear(s, var, elem, x, y): return s._arr('Array_Clear', var, elem, [], [], x, y)
    def length(s, var, elem, x, y):
        n = s._arr('Array_Length', var, elem, [], [I('ReturnValue', default=None)], x, y, pure=True); return (n, 'ReturnValue')
    def item(s, var, elem, idx, x, y):
        n = s.name('Get' + var + 'Item')
        s.G.node(n, 'K2Node_GetArrayItem', [], [dict(elem, name='Array', container='Array', default=None), I('Dimension 1'),
                                                dict(elem, name='Output', out=True, ref=True, default=None)], x, y)
        s.wire(s.get(var, dict(elem, container='Array'), x - 200, y), n, 'Array'); s.wire(idx, n, 'Dimension 1')
        return (n, 'Output')

    # ---- events ----
    def event(s, name, params, x, y):
        props = ['CustomFunctionName="%s"' % name]
        for p in params:
            t = 'PinCategory="%s"' % p['cat'] + (',PinSubCategory="%s"' % p['sub'] if p.get('sub') else '') + \
                (',PinSubCategoryObject=%s' % p['obj'] if p.get('obj') else '') + (',bIsConst=True' if p.get('const') else '')
            props.append('CustomProperties UserDefinedPin (PinName="%s",PinType=(%s),DesiredPinDirection=EGPD_Output)' % (p['name'], t))
        s.G.node(name, 'K2Node_CustomEvent', props,
                 [P('OutputDelegate', 'delegate', out=True, mref='(MemberParent=%s,MemberName="%s")' % (ME, name)), EX('then', True)]
                 + [dict(p, out=True, default=None) for p in params], x, y)
        return name
    def call_self(s, event, x, y, ins=()):
        n = s.name('Call' + event)
        s.G.node(n, 'K2Node_CallFunction', ['FunctionReference=(MemberName="%s",bSelfContext=True)' % event],
                 [EX(), EX('then', True), O('self', ME, friendly=TARGET, hidden=True)] + [p for p, _ in ins], x, y)
        for p, src in ins: s.wire(src, n, p['name'])
        return n
    def actor_event(s, n, member, extra, x, y):
        s.G.node(n, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ACT, member), 'bOverrideFunction=True'],
                 [P('OutputDelegate', 'delegate', out=True, mref='(MemberParent=%s,MemberName="%s")' % (ACT, member)), EX('then', True)] + extra, x, y)
        return n


G = G2(); b = B(G)
SOLDP = O('v', SOLD)                    # element types
VECP = V('v', default=None)
DBL, INT, BOOL = D('v'), I('v'), BO('v')
ACTP, VITP = O('v', ACT), O('v', VITALS)

# =====================================================================================================================
# BeginPlay: tick every 0.5 s; bind OnTentHit to OnTakeAnyDamage of every TentacleHit part of every tentacle
#   (BP_TentacleVitals -> Get Attach Parent Actor -> Get Attached Actors -> Actor Has Tag TentacleHit: exactly what
#    BP_TentacleVitals itself binds, so we see the same hits it does)
# =====================================================================================================================
Y = 0
b.actor_event('EvBeginPlay', 'ReceiveBeginPlay', [], 0, Y)
tick = b.call(ACT, 'SetActorTickInterval', [(F('TickInterval', default='0.5'), None)], [], 250, Y, selfctx=True, tag='SetTickInterval')
allv = b.allof(VITALS, VITALS_P, 550, Y)
lv = b.foreach((allv, 'OutActors'), VITALS, 900, Y)
parts = b.call(ACT, 'GetAttachedActors', [(BO('bResetArray', default='true'), None), (BO('bRecursivelyIncludeAttachedActors'), None)],
               [O('OutActors', ACT, container='Array')], 1000, Y + 300, pure=True, const=True, selfsrc=b.parent((lv, 'Array Element'), 800, Y + 300))
lp = b.foreach((parts, 'OutActors'), ACT, 1300, Y)
br = b.branch(b.tag((lp, 'Array Element'), 'TentacleHit', 1350, Y + 300), 1650, Y)
G.node('BindHit', 'K2Node_AddDelegate', ['DelegateReference=(MemberParent=%s,MemberName="OnTakeAnyDamage")' % ACT],
       [EX(), EX('then', True), O('self', ACT, friendly='NSLOCTEXT("K2Node", "BaseMCDelegateSelfPinName", "Target")'),
        P('Delegate', 'delegate', friendly='NSLOCTEXT("K2Node", "PinFriendlyDelegatetName", "Event")', ref=True, const=True,
          mref='(MemberParent="/Script/CoreUObject.Package\'/Script/Engine\'",MemberName="TakeAnyDamageSignature__DelegateSignature")')], 1950, Y)
b.chain('EvBeginPlay', tick, allv, (lv, 'Exec'))
b.ex(lv, lp, 'LoopBody', 'Exec'); b.ex(lp, br, 'LoopBody'); b.ex(br, 'BindHit')
G.link(lp, 'Array Element', 'BindHit', 'self')

# =====================================================================================================================
# OnTentHit (OnTakeAnyDamage signature): only hits whose DamageCauser is the hero count.
#   LastHitAt = now, HitPart = DamagedActor; if no split is active or it's another tentacle: Restore, Engage(parent)
# =====================================================================================================================
Y = 900
b.event('OnTentHit', [O('DamagedActor', ACT), F('Damage'), O('DamageType', CLS('DamageType'), const=True), O('InstigatedBy', CTRL), O('DamageCauser', ACT)], 0, Y)
G.link('OnTentHit', 'OutputDelegate', 'BindHit', 'Delegate')
br1 = b.branch(b.objeq(('OnTentHit', 'DamageCauser'), b.hero(250, Y + 300), 450, Y + 250), 350, Y)
s1 = b.set('LastHitAt', DBL, b.now(600, Y + 300), 650, Y)
s2 = b.set('HitPart', ACTP, ('OnTentHit', 'DamagedActor'), 900, Y)
tent = b.parent(('OnTentHit', 'DamagedActor'), 900, Y + 300)
same = b.b2('BooleanAND', b.get('Active', BOOL, 1100, Y + 420), b.objeq(tent, b.get('Tentacle', ACTP, 1100, Y + 520), 1300, Y + 450), 1500, Y + 350)
br2 = b.branch(same, 1200, Y)
c1 = b.call_self('Restore', 1500, Y)
c2 = b.call_self('Engage', 1750, Y, ins=[(O('Tent', ACT), tent)])
b.chain('OnTentHit', br1, s1, s2, br2); b.ex(br2, c1, 'else'); b.ex(c1, c2)

# =====================================================================================================================
# Engage(Tent): Tentacle = Tent, TentVitals = the BP_TentacleVitals attached to it, HoldPoint = hero position,
#   if the vitals exist and Health > 0: Pick(swords) then Pick(crossbows). Fewer than 2 followers: Restore (nothing was changed yet).
#   Else Active = true, every member gets order 5 (Order.Y/Z kept), guards get ring slots around HoldPoint, StrikeStep.
# =====================================================================================================================
Y = 1900
b.event('Engage', [O('Tent', ACT)], 0, Y)
e1 = b.set('Tentacle', ACTP, ('Engage', 'Tent'), 250, Y)
e2 = b.set('TentVitals', VITP, None, 500, Y)                       # clear first: a part without a tentacle gives None
e3 = b.set('HoldPoint', VECP, b.loc(b.hero(550, Y + 300), 750, Y + 300), 750, Y)
av = b.allof(VITALS, VITALS_P, 1000, Y)
lv2 = b.foreach((av, 'OutActors'), VITALS, 1300, Y)
brv = b.branch(b.objeq(b.parent((lv2, 'Array Element'), 1350, Y + 300), ('Engage', 'Tent'), 1550, Y + 300), 1650, Y)
e4 = b.set('TentVitals', VITP, (lv2, 'Array Element'), 1900, Y)
b.chain('Engage', e1, e2, e3, av, (lv2, 'Exec')); b.ex(lv2, brv, 'LoopBody'); b.ex(brv, e4)
p1 = b.call_self('Pick', 1700, Y + 650, ins=[(BO('WantXbow'), None)])
p2 = b.call_self('Pick', 1950, Y + 650, ins=[(BO('WantXbow', default='true'), None)])
enough = b.icmp('GreaterEqual_IntInt', b.length('Members', SOLDP, 2150, Y + 900), None, 2350, Y + 900, db='2')
brn = b.branch(enough, 2200, Y + 650)
rs = b.call_self('Restore', 2450, Y + 450)
e5 = b.set('Active', BOOL, None, 2450, Y + 650, default='true')
# only a living tentacle with vitals splits the army (hits on a dead one do nothing)
TVe = b.get('TentVitals', VITP, 1400, Y + 950)
bvv = b.branch(b.valid(TVe, 1400, Y + 800), 1150, Y + 650)
bva = b.branch(b.dcmp('Greater_DoubleDouble', b.oget(VITALS, 'Health', D('v'), TVe, 1600, Y + 950), None, 1800, Y + 950), 1400, Y + 650)
b.ex(lv2, bvv, 'Completed'); b.chain(bvv, bva, p1, p2, brn, e5); b.ex(brn, rs, 'else')
# every member: Order = (5, Order.Y, Order.Z)
lm = b.foreach(b.get('Members', dict(SOLDP, container='Array'), 2500, Y + 1100), SOLD, 2750, Y + 650)
oc = b.comp((lm, 'Array Element'), 'Order', 2800, Y + 950)
ov = b.breakv(b.relloc(oc, 3000, Y + 1050), 3200, Y + 1050)
so = b.setrel(oc, b.makev(None, ov['Y'], ov['Z'], 3400, Y + 1050, dx='5.0'), 3100, Y + 650)   # X = 5: hold at Goal
b.ex(e5, lm, 'then', 'Exec'); b.ex(lm, so, 'LoopBody')
# guards: Goal = HoldPoint + ring slot i of N at GuardRadius
lg = b.foreach(b.get('Guard', dict(SOLDP, container='Array'), 3500, Y + 1300), SOLD, 3700, Y + 650)
ang = b.d2('Multiply_DoubleDouble', b.i2d((lg, 'Array Index'), 3700, Y + 1000),
           b.d2('Divide_DoubleDouble', None, b.i2d(b.length('Guard', SOLDP, 3750, Y + 1250), 3900, Y + 1150), 4050, Y + 1100, da='360.0'), 4200, Y + 1000)
gp = b.polar(b.get('HoldPoint', VECP, 4250, Y + 1300), ang, b.get('GuardRadius', DBL, 4250, Y + 1400), 4400, Y + 1000)
sg = b.setrel(b.comp((lg, 'Array Element'), 'Goal', 4700, Y + 850), gp, 5000, Y + 650)
b.ex(lm, lg, 'Completed', 'Exec'); b.ex(lg, sg, 'LoopBody')
st = b.call_self('StrikeStep', 5000, Y + 450)
b.ex(lg, st, 'Completed')

# =====================================================================================================================
# Pick(WantXbow): every alive BP_SoldierSword (crossbows are a child class) of that role with Order.X 1 or 2 that
#   isn't a commander: save Order and Goal, then alternate guard / strike over both calls (PickN), odd counts guard.
# =====================================================================================================================
Y = 3900
b.event('Pick', [BO('WantXbow')], 0, Y)
gs = b.allof(SOLD, SOLD_P, 250, Y)
ls = b.foreach((gs, 'OutActors'), SOLD, 600, Y)
S = (ls, 'Array Element')
ordv = b.relloc(b.comp(S, 'Order', 600, Y + 300), 800, Y + 300)
ox = b.breakv(ordv, 1000, Y + 300)['X']
foll = b.b2('BooleanOR', b.near(ox, '1.0', 1200, Y + 250), b.near(ox, '2.0', 1200, Y + 400), 1750, Y + 300)
alive = b.dcmp('Less_DoubleDouble', b.breakv(b.relloc(b.comp(S, 'State', 600, Y + 550), 800, Y + 550), 1000, Y + 550)['Z'], None, 1200, Y + 600, db='0.5')
role = b.m('EqualEqual_BoolBool', [(BO('A'), b.tag(S, 'Xbow', 1000, Y + 750)), (BO('B'), ('Pick', 'WantXbow'))], BO('ReturnValue', out=True), 1250, Y + 750)
notcmd = b.bnot(b.tag(S, 'Commander', 1000, Y + 900), 1250, Y + 900)
ok = b.b2('BooleanAND', b.b2('BooleanAND', foll, alive, 1950, Y + 400), b.b2('BooleanAND', role, notcmd, 1450, Y + 800), 2150, Y + 500)
brp = b.branch(ok, 1000, Y)
a1 = b.add('Members', SOLDP, S, 2300, Y)
a2 = b.add('PrevOrder', VECP, ordv, 2600, Y)
a3 = b.add('PrevGoal', VECP, b.relloc(b.comp(S, 'Goal', 2550, Y + 450), 2750, Y + 450), 2900, Y)
odd = b.icmp('EqualEqual_IntInt', b.i2('Percent_IntInt', b.get('PickN', INT, 2950, Y + 350), None, 3150, Y + 300, db='2'), None, 3350, Y + 300, db='1')
bro = b.branch(odd, 3200, Y)
a4 = b.add('Strike', SOLDP, S, 3650, Y - 150)
a5 = b.add('Guard', SOLDP, S, 3650, Y + 200)
sn = b.set('PickN', INT, b.i2('Add_IntInt', b.get('PickN', INT, 3850, Y + 450), None, 4050, Y + 450, db='1'), 4000, Y)
b.chain('Pick', gs, (ls, 'Exec')); b.ex(ls, brp, 'LoopBody'); b.chain(brp, a1, a2, a3, bro)
b.ex(bro, a4); b.ex(bro, a5, 'else'); b.ex(a4, sn); b.ex(a5, sn)

# =====================================================================================================================
# Restore: members still on our order 5 get their saved Order and Goal back (a member the player re-ordered keeps the
#   new order). Then clear the teams, Active = false, PickN = 0.
# =====================================================================================================================
Y = 5300
b.event('Restore', [], 0, Y)
lr = b.foreach(b.get('Members', dict(SOLDP, container='Array'), 0, Y + 250), SOLD, 250, Y)
M = (lr, 'Array Element')
brr = b.branch(b.valid(M, 300, Y + 300), 550, Y)
roc = b.comp(M, 'Order', 600, Y + 450)
brr2 = b.branch(b.near(b.breakv(b.relloc(roc, 800, Y + 450), 1000, Y + 450)['X'], '5.0', 1200, Y + 450), 850, Y)
r1 = b.setrel(roc, b.item('PrevOrder', VECP, (lr, 'Array Index'), 1350, Y + 300), 1300, Y)
r2 = b.setrel(b.comp(M, 'Goal', 1400, Y + 750), b.item('PrevGoal', VECP, (lr, 'Array Index'), 1650, Y + 650), 1650, Y)
b.chain('Restore', (lr, 'Exec')); b.ex(lr, brr, 'LoopBody'); b.chain(brr, brr2, r1, r2)
k = [b.clear(v, e, 2000 + i * 250, Y + 300) for i, (v, e) in enumerate([('Members', SOLDP), ('Strike', SOLDP), ('Guard', SOLDP), ('PrevOrder', VECP), ('PrevGoal', VECP)])]
r3 = b.set('Active', BOOL, None, 3250, Y + 300)
r4 = b.set('PickN', INT, None, 3500, Y + 300)
b.ex(lr, k[0], 'Completed'); b.chain(*k, r3, r4)

# =====================================================================================================================
# Tick (interval 0.5 s, set in BeginPlay): while Active, end when the tentacle or its vitals are gone, Health <= 0,
#   the hero hasn't hit it for EndNoHitTime, or the hero is more than EndDistance away; otherwise StrikeStep.
# =====================================================================================================================
Y = 6500
b.actor_event('EvTick', 'ReceiveTick', [F('DeltaSeconds', out=True, default=None)], 0, Y)
bt1 = b.branch(b.get('Active', BOOL, 50, Y + 250), 250, Y)
TV = b.get('TentVitals', VITP, 250, Y + 450)
TN = b.get('Tentacle', ACTP, 250, Y + 600)
bt2 = b.branch(b.b2('BooleanAND', b.valid(TN, 450, Y + 350), b.valid(TV, 450, Y + 250), 650, Y + 300), 550, Y)
dead = b.dcmp('LessEqual_DoubleDouble', b.oget(VITALS, 'Health', D('v'), TV, 700, Y + 450), None, 900, Y + 450)
idle = b.dcmp('Greater_DoubleDouble', b.d2('Subtract_DoubleDouble', b.now(700, Y + 600), b.get('LastHitAt', DBL, 700, Y + 700), 900, Y + 600),
              b.get('EndNoHitTime', DBL, 900, Y + 750), 1100, Y + 600)
far = b.dcmp('Greater_DoubleDouble', b.dist2d(b.loc(b.hero(700, Y + 850), 900, Y + 850), b.loc(TN, 900, Y + 950), 1100, Y + 850),
             b.get('EndDistance', DBL, 1100, Y + 1000), 1300, Y + 850)
ended = b.b2('BooleanOR', b.b2('BooleanOR', dead, idle, 1300, Y + 500), far, 1500, Y + 600)
bt3 = b.branch(ended, 1050, Y)
tr1 = b.call_self('Restore', 900, Y - 200)
tr2 = b.call_self('Restore', 1350, Y - 200)
ts = b.call_self('StrikeStep', 1350, Y + 150)
b.chain('EvTick', bt1, bt2, bt3); b.ex(bt2, tr1, 'else'); b.ex(bt3, tr2); b.ex(bt3, ts, 'else')

# =====================================================================================================================
# StrikeStep: for each strike member still alive and on order 5:
#   sword Goal    = Tentacle + ring slot i of N at StrikeRadius (StepBackRadius while BPC_TentacleStrike.State != 0)
#   crossbow Goal = Tentacle + XbowStandoff toward the hero, fanned XBOW_SPREAD_DEG per slot around that direction
#   attack (random roll per 0.5 s): sword when in reach and no slam, crossbow when within stand-off + 4 m.
#   Face the tentacle; sword: AM_Slash1/2 + SC_SwordHit; crossbow: AM_Xbow_Aim + SFX_XbowFire + BP_SoldierBolt at
#   HitPart (life span = distance / 5000); then ApplyDamage(HitPart, SwordDamage | XbowDamage, causer = soldier).
# =====================================================================================================================
Y = 8000
b.event('StrikeStep', [], 0, Y)
T = b.loc(b.get('Tentacle', ACTP, 0, Y + 900), 200, Y + 900)
sc = b.call(ACT, 'GetComponentByClass', [(P('ComponentClass', 'class', obj=CLS('ActorComponent'), wrapper=True, dobj=TSTRIKE_P), None)],
            [O('ReturnValue', TSTRIKE)], 200, Y + 1050, pure=True, const=True, selfsrc=b.get('TentVitals', VITP, 0, Y + 1050))
slam = b.icmp('NotEqual_IntInt', b.oget(TSTRIKE, 'State', I('v'), (sc, 'ReturnValue'), 450, Y + 1050), None, 650, Y + 1050)
radius = b.seld(b.get('StepBackRadius', DBL, 650, Y + 1200), b.get('StrikeRadius', DBL, 650, Y + 1300), slam, 850, Y + 1150)
yawTH = b.yaw(b.lookat(T, b.loc(b.hero(200, Y + 1450), 400, Y + 1450), 600, Y + 1400), 800, Y + 1400)
Nd = b.i2d(b.length('Strike', SOLDP, 200, Y + 1650), 400, Y + 1650)
lk = b.foreach(b.get('Strike', dict(SOLDP, container='Array'), 0, Y + 250), SOLD, 250, Y)
S = (lk, 'Array Element')
bk1 = b.branch(b.valid(S, 300, Y + 300), 550, Y)
alive = b.dcmp('Less_DoubleDouble', b.breakv(b.relloc(b.comp(S, 'State', 550, Y + 400), 750, Y + 400), 950, Y + 400)['Z'], None, 1150, Y + 400, db='0.5')
ours = b.near(b.breakv(b.relloc(b.comp(S, 'Order', 550, Y + 550), 750, Y + 550), 950, Y + 550)['X'], '5.0', 1150, Y + 550)
bk2 = b.branch(b.b2('BooleanAND', alive, ours, 1550, Y + 450), 850, Y)
isX = b.tag(S, 'Xbow', 1000, Y + 750)
Id = b.i2d((lk, 'Array Index'), 1000, Y + 900)
angS = b.d2('Multiply_DoubleDouble', Id, b.d2('Divide_DoubleDouble', None, Nd, 1200, Y + 1000, da='360.0'), 1400, Y + 900)
slot = b.d2('Subtract_DoubleDouble', Id, b.d2('Multiply_DoubleDouble', b.d2('Subtract_DoubleDouble', Nd, None, 1200, Y + 1150, db='1.0'), None, 1400, Y + 1150, db='0.5'), 1600, Y + 1050)
angX = b.d2('Add_DoubleDouble', yawTH, b.d2('Multiply_DoubleDouble', slot, None, 1800, Y + 1100, db=XBOW_SPREAD_DEG), 2000, Y + 1050)
ang = b.seld(angX, angS, isX, 2200, Y + 900)
r = b.seld(b.get('XbowStandoff', DBL, 2000, Y + 1250), radius, isX, 2200, Y + 1100)
goal = b.polar(T, ang, r, 2400, Y + 900)
sgk = b.setrel(b.comp(S, 'Goal', 2700, Y + 700), goal, 1150, Y)
b.chain('StrikeStep', (lk, 'Exec')); b.ex(lk, bk1, 'LoopBody'); b.chain(bk1, bk2, sgk)
# attack roll
SL = b.loc(S, 1300, Y + 1700)
dist = b.dist2d(SL, T, 1500, Y + 1700)
chance = b.seld(b.get('XbowShotChance', DBL, 1500, Y + 1850), b.get('SwordHitChance', DBL, 1500, Y + 1950), isX, 1700, Y + 1850)
reach = b.seld(b.d2('Add_DoubleDouble', b.get('XbowStandoff', DBL, 1500, Y + 2100), None, 1700, Y + 2100, db='400.0'),
               b.d2('Add_DoubleDouble', b.get('StrikeRadius', DBL, 1500, Y + 2250), None, 1700, Y + 2250, db='200.0'), isX, 1900, Y + 2150)
roll = b.dcmp('Less_DoubleDouble', b.rand(1900, Y + 1850), chance, 2100, Y + 1850)
inr = b.dcmp('Less_DoubleDouble', dist, reach, 2100, Y + 2050)
free = b.b2('BooleanOR', isX, b.bnot(slam, 1900, Y + 2400), 2100, Y + 2350)
attack = b.b2('BooleanAND', b.b2('BooleanAND', roll, inr, 2300, Y + 1950), free, 2500, Y + 2100)
ba = b.branch(attack, 3000, Y)
face = b.call(ACT, 'K2_SetActorRotation', [(R('NewRotation'), b.yawrot(b.yaw(b.lookat(SL, T, 3000, Y + 300), 3200, Y + 300), 3400, Y + 300)),
                                           (BO('bTeleportPhysics'), None)], [BO('ReturnValue')], 3300, Y, selfsrc=S, tag='FaceTentacle')
bx = b.branch(isX, 3600, Y)
b.chain(sgk, ba, face, bx)
# crossbow: aim montage, fire sound, bolt from chest height toward the hit part
def montage(asset, x, y):
    return b.call(CHAR, 'PlayAnimMontage', [(O('AnimMontage', CLS('AnimMontage'), dobj=asset), None), (F('InPlayRate', default='1.000000'), None),
                                            (P('StartSectionName', 'name', default='None'), None)],
                  [F('ReturnValue')], x, y, selfsrc=S, tag='Montage')
def sound(asset, vol, x, y):
    n = b.call(GS, 'PlaySoundAtLocation', [(WC(), None), (O('Sound', CLS('SoundBase'), dobj=asset), None), (V('Location'), SL),
                                           (R('Rotation', advanced=True), None), (F('VolumeMultiplier', default=vol, advanced=True), None),
                                           (F('PitchMultiplier', default='1.000000', advanced=True), None), (F('StartTime', default='0.000000', advanced=True), None),
                                           (O('AttenuationSettings', CLS('SoundAttenuation'), advanced=True), None),
                                           (O('ConcurrencySettings', CLS('SoundConcurrency'), advanced=True), None),
                                           (O('OwningActor', ACT, const=True, advanced=True), None),
                                           (O('InitialParams', CLS('InitialActiveSoundParams'), const=True, advanced=True), None)],
               [], x, y, lib='GameplayStatics', props=['AdvancedPinDisplay=Hidden'], tag='Sound')
    return n
mx = montage(AM_XBOW, 3900, Y - 400)
sx = sound(SND_XBOW, '0.700000', 4200, Y - 400)
muzzle = b.v2('Add_VectorVector', SL, None, 3900, Y - 700, db='0.000000,0.000000,45.000000')
aim = b.lookat(muzzle, b.loc(b.get('HitPart', ACTP, 3900, Y - 900), 4100, Y - 900), 4300, Y - 800)
xf = b.m('MakeTransform', [(V('Location'), muzzle), (R('Rotation'), aim), (V('Scale', default='1.000000,1.000000,1.000000'), None)],
         P('ReturnValue', 'struct', obj=XFORM, out=True), 4500, Y - 750)
G.node('SpawnBolt', 'K2Node_SpawnActorFromClass', ['AdvancedPinDisplay=Hidden'],
       [EX(), EX('then', True), CL('Class', ACT, BOLT_P), O('ReturnValue', BOLTC, out=True), P('SpawnTransform', 'struct', obj=XFORM),
        P('CollisionHandlingOverride', 'byte', obj='"/Script/CoreUObject.Enum\'/Script/Engine.ESpawnActorCollisionHandlingMethod\'"', default='AlwaysSpawn'),
        P('TransformScaleMethod', 'byte', obj='"/Script/CoreUObject.Enum\'/Script/Engine.ESpawnActorScaleMethod\'"', default='SelectDefaultAtRuntime', advanced=True),
        O('Owner', ACT, advanced=True), O('Instigator', CLS('Pawn'), wrapper=True)], 4500, Y - 400)
G.link(xf[0], xf[1], 'SpawnBolt', 'SpawnTransform')
life = b.m('FMax', [(D('A'), b.d2('Divide_DoubleDouble', dist, None, 4600, Y - 150, db='5000.0')), (D('B', default='0.050000'), None)], D('ReturnValue', out=True), 4800, Y - 150)
sls = b.call(ACT, 'SetLifeSpan', [(F('InLifespan'), life)], [], 4850, Y - 400, selfsrc=('SpawnBolt', 'ReturnValue'))
b.ex(bx, mx); b.chain(mx, sx, 'SpawnBolt', sls)
# sword: one of the two slashes, hit sound
bs = b.branch(b.randbool(3700, Y + 450), 3900, Y + 300)
m1 = montage(AM_SLASH1, 4200, Y + 200)
m2 = montage(AM_SLASH2, 4200, Y + 500)
ss = sound(SND_SWORD, '0.800000', 4550, Y + 300)
b.ex(bx, bs, 'else'); b.ex(bs, m1); b.ex(bs, m2, 'else'); b.ex(m1, ss); b.ex(m2, ss)
# damage on the hit part (BP_TentacleVitals listens on the parts, not on the tentacle actor)
dmg = b.seld(b.get('XbowDamage', DBL, 4900, Y + 350), b.get('SwordDamage', DBL, 4900, Y + 450), isX, 5100, Y + 350)
ad = b.call(GS, 'ApplyDamage', [(O('DamagedActor', ACT), b.get('HitPart', ACTP, 5100, Y + 200)), (F('BaseDamage'), dmg), (O('EventInstigator', CTRL), None),
                                (O('DamageCauser', ACT), S), (P('DamageTypeClass', 'class', obj=CLS('DamageType'), wrapper=True), None)],
            [F('ReturnValue')], 5350, Y, lib='GameplayStatics', tag='ApplyDamage')
b.ex(sls, ad); b.ex(ss, ad)

out = os.path.join(HERE, 'BP_ArmySplit_graph.txt')
open(out, 'w', newline='\r\n').write(G.render())
print('BP_ArmySplit: nodes', len(G.nodes), 'links', len(G.links), '->', out)
