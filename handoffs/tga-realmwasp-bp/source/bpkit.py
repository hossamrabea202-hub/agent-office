# bpkit: build Blueprint EventGraph paste files (T3D) by cloning real node blocks from a live full-asset export.
# Cloning keeps every engine-written pin exactly as UE 5.3 serialises it; only names, PinIds, positions, links and
# chosen defaults change. Nodes the exports don't contain are made with kit-style pins (Codex's kit.py format, #161).
import re, uuid
def g(): return uuid.uuid4().hex.upper()
TAIL = 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'

class Export:
    def __init__(self, path):
        src = open(path, encoding='utf-8', errors='replace').read()
        self.blocks = {}
        for name, mod, cls, body in re.findall(r'Begin Object Name="([^"]+)" ExportPath="/Script/(\w+)\.(\w+)\'[^"]*:\w+\.[^"\']*\'"\n(.*?)\n\s*End Object', src, re.S):
            if 'CustomProperties Pin' in body: self.blocks[name] = (mod, cls, [l.strip() for l in body.split('\n')])
    def find(self, cls=None, member=None, extra=None):
        for n, (mod, c, lines) in self.blocks.items():
            body = '\n'.join(lines)
            if cls and c != cls: continue
            if member and ('MemberName="%s"' % member) not in body: continue
            if extra and extra not in body: continue
            if 'SubPins=' in body or 'ParentPin=' in body: continue
            return n
        raise KeyError('no template %s %s %s' % (cls, member, extra))

class Node:
    def __init__(self, name, mod, cls, props, pins, x, y):
        self.name, self.mod, self.cls, self.props, self.x, self.y = name, mod, cls, props, x, y
        self.pins = pins            # list of dicts: name, out, id, line (template line without PinId/LinkedTo)
    def pin(self, pname, out=None):
        c = [p for p in self.pins if p['name'] == pname and (out is None or p['out'] == out)]
        if not c: raise KeyError('%s has no pin %s (has %s)' % (self.name, pname, [p['name'] for p in self.pins]))
        return c[0]
    def set_default(self, pname, value=None, obj=None):
        p = self.pin(pname, False); line = re.sub(r'DefaultValue="[^"]*",', '', p['line']); line = re.sub(r'DefaultObject="[^"]*",', '', line)
        ins = ''
        if value is not None: ins += 'DefaultValue="%s",' % value
        if obj is not None: ins += 'DefaultObject="%s",' % obj
        p['line'] = line.replace('PersistentGuid=', ins + 'PersistentGuid=', 1); return self
    def set_prop(self, key, val):
        self.props = [l for l in self.props if not l.startswith(key + '=')] + ['%s=%s' % (key, val)]; return self
    def sub_prop(self, old, new):
        self.props = [l.replace(old, new) for l in self.props]; return self
    def retype(self, pname, old, new):
        p = self.pin(pname); p['line'] = p['line'].replace(old, new); return self

