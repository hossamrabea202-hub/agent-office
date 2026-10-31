# #341 fix: makes /Game/CastleDefender/Environment/Cave/BP_UndergroundFog (Actor) and places one (label UndergroundFog,
# tag Mine297, so place_mine297 --remove takes it too). UE 5.3 Python, safe to re-run.  --dry-run supported.
import sys, unreal
DRY = '--dry-run' in sys.argv
P = '/Game/CastleDefender/Environment/Cave/BP_UndergroundFog'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#341 underground fog' + (' (DRY RUN)' if DRY else ''), ('reuse ' if EAL.does_asset_exist(P) else 'create ') + P]
if not DRY:
    bp = unreal.load_asset(P)
    if not bp:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_UndergroundFog', P.rsplit('/', 1)[0], unreal.Blueprint, f)
    BEL.compile_blueprint(bp); EAL.save_asset(P)
    if not [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'UndergroundFog']:
        a = EAS.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_label('UndergroundFog'); a.tags = [unreal.Name('Mine297')]
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); log.append('placed UndergroundFog')
log.append('Next: 3 BPVar lines (BP_UndergroundFog_BPVar.txt), Compile, paste BP_UndergroundFog_graph.txt, Compile, Save.')
print('\n'.join(log)); unreal.log('\n'.join(log))
