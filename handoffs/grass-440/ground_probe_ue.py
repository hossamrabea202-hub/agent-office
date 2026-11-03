# #440 (i5): what is the ground under the meadow? Trace down at a few points, print actor / component / material.
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for x, y in ((-2000, 2600), (-3500, 600), (-1500, 4200), (-5000, 1000), (6500, 1700)):
    hits = unreal.SystemLibrary.line_trace_multi(w, unreal.Vector(x, y, 5000), unreal.Vector(x, y, -3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    for h in hits[:3]:
        t = h.to_tuple(); a, c = t[9], t[10]
        mat = c.get_material(0) if c and hasattr(c, 'get_material') else None
        print('PROBE', (x, y), 'z %.0f' % t[4].z, a.get_actor_label() if a else None, a.get_class().get_name() if a else None, c.get_name() if c else None, mat.get_path_name().split('/')[-1] if mat else None)
