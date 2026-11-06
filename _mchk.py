import unreal
r=[]
EAS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    if a.get_actor_label().startswith('Mine297_Chamber') or a.get_actor_label().startswith('Mine297_Tunnel_Straight') or a.get_actor_label().startswith('MineDoor'):
        c,e=a.get_actor_bounds(False)
        sm=a.static_mesh_component.static_mesh if hasattr(a,'static_mesh_component') else None
        r.append('%s lvl=%s hidden=%s mesh=%s ext=%s mats=%s'%(a.get_actor_label(),a.get_level().get_outermost().get_name(),a.is_hidden_ed(),sm.get_name() if sm else None,e,[m.get_name() if m else None for m in (a.static_mesh_component.get_materials() if sm else [])]))
w=unreal.EditorLevelLibrary.get_editor_world()
for l in unreal.EditorLevelUtils.get_levels(w): r.append('level %s'%l.get_outermost().get_name())
print('\n'.join(r))
