# Cape / hero armour material state: which materials are dirty, do they compile, what does the hero cape use.
import unreal, traceback
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    dirty = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    out.append('DIRTY: %s' % dirty)
    for p in dirty:
        m = unreal.load_asset(p)
        if isinstance(m, unreal.Material):
            out.append('  %s domain=%s blend=%s' % (p, m.get_editor_property('material_domain'), m.get_editor_property('blend_mode')))
    hero = unreal.load_asset('/Game/CastleDefender/Characters/Hero/BP_ThirdPersonCharacter')
    if not hero:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        hits = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == 'BP_ThirdPersonCharacter']
        hero = unreal.load_asset(str(hits[0].package_name)) if hits else None
    out.append('hero BP: %s' % (hero.get_path_name() if hero else None))
    if hero:
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        for h in sds.k2_gather_subobject_data_for_blueprint(hero):
            o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
            if isinstance(o, unreal.MeshComponent):
                out.append('  %s cls=%s mesh=%s mats=%s' % (o.get_name(), o.get_class().get_name(), (o.get_editor_property('skeletal_mesh_asset').get_name() if isinstance(o, unreal.SkeletalMeshComponent) and o.get_editor_property('skeletal_mesh_asset') else (o.static_mesh.get_name() if isinstance(o, unreal.StaticMeshComponent) and o.static_mesh else None)), [m.get_path_name() if m else None for m in o.get_materials()]))
    for nm in ['BP_SoldierSword', 'BP_SoldierXbow']:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        hh = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == nm]
        if not hh: out.append(nm + ' not found'); continue
        b = unreal.load_asset(str(hh[0].package_name)); out.append(nm + ' ' + str(hh[0].package_name))
        for h in sds.k2_gather_subobject_data_for_blueprint(b):
            o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
            if isinstance(o, unreal.MeshComponent) and ('Cape' in o.get_name() or 'Cloak' in o.get_name()):
                sk = o.get_editor_property('skeletal_mesh_asset') if isinstance(o, unreal.SkeletalMeshComponent) else None
                out.append('  %s cls=%s mesh=%s attachParent=%s socket=%s leaderPose=%s cloth=%s mats=%s' % (o.get_name(), o.get_class().get_name(), sk.get_name() if sk else None,
                    o.get_attach_parent().get_name() if o.get_attach_parent() else None, o.get_attach_socket_name(),
                    (o.get_editor_property('leader_pose_component').get_name() if isinstance(o, unreal.SkinnedMeshComponent) and o.get_editor_property('leader_pose_component') else None),
                    (len(sk.get_editor_property('mesh_clothing_assets')) if sk else None), [m.get_path_name() if m else None for m in o.get_materials()]))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
