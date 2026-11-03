# Invisible walls (i5, 2026-11-03): after-save health found 275 hidden pieces with collision on. Reviewed from aftersave_health.json:
#   KEEP, hidden on purpose, never touched here: TentacleHit_* (130, the tentacles' hit capsules), Collision/StairRamps + Tower9_StairRamp (13),
#     SM_KeepEntrance_Baked (i9's collider), Siege_138 (breach pieces), everything outside the folders below.
#   CANDIDATES: Gate_Old_AAA (62), Wall_Old_AAA (50), FireFX/WellFireLogs (9): old pieces replaced by AAA modules.
# A candidate loses collision only if something VISIBLE already blocks at its place: 27 rays through its box (3 axes, 9 each, both directions, hidden actors ignored,
# complex collision), and at least 60 % must hit a visible non-landscape actor within 300 cm of the box. Anything less stays as it is and is listed as SOLE.
#   py hidden_collision_ue.py --dry-run     lists COVERED / SOLE, changes nothing
#   py hidden_collision_ue.py --apply       collision off on COVERED only; backup hidden_collision_backup.json. Not saved: rebuild nav, check nav 8/8, Play, then save the map
#   py hidden_collision_ue.py --revert      collision back as it was
# Aborts in PIE.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
H = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/', 'C:/Users/hossa/Documents/agent-office/handoffs/castle-harmony-461/') if os.path.isdir(h))
BK = H + 'hidden_collision_backup.json'
FOLDERS = ('Gate_Old_AAA', 'Wall_Old_AAA', 'FireFX/WellFireLogs')
THRESH, NEAR, REACH = 0.60, 300.0, 1500.0
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
def hidden(a, c=None):
    if a.is_hidden_ed() or a.get_editor_property('hidden'): return True
    return bool(c) and (not c.get_editor_property('visible') or c.get_editor_property('hidden_in_game'))
def key(a, c): return a.get_path_name() + '|' + c.get_name()
if '--revert' in A:
    if not os.path.exists(BK): print('NO BACKUP', BK); raise SystemExit
    d = json.load(open(BK)); by = {key(a, c): c for a in actors for c in a.get_components_by_class(unreal.StaticMeshComponent)}; n = 0
    for k, v in d.items():
        c = by.get(k)
        if not c: print('MISSING', k); continue
        c.modify(); c.set_collision_enabled(getattr(unreal.CollisionEnabled, v)); n += 1
    os.remove(BK); print('reverted', n); raise SystemExit
if os.path.exists(BK): print('ALREADY APPLIED (backup exists): --revert first'); raise SystemExit
ignore = [a for a in actors if hidden(a)]
cand = []
for a in actors:
    if str(a.get_folder_path()) not in FOLDERS: continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if hidden(a, c) and c.get_static_mesh() and c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION: cand.append((a, c))
print('hidden actors ignored by the rays:', len(ignore), '| candidates:', len(cand))
def ray(p, q, o, e):
    h = unreal.SystemLibrary.line_trace_single(w, p, q, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True).to_tuple()
    if not h[0] or isinstance(h[9], unreal.LandscapeProxy) or (h[9] and hidden(h[9])): return False
    l = h[4]
    return abs(l.x - o.x) <= e.x + NEAR and abs(l.y - o.y) <= e.y + NEAR and abs(l.z - o.z) <= e.z + NEAR
def coverage(c):
    o, e, _ = unreal.SystemLibrary.get_component_bounds(c); hits = tot = 0
    V = lambda v: unreal.Vector(*v); C, E = [o.x, o.y, o.z], [e.x, e.y, e.z]
    for ax in range(3):
        u, v = (ax + 1) % 3, (ax + 2) % 3
        for du in (-0.6, 0, 0.6):
            for dv in (-0.6, 0, 0.6):
                s = list(C); s[u] += du * E[u]; s[v] += dv * E[v]
                a_, b_ = list(s), list(s); a_[ax] = C[ax] - E[ax] - REACH; b_[ax] = C[ax] + E[ax] + REACH
                tot += 1
                if ray(V(a_), V(s), o, e) or ray(V(b_), V(s), o, e): hits += 1
    return hits / max(tot, 1)
covered, sole = [], []
for a, c in cand:
    r = coverage(c); (covered if r >= THRESH else sole).append((a, c, r))
print('COVERED', len(covered), '| SOLE (kept)', len(sole))
for a, c, r in sorted(sole, key=lambda t: t[2]): print('  SOLE %-46s %3d %% %s' % (a.get_actor_label(), r * 100, str(a.get_folder_path())))
for a, c, r in sorted(covered, key=lambda t: t[2])[:10]: print('  lowest covered %-40s %3d %%' % (a.get_actor_label(), r * 100))
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
json.dump({key(a, c): str(c.get_collision_enabled()).split('.')[-1].split(':')[0].strip('<> ') for a, c, r in covered}, open(BK, 'w'), indent=1)
for a, c, r in covered: c.modify(); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
print('APPLIED to', len(covered), '- not saved. Rebuild nav, check nav 8/8, walk the walls + gate in Play, then save the map. Undo: --revert')
