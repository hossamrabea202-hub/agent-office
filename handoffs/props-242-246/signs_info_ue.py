# #246: report the placed signs (bounds, scale, materials) and select them. Read-only apart from selection.
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
s = [a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith('Props242_246_')]
log = []
for a in s:
    o, e = a.get_actor_bounds(False); c = a.static_mesh_component
    mats = [m.get_name() if m else None for m in c.get_materials()]
    log.append('%s loc %s scale %s bounds o(%.0f,%.0f,%.0f) e(%.0f,%.0f,%.0f) hidden %s mats %s' % (
        a.get_actor_label(), a.get_actor_location(), a.get_actor_scale3d(), o.x, o.y, o.z, e.x, e.y, e.z, a.is_hidden_ed(), mats))
EAS.set_selected_level_actors([a for a in s if 'Sign_Smith' in a.get_actor_label()])
out = '\n'.join(log); unreal.log(out); print(out)
