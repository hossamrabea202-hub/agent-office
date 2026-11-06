import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
ar = unreal.AssetRegistryHelpers.get_asset_registry()
wf = [str(a.package_name) for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')) if str(a.asset_name) == 'MI_Castle_WalkFlag_World'][0]
mat = unreal.load_asset(wf); n = 0
with unreal.ScopedEditorTransaction('Walk slabs -> world flagstones (#228)'):
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name() == 'SM_WalkSlab':
            c = a.static_mesh_component
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                if m and m.get_name() == 'MI_Castle_Paving_Walk': a.modify(); c.set_material(i, mat); n += 1
L.append('walk slab material slots switched: %d' % n)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_fix_walkslab.txt', 'w').write('\n'.join(L)); print('WS', L)
