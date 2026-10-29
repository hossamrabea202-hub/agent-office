# #82 Jelly trail v3 ("Netflix slime"), from hossam gmail (Claude) 2026-10-29. Drop-in for ISM_Trail on BP_JellyTrailManager.
# Same per-instance custom data as v1/v2:  [0] BornT  [1] BurnT (-1 = never)  [2] Size (cm)  [3] Seed 0..1
# v3 vs v2: real geometry (dense grid mesh SM_SlimeGrid raised by World Position Offset from the same slime height field),
# translucent liquid (Surface forward shading, refraction), thickness-based absorption colour (thin = clear olive film,
# thick = deep murky brown-green), near-mirror gloss + fake sky glint for overcast light, soaked dark halo on the ground.
import unreal
PATH, NAME = '/Game/CastleDefender/VFX/JellyTrail', 'M_JellyTrail_v3'
FULL = PATH + '/' + NAME
MEL = unreal.MaterialEditingLibrary
if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    unreal.EditorAssetLibrary.delete_asset(FULL)
mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
mat.set_editor_property('opacity_mask_clip_value', 0.5)
mat.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
mat.set_editor_property('used_with_instanced_static_meshes', True)
mat.set_editor_property('two_sided', True)
try: mat.set_editor_property('refraction_method', unreal.RefractionMode.RM_INDEX_OF_REFRACTION)
except Exception: pass
uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
now = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -1100, 120)
data = {}
for i, n in enumerate(['BornT', 'BurnT', 'Size', 'Seed']):
    d = MEL.create_material_expression(mat, unreal.MaterialExpressionPerInstanceCustomData, -1100, 240 + i * 110)
    d.set_editor_property('data_index', i)
    data[n] = d
