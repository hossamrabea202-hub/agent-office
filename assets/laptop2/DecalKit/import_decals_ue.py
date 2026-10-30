# Imports the decal kit into UE 5.3 and makes one deferred-decal master + an MI per decal.
#   py "<repo>/assets/laptop2/DecalKit/import_decals_ue.py"
# -> /Game/CastleDefender/Environment/Decals/<Name>/: T_Decal_<Name>_BaseColor (alpha = opacity), _ORM, _Normal_DirectX,
#    MI_Decal_<Name> of M_LP2Decal (DBuffer Translucent Color,Normal,Roughness; params Opacity, Tint, NormalStrength).
#    Place with DecalActor: blood under kills (BP: spawn MI_Decal_BloodSplatA/B at death, size 80-150 cm, random yaw, fade
#    after 90 s), mud along paths and at the gate, moss on the north side of walls and at the base of towers, scorch
#    under the campfire / brazier and where fire spears land, the crack across courtyard cobbles.
import sys, os, unreal
SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = '/Game/CastleDefender/Environment/Decals'
NAMES = ('BloodSplatA', 'BloodSplatB', 'BloodDrips', 'MudSplashA', 'MudSplashB', 'MossPatchA', 'MossPatchB', 'ScorchA', 'ScorchFlare', 'GroundCrack', 'Footprints', 'BoltHoles', 'MuzzleScorch')
pick = [a for a in sys.argv[1:] if a in NAMES] or list(NAMES)
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()

def import_tex(path, dst, srgb, kind=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dst; t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t]); a = unreal.load_asset(dst + '/' + os.path.splitext(os.path.basename(path))[0])
    a.set_editor_property('srgb', srgb)
    if kind == 'normal': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP); a.set_editor_property('flip_green_channel', False)
    if kind == 'masks': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    a.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); a.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    EAL.save_asset(a.get_path_name()); return a

def master():
    path = ROOT + '/M_LP2Decal'
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    m = tools.create_asset('M_LP2Decal', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('material_domain', unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    try: m.set_editor_property('decal_blend_mode', unreal.DecalBlendMode.DBM_DBUFFER_COLOR_NORMAL_ROUGHNESS)
    except Exception: pass
    def p(cls, pname, x, y, **props):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', pname)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    T = unreal.MaterialExpressionTextureSampleParameter2D
    bc = p(T, 'BaseColor', -900, -300); orm = p(T, 'ORM', -900, 0, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(T, 'Normal', -900, 300, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -900, -500, default_value=unreal.LinearColor(1, 1, 1, 1))
    op = p(unreal.MaterialExpressionScalarParameter, 'Opacity', -900, 600, default_value=1.0)
    ns = p(unreal.MaterialExpressionScalarParameter, 'NormalStrength', -900, 500, default_value=1.0)
    cm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -300); MEL.connect_material_expressions(bc, 'RGB', cm, 'A'); MEL.connect_material_expressions(tint, '', cm, 'B')
    MEL.connect_material_property(cm, '', unreal.MaterialProperty.MP_BASE_COLOR)
    om = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 600); MEL.connect_material_expressions(bc, 'A', om, 'A'); MEL.connect_material_expressions(op, '', om, 'B')
    MEL.connect_material_property(om, '', unreal.MaterialProperty.MP_OPACITY)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    fl = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -600, 300)
    fl.set_editor_property('material_function', unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/FlattenNormal'))
    try:
        MEL.connect_material_expressions(nrm, 'RGB', fl, 'Normal'); om2 = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -750, 500); MEL.connect_material_expressions(ns, '', om2, '')
        MEL.connect_material_expressions(om2, '', fl, 'Flatness'); MEL.connect_material_property(fl, '', unreal.MaterialProperty.MP_NORMAL)
    except Exception:
        MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(m.get_path_name()); return m

M = master()
for n in pick:
    d = os.path.join(SRC, 'textures'); dst = ROOT + '/' + n
    bc = import_tex(os.path.join(d, 'T_Decal_%s_BaseColor.png' % n), dst, True)
    orm = import_tex(os.path.join(d, 'T_Decal_%s_ORM.png' % n), dst, False, 'masks')
    nm = import_tex(os.path.join(d, 'T_Decal_%s_Normal_DirectX.png' % n), dst, False, 'normal')
    mi_path = dst + '/MI_Decal_' + n
    mi = unreal.load_asset(mi_path) if EAL.does_asset_exist(mi_path) else tools.create_asset('MI_Decal_' + n, dst, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, M)
    for pn, t in (('BaseColor', bc), ('ORM', orm), ('Normal', nm)): MEL.set_material_instance_texture_parameter_value(mi, pn, t)
    EAL.save_asset(mi.get_path_name()); unreal.log('DecalKit %s -> %s' % (n, dst))
