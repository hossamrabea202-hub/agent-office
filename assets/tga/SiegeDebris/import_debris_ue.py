# Siege debris set for #162 (#202 item 9; TGA, 2026-10-30): import into UE 5.3. Original procedural work (tools/tga/debris).
# Run in the editor:   py "<repo>/assets/tga/SiegeDebris/import_debris_ue.py"      (re-running re-imports the same files)
# Creates under /Game/CastleDefender/Props/Aftermath/SiegeDebris: SM_Debris_BrokenCart / _Beams / _Palisade, one 2K atlas
# (T_Debris_BC/_ORM/_N, M_Debris + MI_Debris with Tint/TintAmount/Wetness), 18-DOP collision each.
# Pivots on the ground at each pile centre. Spawned by #162 battle memory where a fight happened.
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Props/Aftermath/SiegeDebris'
NAMES = ('SM_Debris_BrokenCart', 'SM_Debris_Beams', 'SM_Debris_Palisade')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

TEX = [('T_Debris_BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_Debris_ORM', False, unreal.TextureCompressionSettings.TC_MASKS),
       ('T_Debris_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
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

MASTER = DST + '/M_Debris'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_Debris', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250, DST + '/T_Debris_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, DST + '/T_Debris_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, DST + '/T_Debris_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
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
    MEL.recompile_material(m); EAL.save_asset(MASTER)
MI = DST + '/MI_Debris'
mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_Debris', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER)); EAL.save_asset(MI)

sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
for n in NAMES:
    sm = unreal.load_asset('%s/%s' % (DST, n)); sm.set_material(0, unreal.load_asset(MI))
    sub.remove_collisions(sm); sub.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.NDOP18); EAL.save_loaded_asset(sm)
unreal.log('Siege debris imported: ' + DST + '. #162: spawn at fought-over spots (gate, road raids); rotate Z freely.')

