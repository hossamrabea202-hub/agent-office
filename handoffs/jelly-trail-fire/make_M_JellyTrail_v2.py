# #82 Jelly trail v2 ("real slime"): builds M_JellyTrail_v2, a drop-in replacement for M_JellyTrail on BP_JellyTrailManager's ISM_Trail.
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/jelly-trail-fire/make_M_JellyTrail_v2.py"
# Same per-instance custom data as v1, so the trail manager and the burning (#32) stay unchanged:
#   [0] BornT  [1] BurnT (-1 = never)  [2] Size (cm)  [3] Seed 0..1
# What changes: a procedural slime height field per piece (smeared lumpy body, satellite droplets, bubbles, stringy streaks)
# drives the normal, colour, gloss and a thin dithered edge (TAA blends it into see-through film). Fresh pieces spread out
# over 1.5 s, glisten, then dry (dull + darker) from 12 s before the old 20-25 s fade.
import unreal

PATH, NAME = '/Game/CastleDefender/VFX/JellyTrail', 'M_JellyTrail_v2'
FULL = PATH + '/' + NAME
MEL = unreal.MaterialEditingLibrary

if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    raise RuntimeError(FULL + ' already exists: delete or rename it first, the script never overwrites')

mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
mat.set_editor_property('used_with_instanced_static_meshes', True)
mat.set_editor_property('opacity_mask_clip_value', 0.5)
mat.set_editor_property('dithered_lod_transition', False)

uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
now = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -1100, 120)
data = {}
for i, n in enumerate(['BornT', 'BurnT', 'Size', 'Seed']):
    d = MEL.create_material_expression(mat, unreal.MaterialExpressionPerInstanceCustomData, -1100, 240 + i * 110)
    d.set_editor_property('data_index', i)   # no default_value in 5.3 Python; the trail manager writes all 4 floats
    data[n] = d

# Shared shape + state, pasted at the top of every Custom node (they can't share functions).
# H[0] = slime thickness at this pixel, H[1] / H[2] = one step along U / V (for the normal).
PRE = '''
float s1 = frac(Seed * 7.13 + 0.11), s2 = frac(Seed * 13.7 + 0.37), s3 = frac(Seed * 3.31 + 0.71);
float age = Now - BornT;
float settle = 0.72 + 0.28 * saturate(age / 1.5);
float E = 0.006;
float H[3];
float B0 = 0;
for (int ki = 0; ki < 3; ki++)   // not 'k': HLSL loop counters leak into the node scope
{
    float2 p = UV * 2 - 1 + (ki == 1 ? float2(E, 0) : (ki == 2 ? float2(0, E) : float2(0, 0)));
    float2 q = float2(p.x * (0.95 - 0.15 * s1), p.y * (1.10 + 0.20 * s2)) / settle;
    q.y += 0.08 * sin(q.x * 2.3 + s3 * 6.283);
    // metaballs: main body, front + back lobes, a side bulge, and droplets that merge or sit apart
    float2 c1 = q - float2(0.30 + 0.20 * s2, 0.40 * (s3 - 0.5));
    float2 c2 = q - float2(-0.28 - 0.20 * s3, 0.44 * (s1 - 0.5));
    float2 c3 = q - float2(0.30 * (s2 - 0.5), 0.36 * (s1 > 0.5 ? 1 : -1));
    float2 d1 = q - float2(0.70 + 0.05 * s2, 0.25 * (s3 - 0.5));
    float2 d2 = q - float2(-0.72 - 0.04 * s3, 0.30 * (s1 - 0.5));
    float2 d3 = q - float2(0.40 * (s2 - 0.5), 0.62 + 0.05 * s1);
    float fm = exp(-dot(q, q) / (0.30 + 0.06 * s1)) + 0.85 * exp(-dot(c1, c1) / (0.16 + 0.05 * s3))
             + (0.45 + 0.45 * s1) * exp(-dot(c2, c2) / (0.10 + 0.08 * s2)) + (0.30 + 0.40 * s3) * exp(-dot(c3, c3) / (0.05 + 0.05 * s2))
             + 0.90 * exp(-dot(d1, d1) / (0.006 + 0.006 * s1)) + 0.90 * exp(-dot(d2, d2) / (0.004 + 0.004 * s3))
             + 0.90 * step(0.45, s3) * exp(-dot(d3, d3) / 0.004);
    fm *= 1 + 0.10 * sin(q.x * 6 + s2 * 20) * sin(q.y * 7 + s3 * 20) + 0.04 * sin(q.x * 17 + q.y * 13 + s1 * 40);
    float h = saturate((fm - 0.45) / 0.55);
    float body = h * h * (3 - 2 * h);
    float lump = 0.10 * sin(q.x * 8.7 + s2 * 20) * sin(q.y * 10.3 + s3 * 20) + 0.05 * sin(q.x * 19 + q.y * 7 + s1 * 30);
    float streak = 0.015 * sin(q.y * 23 + 4.0 * sin(q.x * 2.1 + s1 * 9)) * sin(q.x * 5.3 + s2 * 11);
    float2 g = q * 6.5 + Seed * 31.0;
    float2 id = floor(g);
    float2 f = frac(g) - 0.5;
    float hb = frac(sin(dot(id, float2(127.1, 311.7))) * 43758.5453);
    float br = 0.10 + 0.22 * frac(hb * 17.3);
    float2 bo = (float2(frac(hb * 7.7), frac(hb * 3.9)) - 0.5) * 0.4;
    float bub = (hb > 0.72 ? 1 : 0) * sqrt(saturate(1 - length(f - bo) / br)) * step(0.35, body);
    if (ki == 0) B0 = bub;
    H[ki] = body > 0 ? body + (lump + streak) * body + 0.18 * bub : 0;
}
float T = H[0];
float inside = T > 0 ? 1 : 0;
float dry = saturate((age - 12.0) / 8.0);
float burning = BurnT >= 0 ? 1 : 0;
float since = Now - BurnT;
float bt = burning > 0 ? saturate(since / 3.0) : 0;
float burnt = (burning > 0 && since > 3.0) ? 1 : 0;
float charred = max(burnt, (burning > 0 && T < bt * 1.15) ? 1 : 0);
'''

