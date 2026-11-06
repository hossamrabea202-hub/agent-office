# #450 cannon reactions: import out450/Tentacle_CannonA|B|C.fbx as AS_Tentacle_CannonA|B|C (24 fps, on the tentacle
# skeleton) into Environment/Tentacles/Rig/Polish457/ and make the montages AM_Tentacle_CannonA|B|C (blend in 0.08, out 0.6).
#   py "<repo>/handoffs/tentacle-anim-457/import_cannon_ue.py" [--dry-run]       (editor idle; re-running replaces the clips, keeps the montages)
import unreal, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); DRY = '--dry-run' in sys.argv
R = '/Game/CastleDefender/Environment/Tentacles/Rig'; DST = R + '/Polish457'
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
skel = unreal.load_asset(R + '/SK_CorruptedTentacle_01_Skeleton')
if not skel: raise SystemExit('CANNON450 skeleton missing: ' + R + '/SK_CorruptedTentacle_01_Skeleton')
files = [os.path.join(HERE, 'out450', 'Tentacle_Cannon%s.fbx' % w) for w in 'ABC']
missing = [f for f in files if not os.path.exists(f)]
if missing: raise SystemExit('CANNON450 missing FBX (git pull?): %s' % missing)
tasks = []
for f in files:
    nm = 'AS_' + os.path.splitext(os.path.basename(f))[0]
    print('CANNON450 import', os.path.basename(f), '->', DST + '/' + nm, '(replace)' if EAL.does_asset_exist(DST + '/' + nm) else '(new)')
    if DRY: continue
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in [('use_default_sample_rate', False), ('custom_sample_rate', 24)]:
        try: ad.set_editor_property(k, v)
        except Exception: pass
    t = unreal.AssetImportTask(); t.filename = f; t.destination_path = DST; t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; tasks.append(t)
if tasks: AT.import_asset_tasks(tasks)
for w in 'ABC':
    nm = 'AS_Tentacle_Cannon' + w; mon = DST + '/AM_Tentacle_Cannon' + w
    if DRY: print('CANNON450 would make montage', mon, 'unless it exists:', EAL.does_asset_exist(mon)); continue
    a = unreal.load_asset(DST + '/' + nm)
    if not a: raise SystemExit('CANNON450 import failed for ' + nm)
    print('CANNON450', nm, 'frames', unreal.AnimationLibrary.get_num_frames(a), 'len', round(a.get_play_length(), 3), 'skel', a.get_editor_property('skeleton').get_name())
    if not EAL.does_asset_exist(mon):
        f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', a); f.set_editor_property('target_skeleton', skel)
        m = AT.create_asset('AM_Tentacle_Cannon' + w, DST, unreal.AnimMontage, f)
        for k, v in (('blend_in', 0.08), ('blend_out', 0.6)):
            b = m.get_editor_property(k); b.set_editor_property('blend_time', v); m.set_editor_property(k, b)
        EAL.save_loaded_asset(m); print('CANNON450 montage', mon, round(m.get_play_length(), 3))
print('CANNON450 DONE', 'dry-run' if DRY else 'imported')
