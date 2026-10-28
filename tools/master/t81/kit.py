import uuid
def g(): return uuid.uuid4().hex.upper()
TAIL = 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
CLS = lambda c: '"/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % c
BPC = lambda path, name: '"/Script/Engine.BlueprintGeneratedClass\'%s.%s_C\'"' % (path, name)
STRUCT = lambda s: '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.%s\'"' % s
TARGET = 'NSLOCTEXT("K2Node", "Target", "Target")'
class Graph:
    def __init__(self): self.nodes = []; self.links = []   # links: (nodeA, pinA, nodeB, pinB)
    def node(self, name, cls, props, pins, x=0, y=0):
        self.nodes.append((name, cls, props, pins, x, y)); return name
    def link(self, a, pa, b, pb): self.links.append((a, pa, b, pb))
    def render(self):
        ids = {}
        for n, c, props, pins, x, y in self.nodes:
            for p in pins: ids[(n, p['name'])] = g()
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
                s += 'PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,PinType.PinSubCategoryMemberReference=%s,PinType.PinValueType=(),PinType.ContainerType=%s,PinType.bIsReference=%s,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,' % (
                    p['cat'], p.get('sub', ''), p.get('obj', 'None'), p.get('mref', '()'), p.get('container', 'None'), 'True' if p.get('ref') else 'False')
                if p.get('default') is not None: s += 'DefaultValue="%s",' % p['default']
                if p.get('dobj'): s += 'DefaultObject="%s",' % p['dobj']
                L = linked.get((n, p['name']))
                if L: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in L)
                t = TAIL.replace('bHidden=False', 'bHidden=True') if p.get('hidden') else TAIL
                if p.get('advanced'): t = t.replace('bAdvancedView=False', 'bAdvancedView=True')
                out.append('   ' + s + t)
            for p in props:
                if p.startswith('CustomProperties UserDefinedPin'): out.append('   ' + p)
            out.append('End Object')
        return '\n'.join(out) + '\n'
# pin helpers
def ex(name='execute', out=False): return {'name': name, 'cat': 'exec', 'out': out}
def fl(name, out=False, default=None, sub='float', friendly=None, advanced=False): return {'name': name, 'cat': 'real', 'sub': sub, 'out': out, 'default': default, 'friendly': friendly, 'advanced': advanced}
def it(name, out=False, default=None): return {'name': name, 'cat': 'int', 'out': out, 'default': default}
def bo(name, out=False, default=None): return {'name': name, 'cat': 'bool', 'out': out, 'default': default}
def ob(name, cls, out=False, friendly=None, hidden=False): return {'name': name, 'cat': 'object', 'obj': cls, 'out': out, 'friendly': friendly, 'hidden': hidden}
def st(name, s, out=False, default=None): return {'name': name, 'cat': 'struct', 'obj': s, 'out': out, 'default': default}
def selfpin(cls, hidden=False): return ob('self', cls, friendly=TARGET, hidden=hidden)
# node helpers
def callfn(G, name, parent, member, pins, pure=False, const=False, x=0, y=0, selfcls=None, self_hidden=False):
    props = []
    if pure: props.append('bIsPureFunc=True')
    if const: props.append('bIsConstFunc=True')
    props.append('FunctionReference=(MemberParent=%s,MemberName="%s")' % (parent, member))
    allp = ([] if pure else [ex(), ex('then', True)]) + [selfpin(selfcls or parent, hidden=self_hidden)] + pins
    return G.node(name, 'K2Node_CallFunction', props, allp, x, y)
def mathfn(G, name, member, pins, x=0, y=0):
    return callfn(G, name, CLS('KismetMathLibrary'), member, pins, pure=True, x=x, y=y, self_hidden=True)
def varget(G, name, parent, member, cls_pin, out_pin, x=0, y=0, self_ctx=False):
    ref = 'VariableReference=(MemberName="%s",bSelfContext=True)' % member if self_ctx else 'VariableReference=(MemberParent=%s,MemberName="%s")' % (parent, member)
    return G.node(name, 'K2Node_VariableGet', [ref], [dict(out_pin, out=True), selfpin(cls_pin, hidden=self_ctx)], x, y)
def varset(G, name, parent, member, cls_pin, val_pin, x=0, y=0, self_ctx=False):
    ref = 'VariableReference=(MemberName="%s",bSelfContext=True)' % member if self_ctx else 'VariableReference=(MemberParent=%s,MemberName="%s")' % (parent, member)
    getp = dict(val_pin, name='Output_Get', out=True)
    return G.node(name, 'K2Node_VariableSet', [ref], [ex(), ex('then', True), val_pin, getp, selfpin(cls_pin, hidden=self_ctx)], x, y)
def branch(G, name, x=0, y=0):
    return G.node(name, 'K2Node_IfThenElse', [], [ex(), bo('Condition', default='true'), ex('then', True), ex('else', True)], x, y)
def cast(G, name, target_cls, out_name, x=0, y=0, pure=False):
    props = ['TargetType=%s' % target_cls] + (['bIsPureCast=True'] if pure else [])
    pins = ([] if pure else [ex(), ex('then', True), ex('CastFailed', True)]) + [ob('Object', '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"'), ob(out_name, target_cls, out=True), {'name': 'bSuccess', 'cat': 'bool', 'out': True, 'hidden': True}]
    return G.node(name, 'K2Node_DynamicCast', props, pins, x, y)
def sequence(G, name, n, x=0, y=0):
    return G.node(name, 'K2Node_ExecutionSequence', [], [ex()] + [ex('then_%d' % i, True) for i in range(n)], x, y)
