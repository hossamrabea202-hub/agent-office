import unreal
MEL = unreal.MaterialEditingLibrary; L = []
ar = unreal.AssetRegistryHelpers.get_asset_registry(); bases = {}
for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')):
    if str(a.asset_name).startswith('MI_Castle_'):
        mi = unreal.load_asset(str(a.package_name)); b = mi.get_base_material()
        tex = {str(n): (MEL.get_material_instance_texture_parameter_value(mi, n).get_name() if MEL.get_material_instance_texture_parameter_value(mi, n) else None) for n in MEL.get_texture_parameter_names(mi)}
        L.append('%s base=%s BaseColor=%s' % (a.asset_name, b.get_path_name() if b else None, tex.get('BaseColor')))
        if b: bases[b.get_path_name()] = 1
for b in bases:
    m = unreal.load_asset(b); n = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
    L.append('BASE %s basecolor-node=%s' % (b, n.get_class().get_name() if n else None))
open(r'C:\Users\hossa\Documents\agent-office\_tile_diag.txt', 'w').write('\n'.join(L)); print('TILED')
