# Read-only: the hero's components tagged KitWeapon (scale, socket, mesh). UE 5.8 Python.
import unreal
ar = unreal.AssetRegistryHelpers.get_asset_registry()
hits = [a for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == 'BP_ThirdPersonCharacter']
log = []
for ad in hits:
    bp = ad.get_asset(); log.append('== %s' % ad.package_name)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
        if isinstance(o, unreal.SceneComponent) and ('KitWeapon' in [str(t) for t in o.component_tags] or 'Weapon' in o.get_name()):
            m = o.get_editor_property('static_mesh') if isinstance(o, unreal.StaticMeshComponent) else None
            log.append('  %s tags %s scale %s rot %s socket %s mesh %s' % (o.get_name(), [str(t) for t in o.component_tags], o.relative_scale3d,
                       o.relative_rotation, o.get_attach_socket_name(), m.get_name() if m else None))
out = '\n'.join(log); unreal.log('i5 kitweapon: ' + out)
