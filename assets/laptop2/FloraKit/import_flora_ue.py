# Flora kit (laptop2, 2026-10-30): meadow flowers + realm flora + corrupted ground. Import into UE 5.3.
# Run in the editor:  py "<repo>/assets/laptop2/FloraKit/import_flora_ue.py" [Daisy Poppy ...]
# Each species goes to /Game/CastleDefender/Environment/Flora/<Species>/ with its textures, an MI of the shared
# M_LP2Foliage (Two Sided Foliage shading model: subsurface from BaseColor, wind sway via SimpleGrassWind,
# emissive for the realm plants) and 3 LODs. CorruptPatch uses M_LP2CorruptGround (opaque, emissive cracks,
# dithered rim so it melts into the terrain).
import os, sys
import unreal
REPO = r''
try:
    SRC = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SRC = os.path.join(REPO, 'assets', 'laptop2', 'FloraKit')
ROOT = '/Game/CastleDefender/Environment/Flora'
SPECIES = {'Daisy': False, 'Poppy': False, 'Foxglove': False, 'Bloodcap': True, 'SporeStalk': True, 'TentacleFern': True, 'CorruptPatch': True, 'BlobMine': True, 'EggCluster': True}
pick = [a for a in sys.argv[1:] if a in SPECIES] or list(SPECIES)
EAL, MEL, SML = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.EditorStaticMeshLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, dst, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dst; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
def fbx_ui():
    f = unreal.FbxImportUI(); f.import_mesh = True; f.import_as_skeletal = False; f.import_materials = False; f.import_textures = False
    f.static_mesh_import_data.combine_meshes = True; f.static_mesh_import_data.generate_lightmap_u_vs = False
    f.static_mesh_import_data.auto_generate_collision = False
    f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return f

def make_master(name, T0, foliage, emis):
    path = ROOT + '/' + name
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    m = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if foliage:
        m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE); m.set_editor_property('two_sided', True)
    def p(cls, pname, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', pname)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    T = unreal.MaterialExpressionTextureSampleParameter2D
    bc = p(T, 'BaseColor', -900, -300, T0 + '_BaseColor')
    orm = p(T, 'ORM', -900, 50, T0 + '_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(T, 'Normal', -900, 400, T0 + '_Normal_DirectX', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    MEL.connect_material_property(bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    if foliage:
        ss = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -150)
        sst = p(unreal.MaterialExpressionScalarParameter, 'SubsurfaceAmount', -900, -500); sst.set_editor_property('default_value', 0.6)
        MEL.connect_material_expressions(bc, 'RGB', ss, 'A'); MEL.connect_material_expressions(sst, '', ss, 'B')
        MEL.connect_material_property(ss, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
        wind = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -700, 700)
        wind.set_editor_property('material_function', unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/SimpleGrassWind'))
        wi = p(unreal.MaterialExpressionScalarParameter, 'WindIntensity', -1000, 650); wi.set_editor_property('default_value', 0.6)
        ww = p(unreal.MaterialExpressionScalarParameter, 'WindWeight', -1000, 750); ww.set_editor_property('default_value', 1.0)
        ws = p(unreal.MaterialExpressionScalarParameter, 'WindSpeed', -1000, 850); ws.set_editor_property('default_value', 1.0)
        try:
            MEL.connect_material_expressions(wi, '', wind, 'WindIntensity'); MEL.connect_material_expressions(ww, '', wind, 'WindWeight')
            MEL.connect_material_expressions(ws, '', wind, 'WindSpeed'); MEL.connect_material_property(wind, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        except Exception as e:
            unreal.log_warning('wind not wired (%s): plug SimpleGrassWind into WPO by hand' % e)
    if emis:
        em = p(T, 'Emissive', -900, 1000, T0 + '_Emissive')
        eb = p(unreal.MaterialExpressionScalarParameter, 'EmissiveBoost', -900, 1250); eb.set_editor_property('default_value', 6.0)
        tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 1400)
        sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -750, 1400); sn.set_editor_property('period', 3.7); MEL.connect_material_expressions(tm, '', sn, '')
        pz = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 1400); pz.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(sn, '', pz, 'A')
        pa = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -480, 1400); pa.set_editor_property('const_b', 1.0); MEL.connect_material_expressions(pz, '', pa, 'A')
        e1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, 1050); MEL.connect_material_expressions(em, 'RGB', e1, 'A'); MEL.connect_material_expressions(eb, '', e1, 'B')
        e2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 1100); MEL.connect_material_expressions(e1, '', e2, 'A'); MEL.connect_material_expressions(pa, '', e2, 'B')
        MEL.connect_material_property(e2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(path); return m

for sp in pick:
    emis = SPECIES[sp]; DST = ROOT + '/' + sp; mesh = 'SM_Flora_' + sp; tn = 'T_Flora_' + sp
    SETTINGS = {'_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT), '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
                '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
    if emis: SETTINGS['_Emissive'] = (True, unreal.TextureCompressionSettings.TC_DEFAULT)
    tools.import_asset_tasks([task(os.path.join(SRC, sp, 'textures', tn + s + '.png'), DST) for s in SETTINGS])
    for s, (srgb, comp) in SETTINGS.items():
        t = unreal.load_asset('%s/%s%s' % (DST, tn, s)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if 'Normal' in s: t.set_editor_property('flip_green_channel', False)
        EAL.save_loaded_asset(t)
    tools.import_asset_tasks([task(os.path.join(SRC, sp, mesh + '.fbx'), DST, fbx_ui())])
    master = make_master('M_LP2CorruptGround' if sp == 'CorruptPatch' else ('M_LP2FoliageGlow' if emis else 'M_LP2Foliage'), DST + '/' + tn, sp != 'CorruptPatch', emis)
    MI = '%s/MI_%s' % (DST, mesh[3:])
    mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_' + mesh[3:], DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, master)
    for pn, s in (('BaseColor', '_BaseColor'), ('ORM', '_ORM'), ('Normal', '_Normal_DirectX')) + ((('Emissive', '_Emissive'),) if emis else ()):
        MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s%s' % (DST, tn, s)))
    EAL.save_asset(MI)
    sm = unreal.load_asset('%s/%s' % (DST, mesh)); sm.set_material(0, mi)
    opts = unreal.EditorScriptingMeshReductionOptions()
    opts.reduction_settings = [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0), unreal.EditorScriptingMeshReductionSettings(0.5, 0.2), unreal.EditorScriptingMeshReductionSettings(0.2, 0.08)]
    opts.auto_compute_lod_screen_size = False; SML.set_lods(sm, opts)
    SML.remove_collisions(sm)       # flowers don't collide
    EAL.save_loaded_asset(sm)
    unreal.log('Flora kit: %s imported to %s' % (sp, DST))
