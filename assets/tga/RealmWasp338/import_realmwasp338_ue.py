# Realm wasp v2 (#338, TGA PC, 2026-11-06): import the rebuilt zombie hornet into UE as NEW assets.
#   py "<repo>/assets/tga/RealmWasp338/import_realmwasp338_ue.py"            dry run (default): checks files + live paths, changes nothing
#   py ".../import_realmwasp338_ue.py" --apply     imports into /Game/CastleDefender/Characters/Enemies/RealmWasp/V2 (only that folder)
#   py ".../import_realmwasp338_ue.py" --swap      AFTER the owner's OK on the renders: BP_RealmWasp uses v2. Backs up the 10 v1 assets it
#                                                  references to RealmWasp/V1_Backup, then consolidates each v1 asset into its v2 twin
#                                                  (the BP's mesh / anim / MI literals then load v2; nothing else is edited)
#   py ".../import_realmwasp338_ue.py" --unswap    undo --swap: consolidates the v2 twins into the V1_Backup copies (BP back on v1)
#   py ".../import_realmwasp338_ue.py" --revert    deletes only the V2 folder (run --unswap first if you swapped)
# v2 = same 32 bone names as v1 (+ wingblur_L/R), same 5 clip names, same material slot order (0 body, 1 wings; + 2 hair, 3 wing blur),
# so BP_RealmWasp's SetSkeletalMeshAsset / PlayAnimation / SetMaterial(0|1) nodes keep working unchanged.
import os, sys
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Game/CastleDefender/Characters/Enemies/RealmWasp'
DST = ROOT + '/V2'; BAK = ROOT + '/V1_Backup'
BP = ROOT + '/BP_RealmWasp'
SKINS = ('Ember', 'Blight')
CLIPS = ('Hover', 'Fly', 'Dive', 'Sting', 'Death')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
args = sys.argv[1:]
MODE = next((a for a in ('--apply', '--swap', '--unswap', '--revert') if a in args), '--dry-run')
C = unreal.TextureCompressionSettings
TEX = [('T_RealmWasp_Body_%s_BC' % s, True, C.TC_DEFAULT) for s in SKINS]
TEX += [('T_RealmWasp_Body_%s_ORM' % s, False, C.TC_MASKS) for s in SKINS]
TEX += [('T_RealmWasp_Body_N', False, C.TC_NORMALMAP), ('T_RealmWasp_Body_SSE', False, C.TC_MASKS)]
TEX += [('T_RealmWasp_Wings_%s_BCA' % s, True, C.TC_DEFAULT) for s in SKINS] + [('T_RealmWasp_WingBlur_%s_BCA' % s, True, C.TC_DEFAULT) for s in SKINS]
FBX = os.path.join(SRC, 'SK_RealmWasp.fbx')
# the 10 v1 assets BP_RealmWasp references (from the live export, handoffs/aaa-472/live/BP_RealmWasp.T3D)
PAIRS = [('SK_RealmWasp', 'SK_RealmWasp')] + [('A_RealmWasp_' + c, 'A_RealmWasp_' + c) for c in CLIPS]
PAIRS += [('MI_RealmWasp_Body_' + s, 'MI_RealmWasp_Body_' + s) for s in SKINS] + [('MI_RealmWasp_Wings_' + s, 'MI_RealmWasp_Wings_' + s) for s in SKINS]

def check():
    bad = []
    for n, _, _ in TEX:
        if not os.path.isfile(os.path.join(SRC, 'textures', n + '.png')): bad.append('missing textures/%s.png' % n)
    if not os.path.isfile(FBX): bad.append('missing SK_RealmWasp.fbx')
    if not EAL.does_asset_exist(BP): bad.append('BP_RealmWasp not at ' + BP)
    for v1, _ in PAIRS:
        if not EAL.does_asset_exist(ROOT + '/' + v1): bad.append('v1 asset missing: %s/%s' % (ROOT, v1))
    return bad

