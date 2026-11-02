# Read-only (2026-11-02, i5, stair study): dump every castle stone piece in the level.
# One row per static mesh component (or per ISM instance) whose material lives in a Castle material folder or whose
# mesh/actor name looks like a stair/step/walk piece: actor label, folder, mesh + its local bounds, world transform,
# world bounds and materials. Writes JSON next to this script, saves nothing.
import json, os, unreal
OUT = os.path.join(os.path.dirname(__file__), 'castle_pieces.json')
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
KEYS = ('stair', 'step', 'walk', 'slab', 'landing', 'tower09_floor', 'bevel')


def v(x):
    return [round(x.x, 2), round(x.y, 2), round(x.z, 2)]


def rot(r):
    return [round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)]


rows, mesh_bounds = [], {}
for a in EAS.get_all_level_actors():
    label = a.get_actor_label()
    folder = str(a.get_folder_path())
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        if not sm:
            continue
        mats = [m.get_path_name() if m else '' for m in (c.get_material(i) for i in range(c.get_num_materials()))]
        text = (label + ' ' + sm.get_name() + ' ' + ' '.join(mats)).lower()
        if '/castle/' not in text and not any(k in text for k in KEYS):
            continue
        mp = sm.get_path_name()
        if mp not in mesh_bounds:
            b = sm.get_bounding_box()
            mesh_bounds[mp] = {'min': v(b.min), 'max': v(b.max), 'tris': sm.get_num_triangles(0),
                               'nanite': bool(sm.get_editor_property('nanite_settings').enabled)}
        base = {'actor': label, 'folder': folder, 'class': a.get_class().get_name(), 'comp': c.get_name(),
                'mesh': mp, 'mats': mats, 'visible': c.is_visible(), 'hidden_game': a.is_hidden_ed()}
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                rows.append(dict(base, inst=i, loc=v(t.translation), rot=rot(t.rotation.rotator()), scale=v(t.scale3d)))
        else:
            t = c.get_world_transform()
            o, e = c.get_local_bounds()
            wb = c.bounds if hasattr(c, 'bounds') else None
            rows.append(dict(base, loc=v(t.translation), rot=rot(t.rotation.rotator()), scale=v(t.scale3d)))

json.dump({'meshes': mesh_bounds, 'pieces': rows}, open(OUT, 'w'), indent=0)
print('castle pieces: %d rows, %d meshes -> %s' % (len(rows), len(mesh_bounds), OUT))
