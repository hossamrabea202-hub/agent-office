# #74 health potions, step 1 (i5 core, 2026-11-01). UE 5.8 Python.  [--dry-run]
#   1. imports laptop2's icon assets/laptop2/WeaponPack/PotionHealth/icon/T_Item_Potion_Health.png -> /Game/CastleDefender/UI
#      (if missing; UI group, no mips)
#   2. creates /Game/CastleDefender/Gameplay/Castle/BPC_PotionBelt (ActorComponent) + variables and defaults:
#      Potions 1 (one to start), HealLeft, CoolUntil, LastT, IconTex, MaxHP 100, HealPct 0.35, HealDur 3, Cooldown 8,
#      Price 60, PanelX 40, PanelY 905 (1080p units; the APOTHECARY row in Vesna's shop)
#   3. adds the component 'PotionBelt' to BP_ZombieHUD (backup BP_ZombieHUD_BACKUP74 once). Not saved here: the hook
#      paste + rewire_hook74_ue.py compile and save BP_ZombieHUD in one go.
import sys, unreal
DRY = '--dry-run' in sys.argv
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
ICON = '/Game/CastleDefender/UI/T_Item_Potion_Health'
PNG = 'C:/Users/hossam.rabea/agent-office/assets/laptop2/WeaponPack/PotionHealth/icon/T_Item_Potion_Health.png'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_PotionBelt'
ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
log = ['#74 setup' + (' (DRY RUN)' if DRY else '')]
for p in (ZHUD, HERO, '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree', '/Game/CastleDefender/UI/Trade/SFX_TradeBuy', '/Game/CastleDefender/UI/Trade/SFX_TradeFail'):
    log.append('%-62s %s' % (p, 'ok' if EAL.does_asset_exist(p) else 'MISSING'))
hv = [str(n) for n in BEL.list_member_variable_names(unreal.load_asset(HERO))]
log.append('hero DamageTaken %s, IsDead %s' % ('DamageTaken' in hv, 'IsDead' in hv))
if not DRY:
    if not EAL.does_asset_exist(ICON):
        t = unreal.AssetImportTask(); t.filename = PNG; t.destination_path = '/Game/CastleDefender/UI'; t.automated = True; t.replace_existing = True
        at.import_asset_tasks([t])
    tex = unreal.load_asset(ICON)
    tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    EAL.save_asset(ICON)
    path = COMP_DIR + '/' + COMP
    if EAL.does_asset_exist(path): bp = unreal.load_asset(path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        bp = at.create_asset(COMP, COMP_DIR, unreal.Blueprint, f)
    I, Dd = BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('real')
    assert 'PinSubCategory="double"' in Dd.export_text(), 'real is not double: ' + Dd.export_text()
    DEF = {'Potions': (I, 1), 'HealLeft': (Dd, 0.0), 'CoolUntil': (Dd, 0.0), 'LastT': (Dd, 0.0), 'MaxHP': (Dd, 100.0), 'HealPct': (Dd, 0.35),
           'HealDur': (Dd, 3.0), 'Cooldown': (Dd, 8.0), 'Price': (I, 60), 'PanelX': (Dd, 40.0), 'PanelY': (Dd, 905.0)}
    have = [str(n) for n in BEL.list_member_variable_names(bp)]
    for n, (t_, _) in DEF.items():
        if n not in have and not BEL.add_member_variable(bp, n, t_): raise RuntimeError('could not add ' + n)
    if 'IconTex' not in have and not BEL.add_member_variable(bp, 'IconTex', BEL.get_object_reference_type(unreal.Texture2D)): raise RuntimeError('IconTex')
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(BEL.generated_class(bp))
    for n, (_, v) in DEF.items(): cdo.set_editor_property(n, v)
    cdo.set_editor_property('IconTex', tex)
    EAL.save_asset(path); log.append('component ready: ' + path)
    if not EAL.does_asset_exist(ZHUD + '_BACKUP74'): EAL.duplicate_asset(ZHUD, ZHUD + '_BACKUP74'); EAL.save_asset(ZHUD + '_BACKUP74')
    hud = unreal.load_asset(ZHUD)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hud)
    names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
    if 'PotionBelt' in names: log.append('BP_ZombieHUD already has PotionBelt')
    else:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=BEL.generated_class(bp), blueprint_context=hud))
        if not fail.is_empty(): raise RuntimeError('add PotionBelt: %s' % fail)
        sds.rename_subobject(h, unreal.Text('PotionBelt')); log.append('BP_ZombieHUD: added PotionBelt (not saved yet)')
print('\n'.join(log))
