import json, collections, sys
d = json.load(open(sys.argv[1]))
P = d['pieces']; M = d['meshes']
short = lambda p: p.split('.')[-1]
print('rows', len(P))
c = collections.Counter((r['folder'] or '(none)') for r in P)
print('\n== by folder'); [print('%5d  %s' % (n, k)) for k, n in c.most_common(40)]
c = collections.Counter(short(r['mesh']) for r in P)
print('\n== by mesh'); [print('%5d  %-30s %s' % (n, k, [M[p] for p in M if short(p)==k][0])) for k, n in c.most_common(30)]
c = collections.Counter(tuple(short(m) for m in r['mats']) for r in P)
print('\n== by materials'); [print('%5d  %s' % (n, k)) for k, n in c.most_common(20)]
lab = collections.Counter(''.join(ch for ch in r['actor'] if not ch.isdigit()).rstrip('_') for r in P if any(k in r['actor'].lower() for k in ('stair','step','land','walk','ramp')))
print('\n== stair-ish actor labels'); [print('%5d  %s' % (n, k)) for k, n in lab.most_common(40)]
