# Safe copy of the owner's remodeled bubble mesh. Read-only on the original.
import unreal, time, os
EAL=unreal.EditorAssetLibrary; E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
bub=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Realm_Bubble_Owner'][0]
sm=bub.static_mesh_component.static_mesh
src=sm.get_path_name().split('.')[0]
stamp=time.strftime('%Y%m%d_%H%M')
dst='/Game/CastleDefender/Gameplay/Realm/_Backup/%s_%s'%(sm.get_name(),stamp)
EAL.duplicate_asset(src,dst); EAL.save_asset(dst, only_if_is_dirty=False)
d=r'C:/Users/hossa/Documents/BubbleBackups'; os.makedirs(d,exist_ok=True)
fbx=d+'/%s_%s.fbx'%(sm.get_name(),stamp)
t=unreal.AssetExportTask(); t.object=sm; t.filename=fbx; t.automated=True; t.prompt=False; t.replace_identical=True
t.exporter=unreal.StaticMeshExporterFBX()
ok=unreal.Exporter.run_asset_export_task(t)
open(r'C:/Users/hossa/Documents/agent-office/_bb_out.txt','w').write('src %s\ncopy %s exists=%s\nfbx %s ok=%s size=%s\nverts %s'%(src,dst,EAL.does_asset_exist(dst),fbx,ok,os.path.getsize(fbx) if os.path.exists(fbx) else 0, unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_number_verts(sm,0)))
