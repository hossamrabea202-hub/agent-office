import json, math, collections, sys
d = json.load(open(sys.argv[1])); P = d['pieces']; M = d['meshes']
short = lambda p: p.split('.')[-1]
def is_stair(r):
    t = (r['actor'] + ' ' + r['folder'] + ' ' + short(r['mesh']) + ' ' + ' '.join(short(m) for m in r['mats'])).lower()
    return any(k in t for k in ('stair', 'step', 'tread', 'landing', 'stepcap')) and 'grime' not in t and 'contact' not in t
def aabb(r):
    b = M[r['mesh']]; s = r['scale']; yaw = math.radians(r['rot'][2]); pit = math.radians(r['rot'][1]); rol = math.radians(r['rot'][0])
    # world AABB of the rotated scaled box (full rotation)
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pit), math.sin(pit), math.cos(rol), math.sin(rol)
    R = [[cp*cy, cy*sp*sr - sy*cr, -(cy*sp*cr + sy*sr)], [cp*sy, sy*sp*sr + cy*cr, -(sy*sp*cr - cy*sr)], [sp, -cp*sr, cp*cr]]
    lo, hi = [1e9]*3, [-1e9]*3
    for x in (b['min'][0], b['max'][0]):
        for y in (b['min'][1], b['max'][1]):
            for z in (b['min'][2], b['max'][2]):
                p = (x*s[0], y*s[1], z*s[2])
                w = [r['loc'][i] + R[i][0]*p[0] + R[i][1]*p[1] + R[i][2]*p[2] for i in range(3)]
                lo = [min(lo[i], w[i]) for i in range(3)]; hi = [max(hi[i], w[i]) for i in range(3)]
    return lo, hi
S = [r for r in P if is_stair(r)]
for r in S: r['lo'], r['hi'] = aabb(r)
# union-find on touching boxes (gap <= 15 cm), separately for visible / hidden
par = list(range(len(S)))
def f(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i in range(len(S)):
    for j in range(i+1, len(S)):
        a, b = S[i], S[j]
        if a['visible'] != b['visible']: continue
        if all(a['lo'][k] - 15 <= b['hi'][k] and b['lo'][k] - 15 <= a['hi'][k] for k in range(3)):
            par[f(i)] = f(j)
G = collections.defaultdict(list)
for i, r in enumerate(S): G[f(i)].append(r)
out = []
for k, g in sorted(G.items(), key=lambda kv: -len(kv[1])):
    lo = [min(r['lo'][i] for r in g) for i in range(3)]; hi = [max(r['hi'][i] for r in g) for i in range(3)]
    out.append({'n': len(g), 'visible': g[0]['visible'], 'lo': [round(x) for x in lo], 'hi': [round(x) for x in hi],
        'folders': dict(collections.Counter(r['folder'] for r in g)), 'meshes': dict(collections.Counter(short(r['mesh']) for r in g)),
        'mats': dict(collections.Counter(short(r['mats'][0]) if r['mats'] else '' for r in g)),
        'yaws': sorted(set(round(r['rot'][2]) for r in g))[:8], 'labels': sorted(set(r['actor'] for r in g))[:5], 'pieces': g})
json.dump(out, open(sys.argv[2], 'w'), indent=0)
for i, c in enumerate(out):
    size = [c['hi'][j]-c['lo'][j] for j in range(3)]
    print('#%-2d n=%-3d vis=%-5s size=%s lo=%s yaw=%s\n     folders=%s\n     meshes=%s mats=%s\n     e.g.=%s' % (i, c['n'], c['visible'], size, c['lo'], c['yaws'], c['folders'], c['meshes'], c['mats'], c['labels'][:3]))
