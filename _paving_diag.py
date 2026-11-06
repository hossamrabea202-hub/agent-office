import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if not m: continue
        for i in range(c.get_num_materials()):
            mt = c.get_material(i)
            if mt and 'Paving' in mt.get_name() and m.get_name() not in ('Cube', 'SM_WalkSlab'):
                L.append('%s | %s | slot %d %s | %s | loc %s' % (a.get_actor_label(), m.get_name(), i, c.get_material_slot_names()[i] if i < len(c.get_material_slot_names()) else '?', mt.get_name(), a.get_actor_location()))
open(r'C:\Users\hossa\Documents\agent-office\_paving_diag.txt', 'w').write('\n'.join(L) or 'none'); print('PD', len(L))
