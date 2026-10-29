# #96 Obsidian Sovereign hand shield (item 30): its own VFX, the "Bulwark Rune" (SPEC.md 4). By laptop2, 2026-10-29.
# Run in the Unreal editor (Output Log, Python):  py "<repo>/handoffs/obsidian-set-bonus-96/make_M_BulwarkRune.py"
# Creates (re-running rebuilds the two materials; the MPC entry is only added if missing):
#   vector Shield in the MPC that holds Armor (MPC_SkillTree): R = shield level 0..4, G = last block time (game seconds)
#   /Game/CastleDefender/VFX/ObsidianSet/M_BulwarkRune   additive unlit overlay for SM_ObsidianSovereign_Shield: a gold rune
#                                                       around the boss that grows per level, a flash on block
#   /Game/CastleDefender/VFX/ObsidianSet/M_BulwarkDome   additive unlit hex dome for a sphere shown for 0.3 s on an LV4 block
# Both output black (= invisible when additive) when Shield.R < 1 (no shield / not bought).
import unreal

PATH = '/Game/CastleDefender/VFX/ObsidianSet'
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

# ---- the MPC that holds Armor (the same one make_M_ObsidianSetAura.py uses) ----
mpc = None
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection')):
    c = ad.get_asset()
    if any(str(v.get_editor_property('parameter_name')) == 'Armor' for v in c.get_editor_property('vector_parameters')):
        mpc = c; break
if mpc is None:
    raise RuntimeError('no MaterialParameterCollection with a vector parameter Armor found')
vecs = list(mpc.get_editor_property('vector_parameters'))
if not any(str(v.get_editor_property('parameter_name')) == 'Shield' for v in vecs):
    p = unreal.CollectionVectorParameter()
    p.set_editor_property('parameter_name', 'Shield')
    p.set_editor_property('default_value', unreal.LinearColor(0, -100, 0, 0))   # not owned, last block far in the past
    vecs.append(p)
    mpc.modify()
    mpc.set_editor_property('vector_parameters', vecs)
    EAL.save_asset(mpc.get_path_name())
    unreal.log('#96 added vector Shield to ' + mpc.get_path_name())


def new_material(name, two_sided):
    full = PATH + '/' + name
    if EAL.does_asset_exist(full):
        EAL.delete_asset(full)
    m = tools.create_asset(name, PATH, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided', two_sided)
    return m, full


def custom(m, desc, code, inputs, x=-450, y=200):
    """inputs: list of (name, expression). Returns the Custom node (float3)."""
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property('description', desc)
    c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    c.set_editor_property('code', code)
    ins = []
    for n, _ in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    c.set_editor_property('inputs', ins)
    for n, e in inputs:
        MEL.connect_material_expressions(e, '', c, n)
    return c


def common(m):
    """Local position + local normal (they follow the shield in the hand), Time, the Shield MPC vector."""
    wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, -200)
    lp = MEL.create_material_expression(m, unreal.MaterialExpressionTransformPosition, -1150, -200)
    lp.set_editor_property('transform_source_type', unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    lp.set_editor_property('transform_type', unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    MEL.connect_material_expressions(wp, '', lp, 'Input')
    vn = MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -1400, -80)
    ln = MEL.create_material_expression(m, unreal.MaterialExpressionTransform, -1150, -80)
    ln.set_editor_property('transform_source_type', unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD)
    ln.set_editor_property('transform_type', unreal.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    MEL.connect_material_expressions(vn, '', ln, 'Input')
    now = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1150, 20)
    fres = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -1150, 120)
    fres.set_editor_property('exponent', 3.0)
    st = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -1150, 240)
    st.set_editor_property('collection', mpc)
    st.set_editor_property('parameter_name', 'Shield')
    return lp, ln, now, fres, st


def scalar(m, name, val, y):
    s = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1150, y)
    s.set_editor_property('parameter_name', name); s.set_editor_property('default_value', val)
    return s


