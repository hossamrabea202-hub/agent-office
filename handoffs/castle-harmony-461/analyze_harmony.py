# #461 castle harmony analysis (offline) of castle_scan.json.
#   python analyze_harmony.py [castle_scan.json] -> HARMONY.md (report) + stdout summary
import json, os, re, sys
from collections import Counter, defaultdict
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, 'castle_scan.json')))
E, M = S['elements'], S['materials']
TYPES = [('battlement', r'merlon|crenel|parapet|battlement|wallwalk|walk_?slab|coping'), ('gate', r'gate|portcullis|drawbridge|barbican'),
         ('tower', r'tower'), ('keep', r'keep'), ('stairs', r'stair|step'), ('wall', r'curtain|wall|stringcourse|skirt|buttress|plinth|pier|jamb|spandrel|arch'),
         ('floor', r'floor|paving|courtyard|flag|cobble|ground'), ('roof', r'roof|hoarding|beam|joist|corbel')]
STONE = r'stone|ashlar|masonry|castle|wall|keep|bevel|tower|merlon'
def etype(lbl, mesh):
    s = (lbl + ' ' + mesh).lower()
    for t, rx in TYPES:
        if re.search(rx, s): return t
    return 'prop'
def status(mesh):
    m = mesh.lower()
    if re.search(r'baked|_aaa|aaa_|keepmasonry|masonry|_s447|stairsbaked|castlestones', m): return 'AAA'
    if re.search(r'/plane$|/plane_|grime|decalcard|_card', m): return 'card'
    if re.search(r'sm_bevel|sm_keep_box|/cube|shape_cube|sm_block|basicshapes|_box_', m): return 'kit'
    return 'other'
rows = []
for el in E:
    for c in el['comps']:
        vis = c['visible'] and not el['hidden']
        mat0 = c['mats'][0] if c['mats'] else None
        base = (M.get(mat0) or {}).get('base') if mat0 else None
        rows.append(dict(label=el['label'], cls=el['class'], mesh=c['mesh'], t=etype(el['label'], c['mesh']), st=status(c['mesh']), vis=vis,
                         inst=c['instances'], tris=c['tris'], nanite=c['nanite'], mat=mat0, base=base, ext=c['extent'], scale=c['scale'], origin=c['origin']))
out = ['# #461 Castle harmony scan', '', 'Source: `castle_scan.json` (%d actors, %d mesh components, %d materials).' % (len(E), len(rows), len(M)), '']
# 1. AAA vs kit per element type (visible only)
out += ['## 1. What is AAA and what is still old kit (visible elements)', '', '| Type | AAA | old kit | flat cards | other | hidden (still loaded) |', '|---|---|---|---|---|---|']
by = defaultdict(Counter)
for r in rows:
    by[r['t']]['hidden' if not r['vis'] else r['st']] += 1
for t in [x for x, _ in TYPES] + ['prop']:
    c = by[t]; out.append('| %s | %d | %d | %d | %d | %d |' % (t, c['AAA'], c['kit'], c['card'], c['other'], c['hidden']))
# 2. the visible old kit pieces, grouped by label stem
out += ['', '## 2. Visible old kit pieces still in the castle (convert next)', '']
stems = defaultdict(list)
for r in rows:
    if r['vis'] and r['st'] == 'kit' and r['t'] != 'prop':
        stems[(r['t'], re.sub(r'[_ ]?\d+$', '', r['label']))].append(r)
for (t, s), rs in sorted(stems.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    out.append('- **%s** `%s`: %d pieces (e.g. %s, %s)' % (t, s, len(rs), rs[0]['label'], rs[0]['mesh'].split('/')[-1]))
# 3. stone material families on visible structure
out += ['', '## 3. Stone material families on visible structure (should be 1-2 families, one look)', '', '| Base material | components | types | example MI |', '|---|---|---|---|']
fam = defaultdict(list)
for r in rows:
    if r['vis'] and r['t'] != 'prop' and r['base']: fam[r['base']].append(r)
for b, rs in sorted(fam.items(), key=lambda kv: -len(kv[1])):
    out.append('| `%s` | %d | %s | `%s` |' % (b.split('/')[-1].split('.')[0], len(rs), ', '.join('%s %d' % kv for kv in Counter(r['t'] for r in rs).most_common(4)), (rs[0]['mat'] or '').split('/')[-1].split('.')[0]))
# 4. look parameters that differ between MIs of the same family
out += ['', '## 4. Same family, different look (tints / limewash / scale that do not match)', '']
for b, rs in sorted(fam.items(), key=lambda kv: -len(kv[1])):
    mis = sorted(set(r['mat'] for r in rs if r['mat']))
    if len(mis) < 2: continue
    keys = set()
    for mi in mis: keys |= set(M[mi]['scalars']) | set(M[mi]['vectors'])
    diff = []
    for k in sorted(keys):
        vals = Counter(json.dumps(M[mi]['scalars'].get(k, M[mi]['vectors'].get(k))) for mi in mis)
        if len(vals) > 1: diff.append('%s: %s' % (k, ', '.join('%s x%d' % (v, n) for v, n in vals.most_common(4))))
    if diff:
        out.append('- **%s** (%d MIs):' % (b.split('/')[-1].split('.')[0], len(mis)))
        out += ['  - ' + d for d in diff[:10]]
# 5. hidden leftovers
hid = [r for r in rows if not r['vis'] and r['t'] != 'prop']
out += ['', '## 5. Hidden old pieces still loaded: %d components, %d tris (delete after the owner OK, or keep as backup)' % (len(hid), sum(r['tris'] * r['inst'] for r in hid)), '']
for (t, s), n in Counter((r['t'], re.sub(r'[_ ]?\d+$', '', r['label'])) for r in hid).most_common(15): out.append('- %s `%s`: %d' % (t, s, n))
# 6. non-uniform scale on stone (stretched texture / stone size mismatch)
st = [r for r in rows if r['vis'] and r['t'] != 'prop' and r['scale'] and max(abs(v) for v in r['scale']) / max(1e-3, min(abs(v) for v in r['scale'])) > 1.6]
out += ['', '## 6. Stretched stone (non-uniform scale > 1.6:1 => stones of different size side by side): %d components' % len(st), '']
for (t, s), n in Counter((r['t'], re.sub(r'[_ ]?\d+$', '', r['label'])) for r in st).most_common(15): out.append('- %s `%s`: %d' % (t, s, n))
open(os.path.join(H, 'HARMONY.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out[:60]))
