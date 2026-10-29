# Siege barricade kit (#29 player boundaries; by laptop2, 2026-10-29): import into UE 5.3.
# Run in the editor:  py "<repo>/assets/laptop2/SiegeBarricadeKit/import_siegekit_ue.py"
# Creates (re-running re-imports the same files):
#   /Game/CastleDefender/Environment/Boundaries/SiegeKit/M_SiegeBarricade          shared master (BaseColor/ORM/Normal + Tint, Wetness)
#   .../SM_SiegeBarricade_Palisade, _Cheval, _Breach, _Watchtower  + their textures and MI_ instances
#   4 LODs each (100 / 50 / 25 / 10 %), simple box collision (blocks Pawn and Camera), lightmap UVs off
import os
import unreal

REPO = r''
try:
    SRC = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SRC = os.path.join(REPO, 'assets', 'laptop2', 'SiegeBarricadeKit')
DST = '/Game/CastleDefender/Environment/Boundaries/SiegeKit'
EAL, MEL, SML = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.EditorStaticMeshLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
ASSETS = ('Palisade', 'Cheval', 'Breach', 'Watchtower')

def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

# ---- textures ----
SETTINGS = {'_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
            '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
            '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', 'T_SiegeBarricade_%s%s.png' % (a, s))) for a in ASSETS for s in SETTINGS])
for a in ASSETS:
    for s, (srgb, comp) in SETTINGS.items():
        t = unreal.load_asset('%s/T_SiegeBarricade_%s%s' % (DST, a, s))
        t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if 'Normal' in s: t.set_editor_property('flip_green_channel', False)
        EAL.save_loaded_asset(t)

# ---- meshes ----
def fbx_ui():
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = False; f.import_materials = False; f.import_textures = False
    f.static_mesh_import_data.combine_meshes = True
    f.static_mesh_import_data.generate_lightmap_u_vs = False
    f.static_mesh_import_data.auto_generate_collision = False
    f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return f
tools.import_asset_tasks([task(os.path.join(SRC, 'SM_SiegeBarricade_%s.fbx' % a), fbx_ui()) for a in ASSETS])

# ---- master material ----
MASTER = DST + '/M_SiegeBarricade'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_SiegeBarricade', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    T0 = DST + '/T_SiegeBarricade_Palisade'
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -900, -200, T0 + '_BaseColor')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -900, 150, T0 + '_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -900, 450, T0 + '_Normal_DirectX', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -900, -420); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -900, 320); wet.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -250)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    # wet wood: darker and glossier (rain / fog damp), one slider for the level art
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -350, -250)
    MEL.connect_material_expressions(mul, '', dark, 'A')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, -120)
    MEL.connect_material_expressions(mul, '', half, 'A'); half.set_editor_property('const_b', 0.55)
    MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -350, 120)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.35)
    MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

for a in ASSETS:
    MI = '%s/MI_SiegeBarricade_%s' % (DST, a)
    mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_SiegeBarricade_' + a, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    for pn, s in (('BaseColor', '_BaseColor'), ('ORM', '_ORM'), ('Normal', '_Normal_DirectX')):
        MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/T_SiegeBarricade_%s%s' % (DST, a, s)))
    EAL.save_asset(MI)
    sm = unreal.load_asset('%s/SM_SiegeBarricade_%s' % (DST, a))
    sm.set_material(0, mi)
    # LODs for a prop seen mostly at 10-60 m (boundary rows): 100 / 50 / 25 / 10 %
    opts = unreal.EditorScriptingMeshReductionOptions()
    opts.reduction_settings = [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0), unreal.EditorScriptingMeshReductionSettings(0.5, 0.45),
                               unreal.EditorScriptingMeshReductionSettings(0.25, 0.2), unreal.EditorScriptingMeshReductionSettings(0.1, 0.06)]
    opts.auto_compute_lod_screen_size = False
    SML.set_lods(sm, opts)
    # simple collision: one box around the whole piece (blocks the hero and the camera without snagging on stakes)
    SML.remove_collisions(sm)
    SML.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.BOX)
    EAL.save_loaded_asset(sm)
unreal.log('#29 siege barricade kit imported: ' + DST)
