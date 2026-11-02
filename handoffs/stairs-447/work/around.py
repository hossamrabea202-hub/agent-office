import json, sys
exec(open('C:/Users/hossam.rabea/ckw/stairs/cluster.py').read().split('S = [r for r')[0].replace('json.load(open(sys.argv[1]))', "json.load(open('C:/Users/hossam.rabea/ckw/stairs/castle_pieces.json'))"))
box = [float(x) for x in sys.argv[1:7]]
for r in P:
    if not r['visible'] or 'Pine' in r['mesh']: continue
    lo, hi = aabb(r)
    if lo[0] < box[3] and hi[0] > box[0] and lo[1] < box[4] and hi[1] > box[1] and lo[2] < box[5] and hi[2] > box[2]:
        t = short(r['mesh'])
        if t == 'SM_StairTread' or 'StepCap' in r['mats'][0]: continue
        print('%-26s %-18s %-28s lo=%s hi=%s rot=%s %s' % (r['actor'][:26], t[:18], short(r['mats'][0])[:28], [round(x) for x in lo], [round(x) for x in hi], [round(x) for x in r['rot']], r['folder']))
