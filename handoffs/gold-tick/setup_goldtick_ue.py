# Gold ticks up, step 1 (i5 / adjustedfilm, 2026-11-02). UE 5.8 Python.   [--dry-run]
#   - creates /Game/CastleDefender/Gameplay/Castle/BPC_GoldTick (ActorComponent) with variables Shown (double) and
#     ShownInt (int), Tick enabled AND ticking while the game is paused (the shop pauses; a buy must still animate);
#   - backs up BP_SkillTreeHUD to BP_SkillTreeHUD_BACKUP_GT (once) and adds the component "GoldTick" to it.
# Then: paste build/BPC_GoldTick_graph.txt into BPC_GoldTick's EventGraph (compile, save), paste
# build/SkillTreeHUD_GoldTickHook_graph.txt into BP_SkillTreeHUD's EventGraph, run rewire_goldtick_ue.py.
import sys, unreal
DRY = '--dry-run' in sys.argv
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
DST = '/Game/CastleDefender/Gameplay/Castle'
GT, ST, BK = DST + '/BPC_GoldTick', DST + '/BP_SkillTreeHUD', DST + '/BP_SkillTreeHUD_BACKUP_GT'
log = ['gold tick setup' + (' (DRY RUN)' if DRY else '')]

if EAL.does_asset_exist(GT): bp = unreal.load_asset(GT); log.append('reusing ' + GT)
elif DRY: bp = None; log.append('would create ' + GT)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    bp = AT.create_asset('BPC_GoldTick', DST, unreal.Blueprint, f); log.append('created ' + GT)
if bp:
    have = {str(v) for v in BEL.get_member_variable_names(bp)} if hasattr(BEL, 'get_member_variable_names') else set()
    for n, t in (('Shown', 'real'), ('ShownInt', 'int')):
        if n in have: log.append('  var %s exists' % n); continue
        log.append('  + var %s (%s)' % (n, t))
        if not DRY and not BEL.add_member_variable(bp, n, BEL.get_basic_type_by_name(t)): log.append('  (add %s returned False: exists?)' % n)
    if not DRY:
        BEL.compile_blueprint(bp)
        cdo = unreal.get_default_object(bp.generated_class())
        tick = cdo.get_editor_property('primary_component_tick')
        tick.set_editor_property('can_ever_tick', True); tick.set_editor_property('start_with_tick_enabled', True)
        tick.set_editor_property('tick_even_when_paused', True)
        cdo.set_editor_property('primary_component_tick', tick)
        EAL.save_asset(GT); log.append('  tick: ever, start enabled, even when paused; saved')

st = unreal.load_asset(ST)
hs = SDS.k2_gather_subobject_data_for_blueprint(st)
names = {str(SDL.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))) for h in hs}
if 'GoldTick' in names: log.append('BP_SkillTreeHUD already has GoldTick')
else:
    log.append('backup %s %s' % (BK, 'exists' if EAL.does_asset_exist(BK) else '(will be made)'))
    log.append('add component GoldTick to BP_SkillTreeHUD')
    if not DRY:
        if not EAL.does_asset_exist(BK): EAL.duplicate_asset(ST, BK); EAL.save_asset(BK)
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=bp.generated_class(), blueprint_context=st))
        if not SDL.is_handle_valid(h): raise RuntimeError('add GoldTick: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('GoldTick'))
        BEL.compile_blueprint(st); EAL.save_asset(ST); log.append('  added, compiled, saved')
print('\n'.join(log))