NODES = [
    ('BaseColor', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_BASE_COLOR, '''
float3 edgeC = float3(0.016, 0.022, 0.008);
float3 midC = float3(0.040, 0.070, 0.008);
float3 coreC = float3(0.110, 0.160, 0.012);
float3 c = lerp(edgeC, midC, smoothstep(0.02, 0.35, T));
c = lerp(c, coreC, smoothstep(0.45, 0.95, T));
c = lerp(c, c * 1.8 + float3(0.02, 0.04, 0.0), B0 * 0.5);
c = lerp(c, float3(0.030, 0.040, 0.018), dry * 0.85);
return lerp(c, float3(0.025, 0.02, 0.018), charred);'''),
    ('Emissive', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_EMISSIVE_COLOR, '''
float3 glow = float3(0.015, 0.05, 0.004) * smoothstep(0.5, 1.0, T) * (1 - dry) * (1 - burning);
if (burning < 1 || burnt > 0) return glow;
float flick = 0.6 + 0.4 * sin(Now * 23 + Seed * 40 + T * 9) * sin(Now * 31 + UV.x * 15);
float3 col = lerp(float3(4.0, 0.9, 0.12), float3(6.0, 3.2, 0.6), saturate(T));
return col * (1 - bt) * (1 - charred * 0.7) * flick;'''),
    ('Roughness', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_ROUGHNESS, '''
if (charred > 0) return 0.92;
float wet = lerp(0.14, 0.03, smoothstep(0.05, 0.5, T));
return lerp(wet, 0.62, dry);'''),
    ('Specular', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_SPECULAR, '''
return lerp(0.75, 0.35, max(dry, charred));'''),
    ('Normal', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_NORMAL, '''
float k = 0.55 * (1 - dry * 0.7) * (1 - charred);
float3 n = float3(-(H[1] - H[0]) / E * k * 0.25, (H[2] - H[0]) / E * k * 0.25, 1);
return inside > 0 ? normalize(n) : float3(0, 0, 1);'''),
    ('OpacityMask', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_OPACITY_MASK, '''
float vis = burning > 0 ? 1 - saturate((since - 3.0) / 10.0) : 1 - saturate((age - 20.0) / 5.0);
float film = saturate(T / 0.14) * vis;
float n = frac(sin(dot(floor(UV * Size * 2.0), float2(12.9898, 78.233)) + frac(Now * 7.31) * 91.7) * 43758.5453);
return inside * (n < film ? 1 : 0);'''),
]

for i, (label, out_type, prop, body) in enumerate(NODES):
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -450, i * 220)
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
unreal.log('M_JellyTrail_v2 built: ' + FULL)
