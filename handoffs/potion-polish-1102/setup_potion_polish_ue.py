# Potion polish (i9, 2026-11-02), step 1. UE 5.8 Python.  [--dry-run]
#   1. builds /Game/CastleDefender/UI/HUD/M_UI_PotionBadge (UI domain, translucent): one HLSL node draws the round badge
#      (gold bevel ring, dark disc, the potion icon, a clockwise cooldown sweep, a gold/green pulsing halo, a red refuse
#      flash, a dim "empty" look). Driven per frame through a MID: Pot = (cool 0-1, gold glow, empty, refuse), Pot2.R = heal glow.
#   2. adds the new variables to BPC_PotionBelt with defaults (old variables untouched):
#      HintAt -100, HintStage 0, RefuseAt -100, HPFrac 1, BadgeMID (MID), BadgeMat = M_UI_PotionBadge,
#      PlateTex = T_MenuButton_Plate, GlowTex = T_ST_Glow.  Compiles + saves BPC_PotionBelt (graph unchanged).
import sys, unreal
DRY = '--dry-run' in sys.argv
EAL, BEL, MEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
MAT_DIR, MAT = '/Game/CastleDefender/UI/HUD', 'M_UI_PotionBadge'
BELT = '/Game/CastleDefender/Gameplay/Castle/BPC_PotionBelt'
ICON, PLATE, GLOW = '/Game/CastleDefender/UI/T_Item_Potion_Health', '/Game/CastleDefender/UI/HUD/T_MenuButton_Plate', '/Game/CastleDefender/UI/SkillTree/T_ST_Glow'
log = ['potion polish setup' + (' (DRY RUN)' if DRY else '')]
for p in (BELT, ICON, PLATE, GLOW):
    a = unreal.load_asset(p)
    log.append('%-55s %s' % (p, ('ok %dx%d' % (a.blueprint_get_size_x(), a.blueprint_get_size_y())) if isinstance(a, unreal.Texture2D) else 'ok' if a else 'MISSING'))

HLSL = r'''
float2 c = UV - 0.5;
float r = length(c) * 2.0;
float aa = max(fwidth(r) * 1.2, 0.004);
float a01 = frac(atan2(c.x, -c.y) / 6.2831853 + 1.0);
float disc = 1.0 - smoothstep(0.70 - aa, 0.70 + aa, r);
float outer = 1.0 - smoothstep(0.82 - aa, 0.82 + aa, r);
float ring = saturate(outer - disc);
float2 n = c / max(length(c), 0.0001);
float lit = saturate(dot(n, float2(-0.6, -0.8)) * 0.5 + 0.5);
float bp = saturate((r - 0.70) / 0.12);
float bev = sin(bp * 3.14159);
float emp = saturate(P.b);
float3 gold = lerp(float3(0.26, 0.15, 0.05), float3(1.0, 0.84, 0.48), saturate(bev * (0.35 + 0.9 * lit)));
gold *= lerp(1.0, 0.6, emp);
float3 bg = lerp(float3(0.13, 0.08, 0.05), float3(0.03, 0.02, 0.015), saturate(r / 0.70));
float2 iuv = c / 0.62 + 0.5;
float inI = step(0.0, iuv.x) * step(iuv.x, 1.0) * step(0.0, iuv.y) * step(iuv.y, 1.0);
float4 ic = Texture2DSample(Tex, TexSampler, saturate(iuv));
ic.a *= inI;
float lum = dot(ic.rgb, float3(0.3, 0.59, 0.11));
ic.rgb = lerp(ic.rgb, lum.xxx * 0.4, emp);
float3 col = lerp(bg, ic.rgb, ic.a);
float cool = saturate(P.r);
float sw = (cool > 0.001) ? step(a01, cool) : 0.0;
col = lerp(col, col * 0.2, sw);
float ed = (cool > 0.001) ? (1.0 - smoothstep(0.0, 0.015, abs(a01 - cool))) * step(0.08, r) : 0.0;
col += float3(1.0, 0.82, 0.45) * ed * 0.7;
col *= lerp(1.0, 0.55, smoothstep(0.52, 0.70, r));
float rf = saturate(PA);
gold = lerp(gold, float3(0.95, 0.18, 0.10) * (0.6 + 0.6 * bev), rf);
float pulse = 0.7 + 0.3 * sin(T * 6.2831853 * 1.1);
float gG = saturate(P.g);
float gH = saturate(Q);
float3 glowC = float3(1.0, 0.72, 0.28) * gG + float3(0.35, 1.0, 0.45) * gH;
float gAmt = max(gG, gH) * pulse;
gold += glowC * 0.35 * gAmt;
float body = saturate(disc + ring);
float halo = (1.0 - smoothstep(0.82, 1.0, r)) * smoothstep(0.76, 0.83, r);
float ha = halo * gAmt * 0.85 * (1.0 - body);
float3 glowN = glowC / max(max(glowC.r, max(glowC.g, glowC.b)), 0.001);
float3 bodyC = (col * disc + gold * ring) / max(body, 0.001);
float3 o = lerp(glowN, bodyC, saturate(body * 4.0));
return float4(o, saturate(body + ha));
'''


