# #411 castle scroll, step 1 (i5 core, 2026-11-01). UE 5.8 Python.
#   py ".../setup_scroll411_ue.py" --dry-run    only reports
#   py ".../setup_scroll411_ue.py"              does it:
#     1. imports build/T_HUD_CastleKey.png -> /Game/CastleDefender/UI/HUD/T_HUD_CastleKey (UI group, no mips, sRGB)
#     2. creates /Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll (ActorComponent) with Open, T, LastT, Mid, IconTex,
#        ScrollMat (defaults: the icon, M_NoticeBanner), compiles, saves
#     3. backs up BP_ZombieHUD -> BP_ZombieHUD_BACKUP411 (once), adds the component 'CastleScroll' to BP_ZombieHUD
#        (not saved here: the hook paste + rewire_hook411_ue.py compile and save it in one go)
import sys, unreal
DRY = '--dry-run' in sys.argv
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-scroll-411'
ICON = '/Game/CastleDefender/UI/HUD/T_HUD_CastleKey'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_CastleScroll'
ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
MAT = '/Game/CastleDefender/UI/Notices/M_NoticeBanner'
log = ['#411 setup' + (' (DRY RUN)' if DRY else '')]
for p in (ZHUD, MAT, '/Game/CastleDefender/UI/Fonts/Font_Cinzel', '/Game/CastleDefender/UI/Trade/SFX_TradeSwipe'):
    log.append('%-60s %s' % (p, 'ok' if EAL.does_asset_exist(p) else 'MISSING'))
log.append('icon %s, component %s, backup %s' % ('exists' if EAL.does_asset_exist(ICON) else 'new', 'exists' if EAL.does_asset_exist(COMP_DIR + '/' + COMP) else 'new',
                                                 'exists' if EAL.does_asset_exist(ZHUD + '_BACKUP411') else 'new'))
if not DRY:
    # 1. icon
    if not EAL.does_asset_exist(ICON):
        t = unreal.AssetImportTask(); t.filename = HERE + '/build/T_HUD_CastleKey.png'; t.destination_path = '/Game/CastleDefender/UI/HUD'
        t.automated = True; t.save = False; t.replace_existing = True
        at.import_asset_tasks([t])
    tex = unreal.load_asset(ICON)
    tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property('srgb', True)
    EAL.save_asset(ICON); log.append('icon imported: %s' % ICON)
    # 2. component + variables
    path = COMP_DIR + '/' + COMP
    if EAL.does_asset_exist(path): bp = unreal.load_asset(path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        bp = at.create_asset(COMP, COMP_DIR, unreal.Blueprint, f)
    I, Dd, Bo = BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('bool')
    assert 'PinSubCategory="double"' in Dd.export_text(), 'real is not double: ' + Dd.export_text()
    OBJ = BEL.get_object_reference_type
    VARS = {'Open': Bo, 'T': Dd, 'LastT': Dd, 'Mid': OBJ(unreal.MaterialInstanceDynamic), 'IconTex': OBJ(unreal.Texture2D), 'ScrollMat': OBJ(unreal.MaterialInterface)}
    have = [str(n) for n in BEL.list_member_variable_names(bp)]
    for n, t_ in VARS.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t_): raise RuntimeError('could not add ' + n)
            log.append('  + %s.%s' % (COMP, n))
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(BEL.generated_class(bp))
    cdo.set_editor_property('IconTex', tex); cdo.set_editor_property('ScrollMat', unreal.load_asset(MAT))
    EAL.save_asset(path); log.append('component ready: ' + path)
    # 3. BP_ZombieHUD: backup once, add the component
    if not EAL.does_asset_exist(ZHUD + '_BACKUP411'):
        EAL.duplicate_asset(ZHUD, ZHUD + '_BACKUP411'); EAL.save_asset(ZHUD + '_BACKUP411'); log.append('backup: BP_ZombieHUD_BACKUP411')
    hud = unreal.load_asset(ZHUD)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hud)
    names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
    if 'CastleScroll' in names: log.append('BP_ZombieHUD already has CastleScroll')
    else:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=BEL.generated_class(bp), blueprint_context=hud))
        if not fail.is_empty(): raise RuntimeError('add CastleScroll: %s' % fail)
        sds.rename_subobject(h, unreal.Text('CastleScroll')); log.append('BP_ZombieHUD: added CastleScroll (not saved yet)')
out = '\n'.join(log); unreal.log(out); print(out)
open(HERE + '/setup_scroll411.txt', 'w').write(out)
