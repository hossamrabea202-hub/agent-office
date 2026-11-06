import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
M=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
for a in E.get_all_level_actors():
    if not (isinstance(a, unreal.SkeletalMeshActor) and 'CorruptedTentacle' in a.get_actor_label()): continue
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        for i,m in enumerate(c.get_materials()):
            if m and 'JellyShell' in m.get_name():
                ws=c.get_world_scale(); s=(abs(ws.x)+abs(ws.y)+abs(ws.z))/3.0
                old=M.get_material_instance_scalar_parameter_value(m,'TentScale')
                if abs(old-s)>0.01:
                    M.set_material_instance_scalar_parameter_value(m,'TentScale',s); M.update_material_instance(m); EAL.save_asset(m.get_path_name().split('.')[0])
                print(a.get_actor_label(), c.get_name(), m.get_name(), 'world scale', ws, 'TentScale', round(old,3), '->', round(s,3))
