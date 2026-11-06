# Unreal: import authored FBX clips onto SK_Zombie_Skeleton as new AnimSequences.
#   env Z_IMPORT="C:/a.fbx,C:/b.fbx"   Z_DEST=/Game/CastleDefender/Characters/Enemies/Zombie/Anims_Colossus (default)
import unreal, os
R = '/Game/CastleDefender/Characters/Enemies/Zombie'
DEST = os.environ.get('Z_DEST', R + '/Anims_Colossus')
skel = unreal.load_asset(R + '/SK_Zombie_Skeleton')
tasks = []
for f in [x for x in os.environ.get('Z_IMPORT', '').split(',') if x]:
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data')
    ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in [('use_default_sample_rate', False), ('custom_sample_rate', 30)]:
        try: ad.set_editor_property(k, v)
        except Exception as e: print('opt', k, e)
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', f); t.set_editor_property('destination_path', DEST)
    t.set_editor_property('destination_name', os.path.splitext(os.path.basename(f))[0])
    t.set_editor_property('automated', True); t.set_editor_property('replace_existing', True); t.set_editor_property('save', True)
    t.set_editor_property('options', ui); tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for t in tasks: print('IMPORTED', t.get_editor_property('filename'), [str(p) for p in t.get_editor_property('imported_object_paths')])
print('IMPORT OK')
