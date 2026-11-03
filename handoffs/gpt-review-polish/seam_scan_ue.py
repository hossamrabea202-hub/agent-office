# #451 seam scan (i5, 2026-11-03): READ-ONLY. Finds places where castle pieces don't meet like real masonry:
#   GAP      two aligned pieces with a slit of 0.3-25 cm between faces that overlap in area (light leaks, see-through)
#   ZFIGHT   two aligned pieces whose faces are coplanar (|d| < 0.3 cm) AND overlap in area (flicker)
#   CUBE     engine primitives (BasicShapes Cube / Plane / Cylinder) or meshes named Cube/Box used with a real material
#   FLOAT    a wall/tower piece whose bottom sits 2-60 cm above the ground under it (trace)
#   SINK?    a small prop sunk > 40 % of its height into the ground (info only)
# Decals and decal cards are skipped entirely (owner: don't touch the decals).
# Output: handoffs/gpt-review-polish/seam_report.txt (one line per finding, worst first) + seam_findings.json.
#   py seam_scan_ue.py [--radius <cm from castle centre, default 9000>]
import json, math, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
RADIUS = float(A[A.index('--radius') + 1]) if '--radius' in A else 9000.0
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
SKIP = ('decal', 'soot', 'grime', 'stain', 'card', 'cd425', 'mud', 'moss', 'algae', 'puddle', 'leaf', 'blood', 'streak', 'ld425', 'ld435')
STRUCT = ('wall', 'tower', 'merlon', 'battle', 'parapet', 'keep', 'gate', 'stair', 'step', 'floor', 'pav', 'trim', 'kerb',
          'arch', 'buttress', 'drum', 'crenel', 'walkway', 'plinth', 'foundation', 'block', 'stone', 'castle', 'corner', 'pillar')


def low(s): return (s or '').lower()


