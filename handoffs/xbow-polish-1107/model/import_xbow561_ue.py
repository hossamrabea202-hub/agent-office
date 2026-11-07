# #561 rebuilt Noble crossbow: import into UE as NEW assets, then (owner OK) fit it into BP_Crossbow. checkking, 2026-11-07.
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --src "<folder>"            dry run: checks files, prints nothing changed
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --src "<folder>" --import   mesh + 3 textures + M_Crossbow561M, saved
#   py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --fit                       prints the transform that puts the new mesh
#                                                                                                where the old one sits (no change)
# <folder> holds SM_Crossbow561.fbx, T_Crossbow561M_BaseColor.png, _ORM.png, _Normal.png (fast chat zip xbow561_model_v1.zip).
# Nothing live is edited. The swap in BP_Crossbow is one property (see README_MODEL.md), done after the owner's OK.
import unreal, sys, os
A = sys.argv[1:]
SRC = A[A.index('--src') + 1] if '--src' in A else ''
DST = '/Game/CastleDefender/Equipment/crossbow/Rebuild561'
OLD = '/Game/CastleDefender/Equipment/crossbow/Noble_Crossbow_LowPoly'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
log = lambda *a: unreal.log('XBOW561M ' + ' '.join(str(x) for x in a))
FILES = ['SM_Crossbow561.fbx', 'T_Crossbow561M_BaseColor.png', 'T_Crossbow561M_ORM.png', 'T_Crossbow561M_Normal.png']

def task(f, opts=None):
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, f); t.destination_path = DST; t.automated = True
    t.replace_existing = False; t.save = False
    if opts: t.options = opts
    TOOLS.import_asset_tasks([t]); return unreal.load_asset(DST + '/' + os.path.splitext(f)[0])

def do_import():
    if EAL.does_asset_exist(DST + '/SM_Crossbow561'):
        log('already imported, nothing done (delete the Rebuild561 folder to re-import)'); return
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sd = ui.static_mesh_import_data; sd.combine_meshes = True; sd.generate_lightmap_u_vs = True
    sd.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS   # KB rule 4: import normals
    mesh = task(FILES[0], ui)
    bc, orm, nrm = task(FILES[1]), task(FILES[2]), task(FILES[3])
    bc.set_editor_property('srgb', True); bc.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)
    nrm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    nrm.set_editor_property('srgb', False); nrm.set_editor_property('flip_green_channel', True)          # Blender bakes OpenGL
    orm.set_editor_property('srgb', False); orm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    orm.set_editor_property('composite_texture', nrm)                                                      # no distant sparkle
    orm.set_editor_property('composite_texture_mode', unreal.CompositeTextureMode.CTM_NORMAL_ROUGHNESS_TO_GREEN)
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
    MEL.recompile_material(mat)
    mesh.set_material(0, mat)
    try:
        ns = mesh.get_editor_property('nanite_settings'); ns.enabled = True; mesh.set_editor_property('nanite_settings', ns)
    except Exception as e:
        log('nanite not set (fine, the mesh is 30k tris):', e)
    for x in (mesh, bc, orm, nrm, mat): EAL.save_loaded_asset(x, False)
    log('imported + saved:', DST, '| tris', mesh.get_num_triangles(0) if hasattr(mesh, 'get_num_triangles') else '?')

def fit():
    old, new = unreal.load_asset(OLD), unreal.load_asset(DST + '/SM_Crossbow561')
    if not old or not new: log('need both meshes (run --import first)'); return
    bo, bn = old.get_bounding_box(), new.get_bounding_box()
    so, sn = bo.max - bo.min, bn.max - bn.min
    ax_o = max(range(3), key=lambda i: [so.x, so.y, so.z][i]); names = 'XYZ'
    lo, ln = max(so.x, so.y, so.z), max(sn.x, sn.y, sn.z)
    co, cn = (bo.max + bo.min) * 0.5, (bn.max + bn.min) * 0.5
    log('old size', so, 'long axis', names[ax_o], '| new size', sn, 'long axis X (forward)')
    log('old centre', co, '| new centre', cn)
    log('SUGGESTED on the crossbow mesh component in BP_Crossbow after swapping the mesh: uniform scale x%.3f; '
        'if the old long axis is not X, add yaw 90 (Y) or pitch 90 (Z); then move by (old centre - new centre * scale) '
        'and check the hero grip in the viewport' % (lo / ln))

files_ok = all(os.path.exists(os.path.join(SRC, f)) for f in FILES) if SRC else False
if '--fit' in A: fit()
elif '--import' in A:
    if not files_ok: log('ERROR missing files in', SRC, [f for f in FILES if not os.path.exists(os.path.join(SRC, f))])
    else: do_import()
else:
    log('dry run: files', 'OK' if files_ok else 'MISSING in ' + SRC, '| target', DST, '| exists' if EAL.does_asset_exist(DST + '/SM_Crossbow561') else '| new')