def task(path, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
def param(m, cls, name, x, y, tex=None, sampler=None, default=None):
    e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
    if tex: e.set_editor_property('texture', unreal.load_asset(tex))
    if sampler: e.set_editor_property('sampler_type', sampler)
    if default is not None: e.set_editor_property('default_value', default)
    return e
def expr(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e
def link(a, ao, b, bi): MEL.connect_material_expressions(a, ao, b, bi)
def new_mat(name):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): EAL.delete_asset(path)                 # only ever inside V2 (our own folder)
    m = tools.create_asset(name, DST, unreal.Material, unreal.MaterialFactoryNew()); m.set_editor_property('used_with_skeletal_mesh', True); return m, path
LC = unreal.LinearColor

def build_materials():
    # ---- body: Subsurface shading (thin chitin, tissue, fungus scatter), the zombie skin params, spore glow, hit flash ----
    m, BODY = new_mat('M_RealmWasp_Body')
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_SUBSURFACE)
    bc = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -1400, -300, DST + '/T_RealmWasp_Body_Ember_BC')
    orm = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -1400, 100, DST + '/T_RealmWasp_Body_Ember_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -1400, 450, DST + '/T_RealmWasp_Body_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    sse = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'SSE', -1400, 800, DST + '/T_RealmWasp_Body_SSE', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    tint = param(m, unreal.MaterialExpressionVectorParameter, 'Tint', -1400, -560, default=LC(1, 1, 1, 1))
    tamt = param(m, unreal.MaterialExpressionScalarParameter, 'TintAmount', -1400, -460, default=0.0)
    wet = param(m, unreal.MaterialExpressionScalarParameter, 'Wetness', -1400, 350, default=0.0)
    hit = param(m, unreal.MaterialExpressionScalarParameter, 'HitT', -1400, -660, default=0.0)
    sporec = param(m, unreal.MaterialExpressionVectorParameter, 'SporeColor', -1000, 900, default=LC(1.0, 0.62, 0.25, 1))
    sporeg = param(m, unreal.MaterialExpressionScalarParameter, 'SporeGlow', -1000, 1000, default=3.0)
    sssa = param(m, unreal.MaterialExpressionScalarParameter, 'SubsurfaceAmount', -1000, 700, default=0.6)
    mul = expr(m, unreal.MaterialExpressionMultiply, -1100, -400); link(bc, 'RGB', mul, 'A'); link(tint, '', mul, 'B')
    tl = expr(m, unreal.MaterialExpressionLinearInterpolate, -900, -350); link(bc, 'RGB', tl, 'A'); link(mul, '', tl, 'B'); link(tamt, '', tl, 'Alpha')
    half = expr(m, unreal.MaterialExpressionMultiply, -750, -220, const_b=0.8); link(tl, '', half, 'A')
    dark = expr(m, unreal.MaterialExpressionLinearInterpolate, -600, -320); link(tl, '', dark, 'A'); link(half, '', dark, 'B'); link(wet, '', dark, 'Alpha')
    rg = expr(m, unreal.MaterialExpressionLinearInterpolate, -600, 120, const_b=0.15); link(orm, 'G', rg, 'A'); link(wet, '', rg, 'Alpha')
    ssc = expr(m, unreal.MaterialExpressionMultiply, -600, 560); warm = expr(m, unreal.MaterialExpressionConstant3Vector, -800, 520, constant=LC(1.0, 0.55, 0.3, 1))
    link(tl, '', ssc, 'A'); link(warm, '', ssc, 'B')
    sop = expr(m, unreal.MaterialExpressionMultiply, -600, 720); link(sse, 'R', sop, 'A'); link(sssa, '', sop, 'B')
    gl1 = expr(m, unreal.MaterialExpressionMultiply, -750, 900); link(sse, 'G', gl1, 'A'); link(sporec, '', gl1, 'B')
    gl2 = expr(m, unreal.MaterialExpressionMultiply, -600, 900); link(gl1, '', gl2, 'A'); link(sporeg, '', gl2, 'B')
    flash = expr(m, unreal.MaterialExpressionMultiply, -600, -560); hcol = expr(m, unreal.MaterialExpressionConstant3Vector, -800, -640, constant=LC(4.0, 0.25, 0.1, 1))
    link(hcol, '', flash, 'A'); link(hit, '', flash, 'B')
    emis = expr(m, unreal.MaterialExpressionAdd, -400, -200); link(flash, '', emis, 'A'); link(gl2, '', emis, 'B')
    P = unreal.MaterialProperty
    MEL.connect_material_property(dark, '', P.MP_BASE_COLOR); MEL.connect_material_property(rg, '', P.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', P.MP_AMBIENT_OCCLUSION); MEL.connect_material_property(nrm, 'RGB', P.MP_NORMAL)
    MEL.connect_material_property(emis, '', P.MP_EMISSIVE_COLOR); MEL.connect_material_property(ssc, '', P.MP_SUBSURFACE_COLOR)
    MEL.connect_material_property(sop, '', P.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(BODY)
    # ---- wings: translucent, two-sided, per-pixel lit; WingBlur (v1 param) still fades the membrane ----
    m, WING = new_mat('M_RealmWasp_Wings')
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT); m.set_editor_property('two_sided', True)
    m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    t = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'WingTex', -1000, 0, DST + '/T_RealmWasp_Wings_Ember_BCA')
    blur = param(m, unreal.MaterialExpressionScalarParameter, 'WingBlur', -1000, 300, default=0.0)
    wop = param(m, unreal.MaterialExpressionScalarParameter, 'WingOpacity', -1000, 400, default=1.0)
    k = expr(m, unreal.MaterialExpressionMultiply, -750, 300, const_b=0.6); link(blur, '', k, 'A')
    om = expr(m, unreal.MaterialExpressionOneMinus, -600, 300); link(k, '', om, '')
    a = expr(m, unreal.MaterialExpressionMultiply, -450, 200); link(t, 'A', a, 'A'); link(om, '', a, 'B')
    a2 = expr(m, unreal.MaterialExpressionMultiply, -300, 250); link(a, '', a2, 'A'); link(wop, '', a2, 'B')
    rough = expr(m, unreal.MaterialExpressionConstant, -450, 100, r=0.25)
    MEL.connect_material_property(t, 'RGB', P.MP_BASE_COLOR); MEL.connect_material_property(rough, '', P.MP_ROUGHNESS)
    MEL.connect_material_property(a2, '', P.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(WING)
    # ---- wing blur cards: translucent, faint, shimmering (the speed of the wingbeat in Play) ----
    m, BLUR = new_mat('M_RealmWasp_WingBlur')
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT); m.set_editor_property('two_sided', True)
    m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    t = param(m, unreal.MaterialExpressionTextureSampleParameter2D, 'BlurTex', -1000, 0, DST + '/T_RealmWasp_WingBlur_Ember_BCA')
    bop = param(m, unreal.MaterialExpressionScalarParameter, 'BlurOpacity', -1000, 300, default=1.0)
    tm = expr(m, unreal.MaterialExpressionTime, -1000, 450); tk = expr(m, unreal.MaterialExpressionMultiply, -850, 450, const_b=40.0); link(tm, '', tk, 'A')
    sn = expr(m, unreal.MaterialExpressionSine, -700, 450); link(tk, '', sn, '')
    sh = expr(m, unreal.MaterialExpressionMultiply, -550, 450, const_b=0.15); link(sn, '', sh, 'A')
    sh2 = expr(m, unreal.MaterialExpressionAdd, -400, 450, const_b=0.85); link(sh, '', sh2, 'A')
    a = expr(m, unreal.MaterialExpressionMultiply, -450, 200); link(t, 'A', a, 'A'); link(bop, '', a, 'B')
    a2 = expr(m, unreal.MaterialExpressionMultiply, -250, 250); link(a, '', a2, 'A'); link(sh2, '', a2, 'B')
    rough = expr(m, unreal.MaterialExpressionConstant, -450, 100, r=0.35)
    MEL.connect_material_property(t, 'RGB', P.MP_BASE_COLOR); MEL.connect_material_property(rough, '', P.MP_ROUGHNESS)
    MEL.connect_material_property(a2, '', P.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(BLUR)
    # ---- hair (setae): root-to-tip gradient along UV V, matte, a little scatter ----
    m, HAIR = new_mat('M_RealmWasp_Hair')
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_SUBSURFACE)
    root = param(m, unreal.MaterialExpressionVectorParameter, 'HairRoot', -1000, -200, default=LC(0.045, 0.032, 0.022, 1))
    tip = param(m, unreal.MaterialExpressionVectorParameter, 'HairTip', -1000, -50, default=LC(0.42, 0.30, 0.14, 1))
    uv = expr(m, unreal.MaterialExpressionTextureCoordinate, -1000, 120); mk = expr(m, unreal.MaterialExpressionComponentMask, -850, 120, r=False, g=True, b=False, a=False)
    link(uv, '', mk, '')
    k3 = expr(m, unreal.MaterialExpressionMultiply, -750, 120, const_b=2.85); link(mk, '', k3, 'A')     # dark only at the root (35 %)
    sat = expr(m, unreal.MaterialExpressionSaturate, -650, 120); link(k3, '', sat, '')
    lp = expr(m, unreal.MaterialExpressionLinearInterpolate, -600, -120); link(root, '', lp, 'A'); link(tip, '', lp, 'B'); link(sat, '', lp, 'Alpha')
    rough = expr(m, unreal.MaterialExpressionConstant, -600, 60, r=0.62); op = expr(m, unreal.MaterialExpressionConstant, -600, 160, r=0.3)
    MEL.connect_material_property(lp, '', P.MP_BASE_COLOR); MEL.connect_material_property(rough, '', P.MP_ROUGHNESS)
    MEL.connect_material_property(lp, '', P.MP_SUBSURFACE_COLOR); MEL.connect_material_property(op, '', P.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(HAIR)
    return BODY, WING, BLUR, HAIR

def mi(name, parent, tex=None, vec=None):
    path = DST + '/' + name
    inst = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, unreal.load_asset(parent))
    for p, tn in (tex or {}).items(): MEL.set_material_instance_texture_parameter_value(inst, p, unreal.load_asset(DST + '/' + tn))
    for p, v in (vec or {}).items(): MEL.set_material_instance_vector_parameter_value(inst, p, v)
    EAL.save_asset(path); return inst

