# Anti-tiling (Master, 2026-10-31): tames the few stand-out (very saturated / orange) stones that make the castle stone
# repeat visibly. Inserted once before Base Color in every base material of the MI_Castle_* instances. Backup: <name>_PRETILE.
import unreal
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary; L = []
ar = unreal.AssetRegistryHelpers.get_asset_registry(); bases = set()
for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')):
    if str(a.asset_name).startswith('MI_Castle_'):
        b = unreal.load_asset(str(a.package_name)).get_base_material()
        if b and 'Landscape' not in b.get_name(): bases.add(b.get_path_name().split('.')[0])
CODE = ('float3 c = C; float l = dot(c, float3(0.2126, 0.7152, 0.0722));\n'
        'float s = (max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b))) / max(1e-4, max(c.r, max(c.g, c.b)));\n'
        'float t = saturate((s - Lo) / max(1e-4, Hi - Lo)) * Amount;\n'
        'float3 tame = lerp(c, l.xxx * float3(1.06, 1.0, 0.92), 0.7);\n'
        'tame *= lerp(1.0, (Avg / max(1e-4, l)), 0.35);\n'
        'return lerp(c, tame, t);')
for p in sorted(bases):
    m = unreal.load_asset(p); src = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
    if src is None: L.append('skip (no base color) ' + p); continue
    try:
        if src.get_class().get_name() == 'MaterialExpressionCustom' and src.get_editor_property('description') == 'AntiTile': L.append('already ' + p); continue
    except Exception: pass
    bk = p + '_PRETILE'
    if not EAL.does_asset_exist(bk): EAL.duplicate_asset(p, bk)
    cu = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -250, -600)
    cu.set_editor_property('description', 'AntiTile'); cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3); cu.set_editor_property('code', CODE)
    ins = []
    for n in ('C', 'Lo', 'Hi', 'Amount', 'Avg'):
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    cu.set_editor_property('inputs', ins)
    def sp(name, v, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, y); e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', v); return e
    ok = MEL.connect_material_expressions(src, '', cu, 'C')
    MEL.connect_material_expressions(sp('AntiTile_SatLo', 0.38, -700), '', cu, 'Lo'); MEL.connect_material_expressions(sp('AntiTile_SatHi', 0.62, -650), '', cu, 'Hi')
    MEL.connect_material_expressions(sp('AntiTile_Amount', 0.85, -600), '', cu, 'Amount'); MEL.connect_material_expressions(sp('AntiTile_AvgLum', 0.16, -550), '', cu, 'Avg')
    MEL.connect_material_property(cu, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(p); L.append('anti-tile on %s (input link %s)' % (p, ok))
open(r'C:\Users\hossa\Documents\agent-office\_antitile.txt', 'w').write('\n'.join(L)); print('ANTITILE', L)
