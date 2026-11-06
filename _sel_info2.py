import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = []
for a in eas.get_selected_level_actors():
    L.append('%s | %s | %s' % (a.get_actor_label(), a.get_class().get_path_name(), a.get_folder_path()))
    for c in a.get_components_by_class(unreal.SceneComponent):
        s = '   %s [%s] vis=%s hidden=%s' % (c.get_name(), c.get_class().get_name(), c.is_visible(), c.get_editor_property('hidden_in_game'))
        if isinstance(c, unreal.StaticMeshComponent):
            s += ' mesh=%s coll=%s stepup=%s' % (c.static_mesh.get_name() if c.static_mesh else None, c.get_collision_enabled(), c.get_editor_property('can_character_step_up_on'))
        L.append(s)
others = [x.get_actor_label() for x in eas.get_all_level_actors() if x.get_class() == (eas.get_selected_level_actors() or [None])[0].get_class()] if eas.get_selected_level_actors() else []
L.append('SAME CLASS: ' + ', '.join(others))
open(r'C:\Users\hossa\Documents\agent-office\_sel_info2.txt', 'w').write('\n'.join(L) or 'NOTHING SELECTED')
print('SEL2 DONE')
