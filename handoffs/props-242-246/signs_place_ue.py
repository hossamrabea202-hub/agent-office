# #246: hang the 3 signs as blade signs on real walls (i5 core, 2026-11-01). UE 5.8 Python.
#   py ".../signs_place_ue.py"          dry run: prints the wall hits
#   py ".../signs_place_ue.py" --apply  places them (tag Props242_246; place_242_246_ue.py --remove --apply undoes)
# Decision (Alien didn't answer in 10 min, chat line 237): smith on the bailey wall behind Forge_01, tavern on the wall
# south of the well fire, shop on the north curtain behind Vesna. The sign meshes were imported at 1/100 (metres read as
# cm): scale x100 -> 95 x 75 cm board. Pivot (x=0) is the bracket end, so X points out of the wall along the hit normal.
import sys, math, unreal
APPLY = '--apply' in sys.argv
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
TAG = 'Props242_246'
# key: (start x, y, trace dir x, y)
SPOTS = {'Sign_Smith': (4440, 3100, 0, 1), 'Sign_Tavern': (3900, 2200, 0, -1), 'Sign_Shop': (905, 3250, 0, 1)}   # shop clear of the wall torch at x 700; smith 1.2 m east of the forge roof edge (x 4321)
acts = EAS.get_all_level_actors()
pawns = [a for a in acts if isinstance(a, unreal.Pawn) or a.get_actor_label().startswith(TAG)]
log = ['#246 signs' + ('' if APPLY else ' (DRY RUN)')]


def trace(a, b):
    h = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, pawns,
                                               unreal.DrawDebugTrace.NONE, True)
    if not h: return None
    t = h.to_tuple(); return t[4], t[7], (t[9].get_actor_label() if t[9] else '?')   # impact point, impact normal, actor


for k, (x, y, dx, dy) in SPOTS.items():
    g = trace(unreal.Vector(x, y, 400), unreal.Vector(x, y, -1500))       # start below the wall walk slabs (z ~680)
    gz = g[0].z if g else 0.0
    z = gz + 290
    w = trace(unreal.Vector(x, y, z), unreal.Vector(x + dx * 500, y + dy * 500, z))
    if not w: log.append('%s: no wall within 5 m (ground %.0f on %s)' % (k, gz, g and g[2])); continue
    p, n, who = w
    yaw = math.degrees(math.atan2(n.y, n.x))
    loc = p + n * 2.0
    log.append('%s: ground %.0f (%s), wall %s at (%.0f, %.0f, %.0f) normal (%.2f, %.2f, %.2f) -> yaw %.0f'
               % (k, gz, g and g[2], who, loc.x, loc.y, loc.z, n.x, n.y, n.z, yaw))
    if APPLY:
        for a in acts:
            if a.get_actor_label() == '%s_%s' % (TAG, k): EAS.destroy_actor(a)
        s = EAS.spawn_actor_from_object(unreal.load_asset('/Game/CastleDefender/Props/Town/Signs/SM_' + k), loc, unreal.Rotator(0, 0, yaw))
        s.set_actor_scale3d(unreal.Vector(100, 100, 100))
        s.set_actor_label('%s_%s' % (TAG, k)); s.tags = [unreal.Name(TAG)]
f = [a for a in acts if a.get_actor_label() == 'Forge_01'][0]; fo, fe = f.get_actor_bounds(False)
log.append('Forge_01 bounds o (%.0f, %.0f, %.0f) e (%.0f, %.0f, %.0f)' % (fo.x, fo.y, fo.z, fe.x, fe.y, fe.z))
out = '\n'.join(log); unreal.log(out); print(out)
