"""kit2: helpers on top of t3dlib for regenerating Blueprint graphs as paste text."""
import os, re
import t3dlib as T
W = os.path.dirname(os.path.abspath(__file__))
T.T3D = os.path.join(W, 't3d'); T._FILES.clear()

def C(path):  # class object path literal
    return "/Script/CoreUObject.Class'%s'" % path
KML = C('/Script/Engine.KismetMathLibrary'); KMLD = '/Script/Engine.Default__KismetMathLibrary'
GSL = C('/Script/Engine.GameplayStatics'); GSLD = '/Script/Engine.Default__GameplayStatics'
KSL = C('/Script/Engine.KismetSystemLibrary'); KSLD = '/Script/Engine.Default__KismetSystemLibrary'
KSTR = C('/Script/Engine.KismetStringLibrary'); KSTRD = '/Script/Engine.Default__KismetStringLibrary'
KTXT = C('/Script/Engine.KismetTextLibrary'); KTXTD = '/Script/Engine.Default__KismetTextLibrary'
KMAT = C('/Script/Engine.KismetMaterialLibrary'); KMATD = '/Script/Engine.Default__KismetMaterialLibrary'
AIL = C('/Script/AIModule.AIBlueprintHelperLibrary'); AILD = '/Script/AIModule.Default__AIBlueprintHelperLibrary'
NAV = C('/Script/NavigationSystem.NavigationSystemV1'); NAVD = '/Script/NavigationSystem.Default__NavigationSystemV1'
ACTOR = C('/Script/Engine.Actor'); PAWN = C('/Script/Engine.Pawn'); CHAR = C('/Script/Engine.Character')
SC = C('/Script/Engine.SceneComponent'); PRIM = C('/Script/Engine.PrimitiveComponent'); SMC = C('/Script/Engine.StaticMeshComponent')
SKC = C('/Script/Engine.SkeletalMeshComponent'); CMC = C('/Script/Engine.CharacterMovementComponent')
MID = C('/Script/Engine.MaterialInstanceDynamic'); MATI = C('/Script/Engine.MaterialInterface'); MPCC = C('/Script/Engine.MaterialParameterCollection')
OBJ = C('/Script/CoreUObject.Object'); CLS = C('/Script/CoreUObject.Class')
VEC = "/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"; ROT = "/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Rotator'"
LCOL = "/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.LinearColor'"; XFORM = "/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Transform'"
HIT = "/Script/CoreUObject.ScriptStruct'/Script/Engine.HitResult'"; TIMER = "/Script/CoreUObject.ScriptStruct'/Script/Engine.TimerHandle'"
def BPC(path):  # '/Game/.../BP_X' -> generated class literal
    n = path.rsplit('/', 1)[1]
    return "/Script/Engine.BlueprintGeneratedClass'%s.%s_C'" % (path, n)
F = ('real', False, 'float'); FO = ('real', True, 'float')

