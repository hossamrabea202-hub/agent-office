import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = []
for a in eas.get_selected_level_actors():
    o, e = a.get_actor_bounds(False)
    L.append('%s | class %s | folder %s | loc %s | ext %s' % (a.get_actor_label(), a.get_class().get_name(), a.get_folder_path(), a.get_actor_location(), e))
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        L.append('   comp %s mesh %s stepup %s' % (c.get_name(), c.static_mesh.get_path_name() if c.static_mesh else None, c.get_editor_property('can_character_step_up_on')))
    p = a.get_attach_parent_actor()
    if p: L.append('   parent ' + p.get_actor_label())
    own = a.get_owner()
    if own: L.append('   owner ' + own.get_actor_label())
open(r'C:\Users\hossa\Documents\agent-office\_sel_info.txt', 'w').write('\n'.join(L) or 'NOTHING SELECTED')
print('SEL DONE')
