# Zombie variations v2 (#199; TGA, 2026-10-30): import into UE 5.3. Original procedural work (tools/tga/zombiev2).
# Run in the editor:   py "<repo>/assets/tga/ZombieV2/import_zombiev2_ue.py"      (re-running re-imports the same files)
# Creates under /Game/CastleDefender/Characters/Enemies/ZombieV2:
#   SK_ZombieV2_<Variant> for Bloated / Burnt / Hollow / Infected / Soldier / Crawler, all on ONE skeleton
#     SK_ZombieV2_Skeleton (SK_Zombie's Mixamo bone names, #200) which is added to SK_Zombie_Skeleton's
#     Compatible Skeletons so the existing zombie anims / AnimBP play on the new bodies.
#   A_ZombieV2_Crawl / A_ZombieV2_CrawlDeath (crawler only; from SK_ZombieV2_Crawler.fbx)
#   M_ZombieV2 (BaseColor / ORM / Normal / Emissive mask + Tint, TintAmount, Wetness, HitT, GlowColor, GlowIntensity:
#     the zombie skin master's parameter names, so BP_ZombieVariety / hit flash code can drive it)
#   MI_ZombieV2_<Variant>_<Skin> for skins Pale / Dark / Realm (18 instances); mesh slot 0 defaults to _Pale.
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Characters/Enemies/ZombieV2'
OLD_SKEL = '/Game/CastleDefender/Characters/Enemies/Zombie/SK_Zombie_Skeleton'
VARS = ('Bloated', 'Burnt', 'Hollow', 'Infected', 'Soldier', 'Crawler')
SKINS = ('Pale', 'Dark', 'Realm')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

