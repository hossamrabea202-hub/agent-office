# Caustic light function: 3D projection (no vertical smear on tentacles / cliffs).
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 p = WP / Scale;
float c = 0;
for (int i = 0; i < 2; i++)
{
    float3 q = p * (1.0 + i * 0.73) + float3(T * 0.05 * (i + 1), -T * 0.04 * (i + 1), T * 0.03);
    float3 g = floor(q), f = frac(q); float md = 8.0;
    for (int z = -1; z <= 1; z++) for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++)
    {
        float3 o = float3(x, y, z);
        float3 h = frac(sin(float3(dot(g + o, float3(127.1, 311.7, 74.7)), dot(g + o, float3(269.5, 183.3, 246.1)), dot(g + o, float3(113.5, 271.9, 124.6)))) * 43758.5453);
        h = 0.5 + 0.5 * sin(T * 0.6 + 6.2831853 * h);
        md = min(md, length(o + h - f));
    }
    c += pow(saturate(1.0 - md * 1.15), 5.0);
}
return c * Int * (0.15 + 0.85 * saturate(Amt));
'''
try:
    r=unreal.AssetRegistryHelpers.get_asset_registry()
    paths=[str(x.package_name) for x in r.get_assets_by_path('/Game/CastleDefender/Gameplay/Realm/Dream',True) if str(x.asset_name).startswith('M_RealmCausticLF')]
    for p in paths:
        m=unreal.load_asset(p)
        n=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        if n and n.get_class().get_name()=='MaterialExpressionCustom':
            n.set_editor_property('code',CODE); MEL.recompile_material(m); EAL.save_asset(p); L.append('3D caustics: %s'%p)
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_tent_out.txt','w').write('\n'.join(L))
