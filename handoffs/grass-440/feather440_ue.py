# #440 phase B meadow edge (i5, 2026-11-03): adds the short grass from feather_plan.csv (feather440.py) to Env_GrassTall's own components, so
# it uses the phase A _440 materials. Each point is traced down: only on Landscape, not steeper than ~30 degrees. Aborts in PIE.
#   py feather440_ue.py --dry-run     traces, counts, changes nothing
#   py feather440_ue.py --apply       adds the instances; backup = instance counts in feather_backup.json. Nothing saved: Master saves the map
#   py feather440_ue.py --revert      removes exactly the added instances (the last ones of each component)
# Run nothing else on Env_GrassTall between --apply and --revert: revert keeps the first N instances of each component.
import csv, json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
H = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/grass-440/', 'C:/Users/hossa/Documents/agent-office/handoffs/grass-440/') if os.path.exists(h + 'feather_plan.csv'))
BK = H + 'feather_backup.json'
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == 'Env_GrassTall']
if len(actors) != 1: print('EXPECTED 1 Env_GrassTall, found', len(actors), 'abort'); raise SystemExit
comps = {}
for c in actors[0].get_components_by_class(unreal.InstancedStaticMeshComponent):
    m = c.get_editor_property('static_mesh')
    if m and m.get_name().startswith('SM_vczndjqja_Var'): comps[m.get_name()[-1]] = c
print('components:', {k: c.get_instance_count() for k, c in sorted(comps.items())})

if '--revert' in A:
    if not os.path.exists(BK): print('NO BACKUP', BK); raise SystemExit
    d = json.load(open(BK))
    for k, n in d.items():
        c = comps[k]; xf = [c.get_instance_transform(i, True) for i in range(n)]
        c.modify(); c.clear_instances(); c.add_instances(xf, False, True); print('REVERT', k, '->', c.get_instance_count())
    os.remove(BK); print('reverted'); raise SystemExit
if os.path.exists(BK): print('ALREADY APPLIED (feather_backup.json exists): --revert first'); raise SystemExit

add, skip = {}, {'no_var': 0, 'miss': 0, 'not_landscape': 0, 'steep': 0}
for r in csv.DictReader(open(H + 'feather_plan.csv')):
    if r['var'] not in comps: skip['no_var'] += 1; continue
    x, y = float(r['x']), float(r['y'])
    h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -20000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
    if not h[0]: skip['miss'] += 1; continue
    if not isinstance(h[9], unreal.LandscapeProxy): skip['not_landscape'] += 1; continue
    if h[7].z < 0.86: skip['steep'] += 1; continue
    s, sxy = float(r['sz']), float(r['sxy'])
    add.setdefault(r['var'], []).append(unreal.Transform(unreal.Vector(x, y, h[4].z - 2.0), unreal.Rotator(0, 0, float(r['yaw'])), unreal.Vector(sxy, sxy, s)))
print('to add:', {k: len(v) for k, v in sorted(add.items())}, 'total', sum(len(v) for v in add.values()), '| skipped:', skip)
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
json.dump({k: comps[k].get_instance_count() for k in add}, open(BK, 'w'), indent=1)
for k, xs in add.items():
    c = comps[k]; c.modify(); c.add_instances(xs, False, True); print('ADDED', k, len(xs), '->', c.get_instance_count())
print('APPLIED, not saved. Look from the wall walk and the gate road, then save the map. Undo: --revert')
