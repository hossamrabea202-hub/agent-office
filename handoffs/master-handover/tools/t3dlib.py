"""Tiny toolkit for rebuilding Blueprint graphs as paste-able T3D text.

- load(bp) parses an AssetExportTask T3D export (preferring the editable copy of each node)
- load_graph(bp, 'EventGraph') clones every node of a graph and restores its links (fresh pin ids)
- clone()/member()/spec_call() create new nodes from templates; link() wires pins; emit() writes text
"""
import re, uuid, os

SP = os.path.dirname(os.path.abspath(__file__))
T3D = os.path.join(SP, 't3d')
_FILES = {}


def gid():
    return uuid.uuid4().hex.upper()


def load(bp):
    if bp not in _FILES:
        raw = open(os.path.join(T3D, bp + '.t3d'), 'rb').read()
        t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
        cls = {}
        for full, n in re.findall(r'Begin Object Class=(/Script/[\w.]+) Name="([^"]+)"', t):
            cls.setdefault(n, full)
        defs = {}
        # line-based: a definition's body runs until the next Begin/End Object line (a graph's own definition
        # header is immediately followed by its first child node, which a lazy regex would swallow)
        lines = t.splitlines()
        blocks = []
        for i, line in enumerate(lines):
            m = re.match(r'\s*Begin Object Name="([^"]+)" ExportPath="([^"]*)"', line)
            if not m:
                continue
            body = []
            for l2 in lines[i + 1:]:
                if re.match(r'\s*(Begin|End) Object', l2):
                    break
                body.append(l2)
            blocks.append((m.group(1), m.group(2), '\n'.join(body)))
        for n, path, body in blocks:
            if 'CustomProperties Pin' not in body and 'EdGraphNode_Comment' not in cls.get(n, ''):
                continue
            graph = path.rsplit(':', 1)[-1].split('.')[0]
            uber = graph.startswith('ExecuteUbergraph')
            if n not in defs or (defs[n][0] and not uber):
                defs[n] = (uber, graph, body)
        _FILES[bp] = (cls, {n: (g, b) for n, (u, g, b) in defs.items()})
    return _FILES[bp]


class Pin:
    def __init__(self, line):
        self.line = line
        self.name = re.search(r'PinName="([^"]+)"', line).group(1)
        self.out = 'Direction="EGPD_Output"' in line
        self.id = gid()
        self.links = []
        m = re.search(r'LinkedTo=\(([^)]*)\)', line)
        self.old_links = [x.strip().split(' ') for x in m.group(1).split(',') if x.strip()] if m else []
        self.old_id = re.search(r'PinId=([0-9A-F]+)', line).group(1)


class Graph:
    def __init__(self):
        self.nodes = []
        self.names = set()
        self.counter = 0

    def new_name(self):
        while True:
            self.counter += 1
            n = 'CX_%d' % self.counter
            if n not in self.names:
                return n

    # ------------------------------------------------------------ node creation
    def add(self, cls, body, name=None, x=0, y=0):
        n = Node(self, cls, body, name or self.new_name(), x, y)
        self.nodes.append(n)
        self.names.add(n.name)
        return n

    def clone(self, bp, name, x, y, new_name=None):
        cls, defs = load(bp)
        return self.add(cls[name], defs[name][1], new_name, x, y)

    def member(self, member_name, x, y, prefer=('BP_ZombieHUD', 'BP_Zombie', 'BP_Cannon', 'BP_CastleGateControl',
                                                  'BP_ZombieWaveManager', 'BP_ThirdPersonCharacter'), kind='K2Node_CallFunction'):
        for bp in prefer:
            cls, defs = load(bp)
            for n, (g, body) in defs.items():
                if cls.get(n, '').endswith(kind) and re.search(r'MemberName="%s"' % re.escape(member_name), body):
                    return self.add(cls[n], body, None, x, y)
        raise KeyError(member_name)

    def load_graph(self, bp, graph='EventGraph', dy=0):
        """Clone all nodes of a graph keeping names, positions and links."""
        cls, defs = load(bp)
        made = {}
        for n, (g, body) in defs.items():
            if g != graph:
                continue
            pos = re.search(r'NodePosX=(-?\d+).*?NodePosY=(-?\d+)', body, re.S)
            node = self.add(cls[n], body, n, int(pos.group(1)) if pos else 0, (int(pos.group(2)) if pos else 0) + dy)
            node.raw_extra = [s.strip() for s in body.splitlines() if re.match(r'\s*(NodeWidth|NodeHeight)=', s)]
            made[n] = node
        old2new = {(n, p.old_id): p for n, node in made.items() for p in node.pins}
        for n, node in made.items():
            for p in node.pins:
                if not p.out:
                    continue
                for tn, tid in p.old_links:
                    q = old2new.get((tn, tid))
                    if q is not None:
                        p.links.append((tn, q.id))
                        q.links.append((n, p.id))
        return made

    def emit(self, path):
        out = '\n'.join(n.emit() for n in self.nodes) + '\n'
        open(path, 'w', encoding='utf-8', newline='\r\n').write(out)
        return len(self.nodes), len(out)


