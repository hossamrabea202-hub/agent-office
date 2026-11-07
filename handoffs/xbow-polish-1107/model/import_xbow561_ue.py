# #561 crossbow, game-ready import + swap (checkking (Claude), 2026-11-07). Editor Python, Master only.
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --src "<folder>"            1. dry run: checks files, reads the
#                                                                                               old mesh + BP_Crossbow, prints the fit
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --src "<folder>" --import   2. new assets in Rebuild561, FITTED to
#                                                                                               the old mesh's space (pivot/axes/size)
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --swap                      3. backup the old mesh, then Replace
#                                                                                               References old -> new everywhere
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --revert                    undo 3 (restores from the backup)
# <folder> = the unzipped xbow561_model_v3.zip: SM_Crossbow561.fbx + T_Crossbow561M_BaseColor / _ORM / _Normal.png.
import unreal, sys, os, json
A = sys.argv[1:]
SRC = A[A.index('--src') + 1] if '--src' in A else ''
DST = '/Game/CastleDefender/Equipment/crossbow/Rebuild561'
NEW = DST + '/SM_Crossbow561'
OLD = '/Game/CastleDefender/Equipment/crossbow/Noble_Crossbow_LowPoly'
BAK = '/Game/CastleDefender/Equipment/crossbow/Backup561/Noble_Crossbow_LowPoly_bak'
BP = '/Game/CastleDefender/Gameplay/Crossbow/BP_Crossbow'
HERE = os.path.dirname(os.path.abspath(__file__)); STATE = os.path.join(HERE, 'import_xbow561_state.json')
NEW_CENTRE = unreal.Vector(1.035, 0.0, -2.896)     # bounds centre of SM_Crossbow561 as exported (cm, X fwd, Z up)
NEW_LEN = 88.07                                    # its length along X (cm)
EAL, MEL, ESM = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.EditorStaticMeshLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
FILES = ['SM_Crossbow561.fbx', 'T_Crossbow561M_BaseColor.png', 'T_Crossbow561M_ORM.png', 'T_Crossbow561M_Normal.png']
log = lambda *a: unreal.log('XBOW561 ' + ' '.join(str(x) for x in a))
V = lambda v, i: (v.x, v.y, v.z)[i]

def bp_components():
    """(component name, object) of BP_Crossbow's components, best effort (5.x SubobjectDataSubsystem)."""
    out = []
    try:
        bp = unreal.load_asset(BP); sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        for h in sds.k2_gather_subobject_data_for_blueprint(bp):
            d = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h); o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
            if o: out.append((o.get_name(), o))
    except Exception as e:
        log('could not read BP components (fine, fit uses defaults):', e)
    return out

def fit():
    """Transform that puts the new mesh in the old mesh's local space: same bounds centre, length, long axis, forward/up sign."""
    old = unreal.load_asset(OLD); b = old.get_bounding_box(); mn, mx = b.min, b.max
    ext = [V(mx, i) - V(mn, i) for i in range(3)]; ctr = [(V(mx, i) + V(mn, i)) / 2 for i in range(3)]
    order = sorted(range(3), key=lambda i: -ext[i]); L, S, U = order
    fs, us, why = 1.0, 1.0, 'default +'
    comps = bp_components(); weapon = muzzle = None
    for n, o in comps:
        if isinstance(o, unreal.StaticMeshComponent) and o.get_editor_property('static_mesh') == old: weapon = o
        if n.lower().startswith('muzzle'): muzzle = o
    if weapon and muzzle:
        wt = weapon.get_editor_property('relative_location'), weapon.get_editor_property('relative_rotation'), weapon.get_editor_property('relative_scale3d')
        m = muzzle.get_editor_property('relative_location')
        parent = muzzle.get_attach_parent() if hasattr(muzzle, 'get_attach_parent') else None
        if parent != weapon:
            t = unreal.Transform(wt[0], wt[1], wt[2]); m = t.inverse_transform_location(m)
        d = [V(m, i) - ctr[i] for i in range(3)]
        fs = 1.0 if d[L] >= 0 else -1.0
        us = 1.0 if d[U] >= -0.5 else -1.0
        why = 'from Muzzle at %s (old-mesh space)' % (m,)
    log('old bounds', mn, mx, '| long axis', 'XYZ'[L], 'up axis', 'XYZ'[U], '| forward sign', fs, 'up sign', us, why)
    if weapon: log('BP_Crossbow component showing the old mesh:', weapon.get_name(), '| override materials:',
                   [str(x.get_path_name()) if x else None for x in weapon.get_editor_property('override_materials')])
    axis = lambda i, s: unreal.Vector(*[s if k == i else 0.0 for k in range(3)])
    fwd, up = axis(L, fs), axis(U, us)
    rot = unreal.MathLibrary.make_rot_from_xz(fwd, up)
    scale = ext[L] / NEW_LEN
    c = rot.rotate_vector(NEW_CENTRE * scale)
    trans = unreal.Vector(ctr[0] - c.x, ctr[1] - c.y, ctr[2] - c.z)
    log('FIT scale %.4f rotation %s translation %s' % (scale, rot, trans))
    return scale, rot, trans

