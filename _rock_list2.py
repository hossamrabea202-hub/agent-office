import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
A = eas.get_all_level_actors()
barrels = [a for a in A if 'barrel' in a.get_actor_label().lower()]
rows = {}
for a in A:
    if not isinstance(a, unreal.StaticMeshActor) or 'barrel' in a.get_actor_label().lower(): continue
    sm = a.static_mesh_component.static_mesh
    if not sm: continue
    l = a.get_actor_location(); o, ext = a.get_actor_bounds(False)
    if ext.z < 40 or ext.x > 1500 or ext.y > 1500: continue
    for b in barrels:
        d = (l - b.get_actor_location()).length()
        if d < 800:
            rows[a.get_actor_label()] = '%s | %s | %s | barrel %.0f | ext %.0f %.0f %.0f' % (a.get_actor_label(), sm.get_name(), a.get_folder_path(), d, ext.x, ext.y, ext.z); break
open(r'C:\Users\hossa\Documents\agent-office\_rock_list2.txt', 'w').write('%d barrels\n' % len(barrels) + '\n'.join(sorted(rows.values())))
print('ROCKLIST2 DONE')