class Node:
    def __init__(self, graph, cls, body, name, x, y):
        self.g, self.cls, self.name, self.x, self.y = graph, cls, name, x, y
        self.props, self.pins, self.raw_extra = [], [], []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith('CustomProperties Pin'):
                self.pins.append(Pin(s))
            elif s and not re.match(r'(NodePosX|NodePosY|NodeGuid|NodeWidth|NodeHeight|ErrorType|ErrorMsg|bHasCompilerMessage|Begin |End )', s):
                self.props.append(s)

    def p(self, name):
        for pin in self.pins:
            if pin.name == name:
                return pin
        raise KeyError('%s has no pin %s (has %s)' % (self.name, name, [q.name for q in self.pins]))

    def default(self, pin, value=None, obj=None):
        pin = self.p(pin)
        line = pin.line
        if value is not None:
            if 'DefaultValue="' in line:
                line = re.sub(r'DefaultValue="[^"]*"', 'DefaultValue="%s"' % value, line, 1)
            else:
                line = line.replace('PersistentGuid=', 'DefaultValue="%s",PersistentGuid=' % value, 1)
        if obj is not None:
            if 'DefaultObject="' in line:
                line = re.sub(r'DefaultObject="[^"]*"', 'DefaultObject="%s"' % obj, line, 1)
            elif 'DefaultObject=None' in line:
                line = line.replace('DefaultObject=None', 'DefaultObject="%s"' % obj, 1)
            else:
                line = line.replace('PersistentGuid=', 'DefaultObject="%s",PersistentGuid=' % obj, 1)
        pin.line = line
        return self

    def external(self, owner_cls):
        out = []
        for s in self.props:
            if s.startswith(('VariableReference=', 'FunctionReference=')):
                s = s.replace(',bSelfContext=True', '')
                if 'MemberParent=' not in s:
                    s = s.replace('=(', '=(MemberParent="%s",' % owner_cls, 1)
            out.append(s)
        self.props = out
        sp = self.p('self')
        sp.line = sp.line.replace('bHidden=True', 'bHidden=False')
        sp.line = re.sub(r'DefaultObject="[^"]*",', '', sp.line)
        return self

    def unlink(self, pin):
        """Remove all links of one pin (both directions)."""
        p = self.p(pin)
        for tn, tid in p.links:
            other = next(n for n in self.g.nodes if n.name == tn)
            for q in other.pins:
                if q.id == tid:
                    q.links = [l for l in q.links if l[1] != p.id]
        p.links = []
        return self

    def emit(self):
        lines = ['Begin Object Class=%s Name="%s"' % (self.cls, self.name)]
        lines += ['   ' + s for s in self.props]
        lines += ['   NodePosX=%d' % self.x, '   NodePosY=%d' % self.y]
        lines += ['   ' + s for s in self.raw_extra]
        lines.append('   NodeGuid=%s' % gid())
        idmap = {p.old_id: p.id for p in self.pins}

        def own(m):   # split-struct pins point at sibling pins of the same node: "Node PinId"
            return '%s %s' % (self.name, idmap.get(m.group(2), m.group(2)))
        for pin in self.pins:
            line = re.sub(r'PinId=[0-9A-F]+', 'PinId=' + pin.id, pin.line, 1)
            line = re.sub(r'(?<=ParentPin=)(\w+) ([0-9A-F]+)', own, line)
            line = re.sub(r'SubPins=\(([^)]*)\)',
                          lambda m: 'SubPins=(%s)' % re.sub(r'(\w+) ([0-9A-F]+)', own, m.group(1)), line)
            line = re.sub(r'LinkedTo=\([^)]*\),', '', line)
            if pin.links:
                line = line.replace('PersistentGuid=', 'LinkedTo=(%s),PersistentGuid=' %
                                    ''.join('%s %s,' % l for l in pin.links), 1)
            lines.append('   ' + line)
        lines.append('End Object')
        return '\n'.join(lines)


