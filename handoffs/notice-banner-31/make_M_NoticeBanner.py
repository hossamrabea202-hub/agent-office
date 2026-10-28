# #31 notification box: builds M_NoticeBanner, the UI material the HUD draws behind a game message (DrawMaterial).
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/notice-banner-31/make_M_NoticeBanner.py"
# A dark blackened-steel plate with a gold trim that rolls out sideways from its centre between two gold rods,
# holds, then rolls back. Parameters (set on a dynamic instance by the HUD every frame):
#   Roll    0 = rolled up (only the two rods, touching), 1 = fully open
#   Aspect  banner width / height (e.g. 760 / 64 = 11.9)
#   Fade    1 = shown, 0 = gone
#   Tier    0 = normal (gold), 1 = important (deep red plate, brighter gold)
import unreal

PATH, NAME = '/Game/CastleDefender/UI/Notices', 'M_NoticeBanner'
FULL = PATH + '/' + NAME
MEL = unreal.MaterialEditingLibrary

if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(unreal.load_asset(FULL))
    unreal.EditorAssetLibrary.delete_asset(FULL)   # master: replacing the first build whose HLSL failed ('half' is a reserved HLSL type), 2026-10-28

mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)

uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
params = {}
for i, (n, v) in enumerate([('Roll', 1.0), ('Aspect', 11.9), ('Fade', 1.0), ('Tier', 0.0)]):
    s = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -900, 120 + i * 110)
    s.set_editor_property('parameter_name', n); s.set_editor_property('default_value', v)
    params[n] = s

# Banner space: x in [0, A], y in [0, 1]. The open plate spans |x - A/2| <= hw; the rods sit at its two ends.
CODE = '''
float A = max(Aspect, 1.0);
float x = UV.x * A, y = UV.y;
float cx = A * 0.5;
float rodR = 0.5;                                   // rod radius = hw the banner height
float hw = lerp(rodR * 0.9, cx - rodR, saturate(Roll));
float dx = abs(x - cx);
float aa = 0.02;
// plate: between the rods, a little inset top and bottom (the cloth/plate sits inside the rod ends)
float plate = saturate((hw - dx) / aa) * saturate((y - 0.10) / aa) * saturate((0.90 - y) / aa);
// gold trim lines along top and bottom of the plate, and a thin inner line
float trimO = saturate(1 - abs(y - 0.155) / 0.032) + saturate(1 - abs(y - 0.845) / 0.032);
float trimI = saturate(1 - abs(y - 0.215) / 0.014) + saturate(1 - abs(y - 0.785) / 0.014);
// plate surface: blackened steel with a soft vertical gradient and a faint brushed grain
float grain = frac(sin(floor(x * 140.0) * 12.9898) * 43758.5453) * 0.05;
float grad = 1.0 - abs(y - 0.5) * 0.9;
float3 steel = lerp(float3(0.030, 0.031, 0.036), float3(0.075, 0.020, 0.018), saturate(Tier)) * (0.75 + 0.5 * grad) + grain * 0.02;
float3 gold = lerp(float3(0.78, 0.55, 0.24), float3(1.0, 0.74, 0.34), saturate(Tier));
float3 col = steel;
col = lerp(col, gold, saturate(trimO) * plate);
col = lerp(col, gold * 0.7, saturate(trimI) * plate);
// rods: vertical gold cylinders at both plate ends, shaded as round (lighter in the middle), with end caps
float rodX = abs(dx - hw);
float rodW = 0.13;
float rod = saturate((rodW - rodX) / aa) * saturate((y - 0.02) / aa) * saturate((0.98 - y) / aa);
float shade = sqrt(saturate(1 - (rodX / rodW) * (rodX / rodW)));
float caps = saturate(1 - abs(abs(y - 0.5) - 0.44) / 0.04);
float3 rodC = gold * (0.35 + 0.75 * shade) * (1 - 0.35 * caps);
col = lerp(col, rodC, rod);
// shadow the rods throw onto the plate edge, so it reads as rolled
float sh = saturate(1 - (hw - dx) / 0.35) * plate * (1 - rod);
col *= 1 - 0.45 * sh;
float alpha = max(plate * 0.94, rod) * saturate(Fade);
return float4(col, alpha);
'''
c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -450, 120)
c.set_editor_property('description', 'NoticeBanner')
c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
c.set_editor_property('code', CODE)
names = ['UV'] + list(params)
ins = []
for n in names:
    ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
c.set_editor_property('inputs', ins)
MEL.connect_material_expressions(uv, '', c, 'UV')
for n, s in params.items():
    MEL.connect_material_expressions(s, '', c, n)
rgb = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 60)
rgb.set_editor_property('r', True); rgb.set_editor_property('g', True); rgb.set_editor_property('b', True); rgb.set_editor_property('a', False)
a = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 200)
for ch in ('r', 'g', 'b'): a.set_editor_property(ch, False)
a.set_editor_property('a', True)
MEL.connect_material_expressions(c, '', rgb, '')
MEL.connect_material_expressions(c, '', a, '')
MEL.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(a, '', unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(FULL)
unreal.log('#31 M_NoticeBanner built in ' + PATH)
