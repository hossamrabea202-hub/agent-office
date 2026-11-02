import json, re
d = json.load(open('C:/Users/hossam.rabea/ckw/wood/materials_level.json'))
WOOD = re.compile(r'(?i)wood|oak|plank|timber|beam|barrel|crate|log\b|logs|bench|table|cart|door|palisade|ladder|shelf|stool|chest|cask|bucket|wheel|rack|scaffold|bark|keg|firewood|post|lever|bolt|xbow|crossbow|shield_wood|gate(?!arch)|board|spruce|pine|birch|ash_|walnut|log_')
NOT = re.compile(r'(?i)iron|metal|steel|gold|coin|stone|rock|jelly|bubble|smoke|portal|crack|rays|invisible|banner|bone|insignia|ore|cloth|leaf|leaves|twig|needle|roots|moss|decal|grime|blob|realm|dust|sack')
out = []
for p, v in d.items():
    if v['count'] == 0: continue
    texs = [t['path'] for t in list(v['texture'].values()) + v['used_tex'] if t]
    meshes = ' '.join(v['meshes'])
    name = p.split('.')[-1]
    hay = name + ' ' + ' '.join(v['chain']) + ' ' + meshes + ' ' + ' '.join(texs)
    if WOOD.search(hay) and not NOT.search(name) and not (NOT.search(' '.join(texs)) and not WOOD.search(name + ' '.join(texs))):
        out.append((v['count'], name, p, v))
out.sort(key=lambda t: -t[0])
for n, name, p, v in out:
    tx = sorted(set(t['path'].split('.')[-1] + '(%sx%s%s)' % (t.get('w'), t.get('h'), '' if t.get('srgb', True) else ' lin') for t in list(v['texture'].values()) + v['used_tex'] if t))[:6]
    print('%5d  %-32s base=%s' % (n, name[:32], (v['chain'][-1] if v['chain'] else p).split('.')[-1]))
    print('       meshes: %s' % ', '.join('%s x%d' % (m.split('.')[-1], c) for m, c in list(v['meshes'].items())[:4]))
    print('       tex: %s' % ', '.join(tx))
    if v['scalar'] or v['vector']: print('       params: %s %s' % ({k: v2 for k, v2 in list(v['scalar'].items())[:10]}, {k: v2 for k, v2 in list(v['vector'].items())[:4]}))
print('wood materials:', len(out))
json.dump([p for _, _, p, _ in out], open('C:/Users/hossam.rabea/ckw/wood/wood_list.json', 'w'))
