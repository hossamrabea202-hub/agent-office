# checkking medieval weapon kit: import every weapon in this folder into UE 5.3 (safe to re-run; re-imports replace).
#   py "<repo>/assets/checkking/Weapons/import_weapons_ue.py"
# For each <Name>/ with SM_CK_<Name>.fbx: /Game/CastleDefender/Weapons/CK/<Name>/ gets the static mesh, BaseColor (sRGB),
# ORM (masks: R AO, G roughness, B metallic), Normal_DirectX, and MI_CK_<Name> on the shared master M_CK_Weapon
# (same graph as M_ObsidianSovereign: BaseColor x Tint, ORM, Normal, RoughnessScale). Nothing live is touched.
# Writes import_weapons.txt next to itself.
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Game/CastleDefender/Weapons/CK'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

def task(path, dest, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

def fbx_ui():
    fbx = unreal.FbxImportUI()
    fbx.import_mesh = True; fbx.import_as_skeletal = False; fbx.import_materials = False; fbx.import_textures = False
    fbx.static_mesh_import_data.combine_meshes = True
    fbx.static_mesh_import_data.generate_lightmap_u_vs = True
    fbx.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return fbx

MASTER = ROOT + '/M_CK_Weapon'
def make_master(first):
    m = tools.create_asset('M_CK_Weapon', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex_default=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex_default: e.set_editor_property('texture', unreal.load_asset(tex_default))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -700, -200, first + '_BaseColor')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -700, 100, first + '_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -700, 400, first + '_Normal_DirectX', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
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
    MEL.recompile_material(m); EAL.save_asset(MASTER); log.append('made ' + MASTER)

for name in sorted(os.listdir(SRC)):
    d = os.path.join(SRC, name); fbx = os.path.join(d, 'SM_CK_%s.fbx' % name)
    if not os.path.isfile(fbx): continue
    DST = '%s/%s' % (ROOT, name); TN = 'T_CK_' + name
    tex = {TN + '_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
           TN + '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
           TN + '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
    tools.import_asset_tasks([task(os.path.join(d, 'textures', n + '.png'), DST) for n in tex])
    for n, (srgb, comp) in tex.items():
        t = unreal.load_asset('%s/%s' % (DST, n)); t.modify()
        t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if 'Normal' in n: t.set_editor_property('flip_green_channel', False)
        EAL.save_loaded_asset(t)
    tools.import_asset_tasks([task(fbx, DST, fbx_ui())])
    if not EAL.does_asset_exist(MASTER): make_master('%s/%s' % (DST, TN))
    MI = '%s/MI_CK_%s' % (DST, name)
    mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_CK_' + name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    for pn, tn in (('BaseColor', 'BaseColor'), ('ORM', 'ORM'), ('Normal', 'Normal_DirectX')):
        MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s_%s' % (DST, TN, tn)))
    EAL.save_asset(MI)
    sm = unreal.load_asset('%s/SM_CK_%s' % (DST, name)); sm.set_material(0, mi); EAL.save_loaded_asset(sm)
    b = sm.get_bounding_box(); log.append('%s: %s tris-ish bounds z %.1f..%.1f cm' % (name, sm.get_num_triangles(0), b.min.z, b.max.z))

out = 'checkking weapon kit import\n' + '\n'.join(log)
open(os.path.join(SRC, 'import_weapons.txt'), 'w').write(out)
unreal.log(out)
