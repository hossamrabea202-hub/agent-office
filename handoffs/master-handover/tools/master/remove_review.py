import unreal, traceback
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level('/Game/ThirdPerson/Maps/ThirdPersonMap')
    out.append('loaded castle map')
    EAL = unreal.EditorAssetLibrary
    listed = EAL.list_assets('/Game/Review', True, False)
    out.append('review assets: %s' % listed)
    ok = EAL.delete_directory('/Game/Review')
    out.append('deleted /Game/Review: %s; remaining=%s' % (ok, EAL.list_assets('/Game/Review', True, False)))
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out.append('current world: %s actors=%d' % (w.get_name(), len(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())))
    import os
    for n, p in (('BP_CastleGateLever', '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateLever'), ('BP_CastleGateControl', '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl')):
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        hh = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == n]
        if hh:
            bp = unreal.load_asset(str(hh[0].package_name)); f = r'C:\Users\hossa\Documents\agent-office\handoffs\exports\laptop2\prompt68\' + n + '.t3d'
            t = unreal.AssetExportTask(); t.set_editor_property('object', bp); t.set_editor_property('filename', f)
            t.set_editor_property('exporter', unreal.ObjectExporterT3D()); t.set_editor_property('automated', True); t.set_editor_property('prompt', False); t.set_editor_property('replace_identical', True)
            out.append('%s export ok=%s size=%s' % (n, unreal.Exporter.run_asset_export_task(t), os.path.getsize(f) if os.path.exists(f) else None))
    out.append('dirty maps: %s' % [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()])
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
