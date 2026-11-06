# #502 medic assets (TGA PC, 2026-11-06): import the medic kit into UE 5.8. NEW assets only, nothing live is edited.
#   py "<folder>/import_medic502_assets_ue.py"             DRY RUN (default): checks files + parents, lists the cape parent's params
#   py "<folder>/import_medic502_assets_ue.py" --apply     imports + makes the material instances, saves the new assets
#   py "<folder>/import_medic502_assets_ue.py" --revert    deletes ONLY what --apply made (the Medic502 folder)
# Makes under /Game/CastleDefender/Characters/NPC/Medic502:
#   SM_MedicStaff (hazel staff, pivot = grip centre, axis +Z -> hand_r), SM_MedicSatchel502 (pivot = strap top -> spine_03, like #248)
#   MI_MedicStaff + MI_MedicSatchel502 = children of TGA's M_MedicGear (#248: BaseColorTex / ORMTex / NormalTex / Tint / Wetness)
#   MI_MedicCape = child of the soldier cape MI_Hero_Cloth_Crimson with the linen textures + linen tint (see the cape note below)
#   T_UI_MedicBadge_512 / _128 / _64 (UI textures: no mips, UserInterface2D) for the recruit card and the MEDICS HUD line
# NOT here (other seats): BP_Medic wiring (KnightMesh body, cape slot 2, staff on hand_r, no sword), recruit key (#503), C++.
import os, sys, unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Characters/NPC/Medic502'
GEAR = '/Game/CastleDefender/Characters/NPC/MedicGear/M_MedicGear'
LINEN = unreal.LinearColor(0.56, 0.54, 0.47, 1.0)                   # measured bleached linen (KB: never 255 white)
args = sys.argv[1:]
EAL, MEL, AR = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetRegistryHelpers.get_asset_registry()
tools = unreal.AssetToolsHelpers.get_asset_tools()
TC = unreal.TextureCompressionSettings
TEX = [  # file, srgb, compression, clamp
    ('T_MedicCape_BC', True, TC.TC_DEFAULT, False), ('T_MedicCape_N', False, TC.TC_NORMALMAP, False),
    ('T_MedicCape_ORM', False, TC.TC_MASKS, False), ('T_MedicCape_Wear', False, TC.TC_MASKS, False),
    ('T_MedicEmblem_BCA', True, TC.TC_DEFAULT, True), ('T_MedicEmblem_ORM', False, TC.TC_MASKS, True),
    ('T_MedicStaff_BC', True, TC.TC_DEFAULT, False), ('T_MedicStaff_N', False, TC.TC_NORMALMAP, False), ('T_MedicStaff_ORM', False, TC.TC_MASKS, False),
    ('T_MedicSatchel502_BC', True, TC.TC_DEFAULT, False), ('T_MedicSatchel502_N', False, TC.TC_NORMALMAP, False), ('T_MedicSatchel502_ORM', False, TC.TC_MASKS, False)]
UI = ['T_UI_MedicBadge_512', 'T_UI_MedicBadge_128', 'T_UI_MedicBadge_64']
MESH = ['SM_MedicStaff', 'SM_MedicSatchel502']


def find(name):
    f = unreal.ARFilter(recursive_paths=True, package_paths=['/Game'])
    return [str(a.package_name) for a in AR.get_assets(f) if str(a.asset_name) == name]


def cape_parent():
    p = find('MI_Hero_Cloth_Crimson')
    return p[0] if p else None


def param_names(mat):
    out = {}
    for kind, fn in (('scalar', MEL.get_scalar_parameter_names), ('vector', MEL.get_vector_parameter_names), ('texture', MEL.get_texture_parameter_names)):
        try: out[kind] = [str(n) for n in fn(mat)]
        except Exception as e: out[kind] = ['(could not read: %s)' % e]
    return out


def check():
    bad = []
    for n, *_ in TEX: bad += [] if os.path.exists(os.path.join(SRC, 'textures', n + '.png')) else ['missing textures/%s.png' % n]
    for n in UI: bad += [] if os.path.exists(os.path.join(SRC, 'badge', n + '.png')) else ['missing badge/%s.png' % n]
    for n in MESH: bad += [] if os.path.exists(os.path.join(SRC, 'meshes', n + '.fbx')) else ['missing meshes/%s.fbx' % n]
    if not EAL.does_asset_exist(GEAR): bad.append('M_MedicGear not found at %s (import #248 first)' % GEAR)
    if not cape_parent(): bad.append('MI_Hero_Cloth_Crimson not found anywhere under /Game')
    return bad


def task(path, dst, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dst; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t


def child_mi(name, parent, textures, vectors=None):
    path = DST + '/' + name
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, parent); done = []
    names = param_names(parent)
    for pname, tex in textures.items():
        if pname in names.get('texture', []): MEL.set_material_instance_texture_parameter_value(mi, pname, unreal.load_asset(DST + '/' + tex)); done.append('%s=%s' % (pname, tex))
    for pname, val in (vectors or {}).items():
        if pname in names.get('vector', []): MEL.set_material_instance_vector_parameter_value(mi, pname, val); done.append(pname)
    MEL.update_material_instance(mi); EAL.save_asset(path)
    return done


