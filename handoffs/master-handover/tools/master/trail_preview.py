# Drops 3 temporary trail instances on the floor in front of the editor camera (custom data: fresh / 8 s old / burning) and frames them. Nothing saved. MODE='clear' removes them.
import unreal, traceback, math
MODE = 'show'
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); w = ues.get_editor_world()
    cls = unreal.load_class(None, '/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager.BP_JellyTrailManager_C')
    mgr = unreal.GameplayStatics.get_all_actors_of_class(w, cls)[0]
    ism = mgr.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    if MODE == 'clear':
        ism.clear_instances(); out.append('cleared, instances=%d' % ism.get_instance_count())
    else:
        base = unreal.Vector(1000, 900, 0)   # courtyard spot used earlier
        h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(base.x, base.y, 300), unreal.Vector(base.x, base.y, -300), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
        t = h.to_tuple(); fz = t[4].z if t[0] else 2.6
        now = unreal.GameplayStatics.get_time_seconds(w)
        ism.clear_instances()
        specs = [(0, now, -1.0, 0.33), (1, now - 8.0, -1.0, 0.71), (2, now - 2.0, now - 1.0, 0.52)]   # fresh, 8 s old, burning 1 s
        for k, born, burn, seed in specs:
            xf = unreal.Transform(unreal.Vector(base.x + (k - 1) * 110, base.y, fz + 1.0), unreal.Rotator(0, 0, 0), unreal.Vector(1.0, 1.0, 1.0))
            i = ism.add_instance(xf, True)
            for j, v in enumerate((born, burn, 70.0, seed)): ism.set_custom_data_value(i, j, v, True)
        ism.mark_render_state_dirty()
        ues.set_level_viewport_camera_info(unreal.Vector(base.x, base.y - 260, fz + 300), unreal.Rotator(0, -50, 90))
        out.append('placed 3 test pieces at %s floor z %.1f, time %.1f; material %s' % (base, fz, now, ism.get_material(0).get_name()))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
