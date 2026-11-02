# Read-only: what does a camera ray hit? py trace_ue.py camX camY camZ  tx ty tz [tx ty tz ...]
import sys, unreal
a = [float(x) for x in sys.argv[1:]]
cam = unreal.Vector(*a[:3])
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for i in range(3, len(a), 3):
    t = unreal.Vector(*a[i:i + 3])
    end = cam + (t - cam) * 3.0
    hit = unreal.SystemLibrary.line_trace_single(world, cam, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                                                 unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        print('miss', t); continue
    h = hit.to_tuple()
    actor, comp, loc = h[9], h[10], h[4]
    print('ray to', [round(v) for v in a[i:i + 3]], '-> hit', actor.get_actor_label() if actor else None,
          comp.get_editor_property('static_mesh').get_name() if comp and hasattr(comp, 'static_mesh') else comp,
          actor.get_folder_path() if actor else '', 'at', [round(loc.x), round(loc.y), round(loc.z)])