def guess(names, *keys):
    for n in names:                              # exact short names first (MI_Hero_Cloth_Crimson uses BC / N / ORM)
        if n.lower() in [k.lower() for k in keys]: return n
    for n in names:
        if any(k.lower() in n.lower() for k in keys if len(k) > 2): return n
    return None


if '--revert' in args:
    gone = EAL.list_assets(DST, recursive=True, include_folder=False) if EAL.does_directory_exist(DST) else []
    for a in gone: EAL.delete_asset(a)
    print('REVERTED: deleted %d assets in %s (only what --apply made)' % (len(gone), DST))
else:
    bad = check(); cp = cape_parent()
    print('Medic502 assets -> %s' % DST)
    print('  textures %d, UI badges %d, meshes %d' % (len(TEX), len(UI), len(MESH)))
    if cp:
        names = param_names(unreal.load_asset(cp))
        print('  cape parent %s params: %s' % (cp, names))
        print('  cape will set: BaseColor -> %s, Normal -> %s, ORM/Roughness -> %s, Tint -> %s' % (
            guess(names['texture'], 'BC', 'basecolor', 'albedo', 'diffuse', 'color'), guess(names['texture'], 'N', 'normal'),
            guess(names['texture'], 'orm', 'rough', 'mask'), guess(names['vector'], 'tint', 'color')))
    for b in bad: print('MISMATCH', b)
    if bad: raise SystemExit('STOP: %d problem(s), nothing changed' % len(bad))
    if '--apply' not in args:
        print('DRY RUN OK. Nothing changed. Run with --apply.')
    else:
        tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png'), DST) for n, *_ in TEX] +
                                 [task(os.path.join(SRC, 'badge', n + '.png'), DST) for n in UI])
        for n, srgb, comp, clamp in TEX:
            t = unreal.load_asset(DST + '/' + n); t.modify()
            t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
            if comp == TC.TC_NORMALMAP: t.set_editor_property('flip_green_channel', False)          # repo normals are DirectX already
            if clamp: t.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); t.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
            if n.endswith('_BC'): t.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)   # KB 1.3.6
            EAL.save_loaded_asset(t)
        for n in UI:
            t = unreal.load_asset(DST + '/' + n); t.modify()
            t.set_editor_property('compression_settings', TC.TC_EDITOR_ICON); t.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
            t.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS); EAL.save_loaded_asset(t)
        f = unreal.FbxImportUI()
        f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        f.import_materials = False; f.import_textures = False
        f.static_mesh_import_data.combine_meshes = True; f.static_mesh_import_data.auto_generate_collision = False
        f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        tools.import_asset_tasks([task(os.path.join(SRC, 'meshes', n + '.fbx'), DST, f) for n in MESH])
        gear = unreal.load_asset(GEAR)
        log = ['MI_MedicStaff: ' + ', '.join(child_mi('MI_MedicStaff', gear, {'BaseColorTex': 'T_MedicStaff_BC', 'ORMTex': 'T_MedicStaff_ORM', 'NormalTex': 'T_MedicStaff_N'})),
               'MI_MedicSatchel502: ' + ', '.join(child_mi('MI_MedicSatchel502', gear, {'BaseColorTex': 'T_MedicSatchel502_BC', 'ORMTex': 'T_MedicSatchel502_ORM', 'NormalTex': 'T_MedicSatchel502_N'}))]
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        for n, mi in (('SM_MedicStaff', 'MI_MedicStaff'), ('SM_MedicSatchel502', 'MI_MedicSatchel502')):
            sm = unreal.load_asset(DST + '/' + n); sm.set_material(0, unreal.load_asset(DST + '/' + mi)); sub.remove_collisions(sm); EAL.save_loaded_asset(sm)
        # cape: child of the soldier's cape MI so Cloth shading / Masked / HideBackFlap stay exactly as on the soldiers
        cpm = unreal.load_asset(cp); names = param_names(cpm)
        texmap = {k: v for k, v in ((guess(names['texture'], 'BC', 'basecolor', 'albedo', 'diffuse', 'color'), 'T_MedicCape_BC'),
                                    (guess(names['texture'], 'N', 'normal'), 'T_MedicCape_N'), (guess(names['texture'], 'orm', 'rough', 'mask'), 'T_MedicCape_ORM')) if k}
        vec = {k: LINEN for k in [guess(names['vector'], 'tint', 'color')] if k}
        log.append('MI_MedicCape: ' + (', '.join(child_mi('MI_MedicCape', cpm, texmap, vec)) or 'NO params matched, it is a plain child: see README'))
        for l in log: print('  ' + l)
        print('APPLIED: Medic502 assets saved in %s. BP_Medic wiring is the next seat\'s job (README).' % DST)