class Graph:
    def __init__(self, prefix): self.nodes = {}; self.links = []; self.prefix = prefix; self.n = 0
    def _name(self, tag): self.n += 1; return '%s_%s%d' % (self.prefix, tag, self.n)
    def clone(self, ex, tname, x, y, tag='N'):
        mod, cls, lines = ex.blocks[tname]
        props = [l for l in lines if not l.startswith('CustomProperties Pin') and not l.startswith('NodePos') and not l.startswith('NodeGuid')]
        pins = []
        for l in lines:
            if not l.startswith('CustomProperties Pin'): continue
            nm = re.search(r'PinName="([^"]*)"', l).group(1); out = 'Direction="EGPD_Output"' in l
            l2 = re.sub(r'LinkedTo=\([^)]*\),', '', l); l2 = re.sub(r'PinId=\w+,', 'PinId=@ID@,', l2, count=1)
            pins.append(dict(name=nm, out=out, id=g(), line=l2))
        nd = Node(self._name(tag), mod, cls, props, pins, x, y); self.nodes[nd.name] = nd; return nd
    def make(self, cls, props, pins, x, y, tag='H'):
        """hand-made node; pins = kit-style dicts (name, cat, sub, obj, out, default, dobj, hidden, ref, container)."""
        P = []
        for p in pins:
            s = 'CustomProperties Pin (PinId=@ID@,PinName="%s",' % p['name']
            if p.get('friendly'): s += 'PinFriendlyName=%s,' % p['friendly']
            if p.get('out'): s += 'Direction="EGPD_Output",'
            s += 'PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=%s,PinType.bIsReference=%s,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,' % (
                p['cat'], p.get('sub', ''), p.get('obj', 'None'), p.get('container', 'None'), 'True' if p.get('ref') else 'False')
            if p.get('default') is not None: s += 'DefaultValue="%s",' % p['default']
            if p.get('dobj'): s += 'DefaultObject="%s",' % p['dobj']
            s += TAIL.replace('bHidden=False', 'bHidden=True') if p.get('hidden') else TAIL
            P.append(dict(name=p['name'], out=bool(p.get('out')), id=g(), line=s))
        nd = Node(self._name(tag), 'BlueprintGraph', cls, props, P, x, y); self.nodes[nd.name] = nd; return nd
    def link(self, a, pa, b, pb):
        """a.pa (output) -> b.pb (input). a/b are Node objects."""
        self.links.append((a.pin(pa, True), a, b.pin(pb, False), b))
    def render(self):
        L = {}
        for pa, a, pb, b in self.links:
            L.setdefault(id(pa), []).append('%s %s,' % (b.name, pb['id'])); L.setdefault(id(pb), []).append('%s %s,' % (a.name, pa['id']))
        out = []
        for nd in self.nodes.values():
            out.append('Begin Object Class=/Script/%s.%s Name="%s"' % (nd.mod, nd.cls, nd.name))
            for p in nd.props:
                if not p.startswith('CustomProperties UserDefinedPin'): out.append('   ' + p)
            out += ['   NodePosX=%d' % nd.x, '   NodePosY=%d' % nd.y, '   NodeGuid=%s' % g()]
            for p in nd.pins:
                line = p['line'].replace('PinId=@ID@,', 'PinId=%s,' % p['id'], 1)
                if id(p) in L: line = line.replace('PersistentGuid=', 'LinkedTo=(%s),PersistentGuid=' % ''.join(L[id(p)]), 1)
                out.append('   ' + line)
            for p in nd.props:
                if p.startswith('CustomProperties UserDefinedPin'): out.append('   ' + p)
            out.append('End Object')
        return '\n'.join(out) + '\n'

# kit-style pin helpers for hand-made nodes
CLS = lambda c, mod='Engine': '"/Script/CoreUObject.Class\'/Script/%s.%s\'"' % (mod, c)
STRUCT = lambda s: '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.%s\'"' % s
TARGET = 'NSLOCTEXT("K2Node", "Target", "Target")'
def ex(name='execute', out=False): return {'name': name, 'cat': 'exec', 'out': out}
def fl(name, out=False, default=None): return {'name': name, 'cat': 'real', 'sub': 'double', 'out': out, 'default': default}
def it(name, out=False, default=None): return {'name': name, 'cat': 'int', 'out': out, 'default': default}
def bo(name, out=False, default=None): return {'name': name, 'cat': 'bool', 'out': out, 'default': default}
def ob(name, cls, out=False, friendly=None, hidden=False, dobj=None): return {'name': name, 'cat': 'object', 'obj': cls, 'out': out, 'friendly': friendly, 'hidden': hidden, 'dobj': dobj}
def vec(name, out=False, default=None): return {'name': name, 'cat': 'struct', 'obj': STRUCT('Vector'), 'out': out, 'default': default}
def selfpin(cls, hidden=False): return ob('self', cls, friendly=TARGET, hidden=hidden)
def callfn(G, parent, member, pins, pure=False, x=0, y=0, self_hidden=False, selfcls=None):
    props = (['bIsPureFunc=True'] if pure else []) + ['FunctionReference=(MemberParent=%s,MemberName="%s")' % (parent, member)]
    return G.make('K2Node_CallFunction', props, ([] if pure else [ex(), ex('then', True)]) + [selfpin(selfcls or parent, self_hidden)] + pins, x, y)
def var_get(G, member, pin, x, y):
    return G.make('K2Node_VariableGet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % member], [dict(pin, name=member, out=True)], x, y, 'G')
def var_set(G, member, pin, x, y):
    return G.make('K2Node_VariableSet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % member],
                  [ex(), ex('then', True), dict(pin, name=member), dict(pin, name='Output_Get', out=True, default=None)], x, y, 'S')
def bpvar(name, cat, default, sub=None, obj=None):
    vt = 'PinCategory="%s"' % cat + (',PinSubCategory="%s"' % sub if sub else '') + (',PinSubCategoryObject="%s"' % obj if obj else '')
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (name, g(), vt, name, default)
