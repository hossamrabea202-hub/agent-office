# #246: list big static meshes near the forge, Vesna and the well fire (walls/posts to hang signs on). Read-only. UE 5.8.
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = EAS.get_all_level_actors()
log = []
big = []
for a in acts:
    if isinstance(a, unreal.StaticMeshActor):
        o, e = a.get_actor_bounds(False)
        if max(e.x, e.y) > 60 and e.z > 80: big.append((a, o, e))
for an in [a for a in acts if a.get_actor_label() in ('Forge_01', 'NPCFill_Vesna', 'Castle_WellBase')]:
    c = an.get_actor_location()
    log.append('== %s (%.0f, %.0f, %.0f) yaw %.0f' % (an.get_actor_label(), c.x, c.y, c.z, an.get_actor_rotation().yaw))
    near = sorted(((o - c).length(), id(a), a, o, e) for a, o, e in big if a is not an and (o - c).length() < 1500)
    for d, _, a, o, e in near[:18]:
        sm = a.static_mesh_component.static_mesh.get_name() if a.static_mesh_component.static_mesh else '?'
        log.append('   %-30s %-28s d%4.0f o(%.0f,%.0f,%.0f) e(%.0f,%.0f,%.0f) yaw %.0f' % (a.get_actor_label()[:30], sm[:28], d, o.x, o.y, o.z, e.x, e.y, e.z, a.get_actor_rotation().yaw))
out = '\n'.join(log); unreal.log(out); print(out)
