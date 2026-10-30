# Realm wasp (#156 tentacle realm: giant stinging insects; TGA, 2026-10-30): import into UE 5.3.
# Original procedural work, so it's all in this repo. Run in the editor:
#   py "<repo>/assets/tga/RealmWasp/import_realmwasp_ue.py"
# Creates (re-running re-imports the same files):
#   /Game/CastleDefender/Characters/Enemies/RealmWasp/SK_RealmWasp (+ _Skeleton, _PhysicsAsset) and 5 anims from the FBX:
#       A_RealmWasp_Hover / _Fly / _Dive (loops), _Sting, _Death (one-shots)
#   .../M_RealmWasp_Body   BaseColor / ORM / Normal + Tint, TintAmount, Wetness, HitT (the zombie skin master's names, so
#                          the per-spawn tint and hit-flash code can drive it)
#   .../M_RealmWasp_Wings  two-sided, masked with dithered opacity (the membrane alpha is 0.3-0.5); WingBlur 0..1 fades the
#                          membrane while it beats fast, so the wings read as a blur in flight
#   .../MI_RealmWasp_Body_Ember / _Blight and MI_RealmWasp_Wings_Ember / _Blight
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Characters/Enemies/RealmWasp'
SKINS = ('Ember', 'Blight')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

# ---- textures ----
TEX = [('T_RealmWasp_Body_%s_BC' % s, True, unreal.TextureCompressionSettings.TC_DEFAULT) for s in SKINS]
TEX += [('T_RealmWasp_Body_%s_ORM' % s, False, unreal.TextureCompressionSettings.TC_MASKS) for s in SKINS]
TEX += [('T_RealmWasp_Wings_%s_BCA' % s, True, unreal.TextureCompressionSettings.TC_DEFAULT) for s in SKINS]
TEX += [('T_RealmWasp_Body_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

# ---- skeletal mesh + animations (new skeleton + physics asset) ----
f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = True; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
f.import_materials = False; f.import_textures = False; f.import_animations = True; f.create_physics_asset = True
f.skeletal_mesh_import_data.import_morph_targets = False
f.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
f.anim_sequence_import_data.set_editor_property('import_bone_tracks', True)
tools.import_asset_tasks([task(os.path.join(SRC, 'SK_RealmWasp.fbx'), f)])
# FBX takes arrive as SK_RealmWasp_Anim_Armature_A_RealmWasp_<Clip>: rename them to A_RealmWasp_<Clip>
for path in EAL.list_assets(DST, recursive=False):
    name = path.split('.')[-1]
    if 'A_RealmWasp_' in name and not name.startswith('A_RealmWasp_'):
        new = DST + '/' + name[name.index('A_RealmWasp_'):]
        if EAL.does_asset_exist(new): EAL.delete_asset(new)
        EAL.rename_asset(path.split('.')[0], new)

def param(m, cls, name, x, y, tex=None, sampler=None):
    e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
    if tex: e.set_editor_property('texture', unreal.load_asset(tex))
    if sampler: e.set_editor_property('sampler_type', sampler)
    return e

# ---- body master ----
BODY = DST + '/M_RealmWasp_Body'
if not EAL.does_asset_exist(BODY):
    m = tools.create_asset('M_RealmWasp_Body', DST, unreal.Material, unreal.MaterialFactoryNew())
    bc = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -1100, -250, DST + '/T_RealmWasp_Body_Ember_BC')
    orm = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -1100, 150, DST + '/T_RealmWasp_Body_Ember_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -1100, 500, DST + '/T_RealmWasp_Body_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = param(m, unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = param(m, unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = param(m, unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    hit = param(m, unreal.MaterialExpressionScalarParameter, 'HitT', -1100, -560); hit.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    # wet chitin (Lagarde): slightly darker, gloss gain damped
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.8)
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.15); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    flash = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -520)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, -620); col.set_editor_property('constant', unreal.LinearColor(4.0, 0.25, 0.1, 1))
    MEL.connect_material_expressions(col, '', flash, 'A'); MEL.connect_material_expressions(hit, '', flash, 'B')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(flash, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    m.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(m); EAL.save_asset(BODY)

# ---- wings master: two-sided, masked, dithered opacity ----
WING = DST + '/M_RealmWasp_Wings'
if not EAL.does_asset_exist(WING):
    m = tools.create_asset('M_RealmWasp_Wings', DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED); m.set_editor_property('two_sided', True)
    m.set_editor_property('opacity_mask_clip_value', 0.5); m.set_editor_property('used_with_skeletal_mesh', True)
    t = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'WingTex', -1000, 0, DST + '/T_RealmWasp_Wings_Ember_BCA')
    blur = param(m, unreal.MaterialExpressionScalarParameter, 'WingBlur', -1000, 300); blur.set_editor_property('default_value', 0.0)
    # opacity = alpha * (1 - 0.6 * WingBlur), dithered so partial alpha works in a masked material
    k = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -750, 300); MEL.connect_material_expressions(blur, '', k, 'A'); k.set_editor_property('const_b', 0.6)
    om = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -600, 300); MEL.connect_material_expressions(k, '', om, '')
    a = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 200); MEL.connect_material_expressions(t, 'A', a, 'A'); MEL.connect_material_expressions(om, '', a, 'B')
    dith = MEL.create_material_expression(m, unreal.MaterialExpressionDitherTemporalAA, -250, 250)
    MEL.connect_material_expressions(a, '', dith, 'Alpha Threshold')
    rough = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 100); rough.set_editor_property('r', 0.3)
    MEL.connect_material_property(t, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(dith, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(m); EAL.save_asset(WING)

def mi(name, parent, tex):
    path = DST + '/' + name
    inst = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, unreal.load_asset(parent))
    for p, tn in tex.items(): MEL.set_material_instance_texture_parameter_value(inst, p, unreal.load_asset(DST + '/' + tn))
    EAL.save_asset(path); return inst
for s in SKINS:
    mi('MI_RealmWasp_Body_' + s, BODY, {'BaseColor': 'T_RealmWasp_Body_%s_BC' % s, 'ORM': 'T_RealmWasp_Body_%s_ORM' % s, 'Normal': 'T_RealmWasp_Body_N'})
    mi('MI_RealmWasp_Wings_' + s, WING, {'WingTex': 'T_RealmWasp_Wings_%s_BCA' % s})

# default look: Ember (slots by name: M_RealmWasp_Body, M_RealmWasp_Wings)
sk = unreal.load_asset(DST + '/SK_RealmWasp')
mats = sk.get_editor_property('materials')
for sm in mats:
    slot = str(sm.get_editor_property('material_slot_name'))
    if 'Wings' in slot: sm.set_editor_property('material_interface', unreal.load_asset(DST + '/MI_RealmWasp_Wings_Ember'))
    elif 'Body' in slot: sm.set_editor_property('material_interface', unreal.load_asset(DST + '/MI_RealmWasp_Body_Ember'))
sk.set_editor_property('materials', mats)
EAL.save_loaded_asset(sk)
unreal.log('Realm wasp imported: ' + DST + ' (2 skins, 5 anims). Next: BP_RealmWasp, see README.')
