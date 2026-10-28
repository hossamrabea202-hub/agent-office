# Trail look test in Simulate. STEP = 'clear' (editor world), 'sim' (start simulate), 'place' (3 pieces in the game world + camera), 'end'.
import unreal, traceback
STEP = open(r'C:\Unreal Backups\Castle Defender\Tools\master\trail_sim_step.txt').read().strip()
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = ['step ' + STEP]
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    cls = unreal.load_class(None, '/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager.BP_JellyTrailManager_C')
    def ism_in(w):
        mgr = unreal.GameplayStatics.get_all_actors_of_class(w, cls)[0]
        return mgr.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    if STEP == 'clear':
        i = ism_in(ues.get_editor_world()); i.clear_instances(); out.append('editor instances=%d' % i.get_instance_count())
    elif STEP == 'sim':
        les.editor_play_simulate(); out.append('simulate requested')
    elif STEP == 'place':
        w = ues.get_game_world(); ism = ism_in(w)
        base = unreal.Vector(1000, 900, 0)
        h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(base.x, base.y, 300), unreal.Vector(base.x, base.y, -300), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
        t = h.to_tuple(); fz = t[4].z if t[0] else 2.6
        now = unreal.GameplayStatics.get_time_seconds(w)
        specs = [(0, now, -1.0, 0.33), (1, now - 8.0, -1.0, 0.71), (2, now - 14.0, -1.0, 0.52), (3, now - 2.0, now - 1.0, 0.9)]   # fresh, 8 s, 14 s (drying), burning
        for k, born, burn, seed in specs:
            xf = unreal.Transform(unreal.Vector(base.x + (k - 1.5) * 110, base.y, fz + 1.0), unreal.Rotator(0, 0, 0), unreal.Vector(1.0, 1.0, 1.0))
            i = ism.add_instance(xf, True)
            for j, v in enumerate((born, burn, 70.0, seed)): ism.set_custom_data_value(i, j, v, True)
        ism.mark_render_state_dirty()
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(base.x, base.y - 300, fz + 260), unreal.Rotator(0, -45, 90))
        out.append('placed 4 at t=%.1f floor %.1f mat=%s instances=%d' % (now, fz, ism.get_material(0).get_name(), ism.get_instance_count()))
    elif STEP == 'end':
        les.editor_request_end_play(); out.append('end play requested')
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
