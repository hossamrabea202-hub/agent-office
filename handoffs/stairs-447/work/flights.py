import json, math, collections, sys
exec(open(sys.argv[3]).read().split('S = [r for r')[0])
P = [r for r in P if r['visible'] and 'Pine' not in r['mesh'] and 'Mountain' not in r['folder'] and 'castle_BACKUP' not in r['folder']]
for r in P: r['lo'], r['hi'] = aabb(r); r['c'] = [(r['lo'][k] + r['hi'][k]) / 2 for k in range(3)]
step = lambda r: ('StairTread' in r['mesh'] or any('StepCap' in m for m in r['mats'])) and max(r['hi'][k]-r['lo'][k] for k in range(2)) < 400
T = [r for r in P if step(r)]
# a tread = one StairTread or one cap; caps and treads at the same spot merge
par = list(range(len(T)))
def f(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i in range(len(T)):
    for j in range(i+1, len(T)):
        a, b = T[i], T[j]; dz = abs(a['hi'][2] - b['hi'][2])
        for ax in (0, 1):
            run = abs(a['c'][ax] - b['c'][ax]); lat = abs(a['c'][1-ax] - b['c'][1-ax])
            if 12 <= dz <= 30 and 15 <= run <= 60 and lat < 25: par[f(i)] = f(j)
            if dz < 3 and run < 12 and lat < 25: par[f(i)] = f(j)
G = collections.defaultdict(list)
for i, r in enumerate(T): G[f(i)].append(r)
flights = []
for g in G.values():
    tops = sorted(set(round(r['hi'][2]) for r in g))
    if len(tops) < 3: continue
    lo = [min(r['lo'][k] for r in g) for k in range(3)]; hi = [max(r['hi'][k] for r in g) for k in range(3)]
    ax = 0 if (hi[0]-lo[0]) > (hi[1]-lo[1]) else 1
    # direction up: correlation of position along ax with top z
    by = sorted(g, key=lambda r: r['hi'][2]); d = 1 if by[-1]['c'][ax] > by[0]['c'][ax] else -1
    widths = [round(r['hi'][1-ax]-r['lo'][1-ax]) for r in g]
    rises = [b-a for a, b in zip(tops, tops[1:])]
    runs = sorted(set(round(r['c'][ax]) for r in g)); rr = [abs(b-a) for a, b in zip(runs, runs[1:])]
    # supports: castle stone blocks under the treads (footprint overlap, top <= tread top + 2)
    sup = [r for r in P if r not in g and not step(r) and any('Castle' in m for m in r['mats']) and 'Grime' not in ''.join(r['mats'])
           and max(r['hi'][k]-r['lo'][k] for k in range(3)) < 600
           and r['lo'][0] < hi[0] + 5 and r['hi'][0] > lo[0] - 5 and r['lo'][1] < hi[1] + 5 and r['hi'][1] > lo[1] - 5
           and r['hi'][2] <= hi[2] + 2 and r['hi'][2] >= lo[2] - 120]
    flights.append(dict(steps=len(tops), axis='XY'[ax], up=('+' if d > 0 else '-') + 'XY'[ax], lo=[round(x) for x in lo], hi=[round(x) for x in hi],
        width=collections.Counter(widths).most_common(1)[0][0], rise=collections.Counter(rises).most_common(1)[0][0],
        run=collections.Counter(rr).most_common(1)[0][0] if rr else 0, treads=g, supports=sup))
flights.sort(key=lambda F: (F['lo'][0], F['lo'][1]))
out = []
for i, F in enumerate(flights):
    mt = collections.Counter(short(r['mesh']) + ':' + short(r['mats'][0]) for r in F['treads'] + F['supports'])
    print('F%-2d %2d steps  up %s  width %3d  rise %2d  run %2d  from %s to %s  pieces %d+%d' % (i, F['steps'], F['up'], F['width'], F['rise'], F['run'], F['lo'], F['hi'], len(F['treads']), len(F['supports'])))
    print('     ' + ', '.join('%s x%d' % kv for kv in mt.most_common(6)) + ' | ' + ', '.join(sorted(set(r['folder'] for r in F['treads'] + F['supports']))[:3]))
    keep = lambda r: {k: r[k] for k in ('actor', 'folder', 'mesh', 'mats', 'loc', 'rot', 'scale', 'lo', 'hi')}
    out.append(dict({k: F[k] for k in F if k not in ('treads', 'supports')}, treads=[keep(r) for r in F['treads']], supports=[keep(r) for r in F['supports']]))
json.dump(out, open(sys.argv[2], 'w'))
print('flights:', len(out), ' total pieces:', sum(len(F['treads']) + len(F['supports']) for F in out))
