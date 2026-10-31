# MASTER ONLY (UE 5.3). #276 battle director setup (TGA, 2026-10-31). DRY_RUN = True only prints.
#   py "<repo>/handoffs/battle-276/setup_battle_ue.py"
# Creates /Game/CastleDefender/Gameplay/Siege/BP_BattleDirector (Actor, no components). Needs #274's BP_SiegeEngine /
# BP_SiegeRam / BP_SiegeTower and #138's BP_ZombieWallBreaker / BP_WallBreachSpot in the same folder (it checks).
import unreal
DRY_RUN = False
DST = '/Game/CastleDefender/Gameplay/Siege'
EAL = unreal.EditorAssetLibrary
for need in ('BP_SiegeEngine', 'BP_SiegeRam', 'BP_SiegeTower', 'BP_ZombieWallBreaker', 'BP_WallBreachSpot'):
    if not EAL.does_asset_exist(DST + '/' + need): unreal.log_warning('[battle setup] missing %s/%s (#274 / #138 first)' % (DST, need))
path = DST + '/BP_BattleDirector'
if EAL.does_asset_exist(path): unreal.log('[battle setup] %s exists' % path)
elif DRY_RUN: unreal.log('[battle setup] DRY: would create %s (parent Actor)' % path)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_BattleDirector', DST, unreal.Blueprint, f)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    unreal.log('[battle setup] created %s: paste VARIABLES.md + BP_BattleDirector_graph.txt, compile' % path)
