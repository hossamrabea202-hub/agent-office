import json, re
d = json.load(open('C:/Users/hossam.rabea/ckw/wood/materials_level.json'))
L = json.load(open('C:/Users/hossam.rabea/ckw/wood/wood_list.json'))
SKIP = re.compile(r'(?i)StoneWall|Trim_World|StepCap|WalkFlag|GateArch|Pine_|StairBaked|ArchWeathering|Shield_Paint|TargetArrow|Bolt_Fletch|Obsidian')
BC = re.compile(r'(?i)basecolor|_bc\b|_bc$|_b$|_diff|diffuse|albedo|color|texture_4|fbx_texture_0')
ORM = re.compile(r'(?i)orm|_arm|metallicroughness|roughness|texture_5|fbx_texture_1')
out = []
for p in L:
    name = p.split('.')[-1]
    if SKIP.search(name): continue
    v = d[p]
    texs = [t for t in list(v['texture'].values()) + v['used_tex'] if t and 'w' in t and t['w'] >= 256]
    bc = [t['path'] for t in texs if BC.search(t['path'].split('.')[-1]) and t.get('srgb')]
    orm = [t['path'] for t in texs if ORM.search(t['path'].split('.')[-1]) and not t.get('srgb')]
    # prefer the texture whose name shares a stem with the material
    out.append({'mat': p, 'count': v['count'], 'bc': sorted(set(bc)), 'orm': sorted(set(orm)), 'scalar': v['scalar'], 'vector': v['vector']})
    print('%-30s bc=%s orm=%s' % (name[:30], [b.split('.')[-1] for b in sorted(set(bc))], [o.split('.')[-1] for o in sorted(set(orm))]))
json.dump(out, open('C:/Users/hossam.rabea/ckw/wood/wood_pick.json', 'w'), indent=0)
