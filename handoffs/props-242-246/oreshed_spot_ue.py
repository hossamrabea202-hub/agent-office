# #242: find a clear ground spot for SM_OreShed beside Mine_01 (i5 core, 2026-11-01). UE 5.8 Python.
#   py ".../oreshed_spot_ue.py"            read-only: actors within 18 m of Mine_01 + ground Z at 4 candidate spots
#   py ".../oreshed_spot_ue.py" --apply L  place the shed at candidate L (R/L/RB/LB), tag Props242_246
import sys, math, unreal
A = sys.argv[1:]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
acts = EAS.get_all_level_actors()
mine = [a for a in acts if a.get_actor_label() == 'Mine_01'][0]
m = mine.get_actor_location(); yaw = mine.get_actor_rotation().yaw
f = mine.get_actor_forward_vector(); r = mine.get_actor_right_vector()
log = ['Mine_01 at (%.0f, %.0f, %.0f) yaw %.0f' % (m.x, m.y, m.z, yaw)]
for a in acts:
    d = (a.get_actor_location() - m).length()
    if 1 < d < 1800 and not a.get_actor_label().startswith(('Landscape', 'Sky', 'Post')):
        l = a.get_actor_location(); log.append('  near %-36s d %5.0f (%.0f, %.0f, %.0f)' % (a.get_actor_label()[:36], d, l.x, l.y, l.z))


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, m.z + 3000), unreal.Vector(x, y, m.z - 3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [mine], unreal.DrawDebugTrace.NONE, True)
    if not hit: return None
    t = hit.to_tuple(); return t[4].z, t[9].get_actor_label() if t[9] else '?'


spots = {'R': m + r * 850 + f * 150, 'L': m - r * 850 + f * 150, 'RB': m + r * 850 - f * 300, 'LB': m - r * 850 - f * 300}
for k, p in spots.items():
    g = ground(p.x, p.y)
    log.append('  spot %-2s (%.0f, %.0f) ground %s' % (k, p.x, p.y, g))
if '--apply' in A:
    k = A[A.index('--apply') + 1]; p = spots[k]; g = ground(p.x, p.y)
    for a in acts:
        if 'Props242_246' in [str(t) for t in a.tags] and a.get_actor_label() == 'Props242_246_OreShed': EAS.destroy_actor(a)
    sh = EAS.spawn_actor_from_object(unreal.load_asset('/Game/CastleDefender/Props/Mine/OreShed/SM_OreShed'),
                                     unreal.Vector(p.x, p.y, g[0] - 5), unreal.Rotator(0, 0, yaw))
    sh.set_actor_label('Props242_246_OreShed'); sh.tags = [unreal.Name('Props242_246')]
    o, e = sh.get_actor_bounds(False); log.append('placed OreShed at %s yaw %.0f, bounds %s' % (sh.get_actor_location(), yaw, e))
out = '\n'.join(log); unreal.log(out); print(out)
