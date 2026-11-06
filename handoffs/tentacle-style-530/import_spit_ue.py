# #533: import fbx/Tentacle_SPIT.fbx and Tentacle_CATAPULT.fbx as AS_Tentacle_Spit / _Catapult into Rig/Style530/ and make AM_Tentacle_Spit / _Catapult.
#   py import_spit_ue.py [--dry-run]       (editor idle; new assets only, re-running replaces the clips and keeps the montages)
import unreal, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); DRY = '--dry-run' in (sys.argv[1:] + os.environ.get('ST_ARGS', '').split())
R = '/Game/CastleDefender/Environment/Tentacles/Rig'; DST = R + '/Style530'
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools(); skel = unreal.load_asset(R + '/SK_CorruptedTentacle_01_Skeleton')
CLIPS = [('SPIT', 'Spit', 0.15, 0.4), ('CATAPULT', 'Catapult', 0.12, 0.6)]
for k, nm, bi, bo in CLIPS:
    f = os.path.join(HERE, 'fbx', 'Tentacle_%s.fbx' % k)
    if not os.path.exists(f): raise SystemExit('SPIT533 missing FBX (git pull?): ' + f)
    print('SPIT533 import', k, '->', DST + '/AS_Tentacle_' + nm, 'montage exists:', EAL.does_asset_exist(DST + '/AM_Tentacle_' + nm))
    if DRY: continue
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for pk, pv in [('use_default_sample_rate', False), ('custom_sample_rate', 24)]:
        try: ad.set_editor_property(pk, pv)
        except Exception: pass
    t = unreal.AssetImportTask(); t.filename = f; t.destination_path = DST; t.destination_name = 'AS_Tentacle_' + nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui
    AT.import_asset_tasks([t]); a = unreal.load_asset(DST + '/AS_Tentacle_' + nm)
    if not a: raise SystemExit('SPIT533 import failed: ' + nm)
    a.set_editor_property('enable_root_motion', False); EAL.save_loaded_asset(a)
    print('SPIT533 imported', nm, 'frames', unreal.AnimationLibrary.get_num_frames(a), 'len', round(a.get_play_length(), 3))
    if not EAL.does_asset_exist(DST + '/AM_Tentacle_' + nm):
        fa = unreal.AnimMontageFactory(); fa.set_editor_property('source_animation', a); fa.set_editor_property('target_skeleton', skel)
        m = AT.create_asset('AM_Tentacle_' + nm, DST, unreal.AnimMontage, fa)
        for key, v in (('blend_in', bi), ('blend_out', bo)):
            b = m.get_editor_property(key); b.set_editor_property('blend_time', v); m.set_editor_property(key, b)
        EAL.save_loaded_asset(m); print('SPIT533 montage', nm, round(m.get_play_length(), 3))
print('SPIT533 DONE', 'dry-run' if DRY else 'imported')