TEX = []
for v in VARS:
    TEX += [('T_ZombieV2_%s_N' % v, False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
    for s in SKINS:
        TEX += [('T_ZombieV2_%s_%s_BC' % (v, s), True, unreal.TextureCompressionSettings.TC_DEFAULT),
                ('T_ZombieV2_%s_%s_ORM' % (v, s), False, unreal.TextureCompressionSettings.TC_MASKS)]
        if os.path.exists(os.path.join(SRC, 'textures', 'T_ZombieV2_%s_%s_E.png' % (v, s))):
            TEX += [('T_ZombieV2_%s_%s_E' % (v, s), False, unreal.TextureCompressionSettings.TC_GRAYSCALE)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

SKEL = DST + '/SK_ZombieV2_Skeleton'
for i, v in enumerate(VARS):
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = True; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    f.import_materials = False; f.import_textures = False; f.import_animations = (v == 'Crawler'); f.create_physics_asset = True
    f.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    if EAL.does_asset_exist(SKEL): f.skeleton = unreal.load_asset(SKEL)      # every variant shares the first one's skeleton
    tools.import_asset_tasks([task(os.path.join(SRC, 'SK_ZombieV2_%s.fbx' % v), f)])
    if not EAL.does_asset_exist(SKEL):                                        # first import names it SK_ZombieV2_<Var>_Skeleton
        first = '%s/SK_ZombieV2_%s_Skeleton' % (DST, v)
        if EAL.does_asset_exist(first): EAL.rename_asset(first, SKEL)
for path in EAL.list_assets(DST, recursive=False):                            # FBX takes -> A_ZombieV2_<Clip>
    name = path.split('.')[-1]
    if 'A_ZombieV2_' in name and not name.startswith('A_ZombieV2_'):
        new = DST + '/' + name[name.index('A_ZombieV2_'):]
        if EAL.does_asset_exist(new): EAL.delete_asset(new)
        EAL.rename_asset(path.split('.')[0], new)

# let the existing zombie anims play on the v2 skeleton (and back): Compatible Skeletons, both ways
try:
    for a, b in ((SKEL, OLD_SKEL), (OLD_SKEL, SKEL)):
        sa = unreal.load_asset(a); cs = list(sa.get_editor_property('compatible_skeletons'))
        if not any(str(c).endswith(b.split('/')[-1]) for c in cs):
            cs.append(unreal.load_asset(b)); sa.set_editor_property('compatible_skeletons', cs); EAL.save_loaded_asset(sa)
except Exception as e:
    unreal.log_warning('Compatible Skeletons: add SK_Zombie_Skeleton <-> SK_ZombieV2_Skeleton by hand in each Skeleton\'s details (%s)' % e)

MASTER = DST + '/M_ZombieV2'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_ZombieV2', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250, DST + '/T_ZombieV2_Hollow_Pale_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, DST + '/T_ZombieV2_Hollow_Pale_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, DST + '/T_ZombieV2_Hollow_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    emt = p(unreal.MaterialExpressionTextureSampleParameter2D, 'GlowTex', -1100, 800, DST + '/T_ZombieV2_Hollow_Realm_E', unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    hit = p(unreal.MaterialExpressionScalarParameter, 'HitT', -1100, -560); hit.set_editor_property('default_value', 0.0)
    gcol = p(unreal.MaterialExpressionVectorParameter, 'GlowColor', -1100, 1000); gcol.set_editor_property('default_value', unreal.LinearColor(1.0, 0.35, 0.75, 1))
    gint = p(unreal.MaterialExpressionScalarParameter, 'GlowIntensity', -1100, 1100); gint.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.75)     # wet skin darkens a little
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.25); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    flash = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, -520)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -700, -620); col.set_editor_property('constant', unreal.LinearColor(4.0, 0.25, 0.1, 1))
    MEL.connect_material_expressions(col, '', flash, 'A'); MEL.connect_material_expressions(hit, '', flash, 'B')
    g1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, 900)
    MEL.connect_material_expressions(emt, 'R', g1, 'A'); MEL.connect_material_expressions(gcol, '', g1, 'B')
    g2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, 950)
    MEL.connect_material_expressions(g1, '', g2, 'A'); MEL.connect_material_expressions(gint, '', g2, 'B')
    em = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -300, -450)
    MEL.connect_material_expressions(flash, '', em, 'A'); MEL.connect_material_expressions(g2, '', em, 'B')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(em, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    m.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

GLOW = {'Burnt': (unreal.LinearColor(1.0, 0.35, 0.08, 1), 6.0), 'Infected': (unreal.LinearColor(1.0, 0.35, 0.75, 1), 5.0)}
for v in VARS:
    for s in SKINS:
        name = 'MI_ZombieV2_%s_%s' % (v, s); MI = DST + '/' + name
        mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
        MEL.set_material_instance_texture_parameter_value(mi, 'BaseColorTex', unreal.load_asset('%s/T_ZombieV2_%s_%s_BC' % (DST, v, s)))
        MEL.set_material_instance_texture_parameter_value(mi, 'ORMTex', unreal.load_asset('%s/T_ZombieV2_%s_%s_ORM' % (DST, v, s)))
        MEL.set_material_instance_texture_parameter_value(mi, 'NormalTex', unreal.load_asset('%s/T_ZombieV2_%s_N' % (DST, v)))
        E = '%s/T_ZombieV2_%s_%s_E' % (DST, v, s)
        if EAL.does_asset_exist(E):
            MEL.set_material_instance_texture_parameter_value(mi, 'GlowTex', unreal.load_asset(E))
            c, k = GLOW.get(v, (unreal.LinearColor(1.0, 0.35, 0.75, 1), 3.0))      # realm skin: pink veins + eyes
            MEL.set_material_instance_vector_parameter_value(mi, 'GlowColor', c); MEL.set_material_instance_scalar_parameter_value(mi, 'GlowIntensity', k)
        if v == 'Bloated': MEL.set_material_instance_scalar_parameter_value(mi, 'Wetness', 0.6)       # drowned
        EAL.save_asset(MI)
    sk = unreal.load_asset('%s/SK_ZombieV2_%s' % (DST, v))
    mats = sk.get_editor_property('materials')
    if mats: mats[0].set_editor_property('material_interface', unreal.load_asset('%s/MI_ZombieV2_%s_Pale' % (DST, v))); sk.set_editor_property('materials', mats)
    EAL.save_loaded_asset(sk)
unreal.log('Zombie v2 imported: %s (6 bodies x 3 skins on SK_ZombieV2_Skeleton). Spawn weights: README.' % DST)