def do_import():
    if EAL.does_asset_exist(NEW): log('already imported (delete the Rebuild561 folder to re-import)'); return
    scale, rot, trans = fit()
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data; sd.combine_meshes = True; sd.generate_lightmap_u_vs = True; sd.auto_generate_collision = False
    sd.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS     # KB rule 4
    sd.import_uniform_scale = scale; sd.import_rotation = rot; sd.import_translation = trans    # fitted to the old mesh space
    def task(f, opts=None):
        t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, f); t.destination_path = DST; t.automated = True; t.save = False
        if opts: t.options = opts
        TOOLS.import_asset_tasks([t]); return unreal.load_asset(DST + '/' + os.path.splitext(f)[0])
    mesh = task(FILES[0], ui); bc, orm, nrm = task(FILES[1]), task(FILES[2]), task(FILES[3])
    bc.set_editor_property('srgb', True); bc.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)
    nrm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    nrm.set_editor_property('srgb', False); nrm.set_editor_property('flip_green_channel', True)     # Blender bakes OpenGL
    orm.set_editor_property('srgb', False); orm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    orm.set_editor_property('composite_texture', nrm)                                                 # INDUSTRY_SECRETS 1.3.1
    orm.set_editor_property('composite_texture_mode', unreal.CompositeTextureMode.CTM_NORMAL_ROUGHNESS_TO_GREEN)
    for t in (bc, orm, nrm): t.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WEAPON)
    mat = TOOLS.create_asset('M_Crossbow561M', DST, unreal.Material, unreal.MaterialFactoryNew())
    def samp(tex, st, y):
        e = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -420, y)
        e.set_editor_property('texture', tex); e.set_editor_property('sampler_type', st); return e
    s_bc = samp(bc, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -300)
    s_orm = samp(orm, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, 0)
    s_n = samp(nrm, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, 300)
    MEL.connect_material_property(s_bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(s_orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(s_orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(s_orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(s_n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(mat); mesh.set_material(0, mat)
    # game-ready: 3 LODs (100 / 50 / 25 %), simple box collision, same collision setup as the old mesh
    try:
        opt = unreal.EditorScriptingMeshReductionOptions(); opt.auto_compute_lod_screen_size = False
        opt.reduction_settings = [unreal.EditorScriptingMeshReductionSettings(percent_triangles=1.0, screen_size=1.0),
                                  unreal.EditorScriptingMeshReductionSettings(percent_triangles=0.5, screen_size=0.25),
                                  unreal.EditorScriptingMeshReductionSettings(percent_triangles=0.25, screen_size=0.08)]
        ESM.set_lods(mesh, opt); log('LODs', ESM.get_lod_count(mesh))
    except Exception as e: log('LODs not set:', e)
    try: ESM.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX); log('box collision added')
    except Exception as e: log('collision not added:', e)
    try:
        old = unreal.load_asset(OLD); mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',
            old.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))
    except Exception: pass
    for x in (mesh, bc, orm, nrm, mat): EAL.save_loaded_asset(x, False)
    b = mesh.get_bounding_box(); o = unreal.load_asset(OLD).get_bounding_box()
    log('IMPORTED. new bounds', b.min, b.max, '| old bounds', o.min, o.max, '(should nearly match)')

def swap():
    if not EAL.does_asset_exist(NEW): log('ERROR run --import first'); return
    if not EAL.does_asset_exist(BAK): EAL.duplicate_asset(OLD, BAK); log('backup', BAK)
    refs = unreal.AssetRegistryHelpers.get_asset_registry().get_referencers(OLD, unreal.AssetRegistryDependencyOptions())
    json.dump(dict(referencers=[str(r) for r in (refs or [])]), open(STATE, 'w'), indent=1)
    log('replacing references in', [str(r) for r in (refs or [])])
    ok = EAL.consolidate_assets(unreal.load_asset(NEW), [unreal.load_asset(OLD)])
    log('SWAP', 'OK' if ok else 'FAILED', '- now compile + save BP_Crossbow and every BP listed above, then Play')

def revert():
    if not EAL.does_asset_exist(BAK): log('no backup, nothing to revert'); return
    if not EAL.does_asset_exist(OLD): EAL.duplicate_asset(BAK, OLD)
    ok = EAL.consolidate_assets(unreal.load_asset(OLD), [unreal.load_asset(NEW)])
    log('REVERT', 'OK' if ok else 'FAILED', '(the new mesh was folded back into the old one; re-import with --import if wanted)')

files_ok = bool(SRC) and all(os.path.exists(os.path.join(SRC, f)) for f in FILES)
if '--swap' in A: swap()
elif '--revert' in A: revert()
elif '--import' in A:
    if not files_ok: log('ERROR missing files in', SRC)
    else: do_import()
else:
    log('DRY RUN: files', 'OK' if files_ok else 'MISSING in "%s"' % SRC, '| new mesh', 'exists' if EAL.does_asset_exist(NEW) else 'not imported yet')
    fit()
