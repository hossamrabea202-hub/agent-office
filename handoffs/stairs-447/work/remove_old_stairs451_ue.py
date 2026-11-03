# #301 (owner, 2026-11-03): "if you imported new stairs in the same position and dimension of old stairs, remove old stairs
# and its traces". For every flight that now uses SM_StairBaked451_*: delete the HIDDEN old stair pieces (folders
# Stairs_Old_279 / Stairs_Old_447, or label Stair*/Step*/Tread*/StepCap) whose bounds lie inside that flight's footprint
# (+15 cm), plus the old steps' edge-grime cards (Blend_Contact_* with MI_EdgeGrime_StairContact) there: they were laid on
# the old kit treads and float 6.5 cm over the new ones. Other visible actors, decals, gameplay actors and the invisible
# StairRamps (walking helpers) are never touched.
# Every deleted actor is written to removed_old_stairs451.json (class, label, folder, mesh, materials, transform) so it
# can be rebuilt with --restore.
#   py remove_old_stairs451_ue.py --dry-run | --apply | --restore
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/stairs-447/work/'
A = sys.argv[1:]; REC = H + 'removed_old_stairs451.json'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = EAS.get_all_level_actors()
if '--restore' in A:
    for r in json.load(open(REC)):
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*r['loc']), unreal.Rotator(*r['rot']))
        a.set_actor_scale3d(unreal.Vector(*r['scale'])); a.set_actor_label(r['label']); a.set_folder_path(r['folder'])
        c = a.static_mesh_component; c.set_static_mesh(unreal.load_asset(r['mesh']))
        for i, m in enumerate(r['mats']): c.set_material(i, unreal.load_asset(m) if m else None)
        a.set_actor_hidden_in_game(r['hidden']); c.set_visibility(not r['hidden'])
        c.set_collision_enabled(getattr(unreal.CollisionEnabled, r['coll']))
    print('restored', len(json.load(open(REC)))); raise SystemExit
new = []
for a in acts:
    if a.get_class().get_name() != 'StaticMeshActor': continue
    m = a.static_mesh_component.get_editor_property('static_mesh')
    if m and m.get_name().startswith('SM_StairBaked451_'):
        o, e, _ = unreal.SystemLibrary.get_component_bounds(a.static_mesh_component); new.append((a, o, e))
print('flights with the new mesh:', [a.get_actor_label() for a, _, _ in new])
OLD = ('stairs_old', 'stair', 'step', 'tread', 'stepcap', 'riser')
hits = []
for a in acts:
    if a.get_class().get_name() != 'StaticMeshActor' or any(a == n[0] for n in new): continue
    c = a.static_mesh_component
    if not c.get_editor_property('static_mesh'): continue
    folder = str(a.get_folder_path()).lower(); lab = a.get_actor_label().lower()
    hidden = (not c.is_visible()) or a.is_hidden_ed() or c.get_editor_property('hidden_in_game')
    mats = [x.get_name() for x in c.get_materials() if x]
    old_card = lab.startswith('blend_contact_') and 'MI_EdgeGrime_StairContact' in mats      # the old steps' edge grime: floats over the new treads
    if not old_card and (not hidden or not any(k in folder or k in lab for k in OLD)): continue
    o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
    for na, no, ne in new:
        if all(abs(getattr(o, i) - getattr(no, i)) + (0.0 if old_card else getattr(e, i)) <= getattr(ne, i) + 15.0 for i in ('x', 'y', 'z')):   # cards: centre inside
            hits.append((a, na.get_actor_label())); break
print('%s: %d hidden old pieces inside the new flights' % ('APPLY' if '--apply' in A else 'DRY RUN', len(hits)))
for a, f in hits[:40]: print('   %-34s folder %-28s mesh %-26s in %s' % (a.get_actor_label(), a.get_folder_path(), a.static_mesh_component.get_editor_property('static_mesh').get_name(), f))
if '--apply' in A:
    rec = json.load(open(REC)) if os.path.exists(REC) else []
    for a, f in hits:
        c = a.static_mesh_component; l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
        rec.append({'label': a.get_actor_label(), 'folder': str(a.get_folder_path()), 'mesh': c.get_editor_property('static_mesh').get_path_name(),
                    'mats': [x.get_path_name() if x else '' for x in c.get_materials()], 'loc': [l.x, l.y, l.z], 'rot': [r.roll, r.pitch, r.yaw],
                    'scale': [s.x, s.y, s.z], 'hidden': not c.is_visible(), 'coll': c.get_collision_enabled().name, 'flight': f})
        EAS.destroy_actor(a)
    json.dump(rec, open(REC, 'w'), indent=0)
    print('deleted %d (record %s)' % (len(hits), REC))
