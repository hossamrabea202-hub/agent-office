# AAA stair kit for #279 (TGA, 2026-10-31): import into UE 5.3. Original procedural work (tools/tga/stairs).
# Run in the editor:   py "<repo>/assets/tga/StairKit/import_stairkit_ue.py"      (re-running re-imports the same files)
# Creates under /Game/CastleDefender/Props/StairKit: 120 flights SM_Stair_W{120,200,300,400}_{Solid,Soffit}_N{02..16}
# (one watertight mesh each, <= 646 tris, UCX ramp collision, lightmap UV1), T_StairKit_BC/ORM/N (2K), M_StairKit +
# MI_StairKit (Tint, TintAmount, Wetness). Slot 0 = MI_StairKit (baked steps), slot 1 = the castle wall stone
# MI_Castle_StoneWall_World (used, never edited) for the sides, soffit and back.
import os, glob
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Props/StairKit'
WALL_MI = 'MI_Castle_StoneWall_World'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

TEX = [('T_StairKit_BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_StairKit_ORM', False, unreal.TextureCompressionSettings.TC_MASKS),
       ('T_StairKit_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
f.import_materials = False; f.import_textures = False
f.static_mesh_import_data.combine_meshes = True; f.static_mesh_import_data.auto_generate_collision = False   # UCX_ ramps come with the FBX
f.static_mesh_import_data.generate_lightmap_u_vs = False                                                     # UV1 is authored
f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
FBX = sorted(glob.glob(os.path.join(SRC, 'fbx', 'SM_Stair_*.fbx')))
tools.import_asset_tasks([task(p, f) for p in FBX])

MASTER = DST + '/M_StairKit'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_StairKit', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250, DST + '/T_StairKit_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, DST + '/T_StairKit_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, DST + '/T_StairKit_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.65)      # wet stone darkens
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.25); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(MASTER)
MI = DST + '/MI_StairKit'
mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_StairKit', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
for par, suf in (('BaseColorTex', 'BC'), ('ORMTex', 'ORM'), ('NormalTex', 'N')):
    MEL.set_material_instance_texture_parameter_value(mi, par, unreal.load_asset('%s/T_StairKit_%s' % (DST, suf)))
EAL.save_asset(MI)

reg = unreal.AssetRegistryHelpers.get_asset_registry()
hits = [h for h in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')) if str(h.asset_name) == WALL_MI]
wall = unreal.load_asset(str(hits[0].package_name)) if hits else None
if not wall: unreal.log_warning('#279: %s not found, the sides keep MI_StairKit: set slot 1 by hand' % WALL_MI)
for p in FBX:
    n = os.path.splitext(os.path.basename(p))[0]; sm = unreal.load_asset('%s/%s' % (DST, n))
    if not sm: unreal.log_warning('#279: %s did not import' % n); continue
    sm.set_material(0, mi); sm.set_material(1, wall or mi)          # pawns walk the UCX ramp; traces hit the real steps
    EAL.save_loaded_asset(sm)
unreal.log('#279 stair kit imported: %d flights in %s. Next: py ".../assets/tga/StairKit/place_stairkit_ue.py" (DRY_RUN first).' % (len(FBX), DST))