def link(a, ap, b, bp):
    pa, pb = a.p(ap), b.p(bp)
    pa.links.append((b.name, pb.id))
    pb.links.append((a.name, pa.id))


def chain(*nodes):
    for a, b in zip(nodes, nodes[1:]):
        link(a, 'then', b, 'execute')


def pin_line(name, cat, out=False, sub='', subobj=None, default=None, obj=None, hidden=False, friendly=None):
    parts = ['PinId=%s' % gid(), 'PinName="%s"' % name]
    if friendly:
        parts.append('PinFriendlyName=NSLOCTEXT("K2Node", "%s", "%s")' % (friendly, friendly))
    if out:
        parts.append('Direction="EGPD_Output"')
    parts += ['PinType.PinCategory="%s"' % cat, 'PinType.PinSubCategory="%s"' % sub,
              'PinType.PinSubCategoryObject=%s' % ('"%s"' % subobj if subobj else 'None'),
              'PinType.PinSubCategoryMemberReference=()', 'PinType.PinValueType=()', 'PinType.ContainerType=None',
              'PinType.bIsReference=False', 'PinType.bIsConst=False', 'PinType.bIsWeakPointer=False',
              'PinType.bIsUObjectWrapper=False', 'PinType.bSerializeAsSinglePrecisionFloat=False']
    if default is not None:
        parts.append('DefaultValue="%s"' % default)
    if obj is not None:
        parts.append('DefaultObject="%s"' % obj)
    parts += ['PersistentGuid=00000000000000000000000000000000', 'bHidden=%s' % hidden, 'bNotConnectable=False',
              'bDefaultValueIsReadOnly=False', 'bDefaultValueIsIgnored=False', 'bAdvancedView=False', 'bOrphanedPin=False']
    return 'CustomProperties Pin (%s,)' % ','.join(parts)


def spec_call(g, parent_cls, member_name, pins, x, y, pure=False, lib_default=None):
    """New CallFunction node from an explicit pin list [(name, cat, out, sub, subobj, default)]."""
    lines = []
    if pure:
        lines.append('bIsPureFunc=True')
    lines.append('FunctionReference=(MemberParent="%s",MemberName="%s")' % (parent_cls, member_name))
    if not pure:
        lines.append(pin_line('execute', 'exec'))
        lines.append(pin_line('then', 'exec', out=True))
    if lib_default:
        lines.append(pin_line('self', 'object', subobj=parent_cls, obj=lib_default, hidden=True, friendly='Target'))
    for spec in pins:
        name, cat = spec[0], spec[1]
        kw = dict(zip(('out', 'sub', 'subobj', 'default', 'obj'), spec[2:]))
        lines.append(pin_line(name, cat, **kw))
    return g.add('/Script/BlueprintGraph.K2Node_CallFunction', '\n'.join(lines), None, x, y)


KML = "/Script/CoreUObject.Class'/Script/Engine.KismetMathLibrary'"
KSL = "/Script/CoreUObject.Class'/Script/Engine.KismetStringLibrary'"
KTL = "/Script/CoreUObject.Class'/Script/Engine.KismetTextLibrary'"
GSL = "/Script/CoreUObject.Class'/Script/Engine.GameplayStatics'"
