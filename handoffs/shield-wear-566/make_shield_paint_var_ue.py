# #566 (i5 adjustedfilm, 2026-11-07): build M_Shield_Paint_Var, a NEW copy of the swordsmen's shield paint with a
# per-soldier wear seed. The live M_Shield_Paint_AAA is not touched.
#   py "<repo>/handoffs/shield-wear-566/make_shield_paint_var_ue.py" --dry-run     (checks only, changes nothing)
#   py "<repo>/handoffs/shield-wear-566/make_shield_paint_var_ue.py" --build       (creates + compiles + saves)
#   py "<repo>/handoffs/shield-wear-566/make_shield_paint_var_ue.py" --revert      (deletes the new material only)
# Optional: --folder /Game/Some/Folder (default below).
# Parameters on the material (the soldier BP already sets the first two on every soldier):
#   Tint (vector, 1,1,1)  Wear (scalar, 0)  WearSeed (scalar, -1 = automatic per soldier, 0 = original look, >0 fixed)
import os, sys, unreal
args = sys.argv[1:]
FOLDER = args[args.index('--folder') + 1] if '--folder' in args else '/Game/CastleDefender/Equipment/Weapons/Shield/Var566'
NAME = 'M_Shield_Paint_Var'
PATH = FOLDER + '/' + NAME
WOOD = '/Game/Fab/Megascans/Surfaces/Worn_Wooden_Table_Top_tdfhffuq/Medium/T_tdfhffuq_2K_B'
HLSL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shield_paint_var.hlsl')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
def log(*a): unreal.log('SHIELD566 ' + ' '.join(str(x) for x in a))

mode = '--build' if '--build' in args else '--revert' if '--revert' in args else '--dry-run'
code = open(HLSL, encoding='utf-8').read()
log('mode', mode, '| target', PATH, '| hlsl', len(code), 'chars')
if mode == '--dry-run':
    log('wood texture', WOOD, 'found' if EAL.does_asset_exist(WOOD) else 'MISSING (build would stop)')
    log('target', 'EXISTS (build would stop, run --revert first)' if EAL.does_asset_exist(PATH) else 'free')
    log('live M_Shield_Paint_AAA is not touched. DRY RUN DONE')
elif mode == '--revert':
    if EAL.does_asset_exist(PATH):
        refs = EAL.find_package_referencers_for_asset(PATH, False)
        if refs:
            log('STOP: still used by', list(refs), '- set the soldier back to M_Shield_Paint_AAA first')
        else:
            EAL.delete_asset(PATH); log('deleted', PATH, 'REVERT DONE')
    else:
        log('nothing to revert')
else:
    if not EAL.does_asset_exist(WOOD): raise RuntimeError('wood texture missing: ' + WOOD)
    if EAL.does_asset_exist(PATH): raise RuntimeError(PATH + ' exists already; run --revert first')
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property('tangent_space_normal', False)      # the shader returns a world-space normal (as the original)
    X = -900
    wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, X - 400, -200)
    tp = MEL.create_material_expression(mat, unreal.MaterialExpressionTransformPosition, X, -250)
    tp.set_editor_property('transform_source_type', unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    tp.set_editor_property('transform_type', unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    MEL.connect_material_expressions(wp, '', tp, '')
    nrm = MEL.create_material_expression(mat, unreal.MaterialExpressionVertexNormalWS, X, -50)
    tex = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureObject, X, 50)
    tex.set_editor_property('texture', unreal.load_asset(WOOD))
    tint = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, X - 400, 200)
    tint.set_editor_property('parameter_name', 'Tint'); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    mask = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, X, 200)
    for c in ('r', 'g', 'b'): mask.set_editor_property(c, True)
    mask.set_editor_property('a', False)
    MEL.connect_material_expressions(tint, '', mask, '')
    wear = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, X, 330)
    wear.set_editor_property('parameter_name', 'Wear'); wear.set_editor_property('default_value', 0.0)
    seed = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, X, 430)
    seed.set_editor_property('parameter_name', 'WearSeed'); seed.set_editor_property('default_value', -1.0)
    cu = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, 0)
    cu.set_editor_property('code', code)
    cu.set_editor_property('description', 'ShieldPaintVar566')
    cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for n in ('LP', 'P', 'N', 'W', 'Tint', 'Wear', 'Seed'):
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    cu.set_editor_property('inputs', ins)
    outs = []
    for n, ty in (('Rough', unreal.CustomMaterialOutputType.CMOT_FLOAT1), ('Nrm', unreal.CustomMaterialOutputType.CMOT_FLOAT3),
                  ('Metal', unreal.CustomMaterialOutputType.CMOT_FLOAT1)):
        co = unreal.CustomOutput(); co.set_editor_property('output_name', n); co.set_editor_property('output_type', ty); outs.append(co)
    cu.set_editor_property('additional_outputs', outs)
    # P = camera-relative world position (only used for ddx/ddy in the bump), exactly as in M_Shield_Paint_AAA
    wpc = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, X, -150)
    wpc.set_editor_property('world_position_shader_offset', unreal.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE)
    for src, pin in ((tp, 'LP'), (wpc, 'P'), (nrm, 'N'), (tex, 'W'), (mask, 'Tint'), (wear, 'Wear'), (seed, 'Seed')):
        if not MEL.connect_material_expressions(src, '', cu, pin): raise RuntimeError('could not wire ' + pin)
    # same output wiring as M_Shield_Paint_AAA: BaseColor = code x Tint, Roughness = code Rough + Wear
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 0, -100)
    add = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, 0, 50)
    ok = MEL.connect_material_expressions(cu, '', mul, 'A') and MEL.connect_material_expressions(tint, '', mul, 'B')
    ok = ok and MEL.connect_material_expressions(cu, 'Rough', add, 'A') and MEL.connect_material_expressions(wear, '', add, 'B')
    if not ok: raise RuntimeError('could not wire Tint multiply / Wear add')
    for src, out, prop in ((mul, '', unreal.MaterialProperty.MP_BASE_COLOR), (add, '', unreal.MaterialProperty.MP_ROUGHNESS),
                           (cu, 'Nrm', unreal.MaterialProperty.MP_NORMAL), (cu, 'Metal', unreal.MaterialProperty.MP_METALLIC)):
        if not MEL.connect_material_property(src, out, prop): raise RuntimeError('could not wire output ' + str(prop))
    MEL.recompile_material(mat)
    EAL.save_asset(PATH, only_if_is_dirty=False)
    log('built', PATH, '| expressions', MEL.get_num_material_expressions(mat), '| BUILD DONE (check the Output Log for shader errors)')