def build_material():
    path = MAT_DIR + '/' + MAT
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path); MEL.delete_all_material_expressions(m)
    else:
        m = at.create_asset(MAT, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    E = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    uv = E(unreal.MaterialExpressionTextureCoordinate, -900, -200)
    tex = E(unreal.MaterialExpressionTextureObjectParameter, -900, -50)
    tex.set_editor_property('parameter_name', 'Icon'); tex.set_editor_property('texture', unreal.load_asset(ICON))
    pot = E(unreal.MaterialExpressionVectorParameter, -900, 150)
    pot.set_editor_property('parameter_name', 'Pot'); pot.set_editor_property('default_value', unreal.LinearColor(0, 0, 0, 0))
    pot2 = E(unreal.MaterialExpressionVectorParameter, -900, 400)
    pot2.set_editor_property('parameter_name', 'Pot2'); pot2.set_editor_property('default_value', unreal.LinearColor(0, 0, 0, 0))
    tm = E(unreal.MaterialExpressionTime, -900, 600)
    cu = E(unreal.MaterialExpressionCustom, -400, 0)
    cu.set_editor_property('code', HLSL)
    cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    cu.set_editor_property('description', 'PotionBadge')
    ins = []
    for nm in ('UV', 'Tex', 'P', 'PA', 'Q', 'T'):
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', nm); ins.append(ci)
    cu.set_editor_property('inputs', ins)
    ok = [MEL.connect_material_expressions(uv, '', cu, 'UV'), MEL.connect_material_expressions(tex, '', cu, 'Tex'),
          MEL.connect_material_expressions(pot, '', cu, 'P'), MEL.connect_material_expressions(pot, 'A', cu, 'PA'),
          MEL.connect_material_expressions(pot2, 'R', cu, 'Q'), MEL.connect_material_expressions(tm, '', cu, 'T')]
    rgb = E(unreal.MaterialExpressionComponentMask, -100, -60)
    for k, v in (('r', True), ('g', True), ('b', True), ('a', False)): rgb.set_editor_property(k, v)
    al = E(unreal.MaterialExpressionComponentMask, -100, 80)
    for k, v in (('r', False), ('g', False), ('b', False), ('a', True)): al.set_editor_property(k, v)
    ok += [MEL.connect_material_expressions(cu, '', rgb, ''), MEL.connect_material_expressions(cu, '', al, ''),
           MEL.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR),
           MEL.connect_material_property(al, '', unreal.MaterialProperty.MP_OPACITY)]
    MEL.recompile_material(m)
    EAL.save_asset(path)
    log.append('material %s links %s' % (path, ok))


def add_vars():
    bp = unreal.load_asset(BELT)
    I, Dd = BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('real')
    assert 'PinSubCategory="double"' in Dd.export_text(), 'real is not double: ' + Dd.export_text()
    DEF = {'HintAt': (Dd, -100.0), 'HintStage': (I, 0), 'RefuseAt': (Dd, -100.0), 'HPFrac': (Dd, 1.0)}
    OBJ = {'BadgeMID': (unreal.MaterialInstanceDynamic, None), 'BadgeMat': (unreal.MaterialInterface, MAT_DIR + '/' + MAT),
           'PlateTex': (unreal.Texture2D, PLATE), 'GlowTex': (unreal.Texture2D, GLOW)}
    have = [str(n).split('.')[-1].split(':')[-1] for n in BEL.list_member_variable_names(bp)]
    for n, (t_, _) in DEF.items():
        if n not in have and not BEL.add_member_variable(bp, n, t_): raise RuntimeError('could not add ' + n)
    for n, (c, _) in OBJ.items():
        if n not in have and not BEL.add_member_variable(bp, n, BEL.get_object_reference_type(c)): raise RuntimeError('could not add ' + n)
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(BEL.generated_class(bp))
    for n, (_, v) in DEF.items(): cdo.set_editor_property(n, v)
    for n, (_, p) in OBJ.items():
        if p: cdo.set_editor_property(n, unreal.load_asset(p))
    EAL.save_asset(BELT)
    log.append('BPC_PotionBelt vars now: %s' % [str(n).split('.')[-1].split(':')[-1] for n in BEL.list_member_variable_names(bp)])


if not DRY:
    build_material()
    add_vars()
print('\n'.join(log))
