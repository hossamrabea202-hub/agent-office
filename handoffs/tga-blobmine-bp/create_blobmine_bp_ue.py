# MASTER ONLY (UE 5.3). Two steps in one script, both idempotent:
#  A. Creates /Game/CastleDefender/Realm/BP_BlobMine (parent Actor) with one component, 'Mine' (StaticMeshComponent =
#     laptop2's SM_Flora_BlobMine, blocks everything so shots and blades hit it), added with SubobjectDataSubsystem.
#  B. After its variables + graph are pasted: swaps every static 'Realm_BlobMine_NN' that laptop2's place_realm_ue.py put
#     in the level for a BP_BlobMine with the same transform, label and tag (so laptop2's script still cleans them up;
#     re-run this step after re-running place_realm_ue.py). Save the level afterwards.
#   py "<repo>/handoffs/tga-blobmine-bp/create_blobmine_bp_ue.py"
import unreal
DST, NAME = '/Game/CastleDefender/Realm', 'BP_BlobMine'
MESH = '/Game/CastleDefender/Environment/Flora/BlobMine/SM_Flora_BlobMine'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
path = DST + '/' + NAME
if not EAL.does_asset_exist(path):
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DST, unreal.Blueprint, f)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp))
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h): raise RuntimeError('Adding Mine failed: %s' % reason)
    sds.rename_subobject(h, unreal.Text('Mine'))
    sm = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(sds.k2_find_subobject_data_from_handle(h))
    mesh = unreal.load_asset(MESH)
    if mesh: sm.set_editor_property('static_mesh', mesh)
    else: unreal.log_warning('SM_Flora_BlobMine not found at %s: set the Mine component mesh by hand' % MESH)
    sm.set_collision_profile_name('BlockAll')
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    unreal.log('Created %s with a Mine component. Paste BP_BlobMine_vars.txt (line by line) + the EventGraph, compile, then run this script again.' % path)
else:
    cls = unreal.load_asset(path).generated_class()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); n = 0
    for a in list(eas.get_all_level_actors()):
        lab = a.get_actor_label()
        if not lab.startswith('Realm_BlobMine_') or a.get_class() == cls: continue
        t = a.get_actor_transform(); tags = a.tags; folder = a.get_folder_path()
        eas.destroy_actor(a)
        b = eas.spawn_actor_from_class(cls, t.translation, t.rotation.rotator()); b.set_actor_scale3d(t.scale3d)
        b.set_actor_label(lab); b.tags = tags; b.set_folder_path(folder); n += 1
    unreal.log('Swapped %d static blob mines for BP_BlobMine. Save the level.' % n)
