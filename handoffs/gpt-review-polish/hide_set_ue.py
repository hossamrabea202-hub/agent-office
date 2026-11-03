# #451 hide a matched set of StaticMeshActors (i5, 2026-11-03). Never deletes: hidden in game + editor view, collision off,
# backup per set; --revert shows them again with their old collision. Decal actors are never matched.
#   py hide_set_ue.py <set> --mesh Cube --mat MI_Castle_Paving_POM --size 298x288 --top 3.2 [--dry-run | --apply | --revert]
# Set "paving_plates": the courtyard had 120 separate 3 m paving plates (1.2 cm thick) laid on a 3 m grid ON TOP of the
# continuous Castle_CourtyardFloor_Single (same cobble material). The plates cut the cobbles into a 3 m tile grid with 2 cm
# gaps (shots/litpaving_A.png). A real cobbled courtyard is laid continuously; hiding the plates shows the continuous floor
# (it receives decals, so the mud decals stay).
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]; name = A[0]
opt = lambda k: A[A.index(k) + 1] if k in A else None
BK = H + 'hide_%s_backup.json' % name
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
if '--revert' in A:
    n = 0
    for path, b in json.load(open(BK)).items():
        a = acts.get(path)
        if not a: print('missing', path); continue
        c = a.static_mesh_component; a.modify(); a.set_actor_hidden_in_game(False); c.set_visibility(True)
        c.set_collision_enabled(getattr(unreal.CollisionEnabled, b['coll'])); n += 1
    print('revert %s: %d shown again' % (name, n)); raise SystemExit
mesh, mat, size, top = opt('--mesh'), opt('--mat'), opt('--size'), opt('--top')
sx, sy = [float(v) for v in size.split('x')] if size else (None, None)
hits = []
for a in acts.values():
    if a.get_class().get_name() != 'StaticMeshActor' or isinstance(a, unreal.DecalActor): continue
    c = a.static_mesh_component; m = c.get_editor_property('static_mesh')
    if not m or not c.is_visible(): continue
    if mesh and m.get_name() != mesh: continue
    mi = c.get_materials()[0] if c.get_materials() else None
    if mat and (not mi or mi.get_name() != mat): continue
    o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
    if size and not (abs(e.x * 2 - sx) < 1.5 and abs(e.y * 2 - sy) < 1.5): continue
    if top and abs(o.z + e.z - float(top)) > 0.3: continue
    hits.append(a)
backup = json.load(open(BK)) if os.path.exists(BK) and '--apply' in A else {}
if '--apply' in A:
    for a in hits:
        c = a.static_mesh_component
        backup.setdefault(a.get_path_name(), {'label': a.get_actor_label(), 'coll': c.get_collision_enabled().name})
        a.modify(); a.set_actor_hidden_in_game(True); c.set_visibility(False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    json.dump(backup, open(BK, 'w'), indent=0)
out = '%s %s: %d actors %s' % ('APPLIED' if '--apply' in A else 'DRY RUN', name, len(hits), 'hidden (backup %s)' % BK if '--apply' in A else 'match')
open(H + 'hide_%s_log.txt' % name, 'w', encoding='utf-8').write(out + '\n' + '\n'.join(sorted(a.get_actor_label() for a in hits)))
print(out)
