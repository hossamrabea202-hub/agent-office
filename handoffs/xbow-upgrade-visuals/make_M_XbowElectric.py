# #77 crossbow LV4 "electric field": an Overlay Material (UE 5.1+ MeshComponent.OverlayMaterial) for both crossbows.
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/xbow-upgrade-visuals/make_M_XbowElectric.py"
# Creates (never overwrites):
#   /Game/CastleDefender/VFX/XbowUpgrade/M_XbowElectric           additive, unlit; blue-white arcs crawling over the mesh
#   /Game/CastleDefender/VFX/XbowUpgrade/MI_XbowElectric_Noble     Channel 0 = XbowUp.R (Noble level)
#   /Game/CastleDefender/VFX/XbowUpgrade/MI_XbowElectric_Sovereign Channel 1 = XbowUp.G (Golden Sovereign level)
# The arcs only show at level >= MaxLevel (default 4); below that the overlay outputs black (= invisible when additive).
import unreal

PATH = '/Game/CastleDefender/VFX/XbowUpgrade'
NAME = 'M_XbowElectric'
FULL = PATH + '/' + NAME
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

if EAL.does_asset_exist(FULL):
    raise RuntimeError(FULL + ' already exists: delete or rename it first, the script never overwrites')

# Find the MPC that holds XbowUp (#52 put it next to Armor/Gear in the skill-tree collection).
mpc = None
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection')):
    c = ad.get_asset()
    if any(str(v.parameter_name) == 'XbowUp' for v in c.get_editor_property('vector_parameters')):
        mpc = c; break
if mpc is None:
    raise RuntimeError('no MaterialParameterCollection with a vector parameter XbowUp found')
unreal.log('#77 XbowUp lives in ' + mpc.get_path_name())

mat = tools.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property('two_sided', False)

lp = MEL.create_material_expression(mat, unreal.MaterialExpressionLocalPosition, -1000, -100)
now = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -1000, 0)
fres = MEL.create_material_expression(mat, unreal.MaterialExpressionFresnel, -1000, 100)
fres.set_editor_property('exponent', 2.5)
up = MEL.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, -1000, 220)
up.set_editor_property('collection', mpc)
up.set_editor_property('parameter_name', 'XbowUp')

def scalar(name, val, y):
    s = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1000, y)
    s.set_editor_property('parameter_name', name); s.set_editor_property('default_value', val)
    return s
params = {
    'Channel': scalar('Channel', 0.0, 340),         # 0 = XbowUp.R (Noble), 1 = XbowUp.G (Sovereign)
    'MaxLevel': scalar('MaxLevel', 4.0, 440),
    'ArcScale': scalar('ArcScale', 0.09, 540),     # arcs per cm in local space (crossbow ~80 cm wide)
    'ArcWidth': scalar('ArcWidth', 0.022, 640),
    'Intensity': scalar('Intensity', 14.0, 740),
}

# Two layers of 3D value noise in local space; an arc is where a noise layer crosses 0.5 (thin iso-lines),
# the field jumps a few times per second (crackle) while the whole pattern crawls along the limbs.
CODE = '''
float lvl = Channel < 0.5 ? Up.r : Up.g;
if (lvl < MaxLevel - 0.01) return float3(0, 0, 0);
float3 P = LP * ArcScale;
float step_t = floor(Now * 11.0);
float total = 0;
for (int L = 0; L < 2; L++)
{
    float3 o = float3(Now * (0.6 + L * 0.35), step_t * 1.37 + L * 5.1, Now * 0.25);
    float n = 0, amp = 0.55, fq = 1.0 + L * 0.9;
    for (int O = 0; O < 3; O++)
    {
        float3 x = P * fq + o + O * 17.3;
        float3 i = floor(x); float3 f = frac(x); f = f * f * (3 - 2 * f);
        float v = 0;
        for (int c = 0; c < 8; c++)
        {
            float3 d = float3(c & 1, (c >> 1) & 1, (c >> 2) & 1);
            float h = frac(sin(dot(i + d, float3(127.1, 311.7, 74.7))) * 43758.5453);
            float3 w = lerp(1 - f, f, d);
            v += h * w.x * w.y * w.z;
        }
        n += (v - 0.5) * amp; amp *= 0.5; fq *= 2.3;
    }
    float w2 = ArcWidth * (L == 0 ? 1.0 : 0.6);
    float core = pow(saturate(1 - abs(n) / w2), 3);
    float halo = saturate(1 - abs(n) / (w2 * 5)) * 0.07;
    // sparsity: a slow noise picks where arcs live this crackle step (~1/3 of the surface)
    float3 gx = P * 0.45 + float3(0, step_t * 0.73, L * 9.1);
    float3 gi = floor(gx); float3 gf = frac(gx); gf = gf * gf * (3 - 2 * gf);
    float gv = 0;
    for (int c = 0; c < 8; c++)
    {
        float3 d = float3(c & 1, (c >> 1) & 1, (c >> 2) & 1);
        float3 w = lerp(1 - gf, gf, d);
        gv += frac(sin(dot(gi + d, float3(269.5, 183.3, 246.1))) * 43758.5453) * w.x * w.y * w.z;
    }
    total += (core + halo) * saturate((gv - 0.52) * 6) * (L == 0 ? 1.0 : 0.55);
}
float flicker = 0.55 + 0.45 * frac(sin(step_t * 12.9898) * 43758.5453);
float rim = 0.30 + 0.70 * Fres;
float3 col = lerp(float3(0.35, 0.65, 1.0), float3(0.95, 0.97, 1.0), saturate(total - 0.5));
return col * total * flicker * rim * Intensity;
'''
c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -450, 200)
c.set_editor_property('description', 'XbowElectric')
c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
c.set_editor_property('code', CODE)
names = ['LP', 'Now', 'Fres', 'Up'] + list(params)
ins = []
for n in names:
    ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
c.set_editor_property('inputs', ins)
MEL.connect_material_expressions(lp, '', c, 'LP')
MEL.connect_material_expressions(now, '', c, 'Now')
MEL.connect_material_expressions(fres, '', c, 'Fres')
MEL.connect_material_expressions(up, '', c, 'Up')
for n, s in params.items():
    MEL.connect_material_expressions(s, '', c, n)
MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(mat)
EAL.save_asset(FULL)

for suffix, ch in (('Noble', 0.0), ('Sovereign', 1.0)):
    mi_name = 'MI_XbowElectric_' + suffix
    if EAL.does_asset_exist(PATH + '/' + mi_name):
        unreal.log_warning(mi_name + ' exists, left as is'); continue
    mi = tools.create_asset(mi_name, PATH, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, mat)
    MEL.set_material_instance_scalar_parameter_value(mi, 'Channel', ch)
    EAL.save_asset(PATH + '/' + mi_name)
unreal.log('#77 M_XbowElectric + 2 instances built in ' + PATH)
