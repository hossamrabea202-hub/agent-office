# #509 step 1 (i5 checkking, 2026-11-05): defence stores on the castle wall walks.
#   py place_stores509_ue.py                 DRY RUN: finds the wall walks, plans the clusters, writes stores_report509.txt
#   py place_stores509_ue.py --apply         spawns them (tag WS509, outliner folder CastleProps509), one ISM actor per mesh
#   py place_stores509_ue.py --remove        deletes every WS509 actor (the undo; nothing else is touched)
#   --near <x> <y> <z> <radius cm>           only the clusters near a point (preview)
#   --temp                                   meshes from /Game/_i5tmpWS509/ (i5 lookdev), never saved
# Why these props, and why there (INDUSTRY_SECRETS 4.5 medieval authenticity, rule 3 a physical reason for everything):
#   A garrison kept its ammunition ON the wall, where it is used: arrow sheaves of 24 next to a closed barrel (dry storage),
#   spears stooked so they stand by themselves, heaps of rounded stones to drop on the men at the wall foot (densest over
#   the gate, the point every assault goes for), and full water buckets against fire arrows (by the gate and the towers).
#   Everything stands against the PARAPET, never in the walking line: a lane of >= 1 m stays clear for the hero and the soldiers.
# A wall walk here = an up-facing stone floor with a parapet 20-160 cm to one side whose top is < 1.9 m (or a merlon), a
# drop of > 2 m behind that parapet, >= 1.6 m of free floor on the other side, and floor under the walking lane.
import math, os, random, sys, unreal

args = sys.argv[1:]
TAG = 'WS509'
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-props-509'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
SL = unreal.SystemLibrary
V = unreal.Vector
BOX = (-1900.0, -1900.0, 6500.0, 5350.0)          # the castle box (#461 scan + 15 m), same as #504
GRID = 100.0
SPACING = 700.0                                   # one cluster every ~7 m of wall walk (restraint: a real garrison, not a warehouse)
random.seed(509)
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): print('PIE RUNNING: abort'); raise SystemExit
CAMP = '/Game/_i5tmpWS509/' if '--temp' in args else '/Game/CastleDefender/Environment/Camp/'
BARR = '/Game/CastleDefender/Environment/Barracks/'
MESH = {'Arrow': CAMP + 'ArrowSheaf/SM_Camp_ArrowSheaf', 'Spear': CAMP + 'SpearStook/SM_Camp_SpearStook',
        'Stones': CAMP + 'DropStones/SM_Camp_DropStones', 'Bucket': CAMP + 'FireBucket/SM_Camp_FireBucket',
        'Barrel': BARR + 'Barrel/SM_Barracks_Barrel', 'Crate': BARR + 'Crate/SM_Barracks_Crate'}
SOLID = ('Barrel', 'Crate', 'Stones')              # these keep their box collision (you bump into them); the rest none
# (prop, offset along the parapet cm, depth from the parapet face cm, yaw offset deg, scale)
RECIPES = {
    'arrows': [('Barrel', 0, 34, 0, 1.0), ('Arrow', 48, 10, 0, 1.0), ('Arrow', 64, 12, 37, 1.0)],
    'stones': [('Stones', 0, 38, 0, 0.8)],
    'spears': [('Spear', 0, 32, 0, 1.0), ('Bucket', 52, 19, 0, 1.0)],
    'fire':   [('Bucket', 0, 19, 0, 1.0), ('Bucket', 36, 19, 120, 1.0), ('Crate', -62, 28, 0, 1.0)],
}
DEPTH = {k: max(p[2] * 2 for p in v) for k, v in RECIPES.items()}   # how far a cluster reaches into the walk


def trace(a, b):
    h = SL.line_trace_single(W, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0] or t[1]: return None
    return {'loc': t[4], 'n': t[7], 'dist': t[3], 'actor': t[9]}


def ours(h): return h and h['actor'] and TAG in [str(x) for x in h['actor'].tags]


def is_stone_floor(h):
    if not h or h['n'].z < 0.9 or ours(h): return False
    lab = (h['actor'].get_actor_label() + ' ' + h['actor'].get_class().get_name()).lower() if h['actor'] else ''
    return not any(w in lab for w in ('landscape', 'foliage', 'tree', 'water', 'plank', 'stair', 'bridge', 'cart', 'tent', 'roof'))


def find_gate():
    best = None
    for a in EAS.get_all_level_actors():
        lab = a.get_actor_label().lower()
        if 'gate' in lab and 'portal' not in lab and 'realm' not in lab and 'east' not in lab:
            p = a.get_actor_location()
            if BOX[0] < p.x < BOX[2] and BOX[1] < p.y < BOX[3]: best = best or (lab, p)
    return best


DIRS = [V(math.cos(k * math.pi / 4), math.sin(k * math.pi / 4), 0) for k in range(8)]


