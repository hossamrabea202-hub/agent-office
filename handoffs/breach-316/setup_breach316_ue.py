# #316 breach FX, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/breach-316/setup_breach316_ue.py" --dry-run     only reports
#   py "<repo>/handoffs/breach-316/setup_breach316_ue.py"               imports SFX_WallBreach, makes BP_BreachFX (empty actor)
#   py ".../setup_breach316_ue.py" --place [--dry-run]                 after the BPVar + graph paste: places one BreachFX
import os, sys, unreal
A = sys.argv[1:]; DRY, PLACE = '--dry-run' in A, '--place' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\breach-316'
DST = '/Game/CastleDefender/Gameplay/Siege/Breach'
SFX = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'Breach316', 'sfx', 'SFX_WallBreach.wav'))
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#316 breach FX setup' + (' (DRY RUN, nothing written)' if DRY else '')]
if PLACE:
    if [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'BreachFX']: log.append('BreachFX already placed')
    else:
        log.append('place BreachFX at the origin')
        if not DRY:
            act = EAS.spawn_actor_from_class(unreal.load_class(None, DST + '/BP_BreachFX.BP_BreachFX_C'), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
            act.set_actor_label('BreachFX'); unreal.EditorLevelLibrary.save_current_level()
else:
    log.append('import SFX_WallBreach' + ('' if os.path.exists(SFX) else ' (MISSING ' + SFX + ')'))
    if not DRY and os.path.exists(SFX):
        t = unreal.AssetImportTask()
        for k, v in (('filename', SFX), ('destination_path', DST), ('destination_name', 'SFX_WallBreach'), ('replace_existing', True), ('automated', True), ('save', True)):
            t.set_editor_property(k, v)
        AT.import_asset_tasks([t])
    p = DST + '/BP_BreachFX'
    if EAL.does_asset_exist(p): log.append('reusing ' + p)
    else:
        log.append('create ' + p)
        if not DRY:
            f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
            bp = AT.create_asset('BP_BreachFX', DST, unreal.Blueprint, f); BEL.compile_blueprint(bp); EAL.save_asset(p)
out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_breach316.txt'), 'a').write(out + '\n')
unreal.log(out)
