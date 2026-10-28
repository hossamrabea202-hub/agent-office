import unreal, traceback, math
OUT = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
L = []
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = ues.get_game_world()
    acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
    tent = [a for a in acts if 'TentacleVitals' in a.get_name()]
    for t in tent[:3]:
        loc = t.get_actor_location()
        L.append('== %s loc %s bounds %s' % (t.get_name()[-12:], loc, t.get_actor_bounds(False)))
        for d in (300, 600, 900, 1200, 1600, 2200):
            row = []
            for ang in (0, 90, 180, 270):
                dx = d * math.cos(math.radians(ang)); dy = d * math.sin(math.radians(ang))
                p = loc + unreal.Vector(dx, dy, 0)
                res = unreal.SystemLibrary.line_trace_single(w, p + unreal.Vector(0,0,3000), p + unreal.Vector(0,0,-4000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [t], unreal.DrawDebugTrace.NONE, True)
                if res:
                    tp = res.to_tuple(); row.append('%d:z=%.0f %s' % (ang, tp[4].z - loc.z, tp[9].get_name()[-10:] if tp[9] else None))
                else:
                    row.append('%d:miss' % ang)
            L.append('d=%d ' % d + ' | '.join(row))
except Exception:
    L.append(traceback.format_exc())
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