def apply():
    tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
    for n, srgb, comp in TEX:
        t = unreal.load_asset('%s/%s' % (DST, n)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)                # already DirectX
        EAL.save_loaded_asset(t)
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = True; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    f.import_materials = False; f.import_textures = False; f.import_animations = True; f.create_physics_asset = True
    f.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    f.anim_sequence_import_data.set_editor_property('import_bone_tracks', True)
    tools.import_asset_tasks([task(FBX, f)])
    for path in EAL.list_assets(DST, recursive=False):                                         # FBX takes -> A_RealmWasp_<Clip>
        name = path.split('.')[-1]
        if 'A_RealmWasp_' in name and not name.startswith('A_RealmWasp_'):
            new = DST + '/' + name[name.index('A_RealmWasp_'):]
            if EAL.does_asset_exist(new): EAL.delete_asset(new)
            EAL.rename_asset(path.split('.')[0], new)
    BODY, WING, BLUR, HAIR = build_materials()
    HAIRC = {'Ember': (LC(0.045, 0.032, 0.022, 1), LC(0.42, 0.30, 0.14, 1)), 'Blight': (LC(0.04, 0.033, 0.04, 1), LC(0.36, 0.34, 0.24, 1))}
    for s in SKINS:
        mi('MI_RealmWasp_Body_' + s, BODY, {'BaseColor': 'T_RealmWasp_Body_%s_BC' % s, 'ORM': 'T_RealmWasp_Body_%s_ORM' % s},
           {'SporeColor': LC(1.0, 0.62, 0.25, 1) if s == 'Ember' else LC(0.55, 1.0, 0.45, 1)})
        mi('MI_RealmWasp_Wings_' + s, WING, {'WingTex': 'T_RealmWasp_Wings_%s_BCA' % s})
        mi('MI_RealmWasp_WingBlur_' + s, BLUR, {'BlurTex': 'T_RealmWasp_WingBlur_%s_BCA' % s})
        mi('MI_RealmWasp_Hair_' + s, HAIR, vec={'HairRoot': HAIRC[s][0], 'HairTip': HAIRC[s][1]})
    sk = unreal.load_asset(DST + '/SK_RealmWasp'); mats = sk.get_editor_property('materials'); log = []
    want = {'Body': 'MI_RealmWasp_Body_Ember', 'Wings': 'MI_RealmWasp_Wings_Ember', 'Hair': 'MI_RealmWasp_Hair_Ember', 'WingBlur': 'MI_RealmWasp_WingBlur_Ember'}
    for i, sm in enumerate(mats):
        slot = str(sm.get_editor_property('material_slot_name')); key = slot.replace('M_RealmWasp_', '')
        if key in want: sm.set_editor_property('material_interface', unreal.load_asset(DST + '/' + want[key]))
        log.append('%d:%s' % (i, slot))
    sk.set_editor_property('materials', mats); EAL.save_loaded_asset(sk)
    order_ok = len(mats) >= 2 and 'Body' in log[0] and 'Wings' in log[1]
    print('  material slots: ' + ', '.join(log) + ('  (OK: BP sets 0 = body, 1 = wings)' if order_ok else '  MISMATCH: BP_RealmWasp sets element 0 = body, 1 = wings'))
    print('APPLY OK: %s (SK + 5 anims + 4 masters + 8 MIs + %d textures). The game still uses v1 until --swap.' % (DST, len(TEX)))

