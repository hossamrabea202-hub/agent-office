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
            if isinstance(o, unreal.MeshComponent) and ('Cape' in o.get_name() or 'Cloak' in o.get_name() or isinstance(o, unreal.SkeletalMeshComponent)):
                out.append('  %s mats=%s' % (o.get_name(), [m.get_path_name() if m else None for m in o.get_materials()]))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