class G(T.Graph):
    def __init__(self, selfcls):
        super().__init__(); self.selfcls = selfcls
    def byname(self, n):
        return next(x for x in self.nodes if x.name == n)
    def prop(self, n, key):
        for s in n.props:
            if s.startswith(key): return s
        return ''
    def pure(self, lib, libd, name, pins, x=0, y=0): return T.spec_call(self, lib, name, pins, x, y, pure=True, lib_default=libd)
    def call(self, lib, libd, name, pins, x=0, y=0): return T.spec_call(self, lib, name, pins, x, y, pure=False, lib_default=libd)
    def mcall(self, parent, name, pins, x=0, y=0, pure=False, selfctx=False):
        ref = 'FunctionReference=(MemberParent="%s",MemberName="%s")' % (parent, name) if not selfctx else 'FunctionReference=(MemberName="%s",bSelfContext=True)' % name
        lines = (['bIsPureFunc=True'] if pure else []) + [ref]
        if not pure: lines += [T.pin_line('execute', 'exec'), T.pin_line('then', 'exec', out=True)]
        lines.append(T.pin_line('self', 'object', subobj=parent if not selfctx else self.selfcls, friendly='Target'))
        for spec in pins:
            kw = dict(zip(('out', 'sub', 'subobj', 'default', 'obj'), spec[2:]))
            lines.append(T.pin_line(spec[0], spec[1], **kw))
        return self.add('/Script/BlueprintGraph.K2Node_CallFunction', '\n'.join(lines), None, x, y)
    def vget(self, name, cat, subobj, parent=None, x=0, y=0, external=False):
        if external:
            ref = 'VariableReference=(MemberParent="%s",MemberName="%s")' % (parent, name)
            selfpin = T.pin_line('self', 'object', subobj=parent, friendly='Target')
        else:
            ref = 'VariableReference=(MemberName="%s",%sbSelfContext=True)' % (name, ('MemberParent="%s",' % parent) if parent else '')
            selfpin = T.pin_line('self', 'object', subobj=self.selfcls, hidden=True, friendly='Target')
        return self.add('/Script/BlueprintGraph.K2Node_VariableGet', '\n'.join([ref, T.pin_line(name, cat, out=True, subobj=subobj), selfpin]), None, x, y)
    def vset(self, name, cat, subobj=None, parent=None, x=0, y=0, external=False, default=None):
        if external:
            ref = 'VariableReference=(MemberParent="%s",MemberName="%s")' % (parent, name)
            selfpin = T.pin_line('self', 'object', subobj=parent, friendly='Target')
        else:
            ref = 'VariableReference=(MemberName="%s",%sbSelfContext=True)' % (name, ('MemberParent="%s",' % parent) if parent else '')
            selfpin = T.pin_line('self', 'object', subobj=self.selfcls, hidden=True, friendly='Target')
        return self.add('/Script/BlueprintGraph.K2Node_VariableSet', '\n'.join([ref, T.pin_line('execute', 'exec'), T.pin_line('then', 'exec', out=True),
                        T.pin_line(name, cat, subobj=subobj, default=default), T.pin_line('Output_Get', cat, out=True, subobj=subobj), selfpin]), None, x, y)
    def branch(self, x=0, y=0):
        return self.add('/Script/BlueprintGraph.K2Node_IfThenElse', '\n'.join([T.pin_line('execute', 'exec'), T.pin_line('Condition', 'bool', default='true'), T.pin_line('then', 'exec', out=True, friendly='true'), T.pin_line('else', 'exec', out=True, friendly='false')]), None, x, y)
    def selfnode(self, x=0, y=0):
        return self.add('/Script/BlueprintGraph.K2Node_Self', T.pin_line('self', 'object', out=True, subobj=self.selfcls), None, x, y)
    def custom_event(self, name, x=0, y=0, extra_pins=()):
        lines = ['CustomFunctionName="%s"' % name, T.pin_line('OutputDelegate', 'delegate', out=True), T.pin_line('then', 'exec', out=True)]
        return self.add('/Script/BlueprintGraph.K2Node_CustomEvent', '\n'.join(lines), None, x, y)
    # math shorthands
    def f2(self, name, a=0.0, b=0.0, x=0, y=0):
        return self.pure(KML, KMLD, name, [('A',) + F + (None, str(a)), ('B',) + F + (None, str(b)), ('ReturnValue',) + FO], x, y)
    def cmp(self, name, a=0.0, b=0.0, x=0, y=0):
        return self.pure(KML, KMLD, name, [('A',) + F + (None, str(a)), ('B',) + F + (None, str(b)), ('ReturnValue', 'bool', True)], x, y)
    def b2(self, name, x=0, y=0):
        return self.pure(KML, KMLD, name, [('A', 'bool', False, '', None, 'false'), ('B', 'bool', False, '', None, 'false'), ('ReturnValue', 'bool', True)], x, y)
    def bnot(self, x=0, y=0):
        return self.pure(KML, KMLD, 'Not_PreBool', [('A', 'bool', False, '', None, 'false'), ('ReturnValue', 'bool', True)], x, y)
    def breakvec(self, x=0, y=0):
        return self.pure(KML, KMLD, 'BreakVector', [('InVec', 'struct', False, '', VEC), ('X',) + FO, ('Y',) + FO, ('Z',) + FO], x, y)
    def makevec(self, xv=0.0, yv=0.0, zv=0.0, x=0, y=0):
        return self.pure(KML, KMLD, 'MakeVector', [('X',) + F + (None, str(xv)), ('Y',) + F + (None, str(yv)), ('Z',) + F + (None, str(zv)), ('ReturnValue', 'struct', True, '', VEC)], x, y)
    def actorloc(self, x=0, y=0):  # self location (pure, self context)
        return self.mcall(ACTOR, 'K2_GetActorLocation', [('ReturnValue', 'struct', True, '', VEC)], x, y, pure=True)
    def loc_of(self, x=0, y=0):  # location of linked actor
        return self.mcall(ACTOR, 'K2_GetActorLocation', [('ReturnValue', 'struct', True, '', VEC)], x, y, pure=True)
    def dist_to(self, x=0, y=0):
        return self.mcall(ACTOR, 'GetDistanceTo', [('OtherActor', 'object', False, '', ACTOR), ('ReturnValue',) + FO], x, y, pure=True)
    def relloc(self, x=0, y=0):
        # USceneComponent::GetRelativeLocation is not a UFUNCTION in 5.3 (a pasted CallFunction is silently dropped):
        # read the RelativeLocation property instead; its output pin is aliased as 'ReturnValue' (see _p below)
        return self.add('/Script/BlueprintGraph.K2Node_VariableGet', '\n'.join([
            'VariableReference=(MemberParent="%s",MemberName="RelativeLocation")' % SC,
            T.pin_line('RelativeLocation', 'struct', out=True, subobj=VEC), T.pin_line('self', 'object', subobj=SC, friendly='Target')]), None, x, y)
    def setrelloc(self, x=0, y=0):
        return self.mcall(SC, 'K2_SetRelativeLocation', [('NewLocation', 'struct', False, '', VEC), ('bSweep', 'bool', False, '', None, 'false'), ('SweepHitResult', 'struct', True, '', HIT), ('bTeleport', 'bool', False, '', None, 'true')], x, y)

