import unreal, traceback
OUT = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
L = []
try:
    bp = unreal.load_asset('/Game/Codex/AssignmentMarkers102_v1/BP_AssignmentMarker102')
    BPL = unreal.BlueprintEditorLibrary
    BPL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('hidden', True)
    cdo.set_editor_property('replicates', False)
    BPL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        d = sds.k2_find_subobject_data_from_handle(h)
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
        L.append('sub %s %s' % (unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(d), o.get_class().get_name() if o else None))
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
    L.append('ok')
except Exception:
    L.append(traceback.format_exc())
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
