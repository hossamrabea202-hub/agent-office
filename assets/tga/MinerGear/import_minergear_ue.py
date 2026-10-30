# Miner NPC gear (#202 item 7; TGA, 2026-10-30): import into UE 5.3. Original procedural work (tools/tga/miner).
# Run in the editor:   py "<repo>/assets/tga/MinerGear/import_minergear_ue.py"      (re-running re-imports the same files)
# Creates under /Game/CastleDefender/Characters/NPC/MinerGear: SM_MinerPick / _Helmet / _Satchel sharing one 2K atlas
# (T_MinerGear_BC/_ORM/_N, M_MinerGear + MI_MinerGear with Tint/TintAmount/Wetness), no collision (attachables).
# + T_MinerGear_E (candle flame mask -> emissive, GlowIntensity on the MI). Attach with sockets: see README.
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Characters/NPC/MinerGear'
NAMES = ('SM_MinerPick', 'SM_MinerHelmet', 'SM_MinerSatchel')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

TEX = [('T_MinerGear_BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_MinerGear_ORM', False, unreal.TextureCompressionSettings.TC_MASKS),
       ('T_MinerGear_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP), ('T_MinerGear_E', False, unreal.TextureCompressionSettings.TC_GRAYSCALE)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
f.import_materials = False; f.import_textures = False
f.static_mesh_import_data.combine_meshes = True; f.static_mesh_import_data.auto_generate_collision = False
f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
tools.import_asset_tasks([task(os.path.join(SRC, n + '.fbx'), f) for n in NAMES])

MASTER = DST + '/M_MinerGear'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_MinerGear', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250, DST + '/T_MinerGear_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, DST + '/T_MinerGear_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, DST + '/T_MinerGear_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.6)       # rain-soaked wood darkens
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    emt = p(unreal.MaterialExpressionTextureSampleParameter2D, 'GlowTex', -1100, 800, DST + '/T_MinerGear_E', unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE)
    gint = p(unreal.MaterialExpressionScalarParameter, 'GlowIntensity', -1100, 1000); gint.set_editor_property('default_value', 8.0)
    fcol = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -800, 1050); fcol.set_editor_property('constant', unreal.LinearColor(1.0, 0.55, 0.2, 1))
    e1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, 850); MEL.connect_material_expressions(emt, 'R', e1, 'A'); MEL.connect_material_expressions(fcol, '', e1, 'B')
    e2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, 900); MEL.connect_material_expressions(e1, '', e2, 'A'); MEL.connect_material_expressions(gint, '', e2, 'B')
    MEL.connect_material_property(e2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(MASTER)
MI = DST + '/MI_MinerGear'
mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_MinerGear', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER)); EAL.save_asset(MI)

sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
for n in NAMES:
    sm = unreal.load_asset('%s/%s' % (DST, n)); sm.set_material(0, unreal.load_asset(MI))
    sub.remove_collisions(sm); EAL.save_loaded_asset(sm)                # attachables: no collision
unreal.log('Miner gear imported: ' + DST + '. Attach: pick -> hand_r socket, helmet -> head, satchel -> spine_03 (see README).')


