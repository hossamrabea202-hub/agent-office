# Imports the seamless ground tiles into UE 5.3 and makes one master material + an MI per set.
#   py "<repo>/assets/laptop2/GroundKit/import_ground_ue.py" [Cobble Mud GrassDirt Corrupt]
# -> /Game/CastleDefender/Environment/Ground/<Set>/: T_Ground_<Set>_BaseColor / _ORM / _Normal_DirectX / _Height (+ _Emissive
#    for Corrupt), MI_Ground_<Set> of M_LP2Ground (Tiling in metres: 2 = one tile every 2 m, WetnessBoost, HeightScale for
#    displacement/blend, EmissiveBoost). Use the MIs on landscape layers (the layer blend reads _Height to blend by height)
#    or on ground meshes; the realm tile goes inside the #29 east gate.
import sys, os, unreal
SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = '/Game/CastleDefender/Environment/Ground'
SETS = ('Cobble', 'Mud', 'GrassDirt', 'Corrupt', 'CobbleMud'); pick = [a for a in sys.argv[1:] if a in SETS] or list(SETS)
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()

def import_tex(path, dst, srgb, kind=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dst; t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t]); a = unreal.load_asset(dst + '/' + os.path.splitext(os.path.basename(path))[0])
    a.set_editor_property('srgb', srgb)
    if kind == 'normal': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP); a.set_editor_property('flip_green_channel', False)
    if kind == 'masks': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    if kind == 'height': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_GRAYSCALE)
    a.set_editor_property('address_x', unreal.TextureAddress.TA_WRAP); a.set_editor_property('address_y', unreal.TextureAddress.TA_WRAP)
    EAL.save_asset(a.get_path_name()); return a

def master():
    path = ROOT + '/M_LP2Ground'
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    m = tools.create_asset('M_LP2Ground', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, pname, x, y, **props):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', pname)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    T = unreal.MaterialExpressionTextureSampleParameter2D
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1500, 0)
    xy = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1350, 0); xy.set_editor_property('r', True); xy.set_editor_property('g', True); xy.set_editor_property('b', False)
    MEL.connect_material_expressions(uv, '', xy, '')
    til = p(unreal.MaterialExpressionScalarParameter, 'TilingMetres', -1350, 150, default_value=2.0)
    cm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -1200, 150); cm.set_editor_property('const_b', 100.0); MEL.connect_material_expressions(til, '', cm, 'A')
    dv = MEL.create_material_expression(m, unreal.MaterialExpressionDivide, -1150, 0); MEL.connect_material_expressions(xy, '', dv, 'A'); MEL.connect_material_expressions(cm, '', dv, 'B')
    bc = p(T, 'BaseColor', -900, -300); orm = p(T, 'ORM', -900, 0, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(T, 'Normal', -900, 300, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL); hgt = p(T, 'Height', -900, 600, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    em = p(T, 'Emissive', -900, 900)
    for s in (bc, orm, nrm, hgt, em): MEL.connect_material_expressions(dv, '', s, 'UVs')
    MEL.connect_material_property(bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    wb = p(unreal.MaterialExpressionScalarParameter, 'WetnessBoost', -700, 100, default_value=0.0)
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionSubtract, -550, 60); MEL.connect_material_expressions(orm, 'G', rg, 'A'); MEL.connect_material_expressions(wb, '', rg, 'B')
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    eb = p(unreal.MaterialExpressionScalarParameter, 'EmissiveBoost', -700, 1000, default_value=4.0)
    emm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -550, 950); MEL.connect_material_expressions(em, 'RGB', emm, 'A'); MEL.connect_material_expressions(eb, '', emm, 'B')
    MEL.connect_material_property(emm, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    hs = p(unreal.MaterialExpressionScalarParameter, 'HeightScale', -700, 700, default_value=0.0)    # > 0: Nanite / tessellation displacement cm
    MEL.recompile_material(m); EAL.save_asset(m.get_path_name()); return m

M = master()
for s in pick:
    d = os.path.join(SRC, s, 'textures'); dst = ROOT + '/' + s
    bc = import_tex(os.path.join(d, 'T_Ground_%s_BaseColor.png' % s), dst, True)
    orm = import_tex(os.path.join(d, 'T_Ground_%s_ORM.png' % s), dst, False, 'masks')
    nm = import_tex(os.path.join(d, 'T_Ground_%s_Normal_DirectX.png' % s), dst, False, 'normal')
    hp = os.path.join(d, 'T_Ground_%s_Height.png' % s); hg = import_tex(hp, dst, False, 'height') if os.path.exists(hp) else None
    ep = os.path.join(d, 'T_Ground_%s_Emissive.png' % s); em = import_tex(ep, dst, True) if os.path.exists(ep) else None
    mi_path = dst + '/MI_Ground_' + s
    mi = unreal.load_asset(mi_path) if EAL.does_asset_exist(mi_path) else tools.create_asset('MI_Ground_' + s, dst, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, M)
    for n, t in (('BaseColor', bc), ('ORM', orm), ('Normal', nm), ('Height', hg), ('Emissive', em)):
        if t: MEL.set_material_instance_texture_parameter_value(mi, n, t)
    if em: MEL.set_material_instance_scalar_parameter_value(mi, 'EmissiveBoost', 4.0)
    EAL.save_asset(mi.get_path_name()); unreal.log('GroundKit %s -> %s' % (s, dst))
