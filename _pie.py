import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
v=[a for a in E.get_all_level_actors() if 'vesna' in a.get_actor_label().lower() or 'armor' in a.get_actor_label().lower() or 'armou' in a.get_actor_label().lower()]
print([(a.get_actor_label(),a.get_class().get_name(),a.get_actor_location()) for a in v][:15])
