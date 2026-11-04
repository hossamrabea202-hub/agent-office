# #501 owner's order (Alien, 11-04): REMOVE the SiegeKit barricades from the level (293 actors, 13.5 M triangles, no Nanite).
# Before deleting, every removed actor's mesh, transform, folder, label and materials go to Saved/removed_siegekit_<time>.json, so --restore can put them back.
#   py remove_siegekit_ue.py               dry run: lists what would go (count per mesh, folders); changes nothing
#   py remove_siegekit_ue.py --hide-keep-collision   RECOMMENDED: invisible in game, no shadows, collision kept (they are the map edges)
#   py remove_siegekit_ue.py --apply       writes the JSON, deletes the actors (map edges open!). Then SAVE the level.
#   py remove_siegekit_ue.py --restore <json>   spawns them again from the JSON (same mesh, transform, materials, folder, label)
# Editor idle, not in Play. CHECK FIRST: if any barricade blocks a path or a map edge, zombies or the player can walk there after removal.
import json, sys, time, unreal
A = sys.argv[1:]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
KIT = '/Game/CastleDefender/Environment/Boundaries/SiegeKit/'

if '--restore' in A:
    rows = json.load(open(A[A.index('--restore') + 1], encoding='utf-8')); n = 0
    for r in rows:
        m = unreal.load_asset(r['mesh'])
        a = EAS.spawn_actor_from_object(m, unreal.Vector(*r['loc']), unreal.Rotator(*r['rot']))
        if not a: continue
        a.set_actor_scale3d(unreal.Vector(*r['scale'])); a.set_actor_label(r['label']); a.set_folder_path(unreal.Name(r['folder']))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        for i, mp in enumerate(r['mats']):
            if mp: c.set_material(i, unreal.load_asset(mp))
        n += 1
    print('restored %d of %d barricades. Save the level.' % (n, len(rows))); raise SystemExit

hits, per_mesh, folders = [], {}, {}
for a in EAS.get_all_level_actors():
    cs = a.get_components_by_class(unreal.StaticMeshComponent)
    ms = [c.get_editor_property('static_mesh') for c in cs]
    if cs and all(m and m.get_path_name().startswith(KIT) for m in ms):
        hits.append(a); k = ms[0].get_name(); per_mesh[k] = per_mesh.get(k, 0) + 1
        f = str(a.get_folder_path()); folders[f] = folders.get(f, 0) + 1
blocking = sum(1 for a in hits if a.get_component_by_class(unreal.StaticMeshComponent).get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION)
print('SiegeKit actors: %d (with collision: %d)' % (len(hits), blocking)); print('  per mesh:', per_mesh); print('  folders:', folders)
if '--hide-keep-collision' in A:
    # 292 of the 293 block the map edges (Boundaries_29 A/C/E) and the realm: this mode removes all their drawing cost but keeps them as invisible walls.
    for a in hits:
        a.set_actor_hidden_in_game(True)
        c = a.get_component_by_class(unreal.StaticMeshComponent); c.set_editor_property('cast_shadow', False)
        a.tags = list(a.tags) + [unreal.Name('Hidden501')]
    print('hid %d SiegeKit actors in game (collision kept, shadows off). SAVE the level. Undo: select tag Hidden501, untick Actor Hidden In Game, Cast Shadow back on.' % len(hits))
    raise SystemExit
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
rows = []
for a in hits:
    c = a.get_component_by_class(unreal.StaticMeshComponent); t = a.get_actor_transform(); r = t.rotation.rotator()
    rows.append({'label': a.get_actor_label(), 'folder': str(a.get_folder_path()), 'mesh': c.get_editor_property('static_mesh').get_path_name(),
                 'loc': [t.translation.x, t.translation.y, t.translation.z], 'rot': [r.pitch, r.yaw, r.roll], 'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z],
                 'mats': [(c.get_material(i).get_path_name() if c.get_material(i) else '') for i in range(c.get_num_materials())]})
out = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'removed_siegekit_%s.json' % time.strftime('%m%d_%H%M%S')
json.dump(rows, open(out, 'w', encoding='utf-8'), indent=1); print('saved restore list', out)
gone = sum(1 for a in hits if EAS.destroy_actor(a))
print('removed %d SiegeKit actors. SAVE the level. Undo: py remove_siegekit_ue.py --restore "%s"' % (gone, out))
