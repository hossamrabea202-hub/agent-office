# #477 (i5, 2026-11-04). Owner: the 7 badge covers the health bar. The HP bar is 300 U wide at the bottom centre (150 U each side, gen_potion_polish.py), and my first spot, 0.546 / 0.929, sat on it.
# New spot: mirror of the potion badge across the bar, +177 / -73 U from centre / bottom at 1080p = 0.5922 / 0.9324. Only 2 class defaults, no graph change.
#   py ember_pos_ue.py --dry-run           shows old -> new
#   py ember_pos_ue.py --apply             sets, compiles, saves
#   py ember_pos_ue.py --apply --x 0.5922 --y 0.8    other spot if the right side is taken
# Aborts in PIE.
import sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; arg = lambda k, d: float(A[A.index(k) + 1]) if k in A else d
X, Y = arg('--x', 0.5922), arg('--y', 0.9324)
P = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'; bp = unreal.load_asset(P); c = unreal.get_default_object(bp.generated_class())
print('EmberX', c.get_editor_property('EmberX'), '->', X, '| EmberY', c.get_editor_property('EmberY'), '->', Y)
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
c.set_editor_property('EmberX', X); c.set_editor_property('EmberY', Y)
ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp); c = unreal.get_default_object(bp.generated_class())
print('compile', ok, '| now', c.get_editor_property('EmberX'), c.get_editor_property('EmberY'), '| saved', unreal.EditorAssetLibrary.save_asset(P, only_if_is_dirty=False))
