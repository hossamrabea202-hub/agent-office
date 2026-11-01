# #397 weapon kit AAA (TGA): import the AAA weapons into a NEW folder, UE 5.3. Safe to re-run.
#   py "<repo>/assets/tga/WeaponsAAA/import_weapons_aaa_ue.py"            (DRY_RUN = True: checks and reports only)
# For each <Name>/ here: /Game/CastleDefender/Weapons/CK_AAA/<Name>/ gets SM_CK_<Name> (same name, pivot and axis as the
# live CK kit, so #254 wiring and #95 upgrade looks work after a swap), the 3 textures, and MI_CK_<Name>_AAA whose parent
# is the existing master M_CK_Weapon (read only: the master and the live CK assets are never edited).
# Textures (#260 budget, KB §1.3): authored 2K, Maximum Texture Size 1024 in engine; BaseColor sRGB + mip Sharpen4;
# ORM Masks (no sRGB) with Composite Texture = the normal map on Green (roughness, kills distant sparkle); Normal BC5.
# The swap into the game happens only after the owner's OK (README step 4). Writes import_weapons_aaa.txt.
import os, unreal

DRY_RUN = True

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT, LIVE = '/Game/CastleDefender/Weapons/CK_AAA', '/Game/CastleDefender/Weapons/CK'
MASTER = LIVE + '/M_CK_Weapon'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = ['DRY_RUN = %s' % DRY_RUN]

def task(path, dest, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

def fbx_ui():
    fbx = unreal.FbxImportUI()
    fbx.import_mesh = True; fbx.import_as_skeletal = False; fbx.import_materials = False; fbx.import_textures = False
    fbx.static_mesh_import_data.combine_meshes = True
    fbx.static_mesh_import_data.generate_lightmap_u_vs = True
    fbx.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return fbx

names = [n for n in sorted(os.listdir(SRC)) if os.path.isfile(os.path.join(SRC, n, 'SM_CK_%s.fbx' % n))]
log.append('master %s: %s' % (MASTER, 'ok' if EAL.does_asset_exist(MASTER) else 'MISSING (import the CK kit first, #233)'))
for name in names:
    live = '%s/%s/SM_CK_%s' % (LIVE, name, name)
    log.append('%-14s live mesh %s, new folder %s/%s' % (name, 'ok' if EAL.does_asset_exist(live) else 'MISSING', ROOT, name))
if DRY_RUN or not EAL.does_asset_exist(MASTER):
    log.append('DRY RUN only. Decision: if the master is ok, set DRY_RUN = False and run again. Nothing was changed.')
else:
    for name in names:
        d = os.path.join(SRC, name); DST = '%s/%s' % (ROOT, name); TN = 'T_CK_' + name
        tex = {TN + '_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
               TN + '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
               TN + '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
        tools.import_asset_tasks([task(os.path.join(d, 'textures', n + '.png'), DST) for n in tex])
        nrm = unreal.load_asset('%s/%s_Normal_DirectX' % (DST, TN))
        for n, (srgb, comp) in tex.items():
            t = unreal.load_asset('%s/%s' % (DST, n)); t.modify()
            t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
            t.set_editor_property('max_texture_size', 1024)
            if n.endswith('_BaseColor'): t.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)
            if n.endswith('_Normal_DirectX'): t.set_editor_property('flip_green_channel', False)
            if n.endswith('_ORM'):
                t.set_editor_property('composite_texture', nrm)
                t.set_editor_property('composite_texture_mode', unreal.CompositeTextureMode.CTM_NORMAL_ROUGHNESS_TO_GREEN)
                t.set_editor_property('composite_power', 1.0)
            EAL.save_loaded_asset(t)
        tools.import_asset_tasks([task(os.path.join(d, 'SM_CK_%s.fbx' % name), DST, fbx_ui())])
        MI = '%s/MI_CK_%s_AAA' % (DST, name)
        mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_CK_%s_AAA' % name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
        for pn, tn in (('BaseColor', 'BaseColor'), ('ORM', 'ORM'), ('Normal', 'Normal_DirectX')):
            MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s_%s' % (DST, TN, tn)))
        EAL.save_asset(MI)
        sm = unreal.load_asset('%s/SM_CK_%s' % (DST, name)); sm.set_material(0, mi); EAL.save_loaded_asset(sm)
        b = sm.get_bounding_box(); log.append('%s: imported, %d tris, bounds z %.1f..%.1f cm' % (name, sm.get_num_triangles(0), b.min.z, b.max.z))
        live = unreal.load_asset('%s/%s/SM_CK_%s' % (LIVE, name, name))
        if live:
            lb = live.get_bounding_box(); log.append('   live bounds z %.1f..%.1f cm (pivot / length check: should match within ~1 cm)' % (lb.min.z, lb.max.z))
out = 'Weapon kit AAA import (#397)\n' + '\n'.join(log)
open(os.path.join(SRC, 'import_weapons_aaa.txt'), 'w').write(out); unreal.log(out)
