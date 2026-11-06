import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
P = unreal.CollisionChannel.ECC_PAWN; IGN = unreal.CollisionResponseType.ECR_IGNORE
for a in eas.get_all_level_actors():
    cn = a.get_class().get_name()
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        if (cn == 'BP_CastleMainGate_C' and c.get_name().startswith('LeafCol')) or (cn == 'BP_GateBreachLeaf_C' and isinstance(c, unreal.SkeletalMeshComponent)):
            a.modify(); c.modify(); c.set_collision_response_to_channel(P, IGN); c.set_editor_property('can_ever_affect_navigation', False)
            L.append('%s.%s pawn=%s' % (a.get_actor_label(), c.get_name(), c.get_collision_response_to_channel(P)))
    if cn == 'BP_CastleMainGate_C':
        for cc in a.get_components_by_class(unreal.ChildActorComponent):
            ch = cc.get_editor_property('child_actor')
            if ch:
                for sk in ch.get_components_by_class(unreal.SkeletalMeshComponent):
                    ch.modify(); sk.modify(); sk.set_collision_response_to_channel(P, IGN); L.append('child %s pawn=%s' % (ch.get_actor_label(), sk.get_collision_response_to_channel(P)))
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w, 'RebuildNavigation')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_fixgate2.txt', 'w').write('\n'.join(L)); print('FG2')
