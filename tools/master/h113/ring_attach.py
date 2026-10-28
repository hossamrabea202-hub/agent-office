import unreal, traceback
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    EAL = unreal.EditorAssetLibrary
    comp_bp = unreal.load_asset('/Game/Codex/AssignmentMarkers102_v1/BPC_AssignmentRing')
    comp_cls = comp_bp.generated_class()
    tbp = unreal.load_asset('/Game/CastleDefender/Characters/Knight/BP_SoldierSword')
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(tbp)
    names = [unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)).get_name() for h in handles]
    out.append('BP_SoldierSword components: %s' % names)
    if not any('AssignmentRing' in n for n in names):
        p = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=comp_cls, blueprint_context=tbp)
        h, fail = sds.add_new_subobject(p)
        out.append('add result: %s fail=%s' % (h, fail))
        sds.rename_subobject(h, unreal.Text('AssignmentRing'))
        unreal.BlueprintEditorLibrary.compile_blueprint(tbp)
        ok = EAL.save_loaded_asset(tbp); out.append('BP_SoldierSword compiled + saved: %s' % ok)
    else:
        out.append('already attached')
    # verify
    names2 = [unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)).get_name() for h in sds.k2_gather_subobject_data_for_blueprint(tbp)]
    out.append('now: %s' % [n for n in names2 if 'Ring' in n])
except Exception:
    out.append(traceback.format_exc())
open(L, 'w', encoding='utf-8').write('\n'.join(out))
