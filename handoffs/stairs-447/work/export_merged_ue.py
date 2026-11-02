# Read-only (i5, stair study): export the merged castle-stone meshes that overlap stair F2/F3 to FBX.
import os, unreal
OUT = os.path.join(os.path.dirname(__file__), 'refs')
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
done = set()
for a in EAS.get_all_level_actors():
    if not a.get_actor_label().startswith('CastleStones_0_0_'):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        if not sm or sm.get_name() in done:
            continue
        done.add(sm.get_name())
        t = unreal.AssetExportTask()
        t.object = sm; t.filename = os.path.join(OUT, sm.get_name() + '.fbx'); t.automated = True; t.prompt = False
        t.exporter = unreal.StaticMeshExporterFBX()
        l = a.get_actor_location(); s = a.get_actor_scale3d(); r = a.get_actor_rotation()
        print(a.get_actor_label(), sm.get_path_name(), unreal.Exporter.run_asset_export_task(t), 'loc', l, 'scale', s, 'rot', r, 'tris', sm.get_num_triangles(0))
