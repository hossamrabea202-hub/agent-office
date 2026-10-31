# MASTER ONLY (UE 5.3), #261 / #262 (TGA, 2026-10-31): the master trim material + the two trim instances.
#   py "<repo>/handoffs/texture-plan/create_trim_material_ue.py"
# Creates /Game/CastleDefender/Materials/Trim/M_Trim (BaseColorTex, ORMTex, NormalTex, Tint, TintAmount, Wetness, UScale)
# and MI_Trim_WoodIron + MI_Trim_StonePlaster. Fill TEX below with the licensed textures you built on your PC
# (/Game paths, never pushed to the repo); empty entries are left for you to set in the instance. Re-running only
# refreshes the instances' textures. Import settings it applies to the trim textures: BC sRGB, ORM Masks (linear),
# Normal = Normalmap (DirectX green, no flip), Max size 2048, wrap on both axes.
import unreal
DST = '/Game/CastleDefender/Materials/Trim'
TEX = {   # fill these: '/Game/.../T_Trim_WoodIron_BC' etc.
    'WoodIron': {'BC': '', 'ORM': '', 'N': ''},
    'StonePlaster': {'BC': '', 'ORM': '', 'N': ''},
}
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
MASTER = DST + '/M_Trim'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_Trim', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1700, 100)
    us = p(unreal.MaterialExpressionScalarParameter, 'UScale', -1700, 250); us.set_editor_property('default_value', 1.0)   # stretch / shrink along the strip
    ap = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -1500, 300)
    one = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -1700, 400); one.set_editor_property('r', 1.0)
    MEL.connect_material_expressions(us, '', ap, 'A'); MEL.connect_material_expressions(one, '', ap, 'B')
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -1350, 150)
    MEL.connect_material_expressions(tc, '', uv, 'A'); MEL.connect_material_expressions(ap, '', uv, 'B')
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250)
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    for t in (bc, orm, nrm): MEL.connect_material_expressions(uv, '', t, 'UVs')
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.6)        # wet wood / stone darkens (Lagarde)
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(MASTER)
for sheet, tex in TEX.items():
    path = '%s/MI_Trim_%s' % (DST, sheet)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset('MI_Trim_' + sheet, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    for par, key in (('BaseColorTex', 'BC'), ('ORMTex', 'ORM'), ('NormalTex', 'N')):
        if not tex[key]: continue
        t = unreal.load_asset(tex[key])
        if not t: unreal.log_warning('Trim: %s not found' % tex[key]); continue
        t.modify(); t.set_editor_property('srgb', key == 'BC'); t.set_editor_property('max_texture_size', 2048)
        t.set_editor_property('compression_settings', {'BC': unreal.TextureCompressionSettings.TC_DEFAULT, 'ORM': unreal.TextureCompressionSettings.TC_MASKS,
                                                       'N': unreal.TextureCompressionSettings.TC_NORMALMAP}[key])
        if key == 'N': t.set_editor_property('flip_green_channel', False)
        t.set_editor_property('address_x', unreal.TextureAddress.TA_WRAP); t.set_editor_property('address_y', unreal.TextureAddress.TA_WRAP)
        EAL.save_loaded_asset(t)
        MEL.set_material_instance_texture_parameter_value(mi, par, t)
    EAL.save_asset(path)
unreal.log('Trim material ready: %s + MI_Trim_WoodIron / MI_Trim_StonePlaster. Set the textures in TEX (top of this script) and run again.' % MASTER)
