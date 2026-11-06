# Clean-up on a COPY of the owner's bubble. The original SM_RealmBubbleHi and the level are untouched.
import unreal
L=[]
EAL=unreal.EditorAssetLibrary
SRC='/Game/CastleDefender/Gameplay/Realm/_Backup/SM_RealmBubbleHi_20261031_2228'
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
bub=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Realm_Bubble_Owner'][0]
live=bub.static_mesh_component.static_mesh
DST=live.get_path_name().split('.')[0]+'_Clean'
if EAL.does_asset_exist(DST): EAL.delete_asset(DST)
EAL.duplicate_asset(live.get_path_name().split('.')[0], DST)
sm=unreal.load_asset(DST)
G=unreal
try:
    dm=unreal.DynamicMesh()
    opts=unreal.GeometryScriptCopyMeshFromAssetOptions(); req=unreal.GeometryScriptMeshReadLOD()
    dm,res=unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(sm, dm, opts, req)
    L.append('copy %s tris %d'%(res, unreal.GeometryScript_MeshQueries.get_num_triangle_ids(dm)))
    parts=unreal.GeometryScript_MeshDecomposition.split_mesh_by_components(dm, [], None) if False else None
    # components
    comps=unreal.GeometryScript_MeshDecomposition.split_mesh_by_components(dm, unreal.Array(unreal.DynamicMesh), unreal.DynamicMeshPool())
    L.append('split ret %s'%type(comps))
    arr=comps[0] if isinstance(comps,tuple) else comps
    info=[]
    for i,c in enumerate(arr):
        n=unreal.GeometryScript_MeshQueries.get_num_triangle_ids(c)
        bb=unreal.GeometryScript_MeshQueries.get_mesh_bounding_box(c)
        info.append((n,i,bb))
    info.sort(key=lambda x:-x[0])
    L.append('components %d'%len(info))
    for n,i,bb in info[:15]: L.append('  comp %d tris %d box min %s max %s'%(i,n,bb.min,bb.max))
    big=info[0][0]
    # cleanup: keep only the main shell + weld + remove degenerates + recompute normals
    keep=[arr[i] for n,i,bb in info if n>=big*0.02]
    L.append('keeping %d comps (>=2%% of main)'%len(keep))
    out=unreal.DynamicMesh()
    for c in keep:
        unreal.GeometryScript_MeshBasicEditing.append_mesh(out, c, unreal.Transform())
    try: unreal.GeometryScript_MeshRepair.weld_mesh_edges(out, unreal.GeometryScriptWeldEdgesOptions())
    except Exception as e: L.append('weld err %s'%e)
    try: unreal.GeometryScript_MeshRepair.remove_unused_vertices(out)
    except Exception as e: L.append('unused err %s'%e)
    try: unreal.GeometryScript_MeshRepair.repair_mesh_degenerate_geometry(out, unreal.GeometryScriptDegenerateTriangleOptions())
    except Exception as e: L.append('degen err %s'%e)
    try: unreal.GeometryScript_Normals.recompute_normals(out, unreal.GeometryScriptCalculateNormalsOptions())
    except Exception as e: L.append('normals err %s'%e)
    L.append('clean tris %d'%unreal.GeometryScript_MeshQueries.get_num_triangle_ids(out))
    r=unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(out, sm, unreal.GeometryScriptCopyMeshToAssetOptions(), unreal.GeometryScriptMeshWriteLOD())
    L.append('write %s'%(r,))
    EAL.save_asset(DST, only_if_is_dirty=False)
except Exception as e:
    import traceback; L.append('ERR '+traceback.format_exc())
L.append('copy at '+DST)
open(r'C:/Users/hossa/Documents/agent-office/_bubclean_out.txt','w').write('\n'.join(L))
