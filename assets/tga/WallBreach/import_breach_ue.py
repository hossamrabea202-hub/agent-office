# Wall-section breach collapse for #327 / #316 (TGA, 2026-10-31): import into UE 5.3. Original procedural work (tools/tga/breach).
# Run in the editor:   py "<repo>/assets/tga/WallBreach/import_breach_ue.py"      DRY_RUN = True only lists what it would do.
# Creates under /Game/CastleDefender/Gameplay/Siege/Breach:
#   SK_WallBreach (+ skeleton, physics asset off) with the animation A_WallBreach_Collapse (2.5 s, 30 fps, 57 bones: Root,
#   Frame = the standing wall, Chunk_00..54 = the falling ashlar / half-blocks / core / crumbs), SM_Rubble_Masonry_01..06,
#   T_BreachFracture BC/ORM/N + M_BreachFracture/MI_BreachFracture (fresh broken stone). Slot M_WallStone ->
#   MI_Castle_StoneWall_World (the castle's own world-aligned wall stone, used, never edited), M_WallFracture -> MI_BreachFracture.
import os
import unreal

DRY_RUN = True
SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Gameplay/Siege/Breach'
RUBBLE = ['SM_Rubble_Masonry_%02d' % i for i in range(1, 7)]
log = lambda m: unreal.log('[breach327%s] %s' % (' DRY' if DRY_RUN else '', m))
if DRY_RUN:
    log('would import SK_WallBreach.fbx (skeletal + A_WallBreach_Collapse), %s and T_BreachFracture into %s' % (RUBBLE, DST)); raise SystemExit
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
TEX = [('T_BreachFracture_BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_BreachFracture_ORM', False, unreal.TextureCompressionSettings.TC_MASKS),
       ('T_BreachFracture_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)
    EAL.save_loaded_asset(t)
sk = unreal.FbxImportUI()
sk.import_mesh = True; sk.import_as_skeletal = True; sk.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
sk.import_animations = True; sk.import_materials = False; sk.import_textures = False; sk.create_physics_asset = False
sk.skeletal_mesh_import_data.import_morph_targets = False
sk.anim_sequence_import_data.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
sm = unreal.FbxImportUI()
sm.import_mesh = True; sm.import_as_skeletal = False; sm.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
sm.import_materials = False; sm.import_textures = False
sm.static_mesh_import_data.combine_meshes = True; sm.static_mesh_import_data.auto_generate_collision = False
tools.import_asset_tasks([task(os.path.join(SRC, 'fbx', 'SK_WallBreach.fbx'), sk)] + [task(os.path.join(SRC, 'fbx', n + '.fbx'), sm) for n in RUBBLE])
MASTER = DST + '/M_BreachFracture'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_BreachFracture', DST, unreal.Material, unreal.MaterialFactoryNew())
    def P(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = P(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -700, -200, DST + '/T_BreachFracture_BC')
    orm = P(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -700, 100, DST + '/T_BreachFracture_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = P(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -700, 400, DST + '/T_BreachFracture_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    MEL.connect_material_property(bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(MASTER)
MIP = DST + '/MI_BreachFracture'
mi = unreal.load_asset(MIP) if EAL.does_asset_exist(MIP) else tools.create_asset('MI_BreachFracture', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER)); EAL.save_asset(MIP)
reg = unreal.AssetRegistryHelpers.get_asset_registry()
hits = [h for h in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')) if str(h.asset_name) == 'MI_Castle_StoneWall_World']
wall = unreal.load_asset(str(hits[0].package_name)) if hits else None
if not wall: log('WARNING MI_Castle_StoneWall_World not found: set the M_WallStone slots by hand')
MIS = {'M_WallStone': wall or mi, 'M_WallFracture': mi}
skm = unreal.load_asset(DST + '/SK_WallBreach')
if skm:
    mats = skm.get_editor_property('materials')
    for s in mats:
        key = str(s.get_editor_property('material_slot_name'))
        if key in MIS: s.set_editor_property('material_interface', MIS[key])
    skm.set_editor_property('materials', mats); EAL.save_loaded_asset(skm)
else: log('WARNING SK_WallBreach did not import')
sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
for n in RUBBLE:
    s = unreal.load_asset('%s/%s' % (DST, n))
    if not s: log('WARNING %s did not import' % n); continue
    for i, slot in enumerate(s.get_editor_property('static_materials')):
        key = str(slot.get_editor_property('material_slot_name'))
        if key in MIS: s.set_material(i, MIS[key])
    sub.remove_collisions(s); sub.add_simple_collisions(s, unreal.ScriptingCollisionShapeType.NDOP18); EAL.save_loaded_asset(s)
anims = [a for a in EAL.list_assets(DST, recursive=False) if 'Anim' in a or 'Collapse' in a]
log('imported: SK_WallBreach, anims %s, %d rubble. Rename the anim to A_WallBreach_Collapse if UE named it after the take.' % (anims, len(RUBBLE)))
