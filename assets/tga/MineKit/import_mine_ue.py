# Underground mine dungeon kit for #309 / #297 (TGA, 2026-10-31): import into UE 5.3. Original procedural work (tools/tga/mine).
# Run in the editor:   py "<repo>/assets/tga/MineKit/import_mine_ue.py"     DRY_RUN = True only lists what it would do.
# Creates under /Game/CastleDefender/Environment/Mine: 14 meshes (fbx/), T_MineRock (2K) / T_MineOak / T_MineIron / T_MineOre
# (1K) BC/ORM/N, M_MineSurface (+ vertex-colour R wetness: darker, glossier) with MI_MineRock / Oak / Iron / Ore, and
# M_MineGlow + MI_MineGlow (lantern glass). Material slots are matched by the Blender material names (M_MineRock ...).
# Collision: tunnels and chamber use complex-as-simple (walk the real rock); props get a 26-DOP / box hull.
# SM_Mine_Lantern gets a socket 'Light' (attach a PointLight there: KB rule 6, real light behind every emissive).
import os
import unreal

DRY_RUN = True
SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Environment/Mine'
MESHES = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(SRC, 'fbx')) if f.endswith('.fbx'))
SETS = ('Rock', 'Oak', 'Iron', 'Ore')
SHELLS = ('SM_Mine_Tunnel_', 'SM_Mine_Chamber')
log = lambda m: unreal.log('[mine309%s] %s' % (' DRY' if DRY_RUN else '', m))
if DRY_RUN:
    log('would import %d meshes %s and %d texture sets into %s' % (len(MESHES), MESHES, len(SETS), DST)); raise SystemExit
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
TEX = []
for s in SETS:
    TEX += [('T_Mine%s_BC' % s, True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_Mine%s_ORM' % s, False, unreal.TextureCompressionSettings.TC_MASKS),
            ('T_Mine%s_N' % s, False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)
f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
f.import_materials = False; f.import_textures = False
d = f.static_mesh_import_data; d.combine_meshes = True; d.auto_generate_collision = False
d.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE                     # R = wetness
d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
tools.import_asset_tasks([task(os.path.join(SRC, 'fbx', n + '.fbx'), f) for n in MESHES])

def P(m, cls, name, x, y, tex=None, sampler=None):
    e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
    if tex: e.set_editor_property('texture', unreal.load_asset(tex))
    if sampler: e.set_editor_property('sampler_type', sampler)
    return e
def E(m, cls, x, y): return MEL.create_material_expression(m, cls, x, y)
C = MEL.connect_material_expressions
MASTER = DST + '/M_MineSurface'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_MineSurface', DST, unreal.Material, unreal.MaterialFactoryNew())
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 0); til = P(m, unreal.MaterialExpressionScalarParameter, 'Tiling', -1600, 120)
    til.set_editor_property('default_value', 1.0); uv = E(m, unreal.MaterialExpressionMultiply, -1400, 40); C(tc, '', uv, 'A'); C(til, '', uv, 'B')
    bc = P(m, unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -250, DST + '/T_MineRock_BC')
    orm = P(m, unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 150, DST + '/T_MineRock_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = P(m, unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 500, DST + '/T_MineRock_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    for t in (bc, orm, nrm): C(uv, '', t, 'UVs')
    tint = P(m, unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    wetp = P(m, unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wetp.set_editor_property('default_value', 1.0)
    vc = E(m, unreal.MaterialExpressionVertexColor, -1100, 760)
    wet = E(m, unreal.MaterialExpressionMultiply, -800, 600); C(vc, 'R', wet, 'A'); C(wetp, '', wet, 'B')
    tb = E(m, unreal.MaterialExpressionMultiply, -800, -350); C(bc, 'RGB', tb, 'A'); C(tint, '', tb, 'B')
    dk = E(m, unreal.MaterialExpressionMultiply, -600, -200); C(tb, '', dk, 'A'); dk.set_editor_property('const_b', 0.55)   # damp darkens
    col = E(m, unreal.MaterialExpressionLinearInterpolate, -400, -280); C(tb, '', col, 'A'); C(dk, '', col, 'B'); C(wet, '', col, 'Alpha')
    rg = E(m, unreal.MaterialExpressionLinearInterpolate, -400, 150); C(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.15); C(wet, '', rg, 'Alpha')
    MEL.connect_material_property(col, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(MASTER)
GLOW = DST + '/M_MineGlow'
if not EAL.does_asset_exist(GLOW):
    m = tools.create_asset('M_MineGlow', DST, unreal.Material, unreal.MaterialFactoryNew())
    c = P(m, unreal.MaterialExpressionVectorParameter, 'GlowColor', -600, 0); c.set_editor_property('default_value', unreal.LinearColor(1.0, 0.55, 0.2, 1))
    s = P(m, unreal.MaterialExpressionScalarParameter, 'GlowStrength', -600, 150); s.set_editor_property('default_value', 8.0)
    mu = E(m, unreal.MaterialExpressionMultiply, -350, 60); C(c, '', mu, 'A'); C(s, '', mu, 'B')
    MEL.connect_material_property(mu, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR); MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(GLOW)
MIS = {}
for s in SETS:
    path = '%s/MI_Mine%s' % (DST, s)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset('MI_Mine' + s, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    for par, suf in (('BaseColorTex', 'BC'), ('ORMTex', 'ORM'), ('NormalTex', 'N')):
        MEL.set_material_instance_texture_parameter_value(mi, par, unreal.load_asset('%s/T_Mine%s_%s' % (DST, s, suf)))
    if s != 'Rock': MEL.set_material_instance_scalar_parameter_value(mi, 'Wetness', 0.0)    # only the carved rock carries wetness
    EAL.save_asset(path); MIS['M_Mine' + s] = mi
path = DST + '/MI_MineGlow'
mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset('MI_MineGlow', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(GLOW)); EAL.save_asset(path); MIS['M_MineGlow'] = mi
sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
for n in MESHES:
    sm = unreal.load_asset('%s/%s' % (DST, n))
    if not sm: log('WARNING %s did not import' % n); continue
    for i, slot in enumerate(sm.get_editor_property('static_materials')):
        key = str(slot.get_editor_property('material_slot_name'))
        if key in MIS: sm.set_material(i, MIS[key])
        else: log('slot %s on %s has no MI' % (key, n))
    bs = sm.get_editor_property('body_setup')
    if n.startswith(SHELLS):
        if bs: bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    else:
        sub.remove_collisions(sm); sub.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.NDOP26)
    if n == 'SM_Mine_Lantern':
        for s_ in list(sm.get_editor_property('sockets') or []): sm.remove_socket(s_)
        so = unreal.StaticMeshSocket(sm); so.set_editor_property('socket_name', 'Light'); so.set_editor_property('relative_location', unreal.Vector(0, 0, 20)); sm.add_socket(so)
    EAL.save_loaded_asset(sm)
log('mine kit imported: %d meshes in %s (layout guide: assets/tga/MineKit/README.md)' % (len(MESHES), DST))