_orig_p = T.Node.p
def _p(self, name):
    if name == 'ReturnValue' and not any(q.name == 'ReturnValue' for q in self.pins) and any(q.name == 'RelativeLocation' for q in self.pins):
        name = 'RelativeLocation'
    return _orig_p(self, name)
T.Node.p = _p

def link(a, ap, b, bp): T.link(a, ap, b, bp)
def chain(*ns): T.chain(*ns)
def arrayify(node, pin):
    p = node.p(pin); p.line = p.line.replace('PinType.ContainerType=None', 'PinType.ContainerType=Array')
def setpin_obj(node, pin, subobj):
    p = node.p(pin); p.line = re.sub(r'PinType\.PinSubCategoryObject=[^,]+', 'PinType.PinSubCategoryObject="%s"' % subobj, p.line, 1)

def drop_stale(g, keep_classes=('K2Node_CustomEvent', 'K2Node_Event', 'EdGraphNode_Comment', 'K2Node_FunctionEntry', 'K2Node_EnhancedInputAction', 'K2Node_InputKey')):
    n0 = len(g.nodes)
    g.nodes = [n for n in g.nodes if any(p.links for p in n.pins) or any(k in n.cls for k in keep_classes)]
    return n0 - len(g.nodes)

def consumers(g, node, pin):
    """[(other_node, other_pin_name)] linked to node.pin"""
    out = []
    for tn, tid in node.p(pin).links:
        o = g.byname(tn)
        out.append((o, next(p.name for p in o.pins if p.id == tid)))
    return out

def relink_source(g, consumer, cpin, newsrc, newpin):
    """replace whatever feeds consumer.cpin with newsrc.newpin"""
    consumer.unlink(cpin)
    T.link(newsrc, newpin, consumer, cpin)

def source_of(g, node, pin):
    p = node.p(pin)
    if not p.links: return None, None
    tn, tid = p.links[0]
    o = g.byname(tn)
    return o, next(q.name for q in o.pins if q.id == tid)

def member_name(n):
    for s in n.props:
        m = re.search(r'(?:FunctionReference|VariableReference|EventReference)=\([^)]*MemberName="([^"]+)"', s)
        if m: return m.group(1)
        m = re.search(r'CustomFunctionName="([^"]+)"', s)
        if m: return m.group(1)
    return ''
