import json, math, collections, sys
exec(open(sys.argv[3]).read().split('S = [r for r')[0])   # reuse short/is_stair/aabb from cluster.py
P = [r for r in P if r['visible'] and 'Pine' not in r['mesh'] and 'Mountain' not in r['folder'] and 'castle_BACKUP' not in r['folder']]
for r in P: r['lo'], r['hi'] = aabb(r)
big = lambda r: max(r['hi'][k] - r['lo'][k] for k in range(3)) > 600
seed = [r for r in P if is_stair(r) and not big(r) and 'Collision' not in r['folder']]
seedset = set(map(id, seed))
touch = lambda a, b, t: all(a['lo'][k] - t <= b['hi'][k] and b['lo'][k] - t <= a['hi'][k] for k in range(3))
# add small stone blocks that the stair seeds sit on / touch (stair bodies named Cube_xx)
extra = [r for r in P if id(r) not in seedset and not big(r) and any('Castle' in m for m in r['mats'])
         and 'Grime' not in ''.join(r['mats']) and any(touch(r, s, 2) for s in seed)]
S = seed + extra
par = list(range(len(S)))
def f(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i in range(len(S)):
    for j in range(i+1, len(S)):
        if touch(S[i], S[j], 30 if (S[i]['hi'][2]-S[i]['lo'][2] < 3 or S[j]['hi'][2]-S[j]['lo'][2] < 3) else 2): par[f(i)] = f(j)
G = collections.defaultdict(list)
for i, r in enumerate(S): G[f(i)].append(r)
out = []
for g in sorted(G.values(), key=len, reverse=True):
    lo = [min(r['lo'][i] for r in g) for i in range(3)]; hi = [max(r['hi'][i] for r in g) for i in range(3)]
    tops = sorted(set(round(r['hi'][2]) for r in g if is_stair(r)))
    rises = [b - a for a, b in zip(tops, tops[1:])]
    out.append(dict(n=len(g), lo=[round(x) for x in lo], hi=[round(x) for x in hi], tops=tops,
        rise=collections.Counter(rises).most_common(2), meshes=dict(collections.Counter(short(r['mesh']) for r in g)),
        mats=dict(collections.Counter(short(r['mats'][0]) for r in g if r['mats'])), folders=dict(collections.Counter(r['folder'] for r in g)),
        yaws=sorted(set(round(r['rot'][2]) % 360 for r in g)), pieces=[{k: r[k] for k in ('actor','folder','mesh','mats','loc','rot','scale','lo','hi')} for r in g]))
json.dump(out, open(sys.argv[2], 'w'))
for i, c in enumerate(out):
    if c['n'] < 3: continue
    sz = [c['hi'][k] - c['lo'][k] for k in range(3)]
    print('S%-2d n=%-3d size=%s at=%s steps=%d rise=%s yaw=%s\n     %s\n     %s | %s' % (i, c['n'], sz, c['lo'], len(c['tops']), c['rise'], c['yaws'], c['meshes'], c['mats'], list(c['folders'])[:3]))
print('small leftovers:', sum(1 for c in out if c['n'] < 3))