# =============================== M_BulwarkRune (overlay on the shield) ===============================
# Mesh space (cm after import): the point at z 0, the boss centre at z 45.2, the boss 9 cm wide (with its flange),
# the gold lozenge 15 x 21.5 cm (half sizes). The rune lives between the boss and the lozenge, drawn in the x/z plane:
#   LV1 hex ring (circumradius 11.5)   LV2 + an Algiz (protection) rune above and below the boss
#   LV3 + six rays off the hex corners   LV4 + the boss rim, everything brighter, a slow breathing pulse
# Only the front face shows it (local normal along FaceY). Block: 0.3 s white-gold flash over the whole face.
RUNE = '''
float lvl = floor(Sh.r + 0.5);
if (lvl < 1) return float3(0, 0, 0);
float front = saturate((LN.y * FaceY - 0.25) / 0.35);
float2 p = float2(LP.x, LP.z - CentreZ) / RuneScale;
float w = LineW;
// hex ring: distance to a regular hexagon (corners up and down)
float2 q = abs(p);
float hexR = 11.5 * 0.8660254;
float dh = max(q.x * 0.5 + q.y * 0.8660254, q.x) - hexR;
float ring = saturate(1 - abs(dh) / w);
// Algiz above and below: a stave plus two arms rising from its middle (mirrored below)
float2 a = float2(p.x, abs(p.y));
float stave = (a.y > 13.2 && a.y < 20.0) ? saturate(1 - abs(a.x) / w) : 0;
float2 b0 = float2(0, 15.6), b1 = float2(3.2, 19.4);
float2 ax = float2(abs(a.x), a.y) - b0, bd = b1 - b0;
float arms = saturate(1 - length(ax - bd * saturate(dot(ax, bd) / dot(bd, bd))) / w);
float glyph = max(stave, arms) * step(2, lvl);
// rays off the six hex corners, 11.5 -> 13.6
float ang = atan2(p.x, p.y);
float sector = round(ang / 1.0471976) * 1.0471976;
float2 dir = float2(sin(sector), cos(sector));
float t = dot(p, dir);
float rays = (t > 11.9 && t < 13.6) ? saturate(1 - abs(p.x * dir.y - p.y * dir.x) / w) : 0;
rays *= step(3, lvl);
float rim = saturate(1 - abs(length(p) - 7.4) / (w * 1.4)) * step(4, lvl);
float shape = max(max(ring, glyph), max(rays, rim));
float lvlGain = lvl * 0.35 + (lvl >= 4 ? 0.6 : 0);
float pulse = lvl >= 4 ? 0.8 + 0.2 * sin(Now * 6.28318 * 0.35) : 1;
float halo = saturate(1 - abs(dh) / (w * 5)) * 0.12 * lvl;            // soft glow hugging the hex
float3 gold = float3(1.0, 0.66, 0.22);
float block = saturate(1 - (Now - Sh.g) / 0.3);
float3 col = gold * (shape + halo) * lvlGain * pulse
           + float3(1.0, 0.92, 0.72) * block * block * (0.25 + shape * 2 + Fres);
return col * front * Intensity;
'''
rm, RFULL = new_material('M_BulwarkRune', False)
lp, ln, now, fres, st = common(rm)
rp = [('CentreZ', scalar(rm, 'CentreZ', 45.24, 360)), ('RuneScale', scalar(rm, 'RuneScale', 1.0, 460)),
      ('LineW', scalar(rm, 'LineW', 0.45, 560)), ('FaceY', scalar(rm, 'FaceY', 1.0, 660)),
      ('Intensity', scalar(rm, 'Intensity', 4.0, 760))]
c = custom(rm, 'BulwarkRune', RUNE, [('LP', lp), ('LN', ln), ('Now', now), ('Fres', fres), ('Sh', st)] + rp)
MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(rm)
EAL.save_asset(RFULL)

# =============================== M_BulwarkDome (LV4 block) ===============================
# For a sphere static mesh (e.g. /Engine/BasicShapes/Sphere, 100 cm wide) under the shield, scale ~3 (a 1.5 m dome).
# The material swells it by 0..25 % over the 0.3 s (World Position Offset) and draws a gold hex grid that is
# brightest at the edges (Fresnel) and fades out. BP: show the component on an LV4 block, hide it after 0.3 s.
DOME = '''
float age = (Now - Sh.g) / 0.3;
if (Sh.r < 3.5 || age < 0 || age > 1) return float3(0, 0, 0);
float3 d = normalize(LP);
float2 uv = float2(atan2(d.y, d.x) * HexCount / 6.28318, asin(clamp(d.z, -1, 1)) * HexCount / 3.14159) * float2(1, 1.1547);
// hex grid: distance to the nearest cell edge
float2 r = float2(1, 1.7320508), h = r * 0.5;
float2 ga = fmod(abs(uv), r) - h, gb = fmod(abs(uv - h), r) - h;
float2 g = dot(ga, ga) < dot(gb, gb) ? ga : gb;
float2 ag = abs(g);
float edge = 0.5 - max(ag.x * 0.5 + ag.y * 0.8660254, ag.x);
float lines = saturate(1 - edge / 0.06);
float fade = (1 - age) * (1 - age);
float3 gold = float3(1.0, 0.68, 0.25);
return gold * (lines * (0.35 + Fres * 1.6) + Fres * 0.5) * fade * Intensity;
'''
dm, DFULL = new_material('M_BulwarkDome', True)
lp, ln, now, fres, st = common(dm)
dp = [('HexCount', scalar(dm, 'HexCount', 14.0, 360)), ('Intensity', scalar(dm, 'Intensity', 3.0, 460))]
c = custom(dm, 'BulwarkDome', DOME, [('LP', lp), ('Now', now), ('Fres', fres), ('Sh', st)] + dp)
MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
# swell: WPO = normal * radius * 0.25 * age (object radius 50 cm on the engine sphere -> world via the mesh scale)
WPO = '''
float age = saturate((Now - Sh.g) / 0.3);
return N * Swell * age;
'''
vn = MEL.create_material_expression(dm, unreal.MaterialExpressionVertexNormalWS, -800, 700)
w = custom(dm, 'BulwarkDomeSwell', WPO, [('N', vn), ('Now', now), ('Sh', st), ('Swell', scalar(dm, 'SwellCm', 35.0, 560))],
           -450, 600)
MEL.connect_material_property(w, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
MEL.recompile_material(dm)
EAL.save_asset(DFULL)
unreal.log('#96 Bulwark Rune built: M_BulwarkRune (Overlay Material on the shield) and M_BulwarkDome in ' + PATH)
