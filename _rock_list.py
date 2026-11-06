import unreal, os
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
origin = ps[0].get_actor_location() if ps else unreal.Vector(0, 0, 0)
rows = []
barrels = [a.get_actor_location() for a in eas.get_all_level_actors() if 'barrel' in a.get_actor_label().lower()]
for a in eas.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor): continue
    sm = a.static_mesh_component.static_mesh
    n = (sm.get_name() if sm else '').lower()
    if not any(k in n for k in ('rock', 'boulder', 'stone', 'cliff')): continue
    l = a.get_actor_location(); d = (l - origin).length()
    if d > 4000: continue
    o, ext = a.get_actor_bounds(False)
    db = min([(l - b).length() for b in barrels] or [99999])
    rows.append((ext.x * ext.y * ext.z, d, db, a.get_actor_label(), n, ext.z))
rows.sort(reverse=True)
open(r'C:\Users\hossa\Documents\agent-office\_rock_list.txt', 'w').write('\n'.join('%s | %s | dist %.0f | nearest barrel %.0f | halfH %.0f' % (r[3], r[4], r[1], r[2], r[5]) for r in rows[:15]))
print('ROCKLIST DONE')
