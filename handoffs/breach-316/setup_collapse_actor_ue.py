# #316 + #327 (adjustedfilm, 2026-10-31): BP_WallBreachCollapse = an actor that plays TGA's A_WallBreach_Collapse once on spawn
# and holds the last frame (no graph: single-node animation, not looping). Then it sets CollapseClass on the placed BreachFX.
#   py "<repo>/handoffs/breach-316/setup_collapse_actor_ue.py" --dry-run    /   without --dry-run
# Needs TGA's import first: py "<repo>/assets/tga/WallBreach/import_breach_ue.py" (DRY_RUN False).
import sys, unreal
DRY = '--dry-run' in sys.argv
DST = '/Game/CastleDefender/Gameplay/Siege/Breach'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sk, an = unreal.load_asset(DST + '/SK_WallBreach'), unreal.load_asset(DST + '/A_WallBreach_Collapse')
print('[collapse] SK_WallBreach %s, A_WallBreach_Collapse %s' % (bool(sk), bool(an)))
if not (sk and an): raise SystemExit('run TGA import_breach_ue.py first (and rename the anim to A_WallBreach_Collapse if UE named it after the take)')
p = DST + '/BP_WallBreachCollapse'
if not DRY:
    bp = unreal.load_asset(p) if EAL.does_asset_exist(p) else None
    if not bp:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor); bp = AT.create_asset('BP_WallBreachCollapse', DST, unreal.Blueprint, f)
    hs = SDS.k2_gather_subobject_data_for_blueprint(bp)
    names = {str(SDL.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in hs}
    if 'Collapse' in names: c = SDL.get_object(SDS.k2_find_subobject_data_from_handle(names['Collapse']))
    else:
        h, _ = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=unreal.SkeletalMeshComponent, blueprint_context=bp))
        SDS.rename_subobject(h, unreal.Text('Collapse')); c = SDL.get_object(SDS.k2_find_subobject_data_from_handle(h))
    c.set_editor_property('skeletal_mesh_asset' if hasattr(c, 'get_skeletal_mesh_asset') else 'skeletal_mesh', sk)
    c.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    ad = c.get_editor_property('animation_data'); ad.set_editor_property('anim_to_play', an)
    ad.set_editor_property('saved_looping', False); ad.set_editor_property('saved_playing', True); c.set_editor_property('animation_data', ad)
    c.set_collision_profile_name('NoCollision')
    BEL.compile_blueprint(bp); EAL.save_asset(p)
    fx = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'BreachFX']
    if fx:
        try: fx[0].set_editor_property('CollapseClass', bp.generated_class()); unreal.EditorLevelLibrary.save_current_level(); print('[collapse] BreachFX.CollapseClass set')
        except Exception as e: print('[collapse] set CollapseClass on BreachFX by hand (%s)' % e)
    else: print('[collapse] BreachFX not placed yet: run setup_breach316_ue.py --place, then this again')
print('[collapse] done' + (' (dry run)' if DRY else ''))
