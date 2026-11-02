import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = {}
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.MeshComponent):
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if isinstance(m, unreal.MaterialInstanceDynamic): m = m.get_editor_property('parent')
            if m and m.get_name() == 'M_Metal_Steel' and c.is_visible():
                k = '%s/%s slot%d' % (a.get_class().get_name(), c.get_name(), i); n[k] = n.get(k, 0) + 1
print('visible M_Metal_Steel users:', n)
