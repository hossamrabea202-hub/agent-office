import unreal, traceback
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); w = ues.get_editor_world()
    dirty = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    out.append('dirty maps: %s' % dirty)
    cls = unreal.load_class(None, '/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager.BP_JellyTrailManager_C')
    mgr = unreal.GameplayStatics.get_all_actors_of_class(w, cls)[0]
    ism = mgr.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    out.append('trail instances in editor world: %d' % ism.get_instance_count())
    if ism.get_instance_count() == 0:
        ok = unreal.EditorLoadingAndSavingUtils.save_map(w, '/Game/ThirdPerson/Maps/ThirdPersonMap'); out.append('map saved: %s' % ok)
    else:
        out.append('NOT saved: instances still present')
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
