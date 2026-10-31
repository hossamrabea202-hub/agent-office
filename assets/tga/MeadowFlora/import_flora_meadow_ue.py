# Meadow flora kit for #352 / #351 (TGA, 2026-10-31): import into UE 5.3. Original procedural work (tools/tga/flora).
# Run in the editor:   py "<repo>/assets/tga/MeadowFlora/import_flora_meadow_ue.py"     DRY_RUN = True only lists what it would do.
# Creates under /Game/CastleDefender/Environment/Flora/Meadow (names are what adjustedfilm's place_meadow_ue.py looks for):
#   SM_Flower_Daisy|Poppy|Yarrow|Cornflower_A/B/C, SM_Bush_Hawthorn|Hazel_A/B, SM_Fern_Bracken_A     (pivot = base on the ground)
#   4 LODs each (LOD3 = 2 crossed impostor cards), T_MeadowFlora (2K atlas) + T_MeadowCards (2K: leaf sprays + impostors, alpha),
#   M_MeadowFlora (opaque) / M_MeadowCards (masked), both Two Sided Foliage, subsurface = BaseColor x SubsurfaceAmount, wind:
#   SimpleGrassWind with weight (1 - R)^2 + leaf flutter along the normal (B mask, G phase). Vertex colour: R stiffness, G phase, B flutter.
# No collision (walk-through foliage; give bushes a capsule on the scatter if gameplay wants it). Nanite off (masked cards).
import os
import unreal

