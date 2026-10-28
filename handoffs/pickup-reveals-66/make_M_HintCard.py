# #66 pickup hint card: builds M_HintCard, the UI material the HUD draws behind the hint text (DrawMaterial).
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/pickup-reveals-66/make_M_HintCard.py"
# Parameters (set on a dynamic instance by the HUD every frame):
#   Age    seconds since the card started (frame draws on 0.8-1.6, shimmer 1.2-2.4; see DESIGN.md, offsets are relative)
#   Aspect card width / height (e.g. 520 / 190 = 2.74)
#   Fade   1 = fully shown, 0 = gone (the 0.5 s out)
import unreal

PATH, NAME = '/Game/CastleDefender/UI/Hints', 'M_HintCard'
FULL = PATH + '/' + NAME
MEL = unreal.MaterialEditingLibrary

if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    raise RuntimeError(FULL + ' already exists: delete or rename it first, the script never overwrites')

mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)

uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
params = {}
for i, (n, v) in enumerate([('Age', 10.0), ('Aspect', 2.74), ('Fade', 1.0)]):
    s = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -900, 120 + i * 110)
    s.set_editor_property('parameter_name', n); s.set_editor_property('default_value', v)
    params[n] = s

# Card space: x in [0, Aspect], y in [0, 1] (card height = 1). Frame draws from the top centre outwards both ways.
PRE = '''
float A = max(Aspect, 0.2);
float x = UV.x * A, y = UV.y;
float d = min(min(x, A - x), min(y, 1 - y));
float t;
if (d == y) t = x;
else if (d == A - x) t = A + y;
else if (d == 1 - y) t = A + 1 + (A - x);
else t = 2 * A + 1 + (1 - y);
float P = 2 * A + 2;
float s = abs(t - A * 0.5); s = min(s, P - s) / (P * 0.5);
float prog = saturate((Age - 0.8) / 0.8);
float drawn = s <= prog ? 1 : 0;
float head = saturate(1 - abs(s - prog) / 0.025) * (prog < 1 ? 1 : 0) * saturate(1 - abs(d - 0.041) / 0.035);
float aa = 0.006;
float outer = saturate(1 - abs(d - 0.022) / aa);
float inner = saturate(1 - abs(d - 0.060) / (aa * 0.8));
float corner = 0;
float2 cs[4] = { float2(0.06, 0.06), float2(A - 0.06, 0.06), float2(A - 0.06, 0.94), float2(0.06, 0.94) };
for (int k = 0; k < 4; k++)
{
    float2 q = abs(float2(x, y) - cs[k]);
    float dm = q.x + q.y;
    float lit = prog > 0.97 ? 1 : 0;
    corner = max(corner, saturate(1 - abs(dm - 0.035) / aa) * lit + saturate(1 - dm / 0.016) * lit);
}
float frame = max((outer + inner) * drawn, corner);
float sweep = saturate((Age - 1.2) / 1.2);
float band = saturate(1 - abs((x / A + (1 - y) * 0.25) - (sweep * 1.5 - 0.25)) / 0.08) * (sweep > 0 && sweep < 1 ? 1 : 0);
float fill = saturate((Age - 0.5) / 0.4);
float vign = 1 - 0.5 * pow(saturate(length(float2((x / A - 0.5) * 1.6, y - 0.5)) * 1.3), 2);
'''
NODES = [
    ('Color', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_EMISSIVE_COLOR, '''
float3 panel = float3(0.018, 0.016, 0.020) * vign + float3(0.010, 0.007, 0.003) * (1 - y);
float3 gold = float3(0.92, 0.66, 0.28);
float3 c = panel + gold * frame * 1.4 + float3(1.0, 0.92, 0.70) * head * 3.0;
c += float3(0.55, 0.42, 0.20) * band * 0.16;
return c;'''),
    ('Opacity', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_OPACITY, '''
float a = max(fill * 0.86, max(frame, head));
return saturate(a) * saturate(Fade);'''),
]
for i, (label, out_type, prop, body) in enumerate(NODES):
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, i * 240)
    c.set_editor_property('description', label)
    c.set_editor_property('output_type', out_type)
    c.set_editor_property('code', PRE + body)
    ins = []
    for n in ['UV', 'Age', 'Aspect']:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    if label == 'Opacity':
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', 'Fade'); ins.append(ci)
    c.set_editor_property('inputs', ins)
    MEL.connect_material_expressions(uv, '', c, 'UV')
    MEL.connect_material_expressions(params['Age'], '', c, 'Age')
    MEL.connect_material_expressions(params['Aspect'], '', c, 'Aspect')
    if label == 'Opacity':
        MEL.connect_material_expressions(params['Fade'], '', c, 'Fade')
    MEL.connect_material_property(c, '', prop)

MEL.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(FULL)
unreal.log('M_HintCard built: ' + FULL)
