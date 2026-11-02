# Read-only (i5): for each material given, what feeds BaseColor / Metallic / Roughness / Normal / AO: node class and
# constants / texture names, plus MI parameters and the whole parent chain. Writes mat_graph.json.
import json, os, sys, unreal
MEL = unreal.MaterialEditingLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
names = sys.argv[1:]
idx = {}
for cls in ('Material', 'MaterialInstanceConstant'):
    for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', cls)):
        idx.setdefault(str(a.asset_name), str(a.package_name))


def node_desc(n, depth=0):
    if n is None:
        return None
    d = {'cls': n.get_class().get_name()}
    for prop in ('parameter_name', 'r', 'constant', 'default_value', 'texture'):
        try:
            v = n.get_editor_property(prop)
            d[prop] = v.get_path_name().split('.')[-1] if hasattr(v, 'get_path_name') else (str(v) if not isinstance(v, (int, float, str)) else v)
        except Exception:
            pass
    if depth < 3:
        try:
            ins = MEL.get_inputs_for_material_expression(None, n) if False else []
        except Exception:
            ins = []
    return d


out = {}
for nm in names:
    pk = idx.get(nm)
    if not pk:
        out[nm] = 'NOT FOUND'; continue
    m = unreal.load_asset(pk)
    d = {'path': pk, 'class': m.get_class().get_name(), 'chain': [], 'params': {}}
    base = m
    while isinstance(base, unreal.MaterialInstance):
        if isinstance(base, unreal.MaterialInstanceConstant):
            for n in MEL.get_scalar_parameter_names(base):
                d['params'].setdefault(str(n), round(MEL.get_material_instance_scalar_parameter_value(base, n), 4))
            for n in MEL.get_vector_parameter_names(base):
                c = MEL.get_material_instance_vector_parameter_value(base, n); d['params'].setdefault(str(n), [round(c.r, 3), round(c.g, 3), round(c.b, 3)])
            for n in MEL.get_texture_parameter_names(base):
                t = MEL.get_material_instance_texture_parameter_value(base, n); d['params'].setdefault(str(n), t.get_name() if t else None)
        base = base.get_editor_property('parent'); d['chain'].append(base.get_path_name() if base else None)
    if isinstance(base, unreal.Material):
        for prop in ('MP_BASE_COLOR', 'MP_METALLIC', 'MP_ROUGHNESS', 'MP_NORMAL', 'MP_AMBIENT_OCCLUSION', 'MP_SPECULAR'):
            n = MEL.get_material_property_input_node(base, getattr(unreal.MaterialProperty, prop))
            d[prop] = node_desc(n)
        d['expr_count'] = MEL.get_num_material_expressions(base)
        d['textures'] = [t.get_name() for t in MEL.get_used_textures(base)]
        d['scalars_in_graph'] = [str(n) for n in MEL.get_scalar_parameter_names(base)]
        d['vectors_in_graph'] = [str(n) for n in MEL.get_vector_parameter_names(base)]
    out[nm] = d
json.dump(out, open(os.path.join(os.path.dirname(__file__), 'mat_graph.json'), 'w'), indent=1)
print('graphs:', len(out))
