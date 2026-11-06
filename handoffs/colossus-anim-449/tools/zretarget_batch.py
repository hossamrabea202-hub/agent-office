import unreal, os
EAL = unreal.EditorAssetLibrary; KN = '/Game/CastleDefender/Characters/Knight'; ZW = '/Game/CastleDefender/Characters/Enemies/Zombie/Anims_Walkers'
OUT = 'C:/Users/hossam.rabea/ckw/ztools/fbx_knight'
rtg = unreal.load_asset(KN + '/Retarget/RTG_Zombie_to_Knight')
src_mesh = unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/SK_Zombie'); tgt_mesh = unreal.load_asset('/Game/ShadowKight/Mesh/ShadowknightUE_SK')
names = os.environ.get('Z_RT', 'ZW_Walk_Shamble,ZW_Idle_Shamble,ZW_Attack_Claw').split(',')
arr = unreal.Array(unreal.AssetData)
for c in names: arr.append(unreal.AssetRegistryHelpers.create_asset_data(unreal.load_asset(ZW + '/' + c)))
res = unreal.IKRetargetBatchOperation.duplicate_and_retarget(arr, src_mesh, tgt_mesh, rtg, search='', replace='', prefix='KN_', suffix='', target_path=ZW, use_source_path=False, include_referenced_assets=False, overwrite_existing_files=True)
print('RT334 retargeted', [str(r.asset_name) for r in res])
for r in res:
    s = unreal.load_asset(str(r.package_name)); EAL.save_loaded_asset(s); n = s.get_name()
    t = unreal.AssetExportTask(); t.object = s; t.filename = OUT + '/' + n + '.fbx'; t.automated = True; t.prompt = False; t.replace_identical = True
    o = unreal.FbxExportOption(); o.set_editor_property('export_preview_mesh', False); t.options = o
    print('RT334 export', n, unreal.Exporter.run_asset_export_task(t), 'skeleton', s.get_editor_property('skeleton').get_name(), 'frames', unreal.AnimationLibrary.get_num_frames(s))
print('RT334 DONE')
