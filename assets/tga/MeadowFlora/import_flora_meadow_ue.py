# Meadow flora kit for #352 / #351 (TGA, 2026-10-31): import into UE 5.3. Original procedural work (tools/tga/flora).
# Run in the editor:   py "<repo>/assets/tga/MeadowFlora/import_flora_meadow_ue.py"     DRY_RUN = True only lists what it would do.
# Creates under /Game/CastleDefender/Environment/Flora/Meadow (names are what adjustedfilm's place_meadow_ue.py looks for):
#   SM_Flower_Daisy|Poppy|Yarrow|Cornflower_A/B/C, SM_Bush_Hawthorn|Hazel_A/B, SM_Fern_Bracken_A     (pivot = base on the ground)
#   4 LODs each (LOD3 = 2 crossed impostor cards), T_MeadowFlora (2K atlas) + T_MeadowCards (2K: leaf sprays + impostors, alpha),
#   M_MeadowFlora (opaque) / M_MeadowCards (masked), both Two Sided Foliage, subsurface = BaseColor x SubsurfaceAmount, wind:
#   SimpleGrassWind with weight (1 - R)^2 + leaf flutter along the normal (B mask, G phase). Vertex colour: R stiffness, G phase, B flutter.
# No collision (walk-through foliage; give bushes a capsule on the scatter if gameplay wants it). Nanite off (masked cards).
import os, sys
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

# materials: UE 5.3-safe builder shared with fix_wind_53.py (two-sided foliage enum, instanced flag, wind on WPO)
sys.path.insert(0, SRC)
import meadow_mat53
for _n, _a, _m in (('M_MeadowFlora', 'T_MeadowFlora', False), ('M_MeadowCards', 'T_MeadowCards', True)):
    log('%s: route %s' % (_n, meadow_mat53.build(DST, _n, _a, _m, log)[1]))
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
d.import_uniform_scale = 100.0                                                             # Blender FBX: metre vertices + UnitScaleFactor 100 (#356 / #311)
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
