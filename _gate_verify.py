import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
for a in eas.get_all_level_actors():
    if a.get_class().get_name() in ('BP_CastleMainGate_C', 'BP_GateBreachLeaf_C'):
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
                L.append('%s.%s coll=%s pawn=%s' % (a.get_actor_label(), c.get_name(), c.get_collision_enabled(), c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)))
open(r'C:\Users\hossa\Documents\agent-office\_gate_verify.txt', 'w').write('\n'.join(L)); print('GV')
