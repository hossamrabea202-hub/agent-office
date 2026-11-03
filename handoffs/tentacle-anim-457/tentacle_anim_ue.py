# #457 polished tentacle idles (i5, 2026-11-03). NEW assets only; the old Ripple/Sway clips stay. Aborts in PIE.
#   py tentacle_anim_ue.py import                       out/Polish457_A/B/C.fbx -> AS_Tentacle_Polish457_A/B/C (anim only, on
#                                                        SK_CorruptedTentacle_01_Skeleton) in .../Tentacles/Rig/Polish457, saved
#   py tentacle_anim_ue.py swap --only Env_CorruptedTentacle_02 --apply | --revert   (one actor, live, for the check)
#   py tentacle_anim_ue.py swap --dry-run | --apply | --revert                        (all 8 placed tentacles + their JellyShell)
# Mapping: Ripple -> A, Ripple_Sway000/020 -> B, Ripple_Sway030/040 -> C; each actor keeps its own play rate and start
# position (they were already de-synced). Backup of the old clip per component: tentacle_anim_backup.json.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; mode = A[0]
H = 'C:/Users/hossam.rabea/agent-office/handoffs/tentacle-anim-457/'
RIG = '/Game/CastleDefender/Environment/Tentacles/Rig/'
DST = RIG + 'Polish457'
BK = H + 'tentacle_anim_backup.json'
EAL = unreal.EditorAssetLibrary
MAP = {'Ripple': 'A', 'Ripple_Sway000': 'B', 'Ripple_Sway020': 'B', 'Ripple_Sway030': 'C', 'Ripple_Sway040': 'C'}

if mode == 'import':
    skel = unreal.load_asset(RIG + 'SK_CorruptedTentacle_01_Skeleton')
    for v in (A[1:] or ['A', 'B', 'C']):                  # 'HitReact450' imports out/Tentacle_HitReact450.fbx (#450)
        ui = unreal.FbxImportUI()
        ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
        ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
        ui.set_editor_property('import_as_skeletal', True); ui.set_editor_property('skeleton', skel)
        ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
        ad = ui.get_editor_property('anim_sequence_import_data')
        ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
        src, nm = ('out/Tentacle_HitReact450.fbx', 'AS_Tentacle_HitReact450') if v == 'HitReact450' else ('out/Polish457_%s.fbx' % v, 'AS_Tentacle_Polish457_' + v)
        t = unreal.AssetImportTask(); t.filename = H + src; t.destination_path = DST
        t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = False; t.options = ui
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        paths = [p for p in t.get_editor_property('imported_object_paths')]
        a = next((unreal.load_asset(p) for p in paths if isinstance(unreal.load_asset(p), unreal.AnimSequence)), None)
        if not a: print('IMPORT FAILED', v, paths); continue
        a.set_editor_property('enable_root_motion', False)
        EAL.save_loaded_asset(a)
        print('IMPORT OK', a.get_path_name(), 'len', round(a.get_editor_property('sequence_length'), 2), 'skel', a.get_editor_property('skeleton').get_name())
    raise SystemExit

if mode == 'swap':
    only = A[A.index('--only') + 1].split(',') if '--only' in A else None
    bk = json.load(open(BK)) if os.path.exists(BK) else {}
    n = 0
    for act in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if only and act.get_actor_label() not in only: continue
        for c in act.get_components_by_class(unreal.SkeletalMeshComponent):
            m = c.get_editor_property('skinned_asset')
            if not m or m.get_name() != 'SK_CorruptedTentacle_01': continue
            key = act.get_actor_label() + '/' + c.get_name()
            ad = c.get_editor_property('animation_data'); cur = ad.anim_to_play
            if '--revert' in A:
                if key not in bk: continue
                new = unreal.load_asset(bk[key])
            else:
                if not cur: continue
                suf = cur.get_name().replace('SK_CorruptedTentacle_01_Anim_', '')
                v = MAP.get(suf)
                if not v: print('SKIP', key, cur.get_name()); continue
                new = unreal.load_asset(DST + '/AS_Tentacle_Polish457_' + v)
            n += 1
            print('SWAP', key, cur.get_name() if cur else None, '->', new.get_name(), 'rate', round(ad.saved_play_rate, 2), 'pos', round(ad.saved_position, 2))
            if '--dry-run' in A: continue
            if '--revert' not in A and 'Polish457' not in (cur.get_name() if cur else ''): bk[key] = cur.get_path_name()
            act.modify(); c.modify()
            ad.anim_to_play = new; c.set_editor_property('animation_data', ad)
            c.play_animation(new, True); c.set_play_rate(ad.saved_play_rate); c.set_position(ad.saved_position, False)
    if '--dry-run' not in A and '--revert' not in A: json.dump(bk, open(BK, 'w'), indent=1)
    print('swapped' if '--dry-run' not in A else 'would swap', n)
    raise SystemExit
