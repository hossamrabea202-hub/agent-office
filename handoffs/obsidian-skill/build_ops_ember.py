# #477 (i5): turns gen_ember.py's graph into ops for ember_ops_ue.py (same runner idea as aaa-472/ops: edits the live graph, no paste).
#   python build_ops_ember.py   -> ember_ops.json
# No custom event here: Python can't give one parameters, so DrawEmberSkill's nodes hang directly off DrawArmoury's Sequence.
import json, os, re, runpy, sys
ME = os.path.dirname(os.path.abspath(__file__))
g = runpy.run_path(os.path.join(ME, 'gen_ember.py'), run_name='__main__')
G, MAN = g['G'], json.load(open(os.path.join(ME, 'ember_manifest.json')))
BP = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
SEQ, CALL = g['SEQ'], g['CALL']
def real(ref): return re.search(r"'([^']+)'", ref).group(1)
def conv(n):
    name, cls, props, pins, x, y = n; pj = ' '.join(props); d = {'id': name, 'x': x, 'y': y}
    fr = re.search(r'FunctionReference=\((?:MemberParent=("[^"]+"),)?MemberName="(\w+)"', pj)
    vr = re.search(r'VariableReference=\((?:MemberParent=("[^"]+"),)?MemberName="(\w+)"', pj)
    if cls in ('K2Node_CallFunction', 'K2Node_CallArrayFunction'):
        if not fr: raise SystemExit('no function ref: %s %s' % (name, pj[:300]))
        d.update(kind='call', path='%s:%s' % (real(fr.group(1)), fr.group(2)) if fr.group(1) else '@self:' + fr.group(2))
    elif cls in ('K2Node_VariableGet', 'K2Node_VariableSet'):
        d.update(kind='get' if cls.endswith('Get') else 'set', var=vr.group(2))
        if vr.group(1): d['cls'] = real(vr.group(1))
    elif cls == 'K2Node_IfThenElse': d['kind'] = 'branch'
    elif cls == 'K2Node_ExecutionSequence': d['kind'] = 'seq'
    elif cls == 'K2Node_DynamicCast': d['kind'] = 'cast'
    else: raise SystemExit('no op for %s %s' % (cls, name))
    defaults = []
    for p in pins:
        if p.get('out') or p.get('cat') == 'exec' or p.get('hidden') or p['name'] == 'self': continue
        if p.get('dobj'): defaults.append((p['name'], p['dobj']))
        elif p.get('default') is not None and d['kind'] == 'call': defaults.append((p['name'], str(p['default'])))
    d['defaults'] = defaults
    return d
nodes = [conv(n) for n in G.nodes if n[0] not in ('DrawEmberSkill', CALL)]
for n in nodes:
    if n.get('path', '').startswith('@self:'): n['path'] = '%s.%s_C:%s' % (BP, BP.split('/')[-1], n['path'][6:])
def ref(s): return s.replace('DrawEmberSkill.then', SEQ + '.then_0').replace('DrawEmberSkill.', 'DrawArmoury.')
links = []
for a, pa, b, pb in G.links:
    if b == CALL: continue                                     # Sequence -> the event call: replaced by the direct link above
    links.append([ref('%s.%s' % (a, pa)), '%s.%s' % (b, pb), False])
for r in MAN['rewires']:
    if r['to'].startswith(CALL + '.'): continue
    links.append([r['from'], r['to'], bool(r.get('replace'))])
ops = {'fix': '477', 'bp': BP, 'vars': [], 'nodes': nodes, 'links': links, 'remove': [], 'set_live': [], 'dx': 0, 'dy': 16000}
json.dump(ops, open(os.path.join(ME, 'ember_ops.json'), 'w'), indent=0); print('ember_ops.json', len(nodes), 'nodes', len(links), 'links')
