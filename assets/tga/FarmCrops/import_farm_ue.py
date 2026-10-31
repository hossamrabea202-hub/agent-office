# Farm crops for #223 (TGA, 2026-10-31): import into UE 5.3. Original procedural work (tools/tga/farm).
# Run in the editor:   py "<repo>/assets/tga/FarmCrops/import_farm_ue.py"      (re-running re-imports the same files)
# Creates under /Game/CastleDefender/Props/Farm: SM_Field_Plot (M_FieldSoil, tiling 2 m soil), wheat patches
# SM_Crop_Wheat_Sown/_Growing/_Ripe/_Harvested and SM_Crop_Cabbage_Young/_Ripe (M_Crops: one trim sheet, two-sided,
# SimpleGrassWind on vertex colour R). Crops get Nanite and no collision; the plot gets a thin box so feet do not sink.
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Props/Farm'
CROPS = ('SM_Crop_Wheat_Sown', 'SM_Crop_Wheat_Growing', 'SM_Crop_Wheat_Ripe', 'SM_Crop_Wheat_Harvested', 'SM_Crop_Cabbage_Young', 'SM_Crop_Cabbage_Ripe')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

TEX = []
for a in ('FieldSoil', 'Crops'):
    TEX += [('T_%s_BC' % a, True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_%s_ORM' % a, False, unreal.TextureCompressionSettings.TC_MASKS),
            ('T_%s_N' % a, False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
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
f.static_mesh_import_data.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE     # R = wind weight
tools.import_asset_tasks([task(os.path.join(SRC, n + '.fbx'), f) for n in ('SM_Field_Plot',) + CROPS])

def make_master(name, tex, two_sided, wind):
    path = '%s/%s' % (DST, name)
    if EAL.does_asset_exist(path): return path
    m = tools.create_asset(name, DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('two_sided', two_sided)
    def p(cls, pname, x, y, t=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', pname)
        if t: e.set_editor_property('texture', unreal.load_asset(t))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250, '%s/T_%s_BC' % (DST, tex))
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, '%s/T_%s_ORM' % (DST, tex), unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, '%s/T_%s_N' % (DST, tex), unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.6)        # rain darkens soil / leaves
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    if wind:                                                                       # optional sway; skipped if the engine function moved
        try:
            fn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/SimpleGrassWind')
            call = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -400, 700); call.set_material_function(fn)
            vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -800, 700)
            wi = p(unreal.MaterialExpressionScalarParameter, 'WindIntensity', -800, 800); wi.set_editor_property('default_value', 0.3)
            ws = p(unreal.MaterialExpressionScalarParameter, 'WindSpeed', -800, 880); ws.set_editor_property('default_value', 0.6)
            MEL.connect_material_expressions(wi, '', call, 'WindIntensity'); MEL.connect_material_expressions(vc, 'R', call, 'WindWeight')
            MEL.connect_material_expressions(ws, '', call, 'WindSpeed')
            MEL.connect_material_property(call, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        except Exception as e:
            unreal.log_warning('Farm: wind not wired (%s) - crops import static' % e)
    MEL.recompile_material(m); EAL.save_asset(path); return path
soil = make_master('M_FieldSoil', 'FieldSoil', False, False)
crops = make_master('M_Crops', 'Crops', True, True)
mis = {}
for mname, parent in (('MI_FieldSoil', soil), ('MI_Crops', crops)):
    path = '%s/%s' % (DST, mname)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset(mname, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(parent)); EAL.save_asset(path); mis[mname] = mi

sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
plot = unreal.load_asset(DST + '/SM_Field_Plot'); plot.set_material(0, mis['MI_FieldSoil'])
sub.remove_collisions(plot); sub.add_simple_collisions(plot, unreal.ScriptingCollisionShapeType.BOX); EAL.save_loaded_asset(plot)
for n in CROPS:
    sm = unreal.load_asset('%s/%s' % (DST, n)); sm.set_material(0, mis['MI_Crops']); sub.remove_collisions(sm)
    ns = sm.get_editor_property('nanite_settings'); ns.enabled = True; sm.set_editor_property('nanite_settings', ns)
    EAL.save_loaded_asset(sm)
unreal.log('Farm crops imported: ' + DST + '. Patches go at plot x/y in {-150,-50,50,150} cm; swap the stage mesh as the crop grows.')
