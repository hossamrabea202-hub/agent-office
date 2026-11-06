import unreal
AR=unreal.AssetRegistryHelpers.get_asset_registry(); E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for lab in ('Env_WornGround_Decal','YW_Mud_GateRoad','GateMudPath'):
    a=[x for x in E.get_all_level_actors() if x.get_actor_label()==lab][0]
    m=a.decal.decal_material
    print(lab, a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d(), a.decal.decal_size, m.get_path_name())
    for d in AR.get_dependencies(m.get_outermost().get_name(), unreal.AssetRegistryDependencyOptions()):
        d=str(d); print('   dep', d)
        o=unreal.load_asset(d) if d.startswith('/Game') else None
        if isinstance(o, unreal.Texture2D):
            try: print('     src', o.get_editor_property('asset_import_data').get_first_filename(), o.blueprint_get_size_x(), o.blueprint_get_size_y())
            except Exception as e: print('     src?', e)
