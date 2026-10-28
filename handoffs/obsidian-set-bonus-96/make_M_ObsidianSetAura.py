# #96 Obsidian Sovereign set bonus: the set-complete overlay ("Sovereign's Ember"), one Overlay Material for every set piece.
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/obsidian-set-bonus-96/make_M_ObsidianSetAura.py"
# Creates (never overwrites):
#   vector ObsSet in the MPC that holds Armor (MPC_SkillTree), only if it is missing (R/G/B/A, see SPEC.md)
#   /Game/CastleDefender/VFX/ObsidianSet/M_ObsidianSetAura    additive, unlit; dark-gold embers crawling up the plates,
#                                                             gold rim pulse, a burst when the set completes, a flash on hit
# The overlay outputs black (= invisible when additive) unless ObsSet.R >= 0.5 (all set pieces worn).
import unreal

PATH = '/Game/CastleDefender/VFX/ObsidianSet'
NAME = 'M_ObsidianSetAura'
FULL = PATH + '/' + NAME
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

if EAL.does_asset_exist(FULL):
    EAL.delete_asset(FULL)   # master: removing the half-built asset from the failed first run (2026-10-28)

# The MPC that holds Armor (the Obsidian chest swap, vesna-obsidian-shop/README.md).
mpc = None
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection')):
    c = ad.get_asset()
    if any(str(v.get_editor_property('parameter_name')) == 'Armor' for v in c.get_editor_property('vector_parameters')):
        mpc = c; break
if mpc is None:
    raise RuntimeError('no MaterialParameterCollection with a vector parameter Armor found')
unreal.log('#96 Armor lives in ' + mpc.get_path_name())

vecs = list(mpc.get_editor_property('vector_parameters'))
if not any(str(v.get_editor_property('parameter_name')) == 'ObsSet' for v in vecs):
    p = unreal.CollectionVectorParameter()
    p.set_editor_property('parameter_name', 'ObsSet')
    p.set_editor_property('default_value', unreal.LinearColor(0, -100, -100, 0))   # off, burst/hit far in the past
    vecs.append(p)
    mpc.modify()
    mpc.set_editor_property('vector_parameters', vecs)
    EAL.save_asset(mpc.get_path_name())
    unreal.log('#96 added vector ObsSet to ' + mpc.get_path_name())

mat = tools.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property('two_sided', False)

# UE 5.3 python has no LocalPosition expression: object-relative world position (WorldPosition - ObjectPositionWS) instead
wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1300, -150)
op = MEL.create_material_expression(mat, unreal.MaterialExpressionObjectPositionWS, -1300, -50)
lp = MEL.create_material_expression(mat, unreal.MaterialExpressionSubtract, -1000, -100)
MEL.connect_material_expressions(wp, '', lp, 'A')
MEL.connect_material_expressions(op, '', lp, 'B')
now = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -1000, 0)
fres = MEL.create_material_expression(mat, unreal.MaterialExpressionFresnel, -1000, 100)
fres.set_editor_property('exponent', 3.0)
st = MEL.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, -1000, 220)
st.set_editor_property('collection', mpc)
st.set_editor_property('parameter_name', 'ObsSet')

def scalar(name, val, y):
    s = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1000, y)
    s.set_editor_property('parameter_name', name); s.set_editor_property('default_value', val)
    return s
params = {
    'EmberScale': scalar('EmberScale', 0.18, 340),   # ember cells per cm in local space (a plate is ~20-40 cm)
    'EmberRise': scalar('EmberRise', 6.0, 440),      # cm per second the embers crawl upward
    'RimPulseHz': scalar('RimPulseHz', 0.5, 540),
    'Intensity': scalar('Intensity', 6.0, 640),
}

# Embers: one bright point per 3D cell (local space, rising along Z), each with its own life cycle, so about half the cells
# glows at any time. Rim: a slow gold Fresnel pulse. Burst: 0.8 s white-gold flash from ObsSet.G (completion time).
# Hit: 0.25 s red-gold flare from ObsSet.B (last hit time). Times are game seconds, the same clock as the Time node.
CODE = '''
if (Set.r < 0.5) return float3(0, 0, 0);
float3 gold = float3(1.0, 0.62, 0.18);
float3 P = LP * EmberScale + float3(0, 0, -Now * EmberRise * EmberScale);
float3 ci = floor(P); float3 cf = frac(P);
float em = 0;
for (int ek = 0; ek < 8; ek++)   // own name: HLSL loop counters can leak into the enclosing scope
{
    float3 d = float3(ek & 1, (ek >> 1) & 1, (ek >> 2) & 1) - 0.5 + step(0.5, cf) - 0.5;
    float3 cell = ci + d;
    float3 h = frac(sin(float3(dot(cell, float3(127.1, 311.7, 74.7)), dot(cell, float3(269.5, 183.3, 246.1)),
                               dot(cell, float3(113.5, 271.9, 124.6)))) * 43758.5453);
    float3 q = cf - (d + h);
    float life = frac(Now * (0.25 + h.x * 0.35) + h.y);
    float on = step(0.45, h.z) * sin(life * 3.14159);
    em += on * pow(saturate(1 - length(q) / 0.32), 3);
}
float rim = Fres * (0.35 + 0.25 * sin(Now * 6.28318 * RimPulseHz));
float burst = saturate(1 - (Now - Set.g) / 0.8);
float hit = saturate(1 - (Now - Set.b) / 0.25);
float3 col = gold * (em * 2.5 + rim) + float3(1.0, 0.9, 0.7) * burst * burst * 0.9 * (0.2 + Fres)
           + float3(1.0, 0.35, 0.1) * hit * 0.6 * (0.2 + Fres);
return col * Intensity;
'''
c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -450, 200)
c.set_editor_property('description', 'ObsidianSetAura')
c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
c.set_editor_property('code', CODE)
names = ['LP', 'Now', 'Fres', 'Set'] + list(params)
ins = []
for n in names:
    ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
c.set_editor_property('inputs', ins)
MEL.connect_material_expressions(lp, '', c, 'LP')
MEL.connect_material_expressions(now, '', c, 'Now')
MEL.connect_material_expressions(fres, '', c, 'Fres')
MEL.connect_material_expressions(st, '', c, 'Set')
for n, s in params.items():
    MEL.connect_material_expressions(s, '', c, n)
MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(mat)
EAL.save_asset(FULL)
unreal.log('#96 M_ObsidianSetAura built in ' + PATH + ': set it as Overlay Material on every Obsidian set mesh component')
