import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
for a in eas.get_all_level_actors():
    if a.get_class().get_name() in ('BP_CastleMainGate_C', 'BP_GateBreachLeaf_C'):
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if isinstance(c, (unreal.BoxComponent, unreal.SkeletalMeshComponent)):
                p = c.get_world_location(); r = c.get_world_rotation(); s = c.get_world_scale()
                ext = c.get_scaled_box_extent() if isinstance(c, unreal.BoxComponent) else None
                pa = c.get_editor_property('physics_asset_override') if isinstance(c, unreal.SkeletalMeshComponent) else None
                sk = c.get_editor_property('skeletal_mesh_asset') if isinstance(c, unreal.SkeletalMeshComponent) else None
                L.append('%s.%s pos=(%.0f,%.0f,%.0f) yaw=%.0f ext=%s profile=%s sk=%s anim=%s' % (a.get_actor_label(), c.get_name(), p.x, p.y, p.z, r.yaw, ext, c.get_collision_profile_name(), sk.get_name() if sk else None,
                    c.get_editor_property('animation_mode') if isinstance(c, unreal.SkeletalMeshComponent) else ''))
        L.append('  class ' + a.get_class().get_path_name())
open(r'C:\Users\hossa\Documents\agent-office\_gate_diag4.txt', 'w').write('\n'.join(L)); print('GD4')
