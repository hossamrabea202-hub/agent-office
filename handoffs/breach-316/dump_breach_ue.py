# #316 breach redo (adjustedfilm, 2026-10-31): READ-ONLY dump of every breach spot in the level and of the gate breach parts,
# so the new breach can reuse what is there. Run in the editor with ThirdPersonMap open (not in Play):
#   py "<repo>/handoffs/breach-316/dump_breach_ue.py"
# Writes <repo>/handoffs/exports/adjustedfilm/breach-316/breach_dump.json, then commit + push it. Changes nothing.
import os, json
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'exports', 'adjustedfilm', 'breach-316', 'breach_dump.json'))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
v = lambda x: [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
r = lambda x: [round(x.pitch, 2), round(x.yaw, 2), round(x.roll, 2)]
rows = []
for a in EAS.get_all_level_actors():
    lab, cls = a.get_actor_label(), a.get_class().get_name()
    if not any(k in (lab + cls).lower() for k in ('breach', 'gatebreach', 'gatelever', 'castlegate')): continue
    comps = []
    for c in a.get_components_by_class(unreal.SceneComponent):
        d = {'name': c.get_name(), 'class': c.get_class().get_name(), 'rel_loc': v(c.get_editor_property('relative_location')),
             'rel_rot': r(c.get_editor_property('relative_rotation')), 'rel_scale': v(c.get_editor_property('relative_scale3d')),
             'world_loc': v(c.get_world_location()), 'visible': c.is_visible(), 'hidden_in_game': c.get_editor_property('hidden_in_game'),
             'tags': [str(t) for t in c.get_editor_property('component_tags')]}
        if isinstance(c, unreal.PrimitiveComponent):
            d['simulate_physics'] = c.is_simulating_physics(); d['collision'] = str(c.get_collision_profile_name())
        if isinstance(c, unreal.StaticMeshComponent):
            sm = c.get_editor_property('static_mesh'); d['mesh'] = sm.get_path_name() if sm else None
            d['materials'] = [m.get_path_name() if m else None for m in c.get_materials()]
            if sm: bb = sm.get_bounding_box(); d['mesh_size'] = v(bb.max - bb.min)
        if isinstance(c, unreal.SkeletalMeshComponent):
            sk = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'get_skeletal_mesh_asset') else None
            d['skel'] = sk.get_path_name() if sk else None
        comps.append(d)
    rows.append({'label': lab, 'class': a.get_class().get_path_name(), 'loc': v(a.get_actor_location()), 'rot': r(a.get_actor_rotation()), 'components': comps})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rows, open(OUT, 'w'), indent=1)
print('[breach dump] %d actors -> %s' % (len(rows), OUT))
