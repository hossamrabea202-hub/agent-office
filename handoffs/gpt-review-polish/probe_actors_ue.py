# #451 read-only probe: print label, folder, mesh, materials, location, scale, hidden flags of actors whose label matches.
#   py probe_actors_ue.py <substring> [<substring> ...]
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pats = [s.lower() for s in sys.argv[1:]]
for a in sorted(EAS.get_all_level_actors(), key=lambda x: x.get_actor_label()):
    lab = a.get_actor_label()
    if not any(p in lab.lower() for p in pats): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        l = c.get_world_location(); s = c.get_world_scale(); r = c.get_world_rotation()
        print('%-24s %-28s %-22s mats=%s loc=(%.1f,%.1f,%.1f) rot=(%.1f,%.1f,%.1f) scale=(%.3f,%.3f,%.3f) vis=%s hidGame=%s' % (
            lab, str(a.get_folder_path()), m.get_name() if m else None, [x.get_name() if x else None for x in c.get_materials()],
            l.x, l.y, l.z, r.roll, r.pitch, r.yaw, s.x, s.y, s.z, c.is_visible(), a.is_hidden_ed()))
