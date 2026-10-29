# Flesh Brute (new heavy enemy; TGA, 2026-10-29): import into UE 5.3.
# Model: CGTrader "Flesh Mutant Monster" by andrey-ryzhko, Royalty Free licence. The FBX and textures are LICENSED, so
# they are NOT in this repo: the owner copies FleshBrute_PRIVATE.zip to SRC below (unzipped). Only this script, the
# README and preview renders are public.
# Run in the editor:  py "<repo>/assets/tga/FleshBrute/import_fleshbrute_ue.py"
# Creates (re-running re-imports the same files):
#   /Game/CastleDefender/Characters/Enemies/FleshBrute/SK_FleshBrute (+ _Skeleton, _PhysicsAsset)
#   .../M_FleshBrute       master: BaseColor / ORM / Normal + Tint, TintAmount, Wetness, HitT (same names as the zombie
#                          skin master, so BP_ZombieVariety's per-spawn tint and the hit flash can drive it)
#   .../MI_FleshBrute_<Skin>_P01 / _P02 for Clean, Bloody, Rotten, Charred, Drowned (slot 0 = P01 body, slot 1 = P02)
# The UE 5.8 package that ships with the model can't be opened in 5.3, so the animations come from a retarget (README).
import os
import unreal

SRC = r'C:\Unreal Backups\Castle Defender\Tools\PrivateExports\2026-10-29\flesh-brute'
DST = '/Game/CastleDefender/Characters/Enemies/FleshBrute'
SKINS = ('Clean', 'Bloody', 'Rotten', 'Charred', 'Drowned')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
if not os.path.isfile(os.path.join(SRC, 'SK_FleshBrute.fbx')):
    raise RuntimeError('Flesh Brute: unzip FleshBrute_PRIVATE.zip to ' + SRC + ' first')

def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

# ---- textures ----
TEX = [('T_FleshBrute_%s_P%s_BC' % (s, p), True, unreal.TextureCompressionSettings.TC_DEFAULT) for s in SKINS for p in ('01', '02')]
TEX += [('T_FleshBrute_%s_P%s_ORM' % (s, p), False, unreal.TextureCompressionSettings.TC_MASKS) for s in SKINS for p in ('01', '02')]
TEX += [('T_FleshBrute_P%s_N' % p, False, unreal.TextureCompressionSettings.TC_NORMALMAP) for p in ('01', '02')]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

# ---- skeletal mesh (new skeleton + physics asset; no animations in the FBX) ----
f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = True; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
f.import_materials = False; f.import_textures = False; f.import_animations = False; f.create_physics_asset = True
f.skeletal_mesh_import_data.import_morph_targets = False
f.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
tools.import_asset_tasks([task(os.path.join(SRC, 'SK_FleshBrute.fbx'), f)])

# ---- master material ----
MASTER = DST + '/M_FleshBrute'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_FleshBrute', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -1100, -250, DST + '/T_FleshBrute_Clean_P01_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -1100, 150, DST + '/T_FleshBrute_Clean_P01_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -1100, 500, DST + '/T_FleshBrute_P01_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    hit = p(unreal.MaterialExpressionScalarParameter, 'HitT', -1100, -560); hit.set_editor_property('default_value', 0.0)
    # tint: lerp(BaseColor, BaseColor * Tint, TintAmount)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    # wet flesh: a little darker, much glossier
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.7)
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.18)
    MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    # hit flash: red emissive pulse driven by HitT (0..1)
    flash = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -520)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, -620)
    col.set_editor_property('constant', unreal.LinearColor(4.0, 0.25, 0.1, 1))
    MEL.connect_material_expressions(col, '', flash, 'A'); MEL.connect_material_expressions(hit, '', flash, 'B')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(flash, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    m.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

for s in SKINS:
    for pn in ('01', '02'):
        name = 'MI_FleshBrute_%s_P%s' % (s, pn); MI = DST + '/' + name
        mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
        MEL.set_material_instance_texture_parameter_value(mi, 'BaseColor', unreal.load_asset('%s/T_FleshBrute_%s_P%s_BC' % (DST, s, pn)))
        MEL.set_material_instance_texture_parameter_value(mi, 'ORM', unreal.load_asset('%s/T_FleshBrute_%s_P%s_ORM' % (DST, s, pn)))
        MEL.set_material_instance_texture_parameter_value(mi, 'Normal', unreal.load_asset('%s/T_FleshBrute_P%s_N' % (DST, pn)))
        if s == 'Drowned': MEL.set_material_instance_scalar_parameter_value(mi, 'Wetness', 0.5)
        EAL.save_asset(MI)

# default look on the mesh: Clean (slot order from the FBX: part_01 body, part_02)
sk = unreal.load_asset(DST + '/SK_FleshBrute')
mats = sk.get_editor_property('materials')
for i, pn in enumerate(('01', '02')):
    if i < len(mats):
        mats[i].set_editor_property('material_interface', unreal.load_asset('%s/MI_FleshBrute_Clean_P%s' % (DST, pn)))
sk.set_editor_property('materials', mats)
EAL.save_loaded_asset(sk)
unreal.log('Flesh Brute imported: ' + DST + ' (5 skins). Next: retarget the zombie anims, see README.')
