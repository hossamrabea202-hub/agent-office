# #322 Flesh Brutes in waves, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/brute-waves-322/setup_brute322_ue.py" --dry-run            only reports
#   py "<repo>/handoffs/brute-waves-322/setup_brute322_ue.py"                      makes BP_BruteDirector (empty actor)
#   py ".../setup_brute322_ue.py" --finish [--dry-run]                             after the BPVar + graph paste: sets
#        BruteClass = BP_FleshBrute (found in the project) and places one BruteDirector in the level
#   py ".../setup_brute322_ue.py" --remove-gate-brutes [--dry-run]                 removes the BP_FleshBrute actors placed in the
#        level (the ones at BreachSpot A/B/C, owner: "needs to be removed"); every removed one is logged with its label,
#        location and rotation in removed_brutes.txt, so it can be put back by hand
import os, sys, unreal

A = sys.argv[1:]
DRY, FINISH, REMOVE = '--dry-run' in A, '--finish' in A, '--remove-gate-brutes' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\brute-waves-322'
DST, NAME, LABEL = '/Game/CastleDefender/Gameplay/Castle', 'BP_BruteDirector', 'BruteDirector'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
AR = unreal.AssetRegistryHelpers.get_asset_registry()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#322 brute waves setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def brute_class():
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')], package_paths=['/Game'], recursive_paths=True)
    hits = [ad for ad in AR.get_assets(flt) if str(ad.asset_name) == 'BP_FleshBrute']
    if not hits: return None
    p = str(hits[0].package_name); log.append('BP_FleshBrute: ' + p)
    return unreal.load_class(None, '%s.BP_FleshBrute_C' % p)


def is_brute(a): return 'FleshBrute' in a.get_class().get_name()


if REMOVE:
    found = [a for a in EAS.get_all_level_actors() if is_brute(a)]
    rows = ['%s | %s | %s' % (a.get_actor_label(), a.get_actor_location(), a.get_actor_rotation()) for a in found]
    log.append('placed brutes: %d' % len(found)); log += ['  ' + r for r in rows]
    if found and not DRY:
        open(os.path.join(HERE, 'removed_brutes.txt'), 'a').write('\n'.join(rows) + '\n')
        for a in found: EAS.destroy_actor(a)
        unreal.EditorLevelLibrary.save_current_level(); log.append('removed + level saved (put back by hand from removed_brutes.txt)')
elif FINISH:
    bp = unreal.load_asset(DST + '/' + NAME)
    if not bp: raise SystemExit('run the setup without --finish first')
    cls = brute_class()
    if not cls: log.append('BP_FleshBrute NOT FOUND: set BruteClass on BP_BruteDirector by hand')
    elif not DRY:
        cdo = unreal.get_default_object(bp.generated_class())
        try:
            cdo.set_editor_property('BruteClass', cls); EAL.save_asset(DST + '/' + NAME); log.append('BruteClass = BP_FleshBrute')
        except Exception as e:
            log.append('could not set BruteClass (%s): set it by hand in Class Defaults' % e)
    if [a for a in EAS.get_all_level_actors() if a.get_actor_label() == LABEL]: log.append('BruteDirector already placed')
    else:
        log.append('place BruteDirector at the origin')
        if not DRY:
            act = EAS.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); act.set_actor_label(LABEL)
            unreal.EditorLevelLibrary.save_current_level()
else:
    path = DST + '/' + NAME
    if EAL.does_asset_exist(path): log.append('reusing ' + path)
    else:
        log.append('create ' + path)
        if not DRY:
            f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
            bp = AT.create_asset(NAME, DST, unreal.Blueprint, f); BEL.compile_blueprint(bp); EAL.save_asset(path)
    log.append('Next: README step 2 (9 BPVar lines), step 3 (graph paste), then --finish')
out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_brute322.txt'), 'a').write(out + '\n')
unreal.log(out)