DRY_RUN = True
SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Environment/Flora/Meadow'
FBX = os.path.join(SRC, 'fbx')
MESHES = sorted(os.path.splitext(f)[0] for f in os.listdir(FBX) if f.endswith('.fbx') and '_LOD' not in f)
SCREEN = {'SM_Bush_': (1.0, 0.45, 0.2, 0.07), 'SM_Fern_': (1.0, 0.35, 0.15, 0.05), 'SM_Flower_': (1.0, 0.25, 0.1, 0.035)}
log = lambda m: unreal.log('[flora352%s] %s' % (' DRY' if DRY_RUN else '', m))
if DRY_RUN:
    log('would import %d meshes x 4 LODs %s, 6 textures and 2 materials into %s' % (len(MESHES), MESHES, DST)); raise SystemExit
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
TEX = []
for s in ('Flora', 'Cards'):
    TEX += [('T_Meadow%s_BC' % s, True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_Meadow%s_ORM' % s, False, unreal.TextureCompressionSettings.TC_MASKS),
            ('T_Meadow%s_N' % s, False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

def P(m, cls, name, x, y, tex=None, sampler=None):
    e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
    if tex: e.set_editor_property('texture', unreal.load_asset(tex))
    if sampler: e.set_editor_property('sampler_type', sampler)
    return e
def E(m, cls, x, y): return MEL.create_material_expression(m, cls, x, y)
def S(m, name, v, x, y): e = P(m, unreal.MaterialExpressionScalarParameter, name, x, y); e.set_editor_property('default_value', v); return e
C = MEL.connect_material_expressions
def foliage(name, atlas, masked):
    path = '%s/%s' % (DST, name)
    if EAL.does_asset_exist(path): return
    m = tools.create_asset(name, DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWOSIDED_FOLIAGE); m.set_editor_property('two_sided', True)
    if masked:
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED); m.set_editor_property('opacity_mask_clip_value', 0.4)
    bc = P(m, unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -300, '%s/%s_BC' % (DST, atlas))
    orm = P(m, unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 50, '%s/%s_ORM' % (DST, atlas), unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = P(m, unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 380, '%s/%s_N' % (DST, atlas), unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = P(m, unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -520); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    col = E(m, unreal.MaterialExpressionMultiply, -800, -380); C(bc, 'RGB', col, 'A'); C(tint, '', col, 'B')
    ssa = S(m, 'SubsurfaceAmount', 0.6, -800, -200); ssc = E(m, unreal.MaterialExpressionMultiply, -550, -250); C(col, '', ssc, 'A'); C(ssa, '', ssc, 'B')
    MEL.connect_material_property(col, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(ssc, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    if masked: MEL.connect_material_property(bc, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    # wind: SimpleGrassWind, weight = (1 - R)^2, + flutter = normal * sin(time * speed + G) * B * amount
    vc = E(m, unreal.MaterialExpressionVertexColor, -1100, 800)
    om = E(m, unreal.MaterialExpressionOneMinus, -850, 760); C(vc, 'R', om, '')
    wt = E(m, unreal.MaterialExpressionMultiply, -650, 760); C(om, '', wt, 'A'); C(om, '', wt, 'B')
    tm = E(m, unreal.MaterialExpressionTime, -1100, 1000); fs = S(m, 'FlutterSpeed', 2.5, -1100, 1080)
    ts = E(m, unreal.MaterialExpressionMultiply, -850, 1000); C(tm, '', ts, 'A'); C(fs, '', ts, 'B')
    ph = E(m, unreal.MaterialExpressionAdd, -650, 1000); C(ts, '', ph, 'A'); C(vc, 'G', ph, 'B')
    sn = E(m, unreal.MaterialExpressionSine, -500, 1000); C(ph, '', sn, '')
    fa = S(m, 'FlutterAmount', 0.8, -500, 1120)                                 # cm
    f1 = E(m, unreal.MaterialExpressionMultiply, -350, 1000); C(sn, '', f1, 'A'); C(vc, 'B', f1, 'B')
    f2 = E(m, unreal.MaterialExpressionMultiply, -220, 1060); C(f1, '', f2, 'A'); C(fa, '', f2, 'B')
    vn = E(m, unreal.MaterialExpressionVertexNormalWS, -350, 1200)
    f3 = E(m, unreal.MaterialExpressionMultiply, -100, 1100); C(f2, '', f3, 'A'); C(vn, '', f3, 'B')
    wind = E(m, unreal.MaterialExpressionMaterialFunctionCall, -100, 800)
    wind.set_editor_property('material_function', unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/SimpleGrassWind'))
    wi = S(m, 'WindIntensity', 0.25, -500, 640); ws = S(m, 'WindSpeed', 0.15, -500, 700)
    C(wi, '', wind, 'WindIntensity'); C(wt, '', wind, 'WindWeight'); C(ws, '', wind, 'WindSpeed'); C(f3, '', wind, 'AdditionalWPO')
    MEL.connect_material_property(wind, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    MEL.recompile_material(m); EAL.save_asset(path)
foliage('M_MeadowFlora', 'T_MeadowFlora', False); foliage('M_MeadowCards', 'T_MeadowCards', True)
MIS = {}
for nm, par in (('MI_MeadowFlora', 'M_MeadowFlora'), ('MI_MeadowCards', 'M_MeadowCards')):
    path = '%s/%s' % (DST, nm)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset(nm, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset('%s/%s' % (DST, par))); EAL.save_asset(path); MIS[par] = mi
f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
f.import_materials = False; f.import_textures = False
d = f.static_mesh_import_data; d.combine_meshes = True; d.auto_generate_collision = False; d.generate_lightmap_u_vs = False
d.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE                     # wind masks
d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS  # bent normals on the cards
tools.import_asset_tasks([task(os.path.join(FBX, n + '.fbx'), f) for n in MESHES])
for n in MESHES:
    sm = unreal.load_asset('%s/%s' % (DST, n))
    if not sm: log('WARNING %s did not import' % n); continue
    scr = next(v for k, v in SCREEN.items() if n.startswith(k))
    o = unreal.EditorScriptingMeshReductionOptions(); o.set_editor_property('auto_compute_lod_screen_size', False)
    o.set_editor_property('reduction_settings', [unreal.EditorScriptingMeshReductionSettings(1.0, scr[0])] +
                          [unreal.EditorScriptingMeshReductionSettings(0.5, s_) for s_ in scr[1:]])
    sub.set_lods(sm, o)                                                          # 4 LOD slots with our screen sizes ...
    for lod in (1, 2, 3):                                                        # ... then our hand-built LODs replace the auto reductions
        if sub.import_lod(sm, lod, os.path.join(FBX, '%s_LOD%d.fbx' % (n, lod))) < 0: log('WARNING %s LOD%d failed to import' % (n, lod))
    for i, slot in enumerate(sm.get_editor_property('static_materials')):
        key = str(slot.get_editor_property('material_slot_name'))
        if key in MIS: sm.set_material(i, MIS[key])
        else: log('slot %s on %s has no MI' % (key, n))
    sub.remove_collisions(sm)
    bs = sm.get_editor_property('body_setup')
    if bs: bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    EAL.save_loaded_asset(sm)
    log('%s: %d LODs, screen sizes %s' % (n, sub.get_lod_count(sm), [round(x, 3) for x in sub.get_lod_screen_sizes(sm)]))
log('meadow flora imported: %d meshes in %s (README: assets/tga/MeadowFlora/README.md)' % (len(MESHES), DST))