def swap(undo=False):
    if not EAL.does_directory_exist(DST): raise SystemExit('STOP: run --apply first')
    done = []
    for v1, v2 in PAIRS:
        src1, src2, bak = ROOT + '/' + v1, DST + '/' + v2, BAK + '/' + v1
        if not undo:
            if not EAL.does_asset_exist(bak): EAL.duplicate_asset(src1, bak)
            EAL.consolidate_assets(unreal.load_asset(src2), [unreal.load_asset(src1)])
        else:
            if not EAL.does_asset_exist(bak) or not EAL.does_asset_exist(src2): print('  skip %s (no backup or no v2)' % v1); continue
            EAL.consolidate_assets(unreal.load_asset(bak), [unreal.load_asset(src2)])
        done.append(v1)
    EAL.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
    print(('UNSWAP OK: BP_RealmWasp back on the v1 copies in ' + BAK) if undo else ('SWAP OK: BP_RealmWasp now loads v2 for: ' + ', '.join(done) + '. Backup: ' + BAK))

print('Realm wasp v2 (#338): mode %s' % MODE)
if MODE == '--revert':
    gone = EAL.list_assets(DST, recursive=True, include_folder=False) if EAL.does_directory_exist(DST) else []
    for a in gone: EAL.delete_asset(a)
    print('REVERTED: deleted %d assets in %s (only what --apply made)' % (len(gone), DST))
elif MODE in ('--swap', '--unswap'):
    swap(undo=MODE == '--unswap')
else:
    bad = check()
    print('  %d textures, FBX %s, into %s' % (len(TEX), 'found' if os.path.isfile(FBX) else 'MISSING', DST))
    print('  V2 folder exists already: %s (apply re-imports into it, nothing outside it changes)' % EAL.does_directory_exist(DST))
    print('  --swap would consolidate: ' + ', '.join(v for v, _ in PAIRS))
    for b in bad: print('MISMATCH', b)
    if bad: raise SystemExit('STOP: %d problem(s), nothing changed' % len(bad))
    if MODE == '--apply': apply()
    else: print('DRY RUN OK: nothing changed. Next: --apply')
