# #32 Jelly trail fire, phase 1: builds M_JellyTrail, the per-instance material for BP_JellyTrailManager's ISM.
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/jelly-trail-fire/make_M_JellyTrail.py"
# Per-instance custom data (ISM NumCustomDataFloats = 4):  [0] BornT  [1] BurnT (-1 = never)  [2] Size (cm)  [3] Seed 0..1
# Times are world seconds (GetTimeSeconds in the Blueprint = the material Time node), same as M_SlashFX's Start.
import unreal

PATH, NAME = '/Game/CastleDefender/VFX/JellyTrail', 'M_JellyTrail'
FULL = PATH + '/' + NAME
MEL = unreal.MaterialEditingLibrary

if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    raise RuntimeError(FULL + ' already exists: delete or rename it first, the script never overwrites')

mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
mat.set_editor_property('used_with_instanced_static_meshes', True)
mat.set_editor_property('opacity_mask_clip_value', 0.5)

uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
now = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -900, 120)
data = {}
for i, n in enumerate(['BornT', 'BurnT', 'Size', 'Seed']):
    d = MEL.create_material_expression(mat, unreal.MaterialExpressionPerInstanceCustomData, -900, 240 + i * 110)
    d.set_editor_property('data_index', i)
    d.set_editor_property('default_value', -1.0 if n == 'BurnT' else 0.0)
    data[n] = d

# Shared shape + state, pasted at the top of every Custom node (they can't share functions).
PRE = '''
float2 p = UV * 2 - 1;
float r = length(p);
float a = atan2(p.y, p.x);
float edge = 0.78 + 0.10 * sin(a * 3 + Seed * 6.283) + 0.06 * sin(a * 7 + Seed * 17.0) + 0.04 * sin(a * 13 + Seed * 29.0);
float age = Now - BornT;
float burning = BurnT >= 0 ? 1 : 0;
float since = Now - BurnT;
float bt = burning > 0 ? saturate(since / 3.0) : 0;
float burnt = (burning > 0 && since > 3.0) ? 1 : 0;
float charred = max(burnt, (burning > 0 && r / edge > 1.0 - bt * 1.15) ? 1 : 0);
'''

NODES = [
    ('BaseColor', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_BASE_COLOR, '''
return lerp(float3(0.035, 0.11, 0.04), float3(0.025, 0.02, 0.018), charred);'''),
    ('Emissive', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_EMISSIVE_COLOR, '''
if (burning < 1 || burnt > 0) return float3(0, 0, 0);
float flick = 0.6 + 0.4 * sin(Now * 23 + Seed * 40 + r * 9) * sin(Now * 31 + a * 5);
float3 col = lerp(float3(4.0, 0.9, 0.12), float3(6.0, 3.2, 0.6), saturate(1 - r / edge));
return col * (1 - bt) * (1 - charred * 0.7) * flick;'''),
    ('Roughness', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_ROUGHNESS, '''
return charred > 0 ? 0.92 : 0.07;'''),
    ('OpacityMask', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_OPACITY_MASK, '''
float vis = burning > 0 ? 1 - saturate((since - 3.0) / 10.0) : 1 - saturate((age - 20.0) / 5.0);
float n = frac(sin(dot(floor(UV * Size * 0.5), float2(12.9898, 78.233))) * 43758.5453);
return (r < edge ? 1 : 0) * (n < vis ? 1 : 0);'''),
]

for i, (label, out_type, prop, body) in enumerate(NODES):
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, i * 220)
    c.set_editor_property('description', label)
    c.set_editor_property('output_type', out_type)
    c.set_editor_property('code', PRE + body)
    ins = []
    for n in ['UV', 'Now', 'BornT', 'BurnT', 'Size', 'Seed']:
        ci = unreal.CustomInput()
        ci.set_editor_property('input_name', n)
        ins.append(ci)
    c.set_editor_property('inputs', ins)
    MEL.connect_material_expressions(uv, '', c, 'UV')
    MEL.connect_material_expressions(now, '', c, 'Now')
    for n, d in data.items():
        MEL.connect_material_expressions(d, '', c, n)
    MEL.connect_material_property(c, '', prop)

MEL.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(FULL)
unreal.log('M_JellyTrail built: ' + FULL)
