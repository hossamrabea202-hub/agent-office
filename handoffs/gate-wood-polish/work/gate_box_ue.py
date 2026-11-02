# Read-only (i5): every actor whose bounds touch the main gate opening, with class, mesh components and materials
# (runtime MIDs reported with their parent). Writes gate_actors.json.
import json, os, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LO, HI = (-700, 1350, -50), (300, 2150, 900)
out = []
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if o.x + e.x < LO[0] or o.x - e.x > HI[0] or o.y + e.y < LO[1] or o.y - e.y > HI[1] or o.z + e.z < LO[2] or o.z - e.z > HI[2]:
        continue
    if e.x > 3000 or e.y > 3000:
        continue
    comps = []
    for c in a.get_components_by_class(unreal.MeshComponent):
        mesh = None
        if isinstance(c, unreal.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
        elif isinstance(c, unreal.SkeletalMeshComponent):
            mesh = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'skeletal_mesh_asset') else None
        mats = []
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if isinstance(m, unreal.MaterialInstanceDynamic):
                m = m.get_editor_property('parent')
            mats.append(m.get_path_name() if m else None)
        comps.append({'comp': c.get_name(), 'type': c.get_class().get_name(), 'mesh': mesh.get_path_name() if mesh else None,
                      'mats': mats, 'visible': c.is_visible(), 'movable': str(c.get_editor_property('mobility'))})
    if comps:
        out.append({'actor': a.get_actor_label(), 'class': a.get_class().get_path_name(), 'folder': str(a.get_folder_path()),
                    'loc': [round(o.x), round(o.y), round(o.z)], 'ext': [round(e.x), round(e.y), round(e.z)], 'comps': comps})
json.dump(out, open(os.path.join(os.path.dirname(__file__), 'gate_actors.json'), 'w'), indent=0)
print('gate actors:', len(out))
