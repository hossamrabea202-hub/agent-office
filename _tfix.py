import unreal, sys
# Tentacle skin stretch: new MI (master untouched) with shorter plates along the length, assigned to the skin slot
# of the tentacle actors that use M_CorruptedTentacle_Ripple2. --revert puts the master back.
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
M='/Game/CastleDefender/Environment/Tentacles/M_CorruptedTentacle_Ripple2'; P='/Game/CastleDefender/Environment/Tentacles/MI_CorruptedTentacle_NoStretch'
LB, LT, TILE = float(sys.argv[1]) if len(sys.argv)>1 and sys.argv[1][0].isdigit() else 650.0, 170.0, 3.0
master=unreal.load_asset(M)
if not EAL.does_asset_exist(P):
    mi=unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_CorruptedTentacle_NoStretch','/Game/CastleDefender/Environment/Tentacles',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, master)
mi=unreal.load_asset(P)
MEL.set_material_instance_scalar_parameter_value(mi,'HideLenBase',LB); MEL.set_material_instance_scalar_parameter_value(mi,'HideLenTip',LT); MEL.set_material_instance_scalar_parameter_value(mi,'HideTile',TILE)
MEL.update_material_instance(mi); EAL.save_asset(P)
rev='--revert' in sys.argv; n=0
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if not isinstance(a, unreal.SkeletalMeshActor): continue
    c=a.skeletal_mesh_component
    for i,m in enumerate(c.get_materials()):
        if m and m.get_path_name().split('.')[0] in ((P if rev else M),):
            c.set_material(i, master if rev else mi); n+=1
            print(a.get_actor_label(), 'scale', a.get_actor_scale3d())
print('set', n, 'LenBase', LB, 'LenTip', LT, 'saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels())
