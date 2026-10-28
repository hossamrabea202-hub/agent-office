# #85 Tower #9 round 1: import into an ISOLATED review level (never the castle map). Run after unzipping the release into
# C:\Users\hossa\Documents\agent-office\handoffs\circular-tower-9\review\Circular_Tower_09_Round1\
import unreal, traceback, os
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
SRC = r'C:\Users\hossa\Documents\agent-office\handoffs\circular-tower-9\review\Circular_Tower_09_Round1\Circular_Tower_09_Round1.fbx'
DST = '/Game/Review/Tower9_Round1'
LEVEL = '/Game/Review/Maps/Tower9_Round1_Review'
out = []
try:
    if not os.path.exists(SRC): raise RuntimeError('FBX missing: ' + SRC)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    fbx = unreal.FbxImportUI(); fbx.import_mesh = True; fbx.import_as_skeletal = False; fbx.import_materials = True; fbx.import_textures = False
    fbx.static_mesh_import_data.combine_meshes = True
    fbx.static_mesh_import_data.import_uniform_scale = 100.0   # metres -> cm (Blender export in metres)
    fbx.static_mesh_import_data.generate_lightmap_u_vs = False
    t = unreal.AssetImportTask(); t.filename = SRC; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True; t.options = fbx
    tools.import_asset_tasks([t])
    sm = unreal.load_asset(DST + '/Circular_Tower_09_Round1')
    if not sm: raise RuntimeError('import produced no mesh')
    bs = sm.get_editor_property('body_setup'); bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)  # README: no single convex hull
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    bb = sm.get_bounding_box(); out.append('mesh bounds min=%s max=%s' % (bb.min, bb.max))
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        les.new_level(LEVEL)
    else:
        les.load_level(LEVEL)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'Tower9_Round1']:
        a = eas.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0)); a.set_actor_label('Tower9_Round1')
        fl = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -5)); fl.set_actor_label('ReviewFloor')
        fl.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane')); fl.set_actor_scale3d(unreal.Vector(60, 60, 1))
        lt = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 2000)); lt.set_actor_rotation(unreal.Rotator(0, -50, 30), False)
        sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1000))
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -900, 100))
    les.save_current_level()
    out.append('review level ready: ' + LEVEL + ' (Play from here: walk the +X/+Y portals at 6.8 m, the switchback stair, roof at 10.7 m)')
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
