# Obsidian Sovereign shins / greaves (L/R, AAA by checkking, 2026-10-28): import into UE 5.3 and set up the material.
# Run in the editor:  py "<repo>/assets/checkking/Obsidian-Sovereign/Shins/import_shins_ue.py"
# Creates (re-running re-imports the same files):
#   /Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/M_ObsidianSovereign        (shared master; made here if the chest import hasn't made it)
#   /Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Shins/SM_ObsidianSovereign_Shins_L/_R + 3 textures + MI (both sides share one MI)
import os
import unreal

REPO = r''   # set to your office-repo checkout if the editor doesn't set __file__
try:
    SRC = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SRC = os.path.join(REPO, 'assets', 'checkking', 'Obsidian-Sovereign', 'Shins')
ROOT = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign'
DST = ROOT + '/Shins'
TN = 'T_ObsidianSovereign_Shins'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, dest, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

# ---- textures ----
tex = {
    TN + '_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
    TN + '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
    TN + '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP),
}
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png'), DST) for n in tex])
for n, (srgb, comp) in tex.items():
    t = unreal.load_asset(f'{DST}/{n}')
    t.modify()   # without it the settings don't stick on a re-import
    t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if 'Normal' in n: t.set_editor_property('flip_green_channel', False)
    EAL.save_loaded_asset(t)

# ---- meshes (static, in the set frame; fitting + skinning to ShadowknightUE_SK comes later, like the chest) ----
def fbx_ui():
    fbx = unreal.FbxImportUI()
    fbx.import_mesh = True; fbx.import_as_skeletal = False; fbx.import_materials = False; fbx.import_textures = False
    fbx.static_mesh_import_data.combine_meshes = True
    fbx.static_mesh_import_data.generate_lightmap_u_vs = False
    fbx.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return fbx
tools.import_asset_tasks([task(os.path.join(SRC, f'SM_ObsidianSovereign_Shins_{s}.fbx'), DST, fbx_ui()) for s in ('L', 'R')])

# ---- shared master material (same graph as the chest import; only made if missing) ----
MASTER = ROOT + '/M_ObsidianSovereign'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_ObsidianSovereign', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex_default=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex_default: e.set_editor_property('texture', unreal.load_asset(tex_default))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -700, -200, f'{DST}/{TN}_BaseColor')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -700, 100, f'{DST}/{TN}_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -700, 400, f'{DST}/{TN}_Normal_DirectX', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -700, -420); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, -250)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    rmul = p(unreal.MaterialExpressionScalarParameter, 'RoughnessScale', -700, 250); rmul.set_editor_property('default_value', 1.0)
    rm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, 120)
    MEL.connect_material_expressions(orm, 'G', rm, 'A'); MEL.connect_material_expressions(rmul, '', rm, 'B')
    MEL.connect_material_property(mul, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rm, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

# ---- one instance, used by both sides (the right greave is a mirror sharing the same UVs) ----
MI = f'{DST}/MI_ObsidianSovereign_Shins'
mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_ObsidianSovereign_Shins', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
for pn, tn in (('BaseColor', 'BaseColor'), ('ORM', 'ORM'), ('Normal', 'Normal_DirectX')):
    MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset(f'{DST}/{TN}_{tn}'))
EAL.save_asset(MI)
for s in ('L', 'R'):
    sm = unreal.load_asset(f'{DST}/SM_ObsidianSovereign_Shins_{s}')
    sm.set_material(0, mi)
    EAL.save_loaded_asset(sm)
unreal.log('Obsidian Sovereign shins imported: ' + DST)