def walk_site(P):
    """P = a floor point. Returns (dir to the parapet, parapet distance, free distance on the walk side) or None."""
    best = None
    for d in DIRS:
        h1 = trace(P + V(0, 0, 60), P + V(0, 0, 60) + d * 260.0)
        if not h1 or abs(h1['n'].z) > 0.4 or h1['dist'] < 20.0 or ours(h1): continue
        dp = h1['dist']
        hi = trace(P + V(0, 0, 190), P + V(0, 0, 190) + d * (dp + 40.0))
        merlon = hi is not None and hi['dist'] < dp + 15.0
        # a drop behind the parapet: stepping outward over the (thick) wall top, the ground falls > 2 m below the walk
        drop = False
        for k in range(1, 9):
            Q = P + d * (dp + 50.0 * k) + V(0, 0, 330)
            dn = trace(Q, Q - V(0, 0, 1400))
            if dn and dn['loc'].z < P.z - 200.0: drop = True; break
        if not drop: continue
        if merlon and trace(P + V(0, 0, 300), P + V(0, 0, 300) + d * (dp + 40.0)): continue     # a tower wall, not a merlon
        # the walk side: free floor and air
        f1 = trace(P + V(0, 0, 60), P + V(0, 0, 60) - d * 260.0); f2 = trace(P + V(0, 0, 150), P + V(0, 0, 150) - d * 260.0)
        free = min(f1['dist'] if f1 else 260.0, f2['dist'] if f2 else 260.0)
        if free < 160.0: continue
        fl = trace(P - d * 120.0 + V(0, 0, 40), P - d * 120.0 - V(0, 0, 60))
        if not fl or abs(fl['loc'].z - P.z) > 25.0: continue                     # no hole or stairwell in the lane
        if not best or dp < best[1]: best = (d, dp, free)
    return best


def plan():
    sites = []
    x = BOX[0]
    while x < BOX[2]:
        y = BOX[1]
        while y < BOX[3]:
            h = trace(V(x, y, 6000), V(x, y, -800))
            if is_stone_floor(h) and h['loc'].z > 150.0:
                s = walk_site(h['loc'])
                if s: sites.append((h['loc'], s[0], s[1], s[2]))
            y += GRID
        x += GRID
    random.shuffle(sites)
    gate = find_gate(); gp = gate[1] if gate else None
    picked = []
    for s in sites:
        if all((s[0] - p[0]).length() > SPACING for p in picked): picked.append(s)
    out = []
    cyc = ['arrows', 'spears', 'stones', 'arrows', 'fire']
    for i, (P, d, dp, free) in enumerate(picked):
        near_gate = gp is not None and (V(P.x, P.y, 0) - V(gp.x, gp.y, 0)).length() < 1500.0
        kind = random.choice(['stones', 'stones', 'fire', 'arrows']) if near_gate else cyc[i % len(cyc)]
        if free - DEPTH[kind] < 100.0: kind = 'arrows' if free - DEPTH['arrows'] >= 100.0 else None   # keep a 1 m lane
        if kind: out.append((kind, P, d, dp, near_gate, free))
    return sites, out, gate


def xforms(kind, P, d, dp):
    r = V(-d.y, d.x, 0); yaw0 = math.degrees(math.atan2(r.y, r.x))      # the props' +X runs along the parapet
    face = P + d * dp
    flip = random.choice((1, -1))
    res = []
    for prop, off, depth, yaw, sc in RECIPES[kind]:
        p = face - d * (depth + 4.0) + r * (off * flip) + r * random.uniform(-6, 6)
        h = trace(p + V(0, 0, 60), p - V(0, 0, 80))
        z = (h['loc'].z if h else P.z) - 1.5                             # sink 1.5 cm (grounding, KB rule 5)
        t = unreal.Transform(V(p.x, p.y, z), unreal.Rotator(0, 0, yaw0 + yaw + random.uniform(-8, 8)), V(sc, sc, sc))
        res.append((prop, t))
    return res


def spawn(clusters):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); BFL = unreal.SubobjectDataBlueprintFunctionLibrary
    by = {}
    for kind, P, d, dp, ng, free in clusters:
        for prop, t in xforms(kind, P, d, dp): by.setdefault(prop, []).append(t)
    made = []
    for prop, ts in by.items():
        sm = unreal.load_asset(MESH[prop])
        if not sm: print('MISSING mesh', MESH[prop]); continue
        act = EAS.spawn_actor_from_class(unreal.Actor, V(0, 0, 0))
        act.set_actor_label('WS509_' + prop); act.tags = [unreal.Name(TAG)]; act.set_folder_path('CastleProps509')
        root = sub.k2_gather_subobject_data_for_instance(act)[0]
        hnd, why = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent))
        ism = BFL.get_object(BFL.get_data(hnd)); ism.set_static_mesh(sm)
        if prop not in SOLID: ism.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        ism.set_editor_property('can_ever_affect_navigation', False)       # zombie and soldier paths stay as they are
        for t in ts: ism.add_instance(t, True)
        made.append((prop, len(ts)))
    return made


if '--remove' in args:
    gone = [x for x in EAS.get_all_level_actors() if TAG in [str(t) for t in x.tags]]
    for x in gone: EAS.destroy_actor(x)
    print('removed', len(gone), 'WS509 actors')
    raise SystemExit
if any(TAG in [str(t) for t in x.tags] for x in EAS.get_all_level_actors()):
    print('WS509 props already in the level: run --remove first'); raise SystemExit
sites, clusters, gate = plan()
if '--near' in args:
    i = args.index('--near'); c = V(*[float(a) for a in args[i + 1:i + 4]]); rad = float(args[i + 4])
    clusters = [k for k in clusters if (k[1] - c).length() < rad]
cnt = {}
for k in clusters: cnt[k[0]] = cnt.get(k[0], 0) + 1
lines = ['wall-walk floor points %d, clusters %d %s, gate %s' % (len(sites), len(clusters), cnt, gate)]
lines += ['%-7s %8.0f %8.0f %6.0f  parapet %3.0f cm  lane %3.0f cm%s' % (k, P.x, P.y, P.z, dp, free - DEPTH[k], '  GATE' if ng else '') for k, P, d, dp, ng, free in clusters]
open(HERE + '/stores_report509.txt', 'w').write('\n'.join(lines) + '\n')
print(lines[0])
if '--apply' in args or '--near' in args and '--dry-run' not in args:
    print('spawned', spawn(clusters))
else:
    print('dry run: nothing placed (report in stores_report509.txt)')