PRE = r'''
float s1 = frac(Seed * 7.13 + 0.11), s2 = frac(Seed * 13.7 + 0.37), s3 = frac(Seed * 3.31 + 0.71);
float age = Now - BornT;
float settle = 0.72 + 0.28 * saturate(age / 1.5);
float E = 0.006;
float H[3];
float B0 = 0;
float FM0 = 0;
for (int ki = 0; ki < 3; ki++)   // not 'k': HLSL loop counters leak into the node scope
{
    float2 p = UV * 2 - 1 + (ki == 1 ? float2(E, 0) : (ki == 2 ? float2(0, E) : float2(0, 0)));
    float2 q = p / settle;
    float ang = atan2(q.y, q.x);
    float rr = length(q);
    // soft dome with an irregular rim: thick centre, thin rounded edge; pieces are laid with overlap so they merge into one smear
    float edge = 0.80 + 0.05 * sin(ang * 2 + s1 * 6.283) + 0.04 * sin(ang * 5 + s2 * 6.283) + 0.025 * sin(ang * 9 + s3 * 6.283);
    float dd = rr / edge;
    float dome = pow(saturate(1 - dd * dd), 0.6);
    float fm = dd < 1 ? 0.45 + 0.55 * dome : 0.45 - 1.2 * (dd - 1);   // past the rim fm falls 0.45 -> 0.26 within ~16% = soaked halo band
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
    if (ki == 0) { B0 = bub; FM0 = fm; }
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

float halo = (1 - inside) * smoothstep(0.26, 0.44, FM0);          // soaked ground just outside the body
float vis = burning > 0 ? 1 - saturate((since - 3.0) / 10.0) : 1 - saturate((age - 20.0) / 5.0);
float3 nT = float3(-(H[1] - H[0]) / E * 0.07, (H[2] - H[0]) / E * 0.07, 1);
nT = inside > 0 ? normalize(nT) : float3(0, 0, 1);
'''
NODES = [
    ('BaseColor', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_BASE_COLOR, r'''
float th = smoothstep(0.0, 0.9, T);
float3 thin = float3(0.034, 0.038, 0.012);       // murky olive-brown film
float3 deep = float3(0.014, 0.026, 0.005);       // thick body: deep murky green-brown
float3 c = lerp(thin, deep, th);
c = lerp(c, c * 1.6 + float3(0.012, 0.016, 0.0), B0 * 0.6);   // bubbles a touch lighter
c = lerp(c, float3(0.022, 0.020, 0.012), dry * 0.8);
c = lerp(c, float3(0.010, 0.009, 0.006), halo);
return lerp(c, float3(0.025, 0.02, 0.018), charred);'''),
    ('Emissive', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_EMISSIVE_COLOR, r'''
float wet = inside * (1 - dry) * (1 - charred);
float3 Ls = normalize(float3(0.35, 0.22, 1.0));
float glint = pow(saturate(dot(nT, Ls)), 220) * 0.30 + pow(saturate(dot(nT, normalize(float3(-0.4, 0.5, 1.0)))), 140) * 0.06;
float rim = pow(saturate(1 - nT.z), 2.0) * 0.015;
float3 sky = float3(0.42, 0.46, 0.34) * (glint + rim) * wet * smoothstep(0.03, 0.25, T);
float3 bub = float3(0.05, 0.06, 0.03) * B0 * pow(saturate(dot(nT, Ls)), 60) * wet;
float3 sss = float3(0.0015, 0.005, 0.0004) * smoothstep(0.35, 1.0, T) * wet;   // light scattered inside thick goo
float3 base = sky * 0.7 + bub + sss;
if (burning < 1 || burnt > 0) return base;
float flick = 0.6 + 0.4 * sin(Now * 23 + Seed * 40 + T * 9) * sin(Now * 31 + UV.x * 15);
float3 col = lerp(float3(4.0, 0.9, 0.12), float3(6.0, 3.2, 0.6), saturate(T));
return col * (1 - bt) * (1 - charred * 0.7) * flick;'''),
    ('Roughness', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_ROUGHNESS, r'''
if (charred > 0) return 0.92;
float r = lerp(0.26, 0.11, smoothstep(0.03, 0.4, T));
r = lerp(r, 0.30, halo);
return lerp(r, 0.55, dry);'''),
    ('Specular', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_SPECULAR, r'''
return lerp(0.35, 0.15, max(dry, charred));'''),
    ('Normal', unreal.CustomMaterialOutputType.CMOT_FLOAT3, unreal.MaterialProperty.MP_NORMAL, r'''
float k = (1 - dry * 0.6) * (1 - charred);
return normalize(lerp(float3(0, 0, 1), nT, k));'''),
    ('Opacity', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_OPACITY_MASK, r'''
float body = inside * lerp(0.30, 0.94, smoothstep(0.0, 0.6, T));   // thin edges see-through, thick body dense
float o = max(body, halo * 0.38);
o = lerp(o, o * 0.85, dry);
if (charred > 0) o = max(o, inside * 0.95);
o *= vis;
// masked + temporal dither: TAA turns this into soft see-through edges
float dn = frac(sin(dot(floor(UV * Size * 2.0), float2(12.9898, 78.233)) + frac(Now * 7.31) * 91.7) * 43758.5453);
return dn < o ? 1 : 0;'''),
    ('Refraction', unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.MaterialProperty.MP_REFRACTION, r'''
return 1.0 + 0.18 * inside * smoothstep(0.0, 0.5, T) * (1 - dry);'''),
    ('WPO', unreal.CustomMaterialOutputType.CMOT_FLOAT1, None, r'''
// thickness in cm, in the piece's local Z (local Z scale is 1 -> cm). Outside the body sink 0.4 cm so the halo hugs the ground.
return inside > 0 ? (0.5 + T * Size * 0.032) : -0.4;'''),
]
nodes = {}
for i, (label, out_type, prop, body) in enumerate(NODES):
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -450, i * 220)
    c.set_editor_property('description', label)
    c.set_editor_property('output_type', out_type)
    c.set_editor_property('code', PRE + body)
    ins = []
    for n in ['UV', 'Now', 'BornT', 'BurnT', 'Size', 'Seed']:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    c.set_editor_property('inputs', ins)
    MEL.connect_material_expressions(uv, '', c, 'UV')
    MEL.connect_material_expressions(now, '', c, 'Now')
    for n, d in data.items():
        MEL.connect_material_expressions(d, '', c, n)
    if prop is not None:
        MEL.connect_material_property(c, '', prop)
    nodes[label] = c
# WPO: (0,0,h) in local space -> world
mv = MEL.create_material_expression(mat, unreal.MaterialExpressionAppendVector, -500, 600)
z0 = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant2Vector, -700, 600)
MEL.connect_material_expressions(z0, '', mv, 'A'); MEL.connect_material_expressions(nodes['WPO'], '', mv, 'B')
tr = MEL.create_material_expression(mat, unreal.MaterialExpressionTransform, -300, 600)
tr.set_editor_property('transform_source_type', unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
tr.set_editor_property('transform_type', unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
MEL.connect_material_expressions(mv, '', tr, '')
# UE 5.3 Python has no MP_WORLD_POSITION_OFFSET: wire the Transform node to World Position Offset by hand in the material editor
try: MEL.connect_material_property(tr, '', getattr(unreal.MaterialProperty, 'MP_WORLD_POSITION_OFFSET'))
except AttributeError: unreal.log_warning('M_JellyTrail_v3: connect Transform -> World Position Offset by hand')
MEL.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(FULL)
unreal.log('M_JellyTrail_v3 built: ' + FULL)