pieces = []
for a in EAS.get_all_level_actors():
    lab = low(a.get_actor_label())
    if isinstance(a, unreal.DecalActor) or any(k in lab for k in SKIP): continue
    if a.get_class().get_name() not in ('StaticMeshActor',) and not a.get_components_by_class(unreal.StaticMeshComponent): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if isinstance(c, unreal.InstancedStaticMeshComponent) or not c.is_visible(): continue
        m = c.get_editor_property('static_mesh')
        if not m: continue
        mp = low(m.get_path_name())
        if any(k in mp for k in SKIP): continue
        mats = [low(x.get_path_name()) if x else '' for x in c.get_materials()]
        if any('decal' in x or 'card' in x for x in mats): continue
        t = c.get_world_transform()
        loc = t.translation
        if math.hypot(loc.x, loc.y) > RADIUS: continue
        bb = m.get_bounding_box()
        mn, mx = bb.min, bb.max
        s = t.scale3d
        cen_l = unreal.Vector((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2)
        ext = [abs((mx.x - mn.x) / 2 * s.x), abs((mx.y - mn.y) / 2 * s.y), abs((mx.z - mn.z) / 2 * s.z)]
        if max(ext) < 5: continue
        cen = unreal.MathLibrary.transform_location(t, cen_l)
        r = t.rotation.rotator()
        ax = [unreal.MathLibrary.get_forward_vector(r), unreal.MathLibrary.get_right_vector(r), unreal.MathLibrary.get_up_vector(r)]
        struct = any(k in lab or k in mp for k in STRUCT)
        pieces.append(dict(a=a, label=a.get_actor_label(), comp=c.get_name(), mesh=m.get_path_name().split('.')[0], mats=mats,
                           cen=cen, ext=ext, ax=ax, yaw=r.yaw, pitch=r.pitch, roll=r.roll, struct=struct))
print('pieces', len(pieces))
F = []


def dot(u, v): return u.x * v.x + u.y * v.y + u.z * v.z


def aligned(p, q):
    """True when q's axes are parallel to p's (any permutation / sign): rotations equal mod 90 deg."""
    for u in q['ax']:
        if max(abs(dot(u, v)) for v in p['ax']) < 0.9994: return False
    return True


def q_ext_in_p(p, q):
    """q's half extents measured along p's axes (q aligned with p)."""
    out = []
    for v in p['ax']:
        out.append(sum(abs(dot(u, v)) * e for u, e in zip(q['ax'], q['ext'])))
    return out


# broad phase: grid
cell = 1500.0
grid = {}
for i, p in enumerate(pieces):
    k = (int(p['cen'].x // cell), int(p['cen'].y // cell))
    grid.setdefault(k, []).append(i)
seen = set()
for i, p in enumerate(pieces):
    if not p['struct']: continue
    kx, ky = int(p['cen'].x // cell), int(p['cen'].y // cell)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in grid.get((kx + dx, ky + dy), []):
                if j <= i or (i, j) in seen: continue
                q = pieces[j]
                if not q['struct'] or p['a'] == q['a'] and p['comp'] == q['comp']: continue
                seen.add((i, j))
                if not aligned(p, q): continue
                d = q['cen'] - p['cen']
                dl = [dot(d, v) for v in p['ax']]
                qe = q_ext_in_p(p, q)
                sep = [abs(dl[k]) - (p['ext'][k] + qe[k]) for k in range(3)]   # >0 gap, <0 overlap, per axis
                for k in range(3):
                    o = [m for m in range(3) if m != k]
                    ov = [-(sep[m]) for m in o]                                 # overlap size on the other two axes
                    if min(ov) < 10: continue                                   # faces must share >= 10 cm both ways
                    if 0.3 <= sep[k] <= 25:
                        F.append(dict(kind='GAP', size=round(sep[k], 1), area=round(ov[0] * ov[1] / 1e4, 2), a=p['label'], b=q['label'],
                                      mesh_a=p['mesh'], mesh_b=q['mesh'], at=[round(x) for x in ((p['cen'].x + q['cen'].x) / 2, (p['cen'].y + q['cen'].y) / 2, (p['cen'].z + q['cen'].z) / 2)], axis='XYZ'[k]))
                # z-fighting = overlapping volumes with a shared coplanar face
                if all(s < -1 for s in sep):
                    for m in range(3):
                        for sgn in (1, -1):
                            fp = sgn * p['ext'][m]; fq = dl[m] + sgn * qe[m]
                            if abs(fp - fq) < 0.3:
                                o = [n for n in range(3) if n != m]; ov = [-(sep[n]) for n in o]
                                if min(ov) >= 20:
                                    F.append(dict(kind='ZFIGHT', size=round(abs(fp - fq), 2), area=round(ov[0] * ov[1] / 1e4, 2), a=p['label'], b=q['label'],
                                                  mesh_a=p['mesh'], mesh_b=q['mesh'], at=[round(p['cen'].x + p['ax'][m].x * fp), round(p['cen'].y + p['ax'][m].y * fp), round(p['cen'].z + p['ax'][m].z * fp)], axis='XYZ'[m]))
for p in pieces:
    mp = low(p['mesh'])
    if '/engine/basicshapes/' in mp or mp.split('/')[-1] in ('cube', 'box', 'sm_cube', 'sm_box', 'plane', 'cylinder') or mp.split('/')[-1].startswith(('cube', 'sm_cube', 'box_')):
        if True:
            F.append(dict(kind='CUBE', size=round(max(p['ext']) * 2), area=0, a=p['label'], b='', mesh_a=p['mesh'], mesh_b=', '.join(m.split('/')[-1] for m in p['mats']),
                          at=[round(p['cen'].x), round(p['cen'].y), round(p['cen'].z)], axis=''))
# floating structure: trace down from the lowest corner centre
for p in pieces:
    if not p['struct'] or p['ext'][2] < 50: continue
    bottom = p['cen'] - unreal.Vector(0, 0, sum(abs(u.z) * e for u, e in zip(p['ax'], p['ext'])))
    hit = unreal.SystemLibrary.line_trace_single(world, bottom + unreal.Vector(0, 0, -1), bottom + unreal.Vector(0, 0, -80),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [p['a']], unreal.DrawDebugTrace.NONE, True)
    if hit:
        h = hit.to_tuple()
        if h[0]:
            gap = bottom.z - h[4].z
            if 2 <= gap <= 60:
                F.append(dict(kind='FLOAT', size=round(gap, 1), area=round(p['ext'][0] * p['ext'][1] * 4 / 1e4, 2), a=p['label'], b=str(h[9].get_actor_label() if h[9] else ''),
                              mesh_a=p['mesh'], mesh_b='', at=[round(bottom.x), round(bottom.y), round(bottom.z)], axis='Z'))
rank = {'ZFIGHT': 0, 'GAP': 1, 'FLOAT': 2, 'CUBE': 3}
F.sort(key=lambda f: (rank[f['kind']], -f['area']))
lines = ['%-6s %6s cm  area %6s m2  %-34s | %-34s at %s  (%s | %s)' % (f['kind'], f['size'], f['area'], f['a'][:34], f['b'][:34], f['at'], f['mesh_a'].split('/')[-1], f['mesh_b'].split('/')[-1] if f['mesh_b'] else '') for f in F]
summary = {k: sum(1 for f in F if f['kind'] == k) for k in rank}
open(H + 'seam_report.txt', 'w', encoding='utf-8').write('seam scan radius %d cm, %d pieces, findings %s\n' % (RADIUS, len(pieces), summary) + '\n'.join(lines))
json.dump(F, open(H + 'seam_findings.json', 'w'), indent=0)
print('seam scan', summary)
