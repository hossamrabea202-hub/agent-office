# Read-only: are the #242/#246 props and the #411 component in place after the restart?
import unreal
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
p = [a.get_actor_label() for a in acts if a.get_actor_label().startswith(('Props242_246', 'TmpKit418'))]
hud = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD')
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in sds.k2_gather_subobject_data_for_blueprint(hud)]
unreal.log('i5 check: props %s | ZombieHUD comps %s | CastleScroll asset %s | backup %s' % (p, names,
           unreal.EditorAssetLibrary.does_asset_exist('/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll'),
           unreal.EditorAssetLibrary.does_asset_exist('/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD_BACKUP411')))
