import sys, unreal
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() == sys.argv[1]:
        o, e = a.get_actor_bounds(False); print('WHERE', [round(v) for v in o.to_tuple()], [round(v) for v in e.to_tuple()])
