import unreal
MEL = unreal.MaterialEditingLibrary; L = []
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); seen = {}
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.MeshComponent):
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if m and 'Tentacle' in m.get_name() and 'Jelly' not in m.get_name() and 'Fog' not in m.get_name():
                k = m.get_path_name(); seen.setdefault(k, []).append('%s/%s %s sc=%s' % (a.get_actor_label(), c.get_name(), (c.static_mesh.get_name() if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh else c.get_class().get_name()), c.get_world_scale()))
for k, v in seen.items():
    L.append('MAT %s used %d: %s' % (k, len(v), ' ; '.join(v[:4])))
def nm(e):
    n = e.get_class().get_name().replace('MaterialExpression', '')
    for p in ('material_function', 'parameter_name', 'coordinate_index', 'u_tiling', 'v_tiling'):
        try:
            x = e.get_editor_property(p)
            if x not in (None, '', False): n += '[%s=%s]' % (p, x.get_name() if hasattr(x, 'get_name') else x)
        except Exception: pass
    return n
for k in seen:
    m = unreal.load_asset(k); b = m.get_base_material(); S = set()
    def walk(e, d):
        if e is None or e.get_path_name() in S or d > 7: return
        S.add(e.get_path_name()); L.append('  ' * d + nm(e))
        for i in MEL.get_inputs_for_material_expression(b, e): walk(i, d + 1)
    L.append('== BASE ' + b.get_path_name())
    walk(MEL.get_material_property_input_node(b, unreal.MaterialProperty.MP_BASE_COLOR), 1)
    if isinstance(m, unreal.MaterialInstance):
        L.append('  scalars: ' + ', '.join('%s=%.3g' % (n, MEL.get_material_instance_scalar_parameter_value(m, n)) for n in MEL.get_scalar_parameter_names(m)))
open(r'C:\Users\hossa\Documents\agent-office\_tent_diag.txt', 'w').write('\n'.join(L)); print('TD')
