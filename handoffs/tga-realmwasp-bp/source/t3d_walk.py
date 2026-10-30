# Walk a Blueprint T3D graph: describe nodes and follow exec links from a start node.
#   python t3d_walk.py FILE.t3d GRAPH START_MATCH [depth]
# START_MATCH is a substring matched against node descriptions (e.g. ReceiveAnyDamage, Think).
import re, sys
src = open(sys.argv[1], encoding='utf-8', errors='replace').read()
graph = sys.argv[2]; start = sys.argv[3]; depth = int(sys.argv[4]) if len(sys.argv) > 4 else 60
gi = src.find('Begin Object Class=/Script/Engine.EdGraph Name="%s"' % graph)
# graph body = from its full definition (second occurrence with properties) to the next top-level graph; simplest: take
# all node definitions (blocks with pins) whose ExportPath mentions ':<graph>.'
blocks = re.findall(r'Begin Object (?:Class=\S+ )?Name="([^"]+)" ExportPath="/Script/(\w+)\.(\w+)\'[^"]*:%s\.[^"\']*\'"\n(.*?)\n\s*End Object' % re.escape(graph), src, re.S)
blocks = [(m, c, n, b) for n, m, c, b in blocks]
nodes = {}
for mod, cls, name, body in blocks:
    if 'CustomProperties Pin' not in body: continue
    pins = []
    for m in re.finditer(r'CustomProperties Pin \(PinId=(\w+),PinName="([^"]*)"(.*?)\)\s*$', body, re.M):
        pid, pname, rest = m.groups(); out = 'EGPD_Output' in rest; cat = re.search(r'PinType\.PinCategory="(\w*)"', rest)
        links = re.findall(r'(\w+) (\w{32})', re.search(r'LinkedTo=\(([^)]*)\)', rest).group(1)) if 'LinkedTo=(' in rest else []
        dv = re.search(r'DefaultValue="([^"]*)"', rest); do = re.search(r'DefaultObject="([^"]*)"', rest)
        pins.append(dict(id=pid, name=pname, out=out, cat=cat.group(1) if cat else '', links=links, dv=dv.group(1) if dv else (do.group(1).split('.')[-1] if do else '')))
    desc = cls.replace('K2Node_', '')
    for key in ('MemberName', 'CustomFunctionName', 'TargetType'):
        mm = re.search(key + r'="?([^",)]+)', body)
        if mm: desc += ' ' + mm.group(1).split('.')[-1]; break
    nodes[name] = dict(cls=cls, desc=desc, pins=pins)
pid2 = {p['id']: (n, p['name']) for n, d in nodes.items() for p in d['pins']}
def show(n, ind=''):
    d = nodes[n]; ins = []
    for p in d['pins']:
        if p['cat'] == 'exec' or p['out']: continue
        if p['links']: ins.append('%s<-%s' % (p['name'], ','.join('%s(%s)' % (l[0], nodes.get(l[0], {}).get('desc', '?')) for l in p['links'])))
        elif p['dv']: ins.append('%s=%s' % (p['name'], p['dv']))
    print('%s%s  [%s]  %s' % (ind, n, d['desc'], '; '.join(ins)))
seen = set()
def walk(n, ind, k):
    if n in seen or k > depth: return
    seen.add(n); show(n, ind)
    for p in nodes[n]['pins']:
        if p['cat'] == 'exec' and p['out']:
            for l in p['links']:
                if len(nodes[n]['pins']) and sum(1 for q in nodes[n]['pins'] if q['cat'] == 'exec' and q['out']) > 1: print(ind + '  .' + p['name'] + ':')
                walk(l[0], ind + '  ', k + 1)
starts = [n for n, d in nodes.items() if start in d['desc']]
print('nodes in graph', len(nodes), 'start', starts)
for s in starts[:2]: walk(s, '', 0)
