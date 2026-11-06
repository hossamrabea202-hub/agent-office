import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
A = eas.get_all_level_actors(); S = eas.get_selected_level_actors()
open(r'C:\Users\hossa\Documents\agent-office\_lvlcheck.txt', 'w').write('actors %d\nselected: %s\ndirty: %s' % (len(A), [a.get_actor_label() for a in S][:20], [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()][:10]))
